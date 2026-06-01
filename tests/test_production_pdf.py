from __future__ import annotations

import unittest

from core.production_pdf import (
    PDF_CHECKBOX_SIZE,
    PDF_MARGIN_X,
    pdf_checkbox_appearance,
    pdf_checkbox_changed_javascript,
    pdf_literal_string,
    pdf_number,
    pdf_popup_rect_from_link,
    pdf_rect_from_pixels,
    pdf_stream_object,
)


class ProductionPdfHelpersTests(unittest.TestCase):
    def test_pdf_number_formats_compact_decimal_values(self) -> None:
        self.assertEqual(pdf_number(12.3400), "12.34")
        self.assertEqual(pdf_number(0.0), "0")
        self.assertEqual(pdf_number(1 / 3), "0.3333")

    def test_pdf_literal_string_escapes_pdf_special_characters(self) -> None:
        self.assertEqual(
            pdf_literal_string("A (B)\\C\nD"),
            r"(A \(B\)\\C\nD)",
        )

    def test_pdf_rect_from_pixels_converts_top_left_pixels_to_pdf_rect(self) -> None:
        self.assertEqual(
            pdf_rect_from_pixels(10, 20, 30, 40, page_height_px=200, scale=0.5),
            "5 70 20 90",
        )

    def test_pdf_checkbox_appearance_contains_box_and_optional_checkmark(self) -> None:
        unchecked = pdf_checkbox_appearance(PDF_CHECKBOX_SIZE, checked=False)
        checked = pdf_checkbox_appearance(PDF_CHECKBOX_SIZE, checked=True)

        self.assertIn(b"re S", unchecked)
        self.assertNotIn(b" m\n", unchecked)
        self.assertIn(b" m\n", checked)

    def test_pdf_stream_object_wraps_data_with_length(self) -> None:
        stream = pdf_stream_object("/Type /Test", b"abc")

        self.assertIn(b"/Length 3", stream)
        self.assertTrue(stream.endswith(b"\nendstream"))

    def test_popup_rect_stays_inside_page_margin(self) -> None:
        popup_rect = pdf_popup_rect_from_link(
            (20, 100, 80, 24),
            {"width": 120, "height": 90},
            page_width_px=500,
            page_height_px=700,
        )

        self.assertGreaterEqual(popup_rect[0], PDF_MARGIN_X)
        self.assertGreaterEqual(popup_rect[2], 260)
        self.assertGreaterEqual(popup_rect[3], 200)

    def test_checkbox_changed_javascript_is_stable(self) -> None:
        self.assertIn("this.dirty = true", pdf_checkbox_changed_javascript())


if __name__ == "__main__":
    unittest.main()
