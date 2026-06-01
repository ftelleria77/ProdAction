import tempfile
import unittest
from pathlib import Path

from core import nesting, nesting_service
from core.model import ModuleData, Piece, Project


class NestingServiceTests(unittest.TestCase):
    def test_nesting_exports_generate_cut_diagrams_service(self) -> None:
        self.assertIs(nesting.generate_cut_diagrams, nesting_service.generate_cut_diagrams)

    def test_generate_cut_diagrams_reports_missing_configured_board_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            project = Project(
                name="Proyecto",
                root_directory=temp_dir_name,
                client="Cliente",
                modules=[
                    ModuleData(
                        name="A - Bajo",
                        path=temp_dir_name,
                        pieces=[
                            Piece(
                                id="P1",
                                width=100,
                                height=50,
                                thickness=18,
                                quantity=1,
                                color="Blanco",
                                name="Lateral",
                            )
                        ],
                    )
                ],
            )

            result = nesting_service.generate_cut_diagrams(
                project,
                Path(temp_dir_name),
                board_definitions=[
                    {"color": "Negro", "length": 2750, "width": 1830, "thickness": 18}
                ],
            )

        self.assertIsNone(result["pdf_file"])
        self.assertTrue(result["used_configured_boards"])
        self.assertEqual(result["missing_board_groups"], [{"material": "Blanco", "thickness": 18.0, "piece_count": 1}])
        self.assertEqual(result["skipped_pieces"], ["Lateral (A)"])
        self.assertEqual(result["group_summaries"][0]["board_count"], 0)


if __name__ == "__main__":
    unittest.main()
