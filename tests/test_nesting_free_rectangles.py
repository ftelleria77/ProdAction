import unittest

from core import nesting, nesting_free_rectangles
from core.model import Piece
from core.nesting_model import (
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutPiece,
)


def _cut_piece(label: str, width: float, height: float, *, allow_rotate: bool = True) -> CutPiece:
    return CutPiece(
        piece=Piece(id=label, width=width, height=height, thickness=18),
        label=label,
        width=width,
        height=height,
        thickness=18,
        color="Blanco",
        allow_rotate=allow_rotate,
    )


class NestingFreeRectanglesTests(unittest.TestCase):
    def test_nesting_keeps_free_rectangle_packer_compatibility_facade(self) -> None:
        self.assertIs(nesting._placement_score, nesting_free_rectangles.placement_score)
        self.assertIs(
            nesting._pack_group_into_boards_free_rectangles,
            nesting_free_rectangles.pack_group_into_boards_free_rectangles,
        )

    def test_placement_score_biases_requested_axis(self) -> None:
        free_rect = (0, 0, 100, 80)

        longitudinal = nesting_free_rectangles.placement_score(
            free_rect,
            occupied_width=60,
            occupied_height=50,
            optimization_mode=CUT_OPTIMIZATION_LONGITUDINAL,
        )
        transversal = nesting_free_rectangles.placement_score(
            free_rect,
            occupied_width=60,
            occupied_height=50,
            optimization_mode=CUT_OPTIMIZATION_TRANSVERSAL,
        )

        self.assertEqual(longitudinal, (5000, 30, 30, 40))
        self.assertEqual(transversal, (5000, 40, 30, 40))

    def test_pack_group_places_pieces_in_free_rectangles(self) -> None:
        large = _cut_piece("large", 40, 40, allow_rotate=False)
        small = _cut_piece("small", 30, 20, allow_rotate=False)

        boards, skipped = nesting_free_rectangles.pack_group_into_boards_free_rectangles(
            "Blanco",
            18,
            [large, small],
            board_width=100,
            board_height=50,
            piece_spacing=5,
        )

        self.assertEqual(skipped, [])
        self.assertEqual(len(boards), 1)
        self.assertEqual([placement.cut_piece.label for placement in boards[0].placements], ["large", "small"])
        self.assertEqual(
            [(placement.x, placement.y, placement.width, placement.height) for placement in boards[0].placements],
            [(0.0, 0.0, 40, 40), (45.0, 0.0, 30, 20)],
        )
        self.assertAlmostEqual(boards[0].utilization, (40 * 40 + 30 * 20) / (100 * 50))

    def test_pack_group_skips_pieces_that_do_not_fit_empty_board(self) -> None:
        oversized = _cut_piece("oversized", 120, 80, allow_rotate=False)

        boards, skipped = nesting_free_rectangles.pack_group_into_boards_free_rectangles(
            "Blanco",
            18,
            [oversized],
            board_width=100,
            board_height=50,
            piece_spacing=5,
        )

        self.assertEqual(boards, [])
        self.assertEqual(skipped, [oversized])


if __name__ == "__main__":
    unittest.main()
