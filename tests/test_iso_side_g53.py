"""Regresión del G53 Z de transición lateral (iso.synthesis._machine).

Fórmula (DZ + SECURITY_SIDE + max_i(eff(sp_i)+shf_z(cara_i)), eff(sp)=max(sp, piso)):

    G53 Z = DZ + 20 + max_i( eff(sp_i) + shf_z(cara_i) )

El piso de eff es **10.5** (N016, config canónica). Los casos sp≥20 vienen de N001/N002
(el piso no aplica ahí); los casos de piso (sp<10.5) vienen de N016 (el 5 de N003 era una
config de Maestro descartada y nunca se había testeado con sp bajo).
"""

from __future__ import annotations

import unittest

from iso.synthesis._machine import TLC_LATERAL_CUT, side_transition_g53_z

# Piso del g53 = ToolOffsetLength del tool que se retrae. En estos casos el origen es el top
# vertical (tlc=77); en Side→Side sería el lateral (65). El piso solo "muerde" con sp bajo.
TOP_TLC = 77.0

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
    # --- piso del g53 sobre la SUMA (sp+shf_z) en 77 — CANÓNICO (N016 Front + N017 Right/Back).
    #     El 5/10.5 anteriores eran de N003 (config descartada). g53 = 43+20+max(77, sp+shf_z) ---
    ("N016 Top→Front sp2 (piso)",  43, [("Front", 2)],  140.000),
    ("N016 Top→Front sp10 (piso)", 43, [("Front", 10)], 140.000),
    ("N016 Top→Front sp30",        43, [("Front", 30)], 159.500),
    ("N017 Top→Right sp2 (piso)",  43, [("Right", 2)],  140.000),   # shf_z 66.45: exige piso/suma
    ("N017 Top→Right sp20",        43, [("Right", 20)], 149.450),
    ("N017 Top→Back sp2 (piso)",   43, [("Back", 2)],   140.000),
]


class SideTransitionG53Test(unittest.TestCase):
    def test_formula_matches_maestro_reference(self):
        for desc, dz, faces, expected in CASES:
            with self.subTest(desc):
                self.assertAlmostEqual(
                    side_transition_g53_z(dz, faces, TOP_TLC), expected, places=3
                )

    def test_g53_floor_is_the_head_tool_length_on_the_sum(self):
        # El piso = head_tlc aplica a (sp+shf_z), no a sp: dos caras con shf_z distinto pero
        # ambas bajo el piso dan el MISMO g53 (140), aunque difieran (Front 66.5 / Right 66.45).
        self.assertAlmostEqual(side_transition_g53_z(43, [("Front", 2)], TOP_TLC), 140.0, places=3)
        self.assertAlmostEqual(side_transition_g53_z(43, [("Right", 2)], TOP_TLC), 140.0, places=3)
        # Con head_tlc del top (77) el piso muerde (sp+shf_z < 77); con el lateral (65) no muerde
        # nunca, porque shf_z (≥66.3) ya supera 65 → en Side→Side el piso es inerte.
        self.assertAlmostEqual(
            side_transition_g53_z(43, [("Front", 2)], TLC_LATERAL_CUT), 43 + 20 + 68.5, places=3)

    def test_max_is_per_transition_not_global(self):
        # En H002 (Front→Left→Right) la transición Left→Right NO debe verse
        # arrastrada por el Front (cara lejana): el max es solo de las 2 caras.
        self.assertAlmostEqual(
            side_transition_g53_z(43, [("Left", 20), ("Right", 20)], TLC_LATERAL_CUT),
            149.450, places=3,
        )


if __name__ == "__main__":
    unittest.main()
