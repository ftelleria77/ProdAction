"""Rectangle geometry helpers shared by cut nesting packers."""

from __future__ import annotations


Rect = tuple[float, float, float, float]


def rectangles_intersect(first: Rect, second: Rect) -> bool:
    first_x, first_y, first_w, first_h = first
    second_x, second_y, second_w, second_h = second
    return not (
        second_x >= first_x + first_w
        or second_x + second_w <= first_x
        or second_y >= first_y + first_h
        or second_y + second_h <= first_y
    )


def split_free_rectangle(
    free_rect: Rect,
    used_rect: Rect,
) -> list[Rect]:
    free_x, free_y, free_w, free_h = free_rect
    used_x, used_y, used_w, used_h = used_rect
    results: list[Rect] = []

    if used_x > free_x:
        results.append((free_x, free_y, used_x - free_x, free_h))
    if used_x + used_w < free_x + free_w:
        results.append((used_x + used_w, free_y, free_x + free_w - (used_x + used_w), free_h))
    if used_y > free_y:
        results.append((free_x, free_y, free_w, used_y - free_y))
    if used_y + used_h < free_y + free_h:
        results.append((free_x, used_y + used_h, free_w, free_y + free_h - (used_y + used_h)))

    return [rect for rect in results if rect[2] > 0.01 and rect[3] > 0.01]


def prune_free_rectangles(rectangles: list[Rect]) -> list[Rect]:
    pruned: list[Rect] = []
    for idx, rect in enumerate(rectangles):
        x, y, width, height = rect
        contained = False
        for other_idx, other in enumerate(rectangles):
            if idx == other_idx:
                continue
            other_x, other_y, other_width, other_height = other
            if (
                x >= other_x
                and y >= other_y
                and x + width <= other_x + other_width
                and y + height <= other_y + other_height
            ):
                contained = True
                break
        if not contained:
            pruned.append(rect)
    return pruned


def occupied_span(size: float, free_size: float, spacing: float) -> float:
    if free_size - size <= 0.01:
        return size
    return size + spacing


__all__ = [
    "Rect",
    "occupied_span",
    "prune_free_rectangles",
    "rectangles_intersect",
    "split_free_rectangle",
]
