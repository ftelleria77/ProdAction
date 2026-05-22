from __future__ import annotations

import math
import tempfile
import unittest
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


MANUAL_ROOT = EXTERNAL_ROOT / "manual"
BASELINE_PATH = EXTERNAL_ROOT / "Vaciado_000.pgmx"
STABLE_RECTANGULAR_CASES = (
    tuple(range(1, 22))
    + tuple(range(23, 27))
    + tuple(range(32, 36))
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

    def test_island_contours_are_preserved_and_stay_blocked_for_synthesis(self) -> None:
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
                        temp_root / f"Vaciado_{index:03d}_blocked.pgmx",
                        baseline_path=BASELINE_PATH,
                        source_pgmx_path=BASELINE_PATH,
                    )
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
