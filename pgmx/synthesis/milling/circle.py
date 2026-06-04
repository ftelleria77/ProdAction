"""Circle milling contracts for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

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
    HelicalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _normalize_milling_strategy_spec,
)
from ._common import _normalize_geometry_winding, _normalize_side_of_feature

__all__ = [
    "CircleMillingSpec",
    "build_circle_milling_spec",
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
