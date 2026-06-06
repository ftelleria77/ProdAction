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
    _closed_polyline_center_lead_geometry,
    _line_milling_motion_line,
    _line_milling_no_lead_side_compensation_motion_lines,
    _line_milling_open_polyline_side_compensation_motion_lines,
    _line_milling_trace_context,
    _line_milling_trace_modes,
    _linear_profile_program_point,
    _linear_profile_tangent_axis,
    _no_lead_compensation_points,
    _open_polyline_center_lead_geometry,
    _plan_work_groups,
    _polyline_side_compensation_leads,
    _side_normal,
    _trace_move_tangent_unit,
    _trace_point_tangent,
    _unit_vector,
    _work_stage_groups,
    _xy_changed,
    compare_candidate_to_iso,
)
from iso_state_synthesis.model import (
    EvidenceSource,
    IsoStateEvaluation,
    IsoStatePlan,
    StageDifferential,
    StateChange,
    StateStage,
    StateValue,
    StateVector,
    TraceMove,
    TracePoint,
    to_jsonable,
)


_TEST_SOURCE = EvidenceSource("test", "tests/test_iso_state_synthesis.py", "dispatcher")


def _stage_differential(
    stage_key: str,
    family: str,
    order_index: int,
    *,
    tool_number: int | None = None,
) -> StageDifferential:
    target_changes: tuple[StateChange, ...] = ()
    if tool_number is not None:
        target_changes = (
            StateChange(
                "herramienta",
                "tool_number",
                None,
                tool_number,
                "set",
                _TEST_SOURCE,
            ),
        )
    return StageDifferential(
        stage_key=stage_key,
        family=family,
        order_index=order_index,
        target_changes=target_changes,
    )


def _work_triple(
    family: str,
    start_order: int,
    *,
    tool_number: int | None = None,
) -> tuple[StageDifferential, StageDifferential, StageDifferential]:
    return (
        _stage_differential(f"{family}_prepare", family, start_order, tool_number=tool_number),
        _stage_differential(f"{family}_trace", family, start_order + 1),
        _stage_differential(f"{family}_reset", family, start_order + 2),
    )


def _trace_points(*points: tuple[float, float]) -> SimpleNamespace:
    return SimpleNamespace(points=tuple(SimpleNamespace(x=x, y=y) for x, y in points))


def _trace_move(name: str, *points: tuple[float, float, float]) -> TraceMove:
    return TraceMove(
        name=name,
        points=tuple(
            TracePoint(x=x, y=y, local_z=z, iso_z=z, source=_TEST_SOURCE)
            for x, y, z in points
        ),
        source=_TEST_SOURCE,
    )


def _change(layer: str, key: str, after: object) -> StateChange:
    return StateChange(layer, key, None, after, "set", _TEST_SOURCE)


def _line_milling_test_context(
    *,
    profile_family: str,
    side_of_feature: str,
    contour_points: tuple[tuple[float, float], ...],
    profile_winding: str = "",
    circle_center_x: float | None = None,
    circle_center_y: float | None = None,
    cut_z: float = -8.0,
    approach_type: str = "Line",
    approach_radius_multiplier: float = 2.0,
    lead_paths: bool = False,
) -> object:
    optional_circle_changes: tuple[StateChange, ...] = ()
    if circle_center_x is not None and circle_center_y is not None:
        optional_circle_changes = (
            _change("movimiento", "circle_center_x", circle_center_x),
            _change("movimiento", "circle_center_y", circle_center_y),
        )
    first_x, first_y = contour_points[0]
    last_x, last_y = contour_points[-1]
    approach_move = (
        _trace_move("Approach", (first_x - 2.0, first_y, 5.0), (first_x, first_y, cut_z))
        if lead_paths
        else _trace_move("Approach", (first_x, first_y, 5.0))
    )
    lift_move = (
        _trace_move("Lift", (last_x, last_y, cut_z), (last_x + 2.0, last_y, 5.0))
        if lead_paths
        else _trace_move("Lift", (last_x, last_y, 5.0))
    )
    differential = StageDifferential(
        stage_key="line_milling_trace",
        family="line_milling",
        order_index=1,
        target_changes=(
            _change("movimiento", "start_x", contour_points[0][0]),
            _change("movimiento", "start_y", contour_points[0][1]),
            _change("movimiento", "end_x", contour_points[-1][0]),
            _change("movimiento", "end_y", contour_points[-1][1]),
            _change("movimiento", "rapid_z", 30.0),
            _change("movimiento", "cut_z", cut_z),
            _change("movimiento", "security_z", 5.0),
            _change("movimiento", "plunge_feed", 120.0),
            _change("movimiento", "milling_feed", 600.0),
            _change("movimiento", "profile_family", profile_family),
            _change("movimiento", "profile_winding", profile_winding),
            _change("movimiento", "contour_points", contour_points),
            *optional_circle_changes,
            _change("herramienta", "tool_radius", 2.0),
            _change("herramienta", "tool_offset_length", 107.2),
            _change("trabajo", "side_of_feature", side_of_feature),
            _change("trabajo", "approach_type", approach_type),
            _change("trabajo", "approach_radius_multiplier", approach_radius_multiplier),
        ),
        trace=(
            approach_move,
            _trace_move(
                "TrajectoryPath",
                *((point[0], point[1], cut_z) for point in contour_points),
            ),
            lift_move,
        ),
    )
    evaluation = IsoStateEvaluation(
        source_path=Path("fixture.pgmx"),
        project_name="Fixture",
        initial_state=StateVector(
            (
                StateValue("pieza", "depth", 18.0, _TEST_SOURCE),
                StateValue("pieza", "length", 200.0, _TEST_SOURCE),
                StateValue("pieza", "width", 100.0, _TEST_SOURCE),
            )
        ),
        differentials=(differential,),
        final_state=StateVector(),
    )
    return _line_milling_trace_context(evaluation, differential)


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


