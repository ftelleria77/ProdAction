import unittest

from core import nesting, nesting_model
from core.model import Piece


class NestingModelTests(unittest.TestCase):
    def test_nesting_keeps_type_compatibility_facade(self) -> None:
        self.assertIs(nesting.CutPiece, nesting_model.CutPiece)
        self.assertIs(nesting.CutPlacement, nesting_model.CutPlacement)
        self.assertIs(nesting.CutBoard, nesting_model.CutBoard)
        self.assertEqual(nesting.CUT_OPTIMIZATION_LONGITUDINAL, nesting_model.CUT_OPTIMIZATION_LONGITUDINAL)

    def test_cut_piece_defaults_to_unconstrained_grain(self) -> None:
        piece = Piece(id="P1", width=100, height=50, thickness=18)
        cut_piece = nesting_model.CutPiece(
            piece=piece,
            label="P1",
            width=100,
            height=50,
            thickness=18,
            color="Blanco",
            allow_rotate=True,
        )

        self.assertEqual(cut_piece.grain_mode, nesting_model.PIECE_GRAIN_NONE)
        self.assertIsNone(cut_piece.final_width)
        self.assertIsNone(cut_piece.final_height)

    def test_cut_board_mutable_defaults_are_independent(self) -> None:
        first = nesting_model.CutBoard(
            material="Blanco",
            thickness=18,
            board_width=1830,
            board_height=2750,
            board_margin=0,
            grain="",
            index=1,
        )
        second = nesting_model.CutBoard(
            material="Blanco",
            thickness=18,
            board_width=1830,
            board_height=2750,
            board_margin=0,
            grain="",
            index=2,
        )

        first.main_cut_positions.append(100)

        self.assertEqual(first.main_cut_positions, [100])
        self.assertEqual(second.main_cut_positions, [])


if __name__ == "__main__":
    unittest.main()
