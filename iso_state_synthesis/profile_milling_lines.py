"""Profile milling ISO trace line builders."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .errors import IsoCandidateEmissionError
from .model import StageDifferential, StateChange, TraceMove
from .router_milling_lines import (
    _line_milling_motion_line,
    _profile_milling_arc_line,
    _profile_toolpath_motion_line,
    _xy_changed,
)


@dataclass(frozen=True)
class _ProfileMillingTraceLines:
    """Profile trace lines split by explanatory emission group."""

    mode: str
    setup: tuple[str, ...]
    entry: tuple[str, ...] = ()
    contour: tuple[str, ...] = ()
    exit: tuple[str, ...] = ()
    leadout: tuple[str, ...] = ()
    toolpath: tuple[str, ...] = ()

    def all_lines(self) -> tuple[str, ...]:
        return self.setup + self.entry + self.contour + self.exit + self.leadout + self.toolpath


def _profile_milling_trace_lines(differential: StageDifferential) -> _ProfileMillingTraceLines:
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
    if strategy_name:
        return _profile_milling_strategy_trace_lines(
            differential,
            rapid_z=rapid_z,
            security_z=security_z,
            tool_offset=tool_offset,
            tool_radius=tool_radius,
            plunge_feed=plunge_feed,
            milling_feed=milling_feed,
            contour_points=contour_points,
        )
    approach_primitives = tuple(_optional_change_after(differential, "movimiento", "approach_primitives", ()))
    lift_primitives = tuple(_optional_change_after(differential, "movimiento", "lift_primitives", ()))
    if approach_enabled and retract_enabled and approach_type == "Arc" and retract_type == "Arc":
        try:
            lead_geometry = _profile_arc_leads_from_pgmxd_toolpaths(
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

    setup = (
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

    current_x = float(start_x)
    current_y = float(start_y)
    current_z = float(cut_z)
    contour_lines: list[str] = []
    for point in contour_points[1:]:
        x, y = point
        contour_lines.append(
            _line_milling_motion_line(
                float(x),
                float(y),
                float(cut_z),
                current_x,
                current_y,
                current_z,
                float(milling_feed),
            )
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

    return _ProfileMillingTraceLines(
        mode="profile",
        setup=setup,
        entry=tuple(entry_lines),
        contour=tuple(contour_lines),
        exit=tuple(exit_lines),
        leadout=(
            "G40",
            f"G1 X{_fmt(leadout_x)} Y{_fmt(leadout_y)} Z{_fmt(security_z)} F{_fmt(milling_feed)}",
        ),
    )


def _profile_milling_strategy_trace_lines(
    differential: StageDifferential,
    *,
    rapid_z: object,
    security_z: object,
    tool_offset: object,
    tool_radius: object,
    plunge_feed: object,
    milling_feed: object,
    contour_points: object,
) -> _ProfileMillingTraceLines:
    approach = _trace_move(differential, "Approach")
    trajectory = _trace_move(differential, "TrajectoryPath")
    lift = _trace_move(differential, "Lift")
    if not approach.points or not trajectory.points or not lift.points:
        raise IsoCandidateEmissionError("La estrategia E001 PH5 no contiene toolpaths completos.")
    rapid_point = approach.points[0]

    setup = (
        f"G0 X{_fmt(rapid_point.x)} Y{_fmt(rapid_point.y)}",
        f"G0 Z{_fmt(rapid_z)}",
        "D1",
        f"SVL {_fmt(tool_offset)}",
        f"VL6={_fmt(tool_offset)}",
        f"SVR {_fmt(tool_radius)}",
        f"VL7={_fmt(tool_radius)}",
        f"G1 Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
        "?%ETK[7]=4",
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

    return _ProfileMillingTraceLines(
        mode="strategy",
        setup=setup,
        toolpath=tuple(generated),
    )


def _profile_arc_leads_from_pgmxd_toolpaths(
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
