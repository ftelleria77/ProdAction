"""Validación del ciclo de AUTORÍA pgmx ampliada: los .pgmx sintetizados, postprocesados por
Maestro TAL CUAL, dan byte-idéntico con las reglas derivadas — la autoría reproduce lo que
Maestro genera desde su UI.

- N031 (5/5): rebaba/longitud/invertir/CAD/Avanz-Rotación — features de POSTPROCESADOR
  (autorables con curva plana).
- N033 (4/4): ZigZag y atributos on-route con la forma-Maestro completa (strokes en el
  toolpath ALMACENADO, curvas partidas, namespaces/keys correctos) tras el fallo 0/4 de N032.
Con esto la autoría del fresado lineal queda 100% cerrada."""

from __future__ import annotations

import unittest
from pathlib import Path

from iso.synthesis import convert


def _check_byte_identico(testcase, fixtures: Path, refs: Path, stems: tuple[str, ...]) -> None:
    for stem in stems:
        with testcase.subTest(stem):
            pgmx = fixtures / f"{stem}.pgmx"
            ref = refs / f"{stem.lower()}.iso"
            if not pgmx.exists() or not ref.exists():
                testcase.skipTest("fixtures S:/P: no disponibles")
            gen = [l.rstrip() for l in convert(pgmx).splitlines()]
            exp = [l.rstrip() for l in ref.read_text(
                encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
            testcase.assertEqual(gen, exp)


class AuthoringEndToEndTest(unittest.TestCase):
    def test_n031_features_de_postprocesador(self):
        _check_byte_identico(
            self,
            Path(r"S:\Maestro\Projects\ProdAction\Investigacion iso_converter\N031_authoring"),
            Path(r"P:\USBMIX\ProdAction\Investigacion iso_converter\N031_authoring"),
            ("N_A_aut_reb2", "N_A_aut_long", "N_A_aut_invert", "N_A_aut_cad_l", "N_A_aut_f3s12"),
        )

    def test_n033_zigzag_y_atributos_forma_maestro(self):
        _check_byte_identico(
            self,
            Path(r"S:\Maestro\Projects\ProdAction\Investigacion iso_converter\N033_authoring_c"),
            Path(r"P:\USBMIX\ProdAction\Investigacion iso_converter\N033_authoring_c"),
            ("N_C_aut_zz", "N_C_aut_vel", "N_C_aut_prof", "N_C_aut_multi"),
        )


if __name__ == "__main__":
    unittest.main()
