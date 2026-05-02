"""Initial ISO emitter surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tools import synthesize_pgmx as sp

from .machine_config import (
    LineMillingToolConfig as _LineMillingTool,
    SideDrillToolConfig as _SideDrillTool,
    SlotMillingToolConfig as _SlotMillingTool,
    TopDrillToolConfig as _TopDrillTool,
    load_machine_config,
)
from .model import IsoGenerationError, IsoGenerationWarning, IsoProgram
from .pgmx_source import PgmxIsoSource, load_pgmx_iso_source


class IsoEmissionNotImplemented(IsoGenerationError, NotImplementedError):
    """Raised when callers request operational ISO blocks before the MVP exists."""


_SUPPORTED_IGNORED_STEP_NAMES = {"", "XN"}


@dataclass(frozen=True)
class _EmissionState:
    drilling: sp.DrillingSpec
    rapid_point: tuple[float, float, float]
    spindle: int
    mask: int
    spindle_speed: float


_SupportedOperation = sp.DrillingSpec | sp.LineMillingSpec | sp.SlotMillingSpec


def _work_origin_y_line() -> str:
    return f"%Or[0].ofY={_format_mm(load_machine_config().frame.work_origin_y)}"


def _base_shf_y(origin_y: float = 0.0) -> float:
    return load_machine_config().frame.base_shf_y + origin_y


def _safe_z_line() -> str:
    return f"G0 G53 Z{_format_mm(load_machine_config().frame.safe_z)}"


def _park_x_line(park_x: float | None = None) -> str:
    if park_x is None:
        park_x = load_machine_config().frame.park_x
    return f"G0 G53 X{_format_mm(park_x)}"


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
    - E004 horizontal line milling on the top plane.
    - 082 horizontal slot milling on the top plane.
    """

    if not isinstance(source, PgmxIsoSource):
        source = load_pgmx_iso_source(Path(source))
    resolved_program_name = _program_name(program_name, source.path)
    _validate_supported_source(source)
    operations = _ordered_operations(source)
    park_x = _source_park_x(source)
    lines: list[str] = []
    lines.extend(build_iso_header_lines(source.state, program_name=resolved_program_name))
    if not operations:
        lines.extend(_emit_empty_hg_preamble(source.state))
        lines.extend(_emit_empty_program_end(park_x))
    else:
        first_operation = operations[0]
        lines.extend(
            _emit_hg_preamble(
                source.state,
                _operation_plane_name(first_operation),
                include_operation_reentry=not isinstance(
                    first_operation, (sp.LineMillingSpec, sp.SlotMillingSpec)
                ),
            )
        )
        previous: _EmissionState | None = None
        for operation in operations:
            if isinstance(operation, sp.LineMillingSpec):
                if previous is not None:
                    raise IsoEmissionNotImplemented(
                        "Line milling after drilling is not implemented yet."
                    )
                lines.extend(_emit_line_milling(source.state, operation))
                continue
            if isinstance(operation, sp.SlotMillingSpec):
                if previous is not None:
                    raise IsoEmissionNotImplemented(
                        "Slot milling after drilling is not implemented yet."
                    )
                lines.extend(_emit_slot_milling(source.state, operation))
                continue
            elif operation.plane_name == "Top":
                block_lines, previous = _emit_top_drilling(source.state, operation, previous)
            else:
                block_lines, previous = _emit_side_drilling(source.state, operation, previous)
            lines.extend(block_lines)
        last_operation = operations[-1]
        if isinstance(last_operation, sp.LineMillingSpec):
            lines.extend(_emit_line_milling_program_end(park_x))
        elif isinstance(last_operation, sp.SlotMillingSpec):
            lines.extend(_emit_slot_milling_program_end(park_x))
        else:
            lines.extend(_emit_program_end(source.state, last_operation.plane_name, park_x))
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
        working_step_name = entry.working_step_name.strip().upper()
        if working_step_name not in _SUPPORTED_IGNORED_STEP_NAMES:
            raise IsoEmissionNotImplemented(
                "Only administrative Xn ignored steps are supported by the "
                f"initial emitter; got {entry.working_step_name!r}."
            )
    if source.adaptation.line_millings:
        if (
            len(source.adaptation.line_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.slot_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial line milling emitter supports one standalone line."
            )
        _validate_supported_line_milling(source.adaptation.line_millings[0])
    if source.adaptation.slot_millings:
        if (
            len(source.adaptation.slot_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.line_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial slot milling emitter supports one standalone slot."
            )
        _validate_supported_slot_milling(source.adaptation.slot_millings[0])
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


def _validate_supported_line_milling(line_milling: sp.LineMillingSpec) -> None:
    _line_milling_tool(line_milling)
    if line_milling.plane_name != "Top":
        raise IsoEmissionNotImplemented("Line milling supports only the Top plane.")
    if line_milling.side_of_feature != "Center":
        raise IsoEmissionNotImplemented("Line milling supports only Center side.")
    if _line_milling_axis(line_milling) is None:
        raise IsoEmissionNotImplemented("Line milling supports only axis-aligned lines.")
    if line_milling.approach.is_enabled or line_milling.retract.is_enabled:
        raise IsoEmissionNotImplemented(
            "Line milling approach/retract curves are not implemented yet."
        )
    strategy = line_milling.milling_strategy
    if strategy is None:
        return
    if not isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        raise IsoEmissionNotImplemented(
            "Line milling supports only unidirectional multiple-pass strategy."
        )
    if (
        strategy.connection_mode != "InPiece"
        or not strategy.allow_multiple_passes
        or strategy.axial_cutting_depth <= 0.0
        or strategy.axial_finish_cutting_depth != 0.0
    ):
        raise IsoEmissionNotImplemented(
            "Line milling supports only the observed PH5 InPiece strategy."
        )


def _validate_supported_slot_milling(slot_milling: sp.SlotMillingSpec) -> None:
    _slot_milling_tool(slot_milling)
    if slot_milling.plane_name != "Top":
        raise IsoEmissionNotImplemented("Slot milling supports only the Top plane.")
    if _line_milling_axis(slot_milling) != "X":
        raise IsoEmissionNotImplemented("Slot milling supports only horizontal slots.")
    if slot_milling.approach.is_enabled or slot_milling.retract.is_enabled:
        raise IsoEmissionNotImplemented(
            "Slot milling approach/retract curves are not implemented yet."
        )
    if slot_milling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Slot milling needs a target depth.")
    if slot_milling.material_position != "Left" or slot_milling.side_offset != 0.0:
        raise IsoEmissionNotImplemented(
            "Slot milling supports only the observed material/offset settings."
        )


def _ordered_operations(source: PgmxIsoSource) -> tuple[_SupportedOperation, ...]:
    raw: list[_SupportedOperation] = []
    for entry in source.adaptation.entries:
        if entry.status != "adapted" or entry.spec is None:
            continue
        spec = entry.spec
        if isinstance(spec, sp.LineMillingSpec):
            raw.append(spec)
            continue
        if isinstance(spec, sp.SlotMillingSpec):
            raw.append(spec)
            continue
        if isinstance(spec, sp.DrillingSpec):
            raw.append(spec)
            continue
        if isinstance(spec, sp.DrillingPatternSpec):
            raw.extend(_expand_drilling_pattern(spec))
            continue
        raise IsoEmissionNotImplemented(
            f"Cannot emit adapted entry kind {entry.spec_kind!r} yet."
        )
    ordered: list[_SupportedOperation] = []
    index = 0
    while index < len(raw):
        plane_name = _operation_plane_name(raw[index])
        end = index + 1
        while end < len(raw) and _operation_plane_name(raw[end]) == plane_name:
            end += 1
        group = raw[index:end]
        if plane_name in {"Left", "Back"} and all(
            isinstance(operation, sp.DrillingSpec) for operation in group
        ):
            group = list(reversed(group))
        ordered.extend(group)
        index = end
    return tuple(ordered)


def _source_park_x(source: PgmxIsoSource) -> float | None:
    for step in reversed(source.snapshot.working_steps):
        if step.runtime_type != "Xn":
            continue
        reference = step.reference.strip()
        if reference and reference not in {"Absolute", "Absoluto"}:
            raise IsoEmissionNotImplemented(
                f"Xn reference {reference!r} is not supported for ISO parking."
            )
        return step.x
    return None


def _operation_plane_name(operation: _SupportedOperation) -> str:
    return operation.plane_name


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
        _work_origin_y_line(),
        f"%Or[0].ofZ={_format_mm(header_dz * 1000.0)}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
        f"SHF[Y]={_format_mm(_base_shf_y())}",
        f"SHF[Z]={_format_mm(header_dz)}+%ETK[114]/1000",
        "?%ETK[8]=1",
        "G40",
        "?%ETK[8]=1",
        "G40",
    )


def _emit_empty_program_end(park_x: float | None) -> tuple[str, ...]:
    return (
        "G61",
        "MLV=0",
        "D0",
        _safe_z_line(),
        _park_x_line(park_x),
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
        return tool.tool_offset_length
    if drilling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Top drilling needs a target depth.")
    return state.depth - drilling.depth_spec.target_depth - drilling.depth_spec.extra_depth + tool.tool_offset_length


def _emit_hg_preamble(
    state: sp.PgmxState,
    plane_name: str,
    *,
    include_operation_reentry: bool = True,
) -> tuple[str, ...]:
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
        _work_origin_y_line(),
        f"%Or[0].ofZ={_format_mm(header_dz * 1000.0)}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
        f"SHF[Y]={_format_mm(_base_shf_y())}",
        f"SHF[Z]={_format_mm(header_dz)}+%ETK[114]/1000",
    ]
    lines.extend(_emit_face_selection(state, plane_name))
    if include_operation_reentry:
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
    side = load_machine_config().side_drill_tools.get(plane_name)
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
    base_y = _base_shf_y(state.origin_y)
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
                _work_origin_y_line(),
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
                _work_origin_y_line(),
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
            lines.extend(["MLV=0", _safe_z_line(), "MLV=2"])
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
    side = load_machine_config().side_drill_tools[plane_name]
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
        return load_machine_config().frame.side_g53_z_right
    return load_machine_config().frame.side_g53_z


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


def _emit_line_milling(
    state: sp.PgmxState,
    line_milling: sp.LineMillingSpec,
) -> tuple[str, ...]:
    tool = _line_milling_tool(line_milling)
    rapid_z = line_milling.security_plane + tool.tool_offset_length
    cut_z = _line_milling_cut_z(state, line_milling)
    tool_radius = line_milling.tool_width / 2.0
    lines: list[str] = [
        "MLV=0",
        f"T{tool.tool_number}",
        "SYN",
        "M06",
        f"?%ETK[6]={tool.spindle}",
        f"?%ETK[9]={tool.tool_code}",
        f"?%ETK[18]={tool.etk18}",
        f"S{_format_spindle_speed(tool.spindle_speed)}M3",
        "G17",
        "MLV=2",
        f"%Or[0].ofX={_format_mm(-(state.length + (2.0 * state.origin_x)) * 1000.0)}",
        _work_origin_y_line(),
        f"%Or[0].ofZ={_format_mm((state.depth + state.origin_z) * 1000.0)}",
        "MLV=1",
        f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
        f"SHF[Y]={_format_mm(_base_shf_y(state.origin_y))}",
        f"SHF[Z]={_format_mm(state.depth + state.origin_z)}",
        "MLV=2",
        "?%ETK[13]=1",
        "MLV=2",
        f"SHF[X]={_format_mm(tool.shf_x)}",
        f"SHF[Y]={_format_mm(tool.shf_y)}",
        f"SHF[Z]={_format_mm(tool.shf_z)}",
        f"G0 X{_format_mm(line_milling.start_x)} Y{_format_mm(line_milling.start_y)}",
        f"G0 Z{_format_mm(rapid_z)}",
        "D1",
        f"SVL {_format_mm(rapid_z - line_milling.security_plane)}",
        f"VL6={_format_mm(rapid_z - line_milling.security_plane)}",
        f"SVR {_format_mm(tool_radius)}",
        f"VL7={_format_mm(tool_radius)}",
    ]
    strategy = line_milling.milling_strategy
    if strategy is None:
        lines.extend(
            [
                f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
                "?%ETK[7]=4",
                _emit_line_milling_move(
                    line_milling,
                    _line_milling_end_coordinate(line_milling),
                    cut_z,
                    tool.milling_feed,
                ),
                f"G0 Z{_format_mm(line_milling.security_plane)}",
            ]
        )
    else:
        lines.append(
            f"G1 Z{_format_mm(line_milling.security_plane)} F{_format_mm(tool.plunge_feed)}"
        )
        lines.append("?%ETK[7]=4")
        lines.extend(_emit_line_milling_passes(line_milling, tool, cut_z, strategy))
        lines.append(f"G0 Z{_format_mm(line_milling.security_plane)}")
    lines.extend(
        [
            "D0",
            "SVL 0.000",
            "VL6=0.000",
            "SVR 0.000",
            "VL7=0.000",
            "?%ETK[7]=0",
        ]
    )
    return tuple(lines)


def _emit_line_milling_passes(
    line_milling: sp.LineMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.UnidirectionalMillingStrategySpec,
) -> tuple[str, ...]:
    lines: list[str] = []
    step = abs(float(strategy.axial_cutting_depth))
    depths = _line_milling_pass_depths(final_depth, step)
    for index, depth in enumerate(depths):
        lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        lines.append(
            _emit_line_milling_move(
                line_milling,
                _line_milling_end_coordinate(line_milling),
                depth,
                tool.milling_feed,
            )
        )
        if index == len(depths) - 1:
            lines.append(
                f"G1 Z{_format_mm(line_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
            )
            continue
        retract_z = min(line_milling.security_plane, depth + (2.0 * step))
        lines.append(f"G1 Z{_format_mm(retract_z)} F{_format_mm(tool.milling_feed)}")
        lines.append(
            _emit_line_milling_move(
                line_milling,
                _line_milling_start_coordinate(line_milling),
                retract_z,
                tool.milling_feed,
            )
        )
    return tuple(lines)


def _emit_line_milling_move(
    line_milling: sp.LineMillingSpec,
    coordinate: float,
    z: float,
    feed: float,
) -> str:
    axis = _line_milling_axis(line_milling)
    if axis is None:
        raise IsoEmissionNotImplemented("Line milling supports only axis-aligned lines.")
    return f"G1 {axis}{_format_mm(coordinate)} Z{_format_mm(z)} F{_format_mm(feed)}"


def _line_milling_axis(line_milling: sp.LineMillingSpec) -> str | None:
    if round(float(line_milling.start_y), 3) == round(float(line_milling.end_y), 3):
        return "X"
    if round(float(line_milling.start_x), 3) == round(float(line_milling.end_x), 3):
        return "Y"
    return None


def _line_milling_start_coordinate(line_milling: sp.LineMillingSpec) -> float:
    axis = _line_milling_axis(line_milling)
    if axis == "X":
        return line_milling.start_x
    if axis == "Y":
        return line_milling.start_y
    raise IsoEmissionNotImplemented("Line milling supports only axis-aligned lines.")


def _line_milling_end_coordinate(line_milling: sp.LineMillingSpec) -> float:
    axis = _line_milling_axis(line_milling)
    if axis == "X":
        return line_milling.end_x
    if axis == "Y":
        return line_milling.end_y
    raise IsoEmissionNotImplemented("Line milling supports only axis-aligned lines.")


def _line_milling_pass_depths(final_depth: float, step: float) -> tuple[float, ...]:
    depths: list[float] = []
    current = -step
    while current > final_depth:
        depths.append(current)
        current -= step
    if not depths or round(depths[-1], 3) != round(final_depth, 3):
        depths.append(final_depth)
    return tuple(depths)


def _line_milling_cut_z(state: sp.PgmxState, line_milling: sp.LineMillingSpec) -> float:
    if line_milling.depth_spec.is_through:
        return -(state.depth + line_milling.depth_spec.extra_depth)
    if line_milling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Line milling needs a target depth.")
    return -line_milling.depth_spec.target_depth


def _emit_line_milling_program_end(park_x: float | None) -> tuple[str, ...]:
    return (
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        "M5",
        "D0",
        _safe_z_line(),
        _park_x_line(park_x),
        "G64",
        *_emit_syn_reset(),
    )


def _emit_slot_milling(
    state: sp.PgmxState,
    slot_milling: sp.SlotMillingSpec,
) -> tuple[str, ...]:
    tool = _slot_milling_tool(slot_milling)
    target_depth = slot_milling.depth_spec.target_depth
    if target_depth is None:
        raise IsoEmissionNotImplemented("Slot milling needs a target depth.")
    rapid_z = slot_milling.security_plane + tool.tool_offset_length
    cut_z = -target_depth
    tool_radius = slot_milling.tool_width / 2.0
    start_x = max(slot_milling.start_x, slot_milling.end_x)
    end_x = min(slot_milling.start_x, slot_milling.end_x)
    y = _slot_milling_y(slot_milling, tool_radius)
    return (
        f"?%ETK[6]={tool.spindle}",
        "G17",
        "MLV=2",
        f"%Or[0].ofX={_format_mm(-(state.length + (2.0 * state.origin_x)) * 1000.0)}",
        _work_origin_y_line(),
        f"%Or[0].ofZ={_format_mm((state.depth + state.origin_z) * 1000.0)}",
        "MLV=1",
        f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
        f"SHF[Y]={_format_mm(_base_shf_y(state.origin_y))}",
        f"SHF[Z]={_format_mm(state.depth + state.origin_z)}",
        "MLV=2",
        "?%ETK[17]=257",
        f"S{_format_spindle_speed(tool.spindle_speed)}M3",
        f"?%ETK[1]={tool.mask}",
        "MLV=2",
        f"SHF[X]={_format_mm(tool.shf_x)}",
        f"SHF[Y]={_format_mm(tool.shf_y)}",
        f"SHF[Z]={_format_mm(tool.shf_z)}",
        f"G0 X{_format_mm(start_x)} Y{_format_mm(y)}",
        f"G0 Z{_format_mm(rapid_z)}",
        "D1",
        f"SVL {_format_mm(tool.tool_offset_length)}",
        f"VL6={_format_mm(tool.tool_offset_length)}",
        f"SVR {_format_mm(tool_radius)}",
        f"VL7={_format_mm(tool_radius)}",
        f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
        "?%ETK[7]=1",
        f"G1 X{_format_mm(end_x)} Z{_format_mm(cut_z)} F{_format_mm(tool.milling_feed)}",
        f"G0 Z{_format_mm(slot_milling.security_plane)}",
        "D0",
        "SVL 0.000",
        "VL6=0.000",
        "SVR 0.000",
        "VL7=0.000",
        "?%ETK[7]=0",
    )


def _slot_milling_y(slot_milling: sp.SlotMillingSpec, tool_radius: float) -> float:
    if slot_milling.side_of_feature == "Center":
        return slot_milling.start_y
    direction = 1.0 if slot_milling.end_x > slot_milling.start_x else -1.0
    if slot_milling.side_of_feature == "Right":
        return slot_milling.start_y - (direction * tool_radius)
    if slot_milling.side_of_feature == "Left":
        return slot_milling.start_y + (direction * tool_radius)
    raise IsoEmissionNotImplemented(
        f"Unsupported slot side {slot_milling.side_of_feature!r}."
    )


def _emit_slot_milling_program_end(park_x: float | None) -> tuple[str, ...]:
    return (
        "G61",
        "MLV=0",
        "?%ETK[1]=0",
        "?%ETK[17]=0",
        "G4F1.200",
        "M5",
        "D0",
        _safe_z_line(),
        _park_x_line(park_x),
        "G64",
        *_emit_syn_reset(),
    )


def _emit_program_end(
    state: sp.PgmxState,
    plane_name: str,
    park_x: float | None,
) -> tuple[str, ...]:
    lines: list[str] = [
        "G61",
        "MLV=0",
        "?%ETK[0]=0",
        "?%ETK[17]=0",
        "G4F1.200",
        "M5",
        "D0",
        _safe_z_line(),
        _park_x_line(park_x),
        "G64",
    ]
    if plane_name != "Top":
        if plane_name in {"Left", "Back"}:
            lines.extend(
                [
                    "MLV=1",
                    f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
                    f"SHF[Y]={_format_mm(_base_shf_y(state.origin_y))}",
                    f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
                ]
            )
        lines.extend(["G61"])
        if plane_name in {"Left", "Back"}:
            lines.extend(["MLV=0"])
        lines.extend(
            [
                "D0",
                _safe_z_line(),
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
    tools = load_machine_config().top_drill_tools
    if normalized not in tools:
        raise IsoEmissionNotImplemented(
            f"Top drilling tool {drilling.tool_name or drilling.tool_id!r} is not supported yet."
        )
    return tools[normalized]


def _side_drill_tool(drilling: sp.DrillingSpec) -> _SideDrillTool:
    tool = load_machine_config().side_drill_tools.get(drilling.plane_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Side drilling plane {drilling.plane_name!r} is not supported yet."
        )
    if round(float(drilling.diameter), 3) != 8.0:
        raise IsoEmissionNotImplemented(
            "The initial side drilling emitter supports only D8 lateral drills."
        )
    return tool


def _line_milling_tool(line_milling: sp.LineMillingSpec) -> _LineMillingTool:
    tool_name = line_milling.tool_name.strip().upper()
    if not tool_name and line_milling.tool_id:
        tool_name = _tool_name_from_id(line_milling.tool_id)
    tool = load_machine_config().line_milling_tools.get(tool_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Line milling tool {line_milling.tool_name or line_milling.tool_id!r} "
            "is not supported yet."
        )
    if round(float(line_milling.tool_width), 3) != 4.0:
        raise IsoEmissionNotImplemented("E004 line milling supports only 4 mm width.")
    return tool


def _slot_milling_tool(slot_milling: sp.SlotMillingSpec) -> _SlotMillingTool:
    tool_name = slot_milling.tool_name.strip().upper()
    if not tool_name and slot_milling.tool_id:
        tool_name = _tool_name_from_id(slot_milling.tool_id)
    tool = load_machine_config().slot_milling_tools.get(tool_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Slot milling tool {slot_milling.tool_name or slot_milling.tool_id!r} "
            "is not supported yet."
        )
    if round(float(slot_milling.tool_width), 3) != 3.8:
        raise IsoEmissionNotImplemented("082 slot milling supports only 3.8 mm width.")
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
    return load_machine_config().tool_names_by_id.get(tool_id.strip(), "")


def _format_mm(value: float) -> str:
    return f"{float(value):.3f}"


def _format_spindle_speed(value: float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return _format_mm(number)
