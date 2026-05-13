"""Explanatory ISO candidate emitter for state differentials."""

from __future__ import annotations

import difflib
import math
import struct
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Sequence

from .catalog import (
    block_id_for_stage_key,
    select_transition_id,
    transition_id_for_rule_status,
)
from .differential import evaluate_pgmx_state_plan
from .model import (
    EvidenceSource,
    IsoStateEvaluation,
    IsoStateWarning,
    StageDifferential,
    StateChange,
)


class IsoCandidateEmissionError(RuntimeError):
    """Raised when the explanatory candidate emitter cannot handle a plan."""


_COMMON_STAGE_KEYS = {"program_header", "machine_preamble", "program_close"}
_WORK_STAGE_KEYS = {
    "top_drill": ("top_drill_prepare", "top_drill_trace", "top_drill_reset"),
    "side_drill": ("side_drill_prepare", "side_drill_trace", "side_drill_reset"),
    "slot_milling": ("slot_milling_prepare", "slot_milling_trace", "slot_milling_reset"),
    "line_milling": ("line_milling_prepare", "line_milling_trace", "line_milling_reset"),
    "profile_milling": ("profile_milling_prepare", "profile_milling_trace", "profile_milling_reset"),
}
_ROUTER_MILLING_FAMILIES = {"line_milling", "profile_milling"}
PROGRAMACIONES_SETTINGSX_PATH = "iso_state_synthesis/machine_config/snapshot/maestro/Cfgx/Programaciones.settingsx"


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


@dataclass(frozen=True)
class IsoLineDifference:
    """One differing normalized line."""

    line_number: int
    expected: Optional[str]
    actual: Optional[str]


@dataclass(frozen=True)
class IsoCandidateComparison:
    """Comparison between Maestro ISO and an explained candidate."""

    equal: bool
    expected_line_count: int
    actual_line_count: int
    differences: tuple[IsoLineDifference, ...]
    diff: str = ""

    @property
    def difference_count(self) -> int:
        return len(self.differences)


@dataclass(frozen=True)
class _WorkGroup:
    """Prepared work group plus catalog transitions to neighboring groups."""

    family: str
    prepare: StageDifferential
    trace: StageDifferential
    reset: StageDifferential
    incoming_transition_id: Optional[str] = None
    outgoing_transition_id: Optional[str] = None


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

    This first emitter is intentionally narrow: it supports the minimal Top
    Drill, Side Drill and E004 line-milling fixtures used by the state
    synthesis study.
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
            "El emisor candidato inicial solo soporta secuencias completas "
            "Top Drill, Side Drill, Line Milling y Profile Milling E001."
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


def _work_stage_groups(
    ordered_differentials: list[StageDifferential],
) -> tuple[_WorkGroup, ...]:
    work = [
        differential
        for differential in ordered_differentials
        if differential.stage_key not in _COMMON_STAGE_KEYS
    ]
    if not work or len(work) % 3:
        return ()

    raw_groups: list[tuple[str, StageDifferential, StageDifferential, StageDifferential]] = []
    for index in range(0, len(work), 3):
        stage_group = work[index : index + 3]
        stage_keys = tuple(differential.stage_key for differential in stage_group)
        for family, expected_keys in _WORK_STAGE_KEYS.items():
            if stage_keys == expected_keys:
                prepare, trace, reset = stage_group
                raw_groups.append((family, prepare, trace, reset))
                break
        else:
            return ()
    return _plan_work_groups(tuple(raw_groups))


