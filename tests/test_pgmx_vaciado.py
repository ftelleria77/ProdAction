from __future__ import annotations

from dataclasses import replace
import math
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tools import synthesize_pgmx as sp
from tools.pgmx_adapters import adapt_pgmx_path
from tools.pgmx_vaciado import EXTERNAL_ROOT
from tools.pgmx_vaciado.contour_parallel import (
    _actual_trajectory_xyz,
    _actual_trajectory_xyz_sequences,
    generate_rectangular_contour_parallel_xyz_path,
)
from tools.pgmx_vaciado.island_analysis import (
    generate_rounded_kernel_loop_xy,
    infer_rounded_kernel_loop_xy,
    resolved_boss_ref_xy_contours,
)
from tools.pgmx_vaciado.trace_engine import generate_contour_parallel_pocket_trace


MANUAL_ROOT = EXTERNAL_ROOT / "manual"
BASELINE_PATH = EXTERNAL_ROOT / "Vaciado_000.pgmx"
STABLE_RECTANGULAR_CASES = (
    tuple(range(1, 22))
    + tuple(range(23, 27))
    + tuple(range(32, 35))
)
ISLAND_CASES = {
    22: (
        ((150.0, 250.0, 100.0, 200.0),),
        (42,),
    ),
    27: (
        ((150.0, 250.0, 100.0, 200.0),),
        (12, 20),
    ),
    28: (
        ((150.0, 250.0, 100.0, 200.0),),
        (52,),
    ),
    29: (
        (
            (75.0, 125.0, 125.0, 175.0),
            (275.0, 325.0, 125.0, 175.0),
        ),
        (64,),
    ),
    30: (
        (
            (75.0, 125.0, 125.0, 175.0),
            (275.0, 325.0, 125.0, 175.0),
        ),
        (27,),
    ),
    31: (
        (
            (75.0, 125.0, 125.0, 175.0),
            (275.0, 325.0, 125.0, 175.0),
        ),
        (5, 10),
    ),
}


def _external_corpus_available() -> bool:
    return MANUAL_ROOT.exists() and BASELINE_PATH.exists()


def _manual_path(index: int) -> Path:
    return MANUAL_ROOT / f"Vaciado_{index:03d}.pgmx"


def _variant_path(index: int, tool_index: int) -> Path:
    return MANUAL_ROOT / f"Vaciado_{index:03d}_E{tool_index:03d}.pgmx"


def _assert_same_xyz(
    case: unittest.TestCase,
    actual: tuple[tuple[float, float, float], ...],
    expected: tuple[tuple[float, float, float], ...],
) -> None:
    case.assertEqual(len(actual), len(expected))
    for actual_point, expected_point in zip(actual, expected):
        case.assertTrue(
            all(
                math.isclose(a, e, abs_tol=1e-6)
                for a, e in zip(actual_point, expected_point)
            ),
            f"{actual_point} != {expected_point}",
    )


def _assert_same_xy(
    case: unittest.TestCase,
    actual: tuple[tuple[float, float], ...],
    expected: tuple[tuple[float, float], ...],
) -> None:
    case.assertEqual(len(actual), len(expected))
    for actual_point, expected_point in zip(actual, expected):
        case.assertTrue(
            all(
                math.isclose(a, e, abs_tol=1e-6)
                for a, e in zip(actual_point, expected_point)
            ),
            f"{actual_point} != {expected_point}",
        )


def _xy_bbox(points: tuple[tuple[float, float], ...]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (
        round(min(xs), 6),
        round(max(xs), 6),
        round(min(ys), 6),
        round(max(ys), 6),
    )


def _trajectory_arcs(adaptation) -> tuple[tuple[float, float, float], ...]:
    arcs: list[tuple[float, float, float]] = []
    for toolpath in adaptation.snapshot.operations[0].toolpaths:
        if toolpath.path_type != "TrajectoryPath" or not toolpath.curve:
            continue
        for serialization in toolpath.curve.member_serializations:
            parts = str(serialization).split()
            if len(parts) > 5 and parts[3] == "2":
                arcs.append(
                    (
                        round(float(parts[4]), 6),
                        round(float(parts[5]), 6),
                        round(float(parts[-1]), 6),
                    )
                )
    return tuple(arcs)


def _trajectory_xy_points(adaptation) -> tuple[tuple[float, float], ...]:
    points: list[tuple[float, float]] = []
    for sequence in _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0]):
        points.extend((round(x, 6), round(y, 6)) for x, y, _z in sequence)
    return tuple(points)


def _trajectory_primitive_counts(adaptation) -> tuple[tuple[int, int], ...]:
    counts: list[tuple[int, int]] = []
    for toolpath in adaptation.snapshot.operations[0].toolpaths:
        if toolpath.path_type != "TrajectoryPath" or toolpath.curve is None:
            continue
        lines = 0
        arcs = 0
        for serialization in toolpath.curve.member_serializations:
            primitive = sp._parse_geometry_primitive(serialization)
            if primitive is None:
                continue
            if primitive.primitive_type == "Line":
                lines += 1
            elif primitive.primitive_type == "Arc":
                arcs += 1
        counts.append((lines, arcs))
    return tuple(counts)


