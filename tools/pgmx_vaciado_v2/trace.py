from __future__ import annotations

from dataclasses import dataclass

from .depth import VaciadoDepth
from .geometry import BBox, VaciadoGeometry
from .primitives import TracePrimitiveSequence2D, rectangular_loop_sequence
from .strategy import VaciadoStrategy


@dataclass(frozen=True)
class OffsetFamily:
    owner: str
    limit: float
    offsets: tuple[float, ...]
    bboxes: tuple[BBox, ...]


@dataclass(frozen=True)
class RectangularNoIslandTracePlan:
    geometry: VaciadoGeometry
    strategy: VaciadoStrategy
    depth: VaciadoDepth
    offset_family: OffsetFamily
    traversal_offsets: tuple[float, ...]
    primitive_sequences: tuple[TracePrimitiveSequence2D, ...]


def plan_rectangular_no_islands(
    geometry: VaciadoGeometry,
    strategy: VaciadoStrategy,
    depth: VaciadoDepth,
) -> RectangularNoIslandTracePlan:
    if geometry.has_internal_geometry:
        raise NotImplementedError("rectangular_no_islands does not accept islands or route seeds.")
    if not geometry.outer.is_axis_aligned_rectangle:
        raise NotImplementedError("rectangular_no_islands requires an axis-aligned rectangular contour.")

    bbox = geometry.outer.bbox
    limit = bbox.minimum_half_span
    offsets = _offset_series(
        first_offset=strategy.effective_offset,
        radial_step=strategy.radial_step,
        limit=limit,
    )
    family = OffsetFamily(
        owner="outer",
        limit=limit,
        offsets=offsets,
        bboxes=tuple(bbox.inset(offset) for offset in offsets),
    )
    traversal_offsets = tuple(reversed(offsets)) if strategy.inside_to_outside else offsets
    bboxes_by_offset = dict(zip(family.offsets, family.bboxes))
    return RectangularNoIslandTracePlan(
        geometry=geometry,
        strategy=strategy,
        depth=depth,
        offset_family=family,
        traversal_offsets=traversal_offsets,
        primitive_sequences=tuple(
            rectangular_loop_sequence(
                owner=family.owner,
                offset=offset,
                bbox=bboxes_by_offset[offset],
                rotation_direction=strategy.rotation_direction,
            )
            for offset in traversal_offsets
        ),
    )


def _offset_series(*, first_offset: float, radial_step: float, limit: float) -> tuple[float, ...]:
    if radial_step <= 0.0:
        raise ValueError("radial_step must be positive.")
    offsets: list[float] = []
    current = first_offset
    while current <= limit + 1e-6:
        offsets.append(round(current, 10))
        current += radial_step
    return tuple(offsets)
