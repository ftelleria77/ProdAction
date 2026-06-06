import tempfile
import unittest
from pathlib import Path

from core import nesting, nesting_pieces
from core.model import ModuleData, Piece, Project
from core.nesting_model import PIECE_GRAIN_HEIGHT_AXIS, PIECE_GRAIN_LOCKED


class NestingPiecesTests(unittest.TestCase):
    def test_nesting_keeps_piece_helper_compatibility_facade(self) -> None:
        self.assertIs(nesting._expand_project_pieces, nesting_pieces.expand_project_pieces)
        self.assertIs(nesting._normalize_piece_grain_mode, nesting_pieces.normalize_piece_grain_mode)
        self.assertIs(nesting._is_valid_piece, nesting_pieces.is_valid_piece)
        self.assertIs(nesting._safe_float, nesting_pieces.safe_float)

    def test_normalize_piece_grain_mode_maps_known_and_locked_values(self) -> None:
        self.assertEqual(nesting_pieces.normalize_piece_grain_mode("longitudinal"), PIECE_GRAIN_HEIGHT_AXIS)
        self.assertEqual(nesting_pieces.normalize_piece_grain_mode("veta especial"), PIECE_GRAIN_LOCKED)

    def test_numeric_helpers_accept_decimal_comma(self) -> None:
        self.assertEqual(nesting_pieces.safe_float("18,5"), 18.5)
        self.assertEqual(nesting_pieces.safe_quantity("2,9"), 2)
        self.assertTrue(nesting_pieces.has_valid_cut_dimensions("100,5", "50", "18"))

    def test_expand_project_pieces_groups_valid_piece_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            module_path = Path(temp_dir_name)
            project = Project(
                name="Proyecto",
                root_directory=temp_dir_name,
                modules=[
                    ModuleData(
                        name="A - Bajo",
                        path=str(module_path),
                        quantity=2,
                        pieces=[
                            Piece(
                                id="P1",
                                width="100,5",
                                height=50,
                                thickness=18,
                                quantity=2,
                                color="Blanco",
                                grain_direction="1",
                                name="Lateral",
                                piece_type="F1",
                            ),
                            Piece(
                                id="P2",
                                width=80,
                                height=40,
                                thickness=0,
                                quantity=1,
                                color="Blanco",
                                name="Sin espesor",
                                piece_type="F2",
                            ),
                        ],
                    )
                ],
            )

            grouped = nesting_pieces.expand_project_pieces(project)

        self.assertEqual(list(grouped.keys()), [("Blanco", 18.0)])
        cut_pieces = grouped[("Blanco", 18.0)]
        self.assertEqual([piece.label for piece in cut_pieces], [
            "Lateral #1 (A)",
            "Lateral #2 (A)",
            "Lateral #3 (A)",
            "Lateral #4 (A)",
        ])
        self.assertTrue(all(piece.width == 100.5 and piece.height == 50 for piece in cut_pieces))
        self.assertTrue(all(piece.final_width == 100.5 and piece.final_height == 50 for piece in cut_pieces))


if __name__ == "__main__":
    unittest.main()
