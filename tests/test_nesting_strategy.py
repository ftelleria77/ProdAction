import unittest

from core import nesting, nesting_strategy
from core.model import Piece
from core.nesting_model import (
    BOARD_GRAIN_LENGTH,
    BOARD_GRAIN_WIDTH,
    CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL,
    CUT_GUILLOTINE_ALGORITHM_CURRENT,
    CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_NONE,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutPiece,
    PIECE_GRAIN_HEIGHT_AXIS,
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


class NestingStrategyTests(unittest.TestCase):
    def test_nesting_keeps_strategy_helper_compatibility_facade(self) -> None:
        self.assertIs(nesting._normalize_optimization_mode, nesting_strategy.normalize_optimization_mode)
        self.assertIs(nesting._normalize_board_grain_axis, nesting_strategy.normalize_board_grain_axis)
        self.assertIs(nesting._normalize_guillotine_algorithm, nesting_strategy.normalize_guillotine_algorithm)
        self.assertIs(nesting._orientation_options, nesting_strategy.orientation_options)
        self.assertIs(nesting._order_group_pieces, nesting_strategy.order_group_pieces)
        self.assertIs(nesting._uses_guillotine_mode, nesting_strategy.uses_guillotine_mode)

    def test_normalizers_accept_legacy_labels(self) -> None:
        self.assertEqual(
            nesting_strategy.normalize_optimization_mode("optimización longitudinal"),
            CUT_OPTIMIZATION_LONGITUDINAL,
        )
        self.assertEqual(
            nesting_strategy.normalize_optimization_mode("optimizacion transversal"),
            CUT_OPTIMIZATION_TRANSVERSAL,
        )
        self.assertEqual(nesting_strategy.normalize_optimization_mode("sin optimizar"), CUT_OPTIMIZATION_NONE)
        self.assertEqual(nesting_strategy.normalize_board_grain_axis("longitudinal"), BOARD_GRAIN_LENGTH)
        self.assertEqual(nesting_strategy.normalize_board_grain_axis("transversal"), BOARD_GRAIN_WIDTH)
        self.assertEqual(
            nesting_strategy.normalize_guillotine_algorithm("dimension_scan"),
            CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
        )
        self.assertEqual(
            nesting_strategy.normalize_guillotine_algorithm("genetico"),
            CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL,
        )
        self.assertEqual(nesting_strategy.normalize_guillotine_algorithm("otro"), CUT_GUILLOTINE_ALGORITHM_CURRENT)

    def test_orientation_options_preserve_grain_alignment(self) -> None:
        cut_piece = _cut_piece("P1", 100, 50)
        cut_piece.grain_mode = PIECE_GRAIN_HEIGHT_AXIS

        length_options = nesting_strategy.orientation_options(cut_piece, board_grain="longitudinal")
        width_options = nesting_strategy.orientation_options(cut_piece, board_grain="transversal")

        self.assertEqual(length_options, [(100, 50, False)])
        self.assertEqual(width_options, [(50, 100, True)])

    def test_order_group_pieces_uses_requested_primary_axis(self) -> None:
        wide = _cut_piece("wide", 120, 40, allow_rotate=False)
        tall = _cut_piece("tall", 60, 110, allow_rotate=False)

        longitudinal = nesting_strategy.order_group_pieces([wide, tall], CUT_OPTIMIZATION_LONGITUDINAL)
        transversal = nesting_strategy.order_group_pieces([wide, tall], CUT_OPTIMIZATION_TRANSVERSAL)

        self.assertEqual([piece.label for piece in longitudinal], ["tall", "wide"])
        self.assertEqual([piece.label for piece in transversal], ["wide", "tall"])


if __name__ == "__main__":
    unittest.main()
