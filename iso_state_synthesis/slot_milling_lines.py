"""SlotSide ISO trace line builders."""

from __future__ import annotations

from typing import Optional

from .errors import IsoCandidateEmissionError
from .model import StageDifferential, StateChange


def _slot_milling_trace_lines(
    differential: StageDifferential,
    *,
    previous_slot_trace: Optional[StageDifferential] = None,
    previous_slot_exit_emitted: bool = True,
    emit_transition_lift: bool = False,
    emit_transition_exit: bool = False,
    emit_etk7_before_lift: bool = False,
) -> tuple[str, ...]:
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
    motion_lines: list[str] = []
    if previous_slot_trace is not None:
        previous_rapid_x = _change_after(
            previous_slot_trace,
            "movimiento",
            "rapid_x" if previous_slot_exit_emitted else "cut_x",
        )
        previous_rapid_y = _change_after(previous_slot_trace, "movimiento", "rapid_y")
        motion_lines.extend(
            (
                f"G0 X{_fmt(previous_rapid_x)} Y{_fmt(previous_rapid_y)} Z{_fmt(rapid_z)}",
                f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)} Z{_fmt(rapid_z)}",
            )
        )
    else:
        motion_lines.extend(
            (
                f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)}",
                f"G0 Z{_fmt(rapid_z)}",
            )
        )
    motion_lines.extend(
        (
            "D1",
            f"SVL {_fmt(tool_offset)}",
            f"VL6={_fmt(tool_offset)}",
            f"SVR {_fmt(tool_radius)}",
            f"VL7={_fmt(tool_radius)}",
            f"G1 Z{_fmt(cut_z)} F{_fmt(plunge_feed)}",
            "?%ETK[7]=1",
            _slot_milling_motion_line(
                float(cut_x),
                float(rapid_y),
                float(cut_z),
                float(rapid_x),
                float(rapid_y),
                float(cut_z),
                float(milling_feed),
            ),
        )
    )
    if emit_transition_lift:
        motion_lines.append(f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}")
    if emit_transition_exit:
        clearance_x = float(rapid_x) - 0.75
        motion_lines.extend(
            [
                f"G1 X{_fmt(clearance_x)} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 X{_fmt(rapid_x)} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 Z{_fmt(security_z)} F{_fmt(milling_feed)}",
                f"G1 Z{_fmt(cut_z)} F{_fmt(milling_feed)}",
            ]
        )
    if emit_etk7_before_lift:
        motion_lines.append("?%ETK[7]=0")
    motion_lines.append(f"G0 Z{_fmt(security_z)}")
    return tuple(motion_lines)


def _slot_milling_motion_line(
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


def _change_after(differential: StageDifferential, layer: str, key: str) -> object:
    change = _find_change(differential.target_changes, layer, key)
    if change is None:
        change = _find_change(differential.forced_values, layer, key)
    if change is None:
        raise IsoCandidateEmissionError(
            f"La etapa {differential.stage_key} no contiene {layer}.{key}."
        )
    return change.after


def _find_change(
    changes: tuple[StateChange, ...],
    layer: str,
    key: str,
) -> Optional[StateChange]:
    for change in changes:
        if change.layer == layer and change.key == key:
            return change
    return None


def _fmt(value: object) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.3f}"
