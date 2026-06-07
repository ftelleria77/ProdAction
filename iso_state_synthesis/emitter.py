"""Explanatory ISO candidate emitter for state differentials."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .boring_head_lines import (
    _side_drill_prepare_after_router_lines,
    _side_drill_prepare_after_slot_lines,
    _side_drill_prepare_after_top_lines,
    _side_drill_prepare_between_base_lines,
    _side_drill_prepare_frame_lines,
    _side_drill_prepare_modal_lines,
    _side_drill_prepare_origin_lines,
    _side_drill_reset_lines,
    _side_drill_same_spindle_reposition_lines,
    _side_drill_spindle_change_lines,
    _side_plane_selection_lines,
    _slot_milling_prepare_after_top_lines,
    _slot_milling_prepare_lines,
    _slot_milling_reset_lines,
    _same_top_drill_tool,
    _tool_shift_lines,
    _top_drill_prepare_after_router_base_lines,
    _top_drill_prepare_after_slot_base_lines,
    _top_drill_prepare_after_side_restore_lines,
    _top_drill_prepare_after_side_work_lines,
    _top_drill_prepare_between_tool_change_lines,
    _top_drill_prepare_between_top_base_lines,
    _top_drill_prepare_frame_lines,
    _top_drill_prepare_modal_lines,
    _top_drill_prepare_origin_lines,
    _top_drill_previous_approach_reposition_line,
    _top_drill_reset_lines,
)
from .boring_trace_lines import _side_drill_trace_lines, _top_drill_trace_lines
from .catalog import (
    block_id_for_stage_key,
    select_transition_id,
    transition_id_for_rule_status,
)
from .differential import evaluate_pgmx_state_plan
from .errors import IsoCandidateEmissionError
from .model import (
    EvidenceSource,
    IsoStateEvaluation,
    IsoStateWarning,
    StageDifferential,
    StateChange,
)
from .program_lines import (
    _common_program_close_tail_lines,
    _empty_piece_frame_lines,
    _empty_program_close_tail_lines,
    _empty_program_explicit_close_lines,
    _face_selection_lines,
    _is_mixed_side_close,
    _lateral_program_close_frame_lines,
    _lateral_program_close_reset_lines,
    _machine_metric_mode_line,
    _machine_preamble_template_lines,
    _piece_frame_base_lines,
    _program_close_xy_line,
    _program_header_lines,
    _router_program_close_lines,
    _side_program_close_prefix_lines,
)
from .profile_milling_lines import _profile_milling_trace_lines
from .router_milling_lines import (
    _line_milling_entry_lines,
    _line_milling_prepare_after_boring_lines,
    _line_milling_prepare_lines,
    _line_milling_rapid_point,
    _line_milling_reset_lines,
    _line_milling_trace_context,
    _line_milling_trace_motion_lines,
)
from .slot_milling_lines import _slot_milling_trace_lines
from .transition_lines import (
    _boring_to_router_cleanup_lines,
    _boring_to_router_side_restore_lines,
    _boring_to_router_top_face_lines,
    _router_inter_work_reset_lines,
    _router_to_boring_transition_lines,
    _side_to_slot_milling_transition_lines,
    _slot_to_slot_milling_transition_lines,
    _top_to_slot_milling_transition_lines,
)
from .work_groups import _COMMON_STAGE_KEYS, _WorkGroup, _work_stage_groups


_ROUTER_MILLING_FAMILIES = {"line_milling", "profile_milling"}


@dataclass(frozen=True)
class ExplainedIsoLine:
    """One ISO candidate line with its explanation source."""

    line: str
    stage_key: str
    source: EvidenceSource
    confidence: str = "observed"
    rule_status: str = "observed"
    block_id: Optional[str] = None
    transition_id: Optional[str] = None
    note: str = ""


@dataclass(frozen=True)
class ExplainedIsoProgram:
    """Candidate ISO text plus line-level explanations."""

    source_path: Path
    program_name: str
    lines: tuple[ExplainedIsoLine, ...]
    warnings: tuple[IsoStateWarning, ...] = ()

    def text(self) -> str:
        return "\n".join(item.line for item in self.lines) + "\n"

    def write_text(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.write_text(self.text(), encoding="utf-8")
        return output_path


def emit_candidate_for_pgmx(
    pgmx_path: Path,
    *,
    program_name: Optional[str] = None,
) -> ExplainedIsoProgram:
    """Build a state evaluation and emit the currently supported candidate ISO."""

    return emit_candidate_from_evaluation(
        evaluate_pgmx_state_plan(Path(pgmx_path)),
        program_name=program_name,
    )


def emit_candidate_from_evaluation(
    evaluation: IsoStateEvaluation,
    *,
    program_name: Optional[str] = None,
) -> ExplainedIsoProgram:
    """Emit candidate ISO from a state evaluation.

    This emitter is intentionally narrow: it supports complete observed work
    groups for drilling, slot milling and router milling, plus the transitions
    promoted by the state-synthesis study.
    """

    resolved_program_name = program_name or evaluation.source_path.stem.lower()
    ordered_differentials = sorted(evaluation.differentials, key=lambda item: item.order_index)
    differentials = {
        differential.stage_key: differential
        for differential in ordered_differentials
    }
    unsupported = [
        warning
        for warning in evaluation.warnings
        if warning.code == "unsupported_stage_family"
    ]
    if unsupported:
        unsupported_sources = sorted({warning.source for warning in unsupported})
        sources = ", ".join(unsupported_sources[:5])
        suffix = "..." if len(unsupported_sources) > 5 else ""
        raise IsoCandidateEmissionError(
            "El plan contiene etapas no soportadas por el emisor actual: "
            f"{sources}{suffix}."
        )

    work_differentials = [
        differential
        for differential in ordered_differentials
        if differential.stage_key not in _COMMON_STAGE_KEYS
    ]
    missing = sorted(_COMMON_STAGE_KEYS.difference(differentials))
    if missing:
        if missing == ["program_close"] and not work_differentials:
            return _emit_empty_program_candidate(
                evaluation,
                resolved_program_name,
                differentials,
                explicit_close=False,
            )
        raise IsoCandidateEmissionError(
            "El emisor candidato inicial requiere cabecera, preambulo y cierre; "
            f"faltan etapas: {', '.join(missing)}"
        )

    if not work_differentials:
        return _emit_empty_program_candidate(
            evaluation,
            resolved_program_name,
            differentials,
            explicit_close=True,
        )

    work_groups = _work_stage_groups(ordered_differentials)
    if len(work_differentials) != len(work_groups) * 3:
        raise IsoCandidateEmissionError(
            "El emisor candidato actual solo soporta secuencias completas "
            "prepare/trace/reset para top_drill, side_drill, slot_milling, "
            "line_milling y profile_milling."
        )

    if all(group.family == "top_drill" for group in work_groups):
        return _emit_top_drill_sequence_candidate(
            evaluation,
            resolved_program_name,
            differentials,
            tuple((group.prepare, group.trace, group.reset) for group in work_groups),
        )
    if all(group.family == "side_drill" for group in work_groups):
        return _emit_side_drill_sequence_candidate(
            evaluation,
            resolved_program_name,
            differentials,
            tuple((group.prepare, group.trace, group.reset) for group in work_groups),
        )
    return _emit_work_sequence_candidate(
        evaluation,
        resolved_program_name,
        differentials,
        work_groups,
    )


def _emit_empty_program_candidate(
    evaluation: IsoStateEvaluation,
    program_name: str,
    differentials: dict[str, StageDifferential],
    *,
    explicit_close: bool,
) -> ExplainedIsoProgram:
    lines: list[ExplainedIsoLine] = []
    _emit_program_header(lines, evaluation, differentials["program_header"], program_name)
    _emit_machine_preamble(lines, differentials["machine_preamble"])
    close_differential = differentials.get("program_close", differentials["machine_preamble"])
    _emit_empty_piece_frame(
        lines,
        evaluation,
        differentials["program_header"],
        face_pair_count=2 if explicit_close else 1,
    )
    _emit_empty_program_close(lines, evaluation, close_differential, explicit_close=explicit_close)
    return ExplainedIsoProgram(
        source_path=evaluation.source_path,
        program_name=program_name,
        lines=tuple(lines),
        warnings=evaluation.warnings,
    )


def _emit_top_drill_sequence_candidate(
    evaluation: IsoStateEvaluation,
    program_name: str,
    differentials: dict[str, StageDifferential],
    groups: tuple[tuple[StageDifferential, StageDifferential, StageDifferential], ...],
) -> ExplainedIsoProgram:
    lines: list[ExplainedIsoLine] = []
    _emit_program_header(lines, evaluation, differentials["program_header"], program_name)
    _emit_machine_preamble(lines, differentials["machine_preamble"])
    _emit_piece_frame(
        lines,
        evaluation,
        differentials["program_header"],
        _work_plane(evaluation),
        "top_drill",
    )

    previous_prepare: Optional[StageDifferential] = None
    previous_trace: Optional[StageDifferential] = None
    for index, (prepare, trace, reset) in enumerate(groups):
        incoming_transition_id = (
            select_transition_id("top_drill", previous_prepare, "top_drill", prepare)
            if previous_prepare is not None
            else None
        )
        same_tool = (
            previous_prepare is not None
            and _change_after(previous_prepare, "herramienta", "tool_name")
            == _change_after(prepare, "herramienta", "tool_name")
        )
        _emit_top_drill_prepare(
            lines,
            evaluation,
            prepare,
            previous_prepare=previous_prepare,
            previous_trace=previous_trace,
            transition_id=incoming_transition_id,
        )
        _emit_top_drill_trace(
            lines,
            trace,
            emit_mlv_after_etk7=(index == 0),
            combine_rapid_z=same_tool,
        )
        _emit_top_drill_reset(lines, evaluation, reset, final=(index == len(groups) - 1))
        previous_prepare = prepare
        previous_trace = trace

    _emit_program_close(lines, differentials["program_close"], evaluation)
    return ExplainedIsoProgram(
        source_path=evaluation.source_path,
        program_name=program_name,
        lines=tuple(lines),
        warnings=evaluation.warnings,
    )


def _emit_side_drill_sequence_candidate(
    evaluation: IsoStateEvaluation,
    program_name: str,
    differentials: dict[str, StageDifferential],
    groups: tuple[tuple[StageDifferential, StageDifferential, StageDifferential], ...],
) -> ExplainedIsoProgram:
    lines: list[ExplainedIsoLine] = []
    _emit_program_header(lines, evaluation, differentials["program_header"], program_name)
    _emit_machine_preamble(lines, differentials["machine_preamble"])
    _emit_piece_frame(
        lines,
        evaluation,
        differentials["program_header"],
        _work_plane(evaluation),
        "side_drill",
    )

    previous_prepare: Optional[StageDifferential] = None
    previous_trace: Optional[StageDifferential] = None
    isolated_side_transition = len(groups) == 2
    for index, (prepare, trace, reset) in enumerate(groups):
        next_prepare = groups[index + 1][0] if index + 1 < len(groups) else None
        plane = str(_change_after(prepare, "trabajo", "plane"))
        previous_plane = (
            str(_change_after(previous_prepare, "trabajo", "plane"))
            if previous_prepare is not None
            else None
        )
        next_plane = (
            str(_change_after(next_prepare, "trabajo", "plane"))
            if next_prepare is not None
            else None
        )
        _emit_side_drill_prepare(
            lines,
            evaluation,
            prepare,
            previous_prepare=previous_prepare,
            previous_trace=previous_trace,
            multi_side_sequence=index < len(groups) - 1,
            final_left_pause=_requires_final_short_left_pause(
                evaluation,
                previous_prepare,
                previous_trace,
                prepare,
                trace,
                multi_side_sequence=index < len(groups) - 1,
            ),
        )
        same_spindle = (
            previous_prepare is not None
            and _change_after(previous_prepare, "herramienta", "spindle")
            == _change_after(prepare, "herramienta", "spindle")
        )
        axis = str(_change_after(prepare, "movimiento", "side_axis"))
        fixed_override = None
        if (
            isolated_side_transition
            and plane in {"Back", "Left"}
            and (
                (previous_plane is not None and previous_plane != plane)
                or (previous_plane is None and next_plane is not None and next_plane != plane)
            )
        ):
            fixed_override = _mirrored_side_fixed(evaluation, prepare, trace)
        _emit_side_drill_trace(
            lines,
            trace,
            emit_mlv_after_etk7=(index == 0),
            combine_rapid_z=same_spindle and axis == "X",
            fixed_override=fixed_override,
        )
        _emit_side_drill_reset(lines, evaluation, reset, final=(index == len(groups) - 1))
        previous_prepare = prepare
        previous_trace = trace

    last_family = "side_drill"
    last_plane = str(_change_after(groups[-1][0], "trabajo", "plane"))
    _emit_program_close(
        lines,
        differentials["program_close"],
        evaluation,
        family_override=last_family,
        plane_override=last_plane,
    )
    return ExplainedIsoProgram(
        source_path=evaluation.source_path,
        program_name=program_name,
        lines=tuple(lines),
        warnings=evaluation.warnings,
    )


def _emit_work_sequence_candidate(
    evaluation: IsoStateEvaluation,
    program_name: str,
    differentials: dict[str, StageDifferential],
    groups: tuple[_WorkGroup, ...],
) -> ExplainedIsoProgram:
    lines: list[ExplainedIsoLine] = []
    _emit_program_header(lines, evaluation, differentials["program_header"], program_name)
    _emit_machine_preamble(lines, differentials["machine_preamble"])
    first_family = groups[0].family
    _emit_piece_frame(
        lines,
        evaluation,
        differentials["program_header"],
        _work_plane(evaluation),
        first_family,
    )

    previous_group: Optional[_WorkGroup] = None
    previous_router_group: Optional[_WorkGroup] = None
    for index, group in enumerate(groups):
        next_group = groups[index + 1] if index < len(groups) - 1 else None
        following_group = groups[index + 2] if index < len(groups) - 2 else None
        _emit_planned_work_group(
            lines,
            evaluation,
            group,
            previous_group,
            next_group,
            following_group,
            previous_router_group,
        )
        _emit_planned_outgoing_transition(lines, group, next_group)
        if group.family in _ROUTER_MILLING_FAMILIES:
            previous_router_group = group
        previous_group = group

    last_family = groups[-1].family
    last_plane = _work_group_plane(evaluation, groups[-1])
    _emit_program_close(
        lines,
        differentials["program_close"],
        evaluation,
        family_override=last_family,
        plane_override=last_plane,
    )
    return ExplainedIsoProgram(
        source_path=evaluation.source_path,
        program_name=program_name,
        lines=tuple(lines),
        warnings=evaluation.warnings,
    )


def _emit_planned_work_group(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    group: _WorkGroup,
    previous_group: Optional[_WorkGroup],
    next_group: Optional[_WorkGroup],
    following_group: Optional[_WorkGroup],
    previous_router_group: Optional[_WorkGroup],
) -> None:
    family = group.family
    prepare = group.prepare
    trace = group.trace
    reset = group.reset
    next_family = next_group.family if next_group is not None else None
    previous_family = previous_group.family if previous_group is not None else None
    previous_prepare = previous_group.prepare if previous_group is not None else None
    previous_trace = previous_group.trace if previous_group is not None else None
    incoming_transition_id = group.incoming_transition_id

    if family == "top_drill" and incoming_transition_id == "T-XH-001":
        assert previous_group is not None
        _emit_router_to_top_drill_transition(
            lines,
            previous_group.reset,
            previous_family=previous_group.family,
            include_face_selection=(
                previous_group.incoming_transition_id is not None
                or _profile_to_top_requires_face_selection(evaluation, previous_group)
            ),
            transition_id=incoming_transition_id,
        )
        _emit_top_drill_prepare_after_router(
            lines,
            evaluation,
            prepare,
            previous_family=previous_group.family,
            transition_id=incoming_transition_id,
        )
        _emit_top_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_top_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "top_drill" and incoming_transition_id == "T-BH-004":
        assert previous_prepare is not None
        _emit_top_drill_prepare_after_side(lines, evaluation, prepare, previous_prepare, transition_id=incoming_transition_id)
        _emit_top_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_top_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "top_drill" and previous_family == "top_drill":
        assert previous_prepare is not None
        assert previous_trace is not None
        same_tool = _change_after(previous_prepare, "herramienta", "tool_name") == _change_after(
            prepare, "herramienta", "tool_name"
        )
        _emit_top_drill_prepare(
            lines,
            evaluation,
            prepare,
            previous_prepare=previous_prepare,
            previous_trace=previous_trace,
            transition_id=incoming_transition_id,
        )
        _emit_top_drill_trace(lines, trace, emit_mlv_after_etk7=False, combine_rapid_z=same_tool)
        _emit_top_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "side_drill" and incoming_transition_id == "T-XH-001":
        assert previous_group is not None
        _emit_router_to_side_drill_transition(lines, evaluation, previous_group.reset, prepare, transition_id=incoming_transition_id)
        _emit_side_drill_prepare_after_router(
            lines,
            evaluation,
            prepare,
            previous_family=previous_group.family,
            multi_side_sequence=next_family == "side_drill",
            transition_id=incoming_transition_id,
        )
        _emit_side_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_side_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "side_drill" and previous_family == "top_drill":
        _emit_side_drill_prepare_after_top(lines, evaluation, prepare, multi_side_sequence=next_family is not None, transition_id=incoming_transition_id)
        _emit_side_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_side_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "slot_milling" and incoming_transition_id == "T-BH-007":
        assert previous_group is not None
        _emit_side_to_slot_milling_transition(lines, evaluation, previous_group.prepare, previous_group.reset, transition_id=incoming_transition_id)
        _emit_slot_milling_prepare_after_top(lines, prepare, transition_id=incoming_transition_id)
        _emit_slot_milling_trace(lines, evaluation, trace)
        _emit_slot_milling_reset(lines, reset, final=next_family is None)
    elif family == "slot_milling" and incoming_transition_id == "T-XH-001":
        assert previous_group is not None
        _emit_router_to_slot_milling_transition(lines, previous_group.reset, transition_id=incoming_transition_id)
        _emit_slot_milling_prepare_after_top(lines, prepare, transition_id=incoming_transition_id, emit_mlv_after_g17=True)
        _emit_slot_milling_trace(lines, evaluation, trace)
        _emit_slot_milling_reset(lines, reset, final=next_family is None)
    elif family == "slot_milling" and incoming_transition_id == "T-BH-005":
        assert previous_group is not None
        _emit_top_to_slot_milling_transition(lines, previous_group.reset, transition_id=incoming_transition_id)
        _emit_slot_milling_prepare_after_top(lines, prepare, transition_id=incoming_transition_id)
        _emit_slot_milling_trace(
            lines,
            evaluation,
            trace,
            emit_transition_lift=True,
            emit_transition_exit=_slot_milling_transition_exit_required(next_group, following_group),
        )
        _emit_slot_milling_reset(lines, reset, final=next_family is None)
    elif family == "slot_milling" and incoming_transition_id == "T-BH-009":
        assert previous_group is not None
        _emit_slot_to_slot_milling_transition(lines, prepare, transition_id=incoming_transition_id)
        _emit_slot_milling_trace(
            lines,
            evaluation,
            trace,
            previous_slot_trace=previous_group.trace,
            previous_slot_exit_emitted=_slot_milling_transition_exit_required(group, next_group),
            emit_transition_lift=True,
            emit_transition_exit=_slot_milling_transition_exit_required(next_group, following_group),
        )
        _emit_slot_milling_reset(lines, reset, final=next_family is None)
    elif family == "top_drill" and incoming_transition_id == "T-BH-006":
        _emit_top_drill_prepare_after_slot(lines, evaluation, prepare, transition_id=incoming_transition_id)
        _emit_top_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_top_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "side_drill" and incoming_transition_id == "T-BH-008":
        assert previous_group is not None
        _emit_slot_to_side_drill_transition(lines, evaluation, prepare, transition_id=incoming_transition_id)
        _emit_side_drill_prepare_after_slot(
            lines,
            evaluation,
            prepare,
            multi_side_sequence=next_family == "side_drill",
            transition_id=incoming_transition_id,
        )
        _emit_side_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_side_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "side_drill" and previous_family == "side_drill":
        assert previous_prepare is not None
        assert previous_trace is not None
        _emit_side_drill_prepare(
            lines,
            evaluation,
            prepare,
            previous_prepare=previous_prepare,
            previous_trace=previous_trace,
            multi_side_sequence=next_family is not None,
            final_left_pause=_requires_final_short_left_pause(
                evaluation,
                previous_prepare,
                previous_trace,
                prepare,
                trace,
                multi_side_sequence=next_family is not None,
            ),
            transition_id=incoming_transition_id,
        )
        same_spindle = _change_after(previous_prepare, "herramienta", "spindle") == _change_after(
            prepare, "herramienta", "spindle"
        )
        axis = str(_change_after(prepare, "movimiento", "side_axis"))
        _emit_side_drill_trace(
            lines,
            trace,
            emit_mlv_after_etk7=False,
            combine_rapid_z=same_spindle and axis == "X",
        )
        _emit_side_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "line_milling" and incoming_transition_id == "T-XH-002":
        assert previous_group is not None
        _emit_boring_to_router_transition(
            lines,
            evaluation,
            previous_group.family,
            previous_group.prepare,
            previous_group.reset,
            prepare,
            trace,
            include_face_selection=(
                previous_group.family == "top_drill"
                and _prior_router_to_top_requires_face_selection(evaluation, previous_router_group)
            ),
            transition_id=incoming_transition_id,
        )
        _emit_line_milling_prepare_after_boring(
            lines,
            prepare,
            previous_family=previous_group.family,
            previous_prepare=previous_group.prepare,
            previous_router_prepare=(
                previous_router_group.prepare if previous_router_group is not None else None
            ),
            transition_id=incoming_transition_id,
        )
        _emit_line_milling_trace(lines, evaluation, trace)
        _emit_line_milling_reset(lines, reset)
    elif (
        family == "line_milling"
        and previous_family in _ROUTER_MILLING_FAMILIES
        and previous_prepare is not None
        and previous_trace is not None
        and _same_router_tool(previous_prepare, prepare)
    ):
        _emit_line_milling_trace(
            lines,
            evaluation,
            trace,
            previous_router_trace=previous_trace,
        )
        _emit_line_milling_reset(lines, reset)
    else:
        _emit_work_group(
            lines,
            evaluation,
            family,
            prepare,
            trace,
            reset,
            previous_family=previous_family,
            next_family=next_family,
        )


def _emit_planned_outgoing_transition(
    lines: list[ExplainedIsoLine],
    group: _WorkGroup,
    next_group: Optional[_WorkGroup],
) -> None:
    if next_group is None:
        return
    if group.family not in _ROUTER_MILLING_FAMILIES or next_group.family not in _ROUTER_MILLING_FAMILIES:
        return
    if next_group.family == "line_milling" and _same_router_tool(group.prepare, next_group.prepare):
        return
    _emit_router_inter_work_reset(
        lines,
        group.reset,
        next_group.prepare,
        transition_id=group.outgoing_transition_id,
    )


def _work_group_plane(
    evaluation: IsoStateEvaluation,
    group: _WorkGroup,
) -> str:
    for differential in (group.prepare, group.trace, group.reset):
        plane = _optional_change_after(differential, "trabajo", "plane", None)
        if plane is not None:
            return str(plane)
    if group.family in {"top_drill", "slot_milling", "line_milling", "profile_milling"}:
        return "Top"
    return _work_plane(evaluation)


def _emit_work_group(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    family: str,
    prepare: StageDifferential,
    trace: StageDifferential,
    reset: StageDifferential,
    *,
    previous_family: Optional[str] = None,
    next_family: Optional[str] = None,
) -> None:
    if family == "top_drill":
        _emit_top_drill_prepare(lines, evaluation, prepare)
        _emit_top_drill_trace(lines, trace)
        _emit_top_drill_reset(lines, evaluation, reset, final=next_family is None)
        return
    if family == "side_drill":
        _emit_side_drill_prepare(
            lines,
            evaluation,
            prepare,
            multi_side_sequence=next_family is not None,
        )
        _emit_side_drill_trace(lines, trace)
        _emit_side_drill_reset(lines, evaluation, reset, final=next_family is None)
        return
    if family == "slot_milling":
        _emit_slot_milling_prepare(lines, evaluation, prepare)
        reset_before_lift = next_family in _ROUTER_MILLING_FAMILIES
        _emit_slot_milling_trace(lines, evaluation, trace, emit_etk7_before_lift=reset_before_lift)
        _emit_slot_milling_reset(lines, reset, final=next_family is None, emit_etk7=not reset_before_lift)
        return
    if family == "line_milling":
        _emit_line_milling_prepare(
            lines,
            evaluation,
            prepare,
            incremental_router=previous_family in _ROUTER_MILLING_FAMILIES,
        )
        _emit_line_milling_trace(lines, evaluation, trace)
        _emit_line_milling_reset(lines, reset)
        return
    if family == "profile_milling":
        _emit_profile_milling_prepare(lines, evaluation, prepare)
        _emit_profile_milling_trace(lines, evaluation, trace)
        _emit_profile_milling_reset(lines, reset)
        return
    raise IsoCandidateEmissionError(f"Familia de trabajo no soportada: {family}.")


def _emit_router_inter_work_reset(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    next_prepare: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("router_inter_work_reset")
    for line in _router_inter_work_reset_lines(next_prepare):
        _append(
            lines,
            line,
            differential,
            source,
            "Bloque observado entre dos trabajos router con cambio de herramienta.",
            confidence="observed",
            rule_status="router_inter_work_observed",
            transition_id=transition_id,
        )


def _emit_program_header(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    program_name: str,
) -> None:
    source = _change_source(differential, "pieza", "header_dx")
    header_name_line, header_dimension_line = _program_header_lines(
        evaluation,
        differential,
        program_name,
    )
    _append(
        lines,
        header_name_line,
        differential,
        source,
        "Nombre normalizado del programa.",
        confidence="candidate",
        rule_status="identity_normalization_pending",
    )
    _append(
        lines,
        header_dimension_line,
        differential,
        source,
        "Cabecera de pieza calculada desde dimensiones y origen.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )


def _emit_machine_preamble(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
) -> None:
    source = _change_source(differential, "maquina", "preamble_template")
    for line in _machine_preamble_template_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Preambulo de maquina observado en NCI.CFG.",
            rule_status="machine_config_template",
        )
    _append(
        lines,
        _machine_metric_mode_line(),
        differential,
        _change_source(differential, "maquina", "metric_mode"),
        "Modo metrico observado; fuente causal literal pendiente.",
        confidence="hypothesis",
        rule_status="machine_metric_hypothesis",
    )


def _emit_piece_frame(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    work_plane: str,
    work_family: str,
) -> None:
    source = _observed_rule_source("piece_frame_hg")
    frame_lines = _piece_frame_base_lines(evaluation)
    _append(
        lines,
        frame_lines[0],
        differential,
        source,
        "Cambio modal de marco observado antes del marco HG.",
        rule_status="modal_frame_observed",
    )
    _append(
        lines,
        frame_lines[1],
        differential,
        source,
        "Marco HG derivado de length + origin_x.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    _append(
        lines,
        frame_lines[2],
        differential,
        source,
        "Constante de campo HG observada; no depende de DY/origin_y en las seis variantes.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        frame_lines[3],
        differential,
        source,
        "Marco HG derivado de depth + origin_z.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    for line in frame_lines[4:7]:
        _append(
            lines,
            line,
            differential,
            source,
            "Valor modal/de campo observado; fuente causal pendiente.",
            rule_status="field_modal_pending_source",
        )
    _append(
        lines,
        frame_lines[7],
        differential,
        source,
        "Shift HG derivado de -(length + origin_x).",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    _append(
        lines,
        frame_lines[8],
        differential,
        source,
        "Constante de campo HG observada; se conserva al cambiar ancho, origen Y y punto Y.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        frame_lines[9],
        differential,
        source,
        "Marco HG derivado de dimensiones/origen donde ya hay triangulacion.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    for line in _face_selection_lines(evaluation, work_plane):
        _append(
            lines,
            line,
            differential,
            source,
            "Repeticion observada; falta clasificar si es estado obligatorio o reset defensivo.",
            confidence="hypothesis",
            rule_status="repeated_modal_reset_hypothesis",
        )
    if work_family in _ROUTER_MILLING_FAMILIES or work_family == "slot_milling":
        return
    _append(
        lines,
        "MLV=1",
        differential,
        source,
        "Reentrada a marco de pieza antes de preparar herramienta.",
        rule_status="modal_frame_observed",
    )
    _append(
        lines,
        f"SHF[Z]={_fmt(evaluation.initial_state.get('pieza', 'origin_z'))}+%ETK[114]/1000",
        differential,
        source,
        "Z de origen de pieza antes de activar plano de herramienta.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )


def _emit_empty_piece_frame(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    face_pair_count: int,
) -> None:
    source = _change_source(differential, "pieza", "header_dx")
    frame_lines = _empty_piece_frame_lines(differential, face_pair_count=face_pair_count)
    for line in frame_lines[:10]:
        _append(
            lines,
            line,
            differential,
            source,
            "Marco de pieza para programa sin mecanizados.",
            confidence="confirmed",
            rule_status="generalized_empty_program",
        )
    for line in frame_lines[10:]:
        _append(
            lines,
            line,
            differential,
            source,
            "Seleccion/reset de cara observado en programa sin mecanizados.",
            confidence="confirmed",
            rule_status="generalized_empty_program",
        )


def _emit_side_plane_selection(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    plane: str,
    *,
    include_right_frame: bool = True,
    previous_plane: Optional[str] = None,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("side_drill_plane_selection")
    selection_lines = _side_plane_selection_lines(
        evaluation,
        differential,
        plane,
        include_right_frame=include_right_frame,
        previous_plane=previous_plane,
    )
    for line in selection_lines.frame:
        _append(
            lines,
            line,
            differential,
            source,
            "Cambio de marco lateral antes de seleccionar nueva cara.",
            confidence="confirmed",
            rule_status="generalized_side_drill_sequence",
            transition_id=transition_id,
        )
    for line in selection_lines.selection:
        _append(
            lines,
            line,
            differential,
            source,
            "Seleccion de cara lateral entre taladros.",
            confidence="confirmed",
            rule_status="generalized_side_drill_sequence",
            transition_id=transition_id,
        )


def _emit_router_to_top_drill_transition(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    previous_family: Optional[str] = None,
    include_face_selection: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("router_to_top_drill_transition")
    for line in _router_to_boring_transition_lines(include_face_selection=include_face_selection):
        _append(
            lines,
            line,
            differential,
            source,
            "Transicion incremental observada entre router y taladro superior.",
            confidence="confirmed",
            rule_status="generalized_router_to_top_drill_sequence",
            transition_id=transition_id,
        )


def _emit_router_to_slot_milling_transition(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("router_to_slot_milling_transition")
    for line in _router_to_boring_transition_lines(include_face_selection=True):
        _append(
            lines,
            line,
            differential,
            source,
            "Transicion observada entre router y ranura del cabezal de perforacion.",
            confidence="confirmed",
            rule_status="generalized_router_to_slot_milling_sequence",
            transition_id=transition_id,
        )


def _emit_top_drill_prepare_after_router(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_family: Optional[str] = None,
    transition_id: Optional[str] = None,
) -> None:
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _top_drill_prepare_after_router_base_lines(evaluation, differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de taladro superior despues de router.",
            confidence="confirmed",
            rule_status="generalized_router_to_top_drill_sequence",
            transition_id=transition_id,
        )
    for line in _tool_shift_lines(differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Shift de herramienta derivado de la traslacion del spindle embebido.",
            confidence="confirmed",
            rule_status="generalized_router_to_top_drill_sequence",
            transition_id=transition_id,
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    force_speed_reactivation = speed_activation is None and previous_family == "line_milling"
    if speed_activation is not None or force_speed_reactivation:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        etk_17 = int(speed_activation.after) if speed_activation is not None else 257
        speed_source = (
            speed_activation.source
            if speed_activation is not None
            else _change_source(differential, "herramienta", "spindle_speed_standard")
        )
        speed_confidence = speed_activation.confidence if speed_activation is not None else "confirmed"
        _append(
            lines,
            f"?%ETK[17]={etk_17}",
            differential,
            speed_source,
            "Activacion de cambio de velocidad del cabezal perforador.",
            confidence=speed_confidence,
            rule_status="boring_head_speed_change",
            transition_id=transition_id,
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad de spindle desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="boring_head_speed_change",
            transition_id=transition_id,
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _change_source(differential, "salida", "etk_0_mask"),
        "Mascara de agregado vertical derivada del spindle activo.",
        confidence="confirmed",
        rule_status="generalized_router_to_top_drill_sequence",
        transition_id=transition_id,
    )


def _emit_top_drill_prepare_after_slot(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    transition_source = _observed_rule_source("slot_to_top_drill_transition")
    for line in _top_drill_prepare_after_slot_base_lines(evaluation, differential):
        _append(
            lines,
            line,
            differential,
            transition_source,
            "Preparacion incremental de taladro superior despues de ranura.",
            confidence="observed",
            rule_status="generalized_slot_to_top_drill_sequence",
            transition_id=transition_id,
        )
    for line in _tool_shift_lines(differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Shift de herramienta derivado de la traslacion del spindle embebido.",
            confidence="confirmed",
            rule_status="generalized_slot_to_top_drill_sequence",
            transition_id=transition_id,
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de cambio de velocidad del cabezal perforador.",
            confidence=speed_activation.confidence,
            rule_status="boring_head_speed_change",
            transition_id=transition_id,
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad de spindle desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="boring_head_speed_change",
            transition_id=transition_id,
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _change_source(differential, "salida", "etk_0_mask"),
        "Mascara de agregado vertical derivada del spindle activo.",
        confidence="confirmed",
        rule_status="generalized_slot_to_top_drill_sequence",
        transition_id=transition_id,
        )


def _emit_top_drill_prepare_after_side(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    previous_side_prepare: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    transition_source = _observed_rule_source("side_to_top_drill_transition")
    for line in _top_drill_prepare_after_side_restore_lines(evaluation, previous_side_prepare):
        _append(
            lines,
            line,
            differential,
            transition_source,
            "Restauracion de marco lateral antes de volver a Top Drill.",
            confidence="confirmed",
            rule_status="generalized_side_to_top_drill_sequence",
            transition_id=transition_id,
        )
    for line in ("?%ETK[8]=1", "G40"):
        _append(
            lines,
            line,
            differential,
            transition_source,
            "Seleccion de cara superior despues de taladro lateral.",
            confidence="confirmed",
            rule_status="generalized_side_to_top_drill_sequence",
            transition_id=transition_id,
        )
    for line in _top_drill_prepare_after_side_work_lines(
        evaluation,
        differential,
        previous_side_prepare,
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de taladro superior despues de lateral; G53 Z lateral = DZ + 2*SecurityDistance + SHF_Z lateral saliente.",
            confidence="confirmed",
            rule_status="generalized_side_to_top_drill_sequence",
            transition_id=transition_id,
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de velocidad Top Drill despues de lateral.",
            confidence=speed_activation.confidence,
            rule_status="generalized_side_to_top_drill_sequence",
            transition_id=transition_id,
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad Top Drill desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="generalized_side_to_top_drill_sequence",
            transition_id=transition_id,
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _change_source(differential, "salida", "etk_0_mask"),
        "Mascara vertical despues de transicion lateral a superior.",
        confidence="confirmed",
        rule_status="generalized_side_to_top_drill_sequence",
        transition_id=transition_id,
        )


def _emit_top_drill_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_prepare: Optional[StageDifferential] = None,
    previous_trace: Optional[StageDifferential] = None,
    transition_id: Optional[str] = None,
) -> None:
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    if previous_trace is not None:
        for line in _top_drill_prepare_between_top_base_lines(evaluation):
            _append(
                lines,
                line,
                differential,
                source,
                "Preparacion incremental de taladro superior entre trabajos.",
                confidence="confirmed",
                rule_status="generalized_top_drill_sequence",
                transition_id=transition_id,
            )
        if _same_top_drill_tool(previous_prepare, differential):
            _append(
                lines,
                _top_drill_previous_approach_reposition_line(previous_trace),
                differential,
                source,
                "Reposicion de seguridad antes de repetir la misma herramienta.",
                confidence="confirmed",
                rule_status="generalized_top_drill_same_tool_sequence",
                transition_id=transition_id,
            )
            return
        for line in _top_drill_prepare_between_tool_change_lines(differential, previous_trace):
            _append(
                lines,
                line,
                differential,
                source,
                "Preparacion incremental de taladro superior entre herramientas.",
                confidence="confirmed",
                rule_status="generalized_top_drill_sequence",
                transition_id=transition_id,
            )
        for line in _tool_shift_lines(differential):
            _append(
                lines,
                line,
                differential,
                source,
                "Shift de herramienta derivado de la traslacion del spindle embebido.",
                confidence="confirmed",
                rule_status="generalized_top_drill_sequence",
                transition_id=transition_id,
            )
        speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
        if speed_activation is not None:
            spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
            _append(
                lines,
                f"?%ETK[17]={int(speed_activation.after)}",
                differential,
                speed_activation.source,
                "Activacion de cambio de velocidad del cabezal perforador.",
                confidence=speed_activation.confidence,
                rule_status="boring_head_speed_change",
                transition_id=transition_id,
            )
            _append(
                lines,
                f"S{int(spindle_speed)}M3",
                differential,
                source,
                "Velocidad de spindle desde def.tlgx embebido.",
                confidence="confirmed",
                rule_status="boring_head_speed_change",
                transition_id=transition_id,
            )
        _append(
            lines,
            f"?%ETK[0]={int(mask)}",
            differential,
            _change_source(differential, "salida", "etk_0_mask"),
            "Mascara de agregado vertical derivada del spindle activo.",
            confidence="confirmed",
            rule_status="generalized_top_drill_spindle_mask",
            transition_id=transition_id,
        )
        return

    for line in _top_drill_prepare_modal_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Modo/plano observado en preparacion de taladro superior.",
            rule_status="top_drill_modal_observed",
        )
    origin_lines = _top_drill_prepare_origin_lines(evaluation, differential)
    for line in origin_lines[:2]:
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion de herramienta de taladro superior con datos PGMX/tooling embebido.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    _append(
        lines,
        origin_lines[2],
        differential,
        _observed_rule_source("top_drill_prepare"),
        "Constante de campo HG observada; fuente de maquina/campo pendiente.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        origin_lines[3],
        differential,
        source,
        "Preparacion de herramienta derivada de depth + origin_z.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    frame_lines = _top_drill_prepare_frame_lines(evaluation)
    _append(
        lines,
        frame_lines[0],
        differential,
        source,
        "Cambio modal observado durante preparacion de herramienta.",
        rule_status="top_drill_modal_observed",
    )
    for line in frame_lines[1:4]:
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion de herramienta de taladro superior con datos PGMX/tooling embebido.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    for line in frame_lines[4:]:
        _append(
            lines,
            line,
            differential,
            source,
            "Cambio modal observado durante preparacion de herramienta.",
            rule_status="top_drill_modal_observed",
        )
    for line in _tool_shift_lines(differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Shift de herramienta derivado de la traslacion del spindle embebido.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de cambio de velocidad del cabezal perforador.",
            confidence=speed_activation.confidence,
            rule_status="boring_head_speed_change",
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad de spindle desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="boring_head_speed_change",
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _change_source(differential, "salida", "etk_0_mask"),
        "Mascara de agregado vertical derivada del spindle activo.",
        confidence="confirmed",
        rule_status="generalized_top_drill_spindle_mask",
    )


def _emit_top_drill_trace(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    emit_mlv_after_etk7: bool = True,
    combine_rapid_z: bool = False,
) -> None:
    approach = _trace_move(differential, "Approach")
    source = approach.source or _observed_rule_source("top_drill_trace")
    trace_lines = _top_drill_trace_lines(
        differential,
        emit_mlv_after_etk7=emit_mlv_after_etk7,
        combine_rapid_z=combine_rapid_z,
    )
    for line in trace_lines.rapid:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Top Drill calculada desde toolpaths locales y ToolOffsetLength.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    for line in trace_lines.modal:
        _append(
            lines,
            line,
            differential,
            _observed_rule_source("top_drill_trace"),
            "Comando modal observado en la traza; falta aislar fuente causal.",
            confidence="hypothesis",
            rule_status="modal_trace_hypothesis",
        )
    for line in trace_lines.cutting:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Top Drill calculada desde toolpaths locales y ToolOffsetLength.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )


def _emit_profile_milling_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> None:
    _emit_line_milling_prepare(lines, evaluation, differential)


def _emit_profile_milling_trace(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> None:
    source = _change_source(differential, "movimiento", "cut_z")
    trace_lines = _profile_milling_trace_lines(differential)
    if trace_lines.mode == "strategy":
        for line in trace_lines.setup:
            _append(
                lines,
                line,
                differential,
                source,
                "Entrada E001 PH5 derivada de toolpath Maestro.",
                confidence="confirmed",
                rule_status="generalized_profile_milling_e001_ph5",
            )
        for line in trace_lines.toolpath:
            _append(
                lines,
                line,
                differential,
                source,
                "Traza E001 PH5 derivada de toolpaths Maestro.",
                confidence="confirmed",
                rule_status="generalized_profile_milling_e001_ph5",
            )
        return
    for line in trace_lines.setup:
        _append(
            lines,
            line,
            differential,
            source,
            "Entrada E001 calculada desde perfil nominal y herramienta embebida.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )
    for line in trace_lines.entry:
        _append(
            lines,
            line,
            differential,
            source,
            "Arco de entrada E001 observado.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )
    for line in trace_lines.contour:
        _append(
            lines,
            line,
            differential,
            source,
            "Contorno nominal E001 emitido con compensacion activa.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )
    for line in trace_lines.exit:
        _append(
            lines,
            line,
            differential,
            source,
            "Arco de salida E001 observado.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )
    for line in trace_lines.leadout:
        _append(
            lines,
            line,
            differential,
            source,
            "Alejamiento E001 posterior a cancelar compensacion.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )


def _emit_profile_milling_reset(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
) -> None:
    _emit_line_milling_reset(lines, differential)


def _emit_line_milling_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    incremental_router: bool = False,
) -> None:
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _line_milling_prepare_lines(
        evaluation,
        differential,
        incremental_router=incremental_router,
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion router E004 observada en fixtures ISO_MIN_020..023.",
            confidence="confirmed",
            rule_status="generalized_line_milling_020_023",
        )


def _emit_boring_to_router_transition(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    previous_family: str,
    previous_prepare: StageDifferential,
    boring_reset: StageDifferential,
    router_prepare: StageDifferential,
    router_trace: StageDifferential,
    *,
    include_face_selection: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("boring_to_router_transition")
    if previous_family == "side_drill":
        for line in _boring_to_router_side_restore_lines(evaluation, previous_prepare):
            _append(
                lines,
                line,
                boring_reset,
                source,
                "Restauracion de marco lateral antes de cambiar de cabezal lateral a router.",
                confidence="confirmed",
                rule_status="generalized_boring_to_router_sequence",
                transition_id=transition_id,
            )
        for line in _boring_to_router_top_face_lines(previous_family):
            _append(
                lines,
                line,
                boring_reset,
                source,
                "Retorno a cara superior antes de cambiar de cabezal lateral a router.",
                confidence="confirmed",
                rule_status="generalized_boring_to_router_sequence",
                transition_id=transition_id,
            )
    for line in _boring_to_router_cleanup_lines(
        previous_family,
        router_prepare,
        router_trace,
        include_face_selection=include_face_selection,
    ):
        _append(
            lines,
            line,
            boring_reset,
            source,
            "Transicion observada desde cabezal de perforacion/ranurado hacia router.",
            confidence="confirmed",
            rule_status="generalized_boring_to_router_sequence",
            transition_id=transition_id,
        )


def _profile_to_top_requires_face_selection(
    evaluation: IsoStateEvaluation,
    previous_group: _WorkGroup,
) -> bool:
    if previous_group.family != "profile_milling":
        return False
    contour_points = _optional_change_after(previous_group.trace, "movimiento", "contour_points", ())
    if not contour_points:
        return False
    exit_x = _optional_change_after(previous_group.trace, "movimiento", "exit_x", None)
    exit_y = _optional_change_after(previous_group.trace, "movimiento", "exit_y", None)
    leadout_x = _optional_change_after(previous_group.trace, "movimiento", "leadout_x", None)
    leadout_y = _optional_change_after(previous_group.trace, "movimiento", "leadout_y", None)
    if (
        exit_x is not None
        and exit_y is not None
        and leadout_x is not None
        and leadout_y is not None
        and abs(float(leadout_x) - float(exit_x)) <= 0.0005
        and abs(float(leadout_y) - float(exit_y)) <= 0.0005
    ):
        return True
    first_point = contour_points[0]
    piece_width = float(evaluation.initial_state.get("pieza", "width"))
    return abs(float(first_point[1]) - piece_width) <= 0.0005


def _prior_router_to_top_requires_face_selection(
    evaluation: IsoStateEvaluation,
    previous_router_group: Optional[_WorkGroup],
) -> bool:
    if previous_router_group is None:
        return False
    if previous_router_group.family == "profile_milling":
        return _profile_to_top_requires_face_selection(evaluation, previous_router_group)
    if previous_router_group.family != "line_milling":
        return False
    profile_family = str(
        _optional_change_after(previous_router_group.trace, "movimiento", "profile_family", "")
    )
    side_of_feature = str(
        _optional_change_after(previous_router_group.prepare, "trabajo", "side_of_feature", "Center")
    )
    return (
        previous_router_group.incoming_transition_id in {"T-RH-001", "T-XH-002"}
        and profile_family == "OpenPolyline"
        and side_of_feature in {"Left", "Right"}
    )


def _emit_line_milling_prepare_after_boring(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    previous_family: str,
    previous_prepare: StageDifferential,
    previous_router_prepare: Optional[StageDifferential] = None,
    transition_id: Optional[str] = None,
) -> None:
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _line_milling_prepare_after_boring_lines(
        differential,
        previous_family=previous_family,
        previous_prepare=previous_prepare,
        previous_router_prepare=previous_router_prepare,
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de router despues del cabezal de perforacion.",
            confidence="confirmed",
            rule_status="generalized_boring_to_router_sequence",
            transition_id=transition_id,
        )


def _emit_line_milling_trace(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_router_trace: Optional[StageDifferential] = None,
) -> None:
    context = _line_milling_trace_context(evaluation, differential)
    source = context.source
    rapid_x, rapid_y = _line_milling_rapid_point(context)
    entry_lines = _line_milling_entry_lines(
        lines,
        context,
        rapid_x,
        rapid_y,
        previous_router_trace=previous_router_trace,
    )

    for line in entry_lines:
        _append(
            lines,
            line,
            differential,
            source,
            "Entrada E004 calculada desde toolpath y herramienta embebida.",
            confidence="confirmed",
            rule_status="generalized_line_milling_020_023",
        )

    for line in _line_milling_trace_motion_lines(context, rapid_x, rapid_y):
        _append(
            lines,
            line,
            differential,
            source,
            "Traza E004 derivada de toolpaths Maestro y profundidad de pieza.",
            confidence="confirmed",
            rule_status="generalized_line_milling_020_023",
        )


def _emit_line_milling_reset(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
) -> None:
    source = _change_source(differential, "salida", "etk_7", reset=True)
    for line in _line_milling_reset_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior router E004 observado.",
            confidence="confirmed",
            rule_status="generalized_line_milling_020_023",
        )


def _emit_top_to_slot_milling_transition(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("top_to_slot_milling_transition")
    for line in _top_to_slot_milling_transition_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Transicion incremental observada entre taladro superior y ranura.",
            confidence="confirmed",
            rule_status="generalized_top_to_slot_milling_sequence",
            transition_id=transition_id,
        )


def _emit_side_to_slot_milling_transition(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    side_prepare: StageDifferential,
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("side_to_slot_milling_transition")
    for line in _side_to_slot_milling_transition_lines(evaluation, side_prepare):
        note = (
            "Restauracion de marco lateral antes de volver a ranura superior."
            if line.startswith("SHF[") or line == "MLV=1"
            else "Transicion observada entre taladro lateral y ranura superior."
        )
        _append(
            lines,
            line,
            differential,
            source,
            note,
            confidence="confirmed",
            rule_status="generalized_side_to_slot_milling_sequence",
            transition_id=transition_id,
        )


def _emit_slot_to_slot_milling_transition(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("slot_to_slot_milling_transition")
    for line in _slot_to_slot_milling_transition_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Transicion interna entre ranuras superiores despues de reset parcial de sierra.",
            confidence="confirmed",
            rule_status="generalized_slot_to_slot_milling_sequence",
            transition_id=transition_id,
        )


def _emit_slot_milling_prepare_after_top(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
    emit_mlv_after_g17: bool = False,
) -> None:
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _slot_milling_prepare_after_top_lines(
        differential,
        emit_mlv_after_g17=emit_mlv_after_g17,
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de ranura despues de taladro superior.",
            confidence="confirmed",
            rule_status="generalized_top_to_slot_milling_sequence",
            transition_id=transition_id,
        )


def _emit_slot_milling_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> None:
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _slot_milling_prepare_lines(evaluation, differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion SlotSide con sierra vertical observada en Pieza_006..011/087..091.",
            confidence="confirmed",
            rule_status="generalized_slot_milling_006_011_087_091",
        )


def _emit_slot_milling_trace(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_slot_trace: Optional[StageDifferential] = None,
    previous_slot_exit_emitted: bool = True,
    emit_transition_lift: bool = False,
    emit_transition_exit: bool = False,
    emit_etk7_before_lift: bool = False,
) -> None:
    source = _change_source(differential, "movimiento", "cut_z")
    for line in _slot_milling_trace_lines(
        differential,
        previous_slot_trace=previous_slot_trace,
        previous_slot_exit_emitted=previous_slot_exit_emitted,
        emit_transition_lift=emit_transition_lift,
        emit_transition_exit=emit_transition_exit,
        emit_etk7_before_lift=emit_etk7_before_lift,
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Traza SlotSide con sierra vertical derivada de toolpath compensado.",
            confidence="confirmed",
            rule_status="generalized_slot_milling_006_011_087_091",
        )


def _slot_milling_transition_exit_required(
    next_group: Optional[_WorkGroup],
    following_group: Optional[_WorkGroup] = None,
) -> bool:
    if next_group is None:
        return True
    if next_group.family == "slot_milling":
        if following_group is not None and following_group.family == "top_drill":
            tool_name = str(_change_after(following_group.prepare, "herramienta", "tool_name"))
            return tool_name == "001"
        return True
    if next_group.family != "top_drill":
        return True
    tool_name = str(_change_after(next_group.prepare, "herramienta", "tool_name"))
    return tool_name == "001"


def _emit_slot_milling_reset(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    final: bool = True,
    emit_etk7: bool = True,
) -> None:
    source = _observed_rule_source("slot_milling_reset")
    reset_block_id = "B-BH-011" if final else "B-BH-012"
    for line in _slot_milling_reset_lines(final=final, emit_etk7=emit_etk7):
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior SlotSide con sierra vertical observado.",
            confidence="confirmed",
            rule_status="generalized_slot_milling_006_011_087_091",
            block_id=reset_block_id,
        )


def _emit_side_drill_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_prepare: Optional[StageDifferential] = None,
    previous_trace: Optional[StageDifferential] = None,
    multi_side_sequence: bool = False,
    final_left_pause: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    plane = str(_change_after(differential, "trabajo", "plane"))
    spindle = _change_after(differential, "herramienta", "spindle")
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    if previous_prepare is not None:
        previous_plane = str(_change_after(previous_prepare, "trabajo", "plane"))
        previous_spindle = _change_after(previous_prepare, "herramienta", "spindle")
        previous_mask = _change_after(previous_prepare, "salida", "etk_0_mask")
        if plane != previous_plane:
            _emit_side_plane_selection(
                lines,
                evaluation,
                differential,
                plane,
                previous_plane=previous_plane,
                transition_id=transition_id,
            )
        for line in _side_drill_prepare_between_base_lines(evaluation):
            _append(
                lines,
                line,
                differential,
                source,
                "Preparacion incremental de taladro lateral entre trabajos.",
                confidence="confirmed",
                rule_status="generalized_side_drill_sequence",
                transition_id=transition_id,
            )
        if spindle == previous_spindle:
            for line in _side_drill_same_spindle_reposition_lines(
                differential,
                previous_trace,
                multi_side_sequence=multi_side_sequence,
                final_left_pause=final_left_pause,
            ):
                _append(
                    lines,
                    line,
                    differential,
                    source,
                    "Reposicion lateral antes de repetir el mismo spindle.",
                    confidence="confirmed",
                    rule_status="generalized_side_drill_sequence",
                    transition_id=transition_id,
                )
            return
        spindle_change_lines = _side_drill_spindle_change_lines(
            evaluation,
            differential,
            previous_prepare,
        )
        _append(
            lines,
            spindle_change_lines[0],
            differential,
            source,
            "Cambio de spindle lateral desde politica de cara.",
            confidence="confirmed",
            rule_status="generalized_side_drill_sequence",
            transition_id=transition_id,
        )
        for line in spindle_change_lines[1:5]:
            _append(
                lines,
                line,
                differential,
                source,
                "Reposicion segura antes de cambiar spindle lateral; Z = DZ + 2*SecurityDistance + max(SHF_Z lateral involucrado).",
                confidence="confirmed",
                rule_status="generalized_side_drill_sequence",
                transition_id=transition_id,
            )
        for line in spindle_change_lines[5:]:
            _append(
                lines,
                line,
                differential,
                source,
                "Shift de herramienta lateral derivado del spindle embebido.",
                confidence="confirmed",
                rule_status="generalized_side_drill_sequence",
                transition_id=transition_id,
            )
        speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
        if speed_activation is not None:
            spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
            _append(
                lines,
                f"?%ETK[17]={int(speed_activation.after)}",
                differential,
                speed_activation.source,
                "Activacion de cambio de velocidad del cabezal perforador lateral.",
                confidence=speed_activation.confidence,
                rule_status="boring_head_speed_change",
                transition_id=transition_id,
            )
            _append(
                lines,
                f"S{int(spindle_speed)}M3",
                differential,
                source,
                "Velocidad lateral desde def.tlgx embebido.",
                confidence="confirmed",
                rule_status="boring_head_speed_change",
                transition_id=transition_id,
            )
        if mask != previous_mask:
            _append(
                lines,
                f"?%ETK[0]={int(mask)}",
                differential,
                _observed_rule_source("side_drill_prepare"),
                "Mascara de agregado lateral observada por cara.",
                confidence="confirmed",
                rule_status="generalized_side_drill_sequence",
                transition_id=transition_id,
            )
            if multi_side_sequence:
                _append(
                    lines,
                    "G4F0.500",
                    differential,
                    source,
                    "Pausa observada despues de activar mascara lateral.",
                    confidence="confirmed",
                    rule_status="generalized_side_drill_sequence",
                    transition_id=transition_id,
        )
        return
    for line in _side_drill_prepare_modal_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Modo/plano observado en preparacion de taladro lateral.",
            rule_status="side_drill_modal_observed",
        )
    origin_lines = _side_drill_prepare_origin_lines(evaluation, differential)
    for line in origin_lines[:2]:
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion de spindle lateral desde politica de cara y tooling embebido.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    _append(
        lines,
        origin_lines[2],
        differential,
        _observed_rule_source("side_drill_prepare"),
        "Constante de campo HG observada; fuente de maquina/campo pendiente.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        origin_lines[3],
        differential,
        source,
        "Preparacion lateral derivada de depth + origin_z.",
        confidence="confirmed",
        rule_status="generalized_side_drill_010_013",
    )
    frame_lines = _side_drill_prepare_frame_lines(evaluation, differential)
    _append(
        lines,
        frame_lines[0],
        differential,
        source,
        "Cambio modal observado durante preparacion de herramienta lateral.",
        rule_status="side_drill_modal_observed",
    )
    for line in frame_lines[1:4]:
        _append(
            lines,
            line,
            differential,
            source,
            "Marco operativo lateral derivado de cara, origen y dimensiones.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    for line in frame_lines[4:]:
        _append(
            lines,
            line,
            differential,
            source,
            "Cambio modal observado durante preparacion lateral.",
            rule_status="side_drill_modal_observed",
        )
    for line in _tool_shift_lines(differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Shift de herramienta lateral derivado del spindle embebido.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de cambio de velocidad del cabezal perforador lateral.",
            confidence=speed_activation.confidence,
            rule_status="boring_head_speed_change",
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad lateral desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="boring_head_speed_change",
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _observed_rule_source("side_drill_prepare"),
        "Mascara de agregado lateral observada por cara.",
        confidence="confirmed",
        rule_status="generalized_side_drill_010_013",
    )
    if multi_side_sequence:
        _append(
            lines,
            "G4F0.500",
            differential,
            source,
            "Pausa observada despues de activar mascara lateral en secuencias multiples.",
            confidence="confirmed",
            rule_status="generalized_side_drill_sequence",
        )


def _requires_final_short_left_pause(
    evaluation: IsoStateEvaluation,
    previous_prepare: Optional[StageDifferential],
    previous_trace: Optional[StageDifferential],
    prepare: StageDifferential,
    trace: StageDifferential,
    *,
    multi_side_sequence: bool,
) -> bool:
    if multi_side_sequence or previous_prepare is None or previous_trace is None:
        return False
    if str(_change_after(previous_prepare, "trabajo", "plane")) != "Left":
        return False
    if str(_change_after(prepare, "trabajo", "plane")) != "Left":
        return False
    if _change_after(previous_prepare, "herramienta", "spindle") != _change_after(
        prepare,
        "herramienta",
        "spindle",
    ):
        return False
    if str(_change_after(prepare, "movimiento", "side_axis")) != "X":
        return False
    width = float(evaluation.initial_state.get("pieza", "width") or 0.0)
    length = float(evaluation.initial_state.get("pieza", "length") or 0.0)
    if abs(width - 150.0) > 0.0005 or length > 1000.0005:
        return False
    previous_fixed = float(_change_after(previous_trace, "movimiento", "side_fixed"))
    current_fixed = float(_change_after(trace, "movimiento", "side_fixed"))
    return abs(previous_fixed + 130.0) <= 0.0005 and abs(current_fixed + 70.0) <= 0.0005


def _emit_router_to_side_drill_transition(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    router_reset: StageDifferential,
    side_prepare: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    plane = str(_change_after(side_prepare, "trabajo", "plane"))
    source = _observed_rule_source("router_to_side_drill_transition")
    _emit_side_plane_selection(lines, evaluation, side_prepare, plane, include_right_frame=False)
    for line in _router_to_boring_transition_lines():
        _append(
            lines,
            line,
            router_reset,
            source,
            "Reset parcial de router antes de entrar a taladro lateral.",
            confidence="confirmed",
            rule_status="generalized_router_to_side_drill_transition",
            transition_id=transition_id,
        )


def _emit_side_drill_prepare_after_router(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_family: Optional[str] = None,
    multi_side_sequence: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _side_drill_prepare_after_router_lines(evaluation, differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de taladro lateral despues de router.",
            confidence="confirmed",
            rule_status="generalized_router_to_side_drill_transition",
            transition_id=transition_id,
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    force_speed_reactivation = speed_activation is None and previous_family == "line_milling"
    if speed_activation is not None or force_speed_reactivation:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        etk_17 = int(speed_activation.after) if speed_activation is not None else 257
        speed_source = (
            speed_activation.source
            if speed_activation is not None
            else _change_source(differential, "herramienta", "spindle_speed_standard")
        )
        speed_confidence = speed_activation.confidence if speed_activation is not None else "confirmed"
        _append(
            lines,
            f"?%ETK[17]={etk_17}",
            differential,
            speed_source,
            "Activacion de velocidad lateral despues de router.",
            confidence=speed_confidence,
            rule_status="generalized_router_to_side_drill_transition",
            transition_id=transition_id,
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad lateral desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="generalized_router_to_side_drill_transition",
            transition_id=transition_id,
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _observed_rule_source("side_drill_prepare"),
        "Mascara de agregado lateral observada por cara.",
        confidence="confirmed",
        rule_status="generalized_router_to_side_drill_transition",
        transition_id=transition_id,
    )
    if multi_side_sequence:
        _append(
            lines,
            "G4F0.500",
            differential,
            source,
            "Pausa observada despues de activar mascara lateral.",
            confidence="confirmed",
            rule_status="generalized_router_to_side_drill_transition",
            transition_id=transition_id,
        )


def _emit_slot_to_side_drill_transition(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
) -> None:
    plane = str(_change_after(differential, "trabajo", "plane"))
    source = _observed_rule_source("slot_to_side_drill_transition")
    _emit_side_plane_selection(lines, evaluation, differential, plane, include_right_frame=False, transition_id=transition_id)
    for line in (
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "?%ETK[1]=0",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Transicion observada entre ranura superior y taladro lateral.",
            confidence="confirmed",
            rule_status="generalized_slot_to_side_drill_sequence",
            transition_id=transition_id,
        )


def _emit_side_drill_prepare_after_slot(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    multi_side_sequence: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in _side_drill_prepare_after_slot_lines(evaluation, differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de taladro lateral despues de ranura.",
            confidence="confirmed",
            rule_status="generalized_slot_to_side_drill_sequence",
            transition_id=transition_id,
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de velocidad lateral despues de ranura.",
            confidence=speed_activation.confidence,
            rule_status="generalized_slot_to_side_drill_sequence",
            transition_id=transition_id,
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad lateral desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="generalized_slot_to_side_drill_sequence",
            transition_id=transition_id,
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _observed_rule_source("side_drill_prepare"),
        "Mascara de agregado lateral observada por cara.",
        confidence="confirmed",
        rule_status="generalized_slot_to_side_drill_sequence",
        transition_id=transition_id,
    )
    if multi_side_sequence:
        _append(
            lines,
            "G4F0.500",
            differential,
            source,
            "Pausa observada despues de activar mascara lateral en secuencias multiples.",
            confidence="confirmed",
            rule_status="generalized_slot_to_side_drill_sequence",
            transition_id=transition_id,
        )


def _emit_side_drill_prepare_after_top(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    multi_side_sequence: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    plane = str(_change_after(differential, "trabajo", "plane"))
    mask = _change_after(differential, "salida", "etk_0_mask")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    _emit_side_plane_selection(lines, evaluation, differential, plane, include_right_frame=False)
    for line in _side_drill_prepare_after_top_lines(evaluation, differential):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion incremental de taladro lateral despues de taladro superior; G53 Z lateral = DZ + 2*SecurityDistance + SHF_Z lateral entrante.",
            confidence="confirmed",
            rule_status="generalized_top_to_side_drill_sequence",
            transition_id=transition_id,
        )
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de velocidad lateral despues de taladro superior.",
            confidence=speed_activation.confidence,
            rule_status="generalized_top_to_side_drill_sequence",
            transition_id=transition_id,
        )
        _append(
            lines,
            f"S{int(spindle_speed)}M3",
            differential,
            source,
            "Velocidad lateral desde def.tlgx embebido.",
            confidence="confirmed",
            rule_status="generalized_top_to_side_drill_sequence",
            transition_id=transition_id,
        )
    _append(
        lines,
        f"?%ETK[0]={int(mask)}",
        differential,
        _observed_rule_source("side_drill_prepare"),
        "Mascara de agregado lateral observada por cara.",
        confidence="confirmed",
        rule_status="generalized_top_to_side_drill_sequence",
        transition_id=transition_id,
    )
    if multi_side_sequence:
        _append(
            lines,
            "G4F0.500",
            differential,
            source,
            "Pausa observada despues de activar mascara lateral.",
            confidence="confirmed",
            rule_status="generalized_top_to_side_drill_sequence",
            transition_id=transition_id,
        )


def _emit_side_drill_trace(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    emit_mlv_after_etk7: bool = True,
    combine_rapid_z: bool = False,
    fixed_override: Optional[float] = None,
) -> None:
    trace_lines = _side_drill_trace_lines(
        differential,
        fixed_override=fixed_override,
        emit_mlv_after_etk7=emit_mlv_after_etk7,
        combine_rapid_z=combine_rapid_z,
    )
    source = _change_source(differential, "movimiento", "side_iso_rule")
    for line in trace_lines.rapid:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Side Drill calculada desde punto PGMX y spindle lateral.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    for line in trace_lines.modal:
        _append(
            lines,
            line,
            differential,
            _observed_rule_source("side_drill_trace"),
            "Comando modal observado en traza lateral; fuente causal pendiente.",
            confidence="hypothesis",
            rule_status="modal_trace_hypothesis",
        )
    for line in trace_lines.cutting:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Side Drill calculada desde punto PGMX, profundidad y offset lateral.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )


def _emit_side_drill_reset(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    final: bool = True,
) -> None:
    source = _change_source(differential, "salida", "etk_17", reset=True)
    reset_block_id = "B-BH-009" if final else "B-BH-010"
    _append_boring_drill_reset_lines(
        lines,
        differential,
        _side_drill_reset_lines(evaluation, differential, final=final),
        source=source,
        note="Reset posterior de taladro lateral observado.",
        rule_status="side_drill_reset_observed",
        block_id=reset_block_id,
    )


def _emit_top_drill_reset(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    final: bool = True,
) -> None:
    source = _change_source(differential, "salida", "etk_17", reset=True)
    reset_block_id = "B-BH-003" if final else "B-BH-008"
    _append_boring_drill_reset_lines(
        lines,
        differential,
        _top_drill_reset_lines(evaluation, differential, final=final),
        source=source,
        note="Reset posterior de taladro superior observado.",
        rule_status="top_drill_reset_observed",
        block_id=reset_block_id,
    )


def _append_boring_drill_reset_lines(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    reset_lines: tuple[str, ...],
    *,
    source: EvidenceSource,
    note: str,
    rule_status: str,
    block_id: str,
) -> None:
    for line in reset_lines:
        if line == "G61":
            _append(
                lines,
                line,
                differential,
                _observed_rule_source(differential.stage_key),
                "Reset observado; falta clasificar si depende de familia o plantilla.",
                confidence="hypothesis",
                rule_status="modal_reset_hypothesis",
                block_id=block_id,
            )
            continue
        _append(
            lines,
            line,
            differential,
            source,
            note,
            rule_status=rule_status,
            block_id=block_id,
        )


def _emit_program_close(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    evaluation: IsoStateEvaluation,
    *,
    family_override: Optional[str] = None,
    plane_override: Optional[str] = None,
) -> None:
    source = _observed_rule_source("program_close")
    plane = plane_override if plane_override is not None else _work_plane(evaluation)
    family = family_override if family_override is not None else _work_family(evaluation)
    if family in _ROUTER_MILLING_FAMILIES:
        for line in _router_program_close_lines(differential):
            _append(
                lines,
                line,
                differential,
                source,
                "Cierre router E004 observado antes del reset comun.",
                rule_status="machine_close_observed",
            )
    else:
        close_xy_line = _program_close_xy_line(differential)
        if _is_mixed_side_close(evaluation, differential, plane):
            _emit_side_program_close_prefix(lines, differential, plane)
            close_lines = (close_xy_line, "G64")
        else:
            close_lines = ("G0 G53 Z201.000", close_xy_line, "G64")
        for line in close_lines:
            _append(lines, line, differential, source, "Cierre comun observado.", rule_status="machine_close_observed")
    if family not in _ROUTER_MILLING_FAMILIES and plane != "Top":
        for line in _lateral_program_close_frame_lines(evaluation, plane):
            _append(
                lines,
                line,
                differential,
                source,
                "Reentrada de marco lateral antes del cierre comun.",
                rule_status="machine_close_observed",
            )
        reset_lines = _lateral_program_close_reset_lines(plane)
        _append(
            lines,
            reset_lines[0],
            differential,
            source,
            "Reset lateral observado antes del cierre comun.",
            confidence="hypothesis",
            rule_status="modal_reset_hypothesis",
        )
        for line in reset_lines[1:]:
            _append(
                lines,
                line,
                differential,
                source,
                "Reset lateral observado antes del cierre comun.",
                rule_status="machine_close_observed",
            )
    close_tail_lines = _common_program_close_tail_lines()
    for line in close_tail_lines[:1]:
        _append(
            lines,
            line,
            differential,
            source,
            "Comando de cierre observado; causalidad todavia no aislada.",
            confidence="hypothesis",
            rule_status="machine_close_hypothesis",
        )
    for line in close_tail_lines[1:]:
        _append(lines, line, differential, source, "Cierre comun observado.", rule_status="machine_close_observed")


def _emit_side_program_close_prefix(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    plane: str,
) -> None:
    source = _observed_rule_source("side_program_close")
    for line in _side_program_close_prefix_lines(plane):
        _append(
            lines,
            line,
            differential,
            source,
            "Prefijo de cierre observado despues de taladro lateral.",
            confidence="confirmed",
            rule_status="generalized_side_program_close",
        )


def _emit_empty_program_close(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    explicit_close: bool,
) -> None:
    source = _observed_rule_source("empty_program_close")
    if explicit_close:
        for line in _empty_program_explicit_close_lines(differential):
            _append(
                lines,
                line,
                differential,
                source,
                "Cierre observado para programa vacio con Xn explicito.",
                confidence="confirmed",
                rule_status="generalized_empty_program",
            )
    for line in _empty_program_close_tail_lines():
        _append(
            lines,
            line,
            differential,
            source,
            "Cierre comun observado para programa sin mecanizados.",
            confidence="confirmed",
            rule_status="generalized_empty_program",
        )


def _append(
    lines: list[ExplainedIsoLine],
    line: str,
    differential: StageDifferential,
    source: EvidenceSource,
    note: str,
    *,
    confidence: str = "observed",
    rule_status: str = "observed",
    block_id: Optional[str] = None,
    transition_id: Optional[str] = None,
) -> None:
    resolved_transition_id = transition_id or transition_id_for_rule_status(rule_status)
    resolved_block_id = block_id
    if resolved_block_id is None and resolved_transition_id is None:
        resolved_block_id = block_id_for_stage_key(differential.stage_key)
    lines.append(
        ExplainedIsoLine(
            line=line,
            stage_key=differential.stage_key,
            source=source,
            confidence=confidence,
            rule_status=rule_status,
            block_id=resolved_block_id,
            transition_id=resolved_transition_id,
            note=note,
        )
    )


def _change_after(differential: StageDifferential, layer: str, key: str) -> object:
    change = _find_change(differential.target_changes, layer, key)
    if change is None:
        change = _find_change(differential.forced_values, layer, key)
    if change is None:
        raise IsoCandidateEmissionError(
            f"La etapa {differential.stage_key} no contiene {layer}.{key}."
        )
    return change.after


def _optional_change_after(
    differential: StageDifferential,
    layer: str,
    key: str,
    default: object,
) -> object:
    change = _find_change(differential.target_changes, layer, key)
    if change is None:
        change = _find_change(differential.forced_values, layer, key)
    return default if change is None else change.after


def _same_router_tool(left: StageDifferential, right: StageDifferential) -> bool:
    return int(_change_after(left, "herramienta", "tool_number")) == int(
        _change_after(right, "herramienta", "tool_number")
    )


def _reset_after(differential: StageDifferential, layer: str, key: str) -> object:
    change = _find_change(differential.reset_changes, layer, key)
    if change is None:
        change = _find_change(differential.forced_values, layer, key)
    if change is None:
        raise IsoCandidateEmissionError(
            f"La etapa {differential.stage_key} no resetea {layer}.{key}."
        )
    return change.after


def _change_source(
    differential: StageDifferential,
    layer: str,
    key: str,
    *,
    reset: bool = False,
) -> EvidenceSource:
    candidates = differential.reset_changes if reset else differential.target_changes
    change = _find_change(candidates, layer, key)
    if change is None:
        change = _find_change(differential.forced_values, layer, key)
    return change.source if change is not None else _observed_rule_source(differential.stage_key)


def _find_change(
    changes: tuple[StateChange, ...],
    layer: str,
    key: str,
) -> Optional[StateChange]:
    for change in changes:
        if change.layer == layer and change.key == key:
            return change
    return None


def _trace_move(differential: StageDifferential, name: str):
    for move in differential.trace:
        if move.name == name:
            return move
    raise IsoCandidateEmissionError(
        f"La etapa {differential.stage_key} no contiene toolpath {name}."
    )


def _observed_rule_source(field: str) -> EvidenceSource:
    return EvidenceSource(
        "observed_rule",
        "iso_state_synthesis/experiments/001_top_drill_state_table.md",
        field,
    )


def _work_plane(evaluation: IsoStateEvaluation) -> str:
    for differential in evaluation.differentials:
        for change in differential.target_changes + differential.forced_values:
            if change.layer == "trabajo" and change.key == "plane":
                return str(change.after)
    return "Top"


def _work_family(evaluation: IsoStateEvaluation) -> str:
    for differential in evaluation.differentials:
        for change in differential.target_changes + differential.forced_values:
            if change.layer == "trabajo" and change.key == "family":
                return str(change.after)
    return "top_drill"


def _mirrored_side_fixed(
    evaluation: IsoStateEvaluation,
    prepare: StageDifferential,
    trace: StageDifferential,
) -> float:
    axis = str(_change_after(prepare, "movimiento", "side_axis"))
    fixed = float(_change_after(trace, "movimiento", "side_fixed"))
    span = (
        float(evaluation.initial_state.get("pieza", "width"))
        if axis == "X"
        else float(evaluation.initial_state.get("pieza", "length"))
    )
    sign = -1.0 if fixed < 0 else 1.0
    return sign * (span - abs(fixed))


def _fmt(value: object) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.3f}"
