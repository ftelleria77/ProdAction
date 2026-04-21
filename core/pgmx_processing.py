"""Interpretación básica de archivos PGMX y generación de dibujos por pieza."""

import math
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from core.model import Piece, Project, normalize_piece_grain_direction
from tools import synthesize_pgmx as sp
from tools.pgmx_snapshot import (
    PgmxFeatureSnapshot,
    PgmxGeometrySnapshot,
    PgmxOperationSnapshot,
    PgmxSnapshot,
    PgmxWorkingStepSnapshot,
    read_pgmx_snapshot,
)


@dataclass
class MachiningOperation:
    """Representa un mecanizado detectado en el programa PGMX."""

    op_type: str
    x: float
    y: float
    diameter: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    face: str = "Top"
    depth: Optional[float] = None


@dataclass
class MillingPath:
    """Trayectoria de fresado detectada para una cara de la pieza."""

    face: str
    points: List[tuple[float, float]]
    entry_arrow: Optional["MillingArrow"] = None
    exit_arrow: Optional["MillingArrow"] = None


@dataclass
class MillingArrow:
    """Marca de sentido de avance en entrada o salida."""

    x: float
    y: float
    dx: float
    dy: float


@dataclass
class MillingCircle:
    """Fresado circular detectable y dibujable de forma explicita."""

    face: str
    center_x: float
    center_y: float
    radius: float
    winding: str = "CounterClockwise"
    entry_arrow: Optional[MillingArrow] = None
    exit_arrow: Optional[MillingArrow] = None


@dataclass
class PieceDrawingData:
    """Datos extraídos para dibujar una pieza."""

    width: float
    height: float
    thickness: Optional[float]
    source_path: Path
    operations: List[MachiningOperation]
    milling_paths: List[MillingPath] = field(default_factory=list)
    milling_circles: List[MillingCircle] = field(default_factory=list)
    face_dimensions: dict[str, tuple[float, float]] = field(default_factory=dict)


def _safe_float(value: str) -> Optional[float]:
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _extract_with_patterns(text: str, patterns: List[str]) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        value = _safe_float(match.group(1))
        if value is not None and value > 0:
            return value
    return None


