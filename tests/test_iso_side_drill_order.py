"""Orden de caras laterales (B-BH-005 parcial, F3.2): aparición en fuente + rotación de tanda.

La FACE_PRIORITY fija (Front>Left>Right>Back) era un artefacto del corpus propio: el
sintetizador pre-ordena las caras al serializar, así que ningún fixture N podía
contradecirla (testigo: `N_B008_left_then_front.pgmx`, autorado Left→Front, serializado
Front→Left). La refutó Cazaux `Faja frontal` (fuente Right→Left, ISO Right→Left).
Rotación de tanda validada en Cazaux (Back→Front→Back), acotada a Front/Back por el
contraejemplo Haeublein (Right→Left→Right NO rota).
"""

from __future__ import annotations

import unittest

from pgmx.synthesis import build_drill_spec
from iso.synthesis.converter import _sort_side_drills


def _drill(plane, x):
    return build_drill_spec(center_x=x, center_y=9.0, diameter=8.0, plane_name=plane,
                            target_depth=25.0, tool_resolution="Auto")


def _seq(drills):
    return [(d.plane_name, d.center_x) for d in drills]


class SideDrillOrderTest(unittest.TestCase):
    def test_orden_de_aparicion_no_prioridad(self):
        # Faja frontal: fuente Right,Right,Left,Left → Right primero (prioridad daría Left).
        drills = [_drill("Right", 80), _drill("Right", 20), _drill("Left", 130), _drill("Left", 70)]
        self.assertEqual(_seq(_sort_side_drills(drills)),
                         [("Right", 20), ("Right", 80), ("Left", 130), ("Left", 70)])

    def test_b007_dentro_de_cara_intacto(self):
        # Left/Back descendente en center_x; Right/Front ascendente.
        drills = [_drill("Left", 60), _drill("Left", 140)]
        self.assertEqual(_seq(_sort_side_drills(drills)), [("Left", 140), ("Left", 60)])

    def test_rotacion_de_tanda_back_front_back(self):
        drills = [_drill("Back", 10), _drill("Front", 50), _drill("Back", 90)]
        self.assertEqual(_seq(_sort_side_drills(drills)),
                         [("Back", 90), ("Front", 50), ("Back", 10)])

    def test_right_left_right_NO_rota(self):
        # Contraejemplo Haeublein Divisor_Horiz1: caras X no rotan — se funden por aparición.
        drills = [_drill("Right", 10), _drill("Left", 50), _drill("Right", 90)]
        self.assertEqual(_seq(_sort_side_drills(drills)),
                         [("Right", 10), ("Right", 90), ("Left", 50)])

    def test_corridas_repetidas_sin_rotacion_se_funden(self):
        # 2 corridas de la misma cara sin patrón de tanda (< 3 corridas totales con repetida
        # al inicio y final que no aplique): fusión en primera aparición.
        drills = [_drill("Front", 30), _drill("Back", 60), _drill("Front", 10), _drill("Back", 90)]
        # corridas: F,B,F,B → primera==Front, última==Back → sin rotación → fusión aparición
        self.assertEqual(_seq(_sort_side_drills(drills)),
                         [("Front", 10), ("Front", 30), ("Back", 90), ("Back", 60)])


if __name__ == "__main__":
    unittest.main()
