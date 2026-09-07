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
from ..common.geometry import (
    _build_start_point,
    _build_toolpath,
    _build_toolpath_description,
    _trimmed_curve_spec,
)
from ..common.piece import (
    _drilling_axis_span,
    _drilling_axis_variable_name,
    _drilling_entry_point_and_direction,
    _normalize_plane_name,
    _plane_local_dimensions,
)
from ..common.tools import (
    _catalog_row_for_spec,
    _load_tool_catalog,
    _normalize_tool_resolution,
    _resolve_drilling_tool,
    _validate_tool_sinking_length_for_total_depth,
)
from ..common.xml import (
    BASE_MODEL_NS,
    DRILLING_NS,
    PGMX_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _build_depth_expression,
    _build_point_geometry,
    _build_property_expression,
    _build_working_step,
    _compact_number,
    _find_plane_ref,
    _qname,
    _reserve_ids,
    _set_xmlns,
    _text,
)

__all__ = [
    "DrillSpec",
    "build_drill_spec",
    "_HydratedDrillSpec",
    "_append_drilling",
    "_append_drilling_feature_payload",
    "_build_drill_feature",
    "_build_drill_operation",
    "_default_drill_family",
    "_drilling_bottom_condition_type",
    "_drilling_feature_depth_value",
    "_drilling_total_depth",
    "_hydrate_drill_spec",
    "_normalize_drill_family",
    "_normalize_drill_spec",
    "_uses_drilling_depth_expressions",
    "_validate_drilling_center",
    "_validate_tool_sinking_length_for_drill_spec",
]


@dataclass(frozen=True)
class DrillSpec:
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
    step_number: int = 0
    step_depth: float = 0.0
    feedrate: float = 0.0
    spindle: float = 0.0
    taper_height: float = 0.0
    center_x_expr: Optional[str] = None
    center_y_expr: Optional[str] = None
    is_enabled_expr: Optional[str] = None


@dataclass(frozen=True)
class _HydratedDrillSpec:
    """Datos internos de serializacion y herramienta para `DrillSpec`."""

    spec: DrillSpec
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

    @property
    def step_number(self) -> int:
        return self.spec.step_number

    @property
    def step_depth(self) -> float:
        return self.spec.step_depth

    @property
    def feedrate(self) -> float:
        return self.spec.feedrate

    @property
    def spindle(self) -> float:
        return self.spec.spindle

    @property
    def taper_height(self) -> float:
        return self.spec.taper_height

    @property
    def center_x_expr(self) -> Optional[str]:
        return self.spec.center_x_expr

    @property
    def center_y_expr(self) -> Optional[str]:
        return self.spec.center_y_expr

    @property
    def is_enabled_expr(self) -> Optional[str]:
        return self.spec.is_enabled_expr


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


def _normalize_peck_drilling(step_number: int, step_depth: float) -> tuple[int, float]:
    if step_number < 0:
        raise ValueError("step_number no puede ser negativo.")
    if step_depth < 0.0:
        raise ValueError("step_depth no puede ser negativo.")
    if step_number > 0 and step_depth > 0.0:
        raise ValueError("step_number y step_depth son mutuamente excluyentes: usar uno o el otro.")
    return step_number, step_depth


def _normalize_drill_spec(drilling: DrillSpec) -> DrillSpec:
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
    normalized_step_number, normalized_step_depth = _normalize_peck_drilling(
        int(drilling.step_number), float(drilling.step_depth)
    )
    taper_height_value = float(drilling.taper_height)
    if taper_height_value < 0.0:
        raise ValueError("taper_height no puede ser negativo.")
    feedrate_value = float(drilling.feedrate)
    if feedrate_value < 0.0:
        raise ValueError("feedrate no puede ser negativo.")
    spindle_value = float(drilling.spindle)
    if spindle_value < 0.0:
        raise ValueError("spindle no puede ser negativo.")
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
        step_number=normalized_step_number,
        step_depth=normalized_step_depth,
        feedrate=feedrate_value,
        spindle=spindle_value,
        taper_height=taper_height_value,
    )


