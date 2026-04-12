"""Utilidades para sintetizar archivos `.pgmx` a partir de un baseline limpio.

La API publica del modulo esta pensada para poder reutilizarla desde el flujo
principal de la aplicacion, sin depender de la CLI:

Referencia operativa recomendada:
- `docs/synthesize_pgmx_help.md`

- `read_pgmx_state(...)` lee dimensiones, nombre, origen y area desde un `.pgmx`.
- `build_synthesis_request(...)` arma una solicitud clara y reusable.
- `synthesize_request(...)` aplica la solicitud sobre un baseline y escribe el
    `.pgmx` de salida.
- `synthesize_pgmx(...)` se mantiene como wrapper de compatibilidad para los
    scripts y experimentos ya existentes.

Soporte actual de mecanizados sinteticos:
- `LineMillingSpec`: linea sobre un plano con su fresado asociado.
- `PolylineMillingSpec`: polilinea abierta con su fresado asociado.

Hallazgos ya volcados en la sintesis:
- `Area` de `Parametros de Maquina` usa `HG` por defecto si no se indica otro valor.
- `Approach` y `Retract` soportan `Line` y `Arc`.
- Para `Approach Line + Down` ya se sintetizo la regla observada en Maestro:
    una sola bajada oblicua desde un punto previo desplazado sobre la direccion
    opuesta al avance, sin alterar `TrajectoryPath`.
- Para `Retract Line + Up` ya se sintetizo la regla observada en Maestro:
    una sola subida oblicua hacia un punto final desplazado sobre la direccion
    de salida, sin alterar `TrajectoryPath`.
- Para `Arc + Quote` ya se sintetizo la regla observada en Maestro para entrada/salida
    sobre perfiles rectos: toolpath vertical cuando la estrategia esta deshabilitada y
    `linea vertical + arco` / `arco + linea vertical` cuando esta habilitada.
- Para `Retract Arc + Up` ya se sintetizo la salida observada en Maestro:
    `arco en un plano vertical + linea vertical`, sin alterar `TrajectoryPath`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional, Sequence

PGMX_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.ProjectModule"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
BASE_MODEL_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"
MILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Milling"
GEOMETRY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Geometry"
STRATEGY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Strategy"
UTILITY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Utility"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
ARRAYS_NS = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
PARAMETRIC_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Parametrics"

ET.register_namespace("", PGMX_NS)
ET.register_namespace("i", XSI_NS)

__all__ = [
    "PgmxState",
    "ApproachSpec",
    "RetractSpec",
    "MillingDepthSpec",
    "LineMillingSpec",
    "PolylineMillingSpec",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "build_approach_spec",
    "build_retract_spec",
    "build_milling_depth_spec",
    "build_line_milling_spec",
    "build_polyline_milling_spec",
    "read_pgmx_state",
    "build_synthesis_request",
    "synthesize_request",
    "synthesize_pgmx",
]


# ============================================================================
# Public data model
# ============================================================================

@dataclass(frozen=True)
class PgmxState:
    """Descripcion de la pieza final a sintetizar."""

    piece_name: str
    length: float
    width: float
    depth: float
    origin_x: float
    origin_y: float
    origin_z: float
    execution_fields: str = "HG"


@dataclass(frozen=True)
class ApproachSpec:
    """Configuracion reutilizable del approach de un fresado lineal."""

    is_enabled: bool = False
    approach_type: str = "Line"
    mode: str = "Down"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"


@dataclass(frozen=True)
class RetractSpec:
    """Configuracion reutilizable del retract de un fresado lineal."""

    is_enabled: bool = False
    retract_type: str = "Line"
    mode: str = "Up"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"
    overlap: float = 0.0


@dataclass(frozen=True)
class MillingDepthSpec:
    """Configuracion reutilizable de profundidad para un fresado."""

    is_through: bool = True
    target_depth: Optional[float] = None
    extra_depth: float = 0.0


@dataclass(frozen=True)
class LineMillingSpec:
    """Descripcion reutilizable de un fresado lineal sobre un plano."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1902"
    tool_name: str = "E003"
    tool_width: float = 9.52
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)


@dataclass(frozen=True)
class PolylineMillingSpec:
    """Descripcion reutilizable de un fresado asociado a una polilinea abierta."""

    points: tuple[tuple[float, float], ...]
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1902"
    tool_name: str = "E003"
    tool_width: float = 9.52
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)


@dataclass(frozen=True)
class _CurveSpec:
    """Serializacion XML de una curva usada en geometria o toolpaths."""

    geometry_type: str = "GeomTrimmedCurve"
    serialization: Optional[str] = None
    member_keys: tuple[str, ...] = ()
    member_serializations: tuple[str, ...] = ()


@dataclass(frozen=True)
class _HydratedLineMillingSpec:
    """Datos internos de serializacion que complementan un `LineMillingSpec`."""

    spec: LineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_serialization: Optional[str] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def start_x(self) -> float:
        return self.spec.start_x

    @property
    def start_y(self) -> float:
        return self.spec.start_y

    @property
    def end_x(self) -> float:
        return self.spec.end_x

    @property
    def end_y(self) -> float:
        return self.spec.end_y

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract


@dataclass(frozen=True)
class _HydratedPolylineMillingSpec:
    """Datos internos de serializacion que complementan un `PolylineMillingSpec`."""

    spec: PolylineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def points(self) -> tuple[tuple[float, float], ...]:
        return self.spec.points

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract


@dataclass(frozen=True)
class PgmxSynthesisRequest:
    """Solicitud completa para sintetizar un `.pgmx` reutilizable desde la app."""

    baseline_path: Path
    output_path: Path
    piece: PgmxState
    source_pgmx_path: Optional[Path] = None
    line_millings: tuple[LineMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()


@dataclass(frozen=True)
class PgmxSynthesisResult:
    """Resultado de una sintesis ya escrita a disco."""

    output_path: Path
    piece: PgmxState
    sha256: str
    line_millings: tuple[LineMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()


# ============================================================================
# Public spec builders
# ============================================================================

def _strip_namespace(tag: str) -> str:
    """Devuelve el nombre local de un tag XML, sin su namespace."""

    return tag.split("}", 1)[-1] if "}" in tag else tag


def _compact_number(value: float) -> str:
    """Serializa un numero con el formato compacto que usamos en PGMX."""

    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.6f}".rstrip("0").rstrip(".")


def _xsi_type(element: ET.Element) -> str:
    """Lee el `xsi:type` de un nodo XML sin depender del prefijo exacto."""

    for key, value in element.attrib.items():
        if _strip_namespace(key).lower() == "type":
            return value or ""
    return ""


def _set_text(element: Optional[ET.Element], value) -> None:
    """Asigna texto a un nodo XML, tolerando `None`."""

    if element is not None:
        element.text = "" if value is None else str(value)


def _set_xmlns(element: Optional[ET.Element], prefix: str, uri: str) -> None:
    """Inyecta una declaracion `xmlns:prefix` en un nodo si existe."""

    if element is not None:
        element.set(f"xmlns:{prefix}", uri)


def _load_pgmx_archive(source_path: Path) -> tuple[ET.Element, dict[str, bytes], str]:
    """Abre un `.pgmx` como ZIP y devuelve root XML, entradas crudas y nombre del XML."""

    with zipfile.ZipFile(source_path) as zip_file:
        archive_entries = {name: zip_file.read(name) for name in zip_file.namelist()}
    xml_entry_name = next((name for name in archive_entries if name.lower().endswith(".xml")), "")
    if not xml_entry_name:
        raise ValueError(f"El archivo '{source_path}' no contiene una entrada XML.")
    xml_root = ET.fromstring(archive_entries[xml_entry_name].decode("utf-8", errors="ignore"))
    return xml_root, archive_entries, xml_entry_name


def _id_counter(root: ET.Element):
    """Genera IDs nuevos por encima del mayor ID/unsignedInt ya presente en el XML."""

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


def _toolpath_line_string(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    """Serializa un segmento recto de `ToolpathList` en el formato raw de Maestro."""

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


def _write_pgmx_zip(output_path: Path, xml_bytes: bytes, template_entries: dict[str, bytes], xml_entry_name: str) -> None:
    """Escribe un `.pgmx` preservando el resto de entradas del template ZIP."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epl_written = False
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(xml_entry_name, xml_bytes)
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
    """Normaliza namespaces y tipos XML para que Maestro acepte el `.pgmx`."""

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
    xml_text = xml_text.replace(
        '<Geometry i:type="a:WorkpieceBoxGeometry">',
        workpiece_geometry_decl,
    )
    xml_text = xml_text.replace(
        '<Value i:type="b:double">',
        variable_value_decl,
    )
    return xml_text.encode("utf-8")


def _safe_float(value, default: float) -> float:
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _safe_bool(value, default: bool) -> bool:
    raw = "" if value is None else str(value).strip().lower()
    if not raw:
        return default
    if raw in {"true", "1", "yes", "si", "sí"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    return default


def _finalize_synthesized_pgmx_xml_bytes(xml_bytes: bytes) -> bytes:
    finalized = _finalize_pgmx_xml_bytes(xml_bytes)
    xml_text = finalized.decode("utf-8")
    expressions_decl = f'<Expressions xmlns:a="{PARAMETRIC_NS}">'
    if "<Expressions>" in xml_text and expressions_decl not in xml_text:
        xml_text = xml_text.replace("<Expressions>", expressions_decl, 1)
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Property i:type="a:CompositeField">',
        lambda match: (
            f'<{match.group("prefix") or ""}Property i:type="a:CompositeField" '
            f'xmlns:a="{PARAMETRIC_NS}">'
        ),
        xml_text,
    )
    for element_name, namespace_uri in (
        ("ManufacturingFeature", MILLING_NS),
        ("Operation", MILLING_NS),
        ("GeomGeometry", GEOMETRY_NS),
    ):
        xml_text = re.sub(
            rf'<(?P<prefix>[A-Za-z_][\w.-]*:)?{element_name}(?P<attrs>[^>]*) i:type="a:(?P<dtype>[^"]+)"(?P<tail>[^>]*)>',
            lambda match: (
                match.group(0)
                if 'xmlns:a="' in match.group(0)
                else (
                    f'<{match.group("prefix") or ""}{element_name}'
                    f'{match.group("attrs")} i:type="a:{match.group("dtype")}"'
                    f' xmlns:a="{namespace_uri}"{match.group("tail")}>'
                )
            ),
            xml_text,
        )
    return xml_text.encode("utf-8")


def _text(node: Optional[ET.Element], path: str, default: str = "") -> str:
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return str(found.text).strip()


def _raw_text(node: Optional[ET.Element], path: str, default: str = "") -> str:
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return str(found.text)


def _normalize_execution_fields(value: Optional[str]) -> str:
    raw = (value or "HG").strip().upper().replace(" ", "")
    if not raw:
        return "HG"
    if any(letter not in "ABCDEFGH" for letter in raw):
        raise ValueError(
            "ExecutionFields invalido. Use letras entre A y H, por ejemplo: A, EF o HG."
        )
    if len(set(raw)) != len(raw):
        raise ValueError("ExecutionFields invalido. No debe repetir letras.")
    return raw


def _normalize_side_of_feature(value: Optional[str]) -> str:
    raw = (value or "Center").strip().lower()
    mapping = {
        "center": "Center",
        "centre": "Center",
        "central": "Center",
        "right": "Right",
        "derecha": "Right",
        "left": "Left",
        "izquierda": "Left",
    }
    if raw not in mapping:
        raise ValueError("SideOfFeature invalido. Valores admitidos: Center, Right, Left.")
    return mapping[raw]


def _normalize_approach_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("ApproachType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_approach_mode(value: Optional[str]) -> str:
    raw = (value or "Down").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "down": "Down",
        "vertical": "Down",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("ApproachMode invalido. Valores admitidos: Down o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_approach_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("ApproachArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def _normalize_retract_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("RetractType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_retract_mode(value: Optional[str]) -> str:
    raw = (value or "Up").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "up": "Up",
        "subida": "Up",
        "vertical": "Up",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("RetractMode invalido. Valores admitidos: Up o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_retract_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("RetractArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def build_milling_depth_spec(
    is_through: Optional[bool] = None,
    *,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
) -> MillingDepthSpec:
    """Construye un `MillingDepthSpec` reusable para Pasante/Extra/Profundidad.

    Reglas:
    - si no se pasa nada, devuelve el default observado en Maestro
    - si `is_through=True`, `extra_depth` representa `Extra`
    - si `is_through=False`, `target_depth` es obligatorio y `extra_depth` no aplica
    """

    has_explicit_configuration = any(value is not None for value in (is_through, target_depth, extra_depth))
    if not has_explicit_configuration:
        return MillingDepthSpec()

    normalized_is_through = (target_depth is None) if is_through is None else bool(is_through)
    if normalized_is_through:
        extra_value = 0.0 if extra_depth is None else float(extra_depth)
        if extra_value < -1e-9:
            raise ValueError("ExtraDepth no puede ser negativo.")
        return MillingDepthSpec(is_through=True, target_depth=None, extra_depth=extra_value)

    if target_depth is None:
        raise ValueError("Para un fresado no pasante hay que indicar target_depth.")
    target_depth_value = float(target_depth)
    if target_depth_value <= 0.0:
        raise ValueError("La profundidad no pasante debe ser mayor que cero.")
    extra_value = 0.0 if extra_depth is None else float(extra_depth)
    if not math.isclose(extra_value, 0.0, abs_tol=1e-9):
        raise ValueError("ExtraDepth solo aplica a fresados pasantes.")
    return MillingDepthSpec(is_through=False, target_depth=target_depth_value, extra_depth=0.0)


def build_approach_spec(
    enabled: Optional[bool] = None,
    *,
    approach_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
) -> ApproachSpec:
    """Construye un `ApproachSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Approach` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, approach_type, mode, radius_multiplier, speed, arc_side)
    )
    if not has_explicit_configuration:
        return ApproachSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Down"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return ApproachSpec(
        is_enabled=is_enabled,
        approach_type=_normalize_approach_type(approach_type or "Line"),
        mode=_normalize_approach_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_approach_arc_side(arc_side or "Automatic"),
    )


