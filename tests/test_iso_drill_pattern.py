"""Regresión de la expansión de patrones de perforado (lote N008).

Un patrón rectangular se expande a taladros individuales idénticos al base:
center = esquina mínima; columnas +X (spacing), filas +Y (row_spacing); orden
row-major (Y exterior, X interior).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.synthesis import (
    build_drill_pattern_spec,
    build_synthesis_request,
    synthesize_request,
)
from iso.synthesis import convert
from iso.synthesis._reader import expand_drilling_pattern


def _pattern(**kw):
    base = dict(
        center_x=100.0, center_y=80.0, diameter=8.0, columns=1, rows=1,
        spacing=40.0, row_spacing=30.0, plane_name="Top",
        is_through=False, target_depth=10.0, tool_resolution="Auto",
    )
    base.update(kw)
    return build_drill_pattern_spec(
        base.pop("center_x"), base.pop("center_y"), base.pop("diameter"),
        base.pop("columns"), base.pop("rows"), base.pop("spacing"), **base)


class ExpandPatternTest(unittest.TestCase):
    def test_row_major_3x2_positions_and_order(self):
        holes = expand_drilling_pattern(_pattern(columns=3, rows=2))
        coords = [(h.center_x, h.center_y) for h in holes]
        self.assertEqual(coords, [
            (100.0, 80.0), (140.0, 80.0), (180.0, 80.0),    # fila Y=80
            (100.0, 110.0), (140.0, 110.0), (180.0, 110.0),  # fila Y=110
        ])

    def test_columns_advance_in_x(self):
        holes = expand_drilling_pattern(_pattern(columns=3, rows=1))
        self.assertEqual([h.center_x for h in holes], [100.0, 140.0, 180.0])
        self.assertTrue(all(h.center_y == 80.0 for h in holes))

    def test_rows_advance_in_y(self):
        holes = expand_drilling_pattern(_pattern(columns=1, rows=3))
        self.assertEqual([h.center_y for h in holes], [80.0, 110.0, 140.0])
        self.assertTrue(all(h.center_x == 100.0 for h in holes))

    def test_holes_inherit_base_drill(self):
        h = expand_drilling_pattern(_pattern(columns=2, rows=1))[0]
        self.assertEqual(h.diameter, 8.0)
        self.assertEqual(h.plane_name, "Top")
        self.assertFalse(h.depth_spec.is_through)


class ConvertPatternTest(unittest.TestCase):
    def test_convert_emits_one_cut_per_hole(self):
        tmp = Path(tempfile.mkdtemp())
        path = tmp / "pat.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name="pat",
            length=300, width=200, depth=18, origin_x=5, origin_y=5, origin_z=25,
            drilling_patterns=[_pattern(columns=3, rows=2)],
        )
        synthesize_request(req)
        iso = convert(path)
        self.assertEqual(iso.count("G1 G9 Z85.000"), 6)  # 3x2 = 6 agujeros


if __name__ == "__main__":
    unittest.main()
