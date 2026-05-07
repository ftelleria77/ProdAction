"""Explanatory ISO candidate emitter for state differentials."""

from __future__ import annotations

import difflib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
    "line_milling": ("line_milling_prepare", "line_milling_trace", "line_milling_reset"),
    "profile_milling": ("profile_milling_prepare", "profile_milling_trace", "profile_milling_reset"),
}
_ROUTER_MILLING_FAMILIES = {"line_milling", "profile_milling"}


@dataclass(frozen=True)
class ExplainedIsoLine:
    """One ISO candidate line with its explanation source."""

    line: str
    stage_key: str
    source: EvidenceSource
    confidence: str = "observed"
    rule_status: str = "observed"
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

    missing = sorted(_COMMON_STAGE_KEYS.difference(differentials))
    if missing:
        raise IsoCandidateEmissionError(
            "El emisor candidato inicial requiere cabecera, preambulo y cierre; "
            f"faltan etapas: {', '.join(missing)}"
        )

    work_differentials = [
        differential
        for differential in ordered_differentials
        if differential.stage_key not in _COMMON_STAGE_KEYS
    ]
    work_groups = _work_stage_groups(ordered_differentials)
    if not work_groups or len(work_differentials) != len(work_groups) * 3:
        raise IsoCandidateEmissionError(
            "El emisor candidato inicial solo soporta secuencias completas "
            "Top Drill, Side Drill, Line Milling y Profile Milling E001."
        )

    if all(group[0] == "top_drill" for group in work_groups):
        return _emit_top_drill_sequence_candidate(
            evaluation,
            resolved_program_name,
            differentials,
            tuple((group[1], group[2], group[3]) for group in work_groups),
        )
    return _emit_work_sequence_candidate(
        evaluation,
        resolved_program_name,
        differentials,
        work_groups,
    )


def _work_stage_groups(
    ordered_differentials: list[StageDifferential],
) -> tuple[tuple[str, StageDifferential, StageDifferential, StageDifferential], ...]:
    work = [
        differential
        for differential in ordered_differentials
        if differential.stage_key not in _COMMON_STAGE_KEYS
    ]
    if not work or len(work) % 3:
        return ()

    groups: list[tuple[str, StageDifferential, StageDifferential, StageDifferential]] = []
    for index in range(0, len(work), 3):
        stage_group = work[index : index + 3]
        stage_keys = tuple(differential.stage_key for differential in stage_group)
        for family, expected_keys in _WORK_STAGE_KEYS.items():
            if stage_keys == expected_keys:
                prepare, trace, reset = stage_group
                groups.append((family, prepare, trace, reset))
                break
        else:
            return ()
    return tuple(groups)


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


def _emit_work_sequence_candidate(
    evaluation: IsoStateEvaluation,
    program_name: str,
    differentials: dict[str, StageDifferential],
    groups: tuple[tuple[str, StageDifferential, StageDifferential, StageDifferential], ...],
) -> ExplainedIsoProgram:
    lines: list[ExplainedIsoLine] = []
    _emit_program_header(lines, evaluation, differentials["program_header"], program_name)
    _emit_machine_preamble(lines, differentials["machine_preamble"])
    first_family = groups[0][0]
    _emit_piece_frame(
        lines,
        evaluation,
        differentials["program_header"],
        _work_plane(evaluation),
        first_family,
    )

    previous_family: Optional[str] = None
    for index, (family, prepare, trace, reset) in enumerate(groups):
        _emit_work_group(lines, evaluation, family, prepare, trace, reset, previous_family=previous_family)
        if index < len(groups) - 1:
            next_family, next_prepare = groups[index + 1][0], groups[index + 1][1]
            if family in _ROUTER_MILLING_FAMILIES and next_family in _ROUTER_MILLING_FAMILIES:
                _emit_router_inter_work_reset(lines, reset, next_prepare)
        previous_family = family

    _emit_program_close(lines, differentials["program_close"], evaluation)
    return ExplainedIsoProgram(
        source_path=evaluation.source_path,
        program_name=program_name,
        lines=tuple(lines),
        warnings=evaluation.warnings,
    )


def _emit_work_group(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    family: str,
    prepare: StageDifferential,
    trace: StageDifferential,
    reset: StageDifferential,
    *,
    previous_family: Optional[str] = None,
) -> None:
    if family == "top_drill":
        _emit_top_drill_prepare(lines, evaluation, prepare)
        _emit_top_drill_trace(lines, trace)
        _emit_top_drill_reset(lines, evaluation, reset)
        return
    if family == "side_drill":
        _emit_side_drill_prepare(lines, evaluation, prepare)
        _emit_side_drill_trace(lines, trace)
        _emit_side_drill_reset(lines, evaluation, reset)
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
    if work_family in _ROUTER_MILLING_FAMILIES:
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


