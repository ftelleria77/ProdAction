"""Program-level contracts for PGMX synthesis."""

from __future__ import annotations

import hashlib
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union

from ..drilling.pattern import (
    DrillingPatternSpec,
    _HydratedDrillingPatternSpec,
    _append_drilling_pattern,
    _hydrate_drilling_pattern_spec,
)
from ..drilling.single import (
    DrillingSpec,
    _HydratedDrillingSpec,
    _append_drilling,
    _hydrate_drilling_spec,
    _validate_tool_sinking_length_for_drilling_spec,
)
from ..milling._common import (
    _validate_tool_sinking_length_for_spec,
    _validate_tool_type_for_milling_spec,
)
from ..milling.circle import (
    CircleMillingSpec,
    _HydratedCircleMillingSpec,
    _append_circle_milling,
    _hydrate_circle_milling_spec,
)
from ..milling.line import (
    LineMillingSpec,
    _HydratedLineMillingSpec,
    _append_line_milling,
    _hydrate_line_milling_spec,
)
from ..milling.pocket import (
    PocketMillingSpec,
    _HydratedPocketMillingSpec,
    _append_pocket_milling,
    _hydrate_pocket_milling_spec,
)
from ..milling.profile import (
    PolylineMillingSpec,
    _HydratedPolylineMillingSpec,
    _append_polyline_milling,
    _hydrate_polyline_milling_spec,
)
from ..milling.slot import (
    SlotMillingSpec,
    _HydratedSlotMillingSpec,
    _append_slot_milling,
    _hydrate_slot_milling_spec,
)
from ..milling.squaring import (
    SquaringMillingSpec,
    _HydratedSquaringMillingSpec,
    _append_squaring_milling,
    _hydrate_squaring_milling_spec,
)
from .hydration import _load_pgmx_container
from .output import (
    _finalize_pgmx_xml_bytes,
    _finalize_synthesized_pgmx_xml_bytes,
    _write_pgmx_zip,
)
from .tools import (
    _load_tool_catalog,
    _validate_tool_type_for_drilling_spec,
)
from .xml import (
    BASE_MODEL_NS,
    UTILITY_NS,
    XSD_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _compact_number,
    _qname,
    _reserve_ids,
    _safe_float,
    _set_text,
    _set_xmlns,
    _text,
    _xsi_type,
    register_pgmx_namespaces,
)

__all__ = [
    "DEFAULT_BASELINE_DIR",
    "DEFAULT_BASELINE_XML_PATH",
    "DEFAULT_MACHINING_ORDER",
    "HydratedMachiningSpec",
    "MachiningSpec",
    "MODULE_DIR",
    "PgmxState",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "SYNTHESIZER_VERSION",
    "XnSpec",
    "_apply_circle_millings",
    "_apply_drilling_patterns",
    "_apply_drillings",
    "_append_hydrated_machining",
    "_apply_line_millings",
    "_apply_piece_state",
    "_apply_pocket_millings",
    "_apply_polyline_millings",
    "_apply_slot_millings",
    "_apply_squaring_millings",
    "_build_xn_step",
    "_drilling_plane_priority",
    "_ensure_xn_step",
    "_finalize_pgmx_xml_bytes",
    "_finalize_synthesized_pgmx_xml_bytes",
    "_hydrate_machining_spec",
    "_normalize_machining_order",
    "_normalize_execution_fields",
    "_normalize_xn_reference",
    "_normalize_xn_spec",
    "_merge_state",
    "_module_data_dir",
    "_split_hydrated_machinings",
    "_validate_tool_sinking_lengths",
    "_write_pgmx_zip",
    "build_synthesis_request",
    "build_xn_spec",
    "read_pgmx_state",
    "synthesize_pgmx",
    "synthesize_request",
]


DEFAULT_MACHINING_ORDER = ("line", "slot", "polyline", "circle", "squaring", "pocket", "drilling", "drilling_pattern")


