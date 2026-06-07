"""Pure ISO line builders for boring-head preparation and reset blocks."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .model import IsoStateEvaluation, StageDifferential, TraceMove


PROGRAMACIONES_SETTINGSX_PATH = "iso_state_synthesis/machine_config/snapshot/maestro/Cfgx/Programaciones.settingsx"


class BoringHeadLineError(RuntimeError):
    """Raised when boring-head line builders cannot read required state."""


@dataclass(frozen=True)
class _SidePlaneSelectionLines:
    """Side face selection lines split by explanatory emission group."""

    frame: tuple[str, ...]
    selection: tuple[str, ...]

    def all_lines(self) -> tuple[str, ...]:
        return self.frame + self.selection


def _top_drill_prepare_after_router_base_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
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
    return tuple(prepare_lines)


def _tool_shift_lines(differential: StageDifferential) -> tuple[str, ...]:
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
    return (
        f"SHF[X]={_fmt(shf_x)}",
        f"SHF[Y]={_fmt(shf_y)}",
        f"SHF[Z]={_fmt(shf_z)}",
    )


def _boring_head_speed_lines(
    differential: StageDifferential,
    *,
    forced_etk17: Optional[int] = None,
) -> tuple[str, ...]:
    speed_activation = _find_change(differential.target_changes, "salida", "etk_17")
    if speed_activation is None and forced_etk17 is None:
        return ()
    etk17 = forced_etk17 if speed_activation is None else int(speed_activation.after)
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    return (f"?%ETK[17]={int(etk17)}", f"S{int(spindle_speed)}M3")


def _boring_head_mask_line(differential: StageDifferential) -> str:
    return _etk0_mask_line(differential)


def _side_sequence_pause_line() -> str:
    return "G4F0.500"


def _vertical_mask_line(differential: StageDifferential) -> str:
    return _etk0_mask_line(differential)


def _etk0_mask_line(differential: StageDifferential) -> str:
    mask = _change_after(differential, "salida", "etk_0_mask")
    return f"?%ETK[0]={int(mask)}"


def _top_drill_prepare_after_slot_base_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name
    return (
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
    )


def _top_drill_prepare_after_slot_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    return (
        _top_drill_prepare_after_slot_base_lines(evaluation, differential)
        + _tool_shift_lines(differential)
        + _boring_head_speed_lines(differential)
        + (_vertical_mask_line(differential),)
    )


def _top_drill_prepare_after_side_restore_lines(
    evaluation: IsoStateEvaluation,
    previous_side_prepare: StageDifferential,
) -> tuple[str, ...]:
    previous_plane = str(_change_after(previous_side_prepare, "trabajo", "plane"))
    if previous_plane not in {"Left", "Back"}:
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


def _top_drill_prepare_after_side_work_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    previous_side_prepare: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    tool_number = int(tool_name) if tool_name.isdigit() else tool_name
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={tool_number}",
        "MLV=0",
        f"G0 G53 Z{_fmt(_side_drill_g53_z(evaluation, previous_side_prepare))}",
        "MLV=2",
        "MLV=2",
    ) + _tool_shift_lines(differential)


def _top_drill_prepare_after_side_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    previous_side_prepare: StageDifferential,
) -> tuple[str, ...]:
    return (
        _top_drill_prepare_after_side_restore_lines(evaluation, previous_side_prepare)
        + ("?%ETK[8]=1", "G40")
        + _top_drill_prepare_after_side_work_lines(
            evaluation,
            differential,
            previous_side_prepare,
        )
        + _boring_head_speed_lines(differential)
        + (_vertical_mask_line(differential),)
    )


def _same_top_drill_tool(
    previous_prepare: Optional[StageDifferential],
    differential: StageDifferential,
) -> bool:
    return (
        previous_prepare is not None
        and _change_after(previous_prepare, "herramienta", "tool_name")
        == _change_after(differential, "herramienta", "tool_name")
    )


def _top_drill_tool_number(differential: StageDifferential) -> object:
    tool_name = str(_change_after(differential, "herramienta", "tool_name"))
    return int(tool_name) if tool_name.isdigit() else tool_name


def _top_drill_previous_approach_reposition_line(previous_trace: StageDifferential) -> str:
    previous_approach = _trace_move(previous_trace, "Approach").points[0]
    return (
        f"G0 X{_fmt(previous_approach.x)} "
        f"Y{_fmt(previous_approach.y)} "
        f"Z{_fmt(previous_approach.iso_z)}"
    )


def _top_drill_prepare_between_top_base_lines(
    evaluation: IsoStateEvaluation,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
    )


def _top_drill_prepare_between_tool_change_lines(
    differential: StageDifferential,
    previous_trace: StageDifferential,
) -> tuple[str, ...]:
    return (
        f"?%ETK[6]={_top_drill_tool_number(differential)}",
        _top_drill_previous_approach_reposition_line(previous_trace),
        "MLV=2",
    )


def _top_drill_prepare_between_top_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    previous_prepare: Optional[StageDifferential],
    previous_trace: StageDifferential,
) -> tuple[str, ...]:
    base_lines = _top_drill_prepare_between_top_base_lines(evaluation)
    if _same_top_drill_tool(previous_prepare, differential):
        return base_lines + (_top_drill_previous_approach_reposition_line(previous_trace),)
    return (
        base_lines
        + _top_drill_prepare_between_tool_change_lines(differential, previous_trace)
        + _tool_shift_lines(differential)
        + _boring_head_speed_lines(differential)
        + (_vertical_mask_line(differential),)
    )


def _top_drill_prepare_modal_lines() -> tuple[str, ...]:
    return ("MLV=2", "G17")


def _top_drill_prepare_origin_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    prep_origin_x = length + (2 * origin_x)
    return (
        f"?%ETK[6]={_top_drill_tool_number(differential)}",
        f"%Or[0].ofX={_fmt_scaled(-prep_origin_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
    )


def _top_drill_prepare_frame_lines(evaluation: IsoStateEvaluation) -> tuple[str, ...]:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    return (
        "MLV=1",
        f"SHF[X]={_fmt(-(length + origin_x))}",
        f"SHF[Y]={_fmt(-1515.6 + origin_y)}",
        f"SHF[Z]={_fmt(origin_z)}",
        "MLV=2",
        "MLV=2",
    )


def _top_drill_prepare_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    return (
        _top_drill_prepare_modal_lines()
        + _top_drill_prepare_origin_lines(evaluation, differential)
        + _top_drill_prepare_frame_lines(evaluation)
        + _tool_shift_lines(differential)
        + _boring_head_speed_lines(differential)
        + (_vertical_mask_line(differential),)
    )


def _slot_milling_prepare_after_top_lines(
    differential: StageDifferential,
    *,
    emit_mlv_after_g17: bool = False,
) -> tuple[str, ...]:
    spindle = _change_after(differential, "herramienta", "spindle")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    etk1 = _change_after(differential, "salida", "etk_1")
    etk17 = _optional_change_after(differential, "salida", "etk_17", None)
    prepare_lines = [
        f"?%ETK[6]={int(spindle)}",
        "G17",
    ]
    if emit_mlv_after_g17:
        prepare_lines.append("MLV=2")
    if etk17 is not None:
        prepare_lines.extend((f"?%ETK[17]={int(etk17)}", f"S{int(spindle_speed)}M3"))
    prepare_lines.extend((f"?%ETK[1]={int(etk1)}", "MLV=2"))
    prepare_lines.extend(_tool_shift_lines(differential))
    return tuple(prepare_lines)


def _slot_milling_prepare_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    origin_y = evaluation.initial_state.get("pieza", "origin_y")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    spindle = _change_after(differential, "herramienta", "spindle")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    etk1 = _change_after(differential, "salida", "etk_1")
    etk17 = _optional_change_after(differential, "salida", "etk_17", None)
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
    prepare_lines.extend((f"?%ETK[1]={int(etk1)}", "MLV=2"))
    prepare_lines.extend(_tool_shift_lines(differential))
    return tuple(prepare_lines)


def _slot_milling_reset_lines(
    *,
    final: bool = True,
    emit_etk7: bool = True,
) -> tuple[str, ...]:
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
    return tuple(reset_lines)


def _side_drill_prepare_between_base_lines(
    evaluation: IsoStateEvaluation,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
    )


def _side_plane_selection_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    plane: str,
    *,
    include_right_frame: bool = True,
    previous_plane: Optional[str] = None,
) -> _SidePlaneSelectionLines:
    frame_plane: Optional[str] = None
    if plane in {"Left", "Back"}:
        frame_plane = plane
    elif plane == "Right" and include_right_frame and (
        previous_plane is None or previous_plane in {"Back", "Left"}
    ):
        frame_plane = "Right"
    elif plane == "Front" and previous_plane in {"Back", "Left"}:
        frame_plane = "Right"

    frame_lines: tuple[str, ...] = ()
    if frame_plane is not None:
        side_x, side_y = _side_plane_frame_shift(evaluation, frame_plane)
        header_dz = evaluation.final_state.get("pieza", "header_dz")
        frame_lines = (
            "MLV=1",
            f"SHF[X]={_fmt(side_x)}",
            f"SHF[Y]={_fmt(side_y)}",
            f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        )

    side_etk8 = _change_after(differential, "trabajo", "side_etk8")
    return _SidePlaneSelectionLines(
        frame=frame_lines,
        selection=(f"?%ETK[8]={int(side_etk8)}", "G40"),
    )


def _side_drill_same_spindle_reposition_lines(
    differential: StageDifferential,
    previous_trace: Optional[StageDifferential],
    *,
    multi_side_sequence: bool = False,
    final_left_pause: bool = False,
) -> tuple[str, ...]:
    axis = str(_change_after(differential, "movimiento", "side_axis"))
    pause_required = multi_side_sequence or final_left_pause
    if axis == "X" and previous_trace is not None:
        previous_approach = _trace_move(previous_trace, "Approach").points[0]
        reposition_lines = [
            f"G0 X{_fmt(previous_approach.x)} "
            f"Y{_fmt(previous_approach.y)} "
            f"Z{_fmt(previous_approach.iso_z)}"
        ]
    else:
        reposition_lines = ["MLV=0", "G0 G53 Z201.000", "MLV=2"]
    if pause_required:
        reposition_lines.append("G4F0.500")
    return tuple(reposition_lines)


def _side_drill_spindle_change_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    previous_prepare: StageDifferential,
) -> tuple[str, ...]:
    spindle = _change_after(differential, "herramienta", "spindle")
    park_z = _side_drill_g53_z(evaluation, previous_prepare, differential)
    return (
        f"?%ETK[6]={int(spindle)}",
        "MLV=0",
        f"G0 G53 Z{_fmt(park_z)}",
        "MLV=2",
        "MLV=2",
    ) + _tool_shift_lines(differential)


def _side_drill_prepare_modal_lines() -> tuple[str, ...]:
    return ("MLV=2", "G17")


def _side_drill_prepare_origin_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    length = evaluation.initial_state.get("pieza", "length")
    origin_x = evaluation.initial_state.get("pieza", "origin_x")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    spindle = _change_after(differential, "herramienta", "spindle")
    prep_origin_x = length + (2 * origin_x)
    return (
        f"?%ETK[6]={int(spindle)}",
        f"%Or[0].ofX={_fmt_scaled(-prep_origin_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_fmt_scaled(header_dz)}",
    )


def _side_drill_prepare_frame_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    plane = str(_change_after(differential, "trabajo", "plane"))
    frame_x, frame_y = _side_plane_frame_shift(evaluation, plane)
    return (
        "MLV=1",
        f"SHF[X]={_fmt(frame_x)}",
        f"SHF[Y]={_fmt(frame_y)}",
        f"SHF[Z]={_fmt(origin_z)}",
        "MLV=2",
        "MLV=2",
    )


def _side_drill_prepare_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    multi_side_sequence: bool = False,
) -> tuple[str, ...]:
    prepare_lines = (
        _side_drill_prepare_modal_lines()
        + _side_drill_prepare_origin_lines(evaluation, differential)
        + _side_drill_prepare_frame_lines(evaluation, differential)
        + _tool_shift_lines(differential)
        + _boring_head_speed_lines(differential)
        + (_etk0_mask_line(differential),)
    )
    if multi_side_sequence:
        prepare_lines += ("G4F0.500",)
    return prepare_lines


def _side_drill_prepare_after_router_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    spindle = _change_after(differential, "herramienta", "spindle")
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={int(spindle)}",
        "MLV=2",
    ) + _tool_shift_lines(differential)


def _side_drill_prepare_after_slot_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    spindle = _change_after(differential, "herramienta", "spindle")
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={int(spindle)}",
        "MLV=2",
    ) + _tool_shift_lines(differential)


def _side_drill_prepare_after_top_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> tuple[str, ...]:
    origin_z = evaluation.initial_state.get("pieza", "origin_z")
    spindle = _change_after(differential, "herramienta", "spindle")
    return (
        "MLV=1",
        f"SHF[Z]={_fmt(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={int(spindle)}",
        "MLV=0",
        f"G0 G53 Z{_fmt(_side_drill_g53_z(evaluation, differential))}",
        "MLV=2",
        "MLV=2",
    ) + _tool_shift_lines(differential)


def _top_drill_reset_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    final: bool = True,
) -> tuple[str, ...]:
    return _boring_drill_reset_lines(evaluation, differential, final=final)


def _side_drill_reset_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    final: bool = True,
) -> tuple[str, ...]:
    return _boring_drill_reset_lines(evaluation, differential, final=final)


def _boring_drill_reset_lines(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
    *,
    final: bool = True,
) -> tuple[str, ...]:
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    reset_lines = [
        "MLV=1",
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
    if final:
        etk17 = _reset_after(differential, "salida", "etk_17")
        reset_lines.extend(
            (
                "G61",
                "MLV=0",
                "?%ETK[0]=0",
                f"?%ETK[17]={int(etk17)}",
                "G4F1.200",
                "M5",
                "D0",
            )
        )
    return tuple(reset_lines)


def _change_after(differential: StageDifferential, layer: str, key: str) -> object:
    change = _find_change(differential.target_changes, layer, key)
    if change is None:
        change = _find_change(differential.forced_values, layer, key)
    if change is None:
        raise BoringHeadLineError(f"La etapa {differential.stage_key} no contiene {layer}.{key}.")
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
        raise BoringHeadLineError(f"La etapa {differential.stage_key} no resetea {layer}.{key}.")
    return change.after


def _find_change(changes: tuple[object, ...], layer: str, key: str) -> Optional[object]:
    for change in changes:
        if change.layer == layer and change.key == key:
            return change
    return None


def _trace_move(differential: StageDifferential, name: str) -> TraceMove:
    for move in differential.trace:
        if move.name == name:
            return move
    raise BoringHeadLineError(f"La etapa {differential.stage_key} no contiene traza {name}.")


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


def _side_drill_g53_z(
    evaluation: IsoStateEvaluation,
    *side_prepares: StageDifferential,
) -> float:
    shf_z_values = [
        float(_change_after(prepare, "herramienta", "shf_z"))
        for prepare in side_prepares
    ]
    if not shf_z_values:
        raise BoringHeadLineError("No hay SHF_Z lateral para calcular G53 Z.")
    header_dz = float(evaluation.final_state.get("pieza", "header_dz"))
    return header_dz + (2.0 * _maestro_security_distance()) + max(shf_z_values)


@lru_cache(maxsize=1)
def _maestro_security_distance() -> float:
    path = _resolve_project_path(PROGRAMACIONES_SETTINGSX_PATH)
    if not path.exists():
        raise BoringHeadLineError(f"No existe la configuracion Maestro: {PROGRAMACIONES_SETTINGSX_PATH}.")
    for text in _settingsx_texts(path):
        value = _xml_app_setting(text, "SecurityDistance")
        if value is not None:
            return float(value)
    raise BoringHeadLineError(f"No se encontro SecurityDistance en {PROGRAMACIONES_SETTINGSX_PATH}.")


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


def _base_shf_y(origin_y: object = 0.0) -> float:
    return -1515.6 + float(origin_y)


def _fmt(value: object, digits: int = 3) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.{digits}f}"


def _fmt_scaled(value: object) -> str:
    return _fmt(float(value) * 1000.0)
