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
    _line_milling_center_circle_leads_motion_lines,
    _line_milling_circle_strategy_motion_lines,
    _line_milling_closed_center_leads_motion_lines,
    _line_milling_entry_lines,
    _line_milling_fallback_motion_lines,
    _line_milling_lead_path_motion_lines,
    _line_milling_linear_side_compensation_motion_lines,
    _line_milling_motion_line,
    _line_milling_no_lead_motion_lines,
    _line_milling_no_lead_side_compensation_motion_lines,
    _line_milling_open_center_leads_motion_lines,
    _line_milling_open_polyline_side_compensation_motion_lines,
    _line_milling_rapid_point,
    _line_milling_reset_lines,
    _line_milling_side_compensation_fallback_motion_lines,
    _line_milling_strategy_lead_path_motion_lines,
    _line_milling_strategy_motion_lines,
    _line_milling_trace_context,
    _line_milling_trace_motion_lines,
    _line_milling_trace_modes,
    _line_milling_prepare_after_boring_lines,
    _linear_profile_program_point,
    _linear_profile_tangent_axis,
    _no_lead_compensation_points,
    _open_polyline_center_lead_geometry,
    _plan_work_groups,
    _polyline_side_compensation_leads,
    _boring_to_router_cleanup_lines,
    _boring_to_router_side_restore_lines,
    _boring_to_router_top_face_lines,
    _router_inter_work_reset_lines,
    _router_to_boring_transition_lines,
    _side_drill_prepare_after_router_lines,
    _side_drill_prepare_after_slot_lines,
    _side_drill_prepare_after_top_lines,
    _side_drill_prepare_lines,
    _side_drill_same_spindle_reposition_lines,
    _side_drill_spindle_change_lines,
    _side_drill_reset_lines,
    _slot_milling_prepare_after_top_lines,
    _slot_milling_prepare_lines,
    _slot_milling_reset_lines,
    _side_normal,
    _tool_shift_lines,
    _top_drill_prepare_after_router_base_lines,
    _top_drill_prepare_after_side_lines,
    _top_drill_prepare_after_slot_lines,
    _top_drill_prepare_between_top_lines,
    _top_drill_prepare_lines,
    _top_drill_reset_lines,
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
    strategy_name: str = "",
    approach_type: str = "Line",
    approach_mode: str = "Down",
    approach_radius_multiplier: float = 2.0,
    retract_type: str = "Line",
    retract_mode: str = "Up",
    retract_radius_multiplier: float | None = None,
    lead_paths: bool = False,
    overcut_length: float | None = None,
    trajectory_primitives: tuple[object, ...] = (),
) -> object:
    optional_circle_changes: tuple[StateChange, ...] = ()
    if circle_center_x is not None and circle_center_y is not None:
        optional_circle_changes = (
            _change("movimiento", "circle_center_x", circle_center_x),
            _change("movimiento", "circle_center_y", circle_center_y),
        )
    optional_work_changes: tuple[StateChange, ...] = ()
    if overcut_length is not None:
        optional_work_changes = (_change("trabajo", "overcut_length", overcut_length),)
    optional_strategy_changes: tuple[StateChange, ...] = ()
    if strategy_name:
        optional_strategy_changes = (_change("trabajo", "strategy", strategy_name),)
    optional_primitive_changes: tuple[StateChange, ...] = ()
    if trajectory_primitives:
        optional_primitive_changes = (
            _change("movimiento", "trajectory_primitives", trajectory_primitives),
        )
    optional_retract_radius_changes: tuple[StateChange, ...] = ()
    if retract_radius_multiplier is not None:
        optional_retract_radius_changes = (
            _change("trabajo", "retract_radius_multiplier", retract_radius_multiplier),
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
            *optional_primitive_changes,
            _change("herramienta", "tool_radius", 2.0),
            _change("herramienta", "tool_offset_length", 107.2),
            _change("trabajo", "side_of_feature", side_of_feature),
            *optional_strategy_changes,
            _change("trabajo", "approach_type", approach_type),
            _change("trabajo", "approach_mode", approach_mode),
            _change("trabajo", "approach_radius_multiplier", approach_radius_multiplier),
            _change("trabajo", "retract_type", retract_type),
            _change("trabajo", "retract_mode", retract_mode),
            *optional_retract_radius_changes,
            *optional_work_changes,
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

    def test_router_inter_work_reset_lines_emit_full_router_reset_by_default(self) -> None:
        next_prepare = _stage_differential("profile_milling_prepare", "profile_milling", 0)

        self.assertEqual(
            _router_inter_work_reset_lines(next_prepare),
            (
                "?%ETK[7]=0",
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=2",
                "?%ETK[13]=0",
                "?%ETK[18]=0",
                "M5",
                "MLV=0",
                "G0 G53 Z201.000",
            ),
        )

    def test_router_inter_work_reset_lines_trim_etk7_when_next_router_has_strategy(self) -> None:
        next_prepare = StageDifferential(
            stage_key="line_milling_prepare",
            family="line_milling",
            order_index=0,
            target_changes=(_change("trabajo", "strategy", "Unidirectional"),),
        )

        self.assertEqual(
            _router_inter_work_reset_lines(next_prepare),
            (
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=2",
                "?%ETK[13]=0",
                "?%ETK[18]=0",
                "M5",
                "MLV=0",
                "G0 G53 Z201.000",
            ),
        )

    def test_router_to_boring_transition_lines_optionally_selects_top_face(self) -> None:
        self.assertEqual(
            _router_to_boring_transition_lines(),
            (
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=2",
                "G61",
                "MLV=0",
                "?%ETK[13]=0",
                "?%ETK[18]=0",
                "G0 G53 Z201.000",
                "G64",
            ),
        )
        self.assertEqual(
            _router_to_boring_transition_lines(include_face_selection=True),
            (
                "?%ETK[8]=1",
                "G40",
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=2",
                "G61",
                "MLV=0",
                "?%ETK[13]=0",
                "?%ETK[18]=0",
                "G0 G53 Z201.000",
                "G64",
            ),
        )

    def test_boring_to_router_side_restore_lines_return_to_right_frame(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(
                (
                    StateValue("pieza", "length", 200.0, _TEST_SOURCE),
                    StateValue("pieza", "width", 100.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_x", 5.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_y", 7.0, _TEST_SOURCE),
                )
            ),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        previous_prepare = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=0,
            target_changes=(_change("trabajo", "plane", "Left"),),
        )

        self.assertEqual(
            _boring_to_router_side_restore_lines(evaluation, previous_prepare),
            (
                "MLV=1",
                "SHF[X]=-205.000",
                "SHF[Y]=-1508.600",
                "SHF[Z]=43.000+%ETK[114]/1000",
                "?%ETK[7]=0",
            ),
        )
        self.assertEqual(_boring_to_router_top_face_lines("side_drill"), ("?%ETK[8]=1", "G40"))
        self.assertEqual(_boring_to_router_top_face_lines("top_drill"), ())

    def test_boring_to_router_cleanup_lines_cover_top_and_slot_sources(self) -> None:
        router_prepare = StageDifferential(
            stage_key="line_milling_prepare",
            family="line_milling",
            order_index=0,
            target_changes=(
                _change("herramienta", "tool_number", 4),
                _change("trabajo", "side_of_feature", "Left"),
            ),
        )
        router_trace = StageDifferential(
            stage_key="line_milling_trace",
            family="line_milling",
            order_index=1,
            target_changes=(_change("movimiento", "profile_family", "OpenPolyline"),),
        )

        self.assertEqual(
            _boring_to_router_cleanup_lines(
                "top_drill",
                router_prepare,
                router_trace,
                include_face_selection=True,
            ),
            (
                "?%ETK[7]=0",
                "?%ETK[8]=1",
                "G40",
                "?%ETK[17]=0",
                "M5",
                "?%ETK[0]=0",
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=2",
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=0",
                "T4",
                "SYN",
                "M06",
                "G61",
                "G0 G53 Z201.000",
                "G64",
            ),
        )
        self.assertIn("?%ETK[1]=0", _boring_to_router_cleanup_lines("slot_milling", router_prepare, router_trace))

    def test_line_milling_prepare_after_boring_lines_skip_top_tool_one_spindle(self) -> None:
        previous_prepare = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=0,
            target_changes=(_change("herramienta", "spindle", 1),),
        )
        differential = StageDifferential(
            stage_key="line_milling_prepare",
            family="line_milling",
            order_index=1,
            target_changes=(
                _change("herramienta", "tool_number", 4),
                _change("herramienta", "spindle", 4),
                _change("herramienta", "spindle_speed_standard", 18000),
                _change("herramienta", "shf_x", -12.0),
                _change("herramienta", "shf_y", -2.0),
                _change("herramienta", "shf_z", -90.0),
                _change("salida", "etk_9", 4),
                _change("salida", "etk_18", 1),
            ),
        )

        self.assertEqual(
            _line_milling_prepare_after_boring_lines(
                differential,
                previous_family="top_drill",
                previous_prepare=previous_prepare,
            ),
            (
                "?%ETK[9]=4",
                "?%ETK[18]=1",
                "S18000M3",
                "G17",
                "MLV=2",
                "?%ETK[13]=1",
                "MLV=2",
                "SHF[X]=-12.000",
                "SHF[Y]=-2.000",
                "SHF[Z]=-90.000",
            ),
        )

    def test_top_drill_prepare_after_router_base_lines_insert_spindle_when_needed(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector((StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),)),
            differentials=(),
            final_state=StateVector(),
        )
        differential = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=1,
            target_changes=(_change("herramienta", "tool_name", "005"),),
        )

        self.assertEqual(
            _top_drill_prepare_after_router_base_lines(evaluation, differential),
            (
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=5",
                "MLV=2",
            ),
        )

    def test_tool_shift_lines_emit_xyz_shift_triplet(self) -> None:
        differential = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=1,
            target_changes=(
                _change("herramienta", "shf_x", -64.0),
                _change("herramienta", "shf_y", 0.0),
                _change("herramienta", "shf_z", -0.95),
            ),
        )

        self.assertEqual(
            _tool_shift_lines(differential),
            ("SHF[X]=-64.000", "SHF[Y]=0.000", "SHF[Z]=-0.950"),
        )

    def test_side_drill_prepare_after_router_lines_emit_lateral_base_prepare(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector((StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),)),
            differentials=(),
            final_state=StateVector(),
        )
        differential = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=1,
            target_changes=(
                _change("herramienta", "spindle", 82),
                _change("herramienta", "shf_x", -45.0),
                _change("herramienta", "shf_y", -3.5),
                _change("herramienta", "shf_z", -80.0),
            ),
        )

        self.assertEqual(
            _side_drill_prepare_after_router_lines(evaluation, differential),
            (
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=82",
                "MLV=2",
                "SHF[X]=-45.000",
                "SHF[Y]=-3.500",
                "SHF[Z]=-80.000",
            ),
        )

    def test_line_milling_reset_lines_emit_router_reset(self) -> None:
        self.assertEqual(
            _line_milling_reset_lines(),
            (
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                "SVR 0.000",
                "VL7=0.000",
                "?%ETK[7]=0",
            ),
        )

    def test_boring_drill_reset_lines_cover_partial_and_complete_resets(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 37.25, _TEST_SOURCE),)),
        )
        top_reset = StageDifferential(
            stage_key="top_drill_reset",
            family="top_drill",
            order_index=1,
            target_changes=(),
            reset_changes=(_change("salida", "etk_17", 0),),
        )
        side_reset = StageDifferential(
            stage_key="side_drill_reset",
            family="side_drill",
            order_index=1,
            target_changes=(),
            reset_changes=(_change("salida", "etk_17", 257),),
        )

        self.assertEqual(
            _top_drill_reset_lines(evaluation, top_reset, final=False),
            (
                "MLV=1",
                "SHF[Z]=37.250+%ETK[114]/1000",
                "?%ETK[7]=0",
            ),
        )
        self.assertEqual(
            _side_drill_reset_lines(evaluation, side_reset),
            (
                "MLV=1",
                "SHF[Z]=37.250+%ETK[114]/1000",
                "?%ETK[7]=0",
                "G61",
                "MLV=0",
                "?%ETK[0]=0",
                "?%ETK[17]=257",
                "G4F1.200",
                "M5",
                "D0",
            ),
        )

    def test_slot_milling_reset_lines_cover_final_partial_and_trimmed_etk7(self) -> None:
        self.assertEqual(
            _slot_milling_reset_lines(),
            (
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                "SVR 0.000",
                "VL7=0.000",
                "?%ETK[7]=0",
                "G61",
                "MLV=0",
                "?%ETK[1]=0",
                "?%ETK[17]=0",
                "G4F1.200",
                "M5",
                "D0",
            ),
        )
        self.assertEqual(
            _slot_milling_reset_lines(final=False, emit_etk7=False),
            (
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                "SVR 0.000",
                "VL7=0.000",
            ),
        )

    def test_slot_milling_prepare_after_top_lines_include_optional_speed_and_modal(self) -> None:
        differential = StageDifferential(
            stage_key="slot_milling_prepare",
            family="slot_milling",
            order_index=1,
            target_changes=(
                _change("herramienta", "spindle", 82),
                _change("herramienta", "spindle_speed_standard", 4000),
                _change("herramienta", "shf_x", -64.0),
                _change("herramienta", "shf_y", 0.0),
                _change("herramienta", "shf_z", -0.95),
                _change("salida", "etk_1", 16),
                _change("salida", "etk_17", 257),
            ),
        )

        self.assertEqual(
            _slot_milling_prepare_after_top_lines(differential, emit_mlv_after_g17=True),
            (
                "?%ETK[6]=82",
                "G17",
                "MLV=2",
                "?%ETK[17]=257",
                "S4000M3",
                "?%ETK[1]=16",
                "MLV=2",
                "SHF[X]=-64.000",
                "SHF[Y]=0.000",
                "SHF[Z]=-0.950",
            ),
        )

    def test_slot_milling_prepare_lines_emit_initial_slot_prepare(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(
                (
                    StateValue("pieza", "length", 400.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_x", 5.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_y", 7.0, _TEST_SOURCE),
                )
            ),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        differential = StageDifferential(
            stage_key="slot_milling_prepare",
            family="slot_milling",
            order_index=1,
            target_changes=(
                _change("herramienta", "spindle", 82),
                _change("herramienta", "spindle_speed_standard", 4000),
                _change("herramienta", "shf_x", -64.0),
                _change("herramienta", "shf_y", 0.0),
                _change("herramienta", "shf_z", -0.95),
                _change("salida", "etk_1", 16),
            ),
        )

        self.assertEqual(
            _slot_milling_prepare_lines(evaluation, differential),
            (
                "?%ETK[6]=82",
                "G17",
                "MLV=2",
                "%Or[0].ofX=-410000.000",
                "%Or[0].ofY=-1515599.976",
                "%Or[0].ofZ=43000.000",
                "MLV=1",
                "SHF[X]=-405.000",
                "SHF[Y]=-1508.600",
                "SHF[Z]=43.000",
                "MLV=2",
                "?%ETK[1]=16",
                "MLV=2",
                "SHF[X]=-64.000",
                "SHF[Y]=0.000",
                "SHF[Z]=-0.950",
            ),
        )

    def test_top_drill_prepare_lines_emit_initial_top_prepare(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(
                (
                    StateValue("pieza", "length", 400.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_x", 5.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_y", 7.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),
                )
            ),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        differential = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=1,
            target_changes=(
                _change("herramienta", "tool_name", "005"),
                _change("herramienta", "spindle_speed_standard", 6000),
                _change("herramienta", "shf_x", -64.0),
                _change("herramienta", "shf_y", 0.0),
                _change("herramienta", "shf_z", -0.95),
                _change("salida", "etk_0_mask", 5),
                _change("salida", "etk_17", 257),
            ),
        )

        self.assertEqual(
            _top_drill_prepare_lines(evaluation, differential),
            (
                "MLV=2",
                "G17",
                "?%ETK[6]=5",
                "%Or[0].ofX=-410000.000",
                "%Or[0].ofY=-1515599.976",
                "%Or[0].ofZ=43000.000",
                "MLV=1",
                "SHF[X]=-405.000",
                "SHF[Y]=-1508.600",
                "SHF[Z]=25.000",
                "MLV=2",
                "MLV=2",
                "SHF[X]=-64.000",
                "SHF[Y]=0.000",
                "SHF[Z]=-0.950",
                "?%ETK[17]=257",
                "S6000M3",
                "?%ETK[0]=5",
            ),
        )

    def test_top_drill_prepare_between_top_lines_cover_same_and_changed_tool(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector((StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),)),
            differentials=(),
            final_state=StateVector(),
        )
        previous_prepare = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=1,
            target_changes=(_change("herramienta", "tool_name", "005"),),
        )
        previous_trace = StageDifferential(
            stage_key="top_drill_trace",
            family="top_drill",
            order_index=2,
            target_changes=(),
            trace=(_trace_move("Approach", (10.0, 20.0, 30.0)),),
        )
        same_tool = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=3,
            target_changes=(_change("herramienta", "tool_name", "005"),),
        )
        changed_tool = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=3,
            target_changes=(
                _change("herramienta", "tool_name", "006"),
                _change("herramienta", "spindle_speed_standard", 6000),
                _change("herramienta", "shf_x", -61.0),
                _change("herramienta", "shf_y", 1.0),
                _change("herramienta", "shf_z", -1.25),
                _change("salida", "etk_0_mask", 6),
                _change("salida", "etk_17", 257),
            ),
        )

        self.assertEqual(
            _top_drill_prepare_between_top_lines(
                evaluation,
                same_tool,
                previous_prepare,
                previous_trace,
            ),
            (
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "G0 X10.000 Y20.000 Z30.000",
            ),
        )
        self.assertEqual(
            _top_drill_prepare_between_top_lines(
                evaluation,
                changed_tool,
                previous_prepare,
                previous_trace,
            ),
            (
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=6",
                "G0 X10.000 Y20.000 Z30.000",
                "MLV=2",
                "SHF[X]=-61.000",
                "SHF[Y]=1.000",
                "SHF[Z]=-1.250",
                "?%ETK[17]=257",
                "S6000M3",
                "?%ETK[0]=6",
            ),
        )

    def test_top_drill_prepare_transition_lines_cover_slot_and_side_entries(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(
                (
                    StateValue("pieza", "length", 400.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_x", 5.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_y", 7.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),
                )
            ),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        differential = StageDifferential(
            stage_key="top_drill_prepare",
            family="top_drill",
            order_index=1,
            target_changes=(
                _change("herramienta", "tool_name", "005"),
                _change("herramienta", "spindle_speed_standard", 6000),
                _change("herramienta", "shf_x", -64.0),
                _change("herramienta", "shf_y", 0.0),
                _change("herramienta", "shf_z", -0.95),
                _change("salida", "etk_0_mask", 5),
                _change("salida", "etk_17", 257),
            ),
        )
        previous_side = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=0,
            target_changes=(
                _change("trabajo", "plane", "Left"),
                _change("herramienta", "shf_z", -20.0),
            ),
        )

        self.assertEqual(
            _top_drill_prepare_after_slot_lines(evaluation, differential),
            (
                "?%ETK[8]=1",
                "G40",
                "MLV=0",
                "G0 G53 Z201.000",
                "MLV=2",
                "?%ETK[1]=0",
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=5",
                "MLV=2",
                "SHF[X]=-64.000",
                "SHF[Y]=0.000",
                "SHF[Z]=-0.950",
                "?%ETK[17]=257",
                "S6000M3",
                "?%ETK[0]=5",
            ),
        )
        self.assertEqual(
            _top_drill_prepare_after_side_lines(evaluation, differential, previous_side),
            (
                "MLV=1",
                "SHF[X]=-405.000",
                "SHF[Y]=-1508.600",
                "SHF[Z]=43.000+%ETK[114]/1000",
                "?%ETK[8]=1",
                "G40",
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=5",
                "MLV=0",
                "G0 G53 Z63.000",
                "MLV=2",
                "MLV=2",
                "SHF[X]=-64.000",
                "SHF[Y]=0.000",
                "SHF[Z]=-0.950",
                "?%ETK[17]=257",
                "S6000M3",
                "?%ETK[0]=5",
            ),
        )

    def test_side_drill_prepare_lines_emit_initial_side_prepare(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(
                (
                    StateValue("pieza", "length", 400.0, _TEST_SOURCE),
                    StateValue("pieza", "width", 350.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_x", 5.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_y", 7.0, _TEST_SOURCE),
                    StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),
                )
            ),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        differential = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=1,
            target_changes=(
                _change("trabajo", "plane", "Left"),
                _change("herramienta", "spindle", 82),
                _change("herramienta", "spindle_speed_standard", 6000),
                _change("herramienta", "shf_x", -45.0),
                _change("herramienta", "shf_y", -3.5),
                _change("herramienta", "shf_z", -20.0),
                _change("salida", "etk_0_mask", 6),
                _change("salida", "etk_17", 257),
            ),
        )

        self.assertEqual(
            _side_drill_prepare_lines(evaluation, differential, multi_side_sequence=True),
            (
                "MLV=2",
                "G17",
                "?%ETK[6]=82",
                "%Or[0].ofX=-410000.000",
                "%Or[0].ofY=-1515599.976",
                "%Or[0].ofZ=43000.000",
                "MLV=1",
                "SHF[X]=-405.000",
                "SHF[Y]=-1158.600",
                "SHF[Z]=25.000",
                "MLV=2",
                "MLV=2",
                "SHF[X]=-45.000",
                "SHF[Y]=-3.500",
                "SHF[Z]=-20.000",
                "?%ETK[17]=257",
                "S6000M3",
                "?%ETK[0]=6",
                "G4F0.500",
            ),
        )

    def test_side_drill_prepare_between_lines_cover_same_and_changed_spindle(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector(),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        previous_trace = StageDifferential(
            stage_key="side_drill_trace",
            family="side_drill",
            order_index=2,
            target_changes=(),
            trace=(_trace_move("Approach", (11.0, 22.0, 33.0)),),
        )
        same_spindle = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=3,
            target_changes=(
                _change("movimiento", "side_axis", "X"),
                _change("herramienta", "shf_z", -20.0),
            ),
        )
        previous_prepare = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=1,
            target_changes=(_change("herramienta", "shf_z", -20.0),),
        )
        changed_spindle = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=3,
            target_changes=(
                _change("herramienta", "spindle", 83),
                _change("herramienta", "shf_x", -44.0),
                _change("herramienta", "shf_y", -2.0),
                _change("herramienta", "shf_z", -10.0),
            ),
        )

        self.assertEqual(
            _side_drill_same_spindle_reposition_lines(
                same_spindle,
                previous_trace,
                multi_side_sequence=True,
            ),
            ("G0 X11.000 Y22.000 Z33.000", "G4F0.500"),
        )
        self.assertEqual(
            _side_drill_spindle_change_lines(evaluation, changed_spindle, previous_prepare),
            (
                "?%ETK[6]=83",
                "MLV=0",
                "G0 G53 Z73.000",
                "MLV=2",
                "MLV=2",
                "SHF[X]=-44.000",
                "SHF[Y]=-2.000",
                "SHF[Z]=-10.000",
            ),
        )

    def test_side_drill_prepare_transition_lines_cover_slot_and_top_entries(self) -> None:
        evaluation = IsoStateEvaluation(
            source_path=Path("fixture.pgmx"),
            project_name="Fixture",
            initial_state=StateVector((StateValue("pieza", "origin_z", 25.0, _TEST_SOURCE),)),
            differentials=(),
            final_state=StateVector((StateValue("pieza", "header_dz", 43.0, _TEST_SOURCE),)),
        )
        differential = StageDifferential(
            stage_key="side_drill_prepare",
            family="side_drill",
            order_index=1,
            target_changes=(
                _change("herramienta", "spindle", 82),
                _change("herramienta", "shf_x", -45.0),
                _change("herramienta", "shf_y", -3.5),
                _change("herramienta", "shf_z", -20.0),
            ),
        )

        self.assertEqual(
            _side_drill_prepare_after_slot_lines(evaluation, differential),
            (
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=82",
                "MLV=2",
                "SHF[X]=-45.000",
                "SHF[Y]=-3.500",
                "SHF[Z]=-20.000",
            ),
        )
        self.assertEqual(
            _side_drill_prepare_after_top_lines(evaluation, differential),
            (
                "MLV=1",
                "SHF[Z]=25.000+%ETK[114]/1000",
                "MLV=2",
                "G17",
                "?%ETK[6]=82",
                "MLV=0",
                "G0 G53 Z63.000",
                "MLV=2",
                "MLV=2",
                "SHF[X]=-45.000",
                "SHF[Y]=-3.500",
                "SHF[Z]=-20.000",
            ),
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

    def test_line_milling_rapid_point_uses_center_lead_geometry(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            approach_type="Arc",
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_open_center_leads)
        self.assertEqual(_line_milling_rapid_point(context), (6.0, 24.0))

    def test_line_milling_rapid_point_uses_no_lead_compensation_entry(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Right",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
        )

        self.assertTrue(context.modes.uses_no_lead_side_compensation)
        self.assertEqual(_line_milling_rapid_point(context), (9.0, 20.0))

    def test_line_milling_entry_lines_without_previous_router(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
        )

        self.assertEqual(
            _line_milling_entry_lines([], context, 10.0, 20.0),
            (
                "G0 X10.000 Y20.000",
                "G0 Z30.000",
                "D1",
                "SVL 107.200",
                "VL6=107.200",
                "SVR 2.000",
                "VL7=2.000",
            ),
        )

    def test_line_milling_entry_lines_continue_from_previous_router_xy(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
        )
        previous_trace = _stage_differential("profile_milling_trace", "profile_milling", 0)
        emitted_lines = [
            ExplainedIsoLine(
                "G1 X1.000 Y2.000 Z5.000",
                "profile_milling_trace",
                _TEST_SOURCE,
            )
        ]

        self.assertEqual(
            _line_milling_entry_lines(
                emitted_lines,
                context,
                10.0,
                20.0,
                previous_router_trace=previous_trace,
            ),
            (
                "?%ETK[7]=0",
                "G17",
                "MLV=2",
                "G0 X1.000 Y2.000 Z30.000",
                "G0 X10.000 Y20.000 Z30.000",
                "G0 X10.000 Y20.000 Z30.000",
                "D1",
                "SVL 107.200",
                "VL6=107.200",
                "SVR 2.000",
                "VL7=2.000",
            ),
        )

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

    def test_side_compensation_fallback_builder_uses_lift_y_and_overcut(self) -> None:
        context = _line_milling_test_context(
            profile_family="VerticalFallback",
            side_of_feature="Left",
            contour_points=((10.0, 20.0), (10.0, 110.0)),
            lead_paths=True,
            overcut_length=3.0,
        )

        self.assertTrue(context.modes.uses_side_compensation)
        self.assertEqual(
            _line_milling_side_compensation_fallback_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G41",
                "G1 X10.000 Y20.000 Z5.000 F120.000",
                "G1 Z-8.000 F120.000",
                "G1 Y20.000 Z-8.000 F120.000",
                "G1 Y110.000 Z-8.000 F600.000",
                "G1 Y110.000 Z-8.000 F600.000",
                "G1 Z5.000 F600.000",
                "G40",
                "G1 X10.000 Y116.000 Z5.000 F600.000",
            ),
        )

    def test_linear_side_compensation_builder_reads_context(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Right",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_side_compensation)
        self.assertEqual(
            _line_milling_linear_side_compensation_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G42",
                "G1 X8.000 Y20.000 Z5.000 F120.000",
                "G1 X10.000 Z-8.000 F120.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G1 X112.000 Z5.000 F600.000",
                "G40",
                "G1 X113.000 Y20.000 Z5.000 F600.000",
            ),
        )

    def test_lead_path_builder_walks_approach_trajectory_and_lift(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            lead_paths=True,
        )

        self.assertTrue(context.modes.has_lead_paths)
        self.assertFalse(context.modes.uses_side_compensation)
        self.assertEqual(
            _line_milling_lead_path_motion_lines(context),
            (
                "?%ETK[7]=4",
                "G1 X10.000 Z-8.000 F120.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G1 X112.000 Z5.000 F600.000",
            ),
        )

    def test_open_center_leads_builder_emits_linear_entry_and_exit(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_open_center_leads)
        self.assertEqual(
            _line_milling_open_center_leads_motion_lines(context, 6.0, 20.0),
            (
                "?%ETK[7]=4",
                "G1 X10.000 Z-8.000 F120.000",
                "G1 X110.000 F600.000",
                "G1 X114.000 Z5.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_closed_center_leads_builder_emits_arc_entry_and_linear_exit(self) -> None:
        context = _line_milling_test_context(
            profile_family="ClosedPolylineMidEdgeStart",
            side_of_feature="Center",
            contour_points=(
                (10.0, 10.0),
                (20.0, 10.0),
                (20.0, 20.0),
                (10.0, 20.0),
                (10.0, 10.0),
            ),
            profile_winding="CounterClockwise",
            approach_type="Arc",
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_closed_center_leads)
        self.assertEqual(
            _line_milling_closed_center_leads_motion_lines(context, 6.0, 14.0),
            (
                "?%ETK[7]=4",
                "G3 X10.000 Y10.000 Z-8.000 I10.000 J14.000 F120.000",
                "G1 X20.000 Z-8.000 F600.000",
                "G1 Y20.000 Z-8.000 F600.000",
                "G1 X10.000 Z-8.000 F600.000",
                "G1 Y10.000 Z-8.000 F600.000",
                "G1 X14.000 Z5.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_center_circle_leads_builder_emits_circle_arcs(self) -> None:
        context = _line_milling_test_context(
            profile_family="Circle",
            side_of_feature="Center",
            contour_points=((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)),
            profile_winding="CounterClockwise",
            circle_center_x=15.0,
            circle_center_y=15.0,
            approach_type="Arc",
            lead_paths=True,
        )

        self.assertTrue(context.modes.uses_center_circle_leads)
        self.assertEqual(
            _line_milling_center_circle_leads_motion_lines(context, 6.0, 6.0),
            (
                "?%ETK[7]=4",
                "G3 X10.000 Y10.000 Z-8.000 I6.000 J10.000 F120.000",
                "G3 X20.000 Y10.000 I15.000 J15.000 F600.000",
                "G3 X20.000 Y20.000 I15.000 J15.000 F600.000",
                "G3 X10.000 Y20.000 I15.000 J15.000 F600.000",
                "G1 Y14.000 Z5.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_circle_strategy_builder_walks_strategy_toolpath(self) -> None:
        context = _line_milling_test_context(
            profile_family="Circle",
            side_of_feature="Center",
            contour_points=((10.0, 10.0), (20.0, 10.0)),
            profile_winding="CounterClockwise",
            circle_center_x=15.0,
            circle_center_y=15.0,
            strategy_name="Unidirectional",
        )

        self.assertEqual(
            _line_milling_circle_strategy_motion_lines(context, 10.0, 10.0),
            (
                "G1 Z5.000 F120.000",
                "?%ETK[7]=4",
                "G1 Z-8.000 F600.000",
                "G1 X20.000 Z-8.000 F600.000",
                "G1 Z5.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_trace_motion_lines_dispatches_to_center_lead_builder(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            lead_paths=True,
        )
        rapid_x, rapid_y = _line_milling_rapid_point(context)

        self.assertEqual(
            _line_milling_trace_motion_lines(context, rapid_x, rapid_y),
            _line_milling_open_center_leads_motion_lines(context, rapid_x, rapid_y),
        )

    def test_trace_motion_lines_dispatches_to_linear_side_compensation_builder(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Right",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            lead_paths=True,
        )
        rapid_x, rapid_y = _line_milling_rapid_point(context)

        self.assertEqual(
            _line_milling_trace_motion_lines(context, rapid_x, rapid_y),
            _line_milling_linear_side_compensation_motion_lines(context),
        )

    def test_strategy_lead_path_builder_uses_milling_feed_for_strategy_entry(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            strategy_name="Unidirectional",
            lead_paths=True,
        )

        self.assertTrue(context.modes.has_lead_paths)
        self.assertEqual(
            _line_milling_strategy_lead_path_motion_lines(context),
            (
                "G1 Z5.000 F120.000",
                "?%ETK[7]=4",
                "G1 X10.000 Z-8.000 F600.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G1 X112.000 Z5.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_strategy_builder_without_leads_keeps_open_polyline_z_modal(self) -> None:
        context = _line_milling_test_context(
            profile_family="OpenPolyline",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
            strategy_name="Unidirectional",
        )

        self.assertEqual(
            _line_milling_strategy_motion_lines(context),
            (
                "G1 Z5.000 F120.000",
                "?%ETK[7]=4",
                "G1 Z-8.000 F600.000",
                "G1 X110.000 F600.000",
                "G1 Z5.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_no_lead_builder_emits_center_line_without_compensation(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
        )

        self.assertFalse(context.modes.has_lead_paths)
        self.assertEqual(
            _line_milling_no_lead_motion_lines(context),
            (
                "G1 Z-8.000 F120.000",
                "?%ETK[7]=4",
                "G1 X110.000 Z-8.000 F600.000",
                "G0 Z5.000",
            ),
        )

    def test_fallback_builder_keeps_legacy_plain_toolpath_shape(self) -> None:
        context = _line_milling_test_context(
            profile_family="Line",
            side_of_feature="Center",
            contour_points=((10.0, 20.0), (110.0, 20.0)),
        )

        self.assertEqual(
            _line_milling_fallback_motion_lines(context),
            (
                "G1 Z5.000 F120.000",
                "?%ETK[7]=4",
                "G1 Z-8.000 F600.000",
                "G1 X110.000 Z-8.000 F600.000",
                "G1 Z5.000 F600.000",
                "G0 Z5.000",
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
