import unittest

from core import nesting, nesting_geometry


class NestingGeometryTests(unittest.TestCase):
    def test_nesting_keeps_geometry_helper_compatibility_facade(self) -> None:
        self.assertIs(nesting._rectangles_intersect, nesting_geometry.rectangles_intersect)
        self.assertIs(nesting._split_free_rectangle, nesting_geometry.split_free_rectangle)
        self.assertIs(nesting._prune_free_rectangles, nesting_geometry.prune_free_rectangles)
        self.assertIs(nesting._occupied_span, nesting_geometry.occupied_span)

    def test_rectangles_intersect_treats_touching_edges_as_non_intersecting(self) -> None:
        self.assertTrue(nesting_geometry.rectangles_intersect((0, 0, 10, 10), (5, 5, 10, 10)))
        self.assertFalse(nesting_geometry.rectangles_intersect((0, 0, 10, 10), (10, 0, 5, 5)))

    def test_split_free_rectangle_returns_remaining_strips(self) -> None:
        result = nesting_geometry.split_free_rectangle((0, 0, 10, 10), (2, 3, 4, 5))

        self.assertEqual(
            result,
            [
                (0, 0, 2, 10),
                (6, 0, 4, 10),
                (0, 0, 10, 3),
                (0, 8, 10, 2),
            ],
        )

    def test_prune_free_rectangles_removes_contained_rectangles(self) -> None:
        result = nesting_geometry.prune_free_rectangles(
            [
                (0, 0, 10, 10),
                (2, 2, 3, 3),
                (12, 0, 5, 5),
            ]
        )

        self.assertEqual(result, [(0, 0, 10, 10), (12, 0, 5, 5)])

    def test_occupied_span_omits_spacing_when_piece_consumes_free_span(self) -> None:
        self.assertEqual(nesting_geometry.occupied_span(10, 10, 3), 10)
        self.assertEqual(nesting_geometry.occupied_span(6, 10, 3), 9)


if __name__ == "__main__":
    unittest.main()
