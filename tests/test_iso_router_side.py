"""Corrección de herramienta en el fresado lineal (side_of_feature Left/Right).

Derivado de N023 (byte-validado, 6/6): el control compensa el radio (SVR = width/2) vía G41 (Left)
/ G42 (Right), relativo al sentido de avance; las coordenadas del corte NO cambian. Lead-in/out de
1 mm antes/después de la línea (constante del ciclo, idéntica en E004 y E001), donde se activa y
desactiva la corrección; la retracción compensada es G1 (no G0).
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.milling.line import LineSpec, build_line_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_line

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\Investigacion iso_converter\N023_router_side")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\Investigacion iso_converter\N023_router_side")


def _line(**kw) -> LineSpec:
    base = build_line_spec(
        start_x=20.0, start_y=100.0, end_x=280.0, end_y=100.0,
        feature_name="Fresado",
        tool_id="1903", tool_name="E004", tool_width=4.0,
        security_plane=20.0, is_through=False, target_depth=5.0,
        side_of_feature=kw.pop("side", "Center"),
    )
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_line(_line(**kw))

    def test_side_left_right_pasan(self):
        _validate_line(_line(side="Left"))
        _validate_line(_line(side="Right"))

    def test_side_sobre_diagonal_pasa(self):
        # Validado en N030 dg_side_l (lead de 1 mm sobre la dirección, fórmula genérica).
        _validate_line(_line(side="Left", start_y=20.0, end_y=180.0))

    def test_side_con_cambios_de_recorrido_pasa(self):
        # N036 side_vel: la retracción y el 1mm del G40 salen al feed VIGENTE tras el cambio.
        _validate_line(_line(side="Left", speed_changes=((0.3, 1.0),)))
        _validate_line(_line(side="Right", depth_changes=((0.25, 5.0),)))


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra los ISOs de Maestro (requiere S:/P: montados)."""

    def _check(self, stem: str) -> None:
        pgmx = _FIXTURE_DIR / f"{stem}.pgmx"
        ref = _REF_DIR / f"{stem.lower()}.iso"
        if not pgmx.exists() or not ref.exists():
            self.skipTest("fixtures S:/P: no disponibles")
        gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
        exp = [ln.rstrip() for ln in
               ref.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
        self.assertEqual(gen, exp)

    def test_left(self):
        self._check("N_RS_side_l_x")

    def test_right(self):
        self._check("N_RS_side_r_x")

    def test_left_invertida(self):
        # El lado es relativo al avance: Left en -X sigue siendo G41 (lead-in en X+1).
        self._check("N_RS_side_l_xrev")

    def test_left_en_y(self):
        self._check("N_RS_side_l_y")

    def test_left_fresa_ancha(self):
        # SVR = width/2 (E001 → 9.18): la compensación toma el radio del corrector.
        self._check("N_RS_side_l_wide")


if __name__ == "__main__":
    unittest.main()
