"""Ordering and strategy helpers for cut nesting algorithms."""

from __future__ import annotations

from core.nesting_model import (
    BOARD_GRAIN_LENGTH,
    BOARD_GRAIN_NONE,
    BOARD_GRAIN_WIDTH,
    CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL,
    CUT_GUILLOTINE_ALGORITHM_CURRENT,
    CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_NONE,
    CUT_OPTIMIZATION_TRANSVERSAL,
    PIECE_GRAIN_HEIGHT_AXIS,
    PIECE_GRAIN_NONE,
    PIECE_GRAIN_WIDTH_AXIS,
    CutPiece,
)


def normalize_board_grain_axis(value) -> str:
    raw = str(value or '').strip().lower()
    if not raw or raw in {'0', '0 - sin veta', 'sin veta', 'no veta'}:
        return BOARD_GRAIN_NONE
    if raw in {'1', '1 - longitudinal', 'longitudinal'}:
        return BOARD_GRAIN_LENGTH
    if raw in {'2', '2 - transversal', 'transversal'}:
        return BOARD_GRAIN_WIDTH
    if 'sin veta' in raw or 'no veta' in raw:
        return BOARD_GRAIN_NONE
    if 'longitudinal' in raw:
        return BOARD_GRAIN_LENGTH
    if 'transversal' in raw:
        return BOARD_GRAIN_WIDTH
    return BOARD_GRAIN_NONE


def normalize_optimization_mode(value) -> str:
    raw = str(value or '').strip().lower()
    if raw in {CUT_OPTIMIZATION_LONGITUDINAL, 'optimización longitudinal', 'optimizacion longitudinal'}:
        return CUT_OPTIMIZATION_LONGITUDINAL
    if raw in {CUT_OPTIMIZATION_TRANSVERSAL, 'optimización transversal', 'optimizacion transversal'}:
        return CUT_OPTIMIZATION_TRANSVERSAL
    return CUT_OPTIMIZATION_NONE


def normalize_guillotine_algorithm(value) -> str:
    raw = str(value or '').strip().lower()
    if raw in {CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL, 'brkga_tail', 'genetic-tail', 'genetico'}:
        return CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL
    if raw in {CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN, 'dimension_scan', 'scan', 'escaneo-dimensiones'}:
        return CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN
    return CUT_GUILLOTINE_ALGORITHM_CURRENT


def orientation_options(
    cut_piece: CutPiece,
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
    board_grain: str = '',
) -> list[tuple[float, float, bool]]:
    options = [(cut_piece.width, cut_piece.height, False)]
    if cut_piece.allow_rotate and abs(cut_piece.width - cut_piece.height) > 0.01:
        options.append((cut_piece.height, cut_piece.width, True))

    optimization_mode = normalize_optimization_mode(optimization_mode)
    board_grain_axis = normalize_board_grain_axis(board_grain)

    if cut_piece.grain_mode != PIECE_GRAIN_NONE and board_grain_axis != BOARD_GRAIN_NONE:
        filtered_options: list[tuple[float, float, bool]] = []
        for width, height, rotated in options:
            if cut_piece.grain_mode == PIECE_GRAIN_HEIGHT_AXIS:
                aligned = (not rotated) if board_grain_axis == BOARD_GRAIN_LENGTH else rotated
            elif cut_piece.grain_mode == PIECE_GRAIN_WIDTH_AXIS:
                aligned = rotated if board_grain_axis == BOARD_GRAIN_LENGTH else (not rotated)
            else:
                aligned = not rotated
            if aligned:
                filtered_options.append((width, height, rotated))
        if filtered_options:
            options = filtered_options

    if optimization_mode == CUT_OPTIMIZATION_LONGITUDINAL:
        return sorted(options, key=lambda item: (-item[1], item[0], item[2]))
    if optimization_mode == CUT_OPTIMIZATION_TRANSVERSAL:
        return sorted(options, key=lambda item: (-item[0], item[1], item[2]))
    return sorted(options, key=lambda item: (item[2], -max(item[0], item[1]), -min(item[0], item[1])))


def order_group_pieces(pieces: list[CutPiece], optimization_mode: str, board_grain: str = '') -> list[CutPiece]:
    optimization_mode = normalize_optimization_mode(optimization_mode)

    def sort_key(cut_piece: CutPiece):
        preferred_width, preferred_height, _ = orientation_options(cut_piece, optimization_mode, board_grain)[0]
        if optimization_mode == CUT_OPTIMIZATION_LONGITUDINAL:
            primary = preferred_height
            secondary = preferred_width
        elif optimization_mode == CUT_OPTIMIZATION_TRANSVERSAL:
            primary = preferred_width
            secondary = preferred_height
        else:
            primary = preferred_width * preferred_height
            secondary = max(preferred_width, preferred_height)
        return (
            primary,
            secondary,
            preferred_width * preferred_height,
        )

    return sorted(pieces, key=sort_key, reverse=True)


def uses_guillotine_mode(optimization_mode: str) -> bool:
    normalized = normalize_optimization_mode(optimization_mode)
    return normalized in {CUT_OPTIMIZATION_LONGITUDINAL, CUT_OPTIMIZATION_TRANSVERSAL}


__all__ = [
    "normalize_board_grain_axis",
    "normalize_guillotine_algorithm",
    "normalize_optimization_mode",
    "order_group_pieces",
    "orientation_options",
    "uses_guillotine_mode",
]
