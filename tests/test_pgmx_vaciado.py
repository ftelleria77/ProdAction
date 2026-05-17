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
    generate_rectangular_contour_parallel_xyz_path,
)


MANUAL_ROOT = EXTERNAL_ROOT / "manual"
BASELINE_PATH = EXTERNAL_ROOT / "Vaciado_000.pgmx"
STABLE_RECTANGULAR_CASES = (
    tuple(range(1, 22))
    + tuple(range(23, 27))
    + tuple(range(32, 36))
)


def _external_corpus_available() -> bool:
    return MANUAL_ROOT.exists() and BASELINE_PATH.exists()


def _manual_path(index: int) -> Path:
    return MANUAL_ROOT / f"Vaciado_{index:03d}.pgmx"


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
        manual = _manual_path(22)
        self.assertTrue(manual.exists(), manual)

        adaptation = adapt_pgmx_path(manual)
        self.assertEqual(len(adaptation.pocket_millings), 1)
        self.assertEqual(len(adaptation.unsupported_entries), 0)

        spec = adaptation.pocket_millings[0]
        self.assertTrue(spec.has_bosses)
        self.assertEqual(len(spec.boss_contours), 1)

        boss = spec.boss_contours[0]
        xs = [point[0] for point in boss]
        ys = [point[1] for point in boss]
        self.assertEqual((min(xs), max(xs)), (150.0, 250.0))
        self.assertEqual((min(ys), max(ys)), (100.0, 200.0))

        with tempfile.TemporaryDirectory(prefix="vaciado_boss_guardrail_") as temp_dir:
            request = adaptation.build_synthesis_request(
                Path(temp_dir) / "Vaciado_022_blocked.pgmx",
                baseline_path=BASELINE_PATH,
                source_pgmx_path=BASELINE_PATH,
            )
            with self.assertRaisesRegex(
                NotImplementedError,
                "islas/BossGeometryList",
            ):
                sp.synthesize_request(request)
