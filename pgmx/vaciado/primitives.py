from __future__ import annotations

from dataclasses import dataclass

from .geometry import BBox, Point2


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
