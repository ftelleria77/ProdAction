"""Cambios de velocidad/profundidad DURANTE el recorrido del fresado lineal.

Derivado de N_RT_E001_Vel / N_RT_E001_Prof (hechos por Fermín en Maestro, byte-validados):
- SpeedAttribute(UPar, Speed): la línea se parte en p = start + upar·(end-start); el tramo
  posterior corre a F = Speed×1000. La Z no cambia.
- DepthAttribute(UPar, Depth): rampa lineal desde la prof. de la operación (plunge inicial)
  hasta Depth, alcanzándola en UPar (G1 interpola X y Z); sigue plano a Depth.
Lo no validado (múltiples cambios, ambos tipos, UPar fuera de (0,1), rampa en diagonal)
hace fail-loud.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.milling.line import LineMillingSpec, build_line_milling_spec

from iso.synthesis import convert
from iso.synthesis._router import _cut_segments, _g1_cut
from iso.synthesis._validation import UnsupportedOperationError, _validate_line_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N022_router_expand")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N022_router_expand")


def _line(**kw) -> LineMillingSpec:
    """Línea E001 estándar de N022: (20,100)->(280,100), prof. 3."""
    base = build_line_milling_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado",
        line_tool_id="1900", line_tool_name="E001", line_tool_width=18.36,
        line_security_plane=20.0, line_is_through=False, line_target_depth=3.0,
    )
    return replace(base, **kw) if kw else base


class CutSegmentsTest(unittest.TestCase):
    def test_sin_cambios_un_solo_tramo(self):
        self.assertEqual(
            _cut_segments(_line(), 3.0, 5000.0),
            [(280.0, 100.0, -3.0, 5000.0)],
        )

    def test_cambio_de_velocidad(self):
        # N_RT_E001_Vel: UPar=0.3, Speed=1 → parte en x=20+0.3·260=98; tramo 2 a F1000.
        spec = _line(speed_changes=((0.3, 1.0),))
        self.assertEqual(
            _cut_segments(spec, 3.0, 5000.0),
            [(98.0, 100.0, -3.0, 5000.0), (280.0, 100.0, -3.0, 1000.0)],
        )

    def test_cambio_de_profundidad(self):
        # N_RT_E001_Prof: UPar=0.25, Depth=5 → rampa hasta (85, z=-5); sigue plano a -5.
        spec = _line(depth_changes=((0.25, 5.0),))
        self.assertEqual(
            _cut_segments(spec, 3.0, 5000.0),
            [(85.0, 100.0, -5.0, 5000.0), (280.0, 100.0, -5.0, 5000.0)],
        )


class G1EmissionTest(unittest.TestCase):
    def test_tramo_en_x_repite_z(self):
        self.assertEqual(_g1_cut(20, 100, 98, 100, -3.0, 5000.0),
                         "G1 X98.000 Z-3.000 F5000.000")

    def test_rampa_interpola_x_y_z(self):
        self.assertEqual(_g1_cut(20, 100, 85, 100, -5.0, 5000.0),
                         "G1 X85.000 Z-5.000 F5000.000")

    def test_diagonal_plana_omite_z(self):
        # Quirk de Maestro (N022 dir_diag): con X e Y en movimiento, Z no se emite.
        self.assertEqual(_g1_cut(20, 20, 280, 180, -5.0, 5000.0),
                         "G1 X280.000 Y180.000 F5000.000")

    def test_tramo_en_y_repite_z(self):
        self.assertEqual(_g1_cut(150, 20, 150, 180, -5.0, 5000.0),
                         "G1 Y180.000 Z-5.000 F5000.000")


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(**kw))

    def test_caso_validado_pasa(self):
        _validate_line_milling(_line(speed_changes=((0.3, 1.0),)))
        _validate_line_milling(_line(depth_changes=((0.25, 5.0),)))

    def test_multiples_cambios_y_combinados_pasan(self):
        # Validado en N028 _coment: 2 rampas + 2 cambios de velocidad en una línea.
        _validate_line_milling(_line(speed_changes=((0.3, 1.0), (0.6, 2.0))))
        _validate_line_milling(_line(speed_changes=((0.25, 1.0),), depth_changes=((0.2, 13.0),)))

    def test_upar_fuera_de_rango(self):
        self._assert_rejects(speed_changes=((0.0, 1.0),))
        self._assert_rejects(depth_changes=((1.0, 5.0),))

    def test_profundidad_sobre_diagonal_pasa(self):
        # Validado en N028 diag_prof10: la rampa en diagonal emite G1 X Y Z.
        _validate_line_milling(_line(start_y=20.0, end_y=180.0, depth_changes=((0.25, 5.0),)))


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra los ISOs de Maestro (requiere los discos S:/P: montados)."""

    def _check(self, stem: str) -> None:
        pgmx = _FIXTURE_DIR / f"{stem}.pgmx"
        ref = _REF_DIR / f"{stem.lower()}.iso"
        if not pgmx.exists() or not ref.exists():
            self.skipTest("fixtures S:/P: no disponibles")
        gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
        exp = [ln.rstrip() for ln in
               ref.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
        self.assertEqual(gen, exp)

    def test_vel(self):
        self._check("N_RT_E001_Vel")

    def test_prof(self):
        self._check("N_RT_E001_Prof")


if __name__ == "__main__":
    unittest.main()
