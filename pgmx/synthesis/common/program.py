"""Program-level contracts for PGMX synthesis."""

from __future__ import annotations

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
from .xml import (
    BASE_MODEL_NS,
    UTILITY_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _compact_number,
    _qname,
    _reserve_ids,
    _set_xmlns,
    _text,
    _xsi_type,
)

__all__ = [
    "DEFAULT_MACHINING_ORDER",
    "HydratedMachiningSpec",
    "MachiningSpec",
    "PgmxState",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "XnSpec",
    "_append_hydrated_machining",
    "_build_xn_step",
    "_ensure_xn_step",
    "_hydrate_machining_spec",
    "_normalize_machining_order",
    "_normalize_xn_reference",
    "_normalize_xn_spec",
    "_split_hydrated_machinings",
    "build_xn_spec",
]


DEFAULT_MACHINING_ORDER = ("line", "slot", "polyline", "circle", "squaring", "pocket", "drilling", "drilling_pattern")


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