def build_retract_spec(
    enabled: Optional[bool] = None,
    *,
    retract_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
    overlap: Optional[float] = None,
) -> RetractSpec:
    """Construye un `RetractSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Retract` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, retract_type, mode, radius_multiplier, speed, arc_side, overlap)
    )
    if not has_explicit_configuration:
        return RetractSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Up"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return RetractSpec(
        is_enabled=is_enabled,
        retract_type=_normalize_retract_type(retract_type or "Line"),
        mode=_normalize_retract_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_retract_arc_side(arc_side or "Automatic"),
        overlap=0.0 if overlap is None else float(overlap),
    )


def _normalize_approach_spec(approach: Optional[ApproachSpec]) -> ApproachSpec:
    if approach is None:
        return ApproachSpec()
    return build_approach_spec(
        enabled=approach.is_enabled,
        approach_type=approach.approach_type,
        mode=approach.mode,
        radius_multiplier=approach.radius_multiplier,
        speed=approach.speed,
        arc_side=approach.arc_side,
    )


def _normalize_retract_spec(retract: Optional[RetractSpec]) -> RetractSpec:
    if retract is None:
        return RetractSpec()
    return build_retract_spec(
        enabled=retract.is_enabled,
        retract_type=retract.retract_type,
        mode=retract.mode,
        radius_multiplier=retract.radius_multiplier,
        speed=retract.speed,
        arc_side=retract.arc_side,
        overlap=retract.overlap,
    )


def _normalize_milling_depth_spec(depth_spec: Optional[MillingDepthSpec]) -> MillingDepthSpec:
    if depth_spec is None:
        return MillingDepthSpec()
    return build_milling_depth_spec(
        is_through=depth_spec.is_through,
        target_depth=depth_spec.target_depth,
        extra_depth=depth_spec.extra_depth,
    )


def _normalize_line_milling_spec(line_milling: LineMillingSpec) -> LineMillingSpec:
    return replace(
        line_milling,
        side_of_feature=_normalize_side_of_feature(line_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(line_milling.depth_spec),
        approach=_normalize_approach_spec(line_milling.approach),
        retract=_normalize_retract_spec(line_milling.retract),
    )


def _normalize_polyline_points(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    normalized = tuple((float(point[0]), float(point[1])) for point in points)
    if len(normalized) < 2:
        raise ValueError("Una polilinea abierta necesita al menos 2 puntos.")
    for start_point, end_point in zip(normalized, normalized[1:]):
        if math.isclose(start_point[0], end_point[0], abs_tol=1e-9) and math.isclose(
            start_point[1], end_point[1], abs_tol=1e-9
        ):
            raise ValueError("La polilinea no puede contener segmentos de longitud cero.")
    return normalized


def _normalize_polyline_milling_spec(polyline_milling: PolylineMillingSpec) -> PolylineMillingSpec:
    return replace(
        polyline_milling,
        points=_normalize_polyline_points(polyline_milling.points),
        side_of_feature=_normalize_side_of_feature(polyline_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(polyline_milling.depth_spec),
        approach=_normalize_approach_spec(polyline_milling.approach),
        retract=_normalize_retract_spec(polyline_milling.retract),
    )


def _feature_depth_value(state: PgmxState, spec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    if depth_spec.target_depth > state.depth + 1e-9:
        raise ValueError("La profundidad del fresado no pasante no puede superar el espesor de la pieza.")
    return depth_spec.target_depth


def _toolpath_cut_z(state: PgmxState, spec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return -depth_spec.extra_depth
    return state.depth - _feature_depth_value(state, spec)


def _feature_bottom_condition_type(spec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return "a:ThroughMillingBottom" if depth_spec.is_through else "a:GeneralMillingBottom"


def _operation_overcut_length(spec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return depth_spec.extra_depth if depth_spec.is_through else 0.0


def _uses_feature_depth_expressions(spec) -> bool:
    return _normalize_milling_depth_spec(spec.depth_spec).is_through


def _qname(namespace: str, local_name: str) -> str:
    return f"{{{namespace}}}{local_name}"


def _append_node(
    parent: ET.Element,
    namespace: str,
    local_name: str,
    text: Optional[str] = None,
    attrib: Optional[dict[str, str]] = None,
) -> ET.Element:
    node = ET.SubElement(parent, _qname(namespace, local_name), attrib or {})
    if text is not None:
        node.text = text
    return node


def _append_key(parent: ET.Element, key_id: str, object_type: str) -> ET.Element:
    key = _append_node(parent, UTILITY_NS, "Key")
    _append_node(key, UTILITY_NS, "ID", key_id)
    _append_node(key, UTILITY_NS, "ObjectType", object_type)
    return key


def _append_reference_key(parent: ET.Element, key_id: str, object_type: str) -> ET.Element:
    key = _append_node(parent, UTILITY_NS, "ReferenceKey")
    _append_node(key, UTILITY_NS, "ID", key_id)
    _append_node(key, UTILITY_NS, "ObjectType", object_type)
    return key


def _append_object_ref(
    parent: ET.Element,
    namespace: str,
    local_name: str,
    ref_id: str,
    object_type: str,
    *,
    include_name: bool = False,
    name_text: str = "",
) -> ET.Element:
    ref = _append_node(parent, namespace, local_name)
    _append_node(ref, UTILITY_NS, "ID", ref_id)
    _append_node(ref, UTILITY_NS, "ObjectType", object_type)
    if include_name:
        _append_node(ref, UTILITY_NS, "Name", name_text)
    return ref


def _append_blank_name(parent: ET.Element) -> ET.Element:
    return _append_node(parent, UTILITY_NS, "Name", "")


def _build_line_description(start_x: float, start_y: float, end_x: float, end_y: float) -> str:
    return _build_maestro_line_serialization((start_x, start_y, 0.0), (end_x, end_y, 0.0))


def _build_open_polyline_descriptions(points: Sequence[tuple[float, float]]) -> tuple[str, ...]:
    normalized_points = _normalize_polyline_points(points)
    return tuple(
        _build_line_description(start_point[0], start_point[1], end_point[0], end_point[1])
        for start_point, end_point in zip(normalized_points, normalized_points[1:])
    )


def _build_toolpath_description(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    return _build_maestro_line_serialization(start_point, end_point)


def _format_maestro_number(value: float) -> str:
    number = float(value)
    if math.isclose(number, 0.0, abs_tol=1e-15):
        return "0"
    if number.is_integer():
        return str(int(number))
    return format(number, ".17g")


def _format_maestro_orientation_number(value: float) -> str:
    number = float(value)
    if number == 0.0:
        return "-0" if math.copysign(1.0, number) < 0.0 else "0"
    if number.is_integer():
        return str(int(number))
    text = format(number, ".17g")
    if "e" not in text and "E" not in text:
        return text
    mantissa, exponent = text.lower().split("e", 1)
    sign = exponent[:1]
    digits = exponent[1:].rjust(3, "0")
    return f"{mantissa}e{sign}{digits}"


def _normalize_curve_serialization_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in str(text).strip().splitlines())


def _build_maestro_line_serialization(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    dz = end_point[2] - start_point[2]
    length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if length <= 1e-9:
        raise ValueError("No se puede serializar un segmento de longitud cero.")

    return (
        f"8 0 {_format_maestro_number(length)}\n"
        f"1 {_format_maestro_number(start_point[0])} {_format_maestro_number(start_point[1])} {_format_maestro_number(start_point[2])} "
        f"{_format_maestro_number(dx / length)} {_format_maestro_number(dy / length)} {_format_maestro_number(dz / length)} \n"
    )


def _line_right_normal(start_x: float, start_y: float, end_x: float, end_y: float) -> tuple[float, float]:
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    length = math.hypot(delta_x, delta_y)
    if length <= 1e-9:
        raise ValueError("No se puede sintetizar un fresado lineal con longitud cero.")
    return (delta_y / length, -delta_x / length)


def _line_unit_direction(start_x: float, start_y: float, end_x: float, end_y: float) -> tuple[float, float]:
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    length = math.hypot(delta_x, delta_y)
    if length <= 1e-9:
        raise ValueError("No se puede sintetizar un fresado lineal con longitud cero.")
    return (delta_x / length, delta_y / length)


def _resolve_toolpath_direction(
    toolpath_start: tuple[float, float],
    toolpath_end: tuple[float, float],
    direction: Optional[tuple[float, float]] = None,
) -> tuple[float, float]:
    if direction is not None:
        return direction
    return _line_unit_direction(
        toolpath_start[0],
        toolpath_start[1],
        toolpath_end[0],
        toolpath_end[1],
    )


def _preferred_side_for_arc(side_of_feature: str, arc_side: str) -> str:
    normalized_side = _normalize_side_of_feature(side_of_feature)
    if normalized_side != "Center":
        return normalized_side
    normalized_arc_side = _normalize_approach_arc_side(arc_side)
    if normalized_arc_side in {"Left", "Right"}:
        return normalized_arc_side
    return "Right"


def _side_normal_for_direction(
    direction_x: float,
    direction_y: float,
    side_of_feature: str,
    arc_side: str,
) -> tuple[tuple[float, float], float]:
    right_normal = (direction_y, -direction_x)
    left_normal = (-right_normal[0], -right_normal[1])
    preferred_side = _preferred_side_for_arc(side_of_feature, arc_side)
    if preferred_side == "Left":
        return left_normal, 1.0
    return right_normal, -1.0


def _build_vertical_toolpath_curve(
    x_value: float,
    y_value: float,
    start_z: float,
    end_z: float,
) -> _CurveSpec:
    # Maestro mantiene un toolpath vertical en Approach/Lift aunque la estrategia este deshabilitada.
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (x_value, y_value, start_z),
            (x_value, y_value, end_z),
        )
    )


def _quote_arc_radius(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * max(radius_multiplier - 1.0, 0.0)


def _linear_lead_distance(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * radius_multiplier


def _dominant_component_sign_2d(vector: tuple[float, float]) -> float:
    x_value, y_value = vector
    if abs(x_value) >= abs(y_value):
        if not math.isclose(x_value, 0.0, abs_tol=1e-15):
            return 1.0 if x_value > 0.0 else -1.0
    if not math.isclose(y_value, 0.0, abs_tol=1e-15):
        return 1.0 if y_value > 0.0 else -1.0
    return 1.0


def _build_oriented_maestro_arc_basis(
    direction: tuple[float, float],
    side_normal: tuple[float, float],
    normal_z: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    # Maestro serializa estos arcos con una base 3D orientada y pequeños epsilon
    # en algunos componentes. Mantener esta estructura ayuda a que el XML sintetizado
    # se parezca mas al guardado manualmente desde Maestro.
    epsilon = math.ulp(0.5)
    direction_x, direction_y = direction
    side_x, side_y = side_normal
    u_vector = (
        0.0 if math.isclose(side_x, 0.0, abs_tol=1e-15) else (normal_z * side_x),
        normal_z * side_y,
        epsilon * normal_z,
    )
    v_vector = (
        -normal_z * direction_x,
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-normal_z * direction_y),
        0.0,
    )
    normal_vector = (
        (-0.0 if normal_z > 0.0 else 0.0)
        if math.isclose(direction_y, 0.0, abs_tol=1e-15)
        else (epsilon * direction_y),
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-epsilon * direction_x),
        normal_z,
    )
    return normal_vector, u_vector, v_vector


def _build_quote_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. bajada vertical en el punto inicial del acercamiento
    # 2. cuarto de arco en la cota de corte hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = entry_point[0] + (side_normal[0] * arc_radius)
    center_y = entry_point[1] + (side_normal[1] * arc_radius)
    plunge_x = center_x - (direction_x * arc_radius)
    plunge_y = center_y - (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = (1.5 * math.pi) if normal_z < 0.0 else (0.5 * math.pi)
    end_angle = (2.0 * math.pi) if normal_z < 0.0 else math.pi

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, cut_z),
            ),
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
        ]
    )


def _build_down_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Down:
    # 1. bajada vertical hasta `cut_z + radio`
    # 2. cuarto de arco en un plano vertical hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    right_normal_x = direction_y
    right_normal_y = -direction_x
    pre_entry_z = cut_z + arc_radius
    plunge_x = entry_point[0] - (direction_x * arc_radius)
    plunge_y = entry_point[1] - (direction_y * arc_radius)

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, pre_entry_z),
            ),
            _build_oriented_maestro_arc_serialization(
                1.5 * math.pi,
                2.0 * math.pi,
                (entry_point[0], entry_point[1], pre_entry_z),
                (right_normal_x, right_normal_y, 0.0),
                (0.0, 0.0, -1.0),
                (direction_x, direction_y, 0.0),
                arc_radius,
                z_value=pre_entry_z,
            ),
        ]
    )


def _build_down_line_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Down:
    # una sola bajada oblicua desde un punto previo desplazado
    # en la direccion opuesta al avance del toolpath.
    pre_entry_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    pre_entry_x = entry_point[0] - (direction_x * pre_entry_distance)
    pre_entry_y = entry_point[1] - (direction_y * pre_entry_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (pre_entry_x, pre_entry_y, clearance_z),
            (entry_point[0], entry_point[1], cut_z),
        )
    )


def _build_up_line_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Up:
    # una sola subida oblicua hacia un punto final desplazado
    # sobre la direccion de salida del toolpath.
    post_exit_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    post_exit_x = exit_point[0] + (direction_x * post_exit_distance)
    post_exit_y = exit_point[1] + (direction_y * post_exit_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (exit_point[0], exit_point[1], cut_z),
            (post_exit_x, post_exit_y, clearance_z),
        )
    )


def _build_quote_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. cuarto de arco en la cota de corte desde el punto de salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = exit_point[0] + (side_normal[0] * arc_radius)
    center_y = exit_point[1] + (side_normal[1] * arc_radius)
    lift_x = center_x + (direction_x * arc_radius)
    lift_y = center_y + (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = 0.0 if normal_z < 0.0 else math.pi
    end_angle = (0.5 * math.pi) if normal_z < 0.0 else (1.5 * math.pi)

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, cut_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _build_up_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Up:
    # 1. cuarto de arco en un plano vertical desde la salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    plane_normal = (
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else direction_y,
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-direction_x),
    )
    basis_sign = _dominant_component_sign_2d(plane_normal)
    center_z = cut_z + arc_radius
    lift_x = exit_point[0] + (direction_x * arc_radius)
    lift_y = exit_point[1] + (direction_y * arc_radius)
    lift_z = center_z
    tangent_vector = (
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-basis_sign * direction_x),
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-basis_sign * direction_y),
        0.0,
    )

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                math.pi if basis_sign > 0.0 else 0.0,
                (1.5 * math.pi) if basis_sign > 0.0 else (0.5 * math.pi),
                exit_point,
                (plane_normal[0], plane_normal[1], 0.0),
                (0.0, 0.0, basis_sign),
                tangent_vector,
                arc_radius,
                z_value=center_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, lift_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _polyline_endpoint_directions(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    normalized_points = _normalize_polyline_points(points)
    start_direction = _line_unit_direction(
        normalized_points[0][0],
        normalized_points[0][1],
        normalized_points[1][0],
        normalized_points[1][1],
    )
    end_direction = _line_unit_direction(
        normalized_points[-2][0],
        normalized_points[-2][1],
        normalized_points[-1][0],
        normalized_points[-1][1],
    )
    return start_direction, end_direction


def _offset_factor(side_of_feature: str) -> float:
    normalized = _normalize_side_of_feature(side_of_feature)
    return {
        "Left": -1.0,
        "Center": 0.0,
        "Right": 1.0,
    }[normalized]


def _offset_line_for_toolpath(spec: _HydratedLineMillingSpec) -> tuple[tuple[float, float], tuple[float, float]]:
    right_x, right_y = _line_right_normal(spec.start_x, spec.start_y, spec.end_x, spec.end_y)
    offset_distance = _offset_factor(spec.side_of_feature) * (spec.tool_width / 2.0)
    offset_x = right_x * offset_distance
    offset_y = right_y * offset_distance
    return (
        (spec.start_x + offset_x, spec.start_y + offset_y),
        (spec.end_x + offset_x, spec.end_y + offset_y),
    )


def _offset_point(point: tuple[float, float], offset_x: float, offset_y: float) -> tuple[float, float]:
    return (point[0] + offset_x, point[1] + offset_y)


def _intersect_lines(
    point_a: tuple[float, float],
    direction_a: tuple[float, float],
    point_b: tuple[float, float],
    direction_b: tuple[float, float],
    tolerance: float = 1e-9,
) -> Optional[tuple[float, float]]:
    denominator = (direction_a[0] * direction_b[1]) - (direction_a[1] * direction_b[0])
    if math.isclose(denominator, 0.0, abs_tol=tolerance):
        return None
    delta_x = point_b[0] - point_a[0]
    delta_y = point_b[1] - point_a[1]
    factor = ((delta_x * direction_b[1]) - (delta_y * direction_b[0])) / denominator
    return (
        point_a[0] + (direction_a[0] * factor),
        point_a[1] + (direction_a[1] * factor),
    )


def _points_close_2d(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    tolerance: float = 1e-9,
) -> bool:
    return math.isclose(point_a[0], point_b[0], abs_tol=tolerance) and math.isclose(
        point_a[1], point_b[1], abs_tol=tolerance
    )


def _cross_2d(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> float:
    return (vector_a[0] * vector_b[1]) - (vector_a[1] * vector_b[0])


def _normalize_positive_angle(angle: float) -> float:
    normalized = math.fmod(angle, 2.0 * math.pi)
    if normalized < 0.0:
        normalized += 2.0 * math.pi
    if math.isclose(normalized, 2.0 * math.pi, abs_tol=1e-12):
        return 0.0
    return normalized


def _point_to_maestro_basis_angle(
    center_point: tuple[float, float],
    point: tuple[float, float],
    normal_z: float,
) -> float:
    relative_x = point[0] - center_point[0]
    relative_y = point[1] - center_point[1]
    return _normalize_positive_angle(math.atan2(relative_y * normal_z, relative_x))


def _build_maestro_arc_serialization(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    center_point: tuple[float, float],
    normal_z: float,
    z_value: float = 0.0,
) -> str:
    radius = math.hypot(start_point[0] - center_point[0], start_point[1] - center_point[1])
    if radius <= 1e-9:
        raise ValueError("No se puede serializar un arco de radio cero.")

    start_angle = _point_to_maestro_basis_angle(center_point, start_point, normal_z)
    end_angle = _point_to_maestro_basis_angle(center_point, end_point, normal_z)

    return (
        f"8 {_format_maestro_number(start_angle)} {_format_maestro_number(end_angle)}\n"
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(z_value)} "
        f"0 0 {_format_maestro_number(normal_z)} 1 0 0 0 {_format_maestro_number(normal_z)} 0 {_format_maestro_number(radius)} \n"
    )


def _build_oriented_maestro_arc_serialization(
    start_angle: float,
    end_angle: float,
    center_point: tuple[float, float],
    normal_vector: tuple[float, float, float],
    u_vector: tuple[float, float, float],
    v_vector: tuple[float, float, float],
    radius: float,
    z_value: float = 0.0,
) -> str:
    if radius <= 1e-9:
        raise ValueError("No se puede serializar un arco de radio cero.")
    return (
        f"8 {_format_maestro_number(start_angle)} {_format_maestro_number(end_angle)}\n"
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(z_value)} "
        f"{_format_maestro_orientation_number(normal_vector[0])} {_format_maestro_orientation_number(normal_vector[1])} {_format_maestro_orientation_number(normal_vector[2])} "
        f"{_format_maestro_orientation_number(u_vector[0])} {_format_maestro_orientation_number(u_vector[1])} {_format_maestro_orientation_number(u_vector[2])} "
        f"{_format_maestro_orientation_number(v_vector[0])} {_format_maestro_orientation_number(v_vector[1])} {_format_maestro_orientation_number(v_vector[2])} "
        f"{_format_maestro_number(radius)} \n"
    )


def _build_polyline_offset_segments(
    spec: _HydratedPolylineMillingSpec,
) -> tuple[float, list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]]]:
    offset_distance = _offset_factor(spec.side_of_feature) * (spec.tool_width / 2.0)
    offset_segments: list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]] = []
    for start_point, end_point in zip(spec.points, spec.points[1:]):
        direction = _line_unit_direction(start_point[0], start_point[1], end_point[0], end_point[1])
        right_x, right_y = _line_right_normal(start_point[0], start_point[1], end_point[0], end_point[1])
        offset_x = right_x * offset_distance
        offset_y = right_y * offset_distance
        offset_segments.append(
            (
                _offset_point(start_point, offset_x, offset_y),
                _offset_point(end_point, offset_x, offset_y),
                direction,
            )
        )

    return offset_distance, offset_segments


def _build_generated_polyline_trajectory_curve(
    state: PgmxState,
    spec: _HydratedPolylineMillingSpec,
) -> tuple[_CurveSpec, tuple[float, float], tuple[float, float]]:
    offset_distance, offset_segments = _build_polyline_offset_segments(spec)
    cut_z = _toolpath_cut_z(state, spec)
    if math.isclose(offset_distance, 0.0, abs_tol=1e-9):
        return (
            _composite_curve_spec(
                [
                    _build_toolpath_description(
                        (start_point[0], start_point[1], cut_z),
                        (end_point[0], end_point[1], cut_z),
                    )
                    for start_point, end_point in zip(spec.points, spec.points[1:])
                ]
            ),
            spec.points[0],
            spec.points[-1],
        )

    side_sign = 1.0 if offset_distance > 0.0 else -1.0
    normal_z = side_sign
    member_serializations: list[str] = []
    current_point = offset_segments[0][0]

    for index, (previous_segment, next_segment) in enumerate(zip(offset_segments, offset_segments[1:])):
        previous_start, previous_end, previous_direction = previous_segment
        next_start, _, next_direction = next_segment
        turn_cross = _cross_2d(previous_direction, next_direction)

        if math.isclose(turn_cross, 0.0, abs_tol=1e-9):
            if not _points_close_2d(current_point, previous_end):
                member_serializations.append(
                    _build_toolpath_description(
                        (current_point[0], current_point[1], cut_z),
                        (previous_end[0], previous_end[1], cut_z),
                    )
                )
            current_point = next_start
            continue

        is_outer_corner = (side_sign * turn_cross) > 0.0
        if is_outer_corner:
            if not _points_close_2d(current_point, previous_end):
                member_serializations.append(
                    _build_toolpath_description(
                        (current_point[0], current_point[1], cut_z),
                        (previous_end[0], previous_end[1], cut_z),
                    )
                )
            member_serializations.append(
                _build_maestro_arc_serialization(
                    previous_end,
                    next_start,
                    spec.points[index + 1],
                    normal_z,
                    z_value=cut_z,
                )
            )
            current_point = next_start
            continue

        intersection = _intersect_lines(previous_start, previous_direction, next_start, next_direction)
        if intersection is None:
            if _points_close_2d(previous_end, next_start):
                intersection = previous_end
            else:
                intersection = (
                    (previous_end[0] + next_start[0]) / 2.0,
                    (previous_end[1] + next_start[1]) / 2.0,
                )

        if not _points_close_2d(current_point, intersection):
            member_serializations.append(
                _build_toolpath_description(
                    (current_point[0], current_point[1], cut_z),
                    (intersection[0], intersection[1], cut_z),
                )
            )
        current_point = intersection

    end_point = offset_segments[-1][1]
    if not _points_close_2d(current_point, end_point):
        member_serializations.append(
            _build_toolpath_description(
                (current_point[0], current_point[1], cut_z),
                (end_point[0], end_point[1], cut_z),
            )
        )

    return _composite_curve_spec(member_serializations), offset_segments[0][0], end_point


def _parse_line_serialization(text: str) -> Optional[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    header = lines[0].split()
    body = lines[1].split()
    if len(header) < 3 or len(body) < 7 or body[0] != "1":
        return None
    try:
        length = float(header[2])
        start_x = float(body[1])
        start_y = float(body[2])
        start_z = float(body[3])
        dir_x = float(body[4])
        dir_y = float(body[5])
        dir_z = float(body[6])
    except ValueError:
        return None
    end_point = (
        start_x + (dir_x * length),
        start_y + (dir_y * length),
        start_z + (dir_z * length),
    )
    return ((start_x, start_y, start_z), end_point)


def _matches_line_geometry(template: dict[str, object], spec: LineMillingSpec, tolerance: float = 1e-6) -> bool:
    parsed = _parse_line_serialization(str(template.get("geometry_serialization") or ""))
    if parsed is None:
        return False
    start, end = parsed
    expected = (spec.start_x, spec.start_y, 0.0, spec.end_x, spec.end_y, 0.0)
    direct = (start[0], start[1], start[2], end[0], end[1], end[2])
    reverse = (end[0], end[1], end[2], start[0], start[1], start[2])

    def close(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
        return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(a, b))

    return close(direct, expected) or close(reverse, expected)


def _curve_spec_points(curve_spec: _CurveSpec) -> Optional[tuple[tuple[float, float, float], ...]]:
    if curve_spec.geometry_type == "GeomTrimmedCurve":
        if curve_spec.serialization is None:
            return None
        parsed = _parse_line_serialization(curve_spec.serialization)
        if parsed is None:
            return None
        return (parsed[0], parsed[1])

    if curve_spec.geometry_type != "GeomCompositeCurve":
        return None

    points: list[tuple[float, float, float]] = []
    for member_serialization in curve_spec.member_serializations:
        parsed = _parse_line_serialization(member_serialization)
        if parsed is None:
            return None
        start_point, end_point = parsed
        if not points:
            points.append(start_point)
        points.append(end_point)
    return tuple(points)


def _matches_polyline_geometry(template: dict[str, object], spec: PolylineMillingSpec, tolerance: float = 1e-6) -> bool:
    geometry_curve = template.get("geometry_curve")
    if not isinstance(geometry_curve, _CurveSpec):
        return False
    parsed_points = _curve_spec_points(geometry_curve)
    if parsed_points is None:
        return False
    expected_points = tuple((point[0], point[1], 0.0) for point in spec.points)
    if len(parsed_points) != len(expected_points):
        return False
    return all(
        math.isclose(parsed_point[0], expected_point[0], abs_tol=tolerance)
        and math.isclose(parsed_point[1], expected_point[1], abs_tol=tolerance)
        and math.isclose(parsed_point[2], expected_point[2], abs_tol=tolerance)
        for parsed_point, expected_point in zip(parsed_points, expected_points)
    )


def _extract_depth_spec_from_template(
    feature: ET.Element,
    operation: ET.Element,
    matching_expressions: Sequence[ET.Element],
) -> MillingDepthSpec:
    expression_values = {
        _text(node, "./{*}Property/{*}InnerField/{*}Name"): _text(node, "./{*}Value")
        for node in matching_expressions
        if _text(node, "./{*}Property/{*}Name") == "Depth"
    }
    bottom_condition_type = _xsi_type(feature.find("./{*}BottomCondition"))
    overcut_length = _safe_float(_text(operation, "./{*}OvercutLength"), 0.0)
    if "ThroughMillingBottom" in bottom_condition_type or (
        expression_values.get("StartDepth") == "dz1" and expression_values.get("EndDepth") == "dz1"
    ):
        return build_milling_depth_spec(is_through=True, extra_depth=overcut_length)

    start_depth = _safe_float(_text(feature, "./{*}Depth/{*}StartDepth"), 0.0)
    end_depth = _safe_float(_text(feature, "./{*}Depth/{*}EndDepth"), 0.0)
    if not math.isclose(start_depth, end_depth, abs_tol=1e-6):
        raise ValueError("La plantilla usa profundidades distintas para StartDepth/EndDepth; caso no soportado aun.")
    return build_milling_depth_spec(is_through=False, target_depth=start_depth)


def _can_hydrate_exact_serialization(template: dict[str, object], spec: LineMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    requested_side = _normalize_side_of_feature(spec.side_of_feature)
    source_side = str(template["side_of_feature"])
    if requested_side != source_side:
        return False
    source_approach = _normalize_approach_spec(template.get("approach") if isinstance(template.get("approach"), ApproachSpec) else None)
    requested_approach = _normalize_approach_spec(spec.approach)
    if source_approach != requested_approach:
        return False
    source_retract = _normalize_retract_spec(template.get("retract") if isinstance(template.get("retract"), RetractSpec) else None)
    requested_retract = _normalize_retract_spec(spec.retract)
    if source_retract != requested_retract:
        return False
    if not _matches_line_geometry(template, spec):
        return False
    if requested_side == "Center":
        return True

    source_tool_width = float(template["tool_width"])
    source_tool_id = str(template["tool_id"])
    source_tool_name = str(template["tool_name"])
    return (
        math.isclose(spec.tool_width, source_tool_width, abs_tol=1e-6)
        and spec.tool_id == source_tool_id
        and spec.tool_name == source_tool_name
    )


def _can_hydrate_exact_polyline_serialization(template: dict[str, object], spec: PolylineMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    requested_side = _normalize_side_of_feature(spec.side_of_feature)
    source_side = str(template["side_of_feature"])
    if requested_side != source_side:
        return False
    source_approach = _normalize_approach_spec(template.get("approach") if isinstance(template.get("approach"), ApproachSpec) else None)
    requested_approach = _normalize_approach_spec(spec.approach)
    if source_approach != requested_approach:
        return False
    source_retract = _normalize_retract_spec(template.get("retract") if isinstance(template.get("retract"), RetractSpec) else None)
    requested_retract = _normalize_retract_spec(spec.retract)
    if source_retract != requested_retract:
        return False
    if not _matches_polyline_geometry(template, spec):
        return False
    if requested_side == "Center":
        return True

    source_tool_width = float(template["tool_width"])
    source_tool_id = str(template["tool_id"])
    source_tool_name = str(template["tool_name"])
    return (
        math.isclose(spec.tool_width, source_tool_width, abs_tol=1e-6)
        and spec.tool_id == source_tool_id
        and spec.tool_name == source_tool_name
    )


def _trimmed_curve_spec(serialization: str) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomTrimmedCurve",
        serialization=_normalize_curve_serialization_text(serialization),
    )


def _composite_curve_spec(
    member_serializations: Sequence[str],
    member_keys: Sequence[str] = (),
) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomCompositeCurve",
        member_keys=tuple(member_keys),
        member_serializations=tuple(_normalize_curve_serialization_text(serialization) for serialization in member_serializations),
    )


def _build_curve_holder(
    local_name: str,
    curve_spec: _CurveSpec,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    curve = ET.Element(
        _qname(BASE_MODEL_NS, local_name),
        {f"{{{XSI_NS}}}type": f"c:{curve_spec.geometry_type}"},
    )
    _set_xmlns(curve, "c", GEOMETRY_NS)
    _append_key(curve, "0", "System.Object")
    _append_blank_name(curve)
    _append_node(curve, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(curve, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    if curve_spec.geometry_type == "GeomTrimmedCurve":
        if curve_spec.serialization is None:
            raise ValueError("La curva GeomTrimmedCurve requiere una serializacion raw.")
        _append_node(curve, GEOMETRY_NS, "_serializationGeometryDescription", curve_spec.serialization)
        return curve

    if curve_spec.geometry_type != "GeomCompositeCurve":
        raise ValueError(f"Tipo de curva no soportado: {curve_spec.geometry_type}")

    member_keys = tuple(curve_spec.member_keys or generated_member_keys)
    if not curve_spec.member_serializations:
        raise ValueError("La curva GeomCompositeCurve requiere al menos un miembro serializado.")
    if len(member_keys) != len(curve_spec.member_serializations):
        raise ValueError("La curva GeomCompositeCurve requiere una clave por cada miembro serializado.")

    keys_group = _append_node(curve, GEOMETRY_NS, "_serializingKeys")
    members_group = _append_node(curve, GEOMETRY_NS, "_serializingMembers")
    for key_id, member_serialization in zip(member_keys, curve_spec.member_serializations):
        _append_node(keys_group, ARRAYS_NS, "unsignedInt", key_id)
        _append_node(members_group, ARRAYS_NS, "string", member_serialization)
    return curve


def _build_vector_holder(local_name: str, x_value: float, y_value: float, z_value: float) -> ET.Element:
    vector = ET.Element(_qname(BASE_MODEL_NS, local_name))
    _append_key(vector, "0", "System.Object")
    _append_blank_name(vector)
    _append_node(vector, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(vector, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    _append_node(vector, GEOMETRY_NS, "_x", _compact_number(x_value))
    _append_node(vector, GEOMETRY_NS, "_y", _compact_number(y_value))
    _append_node(vector, GEOMETRY_NS, "_z", _compact_number(z_value))
    _append_node(vector, GEOMETRY_NS, "XRotation", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(vector, GEOMETRY_NS, "ZRotation", attrib={f"{{{XSI_NS}}}nil": "true"})
    return vector


def _build_start_point(x_value: float, y_value: float, z_value: float) -> ET.Element:
    start_point = ET.Element(_qname(PGMX_NS, "StartPoint"))
    _append_key(start_point, "0", "System.Object")
    _append_blank_name(start_point)
    _append_node(start_point, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(start_point, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    _append_node(start_point, GEOMETRY_NS, "_x", _compact_number(x_value))
    _append_node(start_point, GEOMETRY_NS, "_y", _compact_number(y_value))
    _append_node(start_point, GEOMETRY_NS, "_z", _compact_number(z_value))
    return start_point


def _build_identity_profile_placement() -> ET.Element:
    placement = ET.Element(_qname(PGMX_NS, "Placement"))
    _append_key(placement, "0", "System.Object")
    _append_blank_name(placement)
    _append_node(placement, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(placement, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    _append_node(placement, GEOMETRY_NS, "_xN", "0")
    _append_node(placement, GEOMETRY_NS, "_xP", "0")
    _append_node(placement, GEOMETRY_NS, "_xVx", "1")
    _append_node(placement, GEOMETRY_NS, "_yN", "0")
    _append_node(placement, GEOMETRY_NS, "_yP", "0")
    _append_node(placement, GEOMETRY_NS, "_yVx", "0")
    _append_node(placement, GEOMETRY_NS, "_zN", "1")
    _append_node(placement, GEOMETRY_NS, "_zP", "0")
    _append_node(placement, GEOMETRY_NS, "_zVx", "-0")
    return placement


def _find_plane_ref(root: ET.Element, plane_name: str) -> tuple[str, str]:
    planes = root.find("./{*}Planes")
    if planes is None:
        raise ValueError("La plantilla no contiene Planes.")
    for plane in list(planes):
        plane_type = _text(plane, "./{*}Type") or _text(plane, "./{*}Name")
        if plane_type == plane_name:
            return (
                _text(plane, "./{*}Key/{*}ID"),
                _text(plane, "./{*}Key/{*}ObjectType"),
            )
    raise ValueError(f"La plantilla no contiene el plano '{plane_name}'.")


def _reserve_ids(root: ET.Element, count: int, preferred_start: Optional[int] = None) -> list[str]:
    first_default_id = int(next(_id_counter(root)))
    start_id = first_default_id if preferred_start is None else max(first_default_id, preferred_start)
    return [str(start_id + offset) for offset in range(count)]


def _extract_line_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_archive(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomTrimmedCurve" in _xsi_type(node)
        ),
        None,
    )
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "GeneralProfileFeature" in _xsi_type(node)
        ),
        None,
    )
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado lineal compatible.")

    def extract_toolpath_curve(toolpath: ET.Element) -> _CurveSpec:
        basic_curve = toolpath.find("./{*}BasicCurve")
        curve_type = _xsi_type(basic_curve)
        if "GeomCompositeCurve" in curve_type:
            return _composite_curve_spec(
                [
                    member.text or ""
                    for member in basic_curve.findall("./{*}_serializingMembers/{*}string")
                ],
                [
                    (key.text or "").strip()
                    for key in basic_curve.findall("./{*}_serializingKeys/{*}unsignedInt")
                ],
            )
        return _trimmed_curve_spec(_raw_text(basic_curve, "./{*}_serializationGeometryDescription"))

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): extract_toolpath_curve(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
    }
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id

    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(feature, operation, matching_expressions),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "approach": build_approach_spec(
            enabled=_safe_bool(_text(operation, "./{*}Approach/{*}IsEnabled"), False),
            approach_type=_text(operation, "./{*}Approach/{*}ApproachType", "Line"),
            mode=_text(operation, "./{*}Approach/{*}ApproachMode", "Down"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Approach/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Approach/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Approach/{*}ApproachArcSide", "Automatic"),
        ),
        "retract": build_retract_spec(
            enabled=_safe_bool(_text(operation, "./{*}Retract/{*}IsEnabled"), False),
            retract_type=_text(operation, "./{*}Retract/{*}RetractType", "Line"),
            mode=_text(operation, "./{*}Retract/{*}RetractMode", "Up"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Retract/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Retract/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Retract/{*}RetractArcSide", "Automatic"),
            overlap=_safe_float(_text(operation, "./{*}Retract/{*}OverLap"), 0.0),
        ),
        "geometry_serialization": _raw_text(geometry, "./{*}_serializationGeometryDescription"),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_line_milling_spec(
    line_milling: LineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedLineMillingSpec:
    normalized_line_milling = _normalize_line_milling_spec(line_milling)
    if source_pgmx_path is None:
        return _HydratedLineMillingSpec(spec=normalized_line_milling)
    template = _extract_line_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_serialization(template, normalized_line_milling):
        return _HydratedLineMillingSpec(spec=normalized_line_milling)
    return _HydratedLineMillingSpec(
        spec=normalized_line_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_serialization=str(template["geometry_serialization"]),
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def _extract_polyline_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_archive(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomCompositeCurve" in _xsi_type(node)
        ),
        None,
    )
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "GeneralProfileFeature" in _xsi_type(node)
        ),
        None,
    )
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado por polilinea compatible.")

    def extract_composite_curve(node: ET.Element) -> _CurveSpec:
        return _composite_curve_spec(
            [member.text or "" for member in node.findall("./{*}_serializingMembers/{*}string")],
            [(key.text or "").strip() for key in node.findall("./{*}_serializingKeys/{*}unsignedInt")],
        )

    def extract_toolpath_curve(toolpath: ET.Element) -> _CurveSpec:
        basic_curve = toolpath.find("./{*}BasicCurve")
        curve_type = _xsi_type(basic_curve)
        if "GeomCompositeCurve" in curve_type:
            return extract_composite_curve(basic_curve)
        return _trimmed_curve_spec(_raw_text(basic_curve, "./{*}_serializationGeometryDescription"))

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): extract_toolpath_curve(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
    }
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id

    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(feature, operation, matching_expressions),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "approach": build_approach_spec(
            enabled=_safe_bool(_text(operation, "./{*}Approach/{*}IsEnabled"), False),
            approach_type=_text(operation, "./{*}Approach/{*}ApproachType", "Line"),
            mode=_text(operation, "./{*}Approach/{*}ApproachMode", "Down"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Approach/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Approach/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Approach/{*}ApproachArcSide", "Automatic"),
        ),
        "retract": build_retract_spec(
            enabled=_safe_bool(_text(operation, "./{*}Retract/{*}IsEnabled"), False),
            retract_type=_text(operation, "./{*}Retract/{*}RetractType", "Line"),
            mode=_text(operation, "./{*}Retract/{*}RetractMode", "Up"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Retract/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Retract/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Retract/{*}RetractArcSide", "Automatic"),
            overlap=_safe_float(_text(operation, "./{*}Retract/{*}OverLap"), 0.0),
        ),
        "geometry_curve": extract_composite_curve(geometry),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_polyline_milling_spec(
    polyline_milling: PolylineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedPolylineMillingSpec:
    normalized_polyline_milling = _normalize_polyline_milling_spec(polyline_milling)
    if source_pgmx_path is None:
        return _HydratedPolylineMillingSpec(spec=normalized_polyline_milling)
    template = _extract_polyline_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_polyline_serialization(template, normalized_polyline_milling):
        return _HydratedPolylineMillingSpec(spec=normalized_polyline_milling)
    return _HydratedPolylineMillingSpec(
        spec=normalized_polyline_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_curve=template.get("geometry_curve") if isinstance(template.get("geometry_curve"), _CurveSpec) else None,
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def _build_line_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    spec: _HydratedLineMillingSpec,
) -> ET.Element:
    geometry = ET.Element(
        _qname(GEOMETRY_NS, "GeomGeometry"),
        {f"{{{XSI_NS}}}type": "a:GeomTrimmedCurve"},
    )
    _set_xmlns(geometry, "a", GEOMETRY_NS)
    _append_key(geometry, geometry_id, "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve")
    _append_blank_name(geometry)
    _append_node(geometry, GEOMETRY_NS, "IsAbsolute", "false")
    _append_object_ref(geometry, GEOMETRY_NS, "PlaneID", plane_id, plane_object_type)
    _append_node(
        geometry,
        GEOMETRY_NS,
        "_serializationGeometryDescription",
        spec.geometry_serialization or _build_line_description(spec.start_x, spec.start_y, spec.end_x, spec.end_y),
    )
    return geometry


def _build_polyline_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    curve_spec: _CurveSpec,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    geometry = ET.Element(
        _qname(GEOMETRY_NS, "GeomGeometry"),
        {f"{{{XSI_NS}}}type": "a:GeomCompositeCurve"},
    )
    _set_xmlns(geometry, "a", GEOMETRY_NS)
    _append_key(geometry, geometry_id, "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCompositeCurve")
    _append_blank_name(geometry)
    _append_node(geometry, GEOMETRY_NS, "IsAbsolute", "false")
    _append_object_ref(geometry, GEOMETRY_NS, "PlaneID", plane_id, plane_object_type)
    member_keys = tuple(curve_spec.member_keys or generated_member_keys)
    keys_group = _append_node(geometry, GEOMETRY_NS, "_serializingKeys")
    members_group = _append_node(geometry, GEOMETRY_NS, "_serializingMembers")
    for key_id, member_serialization in zip(member_keys, curve_spec.member_serializations):
        _append_node(keys_group, ARRAYS_NS, "unsignedInt", key_id)
        _append_node(members_group, ARRAYS_NS, "string", member_serialization)
    return geometry


def _build_profile_feature(
    state: PgmxState,
    spec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    geometry_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:GeneralProfileFeature"},
    )
    _set_xmlns(feature, "a", MILLING_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        geometry_object_type,
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _feature_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", MILLING_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    end_conditions = _append_node(feature, PGMX_NS, "EndConditions")
    slot_end_a = _append_node(
        end_conditions,
        MILLING_NS,
        "SlotEndType",
        attrib={f"{{{XSI_NS}}}type": "a:RadiusedSlotEndType"},
    )
    slot_end_b = _append_node(
        end_conditions,
        MILLING_NS,
        "SlotEndType",
        attrib={f"{{{XSI_NS}}}type": "a:RadiusedSlotEndType"},
    )
    _set_xmlns(slot_end_a, "a", MILLING_NS)
    _set_xmlns(slot_end_b, "a", MILLING_NS)
    _append_node(feature, PGMX_NS, "IsGeomSameDirection", "true")
    _append_node(feature, PGMX_NS, "IsPrecise", "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", "Left")
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", "0")
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", "0")
    _append_node(feature, PGMX_NS, "SideOfFeature", spec.side_of_feature)
    _append_node(feature, PGMX_NS, "SideOffset", "0")
    swept_shape = _append_node(
        feature,
        PGMX_NS,
        "SweptShape",
        attrib={f"{{{XSI_NS}}}type": "a:SquareUProfile"},
    )
    _set_xmlns(swept_shape, "a", MILLING_NS)
    swept_shape.append(_build_identity_profile_placement())
    _append_node(swept_shape, MILLING_NS, "FirstAngle", "0")
    _append_node(swept_shape, MILLING_NS, "FirstRadius", "0")
    _append_node(swept_shape, MILLING_NS, "SecondAngle", "0")
    _append_node(swept_shape, MILLING_NS, "SecondRadius", "0")
    _append_node(swept_shape, MILLING_NS, "Width", _compact_number(spec.tool_width))
    return feature


def _build_toolpath(
    toolpath_type: str,
    curve_spec: _CurveSpec,
    *,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    toolpath = ET.Element(
        _qname(BASE_MODEL_NS, "Toolpath"),
        {f"{{{XSI_NS}}}type": "b:CutterLocationTrajectory"},
    )
    _set_xmlns(toolpath, "b", BASE_MODEL_NS)
    _append_node(toolpath, BASE_MODEL_NS, "Attributes", "")
    _append_node(toolpath, BASE_MODEL_NS, "Priority", "true")
    _append_node(toolpath, BASE_MODEL_NS, "Type", toolpath_type)
    _append_node(toolpath, BASE_MODEL_NS, "Direction", "true")
    toolpath.append(_build_curve_holder("BasicCurve", curve_spec, generated_member_keys=generated_member_keys))
    toolpath.append(_build_vector_holder("ToolAxis", 1.0, 0.0, 0.0))
    return toolpath


def _build_generated_approach_curve(
    state: PgmxState,
    spec,
    toolpath_start: tuple[float, float],
    toolpath_end: tuple[float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    approach = _normalize_approach_spec(spec.approach)
    clearance_z = state.depth + spec.security_plane
    cut_z = _toolpath_cut_z(state, spec)
    direction_x, direction_y = _resolve_toolpath_direction(toolpath_start, toolpath_end, direction=direction)
    if not approach.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_start[0], toolpath_start[1], clearance_z, cut_z)

    if approach.approach_type == "Line" and approach.mode == "Quote":
        pre_entry_distance = _linear_lead_distance(spec.tool_width, approach.radius_multiplier)
        pre_entry_x = toolpath_start[0] - (direction_x * pre_entry_distance)
        pre_entry_y = toolpath_start[1] - (direction_y * pre_entry_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, clearance_z),
                    (pre_entry_x, pre_entry_y, cut_z),
                ),
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, cut_z),
                    (toolpath_start[0], toolpath_start[1], cut_z),
                ),
            ]
        )

    if approach.approach_type == "Line" and approach.mode == "Down":
        return _build_down_line_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Quote":
        return _build_quote_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=approach.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Down":
        return _build_down_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un approach habilitado con "
        f"type={approach.approach_type} y mode={approach.mode}."
    )


def _build_generated_lift_curve(
    state: PgmxState,
    spec,
    toolpath_start: tuple[float, float],
    toolpath_end: tuple[float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    retract = _normalize_retract_spec(spec.retract)
    clearance_z = state.depth + spec.security_plane
    cut_z = _toolpath_cut_z(state, spec)
    direction_x, direction_y = _resolve_toolpath_direction(toolpath_start, toolpath_end, direction=direction)
    if not retract.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_end[0], toolpath_end[1], cut_z, clearance_z)

    if retract.retract_type == "Line" and retract.mode == "Quote":
        post_exit_distance = (spec.tool_width / 2.0) * retract.radius_multiplier
        post_exit_x = toolpath_end[0] + (direction_x * post_exit_distance)
        post_exit_y = toolpath_end[1] + (direction_y * post_exit_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (toolpath_end[0], toolpath_end[1], cut_z),
                    (post_exit_x, post_exit_y, cut_z),
                ),
                _build_toolpath_description(
                    (post_exit_x, post_exit_y, cut_z),
                    (post_exit_x, post_exit_y, clearance_z),
                ),
            ]
        )

    if retract.retract_type == "Line" and retract.mode == "Up":
        return _build_up_line_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Quote":
        return _build_quote_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=retract.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Up":
        return _build_up_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un retract habilitado con "
        f"type={retract.retract_type} y mode={retract.mode}."
    )


def _build_line_operation(
    state: PgmxState,
    spec,
    operation_id: str,
    approach_curve: _CurveSpec,
    approach_curve_member_keys: Sequence[str] = (),
    lift_curve: Optional[_CurveSpec] = None,
    lift_curve_member_keys: Sequence[str] = (),
    trajectory_curve: Optional[_CurveSpec] = None,
    trajectory_curve_member_keys: Sequence[str] = (),
    toolpath_start: Optional[tuple[float, float]] = None,
    toolpath_end: Optional[tuple[float, float]] = None,
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:BottomAndSideFinishMilling"},
    )
    _set_xmlns(operation, "a", MILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling")
    _append_blank_name(operation)
    _append_node(operation, PGMX_NS, "ActivateCNCCorrection", "true")
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)
    clearance_z = state.depth + spec.security_plane
    cut_z = _toolpath_cut_z(state, spec)
    if toolpath_start is None or toolpath_end is None:
        (toolpath_start_x, toolpath_start_y), (toolpath_end_x, toolpath_end_y) = _offset_line_for_toolpath(spec)
    else:
        toolpath_start_x, toolpath_start_y = toolpath_start
        toolpath_end_x, toolpath_end_y = toolpath_end
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            approach_curve,
            generated_member_keys=approach_curve_member_keys,
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "TrajectoryPath",
            trajectory_curve
            or spec.trajectory_curve
            or _trimmed_curve_spec(
                _build_toolpath_description(
                    (toolpath_start_x, toolpath_start_y, cut_z),
                    (toolpath_end_x, toolpath_end_y, cut_z),
                )
            ),
            generated_member_keys=trajectory_curve_member_keys,
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            lift_curve
            or spec.lift_curve
            or _trimmed_curve_spec(
                _build_toolpath_description(
                    (toolpath_end_x, toolpath_end_y, cut_z),
                    (toolpath_end_x, toolpath_end_y, clearance_z),
                )
            ),
            generated_member_keys=lift_curve_member_keys,
        )
    )
    _append_node(operation, PGMX_NS, "ToolpathPriority", "true")
    _append_node(operation, PGMX_NS, "AdditionalToolKeys", "")
    _append_node(operation, PGMX_NS, "ApproachSecurityPlane", _compact_number(spec.security_plane))
    _append_node(operation, PGMX_NS, "Head", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(operation, PGMX_NS, "HeadRotation", "0")
    _append_node(operation, PGMX_NS, "MachineFunctions", "")
    _append_node(operation, PGMX_NS, "RetractSecurityPlane", _compact_number(spec.security_plane))
    operation.append(_build_start_point(0.0, 0.0, 0.0))
    technology = _append_node(
        operation,
        PGMX_NS,
        "Technology",
        attrib={f"{{{XSI_NS}}}type": "MillingTechnology"},
    )
    _append_node(technology, PGMX_NS, "Feedrate", "0")
    _append_node(technology, PGMX_NS, "CutSpeed", "0")
    _append_node(technology, PGMX_NS, "Spindle", "0")
    _append_object_ref(
        operation,
        PGMX_NS,
        "ToolKey",
        spec.tool_id,
        "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
        include_name=True,
        name_text=spec.tool_name,
    )
    _append_node(operation, PGMX_NS, "OvercutLength", _compact_number(_operation_overcut_length(spec)))
    approach = _append_node(
        operation,
        PGMX_NS,
        "Approach",
        attrib={f"{{{XSI_NS}}}type": "b:BaseApproachStrategy"},
    )
    _set_xmlns(approach, "b", STRATEGY_NS)
    _append_node(approach, STRATEGY_NS, "ApproachArcSide", spec.approach.arc_side)
    _append_node(approach, STRATEGY_NS, "ApproachMode", spec.approach.mode)
    _append_node(approach, STRATEGY_NS, "ApproachType", spec.approach.approach_type)
    _append_node(approach, STRATEGY_NS, "IsEnabled", "true" if spec.approach.is_enabled else "false")
    _append_node(approach, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.approach.radius_multiplier))
    _append_node(approach, STRATEGY_NS, "Speed", _compact_number(spec.approach.speed))
    retract = _append_node(
        operation,
        PGMX_NS,
        "Retract",
        attrib={f"{{{XSI_NS}}}type": "b:BaseRetractStrategy"},
    )
    _set_xmlns(retract, "b", STRATEGY_NS)
    _append_node(retract, STRATEGY_NS, "IsEnabled", "true" if spec.retract.is_enabled else "false")
    _append_node(retract, STRATEGY_NS, "OverLap", _compact_number(spec.retract.overlap))
    _append_node(retract, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.retract.radius_multiplier))
    _append_node(retract, STRATEGY_NS, "RetractArcSide", spec.retract.arc_side)
    _append_node(retract, STRATEGY_NS, "RetractMode", spec.retract.mode)
    _append_node(retract, STRATEGY_NS, "RetractType", spec.retract.retract_type)
    _append_node(retract, STRATEGY_NS, "Speed", _compact_number(spec.retract.speed))
    _append_node(operation, PGMX_NS, "MachiningStrategy", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(operation, PGMX_NS, "AllowanceBottom", "0")
    _append_node(operation, PGMX_NS, "AllowanceSide", "0")
    return operation


def _build_working_step(
    feature_name: str,
    step_id: str,
    feature_id: str,
    operation_id: str,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "a:MachiningWorkingStep"},
    )
    _set_xmlns(step, "a", PGMX_NS)
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep")
    _append_blank_name(step).text = feature_name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")
    feature_ref = _append_object_ref(
        step,
        PGMX_NS,
        "ManufacturingFeatureID",
        feature_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature",
    )
    operation_ref = _append_object_ref(
        step,
        PGMX_NS,
        "OperationID",
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
    )
    _set_xmlns(feature_ref, "b", UTILITY_NS)
    _set_xmlns(operation_ref, "b", UTILITY_NS)
    return step


def _build_depth_expression(expression_id: str, feature_id: str, inner_field_name: str) -> ET.Element:
    expression = ET.Element(_qname(PARAMETRIC_NS, "Expression"))
    _append_key(expression, expression_id, "ScmGroup.XCam.MachiningDataModel.Parametrics.Expression")
    _append_blank_name(expression)
    property_node = _append_node(
        expression,
        PARAMETRIC_NS,
        "Property",
        attrib={f"{{{XSI_NS}}}type": "a:CompositeField"},
    )
    _set_xmlns(property_node, "a", PARAMETRIC_NS)
    _append_node(property_node, PARAMETRIC_NS, "Index", "-1")
    _append_node(property_node, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(property_node, PARAMETRIC_NS, "Name", "Depth")
    inner_field = _append_node(property_node, PARAMETRIC_NS, "InnerField")
    _append_node(inner_field, PARAMETRIC_NS, "Index", "-1")
    _append_node(inner_field, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(inner_field, PARAMETRIC_NS, "Name", inner_field_name)
    _append_object_ref(
        expression,
        PARAMETRIC_NS,
        "ReferencedObject",
        feature_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature",
    )
    _append_node(expression, PARAMETRIC_NS, "Value", "dz1")
    return expression


def _append_line_milling(root: ET.Element, state: PgmxState, spec: _HydratedLineMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None
    toolpath_start, toolpath_end = _offset_line_for_toolpath(spec)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve(state, spec, toolpath_start, toolpath_end)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve(state, spec, toolpath_start, toolpath_end)

    approach_curve_member_keys: tuple[str, ...] = ()
    next_generated_aux_id = int(end_expression_id or step_id) + 1
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth"))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth"))


def _append_polyline_milling(root: ET.Element, state: PgmxState, spec: _HydratedPolylineMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)

    generated_geometry_curve = spec.geometry_curve or _composite_curve_spec(_build_open_polyline_descriptions(spec.points))
    geometry_member_count = len(generated_geometry_curve.member_serializations)
    reserved_ids = _reserve_ids(
        root,
        geometry_member_count + (6 if uses_depth_expressions else 4),
        spec.preferred_id_start,
    )
    geometry_id = reserved_ids[0]
    generated_geometry_member_keys: tuple[str, ...] = ()
    if generated_geometry_curve.geometry_type == "GeomCompositeCurve" and not generated_geometry_curve.member_keys:
        generated_geometry_member_keys = tuple(reserved_ids[1 : 1 + geometry_member_count])

    operation_index = 1 + geometry_member_count
    operation_id = reserved_ids[operation_index]
    feature_id = reserved_ids[operation_index + 1]
    step_id = reserved_ids[operation_index + 2]
    start_expression_id = reserved_ids[operation_index + 3] if uses_depth_expressions else None
    end_expression_id = reserved_ids[operation_index + 4] if uses_depth_expressions else None

    generated_trajectory_curve, start_point, end_point = _build_generated_polyline_trajectory_curve(state, spec)
    trajectory_curve = spec.trajectory_curve or generated_trajectory_curve

    start_direction, end_direction = _polyline_endpoint_directions(spec.points)

    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve(
            state,
            spec,
            start_point,
            spec.points[1],
            direction=start_direction,
        )
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve(
            state,
            spec,
            spec.points[-2],
            end_point,
            direction=end_direction,
        )

    next_generated_aux_id = int(end_expression_id or step_id) + 1
    trajectory_curve_member_keys: tuple[str, ...] = ()
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
        if trajectory_curve.member_serializations == generated_geometry_curve.member_serializations:
            trajectory_curve_member_keys = generated_geometry_curve.member_keys or generated_geometry_member_keys
        else:
            member_count = len(trajectory_curve.member_serializations)
            trajectory_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
            next_generated_aux_id += member_count

    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(
        _build_polyline_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            generated_geometry_curve,
            generated_member_keys=generated_geometry_member_keys,
        )
    )
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCompositeCurve",
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys or trajectory_curve_member_keys,
            toolpath_start=start_point,
            toolpath_end=end_point,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth"))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth"))


# ============================================================================
# Public read/build API
# ============================================================================

def read_pgmx_state(path: Path) -> PgmxState:
    """Lee un `.pgmx` y devuelve el estado basico de pieza, origen y area.

    No interpreta mecanizados. Sirve para reutilizar dimensiones reales y para
    tomar un baseline o un `source_pgmx_path` como punto de partida.
    """

    root, _, _ = _load_pgmx_archive(path)

    variables = root.find("./{*}Variables")
    variable_values: dict[str, float] = {}
    if variables is not None:
        for variable in list(variables):
            name = _text(variable, "./{*}Name").lower()
            if not name:
                continue
            variable_values[name] = _safe_float(_text(variable, "./{*}Value"), 0.0)

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError(f"El archivo '{path}' no contiene WorkPiece.")

    piece_name = _text(workpiece, "./{*}Name", path.stem) or path.stem
    length = variable_values.get("dx1", _safe_float(_text(workpiece, "./{*}Length"), 0.0))
    width = variable_values.get("dy1", _safe_float(_text(workpiece, "./{*}Width"), 0.0))
    depth = variable_values.get("dz1", _safe_float(_text(workpiece, "./{*}Depth"), 0.0))

    setup_placement = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )
    if setup_placement is None:
        raise ValueError(f"El archivo '{path}' no contiene WorkpieceSetup/Placement.")

    origin_x = _safe_float(_text(setup_placement, "./{*}_xP"), 0.0)
    origin_y = _safe_float(_text(setup_placement, "./{*}_yP"), 0.0)
    origin_z = _safe_float(_text(setup_placement, "./{*}_zP"), 0.0)
    execution_fields = _normalize_execution_fields(
        _text(root, "./{*}MachiningParameters/{*}ExecutionFields", "HG")
    )

    return PgmxState(
        piece_name=piece_name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        execution_fields=execution_fields,
    )


def _merge_state(
    base_state: PgmxState,
    piece_name: Optional[str],
    length: Optional[float],
    width: Optional[float],
    depth: Optional[float],
    origin_x: Optional[float],
    origin_y: Optional[float],
    origin_z: Optional[float],
    execution_fields: Optional[str],
) -> PgmxState:
    return PgmxState(
        piece_name=base_state.piece_name if piece_name is None else piece_name,
        length=base_state.length if length is None else length,
        width=base_state.width if width is None else width,
        depth=base_state.depth if depth is None else depth,
        origin_x=base_state.origin_x if origin_x is None else origin_x,
        origin_y=base_state.origin_y if origin_y is None else origin_y,
        origin_z=base_state.origin_z if origin_z is None else origin_z,
        execution_fields=(
            base_state.execution_fields
            if execution_fields is None
            else _normalize_execution_fields(execution_fields)
        ),
    )


def _apply_piece_state(root: ET.Element, state: PgmxState) -> None:
    variables = root.find("./{*}Variables")
    if variables is not None:
        for variable in list(variables):
            value_node = variable.find("./{*}Value")
            _set_xmlns(value_node, "b", XSD_NS)
            name = _text(variable, "./{*}Name").lower()
            if name == "dx1":
                _set_text(value_node, _compact_number(state.length))
            elif name == "dy1":
                _set_text(value_node, _compact_number(state.width))
            elif name == "dz1":
                _set_text(value_node, _compact_number(state.depth))

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    _set_text(workpiece.find("./{*}Name"), state.piece_name)
    _set_text(workpiece.find("./{*}Length"), _compact_number(state.length))
    _set_text(workpiece.find("./{*}Width"), _compact_number(state.width))
    _set_text(workpiece.find("./{*}Depth"), _compact_number(state.depth))
    geometry = workpiece.find("./{*}Geometry")
    if geometry is not None:
        _set_text(geometry.find("./{*}Length"), _compact_number(state.length))
        _set_text(geometry.find("./{*}Width"), _compact_number(state.width))
        _set_text(geometry.find("./{*}Depth"), _compact_number(state.depth))

    plane_specs = {
        "Top": (state.length, state.width, 0.0, 0.0, state.depth),
        "Bottom": (state.length, state.width, 0.0, state.width, 0.0),
        "Right": (state.width, state.depth, state.length, 0.0, 0.0),
        "Left": (state.width, state.depth, 0.0, state.width, 0.0),
        "Front": (state.length, state.depth, 0.0, 0.0, 0.0),
        "Back": (state.length, state.depth, state.length, state.width, 0.0),
    }
    planes = root.find("./{*}Planes")
    if planes is not None:
        for plane in list(planes):
            plane_type = _text(plane, "./{*}Type") or _text(plane, "./{*}Name")
            spec = plane_specs.get(plane_type)
            if spec is None:
                continue
            x_dimension, y_dimension, x_origin, y_origin, z_origin = spec
            _set_text(plane.find("./{*}XDimension"), _compact_number(x_dimension))
            _set_text(plane.find("./{*}YDimension"), _compact_number(y_dimension))
            placement = plane.find("./{*}Placement")
            if placement is None:
                continue
            _set_text(placement.find("./{*}_xP"), _compact_number(x_origin))
            _set_text(placement.find("./{*}_yP"), _compact_number(y_origin))
            _set_text(placement.find("./{*}_zP"), _compact_number(z_origin))

    setup_placement = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )
    if setup_placement is None:
        raise ValueError("La plantilla no contiene WorkpieceSetup/Placement.")
    _set_text(setup_placement.find("./{*}_xP"), _compact_number(state.origin_x))
    _set_text(setup_placement.find("./{*}_yP"), _compact_number(state.origin_y))
    _set_text(setup_placement.find("./{*}_zP"), _compact_number(state.origin_z))

    execution_fields_node = root.find("./{*}MachiningParameters/{*}ExecutionFields")
    if execution_fields_node is None:
        raise ValueError("La plantilla no contiene MachiningParameters/ExecutionFields.")
    _set_text(execution_fields_node, state.execution_fields)


def _apply_line_millings(
    root: ET.Element,
    state: PgmxState,
    line_millings: Sequence[_HydratedLineMillingSpec],
) -> None:
    for line_milling in line_millings:
        _append_line_milling(root, state, line_milling)


def _apply_polyline_millings(
    root: ET.Element,
    state: PgmxState,
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
) -> None:
    for polyline_milling in polyline_millings:
        _append_polyline_milling(root, state, polyline_milling)


# ============================================================================
# Public machining builders
# ============================================================================

def build_line_milling_spec(
    line_x1: Optional[float],
    line_y1: Optional[float],
    line_x2: Optional[float],
    line_y2: Optional[float],
    line_feature_name: Optional[str],
    line_tool_id: Optional[str],
    line_tool_name: Optional[str],
    line_tool_width: Optional[float],
    line_security_plane: Optional[float],
    line_side_of_feature: Optional[str] = None,
    line_is_through: Optional[bool] = None,
    line_target_depth: Optional[float] = None,
    line_extra_depth: Optional[float] = None,
    line_approach_enabled: Optional[bool] = None,
    line_approach_type: Optional[str] = None,
    line_approach_mode: Optional[str] = None,
    line_approach_radius_multiplier: Optional[float] = None,
    line_approach_speed: Optional[float] = None,
    line_approach_arc_side: Optional[str] = None,
    line_retract_enabled: Optional[bool] = None,
    line_retract_type: Optional[str] = None,
    line_retract_mode: Optional[str] = None,
    line_retract_radius_multiplier: Optional[float] = None,
    line_retract_speed: Optional[float] = None,
    line_retract_arc_side: Optional[str] = None,
    line_retract_overlap: Optional[float] = None,
) -> Optional[LineMillingSpec]:
    """Construye un `LineMillingSpec` reusable para un fresado lineal.

    Devuelve `None` si la linea no viene informada, lo que simplifica el uso
    desde CLI y desde capas superiores que quieren tratar este mecanizado como
    opcional.
    """

    values = [line_x1, line_y1, line_x2, line_y2]
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("Para sintetizar el fresado lineal hay que indicar x1, y1, x2 e y2.")
    return LineMillingSpec(
        start_x=float(line_x1),
        start_y=float(line_y1),
        end_x=float(line_x2),
        end_y=float(line_y2),
        feature_name=(line_feature_name or "Fresado").strip() or "Fresado",
        side_of_feature=_normalize_side_of_feature(line_side_of_feature),
        tool_id=(line_tool_id or "1902").strip() or "1902",
        tool_name=(line_tool_name or "E003").strip() or "E003",
        tool_width=9.52 if line_tool_width is None else float(line_tool_width),
        security_plane=20.0 if line_security_plane is None else float(line_security_plane),
        depth_spec=build_milling_depth_spec(
            is_through=line_is_through,
            target_depth=line_target_depth,
            extra_depth=line_extra_depth,
        ),
        approach=build_approach_spec(
            enabled=line_approach_enabled,
            approach_type=line_approach_type,
            mode=line_approach_mode,
            radius_multiplier=line_approach_radius_multiplier,
            speed=line_approach_speed,
            arc_side=line_approach_arc_side,
        ),
        retract=build_retract_spec(
            enabled=line_retract_enabled,
            retract_type=line_retract_type,
            mode=line_retract_mode,
            radius_multiplier=line_retract_radius_multiplier,
            speed=line_retract_speed,
            arc_side=line_retract_arc_side,
            overlap=line_retract_overlap,
        ),
    )


def build_polyline_milling_spec(
    points: Sequence[tuple[float, float]],
    feature_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    side_of_feature: Optional[str] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    approach_enabled: Optional[bool] = None,
    approach_type: Optional[str] = None,
    approach_mode: Optional[str] = None,
    approach_radius_multiplier: Optional[float] = None,
    approach_speed: Optional[float] = None,
    approach_arc_side: Optional[str] = None,
    retract_enabled: Optional[bool] = None,
    retract_type: Optional[str] = None,
    retract_mode: Optional[str] = None,
    retract_radius_multiplier: Optional[float] = None,
    retract_speed: Optional[float] = None,
    retract_arc_side: Optional[str] = None,
    retract_overlap: Optional[float] = None,
) -> PolylineMillingSpec:
    """Construye un `PolylineMillingSpec` reusable para una polilinea abierta."""

    return PolylineMillingSpec(
        points=_normalize_polyline_points(points),
        feature_name=(feature_name or "Fresado").strip() or "Fresado",
        side_of_feature=_normalize_side_of_feature(side_of_feature),
        tool_id=(tool_id or "1902").strip() or "1902",
        tool_name=(tool_name or "E003").strip() or "E003",
        tool_width=9.52 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        ),
        approach=build_approach_spec(
            enabled=approach_enabled,
            approach_type=approach_type,
            mode=approach_mode,
            radius_multiplier=approach_radius_multiplier,
            speed=approach_speed,
            arc_side=approach_arc_side,
        ),
        retract=build_retract_spec(
            enabled=retract_enabled,
            retract_type=retract_type,
            mode=retract_mode,
            radius_multiplier=retract_radius_multiplier,
            speed=retract_speed,
            arc_side=retract_arc_side,
            overlap=retract_overlap,
        ),
    )


# ============================================================================
# Public execution API
# ============================================================================

def build_synthesis_request(
    baseline_path: Path,
    output_path: Path,
    *,
    source_pgmx_path: Optional[Path] = None,
    piece: Optional[PgmxState] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    execution_fields: Optional[str] = None,
    line_millings: Optional[Sequence[LineMillingSpec]] = None,
    polyline_millings: Optional[Sequence[PolylineMillingSpec]] = None,
) -> PgmxSynthesisRequest:
    """Arma una solicitud reusable de sintesis para el flujo principal.

    Orden recomendado de uso:
    1. leer o definir la pieza
    2. construir `LineMillingSpec` y/o `PolylineMillingSpec`
    3. construir el request
    4. ejecutar `synthesize_request(...)`
    """

    base_piece = piece or (read_pgmx_state(source_pgmx_path) if source_pgmx_path else read_pgmx_state(baseline_path))
    effective_execution_fields = execution_fields
    if effective_execution_fields is None and piece is None:
        effective_execution_fields = "HG"
    target_piece = _merge_state(
        base_piece,
        piece_name,
        length,
        width,
        depth,
        origin_x,
        origin_y,
        origin_z,
        effective_execution_fields,
    )
    return PgmxSynthesisRequest(
        baseline_path=baseline_path,
        output_path=output_path,
        piece=target_piece,
        source_pgmx_path=source_pgmx_path,
        line_millings=tuple(line_millings or ()),
        polyline_millings=tuple(polyline_millings or ()),
    )


def synthesize_request(request: PgmxSynthesisRequest) -> PgmxSynthesisResult:
    """Ejecuta una solicitud de sintesis y escribe el `.pgmx` resultante.

    Esta es la funcion principal para el flujo programatico.
    """

    baseline_root, baseline_entries, _ = _load_pgmx_archive(request.baseline_path)
    hydrated_line_millings = [
        _hydrate_line_milling_spec(line_milling, request.source_pgmx_path)
        for line_milling in request.line_millings
    ]
    hydrated_polyline_millings = [
        _hydrate_polyline_milling_spec(polyline_milling, request.source_pgmx_path)
        for polyline_milling in request.polyline_millings
    ]

    _apply_piece_state(baseline_root, request.piece)
    _apply_line_millings(baseline_root, request.piece, hydrated_line_millings)
    _apply_polyline_millings(baseline_root, request.piece, hydrated_polyline_millings)

    xml_bytes = _finalize_synthesized_pgmx_xml_bytes(
        ET.tostring(
            baseline_root,
            encoding="utf-8",
            xml_declaration=request.source_pgmx_path is None,
        )
    )
    _write_pgmx_zip(
        output_path=request.output_path,
        xml_bytes=xml_bytes,
        template_entries=baseline_entries,
        xml_entry_name=f"{request.output_path.stem}.xml",
    )
    return PgmxSynthesisResult(
        output_path=request.output_path,
        piece=request.piece,
        sha256=hashlib.sha256(request.output_path.read_bytes()).hexdigest(),
        line_millings=request.line_millings,
        polyline_millings=request.polyline_millings,
    )


def synthesize_pgmx(
    baseline_path: Path,
    output_path: Path,
    source_pgmx_path: Optional[Path] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    line_milling: Optional[LineMillingSpec] = None,
    polyline_milling: Optional[PolylineMillingSpec] = None,
    execution_fields: Optional[str] = None,
) -> PgmxState:
    """Wrapper de compatibilidad para el flujo historico basado en argumentos sueltos.

    Para codigo nuevo conviene preferir `build_synthesis_request(...)` y
    `synthesize_request(...)`.
    """

    request = build_synthesis_request(
        baseline_path=baseline_path,
        output_path=output_path,
        source_pgmx_path=source_pgmx_path,
        piece_name=piece_name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        execution_fields=execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
        polyline_millings=[polyline_milling] if polyline_milling is not None else (),
    )
    return synthesize_request(request).piece


# ============================================================================
# CLI
# ============================================================================

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sintetiza un PGMX base a partir de un baseline sin mecanizados.")
    parser.add_argument("--baseline", required=True, help="Ruta al .pgmx baseline sin mecanizados.")
    parser.add_argument("--output", required=True, help="Ruta del .pgmx sintetizado de salida.")
    parser.add_argument(
        "--source-pgmx",
        help="Ruta a un .pgmx editado en Maestro del cual copiar dimensiones y origen ya descubiertos.",
    )
    parser.add_argument("--piece-name", help="Nombre interno de la pieza dentro del .pgmx.")
    parser.add_argument("--length", type=float, help="Largo final de la pieza (dx1).")
    parser.add_argument("--width", type=float, help="Ancho final de la pieza (dy1).")
    parser.add_argument("--depth", type=float, help="Espesor final de la pieza (dz1).")
    parser.add_argument("--origin-x", type=float, help="Origen de mecanizado X.")
    parser.add_argument("--origin-y", type=float, help="Origen de mecanizado Y.")
    parser.add_argument("--origin-z", type=float, help="Origen de mecanizado Z.")
    parser.add_argument(
        "--execution-fields",
        "--area",
        dest="execution_fields",
        help="Area de Parametros de Maquina. Valores observados: A, EF, HG. Si no se indica, la sintesis usa HG.",
    )
    parser.add_argument("--line-x1", type=float, help="Coordenada X inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y1", type=float, help="Coordenada Y inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-x2", type=float, help="Coordenada X final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y2", type=float, help="Coordenada Y final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-feature-name", help="Nombre del feature/working step del fresado lineal.")
    parser.add_argument("--line-side-of-feature", help="Correccion de herramienta del fresado lineal: Center, Right o Left.")
    parser.add_argument("--line-tool-id", help="ID de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-name", help="Nombre de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-width", type=float, help="Ancho del perfil barrido para el fresado lineal.")
    parser.add_argument("--line-security-plane", type=float, help="Plano de seguridad usado en approach/retract.")
    parser.add_argument(
        "--line-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado lineal. Por defecto queda activado.",
    )
    parser.add_argument(
        "--line-target-depth",
        type=float,
        help="Profundidad fija del fresado lineal cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--line-extra-depth",
        type=float,
        help="Extra del fresado lineal cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--line-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1."
        ),
    )
    parser.add_argument("--line-approach-type", help="Tipo de approach. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-approach-mode",
        help="Modo de approach. Valores utiles: Down o Quote (UI Maestro: En Cota). Para Arc se valido Quote.",
    )
    parser.add_argument(
        "--line-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach lineal.",
    )
    parser.add_argument(
        "--line-approach-speed",
        type=float,
        help="Velocidad del approach. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-approach-arc-side",
        help="Lado del arco del approach. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1/overlap 0."
        ),
    )
    parser.add_argument("--line-retract-type", help="Tipo de retract. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-retract-mode",
        help="Modo de retract. Valores utiles: Up o Quote (UI Maestro: En Cota). Para Arc se validaron Quote y Up.",
    )
    parser.add_argument(
        "--line-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract lineal.",
    )
    parser.add_argument(
        "--line-retract-speed",
        type=float,
        help="Velocidad del retract. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-retract-arc-side",
        help="Lado del arco del retract. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-overlap",
        type=float,
        help="Sobreposicion del retract lineal.",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output)
    line_milling = build_line_milling_spec(
        line_x1=args.line_x1,
        line_y1=args.line_y1,
        line_x2=args.line_x2,
        line_y2=args.line_y2,
        line_feature_name=args.line_feature_name,
        line_side_of_feature=args.line_side_of_feature,
        line_tool_id=args.line_tool_id,
        line_tool_name=args.line_tool_name,
        line_tool_width=args.line_tool_width,
        line_security_plane=args.line_security_plane,
        line_is_through=args.line_through,
        line_target_depth=args.line_target_depth,
        line_extra_depth=args.line_extra_depth,
        line_approach_enabled=args.line_approach_enabled,
        line_approach_type=args.line_approach_type,
        line_approach_mode=args.line_approach_mode,
        line_approach_radius_multiplier=args.line_approach_radius_multiplier,
        line_approach_speed=args.line_approach_speed,
        line_approach_arc_side=args.line_approach_arc_side,
        line_retract_enabled=args.line_retract_enabled,
        line_retract_type=args.line_retract_type,
        line_retract_mode=args.line_retract_mode,
        line_retract_radius_multiplier=args.line_retract_radius_multiplier,
        line_retract_speed=args.line_retract_speed,
        line_retract_arc_side=args.line_retract_arc_side,
        line_retract_overlap=args.line_retract_overlap,
    )
    request = build_synthesis_request(
        baseline_path=Path(args.baseline),
        output_path=output_path,
        source_pgmx_path=Path(args.source_pgmx) if args.source_pgmx else None,
        piece_name=args.piece_name,
        length=args.length,
        width=args.width,
        depth=args.depth,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        origin_z=args.origin_z,
        execution_fields=args.execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
    )
    result = synthesize_request(request)

    summary = {
        "output": str(output_path),
        "piece_name": result.piece.piece_name,
        "length": _compact_number(result.piece.length),
        "width": _compact_number(result.piece.width),
        "depth": _compact_number(result.piece.depth),
        "origin_x": _compact_number(result.piece.origin_x),
        "origin_y": _compact_number(result.piece.origin_y),
        "origin_z": _compact_number(result.piece.origin_z),
        "execution_fields": result.piece.execution_fields,
        "sha256": result.sha256,
    }
    if line_milling is not None:
        summary["line_milling"] = {
            "feature_name": line_milling.feature_name,
            "start": [_compact_number(line_milling.start_x), _compact_number(line_milling.start_y)],
            "end": [_compact_number(line_milling.end_x), _compact_number(line_milling.end_y)],
            "side_of_feature": line_milling.side_of_feature,
            "tool_id": line_milling.tool_id,
            "tool_name": line_milling.tool_name,
            "tool_width": _compact_number(line_milling.tool_width),
            "security_plane": _compact_number(line_milling.security_plane),
            "approach": {
                "is_enabled": line_milling.approach.is_enabled,
                "approach_type": line_milling.approach.approach_type,
                "mode": line_milling.approach.mode,
                "radius_multiplier": _compact_number(line_milling.approach.radius_multiplier),
                "speed": _compact_number(line_milling.approach.speed),
                "arc_side": line_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": line_milling.retract.is_enabled,
                "retract_type": line_milling.retract.retract_type,
                "mode": line_milling.retract.mode,
                "radius_multiplier": _compact_number(line_milling.retract.radius_multiplier),
                "speed": _compact_number(line_milling.retract.speed),
                "arc_side": line_milling.retract.arc_side,
                "overlap": _compact_number(line_milling.retract.overlap),
            },
        }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
