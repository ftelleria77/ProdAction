"""Fresado CIRCULAR — derivado de N038 (10/10 byte-idéntico).

Modelo: op de la familia ROUTER (mismo header T{n}/transición/teardown que las líneas).
Entrada por el ESTE del círculo (cx+r, cy); plunge estilo línea; el 360° se emite como DOS
SEMICÍRCULOS G3 (CCW) / G2 (CW) con I/J ABSOLUTOS al centro (este→oeste→este); pasante
validado (z = −(espesor+extra)); el círculo cierra donde empezó (ancla de transiciones).
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis import build_circle_milling_spec
from pgmx.synthesis.common.leads import build_approach_spec
from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_circle_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N038_circle")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N038_circle")


def _circ(**kw):
    base = build_circle_milling_spec(
        center_x=150.0, center_y=100.0, radius=30.0,
        tool_id="1903", tool_name="E004", tool_width=4.0, target_depth=5.0)
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_circle_milling(_circ(**kw))

    def test_baseline_pasa(self):
        _validate_circle_milling(_circ())
        _validate_circle_milling(_circ(winding="Clockwise"))

    def test_combos_n039_pasan(self):
        # N039 (12/12): corrección Int/Ext, leads con û=tangente, estrategias Bi/Uni/Helicoidal.
        from pgmx.synthesis.common.leads import build_retract_spec
        from pgmx.synthesis.common.strategy import (
            build_helical_milling_strategy_spec,
            build_unidirectional_milling_strategy_spec,
        )
        bi = build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=True, axial_cutting_depth=4.0)
        for kw in (dict(side_of_feature="Left"),
                   dict(side_of_feature="Right"),
                   dict(approach=build_approach_spec(True, approach_type="Arc")),
                   dict(approach=build_approach_spec(True, approach_type="Line")),
                   dict(milling_strategy=bi),
                   dict(milling_strategy=build_unidirectional_milling_strategy_spec(
                       allow_multiple_passes=True, axial_cutting_depth=4.0)),
                   dict(milling_strategy=build_helical_milling_strategy_spec(
                       axial_cutting_depth=4.0)),
                   dict(milling_strategy=bi,
                        approach=build_approach_spec(True, approach_type="Arc"),
                        retract=build_retract_spec(True, retract_type="Arc"))):
            _validate_circle_milling(_circ(**kw))

    def test_combos_sin_fixture(self):
        from pgmx.synthesis.common.strategy import build_helical_milling_strategy_spec
        heli = build_helical_milling_strategy_spec(axial_cutting_depth=4.0)
        # Corrección+estrategia, helicoidal CW/leads, modos/velocidades de lead — sin fixture.
        self._assert_rejects(side_of_feature="Left",
                             milling_strategy=build_bidirectional_milling_strategy_spec(
                                 allow_multiple_passes=True, axial_cutting_depth=4.0))
        self._assert_rejects(winding="Clockwise", milling_strategy=heli)
        self._assert_rejects(milling_strategy=heli,
                             approach=build_approach_spec(True, approach_type="Arc"))
        self._assert_rejects(approach=build_approach_spec(True, approach_type="Arc",
                                                          mode="Down"))
        self._assert_rejects(approach=build_approach_spec(True, approach_type="Arc",
                                                          speed=2.0))

    def test_degenerado(self):
        self._assert_rejects(radius=0.0)


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    STEMS = ("N_O_base", "N_O_cw", "N_O_r10", "N_O_r60", "N_O_prof10",
             "N_O_th", "N_O_e001", "N_O_pos", "N_O_sec10", "N_O_two")

    N039_DIR = Path(r"S:\Maestro\Projects\ProdAction\N039_circle_combos")
    N039_REFS = Path(r"P:\USBMIX\ProdAction\N039_circle_combos")
    N039_STEMS = ("N_P_side_l", "N_P_side_r", "N_P_side_l_cw", "N_P_side_l_th",
                  "N_P_mp_bi", "N_P_mp_uni", "N_P_heli", "N_P_app_arc",
                  "N_P_app_ret_arc", "N_P_app_line", "N_P_mp_leads", "N_P_side_l_leads")

    def test_n039_combos_byte_identico(self):
        for stem in self.N039_STEMS:
            with self.subTest(stem):
                pgmx = self.N039_DIR / f"{stem}.pgmx"
                ref = self.N039_REFS / f"{stem.lower()}.iso"
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