def _decode_pgmx_bytes(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1", "windows-1252"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="ignore")


def _extract_dimensions_from_xcam_xml(text: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None, None, None

    for element in root.iter():
        if _strip_namespace(element.tag) != "WorkPiece":
            continue

        length = _safe_float(
            _find_text(element, "./{*}Length")
            or _find_text(element, "./{*}Geometry/{*}Length")
            or ""
        )
        width = _safe_float(
            _find_text(element, "./{*}Width")
            or _find_text(element, "./{*}Geometry/{*}Width")
            or ""
        )
        thickness = _safe_float(
            _find_text(element, "./{*}Depth")
            or _find_text(element, "./{*}Geometry/{*}Depth")
            or ""
        )

        if any(value is not None and value > 0 for value in (width, length, thickness)):
            return width, length, thickness

    return None, None, None


def _extract_dimensions(text: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Extrae ancho, alto y espesor del programa PGMX.

    En archivos XCam, la correspondencia es:
    - ancho  -> Width
    - alto   -> Length
    - espesor -> Depth
    """

    width_xml, height_xml, thickness_xml = _extract_dimensions_from_xcam_xml(text)
    if any(value is not None and value > 0 for value in (width_xml, height_xml, thickness_xml)):
        return width_xml, height_xml, thickness_xml

    width_patterns = [
        r"\b(?:x|ancho|width|larg(?:o)?)\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
        r"\b(?:dimx|sizex|size_x)\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
    ]
    height_patterns = [
        r"\b(?:y|alto|height|anch(?:o)?)\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
        r"\b(?:dimy|sizey|size_y)\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
    ]
    thickness_patterns = [
        r"\b(?:z|espesor|thickness|thk)\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
        r"\b(?:dimz|sizez|size_z)\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
    ]

    width = _extract_with_patterns(text, width_patterns)
    height = _extract_with_patterns(text, height_patterns)
    thickness = _extract_with_patterns(text, thickness_patterns)
    return width, height, thickness


def _extract_operations(text: str) -> List[MachiningOperation]:
    """Extrae operaciones básicas (taladros y ranuras) por coordenadas."""

    operations: List[MachiningOperation] = []

    drill_patterns = [
        r"\b(?:drill|taladro|hole|foro)\b[^\n]*?\bx\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)\b[^\n]*?\by\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)\b[^\n]*?(?:\bd\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?))?",
        r"\b(?:drill|taladro|hole|foro)\b\s*\(?\s*([0-9]+(?:[\.,][0-9]+)?)\s*[,;]\s*([0-9]+(?:[\.,][0-9]+)?)\s*\)?(?:\s*[,;]\s*([0-9]+(?:[\.,][0-9]+)?))?",
    ]

    slot_patterns = [
        r"\b(?:slot|ranura|cajeado|pocket)\b[^\n]*?\bx\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)\b[^\n]*?\by\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)\b[^\n]*?\bw\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)\b[^\n]*?\bh\s*[:=]\s*([0-9]+(?:[\.,][0-9]+)?)",
    ]

    def parse_attr_map(raw_attrs: str) -> dict:
        attrs = {}
        for attr_match in re.finditer(
            r"([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
            raw_attrs,
            flags=re.IGNORECASE,
        ):
            key = attr_match.group(1).strip().lower()
            value = attr_match.group(2) or attr_match.group(3) or attr_match.group(4) or ""
            attrs[key] = value.strip()
        return attrs

    def first_attr(attrs: dict, keys: List[str]) -> Optional[float]:
        for key in keys:
            if key in attrs:
                value = _safe_float(attrs.get(key))
                if value is not None:
                    return value
        return None

    for pattern in drill_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            x_val = _safe_float(match.group(1))
            y_val = _safe_float(match.group(2))
            d_val = _safe_float(match.group(3)) if match.lastindex and match.lastindex >= 3 else None
            if x_val is None or y_val is None:
                continue
            operations.append(
                MachiningOperation(
                    op_type="drill",
                    x=x_val,
                    y=y_val,
                    diameter=d_val,
                )
            )

    for pattern in slot_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            x_val = _safe_float(match.group(1))
            y_val = _safe_float(match.group(2))
            w_val = _safe_float(match.group(3))
            h_val = _safe_float(match.group(4))
            if None in (x_val, y_val, w_val, h_val):
                continue
            operations.append(
                MachiningOperation(
                    op_type="slot",
                    x=x_val,
                    y=y_val,
                    width=w_val,
                    height=h_val,
                )
            )

    # Formato XML/tag típico de PGMX (ejemplos: <BORING X="..." Y="..." D="..."/>).
    for match in re.finditer(r"<\s*([A-Za-z0-9_:-]+)\b([^>]*)>", text):
        tag_name = (match.group(1) or "").strip().lower()
        attrs_raw = match.group(2) or ""
        attrs = parse_attr_map(attrs_raw)

        x_val = first_attr(attrs, ["x", "x1", "posx", "centerx", "cx"])
        y_val = first_attr(attrs, ["y", "y1", "posy", "centery", "cy"])

        if x_val is None or y_val is None:
            continue

        diameter = first_attr(attrs, ["d", "diameter", "diam", "tooldiameter", "r"])
        width = first_attr(attrs, ["w", "width", "sizex", "dx"])
        height = first_attr(attrs, ["h", "height", "sizey", "dy"])

        if any(word in tag_name for word in ["slot", "ranura", "pocket", "cajeado"]):
            if width is None:
                width = first_attr(attrs, ["length", "l"])
            if height is None:
                height = first_attr(attrs, ["ancho", "thickness"])
            if width is not None and height is not None:
                operations.append(
                    MachiningOperation(
                        op_type="slot",
                        x=x_val,
                        y=y_val,
                        width=width,
                        height=height,
                    )
                )
            continue

        if any(word in tag_name for word in ["drill", "hole", "foro", "taladro", "bore", "boring"]):
            operations.append(
                MachiningOperation(
                    op_type="drill",
                    x=x_val,
                    y=y_val,
                    diameter=diameter,
                )
            )
            continue

        # Fallback: tag con coordenadas + diámetro => taladro.
        if diameter is not None:
            operations.append(
                MachiningOperation(
                    op_type="drill",
                    x=x_val,
                    y=y_val,
                    diameter=diameter,
                )
            )

    # Soporte G-code básico para ciclo de taladrado G81/G82/G83.
    for line in text.splitlines():
        raw_line = line.strip()
        if not raw_line:
            continue
        if not re.search(r"\bG8[123]\b", raw_line, flags=re.IGNORECASE):
            continue

        x_match = re.search(r"\bX\s*(-?[0-9]+(?:[\.,][0-9]+)?)", raw_line, flags=re.IGNORECASE)
        y_match = re.search(r"\bY\s*(-?[0-9]+(?:[\.,][0-9]+)?)", raw_line, flags=re.IGNORECASE)
        if not x_match or not y_match:
            continue

        x_val = _safe_float(x_match.group(1))
        y_val = _safe_float(y_match.group(1))
        if x_val is None or y_val is None:
            continue

        d_match = re.search(r"\bD\s*(-?[0-9]+(?:[\.,][0-9]+)?)", raw_line, flags=re.IGNORECASE)
        diameter = _safe_float(d_match.group(1)) if d_match else None
        operations.append(
            MachiningOperation(
                op_type="drill",
                x=x_val,
                y=y_val,
                diameter=diameter,
            )
        )

    # Eliminar posibles duplicados exactos para evitar sobreconteo.
    deduplicated: List[MachiningOperation] = []
    seen = set()
    for op in operations:
        key = (
            op.op_type,
            round(op.x, 4),
            round(op.y, 4),
            round(op.diameter, 4) if op.diameter is not None else None,
            round(op.width, 4) if op.width is not None else None,
            round(op.height, 4) if op.height is not None else None,
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(op)

    return deduplicated


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _find_text(element: ET.Element, path: str) -> Optional[str]:
    node = element.find(path)
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value if value else None


def _build_xcam_maps(root: ET.Element) -> tuple[dict[str, ET.Element], dict[str, tuple[str, tuple[float, float]]]]:
    """Construye mapas por ID para resolver objetos y caras de trabajo."""

    id_map: dict[str, ET.Element] = {}
    for element in root.iter():
        key_id = _find_text(element, "./{*}Key/{*}ID")
        if key_id:
            id_map[key_id] = element

    plane_map: dict[str, tuple[str, tuple[float, float]]] = {}
    for plane_id, element in id_map.items():
        if _strip_namespace(element.tag) != "Plane":
            continue

        face_name = (
            _find_text(element, "./{*}Type")
            or _find_text(element, "./{*}Name")
            or "Top"
        )
        x_dim = _safe_float(_find_text(element, "./{*}XDimension") or "") or 0.0
        y_dim = _safe_float(_find_text(element, "./{*}YDimension") or "") or 0.0
        plane_map[plane_id] = (face_name, (x_dim, y_dim))

    return id_map, plane_map


def _extract_enabled_feature_ids(root: ET.Element) -> set[str]:
    """Obtiene IDs de ManufacturingFeature activos en el MainWorkplan.

    En XCam, las condiciones paramétricas suelen resolverse en los elementos
    ejecutables del plan de trabajo. Si un MachiningWorkingStep queda excluido,
    normalmente aparece con IsEnabled=false o directamente fuera del MainWorkplan.
    """

    enabled_feature_ids: set[str] = set()

    for element in root.iter():
        obj_type = _find_text(element, "./{*}Key/{*}ObjectType") or ""
        if obj_type != "ScmGroup.XCam.MachiningDataModel.ProjectModule.MainWorkplan":
            continue

        workplan_enabled = (_find_text(element, "./{*}IsEnabled") or "true").strip().lower()
        if workplan_enabled == "false":
            continue

        elements_node = element.find("./{*}Elements")
        if elements_node is None:
            continue

        for executable in elements_node:
            executable_type = ""
            for attr_key, attr_value in executable.attrib.items():
                if _strip_namespace(attr_key).lower() == "type":
                    executable_type = attr_value or ""
                    break
            if "machiningworkingstep" not in executable_type.lower():
                continue

            step_enabled = (_find_text(executable, "./{*}IsEnabled") or "true").strip().lower()
            if step_enabled == "false":
                continue

            feature_id = _find_text(executable, "./{*}ManufacturingFeatureID/{*}ID")
            if feature_id:
                enabled_feature_ids.add(feature_id)

    return enabled_feature_ids


def _extract_replicate_features(root: ET.Element, geom_points: dict[str, tuple[float, float]], geom_face: dict[str, str], enabled_feature_ids: set[str]) -> List[MachiningOperation]:
    """Extrae operaciones de perforaciones múltiples (ReplicateFeature) del XML XCam.
    
    Para cada ReplicateFeature encontrado:
    - Obtiene el patrón rectangular (NumberOfColumns, NumberOfRows, Spacing, RowSpacing)
    - Obtiene la perforación base (RoundHole del BaseFeature)
    - Expande las coordenadas según el patrón
    - Retorna una lista de MachiningOperation para cada perforación expandida
    """
    operations: List[MachiningOperation] = []
    
    for element in root.iter():
        if _strip_namespace(element.tag) != "ManufacturingFeature":
            continue

        feature_id = _find_text(element, "./{*}Key/{*}ID")
        if enabled_feature_ids and feature_id and feature_id not in enabled_feature_ids:
            continue

        feature_type = ""
        for attr_key, attr_value in element.attrib.items():
            if _strip_namespace(attr_key).lower() == "type":
                feature_type = attr_value or ""
                break

        if "replicatefeature" not in feature_type.lower():
            continue

        # Obtener geometría base
        geometry_id = _find_text(element, "./{*}GeometryID/{*}ID")
        if not geometry_id or geometry_id not in geom_points:
            continue

        x_base, y_base = geom_points[geometry_id]
        face_name = geom_face.get(geometry_id, "Top")

        # Buscar ReplicationPattern
        rep_pattern = element.find("./{*}ReplicationPattern")
        if rep_pattern is None:
            continue

        # Extraer parámetros del patrón rectangular
        num_cols = _safe_float(_find_text(rep_pattern, "./{*}NumberOfColumns") or "") or 1.0
        num_rows = _safe_float(_find_text(rep_pattern, "./{*}NumberOfRows") or "") or 1.0
        spacing_x = _safe_float(_find_text(rep_pattern, "./{*}Spacing") or "") or 0.0
        spacing_y = _safe_float(_find_text(rep_pattern, "./{*}RowSpacing") or "") or 0.0

        # Buscar BaseFeature (RoundHole)
        base_feature = element.find("./{*}BaseFeature")
        if base_feature is None:
            continue

        diameter = _safe_float(_find_text(base_feature, "./{*}Diameter") or "")
        depth = _safe_float(_find_text(base_feature, "./{*}Depth/{*}EndDepth") or "")

        # Generar coordenadas expandidas según el patrón
        num_cols_int = int(num_cols)
        num_rows_int = int(num_rows)

        for row in range(num_rows_int):
            for col in range(num_cols_int):
                x = x_base + (col * spacing_x)
                y = y_base + (row * spacing_y)
                operations.append(
                    MachiningOperation(
                        op_type="drill",
                        x=x,
                        y=y,
                        diameter=diameter,
                        face=face_name,
                        depth=depth,
                    )
                )

    return operations


def _extract_operations_from_xcam_xml(text: str) -> tuple[List[MachiningOperation], dict[str, tuple[float, float]]]:
    """Extrae mecanizados y dimensiones por cara desde XML XCam."""

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return [], {}

    id_map, plane_map = _build_xcam_maps(root)
    enabled_feature_ids = _extract_enabled_feature_ids(root)
    geom_points: dict[str, tuple[float, float]] = {}
    geom_face: dict[str, str] = {}
    face_dimensions: dict[str, tuple[float, float]] = {}

    for element in root.iter():
        key_id = _find_text(element, "./{*}Key/{*}ID")
        if not key_id:
            continue
        x_val = _safe_float(_find_text(element, "./{*}_x") or "")
        y_val = _safe_float(_find_text(element, "./{*}_y") or "")
        if x_val is None or y_val is None:
            continue
        geom_points[key_id] = (x_val, y_val)

        plane_id = _find_text(element, "./{*}PlaneID/{*}ID")
        if plane_id and plane_id in plane_map:
            face_name, dims = plane_map[plane_id]
            geom_face[key_id] = face_name
            face_dimensions[face_name] = dims

    operations: List[MachiningOperation] = []
    
    # Extraer perforaciones individuales (RoundHole)
    for element in root.iter():
        if _strip_namespace(element.tag) != "ManufacturingFeature":
            continue

        feature_id = _find_text(element, "./{*}Key/{*}ID")
        if enabled_feature_ids and feature_id and feature_id not in enabled_feature_ids:
            continue

        feature_type = ""
        for attr_key, attr_value in element.attrib.items():
            if _strip_namespace(attr_key).lower() == "type":
                feature_type = attr_value or ""
                break
        if not feature_type:
            continue

        geometry_id = _find_text(element, "./{*}GeometryID/{*}ID")
        if not geometry_id or geometry_id not in geom_points:
            continue

        x_val, y_val = geom_points[geometry_id]
        face_name = geom_face.get(geometry_id, "Top")

        if "roundhole" in feature_type.lower():
            diameter = _safe_float(_find_text(element, "./{*}Diameter") or "")
            depth = _safe_float(_find_text(element, "./{*}Depth/{*}EndDepth") or "")
            operations.append(
                MachiningOperation(
                    op_type="drill",
                    x=x_val,
                    y=y_val,
                    diameter=diameter,
                    face=face_name,
                    depth=depth,
                )
            )

    # Extraer perforaciones múltiples (ReplicateFeature)
    replicate_ops = _extract_replicate_features(root, geom_points, geom_face, enabled_feature_ids)
    operations.extend(replicate_ops)

    return operations, face_dimensions


def _extract_milling_paths_from_xcam_xml(text: str) -> tuple[List[MillingPath], dict[str, tuple[float, float]]]:
    """Extrae trayectorias de fresado desde GeneralProfileFeature en XML XCam."""

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return [], {}

    id_map, plane_map = _build_xcam_maps(root)
    enabled_feature_ids = _extract_enabled_feature_ids(root)
    milling_paths: List[MillingPath] = []
    face_dimensions: dict[str, tuple[float, float]] = {}

    for feature in root.iter():
        if _strip_namespace(feature.tag) != "ManufacturingFeature":
            continue

        feature_id = _find_text(feature, "./{*}Key/{*}ID")
        if enabled_feature_ids and feature_id and feature_id not in enabled_feature_ids:
            continue

        feature_type = ""
        for attr_key, attr_value in feature.attrib.items():
            if _strip_namespace(attr_key).lower() == "type":
                feature_type = attr_value or ""
                break

        if "generalprofilefeature" not in feature_type.lower():
            continue

        geometry_id = _find_text(feature, "./{*}GeometryID/{*}ID")
        if not geometry_id:
            continue

        geometry_element = id_map.get(geometry_id)
        if geometry_element is None:
            continue

        plane_id = _find_text(geometry_element, "./{*}PlaneID/{*}ID")
        face_name = "Top"
        if plane_id and plane_id in plane_map:
            face_name, dims = plane_map[plane_id]
            face_dimensions[face_name] = dims

        # Parse _serializingMembers/string children.
        # Each <string> encodes one curve segment:
        #   "8 r l\n1 x y z dx dy dz\n"
        # Where (x, y) is the END-POINT of that segment and (dx, dy, dz) + l
        # describe the OUTGOING move to the next point.
        # So the polyline points are: all (x,y) values PLUS the implied final
        # destination: (x_last + dx_last*l_last, y_last + dy_last*l_last).
        # For closed curves the implied final point equals the first point.
        seg_points: List[tuple[float, float]] = []
        last_dx: float = 0.0
        last_dy: float = 0.0
        last_l: float = 0.0

        for member_el in geometry_element.iter():
            if _strip_namespace(member_el.tag) != "string":
                continue
            raw = (member_el.text or "").strip()
            if not raw:
                continue
            seg_x: Optional[float] = None
            seg_y: Optional[float] = None
            seg_dx: float = 0.0
            seg_dy: float = 0.0
            seg_l: float = 0.0
            for seg_line in raw.splitlines():
                seg_line = seg_line.strip()
                m8 = re.match(
                    r"^8\s+(-?[0-9]+(?:[\.,][0-9]+)?)\s+(-?[0-9]+(?:[\.,][0-9]+)?)",
                    seg_line,
                )
                if m8:
                    seg_l = _safe_float(m8.group(2)) or 0.0
                    continue
                m1 = re.match(
                    r"^1\s+(-?[0-9]+(?:[\.,][0-9]+)?)\s+(-?[0-9]+(?:[\.,][0-9]+)?)"
                    r"\s+(-?[0-9]+(?:[\.,][0-9]+)?)"
                    r"\s+(-?[0-9]+(?:[\.,][0-9]+)?)\s+(-?[0-9]+(?:[\.,][0-9]+)?)",
                    seg_line,
                )
                if m1:
                    seg_x = _safe_float(m1.group(1))
                    seg_y = _safe_float(m1.group(2))
                    seg_dx = _safe_float(m1.group(4)) or 0.0
                    seg_dy = _safe_float(m1.group(5)) or 0.0
            if seg_x is None or seg_y is None:
                continue
            seg_points.append((seg_x, seg_y))
            last_dx, last_dy, last_l = seg_dx, seg_dy, seg_l

        if seg_points:
            implied_end = (
                seg_points[-1][0] + last_dx * last_l,
                seg_points[-1][1] + last_dy * last_l,
            )
            _tol = 0.5
            if abs(implied_end[0] - seg_points[0][0]) > _tol or abs(implied_end[1] - seg_points[0][1]) > _tol:
                seg_points.append(implied_end)
            else:
                seg_points.append(seg_points[0])

        if len(seg_points) >= 2:
            dedup_points: List[tuple[float, float]] = []
            for point in seg_points:
                if dedup_points and point == dedup_points[-1]:
                    continue
                dedup_points.append(point)
            if len(dedup_points) >= 2:
                milling_paths.append(MillingPath(face=face_name, points=dedup_points))

    return milling_paths, face_dimensions


def _read_pgmx_text(source_path: Path) -> str:
    """Lee contenido textual del archivo PGMX, incluso si viene comprimido."""

    if zipfile.is_zipfile(source_path):
        xml_chunks: List[str] = []
        with zipfile.ZipFile(source_path) as zip_file:
            entry_names = [name for name in zip_file.namelist() if name.lower().endswith(".xml")]
            for entry_name in entry_names:
                xml_chunks.append(_decode_pgmx_bytes(zip_file.read(entry_name)))
        if xml_chunks:
            return "\n".join(xml_chunks)

    return _decode_pgmx_bytes(source_path.read_bytes())


def _iter_pgmx_search_roots(project: Project, module_path: Path) -> list[Path]:
    roots = [
        module_path,
        Path(project.root_directory) / "archive",
        Path(project.root_directory).parent / "archive",
        module_path.parent / "archive",
    ]
    seen: set[str] = set()
    unique_roots: list[Path] = []
    for root in roots:
        root_key = str(root)
        if root_key in seen or not root.exists():
            continue
        seen.add(root_key)
        unique_roots.append(root)
    return unique_roots


def _find_pgmx_case_insensitive_match(project: Project, module_path: Path, source_name: str) -> Optional[Path]:
    source_name_lower = str(source_name or "").strip().lower()
    if not source_name_lower:
        return None

    for root in _iter_pgmx_search_roots(project, module_path):
        for candidate in root.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() != ".pgmx":
                continue
            if candidate.name.lower() == source_name_lower:
                return candidate
    return None


def _resolve_source_path(project: Project, piece: Piece, module_path: Path) -> Optional[Path]:
    source_value = str(piece.cnc_source or "").strip()
    if not source_value:
        return None

    direct_path = Path(source_value)
    if direct_path.is_file():
        return direct_path

    module_candidate = module_path / source_value
    if module_candidate.is_file():
        return module_candidate

    project_candidate = Path(project.root_directory) / source_value
    if project_candidate.is_file():
        return project_candidate

    source_name = Path(source_value).name
    archive_candidates = [
        Path(project.root_directory) / "archive" / source_name,
        Path(project.root_directory).parent / "archive" / source_name,
        module_path.parent / "archive" / source_name,
    ]
    for candidate in archive_candidates:
        if candidate.is_file():
            return candidate

    matched_by_name = next(module_path.rglob(source_name), None)
    if matched_by_name and matched_by_name.is_file():
        return matched_by_name

    case_insensitive_match = _find_pgmx_case_insensitive_match(project, module_path, source_name)
    if case_insensitive_match is not None:
        return case_insensitive_match

    return None


def get_pgmx_program_dimensions(project: Project, piece: Piece, module_path: Path) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Devuelve las dimensiones reales del programa PGMX asociado a una pieza."""

    source_path = _resolve_source_path(project, piece, module_path)
    if source_path is None:
        return None, None, None

    try:
        text = _read_pgmx_text(source_path)
    except OSError:
        return None, None, None

    return _extract_dimensions(text)


def _normalize_program_dimension(value) -> Optional[float]:
    parsed = _safe_float(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def get_stored_program_dimensions(piece: Piece) -> tuple[Optional[float], Optional[float], Optional[float]]:
    return (
        _normalize_program_dimension(getattr(piece, "program_width", None)),
        _normalize_program_dimension(getattr(piece, "program_height", None)),
        _normalize_program_dimension(getattr(piece, "program_thickness", None)),
    )


def resolve_piece_program_dimensions(
    project: Project,
    piece: Piece,
    module_path: Path,
    cache: Optional[dict[tuple[str, str], tuple[Optional[float], Optional[float], Optional[float]]]] = None,
    prefer_stored: bool = True,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    source_value = str(piece.cnc_source or "").strip()
    stored_width, stored_height, stored_thickness = get_stored_program_dimensions(piece)

    if prefer_stored and source_value and stored_width is not None and stored_height is not None:
        return stored_width, stored_height, stored_thickness

    if not source_value:
        return None, None, None

    if cache is None:
        return get_pgmx_program_dimensions(project, piece, module_path)

    cache_key = (str(module_path), source_value)
    if cache_key not in cache:
        cache[cache_key] = get_pgmx_program_dimensions(project, piece, module_path)
    return cache[cache_key]


def persist_piece_program_dimensions(
    project: Project,
    piece: Piece,
    module_path: Path,
    cache: Optional[dict[tuple[str, str], tuple[Optional[float], Optional[float], Optional[float]]]] = None,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    program_width, program_height, program_thickness = resolve_piece_program_dimensions(
        project,
        piece,
        module_path,
        cache=cache,
        prefer_stored=False,
    )

    piece.program_width = _normalize_program_dimension(program_width)
    piece.program_height = _normalize_program_dimension(program_height)
    piece.program_thickness = _normalize_program_dimension(program_thickness)
    return piece.program_width, piece.program_height, piece.program_thickness


def _dimensions_match(left: Optional[float], right: Optional[float], tolerance: float = 0.01) -> bool:
    if left is None or right is None:
        return False
    return abs(left - right) <= tolerance


def _piece_dimensions_match_program(
    piece_width: Optional[float],
    piece_height: Optional[float],
    program_width: Optional[float],
    program_height: Optional[float],
) -> bool:
    direct_match = _dimensions_match(piece_width, program_width) and _dimensions_match(piece_height, program_height)
    rotated_match = _dimensions_match(piece_width, program_height) and _dimensions_match(piece_height, program_width)
    return direct_match or rotated_match


def _best_program_dimension_alignment(
    piece_width: Optional[float],
    piece_height: Optional[float],
    program_width: Optional[float],
    program_height: Optional[float],
) -> tuple[Optional[float], Optional[float], int, list[float], float]:
    alignments = []
    for is_swapped, aligned_width, aligned_height, differing_values in (
        (
            False,
            program_width,
            program_height,
            [
                value
                for piece_value, value in ((piece_width, program_width), (piece_height, program_height))
                if not _dimensions_match(piece_value, value)
            ],
        ),
        (
            True,
            program_height,
            program_width,
            [
                value
                for piece_value, value in ((piece_width, program_height), (piece_height, program_width))
                if not _dimensions_match(piece_value, value)
            ],
        ),
    ):
        total_delta = 0.0
        for piece_value, candidate_value in ((piece_width, aligned_width), (piece_height, aligned_height)):
            if piece_value is None or candidate_value is None:
                continue
            total_delta += abs(piece_value - candidate_value)
        alignments.append((is_swapped, aligned_width, aligned_height, len(differing_values), differing_values, total_delta))

    _, aligned_width, aligned_height, difference_count, differing_values, total_delta = min(
        alignments,
        key=lambda item: (item[3], item[5], int(item[0])),
    )
    return aligned_width, aligned_height, difference_count, differing_values, total_delta


def _program_axes_are_swapped(
    piece_width: Optional[float],
    piece_height: Optional[float],
    program_width: Optional[float],
    program_height: Optional[float],
) -> bool:
    alignments = []
    for is_swapped, aligned_width, aligned_height, differing_values in (
        (
            False,
            program_width,
            program_height,
            [
                value
                for piece_value, value in ((piece_width, program_width), (piece_height, program_height))
                if not _dimensions_match(piece_value, value)
            ],
        ),
        (
            True,
            program_height,
            program_width,
            [
                value
                for piece_value, value in ((piece_width, program_height), (piece_height, program_width))
                if not _dimensions_match(piece_value, value)
            ],
        ),
    ):
        total_delta = 0.0
        for piece_value, candidate_value in ((piece_width, aligned_width), (piece_height, aligned_height)):
            if piece_value is None or candidate_value is None:
                continue
            total_delta += abs(piece_value - candidate_value)
        alignments.append((is_swapped, len(differing_values), total_delta))

    best_alignment = min(alignments, key=lambda item: (item[1], item[2], int(item[0])))
    return bool(best_alignment[0])


def resolve_piece_grain_hatch_axis(
    grain_direction,
    piece_width: Optional[float],
    piece_height: Optional[float],
    drawn_width: Optional[float],
    drawn_height: Optional[float],
) -> Optional[str]:
    """Devuelve el eje visual del rayado de veta segun como quedo dibujada la pieza."""

    grain_code = normalize_piece_grain_direction(grain_direction)
    if grain_code not in {"1", "2"}:
        return None

    normalized_piece_width = float(piece_width) if piece_width is not None and piece_width > 0 else None
    normalized_piece_height = float(piece_height) if piece_height is not None and piece_height > 0 else None
    normalized_drawn_width = float(drawn_width) if drawn_width is not None and drawn_width > 0 else None
    normalized_drawn_height = float(drawn_height) if drawn_height is not None and drawn_height > 0 else None

    axes_swapped = _program_axes_are_swapped(
        normalized_piece_width,
        normalized_piece_height,
        normalized_drawn_width,
        normalized_drawn_height,
    )
    if grain_code == "1":
        return "horizontal" if axes_swapped else "vertical"
    return "vertical" if axes_swapped else "horizontal"


def _program_dimension_difference_summary(
    piece_width: Optional[float],
    piece_height: Optional[float],
    program_width: Optional[float],
    program_height: Optional[float],
) -> tuple[int, list[float]]:
    _, _, difference_count, differing_values, _ = _best_program_dimension_alignment(
        piece_width,
        piece_height,
        program_width,
        program_height,
    )
    return difference_count, differing_values


def get_program_piece_yield_count(
    piece_width: Optional[float],
    piece_height: Optional[float],
    program_width: Optional[float],
    program_height: Optional[float],
) -> int:
    aligned_width, aligned_height, difference_count, _, _ = _best_program_dimension_alignment(
        piece_width,
        piece_height,
        program_width,
        program_height,
    )

    if difference_count != 1:
        return 1

    width_doubled = (
        piece_width is not None
        and piece_width > 0
        and aligned_width is not None
        and aligned_width >= (piece_width * 2.0) - 0.01
        and _dimensions_match(piece_height, aligned_height)
    )
    height_doubled = (
        piece_height is not None
        and piece_height > 0
        and aligned_height is not None
        and aligned_height >= (piece_height * 2.0) - 0.01
        and _dimensions_match(piece_width, aligned_width)
    )

    if width_doubled or height_doubled:
        return 2
    return 1


def _normalize_program_source(source_value: Optional[str]) -> str:
    return str(source_value or "").strip().replace("\\", "/").lower()


def _build_program_dimension_note_info(
    project: Project,
    piece: Piece,
    module_path: Path,
    cache: Optional[dict[tuple[str, str], tuple[Optional[float], Optional[float], Optional[float]]]] = None,
    only_if_different: bool = True,
) -> dict[str, object]:
    source_value = str(piece.cnc_source or "").strip()
    has_f6_source = bool(str(getattr(piece, "f6_source", "") or "").strip())
    if not source_value:
        return {
            "note": "",
            "source_key": "",
            "difference_count": 0,
            "single_measure_text": "",
            "has_f6_source": has_f6_source,
        }

    program_width, program_height, _ = resolve_piece_program_dimensions(
        project,
        piece,
        module_path,
        cache=cache,
        prefer_stored=True,
    )

    if not (program_width and program_width > 0 and program_height and program_height > 0):
        return {
            "note": "",
            "source_key": _normalize_program_source(source_value),
            "difference_count": 0,
            "single_measure_text": "",
            "has_f6_source": has_f6_source,
        }

    difference_count, differing_values = _program_dimension_difference_summary(
        piece.width,
        piece.height,
        program_width,
        program_height,
    )

    if only_if_different and difference_count == 0:
        note = ""
        single_measure_text = ""
    elif difference_count == 1 and differing_values:
        single_measure_text = _format_dim(differing_values[0])
        note = f"Pasar {single_measure_text}"
    else:
        single_measure_text = ""
        note = f"Pasar {_format_dim(program_width)} x {_format_dim(program_height)}"

    return {
        "note": note,
        "source_key": _normalize_program_source(source_value),
        "difference_count": difference_count,
        "single_measure_text": single_measure_text,
        "has_f6_source": has_f6_source,
    }


def get_pgmx_program_dimension_notes(
    project: Project,
    pieces: List[Piece],
    module_path: Path,
    cache: Optional[dict[tuple[str, str], tuple[Optional[float], Optional[float], Optional[float]]]] = None,
    only_if_different: bool = True,
) -> List[str]:
    """Calcula notas de programa para una lista ordenada de piezas del módulo."""

    return [
        str(item["note"])
        for item in get_pgmx_program_dimension_annotations(
            project,
            pieces,
            module_path,
            cache=cache,
            only_if_different=only_if_different,
        )
    ]


def get_pgmx_program_dimension_annotations(
    project: Project,
    pieces: List[Piece],
    module_path: Path,
    cache: Optional[dict[tuple[str, str], tuple[Optional[float], Optional[float], Optional[float]]]] = None,
    only_if_different: bool = True,
) -> List[dict[str, object]]:
    """Calcula notas y banderas derivadas de programa para piezas del módulo."""

    infos = [
        _build_program_dimension_note_info(
            project,
            piece,
            module_path,
            cache=cache,
            only_if_different=only_if_different,
        )
        for piece in pieces
    ]

    first_piece_by_program: dict[tuple[str, str], str] = {}
    annotations: List[dict[str, object]] = []

    for piece, info in zip(pieces, infos):
        note = str(info["note"])
        difference_count = int(info["difference_count"])
        source_key = str(info["source_key"])
        single_measure_text = str(info["single_measure_text"])
        has_f6_source = bool(info.get("has_f6_source"))
        exclude_from_cut_diagrams = False

        if difference_count == 1 and source_key and single_measure_text:
            program_key = (source_key, single_measure_text)
            if program_key in first_piece_by_program:
                note = f"Cortar de {first_piece_by_program[program_key]}"
                exclude_from_cut_diagrams = True
            else:
                first_piece_by_program[program_key] = str(piece.name or piece.id or "pieza").strip()

        if has_f6_source:
            note = f"F6 - {note}" if note else "F6"

        annotations.append(
            {
                "note": note,
                "exclude_from_cut_diagrams": exclude_from_cut_diagrams,
            }
        )

    return annotations


def get_pgmx_program_dimension_note(
    project: Project,
    piece: Piece,
    module_path: Path,
    cache: Optional[dict[tuple[str, str], tuple[Optional[float], Optional[float], Optional[float]]]] = None,
    only_if_different: bool = True,
) -> str:
    """Formatea la dimensión real del programa PGMX como 'Pasar ancho x alto'."""
    info = _build_program_dimension_note_info(
        project,
        piece,
        module_path,
        cache=cache,
        only_if_different=only_if_different,
    )
    return str(info["note"])


def _normalize_face_name(value: Optional[str], default: str = "Top") -> str:
    raw = str(value or default).strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "top": "Top",
        "superior": "Top",
        "carasuperior": "Top",
        "bottom": "Bottom",
        "inferior": "Bottom",
        "carainferior": "Bottom",
        "front": "Front",
        "frontal": "Front",
        "delantera": "Front",
        "back": "Back",
        "trasera": "Back",
        "right": "Right",
        "derecha": "Right",
        "left": "Left",
        "izquierda": "Left",
    }
    return mapping.get(raw, default)


def _points_close_2d(
    left: tuple[float, float],
    right: tuple[float, float],
    tolerance: float = 1e-6,
) -> bool:
    return abs(left[0] - right[0]) <= tolerance and abs(left[1] - right[1]) <= tolerance


def _deduplicate_points_2d(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    deduplicated: list[tuple[float, float]] = []
    for point in points:
        normalized = (float(point[0]), float(point[1]))
        if deduplicated and _points_close_2d(deduplicated[-1], normalized):
            continue
        deduplicated.append(normalized)
    return deduplicated


def _linked_snapshot_operation(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
    step: Optional[PgmxWorkingStepSnapshot],
) -> Optional[PgmxOperationSnapshot]:
    if step is not None and step.operation_ref is not None and step.operation_ref.id:
        return snapshot.operation_by_id.get(step.operation_ref.id)
    for operation_ref in feature.operation_refs:
        if not operation_ref.id:
            continue
        operation = snapshot.operation_by_id.get(operation_ref.id)
        if operation is not None:
            return operation
    return None


def _ordered_snapshot_features(
    snapshot: PgmxSnapshot,
) -> list[tuple[PgmxFeatureSnapshot, Optional[PgmxOperationSnapshot], Optional[PgmxWorkingStepSnapshot]]]:
    features_by_id = snapshot.feature_by_id
    ordered_entries: list[tuple[PgmxFeatureSnapshot, Optional[PgmxOperationSnapshot], Optional[PgmxWorkingStepSnapshot]]] = []
    seen_feature_ids: set[str] = set()
    has_workplan_features = False

    for step in snapshot.working_steps:
        if not step.is_enabled:
            continue
        feature_ref = step.manufacturing_feature_ref
        if feature_ref is None or not feature_ref.id:
            continue
        feature = features_by_id.get(feature_ref.id)
        if feature is None:
            continue
        ordered_entries.append((feature, _linked_snapshot_operation(snapshot, feature, step), step))
        seen_feature_ids.add(feature.id)
        has_workplan_features = True

    if not has_workplan_features:
        for feature in snapshot.features:
            if feature.id in seen_feature_ids:
                continue
            ordered_entries.append((feature, _linked_snapshot_operation(snapshot, feature, None), None))

    return ordered_entries


def _primitive_points_2d(primitive: sp.GeometryPrimitiveSpec) -> list[tuple[float, float]]:
    if primitive.primitive_type == "Line":
        return [
            (float(primitive.start_point[0]), float(primitive.start_point[1])),
            (float(primitive.end_point[0]), float(primitive.end_point[1])),
        ]

    if (
        primitive.primitive_type != "Arc"
        or primitive.center_point is None
        or primitive.radius is None
        or primitive.u_vector is None
        or primitive.v_vector is None
    ):
        return [
            (float(primitive.start_point[0]), float(primitive.start_point[1])),
            (float(primitive.end_point[0]), float(primitive.end_point[1])),
        ]

    sweep = float(primitive.parameter_end) - float(primitive.parameter_start)
    if math.isclose(sweep, 0.0, abs_tol=1e-9):
        return [
            (float(primitive.start_point[0]), float(primitive.start_point[1])),
            (float(primitive.end_point[0]), float(primitive.end_point[1])),
        ]

    segment_count = max(8, int(math.ceil(abs(math.degrees(sweep)) / 12.0)))
    sampled_points: list[tuple[float, float]] = []
    for index in range(segment_count + 1):
        parameter = float(primitive.parameter_start) + (sweep * (index / segment_count))
        point = sp._sample_arc_point(
            primitive.center_point,
            primitive.u_vector,
            primitive.v_vector,
            float(primitive.radius),
            parameter,
        )
        sampled_points.append((float(point[0]), float(point[1])))
    return sampled_points


def _profile_points_2d(profile: sp.GeometryProfileSpec) -> list[tuple[float, float]]:
    if profile.geometry_type == "GeomTrimmedCurve":
        if not profile.primitives:
            return []
        return _deduplicate_points_2d(_primitive_points_2d(profile.primitives[0]))

    if profile.geometry_type != "GeomCompositeCurve":
        return []

    path_points: list[tuple[float, float]] = []
    for primitive in profile.primitives:
        primitive_points = _primitive_points_2d(primitive)
        if not primitive_points:
            continue
        if path_points and _points_close_2d(path_points[-1], primitive_points[0]):
            path_points.extend(primitive_points[1:])
        else:
            path_points.extend(primitive_points)

    deduplicated = _deduplicate_points_2d(path_points)
    if profile.is_closed and deduplicated and not _points_close_2d(deduplicated[0], deduplicated[-1]):
        deduplicated.append(deduplicated[0])
    return deduplicated


def _curve_sampled_points_2d(geometry: PgmxGeometrySnapshot) -> list[tuple[float, float]]:
    curve = geometry.curve
    if curve is None or not curve.sampled_points:
        return []
    return _deduplicate_points_2d(
        [(float(point[0]), float(point[1])) for point in curve.sampled_points]
    )


def _normalize_toolpath_type(value: Optional[str]) -> str:
    return str(value or "").strip().lower().replace(" ", "").replace("_", "")


def _toolpath_points_2d(operation: Optional[PgmxOperationSnapshot]) -> list[tuple[float, float]]:
    if operation is None:
        return []

    preferred_points: list[tuple[float, float]] = []
    fallback_points: list[tuple[float, float]] = []

    for toolpath in operation.toolpaths:
        curve = toolpath.curve
        if curve is None or not curve.sampled_points:
            continue
        points = _deduplicate_points_2d(
            [(float(point[0]), float(point[1])) for point in curve.sampled_points]
        )
        if len(points) < 2:
            continue
        if not toolpath.direction:
            points = list(reversed(points))

        toolpath_type = _normalize_toolpath_type(toolpath.path_type)
        if toolpath_type == "trajectorypath":
            preferred_points = points
            break
        if not fallback_points and toolpath_type not in {"approach", "lift"}:
            fallback_points = points
        elif not fallback_points:
            fallback_points = points

    return preferred_points or fallback_points


def _normalize_vector_2d(dx: float, dy: float) -> Optional[tuple[float, float]]:
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return None
    return (dx / length, dy / length)


def _entry_exit_arrows_from_points(
    points: Sequence[tuple[float, float]],
) -> tuple[Optional[MillingArrow], Optional[MillingArrow]]:
    normalized_points = _deduplicate_points_2d(points)
    if len(normalized_points) < 2:
        return None, None

    start_point = normalized_points[0]
    end_point = normalized_points[-1]

    entry_arrow: Optional[MillingArrow] = None
    for next_point in normalized_points[1:]:
        direction = _normalize_vector_2d(next_point[0] - start_point[0], next_point[1] - start_point[1])
        if direction is None:
            continue
        entry_arrow = MillingArrow(
            x=float(start_point[0]),
            y=float(start_point[1]),
            dx=float(direction[0]),
            dy=float(direction[1]),
        )
        break

    exit_arrow: Optional[MillingArrow] = None
    for previous_point in reversed(normalized_points[:-1]):
        direction = _normalize_vector_2d(end_point[0] - previous_point[0], end_point[1] - previous_point[1])
        if direction is None:
            continue
        exit_arrow = MillingArrow(
            x=float(end_point[0]),
            y=float(end_point[1]),
            dx=float(direction[0]),
            dy=float(direction[1]),
        )
        break

    return entry_arrow, exit_arrow


def _snapshot_feature_depth(feature: PgmxFeatureSnapshot) -> Optional[float]:
    depth_spec = feature.depth_spec
    if depth_spec is not None:
        if depth_spec.target_depth is not None:
            return float(depth_spec.target_depth)
        if depth_spec.extra_depth and depth_spec.extra_depth > 0:
            return float(depth_spec.extra_depth)

    depth_candidates = [feature.depth_start, feature.depth_end]
    positive_depths = [float(value) for value in depth_candidates if value is not None and value > 0]
    return positive_depths[0] if positive_depths else None


def _snapshot_face_dimensions(
    snapshot: PgmxSnapshot,
    fallback_width: float,
    fallback_height: float,
    fallback_thickness: Optional[float],
) -> dict[str, tuple[float, float]]:
    face_dimensions: dict[str, tuple[float, float]] = {}

    for plane in snapshot.planes:
        face_name = _normalize_face_name(plane.plane_type or plane.name)
        if plane.x_dimension > 0 and plane.y_dimension > 0:
            face_dimensions[face_name] = (float(plane.x_dimension), float(plane.y_dimension))

    state_length = float(snapshot.state.length or 0.0)
    state_width = float(snapshot.state.width or 0.0)
    state_depth = float(snapshot.state.depth or 0.0)

    if state_length > 0 and state_width > 0:
        face_dimensions.setdefault("Top", (state_length, state_width))
        face_dimensions.setdefault("Bottom", (state_length, state_width))
    if state_length > 0 and state_depth > 0:
        face_dimensions.setdefault("Front", (state_length, state_depth))
        face_dimensions.setdefault("Back", (state_length, state_depth))
    if state_width > 0 and state_depth > 0:
        face_dimensions.setdefault("Right", (state_width, state_depth))
        face_dimensions.setdefault("Left", (state_width, state_depth))

    thickness_value = float(fallback_thickness) if fallback_thickness is not None else 0.0
    if fallback_width > 0 and fallback_height > 0:
        face_dimensions.setdefault("Top", (float(fallback_width), float(fallback_height)))
        face_dimensions.setdefault("Bottom", (float(fallback_width), float(fallback_height)))
    if fallback_width > 0 and thickness_value > 0:
        face_dimensions.setdefault("Front", (float(fallback_width), thickness_value))
        face_dimensions.setdefault("Back", (float(fallback_width), thickness_value))
    if fallback_height > 0 and thickness_value > 0:
        face_dimensions.setdefault("Right", (float(fallback_height), thickness_value))
        face_dimensions.setdefault("Left", (float(fallback_height), thickness_value))

    return face_dimensions


def _operation_merge_key(operation: MachiningOperation) -> tuple[object, ...]:
    return (
        operation.op_type,
        round(float(operation.x), 4),
        round(float(operation.y), 4),
        round(float(operation.diameter), 4) if operation.diameter is not None else None,
        round(float(operation.width), 4) if operation.width is not None else None,
        round(float(operation.height), 4) if operation.height is not None else None,
        _normalize_face_name(operation.face),
    )


def _merge_operations(
    base_operations: Sequence[MachiningOperation],
    extra_operations: Sequence[MachiningOperation],
) -> list[MachiningOperation]:
    merged = list(base_operations)
    seen = {_operation_merge_key(operation) for operation in merged}
    for operation in extra_operations:
        key = _operation_merge_key(operation)
        if key in seen:
            continue
        seen.add(key)
        merged.append(operation)
    return merged


def _path_merge_key(path: MillingPath) -> tuple[object, ...]:
    normalized_points = tuple((round(float(x), 4), round(float(y), 4)) for x, y in path.points)
    return (_normalize_face_name(path.face), normalized_points)


def _merge_milling_paths(
    base_paths: Sequence[MillingPath],
    extra_paths: Sequence[MillingPath],
) -> list[MillingPath]:
    merged = list(base_paths)
    seen = {_path_merge_key(path) for path in merged}
    for path in extra_paths:
        key = _path_merge_key(path)
        if key in seen:
            continue
        seen.add(key)
        merged.append(path)
    return merged


def _build_piece_drawing_from_snapshot(
    snapshot: PgmxSnapshot,
    source_path: Path,
    piece: Piece,
) -> Optional[PieceDrawingData]:
    width = float(snapshot.state.length or 0.0)
    height = float(snapshot.state.width or 0.0)
    thickness = float(snapshot.state.depth) if snapshot.state.depth > 0 else piece.thickness

    if width <= 0:
        width = float(piece.width or 0.0)
    if height <= 0:
        height = float(piece.height or 0.0)
    if width <= 0 or height <= 0:
        return None

    operations: list[MachiningOperation] = []
    milling_paths: list[MillingPath] = []
    milling_circles: list[MillingCircle] = []

    for feature, operation, _step in _ordered_snapshot_features(snapshot):
        geometry: Optional[PgmxGeometrySnapshot] = None
        if feature.geometry_ref is not None and feature.geometry_ref.id:
            geometry = snapshot.geometry_by_id.get(feature.geometry_ref.id)

        face_name = _normalize_face_name(feature.plane_name)
        feature_type = feature.feature_type or ""
        operation_type = operation.operation_type if operation is not None else ""
        trajectory_points = _toolpath_points_2d(operation)

        if (
            geometry is not None
            and geometry.point is not None
            and (
                "RoundHole" in feature_type
                or "DrillingOperation" in operation_type
            )
        ):
            operations.append(
                MachiningOperation(
                    op_type="drill",
                    x=float(geometry.point[0]),
                    y=float(geometry.point[1]),
                    diameter=float(feature.diameter) if feature.diameter is not None else None,
                    face=face_name,
                    depth=_snapshot_feature_depth(feature),
                )
            )
            continue

        if geometry is None:
            continue

        profile = geometry.profile
        if profile is not None and (
            "GeneralProfileFeature" in feature_type
            or "BottomAndSideFinishMilling" in operation_type
        ):
            if (
                profile.geometry_type == "GeomCircle"
                and profile.center_point is not None
                and profile.radius is not None
            ):
                entry_arrow, exit_arrow = _entry_exit_arrows_from_points(trajectory_points)
                milling_circles.append(
                    MillingCircle(
                        face=face_name,
                        center_x=float(profile.center_point[0]),
                        center_y=float(profile.center_point[1]),
                        radius=float(profile.radius),
                        winding=profile.winding or "CounterClockwise",
                        entry_arrow=entry_arrow,
                        exit_arrow=exit_arrow,
                    )
                )
                continue

            points = _profile_points_2d(profile)
            if len(points) >= 2:
                direction_points = trajectory_points or points
                if not trajectory_points and feature.is_geom_same_direction is False:
                    direction_points = list(reversed(direction_points))
                entry_arrow, exit_arrow = _entry_exit_arrows_from_points(direction_points)
                milling_paths.append(
                    MillingPath(
                        face=face_name,
                        points=points,
                        entry_arrow=entry_arrow,
                        exit_arrow=exit_arrow,
                    )
                )
                continue

        sampled_points = _curve_sampled_points_2d(geometry)
        if len(sampled_points) >= 2:
            direction_points = trajectory_points or sampled_points
            if not trajectory_points and feature.is_geom_same_direction is False:
                direction_points = list(reversed(direction_points))
            entry_arrow, exit_arrow = _entry_exit_arrows_from_points(direction_points)
            milling_paths.append(
                MillingPath(
                    face=face_name,
                    points=sampled_points,
                    entry_arrow=entry_arrow,
                    exit_arrow=exit_arrow,
                )
            )

    face_dimensions = _snapshot_face_dimensions(snapshot, width, height, thickness)
    top_dimensions = face_dimensions.get("Top")
    if top_dimensions and top_dimensions[0] > 0 and top_dimensions[1] > 0:
        width, height = float(top_dimensions[0]), float(top_dimensions[1])

    return PieceDrawingData(
        width=width,
        height=height,
        thickness=thickness,
        source_path=source_path,
        operations=operations,
        milling_paths=milling_paths,
        milling_circles=milling_circles,
        face_dimensions=face_dimensions,
    )


def parse_pgmx_for_piece(project: Project, piece: Piece, module_path: Path) -> Optional[PieceDrawingData]:
    """Lee PGMX de una pieza y devuelve datos para dibujo."""

    source_path = _resolve_source_path(project, piece, module_path)
    if source_path is None:
        return None

    try:
        snapshot = read_pgmx_snapshot(source_path)
    except Exception:
        snapshot = None

    text: Optional[str] = None
    try:
        text = _read_pgmx_text(source_path)
    except OSError:
        text = None

    if snapshot is not None:
        snapshot_drawing = _build_piece_drawing_from_snapshot(snapshot, source_path, piece)
        if snapshot_drawing is not None:
            if text:
                legacy_operations, legacy_face_dims_ops = _extract_operations_from_xcam_xml(text)
                if not legacy_operations:
                    legacy_operations = [
                        MachiningOperation(
                            op_type=operation.op_type,
                            x=operation.x,
                            y=operation.y,
                            diameter=operation.diameter,
                            width=operation.width,
                            height=operation.height,
                            face="Top",
                        )
                        for operation in _extract_operations(text)
                    ]
                snapshot_drawing.operations = _merge_operations(snapshot_drawing.operations, legacy_operations)

                legacy_paths, legacy_face_dims_milling = _extract_milling_paths_from_xcam_xml(text)
                if legacy_paths:
                    snapshot_drawing.milling_paths = _merge_milling_paths(snapshot_drawing.milling_paths, legacy_paths)
                snapshot_drawing.face_dimensions.update(
                    {
                        face_name: dims
                        for face_name, dims in {**legacy_face_dims_ops, **legacy_face_dims_milling}.items()
                        if face_name not in snapshot_drawing.face_dimensions
                    }
                )
            return snapshot_drawing

    if text is None:
        return None

    width_txt, height_txt, thickness_txt = _extract_dimensions(text)

    width = width_txt if width_txt and width_txt > 0 else float(piece.width or 0)
    height = height_txt if height_txt and height_txt > 0 else float(piece.height or 0)
    thickness = thickness_txt if thickness_txt and thickness_txt > 0 else piece.thickness

    if width <= 0 or height <= 0:
        return None

    operations, face_dims_ops = _extract_operations_from_xcam_xml(text)
    milling_paths, face_dims_milling = _extract_milling_paths_from_xcam_xml(text)
    face_dimensions = dict(face_dims_ops)
    face_dimensions.update(face_dims_milling)

    if not operations:
        operations = _extract_operations(text)
        operations = [
            MachiningOperation(
                op_type=op.op_type,
                x=op.x,
                y=op.y,
                diameter=op.diameter,
                width=op.width,
                height=op.height,
                face="Top",
            )
            for op in operations
        ]

    if not face_dimensions:
        face_dimensions = {
            "Top": (width, height),
        }

    return PieceDrawingData(
        width=width,
        height=height,
        thickness=thickness,
        source_path=source_path,
        operations=operations,
        milling_paths=milling_paths,
        face_dimensions=face_dimensions,
    )


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", value.strip())
    return cleaned.strip("._") or "pieza"


def _format_dim(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")


def _to_canvas_x(x_mm: float, margin: float, scale: float) -> float:
    return margin + (x_mm * scale)


def _to_canvas_y(y_mm: float, margin: float, piece_height_mm: float, scale: float) -> float:
    # Invertir eje Y para visualizar origen en esquina inferior izquierda.
    return margin + ((piece_height_mm - y_mm) * scale)


def build_piece_svg(piece: Piece, drawing: PieceDrawingData, output_path: Path):
    """Genera SVG de la cara superior con proyección punteada de otras caras."""

    top_w, top_h = drawing.face_dimensions.get("Top", (drawing.width, drawing.height))
    if top_w <= 0 or top_h <= 0:
        top_w, top_h = drawing.width, drawing.height
    if top_w <= 0 or top_h <= 0:
        top_w, top_h = 100.0, 100.0

    margin = 30.0
    header_h = 10.0
    footer_h = 10.0
    
    # Escala fija: ancho máximo de pieza = 200px, altura se calcula proporcionalmente
    # Esto garantiza consistencia visual: todas las piezas caben en 200px de ancho máximo
    # manteniendo perfectamente la relación de aspecto
    max_piece_width_px = 200.0
    scale = max_piece_width_px / top_w if top_w > 0 else 1.0

    piece_w_px = top_w * scale
    piece_h_px = top_h * scale
    canvas_w = piece_w_px + margin * 2
    canvas_h = piece_h_px + margin * 2 + header_h + footer_h

    piece_x = margin
    piece_y = margin + header_h

    def to_canvas_x(x_mm: float) -> float:
        return piece_x + (x_mm * scale)

    def to_canvas_y(y_mm: float) -> float:
        return piece_y + ((top_h - y_mm) * scale)

    def clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def is_closed_milling_path(points: List[tuple[float, float]], tolerance_mm: float = 0.5) -> bool:
        if len(points) < 2:
            return False
        x0, y0 = points[0]
        x1, y1 = points[-1]
        return abs(x0 - x1) <= tolerance_mm and abs(y0 - y1) <= tolerance_mm

    def append_chevron(marker: Optional[MillingArrow], color: str, offset_px: float = 0.0) -> None:
        if marker is None:
            return
        canvas_direction = _normalize_vector_2d(float(marker.dx), -float(marker.dy))
        if canvas_direction is None:
            return

        unit_x, unit_y = canvas_direction
        perp_x = -unit_y
        perp_y = unit_x
        anchor_x = to_canvas_x(clamp(float(marker.x), 0.0, top_w))
        anchor_y = to_canvas_y(clamp(float(marker.y), 0.0, top_h))
        if not math.isclose(offset_px, 0.0, abs_tol=1e-9):
            anchor_x += perp_x * offset_px
            anchor_y += perp_y * offset_px

        chevron_length = 4.0
        chevron_half_width = 2.25
        back_x = anchor_x - (unit_x * chevron_length)
        back_y = anchor_y - (unit_y * chevron_length)
        left_x = back_x + (perp_x * chevron_half_width)
        left_y = back_y + (perp_y * chevron_half_width)
        right_x = back_x - (perp_x * chevron_half_width)
        right_y = back_y - (perp_y * chevron_half_width)

        lines.append(
            f'<line x1="{left_x:.2f}" y1="{left_y:.2f}" x2="{anchor_x:.2f}" y2="{anchor_y:.2f}" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
        )
        lines.append(
            f'<line x1="{right_x:.2f}" y1="{right_y:.2f}" x2="{anchor_x:.2f}" y2="{anchor_y:.2f}" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
        )

    def append_entry_marker(entry_marker: Optional[MillingArrow], color: str) -> None:
        append_chevron(entry_marker, color)

    def append_grain_hatching(hatch_axis: Optional[str]) -> None:
        hatch_color = "#d8d2c7"
        hatch_spacing = 10.0
        hatch_margin = 0.0
        hatch_stroke_width = 0.7

        if hatch_axis == "vertical":
            current_x = piece_x + hatch_margin
            hatch_end_y = piece_y + piece_h_px - hatch_margin
            hatch_start_y = piece_y + hatch_margin
            while current_x <= (piece_x + piece_w_px - hatch_margin):
                lines.append(
                    f'<line x1="{current_x:.2f}" y1="{hatch_start_y:.2f}" x2="{current_x:.2f}" y2="{hatch_end_y:.2f}" stroke="{hatch_color}" stroke-width="{hatch_stroke_width}" clip-path="url(#piece-clip)"/>'
                )
                current_x += hatch_spacing
            return

        if hatch_axis == "horizontal":
            current_y = piece_y + hatch_margin
            hatch_start_x = piece_x + hatch_margin
            hatch_end_x = piece_x + piece_w_px - hatch_margin
            while current_y <= (piece_y + piece_h_px - hatch_margin):
                lines.append(
                    f'<line x1="{hatch_start_x:.2f}" y1="{current_y:.2f}" x2="{hatch_end_x:.2f}" y2="{current_y:.2f}" stroke="{hatch_color}" stroke-width="{hatch_stroke_width}" clip-path="url(#piece-clip)"/>'
                )
                current_y += hatch_spacing

    def side_projection_for_operation(op: MachiningOperation):
        face = (op.face or "").strip().lower()
        diameter = op.diameter if op.diameter and op.diameter > 0 else 5.0
        proj_len_mm = op.depth if op.depth and op.depth > 0 else max(8.0, diameter * 2.2)

        if face == "left":
            y_mm = clamp(op.x, 0.0, top_h)
            return (0.0, y_mm, clamp(proj_len_mm, 0.0, top_w), y_mm)
        if face == "right":
            y_mm = clamp(op.x, 0.0, top_h)
            return (top_w, y_mm, clamp(top_w - proj_len_mm, 0.0, top_w), y_mm)
        if face == "front":
            x_mm = clamp(op.x, 0.0, top_w)
            return (x_mm, top_h, x_mm, clamp(top_h - proj_len_mm, 0.0, top_h))
        if face == "back":
            x_mm = clamp(op.x, 0.0, top_w)
            return (x_mm, 0.0, x_mm, clamp(proj_len_mm, 0.0, top_h))
        return None

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.2f}" height="{canvas_h:.2f}" viewBox="0 0 {canvas_w:.2f} {canvas_h:.2f}">',
        f'<rect x="{piece_x:.2f}" y="{piece_y:.2f}" width="{piece_w_px:.2f}" height="{piece_h_px:.2f}" fill="#ffffff" stroke="#2f4f4f" stroke-width="1"/>',
        f'<defs><clipPath id="piece-clip"><rect x="{piece_x:.2f}" y="{piece_y:.2f}" width="{piece_w_px:.2f}" height="{piece_h_px:.2f}"/></clipPath></defs>',
    ]

    append_grain_hatching(
        resolve_piece_grain_hatch_axis(
            piece.grain_direction,
            piece.width,
            piece.height,
            top_w,
            top_h,
        )
    )

    # Fresados visibles de la cara superior (clip-path recorta lo que sale del borde).
    for path in drawing.milling_paths:
        if (path.face or "Top").strip().lower() != "top":
            continue
        is_open_path = not is_closed_milling_path(path.points)
        stroke_color = "#c0392b" if is_open_path else "#0b7a75"
        stroke_width = "1.4" if is_open_path else "0.8"
        svg_points = []
        for x_mm, y_mm in path.points:
            px = to_canvas_x(x_mm)
            py = to_canvas_y(y_mm)
            svg_points.append(f"{px:.2f},{py:.2f}")
        if len(svg_points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(svg_points)}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" clip-path="url(#piece-clip)"/>'
            )
            append_entry_marker(path.entry_arrow, stroke_color)

    for circle in drawing.milling_circles:
        face = (circle.face or "Top").strip().lower()
        circle_x = to_canvas_x(clamp(circle.center_x, 0.0, top_w))
        circle_y = to_canvas_y(clamp(circle.center_y, 0.0, top_h))
        circle_radius = max(1.0, float(circle.radius) * scale)
        if face == "top":
            lines.append(
                f'<circle cx="{circle_x:.2f}" cy="{circle_y:.2f}" r="{circle_radius:.2f}" fill="none" stroke="#0b7a75" stroke-width="1.0" clip-path="url(#piece-clip)"/>'
            )
            append_entry_marker(circle.entry_arrow, "#0b7a75")
        elif face == "bottom":
            lines.append(
                f'<circle cx="{circle_x:.2f}" cy="{circle_y:.2f}" r="{circle_radius:.2f}" fill="none" stroke="#1f78b4" stroke-width="1.1" stroke-dasharray="4,3" clip-path="url(#piece-clip)"/>'
            )

    top_ops = 0
    projected_ops = 0

    for operation in drawing.operations:
        face = (operation.face or "Top").strip().lower()

        if face == "top":
            op_x = to_canvas_x(clamp(operation.x, 0.0, top_w))
            op_y = to_canvas_y(clamp(operation.y, 0.0, top_h))
            if operation.op_type == "drill":
                diameter = operation.diameter if operation.diameter and operation.diameter > 0 else 5.0
                radius = (diameter * scale) / 2.0
                lines.append(
                    f'<circle cx="{op_x:.2f}" cy="{op_y:.2f}" r="{radius:.2f}" fill="#c0392b" stroke="none"/>'
                )
            elif operation.op_type == "slot":
                slot_w = operation.width if operation.width and operation.width > 0 else 5.0
                slot_h = operation.height if operation.height and operation.height > 0 else 5.0
                slot_w_px = max(2.0, slot_w * scale)
                slot_h_px = max(2.0, slot_h * scale)
                lines.append(
                    f'<rect x="{op_x:.2f}" y="{op_y - slot_h_px:.2f}" width="{slot_w_px:.2f}" height="{slot_h_px:.2f}" fill="none" stroke="#1f78b4" stroke-width="0.7"/>'
                )
            top_ops += 1
            continue

        if face == "bottom":
            op_x = to_canvas_x(clamp(operation.x, 0.0, top_w))
            op_y = to_canvas_y(clamp(operation.y, 0.0, top_h))
            diameter = operation.diameter if operation.diameter and operation.diameter > 0 else 5.0
            radius = (diameter * scale) / 2.0
            lines.append(
                f'<circle cx="{op_x:.2f}" cy="{op_y:.2f}" r="{radius:.2f}" fill="none" stroke="#1f78b4" stroke-width="1.2" stroke-dasharray="4,3"/>'
            )
            projected_ops += 1
            continue

        side_line = side_projection_for_operation(operation)
        if side_line is None:
            continue

        x1_mm, y1_mm, x2_mm, y2_mm = side_line
        x1 = to_canvas_x(clamp(x1_mm, 0.0, top_w))
        y1 = to_canvas_y(clamp(y1_mm, 0.0, top_h))
        x2 = to_canvas_x(clamp(x2_mm, 0.0, top_w))
        y2 = to_canvas_y(clamp(y2_mm, 0.0, top_h))
        lines.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#1f78b4" stroke-width="1.4" stroke-dasharray="4,3"/>'
        )
        projected_ops += 1

    lines.append("</svg>")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_project_piece_drawings(project: Project) -> tuple[int, int, int]:
    """Genera dibujos SVG por pieza a partir de archivos PGMX.

    Retorna: (dibujos_generados, piezas_sin_pgmx_utilizable, piezas_con_mecanizados)
    """

    generated = 0
    skipped = 0
    with_machining = 0

    for module in project.modules:
        module_path = Path(module.path)

        for piece in module.pieces:
            drawing_data = parse_pgmx_for_piece(project, piece, module_path)
            if drawing_data is None:
                skipped += 1
                continue

            if drawing_data.operations or drawing_data.milling_paths or drawing_data.milling_circles:
                with_machining += 1

            piece_slug = _sanitize_filename(piece.name or piece.id)
            output_path = module_path / f"{piece_slug}.svg"
            build_piece_svg(piece, drawing_data, output_path)
            generated += 1

    return generated, skipped, with_machining
