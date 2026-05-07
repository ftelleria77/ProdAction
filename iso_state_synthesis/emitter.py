"""Explanatory ISO candidate emitter for state differentials."""

from __future__ import annotations

import difflib
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
    differentials = {
        differential.stage_key: differential
        for differential in evaluation.differentials
    }
    common_required = {"program_header", "machine_preamble", "program_close"}
    has_top_drill = {
        "top_drill_prepare",
        "top_drill_trace",
        "top_drill_reset",
    }.issubset(differentials)
    has_side_drill = {
        "side_drill_prepare",
        "side_drill_trace",
        "side_drill_reset",
    }.issubset(differentials)
    has_line_milling = {
        "line_milling_prepare",
        "line_milling_trace",
        "line_milling_reset",
    }.issubset(differentials)
    active_families = [
        name
        for name, enabled in (
            ("Top Drill", has_top_drill),
            ("Side Drill", has_side_drill),
            ("Line Milling", has_line_milling),
        )
        if enabled
    ]
    if len(active_families) > 1:
        raise IsoCandidateEmissionError(
            "El emisor candidato inicial no mezcla todavia familias de trabajo: "
            f"{', '.join(active_families)}."
        )
    if not active_families:
        raise IsoCandidateEmissionError(
            "El emisor candidato inicial solo soporta planes minimos Top Drill, "
            "Side Drill y Line Milling."
        )
    required = set(common_required)
    if has_line_milling:
        required.update({"line_milling_prepare", "line_milling_trace", "line_milling_reset"})
    elif has_side_drill:
        required.update({"side_drill_prepare", "side_drill_trace", "side_drill_reset"})
    else:
        required.update({"top_drill_prepare", "top_drill_trace", "top_drill_reset"})
    missing = sorted(required.difference(differentials))
    if missing:
        raise IsoCandidateEmissionError(
            "El emisor candidato inicial solo soporta planes Drill minimos; "
            f"faltan etapas: {', '.join(missing)}"
        )

    lines: list[ExplainedIsoLine] = []
    _emit_program_header(lines, evaluation, differentials["program_header"], resolved_program_name)
    _emit_machine_preamble(lines, differentials["machine_preamble"])
    work_plane = _work_plane(evaluation)
    work_family = _work_family(evaluation)
    _emit_piece_frame(lines, evaluation, differentials["program_header"], work_plane, work_family)
    if has_line_milling:
        _emit_line_milling_prepare(lines, evaluation, differentials["line_milling_prepare"])
        _emit_line_milling_trace(lines, evaluation, differentials["line_milling_trace"])
        _emit_line_milling_reset(lines, differentials["line_milling_reset"])
    elif has_side_drill:
        _emit_side_drill_prepare(lines, evaluation, differentials["side_drill_prepare"])
        _emit_side_drill_trace(lines, differentials["side_drill_trace"])
        _emit_side_drill_reset(lines, evaluation, differentials["side_drill_reset"])
    else:
        _emit_top_drill_prepare(lines, evaluation, differentials["top_drill_prepare"])
        _emit_top_drill_trace(lines, differentials["top_drill_trace"])
        _emit_top_drill_reset(lines, evaluation, differentials["top_drill_reset"])
    _emit_program_close(lines, differentials["program_close"], evaluation)
    return ExplainedIsoProgram(
        source_path=evaluation.source_path,
        program_name=resolved_program_name,
        lines=tuple(lines),
        warnings=evaluation.warnings,
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
    if work_family == "line_milling":
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
) -> None:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    source = _change_source(differential, "herramienta", "tool_offset_length")
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name
    prep_origin_x = length + (2 * origin_x)
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
        "?%ETK[0]=16",
        differential,
        _observed_rule_source("top_drill_prepare"),
        "Registro modal observado en preparacion; falta clasificar significado.",
        confidence="hypothesis",
        rule_status="top_drill_modal_hypothesis",
    )


def _emit_top_drill_trace(
    lines: list[ExplainedIsoLine],
    differential: StageDifferential,
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
    for line in (f"G0 X{_fmt(rapid_xy.x)} Y{_fmt(rapid_xy.y)}", f"G0 Z{_fmt(rapid_z)}"):
        _append(
            lines,
            line,
            differential,
            source,
            "Traza Top Drill calculada desde toolpaths locales y ToolOffsetLength.",
            confidence="confirmed",
            rule_status="generalized_top_drill_001_006",
        )
    for line in ("?%ETK[7]=3", "MLV=2"):
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


def _emit_line_milling_prepare(
    lines: list[ExplainedIsoLine],
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
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
    for line in (
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
    trajectory = _trace_move(differential, "TrajectoryPath")
    source = _change_source(differential, "movimiento", "cut_z")

    for line in (
        f"G0 X{_fmt(start_x)} Y{_fmt(start_y)}",
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

    if len(trajectory.points) <= 2:
        first_cut = f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}"
        motion = _line_milling_motion_line(
            float(end_x),
            float(end_y),
            float(cut_z),
            float(start_x),
            float(start_y),
            float(cut_z),
            float(milling_feed),
        )
        motion_lines = (first_cut, "?%ETK[7]=4", motion, f"G0 Z{_fmt(security_z)}")
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
            "Reset posterior de taladro superior observado.",
            rule_status="top_drill_reset_observed",
        )
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
    if family == "line_milling":
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
    if family != "line_milling" and plane != "Top":
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
) -> str:
    words = ["G1"]
    if abs(x - previous_x) >= 0.0005:
        words.append(f"X{_fmt(x)}")
    if abs(y - previous_y) >= 0.0005:
        words.append(f"Y{_fmt(y)}")
    words.append(f"Z{_fmt(z)}")
    words.append(f"F{_fmt(feed)}")
    return " ".join(words)


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
