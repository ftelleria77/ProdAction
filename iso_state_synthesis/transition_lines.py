"""ISO line builders for transitions between work families."""

from __future__ import annotations

from typing import Optional

from .errors import IsoCandidateEmissionError
from .model import IsoStateEvaluation, StageDifferential, StateChange


def _router_inter_work_reset_lines(next_prepare: StageDifferential) -> tuple[str, ...]:
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
    return tuple(reset_lines)


def _router_to_boring_transition_lines(*, include_face_selection: bool = False) -> tuple[str, ...]:
    transition_lines: list[str] = []
    if include_face_selection:
        transition_lines.extend(("?%ETK[8]=1", "G40"))
    transition_lines.extend(
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
        )
    )
    return tuple(transition_lines)


def _boring_to_router_side_restore_lines(
    evaluation: IsoStateEvaluation,
    previous_prepare: StageDifferential,
) -> tuple[str, ...]:
    previous_plane = str(_optional_change_after(previous_prepare, "trabajo", "plane", ""))
    if previous_plane not in {"Back", "Left"}:
        return ()
    side_x, side_y = _side_plane_frame_shift(evaluation, "Right")
    header_dz = evaluation.final_state.get("pieza", "header_dz")
    return (
        "MLV=1",
        f"SHF[X]={_fmt(side_x)}",
        f"SHF[Y]={_fmt(side_y)}",
        f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
        "?%ETK[7]=0",
    )


def _boring_to_router_top_face_lines(previous_family: str) -> tuple[str, ...]:
    if previous_family != "side_drill":
        return ()
    return ("?%ETK[8]=1", "G40")


def _boring_to_router_cleanup_lines(
    previous_family: str,
    router_prepare: StageDifferential,
    router_trace: StageDifferential,
    *,
    include_face_selection: bool = False,
) -> tuple[str, ...]:
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
    return tuple(cleanup_lines)


def _top_to_slot_milling_transition_lines() -> tuple[str, ...]:
    return (
        "?%ETK[8]=1",
        "G40",
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "?%ETK[0]=0",
    )


def _side_to_slot_milling_transition_lines(
    evaluation: IsoStateEvaluation,
    side_prepare: StageDifferential,
) -> tuple[str, ...]:
    transition_lines: list[str] = []
    previous_plane = str(_change_after(side_prepare, "trabajo", "plane"))
    if previous_plane in {"Back", "Left"}:
        side_x, side_y = _side_plane_frame_shift(evaluation, "Right")
        header_dz = evaluation.final_state.get("pieza", "header_dz")
        transition_lines.extend(
            (
                "MLV=1",
                f"SHF[X]={_fmt(side_x)}",
                f"SHF[Y]={_fmt(side_y)}",
                f"SHF[Z]={_fmt(header_dz)}+%ETK[114]/1000",
            )
        )
    transition_lines.extend(_top_to_slot_milling_transition_lines())
    return tuple(transition_lines)


def _slot_to_slot_milling_transition_lines() -> tuple[str, ...]:
    return ("?%ETK[8]=1", "G40", "G17")


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


def _fmt(value: object) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.3f}"
