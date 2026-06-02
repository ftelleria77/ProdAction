import unittest

from core import nesting, nesting_first_fit
from core.model import Piece


class NestingFirstFitTests(unittest.TestCase):
    def test_nesting_keeps_first_fit_compatibility_facade(self) -> None:
        self.assertIs(nesting.first_fit_2d, nesting_first_fit.first_fit_2d)

    def test_first_fit_places_valid_pieces_on_first_board(self) -> None:
        pieces = [
            Piece(id="P1", width=40, height=20, thickness=18, name="Pieza 1"),
            Piece(id="P2", width=30, height=10, thickness=18, name="Pieza 2"),
        ]

        placements = nesting_first_fit.first_fit_2d(pieces, 100, 50, allow_rotate=False)

        self.assertEqual(
            placements,
            [
                {"piece_id": "P1", "x": 0.0, "y": 0.0, "width": 40.0, "height": 20.0},
                {"piece_id": "P2", "x": 0.0, "y": 20.0, "width": 30.0, "height": 10.0},
            ],
        )

    def test_first_fit_skips_invalid_pieces(self) -> None:
        pieces = [
            Piece(id="valid", width=40, height=20, thickness=18),
            Piece(id="invalid", width=0, height=20, thickness=18),
        ]

        placements = nesting_first_fit.first_fit_2d(pieces, 100, 50, allow_rotate=False)

        self.assertEqual([placement["piece_id"] for placement in placements], ["valid"])


if __name__ == "__main__":
    unittest.main()
