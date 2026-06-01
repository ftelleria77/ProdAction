from __future__ import annotations

import os
import unittest

RUN_VACIADO_TESTS = os.environ.get("PRODACTION_ENABLE_VACIADO_TESTS") == "1"
VACIADO_TESTS_PAUSED_REASON = "Vaciado tests paused; set PRODACTION_ENABLE_VACIADO_TESTS=1 to run them."

from tools.pgmx_vaciado_v2 import (
    PolylineContour,
    VaciadoDepth,
    VaciadoGeometry,
    VaciadoStrategy,
    from_pocket_milling_spec,
    plan_rectangular_no_islands,
)
from tools.pgmx_adapters import adapt_pgmx_path
from tools.pgmx_vaciado import EXTERNAL_ROOT


MANUAL_ROOT = EXTERNAL_ROOT / "manual"
STABLE_RECTANGULAR_CASES = tuple(range(1, 22)) + tuple(range(23, 27)) + tuple(range(32, 35))


def _rectangular_geometry() -> VaciadoGeometry:
    return VaciadoGeometry(
        outer=PolylineContour(
            (
                (0.0, 0.0),
                (400.0, 0.0),
                (400.0, 300.0),
                (0.0, 300.0),
                (0.0, 0.0),
            )
        )
    )


def _external_corpus_available() -> bool:
    return MANUAL_ROOT.exists()


def _trajectory_xy_bbox(adaptation) -> tuple[float, float, float, float]:
    points: list[tuple[float, float]] = []
    for operation in adaptation.snapshot.operations:
        for toolpath in operation.toolpaths:
            if toolpath.path_type != "TrajectoryPath" or toolpath.curve is None:
                continue
            points.extend((x, y) for x, y, _z in toolpath.curve.sampled_points)
    if not points:
        raise AssertionError("No TrajectoryPath points found.")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), max(xs), min(ys), max(ys))


