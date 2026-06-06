from __future__ import annotations

import unittest

from core import nesting, nesting_compat, pgmx_processing, production_sheet, summary
from pgmx import processing


class CoreFacadesTests(unittest.TestCase):
    def test_pgmx_processing_facade_reexports_processing_module(self) -> None:
        self.assertIs(pgmx_processing.resolve_piece_program_path, processing.resolve_piece_program_path)
        self.assertIs(pgmx_processing.parse_pgmx_for_piece, processing.parse_pgmx_for_piece)
        self.assertIn("resolve_piece_program_path", dir(pgmx_processing))

    def test_summary_keeps_declared_exports(self) -> None:
        self.assertEqual(
            set(summary.__all__),
            {"export_summary", "export_production_sheet", "export_production_sheet_pdf"},
        )
        self.assertIs(summary.export_production_sheet, production_sheet.export_production_sheet)
        self.assertIs(summary.export_production_sheet_pdf, production_sheet.export_production_sheet_pdf)

    def test_nesting_facade_is_declared_compatibility_contract(self) -> None:
        self.assertEqual(tuple(nesting.__all__), tuple(nesting_compat.__all__))
        self.assertIs(nesting.generate_cut_diagrams, nesting_compat.generate_cut_diagrams)


if __name__ == "__main__":
    unittest.main()
