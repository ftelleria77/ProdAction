from __future__ import annotations

import unittest

from core.en_juego_transform import (
    EnJuegoTransform,
    prefixed_feature_name,
    transform_supported_spec,
)
from pgmx import synthesis as sp


class EnJuegoTransformTests(unittest.TestCase):
    def test_point_applies_translation_and_clockwise_rotation(self) -> None:
        transform = EnJuegoTransform(origin_x_mm=10, origin_y_mm=20, rotation_deg=90)

        self.assertAlmostEqual(transform.point(5, 0)[0], 10)
        self.assertAlmostEqual(transform.point(5, 0)[1], 15)
        self.assertAlmostEqual(transform.point(0, 5)[0], 15)
        self.assertAlmostEqual(transform.point(0, 5)[1], 20)

    def test_feature_name_prefix_keeps_stable_fallback(self) -> None:
        self.assertEqual(prefixed_feature_name("", ""), "Fresado")
        self.assertEqual(prefixed_feature_name("Linea", "Pieza 1"), "Pieza 1 - Linea")

    def test_transform_supported_line_polyline_circle_and_drilling_specs(self) -> None:
        transform = EnJuegoTransform(origin_x_mm=100, origin_y_mm=200, rotation_deg=0)

        line = transform_supported_spec(
            sp.LineSpec(0, 0, 10, 5, feature_name="Linea"),
            transform,
            feature_name_prefix="P1",
        )
        polyline = transform_supported_spec(
            sp.build_polyline_spec(
                points=((0, 0), (5, 5), (10, 5)), feature_name="Perfil"),
            transform,
            feature_name_prefix="P1",
        )
        circle = transform_supported_spec(
            sp.CircleSpec(2, 3, 4, feature_name="Circulo"),
            transform,
            feature_name_prefix="P1",
        )
        drilling = transform_supported_spec(
            sp.DrillSpec(7, 8, 5, feature_name="Taladro"),
            transform,
            feature_name_prefix="P1",
        )

        self.assertEqual((line.start_x, line.start_y, line.end_x, line.end_y), (100, 200, 110, 205))
        self.assertEqual(polyline.points, ((100, 200), (105, 205), (110, 205)))
        self.assertEqual((circle.center_x, circle.center_y), (102, 203))
        self.assertEqual((drilling.center_x, drilling.center_y), (107, 208))
        self.assertEqual(line.feature_name, "P1 - Linea")
        self.assertEqual(polyline.feature_name, "P1 - Perfil")
        self.assertEqual(circle.feature_name, "P1 - Circulo")
        self.assertEqual(drilling.feature_name, "P1 - Taladro")

    def test_transform_supported_spec_rejects_unknown_specs(self) -> None:
        with self.assertRaises(TypeError):
            transform_supported_spec(object(), EnJuegoTransform(0, 0))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
