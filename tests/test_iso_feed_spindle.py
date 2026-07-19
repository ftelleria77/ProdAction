"""Regresión del override de feed/spindle por operación en taladro vertical (N009/N010).

feedrate viene en m/min → F = feedrate×1000, clampado a max_feed de la tool.
spindle en rpm → S = spindle, clampado a max_spindle. Sin override → defaults.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.synthesis import build_drill_spec, build_synthesis_request, synthesize_request
from iso.synthesis import convert
from iso.synthesis._machine import TOP_TOOL, effective_top_feed_spindle


class EffectiveFeedSpindleTest(unittest.TestCase):
    D8 = TOP_TOOL[8.0]   # default feed 2000 / spindle 6000; max 3000 / 6000

    def test_no_override_uses_defaults(self):
        self.assertEqual(effective_top_feed_spindle(self.D8, 0.0, 0.0), (2000.0, 6000))

    def test_feed_below_max_scales_x1000(self):
        feed, _ = effective_top_feed_spindle(self.D8, 2.5, 0.0)
        self.assertEqual(feed, 2500.0)

    def test_feed_above_max_clamps(self):
        feed, _ = effective_top_feed_spindle(self.D8, 1500.0, 0.0)  # 1500 m/min ≫ max
        self.assertEqual(feed, 3000.0)

    def test_spindle_below_max_kept(self):
        _, rpm = effective_top_feed_spindle(self.D8, 0.0, 4500.0)
        self.assertEqual(rpm, 4500)

    def test_spindle_above_max_clamps(self):
        _, rpm = effective_top_feed_spindle(self.D8, 0.0, 50000.0)  # como la UI de Maestro
        self.assertEqual(rpm, 6000)


class ConvertOverrideTest(unittest.TestCase):
    def _convert(self, **drill_kw):
        tmp = Path(tempfile.mkdtemp())
        path = tmp / "fs.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name="fs",
            length=300, width=200, depth=18, origin_x=5, origin_y=5, origin_z=25,
            drills=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=8.0, plane_name="Top",
                target_depth=10.0, tool_resolution="Auto", **drill_kw)],
        )
        synthesize_request(req)
        return convert(path)

    def test_feed_and_spindle_override(self):
        iso = self._convert(feedrate=2.5, spindle=5000.0)
        self.assertIn("S5000M3", iso)
        self.assertIn("G1 G9 Z85.000 F2500.000", iso)

    def test_spindle_clamped_to_max(self):
        iso = self._convert(spindle=50000.0)
        self.assertIn("S6000M3", iso)


if __name__ == "__main__":
    unittest.main()
