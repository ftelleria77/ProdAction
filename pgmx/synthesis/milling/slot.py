"""Slot milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
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
from ..common.piece import _normalize_plane_name
from ._common import _normalize_side_of_feature

__all__ = [
    "SlotMillingSpec",
    "build_slot_milling_spec",
    "_normalize_slot_milling_spec",
]


@dataclass(frozen=True)
class SlotMillingSpec:
    """Ranura lineal `SlotSide` validada para Sierra Vertical X sobre `Top`."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    feature_name: str = "Canal"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1899"
    tool_name: str = "082"
    tool_width: float = 3.8
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(
        default_factory=lambda: MillingDepthSpec(
            is_through=False,
            target_depth=10.0,
            extra_depth=0.0,
        )
    )
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    material_position: str = "Left"
    side_offset: float = 0.0
    end_radius: float = 60.0
    slot_angle: float = 1.5707963267948966

    @property
    def milling_strategy(self) -> None:
        return None


def _normalize_slot_milling_spec(slot_milling: SlotMillingSpec) -> SlotMillingSpec:
    if math.isclose(float(slot_milling.start_x), float(slot_milling.end_x), abs_tol=1e-9) and math.isclose(
        float(slot_milling.start_y),
        float(slot_milling.end_y),
        abs_tol=1e-9,
    ):
        raise ValueError("La ranura no puede tener longitud cero.")
    end_radius = float(slot_milling.end_radius)
    if end_radius < 0.0:
        raise ValueError("El radio de extremo de la ranura no puede ser negativo.")
    return replace(
        slot_milling,
        start_x=float(slot_milling.start_x),
        start_y=float(slot_milling.start_y),
        end_x=float(slot_milling.end_x),
        end_y=float(slot_milling.end_y),
        plane_name=_normalize_plane_name(slot_milling.plane_name),
        side_of_feature=_normalize_side_of_feature(slot_milling.side_of_feature),
        tool_id=(slot_milling.tool_id or "1899").strip() or "1899",
        tool_name=(slot_milling.tool_name or "082").strip() or "082",
        tool_width=float(slot_milling.tool_width),
        security_plane=float(slot_milling.security_plane),
        depth_spec=_normalize_milling_depth_spec(slot_milling.depth_spec),
        approach=_normalize_approach_spec(slot_milling.approach),
        retract=_normalize_retract_spec(slot_milling.retract),
        material_position=(slot_milling.material_position or "Left").strip() or "Left",
        side_offset=float(slot_milling.side_offset),
        end_radius=end_radius,
        slot_angle=float(slot_milling.slot_angle),
    )


def build_slot_milling_spec(
    *,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    side_of_feature: Optional[str] = None,
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
    material_position: Optional[str] = None,
    side_offset: Optional[float] = None,
    end_radius: Optional[float] = None,
    slot_angle: Optional[float] = None,
) -> SlotMillingSpec:
    """Construye una ranura lineal `SlotSide` compatible con Sierra Vertical X."""

    depth_spec = build_milling_depth_spec(
        is_through=False if is_through is None and target_depth is None and extra_depth is None else is_through,
        target_depth=10.0 if is_through is None and target_depth is None and extra_depth is None else target_depth,
        extra_depth=extra_depth,
    )
    return _normalize_slot_milling_spec(
        SlotMillingSpec(
            start_x=float(start_x),
            start_y=float(start_y),
            end_x=float(end_x),
            end_y=float(end_y),
            feature_name=(feature_name or "Canal").strip() or "Canal",
            plane_name=_normalize_plane_name(plane_name),
            side_of_feature=_normalize_side_of_feature(side_of_feature),
            tool_id=(tool_id or "1899").strip() or "1899",
            tool_name=(tool_name or "082").strip() or "082",
            tool_width=3.8 if tool_width is None else float(tool_width),
            security_plane=20.0 if security_plane is None else float(security_plane),
            depth_spec=depth_spec,
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
            material_position=(material_position or "Left").strip() or "Left",
            side_offset=0.0 if side_offset is None else float(side_offset),
            end_radius=60.0 if end_radius is None else float(end_radius),
            slot_angle=1.5707963267948966 if slot_angle is None else float(slot_angle),
        )
    )
