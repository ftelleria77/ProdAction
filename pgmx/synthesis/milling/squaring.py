"""Squaring milling contracts for PGMX synthesis."""

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
from ._common import _normalize_geometry_winding

__all__ = [
    "SquaringMillingSpec",
    "build_squaring_milling_spec",
    "_normalize_squaring_milling_spec",
    "_normalize_squaring_start_edge",
]


@dataclass(frozen=True)
class SquaringMillingSpec:
    """Escuadrado exterior del contorno de la pieza sobre el plano `Top`."""

    start_edge: str = "Bottom"
    winding: str = "CounterClockwise"
    start_coordinate: Optional[float] = None
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    tool_id: str = "1900"
    tool_name: str = "E001"
    tool_width: float = 18.36
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=lambda: MillingDepthSpec(is_through=True, extra_depth=1.0))
    approach: ApproachSpec = field(
        default_factory=lambda: ApproachSpec(
            is_enabled=True,
            approach_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
        )
    )
    retract: RetractSpec = field(
        default_factory=lambda: RetractSpec(
            is_enabled=True,
            retract_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
            overlap=0.0,
        )
    )
    milling_strategy: Optional[MillingStrategySpec] = None

    @property
    def side_of_feature(self) -> str:
        normalized_winding = _normalize_geometry_winding(self.winding)
        return "Right" if normalized_winding == "CounterClockwise" else "Left"


def _normalize_squaring_start_edge(value: Optional[str]) -> str:
    raw = (value or "Bottom").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "bottom": "Bottom",
        "inferior": "Bottom",
        "bordeinferior": "Bottom",
        "right": "Right",
        "derecho": "Right",
        "bordederecho": "Right",
        "top": "Top",
        "superior": "Top",
        "bordesuperior": "Top",
        "left": "Left",
        "izquierdo": "Left",
        "bordeizquierdo": "Left",
    }
    if raw not in mapping:
        raise ValueError("StartEdge invalido. Valores admitidos: Bottom/Inferior, Right/Derecho, Top/Superior o Left/Izquierdo.")
    return mapping[raw]


def _normalize_squaring_milling_spec(squaring_milling: SquaringMillingSpec) -> SquaringMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(squaring_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="SquaringMillingSpec",
    )
    return replace(
        squaring_milling,
        start_edge=_normalize_squaring_start_edge(squaring_milling.start_edge),
        winding=_normalize_geometry_winding(squaring_milling.winding),
        depth_spec=_normalize_milling_depth_spec(squaring_milling.depth_spec),
        approach=_normalize_approach_spec(squaring_milling.approach),
        retract=_normalize_retract_spec(squaring_milling.retract),
        milling_strategy=normalized_strategy,
    )


def build_squaring_milling_spec(
    *,
    start_edge: Optional[str] = None,
    winding: Optional[str] = None,
    start_coordinate: Optional[float] = None,
    feature_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
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
) -> SquaringMillingSpec:
    """Construye un `SquaringMillingSpec` reusable para escuadrar la pieza."""

    has_explicit_depth = any(value is not None for value in (is_through, target_depth, extra_depth))
    depth_spec = (
        build_milling_depth_spec(is_through=True, extra_depth=1.0)
        if not has_explicit_depth
        else build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        )
    )

    has_explicit_approach = any(
        value is not None
        for value in (
            approach_enabled,
            approach_type,
            approach_mode,
            approach_radius_multiplier,
            approach_speed,
            approach_arc_side,
        )
    )
    approach_spec = (
        build_approach_spec(
            enabled=True,
            approach_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
        )
        if not has_explicit_approach
        else build_approach_spec(
            enabled=approach_enabled,
            approach_type=approach_type,
            mode=approach_mode,
            radius_multiplier=approach_radius_multiplier,
            speed=approach_speed,
            arc_side=approach_arc_side,
        )
    )

    has_explicit_retract = any(
        value is not None
        for value in (
            retract_enabled,
            retract_type,
            retract_mode,
            retract_radius_multiplier,
            retract_speed,
            retract_arc_side,
            retract_overlap,
        )
    )
    retract_spec = (
        build_retract_spec(
            enabled=True,
            retract_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
            overlap=0.0,
        )
        if not has_explicit_retract
        else build_retract_spec(
            enabled=retract_enabled,
            retract_type=retract_type,
            mode=retract_mode,
            radius_multiplier=retract_radius_multiplier,
            speed=retract_speed,
            arc_side=retract_arc_side,
            overlap=retract_overlap,
        )
    )

    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="SquaringMillingSpec",
    )
    return SquaringMillingSpec(
        start_edge=_normalize_squaring_start_edge(start_edge),
        winding=_normalize_geometry_winding(winding),
        start_coordinate=None if start_coordinate is None else float(start_coordinate),
        feature_name=(feature_name or "Fresado").strip() or "Fresado",
        tool_id=(tool_id or "1900").strip() or "1900",
        tool_name=(tool_name or "E001").strip() or "E001",
        tool_width=18.36 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        approach=approach_spec,
        retract=retract_spec,
        milling_strategy=normalized_strategy,
    )
