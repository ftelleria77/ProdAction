import unittest

from app.project_detail_piece_table_rows import (
    PGMX_OK_STATUS,
    filtered_piece_table_rows,
    piece_table_observations_text,
    piece_table_program_display,
)


class ProjectDetailPieceTableRowsTests(unittest.TestCase):
    def test_filtered_piece_table_rows_keeps_original_indexes(self):
        rows = [
            {"id": "A", "thickness": "18"},
            {"id": "B", "thickness": ""},
            {"id": "C", "thickness": "25"},
        ]

        filtered = filtered_piece_table_rows(rows, lambda value: bool(value))

        self.assertEqual(filtered, [(0, rows[0]), (2, rows[2])])

    def test_program_display_uses_filename_and_status_color(self):
        display = piece_table_program_display(
            "nested/PZA01.pgmx",
            PGMX_OK_STATUS,
            has_invalid_slots=False,
            invalid_slot_note="",
        )

        self.assertEqual(display.text, f"{PGMX_OK_STATUS} PZA01.pgmx")
        self.assertEqual(display.tooltip, "nested/PZA01.pgmx")
        self.assertEqual(display.color, "#4CAF50")

    def test_program_display_marks_invalid_slots(self):
        display = piece_table_program_display(
            "",
            "x",
            has_invalid_slots=True,
            invalid_slot_note="Ranura no ejecutable.",
        )

        self.assertEqual(display.text, "! (ninguno)")
        self.assertEqual(display.tooltip, "(ninguno)\nRanura no ejecutable.")
        self.assertEqual(display.color, "#E65100")

    def test_observations_text_appends_invalid_slot_note(self):
        text = piece_table_observations_text(
            {"observations": "Revisar"},
            "Dimensiones distintas",
            "Ranura no ejecutable.",
        )

        self.assertEqual(text, "Revisar | Dimensiones distintas\nRanura no ejecutable.")


if __name__ == "__main__":
    unittest.main()
