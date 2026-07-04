"""Validación del ciclo de AUTORÍA pgmx ampliada (N031): los .pgmx sintetizados con
rebaba/longitud/invertir/CAD/Avanz-Rotación, postprocesados por Maestro, dan byte-idéntico
con las reglas derivadas — la autoría reproduce lo que Maestro genera desde su UI."""

from __future__ import annotations

import unittest
from pathlib import Path

from iso.synthesis import convert

_FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N031_authoring")
_REFS = Path(r"P:\USBMIX\ProdAction\N031_authoring")


class AuthoringEndToEndTest(unittest.TestCase):
    def test_byte_identico(self):
        for stem in ("N_A_aut_reb2", "N_A_aut_long", "N_A_aut_invert",
                     "N_A_aut_cad_l", "N_A_aut_f3s12"):
            with self.subTest(stem):
                pgmx = _FIXTURES / f"{stem}.pgmx"
                ref = _REFS / f"{stem.lower()}.iso"
                if not pgmx.exists() or not ref.exists():
                    self.skipTest("fixtures S:/P: no disponibles")
                gen = [l.rstrip() for l in convert(pgmx).splitlines()]
                exp = [l.rstrip() for l in ref.read_text(
                    encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
                self.assertEqual(gen, exp)


if __name__ == "__main__":
    unittest.main()
