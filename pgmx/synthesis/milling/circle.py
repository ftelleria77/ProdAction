"""Circle milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from ..common.depth import (
    MillingDepthSpec,
    _extract_depth_spec_from_template,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.geometry import (
    _CurveSpec,
    GeometryProfileSpec,
    _circle_curve_spec,
    _curve_spec_from_toolpath_node,
    _parse_circle_geometry_profile,
    build_circle_geometry_profile,
    build_compensated_toolpath_profile,
)
from ..common.hydration import _load_pgmx_container
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    _extract_approach_spec_from_operation,
    _extract_retract_spec_from_operation,
    _normalize_approach_spec,
    _normalize_retract_spec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.strategy import (
    BidirectionalMillingStrategySpec,
    HelicalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _extract_milling_strategy_spec_from_operation,
    _build_closed_profile_strategy_toolpath,
    _build_helical_circle_strategy_toolpath,
    _normalize_milling_strategy_spec,
    _strategy_comparison_key,
)
from ..common.piece import _workpiece_depth_name
from ..common.xml import _raw_text, _text, _xsi_type
from ._common import _normalize_geometry_winding, _normalize_side_of_feature

__all__ = [
    "CircleMillingSpec",
    "build_circle_milling_spec",
    "_HydratedCircleMillingSpec",
    "_build_circle_toolpath_profile",
    "_can_hydrate_exact_circle_serialization",
    "_extract_circle_milling_template",
    "_hydrate_circle_milling_spec",
    "_matches_circle_geometry",
    "_normalize_circle_milling_spec",
]


@dataclass(frozen=True)
class CircleMillingSpec:
    """Descripcion reutilizable de un fresado circular sobre el plano `Top`."""

    center_x: float
    center_y: float
    radius: float
    winding: str = "CounterClockwise"
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
    milling_strategy: Optional[MillingStrategySpec] = None


@dataclass(frozen=True)
class _HydratedCircleMillingSpec:
    """Datos internos de serializacion que complementan un `CircleMillingSpec`."""

    spec: CircleMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def center_x(self) -> float:
        return self.spec.center_x

    @property
    def center_y(self) -> float:
        return self.spec.center_y

    @property
    def radius(self) -> float:
        return self.spec.radius

    @property
    def winding(self) -> str:
        return self.spec.winding

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

    @property
    def milling_strategy(self) -> Optional[MillingStrategySpec]:
        return self.spec.milling_strategy


def _normalize_circle_milling_spec(circle_milling: CircleMillingSpec) -> CircleMillingSpec:
    radius_value = float(circle_milling.radius)
    if radius_value <= 1e-9:
        raise ValueError("El radio del fresado circular debe ser mayor que cero.")
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(circle_milling.milling_strategy),
        allowed_types=(
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
        ),
        context="CircleMillingSpec",
    )
    return replace(
        circle_milling,
        center_x=float(circle_milling.center_x),
        center_y=float(circle_milling.center_y),
        radius=radius_value,
        winding=_normalize_geometry_winding(circle_milling.winding),
        side_of_feature=_normalize_side_of_feature(circle_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(circle_milling.depth_spec),
        approach=_normalize_approach_spec(circle_milling.approach),
        retract=_normalize_retract_spec(circle_milling.retract),
        milling_strategy=normalized_strategy,
    )


def _build_circle_toolpath_profile(
    top_level: float,
    final_level: float,
    spec: CircleMillingSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para un fresado circular cerrado."""

    cut_z = float(final_level)
    nominal_profile = build_circle_geometry_profile(
        spec.center_x,
        spec.center_y,
        spec.radius,
        z_value=cut_z,
        winding=spec.winding,
    )
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if isinstance(strategy, HelicalMillingStrategySpec):
        return _build_helical_circle_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)
    return _build_closed_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)


def _matches_circle_geometry(template: dict[str, object], spec: CircleMillingSpec, tolerance: float = 1e-6) -> bool:
    geometry_curve = template.get("geometry_curve")
    if not isinstance(geometry_curve, _CurveSpec):
        return False
    if geometry_curve.geometry_type != "GeomCircle" or geometry_curve.serialization is None:
        return False
    parsed_profile = _parse_circle_geometry_profile(geometry_curve.serialization)
    if parsed_profile is None or parsed_profile.center_point is None or parsed_profile.radius is None:
        return False
    return (
        math.isclose(parsed_profile.center_point[0], spec.center_x, abs_tol=tolerance)
        and math.isclose(parsed_profile.center_point[1], spec.center_y, abs_tol=tolerance)
        and math.isclose(parsed_profile.center_point[2], 0.0, abs_tol=tolerance)
        and math.isclose(parsed_profile.radius, spec.radius, abs_tol=tolerance)
        and _normalize_geometry_winding(parsed_profile.winding) == _normalize_geometry_winding(spec.winding)
    )


def _can_hydrate_exact_circle_serialization(template: dict[str, object], spec: CircleMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    source_strategy = template.get("milling_strategy") if isinstance(
        template.get("milling_strategy"),
        (
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
        ),
    ) else None
    if _strategy_comparison_key(source_strategy, is_closed_profile=True) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=True,
    ):
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
    if not _matches_circle_geometry(template, spec):
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


def _extract_circle_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomCircle" in _xsi_type(node)
        ),
        None,
    )
    geometry_id_text = _text(geometry, "./{*}Key/{*}ID") if geometry is not None else ""
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "GeneralProfileFeature" in _xsi_type(node)
            and _text(node, "./{*}GeometryID/{*}ID") == geometry_id_text
        ),
        None,
    )
    operation_id_text = _text(feature, "./{*}OperationIDs/{*}UtilityObject/{*}ID") if feature is not None else ""
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
            and _text(node, "./{*}Key/{*}ID") == operation_id_text
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado circular compatible.")

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    depth_variable_name = _workpiece_depth_name(workpiece)
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): _curve_spec_from_toolpath_node(toolpath)
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
        "depth_spec": _extract_depth_spec_from_template(
            feature,
            operation,
            matching_expressions,
            depth_variable_name,
        ),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "milling_strategy": _extract_milling_strategy_spec_from_operation(operation),
        "approach": _extract_approach_spec_from_operation(operation),
        "retract": _extract_retract_spec_from_operation(operation),
        "geometry_curve": _circle_curve_spec(_raw_text(geometry, "./{*}_serializationGeometryDescription")),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_circle_milling_spec(
    circle_milling: CircleMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedCircleMillingSpec:
    normalized_circle_milling = _normalize_circle_milling_spec(circle_milling)
    if source_pgmx_path is None:
        return _HydratedCircleMillingSpec(spec=normalized_circle_milling)
    template = _extract_circle_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_circle_serialization(template, normalized_circle_milling):
        return _HydratedCircleMillingSpec(spec=normalized_circle_milling)
    return _HydratedCircleMillingSpec(
        spec=normalized_circle_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_curve=template.get("geometry_curve") if isinstance(template.get("geometry_curve"), _CurveSpec) else None,
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def build_circle_milling_spec(
    *,
    center_x: float,
    center_y: float,
    radius: float,
    winding: Optional[str] = None,
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
    milling_strategy: Optional[MillingStrategySpec] = None,
) -> CircleMillingSpec:
    """Construye un `CircleMillingSpec` reusable para un fresado circular."""

    return _normalize_circle_milling_spec(
        CircleMillingSpec(
            center_x=float(center_x),
            center_y=float(center_y),
            radius=float(radius),
            winding=_normalize_geometry_winding(winding),
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
            milling_strategy=_normalize_milling_strategy_spec(milling_strategy),
        )
    )