class VaciadoTraceEngineSkeletonTests(unittest.TestCase):
    def test_trace_engine_skeleton_preserves_contract_offsets_and_z_levels(self) -> None:
        strategy = sp.build_contour_parallel_milling_strategy_spec(
            rotation_direction="Clockwise",
            stroke_connection_strategy="Straghtline",
            inside_to_outside=False,
            overlap=0.25,
            allow_multiple_passes=True,
            axial_cutting_depth=4.0,
            axial_finish_cutting_depth=1.0,
        )
        spec = sp.PocketMillingSpec(
            contour_points=((0.0, 0.0), (100.0, 0.0), (100.0, 60.0), (0.0, 60.0)),
            tool_width=20.0,
            allowance_side=5.0,
            depth_spec=sp.MillingDepthSpec(target_depth=13.0),
            milling_strategy=strategy,
        )

        plan = generate_contour_parallel_pocket_trace(spec, surface_z=60.0)

        self.assertEqual(plan.outer.start_point, (0.0, 0.0))
        self.assertEqual(plan.outer.bbox, (0.0, 100.0, 0.0, 60.0))
        self.assertTrue(plan.outer.is_axis_aligned_rectangle)
        self.assertTrue(math.isclose(plan.parameters.effective_offset, 15.0, abs_tol=1e-6))
        self.assertTrue(math.isclose(plan.parameters.radial_step, 15.0, abs_tol=1e-6))
        self.assertEqual(plan.outer_offset_family.offsets, (15.0, 30.0))
        self.assertEqual(plan.depth_plan.cut_depths, (4.0, 8.0, 12.0, 13.0))
        self.assertEqual(plan.depth_plan.z_values, (56.0, 52.0, 48.0, 47.0))
        self.assertEqual(len(plan.primitive_sequences), 2)
        self.assertEqual(plan.primitive_sequences[0].offset, 15.0)
        self.assertEqual(plan.primitive_sequences[0].line_count, 4)
        self.assertEqual(plan.primitive_sequences[0].arc_count, 0)
        self.assertEqual(plan.primitive_sequences[1].offset, 30.0)
        self.assertFalse(plan.can_emit_trajectory)
        self.assertIn("topology_resolver", plan.pending_stages)
        self.assertIn("toolpath_emitter", plan.pending_stages)

    @unittest.skipUnless(
        _external_corpus_available(),
        f"Corpus externo de Vaciado no disponible en {EXTERNAL_ROOT}",
    )
    def test_trace_engine_skeleton_extracts_vaciado_027_e005_offset_families(self) -> None:
        adaptation = adapt_pgmx_path(_variant_path(27, 5))
        spec = adaptation.pocket_millings[0]

        plan = generate_contour_parallel_pocket_trace(spec, surface_z=adaptation.snapshot.state.depth)

        self.assertEqual(len(plan.internal_offset_families), 1)
        family = plan.internal_offset_families[0]
        self.assertEqual(family.offsets, (38.0, 76.0))
        self.assertEqual(family.complete_offsets, (38.0, 76.0))
        self.assertEqual(family.partial_offsets, ())
        self.assertTrue(family.bridge_offset is not None)
        self.assertTrue(math.isclose(family.bridge_offset, 114.0, abs_tol=1e-6))
        outer_sequences = tuple(sequence for sequence in plan.primitive_sequences if sequence.owner == "outer")
        self.assertEqual(tuple(sequence.offset for sequence in outer_sequences), (38.0, 76.0))
        self.assertEqual(tuple(sequence.line_count for sequence in outer_sequences), (4, 4))
        internal_sequences = tuple(sequence for sequence in plan.primitive_sequences if sequence.owner == "internal:1")
        self.assertEqual(tuple(sequence.offset for sequence in internal_sequences), (38.0, 76.0))
        self.assertEqual(tuple(sequence.arc_count for sequence in internal_sequences), (5, 5))
        self.assertEqual(tuple(sequence.line_count for sequence in internal_sequences), (4, 4))
        arc_centers = {
            primitive.center
            for sequence in internal_sequences
            for primitive in sequence.primitives
            if primitive.primitive_type == "Arc"
        }
        self.assertEqual(
            arc_centers,
            {
                (175.0, 125.0),
                (175.0, 175.0),
                (225.0, 125.0),
                (225.0, 175.0),
            },
        )
        self.assertEqual(plan.parameters.rotation_direction, "CounterClockwise")
        self.assertFalse(plan.parameters.inside_to_outside)
        self.assertEqual(plan.parameters.stroke_connection_strategy, "Straghtline")
        self.assertEqual(tuple(sequence.name for sequence in plan.resolved_sequences), ("single_seed_bridge_offsets",))
        self.assertEqual(tuple(len(sequence) for sequence in plan.trajectory_sequences), (68,))
        self.assertEqual(plan.resolved_sequences[0].line_count, 51)
        self.assertEqual(plan.resolved_sequences[0].arc_count, 16)
        _assert_same_xyz(
            self,
            plan.trajectory_sequences[0],
            _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])[0],
        )
        self.assertEqual(plan.pending_stages, ())
        self.assertTrue(plan.can_emit_trajectory)

    @unittest.skipUnless(
        _external_corpus_available(),
        f"Corpus externo de Vaciado no disponible en {EXTERNAL_ROOT}",
    )
    def test_trace_engine_resolves_vaciado_027_e002_single_partial_topology(self) -> None:
        adaptation = adapt_pgmx_path(_variant_path(27, 2))
        spec = adaptation.pocket_millings[0]

        plan = generate_contour_parallel_pocket_trace(spec, surface_z=adaptation.snapshot.state.depth)

        self.assertEqual(len(plan.internal_offset_families), 1)
        family = plan.internal_offset_families[0]
        self.assertEqual(family.complete_offsets, (50.0,))
        self.assertEqual(family.partial_offsets, (100.0,))
        self.assertIsNone(family.bridge_offset)
        self.assertEqual(tuple(sequence.name for sequence in plan.resolved_sequences), ("single_seed_single_partial_offset",))
        self.assertEqual(tuple(len(sequence) for sequence in plan.trajectory_sequences), (42,))
        self.assertEqual(plan.resolved_sequences[0].line_count, 30)
        self.assertEqual(plan.resolved_sequences[0].arc_count, 11)
        _assert_same_xyz(
            self,
            plan.trajectory_sequences[0],
            _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])[0],
        )
        self.assertEqual(plan.pending_stages, ())
        self.assertTrue(plan.can_emit_trajectory)

    @unittest.skipUnless(
        _external_corpus_available(),
        f"Corpus externo de Vaciado no disponible en {EXTERNAL_ROOT}",
    )
    def test_trace_engine_resolves_vaciado_027_e006_complete_loop_topology(self) -> None:
        adaptation = adapt_pgmx_path(_variant_path(27, 6))
        spec = adaptation.pocket_millings[0]

        plan = generate_contour_parallel_pocket_trace(spec, surface_z=adaptation.snapshot.state.depth)

        self.assertEqual(tuple(sequence.name for sequence in plan.resolved_sequences), (
            "outer_complete_offsets",
            "internal_complete_offsets",
        ))
        outer, internal = plan.resolved_sequences
        self.assertEqual(outer.line_count, 11)
        self.assertEqual(outer.arc_count, 0)
        self.assertEqual(outer.start, (-10.0, 310.0))
        self.assertEqual(outer.end, (30.0, 270.0))
        self.assertEqual(internal.line_count, 9)
        self.assertEqual(internal.arc_count, 10)
        self.assertEqual(internal.start, (135.0, 125.0))
        self.assertEqual(internal.end, (95.0, 125.0))
        self.assertEqual(tuple(len(sequence) for sequence in plan.trajectory_sequences), (12, 20))
        _assert_same_xyz(
            self,
            plan.trajectory_sequences[0],
            _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])[0],
        )
        _assert_same_xyz(
            self,
            plan.trajectory_sequences[1],
            _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])[1],
        )
        self.assertNotIn("topology_resolver", plan.pending_stages)
        self.assertNotIn("traversal_orderer", plan.pending_stages)
        self.assertNotIn("connector_planner", plan.pending_stages)
        self.assertEqual(plan.pending_stages, ())
        self.assertTrue(plan.can_emit_trajectory)

    @unittest.skipUnless(
        _external_corpus_available(),
        f"Corpus externo de Vaciado no disponible en {EXTERNAL_ROOT}",
    )
    def test_trace_engine_resolves_vaciado_027_dense_partial_bridge_topology(self) -> None:
        expectations = {
            3: {
                "complete_count": 18,
                "complete_tail": (76.16, 80.92, 85.68),
                "partial": (90.44, 95.2, 99.96, 104.72, 109.48),
                "bridge": 114.24,
                "trajectory_lengths": (515,),
                "primitive_counts": ((375, 139),),
            },
            4: {
                "complete_count": 43,
                "complete_tail": (82.0, 84.0, 86.0),
                "partial": (88.0, 90.0, 92.0, 94.0, 96.0, 98.0, 100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 112.0),
                "bridge": 114.0,
                "trajectory_lengths": (1185,),
                "primitive_counts": ((852, 332),),
            },
        }

        for tool_index, expected in expectations.items():
            with self.subTest(tool_index=tool_index):
                adaptation = adapt_pgmx_path(_variant_path(27, tool_index))
                spec = adaptation.pocket_millings[0]

                plan = generate_contour_parallel_pocket_trace(spec, surface_z=adaptation.snapshot.state.depth)

                self.assertEqual(len(plan.internal_offset_families), 1)
                family = plan.internal_offset_families[0]
                self.assertEqual(len(family.complete_offsets), expected["complete_count"])
                self.assertEqual(family.complete_offsets[-3:], expected["complete_tail"])
                self.assertEqual(family.partial_offsets, expected["partial"])
                self.assertTrue(family.bridge_offset is not None)
                self.assertTrue(math.isclose(family.bridge_offset, expected["bridge"], abs_tol=1e-6))
                self.assertEqual(
                    tuple(sequence.name for sequence in plan.resolved_sequences),
                    ("single_seed_dense_bridge_offsets",),
                )
                self.assertEqual(
                    tuple(len(sequence) for sequence in plan.trajectory_sequences),
                    expected["trajectory_lengths"],
                )
                self.assertEqual(
                    tuple((sequence.line_count, sequence.arc_count) for sequence in plan.resolved_sequences),
                    expected["primitive_counts"],
                )
                _assert_same_xyz(
                    self,
                    plan.trajectory_sequences[0],
                    _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])[0],
                )
                self.assertEqual(plan.pending_stages, ())
                self.assertTrue(plan.can_emit_trajectory)
                self.assertEqual(
                    tuple(len(sequence) for sequence in _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])),
                    expected["trajectory_lengths"],
                )
                self.assertEqual(_trajectory_primitive_counts(adaptation), expected["primitive_counts"])

    @unittest.skipUnless(
        _external_corpus_available(),
        f"Corpus externo de Vaciado no disponible en {EXTERNAL_ROOT}",
    )
    def test_trace_engine_resolves_vaciado_027_dense_partial_topology_without_bridge(self) -> None:
        expectations = {
            1: {
                "complete": (9.18, 18.36, 27.54, 36.72, 45.9, 55.08, 64.26, 73.44, 82.62),
                "partial": (91.8, 100.98, 110.16),
                "trajectory_lengths": (273,),
                "primitive_counts": ((200, 72),),
            },
            7: {
                "complete": (8.86, 17.72, 26.58, 35.44, 44.3, 53.16, 62.02, 70.88, 79.74),
                "partial": (88.6, 97.46, 106.32),
                "trajectory_lengths": (273,),
                "primitive_counts": ((196, 76),),
            },
        }

        for tool_index, expected in expectations.items():
            with self.subTest(tool_index=tool_index):
                adaptation = adapt_pgmx_path(_variant_path(27, tool_index))
                spec = adaptation.pocket_millings[0]

                plan = generate_contour_parallel_pocket_trace(spec, surface_z=adaptation.snapshot.state.depth)

                self.assertEqual(len(plan.internal_offset_families), 1)
                family = plan.internal_offset_families[0]
                self.assertEqual(family.complete_offsets, expected["complete"])
                self.assertEqual(family.partial_offsets, expected["partial"])
                self.assertIsNone(family.bridge_offset)
                self.assertEqual(
                    tuple(sequence.name for sequence in plan.resolved_sequences),
                    ("single_seed_dense_partial_offsets",),
                )
                self.assertEqual(
                    tuple(len(sequence) for sequence in plan.trajectory_sequences),
                    expected["trajectory_lengths"],
                )
                self.assertEqual(
                    tuple((sequence.line_count, sequence.arc_count) for sequence in plan.resolved_sequences),
                    expected["primitive_counts"],
                )
                _assert_same_xyz(
                    self,
                    plan.trajectory_sequences[0],
                    _actual_trajectory_xyz_sequences(adaptation.snapshot.operations[0])[0],
                )
                self.assertEqual(plan.pending_stages, ())
                self.assertTrue(plan.can_emit_trajectory)