class IsoStateSynthesisEmitterDispatcherTests(unittest.TestCase):
    def test_work_stage_groups_ignores_common_stages_and_links_router_to_boring_head(self) -> None:
        line = _work_triple("line_milling", 2, tool_number=4)
        profile = _work_triple("profile_milling", 5, tool_number=4)
        top_drill = _work_triple("top_drill", 8)
        ordered_differentials = [
            _stage_differential("program_header", "program", 0),
            _stage_differential("machine_preamble", "program", 1),
            *line,
            *profile,
            *top_drill,
            _stage_differential("program_close", "program", 11),
        ]

        groups = _work_stage_groups(ordered_differentials)

        self.assertEqual(
            [group.family for group in groups],
            ["line_milling", "profile_milling", "top_drill"],
        )
        self.assertIsNone(groups[0].incoming_transition_id)
        self.assertEqual(groups[0].outgoing_transition_id, "T-RH-001")
        self.assertEqual(groups[1].incoming_transition_id, "T-RH-001")
        self.assertEqual(groups[1].outgoing_transition_id, "T-XH-001")
        self.assertEqual(groups[2].incoming_transition_id, "T-XH-001")
        self.assertIsNone(groups[2].outgoing_transition_id)
        self.assertIs(groups[0].prepare, line[0])
        self.assertIs(groups[1].trace, profile[1])
        self.assertIs(groups[2].reset, top_drill[2])

    def test_work_stage_groups_rejects_incomplete_or_misordered_groups(self) -> None:
        line = _work_triple("line_milling", 0, tool_number=4)

        self.assertEqual(_work_stage_groups([line[0], line[1]]), ())
        self.assertEqual(_work_stage_groups([line[0], line[2], line[1]]), ())
        self.assertEqual(
            _work_stage_groups(
                [
                    _stage_differential("top_drill_prepare", "top_drill", 0),
                    _stage_differential("slot_milling_trace", "slot_milling", 1),
                    _stage_differential("top_drill_reset", "top_drill", 2),
                ]
            ),
            (),
        )

    def test_plan_work_groups_selects_boring_head_slot_transitions(self) -> None:
        top = _work_triple("top_drill", 0)
        slot = _work_triple("slot_milling", 3)
        side = _work_triple("side_drill", 6)
        second_slot = _work_triple("slot_milling", 9)

        groups = _plan_work_groups(
            (
                ("top_drill", *top),
                ("slot_milling", *slot),
                ("side_drill", *side),
                ("slot_milling", *second_slot),
            )
        )

        self.assertEqual(
            [group.incoming_transition_id for group in groups],
            [None, "T-BH-005", "T-BH-008", "T-BH-007"],
        )
        self.assertEqual(
            [group.outgoing_transition_id for group in groups],
            ["T-BH-005", "T-BH-008", "T-BH-007", None],
        )

    def test_plan_work_groups_selects_router_tool_change_and_head_switches(self) -> None:
        line = _work_triple("line_milling", 0, tool_number=4)
        profile = _work_triple("profile_milling", 3, tool_number=1)
        side = _work_triple("side_drill", 6)
        second_line = _work_triple("line_milling", 9, tool_number=1)

        groups = _plan_work_groups(
            (
                ("line_milling", *line),
                ("profile_milling", *profile),
                ("side_drill", *side),
                ("line_milling", *second_line),
            )
        )

        self.assertEqual(
            [group.incoming_transition_id for group in groups],
            [None, "T-RH-002", "T-XH-001", "T-XH-002"],
        )
        self.assertEqual(
            [group.outgoing_transition_id for group in groups],
            ["T-RH-002", "T-XH-001", "T-XH-002", None],
        )