@unittest.skipUnless(RUN_VACIADO_TESTS, VACIADO_TESTS_PAUSED_REASON)
class VaciadoV2Tests(unittest.TestCase):
    def test_rectangular_no_islands_builds_offset_family_from_strategy(self) -> None:
        plan = plan_rectangular_no_islands(
            _rectangular_geometry(),
            VaciadoStrategy(tool_width=80.0, overlap=0.5, inside_to_outside=False),
            VaciadoDepth(target_depth=10.0),
        )

        self.assertEqual(plan.offset_family.limit, 150.0)
        self.assertEqual(plan.offset_family.offsets, (40.0, 80.0, 120.0))
        self.assertEqual(plan.traversal_offsets, (40.0, 80.0, 120.0))
        self.assertEqual(tuple(sequence.offset for sequence in plan.primitive_sequences), (40.0, 80.0, 120.0))
        self.assertEqual(
            [(bbox.left, bbox.right, bbox.bottom, bbox.top) for bbox in plan.offset_family.bboxes],
            [
                (40.0, 360.0, 40.0, 260.0),
                (80.0, 320.0, 80.0, 220.0),
                (120.0, 280.0, 120.0, 180.0),
            ],
        )

    def test_inside_to_outside_only_reorders_traversal(self) -> None:
        plan = plan_rectangular_no_islands(
            _rectangular_geometry(),
            VaciadoStrategy(tool_width=80.0, overlap=0.5, inside_to_outside=True),
            VaciadoDepth(target_depth=10.0),
        )

        self.assertEqual(plan.offset_family.offsets, (40.0, 80.0, 120.0))
        self.assertEqual(plan.traversal_offsets, (120.0, 80.0, 40.0))
        self.assertEqual(tuple(sequence.offset for sequence in plan.primitive_sequences), (120.0, 80.0, 40.0))

    def test_allowance_and_overlap_are_strategy_axes(self) -> None:
        plan = plan_rectangular_no_islands(
            _rectangular_geometry(),
            VaciadoStrategy(
                tool_width=80.0,
                overlap=0.25,
                allowance_side=20.0,
                inside_to_outside=False,
            ),
            VaciadoDepth(target_depth=10.0),
        )

        self.assertEqual(plan.strategy.effective_offset, 60.0)
        self.assertEqual(plan.strategy.radial_step, 60.0)
        self.assertEqual(plan.offset_family.offsets, (60.0, 120.0))

    def test_rectangular_loop_primitives_preserve_counterclockwise_orientation(self) -> None:
        plan = plan_rectangular_no_islands(
            _rectangular_geometry(),
            VaciadoStrategy(tool_width=80.0, overlap=0.5, inside_to_outside=False),
            VaciadoDepth(target_depth=10.0),
        )

        sequence = plan.primitive_sequences[0]
        self.assertEqual(sequence.line_count, 4)
        self.assertEqual(sequence.arc_count, 0)
        self.assertEqual(
            [(primitive.start, primitive.end) for primitive in sequence.primitives],
            [
                ((40.0, 40.0), (360.0, 40.0)),
                ((360.0, 40.0), (360.0, 260.0)),
                ((360.0, 260.0), (40.0, 260.0)),
                ((40.0, 260.0), (40.0, 40.0)),
            ],
        )

    def test_rectangular_loop_primitives_preserve_clockwise_orientation(self) -> None:
        plan = plan_rectangular_no_islands(
            _rectangular_geometry(),
            VaciadoStrategy(
                tool_width=80.0,
                overlap=0.5,
                rotation_direction="Clockwise",
                inside_to_outside=False,
            ),
            VaciadoDepth(target_depth=10.0),
        )

        sequence = plan.primitive_sequences[0]
        self.assertEqual(sequence.line_count, 4)
        self.assertEqual(sequence.arc_count, 0)
        self.assertEqual(
            [(primitive.start, primitive.end) for primitive in sequence.primitives],
            [
                ((40.0, 40.0), (40.0, 260.0)),
                ((40.0, 260.0), (360.0, 260.0)),
                ((360.0, 260.0), (360.0, 40.0)),
                ((360.0, 40.0), (40.0, 40.0)),
            ],
        )

    def test_rectangular_no_islands_rejects_internal_geometry(self) -> None:
        island = PolylineContour(
            (
                (150.0, 100.0),
                (250.0, 100.0),
                (250.0, 200.0),
                (150.0, 200.0),
                (150.0, 100.0),
            )
        )
        geometry = VaciadoGeometry(outer=_rectangular_geometry().outer, physical_islands=(island,))

        with self.assertRaises(NotImplementedError):
            plan_rectangular_no_islands(
                geometry,
                VaciadoStrategy(tool_width=80.0),
                VaciadoDepth(target_depth=10.0),
            )

    @unittest.skipUnless(_external_corpus_available(), f"Corpus externo no disponible en {MANUAL_ROOT}")
    def test_adapts_manual_rectangular_pocket_to_v2_contract(self) -> None:
        adaptation = adapt_pgmx_path(MANUAL_ROOT / "Vaciado_008.pgmx")
        spec = adaptation.pocket_millings[0]

        geometry, strategy, depth = from_pocket_milling_spec(spec)
        plan = plan_rectangular_no_islands(geometry, strategy, depth)

        self.assertEqual(strategy.tool_width, 80.0)
        self.assertEqual(strategy.effective_offset, 40.0)
        self.assertEqual(strategy.radial_step, 40.0)
        self.assertEqual(depth.target_depth, 10.0)
        self.assertEqual(plan.offset_family.offsets, (40.0, 80.0, 120.0))

    @unittest.skipUnless(_external_corpus_available(), f"Corpus externo no disponible en {MANUAL_ROOT}")
    def test_manual_stable_rectangular_cases_match_v2_outer_offset_bbox(self) -> None:
        for index in STABLE_RECTANGULAR_CASES:
            with self.subTest(case=f"Vaciado_{index:03d}"):
                adaptation = adapt_pgmx_path(MANUAL_ROOT / f"Vaciado_{index:03d}.pgmx")
                spec = adaptation.pocket_millings[0]
                geometry, strategy, depth = from_pocket_milling_spec(spec)
                plan = plan_rectangular_no_islands(geometry, strategy, depth)
                outermost = plan.offset_family.bboxes[0]
                actual = _trajectory_xy_bbox(adaptation)

                self.assertFalse(geometry.has_internal_geometry)
                self.assertAlmostEqual(plan.offset_family.offsets[0], strategy.effective_offset)
                self.assertAlmostEqual(plan.strategy.radial_step, spec.radial_step)
                self.assertEqual(
                    plan.traversal_offsets,
                    tuple(reversed(plan.offset_family.offsets))
                    if strategy.inside_to_outside
                    else plan.offset_family.offsets,
                )
                self.assertAlmostEqual(actual[0], outermost.left, places=6)
                self.assertAlmostEqual(actual[1], outermost.right, places=6)
                self.assertAlmostEqual(actual[2], outermost.bottom, places=6)
                self.assertAlmostEqual(actual[3], outermost.top, places=6)


if __name__ == "__main__":
    unittest.main()
