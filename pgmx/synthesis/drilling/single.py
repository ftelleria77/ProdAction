"""Single drilling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.piece import _drilling_axis_span, _normalize_plane_name, _plane_local_dimensions
from ..common.tools import (
    _load_tool_catalog,
    _normalize_tool_resolution,
    _resolve_drilling_tool,
    _validate_tool_sinking_length_for_total_depth,
)
from ..common.xml import (
    DRILLING_NS,
    PGMX_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _compact_number,
    _qname,
    _set_xmlns,
)

__all__ = [
    "DrillingSpec",
    "build_drilling_spec",
    "_HydratedDrillingSpec",
    "_append_drilling_feature_payload",
    "_build_drilling_feature",
    "_default_drill_family",
    "_drilling_bottom_condition_type",
    "_drilling_feature_depth_value",
    "_drilling_total_depth",
    "_hydrate_drilling_spec",
    "_normalize_drill_family",
    "_normalize_drilling_spec",
    "_uses_drilling_depth_expressions",
    "_validate_drilling_center",
    "_validate_tool_sinking_length_for_drilling_spec",
]


@dataclass(frozen=True)
class DrillingSpec:
    """Descripcion reutilizable de un taladro puntual sobre una cara de la pieza."""

    center_x: float
    center_y: float
    diameter: float
    feature_name: str = "Taladrado"
    plane_name: str = "Top"
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    drill_family: str = "Flat"
    tool_resolution: str = "Auto"
    tool_id: str = "0"
    tool_name: str = ""


@dataclass(frozen=True)
class _HydratedDrillingSpec:
    """Datos internos de serializacion y herramienta para `DrillingSpec`."""

    spec: DrillingSpec
    preferred_id_start: Optional[int] = None
    resolved_tool_id: str = "0"
    resolved_tool_name: str = ""
    resolved_tool_object_type: str = "System.Object"

    @property
    def center_x(self) -> float:
        return self.spec.center_x

    @property
    def center_y(self) -> float:
        return self.spec.center_y

    @property
    def diameter(self) -> float:
        return self.spec.diameter

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def drill_family(self) -> str:
        return self.spec.drill_family

    @property
    def tool_resolution(self) -> str:
        return self.spec.tool_resolution

    @property
    def tool_id(self) -> str:
        return self.resolved_tool_id

    @property
    def tool_name(self) -> str:
        return self.resolved_tool_name

    @property
    def tool_object_type(self) -> str:
        return self.resolved_tool_object_type


def _normalize_drill_family(value: Optional[str]) -> str:
    raw = (value or "Flat").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "flat": "Flat",
        "plana": "Flat",
        "plano": "Flat",
        "conical": "Conical",
        "conica": "Conical",
        "conico": "Conical",
        "lanza": "Conical",
        "puntadelanza": "Conical",
        "countersunk": "Countersunk",
        "abocinado": "Countersunk",
        "abocinada": "Countersunk",
    }
    if raw not in mapping:
        raise ValueError(
            "DrillFamily invalido. Valores admitidos: Flat/Plana, Conical/Lanza o Countersunk/Abocinado."
        )
    return mapping[raw]


def _default_drill_family(
    plane_name: str,
    diameter: float,
    depth_spec: MillingDepthSpec,
    requested_family: Optional[str],
) -> str:
    if requested_family is not None:
        return _normalize_drill_family(requested_family)
    if depth_spec.is_through and plane_name == "Top" and math.isclose(float(diameter), 5.0, abs_tol=1e-9):
        return "Conical"
    return "Flat"


def _normalize_drilling_spec(drilling: DrillingSpec) -> DrillingSpec:
    normalized_plane_name = _normalize_plane_name(drilling.plane_name)
    normalized_depth_spec = _normalize_milling_depth_spec(drilling.depth_spec)
    normalized_drill_family = _normalize_drill_family(drilling.drill_family)
    if normalized_drill_family == "Countersunk":
        raise ValueError(
            "La familia `Countersunk/Abocinado` todavia no tiene un caso manual validado en Maestro."
        )
    if normalized_drill_family == "Conical":
        if normalized_plane_name != "Top":
            raise ValueError("La broca conica solo esta validada por ahora sobre la cara `Top`.")
        if not math.isclose(float(drilling.diameter), 5.0, abs_tol=1e-9):
            raise ValueError("La broca conica relevada hasta ahora solo existe en `D5`.")
    diameter_value = float(drilling.diameter)
    if diameter_value <= 0.0:
        raise ValueError("El diametro del taladro debe ser mayor que cero.")
    security_plane_value = float(drilling.security_plane)
    if security_plane_value < 0.0:
        raise ValueError("SecurityPlane no puede ser negativo.")
    return replace(
        drilling,
        center_x=float(drilling.center_x),
        center_y=float(drilling.center_y),
        diameter=diameter_value,
        feature_name=(drilling.feature_name or "Taladrado").strip() or "Taladrado",
        plane_name=normalized_plane_name,
        security_plane=security_plane_value,
        depth_spec=normalized_depth_spec,
        drill_family=normalized_drill_family,
        tool_resolution=_normalize_tool_resolution(drilling.tool_resolution),
        tool_id=(drilling.tool_id or "").strip() or "0",
        tool_name=(drilling.tool_name or "").strip(),
    )


def build_drilling_spec(
    *,
    center_x: float,
    center_y: float,
    diameter: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    security_plane: Optional[float] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    drill_family: Optional[str] = None,
    tool_resolution: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> DrillingSpec:
    """Construye un `DrillingSpec` reusable para taladros puntuales."""

    normalized_plane_name = _normalize_plane_name(plane_name)
    depth_spec = build_milling_depth_spec(
        is_through=is_through,
        target_depth=target_depth,
        extra_depth=extra_depth,
    )
    effective_drill_family = _default_drill_family(
        normalized_plane_name,
        float(diameter),
        depth_spec,
        drill_family,
    )
    return DrillingSpec(
        center_x=float(center_x),
        center_y=float(center_y),
        diameter=float(diameter),
        feature_name=(feature_name or "Taladrado").strip() or "Taladrado",
        plane_name=normalized_plane_name,
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        drill_family=effective_drill_family,
        tool_resolution=_normalize_tool_resolution(tool_resolution or "Auto"),
        tool_id=(tool_id or "0").strip() or "0",
        tool_name=(tool_name or "").strip(),
    )


def _hydrate_drilling_spec(
    drilling: DrillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedDrillingSpec:
    del source_pgmx_path
    normalized_drilling = _normalize_drilling_spec(drilling)
    tool_catalog = _load_tool_catalog()
    resolved_tool_id, resolved_tool_name, resolved_tool_object_type = _resolve_drilling_tool(
        normalized_drilling,
        tool_catalog,
    )
    return _HydratedDrillingSpec(
        spec=normalized_drilling,
        resolved_tool_id=resolved_tool_id,
        resolved_tool_name=resolved_tool_name,
        resolved_tool_object_type=resolved_tool_object_type,
    )


def _drilling_feature_depth_value(state, spec: _HydratedDrillingSpec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    plane_span = _drilling_axis_span(state, spec.plane_name)
    if depth_spec.is_through:
        return plane_span
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del taladro no pasante no puede quedar vacia.")
    if depth_spec.target_depth > plane_span + 1e-9:
        raise ValueError(
            "La profundidad del taladro no pasante no puede superar el espesor util de la cara."
        )
    return depth_spec.target_depth


def _drilling_total_depth(state, spec: _HydratedDrillingSpec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return _drilling_axis_span(state, spec.plane_name) + depth_spec.extra_depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del taladro no pasante no puede quedar vacia.")
    return depth_spec.target_depth


def _drilling_bottom_condition_type(spec: _HydratedDrillingSpec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return "a:ThroughHoleBottom"
    if spec.drill_family == "Conical" and spec.tool_object_type == "System.Object":
        return "a:ConicalHoleBottom"
    return "a:FlatHoleBottom"


def _uses_drilling_depth_expressions(spec: _HydratedDrillingSpec) -> bool:
    return _normalize_milling_depth_spec(spec.depth_spec).is_through


def _build_drilling_feature(
    state,
    spec: _HydratedDrillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:RoundHole"},
    )
    _set_xmlns(feature, "a", DRILLING_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint",
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _drilling_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", DRILLING_NS)
    if _drilling_bottom_condition_type(spec) == "a:ConicalHoleBottom":
        _append_node(bottom_condition, DRILLING_NS, "TipAngle", "0")
        _append_node(bottom_condition, DRILLING_NS, "TipRadius", "0")
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_drilling_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    _append_node(feature, DRILLING_NS, "Diameter", _compact_number(spec.diameter))
    _append_node(feature, DRILLING_NS, "TaperHeight", "0")
    return feature


def _append_drilling_feature_payload(
    parent: ET.Element,
    state,
    spec: _HydratedDrillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    *,
    bottom_condition_type: Optional[str] = None,
) -> None:
    _append_key(parent, feature_id, "ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole")
    _append_blank_name(parent).text = spec.feature_name
    _append_object_ref(
        parent,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint",
    )
    operation_ids = _append_node(parent, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
    )
    _append_object_ref(parent, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    effective_bottom_condition = bottom_condition_type or _drilling_bottom_condition_type(spec)
    bottom_condition = _append_node(
        parent,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": effective_bottom_condition},
    )
    if effective_bottom_condition.startswith("b:"):
        _set_xmlns(bottom_condition, "b", DRILLING_NS)
    else:
        _set_xmlns(bottom_condition, "a", DRILLING_NS)
    if "ThroughHoleBottom" in effective_bottom_condition:
        _append_node(bottom_condition, DRILLING_NS, "IsFlat", "false")
    if "ConicalHoleBottom" in effective_bottom_condition:
        _append_node(bottom_condition, DRILLING_NS, "TipAngle", "0")
        _append_node(bottom_condition, DRILLING_NS, "TipRadius", "0")
    depth = _append_node(parent, PGMX_NS, "Depth")
    depth_value = _compact_number(_drilling_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    _append_node(parent, DRILLING_NS, "Diameter", _compact_number(spec.diameter))
    _append_node(parent, DRILLING_NS, "TaperHeight", "0")


def _validate_drilling_center(state, spec: _HydratedDrillingSpec) -> None:
    max_x, max_y = _plane_local_dimensions(state, spec.plane_name)
    if spec.center_x < -1e-9 or spec.center_x > max_x + 1e-9:
        raise ValueError(
            f"El centro X del taladro cae fuera del plano '{spec.plane_name}': "
            f"{_compact_number(spec.center_x)} no pertenece a [0, {_compact_number(max_x)}]."
        )
    if spec.center_y < -1e-9 or spec.center_y > max_y + 1e-9:
        raise ValueError(
            f"El centro Y del taladro cae fuera del plano '{spec.plane_name}': "
            f"{_compact_number(spec.center_y)} no pertenece a [0, {_compact_number(max_y)}]."
        )


def _validate_tool_sinking_length_for_drilling_spec(
    state,
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    if spec.tool_object_type == "System.Object":
        return

    catalog_entry = tool_catalog.get(spec.tool_id)
    _validate_tool_sinking_length_for_total_depth(
        spec,
        catalog_entry,
        total_depth=_drilling_total_depth(state, spec),
        operation_name="taladro",
    )
