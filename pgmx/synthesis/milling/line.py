"""Line milling contracts for PGMX synthesis."""

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
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _normalize_milling_strategy_spec,
)

__all__ = [
    "LineMillingSpec",
    "build_line_milling_spec",
    "_normalize_line_milling_spec",
]


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
    milling_strategy: Optional[MillingStrategySpec] = None


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


def _normalize_line_milling_spec(line_milling: LineMillingSpec) -> LineMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(line_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="LineMillingSpec",
    )
    return replace(
        line_milling,
        side_of_feature=_normalize_side_of_feature(line_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(line_milling.depth_spec),
        approach=_normalize_approach_spec(line_milling.approach),
        retract=_normalize_retract_spec(line_milling.retract),
        milling_strategy=normalized_strategy,
    )


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
    line_milling_strategy: Optional[MillingStrategySpec] = None,
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
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(line_milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="LineMillingSpec",
    )
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
        milling_strategy=normalized_strategy,
    )
