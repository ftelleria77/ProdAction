"""Polyline/profile milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Optional, Sequence

from ..common.geometry import (
    _CurveSpec,
    GeometryProfileSpec,
    _build_closed_polyline_geometry_profile,
    _build_open_polyline_geometry_profile,
    _curve_spec_points,
    _is_closed_polyline_points,
    _normalize_polyline_points,
    build_compensated_toolpath_profile,
)
from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
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
    ContourParallelMillingStrategySpec,
    HelicalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _build_bidirectional_open_profile_strategy_toolpath,
    _build_closed_profile_strategy_toolpath,
    _build_unidirectional_open_profile_strategy_toolpath,
    _normalize_milling_strategy_spec,
    _strategy_comparison_key,
)
from ._common import _normalize_side_of_feature

__all__ = [
    "PolylineMillingSpec",
    "build_polyline_milling_spec",
    "_build_polyline_toolpath_profile",
    "_can_hydrate_exact_polyline_serialization",
    "_is_closed_polyline_points",
    "_matches_polyline_geometry",
    "_normalize_polyline_milling_spec",
    "_normalize_polyline_points",
    "_validate_polyline_postprocessable_by_maestro",
]


@dataclass(frozen=True)
class PolylineMillingSpec:
    """Descripcion reutilizable de un fresado asociado a una polilinea lineal.

    Si `points` termina en el mismo punto en el que empieza, se interpreta como
    contorno cerrado.
    """

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
    milling_strategy: Optional[MillingStrategySpec] = None


def _validate_polyline_postprocessable_by_maestro(spec: PolylineMillingSpec) -> None:
    """Bloquea una combinacion que Maestro no logra postprocesar a ISO."""

    points = _normalize_polyline_points(spec.points)
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    retract = _normalize_retract_spec(spec.retract)
    is_open_multisegment = len(points) > 2 and not _is_closed_polyline_points(points)
    has_ph_multipass = bool(strategy and strategy.allow_multiple_passes)
    uses_arc_up_retract = (
        retract.is_enabled
        and retract.retract_type == "Arc"
        and retract.mode == "Up"
    )
    if is_open_multisegment and has_ph_multipass and uses_arc_up_retract:
        raise ValueError(
            "Maestro no postprocesa polilineas abiertas de varios segmentos con "
            "estrategia multipasada PH y Retract Arc + Up. Usar Retract Line + Up "
            "o Arc + Quote para obtener ISO postprocesable."
        )


def _normalize_polyline_milling_spec(polyline_milling: PolylineMillingSpec) -> PolylineMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(polyline_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="PolylineMillingSpec",
    )
    normalized_spec = replace(
        polyline_milling,
        points=_normalize_polyline_points(polyline_milling.points),
        side_of_feature=_normalize_side_of_feature(polyline_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(polyline_milling.depth_spec),
        approach=_normalize_approach_spec(polyline_milling.approach),
        retract=_normalize_retract_spec(polyline_milling.retract),
        milling_strategy=normalized_strategy,
    )
    _validate_polyline_postprocessable_by_maestro(normalized_spec)
    return normalized_spec


def _build_polyline_toolpath_profile(
    top_level: float,
    final_level: float,
    spec: PolylineMillingSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para una polilinea abierta o cerrada."""

    cut_z = float(final_level)
    if _is_closed_polyline_points(spec.points):
        nominal_profile = _build_closed_polyline_geometry_profile(spec.points, z_value=cut_z)
    else:
        nominal_profile = _build_open_polyline_geometry_profile(spec.points, z_value=cut_z)
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if nominal_profile.is_closed:
        return _build_closed_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_open_profile_strategy_toolpath(
            float(top_level),
            cut_z,
            spec.security_plane,
            base_profile,
            strategy,
        )
    return _build_bidirectional_open_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)


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


def _can_hydrate_exact_polyline_serialization(template: dict[str, object], spec: PolylineMillingSpec) -> bool:
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
            ContourParallelMillingStrategySpec,
        ),
    ) else None
    is_closed_profile = _is_closed_polyline_points(spec.points)
    if _strategy_comparison_key(source_strategy, is_closed_profile=is_closed_profile) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=is_closed_profile,
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
    milling_strategy: Optional[MillingStrategySpec] = None,
) -> PolylineMillingSpec:
    """Construye un `PolylineMillingSpec` reusable para una polilinea lineal.

    Si `points` cierra sobre su primer punto, la polilinea se interpreta como
    contorno cerrado.
    """

    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="PolylineMillingSpec",
    )
    normalized_spec = PolylineMillingSpec(
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
        milling_strategy=normalized_strategy,
    )
    _validate_polyline_postprocessable_by_maestro(normalized_spec)
    return normalized_spec
