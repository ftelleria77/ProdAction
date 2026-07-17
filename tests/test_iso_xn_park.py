"""Regresión del park del footer derivado de la operación nula Xn (lote N015 + N043).

El `G0 G53 X…` (y opcional `Y…`) del footer sale del Xn del .pgmx, no de una constante:
park_x = Xn.x; park_y = -Xn.y (cama 0..-1500 en pgmx → 0..+1500 en máquina). El Z del park
(Z201) es machine config y no cambia.

⚠️ HISTORIA — este archivo tenía un test llamado `test_no_xn_uses_default` que afirmaba que sin
Xn salía el default de Maestro (−3700). **Nunca probó ese caso.** Con la API vieja `xn=None`
significaba "el Xn POR DEFECTO", así que el .pgmx que generaba SÍ tenía Xn (uno con x=−3700):
el test verificaba el Xn por defecto y se llamaba como si verificara su ausencia. No podía ser
de otra manera — el sintetizador SIEMPRE escribía un Xn, así que el caso "sin Xn" era
infabricable, y por eso los 346 fixtures lo tienen todos.

N043 (archivos hechos a mano en Maestro, que no traen Xn) mostró la verdad: **sin Xn el footer
NO lleva `M5` ni park X** — el Xn ES eso; si nadie pide retirar la cabina de seguridad, no se
emite nada. Hoy el caso se fabrica con `xn=None` y vive en `tests/test_pgmx_xn.py`.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.synthesis import (
    DEFAULT_XN, build_drill_spec, build_synthesis_request, build_xn_spec, synthesize_request,
)
from iso.synthesis import convert


def _convert(xn=DEFAULT_XN):
    tmp = Path(tempfile.mkdtemp())
    path = tmp / "xn.pgmx"
    req = build_synthesis_request(
        output_path=path, piece_name="xn",
        length=300.0, width=200.0, depth=18.0, origin_x=5.0, origin_y=5.0, origin_z=25.0,
        drills=[build_drill_spec(center_x=150.0, center_y=100.0, diameter=8.0,
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

    def test_xn_por_defecto_parkea_en_3700(self):
        # Lo que el viejo `test_no_xn_uses_default` verificaba DE VERDAD: el Xn POR DEFECTO lleva
        # x=−3700. No dice nada sobre la ausencia de Xn (ver el docstring del módulo).
        iso = _convert(DEFAULT_XN)
        self.assertIn("G0 G53 X-3700.000", iso)
        self.assertNotIn(" Y", iso.split("G0 G53 X-3700.000")[1][:20])  # sin Y

    def test_z_park_constant(self):
        for xn in (DEFAULT_XN, build_xn_spec(x=-2000.0), build_xn_spec(x=0.0, y=-700.0)):
            self.assertIn("G0 G53 Z201.000", _convert(xn))


if __name__ == "__main__":
    unittest.main()
