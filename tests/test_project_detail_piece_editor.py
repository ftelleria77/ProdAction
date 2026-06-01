from __future__ import annotations

import unittest

from app.project_detail_piece_editor import (
    PieceEditorValues,
    build_piece_editor_row,
    manual_piece_template_label,
    optional_field_text,
)
from core.model import PIECE_GRAIN_CODE_NONE


class ProjectDetailPieceEditorTests(unittest.TestCase):
    def test_manual_piece_template_label_prefers_id_name_pair(self) -> None:
        self.assertEqual(manual_piece_template_label({"id": "P1", "name": "Costado"}), "P1 - Costado")
        self.assertEqual(manual_piece_template_label({"id": "P1", "name": "P1"}), "P1")
        self.assertEqual(manual_piece_template_label({}), "pieza")

    def test_optional_field_text_keeps_zero_and_blanks_none(self) -> None:
        self.assertEqual(optional_field_text(None), "")
        self.assertEqual(optional_field_text(0), "0")
        self.assertEqual(optional_field_text("18"), "18")

    def test_build_piece_editor_row_normalizes_values_and_source(self) -> None:
        row = build_piece_editor_row(
            base_piece_row={
                "program_width": 100,
                "program_height": 200,
                "program_thickness": 18,
                "en_juego": True,
                "include_in_sheet": True,
            },
            values=PieceEditorValues(
                piece_id=" P1 ",
                name=" ",
                quantity="2",
                height="100,5",
                width="200",
                thickness="18",
                color=" Blanco ",
                grain_direction="1",
                source="Modulo/P1.pgmx",
            ),
            normalize_source=lambda value: value.replace("Modulo/", ""),
            infer_companion_f6_source=lambda value: f"{value[:-5]}F6.pgmx" if value else None,
            pgmx_status=lambda value: "ok" if value else "missing",
            color_has_no_grain=lambda color, thickness: color == "Blanco" and thickness == 18,
        )

        self.assertEqual(row["id"], "P1")
        self.assertEqual(row["name"], "P1")
        self.assertEqual(row["quantity"], 2)
        self.assertEqual(row["height"], 100.5)
        self.assertEqual(row["width"], 200.0)
        self.assertEqual(row["thickness"], 18.0)
        self.assertEqual(row["color"], "Blanco")
        self.assertEqual(row["grain_direction"], PIECE_GRAIN_CODE_NONE)
        self.assertEqual(row["source"], "P1.pgmx")
        self.assertEqual(row["f6_source"], "P1F6.pgmx")
        self.assertEqual(row["pgmx"], "ok")
        self.assertEqual(row["program_width"], 100)
        self.assertTrue(row["en_juego"])
        self.assertTrue(row["include_in_sheet"])

    def test_build_piece_editor_row_clears_program_dimensions_without_source(self) -> None:
        row = build_piece_editor_row(
            base_piece_row={
                "program_width": 100,
                "program_height": 200,
                "program_thickness": 18,
            },
            values=PieceEditorValues(
                piece_id="P1",
                name="Pieza",
                quantity="",
                height="",
                width="",
                thickness="",
                color="",
                grain_direction="2",
                source="",
            ),
            normalize_source=lambda value: value,
            infer_companion_f6_source=lambda value: None,
            pgmx_status=lambda value: "missing",
            color_has_no_grain=lambda color, thickness: False,
        )

        self.assertEqual(row["quantity"], 1)
        self.assertIsNone(row["height"])
        self.assertIsNone(row["width"])
        self.assertIsNone(row["thickness"])
        self.assertIsNone(row["color"])
        self.assertEqual(row["source"], "")
        self.assertIsNone(row["program_width"])
        self.assertIsNone(row["program_height"])
        self.assertIsNone(row["program_thickness"])
