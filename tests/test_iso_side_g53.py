"""Regresión del G53 Z de transición lateral (iso.synthesis._machine).

Fórmula validada empíricamente 20/20 contra ISO de Maestro (lotes N001+N002+N003):

    G53 Z = DZ + SECURITY_SIDE + max_i( eff(sp_i) + shf_z(cara_i) )
    eff(sp) = max(sp, SIDE_SECURITY_FLOOR)

Cada caso de `CASES` corresponde a una transición observada en un fixture real;
el comentario indica el fixture de origen.
"""

from __future__ import annotations

import unittest

from iso.synthesis._machine import (
    SIDE_SECURITY_FLOOR,
    _eff_security_plane,
    side_transition_g53_z,
)

# (descripción, dz, faces=[(cara, security_plane), ...], G53 esperado)
CASES = [
    # --- Top/Router → Side: solo el destino aporta mandril lateral ---
    ("c001 Top→Left",            43, [("Left", 20)],                149.300),
    ("Top→Right",                43, [("Right", 20)],               149.450),
    ("Top→Front",                43, [("Front", 20)],               149.500),
    # --- Side → Side: max sobre cara que sale y cara que entra ---
    ("b005 Left→Right",          43, [("Left", 20), ("Right", 20)], 149.450),
    ("b008 Front→Left",          43, [("Front", 20), ("Left", 20)], 149.500),  # origen domina
    ("H001 Front→Right",         43, [("Front", 20), ("Right", 20)],149.500),
    ("H004 Back→Left",           43, [("Back", 20), ("Left", 20)],  149.500),
    # --- Geometría: DZ = origin_z + espesor ---
    ("I001 Front→Left oz40",     58, [("Front", 20), ("Left", 20)], 164.500),
    ("I002 Front→Left d30",      55, [("Front", 20), ("Left", 20)], 161.500),
    ("I004 Front→Left oz10d25",  35, [("Front", 20), ("Left", 20)], 141.500),
    # --- security_plane por taladro (CS30 / CS00) ---
    ("CS30 sec30 ambos",         43, [("Front", 30), ("Right", 30)],159.500),
    ("CS00_1 Front0,Right30",    43, [("Front", 0),  ("Right", 30)],159.450),  # gana Right
    ("CS00_2 Front30,Right0",    43, [("Front", 30), ("Right", 0)], 159.500),  # gana Front
    ("CS00_3 ambos 0 (piso)",    43, [("Front", 0),  ("Right", 0)], 134.500),
    # --- piso eff(sp)=max(sp,5) (serie N003) ---
    ("K01 sp1",                  43, [("Front", 1),  ("Right", 1)], 134.500),
    ("K05 sp5",                  43, [("Front", 5),  ("Right", 5)], 134.500),
    ("K06 sp6",                  43, [("Front", 6),  ("Right", 6)], 135.500),
    ("K07 sp7",                  43, [("Front", 7),  ("Right", 7)], 136.500),
    ("K10 sp10",                 43, [("Front", 10), ("Right", 10)],139.500),
]


class SideTransitionG53Test(unittest.TestCase):
    def test_formula_matches_maestro_reference(self):
        for desc, dz, faces, expected in CASES:
            with self.subTest(desc):
                self.assertAlmostEqual(
                    side_transition_g53_z(dz, faces), expected, places=3
                )

    def test_eff_security_floor(self):
        self.assertEqual(_eff_security_plane(0), SIDE_SECURITY_FLOOR)
        self.assertEqual(_eff_security_plane(5), 5.0)
        self.assertEqual(_eff_security_plane(6), 6.0)

    def test_max_is_per_transition_not_global(self):
        # En H002 (Front→Left→Right) la transición Left→Right NO debe verse
        # arrastrada por el Front (cara lejana): el max es solo de las 2 caras.
        self.assertAlmostEqual(
            side_transition_g53_z(43, [("Left", 20), ("Right", 20)]), 149.450, places=3
        )


if __name__ == "__main__":
    unittest.main()
