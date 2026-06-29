"""Regresión de las features del taladro lateral (A2, lote N011/N012).

Bloquea: la fórmula del cut depende de la profundidad (cut = borde ∓ TLC_CUT ± depth,
approach fijo); el peck lateral se ignora (corte único); el feed se aplica y el husillo
es fijo; y el límite de hundimiento (SinkingLength) rige ciego y pasante.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.synthesis import build_drilling_spec, build_synthesis_request, synthesize_request
from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError


def _convert(width=200.0, **drill_kw):
    tmp = Path(tempfile.mkdtemp())
    path = tmp / "side.pgmx"
    base = dict(center_x=150.0, center_y=9.0, diameter=8.0, tool_resolution="Auto")
    base.update(drill_kw)
    req = build_synthesis_request(
        output_path=path, piece_name="side",
        length=300.0, width=width, depth=18.0, origin_x=5.0, origin_y=5.0, origin_z=25.0,
        drillings=[build_drilling_spec(**base)],
    )
    synthesize_request(req)
    return convert(path)


class SideCutFormulaTest(unittest.TestCase):
    def test_front_cut_depends_on_depth(self):
        self.assertIn("G1 G9 Y-37.000", _convert(plane_name="Front", target_depth=28.0))
        self.assertIn("G1 G9 Y-50.000", _convert(plane_name="Front", target_depth=15.0))

    def test_back_cut(self):  # borde = width+65 = 265; cut = 265-15 = 250
        self.assertIn("G1 G9 Y250.000", _convert(plane_name="Back", target_depth=15.0))

    def test_left_right_cut(self):
        self.assertIn("G1 G9 X-50.000", _convert(plane_name="Left", target_depth=15.0))
        # Right borde = length+65 = 365; cut = 365-15 = 350
        self.assertIn("G1 G9 X350.000", _convert(plane_name="Right", target_depth=15.0))

    def test_approach_independent_of_depth(self):  # approach no depende de la profundidad
        self.assertIn("Y-85.000", _convert(plane_name="Front", target_depth=28.0))
        self.assertIn("Y-85.000", _convert(plane_name="Front", target_depth=15.0))

    def test_approach_uses_security_plane(self):  # approach Front = -(65 + sp). N014
        self.assertIn("Y-70.000", _convert(plane_name="Front", target_depth=20.0, security_plane=5.0))
        self.assertIn("Y-95.000", _convert(plane_name="Front", target_depth=20.0, security_plane=30.0))
        # el cut NO cambia con sp (solo con la profundidad): -65+20 = -45
        iso = _convert(plane_name="Front", target_depth=20.0, security_plane=5.0)
        self.assertIn("G1 G9 Y-45.000", iso)


class SidePeckFeedSpindleTest(unittest.TestCase):
    def test_peck_ignored_single_cut(self):
        iso = _convert(plane_name="Front", target_depth=28.0, step_number=3)
        self.assertEqual(iso.count("G1 G9 Y"), 1)

    def test_feed_applied_spindle_ignored(self):
        iso = _convert(plane_name="Front", target_depth=28.0, feedrate=1.5, spindle=4500.0)
        self.assertIn("G1 G9 Y-37.000 F1500.000", iso)
        self.assertIn("S6000M3", iso)
        self.assertNotIn("S4500M3", iso)

    def test_feed_clamped_to_side_max(self):  # 9 m/min → 9000, clamp a 3000
        iso = _convert(plane_name="Front", target_depth=28.0, feedrate=9.0)
        self.assertIn("G1 G9 Y-37.000 F3000.000", iso)


class SideDepthLimitTest(unittest.TestCase):
    def test_blind_within_limit_ok(self):
        self.assertIn("G1 G9 Y-35.000", _convert(plane_name="Front", target_depth=30.0))

    def test_blind_over_limit_rejected(self):
        with self.assertRaises(UnsupportedOperationError):
            _convert(plane_name="Front", target_depth=35.0)

    def test_through_over_limit_rejected(self):
        # Front through en panel normal: cruza el ancho (200) ≫ 30 → error.
        with self.assertRaises(UnsupportedOperationError):
            _convert(plane_name="Front", is_through=True)

    def test_through_within_limit_ok(self):
        # Panel angosto (ancho 25): Front through cruza 25 ≤ 30 → se taladra (cut=-65+25=-40).
        iso = _convert(width=25.0, plane_name="Front", is_through=True)
        self.assertIn("G1 G9 Y-40.000", iso)


if __name__ == "__main__":
    unittest.main()
