"""Polyline/profile milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Optional, Sequence

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
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _normalize_milling_strategy_spec,
)
from ._common import _normalize_side_of_feature

__all__ = [
    "PolylineMillingSpec",
    "build_polyline_milling_spec",
    "_is_closed_polyline_points",
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


def _points_close_2d(
    first: tuple[float, float],
    second: tuple[float, float],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return math.isclose(first[0], second[0], abs_tol=tolerance) and math.isclose(
        first[1],
        second[1],
        abs_tol=tolerance,
    )


def _normalize_polyline_points(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    normalized = tuple((float(point[0]), float(point[1])) for point in points)
    if len(normalized) < 2:
        raise ValueError("Una polilinea necesita al menos 2 puntos.")
    for start_point, end_point in zip(normalized, normalized[1:]):
        if math.isclose(start_point[0], end_point[0], abs_tol=1e-9) and math.isclose(
            start_point[1], end_point[1], abs_tol=1e-9
        ):
            raise ValueError("La polilinea no puede contener segmentos de longitud cero.")
    return normalized


def _is_closed_polyline_points(points: Sequence[tuple[float, float]]) -> bool:
    normalized_points = tuple((float(point[0]), float(point[1])) for point in points)
    return len(normalized_points) >= 4 and _points_close_2d(normalized_points[0], normalized_points[-1])


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