register_pgmx_namespaces()


def _module_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        for bundled_data_dir in (
            executable_dir / "pgmx" / "data",
            executable_dir / "_internal" / "pgmx" / "data",
        ):
            if bundled_data_dir.exists():
                return bundled_data_dir
    return Path(__file__).resolve().parents[2] / "data"


MODULE_DIR = _module_data_dir()
DEFAULT_BASELINE_DIR = MODULE_DIR / "maestro_baselines"
DEFAULT_BASELINE_XML_PATH = DEFAULT_BASELINE_DIR / "Pieza.xml"
SYNTHESIZER_VERSION = "1.6"


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


MachiningSpec = Union[
    LineMillingSpec,
    SlotMillingSpec,
    PolylineMillingSpec,
    CircleMillingSpec,
    SquaringMillingSpec,
    PocketMillingSpec,
    DrillingSpec,
    DrillingPatternSpec,
]


HydratedMachiningSpec = Union[
    _HydratedLineMillingSpec,
    _HydratedSlotMillingSpec,
    _HydratedPolylineMillingSpec,
    _HydratedCircleMillingSpec,
    _HydratedSquaringMillingSpec,
    _HydratedPocketMillingSpec,
    _HydratedDrillingSpec,
    _HydratedDrillingPatternSpec,
]


@dataclass(frozen=True)
class XnSpec:
    """Configuracion publica de `Xn`, la operacion nula final del workplan."""

    reference: str = "Absolute"
    x: float = -3700.0
    y: Optional[float] = None


def _normalize_xn_reference(value: Optional[str]) -> str:
    raw = (value or "Absolute").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "absolute": "Absolute",
        "absoluto": "Absolute",
        "relative": "Relative",
        "relativo": "Relative",
    }
    normalized = mapping.get(raw)
    if normalized is None:
        raise ValueError("Reference invalido para Xn. Valores admitidos: Absolute/Absoluto o Relative/Relativo.")
    return normalized


def build_xn_spec(
    *,
    reference: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
) -> XnSpec:
    """Construye la spec publica `Xn` con defaults observados en Maestro."""

    return XnSpec(
        reference=_normalize_xn_reference(reference),
        x=-3700.0 if x is None else float(x),
        y=None if y is None else float(y),
    )


def _normalize_xn_spec(xn: Optional[XnSpec]) -> XnSpec:
    if xn is None:
        return build_xn_spec()
    return build_xn_spec(
        reference=xn.reference,
        x=xn.x,
        y=xn.y,
    )


def _build_xn_step(
    step_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: XnSpec,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "Xn"},
    )
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.Xn")
    _append_blank_name(step).text = "Xn"
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    if spec.y is None:
        geometry_ref = _append_node(step, BASE_MODEL_NS, "GeometryID")
        _append_node(geometry_ref, UTILITY_NS, "ID", "0")
        _append_node(geometry_ref, UTILITY_NS, "ObjectType", attrib={f"{{{XSI_NS}}}nil": "true"})
        _set_xmlns(geometry_ref, "a", UTILITY_NS)
    else:
        _append_node(step, BASE_MODEL_NS, "GeometryID", attrib={f"{{{XSI_NS}}}nil": "true"})

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "Reference", spec.reference)
    _append_node(step, BASE_MODEL_NS, "Speed", "0")
    _append_node(step, BASE_MODEL_NS, "SpindleEnable", "Off")

    tool_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "Tool",
        "0",
        "System.Object",
        include_name=True,
        name_text="",
    )
    _set_xmlns(tool_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "X", _compact_number(spec.x))
    if spec.y is None:
        _append_node(step, BASE_MODEL_NS, "Y", attrib={f"{{{XSI_NS}}}nil": "true"})
    else:
        _append_node(step, BASE_MODEL_NS, "Y", _compact_number(spec.y))
    return step


