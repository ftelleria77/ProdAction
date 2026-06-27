"""Regresión de la tabla TOP_TOOL (taladro vertical por diámetro).

Valores ground-truth medidos del lote N004 (un taladro por Ø, postprocesado en
Maestro). Bloquea etk6/etk0/spindle/feed/shf por diámetro y el invariante
etk0 = 2^(etk6-1) observado en los 6 puntos. Si Maestro cambia el toolset,
este test falla y obliga a re-derivar (ver iso/machining_lab/n004_top_diameters).
"""

from __future__ import annotations

import unittest

from iso.synthesis._machine import TOP_TOOL, TOP_TOOL_CONICAL, resolve_top_tool

# Ø -> (etk6, etk0, spindle, feed, shf_x, shf_y, shf_z)
EXPECTED = {
    4.0:  (6, 32, 6000, 2000.0, -96.0, 0.0,  -0.200),
    5.0:  (5, 16, 6000, 2000.0, -64.0, 0.0,  -0.950),
    8.0:  (1, 1,  6000, 2000.0, 0.0,   0.0,  0.000),
    15.0: (2, 2,  4000, 1000.0, 0.0,   32.0, -0.200),
    20.0: (3, 4,  4000, 1000.0, 0.0,   64.0, -0.250),
    35.0: (4, 8,  4000, 1000.0, -32.0, 0.0,  -0.350),
}


class TopToolTableTest(unittest.TestCase):
    def test_table_matches_measured(self):
        self.assertEqual(set(TOP_TOOL), set(EXPECTED))
        for dia, (etk6, etk0, spindle, feed, sx, sy, sz) in EXPECTED.items():
            with self.subTest(diameter=dia):
                t = TOP_TOOL[dia]
                self.assertEqual(
                    (t.etk6, t.etk0, t.spindle, t.feed, t.tlc, t.shf_x, t.shf_y, t.shf_z),
                    (etk6, etk0, spindle, feed, 77.0, sx, sy, sz),
                )

    def test_etk0_is_spindle_bitmask(self):
        """etk0 = 2^(etk6-1) en todos los diámetros montados (planas y cónicas)."""
        for t in (*TOP_TOOL.values(), *TOP_TOOL_CONICAL.values()):
            with self.subTest(etk6=t.etk6):
                self.assertEqual(t.etk0, 1 << (t.etk6 - 1))


class MaxSinkTest(unittest.TestCase):
    # def.tlgx SinkingLength: D8/D5/D4 = 40; D15/D20/D35 = 20 (N013)
    EXPECTED_SINK = {4.0: 40.0, 5.0: 40.0, 8.0: 40.0, 15.0: 20.0, 20.0: 20.0, 35.0: 20.0}

    def test_max_sink_values(self):
        for dia, sink in self.EXPECTED_SINK.items():
            with self.subTest(diameter=dia):
                self.assertEqual(TOP_TOOL[dia].max_sink, sink)
        self.assertEqual(TOP_TOOL_CONICAL[5.0].max_sink, 40.0)

    def test_top_effective_depth(self):
        from iso.synthesis._reader import PieceCtx, top_effective_depth
        ctx = PieceCtx("p", 300.0, 200.0, 40.0, 5.0, 5.0, 25.0)
        through = _spec(diameter=20.0, is_through=True)
        blind = _spec(diameter=20.0, target_depth=12.0)
        self.assertEqual(top_effective_depth(through, ctx), 40.0)   # pasante → espesor
        self.assertEqual(top_effective_depth(blind, ctx), 12.0)     # ciego → target

    def test_d20_through_thick_exceeds_sink(self):
        # D20 (sink 20) pasante en panel de 40 → 40 > 20 (lo que el synth bloquea al autorar)
        self.assertGreater(40.0, TOP_TOOL[20.0].max_sink)


def _spec(**kw):
    from pgmx.synthesis import build_drilling_spec
    base = dict(center_x=150.0, center_y=100.0, diameter=8.0, plane_name="Top")
    base.update(kw)
    return build_drilling_spec(**base)


class ConicalToolTest(unittest.TestCase):
    def test_conical_d5_measured(self):
        t = TOP_TOOL_CONICAL[5.0]
        self.assertEqual(
            (t.etk6, t.etk0, t.spindle, t.feed, t.tlc, t.shf_x, t.shf_y, t.shf_z),
            (7, 64, 6000, 2000.0, 77.0, -128.0, 0.0, 0.0),
        )

    def test_resolver_picks_conical_by_family(self):
        # Forma canónica (sin herramienta): resuelve por punta + diámetro.
        self.assertIs(resolve_top_tool(5.0, "Conical", ""), TOP_TOOL_CONICAL[5.0])

    def test_resolver_picks_flat_by_diameter(self):
        self.assertIs(resolve_top_tool(5.0, "Flat", ""), TOP_TOOL[5.0])
        self.assertIs(resolve_top_tool(8.0, "Flat", ""), TOP_TOOL[8.0])

    def test_resolver_prefers_selected_tool_name(self):
        # tool_name (herramienta ya resuelta = etk6) gana sobre drill_family. Cubre la
        # forma tool-selected donde IsFlat puede faltar y drill_family no es fiable.
        self.assertIs(resolve_top_tool(5.0, "Conical", "005"), TOP_TOOL[5.0])   # 005 plano
        self.assertIs(resolve_top_tool(5.0, "Flat", "007"), TOP_TOOL_CONICAL[5.0])  # 007 cónico

    def test_unknown_tool_falls_back_to_family(self):
        # tool_name desconocido → cae en punta+diámetro (no rompe).
        self.assertIs(resolve_top_tool(8.0, "Flat", "999"), TOP_TOOL[8.0])


if __name__ == "__main__":
    unittest.main()
