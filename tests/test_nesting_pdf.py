import tempfile
import unittest
from pathlib import Path

from core import nesting, nesting_pdf


class NestingPdfTests(unittest.TestCase):
    def test_nesting_exports_cut_diagram_pdf_renderer(self) -> None:
        self.assertIs(nesting.build_cut_diagram_pdf, nesting_pdf.build_cut_diagram_pdf)

    def test_empty_cut_diagram_pdf_has_no_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_pdf = Path(temp_dir) / "diagramas.pdf"

            result = nesting_pdf.build_cut_diagram_pdf(output_pdf, [])

            self.assertIsNone(result)
            self.assertFalse(output_pdf.exists())


if __name__ == "__main__":
    unittest.main()
