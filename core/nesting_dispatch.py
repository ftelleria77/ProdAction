"""Packer dispatch for cut nesting."""

from __future__ import annotations

from core.nesting_brkga import pack_group_into_boards_guillotine_brkga_tail
from core.nesting_free_rectangles import pack_group_into_boards_free_rectangles
from core.nesting_guillotine import (
    pack_group_into_boards_guillotine,
    pack_group_into_boards_guillotine_dimension_scan,
)
from core.nesting_model import (
    CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL,
    CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
    CUT_GUILLOTINE_ALGORITHM_PREFERRED,
    CUT_OPTIMIZATION_NONE,
    CutBoard,
    CutPiece,
)
from core.nesting_strategy import normalize_guillotine_algorithm, uses_guillotine_mode


def pack_group_into_boards(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str = "",
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
    guillotine_algorithm: str = CUT_GUILLOTINE_ALGORITHM_PREFERRED,
) -> tuple[list[CutBoard], list[CutPiece]]:
    if uses_guillotine_mode(optimization_mode):
        resolved_algorithm = normalize_guillotine_algorithm(guillotine_algorithm)
        if resolved_algorithm == CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL:
            return pack_group_into_boards_guillotine_brkga_tail(
                material,
                thickness,
                pieces,
                board_width,
                board_height,
                piece_spacing,
                section_kerf,
                grain=grain,
                optimization_mode=optimization_mode,
            )
        if resolved_algorithm == CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN:
            return pack_group_into_boards_guillotine_dimension_scan(
                material,
                thickness,
                pieces,
                board_width,
                board_height,
                piece_spacing,
                section_kerf,
                grain=grain,
                optimization_mode=optimization_mode,
            )
        return pack_group_into_boards_guillotine(
            material,
            thickness,
            pieces,
            board_width,
            board_height,
            piece_spacing,
            section_kerf,
            grain=grain,
            optimization_mode=optimization_mode,
        )

    return pack_group_into_boards_free_rectangles(
        material,
        thickness,
        pieces,
        board_width,
        board_height,
        piece_spacing,
        grain=grain,
        optimization_mode=optimization_mode,
    )


__all__ = ["pack_group_into_boards"]
