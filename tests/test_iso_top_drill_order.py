"""Regla B-BH-002: orden de los taladros verticales con ToolKey automático (F3.1).

Portada del emisor viejo (`iso_state_synthesis/pgmx_source.py`, 451/453 comparaciones
explicadas) al converter nuevo (`iso/synthesis/_reader.py`). El punto ciego que cierra:
los fixtures N llevan ToolKey EXPLÍCITO (el sintetizador siempre lo resuelve), así que el
corpus propio jamás pudo fabricar el caso auto — y producción es auto (60/60 Cazaux).
Caso real de referencia: Cazaux `Baño\\Vanitory\\Faja frontal` (ensayo 2026-08-05).
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from pgmx.synthesis import build_drill_spec
from iso.synthesis._reader import _ordered_top_drills


def _drill(x, y, *, tool_name="", diameter=8.0, target_depth=10.0, is_through=False):
    spec = build_drill_spec(center_x=x, center_y=y, diameter=diameter, plane_name="Top",
                            target_depth=None if is_through else target_depth,
                            is_through=is_through, tool_resolution="Auto")
    return replace(spec, tool_name=tool_name)


def _xy(specs):
    return [(s.center_x, s.center_y) for s in specs]


class TopDrillOrderTest(unittest.TestCase):
    def test_explicito_conserva_orden_fuente(self):
        block = [_drill(846, 80, tool_name="001"), _drill(34, 20, tool_name="001")]
        ordered = _ordered_top_drills([("top", block, False)])
        self.assertEqual(_xy(ordered), [(846, 80), (34, 20)])

    def test_auto_vecino_mas_cercano_desde_origen(self):
        # La forma de Faja frontal: fuente 846/80, 846/20, 34/80, 34/20 → Maestro emite
        # 34/20 (más cercano al origen), 34/80, 846/80, 846/20.
        block = [_drill(846, 80), _drill(846, 20), _drill(34, 80), _drill(34, 20)]
        ordered = _ordered_top_drills([("milling",), ("top", block, False)])
        self.assertEqual(_xy(ordered), [(34, 20), (34, 80), (846, 80), (846, 20)])

    def test_auto_de_dos_ordena_geometrico(self):
        block = [_drill(500, 10), _drill(100, 300)]
        ordered = _ordered_top_drills([("top", block, False)])
        self.assertEqual(_xy(ordered), [(100, 300), (500, 10)])

    def test_excepcion_s055_arranca_en_max_x_min_y(self):
        # 4 agujeros, UNA fresa, profundidades MIXTAS, precedido por fresado (PGMX-ORD-002,
        # caso TabiqueF6 Haeublein) → arranque en max-X/min-Y en vez del origen.
        block = [_drill(100, 100, target_depth=5.0), _drill(700, 100, target_depth=12.0),
                 _drill(100, 300, target_depth=5.0), _drill(700, 300, target_depth=12.0)]
        ordered = _ordered_top_drills([("milling",), ("top", block, False)])
        self.assertEqual(_xy(ordered)[0], (700, 100))

    def test_excepcion_s055_exige_fresado_previo(self):
        block = [_drill(100, 100, target_depth=5.0), _drill(700, 100, target_depth=12.0),
                 _drill(100, 300, target_depth=5.0), _drill(700, 300, target_depth=12.0)]
        ordered = _ordered_top_drills([("top", block, False)])
        self.assertEqual(_xy(ordered)[0], (100, 100))   # sin milling previo → origen

    def test_patron_con_autos_queda_en_orden_fuente(self):
        patron = [_drill(600, 50), _drill(600, 100)]     # expansión atómica (N008)
        suelto = [_drill(10, 10)]
        ordered = _ordered_top_drills([("top", patron, True), ("top", suelto, False)])
        self.assertEqual(_xy(ordered), [(600, 50), (600, 100), (10, 10)])

    def test_bloques_separados_por_fresado_se_ordenan_aparte(self):
        primero = [_drill(800, 10), _drill(20, 10)]
        segundo = [_drill(900, 10), _drill(50, 10)]
        ordered = _ordered_top_drills([
            ("top", primero, False), ("milling",), ("top", segundo, False)])
        self.assertEqual(_xy(ordered), [(20, 10), (800, 10), (50, 10), (900, 10)])


if __name__ == "__main__":
    unittest.main()
