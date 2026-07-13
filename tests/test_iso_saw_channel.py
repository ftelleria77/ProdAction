"""Canal con la Sierra Vertical X (082, cabezal perforador) — derivado de N037 (9/9).

Modelo: header sin ATC (?%ETK[6]=82 + ?%ETK[17]=257 + S{spindle}M3 + ?%ETK[1]=16 + SHF del
mandril con w/2 restado en Y), cuerpo estilo router con ?%ETK[7]=1, sentido NORMALIZADO a −x
(xfwd byte-idéntico al base), transición entre canales con ?%ETK[8]=1/G40 y DOBLE G0, y
epílogo propio (?%ETK[1]=0 / ?%ETK[17]=0 / G4F1.200).
"""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis import build_synthesis_request, synthesize_request
from pgmx.synthesis.milling.slot import ChannelSpec, build_channel_spec
from pgmx.synthesis.common.leads import build_approach_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_slot_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N037_saw_channel")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N037_saw_channel")


def _slot(**kw) -> ChannelSpec:
    base = build_channel_spec(
        start_x=280.0, start_y=100.0, end_x=20.0, end_y=100.0, target_depth=5.0)
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_slot_milling(_slot(**kw))

    def test_baseline_pasa(self):
        _validate_slot_milling(_slot())

    def test_no_horizontal(self):
        self._assert_rejects(end_y=150.0)

    def test_profundidad_sobre_hundimiento(self):
        from pgmx.synthesis.common.depth import build_milling_depth_spec
        self._assert_rejects(depth_spec=build_milling_depth_spec(
            is_through=False, target_depth=12.0, extra_depth=None))

    def test_combos_sin_fixture(self):
        self._assert_rejects(approach=build_approach_spec(True, approach_type="Arc"))
        self._assert_rejects(side_offset=2.0)
        self._assert_rejects(side_of_feature="Left")

    def test_mezcla_con_fresado_guardada(self):
        # Programa sierra + router: transiciones entre cabezales sin fixture (N037 solo-sierra).
        from pgmx.synthesis import build_line_spec
        line = build_line_spec(
            line_x1=20.0, line_y1=50.0, line_x2=280.0, line_y2=50.0,
            line_feature_name="Fresado", line_tool_id="1903", line_tool_name="E004",
            line_tool_width=4.0, line_security_plane=20.0,
            line_is_through=False, line_target_depth=5.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mix.pgmx"
            synthesize_request(build_synthesis_request(
                output_path=path, piece_name="mix", length=300.0, width=200.0, depth=18.0,
                origin_x=5.0, origin_y=5.0, origin_z=25.0,
                line_millings=[line], slot_millings=[_slot()]))
            with self.assertRaises(UnsupportedOperationError):
                convert(path)


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    STEMS = ("N_S_base", "N_S_prof2", "N_S_prof10", "N_S_y50", "N_S_y150",
             "N_S_corto", "N_S_xfwd", "N_S_sec10", "N_S_two")

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
