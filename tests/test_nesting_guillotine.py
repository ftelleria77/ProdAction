import unittest

from core import nesting, nesting_guillotine
from core.model import Piece
from core.nesting_model import CUT_OPTIMIZATION_LONGITUDINAL, CutPiece


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


class NestingGuillotineTests(unittest.TestCase):
    def test_nesting_keeps_guillotine_packer_compatibility_facade(self) -> None:
        self.assertIs(
            nesting._pack_group_into_boards_guillotine,
            nesting_guillotine.pack_group_into_boards_guillotine,
        )
        self.assertIs(
            nesting._pack_group_into_boards_guillotine_dimension_scan,
            nesting_guillotine.pack_group_into_boards_guillotine_dimension_scan,
        )

    def test_current_guillotine_places_simple_section(self) -> None:
        boards, skipped = nesting_guillotine.pack_group_into_boards_guillotine(
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
        self.assertEqual([placement.cut_piece.label for placement in boards[0].placements], ["wide", "narrow"])
        self.assertEqual(boards[0].main_cut_positions, [40.0])
        self.assertEqual(boards[0].main_cut_orientation, "vertical")

    def test_dimension_scan_places_simple_section(self) -> None:
        boards, skipped = nesting_guillotine.pack_group_into_boards_guillotine_dimension_scan(
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
        self.assertEqual([placement.cut_piece.label for placement in boards[0].placements], ["wide", "narrow"])
        self.assertEqual(boards[0].main_cut_positions, [40.0])
        self.assertEqual(boards[0].main_cut_orientation, "vertical")

    def test_current_guillotine_skips_pieces_that_do_not_fit_empty_board(self) -> None:
        oversized = _cut_piece("oversized", 120, 80)

        boards, skipped = nesting_guillotine.pack_group_into_boards_guillotine(
            "Blanco",
            18,
            [oversized],
            board_width=100,
            board_height=50,
            piece_spacing=5,
            section_kerf=5,
            optimization_mode=CUT_OPTIMIZATION_LONGITUDINAL,
        )

        self.assertEqual(boards, [])
        self.assertEqual(skipped, [oversized])


if __name__ == "__main__":
    unittest.main()
