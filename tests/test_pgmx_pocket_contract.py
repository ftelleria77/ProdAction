from __future__ import annotations

import unittest

from pgmx.synthesis.milling.pocket_contract import (
    PolylineContour,
    VaciadoDepth,
    VaciadoGeometry,
    VaciadoStrategy,
    plan_rectangular_no_islands,
)


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


if __name__ == "__main__":
    unittest.main()