class IsoStateSynthesisLineMillingGeometryTests(unittest.TestCase):
    def test_line_milling_trace_context_reads_state_and_modes(self) -> None:
        differential = StageDifferential(
            stage_key="line_milling_trace",
            family="line_milling",
            order_index=1,
            target_changes=(
                _change("movimiento", "start_x", 10.0),
                _change("movimiento", "start_y", 20.0),
                _change("movimiento", "end_x", 110.0),
                _change("movimiento", "end_y", 20.0),
                _change("movimiento", "rapid_z", 30.0),
                _change("movimiento", "cut_z", -8.0),
                _change("movimiento", "security_z", 5.0),
                _change("movimiento", "plunge_feed", 120.0),
                _change("movimiento", "milling_feed", 600.0),
                _change("movimiento", "profile_family", "OpenPolyline"),
                _change("movimiento", "profile_winding", "CounterClockwise"),
                _change("movimiento", "contour_points", ((10.0, 20.0), (110.0, 20.0))),
                _change("herramienta", "tool_radius", 2.0),
                _change("herramienta", "tool_offset_length", 107.2),
                _change("trabajo", "side_of_feature", "Left"),
                _change("trabajo", "approach_type", "Arc"),
                _change("trabajo", "approach_radius_multiplier", 3.0),
                _change("trabajo", "retract_radius_multiplier", 4.0),
            ),
            trace=(
                _trace_move("Approach", (4.0, 26.0, 5.0), (10.0, 20.0, -8.0)),
                _trace_move("TrajectoryPath", (10.0, 20.0, -8.0), (110.0, 20.0, -8.0)),
                _trace_move("Lift", (110.0, 20.0, -8.0), (116.0, 26.0, 5.0)),
            ),
        )
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(
                (
                    StateValue("pieza", "depth", 18.0, _TEST_SOURCE),
                    StateValue("pieza", "length", 200.0, _TEST_SOURCE),
                    StateValue("pieza", "width", 100.0, _TEST_SOURCE),
                )
            ),
            differentials=(differential,),
            final_state=StateVector(
                (
                    StateValue("trabajo", "strategy", "", _TEST_SOURCE),
                    StateValue("trabajo", "approach_mode", "Down", _TEST_SOURCE),
                    StateValue("trabajo", "retract_type", "Line", _TEST_SOURCE),
                    StateValue("trabajo", "retract_mode", "Up", _TEST_SOURCE),
                )
            ),
        )

        context = _line_milling_trace_context(evaluation, differential)

        self.assertEqual(context.start_x, 10.0)
        self.assertEqual(context.end_x, 110.0)
        self.assertEqual(context.tool_radius, 2.0)
        self.assertEqual(context.tool_offset, 107.2)
        self.assertEqual(context.side_of_feature, "Left")
        self.assertEqual(context.approach_type, "Arc")
        self.assertEqual(context.approach_mode, "Down")
        self.assertEqual(context.retract_type, "Line")
        self.assertEqual(context.retract_mode, "Up")
        self.assertEqual(context.approach_radius_multiplier, 3.0)
        self.assertEqual(context.retract_radius_multiplier, 4.0)
        self.assertEqual(context.nominal_points, ((10.0, 20.0), (110.0, 20.0)))
        self.assertFalse(context.open_polyline_outside_piece)
        self.assertIs(context.approach, differential.trace[0])
        self.assertTrue(context.modes.has_lead_paths)
        self.assertTrue(context.modes.uses_side_compensation)
        self.assertFalse(context.modes.uses_open_center_leads)

    def test_line_milling_trace_modes_detects_center_lead_families(self) -> None:
        approach = _trace_points((0.0, 0.0), (2.0, 0.0))
        lift = _trace_points((10.0, 0.0), (12.0, 0.0))

        open_modes = _line_milling_trace_modes(
            approach=approach,
            lift=lift,
            strategy_name="",
            side_of_feature="Center",
            profile_family="OpenPolyline",
        )
        circle_modes = _line_milling_trace_modes(
            approach=approach,
            lift=lift,
            strategy_name="",
            side_of_feature="Center",
            profile_family="Circle",
        )
        closed_modes = _line_milling_trace_modes(
            approach=approach,
            lift=lift,
            strategy_name="",
            side_of_feature="Center",
            profile_family="ClosedPolylineMidEdgeStart",
        )

        self.assertTrue(open_modes.has_lead_paths)
        self.assertTrue(open_modes.uses_open_center_leads)
        self.assertFalse(open_modes.uses_center_circle_leads)
        self.assertTrue(circle_modes.uses_center_circle_leads)
        self.assertTrue(closed_modes.uses_closed_center_leads)

    def test_line_milling_trace_modes_detects_side_compensation_paths(self) -> None:
        lead_modes = _line_milling_trace_modes(
            approach=_trace_points((0.0, 0.0), (2.0, 0.0)),
            lift=_trace_points((10.0, 0.0), (12.0, 0.0)),
            strategy_name="",
            side_of_feature="Left",
            profile_family="OpenPolyline",
        )
        no_lead_modes = _line_milling_trace_modes(
            approach=_trace_points((0.0, 0.0), (0.0, 0.0)),
            lift=_trace_points((10.0, 0.0), (10.0, 0.0)),
            strategy_name="",
            side_of_feature="Right",
            profile_family="Line",
        )

        self.assertTrue(lead_modes.uses_side_compensation)
        self.assertFalse(lead_modes.uses_no_lead_side_compensation)
        self.assertFalse(no_lead_modes.has_lead_paths)
        self.assertFalse(no_lead_modes.uses_side_compensation)
        self.assertTrue(no_lead_modes.uses_no_lead_side_compensation)

    def test_line_milling_trace_modes_suppresses_compensation_when_strategy_is_active(self) -> None:
        modes = _line_milling_trace_modes(
            approach=_trace_points((0.0, 0.0), (2.0, 0.0)),
            lift=_trace_points((10.0, 0.0), (12.0, 0.0)),
            strategy_name="Unidirectional",
            side_of_feature="Left",
            profile_family="OpenPolyline",
        )

        self.assertTrue(modes.has_lead_paths)
        self.assertFalse(modes.uses_side_compensation)
        self.assertFalse(modes.uses_no_lead_side_compensation)
        self.assertFalse(modes.uses_open_center_leads)

    def test_linear_profile_axis_and_tangent_helpers(self) -> None:
        self.assertEqual(_linear_profile_tangent_axis(((0.0, 0.0), (10.0, 2.0))), "X")
        self.assertEqual(_linear_profile_tangent_axis(((0.0, 0.0), (2.0, 10.0))), "Y")
        self.assertEqual(
            _linear_profile_program_point(((5.0, 7.0), (15.0, 7.0)), 9.0, "X"),
            (9.0, 7.0),
        )
        self.assertEqual(
            _linear_profile_program_point(((5.0, 7.0), (5.0, 17.0)), 9.0, "Y"),
            (5.0, 9.0),
        )
        self.assertEqual(_trace_point_tangent(SimpleNamespace(x=3.0), "X"), 3.0)
        with self.assertRaisesRegex(Exception, "no contiene eje X"):
            _trace_point_tangent(SimpleNamespace(y=3.0), "X")
        with self.assertRaisesRegex(Exception, "puntos suficientes"):
            _linear_profile_tangent_axis(((0.0, 0.0),))

    def test_trace_move_tangent_unit_detects_direction(self) -> None:
        forward = SimpleNamespace(points=(SimpleNamespace(x=0.0), SimpleNamespace(x=5.0)))
        backward = SimpleNamespace(points=(SimpleNamespace(x=5.0), SimpleNamespace(x=0.0)))
        flat = SimpleNamespace(points=(SimpleNamespace(x=5.0), SimpleNamespace(x=5.0)))

        self.assertEqual(_trace_move_tangent_unit(forward, "X"), 1.0)
        self.assertEqual(_trace_move_tangent_unit(backward, "X"), -1.0)
        with self.assertRaisesRegex(Exception, "no desplaza"):
            _trace_move_tangent_unit(flat, "X")

    def test_no_lead_compensation_points_adds_short_entry_and_exit_extensions(self) -> None:
        self.assertEqual(
            _no_lead_compensation_points(
                ((10.0, 10.0), (20.0, 10.0)),
                2.0,
                "OpenPolyline",
                "",
            ),
            ((9.0, 10.0), (21.0, 10.0)),
        )
        self.assertEqual(
            _no_lead_compensation_points(
                ((10.0, 10.0), (20.0, 10.0)),
                2.0,
                "Circle",
                "CounterClockwise",
            ),
            ((10.0, 9.0), (20.0, 11.0)),
        )

    def test_no_lead_side_compensation_builder_emits_linear_profile(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Right",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
        )

        self.assertTrue(context.modes.uses_no_lead_side_compensation)
        self.assertEqual(
            _line_milling_no_lead_side_compensation_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G42",
                "G1 X10.000 Y20.000 Z5.000 F120.000",
                "G1 Z-8.000 F120.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G1 Z5.000 F600.000",
                "G40",
                "G1 X111.000 Y20.000 Z5.000 F600.000",
            ),
        )

    def test_no_lead_side_compensation_builder_emits_circle_arcs(self) -> None:
        context = _line_milling_test_context(
            profile_family="Circle",
            side_of_feature="Left",
            contour_points=((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)),
            profile_winding="CounterClockwise",
            circle_center_x=15.0,
            circle_center_y=15.0,
        )

        self.assertTrue(context.modes.uses_no_lead_side_compensation)
        self.assertEqual(
            _line_milling_no_lead_side_compensation_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G41",
                "G1 X10.000 Y10.000 Z5.000 F120.000",
                "G1 Z-8.000 F120.000",
                "G3 X20.000 Y20.000 I15.000 J15.000 F600.000",
                "G1 Z5.000 F600.000",
                "G40",
                "G1 X10.000 Y21.000 Z5.000 F600.000",
            ),
        )

    def test_open_polyline_side_compensation_builder_emits_line_leads(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Right",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            approach_type="Line",
            approach_radius_multiplier=2.0,
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_side_compensation)
        self.assertEqual(
            _line_milling_open_polyline_side_compensation_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G42",
                "G1 X6.000 Y20.000 Z5.000 F120.000",
                "G1 X10.000 Z-8.000 F120.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G1 X114.000 Z5.000 F600.000",
                "G40",
                "G1 X115.000 Y20.000 Z5.000 F600.000",
            ),
        )

    def test_open_polyline_side_compensation_builder_emits_arc_leads(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Left",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            approach_type="Arc",
            approach_radius_multiplier=2.0,
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_side_compensation)
        self.assertEqual(
            _line_milling_open_polyline_side_compensation_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G41",
                "G1 X6.000 Y24.000 Z5.000 F120.000",
                "G3 X10.000 Y20.000 Z-8.000 I10.000 J24.000 F120.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G3 X114.000 Y24.000 Z5.000 I110.000 J24.000 F600.000",
                "G40",
                "G1 X114.000 Y25.000 Z5.000 F600.000",
            ),
        )

    def test_polyline_side_compensation_leads_support_line_and_arc(self) -> None:
        self.assertEqual(
            _polyline_side_compensation_leads(
                ((10.0, 10.0), (20.0, 10.0)),
                tool_radius=2.0,
                side_of_feature="Left",
                approach_type="Arc",
                radius_multiplier=2.0,
            ),
            {
                "entry_rapid": (6.0, 15.0),
                "entry": (6.0, 14.0),
                "entry_center": (10.0, 14.0),
                "exit": (24.0, 14.0),
                "exit_center": (20.0, 14.0),
                "exit_rapid": (24.0, 15.0),
            },
        )
        self.assertEqual(
            _polyline_side_compensation_leads(
                ((10.0, 10.0), (20.0, 10.0)),
                tool_radius=2.0,
                side_of_feature="Left",
                approach_type="Line",
                radius_multiplier=2.0,
            ),
            {
                "entry_rapid": (5.0, 10.0),
                "entry": (6.0, 10.0),
                "exit": (24.0, 10.0),
                "exit_rapid": (25.0, 10.0),
            },
        )

    def test_center_lead_geometry_for_open_and_closed_polylines(self) -> None:
        self.assertEqual(
            _closed_polyline_center_lead_geometry(
                ((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)),
                lead_distance=2.0,
                lead_type="Arc",
                winding="CounterClockwise",
            ),
            {
                "rapid": (8.0, 12.0),
                "exit": (12.0, 12.0),
                "approach_center": (10.0, 12.0),
                "retract_center": (10.0, 12.0),
            },
        )
        self.assertEqual(
            _open_polyline_center_lead_geometry(
                ((10.0, 10.0), (20.0, 10.0)),
                lead_distance=2.0,
                lead_type="Arc",
            ),
            {
                "rapid": (8.0, 12.0),
                "exit": (22.0, 12.0),
                "approach_center": (10.0, 12.0),
                "retract_center": (20.0, 12.0),
            },
        )
        self.assertEqual(
            _open_polyline_center_lead_geometry(
                ((10.0, 10.0), (20.0, 10.0)),
                lead_distance=2.0,
                lead_type="Line",
            ),
            {
                "rapid": (8.0, 10.0),
                "exit": (22.0, 10.0),
                "approach_center": (10.0, 10.0),
                "retract_center": (20.0, 10.0),
            },
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
