"""Autoría del ARCO SUELTO (Eje B etapa 2, 2026-07-08): roundtrip sintetizador↔adapter.

El arco se autora como GeomCompositeCurve de UN miembro-arco (la forma observada en las piezas
de producción reales — FrenteCurvo/Módulo Curvo — donde los perfiles curvos serializan arcos
como ``8 áng_ini áng_fin \\n 2 cx cy cz n̂ û v̂ r`` con ángulos en la base û/v̂ de Maestro).
La validación final es N040 postprocesado en Maestro (patrón N031/N033).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis import build_arc_milling_spec, build_synthesis_request, synthesize_request


def _authored(tmp: Path, name: str, **kw) -> Path:
    arc = build_arc_milling_spec(
        start_x=kw.pop("start_x", 210.0), start_y=kw.pop("start_y", 100.0),
        end_x=kw.pop("end_x", 90.0), end_y=kw.pop("end_y", 100.0),
        center_x=kw.pop("center_x", 150.0), center_y=kw.pop("center_y", 100.0),
        tool_id="1903", tool_name="E004", tool_width=4.0,
        target_depth=kw.pop("target_depth", 5.0), **kw)
    path = tmp / f"{name}.pgmx"
    synthesize_request(build_synthesis_request(
        output_path=path, piece_name=name, length=300.0, width=200.0, depth=18.0,
        origin_x=5.0, origin_y=5.0, origin_z=25.0, arc_millings=[arc]))
    return path


class ArcAuthoringRoundtripTest(unittest.TestCase):
    def test_roundtrip_ccw(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = adapt_pgmx_path(_authored(Path(tmp), "a180"))
            self.assertFalse(result.unsupported_entries)
            (spec,) = result.arc_millings
            for got, expected in ((spec.start_x, 210.0), (spec.start_y, 100.0),
                                  (spec.end_x, 90.0), (spec.end_y, 100.0),
                                  (spec.center_x, 150.0), (spec.center_y, 100.0)):
                self.assertAlmostEqual(got, expected, places=9)
            self.assertEqual(spec.winding, "CounterClockwise")
            self.assertEqual(spec.depth_spec.target_depth, 5.0)

    def test_roundtrip_cw_y_cuarto(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = adapt_pgmx_path(_authored(
                Path(tmp), "a90cw", start_x=150.0, start_y=160.0,
                end_x=210.0, end_y=100.0, winding="Clockwise"))
            (spec,) = result.arc_millings
            self.assertEqual(spec.winding, "Clockwise")
            self.assertEqual((spec.start_x, spec.start_y), (150.0, 160.0))

    def test_radio_inconsistente_rechazado(self):
        with self.assertRaises(ValueError):
            build_arc_milling_spec(
                start_x=210.0, start_y=100.0, end_x=90.0, end_y=110.0,
                center_x=150.0, center_y=100.0, target_depth=5.0)


class PolylineOpenClosedTest(unittest.TestCase):
    """El sistema distingue polilíneas ABIERTAS y CERRADAS (directiva Fermín 2026-07-08).

    Maestro no usa flag: la clasificación es geométrica (¿cierra sobre el arranque?). El
    sistema la resuelve explícita (spec.is_closed) y valida un flag `closed` declarado."""

    from pgmx.synthesis import build_arc_polyline_milling_spec as _bld

    def _open(self, **kw):
        from pgmx.synthesis import build_arc_polyline_milling_spec
        return build_arc_polyline_milling_spec(
            start=(20.0, 60.0),
            segments=[((20.0, 120.0),),
                      ((80.0, 180.0), (80.0, 120.0), "CounterClockwise"),
                      ((240.0, 180.0),)],
            target_depth=5.0, **kw)

    def _closed(self, **kw):
        from pgmx.synthesis import build_arc_polyline_milling_spec
        return build_arc_polyline_milling_spec(
            start=(60.0, 40.0),
            segments=[((240.0, 40.0),), ((240.0, 140.0),),
                      ((200.0, 180.0), (200.0, 140.0), "CounterClockwise"),
                      ((100.0, 180.0),),
                      ((60.0, 140.0), (100.0, 140.0), "CounterClockwise"),
                      ((60.0, 40.0),)],
            target_depth=5.0, **kw)

    def test_clasificacion_geometrica(self):
        self.assertFalse(self._open().is_closed)
        self.assertTrue(self._closed().is_closed)

    def test_flag_declarado_consistente(self):
        self.assertFalse(self._open(closed=False).is_closed)
        self.assertTrue(self._closed(closed=True).is_closed)

    def test_flag_declarado_inconsistente_falla(self):
        with self.assertRaises(ValueError):
            self._open(closed=True)      # geometría abierta pero declara cerrada
        with self.assertRaises(ValueError):
            self._closed(closed=False)   # geometría cerrada pero declara abierta


if __name__ == "__main__":
    unittest.main()
