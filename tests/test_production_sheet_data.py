from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.model import ModuleData, Piece, Project
from core.production_sheet_data import (
    confirmed_dimension,
    derive_module_dimensions,
    effective_piece_quantity,
    is_valid_thickness,
    load_module_sheet_data,
    piece_from_sheet_row,
    safe_float,
    safe_int,
)


class ProductionSheetDataTests(unittest.TestCase):
    def test_numeric_helpers_accept_decimal_comma_and_keep_defaults(self) -> None:
        self.assertEqual(safe_float("18,5"), 18.5)
        self.assertIsNone(safe_float(""))
        self.assertEqual(safe_int("2,9"), 2)
        self.assertEqual(safe_int("-1", default=4), 4)
        self.assertEqual(confirmed_dimension("1200,5"), 1200.5)
        self.assertTrue(is_valid_thickness("18,5"))
        self.assertFalse(is_valid_thickness("0"))
        self.assertEqual(effective_piece_quantity("2", "3"), 6)

    def test_piece_from_sheet_row_normalizes_dimensions_and_sources(self) -> None:
        piece = piece_from_sheet_row(
            "Modulo",
            {
                "id": "P1",
                "name": "Lateral",
                "quantity": "2",
                "width": "300,5",
                "height": "700",
                "thickness": "18,5",
                "grain_direction": "alto",
                "source": "A.pgmx",
            },
        )

        self.assertEqual(piece.width, 300.5)
        self.assertEqual(piece.height, 700.0)
        self.assertEqual(piece.thickness, 18.5)
        self.assertEqual(piece.quantity, 2)
        self.assertEqual(piece.module_name, "Modulo")
        self.assertEqual(piece.cnc_source, "A.pgmx")

    def test_derive_module_dimensions_uses_name_and_piece_dimensions(self) -> None:
        self.assertEqual(
            derive_module_dimensions(
                "Mod. 01 - 1200 - 450",
                [
                    {"name": "Lateral", "height": 700, "width": 300, "thickness": 18},
                    {"name": "Fondo", "height": 680, "width": 440, "thickness": 18},
                ],
            ),
            (1200, 718, 450),
        )

    def test_load_module_sheet_data_reads_config_sorts_and_adds_program_notes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_sheet_data_") as temp_dir:
            module_dir = Path(temp_dir) / "Modulo"
            module_dir.mkdir()
            (module_dir / "module_config.json").write_text(
                json.dumps(
                    {
                        "settings": {"x": "1200,5", "y": "800", "z": ""},
                        "pieces": [
                            {
                                "id": "H1",
                                "name": "Herraje",
                                "piece_type": "H",
                                "quantity": "1",
                                "width": "100",
                                "height": "200",
                                "thickness": "18",
                                "observations": "Nota | nota",
                            },
                            {
                                "id": "F1",
                                "name": "Frente",
                                "piece_type": "F1",
                                "quantity": "2",
                                "width": "300,5",
                                "height": "700",
                                "thickness": "18,5",
                                "source": "F1.pgmx",
                            },
                            {
                                "id": "SKIP",
                                "name": "Sin espesor",
                                "quantity": "1",
                                "width": "1",
                                "height": "1",
                                "thickness": "0",
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            project = Project(name="Demo", root_directory=temp_dir)
            module = ModuleData(name="Modulo", path=str(module_dir), pieces=[
                Piece(id="Fallback", width=1, height=1, thickness=18),
            ])

            with mock.patch(
                "pgmx.processing.get_pgmx_program_dimension_notes",
                return_value=["Frente note", "Herraje note"],
            ):
                module_data = load_module_sheet_data(project, module, {})

        self.assertEqual([piece["id"] for piece in module_data["pieces"]], ["F1", "H1"])
        self.assertEqual(module_data["pieces"][0]["program_dimension_note"], "Frente note")
        self.assertEqual(module_data["pieces"][1]["observations"], "Nota")
        self.assertEqual(module_data["dimensions"], (1200.5, 800, 300.5))


if __name__ == "__main__":
    unittest.main()
