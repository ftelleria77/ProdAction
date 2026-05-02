"""Initial ISO emitter surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tools import synthesize_pgmx as sp

from .model import IsoGenerationError, IsoGenerationWarning, IsoProgram
from .pgmx_source import PgmxIsoSource, load_pgmx_iso_source


class IsoEmissionNotImplemented(IsoGenerationError, NotImplementedError):
    """Raised when callers request operational ISO blocks before the MVP exists."""


@dataclass(frozen=True)
class _TopDrillTool:
    spindle: int
    mask: int
    shf_x: float
    shf_y: float
    shf_z: float
    tool_offset_length: float
    spindle_speed: float
    descent_feed: float


_TOP_DRILL_TOOLS: dict[str, _TopDrillTool] = {
    "001": _TopDrillTool(1, 1, 0.0, 0.0, 0.0, 77.0, 6000.0, 2000.0),
    "002": _TopDrillTool(2, 2, 0.0, 32.0, -0.2, 77.0, 4000.0, 1000.0),
    "003": _TopDrillTool(3, 4, 0.0, 64.0, -0.25, 77.0, 4000.0, 1000.0),
    "004": _TopDrillTool(4, 8, -32.0, 0.0, -0.35, 77.0, 4000.0, 1000.0),
    "005": _TopDrillTool(5, 16, -64.0, 0.0, -0.95, 77.0, 6000.0, 2000.0),
    "006": _TopDrillTool(6, 32, -96.0, 0.0, -0.2, 77.0, 6000.0, 2000.0),
    "007": _TopDrillTool(7, 64, -128.0, 0.0, 0.0, 77.0, 6000.0, 2000.0),
}


@dataclass(frozen=True)
class _SideDrillTool:
    plane_name: str
    etk8: int
    spindle: int
    mask: int
    shf_x: float
    shf_y: float
    shf_z: float
    tool_offset_length: float
    spindle_speed: float
    descent_feed: float
    axis: str
    direction: int
    coordinate_sign: int


_SIDE_DRILL_TOOLS: dict[str, _SideDrillTool] = {
    "Left": _SideDrillTool(
        "Left",
        3,
        61,
        2147483648,
        -118.0,
        -32.0,
        66.3,
        65.0,
        6000.0,
        2000.0,
        "X",
        -1,
        -1,
    ),
    "Right": _SideDrillTool(
        "Right",
        2,
        60,
        2147483648,
        -66.9,
        -32.0,
        66.45,
        65.0,
        6000.0,
        2000.0,
        "X",
        1,
        1,
    ),
    "Front": _SideDrillTool(
        "Front",
        5,
        58,
        1073741824,
        32.0,
        -21.75,
        66.5,
        65.0,
        6000.0,
        2000.0,
        "Y",
        -1,
        1,
    ),
    "Back": _SideDrillTool(
        "Back",
        4,
        59,
        1073741824,
        32.0,
        29.5,
        66.5,
        65.0,
        6000.0,
        2000.0,
        "Y",
        1,
        -1,
    ),
}

_SUPPORTED_IGNORED_STEP_NAMES = {"", "Xn"}


@dataclass(frozen=True)
class _EmissionState:
    drilling: sp.DrillingSpec
    rapid_point: tuple[float, float, float]
    spindle: int
    mask: int
    spindle_speed: float


def build_iso_header_lines(
    state: sp.PgmxState,
    *,
    program_name: str,
) -> tuple[str, str]:
    """Build the two validated ISO header lines for a PGMX state."""

    area = _normalize_execution_area(state.execution_fields)
    return (
        f"% {program_name}.pgm",
        (
            f";H DX={_format_mm(state.length + state.origin_x)} "
            f"DY={_format_mm(state.width + state.origin_y)} "
            f"DZ={_format_mm(state.depth + state.origin_z)} "
            "BX=0.000 BY=0.000 BZ=0.000 "
            f"-{area} V=0 *MM C=0 T=0"
        ),
    )


def emit_header_only(
    source: PgmxIsoSource | Path,
    *,
    program_name: Optional[str] = None,
) -> IsoProgram:
    """Emit only the validated ISO header.

    This is useful for comparing the first contract rules while the operational
    emitter is still under construction.
    """

    if not isinstance(source, PgmxIsoSource):
        source = load_pgmx_iso_source(Path(source))
    resolved_program_name = _program_name(program_name, source.path)
    warnings = (
        IsoGenerationWarning(
            code="header_only",
            message=(
                "Only the validated ISO header is emitted. Operational blocks "
                "are intentionally not generated yet."
            ),
            source=str(source.path),
        ),
        *source.warnings,
    )
    return IsoProgram(
        program_name=resolved_program_name,
        lines=build_iso_header_lines(source.state, program_name=resolved_program_name),
        warnings=warnings,
    )


def emit_iso_program(
    source: PgmxIsoSource | Path,
    *,
    program_name: Optional[str] = None,
) -> IsoProgram:
    """Emit the currently supported subset of the ISO MVP.

    Supported now:

    - validated header;
    - `HG` frame setup observed in the minimal fixtures;
    - empty pieces;
    - top drilling blocks and patterns;
    - D8 side drilling blocks and patterns on all four side planes.
    """

    if not isinstance(source, PgmxIsoSource):
        source = load_pgmx_iso_source(Path(source))
    resolved_program_name = _program_name(program_name, source.path)
    _validate_supported_source(source)
    drillings = _ordered_drillings(source)
    lines: list[str] = []
    lines.extend(build_iso_header_lines(source.state, program_name=resolved_program_name))
    if not drillings:
        lines.extend(_emit_empty_hg_preamble(source.state))
        lines.extend(_emit_empty_program_end())
    else:
        lines.extend(_emit_hg_preamble(source.state, drillings[0].plane_name))
        previous: _EmissionState | None = None
        for drilling in drillings:
            if drilling.plane_name == "Top":
                block_lines, previous = _emit_top_drilling(source.state, drilling, previous)
            else:
                block_lines, previous = _emit_side_drilling(source.state, drilling, previous)
            lines.extend(block_lines)
        lines.extend(_emit_program_end(source.state, drillings[-1].plane_name))
    return IsoProgram(
        program_name=resolved_program_name,
        lines=tuple(lines),
        warnings=source.warnings,
    )


def _validate_supported_source(source: PgmxIsoSource) -> None:
    if _normalize_execution_area(source.state.execution_fields) != "HG":
        raise IsoEmissionNotImplemented(
            "Only execution area HG is supported by the initial ISO emitter."
        )
    unsupported = source.adaptation.unsupported_entries
    if unsupported:
        details = ", ".join(
            entry.feature_name or entry.feature_id or f"entry {entry.order_index}"
            for entry in unsupported
        )
        raise IsoEmissionNotImplemented(
            f"Unsupported PGMX entries cannot be emitted yet: {details}"
        )
    for entry in source.adaptation.ignored_entries:
        if entry.working_step_name not in _SUPPORTED_IGNORED_STEP_NAMES:
            raise IsoEmissionNotImplemented(
                "Only administrative Xn ignored steps are supported by the "
                f"initial emitter; got {entry.working_step_name!r}."
            )
    if source.adaptation.line_millings:
        raise IsoEmissionNotImplemented("Line milling emission is not implemented yet.")
    if source.adaptation.slot_millings:
        raise IsoEmissionNotImplemented("Slot milling emission is not implemented yet.")
    if source.adaptation.polyline_millings:
        raise IsoEmissionNotImplemented("Polyline milling emission is not implemented yet.")
    if source.adaptation.circle_millings:
        raise IsoEmissionNotImplemented("Circle milling emission is not implemented yet.")
    if source.adaptation.squaring_millings:
        raise IsoEmissionNotImplemented("Squaring emission is not implemented yet.")
    if source.adaptation.drilling_patterns:
        for pattern in source.adaptation.drilling_patterns:
            for drilling in _expand_drilling_pattern(pattern):
                _validate_supported_drilling(drilling)
    for drilling in source.adaptation.drillings:
        _validate_supported_drilling(drilling)


def _validate_supported_drilling(drilling: sp.DrillingSpec) -> None:
    if drilling.plane_name != "Top":
        _side_drill_tool(drilling)
    else:
        _top_drill_tool(drilling)
    if drilling.depth_spec.target_depth is None and not drilling.depth_spec.is_through:
        raise IsoEmissionNotImplemented("Drilling needs a target depth.")


def _ordered_drillings(source: PgmxIsoSource) -> tuple[sp.DrillingSpec, ...]:
    raw: list[sp.DrillingSpec] = []
    for entry in source.adaptation.entries:
        if entry.status != "adapted" or entry.spec is None:
            continue
        spec = entry.spec
        if isinstance(spec, sp.DrillingSpec):
            raw.append(spec)
            continue
        if isinstance(spec, sp.DrillingPatternSpec):
            raw.extend(_expand_drilling_pattern(spec))
            continue
        raise IsoEmissionNotImplemented(
            f"Cannot emit adapted entry kind {entry.spec_kind!r} yet."
        )
    ordered: list[sp.DrillingSpec] = []
    index = 0
    while index < len(raw):
        plane_name = raw[index].plane_name
        end = index + 1
        while end < len(raw) and raw[end].plane_name == plane_name:
            end += 1
        group = raw[index:end]
        if plane_name in {"Left", "Back"}:
            group = list(reversed(group))
        ordered.extend(group)
        index = end
    return tuple(ordered)


def _expand_drilling_pattern(pattern: sp.DrillingPatternSpec) -> tuple[sp.DrillingSpec, ...]:
    drillings: list[sp.DrillingSpec] = []
    row_spacing = pattern.row_spacing if pattern.row_spacing is not None else pattern.spacing
    for row in range(pattern.rows):
        for column in range(pattern.columns):
            drillings.append(
                sp.DrillingSpec(
                    center_x=pattern.center_x + (column * pattern.spacing),
                    center_y=pattern.center_y + (row * row_spacing),
                    diameter=pattern.diameter,
                    feature_name=pattern.feature_name,
                    plane_name=pattern.plane_name,
                    security_plane=pattern.security_plane,
                    depth_spec=pattern.depth_spec,
                    drill_family=pattern.drill_family,
                    tool_resolution=pattern.tool_resolution,
                    tool_id=pattern.tool_id,
                    tool_name=pattern.tool_name,
                )
            )
    return tuple(drillings)


def _emit_empty_hg_preamble(state: sp.PgmxState) -> tuple[str, ...]:
    header_dz = state.depth + state.origin_z
    initial_or_x = -(state.length + state.origin_x) * 1000.0
    return (
        "?%ETK[500]=100",
        "",
        "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )",
        "",
        "G0 G53 Z %ax[2].pa[22]/1000",
        "M58",
        "G71",
        "MLV=0",
        f"%Or[0].ofX={_format_mm(initial_or_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_format_mm(header_dz * 1000.0)}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
        "SHF[Y]=-1515.600",
        f"SHF[Z]={_format_mm(header_dz)}+%ETK[114]/1000",
        "?%ETK[8]=1",
        "G40",
        "?%ETK[8]=1",
        "G40",
    )


def _emit_empty_program_end() -> tuple[str, ...]:
    return (
        "G61",
        "MLV=0",
        "D0",
        "G0 G53 Z201.000",
        "G0 G53 X-3700.000",
        "G64",
        *_emit_syn_reset(),
    )


def _emit_syn_reset() -> tuple[str, ...]:
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


def _is_same_drill_tool(left: sp.DrillingSpec, right: sp.DrillingSpec) -> bool:
    if left.plane_name != right.plane_name:
        return False
    if left.plane_name == "Top":
        return _top_drill_tool(left).spindle == _top_drill_tool(right).spindle
    return _side_drill_tool(left).spindle == _side_drill_tool(right).spindle


def _top_cut_z(state: sp.PgmxState, drilling: sp.DrillingSpec, tool: _TopDrillTool) -> float:
    if drilling.depth_spec.is_through:
        return tool.tool_offset_length - drilling.depth_spec.extra_depth
    if drilling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Top drilling needs a target depth.")
    return state.depth - drilling.depth_spec.target_depth - drilling.depth_spec.extra_depth + tool.tool_offset_length


def _emit_hg_preamble(state: sp.PgmxState, plane_name: str) -> tuple[str, ...]:
    header_dz = state.depth + state.origin_z
    initial_or_x = -(state.length + state.origin_x) * 1000.0
    lines: list[str] = [
        "?%ETK[500]=100",
        "",
        "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )",
        "",
        "G0 G53 Z %ax[2].pa[22]/1000",
        "M58",
        "G71",
        "MLV=0",
        f"%Or[0].ofX={_format_mm(initial_or_x)}",
        "%Or[0].ofY=-1515599.976",
        f"%Or[0].ofZ={_format_mm(header_dz * 1000.0)}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
        "SHF[Y]=-1515.600",
        f"SHF[Z]={_format_mm(header_dz)}+%ETK[114]/1000",
    ]
    lines.extend(_emit_face_selection(state, plane_name))
    lines.extend(
        [
            "MLV=1",
            f"SHF[Z]={_format_mm(state.origin_z)}+%ETK[114]/1000",
            "MLV=2",
            "G17",
        ]
    )
    return tuple(lines)


def _emit_face_selection(state: sp.PgmxState, plane_name: str) -> tuple[str, ...]:
    if plane_name == "Top":
        return (
            "?%ETK[8]=1",
            "G40",
            "?%ETK[8]=1",
            "G40",
            "?%ETK[8]=1",
            "G40",
        )
    side = _SIDE_DRILL_TOOLS.get(plane_name)
    if side is None:
        raise IsoEmissionNotImplemented(f"Unsupported drilling plane {plane_name!r}.")
    lines: list[str] = [
        "?%ETK[8]=1",
        "G40",
        "?%ETK[8]=1",
        "G40",
    ]
    shf_x, shf_y = _side_plane_frame_shift(state, plane_name)
    if plane_name in {"Left", "Back"}:
        lines.extend(
            [
                "MLV=1",
                f"SHF[X]={_format_mm(shf_x)}",
                f"SHF[Y]={_format_mm(shf_y)}",
                f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
            ]
        )
    lines.extend([f"?%ETK[8]={side.etk8}", "G40"])
    return tuple(lines)


def _side_plane_frame_shift(state: sp.PgmxState, plane_name: str) -> tuple[float, float]:
    base_x = -(state.length + state.origin_x)
    base_y = -1515.600 + state.origin_y
    if plane_name == "Left":
        return base_x, base_y + state.width
    if plane_name == "Back":
        return base_x + state.length, base_y
    return base_x, base_y


def _emit_primary_work_frame(state: sp.PgmxState, plane_name: str) -> tuple[str, ...]:
    shf_x, shf_y = _side_plane_frame_shift(state, plane_name)
    return (
        "MLV=1",
        f"SHF[X]={_format_mm(shf_x)}",
        f"SHF[Y]={_format_mm(shf_y)}",
        f"SHF[Z]={_format_mm(state.origin_z)}",
        "MLV=2",
    )


def _emit_top_drilling(
    state: sp.PgmxState,
    drilling: sp.DrillingSpec,
    previous: _EmissionState | None,
) -> tuple[tuple[str, ...], _EmissionState]:
    tool = _top_drill_tool(drilling)
    rapid_z = state.depth + drilling.security_plane + tool.tool_offset_length
    cut_z = _top_cut_z(state, drilling, tool)
    operational_or_x = -(state.length + (2.0 * state.origin_x)) * 1000.0
    current = _EmissionState(
        drilling=drilling,
        rapid_point=(drilling.center_x, drilling.center_y, rapid_z),
        spindle=tool.spindle,
        mask=tool.mask,
        spindle_speed=tool.spindle_speed,
    )
    lines: list[str] = []
    if previous is None:
        lines.extend(
            [
                f"?%ETK[6]={tool.spindle}",
                f"%Or[0].ofX={_format_mm(operational_or_x)}",
                "%Or[0].ofY=-1515599.976",
                f"%Or[0].ofZ={_format_mm((state.depth + state.origin_z) * 1000.0)}",
                *_emit_primary_work_frame(state, "Top"),
                "MLV=2",
                f"SHF[X]={_format_mm(tool.shf_x)}",
                f"SHF[Y]={_format_mm(tool.shf_y)}",
                f"SHF[Z]={_format_mm(tool.shf_z)}",
                "?%ETK[17]=257",
                f"S{_format_spindle_speed(tool.spindle_speed)}M3",
                f"?%ETK[0]={tool.mask}",
                f"G0 X{_format_mm(drilling.center_x)} Y{_format_mm(drilling.center_y)}",
                f"G0 Z{_format_mm(rapid_z)}",
            ]
        )
    else:
        lines.extend(_emit_operation_reentry(state))
        same_tool = _is_same_drill_tool(previous.drilling, drilling)
        if not same_tool:
            lines.append(f"?%ETK[6]={tool.spindle}")
        lines.append(_format_top_full_rapid(previous.rapid_point))
        if not same_tool:
            lines.extend(
                [
                    "MLV=2",
                    f"SHF[X]={_format_mm(tool.shf_x)}",
                    f"SHF[Y]={_format_mm(tool.shf_y)}",
                    f"SHF[Z]={_format_mm(tool.shf_z)}",
                ]
            )
            if previous.spindle_speed != tool.spindle_speed:
                lines.extend(
                    [
                        "?%ETK[17]=257",
                        f"S{_format_spindle_speed(tool.spindle_speed)}M3",
                    ]
                )
            lines.extend(
                [
                    f"?%ETK[0]={tool.mask}",
                    f"G0 X{_format_mm(drilling.center_x)} Y{_format_mm(drilling.center_y)}",
                    f"G0 Z{_format_mm(rapid_z)}",
                ]
            )
        else:
            lines.append(_format_top_full_rapid(current.rapid_point))
    lines.append("?%ETK[7]=3")
    if previous is None:
        lines.append("MLV=2")
    lines.extend(
        [
            f"G1 G9 Z{_format_mm(cut_z)} F{_format_mm(tool.descent_feed)}",
            f"G0 Z{_format_mm(rapid_z)}",
            "MLV=1",
            f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
            "?%ETK[7]=0",
        ]
    )
    return tuple(lines), current


def _emit_operation_reentry(state: sp.PgmxState) -> tuple[str, ...]:
    return (
        "MLV=1",
        f"SHF[Z]={_format_mm(state.origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
    )


def _format_top_full_rapid(point: tuple[float, float, float]) -> str:
    x, y, z = point
    return f"G0 X{_format_mm(x)} Y{_format_mm(y)} Z{_format_mm(z)}"


def _emit_side_drilling(
    state: sp.PgmxState,
    drilling: sp.DrillingSpec,
    previous: _EmissionState | None,
) -> tuple[tuple[str, ...], _EmissionState]:
    tool = _side_drill_tool(drilling)
    target_depth = drilling.depth_spec.target_depth
    if target_depth is None:
        raise IsoEmissionNotImplemented("Side drilling needs a target depth.")
    rapid = tool.direction * _side_axis_rapid_base(state, tool)
    cut = tool.direction * _side_axis_cut_base(state, tool, target_depth, drilling.depth_spec.extra_depth)
    fixed = tool.coordinate_sign * drilling.center_x
    current = _EmissionState(
        drilling=drilling,
        rapid_point=_side_rapid_point(tool, rapid, fixed, drilling.center_y),
        spindle=tool.spindle,
        mask=tool.mask,
        spindle_speed=tool.spindle_speed,
    )
    lines: list[str] = []
    if previous is None:
        lines.extend(
            [
                f"?%ETK[6]={tool.spindle}",
                f"%Or[0].ofX={_format_mm(-(state.length + (2.0 * state.origin_x)) * 1000.0)}",
                "%Or[0].ofY=-1515599.976",
                f"%Or[0].ofZ={_format_mm((state.depth + state.origin_z) * 1000.0)}",
                *_emit_primary_work_frame(state, drilling.plane_name),
                "MLV=2",
                f"SHF[X]={_format_mm(tool.shf_x)}",
                f"SHF[Y]={_format_mm(tool.shf_y)}",
                f"SHF[Z]={_format_mm(tool.shf_z)}",
                "?%ETK[17]=257",
                f"S{_format_spindle_speed(tool.spindle_speed)}M3",
                f"?%ETK[0]={tool.mask}",
            ]
        )
        if _side_uses_short_dwell(drilling):
            lines.append("G4F0.500")
        lines.extend(_emit_side_position_lines(tool, rapid, fixed, drilling.center_y))
        lines.append("?%ETK[7]=3")
        lines.append("MLV=2")
    elif previous.drilling.plane_name == drilling.plane_name:
        lines.extend(_emit_operation_reentry(state))
        if drilling.plane_name in {"Front", "Back"}:
            lines.extend(["MLV=0", "G0 G53 Z201.000", "MLV=2"])
            if _side_uses_short_dwell(drilling):
                lines.append("G4F0.500")
            lines.extend(_emit_side_position_lines(tool, rapid, fixed, drilling.center_y))
        else:
            lines.append(_format_side_full_rapid(previous.rapid_point))
            if drilling.plane_name == "Left" and _side_uses_short_dwell(drilling):
                lines.append("G4F0.500")
            if _is_repeated_right_pattern(previous.drilling, drilling):
                lines.append("G4F0.500")
            lines.append(_format_side_full_rapid(current.rapid_point))
        lines.append("?%ETK[7]=3")
    else:
        lines.extend(_emit_side_face_change(state, drilling.plane_name))
        lines.append(f"?%ETK[6]={tool.spindle}")
        if drilling.plane_name in {"Back", "Left", "Right"}:
            lines.extend(["MLV=0", f"G0 G53 Z{_format_mm(_side_g53_z(drilling.plane_name))}", "MLV=2"])
        lines.extend(
            [
                "MLV=2",
                f"SHF[X]={_format_mm(tool.shf_x)}",
                f"SHF[Y]={_format_mm(tool.shf_y)}",
                f"SHF[Z]={_format_mm(tool.shf_z)}",
            ]
        )
        if previous.mask != tool.mask:
            lines.append(f"?%ETK[0]={tool.mask}")
        if drilling.plane_name == "Left" and _side_uses_short_dwell(drilling):
            lines.append("G4F0.500")
        lines.extend(_emit_side_position_lines(tool, rapid, fixed, drilling.center_y))
        lines.append("?%ETK[7]=3")
    lines.extend(
        [
            _emit_side_cut_line(tool, cut),
            _emit_side_retract_line(tool, rapid, drilling.center_y),
            "MLV=1",
            f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
            "?%ETK[7]=0",
        ]
    )
    return tuple(lines), current


def _emit_side_face_change(state: sp.PgmxState, plane_name: str) -> tuple[str, ...]:
    side = _SIDE_DRILL_TOOLS[plane_name]
    shf_x, shf_y = _side_plane_frame_shift(state, plane_name)
    return (
        "MLV=1",
        f"SHF[X]={_format_mm(shf_x)}",
        f"SHF[Y]={_format_mm(shf_y)}",
        f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
        f"?%ETK[8]={side.etk8}",
        "G40",
        "MLV=1",
        f"SHF[Z]={_format_mm(state.origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
    )


def _side_uses_short_dwell(drilling: sp.DrillingSpec) -> bool:
    return (
        drilling.depth_spec.target_depth is not None
        and drilling.depth_spec.target_depth <= 10.0
    )


def _side_g53_z(plane_name: str) -> float:
    if plane_name == "Right":
        return 149.45
    return 149.5


def _is_repeated_right_pattern(
    previous: sp.DrillingSpec,
    current: sp.DrillingSpec,
) -> bool:
    return (
        current.plane_name == "Right"
        and previous.plane_name == "Right"
        and previous.feature_name == current.feature_name
        and current.center_x > previous.center_x
        and (current.center_x - previous.center_x) <= 32.0
        and previous.center_x < 100.0
    )


def _side_axis_rapid_base(state: sp.PgmxState, tool: _SideDrillTool) -> float:
    offset = 20.0 + tool.tool_offset_length
    if tool.direction > 0:
        if tool.axis == "X":
            return state.length + offset
        return state.width + offset
    return offset


def _side_axis_cut_base(
    state: sp.PgmxState,
    tool: _SideDrillTool,
    target_depth: float,
    extra_depth: float,
) -> float:
    offset = tool.tool_offset_length - target_depth - extra_depth
    if tool.direction > 0:
        if tool.axis == "X":
            return state.length + offset
        return state.width + offset
    return offset


def _emit_side_position_lines(
    tool: _SideDrillTool,
    rapid: float,
    fixed: float,
    z: float,
) -> tuple[str, str]:
    if tool.axis == "X":
        return (
            f"G0 X{_format_mm(rapid)} Y{_format_mm(fixed)}",
            f"G0 Z{_format_mm(z)}",
        )
    return (
        f"G0 X{_format_mm(fixed)} Y{_format_mm(rapid)}",
        f"G0 Z{_format_mm(z)}",
    )


def _side_rapid_point(
    tool: _SideDrillTool,
    rapid: float,
    fixed: float,
    z: float,
) -> tuple[float, float, float]:
    if tool.axis == "X":
        return rapid, fixed, z
    return fixed, rapid, z


def _emit_side_cut_line(tool: _SideDrillTool, cut: float) -> str:
    return f"G1 G9 {tool.axis}{_format_mm(cut)} F{_format_mm(tool.descent_feed)}"


def _emit_side_retract_line(
    tool: _SideDrillTool,
    rapid: float,
    z: float,
) -> str:
    return f"G0 {tool.axis}{_format_mm(rapid)} Z{_format_mm(z)}"


def _format_side_full_rapid(point: tuple[float, float, float]) -> str:
    x, y, z = point
    return f"G0 X{_format_mm(x)} Y{_format_mm(y)} Z{_format_mm(z)}"


def _emit_program_end(state: sp.PgmxState, plane_name: str) -> tuple[str, ...]:
    lines: list[str] = [
        "G61",
        "MLV=0",
        "?%ETK[0]=0",
        "?%ETK[17]=0",
        "G4F1.200",
        "M5",
        "D0",
        "G0 G53 Z201.000",
        "G0 G53 X-3700.000",
        "G64",
    ]
    if plane_name != "Top":
        if plane_name in {"Left", "Back"}:
            lines.extend(
                [
                    "MLV=1",
                    f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
                    f"SHF[Y]={_format_mm(-1515.600 + state.origin_y)}",
                    f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
                ]
            )
        lines.extend(["G61"])
        if plane_name in {"Left", "Back"}:
            lines.extend(["MLV=0"])
        lines.extend(
            [
                "D0",
                "G0 G53 Z201.000",
                "G64",
            ]
        )
    lines.extend(
        [
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
        ]
    )
    return tuple(lines)


def _top_drill_tool(drilling: sp.DrillingSpec) -> _TopDrillTool:
    tool_name = drilling.tool_name.strip()
    if not tool_name and drilling.tool_id:
        tool_name = _tool_name_from_id(drilling.tool_id)
    normalized = _normalize_drill_tool_name(tool_name)
    if normalized not in _TOP_DRILL_TOOLS:
        raise IsoEmissionNotImplemented(
            f"Top drilling tool {drilling.tool_name or drilling.tool_id!r} is not supported yet."
        )
    return _TOP_DRILL_TOOLS[normalized]


def _side_drill_tool(drilling: sp.DrillingSpec) -> _SideDrillTool:
    tool = _SIDE_DRILL_TOOLS.get(drilling.plane_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Side drilling plane {drilling.plane_name!r} is not supported yet."
        )
    if round(float(drilling.diameter), 3) != 8.0:
        raise IsoEmissionNotImplemented(
            "The initial side drilling emitter supports only D8 lateral drills."
        )
    return tool


def _program_name(program_name: Optional[str], source_path: Path) -> str:
    raw = (program_name or source_path.stem).strip()
    return raw or "program"


def _normalize_execution_area(value: str) -> str:
    normalized = (value or "HG").strip().upper().replace(" ", "")
    return normalized or "HG"


def _normalize_drill_tool_name(value: str) -> str:
    raw = value.strip().upper()
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def _tool_name_from_id(tool_id: str) -> str:
    mapping = {
        "1888": "001",
        "1889": "002",
        "1890": "003",
        "1891": "004",
        "1892": "005",
        "1893": "006",
        "1894": "007",
    }
    return mapping.get(tool_id.strip(), "")


def _format_mm(value: float) -> str:
    return f"{float(value):.3f}"


def _format_spindle_speed(value: float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return _format_mm(number)
