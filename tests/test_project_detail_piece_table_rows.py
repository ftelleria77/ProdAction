import unittest

from app.project_detail_piece_table_rows import (
    PGMX_OK_STATUS,
    bounded_table_row,
    can_move_visible_piece,
    filtered_piece_table_rows,
    piece_table_observations_text,
    piece_table_program_display,
    visible_piece_all_index,
    visible_piece_row_for_all_index,
    visible_piece_row_for_id,
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

    def test_visible_piece_selection_helpers_resolve_indexes(self):
        rows = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        visible = [0, 2]

        self.assertEqual(visible_piece_all_index(1, visible, all_rows_count=len(rows)), 2)
        self.assertIsNone(visible_piece_all_index(2, visible, all_rows_count=len(rows)))
        self.assertEqual(visible_piece_row_for_all_index(2, visible), 1)
        self.assertEqual(visible_piece_row_for_id("C", rows, visible), 1)
        self.assertIsNone(visible_piece_row_for_id("B", rows, visible))

    def test_visible_piece_selection_helpers_bound_fallbacks_and_moves(self):
        visible = [0, 2, 4]

        self.assertEqual(bounded_table_row(8, 3), 2)
        self.assertEqual(bounded_table_row(-3, 3), 0)
        self.assertIsNone(bounded_table_row(0, 0))
        self.assertTrue(can_move_visible_piece(1, 3, visible, -1))
        self.assertTrue(can_move_visible_piece(1, 3, visible, 1))
        self.assertFalse(can_move_visible_piece(0, 3, visible, -1))
        self.assertFalse(can_move_visible_piece(2, 3, visible, 1))

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
