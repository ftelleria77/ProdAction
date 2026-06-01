import unittest

from app.project_detail_piece_table import (
    PIECE_TABLE_HEADERS,
    PIECES_COL_COLOR,
    PIECES_COL_EXCEL,
    PIECES_COL_ID,
    PIECES_COL_NOTES,
    PIECES_COL_PROGRAM,
    PIECES_COL_SWAP,
    piece_table_fixed_column_widths,
    piece_table_swap_button_metrics,
)


class ProjectDetailPieceTableTests(unittest.TestCase):
    def test_headers_match_column_count(self):
        self.assertEqual(len(PIECE_TABLE_HEADERS), 13)
        self.assertEqual(PIECE_TABLE_HEADERS[PIECES_COL_ID], "ID")
        self.assertEqual(PIECE_TABLE_HEADERS[PIECES_COL_EXCEL], "Excel")

    def test_fixed_column_widths_include_non_auto_columns(self):
        widths = piece_table_fixed_column_widths(1.0)

        self.assertEqual(widths[PIECES_COL_ID], 50)
        self.assertEqual(widths[PIECES_COL_SWAP], 18)
        self.assertEqual(widths[PIECES_COL_COLOR], 110)
        self.assertEqual(widths[PIECES_COL_PROGRAM], 250)
        self.assertEqual(widths[PIECES_COL_NOTES], 320)
        self.assertEqual(widths[PIECES_COL_EXCEL], 70)

    def test_swap_button_metrics_scale_with_minimums(self):
        self.assertEqual(piece_table_swap_button_metrics(1.0).width, 14)
        self.assertEqual(piece_table_swap_button_metrics(0.1).width, 11)


if __name__ == "__main__":
    unittest.main()
