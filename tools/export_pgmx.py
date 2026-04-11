"""Exporta un En-Juego como un PGMX compuesto.

Herramienta experimental y aislada: no modifica el flujo principal de la app.
Genera un `.pgmx` a partir de las piezas marcadas como En Juego dentro de un
módulo, aplicando la disposición guardada en `en_juego_layout` sobre una
plantilla `.pgmx` real para conservar la estructura que espera Maestro/XCam.

Modo estable actual validado en Maestro:
- preserva `Xn` dentro del `MainWorkplan`
- conserva `ToolpathList` de taladro en modo raw
- genera toolpaths sintéticos compatibles para `ESCUADRADO_EN_JUEGO` y
    `DIVISION_EN_JUEGO`
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QPointF
from PySide6.QtGui import QTransform

from core.model import Piece, Project
from core.pgmx_processing import PieceDrawingData, parse_pgmx_for_piece


PGMX_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.ProjectModule"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
BASE_MODEL_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"
MILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Milling"
DRILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Drilling"
GEOMETRY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Geometry"
STRATEGY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Strategy"
UTILITY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Utility"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
ARRAYS_NS = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
MACHINING_SETUP_Z_ORIGIN = 9.0

ET.register_namespace("", PGMX_NS)
ET.register_namespace("i", XSI_NS)


def _safe_float(value, default: Optional[float] = None) -> Optional[float]:
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _compact_number(value: float) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.6f}".rstrip("0").rstrip(".")


def _sanitize_filename(value: str) -> str:
    sanitized = "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
    sanitized = sanitized.strip("._")
    return sanitized or "en_juego_compuesto"


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _xsi_type(element: ET.Element) -> str:
    for key, value in element.attrib.items():
        if _strip_namespace(key).lower() == "type":
            return value or ""
    return ""


def _find_collection(root: ET.Element, collection_name: str) -> ET.Element:
    element = root.find(f"./{{*}}{collection_name}")
    if element is None:
        raise ValueError(f"No se encontró la colección '{collection_name}' en el PGMX plantilla.")
    return element


def _get_key_id(element: ET.Element) -> str:
    return str(element.findtext("./{*}Key/{*}ID") or "").strip()


def _set_text(element: Optional[ET.Element], value) -> None:
    if element is not None:
        element.text = "" if value is None else str(value)


def _set_ref_id(parent: ET.Element, path: str, ref_id: str, object_type: Optional[str] = None) -> None:
    ref = parent.find(path)
    if ref is None:
        return
    id_node = ref.find("./{*}ID")
    object_type_node = ref.find("./{*}ObjectType")
    _set_text(id_node, ref_id)
    if object_type is not None:
        _set_text(object_type_node, object_type)


def _set_xmlns(element: Optional[ET.Element], prefix: str, uri: str) -> None:
    if element is not None:
        element.set(f"xmlns:{prefix}", uri)


def _set_default_xmlns(element: Optional[ET.Element], uri: str) -> None:
    if element is not None:
        element.set("xmlns", uri)


def _domain_namespace_from_object_type(object_type: str) -> Optional[str]:
    raw = str(object_type or "")
    if ".Milling." in raw:
        return MILLING_NS
    if ".Drilling." in raw:
        return DRILLING_NS
    return None


def _load_project(project_json_path: Path) -> Project:
    data = json.loads(project_json_path.read_text(encoding="utf-8"))
    return Project(
        name=str(data.get("name") or project_json_path.stem),
        root_directory=str(data.get("root_directory") or ""),
        client=str(data.get("client") or ""),
        local=str(data.get("local") or ""),
        created_at=str(data.get("created_at") or ""),
        modules=[],
    )


def _build_piece_from_row(module_name: str, row: dict) -> Piece:
    return Piece(
        id=str(row.get("id") or row.get("name") or "pieza").strip(),
        name=str(row.get("name") or row.get("id") or "pieza").strip(),
        quantity=int(_safe_float(row.get("quantity"), 1) or 1),
        width=float(_safe_float(row.get("width"), 0.0) or 0.0),
        height=float(_safe_float(row.get("height"), 0.0) or 0.0),
        thickness=_safe_float(row.get("thickness")),
        color=row.get("color"),
        grain_direction=row.get("grain_direction"),
        module_name=module_name,
        cnc_source=str(row.get("source") or "").strip() or None,
        f6_source=str(row.get("f6_source") or "").strip() or None,
        piece_type=row.get("piece_type"),
        program_width=_safe_float(row.get("program_width")),
        program_height=_safe_float(row.get("program_height")),
        program_thickness=_safe_float(row.get("program_thickness")),
    )


def _preview_dimensions_mm(piece_row: dict, drawing: PieceDrawingData) -> tuple[float, float]:
    top_dimensions = drawing.face_dimensions.get("Top")
    if top_dimensions and top_dimensions[0] > 0 and top_dimensions[1] > 0:
        return float(top_dimensions[0]), float(top_dimensions[1])

    program_width = _safe_float(piece_row.get("program_width"), 0.0) or 0.0
    program_height = _safe_float(piece_row.get("program_height"), 0.0) or 0.0
    if program_width > 0 and program_height > 0:
        return program_width, program_height

    return (
        float(_safe_float(piece_row.get("width"), 0.0) or 0.0),
        float(_safe_float(piece_row.get("height"), 0.0) or 0.0),
    )


def _build_scene_transform(pos_x: float, pos_y: float, width_mm: float, height_mm: float, rotation_deg: float) -> QTransform:
    transform = QTransform()
    transform.translate(pos_x, pos_y)
    transform.translate(width_mm / 2.0, height_mm / 2.0)
    transform.rotate(rotation_deg)
    transform.translate(-width_mm / 2.0, -height_mm / 2.0)
    return transform


@dataclass
class PieceInstance:
    piece: Piece
    piece_row: dict
    drawing: PieceDrawingData
    instance_key: str
    title_text: str
    pos_x: float
    pos_y: float
    rotation: float
    top_width: float
    top_height: float
    transform: QTransform
    bounds: tuple[float, float, float, float]


@dataclass
class SourceContext:
    source_path: Path
    root: ET.Element
    archive_entries: dict[str, bytes]
    xml_entry_name: str
    features: ET.Element
    geometries: ET.Element
    operations: ET.Element
    planes: ET.Element
    workplans: ET.Element
    workplan_elements: ET.Element
    workpiece_id: str
    workpiece_object_type: str
    geometry_by_id: dict[str, ET.Element]
    operation_by_id: dict[str, ET.Element]
    plane_by_id: dict[str, ET.Element]
    plane_face_by_id: dict[str, str]
    workingsteps_by_feature_id: dict[str, list[ET.Element]]


@dataclass
class CompositeReport:
    module_name: str
    output_path: Path
    width: float
    height: float
    thickness: float
    source_instances: list[str] = field(default_factory=list)
    drill_count: int = 0
    milling_path_count: int = 0
    skipped_operations: list[str] = field(default_factory=list)
    skipped_paths: list[str] = field(default_factory=list)


@dataclass
class ProfileTemplate:
    feature: ET.Element
    geometry: ET.Element
    operations: list[ET.Element]
    workingsteps: list[ET.Element]
    face_name: str


def _load_piece_instances(project: Project, module_path: Path, config_data: dict) -> list[PieceInstance]:
    module_name = str(config_data.get("module") or module_path.name)
    saved_layout = config_data.get("en_juego_layout", {})
    if not isinstance(saved_layout, dict):
        saved_layout = {}

    instances: list[PieceInstance] = []
    for row in config_data.get("pieces", []):
        if not bool(row.get("en_juego", False)):
            continue

        piece = _build_piece_from_row(module_name, row)
        if not piece.cnc_source:
            raise ValueError(f"La pieza '{piece.name}' no tiene programa asociado.")

        drawing = parse_pgmx_for_piece(project, piece, module_path)
        if drawing is None:
            raise ValueError(f"No se pudo leer el PGMX de '{piece.name}'.")

        top_width, top_height = _preview_dimensions_mm(row, drawing)
        if top_width <= 0 or top_height <= 0:
            raise ValueError(f"Dimensiones inválidas para '{piece.name}'.")

        quantity = max(1, int(_safe_float(row.get("quantity"), 1) or 1))
        for copy_index in range(1, quantity + 1):
            piece_id = str(row.get("id") or row.get("name") or piece.name).strip()
            instance_key = f"{piece_id}#{copy_index}"
            layout_data = saved_layout.get(instance_key)
            if copy_index == 1 and not isinstance(layout_data, dict):
                layout_data = saved_layout.get(piece_id)

            if not isinstance(layout_data, dict):
                raise ValueError(f"Falta layout para '{piece.name} #{copy_index}' en en_juego_layout.")

            pos_x = float(_safe_float(layout_data.get("x"), 0.0) or 0.0)
            pos_y = float(_safe_float(layout_data.get("y"), 0.0) or 0.0)
            rotation = float(_safe_float(layout_data.get("rotation"), 0.0) or 0.0)
            transform = _build_scene_transform(pos_x, pos_y, top_width, top_height, rotation)

            corners = [
                transform.map(QPointF(0.0, 0.0)),
                transform.map(QPointF(top_width, 0.0)),
                transform.map(QPointF(top_width, top_height)),
                transform.map(QPointF(0.0, top_height)),
            ]
            xs = [point.x() for point in corners]
            ys = [point.y() for point in corners]
            instances.append(
                PieceInstance(
                    piece=piece,
                    piece_row=row,
                    drawing=drawing,
                    instance_key=instance_key,
                    title_text=f"{piece.name} #{copy_index}",
                    pos_x=pos_x,
                    pos_y=pos_y,
                    rotation=rotation,
                    top_width=top_width,
                    top_height=top_height,
                    transform=transform,
                    bounds=(min(xs), min(ys), max(xs), max(ys)),
                )
            )

    if not instances:
        raise ValueError("El módulo no tiene piezas marcadas como En Juego con layout exportable.")

    return instances


def _load_cut_saw_kerf_mm(default: float = 4.0) -> float:
    settings_path = Path(__file__).resolve().parents[1] / "app_settings.json"
    try:
        settings_data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default
    return float(_safe_float(settings_data.get("cut_saw_kerf"), default) or default)


def _refresh_instance_transform_and_bounds(instance: PieceInstance) -> None:
    instance.transform = _build_scene_transform(
        instance.pos_x,
        instance.pos_y,
        instance.top_width,
        instance.top_height,
        instance.rotation,
    )
    corners = [
        instance.transform.map(QPointF(0.0, 0.0)),
        instance.transform.map(QPointF(instance.top_width, 0.0)),
        instance.transform.map(QPointF(instance.top_width, instance.top_height)),
        instance.transform.map(QPointF(0.0, instance.top_height)),
    ]
    xs = [point.x() for point in corners]
    ys = [point.y() for point in corners]
    instance.bounds = (min(xs), min(ys), max(xs), max(ys))


def _shift_instance(instance: PieceInstance, delta_x: float = 0.0, delta_y: float = 0.0) -> None:
    instance.pos_x += delta_x
    instance.pos_y += delta_y
    _refresh_instance_transform_and_bounds(instance)


def _overlap_amount(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    return max(0.0, min(end_a, end_b) - max(start_a, start_b))


def _enforce_min_instance_spacing(instances: list[PieceInstance], minimum_gap_mm: float) -> None:
    if minimum_gap_mm <= 0 or len(instances) < 2:
        return

    tolerance = 0.05
    overlap_tolerance = 1.0
    changed = True
    while changed:
        changed = False

        ordered_by_x = sorted(instances, key=lambda item: item.bounds[0])
        for left in ordered_by_x:
            for right in ordered_by_x:
                if left is right or left.bounds[0] > right.bounds[0]:
                    continue
                vertical_overlap = _overlap_amount(left.bounds[1], left.bounds[3], right.bounds[1], right.bounds[3])
                if vertical_overlap <= overlap_tolerance:
                    continue
                gap_x = right.bounds[0] - left.bounds[2]
                if gap_x >= minimum_gap_mm - tolerance:
                    continue
                delta_x = minimum_gap_mm - gap_x
                pivot_x = right.bounds[0] - tolerance
                for instance in instances:
                    if instance.bounds[0] >= pivot_x:
                        _shift_instance(instance, delta_x=delta_x)
                changed = True
                break
            if changed:
                break

        if changed:
            continue

        ordered_by_y = sorted(instances, key=lambda item: item.bounds[1])
        for top in ordered_by_y:
            for bottom in ordered_by_y:
                if top is bottom or top.bounds[1] > bottom.bounds[1]:
                    continue
                horizontal_overlap = _overlap_amount(top.bounds[0], top.bounds[2], bottom.bounds[0], bottom.bounds[2])
                if horizontal_overlap <= overlap_tolerance:
                    continue
                gap_y = bottom.bounds[1] - top.bounds[3]
                if gap_y >= minimum_gap_mm - tolerance:
                    continue
                delta_y = minimum_gap_mm - gap_y
                pivot_y = bottom.bounds[1] - tolerance
                for instance in instances:
                    if instance.bounds[1] >= pivot_y:
                        _shift_instance(instance, delta_y=delta_y)
                changed = True
                break
            if changed:
                break


def _composite_dimensions(instances: list[PieceInstance]) -> tuple[float, float, float, float, float]:
    min_x = min(instance.bounds[0] for instance in instances)
    min_y = min(instance.bounds[1] for instance in instances)
    max_x = max(instance.bounds[2] for instance in instances)
    max_y = max(instance.bounds[3] for instance in instances)
    thickness_values = [float(instance.piece.thickness) for instance in instances if instance.piece.thickness is not None]
    thickness = max(thickness_values, default=0.0)
    return min_x, min_y, round(max_x - min_x, 4), round(max_y - min_y, 4), round(thickness, 4)


def _load_pgmx_archive(source_path: Path) -> tuple[ET.Element, dict[str, bytes], str]:
    archive_entries: dict[str, bytes] = {}
    with zipfile.ZipFile(source_path) as zip_file:
        for name in zip_file.namelist():
            archive_entries[name] = zip_file.read(name)

    xml_entry_name = next((name for name in archive_entries if name.lower().endswith(".xml")), "")
    if not xml_entry_name:
        raise ValueError(f"El archivo '{source_path}' no contiene XML interno.")

    xml_root = ET.fromstring(archive_entries[xml_entry_name].decode("utf-8", errors="ignore"))
    return xml_root, archive_entries, xml_entry_name


def _build_source_context(source_path: Path) -> SourceContext:
    root, archive_entries, xml_entry_name = _load_pgmx_archive(source_path)
    features = _find_collection(root, "Features")
    geometries = _find_collection(root, "Geometries")
    operations = _find_collection(root, "Operations")
    planes = _find_collection(root, "Planes")
    workplans = _find_collection(root, "Workplans")
    main_workplan = workplans.find("./{*}MainWorkplan")
    if main_workplan is None:
        raise ValueError(f"El archivo '{source_path.name}' no contiene MainWorkplan.")
    workplan_elements = main_workplan.find("./{*}Elements")
    if workplan_elements is None:
        raise ValueError(f"El archivo '{source_path.name}' no contiene Elements en MainWorkplan.")

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError(f"El archivo '{source_path.name}' no contiene WorkPiece.")

    geometry_by_id = {_get_key_id(element): element for element in list(geometries)}
    operation_by_id = {_get_key_id(element): element for element in list(operations)}
    plane_by_id = {_get_key_id(element): element for element in list(planes)}
    plane_face_by_id = {
        plane_id: str(element.findtext("./{*}Type") or "Top").strip() or "Top"
        for plane_id, element in plane_by_id.items()
    }

    workingsteps_by_feature_id: dict[str, list[ET.Element]] = {}
    for executable in list(workplan_elements):
        if "MachiningWorkingStep" not in _xsi_type(executable):
            continue
        feature_id = str(executable.findtext("./{*}ManufacturingFeatureID/{*}ID") or "").strip()
        if not feature_id:
            continue
        workingsteps_by_feature_id.setdefault(feature_id, []).append(executable)

    return SourceContext(
        source_path=source_path,
        root=root,
        archive_entries=archive_entries,
        xml_entry_name=xml_entry_name,
        features=features,
        geometries=geometries,
        operations=operations,
        planes=planes,
        workplans=workplans,
        workplan_elements=workplan_elements,
        workpiece_id=_get_key_id(workpiece),
        workpiece_object_type=str(workpiece.findtext("./{*}Key/{*}ObjectType") or "").strip(),
        geometry_by_id=geometry_by_id,
        operation_by_id=operation_by_id,
        plane_by_id=plane_by_id,
        plane_face_by_id=plane_face_by_id,
        workingsteps_by_feature_id=workingsteps_by_feature_id,
    )


def _id_counter(root: ET.Element):
    max_value = 0
    for element in root.iter():
        tag = _strip_namespace(element.tag)
        text = str(element.text or "").strip()
        if tag not in {"ID", "unsignedInt"} or not text.isdigit():
            continue
        max_value = max(max_value, int(text))

    current = max_value + 1
    while True:
        yield str(current)
        current += 1


def _instance_suffix(instance_key: str) -> str:
    return instance_key.replace("#", "_")


def _rename_text_field(element: ET.Element, path: str, suffix: str) -> None:
    node = element.find(path)
    if node is None:
        return
    original = str(node.text or "").strip()
    if original:
        node.text = f"{original}_{suffix}"


def _map_local_point_to_composite(instance: PieceInstance, min_x: float, min_y: float, composite_height: float, x_value: float, y_value: float) -> tuple[float, float]:
    scene_point = instance.transform.map(QPointF(x_value, instance.top_height - y_value))
    return (
        round(scene_point.x() - min_x, 6),
        round(composite_height - (scene_point.y() - min_y), 6),
    )


def _map_local_vector_to_composite(instance: PieceInstance, min_x: float, min_y: float, composite_height: float, x_value: float, y_value: float) -> tuple[float, float]:
    origin_x, origin_y = _map_local_point_to_composite(instance, min_x, min_y, composite_height, 0.0, 0.0)
    mapped_x, mapped_y = _map_local_point_to_composite(instance, min_x, min_y, composite_height, x_value, y_value)
    return round(mapped_x - origin_x, 6), round(mapped_y - origin_y, 6)


def _curve_points_from_geometry(geometry_element: ET.Element) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    last_dx = 0.0
    last_dy = 0.0
    last_length = 0.0

    for member_el in geometry_element.findall(".//{*}_serializingMembers/{*}string"):
        raw = str(member_el.text or "").strip()
        if not raw:
            continue

        seg_x: Optional[float] = None
        seg_y: Optional[float] = None
        seg_dx = 0.0
        seg_dy = 0.0
        seg_length = 0.0

        for seg_line in raw.splitlines():
            line = seg_line.strip()
            match_8 = re.match(
                r"^8\s+(-?[0-9]+(?:[\.,][0-9]+)?)\s+(-?[0-9]+(?:[\.,][0-9]+)?)",
                line,
            )
            if match_8:
                seg_length = float(_safe_float(match_8.group(2), 0.0) or 0.0)
                continue

            match_1 = re.match(
                r"^1\s+(-?[0-9]+(?:[\.,][0-9]+)?)\s+(-?[0-9]+(?:[\.,][0-9]+)?)"
                r"\s+(-?[0-9]+(?:[\.,][0-9]+)?)"
                r"\s+(-?[0-9]+(?:[\.,][0-9]+)?)\s+(-?[0-9]+(?:[\.,][0-9]+)?)",
                line,
            )
            if match_1:
                seg_x = _safe_float(match_1.group(1))
                seg_y = _safe_float(match_1.group(2))
                seg_dx = float(_safe_float(match_1.group(4), 0.0) or 0.0)
                seg_dy = float(_safe_float(match_1.group(5), 0.0) or 0.0)

        if seg_x is None or seg_y is None:
            continue

        point = (round(float(seg_x), 6), round(float(seg_y), 6))
        if not points or point != points[-1]:
            points.append(point)
        last_dx = seg_dx
        last_dy = seg_dy
        last_length = seg_length

    if points:
        implied_end = (
            round(points[-1][0] + (last_dx * last_length), 6),
            round(points[-1][1] + (last_dy * last_length), 6),
        )
        if implied_end != points[-1]:
            points.append(implied_end)

    return points


def _polyline_segment_strings(points: list[tuple[float, float]], closed: bool) -> list[str]:
    if len(points) < 2:
        raise ValueError("Se requieren al menos dos puntos para serializar una curva.")

    strings: list[str] = []
    limit = len(points) if closed else len(points) - 1
    for index in range(limit):
        start_x, start_y = points[index]
        end_x, end_y = points[(index + 1) % len(points)] if closed else points[index + 1]
        dx = end_x - start_x
        dy = end_y - start_y
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length <= 1e-6:
            continue
        dir_x = dx / length
        dir_y = dy / length
        strings.append(
            "\n".join(
                [
                    f"8 0 {_compact_number(length)}",
                    " ".join(
                        [
                            "1",
                            _compact_number(start_x),
                            _compact_number(start_y),
                            "0",
                            _compact_number(dir_x),
                            _compact_number(dir_y),
                            "0",
                        ]
                    ),
                ]
            )
        )

    return strings


def _replace_serialized_curve_members(curve_element: ET.Element, curve_strings: list[str], key_counter) -> None:
    keys_group = next((element for element in curve_element.iter() if _strip_namespace(element.tag) == "_serializingKeys"), None)
    members_group = next((element for element in curve_element.iter() if _strip_namespace(element.tag) == "_serializingMembers"), None)
    if keys_group is None or members_group is None:
        raise ValueError("La geometría perfilada no contiene _serializingKeys/_serializingMembers.")

    key_children = list(keys_group)
    member_children = list(members_group)
    key_tag = key_children[0].tag if key_children else f"{{{ARRAYS_NS}}}unsignedInt"
    member_tag = member_children[0].tag if member_children else f"{{{ARRAYS_NS}}}string"

    keys_group.clear()
    members_group.clear()
    for curve_text in curve_strings:
        key_node = ET.Element(key_tag)
        key_node.text = next(key_counter)
        keys_group.append(key_node)

        member_node = ET.Element(member_tag)
        member_node.text = curve_text
        members_group.append(member_node)


def _prepare_operation_clone_namespaces(operation_clone: ET.Element) -> None:
    for head in operation_clone.findall(".//{*}Head"):
        _set_xmlns(head, "b", BASE_MODEL_NS)
    for machine_functions in operation_clone.findall(".//{*}MachineFunctions"):
        _set_xmlns(machine_functions, "b", BASE_MODEL_NS)
    for toolpath_list in operation_clone.findall(".//{*}ToolpathList"):
        _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)
    for start_point in operation_clone.findall(".//{*}StartPoint"):
        _set_xmlns(start_point, "b", GEOMETRY_NS)
        _set_xmlns(start_point.find("./{*}PlaneID"), "c", UTILITY_NS)
    for tool_key in operation_clone.findall(".//{*}ToolKey"):
        _set_xmlns(tool_key, "b", UTILITY_NS)
    for approach in operation_clone.findall(".//{*}Approach"):
        if "BaseApproachStrategy" in _xsi_type(approach):
            _set_xmlns(approach, "b", STRATEGY_NS)
    for retract in operation_clone.findall(".//{*}Retract"):
        if "BaseRetractStrategy" in _xsi_type(retract):
            _set_xmlns(retract, "b", STRATEGY_NS)
    for basic_curve in operation_clone.findall(".//{*}BasicCurve"):
        if "Geom" in _xsi_type(basic_curve):
            _set_xmlns(basic_curve, "c", GEOMETRY_NS)


def _is_squaring_profile(
    feature: ET.Element,
    geometry: ET.Element,
    operations: list[ET.Element],
    width_mm: float,
    height_mm: float,
    tolerance: float = 1.0,
) -> bool:
    if "GeneralProfileFeature" not in _xsi_type(feature):
        return False
    if "GeomCompositeCurve" not in _xsi_type(geometry):
        return False
    if not any("BottomAndSideFinishMilling" in _xsi_type(operation) for operation in operations):
        return False

    points = _curve_points_from_geometry(geometry)
    if len(points) < 4:
        return False

    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)

    return (
        abs(min_x) <= tolerance
        and abs(min_y) <= tolerance
        and abs((max_x - min_x) - width_mm) <= tolerance
        and abs((max_y - min_y) - height_mm) <= tolerance
    )


def _profile_tool_radius(profile_feature: ET.Element) -> float:
    width = float(_safe_float(profile_feature.findtext("./{*}SweptShape/{*}Width"), 0.0) or 0.0)
    return round(width / 2.0, 6) if width > 0 else 0.0


def _toolpath_line_string(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    dz = end_point[2] - start_point[2]
    length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if length <= 1e-6:
        raise ValueError("No se puede crear un segmento de toolpath con longitud cero.")

    return "\n".join(
        [
            f"8 0 {_compact_number(length)}",
            " ".join(
                [
                    "1",
                    _compact_number(start_point[0]),
                    _compact_number(start_point[1]),
                    _compact_number(start_point[2]),
                    _compact_number(dx / length),
                    _compact_number(dy / length),
                    _compact_number(dz / length),
                ]
            ),
        ]
    )


def _toolpath_arc_string(
    start_angle: float,
    end_angle: float,
    center_point: tuple[float, float, float],
    normal_vector: tuple[float, float, float],
    u_vector: tuple[float, float, float],
    v_vector: tuple[float, float, float],
    radius: float,
) -> str:
    return "\n".join(
        [
            f"8 {_compact_number(start_angle)} {_compact_number(end_angle)}",
            " ".join(
                [
                    "2",
                    _compact_number(center_point[0]),
                    _compact_number(center_point[1]),
                    _compact_number(center_point[2]),
                    _compact_number(normal_vector[0]),
                    _compact_number(normal_vector[1]),
                    _compact_number(normal_vector[2]),
                    _compact_number(u_vector[0]),
                    _compact_number(u_vector[1]),
                    _compact_number(u_vector[2]),
                    _compact_number(v_vector[0]),
                    _compact_number(v_vector[1]),
                    _compact_number(v_vector[2]),
                    _compact_number(radius),
                ]
            ),
        ]
    )


def _build_milling_toolpath_points(
    curve_points: list[tuple[float, float]],
    closed: bool,
    tool_radius: float,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float]]]:
    if not curve_points:
        raise ValueError("No hay puntos para construir ToolpathList sintético.")

    if closed:
        min_x = min(point[0] for point in curve_points)
        max_x = max(point[0] for point in curve_points)
        min_y = min(point[1] for point in curve_points)
        max_y = max(point[1] for point in curve_points)
        trajectory_points = [
            (min_x - tool_radius, min_y - tool_radius),
            (max_x + tool_radius, min_y - tool_radius),
            (max_x + tool_radius, max_y + tool_radius),
            (min_x - tool_radius, max_y + tool_radius),
        ]
        start_x, start_y = trajectory_points[0]
        approach_points = [
            (start_x - tool_radius, start_y),
            (start_x, start_y),
        ]
        lift_points = [
            (start_x, start_y),
            (start_x - tool_radius, start_y),
        ]
        return trajectory_points, approach_points, lift_points

    start_x, start_y = curve_points[0]
    end_x, end_y = curve_points[-1]
    if abs(end_x - start_x) >= abs(end_y - start_y):
        offset = (0.0, tool_radius)
        approach_delta = (0.0, -tool_radius)
    else:
        offset = (tool_radius, 0.0)
        approach_delta = (tool_radius, -tool_radius)

    trajectory_points = [
        (round(start_x + offset[0], 6), round(start_y + offset[1], 6)),
        (round(end_x + offset[0], 6), round(end_y + offset[1], 6)),
    ]
    approach_points = [
        (
            round(trajectory_points[0][0] + approach_delta[0], 6),
            round(trajectory_points[0][1] + approach_delta[1], 6),
        ),
        trajectory_points[0],
    ]
    lift_points = [
        trajectory_points[-1],
        (
            round(trajectory_points[-1][0] + approach_delta[0], 6),
            round(trajectory_points[-1][1] + tool_radius, 6),
        ),
    ]
    return trajectory_points, approach_points, lift_points


def _build_rectangle_milling_toolpath_strings(
    curve_points: list[tuple[float, float]],
    tool_radius: float,
) -> dict[str, list[str]]:
    min_x = min(point[0] for point in curve_points)
    max_x = max(point[0] for point in curve_points)
    min_y = min(point[1] for point in curve_points)
    max_y = max(point[1] for point in curve_points)
    width = max_x - min_x
    height = max_y - min_y
    safe_z = 38.0
    machining_z = -1.0
    radius = tool_radius

    return {
        "Approach": [
            _toolpath_line_string(
                (min_x - (2.0 * radius), min_y + radius, safe_z),
                (min_x - (2.0 * radius), min_y + radius, machining_z),
            ),
            _toolpath_arc_string(
                math.pi,
                1.5 * math.pi,
                (min_x - (2.0 * radius), min_y, machining_z),
                (0.0, 0.0, -1.0),
                (0.0, -1.0, 0.0),
                (-1.0, 0.0, 0.0),
                radius,
            ),
        ],
        "TrajectoryPath": [
            _toolpath_arc_string(
                math.pi,
                1.5 * math.pi,
                (min_x, min_y, machining_z),
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                radius,
            ),
            _toolpath_line_string(
                (min_x, min_y - radius, machining_z),
                (max_x, min_y - radius, machining_z),
            ),
            _toolpath_arc_string(
                1.5 * math.pi,
                2.0 * math.pi,
                (max_x, min_y, machining_z),
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                radius,
            ),
            _toolpath_line_string(
                (max_x + radius, min_y, machining_z),
                (max_x + radius, max_y, machining_z),
            ),
            _toolpath_arc_string(
                0.0,
                0.5 * math.pi,
                (max_x, max_y, machining_z),
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                radius,
            ),
            _toolpath_line_string(
                (max_x, max_y + radius, machining_z),
                (min_x, max_y + radius, machining_z),
            ),
            _toolpath_arc_string(
                0.5 * math.pi,
                math.pi,
                (min_x, max_y, machining_z),
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                radius,
            ),
            _toolpath_line_string(
                (min_x - radius, max_y, machining_z),
                (min_x - radius, min_y, machining_z),
            ),
        ],
        "Lift": [
            _toolpath_arc_string(
                0.0,
                0.5 * math.pi,
                (min_x - (2.0 * radius), min_y, machining_z),
                (0.0, 0.0, -1.0),
                (1.0, 0.0, 0.0),
                (0.0, -1.0, 0.0),
                radius,
            ),
            _toolpath_line_string(
                (min_x - (2.0 * radius), min_y - radius, machining_z),
                (min_x - (2.0 * radius), min_y - radius, safe_z),
            ),
        ],
    }


def _build_vertical_split_toolpath_strings(
    curve_points: list[tuple[float, float]],
    tool_radius: float,
) -> dict[str, list[str]]:
    split_x = round(curve_points[0][0], 6)
    start_y = min(point[1] for point in curve_points)
    end_y = max(point[1] for point in curve_points)
    safe_z = 38.0
    machining_z = -1.0
    radius = tool_radius
    center_x = split_x + (2.0 * radius)
    path_x = split_x + radius

    return {
        "Approach": [
            _toolpath_line_string(
                (center_x, start_y - radius, safe_z),
                (center_x, start_y - radius, machining_z),
            ),
            _toolpath_arc_string(
                0.5 * math.pi,
                math.pi,
                (center_x, start_y, machining_z),
                (0.0, 0.0, -1.0),
                (1.0, 0.0, 0.0),
                (0.0, -1.0, 0.0),
                radius,
            ),
        ],
        "TrajectoryPath": [
            _toolpath_line_string(
                (path_x, start_y, machining_z),
                (path_x, end_y, machining_z),
            ),
        ],
        "Lift": [
            _toolpath_arc_string(
                math.pi,
                1.5 * math.pi,
                (center_x, end_y, machining_z),
                (0.0, 0.0, -1.0),
                (1.0, 0.0, 0.0),
                (0.0, -1.0, 0.0),
                radius,
            ),
            _toolpath_line_string(
                (center_x, end_y + radius, machining_z),
                (center_x, end_y + radius, safe_z),
            ),
        ],
    }


def _build_milling_toolpath_strings(
    curve_points: list[tuple[float, float]],
    closed: bool,
    tool_radius: float,
) -> dict[str, list[str]]:
    if closed and len(curve_points) >= 4:
        return _build_rectangle_milling_toolpath_strings(curve_points, tool_radius)

    if not closed and len(curve_points) == 2 and abs(curve_points[0][0] - curve_points[1][0]) <= 1e-6:
        return _build_vertical_split_toolpath_strings(curve_points, tool_radius)

    trajectory_points, approach_points, lift_points = _build_milling_toolpath_points(
        curve_points,
        closed,
        tool_radius,
    )

    trajectory_path = list(trajectory_points)
    if closed and trajectory_path[0] != trajectory_path[-1]:
        trajectory_path.append(trajectory_path[0])

    safe_z = 38.0
    machining_z = -1.0
    approach_start = approach_points[0]
    approach_end = approach_points[-1]
    lift_start = lift_points[0]
    lift_end = lift_points[-1]

    return {
        "Approach": [
            _toolpath_line_string(
                (approach_start[0], approach_start[1], safe_z),
                (approach_start[0], approach_start[1], machining_z),
            ),
            _toolpath_line_string(
                (approach_start[0], approach_start[1], machining_z),
                (approach_end[0], approach_end[1], machining_z),
            ),
        ],
        "TrajectoryPath": [
            _toolpath_line_string(
                (start_x, start_y, machining_z),
                (end_x, end_y, machining_z),
            )
            for (start_x, start_y), (end_x, end_y) in zip(trajectory_path, trajectory_path[1:])
        ],
        "Lift": [
            _toolpath_line_string(
                (lift_start[0], lift_start[1], machining_z),
                (lift_end[0], lift_end[1], machining_z),
            ),
            _toolpath_line_string(
                (lift_end[0], lift_end[1], machining_z),
                (lift_end[0], lift_end[1], safe_z),
            ),
        ],
    }


def _configure_operation_toolpaths(
    operation_clone: ET.Element,
    curve_points: list[tuple[float, float]],
    closed: bool,
    tool_radius: float,
    key_counter,
) -> None:
    toolpath_list = operation_clone.find("./{*}ToolpathList")
    if toolpath_list is None:
        return

    toolpath_strings_by_type = _build_milling_toolpath_strings(
        curve_points,
        closed,
        tool_radius,
    )

    for toolpath in toolpath_list.findall("./{*}Toolpath"):
        path_type = str(toolpath.findtext("./{*}Type") or "").strip()
        basic_curve = toolpath.find("./{*}BasicCurve")
        if basic_curve is None or path_type not in toolpath_strings_by_type:
            continue
        _replace_serialized_curve_members(
            basic_curve,
            toolpath_strings_by_type[path_type],
            key_counter,
        )


def _configure_profile_geometry(
    geometry_clone: ET.Element,
    target_plane_id: str,
    target_plane_object_type: str,
    curve_points: list[tuple[float, float]],
    closed: bool,
    key_counter,
) -> None:
    _set_ref_id(geometry_clone, "./{*}PlaneID", target_plane_id, target_plane_object_type)
    _replace_serialized_curve_members(
        geometry_clone,
        _polyline_segment_strings(curve_points, closed=closed),
        key_counter,
    )


def _center_split_points(composite_width: float, composite_height: float) -> list[tuple[float, float]]:
    if composite_width >= composite_height:
        split_x = round(composite_width / 2.0, 6)
        return [(split_x, 0.0), (split_x, composite_height)]

    split_y = round(composite_height / 2.0, 6)
    return [(0.0, split_y), (composite_width, split_y)]


def _append_profile_from_template(
    profile_template: ProfileTemplate,
    profile_label: str,
    curve_points: list[tuple[float, float]],
    closed: bool,
    workpiece_id: str,
    workpiece_object_type: str,
    plane_ids_by_face: dict[str, str],
    plane_object_types_by_face: dict[str, str],
    features_collection: ET.Element,
    geometries_collection: ET.Element,
    operations_collection: ET.Element,
    id_generator,
    reference_instance: PieceInstance,
    synthetic_toolpaths_mode: str,
) -> list[ET.Element]:
    feature_clone = copy.deepcopy(profile_template.feature)
    geometry_clone = copy.deepcopy(profile_template.geometry)
    operation_clones = [copy.deepcopy(operation) for operation in profile_template.operations]
    step_clones = [copy.deepcopy(step) for step in profile_template.workingsteps]

    new_feature_id = next(id_generator)
    _set_text(feature_clone.find("./{*}Key/{*}ID"), new_feature_id)

    new_geometry_id = next(id_generator)
    _set_text(geometry_clone.find("./{*}Key/{*}ID"), new_geometry_id)

    op_id_map: dict[str, str] = {}
    op_object_types: dict[str, str] = {}
    for operation_clone in operation_clones:
        old_operation_id = _get_key_id(operation_clone)
        new_operation_id = next(id_generator)
        op_id_map[old_operation_id] = new_operation_id
        op_object_types[new_operation_id] = str(operation_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
        _set_text(operation_clone.find("./{*}Key/{*}ID"), new_operation_id)

    for step_clone in step_clones:
        _set_text(step_clone.find("./{*}Key/{*}ID"), next(id_generator))

    feature_object_type = str(feature_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
    geometry_object_type = str(geometry_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
    feature_domain_ns = _domain_namespace_from_object_type(feature_object_type)
    if feature_domain_ns:
        _set_xmlns(feature_clone, "a", feature_domain_ns)

    face_key = profile_template.face_name if profile_template.face_name in plane_ids_by_face else profile_template.face_name.title()
    _set_ref_id(feature_clone, "./{*}GeometryID", new_geometry_id, geometry_object_type)
    _set_ref_id(feature_clone, "./{*}WorkpieceID", workpiece_id, workpiece_object_type)
    _set_text(feature_clone.find("./{*}Name"), profile_label)
    for operation_ref in feature_clone.findall("./{*}OperationIDs/{*}ReferenceKey"):
        old_operation_id = str(operation_ref.findtext("./{*}ID") or "").strip()
        if old_operation_id not in op_id_map:
            continue
        _set_text(operation_ref.find("./{*}ID"), op_id_map[old_operation_id])
        _set_text(operation_ref.find("./{*}ObjectType"), op_object_types[op_id_map[old_operation_id]])

    _configure_profile_geometry(
        geometry_clone,
        plane_ids_by_face[face_key],
        plane_object_types_by_face[face_key],
        curve_points,
        closed,
        id_generator,
    )

    for operation_clone in operation_clones:
        operation_object_type = str(operation_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
        operation_domain_ns = _domain_namespace_from_object_type(operation_object_type)
        if operation_domain_ns:
            _set_xmlns(operation_clone, "a", operation_domain_ns)
        _set_xmlns(operation_clone, "b", BASE_MODEL_NS)
        _set_xmlns(operation_clone, "c", GEOMETRY_NS)
        _set_text(operation_clone.find("./{*}Name"), profile_label)
        _prepare_operation_clone_namespaces(operation_clone)
        if synthetic_toolpaths_mode == "generated":
            _configure_operation_toolpaths(
                operation_clone,
                curve_points,
                closed,
                _profile_tool_radius(feature_clone),
                id_generator,
            )
        else:
            _strip_operation_visualization_data(operation_clone)
            _prepare_operation_clone_namespaces(operation_clone)
        start_point = operation_clone.find("./{*}StartPoint")
        if start_point is not None and curve_points:
            _set_text(start_point.find("./{*}_x"), _compact_number(curve_points[0][0]))
            _set_text(start_point.find("./{*}_y"), _compact_number(curve_points[0][1]))
            _set_text(start_point.find("./{*}_z"), "0")

    for step_clone in step_clones:
        _set_ref_id(step_clone, "./{*}ManufacturingFeatureID", new_feature_id, feature_object_type)
        old_operation_id = str(step_clone.findtext("./{*}OperationID/{*}ID") or "").strip()
        if old_operation_id in op_id_map:
            _set_ref_id(step_clone, "./{*}OperationID", op_id_map[old_operation_id], op_object_types[op_id_map[old_operation_id]])
        if "MachiningWorkingStep" in _xsi_type(step_clone):
            _set_xmlns(step_clone, "a", PGMX_NS)
            _set_xmlns(step_clone.find("./{*}ManufacturingFeatureID"), "b", UTILITY_NS)
            _set_xmlns(step_clone.find("./{*}OperationID"), "b", UTILITY_NS)
        _set_text(step_clone.find("./{*}Name"), profile_label)
        _set_text(step_clone.find("./{*}Description"), "")

    features_collection.append(feature_clone)
    geometries_collection.append(geometry_clone)
    for operation_clone in operation_clones:
        operations_collection.append(operation_clone)

    return step_clones


def _transform_serialized_curve_text(text: str, instance: PieceInstance, min_x: float, min_y: float, composite_height: float) -> str:
    transformed_lines: list[str] = []
    for raw_line in (text or "").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        parts = stripped.split()
        if not parts or parts[0] not in {"1", "2"}:
            transformed_lines.append(stripped)
            continue

        try:
            values = [float(part.replace(",", ".")) for part in parts[1:]]
        except ValueError:
            transformed_lines.append(stripped)
            continue

        if len(values) < 3:
            transformed_lines.append(stripped)
            continue

        point_x, point_y = _map_local_point_to_composite(
            instance,
            min_x,
            min_y,
            composite_height,
            values[0],
            values[1],
        )
        values[0] = point_x
        values[1] = point_y

        remaining = values[3:]
        vector_count = len(remaining) // 3
        for index in range(vector_count):
            base = 3 + (index * 3)
            vector_x, vector_y = _map_local_vector_to_composite(
                instance,
                min_x,
                min_y,
                composite_height,
                values[base],
                values[base + 1],
            )
            values[base] = vector_x
            values[base + 1] = vector_y

        transformed_lines.append(" ".join([parts[0], *(_compact_number(value) for value in values)]))

    return "\n".join(transformed_lines)


def _remap_serializing_keys(container: ET.Element, key_counter) -> None:
    for key_group in container.iter():
        if _strip_namespace(key_group.tag) != "_serializingKeys":
            continue
        for key_node in list(key_group):
            if _strip_namespace(key_node.tag) != "unsignedInt":
                continue
            key_node.text = next(key_counter)


def _update_geometry_clone(geometry_clone: ET.Element, instance: PieceInstance, min_x: float, min_y: float, composite_height: float, target_plane_id: str, target_plane_object_type: str, key_counter) -> None:
    _set_ref_id(geometry_clone, "./{*}PlaneID", target_plane_id, target_plane_object_type)
    geometry_type = _xsi_type(geometry_clone)
    if "GeomCartesianPoint" in geometry_type:
        source_x = float(_safe_float(geometry_clone.findtext("./{*}_x"), 0.0) or 0.0)
        source_y = float(_safe_float(geometry_clone.findtext("./{*}_y"), 0.0) or 0.0)
        mapped_x, mapped_y = _map_local_point_to_composite(instance, min_x, min_y, composite_height, source_x, source_y)
        _set_text(geometry_clone.find("./{*}_x"), _compact_number(mapped_x))
        _set_text(geometry_clone.find("./{*}_y"), _compact_number(mapped_y))
        return

    if "GeomCompositeCurve" in geometry_type:
        for string_node in geometry_clone.findall(".//{*}_serializingMembers/{*}string"):
            string_node.text = _transform_serialized_curve_text(string_node.text or "", instance, min_x, min_y, composite_height)
        _remap_serializing_keys(geometry_clone, key_counter)


def _update_operation_clone(operation_clone: ET.Element, instance: PieceInstance, min_x: float, min_y: float, composite_height: float, key_counter) -> None:
    _prepare_operation_clone_namespaces(operation_clone)

    for text_node in operation_clone.iter():
        tag_name = _strip_namespace(text_node.tag)
        if tag_name == "_serializationGeometryDescription" and str(text_node.text or "").strip():
            text_node.text = _transform_serialized_curve_text(text_node.text or "", instance, min_x, min_y, composite_height)
    for string_node in operation_clone.findall(".//{*}_serializingMembers/{*}string"):
        string_node.text = _transform_serialized_curve_text(string_node.text or "", instance, min_x, min_y, composite_height)
    _remap_serializing_keys(operation_clone, key_counter)


def _strip_operation_visualization_data(operation_clone: ET.Element) -> None:
    for toolpath_list in operation_clone.findall(".//{*}ToolpathList"):
        for child in list(toolpath_list):
            toolpath_list.remove(child)

    for node in operation_clone.iter():
        if _strip_namespace(node.tag) == "_serializationGeometryDescription":
            node.text = ""


def _prepare_template_root(template_context: SourceContext, module_name: str, composite_width: float, composite_height: float, composite_thickness: float, source_instances: list[str]) -> tuple[ET.Element, str, dict[str, str], dict[str, str], ET.Element, list[ET.Element]]:
    root = copy.deepcopy(template_context.root)

    _set_text(root.find("./{*}CurrentWorkplanIndex"), "0")
    _set_xmlns(root.find("./{*}GlobalSetup"), "a", BASE_MODEL_NS)
    _set_xmlns(root.find("./{*}MachiningParameters"), "a", BASE_MODEL_NS)

    features = _find_collection(root, "Features")
    geometries = _find_collection(root, "Geometries")
    operations = _find_collection(root, "Operations")
    planes = _find_collection(root, "Planes")
    workplans = _find_collection(root, "Workplans")
    workpieces = _find_collection(root, "Workpieces")
    expressions = _find_collection(root, "Expressions")
    variables = _find_collection(root, "Variables")

    main_workplan = workplans.find("./{*}MainWorkplan")
    if main_workplan is None:
        raise ValueError("La plantilla no contiene MainWorkplan.")
    elements = main_workplan.find("./{*}Elements")
    if elements is None:
        raise ValueError("La plantilla no contiene Elements dentro del MainWorkplan.")
    setup = main_workplan.find("./{*}Setup")
    if setup is not None:
        _set_xmlns(setup, "a", BASE_MODEL_NS)
        for placement in setup.findall(".//{*}Placement"):
            _set_xmlns(placement, "b", GEOMETRY_NS)
            _set_xmlns(placement.find("./{*}PlaneID"), "c", UTILITY_NS)
            _set_text(placement.find("./{*}_zP"), _compact_number(MACHINING_SETUP_Z_ORIGIN))

    preserved_non_steps = [
        copy.deepcopy(executable)
        for executable in list(elements)
        if "MachiningWorkingStep" not in _xsi_type(executable)
    ]
    for preserved in preserved_non_steps:
        if _xsi_type(preserved) == "Xn":
            _set_default_xmlns(preserved, BASE_MODEL_NS)
            _set_xmlns(preserved.find("./{*}GeometryID"), "a", UTILITY_NS)
            _set_xmlns(preserved.find("./{*}WorkpieceID"), "a", UTILITY_NS)
            _set_xmlns(preserved.find("./{*}Tool"), "a", UTILITY_NS)

    features.clear()
    geometries.clear()
    operations.clear()
    elements.clear()

    _set_xmlns(geometries, "a", GEOMETRY_NS)

    workpiece = workpieces.find("./{*}WorkPiece")
    if workpiece is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    workpiece_id = _get_key_id(workpiece)
    workpiece_object_type = str(workpiece.findtext("./{*}Key/{*}ObjectType") or "").strip()

    _set_text(workpiece.find("./{*}Name"), f"{module_name} - En Juego Compuesto")
    _set_text(workpiece.find("./{*}Depth"), _compact_number(composite_thickness))
    _set_text(workpiece.find("./{*}Length"), _compact_number(composite_width))
    _set_text(workpiece.find("./{*}Width"), _compact_number(composite_height))
    _set_text(workpiece.find("./{*}Geometry/{*}Depth"), _compact_number(composite_thickness))
    _set_text(workpiece.find("./{*}Geometry/{*}Length"), _compact_number(composite_width))
    _set_text(workpiece.find("./{*}Geometry/{*}Width"), _compact_number(composite_height))
    _set_xmlns(workpiece.find("./{*}Geometry"), "a", BASE_MODEL_NS)

    plane_ids_by_face: dict[str, str] = {}
    plane_object_types_by_face: dict[str, str] = {}
    for plane in list(planes):
        face_name = str(plane.findtext("./{*}Type") or plane.findtext("./{*}Name") or "Top").strip() or "Top"
        plane_id = _get_key_id(plane)
        plane_ids_by_face[face_name] = plane_id
        plane_object_types_by_face[face_name] = str(plane.findtext("./{*}Key/{*}ObjectType") or "").strip()

        _set_text(plane.find("./{*}GeneratorKey/{*}ID"), workpiece_id)
        _set_text(plane.find("./{*}GeneratorKey/{*}ObjectType"), workpiece_object_type)
        _set_text(plane.find("./{*}WorkpieceID/{*}ID"), workpiece_id)
        _set_text(plane.find("./{*}WorkpieceID/{*}ObjectType"), workpiece_object_type)

        if face_name == "Top":
            x_dimension, y_dimension = composite_width, composite_height
            placement_updates = {"_xP": 0.0, "_yP": 0.0, "_zP": composite_thickness}
        elif face_name == "Bottom":
            x_dimension, y_dimension = composite_width, composite_height
            placement_updates = {"_xP": 0.0, "_yP": composite_height, "_zP": 0.0}
        elif face_name == "Right":
            x_dimension, y_dimension = composite_height, composite_thickness
            placement_updates = {"_xP": composite_width, "_yP": 0.0, "_zP": 0.0}
        elif face_name == "Left":
            x_dimension, y_dimension = composite_height, composite_thickness
            placement_updates = {"_xP": 0.0, "_yP": composite_height, "_zP": 0.0}
        elif face_name == "Front":
            x_dimension, y_dimension = composite_width, composite_thickness
            placement_updates = {"_xP": 0.0, "_yP": 0.0, "_zP": 0.0}
        elif face_name == "Back":
            x_dimension, y_dimension = composite_width, composite_thickness
            placement_updates = {"_xP": composite_width, "_yP": composite_height, "_zP": 0.0}
        else:
            x_dimension, y_dimension = composite_width, composite_height
            placement_updates = {"_xP": 0.0, "_yP": 0.0, "_zP": 0.0}

        _set_text(plane.find("./{*}XDimension"), _compact_number(x_dimension))
        _set_text(plane.find("./{*}YDimension"), _compact_number(y_dimension))
        placement = plane.find("./{*}Placement")
        if placement is not None:
            for key, value in placement_updates.items():
                _set_text(placement.find(f"./{{*}}{key}"), _compact_number(value))

    for expression in list(expressions):
        property_name = str(expression.findtext("./{*}Property/{*}Name") or "").strip().lower()
        _set_text(expression.find("./{*}ReferencedObject/{*}ID"), workpiece_id)
        _set_text(expression.find("./{*}ReferencedObject/{*}ObjectType"), workpiece_object_type)
        if property_name == "length":
            _set_text(expression.find("./{*}Value"), "dx1")
        elif property_name == "width":
            _set_text(expression.find("./{*}Value"), "dy1")
        elif property_name == "depth":
            _set_text(expression.find("./{*}Value"), "dz1")

    for variable in list(variables):
        variable_name = str(variable.findtext("./{*}Name") or "").strip().lower()
        if variable_name == "dx1":
            _set_text(variable.find("./{*}Value"), _compact_number(composite_width))
        elif variable_name == "dy1":
            _set_text(variable.find("./{*}Value"), _compact_number(composite_height))
        elif variable_name == "dz1":
            _set_text(variable.find("./{*}Value"), _compact_number(composite_thickness))
        _set_xmlns(variable.find("./{*}Value"), "b", XSD_NS)

    return root, workpiece_id, plane_ids_by_face, plane_object_types_by_face, elements, preserved_non_steps


def _bundle_info(feature: ET.Element, context: SourceContext) -> tuple[ET.Element, list[ET.Element], list[ET.Element], str]:
    feature_id = _get_key_id(feature)
    geometry_id = str(feature.findtext("./{*}GeometryID/{*}ID") or "").strip()
    if not geometry_id or geometry_id not in context.geometry_by_id:
        raise ValueError(f"Feature sin GeometryID válido en '{context.source_path.name}'.")
    geometry = context.geometry_by_id[geometry_id]
    plane_id = str(geometry.findtext("./{*}PlaneID/{*}ID") or "").strip()
    face_name = context.plane_face_by_id.get(plane_id, "Top")
    operation_ids = [
        str(ref.text or "").strip()
        for ref in feature.findall("./{*}OperationIDs/{*}ReferenceKey/{*}ID")
        if str(ref.text or "").strip()
    ]
    operations = [context.operation_by_id[op_id] for op_id in operation_ids if op_id in context.operation_by_id]
    workingsteps = [copy.deepcopy(step) for step in context.workingsteps_by_feature_id.get(feature_id, [])]
    return geometry, operations, workingsteps, face_name


def _write_pgmx_zip(output_path: Path, xml_bytes: bytes, template_entries: dict[str, bytes], xml_entry_name: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(xml_entry_name, xml_bytes)
        epl_written = False
        for entry_name, data in template_entries.items():
            if entry_name.lower().endswith(".xml"):
                continue
            if entry_name.lower().endswith(".epl"):
                zip_file.writestr(f"{output_path.stem}.epl", data)
                epl_written = True
                continue
            zip_file.writestr(entry_name, data)
        if not epl_written:
            zip_file.writestr(f"{output_path.stem}.epl", b"")


def _finalize_pgmx_xml_bytes(xml_bytes: bytes) -> bytes:
    xml_text = xml_bytes.decode("utf-8")
    geometry_decl = f'<Geometries xmlns:a="{GEOMETRY_NS}">'
    global_setup_decl = f'<GlobalSetup xmlns:a="{BASE_MODEL_NS}">'
    machining_params_decl = (
        f'<MachiningParameters i:type="a:XilogHeaderParameters" xmlns:a="{BASE_MODEL_NS}">'
    )
    workpiece_geometry_decl = f'<Geometry i:type="a:WorkpieceBoxGeometry" xmlns:a="{BASE_MODEL_NS}">'
    variable_value_decl = f'<Value i:type="b:double" xmlns:b="{XSD_NS}">'
    toolpath_list_decl = f'<ToolpathList xmlns:b="{BASE_MODEL_NS}">'
    head_decl = f'<Head xmlns:b="{BASE_MODEL_NS}">'
    machine_functions_decl = f'<MachineFunctions xmlns:b="{BASE_MODEL_NS}">'
    start_point_decl = f'<StartPoint xmlns:b="{GEOMETRY_NS}">'
    tool_key_decl = f'<ToolKey xmlns:b="{UTILITY_NS}">'
    approach_decl = f'<Approach i:type="b:BaseApproachStrategy" xmlns:b="{STRATEGY_NS}">'
    retract_decl = f'<Retract i:type="b:BaseRetractStrategy" xmlns:b="{STRATEGY_NS}">'

    if "<Geometries>" in xml_text and geometry_decl not in xml_text:
        xml_text = xml_text.replace("<Geometries>", geometry_decl, 1)
    if "<GlobalSetup>" in xml_text and global_setup_decl not in xml_text:
        xml_text = xml_text.replace("<GlobalSetup>", global_setup_decl, 1)
    xml_text = xml_text.replace(
        '<MachiningParameters i:type="a:XilogHeaderParameters">',
        machining_params_decl,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Geometry i:type="a:WorkpieceBoxGeometry">',
        lambda match: (
            f'<{match.group("prefix") or ""}Geometry i:type="a:WorkpieceBoxGeometry" '
            f'xmlns:a="{BASE_MODEL_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Value i:type="b:double">',
        lambda match: (
            f'<{match.group("prefix") or ""}Value i:type="b:double" '
            f'xmlns:b="{XSD_NS}">'
        ),
        xml_text,
    )
    if "<ToolpathList>" in xml_text and toolpath_list_decl not in xml_text:
        xml_text = xml_text.replace("<ToolpathList>", toolpath_list_decl)
    if "<Head>" in xml_text and head_decl not in xml_text:
        xml_text = xml_text.replace("<Head>", head_decl)
    if "<MachineFunctions>" in xml_text and machine_functions_decl not in xml_text:
        xml_text = xml_text.replace("<MachineFunctions>", machine_functions_decl)
    if "<StartPoint>" in xml_text and start_point_decl not in xml_text:
        xml_text = xml_text.replace("<StartPoint>", start_point_decl)
    if "<ToolKey>" in xml_text and tool_key_decl not in xml_text:
        xml_text = xml_text.replace("<ToolKey>", tool_key_decl)
    xml_text = xml_text.replace(
        '<Approach i:type="b:BaseApproachStrategy">',
        approach_decl,
    )
    xml_text = xml_text.replace(
        '<Retract i:type="b:BaseRetractStrategy">',
        retract_decl,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="a:MachiningWorkingStep">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="a:MachiningWorkingStep" '
            f'xmlns:a="{PGMX_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="Xn">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="Xn" '
            f'xmlns="{BASE_MODEL_NS}">'
        ),
        xml_text,
        count=1,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?ManufacturingFeatureID>',
        lambda match: (
            f'<{match.group("prefix") or ""}ManufacturingFeatureID '
            f'xmlns:b="{UTILITY_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?OperationID>',
        lambda match: (
            f'<{match.group("prefix") or ""}OperationID '
            f'xmlns:b="{UTILITY_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?PlaneID>',
        lambda match: f'<{match.group("prefix") or ""}PlaneID xmlns:c="{UTILITY_NS}">',
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?BasicCurve i:type="c:GeomCompositeCurve">',
        lambda match: (
            f'<{match.group("prefix") or ""}BasicCurve i:type="c:GeomCompositeCurve" '
            f'xmlns:c="{GEOMETRY_NS}">'
        ),
        xml_text,
    )
    return xml_text.encode("utf-8")


def export_module_en_juego_to_pgmx(
    project_json_path: Path,
    module_path: Path,
    output_path: Optional[Path] = None,
    template_pgmx_path: Optional[Path] = None,
    preserve_visualization_paths: bool = False,
    preserve_drill_toolpaths: bool = True,
    synthetic_toolpaths_mode: str = "generated",
    preserve_xn: bool = True,
    raw_drill_toolpaths: bool = True,
) -> CompositeReport:
    project = _load_project(project_json_path)
    config_data = json.loads((module_path / "module_config.json").read_text(encoding="utf-8"))
    module_name = str(config_data.get("module") or module_path.name)

    instances = _load_piece_instances(project, module_path, config_data)
    _enforce_min_instance_spacing(instances, _load_cut_saw_kerf_mm())
    min_x, min_y, composite_width, composite_height, composite_thickness = _composite_dimensions(instances)
    if composite_width <= 0 or composite_height <= 0:
        raise ValueError("El conjunto En-Juego produjo dimensiones compuestas inválidas.")

    if output_path is None:
        if template_pgmx_path is not None:
            output_path = template_pgmx_path.parent / f"{_sanitize_filename(module_name)}_en_juego_compuesto.pgmx"
        else:
            output_path = module_path / f"{_sanitize_filename(module_name)}_en_juego_compuesto.pgmx"

    source_context_cache: dict[str, SourceContext] = {}

    def get_context(source_path: Path) -> SourceContext:
        cache_key = str(source_path)
        if cache_key not in source_context_cache:
            source_context_cache[cache_key] = _build_source_context(source_path)
        return source_context_cache[cache_key]

    template_context = (
        _build_source_context(template_pgmx_path)
        if template_pgmx_path is not None
        else get_context(instances[0].drawing.source_path)
    )
    (
        root,
        workpiece_id,
        plane_ids_by_face,
        plane_object_types_by_face,
        workplan_elements,
        preserved_non_steps,
    ) = _prepare_template_root(
        template_context,
        module_name,
        composite_width,
        composite_height,
        composite_thickness,
        [instance.title_text for instance in instances],
    )

    features_collection = _find_collection(root, "Features")
    geometries_collection = _find_collection(root, "Geometries")
    operations_collection = _find_collection(root, "Operations")
    id_generator = _id_counter(root)

    drill_count = 0
    milling_path_count = 0
    skipped_operations: list[str] = []
    skipped_paths: list[str] = []
    appended_steps: list[ET.Element] = []
    squaring_template: Optional[ProfileTemplate] = None

    if not preserve_xn:
        preserved_non_steps = []

    for instance in instances:
        source_context = get_context(instance.drawing.source_path)
        suffix = _instance_suffix(instance.instance_key)

        for source_feature in list(source_context.features):
            geometry, source_operations, workingsteps, face_name = _bundle_info(source_feature, source_context)
            face_key = face_name if face_name in plane_ids_by_face else face_name.title()
            if str(face_key).strip().lower() not in {"top", "bottom"}:
                label = str(source_feature.findtext("./{*}Name") or _get_key_id(source_feature) or "feature").strip()
                skipped_operations.append(f"{instance.title_text}: {label} en cara {face_name}")
                continue

            if _is_squaring_profile(source_feature, geometry, source_operations, instance.top_width, instance.top_height):
                if squaring_template is None:
                    squaring_template = ProfileTemplate(
                        feature=copy.deepcopy(source_feature),
                        geometry=copy.deepcopy(geometry),
                        operations=[copy.deepcopy(operation) for operation in source_operations],
                        workingsteps=[copy.deepcopy(step) for step in workingsteps],
                        face_name=face_key,
                    )
                skipped_operations.append(f"{instance.title_text}: escuadrado original sustituido por perfil global")
                continue

            feature_clone = copy.deepcopy(source_feature)
            geometry_clone = copy.deepcopy(geometry)
            operation_clones = [copy.deepcopy(operation) for operation in source_operations]

            new_feature_id = next(id_generator)
            _set_text(feature_clone.find("./{*}Key/{*}ID"), new_feature_id)

            new_geometry_id = next(id_generator)
            _set_text(geometry_clone.find("./{*}Key/{*}ID"), new_geometry_id)

            op_id_map: dict[str, str] = {}
            op_object_types: dict[str, str] = {}
            for operation_clone in operation_clones:
                old_operation_id = _get_key_id(operation_clone)
                new_operation_id = next(id_generator)
                op_id_map[old_operation_id] = new_operation_id
                op_object_types[new_operation_id] = str(operation_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
                _set_text(operation_clone.find("./{*}Key/{*}ID"), new_operation_id)

            step_clones = [copy.deepcopy(step) for step in workingsteps]
            for step_clone in step_clones:
                _set_text(step_clone.find("./{*}Key/{*}ID"), next(id_generator))

            feature_object_type = str(feature_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
            geometry_object_type = str(geometry_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
            feature_domain_ns = _domain_namespace_from_object_type(feature_object_type)
            if feature_domain_ns:
                _set_xmlns(feature_clone, "a", feature_domain_ns)

            _set_ref_id(feature_clone, "./{*}GeometryID", new_geometry_id, geometry_object_type)
            _set_ref_id(feature_clone, "./{*}WorkpieceID", workpiece_id, template_context.workpiece_object_type)
            for operation_ref in feature_clone.findall("./{*}OperationIDs/{*}ReferenceKey"):
                old_operation_id = str(operation_ref.findtext("./{*}ID") or "").strip()
                if old_operation_id not in op_id_map:
                    continue
                _set_text(operation_ref.find("./{*}ID"), op_id_map[old_operation_id])
                _set_text(operation_ref.find("./{*}ObjectType"), op_object_types[op_id_map[old_operation_id]])

            _rename_text_field(feature_clone, "./{*}Name", suffix)

            _update_geometry_clone(
                geometry_clone,
                instance,
                min_x,
                min_y,
                composite_height,
                plane_ids_by_face[face_key],
                plane_object_types_by_face[face_key],
                id_generator,
            )

            for operation_clone in operation_clones:
                operation_object_type = str(operation_clone.findtext("./{*}Key/{*}ObjectType") or "").strip()
                operation_domain_ns = _domain_namespace_from_object_type(operation_object_type)
                is_drill_operation = "DrillingOperation" in operation_object_type
                if operation_domain_ns:
                    _set_xmlns(operation_clone, "a", operation_domain_ns)
                _set_xmlns(operation_clone, "b", BASE_MODEL_NS)
                _set_xmlns(operation_clone, "c", GEOMETRY_NS)
                keep_toolpaths = preserve_visualization_paths or (
                    preserve_drill_toolpaths and is_drill_operation
                )
                if not keep_toolpaths:
                    _strip_operation_visualization_data(operation_clone)
                    _update_operation_clone(operation_clone, instance, min_x, min_y, composite_height, id_generator)
                elif is_drill_operation and raw_drill_toolpaths and not preserve_visualization_paths:
                    _prepare_operation_clone_namespaces(operation_clone)
                else:
                    _update_operation_clone(operation_clone, instance, min_x, min_y, composite_height, id_generator)

            for step_clone in step_clones:
                _set_ref_id(step_clone, "./{*}ManufacturingFeatureID", new_feature_id, feature_object_type)
                old_operation_id = str(step_clone.findtext("./{*}OperationID/{*}ID") or "").strip()
                if old_operation_id in op_id_map:
                    _set_ref_id(step_clone, "./{*}OperationID", op_id_map[old_operation_id], op_object_types[op_id_map[old_operation_id]])
                if "MachiningWorkingStep" in _xsi_type(step_clone):
                    _set_xmlns(step_clone, "a", PGMX_NS)
                    _set_xmlns(step_clone.find("./{*}ManufacturingFeatureID"), "b", UTILITY_NS)
                    _set_xmlns(step_clone.find("./{*}OperationID"), "b", UTILITY_NS)
                _rename_text_field(step_clone, "./{*}Name", suffix)
                _rename_text_field(step_clone, "./{*}Description", suffix)

            features_collection.append(feature_clone)
            geometries_collection.append(geometry_clone)
            for operation_clone in operation_clones:
                operations_collection.append(operation_clone)
            appended_steps.extend(step_clones)

            if "RoundHole" in _xsi_type(feature_clone) or "Drilling" in feature_object_type:
                drill_count += 1
            if "GeneralProfileFeature" in _xsi_type(feature_clone):
                milling_path_count += 1

    if squaring_template is None:
        raise ValueError("No se detectó un mecanizado de escuadrado en las piezas En Juego.")

    appended_steps.extend(
        _append_profile_from_template(
            profile_template=squaring_template,
            profile_label="ESCUADRADO_EN_JUEGO",
            curve_points=[
                (0.0, 0.0),
                (composite_width, 0.0),
                (composite_width, composite_height),
                (0.0, composite_height),
            ],
            closed=True,
            workpiece_id=workpiece_id,
            workpiece_object_type=template_context.workpiece_object_type,
            plane_ids_by_face=plane_ids_by_face,
            plane_object_types_by_face=plane_object_types_by_face,
            features_collection=features_collection,
            geometries_collection=geometries_collection,
            operations_collection=operations_collection,
            id_generator=id_generator,
            reference_instance=instances[0],
            synthetic_toolpaths_mode=synthetic_toolpaths_mode,
        )
    )
    appended_steps.extend(
        _append_profile_from_template(
            profile_template=squaring_template,
            profile_label="DIVISION_EN_JUEGO",
            curve_points=_center_split_points(composite_width, composite_height),
            closed=False,
            workpiece_id=workpiece_id,
            workpiece_object_type=template_context.workpiece_object_type,
            plane_ids_by_face=plane_ids_by_face,
            plane_object_types_by_face=plane_object_types_by_face,
            features_collection=features_collection,
            geometries_collection=geometries_collection,
            operations_collection=operations_collection,
            id_generator=id_generator,
            reference_instance=instances[0],
            synthetic_toolpaths_mode=synthetic_toolpaths_mode,
        )
    )
    milling_path_count += 2

    for priority, step in enumerate(appended_steps):
        _set_text(step.find("./{*}Priority"), priority)
        workplan_elements.append(step)

    for preserved in preserved_non_steps:
        workplan_elements.append(preserved)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    xml_bytes = _finalize_pgmx_xml_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    _write_pgmx_zip(
        output_path=output_path,
        xml_bytes=xml_bytes,
        template_entries=template_context.archive_entries,
        xml_entry_name=f"{output_path.stem}.xml",
    )

    return CompositeReport(
        module_name=module_name,
        output_path=output_path,
        width=composite_width,
        height=composite_height,
        thickness=composite_thickness,
        source_instances=[instance.title_text for instance in instances],
        drill_count=drill_count,
        milling_path_count=milling_path_count,
        skipped_operations=skipped_operations,
        skipped_paths=skipped_paths,
    )


def _resolve_module_path(project_json_path: Path, module_name: Optional[str], module_path: Optional[Path]) -> Path:
    if module_path is not None:
        return module_path

    if not module_name:
        raise ValueError("Debe indicar --module-path o --module-name.")

    data = json.loads(project_json_path.read_text(encoding="utf-8"))
    for module_data in data.get("modules", []):
        if str(module_data.get("name") or "").strip().lower() == module_name.strip().lower():
            return Path(module_data["path"])

    raise ValueError(f"No se encontró el módulo '{module_name}' en el proyecto.")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Exporta el layout En-Juego de un módulo a un PGMX compuesto.")
    parser.add_argument("--project-json", required=True, help="Ruta al archivo JSON del proyecto.")
    parser.add_argument("--module-name", help="Nombre exacto del módulo dentro del proyecto.")
    parser.add_argument("--module-path", help="Ruta directa a la carpeta del módulo.")
    parser.add_argument(
        "--template-pgmx",
        help="Ruta a un .pgmx plantilla para usar como root base de salida; útil para trabajar con baselines locales del repo.",
    )
    parser.add_argument("--output", help="Ruta del .pgmx de salida.")
    parser.add_argument(
        "--keep-visualization-paths",
        action="store_true",
        help="Conserva ToolpathList/Xn/geom. serializada de operaciones tal como salen de la clonación.",
    )
    parser.set_defaults(preserve_drill_toolpaths=True)
    parser.add_argument(
        "--keep-drill-toolpaths",
        dest="preserve_drill_toolpaths",
        action="store_true",
        help="Conserva los ToolpathList de los taladros clonados; ahora es el modo por defecto.",
    )
    parser.add_argument(
        "--raw-drill-toolpaths",
        action="store_true",
        help="Conserva los ToolpathList de taladro sin transformar sus coordenadas; ahora es el modo por defecto.",
    )
    parser.add_argument(
        "--transform-drill-toolpaths",
        dest="raw_drill_toolpaths",
        action="store_false",
        help="Transforma las coordenadas de los ToolpathList de taladro al tablero compuesto; útil sólo para depuración.",
    )
    parser.add_argument(
        "--strip-drill-toolpaths",
        dest="preserve_drill_toolpaths",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--synthetic-toolpaths",
        choices=["generated", "empty"],
        default="generated",
        help="Define si los perfiles sintéticos globales llevan ToolpathList generado o vacío.",
    )
    parser.set_defaults(preserve_xn=True, raw_drill_toolpaths=True)
    parser.add_argument(
        "--strip-xn",
        dest="preserve_xn",
        action="store_false",
        help="Quita el ejecutable auxiliar XN del MainWorkplan; útil sólo para depuración.",
    )
    args = parser.parse_args(argv)

    project_json_path = Path(args.project_json)
    module_path = _resolve_module_path(
        project_json_path,
        args.module_name,
        Path(args.module_path) if args.module_path else None,
    )
    report = export_module_en_juego_to_pgmx(
        project_json_path=project_json_path,
        module_path=module_path,
        output_path=Path(args.output) if args.output else None,
        template_pgmx_path=Path(args.template_pgmx) if args.template_pgmx else None,
        preserve_visualization_paths=args.keep_visualization_paths,
        preserve_drill_toolpaths=args.preserve_drill_toolpaths,
        synthetic_toolpaths_mode=args.synthetic_toolpaths,
        preserve_xn=args.preserve_xn,
        raw_drill_toolpaths=args.raw_drill_toolpaths,
    )

    print(f"PGMX compuesto generado: {report.output_path}")
    print(
        "Dimensiones finales: "
        f"{_compact_number(report.width)} x {_compact_number(report.height)} x {_compact_number(report.thickness)} mm"
    )
    print(f"Instancias fuente: {', '.join(report.source_instances)}")
    print(f"Taladros exportados: {report.drill_count}")
    print(f"Trayectorias exportadas: {report.milling_path_count}")
    if report.skipped_operations:
        print("Operaciones omitidas:")
        for item in report.skipped_operations:
            print(f"- {item}")
    if report.skipped_paths:
        print("Trayectorias omitidas:")
        for item in report.skipped_paths:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())