def _ensure_xn_step(root: ET.Element, xn: XnSpec) -> None:
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if elements is None or workpiece is None:
        raise ValueError("La plantilla no contiene MainWorkplan/Elements o WorkPiece para sintetizar Xn.")

    for executable in list(elements):
        if _xsi_type(executable) == "Xn":
            elements.remove(executable)

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    [step_id] = _reserve_ids(root, 1)
    elements.append(_build_xn_step(step_id, workpiece_id, workpiece_object_type, _normalize_xn_spec(xn)))


@dataclass(frozen=True)
class PgmxSynthesisRequest:
    """Solicitud completa para sintetizar un `.pgmx` reutilizable desde la app."""

    baseline_path: Path
    output_path: Path
    piece: PgmxState
    source_pgmx_path: Optional[Path] = None
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = DEFAULT_MACHINING_ORDER
    xn: XnSpec = field(default_factory=XnSpec)


@dataclass(frozen=True)
class PgmxSynthesisResult:
    """Resultado de una sintesis ya escrita a disco."""

    output_path: Path
    piece: PgmxState
    sha256: str
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = DEFAULT_MACHINING_ORDER
    xn: XnSpec = field(default_factory=XnSpec)


def _hydrate_machining_spec(
    spec: MachiningSpec,
    source_pgmx_path: Optional[Path],
) -> HydratedMachiningSpec:
    if isinstance(spec, SlotMillingSpec):
        return _hydrate_slot_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, LineMillingSpec):
        return _hydrate_line_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, PolylineMillingSpec):
        return _hydrate_polyline_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, CircleMillingSpec):
        return _hydrate_circle_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, SquaringMillingSpec):
        return _hydrate_squaring_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, PocketMillingSpec):
        return _hydrate_pocket_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, DrillingSpec):
        return _hydrate_drilling_spec(spec, source_pgmx_path)
    if isinstance(spec, DrillingPatternSpec):
        return _hydrate_drilling_pattern_spec(spec, source_pgmx_path)
    raise TypeError(f"Spec de mecanizado no soportado: {type(spec).__name__}")


def _append_hydrated_machining(
    root: ET.Element,
    state: PgmxState,
    spec: HydratedMachiningSpec,
) -> None:
    if isinstance(spec, _HydratedLineMillingSpec):
        _append_line_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedSlotMillingSpec):
        _append_slot_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedPolylineMillingSpec):
        _append_polyline_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedCircleMillingSpec):
        _append_circle_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedSquaringMillingSpec):
        _append_squaring_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedPocketMillingSpec):
        _append_pocket_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedDrillingSpec):
        _append_drilling(root, state, spec)
        return
    if isinstance(spec, _HydratedDrillingPatternSpec):
        _append_drilling_pattern(root, state, spec)
        return
    raise TypeError(f"Spec hidratado no soportado: {type(spec).__name__}")


def _split_hydrated_machinings(
    specs: Sequence[HydratedMachiningSpec],
) -> tuple[
    list[_HydratedLineMillingSpec],
    list[_HydratedSlotMillingSpec],
    list[_HydratedPolylineMillingSpec],
    list[_HydratedCircleMillingSpec],
    list[_HydratedSquaringMillingSpec],
    list[_HydratedPocketMillingSpec],
    list[_HydratedDrillingSpec],
    list[_HydratedDrillingPatternSpec],
]:
    line_millings: list[_HydratedLineMillingSpec] = []
    slot_millings: list[_HydratedSlotMillingSpec] = []
    polyline_millings: list[_HydratedPolylineMillingSpec] = []
    circle_millings: list[_HydratedCircleMillingSpec] = []
    squaring_millings: list[_HydratedSquaringMillingSpec] = []
    pocket_millings: list[_HydratedPocketMillingSpec] = []
    drillings: list[_HydratedDrillingSpec] = []
    drilling_patterns: list[_HydratedDrillingPatternSpec] = []
    for spec in specs:
        if isinstance(spec, _HydratedLineMillingSpec):
            line_millings.append(spec)
        elif isinstance(spec, _HydratedSlotMillingSpec):
            slot_millings.append(spec)
        elif isinstance(spec, _HydratedPolylineMillingSpec):
            polyline_millings.append(spec)
        elif isinstance(spec, _HydratedCircleMillingSpec):
            circle_millings.append(spec)
        elif isinstance(spec, _HydratedSquaringMillingSpec):
            squaring_millings.append(spec)
        elif isinstance(spec, _HydratedPocketMillingSpec):
            pocket_millings.append(spec)
        elif isinstance(spec, _HydratedDrillingSpec):
            drillings.append(spec)
        elif isinstance(spec, _HydratedDrillingPatternSpec):
            drilling_patterns.append(spec)
    return (
        line_millings,
        slot_millings,
        polyline_millings,
        circle_millings,
        squaring_millings,
        pocket_millings,
        drillings,
        drilling_patterns,
    )


