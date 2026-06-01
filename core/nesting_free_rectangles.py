"""Free-rectangle packer for cut nesting."""

from __future__ import annotations

from core.nesting_geometry import (
    Rect,
    occupied_span,
    prune_free_rectangles,
    rectangles_intersect,
    split_free_rectangle,
)
from core.nesting_model import (
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_NONE,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutBoard,
    CutPiece,
    CutPlacement,
)
from core.nesting_strategy import normalize_optimization_mode, orientation_options


PlacementScore = tuple[float, float, float, float]
PlacementCandidate = tuple[int, float, float, bool, Rect, Rect, PlacementScore]


def placement_score(
    free_rect: Rect,
    occupied_width: float,
    occupied_height: float,
    optimization_mode: str,
) -> PlacementScore:
    _, _, free_width, free_height = free_rect
    waste_area = free_width * free_height - occupied_width * occupied_height
    short_side = min(free_width - occupied_width, free_height - occupied_height)
    long_side = max(free_width - occupied_width, free_height - occupied_height)
    if optimization_mode == CUT_OPTIMIZATION_LONGITUDINAL:
        axis_fit = free_height - occupied_height
    elif optimization_mode == CUT_OPTIMIZATION_TRANSVERSAL:
        axis_fit = free_width - occupied_width
    else:
        axis_fit = min(free_width - occupied_width, free_height - occupied_height)
    return (round(waste_area, 4), round(axis_fit, 4), round(short_side, 4), round(long_side, 4))


def pack_group_into_boards_free_rectangles(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    grain: str = "",
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
) -> tuple[list[CutBoard], list[CutPiece]]:
    remaining = list(pieces)
    boards: list[CutBoard] = []
    skipped: list[CutPiece] = []
    board_index = 1
    optimization_mode = normalize_optimization_mode(optimization_mode)

    while remaining:
        placements: list[CutPlacement] = []
        used_area = 0.0
        free_rectangles: list[Rect] = [(0.0, 0.0, float(board_width), float(board_height))]

        while True:
            found: PlacementCandidate | None = None
            for idx, cut_piece in enumerate(remaining):
                for width, height, rotated in orientation_options(cut_piece, optimization_mode, grain):
                    for free_rect in free_rectangles:
                        _, _, free_width, free_height = free_rect
                        occupied_width = occupied_span(width, free_width, piece_spacing)
                        occupied_height = occupied_span(height, free_height, piece_spacing)
                        if occupied_width > free_width or occupied_height > free_height:
                            continue
                        score = placement_score(free_rect, occupied_width, occupied_height, optimization_mode)
                        candidate = (
                            idx,
                            width,
                            height,
                            rotated,
                            free_rect,
                            (free_rect[0], free_rect[1], occupied_width, occupied_height),
                            score,
                        )
                        if found is None or candidate[-1] < found[-1]:
                            found = candidate

            if found is not None:
                idx, width, height, rotated, free_rect, used_rect, _ = found
                cut_piece = remaining.pop(idx)
                placements.append(
                    CutPlacement(
                        cut_piece=cut_piece,
                        x=free_rect[0],
                        y=free_rect[1],
                        width=width,
                        height=height,
                        rotated=rotated,
                    )
                )
                used_area += cut_piece.width * cut_piece.height

                updated_rectangles: list[Rect] = []
                for free_rect_candidate in free_rectangles:
                    if not rectangles_intersect(free_rect_candidate, used_rect):
                        updated_rectangles.append(free_rect_candidate)
                        continue
                    updated_rectangles.extend(split_free_rectangle(free_rect_candidate, used_rect))
                free_rectangles = prune_free_rectangles(updated_rectangles)
                continue

            break

        if not placements:
            skipped.extend(remaining)
            break

        boards.append(
            CutBoard(
                material=material,
                thickness=thickness,
                board_width=board_width,
                board_height=board_height,
                board_margin=0.0,
                grain=grain,
                index=board_index,
                placements=placements,
                utilization=used_area / float(board_width * board_height),
            )
        )
        board_index += 1

    return boards, skipped


__all__ = [
    "PlacementCandidate",
    "PlacementScore",
    "pack_group_into_boards_free_rectangles",
    "placement_score",
]
