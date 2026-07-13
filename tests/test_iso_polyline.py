"""Fresado de POLILÍNEA (rectas + arcos) en ISO — derivado de N041 (10/10 byte-idéntico).

Modelo: op de la familia ROUTER; entrada por el START real; UN G-code por segmento en orden —
recta = G1 (regla _g1_cut de siempre), arco = G3 (CCW) / G2 (CW) con I/J ABSOLUTOS al centro.
Abierto o cerrado; pasante = −(espesor+extra); TLC/SVR/S del catálogo. Cubre polilínea recta
(PolylineSpec) y mixta (PolylineSpec); ambas son la MISMA familia "poly" y
transicionan byte-idéntico (N041 two). Corrección/leads/estrategia → lote de combos futuro.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis import build_polyline_spec
from pgmx.synthesis.common.leads import build_approach_spec
from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_arc_polyline_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N041_poly_profile")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N041_poly_profile")


def _poly(**kw):
    base = build_polyline_spec(
        start=(20.0, 60.0),
        segments=[((20.0, 120.0),),
                  ((80.0, 180.0), (80.0, 120.0), "CounterClockwise"),
                  ((240.0, 180.0),)],
        tool_id="1903", tool_name="E004", tool_width=4.0, target_depth=5.0)
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_arc_polyline_milling(_poly(**kw))

    def test_baseline_pasa(self):
        _validate_arc_polyline_milling(_poly())

    def test_correccion_y_acercamiento_pasan(self):
        # N042: corrección izq/der y acercamiento (Arco/En cota/Automatic) — byte-validados.
        _validate_arc_polyline_milling(_poly(side_of_feature="Left"))
        _validate_arc_polyline_milling(_poly(side_of_feature="Right"))
        _validate_arc_polyline_milling(_poly(approach=build_approach_spec(True, approach_type="Arc")))
        _validate_arc_polyline_milling(_poly(side_of_feature="Left",
                                             approach=build_approach_spec(True, approach_type="Arc")))

    def test_combos_sin_fixture(self):
        from pgmx.synthesis.common.leads import build_retract_spec
        # Estrategia, alejamiento, acercamiento no-Arco/velocidad — sin fixture.
        self._assert_rejects(milling_strategy=build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=True, axial_cutting_depth=4.0))
        self._assert_rejects(retract=build_retract_spec(True, retract_type="Arc"))
        self._assert_rejects(approach=build_approach_spec(True, approach_type="Line"))
        self._assert_rejects(approach=build_approach_spec(True, approach_type="Arc", speed=2.0))


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    STEMS = ("N_R_ll", "N_R_lar", "N_R_lar_cw", "N_R_aa", "N_R_ar_l",
             "N_R_closed", "N_R_prof10", "N_R_th", "N_R_e001", "N_R_two")

    _N042_DIR = Path(r"S:\Maestro\Projects\ProdAction\N042_poly_correction")
    _N042_REFS = Path(r"P:\USBMIX\ProdAction\N042_poly_correction")
    N042_STEMS = ("N_T_open_l", "N_T_open_r", "N_T_open_app", "N_T_open_l_app",
                  "N_T_closed_l", "N_T_closed_r", "N_T_closed_l_rev",
                  "N_T_closed_app", "N_T_closed_l_app",
                  "N_T_closed_mid", "N_T_closed_l_mid")

    def test_n042_correccion_byte_identico(self):
        for stem in self.N042_STEMS:
            with self.subTest(stem):
                pgmx = self._N042_DIR / f"{stem}.pgmx"
                ref = self._N042_REFS / f"{stem.lower()}.iso"
                if not pgmx.exists() or not ref.exists():
                    self.skipTest("fixtures S:/P: no disponibles")
                gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
                exp = [ln.rstrip() for ln in
                       ref.read_text(encoding="utf-8", errors="replace")
                       .replace("\r\n", "\n").splitlines()]
                self.assertEqual(gen, exp)

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                pgmx = _FIXTURE_DIR / f"{stem}.pgmx"
                ref = _REF_DIR / f"{stem.lower()}.iso"
                if not pgmx.exists() or not ref.exists():
                    self.skipTest("fixtures S:/P: no disponibles")
                gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
                exp = [ln.rstrip() for ln in
                       ref.read_text(encoding="utf-8", errors="replace")
                       .replace("\r\n", "\n").splitlines()]
                self.assertEqual(gen, exp)


if __name__ == "__main__":
    unittest.main()
