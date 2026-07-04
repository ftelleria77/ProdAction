"""Corrección CAD, ZigZag, Avanz./Rotación y atributos sobre diagonal (N023/N025/N028 ampliados).

- CAD (ActivateCNCCorrection=false): coordenadas desplazadas radio×normal(lado) — izq=rot90ccw(û) —
  sin G41/G42 ni leads ni reset de preamble; entrada/salida Z estilo security (patrón compartido
  con multipasada). SVR se emite igual.
- ZigZag: baja a Z0 y corta EN RAMPA alternando (ida `pasada avance`, vuelta `pasada retorno`),
  clavado en total−último hueco; pasada del último hueco y final plana.
- Avanz./Rotación por operación: corte a F=Avanz×1000 (plunge intacto); S{Rotación}M3 antes del G17
  (misma fresa) o en el header (cambio de herramienta).
- Diagonal: la rampa emite G1 X Y Z; el tramo plano posterior omite Z. Teardown antes de cambio de
  herramienta: ETK[7]=0 al final si la op entrante trae atributos de recorrido.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from iso.synthesis import convert

CASES = [
    ("N023_router_side", "N_RS_side_c_x_CAD"),
    ("N023_router_side", "N_RS_side_l_x_CAD"),
    ("N023_router_side", "N_RS_side_r_x_CAD"),
    ("N023_router_side", "N_RS_side_l_xrev_CAD"),
    ("N023_router_side", "N_RS_side_l_y_CAD"),
    ("N023_router_side", "N_RS_side_l_wide_CAD"),
    ("N025_router_multipass", "N_MP_zigzag_pa2_pr3_uh1"),
    ("N028_router_multitool", "N_MF_mf_e4_e4_e1_F3_S12K"),
    ("N028_router_multitool", "N_MF_mf_e4_e4_e1_diag_prof10"),
    ("N028_router_multitool", "N_MF_mf_e4_e4_e1_diag_vel5"),
]


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    def test_byte_identico(self):
        for lot, stem in CASES:
            with self.subTest(stem):
                pgmx = Path(rf"S:\Maestro\Projects\ProdAction\{lot}\{stem}.pgmx")
                ref = Path(rf"P:\USBMIX\ProdAction\{lot}\{stem.lower()}.iso")
                if not pgmx.exists() or not ref.exists():
                    self.skipTest("fixtures S:/P: no disponibles")
                gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
                exp = [ln.rstrip() for ln in ref.read_text(
                    encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
                self.assertEqual(gen, exp)


if __name__ == "__main__":
    unittest.main()
