from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import iso_state_synthesis as iso
from iso_state_synthesis.catalog import select_transition_id
from iso_state_synthesis.differential import evaluate_state_plan
from iso_state_synthesis.emitter import (
    ExplainedIsoLine,
    ExplainedIsoProgram,
    _line_milling_motion_line,
    _side_normal,
    _unit_vector,
    _xy_changed,
    compare_candidate_to_iso,
)
from iso_state_synthesis.model import (
    EvidenceSource,
    IsoStatePlan,
    StageDifferential,
    StateChange,
    StateStage,
    StateValue,
    StateVector,
    to_jsonable,
)


class IsoStateSynthesisModelTests(unittest.TestCase):
    def test_public_facade_exports_core_contracts(self) -> None:
        self.assertIs(iso.StateVector, StateVector)
        self.assertTrue(callable(iso.evaluate_state_plan))
        self.assertTrue(callable(iso.emit_candidate_from_evaluation))

    def test_state_vector_replace_and_jsonable_keep_addresses(self) -> None:
        source = EvidenceSource("test", "tests/test_iso_state_synthesis.py", "fixture")
        original_dx = StateValue("pieza", "dx", 100.0, source)
        replacement_dx = StateValue("pieza", "dx", 120.0, source)
        dy = StateValue("pieza", "dy", 50.0, source)

        vector = StateVector((original_dx,))
        replaced = vector.replace(replacement_dx, dy)

        self.assertEqual(replaced.get("pieza", "dx"), 120.0)
        self.assertEqual(replaced.get("pieza", "dy"), 50.0)
        self.assertEqual([value.address for value in replaced.values], ["pieza.dx", "pieza.dy"])
        self.assertEqual(
            to_jsonable(replaced)["values"][0]["source"]["path"],
            "tests/test_iso_state_synthesis.py",
        )

    def test_evaluate_state_plan_tracks_changes_forces_and_boring_speed_emit(self) -> None:
        source = EvidenceSource("test", "tests/test_iso_state_synthesis.py", "state")
        initial = StateVector(
            (
                StateValue("maquina", "boring_head_speed", 1000.0, source),
                StateValue("salida", "etk_17", 0, source),
                StateValue("pieza", "area", "HG", source),
            )
        )
        stage = StateStage(
            key="top_drill_prepare",
            family="top_drill",
            order_index=1,
            target_state=StateVector(
                (
                    StateValue("maquina", "boring_head_speed", 1500.0, source),
                    StateValue("pieza", "area", "HG", source, required=True),
                )
            ),
        )
        plan = IsoStatePlan(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=initial,
            stages=(stage,),
        )

        evaluation = evaluate_state_plan(plan)
        differential = evaluation.differentials[0]

        self.assertEqual(differential.change_count, 3)
        self.assertIn(
            ("maquina", "boring_head_speed", "set", 1500.0),
            {
                (change.layer, change.key, change.change_type, change.after)
                for change in differential.target_changes
            },
        )
        self.assertIn(
            ("salida", "etk_17", "emit", 257),
            {
                (change.layer, change.key, change.change_type, change.after)
                for change in differential.target_changes
            },
        )
        self.assertEqual(differential.forced_values[0].address, "pieza.area")


class IsoStateSynthesisCatalogTests(unittest.TestCase):
    def test_select_transition_id_uses_heads_and_router_tool_numbers(self) -> None:
        source = EvidenceSource("test", "tests/test_iso_state_synthesis.py", "transition")

        def prepare(tool_number: int) -> StageDifferential:
            return StageDifferential(
                stage_key="line_milling_prepare",
                family="line_milling",
                order_index=0,
                target_changes=(
                    StateChange(
                        "herramienta",
                        "tool_number",
                        None,
                        tool_number,
                        "set",
                        source,
                    ),
                ),
            )

        self.assertEqual(
            select_transition_id("line_milling", prepare(4), "profile_milling", prepare(4)),
            "T-RH-001",
        )
        self.assertEqual(
            select_transition_id("line_milling", prepare(4), "profile_milling", prepare(1)),
            "T-RH-002",
        )
        self.assertEqual(
            select_transition_id("line_milling", prepare(4), "top_drill", prepare(4)),
            "T-XH-001",
        )


class IsoStateSynthesisEmitterTests(unittest.TestCase):
    def test_explained_program_writes_text_and_comparison_normalizes_iso_lines(self) -> None:
        source = EvidenceSource("test", "tests/test_iso_state_synthesis.py", "line")
        program = ExplainedIsoProgram(
            source_path=Path("fixture.pgmx"),
            program_name="fixture",
            lines=(
                ExplainedIsoLine("% fixture.pgm", "program_header", source),
                ExplainedIsoLine("G0   X1.000   Y2.000", "trace", source),
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            expected = tmp_path / "fixture.iso"
            output = tmp_path / "candidate.iso"
            expected.write_text("% maestro.pgm\r\nG0 X1.000 Y2.000\r\n", encoding="utf-8")
            program.write_text(output)

            self.assertEqual(output.read_text(encoding="utf-8"), program.text())
            result = compare_candidate_to_iso(expected, program)

        self.assertTrue(result.equal)
        self.assertEqual(result.difference_count, 0)
        self.assertEqual(result.expected_line_count, 2)
        self.assertEqual(result.actual_line_count, 2)

    def test_xy_changed_detects_single_axis_motion(self) -> None:
        self.assertFalse(_xy_changed(0.0, 0.0, SimpleNamespace(x=0.0001, y=0.0001)))
        self.assertTrue(_xy_changed(0.0, 0.0, SimpleNamespace(x=1.0, y=0.0)))
        self.assertTrue(_xy_changed(0.0, 0.0, SimpleNamespace(x=0.0, y=1.0)))
        self.assertTrue(_xy_changed(0.0, 0.0, SimpleNamespace(x=1.0, y=1.0)))

    def test_line_milling_motion_line_emits_only_changed_axes(self) -> None:
        self.assertEqual(
            _line_milling_motion_line(
                10.0,
                5.0,
                -3.0,
                10.0,
                0.0,
                -3.0,
                200.0,
                always_include_z=False,
            ),
            "G1 Y5.000 F200.000",
        )
        self.assertEqual(
            _line_milling_motion_line(
                10.0,
                5.0,
                -4.0,
                10.0,
                5.0,
                -3.0,
                200.0,
                always_include_z=False,
            ),
            "G1 Z-4.000 F200.000",
        )

    def test_vector_helpers_define_profile_side_geometry(self) -> None:
        self.assertEqual(_unit_vector((0.0, 0.0), (3.0, 4.0)), (0.6, 0.8))
        self.assertEqual(_side_normal(0.6, 0.8, "Left"), (-0.8, 0.6))
        self.assertEqual(_side_normal(0.6, 0.8, "Right"), (0.8, -0.6))
        with self.assertRaisesRegex(Exception, "longitud cero"):
            _unit_vector((1.0, 1.0), (1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
