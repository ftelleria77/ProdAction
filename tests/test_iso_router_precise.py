"""Corrección de longitud del fresado lineal (<IsPrecise> del feature).

Derivado de N023 _long (6/6 byte-validado): el recorrido se ACORTA el radio de la fresa en ambos
extremos — el centro viaja [start + r·dir, end − r·dir] — para que el FILO cubra exactamente el
segmento programado. r = width/2 (E004 ±2, E001 ±9.18). Con corrección G41/G42, el lead-in/out de
1 mm se calcula sobre los extremos ya acortados. Validada en líneas a eje, ambos sentidos.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.milling.line import LineMillingSpec, build_line_milling_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_line_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N023_router_side")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N023_router_side")


def _line(**kw) -> LineMillingSpec:
    base = build_line_milling_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado",
        line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
        line_security_plane=20.0, line_is_through=False, line_target_depth=5.0,
    )
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(**kw))

    def test_precise_pasa(self):
        _validate_line_milling(_line(is_precise=True))

    def test_precise_sobre_diagonal_pasa(self):
        # Validado en N030 dg_long re-postprocesado: acorte ±r·û genérico (21.703/21.048 exactos).
        _validate_line_milling(_line(is_precise=True, start_y=20.0, end_y=180.0))

    def test_precise_con_rebaba_pasa(self):
        # Resuelto en N029 reb2_long: el acorte usa width/2 (NO el SVR).
        _validate_line_milling(_line(is_precise=True, side_offset=2.0))

    def test_precise_con_cambios_de_recorrido(self):
        self._assert_rejects(is_precise=True, speed_changes=((0.3, 1.0),))
        self._assert_rejects(is_precise=True, depth_changes=((0.25, 5.0),))

    def test_precise_recorrido_degenerado(self):
        # Línea que no supera el ancho de la fresa: el acorte la invierte.
        self._assert_rejects(is_precise=True, end_x=23.0)


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

    def test_center(self):
        self._check("N_RS_side_c_x_long")        # sin G41: corte 22→278

    def test_con_correccion_left(self):
        self._check("N_RS_side_l_x_long")        # G41 + lead-in sobre extremos acortados

    def test_sentido_invertido(self):
        self._check("N_RS_side_l_xrev_long")     # el acorte sigue la dirección de avance

    def test_en_y(self):
        self._check("N_RS_side_l_y_long")

    def test_fresa_ancha(self):
        self._check("N_RS_side_l_wide_long")     # r = 9.18 (width/2, no constante)


if __name__ == "__main__":
    unittest.main()
