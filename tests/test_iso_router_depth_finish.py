"""Fresado lineal: pasante (is_through), profundidad extra y rebaba (SideOffset).

Derivado de N024 (11/11 byte-validado):
- Pasante: z = -(espesor + extra) — el fresado SÍ pasa la cara inferior (a diferencia del taladro
  vertical, que para en la mesa e ignora extra). Borde inclusivo del sinking (18+4=22=sink E004 OK).
- Rebaba: en línea es <SideOffset> del ManufacturingFeature (NO AllowanceSide, que queda 0). Suma
  al corrector de radio: SVR = width/2 + rebaba; si da 0, las líneas SVR/VL7 se OMITEN (setup y
  teardown). Ortogonal a la corrección G41/G42 (validada en Center/L/R/xrev con ±2).
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.milling.line import LineSpec, build_line_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_line_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N024_router_through")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N024_router_through")


def _line(**kw) -> LineSpec:
    base = build_line_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado",
        line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
        line_security_plane=20.0, line_is_through=False, line_target_depth=5.0,
    )
    return replace(base, **kw) if kw else base


class FailLoudTest(unittest.TestCase):
    def test_rebaba_valida_pasa(self):
        _validate_line_milling(_line(side_offset=2.0))
        _validate_line_milling(_line(side_offset=-2.0))   # SVR = 0: se omiten las líneas

    def test_rebaba_corrector_negativo(self):
        # width/2 + rebaba < 0 → sin fixture de referencia.
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(side_offset=-3.0))

    def test_allowance_desconocido(self):
        # La rebaba de línea es SideOffset; Allowance* ≠ 0 no tiene uso conocido.
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(allowance_side=2.0))
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(allowance_bottom=1.0))


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

    def test_pasante_extra0(self):
        self._check("N_RTH_th_e0")      # z=-18 (espesor)

    def test_pasante_extra4_borde_sinking(self):
        self._check("N_RTH_th_e4")      # z=-22 = sinking E004 exacto (borde inclusivo)

    def test_rebaba_positiva_center(self):
        self._check("N_RS_side_c_x_reb2")     # SVR 2→4

    def test_rebaba_cero_omite_svr(self):
        self._check("N_RS_side_c_x_rebm2")    # SVR=0: sin líneas SVR/VL7

    def test_rebaba_con_correccion(self):
        self._check("N_RS_side_l_x_reb2")     # rebaba + G41
        self._check("N_RS_side_r_x_rebm2")    # rebaba 0 + G42


if __name__ == "__main__":
    unittest.main()
