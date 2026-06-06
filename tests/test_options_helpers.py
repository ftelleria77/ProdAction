from __future__ import annotations

import unittest

from app.options_helpers import parse_non_negative_measure


class OptionsHelpersTests(unittest.TestCase):
    def test_parse_non_negative_measure_accepts_decimal_comma(self) -> None:
        parsed = parse_non_negative_measure("12,5")

        self.assertEqual(parsed.value, 12.5)
        self.assertIsNone(parsed.error)

    def test_parse_non_negative_measure_reports_invalid_and_negative_values(self) -> None:
        self.assertEqual(parse_non_negative_measure("bad").error, "invalid")
        self.assertEqual(parse_non_negative_measure("-1").error, "negative")


if __name__ == "__main__":
    unittest.main()