def _normalize_machining_order(value: Optional[Sequence[str]]) -> tuple[str, ...]:
    default_order = DEFAULT_MACHINING_ORDER
    aliases = {
        "lines": "line",
        "line_milling": "line",
        "line_millings": "line",
        "slots": "slot",
        "slot_milling": "slot",
        "slot_millings": "slot",
        "canal": "slot",
        "canales": "slot",
        "ranura": "slot",
        "ranuras": "slot",
        "polyline_milling": "polyline",
        "polyline_millings": "polyline",
        "division": "polyline",
        "divisions": "polyline",
        "cutting": "polyline",
        "circle_milling": "circle",
        "circle_millings": "circle",
        "squaring_milling": "squaring",
        "squaring_millings": "squaring",
        "square": "squaring",
        "pocket": "pocket",
        "pockets": "pocket",
        "pocket_milling": "pocket",
        "pocket_millings": "pocket",
        "vaciado": "pocket",
        "vaciados": "pocket",
        "drilling": "drilling",
        "drilling_millings": "drilling",
        "drilling_pattern": "drilling_pattern",
        "drilling_patterns": "drilling_pattern",
        "hole_pattern": "drilling_pattern",
        "hole_patterns": "drilling_pattern",
        "pattern": "drilling_pattern",
        "patterns": "drilling_pattern",
        "patron": "drilling_pattern",
        "patrones": "drilling_pattern",
        "repeticion": "drilling_pattern",
        "repeticiones": "drilling_pattern",
    }
    ordered: list[str] = []
    for raw_item in value or default_order:
        normalized = aliases.get(str(raw_item or "").strip().lower(), str(raw_item or "").strip().lower())
        if normalized not in default_order or normalized in ordered:
            continue
        ordered.append(normalized)
    for item in default_order:
        if item not in ordered:
            ordered.append(item)
    return tuple(ordered)


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


def _validate_tool_sinking_lengths(
    state: PgmxState,
    line_millings: Sequence[_HydratedLineMillingSpec],
    slot_millings: Sequence[_HydratedSlotMillingSpec],
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
    circle_millings: Sequence[_HydratedCircleMillingSpec],
    squaring_millings: Sequence[_HydratedSquaringMillingSpec],
    pocket_millings: Sequence[_HydratedPocketMillingSpec],
    drillings: Sequence[_HydratedDrillingSpec],
    drilling_patterns: Sequence[_HydratedDrillingPatternSpec] = (),
) -> None:
    """Aplica la validacion de `sinking_length` a todos los mecanizados del request."""

    tool_catalog = _load_tool_catalog()
    for spec in line_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in slot_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in polyline_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in circle_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in squaring_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in pocket_millings:
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in drillings:
        _validate_tool_type_for_drilling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_drilling_spec(state, spec, tool_catalog)
    for spec in drilling_patterns:
        _validate_tool_type_for_drilling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_drilling_spec(state, spec, tool_catalog)


# ============================================================================
# Public read/build API
# ============================================================================

