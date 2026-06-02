"""Single-board first-fit compatibility helper for cut nesting."""

from typing import List

from core.model import Piece
from core.nesting_dispatch import pack_group_into_boards
from core.nesting_model import CutPiece
from core.nesting_pieces import is_valid_piece, normalize_piece_grain_mode


def first_fit_2d(pieces: List[Piece], board_width: float, board_height: float, allow_rotate: bool = True):
    """Wrapper simple de compatibilidad para obtener ubicaciones en un solo tablero."""

    cut_pieces = [
        CutPiece(
            piece=piece,
            label=str(piece.name or piece.id or "pieza"),
            width=float(piece.width),
            height=float(piece.height),
            thickness=float(piece.thickness or 0),
            color=str(piece.color or ""),
            allow_rotate=allow_rotate,
            grain_mode=normalize_piece_grain_mode(piece.grain_direction),
            final_width=float(piece.width),
            final_height=float(piece.height),
        )
        for piece in pieces
        if is_valid_piece(piece)
    ]
    boards, _ = pack_group_into_boards(
        "TEMP",
        0.0,
        cut_pieces,
        float(board_width),
        float(board_height),
        0.0,
        0.0,
    )
    if not boards:
        return []

    return [
        {
            "piece_id": placement.cut_piece.piece.id,
            "x": placement.x,
            "y": placement.y,
            "width": placement.width,
            "height": placement.height,
        }
        for placement in boards[0].placements
    ]


__all__ = ["first_fit_2d"]
