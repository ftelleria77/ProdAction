"""Regresión del park del footer derivado de la operación nula Xn (lote N015).

El `G0 G53 X…` (y opcional `Y…`) del footer sale del Xn del .pgmx, no de una constante:
park_x = Xn.x; park_y = -Xn.y (cama 0..-1500 en pgmx → 0..+1500 en máquina). Sin Xn, el
default de Maestro (-3700). El Z del park (Z201) es machine config y no cambia.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.synthesis import (
    build_drilling_spec, build_synthesis_request, build_xn_spec, synthesize_request,
)
from iso.synthesis import convert


def _convert(xn=None):
    tmp = Path(tempfile.mkdtemp())
    path = tmp / "xn.pgmx"
    req = build_synthesis_request(
        output_path=path, piece_name="xn",
        length=300.0, width=200.0, depth=18.0, origin_x=5.0, origin_y=5.0, origin_z=25.0,
        drillings=[build_drilling_spec(center_x=150.0, center_y=100.0, diameter=8.0,
                                       plane_name="Top", target_depth=10.0, tool_resolution="Auto")],
        xn=xn,
    )
    synthesize_request(req)
    return convert(path)


class XnParkTest(unittest.TestCase):
    def test_park_x_tracks_xn(self):
        self.assertIn("G0 G53 X-2000.000", _convert(build_xn_spec(x=-2000.0)))
        self.assertIn("G0 G53 X0.000", _convert(build_xn_spec(x=0.0)))

    def test_park_y_from_xn_negated(self):
        iso = _convert(build_xn_spec(x=-1500.0, y=-700.0))
        self.assertIn("G0 G53 X-1500.000 Y700.000", iso)

    def test_no_xn_uses_default(self):
        iso = _convert(xn=None)
        self.assertIn("G0 G53 X-3700.000", iso)
        self.assertNotIn(" Y", iso.split("G0 G53 X-3700.000")[1][:20])  # sin Y

    def test_z_park_constant(self):
        for xn in (None, build_xn_spec(x=-2000.0), build_xn_spec(x=0.0, y=-700.0)):
            self.assertIn("G0 G53 Z201.000", _convert(xn))


if __name__ == "__main__":
    unittest.main()