def read_pgmx_state(path: Path) -> PgmxState:
    """Lee un baseline Maestro y devuelve el estado basico de pieza, origen y area.

    No interpreta mecanizados. Sirve para reutilizar dimensiones reales y para
    tomar un baseline o un `source_pgmx_path` como punto de partida.
    """

    root, _, _ = _load_pgmx_container(path)

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


def _apply_slot_millings(
    root: ET.Element,
    state: PgmxState,
    slot_millings: Sequence[_HydratedSlotMillingSpec],
) -> None:
    for slot_milling in slot_millings:
        _append_slot_milling(root, state, slot_milling)


def _apply_polyline_millings(
    root: ET.Element,
    state: PgmxState,
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
) -> None:
    for polyline_milling in polyline_millings:
        _append_polyline_milling(root, state, polyline_milling)


def _apply_circle_millings(
    root: ET.Element,
    state: PgmxState,
    circle_millings: Sequence[_HydratedCircleMillingSpec],
) -> None:
    for circle_milling in circle_millings:
        _append_circle_milling(root, state, circle_milling)


def _apply_squaring_millings(
    root: ET.Element,
    state: PgmxState,
    squaring_millings: Sequence[_HydratedSquaringMillingSpec],
) -> None:
    for squaring_milling in squaring_millings:
        _append_squaring_milling(root, state, squaring_milling)


def _apply_drillings(
    root: ET.Element,
    state: PgmxState,
    drillings: Sequence[_HydratedDrillingSpec],
) -> None:
    # Maestro guarda consistentemente los taladros multicara agrupados por
    # plano. Mantener ese orden reduce diferencias contra los ejemplos manuales
    # y evita mezclar caras arbitrariamente segun el orden de entrada.
    plane_priority = {
        "Top": 0,
        "Front": 1,
        "Back": 2,
        "Left": 3,
        "Right": 4,
    }
    ordered_drillings = sorted(
        enumerate(drillings),
        key=lambda item: (plane_priority.get(item[1].plane_name, 99), item[0]),
    )
    for _, drilling in ordered_drillings:
        _append_drilling(root, state, drilling)


def _drilling_plane_priority(plane_name: str) -> int:
    plane_priority = {
        "Top": 0,
        "Front": 1,
        "Back": 2,
        "Left": 3,
        "Right": 4,
    }
    return plane_priority.get(plane_name, 99)


def _apply_drilling_patterns(
    root: ET.Element,
    state: PgmxState,
    drilling_patterns: Sequence[_HydratedDrillingPatternSpec],
) -> None:
    ordered_drilling_patterns = sorted(
        enumerate(drilling_patterns),
        key=lambda item: (_drilling_plane_priority(item[1].plane_name), item[0]),
    )
    for _, drilling_pattern in ordered_drilling_patterns:
        _append_drilling_pattern(root, state, drilling_pattern)


def _apply_pocket_millings(
    root: ET.Element,
    state: PgmxState,
    pocket_millings: Sequence[_HydratedPocketMillingSpec],
) -> None:
    for pocket_milling in pocket_millings:
        _append_pocket_milling(root, state, pocket_milling)


# ============================================================================
# Public execution API
# ============================================================================

