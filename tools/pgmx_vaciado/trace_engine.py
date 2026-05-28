"""General skeleton for Maestro-like Vaciado trace generation.

The module is intentionally independent from the legacy rectangular helpers.
It turns a `PocketMillingSpec` into a normalized trace plan that can be used by
future topology and toolpath emitters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from tools import synthesize_pgmx as sp


Point2 = tuple[float, float]
Point3 = tuple[float, float, float]
BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class TraceContour:
    points: tuple[Point2, ...]
    start_point: Point2
    bbox: BBox
    winding: str
    is_axis_aligned_rectangle: bool

    @property
    def width(self) -> float:
        return self.bbox[1] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[2]


@dataclass(frozen=True)
class TraceClearance:
    left: float
    right: float
    bottom: float
    top: float

    @property
    def horizontal_half(self) -> float:
        return min(self.left, self.right) / 2.0

    @property
    def vertical_half(self) -> float:
        return min(self.bottom, self.top) / 2.0

    @property
    def minimum_half(self) -> float:
        return min(self.horizontal_half, self.vertical_half)

    @property
    def maximum_side_half(self) -> float:
        return max(self.left, self.right, self.bottom, self.top) / 2.0


@dataclass(frozen=True)
class TraceInternalContour:
    physical: TraceContour
    route_seed: TraceContour | None = None
    route_seed_name: str = ""
    route_seed_geometry_id: str = ""

    @property
    def effective_route_contour(self) -> TraceContour:
        return self.route_seed or self.physical


@dataclass(frozen=True)
class TraceParameters:
    tool_width: float
    allowance_side: float
    effective_offset: float
    radial_step: float
    target_depth: float
    security_plane: float
    rotation_direction: str
    stroke_connection_strategy: str
    inside_to_outside: bool
    overlap: float
    is_helic_strategy: bool
    allow_multiple_passes: bool
    axial_cutting_depth: float
    axial_finish_cutting_depth: float


@dataclass(frozen=True)
class TraceOffsetFamily:
    owner: str
    contour: TraceContour
    limit: float
    offsets: tuple[float, ...]
    complete_offsets: tuple[float, ...] = ()
    partial_offsets: tuple[float, ...] = ()
    bridge_offset: float | None = None
    clearance: TraceClearance | None = None


@dataclass(frozen=True)
class TraceDepthPlan:
    surface_z: float
    cut_depths: tuple[float, ...]
    z_values: tuple[float, ...]


@dataclass(frozen=True)
class TracePrimitive2D:
    primitive_type: str
    owner: str
    offset: float
    start: Point2
    end: Point2
    center: Point2 | None = None
    radius: float | None = None
    orientation: str = ""


@dataclass(frozen=True)
class TracePrimitiveSequence2D:
    owner: str
    offset: float
    primitives: tuple[TracePrimitive2D, ...]
    closed: bool = True

    @property
    def arc_count(self) -> int:
        return sum(1 for primitive in self.primitives if primitive.primitive_type == "Arc")

    @property
    def line_count(self) -> int:
        return sum(1 for primitive in self.primitives if primitive.primitive_type == "Line")


@dataclass(frozen=True)
class TraceResolvedSequence2D:
    name: str
    primitives: tuple[TracePrimitive2D, ...]

    @property
    def arc_count(self) -> int:
        return sum(1 for primitive in self.primitives if primitive.primitive_type == "Arc")

    @property
    def line_count(self) -> int:
        return sum(1 for primitive in self.primitives if primitive.primitive_type == "Line")

    @property
    def start(self) -> Point2 | None:
        return self.primitives[0].start if self.primitives else None

    @property
    def end(self) -> Point2 | None:
        return self.primitives[-1].end if self.primitives else None


@dataclass(frozen=True)
class ContourParallelTracePlan:
    outer: TraceContour
    internal_contours: tuple[TraceInternalContour, ...]
    parameters: TraceParameters
    outer_offset_family: TraceOffsetFamily
    internal_offset_families: tuple[TraceOffsetFamily, ...]
    depth_plan: TraceDepthPlan
    primitive_sequences: tuple[TracePrimitiveSequence2D, ...]
    resolved_sequences: tuple[TraceResolvedSequence2D, ...]
    trajectory_sequences: tuple[tuple[Point3, ...], ...]
    pending_stages: tuple[str, ...]

    @property
    def can_emit_trajectory(self) -> bool:
        return not self.pending_stages and bool(self.trajectory_sequences)


def generate_contour_parallel_pocket_trace(
    spec: sp.PocketMillingSpec,
    *,
    surface_z: float = 0.0,
) -> ContourParallelTracePlan:
    """Build a general ContourParallel trace plan from a pocket contract.

    This is the stable entry point for the future Vaciado trace engine. The
    current implementation computes the normalized geometry, offset families
    and Z levels; topology resolution and final `TrajectoryPath` emission are
    deliberately left as explicit pending stages.
    """

    strategy = spec.milling_strategy
    if not isinstance(strategy, sp.ContourParallelMillingStrategySpec):
        raise TypeError("Vaciado trace generation requires ContourParallelMillingStrategySpec.")

    parameters = _trace_parameters(spec, strategy)
    if parameters.tool_width <= 0.0:
        raise ValueError("tool_width must be positive.")
    if parameters.radial_step <= 0.0:
        raise ValueError("radial_step must be positive; check tool_width and overlap.")
    if parameters.target_depth <= 0.0:
        raise ValueError("target_depth must be positive.")

    outer = _trace_contour(spec.contour_points)
    internal_contours = _trace_internal_contours(spec)
    outer_family = _outer_offset_family(outer, parameters)
    internal_families = tuple(
        _internal_offset_family(index, outer, internal, parameters)
        for index, internal in enumerate(internal_contours, 1)
    )
    depth_plan = _depth_plan(parameters, surface_z=surface_z)
    primitive_sequences = _primitive_sequences(outer_family, internal_families, parameters)
    resolved_sequences = _resolved_sequences(outer, internal_families, parameters)
    trajectory_sequences = _trajectory_sequences(resolved_sequences, depth_plan)
    return ContourParallelTracePlan(
        outer=outer,
        internal_contours=internal_contours,
        parameters=parameters,
        outer_offset_family=outer_family,
        internal_offset_families=internal_families,
        depth_plan=depth_plan,
        primitive_sequences=primitive_sequences,
        resolved_sequences=resolved_sequences,
        trajectory_sequences=trajectory_sequences,
        pending_stages=_pending_stages(spec, outer, internal_contours, resolved_sequences),
    )


def _trace_parameters(
    spec: sp.PocketMillingSpec,
    strategy: sp.ContourParallelMillingStrategySpec,
) -> TraceParameters:
    tool_width = float(spec.tool_width)
    allowance_side = float(spec.allowance_side)
    return TraceParameters(
        tool_width=tool_width,
        allowance_side=allowance_side,
        effective_offset=(tool_width / 2.0) + allowance_side,
        radial_step=tool_width * (1.0 - float(strategy.overlap)),
        target_depth=float(spec.depth_spec.target_depth or 0.0),
        security_plane=float(spec.security_plane),
        rotation_direction=strategy.rotation_direction,
        stroke_connection_strategy=strategy.stroke_connection_strategy,
        inside_to_outside=bool(strategy.inside_to_outside),
        overlap=float(strategy.overlap),
        is_helic_strategy=bool(strategy.is_helic_strategy),
        allow_multiple_passes=bool(strategy.allow_multiple_passes),
        axial_cutting_depth=float(strategy.axial_cutting_depth),
        axial_finish_cutting_depth=float(strategy.axial_finish_cutting_depth),
    )


def _trace_internal_contours(spec: sp.PocketMillingSpec) -> tuple[TraceInternalContour, ...]:
    route_seeds = tuple(seed for seed in spec.boss_route_seeds if seed.is_resolved)
    internal_contours: list[TraceInternalContour] = []
    for index, physical_points in enumerate(spec.boss_contours):
        route_seed = route_seeds[index] if index < len(route_seeds) else None
        internal_contours.append(
            TraceInternalContour(
                physical=_trace_contour(physical_points),
                route_seed=_trace_contour(route_seed.contour_points) if route_seed is not None else None,
                route_seed_name=route_seed.name if route_seed is not None else "",
                route_seed_geometry_id=route_seed.geometry_id if route_seed is not None else "",
            )
        )
    for route_seed in route_seeds[len(spec.boss_contours) :]:
        contour = _trace_contour(route_seed.contour_points)
        internal_contours.append(
            TraceInternalContour(
                physical=contour,
                route_seed=contour,
                route_seed_name=route_seed.name,
                route_seed_geometry_id=route_seed.geometry_id,
            )
        )
    return tuple(internal_contours)


def _outer_offset_family(outer: TraceContour, parameters: TraceParameters) -> TraceOffsetFamily:
    limit = min(outer.width, outer.height) / 2.0
    offsets, bridge = _offset_series(
        first_offset=parameters.effective_offset,
        radial_step=parameters.radial_step,
        limit=limit,
        bridge_tolerance=0.0,
    )
    return TraceOffsetFamily(
        owner="outer",
        contour=outer,
        limit=limit,
        offsets=offsets,
        bridge_offset=bridge,
    )


def _internal_offset_family(
    index: int,
    outer: TraceContour,
    internal: TraceInternalContour,
    parameters: TraceParameters,
) -> TraceOffsetFamily:
    route_contour = internal.effective_route_contour
    clearance = _clearance_between(outer.bbox, route_contour.bbox)
    limit = clearance.maximum_side_half
    offsets, bridge = _offset_series(
        first_offset=parameters.effective_offset,
        radial_step=parameters.radial_step,
        limit=limit,
        bridge_tolerance=2.0,
    )
    complete_limit = clearance.minimum_half
    complete_offsets = tuple(offset for offset in offsets if offset <= complete_limit + 1e-6)
    partial_offsets = tuple(offset for offset in offsets if offset > complete_limit + 1e-6)
    return TraceOffsetFamily(
        owner=f"internal:{index}",
        contour=route_contour,
        limit=limit,
        offsets=offsets,
        complete_offsets=complete_offsets,
        partial_offsets=partial_offsets,
        bridge_offset=bridge,
        clearance=clearance,
    )


def _offset_series(
    *,
    first_offset: float,
    radial_step: float,
    limit: float,
    bridge_tolerance: float,
) -> tuple[tuple[float, ...], float | None]:
    if first_offset < -1e-9:
        raise ValueError("tool radius + allowance_side must not be negative.")
    if radial_step <= 0.0:
        raise ValueError("radial_step must be positive.")
    offsets: list[float] = []
    current = first_offset
    while current <= limit + 1e-6:
        offsets.append(round(current, 10))
        current += radial_step
    bridge = None
    if bridge_tolerance > 0.0 and offsets and 0.0 < current - limit <= bridge_tolerance + 1e-6:
        bridge = round(current, 10)
    return tuple(offsets), bridge


def _depth_plan(parameters: TraceParameters, *, surface_z: float) -> TraceDepthPlan:
    cut_depths = _cut_depth_levels(
        target_depth=parameters.target_depth,
        allow_multiple_passes=parameters.allow_multiple_passes,
        axial_cutting_depth=parameters.axial_cutting_depth,
        axial_finish_cutting_depth=parameters.axial_finish_cutting_depth,
    )
    z_values = tuple(round(float(surface_z) - depth, 10) for depth in cut_depths)
    return TraceDepthPlan(
        surface_z=float(surface_z),
        cut_depths=cut_depths,
        z_values=z_values,
    )


def _primitive_sequences(
    outer_family: TraceOffsetFamily,
    internal_families: Sequence[TraceOffsetFamily],
    parameters: TraceParameters,
) -> tuple[TracePrimitiveSequence2D, ...]:
    sequences: list[TracePrimitiveSequence2D] = []
    if outer_family.contour.is_axis_aligned_rectangle:
        for offset in _ordered_offsets(_outer_sequence_offsets(outer_family, internal_families), parameters):
            sequence = _rectangle_offset_sequence(
                owner=outer_family.owner,
                bbox=outer_family.contour.bbox,
                offset=offset,
                rotation_direction=parameters.rotation_direction,
                outward=False,
            )
            if sequence is not None:
                sequences.append(sequence)

    for family in internal_families:
        if not family.contour.is_axis_aligned_rectangle:
            continue
        for offset in _ordered_offsets(family.complete_offsets, parameters):
            sequence = _rounded_rectangle_offset_sequence(
                owner=family.owner,
                bbox=family.contour.bbox,
                offset=offset,
            )
            if sequence is not None:
                sequences.append(sequence)
    return tuple(sequences)


def _resolved_sequences(
    outer: TraceContour,
    internal_families: Sequence[TraceOffsetFamily],
    parameters: TraceParameters,
) -> tuple[TraceResolvedSequence2D, ...]:
    if not internal_families:
        return ()
    if len(internal_families) != 1:
        return ()
    if parameters.inside_to_outside:
        return ()
    if parameters.allow_multiple_passes or parameters.is_helic_strategy:
        return ()
    if parameters.stroke_connection_strategy != "Straghtline":
        return ()
    if not outer.is_axis_aligned_rectangle:
        return ()

    family = internal_families[0]
    if not family.contour.is_axis_aligned_rectangle:
        return ()
    if family.partial_offsets or family.bridge_offset is not None:
        bridged = _resolved_single_seed_bridge_sequence(outer.bbox, family)
        if bridged is not None:
            return (bridged,)
        large_partial = _resolved_single_seed_large_single_partial_sequence(outer.bbox, family)
        if large_partial is not None:
            return (large_partial,)
        partial = _resolved_single_seed_single_partial_sequence(outer.bbox, family)
        if partial is not None:
            return (partial,)
        dense_bridge = _resolved_single_seed_dense_bridge_sequence(outer.bbox, family)
        if dense_bridge is not None:
            return (dense_bridge,)
        dense_partial = _resolved_single_seed_dense_partial_sequence(outer.bbox, family)
        if dense_partial is not None:
            return (dense_partial,)
        unbalanced_early_dense = _resolved_single_seed_unbalanced_left_early_dense_sequence(outer.bbox, family)
        if unbalanced_early_dense is not None:
            return (unbalanced_early_dense,)
        unbalanced_dense_partial = _resolved_single_seed_unbalanced_left_dense_partial_sequence(outer.bbox, family)
        if unbalanced_dense_partial is not None:
            return (unbalanced_dense_partial,)
        extended_dense = _resolved_single_seed_unbalanced_left_extended_dense_sequence(outer.bbox, family)
        if extended_dense is not None:
            return (extended_dense,)
        terminal_partial = _resolved_single_seed_unbalanced_left_terminal_partial_sequence(outer.bbox, family)
        if terminal_partial is not None:
            return (terminal_partial,)
        repeated_partial = _resolved_single_seed_unbalanced_left_repeated_partial_sequence(outer.bbox, family)
        if repeated_partial is not None:
            return (repeated_partial,)
        unbalanced_left_partial = _resolved_single_seed_unbalanced_left_partial_sequence(outer.bbox, family)
        if unbalanced_left_partial is not None:
            return (unbalanced_left_partial,)
        unbalanced_right_terminal = _resolved_single_seed_unbalanced_right_terminal_partial_sequence(
            outer.bbox,
            family,
        )
        if unbalanced_right_terminal is not None:
            return (unbalanced_right_terminal,)
        unbalanced_right = _resolved_single_seed_unbalanced_right_mirrored_sequence(outer.bbox, family)
        if unbalanced_right is not None:
            return (unbalanced_right,)
        return ()

    offsets = tuple(float(offset) for offset in family.complete_offsets)
    if not offsets:
        return ()

    outer_sequence = _resolved_outer_rectangle_sequence(outer.bbox, offsets)
    internal_sequence = _resolved_rounded_rectangle_seed_sequence(family.contour.bbox, offsets)
    return tuple(sequence for sequence in (outer_sequence, internal_sequence) if sequence.primitives)


def _resolved_single_seed_bridge_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.partial_offsets or family.bridge_offset is None:
        return None
    if family.clearance is None or not _has_balanced_clearance(family.clearance):
        return None
    if len(family.complete_offsets) != 2:
        return None

    inner_offset, outer_offset = (float(value) for value in family.complete_offsets)
    bridge_offset = float(family.bridge_offset)
    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox

    left_inner, right_inner, bottom_inner, top_inner = _inset_bbox(outer_bbox, inner_offset)
    left_outer, right_outer, bottom_outer, top_outer = _inset_bbox(outer_bbox, outer_offset)
    left_bridge, right_bridge, bottom_bridge, top_bridge = _inset_bbox(outer_bbox, bridge_offset)

    primitives: list[TracePrimitive2D] = []

    def add_line(end: Point2) -> None:
        _append_line(primitives, "bridge_offsets", bridge_offset, end)

    def add_arc(end: Point2, center: Point2) -> None:
        _append_arc(primitives, "bridge_offsets", bridge_offset, end, center, bridge_offset)

    start = (left_inner, top_inner)
    primitives.append(_line("bridge_offsets", inner_offset, start, (left_inner, top_outer)))
    add_line((left_inner, bottom_inner))
    add_line((right_inner, bottom_inner))
    add_line((right_inner, top_inner))
    add_line((left_inner, top_inner))
    add_line((left_inner, top_outer))
    add_line((left_outer, top_outer))
    add_line((left_outer, top_bridge))
    add_line((left_outer, bottom_outer))
    add_line((left_bridge, bottom_outer))
    add_line((right_outer, bottom_outer))
    add_line((right_outer, bottom_bridge))
    add_line((right_outer, top_outer))
    add_line((right_bridge, top_outer))
    add_line((left_outer, top_outer))
    add_line((left_outer, top_bridge))
    add_line((left_bridge, top_bridge))

    top_left_center = (seed_min_x, seed_max_y)
    top_left_vertical = _circle_x_intersection_y(top_left_center, bridge_offset, left_bridge, upper=True)
    top_left_top = _circle_y_intersection_x(top_left_center, bridge_offset, top_bridge, left_side=True)
    add_line(top_left_vertical)
    add_arc(top_left_top, top_left_center)
    add_line((left_bridge, top_bridge))
    add_line(top_left_vertical)

    split_points = {
        offset: _radial_projection(top_left_center, top_left_vertical, bridge_offset, offset)
        for offset in (outer_offset, inner_offset)
    }
    add_line(split_points[outer_offset])
    _append_top_left_split_rounded_loop(primitives, family.contour.bbox, outer_offset, split_points[outer_offset])
    add_line(split_points[inner_offset])
    _append_top_left_split_rounded_loop(primitives, family.contour.bbox, inner_offset, split_points[inner_offset])
    add_line(split_points[outer_offset])
    add_line(top_left_vertical)
    add_line((left_bridge, top_bridge))
    add_line((left_outer, top_bridge))
    add_line((left_outer, bottom_outer))
    add_line((left_bridge, bottom_outer))

    bottom_left_center = (seed_min_x, seed_min_y)
    bottom_left_bottom = _circle_y_intersection_x(bottom_left_center, bridge_offset, bottom_bridge, left_side=True)
    bottom_left_vertical = _circle_x_intersection_y(bottom_left_center, bridge_offset, left_bridge, upper=False)
    add_line((left_bridge, bottom_bridge))
    add_line(bottom_left_bottom)
    add_arc(bottom_left_vertical, bottom_left_center)
    add_line((left_bridge, bottom_bridge))
    add_line((left_bridge, bottom_outer))
    add_line((right_outer, bottom_outer))
    add_line((right_outer, bottom_bridge))
    add_line((right_bridge, bottom_bridge))

    bottom_right_center = (seed_max_x, seed_min_y)
    bottom_right_vertical = _circle_x_intersection_y(bottom_right_center, bridge_offset, right_bridge, upper=False)
    bottom_right_bottom = _circle_y_intersection_x(bottom_right_center, bridge_offset, bottom_bridge, left_side=False)
    add_line(bottom_right_vertical)
    add_arc(bottom_right_bottom, bottom_right_center)
    add_line((right_bridge, bottom_bridge))
    add_line((right_outer, bottom_bridge))
    add_line((right_outer, top_outer))
    add_line((right_bridge, top_outer))
    add_line((right_bridge, top_bridge))

    top_right_center = (seed_max_x, seed_max_y)
    top_right_top = _circle_y_intersection_x(top_right_center, bridge_offset, top_bridge, left_side=False)
    top_right_vertical = _circle_x_intersection_y(top_right_center, bridge_offset, right_bridge, upper=True)
    add_line(top_right_top)
    add_arc(top_right_vertical, top_right_center)
    add_line((right_bridge, top_bridge))

    return TraceResolvedSequence2D(
        name="single_seed_bridge_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_single_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None or not _has_balanced_clearance(family.clearance):
        return None
    if len(family.complete_offsets) != 1 or len(family.partial_offsets) != 1:
        return None

    complete_offset = float(family.complete_offsets[0])
    partial_offset = float(family.partial_offsets[0])
    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    left_complete, right_complete, bottom_complete, top_complete = _inset_bbox(outer_bbox, complete_offset)
    left_partial, right_partial, bottom_partial, top_partial = _inset_bbox(outer_bbox, partial_offset)

    primitives: list[TracePrimitive2D] = []

    def add_line(end: Point2) -> None:
        _append_line(primitives, "single_partial_offset", partial_offset, end)

    def add_arc(end: Point2, center: Point2, radius: float) -> None:
        _append_arc(primitives, "single_partial_offset", radius, end, center, radius)

    start = (left_complete, top_complete)
    primitives.append(_line("single_partial_offset", complete_offset, start, (left_complete, bottom_complete)))
    add_line((left_partial, bottom_complete))
    add_line((right_complete, bottom_complete))
    add_line((right_complete, top_complete))
    add_line((right_partial, top_complete))
    add_line((left_complete, top_complete))
    add_line((left_complete, bottom_complete))
    add_line((left_partial, bottom_complete))
    add_line((left_partial, bottom_partial))

    bottom_left_center = (seed_min_x, seed_min_y)
    top_left_center = (seed_min_x, seed_max_y)
    left_bottom = _circle_y_intersection_x(bottom_left_center, partial_offset, bottom_partial, left_side=True)
    left_top = _circle_y_intersection_x(top_left_center, partial_offset, top_partial, left_side=True)
    add_line(left_bottom)
    add_arc((seed_min_x - partial_offset, seed_min_y), bottom_left_center, partial_offset)
    add_line((seed_min_x - partial_offset, seed_max_y))
    add_arc(left_top, top_left_center, partial_offset)
    add_line((left_partial, top_partial))
    add_line((left_partial, bottom_partial))
    add_line(left_bottom)

    complete_split = _radial_projection(bottom_left_center, left_bottom, partial_offset, complete_offset)
    add_line(complete_split)
    _append_bottom_left_split_rounded_loop(primitives, family.contour.bbox, complete_offset, complete_split)
    add_line(left_bottom)
    add_line((left_partial, bottom_partial))
    add_line((left_partial, bottom_complete))
    add_line((right_complete, bottom_complete))
    add_line((right_complete, top_complete))
    add_line((right_partial, top_complete))
    add_line((right_partial, top_partial))

    top_right_center = (seed_max_x, seed_max_y)
    bottom_right_center = (seed_max_x, seed_min_y)
    right_top = _circle_y_intersection_x(top_right_center, partial_offset, top_partial, left_side=False)
    right_bottom = _circle_y_intersection_x(bottom_right_center, partial_offset, bottom_partial, left_side=False)
    top_right_mid = (
        seed_max_x + (partial_offset / math.sqrt(2.0)),
        seed_max_y + (partial_offset / math.sqrt(2.0)),
    )
    add_line(right_top)
    add_arc(top_right_mid, top_right_center, partial_offset)
    add_arc((seed_max_x + partial_offset, seed_max_y), top_right_center, partial_offset)
    add_line((seed_max_x + partial_offset, seed_min_y))
    add_arc(right_bottom, bottom_right_center, partial_offset)
    add_line((right_partial, bottom_partial))
    add_line((right_partial, top_partial))

    return TraceResolvedSequence2D(
        name="single_seed_single_partial_offset",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_large_single_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None or not _has_balanced_clearance(family.clearance):
        return None
    if len(family.complete_offsets) != 1 or len(family.partial_offsets) != 1:
        return None

    complete_offset = float(family.complete_offsets[0])
    partial_offset = float(family.partial_offsets[0])
    if not (
        math.isclose(family.contour.width, partial_offset, abs_tol=1e-6)
        and math.isclose(family.contour.height, partial_offset, abs_tol=1e-6)
    ):
        return None

    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    left_complete, right_complete, bottom_complete, top_complete = _inset_bbox(outer_bbox, complete_offset)
    left_partial, right_partial, bottom_partial, top_partial = _inset_bbox(outer_bbox, partial_offset)

    owner = "single_seed_large_single_partial_offset"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((left_complete, top_complete))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    top_left_center = (seed_min_x, seed_max_y)
    bottom_left_center = (seed_min_x, seed_min_y)
    top_right_center = (seed_max_x, seed_max_y)
    bottom_right_center = (seed_max_x, seed_min_y)
    left_top_partial = _circle_y_intersection_x(top_left_center, partial_offset, top_partial, left_side=True)
    left_bottom_partial = _circle_y_intersection_x(bottom_left_center, partial_offset, bottom_partial, left_side=True)
    right_top_partial = _circle_y_intersection_x(top_right_center, partial_offset, top_partial, left_side=False)
    right_bottom_partial = _circle_y_intersection_x(bottom_right_center, partial_offset, bottom_partial, left_side=False)
    top_right_mid = (
        seed_max_x + (complete_offset / math.sqrt(2.0)),
        seed_max_y + (complete_offset / math.sqrt(2.0)),
    )

    add_line(point(left_complete, top_partial), offset=complete_offset)
    add_line(point(left_complete, bottom_complete), offset=complete_offset)
    add_line(point(left_partial, bottom_complete), offset=complete_offset)
    add_line(point(right_complete, bottom_complete), offset=complete_offset)
    add_line(point(right_complete, top_complete), offset=complete_offset)
    add_line(point(right_partial, top_complete), offset=complete_offset)
    add_line(point(left_complete, top_complete), offset=complete_offset)
    add_line(point(left_complete, top_partial), offset=complete_offset)
    add_line(point(left_partial, top_partial), offset=partial_offset)
    add_line(point(left_partial, seed_max_y), offset=partial_offset)
    add_arc(left_top_partial, top_left_center, partial_offset)
    add_line(point(left_partial, top_partial), offset=partial_offset)
    add_line(point(left_partial, seed_max_y), offset=partial_offset)
    add_line(point(seed_min_x - complete_offset, seed_max_y), offset=complete_offset)
    add_arc(point(seed_min_x, seed_max_y + complete_offset), top_left_center, complete_offset)
    add_line(point(seed_max_x, seed_max_y + complete_offset), offset=complete_offset)
    add_arc(top_right_mid, top_right_center, complete_offset)
    add_arc(point(seed_max_x + complete_offset, seed_max_y), top_right_center, complete_offset)
    add_line(point(seed_max_x + complete_offset, seed_min_y), offset=complete_offset)
    add_arc(point(seed_max_x, seed_min_y - complete_offset), bottom_right_center, complete_offset)
    add_line(point(seed_min_x, seed_min_y - complete_offset), offset=complete_offset)
    add_arc(point(seed_min_x - complete_offset, seed_min_y), bottom_left_center, complete_offset)
    add_line(point(seed_min_x - complete_offset, seed_max_y), offset=complete_offset)
    add_line(point(left_partial, seed_max_y), offset=partial_offset)
    add_line(point(left_partial, top_partial), offset=partial_offset)
    add_line(point(left_complete, top_partial), offset=complete_offset)
    add_line(point(left_complete, bottom_complete), offset=complete_offset)
    add_line(point(left_partial, bottom_complete), offset=complete_offset)
    add_line(point(left_partial, bottom_partial), offset=partial_offset)
    add_line(left_bottom_partial, offset=partial_offset)
    add_arc(point(left_partial, seed_min_y), bottom_left_center, partial_offset)
    add_line(point(left_partial, seed_max_y), offset=partial_offset)
    add_line(point(left_partial, bottom_partial), offset=partial_offset)
    add_line(point(left_partial, bottom_complete), offset=complete_offset)
    add_line(point(right_complete, bottom_complete), offset=complete_offset)
    add_line(point(right_complete, top_complete), offset=complete_offset)
    add_line(point(right_partial, top_complete), offset=complete_offset)
    add_line(point(right_partial, top_partial), offset=partial_offset)
    add_line(right_top_partial, offset=partial_offset)
    add_arc(point(right_partial, seed_max_y), top_right_center, partial_offset)
    add_line(point(right_partial, seed_min_y), offset=partial_offset)
    add_arc(right_bottom_partial, bottom_right_center, partial_offset)
    add_line(point(right_partial, bottom_partial), offset=partial_offset)
    add_line(point(right_partial, top_partial), offset=partial_offset)

    return TraceResolvedSequence2D(
        name="single_seed_large_single_partial_offset",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_dense_bridge_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is None:
        return None
    if family.clearance is None or not _has_balanced_clearance(family.clearance):
        return None
    if len(family.complete_offsets) < 2 or len(family.partial_offsets) < 2:
        return None

    complete_radii = tuple(float(value) for value in family.complete_offsets)
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    bridge_radius = float(family.bridge_offset)
    radial_step = _inferred_offset_step((*complete_radii, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    min_partial = partial_radii[0]
    max_partial = partial_radii[-1]
    max_complete = complete_radii[-1]
    complete_loop_min_chord = 0.0 if math.isclose(family.contour.width, max_partial, abs_tol=1e-6) else 0.5
    extra_radii = _dense_bridge_extra_radii(
        outer_bbox,
        family.contour.bbox,
        bridge_radius,
        radial_step,
    )
    if not extra_radii:
        return None

    partial_bottom_y = outer_min_y + min_partial
    sin_beta = (seed_min_y - partial_bottom_y) / min_partial
    if sin_beta <= -1.0 or sin_beta >= 1.0:
        return None
    beta_angle = math.pi - math.asin(sin_beta)

    owner = "single_seed_dense_bridge_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_radii[0], outer_max_y - complete_radii[0]))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def add_arc_or_line(end_point: Point2, center_point: Point2, radius: float, *, min_chord: float) -> None:
        start_point = points[-1]
        if math.hypot(end_point[0] - start_point[0], end_point[1] - start_point[1]) <= min_chord:
            add_line(end_point, offset=radius)
        else:
            add_arc(end_point, center_point, radius)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_top_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def beta_point(radius: float) -> Point2:
        return point(
            seed_min_x + (radius * math.cos(beta_angle)),
            seed_min_y - (radius * math.sin(beta_angle)),
        )

    def append_top_right_arc(radius: float) -> None:
        diagonal = radius / math.sqrt(2.0)
        diagonal_point = point(seed_max_x + diagonal, seed_max_y + diagonal)
        if top(radius) >= seed_max_y + diagonal - 1e-6:
            if math.hypot(diagonal_point[0] - points[-1][0], diagonal_point[1] - points[-1][1]) > 2.0:
                add_arc(diagonal_point, (seed_max_x, seed_max_y), radius)
            else:
                add_line(diagonal_point, offset=radius)
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y), radius)

    def append_complete_loop(radius: float) -> None:
        diagonal = radius / math.sqrt(2.0)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y), radius)
        add_line(point(seed_max_x, seed_max_y + radius), offset=radius)
        add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y), radius)
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y), radius)
        add_line(point(seed_max_x + radius, seed_min_y), offset=radius)
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y), radius)
        add_line(point(seed_min_x, seed_min_y - radius), offset=radius)
        add_arc_or_line(beta_point(radius), (seed_min_x, seed_min_y), radius, min_chord=complete_loop_min_chord)

    for index, radius in enumerate(complete_radii[:-1]):
        next_radius = complete_radii[index + 1]
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(next_radius), top(next_radius)), offset=next_radius)

    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(left(min_partial), bottom(max_complete)), offset=min_partial)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(right(min_partial), top(max_complete)), offset=min_partial)
    add_line(point(left(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(left(min_partial), bottom(max_complete)), offset=min_partial)

    first_pre_entry = partial_radii[1]
    add_line(point(left(min_partial), bottom(min_partial)), offset=min_partial)
    add_line(point(left(first_pre_entry), bottom(min_partial)), offset=first_pre_entry)

    for index, radius in enumerate(partial_radii):
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(left_top_intersection(radius), (seed_min_x, seed_max_y), radius)
        add_line(point(left(radius), top(radius)), offset=radius)

        if index + 1 < len(partial_radii):
            next_radius = partial_radii[index + 1]
            after_next = partial_radii[index + 2] if index + 2 < len(partial_radii) else bridge_radius
            add_line(point(left(radius), bottom(radius)), offset=radius)
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
            add_line(point(left(next_radius), bottom(next_radius)), offset=next_radius)
            add_line(point(left(after_next), bottom(next_radius)), offset=after_next)
            continue

        add_line(point(left(radius), top(bridge_radius)), offset=bridge_radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(left(bridge_radius), bottom(radius)), offset=bridge_radius)

    add_line(point(left(bridge_radius), bottom(bridge_radius)), offset=bridge_radius)
    add_line(point(left(extra_radii[0]), bottom(bridge_radius)), offset=extra_radii[0])
    add_line(left_bottom_intersection(bridge_radius), offset=bridge_radius)
    add_arc(_circle_x_intersection_y((seed_min_x, seed_min_y), bridge_radius, left(bridge_radius), upper=False), (seed_min_x, seed_min_y), bridge_radius)
    add_line(point(left(bridge_radius), bottom(bridge_radius)), offset=bridge_radius)

    for index, radius in enumerate(extra_radii):
        previous_radius = bridge_radius if index == 0 else extra_radii[index - 1]
        next_radius = extra_radii[index + 1] if index + 1 < len(extra_radii) else None
        add_line(point(left(radius), bottom(previous_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc_or_line(
            _circle_x_intersection_y((seed_min_x, seed_min_y), radius, left(radius), upper=False),
            (seed_min_x, seed_min_y),
            radius,
            min_chord=2.5,
        )
        add_line(point(left(radius), bottom(radius)), offset=radius)

    current_radius = extra_radii[-1]
    for previous_radius in reversed((bridge_radius, *extra_radii[:-1])):
        add_line(point(left(current_radius), bottom(previous_radius)), offset=current_radius)
        add_line(point(left(previous_radius), bottom(previous_radius)), offset=previous_radius)
        current_radius = previous_radius
    add_line(point(left(bridge_radius), bottom(max_partial)), offset=bridge_radius)

    add_line(left_bottom_intersection(max_partial), offset=max_partial)
    add_arc(point(seed_min_x - max_partial, seed_min_y), (seed_min_x, seed_min_y), max_partial)
    add_line(point(seed_min_x - max_partial, seed_max_y), offset=max_partial)
    add_arc(left_top_intersection(max_partial), (seed_min_x, seed_max_y), max_partial)
    add_line(point(left(max_partial), top(max_partial)), offset=max_partial)
    add_line(point(left(max_partial), top(bridge_radius)), offset=bridge_radius)
    add_line(point(left(bridge_radius), top(bridge_radius)), offset=bridge_radius)

    add_line(point(left(bridge_radius), top(extra_radii[0])), offset=extra_radii[0])
    add_line(_circle_x_intersection_y((seed_min_x, seed_max_y), bridge_radius, left(bridge_radius), upper=True), offset=bridge_radius)
    add_arc(left_top_intersection(bridge_radius), (seed_min_x, seed_max_y), bridge_radius)
    add_line(point(left(bridge_radius), top(bridge_radius)), offset=bridge_radius)
    add_line(point(left(bridge_radius), top(extra_radii[0])), offset=extra_radii[0])

    for index, radius in enumerate(extra_radii):
        next_radius = extra_radii[index + 1] if index + 1 < len(extra_radii) else None
        add_line(point(left(radius), top(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(left(radius), top(next_radius)), offset=next_radius)
        add_line(_circle_x_intersection_y((seed_min_x, seed_max_y), radius, left(radius), upper=True), offset=radius)
        add_arc_or_line(left_top_intersection(radius), (seed_min_x, seed_max_y), radius, min_chord=2.5)
        add_line(point(left(radius), top(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(left(radius), top(next_radius)), offset=next_radius)

    current_radius = extra_radii[-1]
    for previous_radius in reversed((bridge_radius, *extra_radii[:-1])):
        add_line(point(left(previous_radius), top(current_radius)), offset=current_radius)
        add_line(point(left(previous_radius), top(previous_radius)), offset=previous_radius)
        current_radius = previous_radius
    add_line(point(left(max_partial), top(bridge_radius)), offset=bridge_radius)
    add_line(point(left(max_partial), bottom(max_partial)), offset=max_partial)

    current_x_radius = max_partial
    for index in range(len(partial_radii) - 2, -1, -1):
        radius = partial_radii[index]
        add_line(point(left(current_x_radius), bottom(radius)), offset=radius)
        if index > 0:
            add_line(point(left(radius), bottom(radius)), offset=radius)
            current_x_radius = radius

    add_line(left_bottom_intersection(min_partial), offset=min_partial)
    add_line(beta_point(max_complete), offset=max_complete)

    for index, radius in enumerate(reversed(complete_radii)):
        append_complete_loop(radius)
        remaining = tuple(reversed(complete_radii))[index + 1 :]
        if remaining:
            add_line(beta_point(remaining[0]), offset=remaining[0])

    for radius in complete_radii[1:]:
        add_line(beta_point(radius), offset=radius)

    add_line(left_bottom_intersection(min_partial), offset=min_partial)
    add_line(point(left(partial_radii[1]), bottom(min_partial)), offset=partial_radii[1])
    add_line(point(left(min_partial), bottom(min_partial)), offset=min_partial)
    add_line(point(left(min_partial), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(right(min_partial), top(max_complete)), offset=min_partial)
    add_line(point(right(min_partial), top(min_partial)), offset=min_partial)
    add_line(point(right(partial_radii[1]), top(min_partial)), offset=partial_radii[1])

    for index, radius in enumerate(partial_radii):
        add_line(right_top_intersection(radius), offset=radius)
        append_top_right_arc(radius)
        add_line(point(seed_max_x + radius, seed_min_y), offset=radius)
        add_arc(right_bottom_intersection(radius), (seed_max_x, seed_min_y), radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)

        if index + 1 < len(partial_radii):
            next_radius = partial_radii[index + 1]
            after_next = partial_radii[index + 2] if index + 2 < len(partial_radii) else bridge_radius
            add_line(point(right(radius), top(radius)), offset=radius)
            add_line(point(right(next_radius), top(radius)), offset=next_radius)
            add_line(point(right(next_radius), top(next_radius)), offset=next_radius)
            add_line(point(right(after_next), top(next_radius)), offset=after_next)
            continue

        add_line(point(right(radius), bottom(bridge_radius)), offset=bridge_radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(right(bridge_radius), top(radius)), offset=bridge_radius)
        add_line(point(right(bridge_radius), top(bridge_radius)), offset=bridge_radius)
        add_line(point(right(extra_radii[0]), top(bridge_radius)), offset=extra_radii[0])
        add_line(right_top_intersection(bridge_radius), offset=bridge_radius)
        add_arc(
            _circle_x_intersection_y((seed_max_x, seed_max_y), bridge_radius, right(bridge_radius), upper=True),
            (seed_max_x, seed_max_y),
            bridge_radius,
        )
        add_line(point(right(bridge_radius), top(bridge_radius)), offset=bridge_radius)
        add_line(point(right(extra_radii[0]), top(bridge_radius)), offset=extra_radii[0])

    for index, radius in enumerate(extra_radii):
        next_radius = extra_radii[index + 1] if index + 1 < len(extra_radii) else None
        add_line(point(right(radius), top(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(right(next_radius), top(radius)), offset=next_radius)
        add_line(right_top_intersection(radius), offset=radius)
        add_arc_or_line(
            _circle_x_intersection_y((seed_max_x, seed_max_y), radius, right(radius), upper=True),
            (seed_max_x, seed_max_y),
            radius,
            min_chord=2.5,
        )
        add_line(point(right(radius), top(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(right(next_radius), top(radius)), offset=next_radius)
            add_line(point(right(next_radius), top(next_radius)), offset=next_radius)

    current_radius = extra_radii[-1]
    for previous_radius in reversed((bridge_radius, *extra_radii[:-1])):
        add_line(point(right(current_radius), top(previous_radius)), offset=current_radius)
        add_line(point(right(previous_radius), top(previous_radius)), offset=previous_radius)
        current_radius = previous_radius
    add_line(point(right(bridge_radius), top(max_partial)), offset=bridge_radius)

    add_line(right_top_intersection(max_partial), offset=max_partial)
    append_top_right_arc(max_partial)
    add_line(point(seed_max_x + max_partial, seed_min_y), offset=max_partial)
    add_arc(right_bottom_intersection(max_partial), (seed_max_x, seed_min_y), max_partial)
    add_line(point(right(max_partial), bottom(max_partial)), offset=max_partial)
    add_line(point(right(max_partial), bottom(bridge_radius)), offset=bridge_radius)
    add_line(point(right(bridge_radius), bottom(bridge_radius)), offset=bridge_radius)
    add_line(point(right(bridge_radius), bottom(extra_radii[0])), offset=extra_radii[0])
    add_line(_circle_x_intersection_y((seed_max_x, seed_min_y), bridge_radius, right(bridge_radius), upper=False), offset=bridge_radius)
    add_arc(right_bottom_intersection(bridge_radius), (seed_max_x, seed_min_y), bridge_radius)
    add_line(point(right(bridge_radius), bottom(bridge_radius)), offset=bridge_radius)
    add_line(point(right(bridge_radius), bottom(extra_radii[0])), offset=extra_radii[0])

    for index, radius in enumerate(extra_radii):
        next_radius = extra_radii[index + 1] if index + 1 < len(extra_radii) else None
        add_line(point(right(radius), bottom(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(right(radius), bottom(next_radius)), offset=next_radius)
        add_line(_circle_x_intersection_y((seed_max_x, seed_min_y), radius, right(radius), upper=False), offset=radius)
        add_arc_or_line(right_bottom_intersection(radius), (seed_max_x, seed_min_y), radius, min_chord=2.5)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        if next_radius is not None:
            add_line(point(right(radius), bottom(next_radius)), offset=next_radius)

    return TraceResolvedSequence2D(
        name="single_seed_dense_bridge_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_dense_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None or not _has_balanced_clearance(family.clearance):
        return None
    if len(family.complete_offsets) < 2 or len(family.partial_offsets) < 2:
        return None

    complete_radii = tuple(float(value) for value in family.complete_offsets)
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    radial_step = _inferred_offset_step((*complete_radii, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    min_partial = partial_radii[0]
    max_partial = partial_radii[-1]
    max_complete = complete_radii[-1]
    extra_radii = _dense_bridge_extra_radii(
        outer_bbox,
        family.contour.bbox,
        max_partial,
        radial_step,
    )
    if not extra_radii:
        return None

    partial_bottom_y = outer_min_y + min_partial
    sin_beta = (seed_min_y - partial_bottom_y) / min_partial
    if sin_beta <= -1.0 or sin_beta >= 1.0:
        return None
    beta_angle = math.pi - math.asin(sin_beta)

    owner = "single_seed_dense_partial_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_radii[0], outer_max_y - complete_radii[0]))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def add_arc_or_line(end_point: Point2, center_point: Point2, radius: float, *, min_chord: float) -> None:
        start_point = points[-1]
        if math.hypot(end_point[0] - start_point[0], end_point[1] - start_point[1]) <= min_chord:
            add_line(end_point, offset=radius)
        else:
            add_arc(end_point, center_point, radius)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_top_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def beta_point(radius: float) -> Point2:
        return point(
            seed_min_x + (radius * math.cos(beta_angle)),
            seed_min_y - (radius * math.sin(beta_angle)),
        )

    def append_top_right_arc(radius: float) -> None:
        diagonal = radius / math.sqrt(2.0)
        diagonal_point = point(seed_max_x + diagonal, seed_max_y + diagonal)
        if top(radius) >= seed_max_y + diagonal - 1e-6:
            if math.hypot(diagonal_point[0] - points[-1][0], diagonal_point[1] - points[-1][1]) > 2.0:
                add_arc(diagonal_point, (seed_max_x, seed_max_y), radius)
            else:
                add_line(diagonal_point, offset=radius)
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y), radius)

    def append_complete_loop(radius: float) -> None:
        diagonal = radius / math.sqrt(2.0)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y), radius)
        add_line(point(seed_max_x, seed_max_y + radius), offset=radius)
        add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y), radius)
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y), radius)
        add_line(point(seed_max_x + radius, seed_min_y), offset=radius)
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y), radius)
        add_line(point(seed_min_x, seed_min_y - radius), offset=radius)
        add_arc_or_line(beta_point(radius), (seed_min_x, seed_min_y), radius, min_chord=0.5)

    for index, radius in enumerate(complete_radii[:-1]):
        next_radius = complete_radii[index + 1]
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(next_radius), top(next_radius)), offset=next_radius)

    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(left(min_partial), bottom(max_complete)), offset=min_partial)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(right(min_partial), top(max_complete)), offset=min_partial)
    add_line(point(left(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(left(min_partial), bottom(max_complete)), offset=min_partial)

    add_line(point(left(min_partial), bottom(min_partial)), offset=min_partial)
    add_line(point(left(partial_radii[1]), bottom(min_partial)), offset=partial_radii[1])

    for index, radius in enumerate(partial_radii):
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(left_top_intersection(radius), (seed_min_x, seed_max_y), radius)
        add_line(point(left(radius), top(radius)), offset=radius)

        if index + 1 < len(partial_radii):
            next_radius = partial_radii[index + 1]
            after_next = partial_radii[index + 2] if index + 2 < len(partial_radii) else extra_radii[0]
            add_line(point(left(radius), bottom(radius)), offset=radius)
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
            add_line(point(left(next_radius), bottom(next_radius)), offset=next_radius)
            add_line(point(left(after_next), bottom(next_radius)), offset=after_next)
            continue

        add_line(point(left(radius), top(extra_radii[0])), offset=extra_radii[0])
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(left(extra_radii[0]), bottom(radius)), offset=extra_radii[0])

    for radius in extra_radii:
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc_or_line(
            _circle_x_intersection_y((seed_min_x, seed_min_y), radius, left(radius), upper=False),
            (seed_min_x, seed_min_y),
            radius,
            min_chord=2.5,
        )
        add_line(point(left(radius), bottom(radius)), offset=radius)

    add_line(point(left(extra_radii[-1]), bottom(max_partial)), offset=max_partial)
    add_line(left_bottom_intersection(max_partial), offset=max_partial)
    add_arc(point(seed_min_x - max_partial, seed_min_y), (seed_min_x, seed_min_y), max_partial)
    add_line(point(seed_min_x - max_partial, seed_max_y), offset=max_partial)
    add_arc(left_top_intersection(max_partial), (seed_min_x, seed_max_y), max_partial)
    add_line(point(left(max_partial), top(max_partial)), offset=max_partial)
    add_line(point(left(max_partial), top(extra_radii[0])), offset=extra_radii[0])

    for radius in extra_radii:
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(_circle_x_intersection_y((seed_min_x, seed_max_y), radius, left(radius), upper=True), offset=radius)
        add_arc_or_line(left_top_intersection(radius), (seed_min_x, seed_max_y), radius, min_chord=2.5)
        add_line(point(left(radius), top(radius)), offset=radius)

    add_line(point(left(max_partial), top(extra_radii[0])), offset=extra_radii[0])
    add_line(point(left(max_partial), bottom(max_partial)), offset=max_partial)

    current_x_radius = max_partial
    for index in range(len(partial_radii) - 2, -1, -1):
        radius = partial_radii[index]
        add_line(point(left(current_x_radius), bottom(radius)), offset=radius)
        if index > 0:
            add_line(point(left(radius), bottom(radius)), offset=radius)
            current_x_radius = radius

    add_line(left_bottom_intersection(min_partial), offset=min_partial)
    add_line(beta_point(max_complete), offset=max_complete)

    for index, radius in enumerate(reversed(complete_radii)):
        append_complete_loop(radius)
        remaining = tuple(reversed(complete_radii))[index + 1 :]
        if remaining:
            add_line(beta_point(remaining[0]), offset=remaining[0])

    for radius in complete_radii[1:]:
        add_line(beta_point(radius), offset=radius)

    add_line(left_bottom_intersection(min_partial), offset=min_partial)
    add_line(point(left(partial_radii[1]), bottom(min_partial)), offset=partial_radii[1])
    add_line(point(left(min_partial), bottom(min_partial)), offset=min_partial)
    add_line(point(left(min_partial), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(right(min_partial), top(max_complete)), offset=min_partial)
    add_line(point(right(min_partial), top(min_partial)), offset=min_partial)
    add_line(point(right(partial_radii[1]), top(min_partial)), offset=partial_radii[1])

    for index, radius in enumerate(partial_radii):
        add_line(right_top_intersection(radius), offset=radius)
        append_top_right_arc(radius)
        add_line(point(seed_max_x + radius, seed_min_y), offset=radius)
        add_arc(right_bottom_intersection(radius), (seed_max_x, seed_min_y), radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)

        if index + 1 < len(partial_radii):
            next_radius = partial_radii[index + 1]
            after_next = partial_radii[index + 2] if index + 2 < len(partial_radii) else extra_radii[0]
            add_line(point(right(radius), top(radius)), offset=radius)
            add_line(point(right(next_radius), top(radius)), offset=next_radius)
            add_line(point(right(next_radius), top(next_radius)), offset=next_radius)
            add_line(point(right(after_next), top(next_radius)), offset=after_next)
            continue

        add_line(point(right(radius), bottom(extra_radii[0])), offset=extra_radii[0])
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(right(extra_radii[0]), top(radius)), offset=extra_radii[0])
        add_line(point(right(extra_radii[0]), top(extra_radii[0])), offset=extra_radii[0])

    for radius in extra_radii:
        add_line(right_top_intersection(radius), offset=radius)
        add_arc_or_line(
            _circle_x_intersection_y((seed_max_x, seed_max_y), radius, right(radius), upper=True),
            (seed_max_x, seed_max_y),
            radius,
            min_chord=2.5,
        )
        add_line(point(right(radius), top(radius)), offset=radius)

    add_line(point(right(extra_radii[-1]), top(max_partial)), offset=max_partial)
    add_line(right_top_intersection(max_partial), offset=max_partial)
    append_top_right_arc(max_partial)
    add_line(point(seed_max_x + max_partial, seed_min_y), offset=max_partial)
    add_arc(right_bottom_intersection(max_partial), (seed_max_x, seed_min_y), max_partial)
    add_line(point(right(max_partial), bottom(max_partial)), offset=max_partial)
    add_line(point(right(max_partial), bottom(extra_radii[0])), offset=extra_radii[0])
    add_line(point(right(extra_radii[0]), bottom(extra_radii[0])), offset=extra_radii[0])

    for radius in extra_radii:
        add_line(_circle_x_intersection_y((seed_max_x, seed_min_y), radius, right(radius), upper=False), offset=radius)
        add_arc_or_line(right_bottom_intersection(radius), (seed_max_x, seed_min_y), radius, min_chord=2.5)
        add_line(point(right(radius), bottom(radius)), offset=radius)

    return TraceResolvedSequence2D(
        name="single_seed_dense_partial_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_left_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.left <= family.clearance.right + 1e-6:
        return None
    if len(family.complete_offsets) != 1 or len(family.partial_offsets) != 2:
        return None

    complete_offset = float(family.complete_offsets[0])
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    if partial_radii[0] <= (family.clearance.right / 2.0) + 1e-6:
        return None
    if partial_radii[-1] > (family.clearance.left / 2.0) + 1e-6:
        return None
    radial_step = _inferred_offset_step((complete_offset, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, _seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    min_partial = partial_radii[0]
    max_partial = partial_radii[-1]

    owner = "single_seed_unbalanced_left_partial_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_offset, outer_max_y - complete_offset))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(left(min_partial), bottom(complete_offset)), offset=min_partial)
    add_line(point(right(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(left(min_partial), bottom(complete_offset)), offset=min_partial)
    add_line(point(left(min_partial), bottom(min_partial)), offset=min_partial)
    add_line(point(left(max_partial), bottom(min_partial)), offset=max_partial)

    for index, radius in enumerate(partial_radii):
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(left_top_intersection(radius), (seed_min_x, seed_max_y), radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        if index + 1 < len(partial_radii):
            next_radius = partial_radii[index + 1]
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
            add_line(point(left(next_radius), bottom(next_radius)), offset=next_radius)

    add_line(point(left(max_partial), bottom(min_partial)), offset=min_partial)
    add_line(left_bottom_intersection(min_partial), offset=min_partial)
    split_point = _radial_projection(
        (seed_min_x, seed_min_y),
        left_bottom_intersection(min_partial),
        min_partial,
        complete_offset,
    )
    add_line(split_point, offset=complete_offset)
    _append_bottom_left_split_rounded_loop(primitives, family.contour.bbox, complete_offset, split_point)

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_left_partial_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_left_terminal_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.left <= family.clearance.right + 1e-6:
        return None
    if len(family.complete_offsets) != 1 or len(family.partial_offsets) != 3:
        return None

    complete_offset = float(family.complete_offsets[0])
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    terminal_gap = (family.clearance.left / 2.0) - partial_radii[-1]
    if terminal_gap < -1e-6 or terminal_gap > 3.0 + 1e-6:
        return None
    radial_step = _inferred_offset_step((complete_offset, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    first_partial, middle_partial, terminal_partial = partial_radii

    owner = "single_seed_unbalanced_left_terminal_partial_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_offset, outer_max_y - complete_offset))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_y(radius: float, center_x: float, x_value: float, *, upper: bool) -> float:
        delta_x = center_x - x_value
        delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
        return (seed_min_y if not upper else seed_max_y) + (delta_y if upper else -delta_y)

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=False))

    def right_top_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=True))

    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(first_partial)), offset=first_partial)
    add_line(point(right(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)
    add_arc(point(seed_max_x, seed_min_y - first_partial), (seed_max_x, seed_min_y), first_partial)
    add_line(point(seed_min_x, seed_min_y - first_partial), offset=first_partial)
    add_arc(point(seed_min_x - first_partial, seed_min_y), (seed_min_x, seed_min_y), first_partial)
    add_line(point(seed_min_x - first_partial, seed_max_y), offset=first_partial)
    add_arc(point(seed_min_x, seed_max_y + first_partial), (seed_min_x, seed_max_y), first_partial)
    add_line(point(seed_max_x, seed_max_y + first_partial), offset=first_partial)
    add_arc(right_top_intersection(first_partial), (seed_max_x, seed_max_y), first_partial)
    add_line(point(right(first_partial), top(first_partial)), offset=first_partial)
    add_line(point(left(first_partial), top(first_partial)), offset=first_partial)
    add_line(point(left(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)

    complete_split = _radial_projection(
        (seed_max_x, seed_min_y),
        right_bottom_intersection(first_partial),
        first_partial,
        complete_offset,
    )
    add_line(complete_split, offset=complete_offset)
    _append_bottom_right_split_rounded_loop(primitives, family.contour.bbox, complete_offset, complete_split)
    points[:] = [primitives[-1].end]

    add_line(right_bottom_intersection(first_partial), offset=first_partial)
    add_arc(point(seed_max_x, seed_min_y - first_partial), (seed_max_x, seed_min_y), first_partial)
    add_line(point(seed_min_x, seed_min_y - first_partial), offset=first_partial)
    add_arc(point(seed_min_x - first_partial, seed_min_y), (seed_min_x, seed_min_y), first_partial)

    add_line(point(seed_min_x - middle_partial, seed_min_y), offset=middle_partial)
    add_line(point(seed_min_x - middle_partial, seed_max_y), offset=middle_partial)
    add_arc(left_top_intersection(middle_partial), (seed_min_x, seed_max_y), middle_partial)
    add_line(point(left(middle_partial), top(middle_partial)), offset=middle_partial)
    add_line(point(left(middle_partial), bottom(middle_partial)), offset=middle_partial)
    add_line(left_bottom_intersection(middle_partial), offset=middle_partial)
    add_arc(point(seed_min_x - middle_partial, seed_min_y), (seed_min_x, seed_min_y), middle_partial)

    add_line(point(seed_min_x - terminal_partial, seed_min_y), offset=terminal_partial)
    add_line(point(seed_min_x - terminal_partial, seed_max_y), offset=terminal_partial)
    add_arc(left_top_intersection(terminal_partial), (seed_min_x, seed_max_y), terminal_partial)
    add_line(point(left(terminal_partial), top(terminal_partial)), offset=terminal_partial)
    add_line(point(left(terminal_partial), bottom(terminal_partial)), offset=terminal_partial)
    add_line(left_bottom_intersection(terminal_partial), offset=terminal_partial)
    add_arc(point(seed_min_x - terminal_partial, seed_min_y), (seed_min_x, seed_min_y), terminal_partial)

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_left_terminal_partial_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_left_early_dense_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.left <= family.clearance.right + 1e-6:
        return None
    if len(family.complete_offsets) != 6 or len(family.partial_offsets) != 11:
        return None

    complete_radii = tuple(float(value) for value in family.complete_offsets)
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    radial_step = _inferred_offset_step((*complete_radii, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    max_complete = complete_radii[-1]
    first_partial, second_partial, third_partial = partial_radii[:3]

    owner = "single_seed_unbalanced_left_early_dense_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_radii[0], outer_max_y - complete_radii[0]))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_y(radius: float, center_x: float, x_value: float, *, upper: bool) -> float:
        delta_x = center_x - x_value
        delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
        return (seed_min_y if not upper else seed_max_y) + (delta_y if upper else -delta_y)

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=False))

    def right_top_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=True))

    def radial_projection(center: Point2, source: Point2, source_radius: float, radius: float) -> Point2:
        return _radial_projection(center, source, source_radius, radius)

    def top_right_diagonal(radius: float) -> Point2:
        diagonal = radius / math.sqrt(2.0)
        return point(seed_max_x + diagonal, seed_max_y + diagonal)

    def append_clipped_right_loop(radius: float) -> None:
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y), radius)
        add_line(point(seed_min_x, seed_min_y - radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y), radius)
        add_line(point(seed_max_x, seed_max_y + radius), offset=radius)
        diagonal = top_right_diagonal(radius)
        if right(radius) >= diagonal[0] - 1e-6 and top(radius) >= diagonal[1] - 1e-6:
            add_arc(diagonal, (seed_max_x, seed_max_y), radius)
        add_arc(right_top_intersection(radius), (seed_max_x, seed_max_y), radius)
        add_line(point(right(radius), top(radius)), offset=radius)

    for index, radius in enumerate(complete_radii[:-1]):
        next_radius = complete_radii[index + 1]
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(next_radius), top(next_radius)), offset=next_radius)

    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(first_partial)), offset=first_partial)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(second_partial)), offset=second_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)
    append_clipped_right_loop(first_partial)
    add_line(point(left(first_partial), top(first_partial)), offset=first_partial)
    add_line(point(left(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(third_partial)), offset=third_partial)
    add_line(right_bottom_intersection(second_partial), offset=second_partial)
    append_clipped_right_loop(second_partial)
    add_line(point(left(second_partial), top(second_partial)), offset=second_partial)
    add_line(point(left(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(third_partial)), offset=third_partial)
    add_line(point(right(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(right_bottom_intersection(third_partial), offset=third_partial)
    append_clipped_right_loop(third_partial)
    add_line(point(left(third_partial), top(third_partial)), offset=third_partial)
    add_line(point(left(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(point(left(partial_radii[3]), bottom(third_partial)), offset=partial_radii[3])
    add_line(point(right(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(right_bottom_intersection(third_partial), offset=third_partial)
    append_clipped_right_loop(third_partial)
    add_line(point(left(third_partial), top(third_partial)), offset=third_partial)
    add_line(point(left(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(point(left(partial_radii[3]), bottom(third_partial)), offset=partial_radii[3])
    add_line(point(left(partial_radii[3]), bottom(partial_radii[3])), offset=partial_radii[3])
    add_line(point(left(partial_radii[4]), bottom(partial_radii[3])), offset=partial_radii[4])

    left_partials = partial_radii[3:]
    for index, radius in enumerate(left_partials):
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(left_top_intersection(radius), (seed_min_x, seed_max_y), radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        if index + 1 < len(left_partials):
            next_radius = left_partials[index + 1]
            after_next = left_partials[index + 2] if index + 2 < len(left_partials) else None
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
            add_line(point(left(next_radius), bottom(next_radius)), offset=next_radius)
            if after_next is not None:
                add_line(point(left(after_next), bottom(next_radius)), offset=after_next)

    current_radius = partial_radii[-1]
    for previous_radius in reversed(partial_radii[3:-1]):
        add_line(point(left(current_radius), bottom(previous_radius)), offset=previous_radius)
        add_line(point(left(previous_radius), bottom(previous_radius)), offset=previous_radius)
        current_radius = previous_radius
    add_line(point(left(partial_radii[3]), bottom(third_partial)), offset=third_partial)
    add_line(point(right(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(point(right(second_partial), bottom(third_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(first_partial), bottom(second_partial)), offset=first_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)

    split_source = right_bottom_intersection(first_partial)
    for radius in reversed(complete_radii):
        split = radial_projection((seed_max_x, seed_min_y), split_source, first_partial, radius)
        add_line(split, offset=radius)
        _append_bottom_right_split_rounded_loop(primitives, family.contour.bbox, radius, split)
        points[:] = [primitives[-1].end]

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_left_early_dense_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_left_dense_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.left <= family.clearance.right + 1e-6:
        return None
    if len(family.complete_offsets) != 7 or len(family.partial_offsets) != 11:
        return None

    complete_radii = tuple(float(value) for value in family.complete_offsets)
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    radial_step = _inferred_offset_step((*complete_radii, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    max_complete = complete_radii[-1]
    first_partial, second_partial, third_partial = partial_radii[:3]

    owner = "single_seed_unbalanced_left_dense_partial_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_radii[0], outer_max_y - complete_radii[0]))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_y(radius: float, center_x: float, x_value: float, *, upper: bool) -> float:
        delta_x = center_x - x_value
        delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
        return (seed_min_y if not upper else seed_max_y) + (delta_y if upper else -delta_y)

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=False))

    def right_top_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=True))

    def right_bottom_y_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def right_top_y_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def radial_projection(center: Point2, source: Point2, source_radius: float, radius: float) -> Point2:
        return _radial_projection(center, source, source_radius, radius)

    def top_right_diagonal(radius: float) -> Point2:
        diagonal = radius / math.sqrt(2.0)
        return point(seed_max_x + diagonal, seed_max_y + diagonal)

    def append_clipped_right_loop(radius: float) -> None:
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y), radius)
        add_line(point(seed_min_x, seed_min_y - radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y), radius)
        add_line(point(seed_max_x, seed_max_y + radius), offset=radius)
        diagonal = top_right_diagonal(radius)
        if right(radius) >= diagonal[0] - 1e-6 and top(radius) >= diagonal[1] - 1e-6:
            add_arc(diagonal, (seed_max_x, seed_max_y), radius)
        add_arc(right_top_intersection(radius), (seed_max_x, seed_max_y), radius)
        add_line(point(right(radius), top(radius)), offset=radius)

    for index, radius in enumerate(complete_radii[:-1]):
        next_radius = complete_radii[index + 1]
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(next_radius), top(next_radius)), offset=next_radius)

    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(first_partial)), offset=first_partial)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(second_partial)), offset=second_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)
    append_clipped_right_loop(first_partial)
    add_line(point(left(first_partial), top(first_partial)), offset=first_partial)
    add_line(point(left(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(third_partial)), offset=third_partial)
    add_line(right_bottom_intersection(second_partial), offset=second_partial)
    append_clipped_right_loop(second_partial)
    add_line(point(right(third_partial), top(second_partial)), offset=third_partial)
    add_line(point(left(second_partial), top(second_partial)), offset=second_partial)
    add_line(point(left(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(left(third_partial), bottom(second_partial)), offset=third_partial)
    add_line(point(right(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(third_partial)), offset=third_partial)
    add_line(point(right(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(right_bottom_intersection(third_partial), offset=third_partial)
    add_arc(right_bottom_y_intersection(third_partial), (seed_max_x, seed_min_y), third_partial)
    add_line(point(right(third_partial), bottom(third_partial)), offset=third_partial)
    add_line(point(right(second_partial), bottom(third_partial)), offset=second_partial)
    add_line(right_bottom_intersection(second_partial), offset=second_partial)
    append_clipped_right_loop(second_partial)
    add_line(point(right(third_partial), top(second_partial)), offset=third_partial)
    add_line(point(right(third_partial), top(third_partial)), offset=third_partial)
    add_line(right_top_y_intersection(third_partial), offset=third_partial)
    add_arc(right_top_intersection(third_partial), (seed_max_x, seed_max_y), third_partial)
    add_line(point(right(third_partial), top(third_partial)), offset=third_partial)
    add_line(point(right(third_partial), top(second_partial)), offset=third_partial)
    add_line(point(left(second_partial), top(second_partial)), offset=second_partial)
    add_line(point(left(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(left(third_partial), bottom(second_partial)), offset=third_partial)
    add_line(point(left(third_partial), bottom(third_partial)), offset=third_partial)

    left_partials = partial_radii[2:]
    for index, radius in enumerate(left_partials):
        if index == 0:
            add_line(point(left(partial_radii[3]), bottom(radius)), offset=partial_radii[3])
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(left_top_intersection(radius), (seed_min_x, seed_max_y), radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        if index + 1 < len(left_partials):
            next_radius = left_partials[index + 1]
            after_next = left_partials[index + 2] if index + 2 < len(left_partials) else None
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
            add_line(point(left(next_radius), bottom(next_radius)), offset=next_radius)
            if after_next is not None:
                add_line(point(left(after_next), bottom(next_radius)), offset=after_next)

    current_radius = partial_radii[-1]
    for previous_radius in reversed(partial_radii[2:-1]):
        add_line(point(left(current_radius), bottom(previous_radius)), offset=previous_radius)
        add_line(point(left(previous_radius), bottom(previous_radius)), offset=previous_radius)
        current_radius = previous_radius
    add_line(point(left(third_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(second_partial), bottom(second_partial)), offset=second_partial)
    add_line(point(right(first_partial), bottom(second_partial)), offset=first_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)

    split_source = right_bottom_intersection(first_partial)
    for radius in reversed(complete_radii):
        split = radial_projection((seed_max_x, seed_min_y), split_source, first_partial, radius)
        add_line(split, offset=radius)
        _append_bottom_right_split_rounded_loop(primitives, family.contour.bbox, radius, split)
        points[:] = [primitives[-1].end]

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_left_dense_partial_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_left_extended_dense_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.left <= family.clearance.right + 1e-6:
        return None
    if len(family.complete_offsets) < 13 or len(family.partial_offsets) < 21:
        return None

    complete_radii = tuple(float(value) for value in family.complete_offsets)
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    radial_step = _inferred_offset_step((*complete_radii, *partial_radii))
    if radial_step is None:
        return None
    if family.bridge_offset is not None and not math.isclose(
        float(family.bridge_offset) - partial_radii[-1],
        radial_step,
        abs_tol=1e-6,
    ):
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    max_complete = complete_radii[-1]

    owner = "single_seed_unbalanced_left_extended_dense_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_radii[0], outer_max_y - complete_radii[0]))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def add_arc_or_line(
        end_point: Point2,
        center_point: Point2,
        radius: float,
        *,
        min_chord: float = 3.0,
    ) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if math.hypot(end_point[0] - start_point[0], end_point[1] - start_point[1]) <= min_chord:
            add_line(end_point, offset=radius)
        else:
            add_arc(end_point, center_point, radius)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_y(radius: float, center_x: float, x_value: float, *, upper: bool) -> float:
        delta_x = center_x - x_value
        delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
        return (seed_min_y if not upper else seed_max_y) + (delta_y if upper else -delta_y)

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=False))

    def right_top_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=True))

    def right_bottom_y_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def right_top_y_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def bottom_x_intersection(radius: float) -> float:
        return right_intersection_x(radius, seed_min_y, bottom(radius))

    def vertical_gap(radius: float) -> float:
        return right_intersection_y(radius, seed_max_x, right(radius), upper=False) - bottom(radius)

    def top_right_diagonal(radius: float) -> Point2:
        diagonal = radius / math.sqrt(2.0)
        return point(seed_max_x + diagonal, seed_max_y + diagonal)

    def append_clipped_right_loop(radius: float) -> None:
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y), radius)
        add_line(point(seed_min_x, seed_min_y - radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y), radius)
        add_line(point(seed_max_x, seed_max_y + radius), offset=radius)
        diagonal = top_right_diagonal(radius)
        if right(radius) >= diagonal[0] - 1e-6 and top(radius) >= diagonal[1] - 1e-6:
            add_arc(diagonal, (seed_max_x, seed_max_y), radius)
        add_arc(right_top_intersection(radius), (seed_max_x, seed_max_y), radius)
        add_line(point(right(radius), top(radius)), offset=radius)

    transition_index = None
    for index, radius in enumerate(partial_radii):
        if bottom_x_intersection(radius) > seed_max_x + 1e-6:
            transition_index = index
            break
    if transition_index is None or transition_index < 1 or transition_index + 1 >= len(partial_radii):
        return None

    sliver_radii: list[float] = []
    for radius in partial_radii[transition_index:]:
        if vertical_gap(radius) <= 1e-6:
            break
        sliver_radii.append(radius)
    if not sliver_radii:
        return None

    for index, radius in enumerate(complete_radii[:-1]):
        next_radius = complete_radii[index + 1]
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(next_radius), top(next_radius)), offset=next_radius)

    first_partial = partial_radii[0]
    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(first_partial)), offset=first_partial)
    add_line(point(right(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), top(max_complete)), offset=max_complete)
    add_line(point(left(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(max_complete)), offset=max_complete)
    add_line(point(right(max_complete), bottom(first_partial)), offset=first_partial)

    for index, radius in enumerate(partial_radii[:transition_index]):
        next_radius = partial_radii[index + 1]
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(next_radius)), offset=next_radius)
        add_line(right_bottom_intersection(radius), offset=radius)
        append_clipped_right_loop(radius)
        if index + 1 < transition_index:
            add_line(point(left(radius), top(radius)), offset=radius)
            add_line(point(left(radius), bottom(radius)), offset=radius)
            add_line(point(right(radius), bottom(radius)), offset=radius)
            add_line(point(right(radius), bottom(next_radius)), offset=next_radius)

    previous_right_radius = partial_radii[transition_index - 1]
    left_start_radius = partial_radii[transition_index]
    after_left_start_radius = partial_radii[transition_index + 1]

    add_line(point(right(left_start_radius), top(previous_right_radius)), offset=left_start_radius)
    add_line(point(left(previous_right_radius), top(previous_right_radius)), offset=previous_right_radius)
    add_line(point(left(previous_right_radius), bottom(previous_right_radius)), offset=previous_right_radius)
    add_line(point(left(left_start_radius), bottom(previous_right_radius)), offset=left_start_radius)
    add_line(point(right(previous_right_radius), bottom(previous_right_radius)), offset=previous_right_radius)
    add_line(point(right(previous_right_radius), bottom(left_start_radius)), offset=left_start_radius)

    for index, radius in enumerate(sliver_radii):
        next_sliver = sliver_radii[index + 1] if index + 1 < len(sliver_radii) else None
        add_line(point(right(radius), bottom(radius)), offset=radius)
        if next_sliver is not None:
            add_line(point(right(radius), bottom(next_sliver)), offset=next_sliver)
        add_line(right_bottom_intersection(radius), offset=radius)
        add_arc_or_line(right_bottom_y_intersection(radius), (seed_max_x, seed_min_y), radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        if next_sliver is not None:
            add_line(point(right(radius), bottom(next_sliver)), offset=next_sliver)

    current_sliver = sliver_radii[-1]
    for radius in reversed(sliver_radii[:-1]):
        add_line(point(right(radius), bottom(current_sliver)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        current_sliver = radius

    add_line(point(right(previous_right_radius), bottom(sliver_radii[0])), offset=previous_right_radius)
    add_line(right_bottom_intersection(previous_right_radius), offset=previous_right_radius)
    append_clipped_right_loop(previous_right_radius)

    add_line(point(right(left_start_radius), top(previous_right_radius)), offset=left_start_radius)
    if len(sliver_radii) > 1:
        add_line(point(right(left_start_radius), top(left_start_radius)), offset=left_start_radius)
        for index, radius in enumerate(sliver_radii):
            next_sliver = sliver_radii[index + 1] if index + 1 < len(sliver_radii) else None
            if next_sliver is not None:
                add_line(point(right(next_sliver), top(radius)), offset=next_sliver)
            add_line(right_top_y_intersection(radius), offset=radius)
            add_arc_or_line(right_top_intersection(radius), (seed_max_x, seed_max_y), radius)
            add_line(point(right(radius), top(radius)), offset=radius)
            if next_sliver is not None:
                add_line(point(right(next_sliver), top(radius)), offset=next_sliver)
                add_line(point(right(next_sliver), top(next_sliver)), offset=next_sliver)

        current_sliver = sliver_radii[-1]
        for radius in reversed(sliver_radii[:-1]):
            add_line(point(right(current_sliver), top(radius)), offset=current_sliver)
            add_line(point(right(radius), top(radius)), offset=radius)
            current_sliver = radius
        add_line(point(right(left_start_radius), top(previous_right_radius)), offset=left_start_radius)
    else:
        add_line(point(right(left_start_radius), top(left_start_radius)), offset=left_start_radius)
        add_line(right_top_y_intersection(left_start_radius), offset=left_start_radius)
        add_arc_or_line(
            right_top_intersection(left_start_radius),
            (seed_max_x, seed_max_y),
            left_start_radius,
        )
        add_line(point(right(left_start_radius), top(left_start_radius)), offset=left_start_radius)
        add_line(point(right(left_start_radius), top(previous_right_radius)), offset=left_start_radius)

    add_line(point(left(previous_right_radius), top(previous_right_radius)), offset=previous_right_radius)
    add_line(point(left(previous_right_radius), bottom(previous_right_radius)), offset=previous_right_radius)
    add_line(point(left(left_start_radius), bottom(previous_right_radius)), offset=left_start_radius)
    add_line(point(left(left_start_radius), bottom(left_start_radius)), offset=left_start_radius)
    add_line(point(left(after_left_start_radius), bottom(left_start_radius)), offset=after_left_start_radius)

    left_partials = partial_radii[transition_index:]
    for index, radius in enumerate(left_partials):
        add_line(left_bottom_intersection(radius), offset=radius)
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y), radius)
        add_line(point(seed_min_x - radius, seed_max_y), offset=radius)
        add_arc(left_top_intersection(radius), (seed_min_x, seed_max_y), radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        if index + 1 < len(left_partials):
            next_radius = left_partials[index + 1]
            after_next = left_partials[index + 2] if index + 2 < len(left_partials) else None
            add_line(point(left(next_radius), bottom(radius)), offset=next_radius)
            add_line(point(left(next_radius), bottom(next_radius)), offset=next_radius)
            if after_next is not None:
                add_line(point(left(after_next), bottom(next_radius)), offset=after_next)

    current_radius = left_partials[-1]
    for previous_radius in reversed(left_partials[:-1]):
        add_line(point(left(current_radius), bottom(previous_radius)), offset=previous_radius)
        add_line(point(left(previous_radius), bottom(previous_radius)), offset=previous_radius)
        current_radius = previous_radius

    add_line(point(left(left_partials[0]), bottom(previous_right_radius)), offset=previous_right_radius)
    add_line(point(right(previous_right_radius), bottom(previous_right_radius)), offset=previous_right_radius)
    for index in range(transition_index - 2, -1, -1):
        radius = partial_radii[index]
        next_radius = partial_radii[index + 1]
        add_line(point(right(radius), bottom(next_radius)), offset=radius)
        if index > 0:
            add_line(point(right(radius), bottom(radius)), offset=radius)

    add_line(right_bottom_intersection(first_partial), offset=first_partial)

    split_source = right_bottom_intersection(first_partial)
    for radius in reversed(complete_radii):
        split = _radial_projection((seed_max_x, seed_min_y), split_source, first_partial, radius)
        add_line(split, offset=radius)
        _append_bottom_right_split_rounded_loop(primitives, family.contour.bbox, radius, split)
        points[:] = [primitives[-1].end]

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_left_extended_dense_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_left_repeated_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.left <= family.clearance.right + 1e-6:
        return None
    if len(family.complete_offsets) != 1 or len(family.partial_offsets) != 3:
        return None

    complete_offset = float(family.complete_offsets[0])
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    terminal_gap = (family.clearance.left / 2.0) - partial_radii[-1]
    if terminal_gap <= 3.0 + 1e-6:
        return None
    radial_step = _inferred_offset_step((complete_offset, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    first_partial, middle_partial, terminal_partial = partial_radii

    owner = "single_seed_unbalanced_left_repeated_partial_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_offset, outer_max_y - complete_offset))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_y(radius: float, center_x: float, x_value: float, *, upper: bool) -> float:
        delta_x = center_x - x_value
        delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
        return (seed_min_y if not upper else seed_max_y) + (delta_y if upper else -delta_y)

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def left_top_intersection(radius: float) -> Point2:
        return point(left_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=False))

    def right_top_intersection(radius: float) -> Point2:
        return point(right(radius), right_intersection_y(radius, seed_max_x, right(radius), upper=True))

    def append_first_partial_loop() -> None:
        add_arc(point(seed_max_x, seed_min_y - first_partial), (seed_max_x, seed_min_y), first_partial)
        add_line(point(seed_min_x, seed_min_y - first_partial), offset=first_partial)
        add_arc(point(seed_min_x - first_partial, seed_min_y), (seed_min_x, seed_min_y), first_partial)
        add_line(point(seed_min_x - first_partial, seed_max_y), offset=first_partial)
        add_arc(point(seed_min_x, seed_max_y + first_partial), (seed_min_x, seed_max_y), first_partial)
        add_line(point(seed_max_x, seed_max_y + first_partial), offset=first_partial)
        add_arc(right_top_intersection(first_partial), (seed_max_x, seed_max_y), first_partial)
        add_line(point(right(first_partial), top(first_partial)), offset=first_partial)
        add_line(point(left(first_partial), top(first_partial)), offset=first_partial)
        add_line(point(left(first_partial), bottom(first_partial)), offset=first_partial)
        add_line(point(left(middle_partial), bottom(first_partial)), offset=middle_partial)

    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(first_partial)), offset=first_partial)
    add_line(point(right(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)
    append_first_partial_loop()
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(right_bottom_intersection(first_partial), offset=first_partial)

    complete_split = _radial_projection(
        (seed_max_x, seed_min_y),
        right_bottom_intersection(first_partial),
        first_partial,
        complete_offset,
    )
    add_line(complete_split, offset=complete_offset)
    _append_bottom_right_split_rounded_loop(primitives, family.contour.bbox, complete_offset, complete_split)
    points[:] = [primitives[-1].end]

    add_line(right_bottom_intersection(first_partial), offset=first_partial)
    append_first_partial_loop()
    add_line(point(left(middle_partial), bottom(middle_partial)), offset=middle_partial)
    add_line(point(left(terminal_partial), bottom(middle_partial)), offset=terminal_partial)
    add_line(left_bottom_intersection(middle_partial), offset=middle_partial)
    add_arc(point(seed_min_x - middle_partial, seed_min_y), (seed_min_x, seed_min_y), middle_partial)
    add_line(point(seed_min_x - middle_partial, seed_max_y), offset=middle_partial)
    add_arc(left_top_intersection(middle_partial), (seed_min_x, seed_max_y), middle_partial)
    add_line(point(left(middle_partial), top(middle_partial)), offset=middle_partial)
    add_line(point(left(middle_partial), bottom(middle_partial)), offset=middle_partial)
    add_line(point(left(terminal_partial), bottom(middle_partial)), offset=terminal_partial)
    add_line(point(left(terminal_partial), bottom(terminal_partial)), offset=terminal_partial)
    add_line(left_bottom_intersection(terminal_partial), offset=terminal_partial)
    add_arc(point(seed_min_x - terminal_partial, seed_min_y), (seed_min_x, seed_min_y), terminal_partial)
    add_line(point(seed_min_x - terminal_partial, seed_max_y), offset=terminal_partial)
    add_arc(left_top_intersection(terminal_partial), (seed_min_x, seed_max_y), terminal_partial)
    add_line(point(left(terminal_partial), top(terminal_partial)), offset=terminal_partial)
    add_line(point(left(terminal_partial), bottom(terminal_partial)), offset=terminal_partial)

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_left_repeated_partial_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_right_terminal_partial_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.bridge_offset is not None:
        return None
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.right <= family.clearance.left + 1e-6:
        return None
    if len(family.complete_offsets) != 1 or len(family.partial_offsets) != 3:
        return None

    complete_offset = float(family.complete_offsets[0])
    partial_radii = tuple(float(value) for value in family.partial_offsets)
    terminal_gap = (family.clearance.right / 2.0) - partial_radii[-1]
    if terminal_gap < -1e-6 or terminal_gap > 3.0 + 1e-6:
        return None
    radial_step = _inferred_offset_step((complete_offset, *partial_radii))
    if radial_step is None:
        return None

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = family.contour.bbox
    first_partial, middle_partial, terminal_partial = partial_radii

    owner = "single_seed_unbalanced_right_terminal_partial_offsets"
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + complete_offset, outer_max_y - complete_offset))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    def add_arc(end_point: Point2, center_point: Point2, radius: float) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_arc(owner, radius, start_point, end_point, center_point, radius))
        points.append(end_point)

    def left_intersection_y(radius: float, center_x: float, x_value: float, *, upper: bool) -> float:
        delta_x = center_x - x_value
        delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
        return (seed_min_y if not upper else seed_max_y) + (delta_y if upper else -delta_y)

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def left_top_intersection(radius: float) -> Point2:
        return point(left(radius), left_intersection_y(radius, seed_min_x, left(radius), upper=True))

    def left_bottom_intersection(radius: float) -> Point2:
        return point(left(radius), left_intersection_y(radius, seed_min_x, left(radius), upper=False))

    def right_top_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_max_y, top(radius)), top(radius))

    def right_bottom_intersection(radius: float) -> Point2:
        return point(right_intersection_x(radius, seed_min_y, bottom(radius)), bottom(radius))

    def top_right_mid(radius: float) -> Point2:
        diagonal = radius / math.sqrt(2.0)
        return point(seed_max_x + diagonal, seed_max_y + diagonal)

    add_line(point(left(complete_offset), top(first_partial)), offset=complete_offset)
    add_line(point(left(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), bottom(complete_offset)), offset=complete_offset)
    add_line(point(right(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), top(complete_offset)), offset=complete_offset)
    add_line(point(left(complete_offset), top(first_partial)), offset=first_partial)
    add_line(point(left(first_partial), top(first_partial)), offset=first_partial)
    add_line(left_top_intersection(first_partial), offset=first_partial)
    add_arc(point(seed_min_x, seed_max_y + first_partial), (seed_min_x, seed_max_y), first_partial)
    add_line(point(seed_max_x, seed_max_y + first_partial), offset=first_partial)
    add_arc(top_right_mid(first_partial), (seed_max_x, seed_max_y), first_partial)
    add_arc(point(seed_max_x + first_partial, seed_max_y), (seed_max_x, seed_max_y), first_partial)
    add_line(point(seed_max_x + first_partial, seed_min_y), offset=first_partial)
    add_arc(point(seed_max_x, seed_min_y - first_partial), (seed_max_x, seed_min_y), first_partial)
    add_line(point(seed_min_x, seed_min_y - first_partial), offset=first_partial)
    add_arc(left_bottom_intersection(first_partial), (seed_min_x, seed_min_y), first_partial)
    add_line(point(left(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), bottom(first_partial)), offset=first_partial)
    add_line(point(right(first_partial), top(first_partial)), offset=first_partial)
    add_line(point(left(first_partial), top(first_partial)), offset=first_partial)
    add_line(left_top_intersection(first_partial), offset=first_partial)

    complete_split = _radial_projection(
        (seed_min_x, seed_max_y),
        left_top_intersection(first_partial),
        first_partial,
        complete_offset,
    )
    add_line(complete_split, offset=complete_offset)
    _append_top_left_split_rounded_loop(primitives, family.contour.bbox, complete_offset, complete_split)
    points[:] = [primitives[-1].end]

    add_line(left_top_intersection(first_partial), offset=first_partial)
    add_arc(point(seed_min_x, seed_max_y + first_partial), (seed_min_x, seed_max_y), first_partial)
    add_line(point(seed_max_x, seed_max_y + first_partial), offset=first_partial)
    add_arc(top_right_mid(first_partial), (seed_max_x, seed_max_y), first_partial)
    add_arc(point(seed_max_x + first_partial, seed_max_y), (seed_max_x, seed_max_y), first_partial)

    add_line(point(seed_max_x + middle_partial, seed_max_y), offset=middle_partial)
    add_line(point(seed_max_x + middle_partial, seed_min_y), offset=middle_partial)
    add_arc(right_bottom_intersection(middle_partial), (seed_max_x, seed_min_y), middle_partial)
    add_line(point(right(middle_partial), bottom(middle_partial)), offset=middle_partial)
    add_line(point(right(middle_partial), top(middle_partial)), offset=middle_partial)
    add_line(right_top_intersection(middle_partial), offset=middle_partial)
    add_arc(point(seed_max_x + middle_partial, seed_max_y), (seed_max_x, seed_max_y), middle_partial)

    add_line(point(seed_max_x + terminal_partial, seed_max_y), offset=terminal_partial)
    add_line(point(seed_max_x + terminal_partial, seed_min_y), offset=terminal_partial)
    add_arc(right_bottom_intersection(terminal_partial), (seed_max_x, seed_min_y), terminal_partial)
    add_line(point(right(terminal_partial), bottom(terminal_partial)), offset=terminal_partial)
    add_line(point(right(terminal_partial), top(terminal_partial)), offset=terminal_partial)
    add_line(right_top_intersection(terminal_partial), offset=terminal_partial)
    add_arc(point(seed_max_x + terminal_partial, seed_max_y), (seed_max_x, seed_max_y), terminal_partial)

    return TraceResolvedSequence2D(
        name="single_seed_unbalanced_right_terminal_partial_offsets",
        primitives=tuple(primitives),
    )


def _resolved_single_seed_unbalanced_right_mirrored_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
) -> TraceResolvedSequence2D | None:
    if family.clearance is None:
        return None
    if _has_balanced_clearance(family.clearance):
        return None
    if not math.isclose(family.clearance.bottom, family.clearance.top, abs_tol=1e-6):
        return None
    if family.clearance.right <= family.clearance.left + 1e-6:
        return None

    mirrored_family = _mirror_trace_offset_family_x(family, outer_bbox)
    mirrored_outer_bbox = _mirror_bbox_x(outer_bbox, outer_bbox)
    for resolver in (
        _resolved_single_seed_unbalanced_left_early_dense_sequence,
        _resolved_single_seed_unbalanced_left_dense_partial_sequence,
        _resolved_single_seed_unbalanced_left_extended_dense_sequence,
        _resolved_single_seed_unbalanced_left_terminal_partial_sequence,
        _resolved_single_seed_unbalanced_left_repeated_partial_sequence,
        _resolved_single_seed_unbalanced_left_partial_sequence,
    ):
        resolved = resolver(mirrored_outer_bbox, mirrored_family)
        if resolved is not None:
            mirrored = _mirror_resolved_sequence_x(resolved, outer_bbox)
            return _maestroize_unbalanced_right_sequence(outer_bbox, family, mirrored)
    return None


def _maestroize_unbalanced_right_sequence(
    outer_bbox: BBox,
    family: TraceOffsetFamily,
    sequence: TraceResolvedSequence2D,
) -> TraceResolvedSequence2D:
    """Convert the geometric right mirror into Maestro's right-side traversal.

    Maestro keeps the exterior polyline start when the island is shifted to the
    left. A simple horizontal mirror produces the right geometry, but starts and
    segmentizes the trace from the opposite side.
    """

    transformed = tuple(
        _right_maestroize_corner_arcs(
            tuple(_mirror_primitive_y(primitive, outer_bbox) for primitive in sequence.primitives),
            family.contour.bbox,
        )
    )
    owner = transformed[0].owner if transformed else sequence.name

    if len(family.complete_offsets) > 1:
        prefix = _right_unbalanced_complete_prefix(outer_bbox, family.complete_offsets, owner)
        skip_count = ((len(family.complete_offsets) - 1) * 7) + 2
        primitives = prefix + transformed[skip_count:]
    elif len(family.complete_offsets) == 1 and len(family.partial_offsets) == 2:
        prefix = _right_unbalanced_single_complete_entry_prefix(
            outer_bbox,
            float(family.complete_offsets[0]),
            owner,
        )
        primitives = prefix + transformed
    elif len(family.complete_offsets) == 1 and len(family.partial_offsets) == 3:
        primitives = transformed[2:]
    else:
        primitives = transformed

    return TraceResolvedSequence2D(
        name=sequence.name,
        primitives=tuple(primitives),
    )


def _right_unbalanced_complete_prefix(
    outer_bbox: BBox,
    complete_offsets: Sequence[float],
    owner: str,
) -> tuple[TracePrimitive2D, ...]:
    if len(complete_offsets) < 2:
        return ()

    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    radii = tuple(float(value) for value in complete_offsets)
    primitives: list[TracePrimitive2D] = []
    points: list[Point2] = [_round_point((outer_min_x + radii[0], outer_max_y - radii[0]))]

    def point(x_value: float, y_value: float) -> Point2:
        return _round_point((float(x_value), float(y_value)))

    def left(radius: float) -> float:
        return outer_min_x + radius

    def right(radius: float) -> float:
        return outer_max_x - radius

    def bottom(radius: float) -> float:
        return outer_min_y + radius

    def top(radius: float) -> float:
        return outer_max_y - radius

    def add_line(end_point: Point2, *, offset: float = 0.0) -> None:
        start_point = points[-1]
        end_point = _round_point(end_point)
        if _same_xy(start_point, end_point):
            return
        primitives.append(_line(owner, offset, start_point, end_point))
        points.append(end_point)

    for index, radius in enumerate(radii[:-1]):
        next_radius = radii[index + 1]
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), bottom(radius)), offset=radius)
        add_line(point(right(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(radius)), offset=radius)
        add_line(point(left(radius), top(next_radius)), offset=radius)
        add_line(point(left(next_radius), top(next_radius)), offset=next_radius)
    return tuple(primitives)


def _right_unbalanced_single_complete_entry_prefix(
    outer_bbox: BBox,
    complete_offset: float,
    owner: str,
) -> tuple[TracePrimitive2D, ...]:
    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    offset = float(complete_offset)
    left = outer_min_x + offset
    right = outer_max_x - offset
    bottom = outer_min_y + offset
    top = outer_max_y - offset
    start = _round_point((left, top))
    middle = _round_point((left, bottom))
    end = _round_point((right, bottom))
    return (
        _line(owner, offset, start, middle),
        _line(owner, offset, middle, end),
    )


def _right_maestroize_corner_arcs(
    primitives: Sequence[TracePrimitive2D],
    seed_bbox: BBox,
) -> tuple[TracePrimitive2D, ...]:
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = seed_bbox
    result: list[TracePrimitive2D] = []
    index = 0
    while index < len(primitives):
        primitive = primitives[index]
        if (
            primitive.primitive_type == "Arc"
            and primitive.center is not None
            and primitive.radius is not None
        ):
            center = primitive.center
            radius = float(primitive.radius)
            diagonal = radius / math.sqrt(2.0)
            bottom_left_diagonal = (center[0] - diagonal, center[1] - diagonal)
            if (
                math.isclose(center[0], seed_min_x, abs_tol=1e-6)
                and math.isclose(center[1], seed_min_y, abs_tol=1e-6)
                and index + 1 < len(primitives)
            ):
                next_primitive = primitives[index + 1]
                if (
                    next_primitive.primitive_type == "Arc"
                    and next_primitive.center is not None
                    and next_primitive.radius is not None
                    and _same_xy(next_primitive.center, center)
                    and math.isclose(next_primitive.radius, radius, abs_tol=1e-6)
                    and _same_xy(primitive.end, bottom_left_diagonal)
                    and _same_xy(next_primitive.start, bottom_left_diagonal)
                ):
                    result.append(
                        TracePrimitive2D(
                            primitive_type="Arc",
                            owner=primitive.owner,
                            offset=primitive.offset,
                            start=primitive.start,
                            end=next_primitive.end,
                            center=center,
                            radius=primitive.radius,
                            orientation=primitive.orientation,
                        )
                    )
                    index += 2
                    continue

            top_right_diagonal = (center[0] + diagonal, center[1] + diagonal)
            if (
                math.isclose(center[0], seed_max_x, abs_tol=1e-6)
                and math.isclose(center[1], seed_max_y, abs_tol=1e-6)
                and primitive.start[1] > center[1] + 1e-6
                and primitive.end[0] > center[0] + 1e-6
                and primitive.end[1] <= center[1] + 1e-6
                and primitive.start[0] <= top_right_diagonal[0] + 1e-6
                and primitive.start[1] >= top_right_diagonal[1] - 1e-6
                and not _same_xy(primitive.start, top_right_diagonal)
                and not _same_xy(primitive.end, top_right_diagonal)
            ):
                diagonal_point = _round_point(top_right_diagonal)
                if math.hypot(
                    diagonal_point[0] - primitive.start[0],
                    diagonal_point[1] - primitive.start[1],
                ) <= 2.0 and not (
                    math.isclose(primitive.start[0], center[0], abs_tol=1e-6)
                    and math.isclose(primitive.start[1], center[1] + radius, abs_tol=1e-6)
                ):
                    result.append(_line(primitive.owner, primitive.offset, primitive.start, diagonal_point))
                else:
                    result.append(
                        TracePrimitive2D(
                            primitive_type="Arc",
                            owner=primitive.owner,
                            offset=primitive.offset,
                            start=primitive.start,
                            end=diagonal_point,
                            center=center,
                            radius=primitive.radius,
                            orientation=primitive.orientation,
                        )
                    )
                result.append(
                    TracePrimitive2D(
                        primitive_type="Arc",
                        owner=primitive.owner,
                        offset=primitive.offset,
                        start=diagonal_point,
                        end=primitive.end,
                        center=center,
                        radius=primitive.radius,
                        orientation=primitive.orientation,
                    )
                )
                index += 1
                continue

        result.append(primitive)
        index += 1
    return tuple(result)


def _mirror_trace_offset_family_x(
    family: TraceOffsetFamily,
    axis_bbox: BBox,
) -> TraceOffsetFamily:
    clearance = family.clearance
    return TraceOffsetFamily(
        owner=family.owner,
        contour=_mirror_trace_contour_x(family.contour, axis_bbox),
        limit=family.limit,
        offsets=family.offsets,
        complete_offsets=family.complete_offsets,
        partial_offsets=family.partial_offsets,
        bridge_offset=family.bridge_offset,
        clearance=(
            None
            if clearance is None
            else TraceClearance(
                left=clearance.right,
                right=clearance.left,
                bottom=clearance.bottom,
                top=clearance.top,
            )
        ),
    )


def _mirror_resolved_sequence_x(
    sequence: TraceResolvedSequence2D,
    axis_bbox: BBox,
) -> TraceResolvedSequence2D:
    name = sequence.name.replace("unbalanced_left", "unbalanced_right")
    if name == sequence.name:
        name = f"{sequence.name}_mirrored_right"
    return TraceResolvedSequence2D(
        name=name,
        primitives=tuple(_mirror_primitive_x(primitive, axis_bbox) for primitive in sequence.primitives),
    )


def _mirror_primitive_x(
    primitive: TracePrimitive2D,
    axis_bbox: BBox,
) -> TracePrimitive2D:
    orientation = primitive.orientation
    if primitive.primitive_type == "Arc":
        orientation = _mirror_arc_orientation(orientation)
    return TracePrimitive2D(
        primitive_type=primitive.primitive_type,
        owner=primitive.owner,
        offset=primitive.offset,
        start=_mirror_point_x(primitive.start, axis_bbox),
        end=_mirror_point_x(primitive.end, axis_bbox),
        center=(
            None
            if primitive.center is None
            else _mirror_point_x(primitive.center, axis_bbox)
        ),
        radius=primitive.radius,
        orientation=orientation,
    )


def _mirror_primitive_y(
    primitive: TracePrimitive2D,
    axis_bbox: BBox,
) -> TracePrimitive2D:
    orientation = primitive.orientation
    if primitive.primitive_type == "Arc":
        orientation = _mirror_arc_orientation(orientation)
    return TracePrimitive2D(
        primitive_type=primitive.primitive_type,
        owner=primitive.owner,
        offset=primitive.offset,
        start=_mirror_point_y(primitive.start, axis_bbox),
        end=_mirror_point_y(primitive.end, axis_bbox),
        center=(
            None
            if primitive.center is None
            else _mirror_point_y(primitive.center, axis_bbox)
        ),
        radius=primitive.radius,
        orientation=orientation,
    )


def _mirror_trace_contour_x(
    contour: TraceContour,
    axis_bbox: BBox,
) -> TraceContour:
    return _trace_contour(tuple(_mirror_point_x(point, axis_bbox) for point in contour.points))


def _mirror_bbox_x(
    bbox: BBox,
    axis_bbox: BBox,
) -> BBox:
    min_x, max_x, min_y, max_y = bbox
    mirrored_min_x = _mirror_x(max_x, axis_bbox)
    mirrored_max_x = _mirror_x(min_x, axis_bbox)
    return (
        min(mirrored_min_x, mirrored_max_x),
        max(mirrored_min_x, mirrored_max_x),
        min_y,
        max_y,
    )


def _mirror_point_x(
    point: Point2,
    axis_bbox: BBox,
) -> Point2:
    return _round_point((_mirror_x(point[0], axis_bbox), point[1]))


def _mirror_point_y(
    point: Point2,
    axis_bbox: BBox,
) -> Point2:
    return _round_point((point[0], _mirror_y(point[1], axis_bbox)))


def _mirror_x(
    x_value: float,
    axis_bbox: BBox,
) -> float:
    axis_min_x, axis_max_x, _axis_min_y, _axis_max_y = axis_bbox
    return axis_min_x + axis_max_x - float(x_value)


def _mirror_y(
    y_value: float,
    axis_bbox: BBox,
) -> float:
    _axis_min_x, _axis_max_x, axis_min_y, axis_max_y = axis_bbox
    return axis_min_y + axis_max_y - float(y_value)


def _mirror_arc_orientation(orientation: str) -> str:
    if orientation == "Clockwise":
        return "CounterClockwise"
    if orientation == "CounterClockwise":
        return "Clockwise"
    return orientation


def _append_bottom_right_split_rounded_loop(
    primitives: list[TracePrimitive2D],
    bbox: BBox,
    radius: float,
    split_point: Point2,
) -> None:
    min_x, max_x, min_y, max_y = bbox
    diagonal = radius / math.sqrt(2.0)
    p0 = (min_x - radius, min_y)
    p1 = (min_x - radius, max_y)
    p2 = (min_x, max_y + radius)
    p3 = (max_x, max_y + radius)
    p4 = (max_x + diagonal, max_y + diagonal)
    p5 = (max_x + radius, max_y)
    p6 = (max_x + radius, min_y)
    p7 = (max_x, min_y - radius)
    p8 = (min_x, min_y - radius)
    owner = "internal:1"
    _append_arc(primitives, owner, radius, p7, (max_x, min_y), radius)
    _append_line(primitives, owner, radius, p8)
    _append_arc(primitives, owner, radius, p0, (min_x, min_y), radius)
    _append_line(primitives, owner, radius, p1)
    _append_arc(primitives, owner, radius, p2, (min_x, max_y), radius)
    _append_line(primitives, owner, radius, p3)
    _append_arc(primitives, owner, radius, p4, (max_x, max_y), radius)
    _append_arc(primitives, owner, radius, p5, (max_x, max_y), radius)
    _append_line(primitives, owner, radius, p6)
    _append_arc(primitives, owner, radius, split_point, (max_x, min_y), radius)


def _append_top_left_split_rounded_loop(
    primitives: list[TracePrimitive2D],
    bbox: BBox,
    radius: float,
    split_point: Point2,
) -> None:
    min_x, max_x, min_y, max_y = bbox
    diagonal = radius / math.sqrt(2.0)
    p0 = (min_x - radius, min_y)
    p1 = (min_x - radius, max_y)
    p2 = (min_x, max_y + radius)
    p3 = (max_x, max_y + radius)
    p4 = (max_x + diagonal, max_y + diagonal)
    p5 = (max_x + radius, max_y)
    p6 = (max_x + radius, min_y)
    p7 = (max_x, min_y - radius)
    p8 = (min_x, min_y - radius)
    owner = "internal:1"
    _append_arc(primitives, owner, radius, p2, (min_x, max_y), radius)
    _append_line(primitives, owner, radius, p3)
    _append_arc(primitives, owner, radius, p4, (max_x, max_y), radius)
    _append_arc(primitives, owner, radius, p5, (max_x, max_y), radius)
    _append_line(primitives, owner, radius, p6)
    _append_arc(primitives, owner, radius, p7, (max_x, min_y), radius)
    _append_line(primitives, owner, radius, p8)
    _append_arc(primitives, owner, radius, p0, (min_x, min_y), radius)
    _append_line(primitives, owner, radius, p1)
    _append_arc(primitives, owner, radius, split_point, (min_x, max_y), radius)


def _append_bottom_left_split_rounded_loop(
    primitives: list[TracePrimitive2D],
    bbox: BBox,
    radius: float,
    split_point: Point2,
) -> None:
    min_x, max_x, min_y, max_y = bbox
    diagonal = radius / math.sqrt(2.0)
    p0 = (min_x - radius, min_y)
    p1 = (min_x - radius, max_y)
    p2 = (min_x, max_y + radius)
    p3 = (max_x, max_y + radius)
    p4 = (max_x + diagonal, max_y + diagonal)
    p5 = (max_x + radius, max_y)
    p6 = (max_x + radius, min_y)
    p7 = (max_x, min_y - radius)
    p8 = (min_x, min_y - radius)
    owner = "internal:1"
    _append_arc(primitives, owner, radius, p0, (min_x, min_y), radius)
    _append_line(primitives, owner, radius, p1)
    _append_arc(primitives, owner, radius, p2, (min_x, max_y), radius)
    _append_line(primitives, owner, radius, p3)
    _append_arc(primitives, owner, radius, p4, (max_x, max_y), radius)
    _append_arc(primitives, owner, radius, p5, (max_x, max_y), radius)
    _append_line(primitives, owner, radius, p6)
    _append_arc(primitives, owner, radius, p7, (max_x, min_y), radius)
    _append_line(primitives, owner, radius, p8)
    _append_arc(primitives, owner, radius, split_point, (min_x, min_y), radius)


def _resolved_outer_rectangle_sequence(
    bbox: BBox,
    offsets: Sequence[float],
) -> TraceResolvedSequence2D:
    min_x, max_x, min_y, max_y = bbox
    points: list[Point2] = []
    for index, offset in enumerate(offsets):
        left = min_x + offset
        right = max_x - offset
        bottom = min_y + offset
        top = max_y - offset
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else None

        if not points:
            points.append(_round_point((left, top)))
        if next_offset is not None:
            points.append(_round_point((left, max_y - next_offset)))
        points.extend(
            _round_point(point)
            for point in (
                (left, bottom),
                (right, bottom),
                (right, top),
                (left, top),
            )
        )
        if next_offset is not None:
            next_left = min_x + next_offset
            next_top = max_y - next_offset
            points.extend(
                (
                    _round_point((left, next_top)),
                    _round_point((next_left, next_top)),
                )
            )
    return TraceResolvedSequence2D(
        name="outer_complete_offsets",
        primitives=_line_primitives("outer", 0.0, points),
    )


def _resolved_rounded_rectangle_seed_sequence(
    bbox: BBox,
    offsets: Sequence[float],
) -> TraceResolvedSequence2D:
    primitives: list[TracePrimitive2D] = []
    previous_end: Point2 | None = None
    for offset in offsets:
        loop = _rounded_rectangle_offset_sequence(owner="internal:1", bbox=bbox, offset=offset)
        if loop is None:
            continue
        loop_start = loop.primitives[0].start
        if previous_end is not None and not _same_xy(previous_end, loop_start):
            primitives.append(_line("internal:1", offset, previous_end, loop_start))
        primitives.extend(loop.primitives)
        previous_end = loop.primitives[-1].end
    return TraceResolvedSequence2D(
        name="internal_complete_offsets",
        primitives=tuple(primitives),
    )


def _trajectory_sequences(
    resolved_sequences: Sequence[TraceResolvedSequence2D],
    depth_plan: TraceDepthPlan,
) -> tuple[tuple[Point3, ...], ...]:
    if not resolved_sequences:
        return ()
    sequences: list[tuple[Point3, ...]] = []
    for z_value in depth_plan.z_values:
        for sequence in resolved_sequences:
            points = _sequence_points_3d(sequence, z_value)
            if points:
                sequences.append(points)
    return tuple(sequences)


def _sequence_points_3d(
    sequence: TraceResolvedSequence2D,
    z_value: float,
) -> tuple[Point3, ...]:
    if not sequence.primitives:
        return ()
    points: list[Point3] = [_point3(sequence.primitives[0].start, z_value)]
    for primitive in sequence.primitives:
        points.append(_point3(primitive.end, z_value))
    return tuple(points)


def _outer_sequence_offsets(
    outer_family: TraceOffsetFamily,
    internal_families: Sequence[TraceOffsetFamily],
) -> tuple[float, ...]:
    if not internal_families:
        return outer_family.offsets
    limits = tuple(
        family.clearance.minimum_half
        for family in internal_families
        if family.clearance is not None
    )
    if not limits:
        return outer_family.offsets
    limit = min(limits)
    return tuple(offset for offset in outer_family.offsets if offset <= limit + 1e-6)


def _ordered_offsets(offsets: Sequence[float], parameters: TraceParameters) -> tuple[float, ...]:
    normalized = tuple(float(offset) for offset in offsets)
    if parameters.inside_to_outside:
        return tuple(reversed(normalized))
    return normalized


def _rectangle_offset_sequence(
    *,
    owner: str,
    bbox: BBox,
    offset: float,
    rotation_direction: str,
    outward: bool,
) -> TracePrimitiveSequence2D | None:
    min_x, max_x, min_y, max_y = bbox
    sign = -1.0 if outward else 1.0
    left = min_x + (sign * offset)
    right = max_x - (sign * offset)
    bottom = min_y + (sign * offset)
    top = max_y - (sign * offset)
    if left > right + 1e-6 or bottom > top + 1e-6:
        return None

    if rotation_direction == "Clockwise":
        points = ((left, bottom), (left, top), (right, top), (right, bottom), (left, bottom))
    else:
        points = ((left, bottom), (right, bottom), (right, top), (left, top), (left, bottom))
    return TracePrimitiveSequence2D(
        owner=owner,
        offset=round(float(offset), 10),
        primitives=_line_primitives(owner, offset, points),
    )


def _rounded_rectangle_offset_sequence(
    *,
    owner: str,
    bbox: BBox,
    offset: float,
) -> TracePrimitiveSequence2D | None:
    min_x, max_x, min_y, max_y = bbox
    if offset <= 0.0:
        return None
    diagonal = offset / math.sqrt(2.0)
    p0 = (min_x - offset, min_y)
    p1 = (min_x - offset, max_y)
    p2 = (min_x, max_y + offset)
    p3 = (max_x, max_y + offset)
    p4 = (max_x + diagonal, max_y + diagonal)
    p5 = (max_x + offset, max_y)
    p6 = (max_x + offset, min_y)
    p7 = (max_x, min_y - offset)
    p8 = (min_x, min_y - offset)
    primitives = (
        _line(owner, offset, p0, p1),
        _arc(owner, offset, p1, p2, (min_x, max_y), offset),
        _line(owner, offset, p2, p3),
        _arc(owner, offset, p3, p4, (max_x, max_y), offset),
        _arc(owner, offset, p4, p5, (max_x, max_y), offset),
        _line(owner, offset, p5, p6),
        _arc(owner, offset, p6, p7, (max_x, min_y), offset),
        _line(owner, offset, p7, p8),
        _arc(owner, offset, p8, p0, (min_x, min_y), offset),
    )
    return TracePrimitiveSequence2D(
        owner=owner,
        offset=round(float(offset), 10),
        primitives=primitives,
    )


def _line_primitives(
    owner: str,
    offset: float,
    points: Sequence[Point2],
) -> tuple[TracePrimitive2D, ...]:
    primitives: list[TracePrimitive2D] = []
    for start, end in zip(points, points[1:]):
        if _same_xy(start, end):
            continue
        primitives.append(_line(owner, offset, start, end))
    return tuple(primitives)


def _append_line(
    primitives: list[TracePrimitive2D],
    owner: str,
    offset: float,
    end: Point2,
) -> None:
    if not primitives:
        raise ValueError("Cannot append a connected line without a start primitive.")
    start = primitives[-1].end
    if _same_xy(start, end):
        return
    primitives.append(_line(owner, offset, start, end))


def _append_arc(
    primitives: list[TracePrimitive2D],
    owner: str,
    offset: float,
    end: Point2,
    center: Point2,
    radius: float,
) -> None:
    if not primitives:
        raise ValueError("Cannot append a connected arc without a start primitive.")
    start = primitives[-1].end
    if _same_xy(start, end):
        return
    primitives.append(_arc(owner, offset, start, end, center, radius))


def _line(owner: str, offset: float, start: Point2, end: Point2) -> TracePrimitive2D:
    return TracePrimitive2D(
        primitive_type="Line",
        owner=owner,
        offset=round(float(offset), 10),
        start=_round_point(start),
        end=_round_point(end),
    )


def _arc(
    owner: str,
    offset: float,
    start: Point2,
    end: Point2,
    center: Point2,
    radius: float,
) -> TracePrimitive2D:
    return TracePrimitive2D(
        primitive_type="Arc",
        owner=owner,
        offset=round(float(offset), 10),
        start=_round_point(start),
        end=_round_point(end),
        center=_round_point(center),
        radius=round(float(radius), 10),
        orientation="Clockwise",
    )


def _cut_depth_levels(
    *,
    target_depth: float,
    allow_multiple_passes: bool,
    axial_cutting_depth: float,
    axial_finish_cutting_depth: float,
) -> tuple[float, ...]:
    target = float(target_depth)
    step = float(axial_cutting_depth)
    finish = float(axial_finish_cutting_depth)
    if not allow_multiple_passes or step <= 0.0 or target <= max(finish, step):
        return (round(target, 10),)

    rough_limit = target - max(finish, 0.0)
    levels: list[float] = []
    current = step
    while current <= rough_limit + 1e-6:
        levels.append(round(current, 10))
        current += step
    if not levels:
        levels.append(round(min(step, target), 10))
    if not math.isclose(levels[-1], target, abs_tol=1e-6):
        levels.append(round(target, 10))
    return tuple(levels)


def _trace_contour(points: Sequence[Point2]) -> TraceContour:
    normalized = _normalize_contour_points(points)
    return TraceContour(
        points=normalized,
        start_point=normalized[0],
        bbox=_bbox(normalized),
        winding=_winding(normalized),
        is_axis_aligned_rectangle=_is_axis_aligned_rectangle(normalized),
    )


def _normalize_contour_points(points: Sequence[Point2]) -> tuple[Point2, ...]:
    normalized = tuple((float(x), float(y)) for x, y in points)
    if len(normalized) < 3:
        raise ValueError("A closed Vaciado contour requires at least 3 points.")
    if _same_xy(normalized[0], normalized[-1]):
        normalized = normalized[:-1]
    if len(normalized) < 3:
        raise ValueError("A closed Vaciado contour requires at least 3 unique points.")
    return normalized


def _bbox(points: Sequence[Point2]) -> BBox:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), max(xs), min(ys), max(ys))


def _clearance_between(outer_bbox: BBox, inner_bbox: BBox) -> TraceClearance:
    outer_min_x, outer_max_x, outer_min_y, outer_max_y = outer_bbox
    inner_min_x, inner_max_x, inner_min_y, inner_max_y = inner_bbox
    return TraceClearance(
        left=inner_min_x - outer_min_x,
        right=outer_max_x - inner_max_x,
        bottom=inner_min_y - outer_min_y,
        top=outer_max_y - inner_max_y,
    )


def _winding(points: Sequence[Point2]) -> str:
    signed_area = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        signed_area += (x0 * y1) - (x1 * y0)
    if math.isclose(signed_area, 0.0, abs_tol=1e-9):
        return "Degenerate"
    return "CounterClockwise" if signed_area > 0.0 else "Clockwise"


def _is_axis_aligned_rectangle(points: Sequence[Point2]) -> bool:
    if len(points) != 4:
        return False
    for start, end in zip(points, points[1:] + points[:1]):
        if not (
            math.isclose(start[0], end[0], abs_tol=1e-6)
            or math.isclose(start[1], end[1], abs_tol=1e-6)
        ):
            return False
    return True


def _pending_stages(
    spec: sp.PocketMillingSpec,
    outer: TraceContour,
    internal_contours: Sequence[TraceInternalContour],
    resolved_sequences: Sequence[TraceResolvedSequence2D],
) -> tuple[str, ...]:
    pending: list[str] = []
    if not resolved_sequences:
        pending.extend(
            [
                "topology_resolver",
                "traversal_orderer",
                "connector_planner",
                "toolpath_emitter",
            ]
        )
    if not outer.is_axis_aligned_rectangle:
        pending.insert(1, "non_rectangular_outer_contour")
    if len(internal_contours) > 1:
        pending.insert(2, "multi_internal_contour_topology")
    if spec.milling_strategy.is_helic_strategy:
        pending.append("helical_interpolator")
    return tuple(pending)


def _same_xy(first: Point2, second: Point2, *, tolerance: float = 1e-6) -> bool:
    return math.isclose(first[0], second[0], abs_tol=tolerance) and math.isclose(
        first[1],
        second[1],
        abs_tol=tolerance,
    )


def _has_balanced_clearance(clearance: TraceClearance) -> bool:
    return math.isclose(clearance.left, clearance.right, abs_tol=1e-6) and math.isclose(
        clearance.bottom,
        clearance.top,
        abs_tol=1e-6,
    )


def _inferred_offset_step(offsets: Sequence[float]) -> float | None:
    normalized = tuple(float(offset) for offset in offsets)
    if len(normalized) < 2:
        return None
    deltas = [
        round(normalized[index + 1] - normalized[index], 10)
        for index in range(len(normalized) - 1)
        if normalized[index + 1] > normalized[index] + 1e-6
    ]
    if not deltas:
        return None
    step = deltas[0]
    if step <= 0.0:
        return None
    if any(not math.isclose(delta, step, abs_tol=1e-6) for delta in deltas):
        return None
    return step


def _dense_bridge_extra_radii(
    outer_bbox: BBox,
    seed_bbox: BBox,
    bridge_radius: float,
    radial_step: float,
) -> tuple[float, ...]:
    outer_min_x, _outer_max_x, outer_min_y, _outer_max_y = outer_bbox
    seed_min_x, _seed_max_x, seed_min_y, _seed_max_y = seed_bbox
    radii: list[float] = []
    radius = bridge_radius + radial_step
    while True:
        bottom_y = outer_min_y + radius
        left_boundary = outer_min_x + radius
        delta_y = seed_min_y - bottom_y
        if abs(delta_y) > radius + 1e-6:
            break
        intersection_x = seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))
        if intersection_x < left_boundary - 1e-6:
            break
        radii.append(round(radius, 10))
        radius += radial_step
    return tuple(radii)


def _round_point(point: Point2) -> Point2:
    return (round(float(point[0]), 10), round(float(point[1]), 10))


def _point3(point: Point2, z_value: float) -> Point3:
    return (round(float(point[0]), 10), round(float(point[1]), 10), round(float(z_value), 10))


def _inset_bbox(bbox: BBox, offset: float) -> BBox:
    min_x, max_x, min_y, max_y = bbox
    return (
        round(float(min_x + offset), 10),
        round(float(max_x - offset), 10),
        round(float(min_y + offset), 10),
        round(float(max_y - offset), 10),
    )


def _circle_x_intersection_y(
    center: Point2,
    radius: float,
    x_value: float,
    *,
    upper: bool,
) -> Point2:
    delta_x = float(x_value) - center[0]
    delta_y = math.sqrt(max(0.0, (radius * radius) - (delta_x * delta_x)))
    y_value = center[1] + delta_y if upper else center[1] - delta_y
    return _round_point((x_value, y_value))


def _circle_y_intersection_x(
    center: Point2,
    radius: float,
    y_value: float,
    *,
    left_side: bool,
) -> Point2:
    delta_y = float(y_value) - center[1]
    delta_x = math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))
    x_value = center[0] - delta_x if left_side else center[0] + delta_x
    return _round_point((x_value, y_value))


def _radial_projection(
    center: Point2,
    source: Point2,
    source_radius: float,
    target_radius: float,
) -> Point2:
    if source_radius <= 0.0:
        raise ValueError("source_radius must be positive.")
    scale = float(target_radius) / float(source_radius)
    return _round_point(
        (
            center[0] + ((source[0] - center[0]) * scale),
            center[1] + ((source[1] - center[1]) * scale),
        )
    )
