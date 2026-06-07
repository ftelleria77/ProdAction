"""Boring-head ISO trace line builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import IsoCandidateEmissionError
from .model import StageDifferential, StateChange, TraceMove


@dataclass(frozen=True)
class _BoringTraceLines:
    """Trace lines split by evidence source group."""

    rapid: tuple[str, ...]
    modal: tuple[str, ...]
    cutting: tuple[str, ...]

    def all_lines(self) -> tuple[str, ...]:
        return self.rapid + self.modal + self.cutting


def _top_drill_trace_lines(
    differential: StageDifferential,
    *,
    emit_mlv_after_etk7: bool = True,
    combine_rapid_z: bool = False,
) -> _BoringTraceLines:
    approach = _trace_move(differential, "Approach")
    trajectory = _trace_move(differential, "TrajectoryPath")
    lift = _trace_move(differential, "Lift")
    rapid_xy = approach.points[0]
    rapid_z = approach.points[0].iso_z
    cut_z = trajectory.points[-1].iso_z
    lift_z = lift.points[-1].iso_z
    feed = trajectory.feed
    if combine_rapid_z:
        rapid_lines = (f"G0 X{_fmt(rapid_xy.x)} Y{_fmt(rapid_xy.y)} Z{_fmt(rapid_z)}",)
    else:
        rapid_lines = (
            f"G0 X{_fmt(rapid_xy.x)} Y{_fmt(rapid_xy.y)}",
            f"G0 Z{_fmt(rapid_z)}",
        )
    modal_lines = ["?%ETK[7]=3"]
    if emit_mlv_after_etk7:
        modal_lines.append("MLV=2")
    return _BoringTraceLines(
        rapid=rapid_lines,
        modal=tuple(modal_lines),
        cutting=(
            f"G1 G9 Z{_fmt(cut_z)} F{_fmt(feed)}",
            f"G0 Z{_fmt(lift_z)}",
        ),
    )


def _side_drill_trace_lines(
    differential: StageDifferential,
    *,
    fixed_override: Optional[float] = None,
    emit_mlv_after_etk7: bool = True,
    combine_rapid_z: bool = False,
) -> _BoringTraceLines:
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
    if axis == "X":
        rapid_line = f"G0 X{_fmt(rapid)} Y{_fmt(fixed)}"
        rapid_z_line = (
            f"G0 X{_fmt(rapid)} Y{_fmt(fixed)} Z{_fmt(z)}"
            if combine_rapid_z
            else f"G0 Z{_fmt(z)}"
        )
        cut_line = f"G1 G9 X{_fmt(cut)} F{_fmt(feed)}"
        retract_line = f"G0 X{_fmt(rapid)} Z{_fmt(z)}"
    else:
        rapid_line = f"G0 X{_fmt(fixed)} Y{_fmt(rapid)}"
        rapid_z_line = (
            f"G0 X{_fmt(fixed)} Y{_fmt(rapid)} Z{_fmt(z)}"
            if combine_rapid_z
            else f"G0 Z{_fmt(z)}"
        )
        cut_line = f"G1 G9 Y{_fmt(cut)} F{_fmt(feed)}"
        retract_line = f"G0 Y{_fmt(rapid)} Z{_fmt(z)}"
    modal_lines = ("?%ETK[7]=3", "MLV=2") if emit_mlv_after_etk7 else ("?%ETK[7]=3",)
    return _BoringTraceLines(
        rapid=(rapid_z_line,) if combine_rapid_z else (rapid_line, rapid_z_line),
        modal=modal_lines,
        cutting=(cut_line, retract_line),
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


def _find_change(
    changes: tuple[StateChange, ...],
    layer: str,
    key: str,
) -> Optional[StateChange]:
    for change in changes:
        if change.layer == layer and change.key == key:
            return change
    return None


def _trace_move(differential: StageDifferential, name: str) -> TraceMove:
    for move in differential.trace:
        if move.name == name:
            return move
    raise IsoCandidateEmissionError(
        f"La etapa {differential.stage_key} no contiene traza {name}."
    )


def _fmt(value: object) -> str:
    number = float(value)
    if abs(number) < 0.0005:
        number = 0.0
    return f"{number:.3f}"
