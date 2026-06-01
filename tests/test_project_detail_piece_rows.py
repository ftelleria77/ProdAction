from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.project_detail_piece_rows import (
    build_piece_from_row,
    build_module_pieces_from_rows,
    coerce_saved_flag,
    find_orphan_pgmx_files,
    infer_companion_f6_source,
    normalize_piece_row_flags,
    normalize_source_path,
    parse_module_setting_dimension,
    parse_optional_piece_float,
    parse_positive_optional_piece_float,
    serialize_piece_rows_for_config,
    unique_orphan_piece_id,
)


class ProjectDetailPieceRowsTests(unittest.TestCase):
    def test_normalize_piece_row_flags_migrates_excel_and_quantity(self) -> None:
        row = normalize_piece_row_flags(
            {
                "id": "P1",
                "excel": "x",
                "en_juego": "si",
                "quantity": "2",
                "quantity_step": 1,
                "grain_direction": "alto",
                "observations": None,
            }
        )

        self.assertTrue(row["en_juego"])
        self.assertTrue(row["include_in_sheet"])
        self.assertEqual(row["quantity"], 2)
        self.assertNotIn("excel", row)
        self.assertNotIn("quantity_step", row)

    def test_piece_float_parsers_keep_editor_and_program_rules_separate(self) -> None:
        self.assertEqual(parse_optional_piece_float("0"), 0.0)
        self.assertEqual(parse_optional_piece_float("-1,5"), -1.5)
        self.assertIsNone(parse_optional_piece_float(""))
        self.assertIsNone(parse_positive_optional_piece_float("0"))
        self.assertEqual(parse_positive_optional_piece_float("2,5"), 2.5)

    def test_parse_module_setting_dimension_compacts_numeric_values(self) -> None:
        self.assertEqual(parse_module_setting_dimension("100,0"), 100)
        self.assertEqual(parse_module_setting_dimension("100,125"), 100.12)
        self.assertEqual(parse_module_setting_dimension(""), "")
        self.assertEqual(parse_module_setting_dimension("abc"), "abc")

    def test_build_piece_from_row_parses_dimensions_and_program_dimensions(self) -> None:
        piece = build_piece_from_row(
            {
                "id": "P1",
                "name": "Pieza",
                "quantity": "3",
                "height": "100,5",
                "width": "200",
                "thickness": "18",
                "source": "P1.pgmx",
                "program_width": "0",
                "program_height": "200",
            },
            module_name="Modulo",
        )

        self.assertEqual(piece.quantity, 3)
        self.assertEqual(piece.height, 100.5)
        self.assertEqual(piece.width, 200.0)
        self.assertEqual(piece.thickness, 18.0)
        self.assertIsNone(piece.program_width)
        self.assertEqual(piece.program_height, 200.0)

    def test_program_reference_helpers_use_relative_and_companion_f6_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_piece_rows_") as temp_dir:
            module_path = Path(temp_dir)
            nested_path = module_path / "Nested"
            nested_path.mkdir()
            program_path = nested_path / "P1.pgmx"
            program_path.write_text("<xml />", encoding="utf-8")
            companion_path = nested_path / "P1F6.pgmx"
            companion_path.write_text("<xml />", encoding="utf-8")

            self.assertEqual(normalize_source_path(str(program_path), module_path), "Nested/P1.pgmx")
            self.assertEqual(infer_companion_f6_source("Nested/P1.pgmx", module_path), "Nested/P1F6.pgmx")
            self.assertEqual(find_orphan_pgmx_files(module_path, [{"source": "Nested/P1.pgmx"}]), [companion_path])

    def test_unique_orphan_piece_id_sanitizes_and_deduplicates(self) -> None:
        piece_id = unique_orphan_piece_id(Path("Pieza nueva.pgmx"), [{"id": "Pieza_nueva"}])

        self.assertEqual(piece_id, "Pieza_nueva_2")

    def test_serialize_piece_rows_for_config_removes_legacy_fields(self) -> None:
        rows = serialize_piece_rows_for_config(
            [
                {
                    "id": "P1",
                    "quantity": "",
                    "excel": True,
                    "en_juego": "",
                    "quantity_step": 1,
                    "observations": None,
                }
            ]
        )

        self.assertEqual(rows[0]["quantity"], 1)
        self.assertFalse(rows[0]["en_juego"])
        self.assertTrue(rows[0]["include_in_sheet"])
        self.assertNotIn("excel", rows[0])
        self.assertNotIn("quantity_step", rows[0])

    def test_build_module_pieces_from_rows_maps_ui_fields_to_piece_model(self) -> None:
        pieces = build_module_pieces_from_rows(
            [
                {
                    "id": "P1",
                    "name": "Pieza",
                    "quantity": "2",
                    "height": "",
                    "width": "120",
                    "thickness": "",
                    "source": "P1.pgmx",
                    "pgmx": "ok",
                    "en_juego": True,
                    "include_in_sheet": True,
                }
            ],
            module_name="Modulo",
        )

        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0].quantity, 2)
        self.assertEqual(pieces[0].height, 0.0)
        self.assertEqual(pieces[0].width, 120.0)
        self.assertIsNone(pieces[0].thickness)
        self.assertEqual(pieces[0].cnc_source, "P1.pgmx")
        self.assertEqual(pieces[0].module_name, "Modulo")

    def test_coerce_saved_flag_accepts_known_truthy_values(self) -> None:
        self.assertTrue(coerce_saved_flag("x"))
        self.assertTrue(coerce_saved_flag("sí"))
        self.assertFalse(coerce_saved_flag(""))
