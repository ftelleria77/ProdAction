"""Regresión del taladro vertical multi-step / peck (lote N006).

Bloquea la fórmula de profundidades (n pasos iguales; step_depth = máximo) y la
estructura de movimientos del peck (retracción total en pass 1 y última; retracción
a la profundidad previa en las intermedias; aproximación 1 mm sobre la previa).
"""

from __future__ import annotations

import unittest

from iso.synthesis._top_drill import _cut_motion, _peck_depths


class PeckDepthsTest(unittest.TestCase):
    # superficie 95, fondo 81 (target 14 sobre espesor 18, tlc 77)
    SURF, CUT = 95.0, 81.0

    def test_no_step_single_pass(self):
        self.assertEqual(_peck_depths(self.SURF, self.CUT, 0, 0.0), [81.0])

    def test_step_number_equal_steps(self):
        d = _peck_depths(self.SURF, self.CUT, 3, 0.0)
        self.assertEqual([round(z, 3) for z in d], [90.333, 85.667, 81.0])

    def test_step_depth_is_maximum(self):
        # step_depth=3 → ceil(14/3)=5 pasos de 2.8
        d = _peck_depths(self.SURF, self.CUT, 0, 3.0)
        self.assertEqual([round(z, 3) for z in d], [92.2, 89.4, 86.6, 83.8, 81.0])

    def test_last_depth_is_exact_cut(self):
        for d in (_peck_depths(self.SURF, self.CUT, 4, 0.0),
                  _peck_depths(self.SURF, self.CUT, 0, 5.0)):
            self.assertEqual(d[-1], self.CUT)


class CutMotionTest(unittest.TestCase):
    def test_single_pass_plain_retract(self):
        self.assertEqual(
            _cut_motion(150.0, 100.0, 115.0, 2000.0, [81.0]),
            ["G1 G9 Z81.000 F2000.000", "G0 Z115.000"],
        )

    def test_two_pass_peck(self):
        # N006 n2: depths [88, 81]
        self.assertEqual(
            _cut_motion(150.0, 100.0, 115.0, 2000.0, [88.0, 81.0]),
            [
                "G1 G9 Z88.000 F2000.000",
                "G0 X150.000 Y100.000 Z115.000",
                "G0 Z89.000",
                "G1 G9 Z81.000 F2000.000",
                "G0 X150.000 Y100.000 Z115.000",
            ],
        )

    def test_four_pass_peck_intermediate_retracts(self):
        # N006 n4: depths [91.5, 88, 84.5, 81]
        self.assertEqual(
            _cut_motion(150.0, 100.0, 115.0, 2000.0, [91.5, 88.0, 84.5, 81.0]),
            [
                "G1 G9 Z91.500 F2000.000",
                "G0 X150.000 Y100.000 Z115.000",
                "G0 Z92.500",
                "G1 G9 Z88.000 F2000.000",
                "G0 Z91.500",
                "G0 Z89.000",
                "G1 G9 Z84.500 F2000.000",
                "G0 Z88.000",
                "G0 Z85.500",
                "G1 G9 Z81.000 F2000.000",
                "G0 X150.000 Y100.000 Z115.000",
            ],
        )


if __name__ == "__main__":
    unittest.main()
