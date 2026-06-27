"""Regresión de la derivación de punta (drill_family) desde el BottomCondition.

El tipo de punta de un pasante NO está en el xsi:type ('ThroughHoleBottom') sino en
BottomCondition/IsFlat (true=plana, false=cónica). El adapter debe derivarlo de ahí;
si no, dos pasantes idénticos salvo la punta colapsan a la misma familia. (N007)
"""

from __future__ import annotations

import unittest

from pgmx.adapters import _drill_family_from_bottom


class DrillFamilyFromBottomTest(unittest.TestCase):
    def test_blind_explicit_bottoms(self):
        self.assertEqual(_drill_family_from_bottom("a:ConicalHoleBottom", None), "Conical")
        self.assertEqual(_drill_family_from_bottom("a:FlatHoleBottom", None), "Flat")

    def test_through_uses_is_flat(self):
        self.assertEqual(_drill_family_from_bottom("a:ThroughHoleBottom", True), "Flat")
        self.assertEqual(_drill_family_from_bottom("a:ThroughHoleBottom", False), "Conical")

    def test_through_without_is_flat_is_none(self):
        # Sin IsFlat → None: el default del builder decide (D5+pasante → Conical).
        self.assertIsNone(_drill_family_from_bottom("a:ThroughHoleBottom", None))

    def test_unknown_bottom_is_none(self):
        self.assertIsNone(_drill_family_from_bottom("a:SomethingElse", None))


if __name__ == "__main__":
    unittest.main()