def build_drill_spec(
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
    step_number: Optional[int] = None,
    step_depth: Optional[float] = None,
    feedrate: Optional[float] = None,
    spindle: Optional[float] = None,
    taper_height: Optional[float] = None,
    center_x_expr: Optional[str] = None,
    center_y_expr: Optional[str] = None,
    is_enabled_expr: Optional[str] = None,
) -> DrillSpec:
    """Construye un `DrillSpec` reusable para taladros puntuales."""

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
    return DrillSpec(
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
        step_number=0 if step_number is None else int(step_number),
        step_depth=0.0 if step_depth is None else float(step_depth),
        feedrate=0.0 if feedrate is None else float(feedrate),
        spindle=0.0 if spindle is None else float(spindle),
        taper_height=0.0 if taper_height is None else float(taper_height),
        center_x_expr=None if center_x_expr is None else str(center_x_expr).strip() or None,
        center_y_expr=None if center_y_expr is None else str(center_y_expr).strip() or None,
        is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
    )


def _hydrate_drill_spec(
    drilling: DrillSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedDrillSpec:
    del source_pgmx_path
    normalized_drilling = _normalize_drill_spec(drilling)
    tool_catalog = _load_tool_catalog()
    resolved_tool_id, resolved_tool_name, resolved_tool_object_type = _resolve_drilling_tool(
        normalized_drilling,
        tool_catalog,
    )
    return _HydratedDrillSpec(
        spec=normalized_drilling,
        resolved_tool_id=resolved_tool_id,
        resolved_tool_name=resolved_tool_name,
        resolved_tool_object_type=resolved_tool_object_type,
    )


def _drilling_feature_depth_value(state, spec: _HydratedDrillSpec) -> float:
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


def _drilling_total_depth(state, spec: _HydratedDrillSpec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return _drilling_axis_span(state, spec.plane_name) + depth_spec.extra_depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del taladro no pasante no puede quedar vacia.")
    return depth_spec.target_depth


def _drilling_bottom_condition_type(spec: _HydratedDrillSpec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return "a:ThroughHoleBottom"
    if spec.drill_family == "Conical" and spec.tool_object_type == "System.Object":
        return "a:ConicalHoleBottom"
    return "a:FlatHoleBottom"


def _uses_drilling_depth_expressions(spec: _HydratedDrillSpec) -> bool:
    return _normalize_milling_depth_spec(spec.depth_spec).is_through


def _build_drill_feature(
    state,
    spec: _HydratedDrillSpec,
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
    _append_node(feature, DRILLING_NS, "TaperHeight", _compact_number(spec.taper_height))
    return feature


def _append_drilling_feature_payload(
    parent: ET.Element,
    state,
    spec: _HydratedDrillSpec,
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
    _append_node(parent, DRILLING_NS, "TaperHeight", _compact_number(spec.taper_height))


def _build_drill_operation(
    state,
    spec: _HydratedDrillSpec,
    operation_id: str,
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:DrillingOperation"},
    )
    _set_xmlns(operation, "a", DRILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation")
    _append_blank_name(operation)
    _append_node(operation, PGMX_NS, "ActivateCNCCorrection", "true")
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)

    entry_point, direction = _drilling_entry_point_and_direction(state, spec)
    total_depth = _drilling_total_depth(state, spec)
    clearance_point = (
        entry_point[0] - (direction[0] * spec.security_plane),
        entry_point[1] - (direction[1] * spec.security_plane),
        entry_point[2] - (direction[2] * spec.security_plane),
    )
    cut_point = (
        entry_point[0] + (direction[0] * total_depth),
        entry_point[1] + (direction[1] * total_depth),
        entry_point[2] + (direction[2] * total_depth),
    )
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            _trimmed_curve_spec(_build_toolpath_description(clearance_point, entry_point)),
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "TrajectoryPath",
            _trimmed_curve_spec(_build_toolpath_description(entry_point, cut_point)),
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            _trimmed_curve_spec(_build_toolpath_description(cut_point, clearance_point)),
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
    _append_node(technology, PGMX_NS, "Feedrate", _compact_number(spec.feedrate))
    _append_node(technology, PGMX_NS, "CutSpeed", "0")
    _append_node(technology, PGMX_NS, "Spindle", _compact_number(spec.spindle))
    _append_object_ref(
        operation,
        PGMX_NS,
        "ToolKey",
        spec.tool_id,
        spec.tool_object_type,
        include_name=True,
        name_text=spec.tool_name,
    )
    _append_node(operation, PGMX_NS, "OvercutLength", "0")
    _append_node(operation, DRILLING_NS, "CuttingDepth", "0")
    use_peck = spec.step_number > 0 or spec.step_depth > 0.0
    if use_peck:
        machining_strategy = _append_node(
            operation,
            DRILLING_NS,
            "MachiningStrategy",
            attrib={f"{{{XSI_NS}}}type": "b:MultiStepDrilling"},
        )
        _set_xmlns(machining_strategy, "b", BASE_MODEL_NS)
        is_step_depth = spec.step_depth > 0.0
        _append_node(machining_strategy, BASE_MODEL_NS, "IsStepDepth", "true" if is_step_depth else "false")
        _append_node(machining_strategy, BASE_MODEL_NS, "StepDepth", _compact_number(spec.step_depth))
        _append_node(machining_strategy, BASE_MODEL_NS, "StepNumber", str(spec.step_number))
    else:
        machining_strategy = _append_node(
            operation,
            DRILLING_NS,
            "MachiningStrategy",
            attrib={f"{{{XSI_NS}}}type": "b:SingleStepDrilling"},
        )
        _set_xmlns(machining_strategy, "b", BASE_MODEL_NS)
    return operation


def _append_drilling(root: ET.Element, state, spec: _HydratedDrillSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el taladro.")

    _validate_drilling_center(state, spec)
    _drilling_feature_depth_value(state, spec)

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _drilling_axis_variable_name(workpiece, spec.plane_name)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_drilling_depth_expressions(spec)
    has_x_expr = spec.center_x_expr is not None
    has_y_expr = spec.center_y_expr is not None
    has_enabled_expr = spec.is_enabled_expr is not None
    n_total = (
        4
        + (2 if uses_depth_expressions else 0)
        + has_x_expr
        + has_y_expr
        + has_enabled_expr
    )
    reserved_ids = _reserve_ids(root, n_total, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    i = 4
    start_expression_id = end_expression_id = None
    if uses_depth_expressions:
        start_expression_id = reserved_ids[i]; i += 1
        end_expression_id = reserved_ids[i]; i += 1
    x_expr_id = None
    if has_x_expr:
        x_expr_id = reserved_ids[i]; i += 1
    y_expr_id = None
    if has_y_expr:
        y_expr_id = reserved_ids[i]; i += 1
    enabled_expr_id = reserved_ids[i] if has_enabled_expr else None

    geometries.append(
        _build_point_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            spec.center_x,
            spec.center_y,
            0.0,
        )
    )
    features.append(
        _build_drill_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
        )
    )
    operations.append(_build_drill_operation(state, spec, operation_id))
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            operation_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(
            _build_depth_expression(
                start_expression_id,
                feature_id,
                "StartDepth",
                depth_variable_name,
                referenced_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            )
        )
        expressions.append(
            _build_depth_expression(
                end_expression_id,
                feature_id,
                "EndDepth",
                depth_variable_name,
                referenced_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            )
        )
    if has_x_expr and x_expr_id is not None:
        expressions.append(
            _build_property_expression(
                x_expr_id,
                geometry_id,
                "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint",
                "X",
                spec.center_x_expr,
            )
        )
    if has_y_expr and y_expr_id is not None:
        expressions.append(
            _build_property_expression(
                y_expr_id,
                geometry_id,
                "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint",
                "Y",
                spec.center_y_expr,
            )
        )
    if has_enabled_expr and enabled_expr_id is not None:
        expressions.append(
            _build_property_expression(
                enabled_expr_id,
                step_id,
                "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep",
                "IsEnabled",
                spec.is_enabled_expr,
            )
        )


def _validate_drilling_center(state, spec: _HydratedDrillSpec) -> None:
    max_x, max_y = _plane_local_dimensions(state, spec.plane_name)
    if spec.center_x_expr is None:
        if spec.center_x < -1e-9 or spec.center_x > max_x + 1e-9:
            raise ValueError(
                f"El centro X del taladro cae fuera del plano '{spec.plane_name}': "
                f"{_compact_number(spec.center_x)} no pertenece a [0, {_compact_number(max_x)}]."
            )
    if spec.center_y_expr is None:
        if spec.center_y < -1e-9 or spec.center_y > max_y + 1e-9:
            raise ValueError(
                f"El centro Y del taladro cae fuera del plano '{spec.plane_name}': "
                f"{_compact_number(spec.center_y)} no pertenece a [0, {_compact_number(max_y)}]."
            )


def _validate_tool_sinking_length_for_drill_spec(
    state,
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    if spec.tool_object_type == "System.Object":
        return

    catalog_entry = _catalog_row_for_spec(spec, tool_catalog)
    _validate_tool_sinking_length_for_total_depth(
        spec,
        catalog_entry,
        total_depth=_drilling_total_depth(state, spec),
        operation_name="taladro",
    )
