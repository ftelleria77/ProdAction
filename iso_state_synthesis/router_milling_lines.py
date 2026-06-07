"""Router milling ISO line builders."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

from .errors import IsoCandidateEmissionError
from .model import EvidenceSource, IsoStateEvaluation, StageDifferential, StateChange


@dataclass(frozen=True)
class _LineMillingTraceModes:
    """Branch predicates for router milling trace emission."""

    has_lead_paths: bool
    uses_side_compensation: bool
    uses_no_lead_side_compensation: bool
    uses_center_circle_leads: bool
    uses_closed_center_leads: bool
    uses_open_center_leads: bool


@dataclass(frozen=True)
class _LineMillingTraceContext:
    """State read by the router milling trace emitter before generating ISO."""

    start_x: object
    start_y: object
    end_x: object
    end_y: object
    rapid_z: object
    cut_z: object
    security_z: object
    tool_radius: object
    plunge_feed: object
    milling_feed: object
    tool_offset: object
    approach: object
    trajectory: object
    lift: object
    source: EvidenceSource
    side_of_feature: str
    overcut_length: float
    strategy_name: str
    profile_family: str
    profile_winding: str
    circle_center_x: Optional[object]
    circle_center_y: Optional[object]
    contour_points: object
    nominal_points: tuple[tuple[float, float], ...]
    open_polyline_outside_piece: bool
    piece_depth: float
    trajectory_primitives: tuple[object, ...]
    approach_type: str
    approach_mode: str
    approach_radius_multiplier: float
    retract_type: str
    retract_mode: str
    retract_radius_multiplier: float
    modes: _LineMillingTraceModes


def _line_milling_prepare_after_boring_lines(
    differential: StageDifferential,
    *,
    previous_family: str,
    previous_prepare: StageDifferential,
    previous_router_prepare: Optional[StageDifferential] = None,
) -> tuple[str, ...]:
    spindle = _change_after(differential, "herramienta", "spindle")
    etk9 = _change_after(differential, "salida", "etk_9")
    etk18 = _change_after(differential, "salida", "etk_18")
    spindle_speed = _change_after(differential, "herramienta", "spindle_speed_standard")
    shf_x = _change_after(differential, "herramienta", "shf_x")
    shf_y = _change_after(differential, "herramienta", "shf_y")
    shf_z = _change_after(differential, "herramienta", "shf_z")
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
    return tuple(prepare_lines)


def _line_milling_trace_context(
    evaluation: IsoStateEvaluation,
    differential: StageDifferential,
) -> _LineMillingTraceContext:
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
    piece_depth = float(evaluation.initial_state.get("pieza", "depth"))
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
    modes = _line_milling_trace_modes(
        approach=approach,
        lift=lift,
        strategy_name=strategy_name,
        side_of_feature=side_of_feature,
        profile_family=profile_family,
    )
    return _LineMillingTraceContext(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        rapid_z=rapid_z,
        cut_z=cut_z,
        security_z=security_z,
        tool_radius=tool_radius,
        plunge_feed=plunge_feed,
        milling_feed=milling_feed,
        tool_offset=tool_offset,
        approach=approach,
        trajectory=trajectory,
        lift=lift,
        source=source,
        side_of_feature=side_of_feature,
        overcut_length=overcut_length,
        strategy_name=strategy_name,
        profile_family=profile_family,
        profile_winding=profile_winding,
        circle_center_x=circle_center_x,
        circle_center_y=circle_center_y,
        contour_points=contour_points,
        nominal_points=nominal_points,
        open_polyline_outside_piece=open_polyline_outside_piece,
        piece_depth=piece_depth,
        trajectory_primitives=trajectory_primitives,
        approach_type=approach_type,
        approach_mode=approach_mode,
        approach_radius_multiplier=approach_radius_multiplier,
        retract_type=retract_type,
        retract_mode=retract_mode,
        retract_radius_multiplier=retract_radius_multiplier,
        modes=modes,
    )


def _line_milling_rapid_point(context: _LineMillingTraceContext) -> tuple[object, object]:
    modes = context.modes
    if modes.uses_open_center_leads:
        lead_geometry = _open_polyline_center_lead_geometry(
            context.nominal_points,
            float(context.tool_radius) * context.approach_radius_multiplier,
            context.approach_type,
        )
        return lead_geometry["rapid"]
    if modes.uses_closed_center_leads:
        lead_geometry = _closed_polyline_center_lead_geometry(
            context.nominal_points,
            float(context.tool_radius) * context.approach_radius_multiplier,
            context.approach_type,
            context.profile_winding,
        )
        return lead_geometry["rapid"]
    if modes.uses_center_circle_leads:
        lead_distance = float(context.tool_radius) * context.approach_radius_multiplier
        if context.approach_type == "Arc":
            return (
                float(context.start_x) - lead_distance,
                float(context.start_y) - lead_distance,
            )
        return (float(context.start_x), float(context.start_y) - lead_distance)
    if context.strategy_name and not modes.has_lead_paths and context.approach.points:
        return (float(context.approach.points[0].x), float(context.approach.points[0].y))
    if modes.uses_no_lead_side_compensation:
        rapid_point, _ = _no_lead_compensation_points(
            context.nominal_points,
            float(context.tool_radius),
            context.profile_family,
            context.profile_winding,
        )
        return rapid_point
    if (
        modes.uses_side_compensation
        and context.profile_family.startswith("Line")
        and context.approach_type == "Line"
        and context.approach_mode == "Down"
        and context.retract_type == "Line"
        and context.retract_mode == "Up"
    ):
        return _linear_side_compensation_rapid_point(
            context.nominal_points,
            context.approach,
        )
    if modes.uses_side_compensation and context.profile_family == "OpenPolyline":
        polyline_lead = _polyline_side_compensation_leads(
            context.nominal_points,
            float(context.tool_radius),
            context.side_of_feature,
            context.approach_type,
            context.approach_radius_multiplier,
        )
        return polyline_lead["entry_rapid"]
    if modes.uses_side_compensation:
        return (
            context.start_x,
            float(context.approach.points[0].y) - (2.0 * context.overcut_length),
        )
    return (
        context.approach.points[0].x if modes.has_lead_paths else context.start_x,
        context.approach.points[0].y if modes.has_lead_paths else context.start_y,
    )


def _line_milling_entry_lines(
    emitted_lines: list[ExplainedIsoLine],
    context: _LineMillingTraceContext,
    rapid_x: object,
    rapid_y: object,
    *,
    previous_router_trace: Optional[StageDifferential] = None,
) -> tuple[str, ...]:
    if previous_router_trace is not None:
        last_xy = _last_emitted_xy(emitted_lines)
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
        return tuple(entry_prefix) + (
            f"G0 X{_fmt(previous_x)} Y{_fmt(previous_y)} Z{_fmt(context.rapid_z)}",
            f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)} Z{_fmt(context.rapid_z)}",
            f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)} Z{_fmt(context.rapid_z)}",
            "D1",
            f"SVL {_fmt(context.tool_offset)}",
            f"VL6={_fmt(context.tool_offset)}",
            f"SVR {_fmt(context.tool_radius)}",
            f"VL7={_fmt(context.tool_radius)}",
        )
    return (
        f"G0 X{_fmt(rapid_x)} Y{_fmt(rapid_y)}",
        f"G0 Z{_fmt(context.rapid_z)}",
        "D1",
        f"SVL {_fmt(context.tool_offset)}",
        f"VL6={_fmt(context.tool_offset)}",
        f"SVR {_fmt(context.tool_radius)}",
        f"VL7={_fmt(context.tool_radius)}",
    )


def _line_milling_trace_motion_lines(
    context: _LineMillingTraceContext,
    rapid_x: object,
    rapid_y: object,
) -> tuple[str, ...]:
    modes = context.modes
    if modes.uses_open_center_leads:
        return _line_milling_open_center_leads_motion_lines(context, rapid_x, rapid_y)
    if modes.uses_closed_center_leads:
        return _line_milling_closed_center_leads_motion_lines(context, rapid_x, rapid_y)
    if modes.uses_center_circle_leads:
        return _line_milling_center_circle_leads_motion_lines(context, rapid_x, rapid_y)
    if context.strategy_name and context.profile_family == "Circle":
        return _line_milling_circle_strategy_motion_lines(context, rapid_x, rapid_y)
    if context.strategy_name and modes.has_lead_paths:
        return _line_milling_strategy_lead_path_motion_lines(context)
    if (
        modes.uses_side_compensation
        and context.profile_family.startswith("Line")
        and context.approach_type == "Line"
        and context.approach_mode == "Down"
        and context.retract_type == "Line"
        and context.retract_mode == "Up"
    ):
        return _line_milling_linear_side_compensation_motion_lines(context)
    if modes.uses_side_compensation and context.profile_family == "OpenPolyline":
        return _line_milling_open_polyline_side_compensation_motion_lines(context)
    if modes.uses_side_compensation:
        return _line_milling_side_compensation_fallback_motion_lines(context)
    if modes.has_lead_paths:
        return _line_milling_lead_path_motion_lines(context)
    if modes.uses_no_lead_side_compensation:
        return _line_milling_no_lead_side_compensation_motion_lines(context)
    if context.strategy_name:
        return _line_milling_strategy_motion_lines(context)
    if not modes.has_lead_paths:
        return _line_milling_no_lead_motion_lines(context)
    return _line_milling_fallback_motion_lines(context)


def _line_milling_linear_side_compensation_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    compensation_code = "G42" if context.side_of_feature == "Right" else "G41"
    include_cut_z = (
        context.open_polyline_outside_piece
        or float(context.cut_z) > -context.piece_depth
    )
    return _linear_side_compensation_motion_lines(
        context.nominal_points,
        context.approach,
        context.lift,
        compensation_code,
        float(context.security_z),
        float(context.cut_z),
        float(context.plunge_feed),
        float(context.milling_feed),
        include_cut_z=include_cut_z,
    )


def _line_milling_open_center_leads_motion_lines(
    context: _LineMillingTraceContext,
    rapid_x: object,
    rapid_y: object,
) -> tuple[str, ...]:
    lead_geometry = _open_polyline_center_lead_geometry(
        context.nominal_points,
        float(context.tool_radius) * context.approach_radius_multiplier,
        context.approach_type,
    )
    retract_geometry = _open_polyline_center_lead_geometry(
        context.nominal_points,
        float(context.tool_radius) * context.retract_radius_multiplier,
        context.retract_type,
    )
    arc_code = "G3" if context.profile_winding != "Clockwise" else "G2"
    generated = ["?%ETK[7]=4"]
    current_x = float(rapid_x)
    current_y = float(rapid_y)
    current_z = float(context.security_z)
    if context.approach_type == "Arc":
        if context.approach_mode == "Down":
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    context.start_x,
                    context.start_y,
                    lead_geometry["approach_center"][0],
                    lead_geometry["approach_center"][1],
                    context.plunge_feed,
                    z=context.cut_z,
                )
            )
        else:
            generated.append(f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}")
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    context.start_x,
                    context.start_y,
                    lead_geometry["approach_center"][0],
                    lead_geometry["approach_center"][1],
                    context.plunge_feed,
                )
            )
    elif context.approach_mode == "Down":
        generated.append(
            _line_milling_motion_line(
                float(context.start_x),
                float(context.start_y),
                float(context.cut_z),
                current_x,
                current_y,
                current_z,
                float(context.plunge_feed),
            )
        )
    else:
        generated.append(f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}")
        generated.append(
            _line_milling_motion_line(
                float(context.start_x),
                float(context.start_y),
                float(context.cut_z),
                current_x,
                current_y,
                float(context.cut_z),
                float(context.plunge_feed),
                always_include_z=False,
            )
        )
    current_x = float(context.start_x)
    current_y = float(context.start_y)
    current_z = float(context.cut_z)
    for point in context.trajectory.points[1:]:
        generated.append(
            _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
                always_include_z=context.open_polyline_outside_piece,
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    if context.retract_type == "Arc":
        exit_x, exit_y = retract_geometry["exit"]
        if context.retract_mode == "Up":
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_x,
                    exit_y,
                    retract_geometry["retract_center"][0],
                    retract_geometry["retract_center"][1],
                    context.milling_feed,
                    z=context.security_z,
                )
            )
            generated.append(f"G0 Z{_fmt(context.security_z)}")
        else:
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_x,
                    exit_y,
                    retract_geometry["retract_center"][0],
                    retract_geometry["retract_center"][1],
                    context.milling_feed,
                )
            )
            generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    else:
        exit_x, exit_y = retract_geometry["exit"]
        if context.retract_mode == "Up":
            generated.append(
                _line_milling_motion_line(
                    exit_x,
                    exit_y,
                    float(context.security_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                )
            )
            generated.append(f"G0 Z{_fmt(context.security_z)}")
        else:
            generated.append(
                _line_milling_motion_line(
                    exit_x,
                    exit_y,
                    float(context.cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                    always_include_z=False,
                )
            )
            generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    return tuple(generated)


def _line_milling_closed_center_leads_motion_lines(
    context: _LineMillingTraceContext,
    rapid_x: object,
    rapid_y: object,
) -> tuple[str, ...]:
    lead_geometry = _closed_polyline_center_lead_geometry(
        context.nominal_points,
        float(context.tool_radius) * context.approach_radius_multiplier,
        context.approach_type,
        context.profile_winding,
    )
    retract_geometry = _closed_polyline_center_lead_geometry(
        context.nominal_points,
        float(context.tool_radius) * context.retract_radius_multiplier,
        context.retract_type,
        context.profile_winding,
    )
    arc_code = "G3" if context.profile_winding == "CounterClockwise" else "G2"
    generated = ["?%ETK[7]=4"]
    current_x = float(rapid_x)
    current_y = float(rapid_y)
    current_z = float(context.security_z)
    if context.approach_type == "Arc":
        if context.approach_mode == "Down":
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    context.start_x,
                    context.start_y,
                    lead_geometry["approach_center"][0],
                    lead_geometry["approach_center"][1],
                    context.plunge_feed,
                    z=context.cut_z,
                )
            )
        else:
            generated.append(f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}")
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    context.start_x,
                    context.start_y,
                    lead_geometry["approach_center"][0],
                    lead_geometry["approach_center"][1],
                    context.plunge_feed,
                )
            )
    elif context.approach_mode == "Down":
        generated.append(
            _line_milling_motion_line(
                float(context.start_x),
                float(context.start_y),
                float(context.cut_z),
                current_x,
                current_y,
                current_z,
                float(context.plunge_feed),
            )
        )
    else:
        generated.append(f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}")
        generated.append(
            _line_milling_motion_line(
                float(context.start_x),
                float(context.start_y),
                float(context.cut_z),
                current_x,
                current_y,
                float(context.cut_z),
                float(context.plunge_feed),
            )
        )
    current_x = float(context.start_x)
    current_y = float(context.start_y)
    current_z = float(context.cut_z)
    primitive_index = 0
    for point in context.trajectory.points[1:]:
        matched_index, primitive = _matching_primitive_record(
            context.trajectory_primitives,
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
                    float(context.milling_feed),
                    fallback_center=(0.0, 0.0),
                    fallback_winding=context.profile_winding,
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
                    float(context.milling_feed),
                )
            )
            if matched_index >= 0:
                primitive_index = matched_index + 1
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    if context.retract_type == "Arc":
        exit_x, exit_y = retract_geometry["exit"]
        if context.retract_mode == "Up":
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_x,
                    exit_y,
                    retract_geometry["retract_center"][0],
                    retract_geometry["retract_center"][1],
                    context.milling_feed,
                    z=context.security_z,
                )
            )
            generated.append(f"G0 Z{_fmt(context.security_z)}")
        else:
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_x,
                    exit_y,
                    retract_geometry["retract_center"][0],
                    retract_geometry["retract_center"][1],
                    context.milling_feed,
                )
            )
            generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    else:
        exit_x, exit_y = retract_geometry["exit"]
        if context.retract_mode == "Up":
            generated.append(
                _line_milling_motion_line(
                    exit_x,
                    exit_y,
                    float(context.security_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                )
            )
            generated.append(f"G0 Z{_fmt(context.security_z)}")
        else:
            generated.append(
                _line_milling_motion_line(
                    exit_x,
                    exit_y,
                    float(context.cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                )
            )
            generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    return tuple(generated)


def _line_milling_center_circle_leads_motion_lines(
    context: _LineMillingTraceContext,
    rapid_x: object,
    rapid_y: object,
) -> tuple[str, ...]:
    if context.circle_center_x is None or context.circle_center_y is None:
        raise IsoCandidateEmissionError("El fresado circular con entrada no contiene centro.")
    lead_distance = float(context.tool_radius) * context.approach_radius_multiplier
    retract_lead_distance = float(context.tool_radius) * context.retract_radius_multiplier
    arc_code = "G3" if context.profile_winding == "CounterClockwise" else "G2"
    approach_center = (float(context.start_x) - lead_distance, float(context.start_y))
    retract_center = (float(context.start_x) - retract_lead_distance, float(context.start_y))
    generated = ["?%ETK[7]=4"]
    current_x = float(rapid_x)
    current_y = float(rapid_y)
    current_z = float(context.security_z)
    if context.approach_type == "Arc":
        if context.approach_mode == "Down":
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    context.start_x,
                    context.start_y,
                    approach_center[0],
                    approach_center[1],
                    context.plunge_feed,
                    z=context.cut_z,
                )
            )
        else:
            generated.append(f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}")
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    context.start_x,
                    context.start_y,
                    approach_center[0],
                    approach_center[1],
                    context.plunge_feed,
                )
            )
    elif context.approach_mode == "Down":
        generated.append(
            _line_milling_motion_line(
                float(context.start_x),
                float(context.start_y),
                float(context.cut_z),
                current_x,
                current_y,
                current_z,
                float(context.plunge_feed),
            )
        )
    else:
        generated.append(f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}")
        generated.append(
            _line_milling_motion_line(
                float(context.start_x),
                float(context.start_y),
                float(context.cut_z),
                current_x,
                current_y,
                float(context.cut_z),
                float(context.plunge_feed),
            )
        )
    current_x = float(context.start_x)
    current_y = float(context.start_y)
    current_z = float(context.cut_z)
    primitive_index = 0
    for point in context.trajectory.points[1:]:
        matched_index, primitive = _matching_primitive_record(
            context.trajectory_primitives,
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
                    float(context.milling_feed),
                    fallback_center=(float(context.circle_center_x), float(context.circle_center_y)),
                    fallback_winding=context.profile_winding,
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
                    float(context.milling_feed),
                    center=(float(context.circle_center_x), float(context.circle_center_y)),
                    winding=context.profile_winding,
                )
            )
            if matched_index >= 0:
                primitive_index = matched_index + 1
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    if context.retract_type == "Arc":
        exit_x = float(context.start_x) - retract_lead_distance
        exit_y = float(context.start_y) + retract_lead_distance
        if context.retract_mode == "Up":
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_x,
                    exit_y,
                    retract_center[0],
                    retract_center[1],
                    context.milling_feed,
                    z=context.security_z,
                )
            )
            generated.append(f"G0 Z{_fmt(context.security_z)}")
        else:
            generated.append(
                _profile_milling_arc_line(
                    arc_code,
                    exit_x,
                    exit_y,
                    retract_center[0],
                    retract_center[1],
                    context.milling_feed,
                )
            )
            generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    else:
        exit_x = float(context.start_x)
        exit_y = float(context.start_y) + retract_lead_distance
        if context.retract_mode == "Up":
            generated.append(
                _line_milling_motion_line(
                    exit_x,
                    exit_y,
                    float(context.security_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                )
            )
            generated.append(f"G0 Z{_fmt(context.security_z)}")
        else:
            generated.append(
                _line_milling_motion_line(
                    exit_x,
                    exit_y,
                    float(context.cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                )
            )
            generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    return tuple(generated)


def _line_milling_circle_strategy_motion_lines(
    context: _LineMillingTraceContext,
    rapid_x: object,
    rapid_y: object,
) -> tuple[str, ...]:
    if context.circle_center_x is None or context.circle_center_y is None:
        raise IsoCandidateEmissionError("El fresado circular con estrategia no contiene centro.")
    current_x = float(rapid_x)
    current_y = float(rapid_y)
    current_z = float(context.security_z)
    primitive_index = 0
    generated = [f"G1 Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}", "?%ETK[7]=4"]
    for point in context.trajectory.points:
        matched_index, primitive = _matching_primitive_record(
            context.trajectory_primitives,
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
                float(context.milling_feed),
                fallback_center=(float(context.circle_center_x), float(context.circle_center_y)),
                fallback_winding=context.profile_winding,
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
                float(context.milling_feed),
            )
            if matched_index >= 0:
                primitive_index = matched_index + 1
        generated.append(line)
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    generated.append(f"G0 Z{_fmt(context.security_z)}")
    return tuple(generated)


def _line_milling_strategy_lead_path_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    generated = [f"G1 Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}", "?%ETK[7]=4"]
    current_x = float(context.approach.points[0].x)
    current_y = float(context.approach.points[0].y)
    current_z = float(context.security_z)
    for point in context.approach.points[1:]:
        generated.append(
            _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    primitive_index = 0
    for point in context.trajectory.points[1:]:
        matched_index, primitive = _matching_primitive_record(
            context.trajectory_primitives,
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
                    float(context.milling_feed),
                    fallback_center=(0.0, 0.0),
                    fallback_winding=context.profile_winding,
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
                    float(context.milling_feed),
                )
            )
            if matched_index >= 0:
                primitive_index = matched_index + 1
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    for point in context.lift.points[1:]:
        generated.append(
            _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    generated.append(f"G0 Z{_fmt(context.security_z)}")
    return tuple(generated)


def _line_milling_strategy_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    current_x = float(context.start_x)
    current_y = float(context.start_y)
    current_z = float(context.security_z)
    generated = [f"G1 Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}", "?%ETK[7]=4"]
    for point in context.trajectory.points:
        line = _line_milling_motion_line(
            float(point.x),
            float(point.y),
            float(point.iso_z),
            current_x,
            current_y,
            current_z,
            float(context.milling_feed),
            always_include_z=context.profile_family != "OpenPolyline",
        )
        generated.append(line)
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    generated.append(f"G0 Z{_fmt(context.security_z)}")
    return tuple(generated)


def _line_milling_no_lead_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    current_x = float(context.trajectory.points[0].x if context.trajectory.points else context.start_x)
    current_y = float(context.trajectory.points[0].y if context.trajectory.points else context.start_y)
    current_z = float(context.cut_z)
    generated = [f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}", "?%ETK[7]=4"]
    for point in context.trajectory.points[1:]:
        center = None
        if (
            context.profile_family == "Circle"
            and context.circle_center_x is not None
            and context.circle_center_y is not None
        ):
            center = (float(context.circle_center_x), float(context.circle_center_y))
        always_include_z = context.profile_family.startswith("Line") or context.open_polyline_outside_piece
        generated.append(
            _profile_toolpath_motion_line(
                point,
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
                center=center,
                winding=context.profile_winding,
                always_include_z=always_include_z,
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    generated.append(f"G0 Z{_fmt(context.security_z)}")
    return tuple(generated)


def _line_milling_fallback_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    current_x = float(context.start_x)
    current_y = float(context.start_y)
    current_z = float(context.security_z)
    generated: list[str] = [f"G1 Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}", "?%ETK[7]=4"]
    for point in context.trajectory.points:
        line = _line_milling_motion_line(
            float(point.x),
            float(point.y),
            float(point.iso_z),
            current_x,
            current_y,
            current_z,
            float(context.milling_feed),
        )
        generated.append(line)
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    generated.append(f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}")
    generated.append(f"G0 Z{_fmt(context.security_z)}")
    return tuple(generated)


def _line_milling_no_lead_side_compensation_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    compensation_code = "G42" if context.side_of_feature == "Right" else "G41"
    _, leadout_point = _no_lead_compensation_points(
        context.nominal_points,
        float(context.tool_radius),
        context.profile_family,
        context.profile_winding,
    )
    current_x = context.nominal_points[0][0]
    current_y = context.nominal_points[0][1]
    current_z = float(context.cut_z)
    include_cut_z = (
        context.profile_family.startswith("Line")
        or context.open_polyline_outside_piece
        or float(context.cut_z) > -context.piece_depth
    )
    generated = [
        "?%ETK[7]=4",
        compensation_code,
        (
            f"G1 X{_fmt(context.nominal_points[0][0])} "
            f"Y{_fmt(context.nominal_points[0][1])} "
            f"Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}"
        ),
        f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}",
    ]
    if (
        context.profile_family == "Circle"
        and context.circle_center_x is not None
        and context.circle_center_y is not None
    ):
        for point in context.nominal_points[2::2] or context.nominal_points[1:]:
            generated.append(
                _profile_milling_arc_line(
                    "G3" if context.profile_winding == "CounterClockwise" else "G2",
                    point[0],
                    point[1],
                    context.circle_center_x,
                    context.circle_center_y,
                    context.milling_feed,
                )
            )
            current_x, current_y = point
    else:
        for point in context.nominal_points[1:]:
            generated.append(
                _line_milling_motion_line(
                    point[0],
                    point[1],
                    float(context.cut_z),
                    current_x,
                    current_y,
                    current_z,
                    float(context.milling_feed),
                    always_include_z=include_cut_z,
                )
            )
            current_x, current_y = point
    generated.extend(
        (
            f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}",
            "G40",
            (
                f"G1 X{_fmt(leadout_point[0])} Y{_fmt(leadout_point[1])} "
                f"Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}"
            ),
        )
    )
    return tuple(generated)


def _line_milling_open_polyline_side_compensation_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    compensation_code = "G42" if context.side_of_feature == "Right" else "G41"
    polyline_lead = _polyline_side_compensation_leads(
        context.nominal_points,
        float(context.tool_radius),
        context.side_of_feature,
        context.approach_type,
        context.approach_radius_multiplier,
    )
    entry_point = polyline_lead["entry"]
    exit_point = polyline_lead["exit"]
    exit_rapid = polyline_lead["exit_rapid"]
    arc_code = "G3" if context.side_of_feature == "Left" else "G2"
    generated = [
        "?%ETK[7]=4",
        compensation_code,
        (
            f"G1 X{_fmt(entry_point[0])} Y{_fmt(entry_point[1])} "
            f"Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}"
        ),
    ]
    if context.approach_type == "Arc":
        entry_center = polyline_lead["entry_center"]
        generated.append(
            _profile_milling_arc_line(
                arc_code,
                context.nominal_points[0][0],
                context.nominal_points[0][1],
                entry_center[0],
                entry_center[1],
                context.plunge_feed,
                z=context.cut_z,
            )
        )
    else:
        generated.append(
            _line_milling_motion_line(
                context.nominal_points[0][0],
                context.nominal_points[0][1],
                float(context.cut_z),
                entry_point[0],
                entry_point[1],
                float(context.security_z),
                float(context.plunge_feed),
            )
        )
    current_x, current_y = context.nominal_points[0]
    current_z = float(context.cut_z)
    include_cut_z = (
        context.open_polyline_outside_piece
        or float(context.cut_z) > -context.piece_depth
    )
    for point in context.nominal_points[1:]:
        generated.append(
            _line_milling_motion_line(
                point[0],
                point[1],
                float(context.cut_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
                always_include_z=include_cut_z,
            )
        )
        current_x, current_y = point
    if context.approach_type == "Arc":
        exit_center = polyline_lead["exit_center"]
        generated.append(
            _profile_milling_arc_line(
                arc_code,
                exit_point[0],
                exit_point[1],
                exit_center[0],
                exit_center[1],
                context.milling_feed,
                z=context.security_z,
            )
        )
    else:
        generated.append(
            _line_milling_motion_line(
                exit_point[0],
                exit_point[1],
                float(context.security_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
            )
        )
    generated.extend(
        (
            "G40",
            (
                f"G1 X{_fmt(exit_rapid[0])} Y{_fmt(exit_rapid[1])} "
                f"Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}"
            ),
        )
    )
    return tuple(generated)


def _line_milling_side_compensation_fallback_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    compensation_code = "G42" if context.side_of_feature == "Right" else "G41"
    lift_y = float(context.lift.points[-2].y)
    return (
        "?%ETK[7]=4",
        compensation_code,
        (
            f"G1 X{_fmt(context.start_x)} Y{_fmt(context.approach.points[0].y)} "
            f"Z{_fmt(context.security_z)} F{_fmt(context.plunge_feed)}"
        ),
        f"G1 Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}",
        f"G1 Y{_fmt(context.start_y)} Z{_fmt(context.cut_z)} F{_fmt(context.plunge_feed)}",
        f"G1 Y{_fmt(context.end_y)} Z{_fmt(context.cut_z)} F{_fmt(context.milling_feed)}",
        f"G1 Y{_fmt(lift_y)} Z{_fmt(context.cut_z)} F{_fmt(context.milling_feed)}",
        f"G1 Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}",
        "G40",
        (
            f"G1 X{_fmt(context.start_x)} "
            f"Y{_fmt(lift_y + (2.0 * context.overcut_length))} "
            f"Z{_fmt(context.security_z)} F{_fmt(context.milling_feed)}"
        ),
    )


def _line_milling_lead_path_motion_lines(
    context: _LineMillingTraceContext,
) -> tuple[str, ...]:
    generated = ["?%ETK[7]=4"]
    current_x = float(context.approach.points[0].x)
    current_y = float(context.approach.points[0].y)
    current_z = float(context.security_z)
    for point in context.approach.points[1:]:
        generated.append(
            _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(context.plunge_feed),
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    for point in context.trajectory.points[1:]:
        generated.append(
            _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    for point in context.lift.points[1:]:
        generated.append(
            _line_milling_motion_line(
                float(point.x),
                float(point.y),
                float(point.iso_z),
                current_x,
                current_y,
                current_z,
                float(context.milling_feed),
            )
        )
        current_x = float(point.x)
        current_y = float(point.y)
        current_z = float(point.iso_z)
    return tuple(generated)


def _line_milling_trace_modes(
    *,
    approach: object,
    lift: object,
    strategy_name: str,
    side_of_feature: str,
    profile_family: str,
) -> _LineMillingTraceModes:
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
        and (profile_family in {"OpenPolyline", "Circle"} or profile_family.startswith("Line"))
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
    return _LineMillingTraceModes(
        has_lead_paths=has_lead_paths,
        uses_side_compensation=uses_side_compensation,
        uses_no_lead_side_compensation=uses_no_lead_side_compensation,
        uses_center_circle_leads=uses_center_circle_leads,
        uses_closed_center_leads=uses_closed_center_leads,
        uses_open_center_leads=uses_open_center_leads,
    )


def _line_milling_reset_lines() -> tuple[str, ...]:
    return (
        "D0",
        "SVL 0.000",
        "VL6=0.000",
        "SVR 0.000",
        "VL7=0.000",
        "?%ETK[7]=0",
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


def _linear_side_compensation_rapid_point(
    nominal_points: tuple[tuple[float, float], ...],
    approach: object,
) -> tuple[float, float]:
    axis = _linear_profile_tangent_axis(nominal_points)
    entry_tangent = _trace_point_tangent(approach.points[0], axis)
    approach_unit = _trace_move_tangent_unit(approach, axis)
    return _linear_profile_program_point(
        nominal_points,
        entry_tangent - approach_unit,
        axis,
    )


def _linear_side_compensation_motion_lines(
    nominal_points: tuple[tuple[float, float], ...],
    approach: object,
    lift: object,
    compensation_code: str,
    security_z: float,
    cut_z: float,
    plunge_feed: float,
    milling_feed: float,
    *,
    include_cut_z: bool,
) -> tuple[str, ...]:
    if len(nominal_points) < 2:
        raise IsoCandidateEmissionError("El perfil lineal compensado no contiene puntos suficientes.")
    axis = _linear_profile_tangent_axis(nominal_points)
    entry_tangent = _trace_point_tangent(approach.points[0], axis)
    entry_x, entry_y = _linear_profile_program_point(nominal_points, entry_tangent, axis)
    start_x, start_y = nominal_points[0]
    generated = [
        "?%ETK[7]=4",
        compensation_code,
        f"G1 X{_fmt(entry_x)} Y{_fmt(entry_y)} Z{_fmt(security_z)} F{_fmt(plunge_feed)}",
    ]
    current_x = entry_x
    current_y = entry_y
    current_z = security_z
    generated.append(
        _line_milling_motion_line(
            start_x,
            start_y,
            cut_z,
            current_x,
            current_y,
            current_z,
            plunge_feed,
        )
    )
    current_x = start_x
    current_y = start_y
    current_z = cut_z
    for point in nominal_points[1:]:
        generated.append(
            _line_milling_motion_line(
                point[0],
                point[1],
                cut_z,
                current_x,
                current_y,
                current_z,
                milling_feed,
                always_include_z=include_cut_z,
            )
        )
        current_x, current_y = point
    current_z = cut_z
    lift_tangent = _trace_point_tangent(lift.points[-1], axis)
    lift_x, lift_y = _linear_profile_program_point(nominal_points, lift_tangent, axis)
    generated.append(
        _line_milling_motion_line(
            lift_x,
            lift_y,
            security_z,
            current_x,
            current_y,
            current_z,
            milling_feed,
        )
    )
    current_z = security_z
    current_x = lift_x
    current_y = lift_y
    lift_unit = _trace_move_tangent_unit(lift, axis)
    leadout_x, leadout_y = _linear_profile_program_point(
        nominal_points,
        lift_tangent + lift_unit,
        axis,
    )
    generated.extend(
        (
            "G40",
            f"G1 X{_fmt(leadout_x)} Y{_fmt(leadout_y)} Z{_fmt(current_z)} F{_fmt(milling_feed)}",
        )
    )
    return tuple(generated)


def _linear_profile_tangent_axis(points: tuple[tuple[float, float], ...]) -> str:
    if len(points) < 2:
        raise IsoCandidateEmissionError("El perfil lineal no contiene puntos suficientes.")
    start_x, start_y = points[0]
    end_x, end_y = points[-1]
    return "X" if abs(end_x - start_x) >= abs(end_y - start_y) else "Y"


def _linear_profile_program_point(
    points: tuple[tuple[float, float], ...],
    tangent: float,
    axis: str,
) -> tuple[float, float]:
    if axis == "X":
        return tangent, points[0][1]
    return points[0][0], tangent


def _trace_point_tangent(point: object, axis: str) -> float:
    value = getattr(point, axis.lower(), None)
    if value is None:
        raise IsoCandidateEmissionError(f"El toolpath lineal compensado no contiene eje {axis}.")
    return float(value)


def _trace_move_tangent_unit(move: object, axis: str) -> float:
    if len(move.points) < 2:
        raise IsoCandidateEmissionError("El lead lineal compensado no contiene puntos suficientes.")
    start = _trace_point_tangent(move.points[0], axis)
    end = _trace_point_tangent(move.points[-1], axis)
    distance = end - start
    if abs(distance) < 0.0005:
        raise IsoCandidateEmissionError("El lead lineal compensado no desplaza sobre el eje de corte.")
    return 1.0 if distance > 0.0 else -1.0


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


def _xy_changed(previous_x: float, previous_y: float, point) -> bool:
    return (
        abs(float(point.x) - previous_x) >= 0.0005
        or abs(float(point.y) - previous_y) >= 0.0005
    )


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