class VaciadoIslandBaseLoopRuleTests(unittest.TestCase):
    def test_rounded_kernel_loop_rule_matches_observed_base_points(self) -> None:
        expected = (
            (135.0, 125.0),
            (135.0, 175.0),
            (175.0, 215.0),
            (225.0, 215.0),
            (253.2842712474619, 203.2842712474619),
            (265.0, 175.0),
            (265.0, 125.0),
            (225.0, 85.0),
            (175.0, 85.0),
            (135.0, 125.0),
        )
        generated = generate_rounded_kernel_loop_xy((175.0, 225.0, 125.0, 175.0), 40.0)
        _assert_same_xy(self, generated, expected)

        rule = infer_rounded_kernel_loop_xy(generated)
        self.assertIsNotNone(rule)
        assert rule is not None
        self.assertEqual(rule.kernel_bbox, (175.0, 225.0, 125.0, 175.0))
        self.assertTrue(math.isclose(rule.radius, 40.0, abs_tol=1e-6))
        self.assertTrue(math.isclose(rule.max_delta, 0.0, abs_tol=1e-6))


@unittest.skipUnless(
    _external_corpus_available(),
    f"Corpus externo de Vaciado no disponible en {EXTERNAL_ROOT}",
)
class VaciadoPocketMillingCorpusTests(unittest.TestCase):
    def test_rectangular_vaciados_roundtrip_and_match_trace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vaciado_roundtrip_") as temp_dir:
            temp_root = Path(temp_dir)

            for index in STABLE_RECTANGULAR_CASES:
                with self.subTest(index=index):
                    manual = _manual_path(index)
                    self.assertTrue(manual.exists(), manual)

                    manual_adaptation = adapt_pgmx_path(manual)
                    self.assertEqual(len(manual_adaptation.pocket_millings), 1)
                    self.assertEqual(len(manual_adaptation.unsupported_entries), 0)

                    spec = manual_adaptation.pocket_millings[0]
                    manual_operation = manual_adaptation.snapshot.operations[0]
                    manual_xyz = _actual_trajectory_xyz(manual_operation)
                    output = temp_root / f"Vaciado_{index:03d}_synth.pgmx"
                    request = manual_adaptation.build_synthesis_request(
                        output,
                        baseline_path=BASELINE_PATH,
                        source_pgmx_path=BASELINE_PATH,
                    )
                    sp.synthesize_request(request)

                    generated_adaptation = adapt_pgmx_path(output)
                    self.assertEqual(len(generated_adaptation.pocket_millings), 1)
                    self.assertEqual(len(generated_adaptation.unsupported_entries), 0)

                    generated_operation = generated_adaptation.snapshot.operations[0]
                    actual_xyz = _actual_trajectory_xyz(generated_operation)
                    _assert_same_xyz(self, actual_xyz, manual_xyz)

                    strategy = spec.milling_strategy
                    expected_xyz = generate_rectangular_contour_parallel_xyz_path(
                        length=manual_adaptation.snapshot.state.length,
                        width=manual_adaptation.snapshot.state.width,
                        depth=manual_adaptation.snapshot.state.depth,
                        contour_points=spec.contour_points,
                        tool_width=spec.tool_width,
                        target_depth=float(spec.depth_spec.target_depth or 0.0),
                        security_plane=spec.security_plane,
                        allowance_side=spec.allowance_side,
                        overlap=strategy.overlap,
                        radial_cutting_depth=strategy.radial_cutting_depth,
                        rotation_direction=strategy.rotation_direction,
                        inside_to_outside=strategy.inside_to_outside,
                        stroke_connection_strategy=strategy.stroke_connection_strategy,
                        allow_multiple_passes=strategy.allow_multiple_passes,
                        axial_cutting_depth=strategy.axial_cutting_depth,
                        axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
                    )
                    _assert_same_xyz(self, actual_xyz, expected_xyz)

    def test_island_contours_are_preserved_and_unsupported_cases_stay_blocked_for_synthesis(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vaciado_boss_guardrail_") as temp_dir:
            temp_root = Path(temp_dir)

            for index, (expected_boss_bboxes, expected_trajectory_counts) in ISLAND_CASES.items():
                with self.subTest(index=index):
                    manual = _manual_path(index)
                    self.assertTrue(manual.exists(), manual)

                    adaptation = adapt_pgmx_path(manual)
                    self.assertEqual(len(adaptation.pocket_millings), 1)
                    self.assertEqual(len(adaptation.unsupported_entries), 0)

                    spec = adaptation.pocket_millings[0]
                    self.assertTrue(spec.has_bosses)
                    self.assertEqual(
                        tuple(_xy_bbox(boss) for boss in spec.boss_contours),
                        expected_boss_bboxes,
                    )

                    operation = adaptation.snapshot.operations[0]
                    trajectory_sequences = _actual_trajectory_xyz_sequences(operation)
                    self.assertEqual(
                        tuple(len(sequence) for sequence in trajectory_sequences),
                        expected_trajectory_counts,
                    )
                    self.assertEqual(
                        len(_actual_trajectory_xyz(operation)),
                        sum(expected_trajectory_counts),
                    )

                    request = adaptation.build_synthesis_request(
                        temp_root / f"Vaciado_{index:03d}_synth.pgmx",
                        baseline_path=BASELINE_PATH,
                        source_pgmx_path=BASELINE_PATH,
                    )
                    if index in {22, 27}:
                        sp.synthesize_request(request)
                        generated_adaptation = adapt_pgmx_path(request.output_path)
                        generated_sequences = _actual_trajectory_xyz_sequences(
                            generated_adaptation.snapshot.operations[0]
                        )
                        self.assertEqual(
                            tuple(len(sequence) for sequence in generated_sequences),
                            expected_trajectory_counts,
                        )
                        self.assertEqual(
                            _trajectory_primitive_counts(generated_adaptation),
                            _trajectory_primitive_counts(adaptation),
                        )
                        for actual, expected in zip(generated_sequences, trajectory_sequences):
                            _assert_same_xyz(self, actual, expected)
                        continue

                    with self.assertRaisesRegex(
                        NotImplementedError,
                        "islas/BossGeometryList",
                    ):
                        sp.synthesize_request(request)

    def test_island_base_loop_rule_matches_vaciado_027_and_031(self) -> None:
        v027 = adapt_pgmx_path(_manual_path(27))
        v031 = adapt_pgmx_path(_manual_path(31))
        v027_sequences = _actual_trajectory_xyz_sequences(v027.snapshot.operations[0])
        v031_sequences = _actual_trajectory_xyz_sequences(v031.snapshot.operations[0])

        v027_base = v027_sequences[1][: len(v027_sequences[1]) // 2]
        v031_base = v031_sequences[1]
        generated = generate_rounded_kernel_loop_xy((175.0, 225.0, 125.0, 175.0), 40.0)

        _assert_same_xy(self, tuple((x, y) for x, y, _z in v027_base), generated)
        _assert_same_xy(self, tuple((x, y) for x, y, _z in v031_base), generated)

        v027_rule = infer_rounded_kernel_loop_xy(v027_base)
        v031_rule = infer_rounded_kernel_loop_xy(v031_base)
        self.assertIsNotNone(v027_rule)
        self.assertIsNotNone(v031_rule)
        assert v027_rule is not None
        assert v031_rule is not None
        self.assertEqual(v027_rule.kernel_bbox, v031_rule.kernel_bbox)
        self.assertTrue(math.isclose(v027_rule.radius, v031_rule.radius, abs_tol=1e-6))

    def test_boss_list_geometry_preserves_route_seed_distinct_from_boss_geometry(self) -> None:
        expected_ref_bboxes = {
            22: (("10748", (150.0, 250.0, 100.0, 200.0)),),
            27: (("10748", (175.0, 225.0, 125.0, 175.0)),),
            28: (("10748", (275.0, 325.0, 125.0, 175.0)),),
            30: (("13322", None), ("10748", (325.0, 375.0, 125.0, 175.0))),
            31: (("13322", None), ("10748", (175.0, 225.0, 125.0, 175.0))),
        }

        for index, expected in expected_ref_bboxes.items():
            with self.subTest(index=index):
                adaptation = adapt_pgmx_path(_manual_path(index))
                spec = adaptation.pocket_millings[0]
                actual = tuple(
                    (ref_id, _xy_bbox(contour) if contour else None)
                    for ref_id, contour in resolved_boss_ref_xy_contours(adaptation)
                )
                self.assertEqual(actual, expected)
                self.assertEqual(
                    tuple(
                        (seed.geometry_id, _xy_bbox(seed.contour_points) if seed.is_resolved else None)
                        for seed in spec.boss_route_seeds
                    ),
                    expected,
                )

    def test_tool_change_variants_materialize_route_seed_for_vaciado_030_and_031(self) -> None:
        expected_variant_bboxes = {
            30: (325.0, 375.0, 125.0, 175.0),
            31: (175.0, 225.0, 125.0, 175.0),
        }

        for index, expected_bbox in expected_variant_bboxes.items():
            base_sequences = _actual_trajectory_xyz_sequences(
                adapt_pgmx_path(_manual_path(index)).snapshot.operations[0]
            )
            for tool_index in range(1, 8):
                with self.subTest(index=index, tool_index=tool_index):
                    adaptation = adapt_pgmx_path(_variant_path(index, tool_index))
                    spec = adaptation.pocket_millings[0]
                    self.assertEqual((_xy_bbox(spec.boss_contours[0]),), (expected_bbox,))
                    self.assertEqual(
                        tuple(
                            (seed.geometry_id, _xy_bbox(seed.contour_points) if seed.is_resolved else None)
                            for seed in spec.boss_route_seeds
                        ),
                        (("10748", expected_bbox),),
                    )
                    self.assertEqual(
                        tuple(
                            (ref_id, _xy_bbox(contour) if contour else None)
                            for ref_id, contour in resolved_boss_ref_xy_contours(adaptation)
                        ),
                        (("10748", expected_bbox),),
                    )

                    strategy = spec.milling_strategy
                    self.assertTrue(
                        math.isclose(
                            strategy.radial_cutting_depth,
                            spec.tool_width * (1.0 - strategy.overlap),
                            abs_tol=1e-6,
                        )
                    )

                    variant_sequences = _actual_trajectory_xyz_sequences(
                        adaptation.snapshot.operations[0]
                    )
                    if tool_index == 6:
                        self.assertEqual(
                            tuple(len(sequence) for sequence in variant_sequences),
                            tuple(len(sequence) for sequence in base_sequences),
                        )
                        for actual, expected in zip(variant_sequences, base_sequences):
                            _assert_same_xyz(self, actual, expected)

    def test_vaciado_030_e004_extra_centers_are_step_sized_transition_arcs(self) -> None:
        adaptation = adapt_pgmx_path(_variant_path(30, 4))
        spec = adaptation.pocket_millings[0]
        strategy = spec.milling_strategy
        radial_step = spec.tool_width * (1.0 - strategy.overlap)
        self.assertTrue(math.isclose(radial_step, 2.0, abs_tol=1e-6))

        arcs = _trajectory_arcs(adaptation)
        self.assertEqual(arcs.count((203.0, 125.0, 2.0)), 1)
        self.assertEqual(arcs.count((203.0, 175.0, 2.0)), 1)
        self.assertEqual(
            tuple(arc for arc in arcs if arc[0] == 203.0),
            (
                (203.0, 125.0, round(radial_step, 6)),
                (203.0, 175.0, round(radial_step, 6)),
            ),
        )

        points = _trajectory_xy_points(adaptation)
        seed_left_x = 325.0
        seed_y_min = 125.0

        x_at_offset_122 = seed_left_x - math.sqrt((122.0**2) - ((seed_y_min - 122.0) ** 2))
        self.assertIn((round(x_at_offset_122, 6), 122.0), points)
        self.assertIn((203.0, 125.0), points)

        x_at_offset_120 = seed_left_x - math.sqrt((120.0**2) - ((seed_y_min - 120.0) ** 2))
        self.assertIn((round(x_at_offset_120, 6), 120.0), points)
        self.assertIn((325.0, 125.0, 120.0), arcs)

    def test_vaciado_031_e006_single_seed_synthesis_matches_trace(self) -> None:
        manual = _variant_path(31, 6)
        manual_adaptation = adapt_pgmx_path(manual)
        manual_sequences = _actual_trajectory_xyz_sequences(manual_adaptation.snapshot.operations[0])

        with tempfile.TemporaryDirectory(prefix="vaciado_031_e006_") as temp_dir:
            output = Path(temp_dir) / "Vaciado_031_E006_synth.pgmx"
            request = manual_adaptation.build_synthesis_request(
                output,
                baseline_path=BASELINE_PATH,
                source_pgmx_path=BASELINE_PATH,
            )
            sp.synthesize_request(request)

            generated_adaptation = adapt_pgmx_path(output)
            self.assertEqual(len(generated_adaptation.pocket_millings), 1)
            generated_spec = generated_adaptation.pocket_millings[0]
            self.assertEqual(
                tuple(_xy_bbox(boss) for boss in generated_spec.boss_contours),
                ((175.0, 225.0, 125.0, 175.0),),
            )
            self.assertEqual(
                tuple(
                    _xy_bbox(seed.contour_points)
                    for seed in generated_spec.boss_route_seeds
                    if seed.is_resolved
                ),
                ((175.0, 225.0, 125.0, 175.0),),
            )

            generated_sequences = _actual_trajectory_xyz_sequences(
                generated_adaptation.snapshot.operations[0]
            )
            self.assertEqual(
                tuple(len(sequence) for sequence in generated_sequences),
                (5, 10),
            )
            for actual, expected in zip(generated_sequences, manual_sequences):
                _assert_same_xyz(self, actual, expected)
            self.assertEqual(
                _trajectory_arcs(generated_adaptation),
                _trajectory_arcs(manual_adaptation),
            )

    def test_vaciado_031_e001_single_seed_multiloop_synthesis_matches_trace(self) -> None:
        expected_lengths = {
            1: (152,),
            2: (15,),
            3: (332,),
            4: (741,),
            5: (49,),
            7: (152,),
        }

        with tempfile.TemporaryDirectory(prefix="vaciado_031_e001_") as temp_dir:
            temp_root = Path(temp_dir)
            for tool_index, expected_length in expected_lengths.items():
                with self.subTest(tool_index=tool_index):
                    manual = _variant_path(31, tool_index)
                    manual_adaptation = adapt_pgmx_path(manual)
                    manual_sequences = _actual_trajectory_xyz_sequences(manual_adaptation.snapshot.operations[0])
                    output = temp_root / f"Vaciado_031_E{tool_index:03d}_synth.pgmx"
                    request = manual_adaptation.build_synthesis_request(
                        output,
                        baseline_path=BASELINE_PATH,
                        source_pgmx_path=BASELINE_PATH,
                    )
                    sp.synthesize_request(request)

                    generated_adaptation = adapt_pgmx_path(output)
                    generated_sequences = _actual_trajectory_xyz_sequences(
                        generated_adaptation.snapshot.operations[0]
                    )
                    self.assertEqual(tuple(len(sequence) for sequence in generated_sequences), expected_length)
                    _assert_same_xyz(self, generated_sequences[0], manual_sequences[0])
                    self.assertEqual(
                        _trajectory_arcs(generated_adaptation),
                        _trajectory_arcs(manual_adaptation),
                    )

    def test_vaciado_027_e006_single_seed_multi_base_loop_synthesis_matches_trace(self) -> None:
        manual_adaptation = adapt_pgmx_path(_variant_path(27, 6))
        manual_sequences = _actual_trajectory_xyz_sequences(manual_adaptation.snapshot.operations[0])

        with tempfile.TemporaryDirectory(prefix="vaciado_027_e006_") as temp_dir:
            output = Path(temp_dir) / "Vaciado_027_E006_synth.pgmx"
            request = manual_adaptation.build_synthesis_request(
                output,
                baseline_path=BASELINE_PATH,
                source_pgmx_path=BASELINE_PATH,
            )
            with mock.patch.object(
                sp,
                "_build_single_seed_base_loop_xyz_sequences",
                side_effect=AssertionError("legacy single-seed helper should not be used"),
            ):
                sp.synthesize_request(request)

            generated_adaptation = adapt_pgmx_path(output)
            generated_sequences = _actual_trajectory_xyz_sequences(
                generated_adaptation.snapshot.operations[0]
            )
            self.assertEqual(tuple(len(sequence) for sequence in generated_sequences), (12, 20))
            for actual, expected in zip(generated_sequences, manual_sequences):
                _assert_same_xyz(self, actual, expected)
            self.assertEqual(
                _trajectory_arcs(generated_adaptation),
                _trajectory_arcs(manual_adaptation),
            )
            self.assertEqual(
                _trajectory_primitive_counts(generated_adaptation),
                ((11, 0), (9, 10)),
            )
            self.assertEqual(
                _trajectory_primitive_counts(generated_adaptation),
                _trajectory_primitive_counts(manual_adaptation),
            )

    def test_vaciado_027_dense_partial_synthesis_uses_trace_engine(self) -> None:
        expected_lengths = {
            1: (273,),
            3: (515,),
            4: (1185,),
            7: (273,),
        }

        with tempfile.TemporaryDirectory(prefix="vaciado_027_dense_partial_") as temp_dir:
            temp_root = Path(temp_dir)
            for tool_index, expected_length in expected_lengths.items():
                with self.subTest(tool_index=tool_index):
                    manual_adaptation = adapt_pgmx_path(_variant_path(27, tool_index))
                    manual_sequences = _actual_trajectory_xyz_sequences(
                        manual_adaptation.snapshot.operations[0]
                    )
                    output = temp_root / f"Vaciado_027_E{tool_index:03d}_synth.pgmx"
                    request = manual_adaptation.build_synthesis_request(
                        output,
                        baseline_path=BASELINE_PATH,
                        source_pgmx_path=BASELINE_PATH,
                    )
                    with mock.patch.object(
                        sp,
                        "_build_single_seed_multiloop_curve_and_sequence",
                        side_effect=AssertionError("legacy single-seed multiloop helper should not be used"),
                    ):
                        sp.synthesize_request(request)

                    generated_adaptation = adapt_pgmx_path(output)
                    generated_sequences = _actual_trajectory_xyz_sequences(
                        generated_adaptation.snapshot.operations[0]
                    )
                    self.assertEqual(tuple(len(sequence) for sequence in generated_sequences), expected_length)
                    _assert_same_xyz(self, generated_sequences[0], manual_sequences[0])
                    self.assertEqual(
                        _trajectory_arcs(generated_adaptation),
                        _trajectory_arcs(manual_adaptation),
                    )
                    self.assertEqual(
                        _trajectory_primitive_counts(generated_adaptation),
                        _trajectory_primitive_counts(manual_adaptation),
                    )

    def test_vaciado_027_tool_series_trace_engine_synthesis_without_template(self) -> None:
        expected_lengths = {
            1: (273,),
            2: (42,),
            3: (515,),
            4: (1185,),
            5: (68,),
            6: (12, 20),
            7: (273,),
        }

        with tempfile.TemporaryDirectory(prefix="vaciado_027_trace_engine_series_") as temp_dir:
            temp_root = Path(temp_dir)
            with mock.patch.object(
                sp,
                "_build_single_seed_base_loop_xyz_sequences",
                side_effect=AssertionError("legacy single-seed base-loop helper should not be used"),
            ), mock.patch.object(
                sp,
                "_build_single_seed_multiloop_curve_and_sequence",
                side_effect=AssertionError("legacy single-seed multiloop helper should not be used"),
            ):
                for tool_index, expected_length in expected_lengths.items():
                    with self.subTest(tool_index=tool_index):
                        manual_adaptation = adapt_pgmx_path(_variant_path(27, tool_index))
                        manual_sequences = _actual_trajectory_xyz_sequences(
                            manual_adaptation.snapshot.operations[0]
                        )
                        output = temp_root / f"Vaciado_027_E{tool_index:03d}_synth.pgmx"
                        request = manual_adaptation.build_synthesis_request(
                            output,
                            baseline_path=BASELINE_PATH,
                            source_pgmx_path=BASELINE_PATH,
                        )
                        sp.synthesize_request(request)

                        generated_adaptation = adapt_pgmx_path(output)
                        generated_sequences = _actual_trajectory_xyz_sequences(
                            generated_adaptation.snapshot.operations[0]
                        )
                        self.assertEqual(tuple(len(sequence) for sequence in generated_sequences), expected_length)
                        for actual, expected in zip(generated_sequences, manual_sequences):
                            _assert_same_xyz(self, actual, expected)
                        self.assertEqual(
                            _trajectory_arcs(generated_adaptation),
                            _trajectory_arcs(manual_adaptation),
                        )
                        self.assertEqual(
                            _trajectory_primitive_counts(generated_adaptation),
                            _trajectory_primitive_counts(manual_adaptation),
                        )

    def test_vaciado_027_tool_series_template_trace_synthesis_matches_trace(self) -> None:
        expected_lengths = {
            1: (273,),
            2: (42,),
            3: (515,),
            4: (1185,),
            5: (68,),
            6: (12, 20),
            7: (273,),
        }

        with tempfile.TemporaryDirectory(prefix="vaciado_027_series_") as temp_dir:
            temp_root = Path(temp_dir)
            for tool_index, expected_length in expected_lengths.items():
                with self.subTest(tool_index=tool_index):
                    manual = _variant_path(27, tool_index)
                    manual_adaptation = adapt_pgmx_path(manual)
                    manual_sequences = _actual_trajectory_xyz_sequences(
                        manual_adaptation.snapshot.operations[0]
                    )
                    output = temp_root / f"Vaciado_027_E{tool_index:03d}_synth.pgmx"
                    request = manual_adaptation.build_synthesis_request(
                        output,
                        baseline_path=BASELINE_PATH,
                    )
                    sp.synthesize_request(request)

                    generated_adaptation = adapt_pgmx_path(output)
                    generated_sequences = _actual_trajectory_xyz_sequences(
                        generated_adaptation.snapshot.operations[0]
                    )
                    self.assertEqual(tuple(len(sequence) for sequence in generated_sequences), expected_length)
                    for actual, expected in zip(generated_sequences, manual_sequences):
                        _assert_same_xyz(self, actual, expected)
                    self.assertEqual(
                        _trajectory_arcs(generated_adaptation),
                        _trajectory_arcs(manual_adaptation),
                    )

    def test_pocket_template_trace_hydration_requires_full_trace_contract(self) -> None:
        manual = _variant_path(27, 1)
        manual_adaptation = adapt_pgmx_path(manual)
        spec = manual_adaptation.pocket_millings[0]
        template = sp._extract_pocket_milling_template(manual)

        self.assertTrue(sp._can_hydrate_pocket_template_trace(template, spec))

        strategy = spec.milling_strategy
        changed_rotation = replace(
            spec,
            milling_strategy=sp.build_contour_parallel_milling_strategy_spec(
                rotation_direction="Clockwise"
                if strategy.rotation_direction == "CounterClockwise"
                else "CounterClockwise",
                stroke_connection_strategy=strategy.stroke_connection_strategy,
                inside_to_outside=strategy.inside_to_outside,
                overlap=strategy.overlap,
                is_helic_strategy=strategy.is_helic_strategy,
                allow_multiple_passes=strategy.allow_multiple_passes,
                axial_cutting_depth=strategy.axial_cutting_depth,
                axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
                cutmode=strategy.cutmode,
                is_internal=strategy.is_internal,
                radial_cutting_depth=strategy.radial_cutting_depth,
                radial_finish_cutting_depth=strategy.radial_finish_cutting_depth,
                allows_bidirectional=strategy.allows_bidirectional,
                allows_finish_cutting=strategy.allows_finish_cutting,
            ),
        )
        self.assertFalse(sp._can_hydrate_pocket_template_trace(template, changed_rotation))

        changed_allowance = replace(spec, allowance_side=spec.allowance_side + 1.0)
        self.assertFalse(sp._can_hydrate_pocket_template_trace(template, changed_allowance))

        changed_depth = replace(
            spec,
            depth_spec=sp.build_milling_depth_spec(
                is_through=False,
                target_depth=float(spec.depth_spec.target_depth or 0.0) + 1.0,
            ),
        )
        self.assertFalse(sp._can_hydrate_pocket_template_trace(template, changed_depth))

    def test_vaciado_035_circular_helical_case_stays_outside_polyline_adapter(self) -> None:
        manual = _manual_path(35)
        self.assertTrue(manual.exists(), manual)

        adaptation = adapt_pgmx_path(manual)
        self.assertEqual(len(adaptation.pocket_millings), 0)
        self.assertEqual(len(adaptation.unsupported_entries), 1)

        feature = adaptation.snapshot.features[0]
        operation = adaptation.snapshot.operations[0]
        self.assertIn("ClosedPocket", feature.feature_type)
        self.assertEqual(feature.geometry_ref.id, "4561")
        geometry = adaptation.snapshot.geometry_by_id[feature.geometry_ref.id]
        self.assertEqual(geometry.geometry_type, "a:GeomCircle")
        self.assertTrue(operation.milling_strategy.is_helic_strategy)
        self.assertFalse(operation.milling_strategy.inside_to_outside)
        self.assertTrue(math.isclose(operation.allowance_side, 20.0, abs_tol=1e-6))