def build_synthesis_request(
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
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
    slot_millings: Optional[Sequence[SlotMillingSpec]] = None,
    polyline_millings: Optional[Sequence[PolylineMillingSpec]] = None,
    circle_millings: Optional[Sequence[CircleMillingSpec]] = None,
    squaring_millings: Optional[Sequence[SquaringMillingSpec]] = None,
    pocket_millings: Optional[Sequence[PocketMillingSpec]] = None,
    drillings: Optional[Sequence[DrillingSpec]] = None,
    drilling_patterns: Optional[Sequence[DrillingPatternSpec]] = None,
    ordered_machinings: Optional[Sequence[MachiningSpec]] = None,
    machining_order: Optional[Sequence[str]] = None,
    xn: Optional[XnSpec] = None,
) -> PgmxSynthesisRequest:
    """Arma una solicitud reusable de sintesis para el flujo principal.

    Orden recomendado de uso:
    1. leer o definir la pieza
    2. construir `LineMillingSpec`, `SlotMillingSpec`, `PolylineMillingSpec`,
       `CircleMillingSpec`, `SquaringMillingSpec`, `DrillingSpec` y
       `DrillingPatternSpec`, y
       opcionalmente `XnSpec`
    3. construir el request
    4. ejecutar `synthesize_request(...)`

    Soporte de contenedores baseline:
    - `baseline_path`: `.pgmx`, `Pieza.xml` o carpeta que contenga `Pieza.xml`
      Si no se indica, usa `DEFAULT_BASELINE_DIR`.
    - `source_pgmx_path`: `.pgmx`, `Pieza.xml` o carpeta usada como plantilla de serializacion
    """

    if output_path is None:
        raise ValueError("`output_path` es obligatorio para construir un `PgmxSynthesisRequest`.")

    effective_baseline_path = Path(baseline_path) if baseline_path is not None else DEFAULT_BASELINE_DIR
    effective_output_path = Path(output_path)

    base_piece = piece or (
        read_pgmx_state(source_pgmx_path) if source_pgmx_path else read_pgmx_state(effective_baseline_path)
    )
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
        baseline_path=effective_baseline_path,
        output_path=effective_output_path,
        piece=target_piece,
        source_pgmx_path=source_pgmx_path,
        line_millings=tuple(line_millings or ()),
        slot_millings=tuple(slot_millings or ()),
        polyline_millings=tuple(polyline_millings or ()),
        circle_millings=tuple(circle_millings or ()),
        squaring_millings=tuple(squaring_millings or ()),
        pocket_millings=tuple(pocket_millings or ()),
        drillings=tuple(drillings or ()),
        drilling_patterns=tuple(drilling_patterns or ()),
        ordered_machinings=tuple(ordered_machinings or ()),
        machining_order=_normalize_machining_order(machining_order),
        xn=_normalize_xn_spec(xn),
    )


