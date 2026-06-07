"""Program-level ISO line builders."""

from __future__ import annotations

import struct
from typing import Optional

from .errors import IsoCandidateEmissionError
from .model import IsoStateEvaluation, StageDifferential, StateChange
from .work_groups import _COMMON_STAGE_KEYS


def _program_header_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    program_name: str,
) -> tuple[str, str]:
    dx = _change_after(differential, "pieza", "header_dx")
    dy = _change_after(differential, "pieza", "header_dy")
    dz = _change_after(differential, "pieza", "header_dz")
    area = evaluation.initial_state.get("pieza", "execution_fields", "HG")
    return (
        f"% {program_name}.pgm",
        (
            f";H DX={_fmt(dx)} DY={_fmt(dy)} DZ={_fmt(dz)} "
            f"BX=0.000 BY=0.000 BZ=0.000 -{area} V=0 *MM C=0 T=0"
        ),
    )


def _machine_preamble_template_lines() -> tuple[str, ...]:
    return (
        "?%ETK[500]=100",
        "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )",
        "G0 G53 Z %ax[2].pa[22]/1000",
        "M58",
    )


def _machine_metric_mode_line() -> str:
    return "G71"


def _piece_frame_base_lines(evaluation: IsoStateEvaluation) -> tuple[str, ...]:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    frame_x = length + origin_x
    return (
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
    )


def _piece_frame_tool_reentry_lines(evaluation: IsoStateEvaluation) -> tuple[str, str]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
    )


def _piece_frame_lines(
    evaluation: IsoStateEvaluation,
    work_plane: str,
    work_family: str,
    router_milling_families: set[str],
) -> tuple[str, ...]:
    lines = list(_piece_frame_base_lines(evaluation))
    lines.extend(_face_selection_lines(evaluation, work_plane))
    if work_family not in router_milling_families and work_family != "slot_milling":
        lines.extend(_piece_frame_tool_reentry_lines(evaluation))
    return tuple(lines)


def _empty_piece_frame_lines(
    differential: StageDifferential,
    *,
    face_pair_count: int,
) -> tuple[str, ...]:
    frame_x = _change_after(differential, "pieza", "header_dx")
    header_dz = _change_after(differential, "pieza", "header_dz")
    lines = [
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
    ]
    for _ in range(face_pair_count):
        lines.extend(("?%ETK[8]=1", "G40"))
    return tuple(lines)


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


def _router_program_close_lines(differential: StageDifferential) -> tuple[str, ...]:
    return (
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        "M5",
        "D0",
        "G0 G53 Z201.000",
        _program_close_xy_line(differential),
        "G64",
    )


def _program_close_xy_line(differential: StageDifferential) -> str:
    close_x = _optional_change_after(differential, "movimiento", "program_close_x", -3700.0)
    close_y = _optional_change_after(differential, "movimiento", "program_close_y", None)
    line = f"G0 G53 X{_fmt(close_x)}"
    if close_y is not None:
        line += f" Y{_fmt(close_y)}"
    return line


def _is_mixed_side_close(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    plane: str,
) -> bool:
    close_x = _optional_change_after(differential, "movimiento", "program_close_x", -3700.0)
    close_y = _optional_change_after(differential, "movimiento", "program_close_y", None)
    return (
        plane == "Right"
        and _has_non_side_work(evaluation)
        and float(close_x) != -3700.0
        and close_y is None
    )


def _side_program_close_prefix_lines(plane: str) -> tuple[str, ...]:
    return (
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
    )


def _lateral_program_close_frame_lines(
    evaluation: IsoStateEvaluation,
    plane: str,
) -> tuple[str, ...]:
    if plane not in {"Left", "Back"}:
        return ()
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    return (
        "MLV=1",
        f"SHF[X]={_fmt(-(length + origin_x))}",
        f"SHF[Y]={_fmt(_base_shf_y(origin_y))}",
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
    )


def _lateral_program_close_reset_lines(plane: str) -> tuple[str, ...]:
    lines = ["G61"]
    if plane in {"Left", "Back"}:
        lines.append("MLV=0")
    lines.extend(("D0", "G0 G53 Z201.000", "G64"))
    return tuple(lines)


def _common_program_close_tail_lines() -> tuple[str, ...]:
    return (
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
    )


def _empty_program_explicit_close_lines(differential: StageDifferential) -> tuple[str, ...]:
    close_x = _optional_change_after(differential, "movimiento", "program_close_x", -3700.0)
    return (
        "G61",
        "MLV=0",
        "D0",
        "G0 G53 Z201.000",
        f"G0 G53 X{_fmt(close_x)}",
        "G64",
    )


def _empty_program_close_tail_lines() -> tuple[str, ...]:
    return _common_program_close_tail_lines()


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


def _side_etk8_for_plane(plane_name: str) -> int:
    return {
        "Left": 3,
        "Right": 2,
        "Front": 5,
        "Back": 4,
    }.get(plane_name, 1)


def _base_shf_y(origin_y: object = 0.0) -> float:
    return -1515.6 + float(origin_y)


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


def _find_change(
    changes: tuple[StateChange, ...],
    layer: str,
    key: str,
) -> Optional[StateChange]:
    for change in changes:
        if change.layer == layer and change.key == key:
            return change
    return None


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


def _fmt(value: object) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.3f}"


def _fmt_scaled(value: object) -> str:
    number = struct.unpack("f", struct.pack("f", float(value)))[0]
    return f"{number * 1000.0:.3f}"