def _plan_work_groups(
    groups: tuple[tuple[str, StageDifferential, StageDifferential, StageDifferential], ...],
) -> tuple[_WorkGroup, ...]:
    planned: list[_WorkGroup] = []
    for index, (family, prepare, trace, reset) in enumerate(groups):
        previous = groups[index - 1] if index > 0 else None
        next_group = groups[index + 1] if index < len(groups) - 1 else None
        incoming_transition_id = (
            select_transition_id(previous[0], previous[1], family, prepare)
            if previous is not None
            else None
        )
        outgoing_transition_id = (
            select_transition_id(family, prepare, next_group[0], next_group[1])
            if next_group is not None
            else None
        )
        planned.append(
            _WorkGroup(
                family=family,
                prepare=prepare,
                trace=trace,
                reset=reset,
                incoming_transition_id=incoming_transition_id,
                outgoing_transition_id=outgoing_transition_id,
            )
        )
    return tuple(planned)


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
        _emit_planned_work_group(lines, evaluation, group, previous_group, next_group, previous_router_group)
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
        _emit_side_drill_prepare_after_router(lines, evaluation, prepare, multi_side_sequence=next_family == "side_drill", transition_id=incoming_transition_id)
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
        _emit_slot_milling_trace(lines, evaluation, trace, emit_transition_exit=True)
        _emit_slot_milling_reset(lines, reset, final=next_family is None)
    elif family == "top_drill" and incoming_transition_id == "T-BH-006":
        _emit_top_drill_prepare_after_slot(lines, evaluation, prepare, transition_id=incoming_transition_id)
        _emit_top_drill_trace(lines, trace, emit_mlv_after_etk7=False)
        _emit_top_drill_reset(lines, evaluation, reset, final=next_family is None)
    elif family == "side_drill" and incoming_transition_id == "T-BH-008":
        assert previous_group is not None
        _emit_slot_to_side_drill_transition(lines, evaluation, prepare, transition_id=incoming_transition_id)
        _emit_side_drill_prepare_after_slot(lines, evaluation, prepare, transition_id=incoming_transition_id)
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
            previous_group.family,
            previous_group.reset,
            prepare,
            trace,
            include_face_selection=(
                previous_group.family == "top_drill"
                and _prior_profile_to_top_requires_face_selection(evaluation, previous_router_group)
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
    strategy_change = _find_change(next_prepare.target_changes, "trabajo", "strategy")
    next_strategy = "" if strategy_change is None else str(strategy_change.after or "")
    approach_change = _find_change(next_prepare.target_changes, "trabajo", "approach_enabled")
    if approach_change is None:
        approach_change = _find_change(next_prepare.forced_values, "trabajo", "approach_enabled")
    next_approach_enabled = True if approach_change is None else bool(approach_change.after)
    next_side = str(_optional_change_after(next_prepare, "trabajo", "side_of_feature", "Center"))
    reset_lines = [
        "?%ETK[7]=0",
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        "M5",
        "MLV=0",
        "G0 G53 Z201.000",
    ]
    if next_strategy or (not next_approach_enabled and next_side not in {"Left", "Right"}):
        reset_lines = reset_lines[1:]
    for line in reset_lines:
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


def compare_candidate_to_iso(
    expected_iso_path: Path,
    candidate: ExplainedIsoProgram,
    *,
    include_diff: bool = False,
) -> IsoCandidateComparison:
    """Compare an explained candidate against a Maestro ISO file."""

    expected_text = Path(expected_iso_path).read_text(encoding="utf-8", errors="replace")
    expected = _normalize_iso_lines(expected_text)
    actual = _normalize_iso_lines(candidate.text())
    differences: list[IsoLineDifference] = []
    for index in range(max(len(expected), len(actual))):
        expected_line = expected[index] if index < len(expected) else None
        actual_line = actual[index] if index < len(actual) else None
        if expected_line != actual_line:
            differences.append(
                IsoLineDifference(
                    line_number=index + 1,
                    expected=expected_line,
                    actual=actual_line,
                )
            )
    diff = ""
    if include_diff and differences:
        diff = "\n".join(
            difflib.unified_diff(
                expected,
                actual,
                fromfile=str(expected_iso_path),
                tofile="candidate",
                lineterm="",
            )
        )
    return IsoCandidateComparison(
        equal=not differences,
        expected_line_count=len(expected),
        actual_line_count=len(actual),
        differences=tuple(differences),
        diff=diff,
    )


def _emit_program_header(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    program_name: str,
) -> None:
    dx = _change_after(differential, "pieza", "header_dx")
    dy = _change_after(differential, "pieza", "header_dy")
    dz = _change_after(differential, "pieza", "header_dz")
    area = evaluation.initial_state.get("pieza", "execution_fields", "HG")
    source = _change_source(differential, "pieza", "header_dx")
    _append(
        lines,
        f"% {program_name}.pgm",
        differential,
        source,
        "Nombre normalizado del programa.",
        confidence="candidate",
        rule_status="identity_normalization_pending",
    )
    _append(
        lines,
        (
            f";H DX={_fmt(dx)} DY={_fmt(dy)} DZ={_fmt(dz)} "
            f"BX=0.000 BY=0.000 BZ=0.000 -{area} V=0 *MM C=0 T=0"
        ),
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
    for line in (
        "?%ETK[500]=100",
        "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )",
        "G0 G53 Z %ax[2].pa[22]/1000",
        "M58",
    ):
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
        "G71",
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
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    source = _observed_rule_source("piece_frame_hg")
    frame_x = length + origin_x
    _append(
        lines,
        "MLV=0",
        differential,
        source,
        "Cambio modal de marco observado antes del marco HG.",
        rule_status="modal_frame_observed",
    )
    _append(
        lines,
        f"%Or[0].ofX={_fmt_scaled(-frame_x)}",
        differential,
        source,
        "Marco HG derivado de length + origin_x.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    _append(
        lines,
        "%Or[0].ofY=-1515599.976",
        differential,
        source,
        "Constante de campo HG observada; no depende de DY/origin_y en las seis variantes.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
        differential,
        source,
        "Marco HG derivado de depth + origin_z.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    for line in ("?%EDK[0].0=0", "?%EDK[1].0=0", "MLV=1"):
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
        f"SHF[X]={_fmt(-frame_x)}",
        differential,
        source,
        "Shift HG derivado de -(length + origin_x).",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    _append(
        lines,
        "SHF[Y]=-1515.600",
        differential,
        source,
        "Constante de campo HG observada; se conserva al cambiar ancho, origen Y y punto Y.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
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
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
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
    frame_x = _change_after(differential, "pieza", "header_dx")
    header_dz = _change_after(differential, "pieza", "header_dz")
    source = _change_source(differential, "pieza", "header_dx")
    for line in (
        "MLV=0",
        f"%Or[0].ofX={_fmt_scaled(-frame_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]={_fmt(-frame_x)}",
        "SHF[Y]=-1515.600",
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Marco de pieza para programa sin mecanizados.",
            confidence="confirmed",
            rule_status="generalized_empty_program",
        )
    for _ in range(face_pair_count):
        for line in ("?%ETK[8]=1", "G40"):
            _append(
                lines,
                line,
                differential,
                source,
                "Seleccion/reset de cara observado en programa sin mecanizados.",
                confidence="confirmed",
                rule_status="generalized_empty_program",
            )


def _face_selection_lines(evaluation: IsoStateEvaluation, work_plane: str) -> tuple[str, ...]:
    lines: list[str] = ["?%ETK[8]=1", "G40", "?%ETK[8]=1", "G40"]
    if work_plane == "Top":
        if (
            _work_family(evaluation) == "profile_milling"
            and not _first_work_value(evaluation, "trabajo", "strategy", "")
        ) or (
            _work_family(evaluation) == "line_milling"
            and _first_work_value(evaluation, "trabajo", "side_of_feature", "Center")
            in {"Left", "Right"}
        ):
            lines.append("?%ETK[7]=0")
        lines.extend(["?%ETK[8]=1", "G40"])
        return tuple(lines)

    side_etk8 = _side_value(evaluation, "trabajo", "side_etk8")
    if work_plane in {"Left", "Back"}:
        side_x, side_y = _side_plane_frame_shift(evaluation, work_plane)
        header_dz = evaluation.final_state.get("pieza", "header_dz")
        lines.extend(
            [
                "MLV=1",
                f"SHF[X]={_fmt(side_x)}",
                f"SHF[Y]={_fmt(side_y)}",
                f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
            ]
        )
    lines.extend([f"?%ETK[8]={int(side_etk8)}", "G40"])
    return tuple(lines)


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
    frame_plane: Optional[str] = None
    if plane in {"Left", "Back"}:
        frame_plane = plane
    elif plane == "Right" and include_right_frame and (
        previous_plane is None or previous_plane in {"Back", "Left"}
    ):
        frame_plane = "Right"
    elif plane == "Front" and previous_plane in {"Back", "Left"}:
        frame_plane = "Right"
    if frame_plane is not None:
        side_x, side_y = _side_plane_frame_shift(evaluation, frame_plane)
        header_dz = evaluation.final_state.get("pieza", "header_dz")
        for line in (
            "MLV=1",
            f"SHF[X]={_fmt(side_x)}",
            f"SHF[Y]={_fmt(side_y)}",
            f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        ):
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
    side_etk8 = _change_after(differential, "trabajo", "side_etk8")
    for line in (f"?%ETK[8]={int(side_etk8)}", "G40"):
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
    transition_lines: list[str] = []
    if include_face_selection:
        transition_lines.extend(("?%ETK[8]=1", "G40"))
    transition_lines.extend((
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        "G0 G53 Z201.000",
        "G64",
    ))
    for line in transition_lines:
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
    for line in (
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
    ):
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
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name
    prepare_lines = [
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        "MLV=2",
    ]
    if tool_number != 1:
        prepare_lines.insert(4, f"?%ETK[6]={tool_number}")
    for line in prepare_lines:
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
    for line in (f"SHF[X]={_fmt(shf_x)}", f"SHF[Y]={_fmt(shf_y)}", f"SHF[Z]={_fmt(shf_z)}"):
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
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name
    transition_source = _observed_rule_source("slot_to_top_drill_transition")
    for line in (
        "?%ETK[8]=1",
        "G40",
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "?%ETK[1]=0",
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={tool_number}",
        "MLV=2",
    ):
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
    for line in (f"SHF[X]={_fmt(shf_x)}", f"SHF[Y]={_fmt(shf_y)}", f"SHF[Z]={_fmt(shf_z)}"):
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
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    previous_plane = str(_change_after(previous_side_prepare, "trabajo", "plane"))
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    transition_source = _observed_rule_source("side_to_top_drill_transition")
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name

    if previous_plane in {"Left", "Back"}:
        length = evaluation.initial_state.get("pieza", "length")
        origin_x = evaluation.initial_state.get("pieza", "origin_x")
        origin_y = evaluation.initial_state.get("pieza", "origin_y")
        for line in (
            "MLV=1",
            f"SHF[X]={_fmt(-(length + origin_x))}",
            f"SHF[Y]={_fmt(_base_shf_y(origin_y))}",
            f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        ):
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
    for line in (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={tool_number}",
        "MLV=0",
        f"G0 G53 Z{_fmt(_side_drill_g53_z(evaluation, previous_side_prepare))}",
        "MLV=2",
        "MLV=2",
        f"SHF[X]={_fmt(shf_x)}",
        f"SHF[Y]={_fmt(shf_y)}",
        f"SHF[Z]={_fmt(shf_z)}",
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
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name
    prep_origin_x = length + (2 * origin_x)
    if previous_trace is not None:
        previous_approach = _trace_move(previous_trace, "Approach").points[0]
        previous_rapid_z = previous_approach.iso_z
        same_tool = (
            previous_prepare is not None
            and _change_after(previous_prepare, "herramienta", "tool_name") == tool_name
        )
        base_lines = (
            "MLV=1",
            f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
            "MLV=2",
            "G17",
        )
        for line in base_lines:
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
        if same_tool:
            _append(
                lines,
                f"G0 X{_fmt(previous_approach.x)} Y{_fmt(previous_approach.y)} Z{_fmt(previous_rapid_z)}",
                differential,
                source,
                "Reposicion de seguridad antes de repetir la misma herramienta.",
                confidence="confirmed",
                rule_status="generalized_top_drill_same_tool_sequence",
                transition_id=transition_id,
            )
            return
        for line in (
            f"?%ETK[6]={tool_number}",
            f"G0 X{_fmt(previous_approach.x)} Y{_fmt(previous_approach.y)} Z{_fmt(previous_rapid_z)}",
            "MLV=2",
        ):
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
        for line in (f"SHF[X]={_fmt(shf_x)}", f"SHF[Y]={_fmt(shf_y)}", f"SHF[Z]={_fmt(shf_z)}"):
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

    for line in ("MLV=2", "G17"):
        _append(
            lines,
            line,
            differential,
            source,
            "Modo/plano observado en preparacion de taladro superior.",
            rule_status="top_drill_modal_observed",
        )
    for line in (f"?%ETK[6]={tool_number}", f"%Or[0].ofX={_fmt_scaled(-prep_origin_x)}"):
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
        "%Or[0].ofY=-1515599.976",
        differential,
        _observed_rule_source("top_drill_prepare"),
        "Constante de campo HG observada; fuente de maquina/campo pendiente.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
        differential,
        source,
        "Preparacion de herramienta derivada de depth + origin_z.",
        confidence="confirmed",
        rule_status="generalized_top_drill_001_006",
    )
    _append(
        lines,
        "MLV=1",
        differential,
        source,
        "Cambio modal observado durante preparacion de herramienta.",
        rule_status="top_drill_modal_observed",
    )
    for line in (
        f"SHF[X]={_fmt(-(length + origin_x))}",
        f"SHF[Y]={_fmt(-1515.6 + origin_y)}",
        f"SHF[Z]={_fmt(origin_z)}",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Preparacion de herramienta de taladro superior con datos PGMX/tooling embebido.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    for line in ("MLV=2", "MLV=2"):
        _append(
            lines,
            line,
            differential,
            source,
            "Cambio modal observado durante preparacion de herramienta.",
            rule_status="top_drill_modal_observed",
        )
    for line in (f"SHF[X]={_fmt(shf_x)}", f"SHF[Y]={_fmt(shf_y)}", f"SHF[Z]={_fmt(shf_z)}"):
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
    trajectory = _trace_move(differential, "TrajectoryPath")
    lift = _trace_move(differential, "Lift")
    source = approach.source or _observed_rule_source("top_drill_trace")
    rapid_xy = approach.points[0]
    rapid_z = approach.points[0].iso_z
    cut_z = trajectory.points[-1].iso_z
    lift_z = lift.points[-1].iso_z
    feed = trajectory.feed
    if combine_rapid_z:
        rapid_lines = (f"G0 X{_fmt(rapid_xy.x)} Y{_fmt(rapid_xy.y)} Z{_fmt(rapid_z)}",)
    else:
        rapid_lines = (f"G0 X{_fmt(rapid_xy.x)} Y{_fmt(rapid_xy.y)}", f"G0 Z{_fmt(rapid_z)}")
    for line in rapid_lines:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Top Drill calculada desde toolpaths locales y ToolOffsetLength.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    modal_lines = ["?%ETK[7]=3"]
    if emit_mlv_after_etk7:
        modal_lines.append("MLV=2")
    for line in modal_lines:
        _append(
            lines,
            line,
            differential,
            _observed_rule_source("top_drill_trace"),
            "Comando modal observado en la traza; falta aislar fuente causal.",
            confidence="hypothesis",
            rule_status="modal_trace_hypothesis",
        )
    for line in (f"G1 G9 Z{_fmt(cut_z)} F{_fmt(feed)}", f"G0 Z{_fmt(lift_z)}"):
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
    rapid_x = _change_after(differential, "movimiento", "rapid_x")
    rapid_y = _change_after(differential, "movimiento", "rapid_y")
    rapid_z = _change_after(differential, "movimiento", "rapid_z")
    entry_x = _change_after(differential, "movimiento", "entry_x")
    entry_y = _change_after(differential, "movimiento", "entry_y")
    exit_x = _change_after(differential, "movimiento", "exit_x")
    exit_y = _change_after(differential, "movimiento", "exit_y")
    leadout_x = _change_after(differential, "movimiento", "leadout_x")
    leadout_y = _change_after(differential, "movimiento", "leadout_y")
    arc_i = _change_after(differential, "movimiento", "arc_i")
    arc_j = _change_after(differential, "movimiento", "arc_j")
    exit_arc_i = arc_i
    exit_arc_j = arc_j
    cut_z = _change_after(differential, "movimiento", "cut_z")
    security_z = _change_after(differential, "movimiento", "security_z")
    tool_radius = _change_after(differential, "herramienta", "tool_radius")
    plunge_feed = _change_after(differential, "movimiento", "plunge_feed")
    milling_feed = _change_after(differential, "movimiento", "milling_feed")
    contour_points = _change_after(differential, "movimiento", "contour_points")
    compensation_code = str(_change_after(differential, "salida", "compensation_code"))
    arc_code = str(_change_after(differential, "salida", "arc_code"))
    approach_enabled = bool(_change_after(differential, "trabajo", "approach_enabled"))
    approach_type = str(_change_after(differential, "trabajo", "approach_type"))
    approach_mode = str(_change_after(differential, "trabajo", "approach_mode"))
    strategy_name = str(_change_after(differential, "trabajo", "strategy"))
    retract_enabled = bool(_change_after(differential, "trabajo", "retract_enabled"))
    retract_type = str(_change_after(differential, "trabajo", "retract_type"))
    retract_mode = str(_change_after(differential, "trabajo", "retract_mode"))
    tool_offset = _change_after(differential, "herramienta", "tool_offset_length")
    source = _change_source(differential, "movimiento", "cut_z")
    if strategy_name:
        _emit_profile_milling_strategy_trace(
            lines,
            differential,
            rapid_z=rapid_z,
            security_z=security_z,
            tool_offset=tool_offset,
            tool_radius=tool_radius,
            plunge_feed=plunge_feed,
            milling_feed=milling_feed,
            contour_points=contour_points,
        )
        return
    approach_primitives = tuple(_optional_change_after(differential, "movimiento", "approach_primitives", ()))
    lift_primitives = tuple(_optional_change_after(differential, "movimiento", "lift_primitives", ()))
    if approach_enabled and retract_enabled and approach_type == "Arc" and retract_type == "Arc":
        try:
            lead_geometry = _profile_arc_leads_from_pgmxd_toolpaths(
                contour_points,
                approach_primitives,
                lift_primitives,
                float(tool_radius),
                arc_code,
            )
        except IsoCandidateEmissionError as exc:
            if "radio cero" not in str(exc):
                raise
            lead_geometry = None
        if lead_geometry is not None:
            rapid_x, rapid_y = lead_geometry["rapid"]
            entry_x, entry_y = lead_geometry["entry"]
            exit_x, exit_y = lead_geometry["exit"]
            leadout_x, leadout_y = lead_geometry["leadout"]
            arc_i, arc_j = lead_geometry["approach_center"]
            exit_arc_i, exit_arc_j = lead_geometry["retract_center"]

    for line in (
        f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)}",
        f"G0 Z{_fmt(rapid_z)}",
        "D1",
        f"SVL {_fmt(tool_offset)}",
        f"VL6={_fmt(tool_offset)}",
        f"SVR {_fmt(tool_radius)}",
        f"VL7={_fmt(tool_radius)}",
        "?%ETK[7]=4",
        compensation_code,
        f"G1 X{_fmt(entry_x)} Y{_fmt(entry_y)} Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Entrada E001 calculada desde perfil nominal y herramienta embebida.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )

    start_x, start_y = contour_points[0]
    if not approach_enabled:
        entry_lines = (f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",)
    elif approach_type == "Line":
        line = _line_milling_motion_line(
            float(start_x),
            float(start_y),
            float(cut_z),
            float(entry_x),
            float(entry_y),
            float(security_z),
            float(plunge_feed),
        )
        if approach_mode == "Down":
            entry_lines = (line,)
        else:
            entry_lines = (f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}", line)
    elif approach_mode == "Down":
        entry_lines = (
            _profile_milling_arc_line(
                arc_code,
                start_x,
                start_y,
                arc_i,
                arc_j,
                plunge_feed,
                z=cut_z,
            ),
        )
    else:
        entry_lines = (
            f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",
            _profile_milling_arc_line(arc_code, start_x, start_y, arc_i, arc_j, plunge_feed),
        )
    for line in entry_lines:
        _append(
            lines,
            line,
            differential,
            source,
            "Arco de entrada E001 observado.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )

    current_x = float(start_x)
    current_y = float(start_y)
    current_z = float(cut_z)
    for point in contour_points[1:]:
        x, y = point
        line = _line_milling_motion_line(
            float(x),
            float(y),
            float(cut_z),
            current_x,
            current_y,
            current_z,
            float(milling_feed),
        )
        _append(
            lines,
            line,
            differential,
            source,
            "Contorno nominal E001 emitido con compensacion activa.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )
        current_x = float(x)
        current_y = float(y)
        current_z = float(cut_z)

    if not retract_enabled:
        exit_lines = (f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",)
    elif retract_type == "Line":
        line = _line_milling_motion_line(
            float(exit_x),
            float(exit_y),
            float(cut_z),
            current_x,
            current_y,
            current_z,
            float(milling_feed),
        )
        if retract_mode == "Up":
            exit_lines = (
                _line_milling_motion_line(
                    float(exit_x),
                    float(exit_y),
                    float(security_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                ),
            )
        else:
            exit_lines = (line, f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
    elif retract_mode == "Up":
        exit_lines = (
            _profile_milling_arc_line(
                arc_code,
                exit_x,
                exit_y,
                exit_arc_i,
                exit_arc_j,
                milling_feed,
                z=security_z,
            ),
        )
    else:
        exit_lines = (
            _profile_milling_arc_line(arc_code, exit_x, exit_y, exit_arc_i, exit_arc_j, milling_feed),
            f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",
        )
    for line in exit_lines:
        _append(
            lines,
            line,
            differential,
            source,
            "Arco de salida E001 observado.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )

    for line in (
        "G40",
        f"G1 X{_fmt(leadout_x)} Y{_fmt(leadout_y)} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Alejamiento E001 posterior a cancelar compensacion.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001",
        )


def _emit_profile_milling_strategy_trace(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    rapid_z: object,
    security_z: object,
    tool_offset: object,
    tool_radius: object,
    plunge_feed: object,
    milling_feed: object,
    contour_points: object,
) -> None:
    approach = _trace_move(differential, "Approach")
    trajectory = _trace_move(differential, "TrajectoryPath")
    lift = _trace_move(differential, "Lift")
    if not approach.points or not trajectory.points or not lift.points:
        raise IsoCandidateEmissionError("La estrategia E001 PH5 no contiene toolpaths completos.")
    source = _change_source(differential, "movimiento", "cut_z")
    rapid_point = approach.points[0]

    for line in (
        f"G0 X{_fmt(rapid_point.x)} Y{_fmt(rapid_point.y)}",
        f"G0 Z{_fmt(rapid_z)}",
        "D1",
        f"SVL {_fmt(tool_offset)}",
        f"VL6={_fmt(tool_offset)}",
        f"SVR {_fmt(tool_radius)}",
        f"VL7={_fmt(tool_radius)}",
        f"G1 Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
        "?%ETK[7]=4",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Entrada E001 PH5 derivada de toolpath Maestro.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001_ph5",
        )

    current_x = float(rapid_point.x)
    current_y = float(rapid_point.y)
    current_z = float(security_z)
    start_x, _ = contour_points[0]

    generated: list[str] = []
    for point in approach.points[1:]:
        line = _profile_toolpath_motion_line(
            point,
            current_x,
            current_y,
            current_z,
            float(milling_feed),
            center=(
                (float(start_x), float(_change_after(differential, "movimiento", "arc_j")))
                if _xy_changed(current_x, current_y, point)
                else None
            ),
        )
        generated.append(line)
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)

    for point in trajectory.points[1:]:
        center = None
        if _xy_changed(current_x, current_y, point):
            center = _profile_corner_center(current_x, current_y, float(point.x), float(point.y), contour_points)
        generated.append(
            _profile_toolpath_motion_line(
                point,
                current_x,
                current_y,
                current_z,
                float(milling_feed),
                center=center,
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)

    for point in lift.points[1:]:
        center = None
        if _xy_changed(current_x, current_y, point):
            center = (float(start_x), float(point.y))
        generated.append(
            _profile_toolpath_motion_line(
                point,
                current_x,
                current_y,
                current_z,
                float(milling_feed),
                center=center,
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    generated.append(f"G0 Z{_fmt(security_z)}")

    for line in generated:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza E001 PH5 derivada de toolpaths Maestro.",
            confidence="confirmed",
            rule_status="generalized_profile_milling_e001_ph5",
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
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    tool_number = _change_after(differential, "herramienta", "tool_number")
    spindle = _change_after(differential, "herramienta", "spindle")
    etk9 = _change_after(differential, "salida", "etk_9")
    etk18 = _change_after(differential, "salida", "etk_18")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    prep_origin_x = length + (2 * origin_x)
    if incremental_router:
        prepare_lines = (
            "MLV=0",
            f"T{int(tool_number)}",
            "SYN",
            "M06",
            f"?%ETK[9]={int(etk9)}",
            f"?%ETK[18]={int(etk18)}",
            f"S{int(spindle_speed)}M3",
            "G17",
            "MLV=2",
            "?%ETK[13]=1",
        )
    else:
        prepare_lines = (
        "MLV=0",
        f"T{int(tool_number)}",
        "SYN",
        "M06",
        f"?%ETK[6]={int(spindle)}",
        f"?%ETK[9]={int(etk9)}",
        f"?%ETK[18]={int(etk18)}",
        f"S{int(spindle_speed)}M3",
        "G17",
        "MLV=2",
        f"%Or[0].ofX={_fmt_scaled(-prep_origin_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
        "MLV=1",
        f"SHF[X]={_fmt(-(length + origin_x))}",
        f"SHF[Y]={_fmt(_base_shf_y(origin_y))}",
        f"SHF[Z]={_fmt(header_dz)}",
        "MLV=2",
        "?%ETK[13]=1",
        "MLV=2",
        f"SHF[X]={_fmt(shf_x)}",
        f"SHF[Y]={_fmt(shf_y)}",
        f"SHF[Z]={_fmt(shf_z)}",
        )
    for line in prepare_lines:
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
    previous_family: str,
    boring_reset: StageDifferential,
    router_prepare: StageDifferential,
    router_trace: StageDifferential,
    *,
    include_face_selection: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    source = _observed_rule_source("boring_to_router_transition")
    if previous_family == "side_drill":
        for line in ("?%ETK[8]=1", "G40"):
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
    cleanup_lines: list[str] = []
    if previous_family == "top_drill" and _router_trace_requires_pre_router_etk7_reset(
        router_prepare,
        router_trace,
    ):
        cleanup_lines.append("?%ETK[7]=0")
    if include_face_selection:
        cleanup_lines.extend(("?%ETK[8]=1", "G40"))
    if previous_family in {"top_drill", "side_drill"}:
        cleanup_lines.extend(("?%ETK[17]=0", "M5", "?%ETK[0]=0"))
    elif previous_family == "slot_milling":
        cleanup_lines.extend(("?%ETK[17]=0", "M5", "?%ETK[1]=0"))
    cleanup_lines.extend(
        (
            "MLV=0",
            "G0 G53 Z201.000",
            "MLV=2",
            "MLV=0",
            "G0 G53 Z201.000",
            "MLV=0",
            f"T{int(_change_after(router_prepare, 'herramienta', 'tool_number'))}",
            "SYN",
            "M06",
            "G61",
            "G0 G53 Z201.000",
            "G64",
        )
    )
    for line in cleanup_lines:
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


def _router_trace_requires_pre_router_etk7_reset(
    router_prepare: StageDifferential,
    router_trace: StageDifferential,
) -> bool:
    profile_family = str(_optional_change_after(router_trace, "movimiento", "profile_family", ""))
    side_of_feature = str(_optional_change_after(router_prepare, "trabajo", "side_of_feature", "Center"))
    approach_enabled = bool(
        _optional_change_after(router_prepare, "trabajo", "approach_enabled", False)
    )
    retract_enabled = bool(
        _optional_change_after(router_prepare, "trabajo", "retract_enabled", False)
    )
    return profile_family == "OpenPolyline" and (
        side_of_feature in {"Left", "Right"} or (approach_enabled and retract_enabled)
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


def _prior_profile_to_top_requires_face_selection(
    evaluation: IsoStateEvaluation,
    previous_router_group: Optional[_WorkGroup],
) -> bool:
    return (
        previous_router_group is not None
        and previous_router_group.family == "profile_milling"
        and _profile_to_top_requires_face_selection(evaluation, previous_router_group)
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
    spindle = _change_after(differential, "herramienta", "spindle")
    etk9 = _change_after(differential, "salida", "etk_9")
    etk18 = _change_after(differential, "salida", "etk_18")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    prepare_lines: list[str] = []
    previous_tool_number = _optional_change_after(previous_prepare, "herramienta", "spindle", None)
    if previous_tool_number is None:
        previous_tool_number = _optional_change_after(previous_prepare, "herramienta", "tool_name", None)
    if previous_family != "top_drill" or int(previous_tool_number or 0) != 1:
        prepare_lines.append(f"?%ETK[6]={int(spindle)}")
    if previous_router_prepare is None or not _same_router_tool(previous_router_prepare, differential):
        prepare_lines.append(f"?%ETK[9]={int(etk9)}")
    prepare_lines.extend(
        (
            f"?%ETK[18]={int(etk18)}",
            f"S{int(spindle_speed)}M3",
            "G17",
            "MLV=2",
            "?%ETK[13]=1",
            "MLV=2",
            f"SHF[X]={_fmt(shf_x)}",
            f"SHF[Y]={_fmt(shf_y)}",
            f"SHF[Z]={_fmt(shf_z)}",
        )
    )
    for line in prepare_lines:
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
    start_x = _change_after(differential, "movimiento", "start_x")
    start_y = _change_after(differential, "movimiento", "start_y")
    end_x = _change_after(differential, "movimiento", "end_x")
    end_y = _change_after(differential, "movimiento", "end_y")
    rapid_z = _change_after(differential, "movimiento", "rapid_z")
    cut_z = _change_after(differential, "movimiento", "cut_z")
    security_z = _change_after(differential, "movimiento", "security_z")
    tool_radius = _change_after(differential, "herramienta", "tool_radius")
    plunge_feed = _change_after(differential, "movimiento", "plunge_feed")
    milling_feed = _change_after(differential, "movimiento", "milling_feed")
    tool_offset = _change_after(differential, "herramienta", "tool_offset_length")
    approach = _trace_move(differential, "Approach")
    trajectory = _trace_move(differential, "TrajectoryPath")
    lift = _trace_move(differential, "Lift")
    source = _change_source(differential, "movimiento", "cut_z")
    side_of_feature = str(
        _optional_change_after(
            differential,
            "trabajo",
            "side_of_feature",
            evaluation.final_state.get("trabajo", "side_of_feature", "Center"),
        )
    )
    overcut_length = float(
        _optional_change_after(
            differential,
            "trabajo",
            "overcut_length",
            evaluation.final_state.get("trabajo", "overcut_length", 0.0),
        )
        or 0.0
    )
    strategy_name = str(
        _optional_change_after(
            differential,
            "trabajo",
            "strategy",
            evaluation.final_state.get("trabajo", "strategy", ""),
        )
    )
    profile_family = str(_optional_change_after(differential, "movimiento", "profile_family", "Line"))
    profile_winding = str(_optional_change_after(differential, "movimiento", "profile_winding", ""))
    circle_center_x = _optional_change_after(differential, "movimiento", "circle_center_x", None)
    circle_center_y = _optional_change_after(differential, "movimiento", "circle_center_y", None)
    contour_points = _change_after(differential, "movimiento", "contour_points")
    nominal_points = tuple((float(point[0]), float(point[1])) for point in contour_points)
    open_polyline_outside_piece = profile_family == "OpenPolyline" and _polyline_leaves_workpiece(
        evaluation,
        nominal_points,
    )
    trajectory_primitives = tuple(_optional_change_after(differential, "movimiento", "trajectory_primitives", ()))
    approach_type = str(
        _optional_change_after(
            differential,
            "trabajo",
            "approach_type",
            evaluation.final_state.get("trabajo", "approach_type", "Line"),
        )
    )
    approach_mode = str(
        _optional_change_after(
            differential,
            "trabajo",
            "approach_mode",
            evaluation.final_state.get("trabajo", "approach_mode", "Down"),
        )
    )
    approach_radius_multiplier = float(
        _optional_change_after(
            differential,
            "trabajo",
            "approach_radius_multiplier",
            evaluation.final_state.get("trabajo", "approach_radius_multiplier", 2.0),
        )
        or 2.0
    )
    retract_type = str(
        _optional_change_after(
            differential,
            "trabajo",
            "retract_type",
            evaluation.final_state.get("trabajo", "retract_type", "Line"),
        )
    )
    retract_mode = str(
        _optional_change_after(
            differential,
            "trabajo",
            "retract_mode",
            evaluation.final_state.get("trabajo", "retract_mode", "Up"),
        )
    )
    retract_radius_multiplier = float(
        _optional_change_after(
            differential,
            "trabajo",
            "retract_radius_multiplier",
            evaluation.final_state.get("trabajo", "retract_radius_multiplier", approach_radius_multiplier),
        )
        or approach_radius_multiplier
    )
    has_lead_paths = (
        len(approach.points) >= 2
        and len(lift.points) >= 2
        and (
            abs(float(approach.points[0].x) - float(approach.points[-1].x)) >= 0.0005
            or abs(float(approach.points[0].y) - float(approach.points[-1].y)) >= 0.0005
        )
    )
    uses_side_compensation = (
        has_lead_paths
        and not strategy_name
        and side_of_feature in {"Right", "Left"}
    )
    uses_no_lead_side_compensation = (
        not has_lead_paths
        and not strategy_name
        and side_of_feature in {"Right", "Left"}
        and profile_family in {"OpenPolyline", "Circle"}
    )
    uses_center_circle_leads = (
        has_lead_paths
        and not strategy_name
        and profile_family == "Circle"
        and side_of_feature == "Center"
    )
    uses_closed_center_leads = (
        has_lead_paths
        and not strategy_name
        and profile_family.startswith("ClosedPolyline")
        and side_of_feature == "Center"
    )
    uses_open_center_leads = (
        has_lead_paths
        and not strategy_name
        and profile_family == "OpenPolyline"
        and side_of_feature == "Center"
    )
    if uses_open_center_leads:
        lead_geometry = _open_polyline_center_lead_geometry(
            nominal_points,
            float(tool_radius) * approach_radius_multiplier,
            approach_type,
        )
        rapid_x, rapid_y = lead_geometry["rapid"]
    elif uses_closed_center_leads:
        lead_geometry = _closed_polyline_center_lead_geometry(
            nominal_points,
            float(tool_radius) * approach_radius_multiplier,
            approach_type,
            profile_winding,
        )
        rapid_x, rapid_y = lead_geometry["rapid"]
    elif uses_center_circle_leads:
        lead_distance = float(tool_radius) * approach_radius_multiplier
        if approach_type == "Arc":
            rapid_x = float(start_x) - lead_distance
            rapid_y = float(start_y) - lead_distance
        else:
            rapid_x = float(start_x)
            rapid_y = float(start_y) - lead_distance
    elif strategy_name and not has_lead_paths and approach.points:
        rapid_x = float(approach.points[0].x)
        rapid_y = float(approach.points[0].y)
    elif uses_no_lead_side_compensation:
        rapid_point, _ = _no_lead_compensation_points(
            nominal_points,
            float(tool_radius),
            profile_family,
            profile_winding,
        )
        rapid_x, rapid_y = rapid_point
    elif uses_side_compensation and profile_family == "OpenPolyline":
        polyline_lead = _polyline_side_compensation_leads(
            nominal_points,
            float(tool_radius),
            side_of_feature,
            approach_type,
            approach_radius_multiplier,
        )
        rapid_x, rapid_y = polyline_lead["entry_rapid"]
    elif uses_side_compensation:
        rapid_x = start_x
        rapid_y = float(approach.points[0].y) - (2.0 * overcut_length)
    else:
        rapid_x = approach.points[0].x if has_lead_paths else start_x
        rapid_y = approach.points[0].y if has_lead_paths else start_y

    entry_lines: tuple[str, ...]
    if previous_router_trace is not None:
        last_xy = _last_emitted_xy(lines)
        previous_x = last_xy[0] if last_xy is not None else None
        previous_y = last_xy[1] if last_xy is not None else None
        if previous_x is None or previous_y is None:
            previous_x = _optional_change_after(previous_router_trace, "movimiento", "leadout_x", None)
            previous_y = _optional_change_after(previous_router_trace, "movimiento", "leadout_y", None)
        if previous_x is None or previous_y is None:
            previous_lift = _trace_move(previous_router_trace, "Lift")
            previous_x = previous_lift.points[-1].x
            previous_y = previous_lift.points[-1].y
        entry_prefix = ["?%ETK[7]=0", "G17"]
        if previous_router_trace.family != "line_milling":
            entry_prefix.append("MLV=2")
        entry_lines = tuple(entry_prefix) + (
            f"G0 X{_fmt(previous_x)} Y{_fmt(previous_y)} Z{_fmt(rapid_z)}",
            f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)} Z{_fmt(rapid_z)}",
            f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)} Z{_fmt(rapid_z)}",
            "D1",
            f"SVL {_fmt(tool_offset)}",
            f"VL6={_fmt(tool_offset)}",
            f"SVR {_fmt(tool_radius)}",
            f"VL7={_fmt(tool_radius)}",
        )
    else:
        entry_lines = (
            f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)}",
            f"G0 Z{_fmt(rapid_z)}",
            "D1",
            f"SVL {_fmt(tool_offset)}",
            f"VL6={_fmt(tool_offset)}",
            f"SVR {_fmt(tool_radius)}",
            f"VL7={_fmt(tool_radius)}",
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

    if uses_open_center_leads:
        lead_geometry = _open_polyline_center_lead_geometry(
            nominal_points,
            float(tool_radius) * approach_radius_multiplier,
            approach_type,
        )
        retract_geometry = _open_polyline_center_lead_geometry(
            nominal_points,
            float(tool_radius) * retract_radius_multiplier,
            retract_type,
        )
        arc_code = "G3" if profile_winding != "Clockwise" else "G2"
        generated = ["?%ETK[7]=4"]
        current_x = float(rapid_x)
        current_y = float(rapid_y)
        current_z = float(security_z)
        if approach_type == "Arc":
            if approach_mode == "Down":
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        start_x,
                        start_y,
                        lead_geometry["approach_center"][0],
                        lead_geometry["approach_center"][1],
                        plunge_feed,
                        z=cut_z,
                    )
                )
            else:
                generated.append(f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}")
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        start_x,
                        start_y,
                        lead_geometry["approach_center"][0],
                        lead_geometry["approach_center"][1],
                        plunge_feed,
                    )
                )
        elif approach_mode == "Down":
            generated.append(
                _line_milling_motion_line(
                    float(start_x),
                    float(start_y),
                    float(cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(plunge_feed),
                )
            )
        else:
            generated.append(f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}")
            generated.append(
                _line_milling_motion_line(
                    float(start_x),
                    float(start_y),
                    float(cut_z),
                    current_x,
                    current_y,
                    float(cut_z),
                    float(plunge_feed),
                    always_include_z=False,
                )
            )
        current_x = float(start_x)
        current_y = float(start_y)
        current_z = float(cut_z)
        for point in trajectory.points[1:]:
            generated.append(
                _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                    always_include_z=open_polyline_outside_piece,
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        if retract_type == "Arc":
            exit_x, exit_y = retract_geometry["exit"]
            if retract_mode == "Up":
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        exit_x,
                        exit_y,
                        retract_geometry["retract_center"][0],
                        retract_geometry["retract_center"][1],
                        milling_feed,
                        z=security_z,
                    )
                )
                generated.append(f"G0 Z{_fmt(security_z)}")
            else:
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        exit_x,
                        exit_y,
                        retract_geometry["retract_center"][0],
                        retract_geometry["retract_center"][1],
                        milling_feed,
                    )
                )
                generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        else:
            exit_x, exit_y = retract_geometry["exit"]
            if retract_mode == "Up":
                generated.append(
                    _line_milling_motion_line(
                        exit_x,
                        exit_y,
                        float(security_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                generated.append(f"G0 Z{_fmt(security_z)}")
            else:
                generated.append(
                    _line_milling_motion_line(
                        exit_x,
                        exit_y,
                        float(cut_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                        always_include_z=False,
                    )
                )
                generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        motion_lines = tuple(generated)
    elif uses_closed_center_leads:
        lead_geometry = _closed_polyline_center_lead_geometry(
            nominal_points,
            float(tool_radius) * approach_radius_multiplier,
            approach_type,
            profile_winding,
        )
        retract_geometry = _closed_polyline_center_lead_geometry(
            nominal_points,
            float(tool_radius) * retract_radius_multiplier,
            retract_type,
            profile_winding,
        )
        arc_code = "G3" if profile_winding == "CounterClockwise" else "G2"
        generated = ["?%ETK[7]=4"]
        current_x = float(rapid_x)
        current_y = float(rapid_y)
        current_z = float(security_z)
        if approach_type == "Arc":
            if approach_mode == "Down":
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        start_x,
                        start_y,
                        lead_geometry["approach_center"][0],
                        lead_geometry["approach_center"][1],
                        plunge_feed,
                        z=cut_z,
                    )
                )
            else:
                generated.append(f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}")
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        start_x,
                        start_y,
                        lead_geometry["approach_center"][0],
                        lead_geometry["approach_center"][1],
                        plunge_feed,
                    )
                )
        elif approach_mode == "Down":
            generated.append(
                _line_milling_motion_line(
                    float(start_x),
                    float(start_y),
                    float(cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(plunge_feed),
                )
            )
        else:
            generated.append(f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}")
            generated.append(
                _line_milling_motion_line(
                    float(start_x),
                    float(start_y),
                    float(cut_z),
                    current_x,
                    current_y,
                    float(cut_z),
                    float(plunge_feed),
                )
            )
        current_x = float(start_x)
        current_y = float(start_y)
        current_z = float(cut_z)
        primitive_index = 0
        for point in trajectory.points[1:]:
            matched_index, primitive = _matching_primitive_record(
                trajectory_primitives,
                primitive_index,
                point,
                current_x,
                current_y,
            )
            if primitive is not None and str(primitive[0]) == "Arc":
                generated.append(
                    _arc_record_motion_line(
                        primitive,
                        point,
                        current_z,
                        float(milling_feed),
                        fallback_center=(0.0, 0.0),
                        fallback_winding=profile_winding,
                    )
                )
                primitive_index = matched_index + 1
            else:
                generated.append(
                    _line_milling_motion_line(
                        float(point.x),
                        float(point.y),
                        float(point.iso_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                if matched_index >= 0:
                    primitive_index = matched_index + 1
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        if retract_type == "Arc":
            exit_x, exit_y = retract_geometry["exit"]
            if retract_mode == "Up":
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        exit_x,
                        exit_y,
                        retract_geometry["retract_center"][0],
                        retract_geometry["retract_center"][1],
                        milling_feed,
                        z=security_z,
                    )
                )
                generated.append(f"G0 Z{_fmt(security_z)}")
            else:
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        exit_x,
                        exit_y,
                        retract_geometry["retract_center"][0],
                        retract_geometry["retract_center"][1],
                        milling_feed,
                    )
                )
                generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        else:
            exit_x, exit_y = retract_geometry["exit"]
            if retract_mode == "Up":
                generated.append(
                    _line_milling_motion_line(
                        exit_x,
                        exit_y,
                        float(security_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                generated.append(f"G0 Z{_fmt(security_z)}")
            else:
                generated.append(
                    _line_milling_motion_line(
                        exit_x,
                        exit_y,
                        float(cut_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        motion_lines = tuple(generated)
    elif uses_center_circle_leads:
        if circle_center_x is None or circle_center_y is None:
            raise IsoCandidateEmissionError("El fresado circular con entrada no contiene centro.")
        lead_distance = float(tool_radius) * approach_radius_multiplier
        retract_lead_distance = float(tool_radius) * retract_radius_multiplier
        arc_code = "G3" if profile_winding == "CounterClockwise" else "G2"
        approach_center = (float(start_x) - lead_distance, float(start_y))
        retract_center = (float(start_x) - retract_lead_distance, float(start_y))
        generated = ["?%ETK[7]=4"]
        current_x = float(rapid_x)
        current_y = float(rapid_y)
        current_z = float(security_z)
        if approach_type == "Arc":
            if approach_mode == "Down":
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        start_x,
                        start_y,
                        approach_center[0],
                        approach_center[1],
                        plunge_feed,
                        z=cut_z,
                    )
                )
            else:
                generated.append(f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}")
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        start_x,
                        start_y,
                        approach_center[0],
                        approach_center[1],
                        plunge_feed,
                    )
                )
        elif approach_mode == "Down":
            generated.append(
                _line_milling_motion_line(
                    float(start_x),
                    float(start_y),
                    float(cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(plunge_feed),
                )
            )
        else:
            generated.append(f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}")
            generated.append(
                _line_milling_motion_line(
                    float(start_x),
                    float(start_y),
                    float(cut_z),
                    current_x,
                    current_y,
                    float(cut_z),
                    float(plunge_feed),
                )
            )
        current_x = float(start_x)
        current_y = float(start_y)
        current_z = float(cut_z)
        primitive_index = 0
        for point in trajectory.points[1:]:
            matched_index, primitive = _matching_primitive_record(
                trajectory_primitives,
                primitive_index,
                point,
                current_x,
                current_y,
            )
            if primitive is not None and str(primitive[0]) == "Arc":
                generated.append(
                    _arc_record_motion_line(
                        primitive,
                        point,
                        current_z,
                        float(milling_feed),
                        fallback_center=(float(circle_center_x), float(circle_center_y)),
                        fallback_winding=profile_winding,
                    )
                )
                primitive_index = matched_index + 1
            else:
                generated.append(
                    _profile_toolpath_motion_line(
                        point,
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                        center=(float(circle_center_x), float(circle_center_y)),
                        winding=profile_winding,
                    )
                )
                if matched_index >= 0:
                    primitive_index = matched_index + 1
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        if retract_type == "Arc":
            exit_x = float(start_x) - retract_lead_distance
            exit_y = float(start_y) + retract_lead_distance
            if retract_mode == "Up":
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        exit_x,
                        exit_y,
                        retract_center[0],
                        retract_center[1],
                        milling_feed,
                        z=security_z,
                    )
                )
                generated.append(f"G0 Z{_fmt(security_z)}")
            else:
                generated.append(
                    _profile_milling_arc_line(
                        arc_code,
                        exit_x,
                        exit_y,
                        retract_center[0],
                        retract_center[1],
                        milling_feed,
                    )
                )
                generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        else:
            exit_x = float(start_x)
            exit_y = float(start_y) + retract_lead_distance
            if retract_mode == "Up":
                generated.append(
                    _line_milling_motion_line(
                        exit_x,
                        exit_y,
                        float(security_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                generated.append(f"G0 Z{_fmt(security_z)}")
            else:
                generated.append(
                    _line_milling_motion_line(
                        exit_x,
                        exit_y,
                        float(cut_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        motion_lines = tuple(generated)
    elif strategy_name and profile_family == "Circle":
        if circle_center_x is None or circle_center_y is None:
            raise IsoCandidateEmissionError("El fresado circular con estrategia no contiene centro.")
        current_x = float(rapid_x)
        current_y = float(rapid_y)
        current_z = float(security_z)
        primitive_index = 0
        generated = [f"G1 Z{_fmt(security_z)} F{_fmt(plunge_feed)}", "?%ETK[7]=4"]
        for point in trajectory.points:
            matched_index, primitive = _matching_primitive_record(
                trajectory_primitives,
                primitive_index,
                point,
                current_x,
                current_y,
            )
            if primitive is not None and str(primitive[0]) == "Arc":
                line = _arc_record_motion_line(
                    primitive,
                    point,
                    current_z,
                    float(milling_feed),
                    fallback_center=(float(circle_center_x), float(circle_center_y)),
                    fallback_winding=profile_winding,
                )
                primitive_index = matched_index + 1
            else:
                line = _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                )
                if matched_index >= 0:
                    primitive_index = matched_index + 1
            generated.append(line)
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        generated.append(f"G0 Z{_fmt(security_z)}")
        motion_lines = tuple(generated)
    elif strategy_name and has_lead_paths:
        generated = [f"G1 Z{_fmt(security_z)} F{_fmt(plunge_feed)}", "?%ETK[7]=4"]
        current_x = float(approach.points[0].x)
        current_y = float(approach.points[0].y)
        current_z = float(security_z)
        for point in approach.points[1:]:
            generated.append(
                _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        primitive_index = 0
        for point in trajectory.points[1:]:
            matched_index, primitive = _matching_primitive_record(
                trajectory_primitives,
                primitive_index,
                point,
                current_x,
                current_y,
            )
            if primitive is not None and str(primitive[0]) == "Arc":
                generated.append(
                    _arc_record_motion_line(
                        primitive,
                        point,
                        current_z,
                        float(milling_feed),
                        fallback_center=(0.0, 0.0),
                        fallback_winding=profile_winding,
                    )
                )
                primitive_index = matched_index + 1
            else:
                generated.append(
                    _line_milling_motion_line(
                        float(point.x),
                        float(point.y),
                        float(point.iso_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                    )
                )
                if matched_index >= 0:
                    primitive_index = matched_index + 1
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        for point in lift.points[1:]:
            generated.append(
                _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        generated.append(f"G0 Z{_fmt(security_z)}")
        motion_lines = tuple(generated)
    elif uses_side_compensation and profile_family == "OpenPolyline":
        compensation_code = "G42" if side_of_feature == "Right" else "G41"
        polyline_lead = _polyline_side_compensation_leads(
            nominal_points,
            float(tool_radius),
            side_of_feature,
            approach_type,
            approach_radius_multiplier,
        )
        entry_point = polyline_lead["entry"]
        exit_point = polyline_lead["exit"]
        exit_rapid = polyline_lead["exit_rapid"]
        arc_code = "G3" if side_of_feature == "Left" else "G2"
        generated = [
            "?%ETK[7]=4",
            compensation_code,
            f"G1 X{_fmt(entry_point[0])} Y{_fmt(entry_point[1])} Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
        ]
        if approach_type == "Arc":
            entry_center = polyline_lead["entry_center"]
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    nominal_points[0][0],
                    nominal_points[0][1],
                    entry_center[0],
                    entry_center[1],
                    plunge_feed,
                    z=cut_z,
                )
            )
        else:
            generated.append(
                _line_milling_motion_line(
                    nominal_points[0][0],
                    nominal_points[0][1],
                    float(cut_z),
                    entry_point[0],
                    entry_point[1],
                    float(security_z),
                    float(plunge_feed),
                )
            )
        current_x, current_y = nominal_points[0]
        current_z = float(cut_z)
        include_cut_z = (
            open_polyline_outside_piece
            or float(cut_z) > -float(evaluation.initial_state.get("pieza", "depth"))
        )
        for point in nominal_points[1:]:
            generated.append(
                _line_milling_motion_line(
                    point[0],
                    point[1],
                    float(cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                    always_include_z=include_cut_z,
                )
            )
            current_x, current_y = point
        if approach_type == "Arc":
            exit_center = polyline_lead["exit_center"]
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_point[0],
                    exit_point[1],
                    exit_center[0],
                    exit_center[1],
                    milling_feed,
                    z=security_z,
                )
            )
        else:
            generated.append(
                _line_milling_motion_line(
                    exit_point[0],
                    exit_point[1],
                    float(security_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                )
            )
        generated.extend(
            (
                "G40",
                f"G1 X{_fmt(exit_rapid[0])} Y{_fmt(exit_rapid[1])} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
            )
        )
        motion_lines = tuple(generated)
    elif uses_side_compensation:
        compensation_code = "G42" if side_of_feature == "Right" else "G41"
        lift_y = float(lift.points[-2].y)
        motion_lines = (
            "?%ETK[7]=4",
            compensation_code,
            f"G1 X{_fmt(start_x)} Y{_fmt(approach.points[0].y)} Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
            f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",
            f"G1 Y{_fmt(start_y)} Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",
            f"G1 Y{_fmt(end_y)} Z{_fmt(cut_z)} F{_fmt(milling_feed)}",
            f"G1 Y{_fmt(lift_y)} Z{_fmt(cut_z)} F{_fmt(milling_feed)}",
            f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",
            "G40",
            f"G1 X{_fmt(start_x)} Y{_fmt(lift_y + (2.0 * overcut_length))} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
        )
    elif has_lead_paths:
        generated = ["?%ETK[7]=4"]
        current_x = float(approach.points[0].x)
        current_y = float(approach.points[0].y)
        current_z = float(security_z)
        for point in approach.points[1:]:
            generated.append(
                _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(plunge_feed),
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        for point in trajectory.points[1:]:
            generated.append(
                _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        for point in lift.points[1:]:
            generated.append(
                _line_milling_motion_line(
                    float(point.x),
                    float(point.y),
                    float(point.iso_z),
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        motion_lines = tuple(generated)
    elif uses_no_lead_side_compensation:
        compensation_code = "G42" if side_of_feature == "Right" else "G41"
        rapid_point, leadout_point = _no_lead_compensation_points(
            nominal_points,
            float(tool_radius),
            profile_family,
            profile_winding,
        )
        current_x = nominal_points[0][0]
        current_y = nominal_points[0][1]
        current_z = float(cut_z)
        include_cut_z = (
            profile_family.startswith("Line")
            or open_polyline_outside_piece
            or float(cut_z) > -float(evaluation.initial_state.get("pieza", "depth"))
        )
        generated = [
            "?%ETK[7]=4",
            compensation_code,
            f"G1 X{_fmt(nominal_points[0][0])} Y{_fmt(nominal_points[0][1])} Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
            f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",
        ]
        if profile_family == "Circle" and circle_center_x is not None and circle_center_y is not None:
            for point in nominal_points[2::2] or nominal_points[1:]:
                generated.append(
                    _profile_milling_arc_line(
                        "G3" if profile_winding == "CounterClockwise" else "G2",
                        point[0],
                        point[1],
                        circle_center_x,
                        circle_center_y,
                        milling_feed,
                    )
                )
                current_x, current_y = point
        else:
            for point in nominal_points[1:]:
                generated.append(
                    _line_milling_motion_line(
                        point[0],
                        point[1],
                        float(cut_z),
                        current_x,
                        current_y,
                        current_z,
                        float(milling_feed),
                        always_include_z=include_cut_z,
                    )
                )
                current_x, current_y = point
        generated.extend(
            (
                f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                "G40",
                f"G1 X{_fmt(leadout_point[0])} Y{_fmt(leadout_point[1])} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
            )
        )
        motion_lines = tuple(generated)
    elif strategy_name:
        current_x = float(start_x)
        current_y = float(start_y)
        current_z = float(security_z)
        generated = [f"G1 Z{_fmt(security_z)} F{_fmt(plunge_feed)}", "?%ETK[7]=4"]
        for point in trajectory.points:
            line = _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(milling_feed),
                always_include_z=profile_family != "OpenPolyline",
            )
            generated.append(line)
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        generated.append(f"G0 Z{_fmt(security_z)}")
        motion_lines = tuple(generated)
    elif not has_lead_paths:
        current_x = float(trajectory.points[0].x if trajectory.points else start_x)
        current_y = float(trajectory.points[0].y if trajectory.points else start_y)
        current_z = float(cut_z)
        generated = [f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}", "?%ETK[7]=4"]
        for point in trajectory.points[1:]:
            center = None
            if profile_family == "Circle" and circle_center_x is not None and circle_center_y is not None:
                center = (float(circle_center_x), float(circle_center_y))
            always_include_z = profile_family.startswith("Line") or open_polyline_outside_piece
            generated.append(
                _profile_toolpath_motion_line(
                    point,
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                    center=center,
                    winding=profile_winding,
                    always_include_z=always_include_z,
                )
            )
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        generated.append(f"G0 Z{_fmt(security_z)}")
        motion_lines = tuple(generated)
    else:
        current_x = float(start_x)
        current_y = float(start_y)
        current_z = float(security_z)
        generated: list[str] = [f"G1 Z{_fmt(security_z)} F{_fmt(plunge_feed)}", "?%ETK[7]=4"]
        for point in trajectory.points:
            line = _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(milling_feed),
            )
            generated.append(line)
            current_x = float(point.x)
            current_y = float(point.y)
            current_z = float(point.iso_z)
        generated.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
        generated.append(f"G0 Z{_fmt(security_z)}")
        motion_lines = tuple(generated)

    for line in motion_lines:
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
    for line in (
        "D0",
        "SVL 0.000",
        "VL6=0.000",
        "SVR 0.000",
        "VL7=0.000",
        "?%ETK[7]=0",
    ):
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
    for line in (
        "?%ETK[8]=1",
        "G40",
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "?%ETK[0]=0",
    ):
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
    previous_plane = str(_change_after(side_prepare, "trabajo", "plane"))
    if previous_plane in {"Back", "Left"}:
        side_x, side_y = _side_plane_frame_shift(evaluation, "Right")
        header_dz = evaluation.final_state.get("pieza", "header_dz")
        for line in (
            "MLV=1",
            f"SHF[X]={_fmt(side_x)}",
            f"SHF[Y]={_fmt(side_y)}",
            f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        ):
            _append(
                lines,
                line,
                differential,
                source,
                "Restauracion de marco lateral antes de volver a ranura superior.",
                confidence="confirmed",
                rule_status="generalized_side_to_slot_milling_sequence",
                transition_id=transition_id,
            )
    for line in (
        "?%ETK[8]=1",
        "G40",
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "?%ETK[0]=0",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Transicion observada entre taladro lateral y ranura superior.",
            confidence="confirmed",
            rule_status="generalized_side_to_slot_milling_sequence",
            transition_id=transition_id,
        )


def _emit_slot_milling_prepare_after_top(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    transition_id: Optional[str] = None,
    emit_mlv_after_g17: bool = False,
) -> None:
    spindle = _change_after(differential, "herramienta", "spindle")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    etk1 = _change_after(differential, "salida", "etk_1")
    etk17 = _optional_change_after(differential, "salida", "etk_17", None)
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    prepare_lines = [
        f"?%ETK[6]={int(spindle)}",
        "G17",
    ]
    if emit_mlv_after_g17:
        prepare_lines.append("MLV=2")
    if etk17 is not None:
        prepare_lines.extend((f"?%ETK[17]={int(etk17)}", f"S{int(spindle_speed)}M3"))
    prepare_lines.extend(
        (
            f"?%ETK[1]={int(etk1)}",
            "MLV=2",
            f"SHF[X]={_fmt(shf_x)}",
            f"SHF[Y]={_fmt(shf_y)}",
            f"SHF[Z]={_fmt(shf_z)}",
        )
    )
    for line in prepare_lines:
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
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    spindle = _change_after(differential, "herramienta", "spindle")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    etk1 = _change_after(differential, "salida", "etk_1")
    etk17 = _optional_change_after(differential, "salida", "etk_17", None)
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    prep_origin_x = length + (2 * origin_x)
    frame_x = length + origin_x
    prepare_lines = [
        f"?%ETK[6]={int(spindle)}",
        "G17",
        "MLV=2",
        f"%Or[0].ofX={_fmt_scaled(-prep_origin_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
        "MLV=1",
        f"SHF[X]={_fmt(-frame_x)}",
        f"SHF[Y]={_fmt(_base_shf_y(origin_y))}",
        f"SHF[Z]={_fmt(header_dz)}",
        "MLV=2",
    ]
    if etk17 is not None:
        prepare_lines.extend((f"?%ETK[17]={int(etk17)}", f"S{int(spindle_speed)}M3"))
    prepare_lines.extend(
        (
            f"?%ETK[1]={int(etk1)}",
            "MLV=2",
            f"SHF[X]={_fmt(shf_x)}",
            f"SHF[Y]={_fmt(shf_y)}",
            f"SHF[Z]={_fmt(shf_z)}",
        )
    )
    for line in prepare_lines:
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
    emit_transition_exit: bool = False,
    emit_etk7_before_lift: bool = False,
) -> None:
    rapid_x = _change_after(differential, "movimiento", "rapid_x")
    rapid_y = _change_after(differential, "movimiento", "rapid_y")
    cut_x = _change_after(differential, "movimiento", "cut_x")
    rapid_z = _change_after(differential, "movimiento", "rapid_z")
    cut_z = _change_after(differential, "movimiento", "cut_z")
    security_z = _change_after(differential, "movimiento", "security_z")
    tool_offset = _change_after(differential, "herramienta", "tool_offset_length")
    tool_radius = _change_after(differential, "herramienta", "tool_radius")
    plunge_feed = _change_after(differential, "movimiento", "plunge_feed")
    milling_feed = _change_after(differential, "movimiento", "milling_feed")
    source = _change_source(differential, "movimiento", "cut_z")
    motion_lines = [
        f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)}",
        f"G0 Z{_fmt(rapid_z)}",
        "D1",
        f"SVL {_fmt(tool_offset)}",
        f"VL6={_fmt(tool_offset)}",
        f"SVR {_fmt(tool_radius)}",
        f"VL7={_fmt(tool_radius)}",
        f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",
        "?%ETK[7]=1",
        _line_milling_motion_line(
            float(cut_x),
            float(rapid_y),
            float(cut_z),
            float(rapid_x),
            float(rapid_y),
            float(cut_z),
            float(milling_feed),
        ),
    ]
    if emit_transition_exit:
        clearance_x = float(rapid_x) - 0.75
        motion_lines.extend(
            [
                f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 X{_fmt(clearance_x)} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 X{_fmt(rapid_x)} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 Z{_fmt(cut_z)} F{_fmt(milling_feed)}",
            ]
        )
    if emit_etk7_before_lift:
        motion_lines.append("?%ETK[7]=0")
    motion_lines.append(f"G0 Z{_fmt(security_z)}")
    for line in motion_lines:
        _append(
            lines,
            line,
            differential,
            source,
            "Traza SlotSide con sierra vertical derivada de toolpath compensado.",
            confidence="confirmed",
            rule_status="generalized_slot_milling_006_011_087_091",
        )


def _emit_slot_milling_reset(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    *,
    final: bool = True,
    emit_etk7: bool = True,
) -> None:
    source = _observed_rule_source("slot_milling_reset")
    reset_lines = [
        "D0",
        "SVL 0.000",
        "VL6=0.000",
        "SVR 0.000",
        "VL7=0.000",
    ]
    if emit_etk7:
        reset_lines.append("?%ETK[7]=0")
    if final:
        reset_lines.extend(
            (
                "G61",
                "MLV=0",
                "?%ETK[1]=0",
                "?%ETK[17]=0",
                "G4F1.200",
                "M5",
                "D0",
            )
        )
    for line in reset_lines:
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior SlotSide con sierra vertical observado.",
            confidence="confirmed",
            rule_status="generalized_slot_milling_006_011_087_091",
        )


def _emit_side_drill_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_prepare: Optional[StageDifferential] = None,
    previous_trace: Optional[StageDifferential] = None,
    multi_side_sequence: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    plane = str(_change_after(differential, "trabajo", "plane"))
    spindle = _change_after(differential, "herramienta", "spindle")
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    frame_x, frame_y = _side_plane_frame_shift(evaluation, plane)
    source = _change_source(differential, "herramienta", "tool_offset_length")
    prep_origin_x = length + (2 * origin_x)
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
        for line in (
            "MLV=1",
            f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
            "MLV=2",
            "G17",
        ):
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
            axis = str(_change_after(differential, "movimiento", "side_axis"))
            if axis == "X" and previous_trace is not None:
                previous_approach = _trace_move(previous_trace, "Approach").points[0]
                _append(
                    lines,
                    f"G0 X{_fmt(previous_approach.x)} Y{_fmt(previous_approach.y)} Z{_fmt(previous_approach.iso_z)}",
                    differential,
                    source,
                    "Reposicion lateral antes de repetir el mismo spindle.",
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
                        "Pausa observada antes de repetir taladro lateral.",
                        confidence="confirmed",
                        rule_status="generalized_side_drill_sequence",
                        transition_id=transition_id,
                    )
            else:
                reposition_lines = ["MLV=0", "G0 G53 Z201.000", "MLV=2"]
                if multi_side_sequence:
                    reposition_lines.append("G4F0.500")
                for line in tuple(reposition_lines):
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
        _append(
            lines,
            f"?%ETK[6]={int(spindle)}",
            differential,
            source,
            "Cambio de spindle lateral desde politica de cara.",
            confidence="confirmed",
            rule_status="generalized_side_drill_sequence",
            transition_id=transition_id,
        )
        park_z = _side_drill_g53_z(evaluation, previous_prepare, differential)
        for line in ("MLV=0", f"G0 G53 Z{_fmt(park_z)}", "MLV=2", "MLV=2"):
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
        for line in (f"SHF[X]={_fmt(shf_x)}", f"SHF[Y]={_fmt(shf_y)}", f"SHF[Z]={_fmt(shf_z)}"):
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
    for line in ("MLV=2", "G17"):
        _append(
            lines,
            line,
            differential,
            source,
            "Modo/plano observado en preparacion de taladro lateral.",
            rule_status="side_drill_modal_observed",
        )
    for line in (f"?%ETK[6]={int(spindle)}", f"%Or[0].ofX={_fmt_scaled(-prep_origin_x)}"):
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
        "%Or[0].ofY=-1515599.976",
        differential,
        _observed_rule_source("side_drill_prepare"),
        "Constante de campo HG observada; fuente de maquina/campo pendiente.",
        confidence="observed",
        rule_status="field_constant_pending_source",
    )
    _append(
        lines,
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
        differential,
        source,
        "Preparacion lateral derivada de depth + origin_z.",
        confidence="confirmed",
        rule_status="generalized_side_drill_010_013",
    )
    _append(
        lines,
        "MLV=1",
        differential,
        source,
        "Cambio modal observado durante preparacion de herramienta lateral.",
        rule_status="side_drill_modal_observed",
    )
    for line in (
        f"SHF[X]={_fmt(frame_x)}",
        f"SHF[Y]={_fmt(frame_y)}",
        f"SHF[Z]={_fmt(origin_z)}",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Marco operativo lateral derivado de cara, origen y dimensiones.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    for line in ("MLV=2", "MLV=2"):
        _append(
            lines,
            line,
            differential,
            source,
            "Cambio modal observado durante preparacion lateral.",
            rule_status="side_drill_modal_observed",
        )
    for line in (f"SHF[X]={_fmt(shf_x)}", f"SHF[Y]={_fmt(shf_y)}", f"SHF[Z]={_fmt(shf_z)}"):
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
    for line in (
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        "G0 G53 Z201.000",
        "G64",
    ):
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
    multi_side_sequence: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    spindle = _change_after(differential, "herramienta", "spindle")
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={int(spindle)}",
        "MLV=2",
        f"SHF[X]={_fmt(shf_x)}",
        f"SHF[Y]={_fmt(shf_y)}",
        f"SHF[Z]={_fmt(shf_z)}",
    ):
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
    if speed_activation is not None:
        spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
        _append(
            lines,
            f"?%ETK[17]={int(speed_activation.after)}",
            differential,
            speed_activation.source,
            "Activacion de velocidad lateral despues de router.",
            confidence=speed_activation.confidence,
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
    transition_id: Optional[str] = None,
) -> None:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    spindle = _change_after(differential, "herramienta", "spindle")
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    for line in (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={int(spindle)}",
        "MLV=2",
        f"SHF[X]={_fmt(shf_x)}",
        f"SHF[Y]={_fmt(shf_y)}",
        f"SHF[Z]={_fmt(shf_z)}",
    ):
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


def _emit_side_drill_prepare_after_top(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    multi_side_sequence: bool = False,
    transition_id: Optional[str] = None,
) -> None:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    plane = str(_change_after(differential, "trabajo", "plane"))
    spindle = _change_after(differential, "herramienta", "spindle")
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    _emit_side_plane_selection(lines, evaluation, differential, plane, include_right_frame=False)
    for line in (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={int(spindle)}",
        "MLV=0",
        f"G0 G53 Z{_fmt(_side_drill_g53_z(evaluation, differential))}",
        "MLV=2",
        "MLV=2",
        f"SHF[X]={_fmt(shf_x)}",
        f"SHF[Y]={_fmt(shf_y)}",
        f"SHF[Z]={_fmt(shf_z)}",
    ):
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
    axis = str(_change_after(differential, "movimiento", "side_axis"))
    rapid = _change_after(differential, "movimiento", "side_rapid")
    cut = _change_after(differential, "movimiento", "side_cut")
    fixed = (
        fixed_override
        if fixed_override is not None
        else _change_after(differential, "movimiento", "side_fixed")
    )
    z = _change_after(differential, "movimiento", "side_z")
    feed = _change_after(differential, "movimiento", "side_feed")
    source = _change_source(differential, "movimiento", "side_iso_rule")
    if axis == "X":
        rapid_line = f"G0 X{_fmt(rapid)} Y{_fmt(fixed)}"
        rapid_z_line = f"G0 X{_fmt(rapid)} Y{_fmt(fixed)} Z{_fmt(z)}" if combine_rapid_z else f"G0 Z{_fmt(z)}"
        cut_line = f"G1 G9 X{_fmt(cut)} F{_fmt(feed)}"
        retract_line = f"G0 X{_fmt(rapid)} Z{_fmt(z)}"
    else:
        rapid_line = f"G0 X{_fmt(fixed)} Y{_fmt(rapid)}"
        rapid_z_line = f"G0 X{_fmt(fixed)} Y{_fmt(rapid)} Z{_fmt(z)}" if combine_rapid_z else f"G0 Z{_fmt(z)}"
        cut_line = f"G1 G9 Y{_fmt(cut)} F{_fmt(feed)}"
        retract_line = f"G0 Y{_fmt(rapid)} Z{_fmt(z)}"
    for line in (rapid_z_line,) if combine_rapid_z else (rapid_line, rapid_z_line):
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Side Drill calculada desde punto PGMX y spindle lateral.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    modal_lines = ("?%ETK[7]=3", "MLV=2") if emit_mlv_after_etk7 else ("?%ETK[7]=3",)
    for line in modal_lines:
        _append(
            lines,
            line,
            differential,
            _observed_rule_source("side_drill_trace"),
            "Comando modal observado en traza lateral; fuente causal pendiente.",
            confidence="hypothesis",
            rule_status="modal_trace_hypothesis",
        )
    for line in (cut_line, retract_line):
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
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    etk17 = _reset_after(differential, "salida", "etk_17")
    source = _change_source(differential, "salida", "etk_17", reset=True)
    for line in (
        "MLV=1",
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior de taladro lateral observado.",
            rule_status="side_drill_reset_observed",
        )
    if not final:
        return
    _append(
        lines,
        "G61",
        differential,
        _observed_rule_source("side_drill_reset"),
        "Reset observado; falta clasificar si depende de familia o plantilla.",
        confidence="hypothesis",
        rule_status="modal_reset_hypothesis",
    )
    for line in (
        "MLV=0",
        "?%ETK[0]=0",
        f"?%ETK[17]={int(etk17)}",
        "G4F1.200",
        "M5",
        "D0",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior de taladro lateral observado.",
            rule_status="side_drill_reset_observed",
        )


def _emit_top_drill_reset(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    final: bool = True,
) -> None:
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    source = _change_source(differential, "salida", "etk_17", reset=True)
    for line in (
        "MLV=1",
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior de taladro superior observado.",
            rule_status="top_drill_reset_observed",
        )
    if not final:
        return
    etk17 = _reset_after(differential, "salida", "etk_17")
    _append(
        lines,
        "G61",
        differential,
        _observed_rule_source("top_drill_reset"),
        "Reset observado; falta clasificar si depende de familia o plantilla.",
        confidence="hypothesis",
        rule_status="modal_reset_hypothesis",
    )
    for line in (
        "MLV=0",
        "?%ETK[0]=0",
        f"?%ETK[17]={int(etk17)}",
        "G4F1.200",
        "M5",
        "D0",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Reset posterior de taladro superior observado.",
            rule_status="top_drill_reset_observed",
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
        close_x = _optional_change_after(differential, "movimiento", "program_close_x", -3700.0)
        close_y = _optional_change_after(differential, "movimiento", "program_close_y", None)
        close_xy_line = f"G0 G53 X{_fmt(close_x)}"
        if close_y is not None:
            close_xy_line += f" Y{_fmt(close_y)}"
        for line in (
            "G61",
            "MLV=0",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            "M5",
            "D0",
            "G0 G53 Z201.000",
            close_xy_line,
            "G64",
        ):
            _append(
                lines,
                line,
                differential,
                source,
                "Cierre router E004 observado antes del reset comun.",
                rule_status="machine_close_observed",
            )
    else:
        close_x = _optional_change_after(differential, "movimiento", "program_close_x", -3700.0)
        close_y = _optional_change_after(differential, "movimiento", "program_close_y", None)
        close_xy_line = f"G0 G53 X{_fmt(close_x)}"
        if close_y is not None:
            close_xy_line += f" Y{_fmt(close_y)}"
        mixed_side_close = plane == "Right" and _has_non_side_work(evaluation) and float(close_x) != -3700.0
        if mixed_side_close:
            _emit_side_program_close_prefix(lines, differential, plane)
            close_lines = (close_xy_line, "G64")
        else:
            close_lines = ("G0 G53 Z201.000", close_xy_line, "G64")
        for line in close_lines:
            _append(lines, line, differential, source, "Cierre comun observado.", rule_status="machine_close_observed")
    if family not in _ROUTER_MILLING_FAMILIES and plane != "Top":
        if plane in {"Left", "Back"}:
            length = evaluation.initial_state.get("pieza", "length")
            origin_x = evaluation.initial_state.get("pieza", "origin_x")
            origin_y = evaluation.initial_state.get("pieza", "origin_y")
            header_dz = evaluation.final_state.get("pieza", "header_dz")
            for line in (
                "MLV=1",
                f"SHF[X]={_fmt(-(length + origin_x))}",
                f"SHF[Y]={_fmt(_base_shf_y(origin_y))}",
                f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
            ):
                _append(
                    lines,
                    line,
                    differential,
                    source,
                    "Reentrada de marco lateral antes del cierre comun.",
                    rule_status="machine_close_observed",
                )
        _append(
            lines,
            "G61",
            differential,
            source,
            "Reset lateral observado antes del cierre comun.",
            confidence="hypothesis",
            rule_status="modal_reset_hypothesis",
        )
        if plane in {"Left", "Back"}:
            _append(
                lines,
                "MLV=0",
                differential,
                source,
                "Reset lateral observado antes del cierre comun.",
                rule_status="machine_close_observed",
            )
        for line in ("D0", "G0 G53 Z201.000", "G64"):
            _append(
                lines,
                line,
                differential,
                source,
                "Reset lateral observado antes del cierre comun.",
                rule_status="machine_close_observed",
            )
    for line in ("SYN",):
        _append(
            lines,
            line,
            differential,
            source,
            "Comando de cierre observado; causalidad todavia no aislada.",
            confidence="hypothesis",
            rule_status="machine_close_hypothesis",
        )
    for line in (
        "?%ETK[0]=0",
        "?%ETK[1]=0",
        "?%ETK[2]=0",
        "?%ETK[13]=0",
        "?%ETK[17]=0",
        "?%ETK[18]=0",
        "?%ETK[19]=0",
        "?%EDK[13].0=1",
        "MLV=1",
        "SHF[X]=0",
        "SHF[Y]=0",
        "SHF[Z]=0",
        "MLV=2",
        "SHF[X]=0",
        "SHF[Y]=0",
        "SHF[Z]=0",
        "MLV=0",
        "VL6=0",
        "VL7=0",
        "?%EDK[13].0=0",
        "M2",
    ):
        _append(lines, line, differential, source, "Cierre comun observado.", rule_status="machine_close_observed")


def _emit_side_program_close_prefix(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
    plane: str,
) -> None:
    source = _observed_rule_source("side_program_close")
    for line in (
        "G0 G53 Z201.000",
        "G64",
        f"?%ETK[8]={_side_etk8_for_plane(plane)}",
        "G40",
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=0",
        "T1",
        "SYN",
        "M06",
        "G61",
        "D0",
        "G0 G53 Z201.000",
    ):
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
        close_x = _optional_change_after(differential, "movimiento", "program_close_x", -3700.0)
        for line in (
            "G61",
            "MLV=0",
            "D0",
            "G0 G53 Z201.000",
            f"G0 G53 X{_fmt(close_x)}",
            "G64",
        ):
            _append(
                lines,
                line,
                differential,
                source,
                "Cierre observado para programa vacio con Xn explicito.",
                confidence="confirmed",
                rule_status="generalized_empty_program",
            )
    for line in (
        "SYN",
        "?%ETK[0]=0",
        "?%ETK[1]=0",
        "?%ETK[2]=0",
        "?%ETK[13]=0",
        "?%ETK[17]=0",
        "?%ETK[18]=0",
        "?%ETK[19]=0",
        "?%EDK[13].0=1",
        "MLV=1",
        "SHF[X]=0",
        "SHF[Y]=0",
        "SHF[Z]=0",
        "MLV=2",
        "SHF[X]=0",
        "SHF[Y]=0",
        "SHF[Z]=0",
        "MLV=0",
        "VL6=0",
        "VL7=0",
        "?%EDK[13].0=0",
        "M2",
    ):
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


def _has_non_side_work(evaluation: IsoStateEvaluation) -> bool:
    for differential in evaluation.differentials:
        if differential.stage_key in _COMMON_STAGE_KEYS:
            continue
        for change in differential.target_changes + differential.forced_values:
            if change.layer == "trabajo" and change.key == "family" and str(change.after) != "side_drill":
                return True
    return False


def _first_work_value(
    evaluation: IsoStateEvaluation,
    layer: str,
    key: str,
    default: object = None,
) -> object:
    for differential in sorted(evaluation.differentials, key=lambda item: item.order_index):
        if differential.stage_key in _COMMON_STAGE_KEYS:
            continue
        for change in differential.target_changes + differential.forced_values:
            if change.layer == layer and change.key == key:
                return change.after
    return default


def _side_value(evaluation: IsoStateEvaluation, layer: str, key: str) -> object:
    for differential in evaluation.differentials:
        for change in differential.target_changes + differential.forced_values:
            if change.layer == layer and change.key == key:
                return change.after
    raise IsoCandidateEmissionError(f"El plan no contiene {layer}.{key}.")


def _side_plane_frame_shift(evaluation: IsoStateEvaluation, plane_name: str) -> tuple[float, float]:
    length = evaluation.initial_state.get("pieza", "length")
    width = evaluation.initial_state.get("pieza", "width")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    base_x = -(length + origin_x)
    base_y = _base_shf_y(origin_y)
    if plane_name == "Left":
        return base_x, base_y + width
    if plane_name == "Back":
        return base_x + length, base_y
    return base_x, base_y


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


def _polyline_leaves_workpiece(
    evaluation: IsoStateEvaluation,
    points: Sequence[tuple[float, float]],
) -> bool:
    length = float(evaluation.initial_state.get("pieza", "length"))
    width = float(evaluation.initial_state.get("pieza", "width"))
    tolerance = 0.0005
    return any(
        x < -tolerance
        or y < -tolerance
        or x > length + tolerance
        or y > width + tolerance
        for x, y in points
    )


def _side_drill_g53_z(
    evaluation: IsoStateEvaluation,
    *side_prepares: StageDifferential,
) -> float:
    shf_z_values = [
        float(_change_after(prepare, "herramienta", "shf_z"))
        for prepare in side_prepares
    ]
    if not shf_z_values:
        raise IsoCandidateEmissionError("No hay SHF_Z lateral para calcular G53 Z.")
    header_dz = float(evaluation.final_state.get("pieza", "header_dz"))
    return header_dz + (2.0 * _maestro_security_distance()) + max(shf_z_values)


@lru_cache(maxsize=1)
def _maestro_security_distance() -> float:
    path = _resolve_project_path(PROGRAMACIONES_SETTINGSX_PATH)
    if not path.exists():
        raise IsoCandidateEmissionError(f"No existe la configuracion Maestro: {PROGRAMACIONES_SETTINGSX_PATH}.")
    for text in _settingsx_texts(path):
        value = _xml_app_setting(text, "SecurityDistance")
        if value is not None:
            return float(value)
    raise IsoCandidateEmissionError(f"No se encontro SecurityDistance en {PROGRAMACIONES_SETTINGSX_PATH}.")


def _settingsx_texts(path: Path) -> tuple[str, ...]:
    if zipfile.is_zipfile(path):
        texts: list[str] = []
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.lower().endswith(".config"):
                    continue
                texts.append(archive.read(name).decode("utf-8-sig"))
        return tuple(texts)
    return (path.read_text(encoding="utf-8-sig"),)


def _xml_app_setting(text: str, key: str) -> Optional[str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "add" and element.attrib.get("key") == key:
            return element.attrib.get("value")
    return None


def _resolve_project_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.exists():
        return path
    return Path(__file__).resolve().parent.parent / path


def _side_etk8_for_plane(plane_name: str) -> int:
    return {
        "Left": 3,
        "Right": 2,
        "Front": 5,
        "Back": 4,
    }.get(plane_name, 1)


def _base_shf_y(origin_y: object = 0.0) -> float:
    return -1515.6 + float(origin_y)


def _line_milling_motion_line(
    x: float,
    y: float,
    z: float,
    previous_x: float,
    previous_y: float,
    previous_z: float,
    feed: float,
    *,
    always_include_z: bool = True,
) -> str:
    words = ["G1"]
    if abs(x - previous_x) >= 0.0005:
        words.append(f"X{_fmt(x)}")
    if abs(y - previous_y) >= 0.0005:
        words.append(f"Y{_fmt(y)}")
    if always_include_z or abs(z - previous_z) >= 0.0005:
        words.append(f"Z{_fmt(z)}")
    words.append(f"F{_fmt(feed)}")
    return " ".join(words)


def _no_lead_compensation_points(
    points: tuple[tuple[float, float], ...],
    tool_radius: float,
    profile_family: str,
    profile_winding: str,
) -> tuple[tuple[float, float], tuple[float, float]]:
    if len(points) < 2:
        raise IsoCandidateEmissionError("La traza sin lead no contiene puntos nominales suficientes.")
    lead = 1.0
    start_x, start_y = points[0]
    end_x, end_y = points[-1]
    if profile_family == "Circle":
        direction = -1.0 if profile_winding == "CounterClockwise" else 1.0
        return (start_x, start_y + direction * lead), (end_x, end_y - direction * lead)
    first_dx, first_dy = _unit_vector(points[0], points[1])
    last_dx, last_dy = _unit_vector(points[-2], points[-1])
    return (
        (start_x - first_dx * lead, start_y - first_dy * lead),
        (end_x + last_dx * lead, end_y + last_dy * lead),
    )


def _polyline_side_compensation_leads(
    points: tuple[tuple[float, float], ...],
    tool_radius: float,
    side_of_feature: str,
    approach_type: str,
    radius_multiplier: float,
) -> dict[str, tuple[float, float]]:
    if len(points) < 2:
        raise IsoCandidateEmissionError("La polilinea compensada no contiene puntos nominales suficientes.")
    lead_distance = float(tool_radius) * float(radius_multiplier)
    rapid_extra = 1.0
    first_dx, first_dy = _unit_vector(points[0], points[1])
    last_dx, last_dy = _unit_vector(points[-2], points[-1])
    start_x, start_y = points[0]
    end_x, end_y = points[-1]
    if approach_type == "Arc":
        start_nx, start_ny = _side_normal(first_dx, first_dy, side_of_feature)
        end_nx, end_ny = _side_normal(last_dx, last_dy, side_of_feature)
        entry_center = (
            start_x + start_nx * lead_distance,
            start_y + start_ny * lead_distance,
        )
        entry = (
            entry_center[0] - first_dx * lead_distance,
            entry_center[1] - first_dy * lead_distance,
        )
        exit_center = (
            end_x + end_nx * lead_distance,
            end_y + end_ny * lead_distance,
        )
        exit_point = (
            exit_center[0] + last_dx * lead_distance,
            exit_center[1] + last_dy * lead_distance,
        )
        return {
            "entry_rapid": (entry[0] + start_nx * rapid_extra, entry[1] + start_ny * rapid_extra),
            "entry": entry,
            "entry_center": entry_center,
            "exit": exit_point,
            "exit_center": exit_center,
            "exit_rapid": (exit_point[0] + end_nx * rapid_extra, exit_point[1] + end_ny * rapid_extra),
        }
    return {
        "entry_rapid": (
            start_x - first_dx * (lead_distance + rapid_extra),
            start_y - first_dy * (lead_distance + rapid_extra),
        ),
        "entry": (
            start_x - first_dx * lead_distance,
            start_y - first_dy * lead_distance,
        ),
        "exit": (
            end_x + last_dx * lead_distance,
            end_y + last_dy * lead_distance,
        ),
        "exit_rapid": (
            end_x + last_dx * (lead_distance + rapid_extra),
            end_y + last_dy * (lead_distance + rapid_extra),
        ),
    }


def _side_normal(dx: float, dy: float, side_of_feature: str) -> tuple[float, float]:
    if side_of_feature == "Left":
        return -dy, dx
    return dy, -dx


def _unit_vector(
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 0.0005:
        raise IsoCandidateEmissionError("Segmento de trayectoria con longitud cero.")
    return dx / length, dy / length


def _profile_arc_leads_from_pgmxd_toolpaths(
    contour_points: object,
    approach_primitives: tuple[tuple[object, ...], ...],
    lift_primitives: tuple[tuple[object, ...], ...],
    tool_radius: float,
    arc_code: str,
) -> dict[str, tuple[float, float]]:
    approach_arc = _first_arc_primitive(approach_primitives)
    retract_arc = _first_arc_primitive(lift_primitives)
    entry = _programmed_arc_point_from_centerline(approach_arc, "start", tool_radius)
    contour_entry = _programmed_arc_point_from_centerline(approach_arc, "end", tool_radius)
    contour_exit = _programmed_arc_point_from_centerline(retract_arc, "start", tool_radius)
    exit_point = _programmed_arc_point_from_centerline(retract_arc, "end", tool_radius)
    approach_center = _primitive_center_xy(approach_arc)
    retract_center = _primitive_center_xy(retract_arc)
    entry_tangent = _arc_forward_tangent(arc_code, approach_center, entry)
    exit_tangent = _arc_forward_tangent(arc_code, retract_center, exit_point)
    rapid = (entry[0] - entry_tangent[0], entry[1] - entry_tangent[1])
    leadout = (exit_point[0] + exit_tangent[0], exit_point[1] + exit_tangent[1])
    return {
        "rapid": rapid,
        "entry": entry,
        "contour_entry": contour_entry,
        "exit_start": contour_exit,
        "exit": exit_point,
        "leadout": leadout,
        "approach_center": approach_center,
        "retract_center": retract_center,
    }


def _first_arc_primitive(
    primitives: tuple[tuple[object, ...], ...],
) -> tuple[object, ...]:
    for primitive in primitives:
        if primitive and str(primitive[0]) == "Arc":
            return primitive
    raise IsoCandidateEmissionError("El perfil E001 indica arco pero el PGMX no trae primitiva Arc.")


def _primitive_center_xy(primitive: tuple[object, ...]) -> tuple[float, float]:
    if primitive[7] is None or primitive[8] is None:
        raise IsoCandidateEmissionError("La primitiva Arc del PGMX no trae centro.")
    return float(primitive[7]), float(primitive[8])


def _programmed_arc_point_from_centerline(
    primitive: tuple[object, ...],
    endpoint: str,
    tool_radius: float,
) -> tuple[float, float]:
    center_x, center_y = _primitive_center_xy(primitive)
    if endpoint == "start":
        point_x, point_y = float(primitive[1]), float(primitive[2])
    elif endpoint == "end":
        point_x, point_y = float(primitive[4]), float(primitive[5])
    else:
        raise IsoCandidateEmissionError(f"Endpoint de arco no soportado: {endpoint}.")
    vector_x = point_x - center_x
    vector_y = point_y - center_y
    centerline_radius = math.hypot(vector_x, vector_y)
    if centerline_radius < 0.0005:
        raise IsoCandidateEmissionError("La primitiva Arc del PGMX tiene radio cero.")
    programmed_radius = centerline_radius + tool_radius
    scale = programmed_radius / centerline_radius
    return center_x + (vector_x * scale), center_y + (vector_y * scale)


def _arc_forward_tangent(
    arc_code: str,
    center: tuple[float, float],
    point: tuple[float, float],
) -> tuple[float, float]:
    radius_x = point[0] - center[0]
    radius_y = point[1] - center[1]
    radius = math.hypot(radius_x, radius_y)
    if radius < 0.0005:
        raise IsoCandidateEmissionError("No se puede calcular tangente de arco con radio cero.")
    unit_x = radius_x / radius
    unit_y = radius_y / radius
    if arc_code == "G2":
        return unit_y, -unit_x
    return -unit_y, unit_x


def _profile_milling_arc_line(
    code: str,
    x: object,
    y: object,
    i: object,
    j: object,
    feed: object,
    *,
    z: Optional[object] = None,
) -> str:
    words = [code, f"X{_fmt(x)}", f"Y{_fmt(y)}"]
    if z is not None:
        words.append(f"Z{_fmt(z)}")
    words.extend((f"I{_fmt(i)}", f"J{_fmt(j)}", f"F{_fmt(feed)}"))
    return " ".join(words)


def _profile_toolpath_motion_line(
    point,
    previous_x: float,
    previous_y: float,
    previous_z: float,
    feed: float,
    *,
    center: Optional[tuple[float, float]] = None,
    winding: str = "",
    always_include_z: bool = True,
) -> str:
    if center is not None:
        code = _arc_code_from_points(
            previous_x,
            previous_y,
            float(point.x),
            float(point.y),
            center[0],
            center[1],
            winding=winding,
        )
        return _profile_milling_arc_line(
            code,
            point.x,
            point.y,
            center[0],
            center[1],
            feed,
            z=point.iso_z if abs(float(point.iso_z) - previous_z) >= 0.0005 else None,
        )
    return _line_milling_motion_line(
        float(point.x),
        float(point.y),
        float(point.iso_z),
        previous_x,
        previous_y,
        previous_z,
        feed,
        always_include_z=always_include_z,
    )


def _closed_polyline_center_lead_geometry(
    contour_points: tuple[tuple[float, float], ...],
    lead_distance: float,
    lead_type: str,
    winding: str,
) -> dict[str, tuple[float, float]]:
    if len(contour_points) < 2:
        raise IsoCandidateEmissionError("La polilinea cerrada no contiene suficientes puntos.")
    start = contour_points[0]
    next_point = contour_points[1]
    tangent_x, tangent_y = _unit_vector(start, next_point)
    normal_sign = 1.0 if winding == "CounterClockwise" else -1.0
    normal_x = -tangent_y * normal_sign
    normal_y = tangent_x * normal_sign
    if lead_type == "Arc":
        rapid = (
            start[0] - (tangent_x * lead_distance) + (normal_x * lead_distance),
            start[1] - (tangent_y * lead_distance) + (normal_y * lead_distance),
        )
        exit_point = (
            start[0] + (tangent_x * lead_distance) + (normal_x * lead_distance),
            start[1] + (tangent_y * lead_distance) + (normal_y * lead_distance),
        )
        center = (
            start[0] + (normal_x * lead_distance),
            start[1] + (normal_y * lead_distance),
        )
    else:
        rapid = (
            start[0] - (tangent_x * lead_distance),
            start[1] - (tangent_y * lead_distance),
        )
        exit_point = (
            start[0] + (tangent_x * lead_distance),
            start[1] + (tangent_y * lead_distance),
        )
        center = start
    return {
        "rapid": rapid,
        "exit": exit_point,
        "approach_center": center,
        "retract_center": center,
    }


def _open_polyline_center_lead_geometry(
    contour_points: tuple[tuple[float, float], ...],
    lead_distance: float,
    lead_type: str,
) -> dict[str, tuple[float, float]]:
    if len(contour_points) < 2:
        raise IsoCandidateEmissionError("La polilinea abierta no contiene suficientes puntos.")
    start = contour_points[0]
    next_point = contour_points[1]
    previous_point = contour_points[-2]
    end = contour_points[-1]
    start_tx, start_ty = _unit_vector(start, next_point)
    end_tx, end_ty = _unit_vector(previous_point, end)
    start_normal = (-start_ty, start_tx)
    end_normal = (-end_ty, end_tx)
    if lead_type == "Arc":
        rapid = (
            start[0] - (start_tx * lead_distance) + (start_normal[0] * lead_distance),
            start[1] - (start_ty * lead_distance) + (start_normal[1] * lead_distance),
        )
        exit_point = (
            end[0] + (end_tx * lead_distance) + (end_normal[0] * lead_distance),
            end[1] + (end_ty * lead_distance) + (end_normal[1] * lead_distance),
        )
        approach_center = (
            start[0] + (start_normal[0] * lead_distance),
            start[1] + (start_normal[1] * lead_distance),
        )
        retract_center = (
            end[0] + (end_normal[0] * lead_distance),
            end[1] + (end_normal[1] * lead_distance),
        )
    else:
        rapid = (
            start[0] - (start_tx * lead_distance),
            start[1] - (start_ty * lead_distance),
        )
        exit_point = (
            end[0] + (end_tx * lead_distance),
            end[1] + (end_ty * lead_distance),
        )
        approach_center = start
        retract_center = end
    return {
        "rapid": rapid,
        "exit": exit_point,
        "approach_center": approach_center,
        "retract_center": retract_center,
    }


def _matching_primitive_record(
    records: tuple[object, ...],
    start_index: int,
    point,
    previous_x: float,
    previous_y: float,
) -> tuple[int, Optional[tuple[object, ...]]]:
    for index in range(start_index, len(records)):
        record = records[index]
        if not isinstance(record, tuple) or len(record) < 14:
            continue
        if _primitive_record_matches_move(record, point, previous_x, previous_y):
            return index, record
    return -1, None


def _primitive_record_matches_move(
    record: tuple[object, ...],
    point,
    previous_x: float,
    previous_y: float,
) -> bool:
    if point.x is None or point.y is None or point.local_z is None:
        return False
    return (
        math.isclose(float(record[1]), previous_x, abs_tol=0.0005)
        and math.isclose(float(record[2]), previous_y, abs_tol=0.0005)
        and math.isclose(float(record[4]), float(point.x), abs_tol=0.0005)
        and math.isclose(float(record[5]), float(point.y), abs_tol=0.0005)
        and math.isclose(float(record[6]), float(point.local_z), abs_tol=0.0005)
    )


def _arc_record_motion_line(
    record: tuple[object, ...],
    point,
    previous_z: float,
    feed: float,
    *,
    fallback_center: tuple[float, float],
    fallback_winding: str = "",
) -> str:
    center = _iso_arc_center_from_record(record, fallback_center)
    code = _arc_code_from_record(record, fallback_winding)
    return _profile_milling_arc_line(
        code,
        point.x,
        point.y,
        center[0],
        center[1],
        feed,
        z=point.iso_z if abs(float(point.iso_z) - previous_z) >= 0.0005 else None,
    )


def _arc_code_from_record(record: tuple[object, ...], fallback_winding: str = "") -> str:
    normal_z = record[13]
    if normal_z is not None:
        return "G3" if float(normal_z) >= 0.0 else "G2"
    return "G3" if fallback_winding == "CounterClockwise" else "G2"


def _iso_arc_center_from_record(
    record: tuple[object, ...],
    fallback_center: tuple[float, float],
) -> tuple[float, float]:
    if record[7] is None or record[8] is None:
        return fallback_center
    center_x = float(record[7])
    center_y = float(record[8])
    if record[10] is None or record[13] is None:
        return center_x, center_y

    start_x = float(record[1])
    start_y = float(record[2])
    end_x = float(record[4])
    end_y = float(record[5])
    radius = float(record[10])
    flat_radius = math.hypot(start_x - center_x, start_y - center_y)
    center_offset = radius - flat_radius
    chord_length = math.hypot(end_x - start_x, end_y - start_y)
    if center_offset <= 0.0005 or chord_length <= 0.0005:
        return center_x, center_y

    right_normal_x = (end_y - start_y) / chord_length
    right_normal_y = -(end_x - start_x) / chord_length
    normal_sign = 1.0 if float(record[13]) >= 0.0 else -1.0
    return (
        center_x + (normal_sign * right_normal_x * center_offset),
        center_y + (normal_sign * right_normal_y * center_offset),
    )


def _xy_changed(previous_x: float, previous_y: float, point) -> bool:
    return (
        abs(float(point.x) - previous_x) >= 0.0005
        and abs(float(point.y) - previous_y) >= 0.0005
    )


def _arc_code_from_points(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    center_x: float,
    center_y: float,
    *,
    winding: str = "",
) -> str:
    cross = ((start_x - center_x) * (end_y - center_y)) - (
        (start_y - center_y) * (end_x - center_x)
    )
    if abs(cross) < 0.0005 and winding:
        return "G3" if winding == "CounterClockwise" else "G2"
    return "G3" if cross > 0 else "G2"


def _profile_corner_center(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    contour_points: object,
) -> tuple[float, float]:
    min_x = min(float(point[0]) for point in contour_points)
    max_x = max(float(point[0]) for point in contour_points)
    min_y = min(float(point[1]) for point in contour_points)
    max_y = max(float(point[1]) for point in contour_points)
    candidates = ((start_x, end_y), (end_x, start_y))
    for x, y in candidates:
        if min_x - 0.0005 <= x <= max_x + 0.0005 and min_y - 0.0005 <= y <= max_y + 0.0005:
            return x, y
    return candidates[0]


def _fmt(value: object) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.3f}"


def _last_emitted_xy(lines: list[ExplainedIsoLine]) -> Optional[tuple[float, float]]:
    for emitted in reversed(lines):
        x_value: Optional[float] = None
        y_value: Optional[float] = None
        for word in emitted.line.split():
            if word.startswith("X"):
                x_value = float(word[1:])
            elif word.startswith("Y"):
                y_value = float(word[1:])
        if x_value is not None and y_value is not None:
            return x_value, y_value
    return None


def _fmt_scaled(value: object) -> str:
    number = struct.unpack("f", struct.pack("f", float(value)))[0]
    return f"{number * 1000.0:.3f}"


def _normalize_iso_lines(text: str) -> tuple[str, ...]:
    lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        line = " ".join(line.split())
        if line == "%" or line.startswith("% "):
            line = "%"
        lines.append(line)
    return tuple(lines)
