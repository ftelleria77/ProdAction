from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import iso_state_synthesis as iso
from iso_state_synthesis.catalog import select_transition_id
from iso_state_synthesis.differential import evaluate_state_plan
from iso_state_synthesis.emitter import (
    ExplainedIsoLine,
    ExplainedIsoProgram,
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


if __name__ == "__main__":
    unittest.main()
