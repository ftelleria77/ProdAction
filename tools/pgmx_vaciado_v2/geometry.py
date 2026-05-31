from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

Point2 = tuple[float, float]


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


def _same_point(first: Point2, second: Point2) -> bool:
    return math.isclose(first[0], second[0], abs_tol=1e-6) and math.isclose(
        first[1],
        second[1],
        abs_tol=1e-6,
    )


def _contains_point(points: Sequence[Point2], expected: Point2) -> bool:
    return any(_same_point(point, expected) for point in points)
