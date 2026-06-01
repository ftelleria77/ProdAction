import unittest

from core import nesting, nesting_dispatch
from core.model import Piece
from core.nesting_model import (
    CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_NONE,
    CutPiece,
)


def _cut_piece(label: str, width: float, height: float, *, allow_rotate: bool = False) -> CutPiece:
    return CutPiece(
        piece=Piece(id=label, width=width, height=height, thickness=18),
        label=label,
        width=width,
        height=height,
        thickness=18,
        color="Blanco",
        allow_rotate=allow_rotate,
    )


class NestingDispatchTests(unittest.TestCase):
    def test_nesting_keeps_dispatch_compatibility_facade(self) -> None:
        self.assertIs(nesting._pack_group_into_boards, nesting_dispatch.pack_group_into_boards)

    def test_dispatch_uses_free_rectangles_for_unoptimized_mode(self) -> None:
        boards, skipped = nesting_dispatch.pack_group_into_boards(
            "Blanco",
            18,
            [_cut_piece("wide", 40, 20), _cut_piece("narrow", 30, 10)],
            board_width=100,
            board_height=50,
            piece_spacing=5,
            section_kerf=5,
            optimization_mode=CUT_OPTIMIZATION_NONE,
        )

        self.assertEqual(skipped, [])
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0].main_cut_orientation, "")
        self.assertEqual([placement.cut_piece.label for placement in boards[0].placements], ["wide", "narrow"])

    def test_dispatch_uses_preferred_brkga_for_guillotine_mode(self) -> None:
        boards, skipped = nesting_dispatch.pack_group_into_boards(
            "Blanco",
            18,
            [_cut_piece("wide", 40, 20), _cut_piece("narrow", 40, 10)],
            board_width=100,
            board_height=50,
            piece_spacing=5,
            section_kerf=5,
            optimization_mode=CUT_OPTIMIZATION_LONGITUDINAL,
        )

        self.assertEqual(skipped, [])
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0].main_cut_orientation, "vertical")
        self.assertEqual(boards[0].main_cut_positions, [40.0])

    def test_dispatch_can_select_dimension_scan_guillotine(self) -> None:
        boards, skipped = nesting_dispatch.pack_group_into_boards(
            "Blanco",
            18,
            [_cut_piece("wide", 40, 20), _cut_piece("narrow", 40, 10)],
            board_width=100,
            board_height=50,
            piece_spacing=5,
            section_kerf=5,
            optimization_mode=CUT_OPTIMIZATION_LONGITUDINAL,
            guillotine_algorithm=CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
        )

        self.assertEqual(skipped, [])
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0].main_cut_orientation, "vertical")
        self.assertEqual(boards[0].main_cut_positions, [40.0])


if __name__ == "__main__":
    unittest.main()
