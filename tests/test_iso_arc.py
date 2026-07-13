"""Fresado de ARCO SUELTO en ISO — derivado de N040 (10/10 byte-idéntico).

Modelo: op de la familia ROUTER (mismo header/transición/teardown que líneas y círculos).
Entrada por el START real del arco; UN G3 (CCW) / G2 (CW) al end con I/J ABSOLUTOS al centro;
pasante = −(espesor+extra); TLC/SVR/S del catálogo. Baseline Center; corrección/leads/
estrategia → lote de combos futuro (fail-loud).
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis import build_arc_spec
from pgmx.synthesis.common.leads import build_approach_spec
from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_arc_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N040_arc")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N040_arc")


def _arc(**kw):
    base = build_arc_spec(
        start_x=210.0, start_y=100.0, end_x=90.0, end_y=100.0,
        center_x=150.0, center_y=100.0,
        tool_id="1903", tool_name="E004", tool_width=4.0, target_depth=5.0)
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_arc_milling(_arc(**kw))

    def test_baseline_pasa(self):
        _validate_arc_milling(_arc())
        _validate_arc_milling(_arc(winding="Clockwise"))

    def test_combos_sin_fixture(self):
        self._assert_rejects(side_of_feature="Left")
        self._assert_rejects(approach=build_approach_spec(True, approach_type="Arc"))
        self._assert_rejects(milling_strategy=build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=True, axial_cutting_depth=4.0))


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    STEMS = ("N_Q_a180", "N_Q_a90", "N_Q_a270", "N_Q_a180_cw", "N_Q_a90_cw",
             "N_Q_prof10", "N_Q_th", "N_Q_e001", "N_Q_pos", "N_Q_two")

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
