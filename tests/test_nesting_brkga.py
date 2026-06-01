import random
import unittest

from core import nesting, nesting_brkga
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


class NestingBrkgaTests(unittest.TestCase):
    def test_nesting_keeps_brkga_helper_compatibility_facade(self) -> None:
        self.assertIs(nesting._full_tail_section_metrics, nesting_brkga.full_tail_section_metrics)
        self.assertIs(nesting._decode_random_key_order, nesting_brkga.decode_random_key_order)
        self.assertIs(nesting._initial_order_keys, nesting_brkga.initial_order_keys)
        self.assertIs(nesting._mutate_random_keys, nesting_brkga.mutate_random_keys)
        self.assertIs(nesting._brkga_tail_fitness, nesting_brkga.brkga_tail_fitness)
        self.assertIs(
            nesting._pack_group_into_boards_guillotine_brkga_tail,
            nesting_brkga.pack_group_into_boards_guillotine_brkga_tail,
        )
        self.assertIs(
            nesting._pack_group_into_boards_order_driven_guillotine,
            nesting_brkga.pack_group_into_boards_order_driven_guillotine,
        )

    def test_decode_random_key_order_is_stable_for_equal_keys(self) -> None:
        first = _cut_piece("first", 40, 20)
        second = _cut_piece("second", 30, 20)
        third = _cut_piece("third", 20, 20)

        result = nesting_brkga.decode_random_key_order([first, second, third], [0.5, 0.1, 0.5])

        self.assertEqual([piece.label for piece in result], ["second", "first", "third"])

    def test_initial_and_mutated_keys_stay_in_range(self) -> None:
        self.assertEqual(nesting_brkga.initial_order_keys(1), [0.0])
        self.assertEqual(nesting_brkga.initial_order_keys(3), [0.0, 0.5, 1.0])

        mutated = nesting_brkga.mutate_random_keys(
            [0.0, 0.5, 1.0],
            random.Random(7),
            mutation_rate=1.0,
            mutation_scale=2.0,
        )

        self.assertEqual(len(mutated), 3)
        self.assertTrue(all(0.0 <= key <= 1.0 for key in mutated))

    def test_order_driven_guillotine_places_simple_section(self) -> None:
        boards, skipped = nesting_brkga.pack_group_into_boards_order_driven_guillotine(
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

    def test_brkga_tail_packer_places_simple_section(self) -> None:
        boards, skipped = nesting_brkga.pack_group_into_boards_guillotine_brkga_tail(
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


if __name__ == "__main__":
    unittest.main()
