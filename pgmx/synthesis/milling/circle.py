"""Circle milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Optional

from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.geometry import (
    _CurveSpec,
    GeometryProfileSpec,
    _parse_circle_geometry_profile,
    build_circle_geometry_profile,
    build_compensated_toolpath_profile,
)
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
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
    _build_closed_profile_strategy_toolpath,
    _build_helical_circle_strategy_toolpath,
    _normalize_milling_strategy_spec,
    _strategy_comparison_key,
)
from ._common import _normalize_geometry_winding, _normalize_side_of_feature

__all__ = [
    "CircleMillingSpec",
    "build_circle_milling_spec",
    "_build_circle_toolpath_profile",
    "_can_hydrate_exact_circle_serialization",
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