def _emit_top_drill_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    previous_prepare: Optional[StageDifferential] = None,
    previous_trace: Optional[StageDifferential] = None,
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
                arc_i,
                arc_j,
                milling_feed,
                z=security_z,
            ),
        )
    else:
        exit_lines = (
            _profile_milling_arc_line(arc_code, exit_x, exit_y, arc_i, arc_j, milling_feed),
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


def _emit_line_milling_trace(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
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
    tool_offset = evaluation.final_state.get("herramienta", "tool_offset_length")
    approach = _trace_move(differential, "Approach")
    trajectory = _trace_move(differential, "TrajectoryPath")
    lift = _trace_move(differential, "Lift")
    source = _change_source(differential, "movimiento", "cut_z")
    side_of_feature = str(evaluation.final_state.get("trabajo", "side_of_feature", "Center"))
    overcut_length = float(evaluation.final_state.get("trabajo", "overcut_length", 0.0) or 0.0)
    strategy_name = str(evaluation.final_state.get("trabajo", "strategy", ""))
    profile_family = str(_optional_change_after(differential, "movimiento", "profile_family", "Line"))
    profile_winding = str(_optional_change_after(differential, "movimiento", "profile_winding", ""))
    circle_center_x = _optional_change_after(differential, "movimiento", "circle_center_x", None)
    circle_center_y = _optional_change_after(differential, "movimiento", "circle_center_y", None)
    contour_points = _change_after(differential, "movimiento", "contour_points")
    nominal_points = tuple((float(point[0]), float(point[1])) for point in contour_points)
    approach_type = str(evaluation.final_state.get("trabajo", "approach_type", "Line"))
    approach_radius_multiplier = float(
        evaluation.final_state.get("trabajo", "approach_radius_multiplier", 2.0) or 2.0
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
    if uses_no_lead_side_compensation:
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

    for line in (
        f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)}",
        f"G0 Z{_fmt(rapid_z)}",
        "D1",
        f"SVL {_fmt(tool_offset)}",
        f"VL6={_fmt(tool_offset)}",
        f"SVR {_fmt(tool_radius)}",
        f"VL7={_fmt(tool_radius)}",
    ):
        _append(
            lines,
            line,
            differential,
            source,
            "Entrada E004 calculada desde toolpath y herramienta embebida.",
            confidence="confirmed",
            rule_status="generalized_line_milling_020_023",
        )

    if strategy_name and has_lead_paths:
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
            _line_milling_motion_line(
                entry_point[0],
                entry_point[1],
                float(security_z),
                float(rapid_x),
                float(rapid_y),
                float(security_z),
                float(plunge_feed),
            ),
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
                    always_include_z=False,
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
                _line_milling_motion_line(
                    exit_rapid[0],
                    exit_rapid[1],
                    float(security_z),
                    exit_point[0],
                    exit_point[1],
                    float(security_z),
                    float(milling_feed),
                ),
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
        include_cut_z = profile_family.startswith("Line") or float(cut_z) > -float(
            evaluation.initial_state.get("pieza", "depth")
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
            generated.append(
                _profile_toolpath_motion_line(
                    point,
                    current_x,
                    current_y,
                    current_z,
                    float(milling_feed),
                    center=center,
                    winding=profile_winding,
                    always_include_z=profile_family.startswith("Line"),
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


def _emit_side_drill_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> None:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    plane = str(_change_after(differential, "trabajo", "plane"))
    spindle = _change_after(differential, "herramienta", "spindle")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    mask = _change_after(differential, "salida", "etk_0_mask")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    frame_x, frame_y = _side_plane_frame_shift(evaluation, plane)
    source = _change_source(differential, "herramienta", "tool_offset_length")
    prep_origin_x = length + (2 * origin_x)
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


def _emit_side_drill_trace(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
) -> None:
    axis = str(_change_after(differential, "movimiento", "side_axis"))
    rapid = _change_after(differential, "movimiento", "side_rapid")
    cut = _change_after(differential, "movimiento", "side_cut")
    fixed = _change_after(differential, "movimiento", "side_fixed")
    z = _change_after(differential, "movimiento", "side_z")
    feed = _change_after(differential, "movimiento", "side_feed")
    source = _change_source(differential, "movimiento", "side_iso_rule")
    if axis == "X":
        rapid_line = f"G0 X{_fmt(rapid)} Y{_fmt(fixed)}"
        cut_line = f"G1 G9 X{_fmt(cut)} F{_fmt(feed)}"
        retract_line = f"G0 X{_fmt(rapid)} Z{_fmt(z)}"
    else:
        rapid_line = f"G0 X{_fmt(fixed)} Y{_fmt(rapid)}"
        cut_line = f"G1 G9 Y{_fmt(cut)} F{_fmt(feed)}"
        retract_line = f"G0 Y{_fmt(rapid)} Z{_fmt(z)}"
    for line in (rapid_line, f"G0 Z{_fmt(z)}"):
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Side Drill calculada desde punto PGMX y spindle lateral.",
            confidence="confirmed",
            rule_status="generalized_side_drill_010_013",
        )
    for line in ("?%ETK[7]=3", "MLV=2"):
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
) -> None:
    source = _observed_rule_source("program_close")
    plane = _work_plane(evaluation)
    family = _work_family(evaluation)
    if family in _ROUTER_MILLING_FAMILIES:
        for line in (
            "G61",
            "MLV=0",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            "M5",
            "D0",
            "G0 G53 Z201.000",
            "G0 G53 X-3700.000",
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
        for line in ("G0 G53 Z201.000", "G0 G53 X-3700.000"):
            _append(lines, line, differential, source, "Cierre comun observado.", rule_status="machine_close_observed")
        _append(lines, "G64", differential, source, "Cierre comun observado.", rule_status="machine_close_observed")
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


def _append(
    lines: list[ExplainedIsoLine],
    line: str,
    differential: StageDifferential,
    source: EvidenceSource,
    note: str,
    *,
    confidence: str = "observed",
    rule_status: str = "observed",
) -> None:
    lines.append(
        ExplainedIsoLine(
            line=line,
            stage_key=differential.stage_key,
            source=source,
            confidence=confidence,
            rule_status=rule_status,
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


def _fmt_scaled(value: object) -> str:
    return f"{float(value) * 1000.0:.3f}"


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
