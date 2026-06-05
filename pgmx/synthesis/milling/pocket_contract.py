"""Pocket milling contract helpers promoted from the historical Vaciado V2 model."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Sequence

from ..common.strategy import ContourParallelMillingStrategySpec

if TYPE_CHECKING:
    from .pocket import PocketMillingSpec

Point2 = tuple[float, float]

__all__ = [
    "BBox",
    "OffsetFamily",
    "Point2",
    "PolylineContour",
    "RectangularNoIslandTracePlan",
    "TracePrimitive2D",
    "TracePrimitiveSequence2D",
    "VaciadoDepth",
    "VaciadoGeometry",
    "VaciadoStrategy",
    "from_pocket_milling_spec",
    "plan_rectangular_no_islands",
    "rectangular_loop_sequence",
]


@dataclass(frozen=True)
class BBox:
    left: float
    right: float
    bottom: float
    top: float

    @classmethod
    def from_points(cls, points: Sequence[Point2]) -> BBox:
        if not points:
            raise ValueError("BBox requires at least one point.")
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return cls(min(xs), max(xs), min(ys), max(ys))

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def minimum_half_span(self) -> float:
        return min(self.width, self.height) / 2.0

    def inset(self, offset: float) -> BBox:
        value = float(offset)
        return BBox(
            self.left + value,
            self.right - value,
            self.bottom + value,
            self.top - value,
        )


@dataclass(frozen=True)
class PolylineContour:
    points: tuple[Point2, ...]

    def __post_init__(self) -> None:
        if len(self.points) < 4:
            raise ValueError("A closed polyline contour requires at least 4 points.")
        if not _same_point(self.points[0], self.points[-1]):
            raise ValueError("A closed polyline contour must repeat its first point at the end.")

    @property
    def bbox(self) -> BBox:
        return BBox.from_points(self.points[:-1])

    @property
    def start(self) -> Point2:
        return self.points[0]

    @property
    def is_axis_aligned_rectangle(self) -> bool:
        unique = self.points[:-1]
        if len(unique) < 4:
            return False
        bbox = self.bbox
        corners = {
            (bbox.left, bbox.bottom),
            (bbox.right, bbox.bottom),
            (bbox.right, bbox.top),
            (bbox.left, bbox.top),
        }
        if any(not _contains_point(unique, corner) for corner in corners):
            return False
        for x_value, y_value in unique:
            on_vertical_edge = math.isclose(x_value, bbox.left, abs_tol=1e-6) or math.isclose(
                x_value,
                bbox.right,
                abs_tol=1e-6,
            )
            on_horizontal_edge = math.isclose(y_value, bbox.bottom, abs_tol=1e-6) or math.isclose(
                y_value,
                bbox.top,
                abs_tol=1e-6,
            )
            if not (on_vertical_edge or on_horizontal_edge):
                return False
        return all(
            math.isclose(a[0], b[0], abs_tol=1e-6)
            or math.isclose(a[1], b[1], abs_tol=1e-6)
            for a, b in zip(self.points, self.points[1:])
        )


@dataclass(frozen=True)
class VaciadoGeometry:
    outer: PolylineContour
    physical_islands: tuple[PolylineContour, ...] = ()
    route_seeds: tuple[PolylineContour, ...] = ()

    @property
    def has_internal_geometry(self) -> bool:
        return bool(self.physical_islands or self.route_seeds)


@dataclass(frozen=True)
class VaciadoStrategy:
    tool_width: float
    overlap: float = 0.5
    allowance_side: float = 0.0
    rotation_direction: str = "CounterClockwise"
    inside_to_outside: bool = True
    stroke_connection_strategy: str = "LiftShiftPlunge"
    is_helic_strategy: bool = False

    def __post_init__(self) -> None:
        if self.tool_width <= 0.0:
            raise ValueError("tool_width must be positive.")
        if not 0.0 <= self.overlap < 1.0:
            raise ValueError("overlap must be in the range [0, 1).")
        if self.effective_offset < -1e-9:
            raise ValueError("tool radius + allowance_side must not be negative.")
        if self.rotation_direction not in {"Clockwise", "CounterClockwise"}:
            raise ValueError("rotation_direction must be Clockwise or CounterClockwise.")
        if self.stroke_connection_strategy not in {"LiftShiftPlunge", "Straghtline"}:
            raise ValueError("unsupported stroke_connection_strategy.")

    @property
    def tool_radius(self) -> float:
        return self.tool_width / 2.0

    @property
    def effective_offset(self) -> float:
        return self.tool_radius + self.allowance_side

    @property
    def radial_step(self) -> float:
        return self.tool_width * (1.0 - self.overlap)


@dataclass(frozen=True)
class VaciadoDepth:
    target_depth: float
    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0

    def __post_init__(self) -> None:
        if self.target_depth <= 0.0:
            raise ValueError("target_depth must be positive.")
        if self.axial_cutting_depth < 0.0:
            raise ValueError("axial_cutting_depth must not be negative.")
        if self.axial_finish_cutting_depth < 0.0:
            raise ValueError("axial_finish_cutting_depth must not be negative.")


@dataclass(frozen=True)
class TracePrimitive2D:
    primitive_type: str
    start: Point2
    end: Point2
    center: Point2 | None = None
    radius: float | None = None
    orientation: str | None = None


@dataclass(frozen=True)
class TracePrimitiveSequence2D:
    owner: str
    offset: float
    primitives: tuple[TracePrimitive2D, ...]

    @property
    def start(self) -> Point2 | None:
        return self.primitives[0].start if self.primitives else None

    @property
    def end(self) -> Point2 | None:
        return self.primitives[-1].end if self.primitives else None

    @property
    def line_count(self) -> int:
        return sum(1 for primitive in self.primitives if primitive.primitive_type == "Line")

    @property
    def arc_count(self) -> int:
        return sum(1 for primitive in self.primitives if primitive.primitive_type == "Arc")


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


def from_pocket_milling_spec(
    spec: PocketMillingSpec,
) -> tuple[VaciadoGeometry, VaciadoStrategy, VaciadoDepth]:
    strategy_spec = spec.milling_strategy
    if not isinstance(strategy_spec, ContourParallelMillingStrategySpec):
        raise TypeError("Pocket milling contract requires ContourParallelMillingStrategySpec.")
    target_depth = spec.depth_spec.target_depth
    if target_depth is None:
        raise ValueError("Pocket milling contract requires an explicit target depth.")

    geometry = VaciadoGeometry(
        outer=_contour(spec.contour_points),
        physical_islands=tuple(_contour(points) for points in spec.boss_contours),
        route_seeds=tuple(_contour(points) for points in spec.resolved_boss_route_seed_contours),
    )
    strategy = VaciadoStrategy(
        tool_width=float(spec.tool_width),
        overlap=float(strategy_spec.overlap),
        allowance_side=float(spec.allowance_side),
        rotation_direction=strategy_spec.rotation_direction,
        inside_to_outside=bool(strategy_spec.inside_to_outside),
        stroke_connection_strategy=strategy_spec.stroke_connection_strategy,
        is_helic_strategy=bool(strategy_spec.is_helic_strategy),
    )
    depth = VaciadoDepth(
        target_depth=float(target_depth),
        allow_multiple_passes=bool(strategy_spec.allow_multiple_passes),
        axial_cutting_depth=float(strategy_spec.axial_cutting_depth),
        axial_finish_cutting_depth=float(strategy_spec.axial_finish_cutting_depth),
    )
    return geometry, strategy, depth


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


def rectangular_loop_sequence(
    *,
    owner: str,
    offset: float,
    bbox: BBox,
    rotation_direction: str,
) -> TracePrimitiveSequence2D:
    if rotation_direction == "Clockwise":
        points = (
            (bbox.left, bbox.bottom),
            (bbox.left, bbox.top),
            (bbox.right, bbox.top),
            (bbox.right, bbox.bottom),
            (bbox.left, bbox.bottom),
        )
    elif rotation_direction == "CounterClockwise":
        points = (
            (bbox.left, bbox.bottom),
            (bbox.right, bbox.bottom),
            (bbox.right, bbox.top),
            (bbox.left, bbox.top),
            (bbox.left, bbox.bottom),
        )
    else:
        raise ValueError("rotation_direction must be Clockwise or CounterClockwise.")
    return TracePrimitiveSequence2D(
        owner=owner,
        offset=round(float(offset), 10),
        primitives=tuple(
            TracePrimitive2D(
                primitive_type="Line",
                start=start,
                end=end,
                orientation=rotation_direction,
            )
            for start, end in zip(points, points[1:])
        ),
    )


def _contour(points: tuple[tuple[float, float], ...]) -> PolylineContour:
    return PolylineContour(tuple((float(x), float(y)) for x, y in points))


def _offset_series(*, first_offset: float, radial_step: float, limit: float) -> tuple[float, ...]:
    if radial_step <= 0.0:
        raise ValueError("radial_step must be positive.")
    offsets: list[float] = []
    current = first_offset
    while current <= limit + 1e-6:
        offsets.append(round(current, 10))
        current += radial_step
    return tuple(offsets)


def _same_point(first: Point2, second: Point2) -> bool:
    return math.isclose(first[0], second[0], abs_tol=1e-6) and math.isclose(
        first[1],
        second[1],
        abs_tol=1e-6,
    )


def _contains_point(points: Sequence[Point2], expected: Point2) -> bool:
    return any(_same_point(point, expected) for point in points)
