import unittest

from core import nesting, nesting_boards
from core.model import Piece
from core.nesting_model import CutBoard, CutPiece, CutPlacement


class NestingBoardsTests(unittest.TestCase):
    def test_nesting_keeps_board_helper_compatibility_facade(self) -> None:
        self.assertIs(nesting._normalize_board_definition, nesting_boards.normalize_board_definition)
        self.assertIs(nesting._resolve_board_definition, nesting_boards.resolve_board_definition)
        self.assertIs(nesting._apply_board_margin, nesting_boards.apply_board_margin)

    def test_normalize_board_definition_accepts_veta_alias_and_defaults_margin(self) -> None:
        result = nesting_boards.normalize_board_definition(
            {
                "color": " Blanco ",
                "length": "2750,5",
                "width": "1830,25",
                "thickness": "18,5",
                "veta": "longitudinal",
            }
        )

        self.assertEqual(
            result,
            {
                "color": "Blanco",
                "length": 2750.5,
                "width": 1830.25,
                "thickness": 18.5,
                "grain": "longitudinal",
                "margin": 0.0,
            },
        )

    def test_normalize_board_definition_rejects_invalid_margin(self) -> None:
        self.assertIsNone(
            nesting_boards.normalize_board_definition(
                {
                    "color": "Blanco",
                    "length": 100,
                    "width": 40,
                    "thickness": 18,
                    "margin": 20,
                }
            )
        )

    def test_resolve_board_definition_picks_largest_matching_board(self) -> None:
        result = nesting_boards.resolve_board_definition(
            "blanco",
            18.0,
            [
                {"color": "Blanco", "length": 2000, "width": 1000, "thickness": 18},
                {"color": "Blanco", "length": 2750, "width": 1830, "thickness": 18},
                {"color": "Blanco", "length": 3000, "width": 1000, "thickness": 25},
            ],
        )

        self.assertEqual(result["length"], 2750.0)
        self.assertEqual(result["width"], 1830.0)

    def test_apply_board_margin_shifts_board_content_and_keeps_utilization_on_full_board(self) -> None:
        piece = Piece(id="P1", width=100, height=50, thickness=18)
        cut_piece = CutPiece(
            piece=piece,
            label="P1",
            width=100,
            height=50,
            thickness=18,
            color="Blanco",
            allow_rotate=True,
        )
        board = CutBoard(
            material="Blanco",
            thickness=18,
            board_width=180,
            board_height=100,
            board_margin=0,
            grain="",
            index=1,
            placements=[CutPlacement(cut_piece=cut_piece, x=5, y=7, width=100, height=50)],
            main_cut_positions=[80],
        )

        result = nesting_boards.apply_board_margin([board], board_width=200, board_height=120, board_margin=10)

        self.assertIs(result[0], board)
        self.assertEqual((board.placements[0].x, board.placements[0].y), (15, 17))
        self.assertEqual(board.main_cut_positions, [90])
        self.assertEqual(board.board_width, 200.0)
        self.assertEqual(board.board_height, 120.0)
        self.assertEqual(board.board_margin, 10.0)
        self.assertAlmostEqual(board.utilization, (100 * 50) / (200 * 120))


if __name__ == "__main__":
    unittest.main()