def synthesize_request(request: PgmxSynthesisRequest) -> PgmxSynthesisResult:
    """Ejecuta una solicitud de sintesis y escribe el `.pgmx` resultante.

    Esta es la funcion principal para el flujo programatico.
    """

    baseline_root, baseline_entries, _ = _load_pgmx_container(request.baseline_path)
    hydrated_line_millings = [
        _hydrate_line_milling_spec(line_milling, request.source_pgmx_path)
        for line_milling in request.line_millings
    ]
    hydrated_slot_millings = [
        _hydrate_slot_milling_spec(slot_milling, request.source_pgmx_path)
        for slot_milling in request.slot_millings
    ]
    hydrated_polyline_millings = [
        _hydrate_polyline_milling_spec(polyline_milling, request.source_pgmx_path)
        for polyline_milling in request.polyline_millings
    ]
    hydrated_circle_millings = [
        _hydrate_circle_milling_spec(circle_milling, request.source_pgmx_path)
        for circle_milling in request.circle_millings
    ]
    hydrated_squaring_millings = [
        _hydrate_squaring_milling_spec(squaring_milling, request.source_pgmx_path)
        for squaring_milling in request.squaring_millings
    ]
    hydrated_pocket_millings = [
        _hydrate_pocket_milling_spec(pocket_milling, request.source_pgmx_path)
        for pocket_milling in request.pocket_millings
    ]
    hydrated_drillings = [
        _hydrate_drilling_spec(drilling, request.source_pgmx_path)
        for drilling in request.drillings
    ]
    hydrated_drilling_patterns = [
        _hydrate_drilling_pattern_spec(drilling_pattern, request.source_pgmx_path)
        for drilling_pattern in request.drilling_patterns
    ]
    hydrated_ordered_machinings = [
        _hydrate_machining_spec(spec, request.source_pgmx_path)
        for spec in request.ordered_machinings
    ]
    (
        ordered_line_millings,
        ordered_slot_millings,
        ordered_polyline_millings,
        ordered_circle_millings,
        ordered_squaring_millings,
        ordered_pocket_millings,
        ordered_drillings,
        ordered_drilling_patterns,
    ) = _split_hydrated_machinings(hydrated_ordered_machinings)
    normalized_xn = _normalize_xn_spec(request.xn)
    _validate_tool_sinking_lengths(
        request.piece,
        hydrated_line_millings + ordered_line_millings,
        hydrated_slot_millings + ordered_slot_millings,
        hydrated_polyline_millings + ordered_polyline_millings,
        hydrated_circle_millings + ordered_circle_millings,
        hydrated_squaring_millings + ordered_squaring_millings,
        hydrated_pocket_millings + ordered_pocket_millings,
        hydrated_drillings + ordered_drillings,
        hydrated_drilling_patterns + ordered_drilling_patterns,
    )

    _apply_piece_state(baseline_root, request.piece)
    for spec in hydrated_ordered_machinings:
        _append_hydrated_machining(baseline_root, request.piece, spec)
    apply_group = {
        "line": lambda: _apply_line_millings(
            baseline_root,
            request.piece,
            hydrated_line_millings,
        ),
        "slot": lambda: _apply_slot_millings(
            baseline_root,
            request.piece,
            hydrated_slot_millings,
        ),
        "polyline": lambda: _apply_polyline_millings(
            baseline_root,
            request.piece,
            hydrated_polyline_millings,
        ),
        "circle": lambda: _apply_circle_millings(
            baseline_root,
            request.piece,
            hydrated_circle_millings,
        ),
        "squaring": lambda: _apply_squaring_millings(
            baseline_root,
            request.piece,
            hydrated_squaring_millings,
        ),
        "pocket": lambda: _apply_pocket_millings(
            baseline_root,
            request.piece,
            hydrated_pocket_millings,
        ),
        "drilling": lambda: _apply_drillings(
            baseline_root,
            request.piece,
            hydrated_drillings,
        ),
        "drilling_pattern": lambda: _apply_drilling_patterns(
            baseline_root,
            request.piece,
            hydrated_drilling_patterns,
        ),
    }
    for group_name in _normalize_machining_order(request.machining_order):
        apply_group[group_name]()
    _ensure_xn_step(baseline_root, normalized_xn)

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
        slot_millings=request.slot_millings,
        polyline_millings=request.polyline_millings,
        circle_millings=request.circle_millings,
        squaring_millings=request.squaring_millings,
        pocket_millings=request.pocket_millings,
        drillings=request.drillings,
        drilling_patterns=request.drilling_patterns,
        ordered_machinings=request.ordered_machinings,
        machining_order=_normalize_machining_order(request.machining_order),
        xn=normalized_xn,
    )


def synthesize_pgmx(
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    source_pgmx_path: Optional[Path] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    line_milling: Optional[LineMillingSpec] = None,
    slot_milling: Optional[SlotMillingSpec] = None,
    polyline_milling: Optional[PolylineMillingSpec] = None,
    circle_milling: Optional[CircleMillingSpec] = None,
    squaring_milling: Optional[SquaringMillingSpec] = None,
    drilling: Optional[DrillingSpec] = None,
    drilling_pattern: Optional[DrillingPatternSpec] = None,
    xn: Optional[XnSpec] = None,
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
        slot_millings=[slot_milling] if slot_milling is not None else (),
        polyline_millings=[polyline_milling] if polyline_milling is not None else (),
        circle_millings=[circle_milling] if circle_milling is not None else (),
        squaring_millings=[squaring_milling] if squaring_milling is not None else (),
        drillings=[drilling] if drilling is not None else (),
        drilling_patterns=[drilling_pattern] if drilling_pattern is not None else (),
        xn=xn,
    )
    return synthesize_request(request).piece
