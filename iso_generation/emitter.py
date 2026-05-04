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
    side_shf_z: float | None = None
    side_group_from_top: bool = False


_SupportedOperation = (
    sp.DrillingSpec
    | sp.LineMillingSpec
    | sp.SlotMillingSpec
    | sp.PolylineMillingSpec
    | sp.CircleMillingSpec
    | sp.SquaringMillingSpec
)

_TopProfileOperation = (
    sp.LineMillingSpec
    | sp.SlotMillingSpec
    | sp.PolylineMillingSpec
    | sp.CircleMillingSpec
    | sp.SquaringMillingSpec
)

_AUTO_TOP_DRILL_TOOL_NAMES: dict[tuple[str, str], str] = {
    ("Flat", "8"): "001",
    ("Flat", "15"): "002",
    ("Flat", "20"): "003",
    ("Flat", "35"): "004",
    ("Flat", "5"): "005",
    ("Flat", "4"): "006",
    ("Conical", "5"): "007",
}


def _work_origin_y_line() -> str:
    return f"%Or[0].ofY={_format_mm(load_machine_config().frame.work_origin_y)}"


def _base_shf_y(origin_y: float = 0.0) -> float:
    return load_machine_config().frame.base_shf_y + origin_y


def _safe_z_line() -> str:
    return f"G0 G53 Z{_format_mm(load_machine_config().frame.safe_z)}"


def _park_x_line(
    park_x: float | tuple[float, float | None] | None = None,
) -> str:
    if park_x is None:
        park_x = load_machine_config().frame.park_x
    if isinstance(park_x, tuple):
        x, y = park_x
        line = f"G0 G53 X{_format_mm(x)}"
        if y is not None:
            line += f" Y{_format_mm(y)}"
        return line
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
    - E004 open polyline milling on the top plane without custom leads.
    - E004 circle milling on the top plane for observed no-lead, lead and
      strategy cases.
    - E001 bottom-start squaring on the top plane with no leads or observed
      Arc/Quote leads.
    - E001 squaring followed by observed top/side drilling sequences.
    - E001 squaring followed by observed top drilling and 082 slot sequences.
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
        include_top_profile_reset = (
            isinstance(first_operation, sp.PolylineMillingSpec)
            or (
                isinstance(first_operation, sp.CircleMillingSpec)
                and (
                    _circle_compensation(first_operation) is not None
                    or _circle_has_leads(first_operation)
                )
            )
            or (
                isinstance(first_operation, sp.SquaringMillingSpec)
                and first_operation.milling_strategy is None
            )
        )
        lines.extend(
            _emit_hg_preamble(
                source.state,
                _operation_plane_name(first_operation),
                include_operation_reentry=not isinstance(
                    first_operation,
                    (
                        sp.LineMillingSpec,
                        sp.SlotMillingSpec,
                        sp.PolylineMillingSpec,
                        sp.SquaringMillingSpec,
                    ),
                ),
                include_top_profile_reset=include_top_profile_reset,
            )
        )
        previous: _EmissionState | None = None
        top_profile_seen = False
        for operation in operations:
            if isinstance(operation, sp.LineMillingSpec):
                if previous is not None:
                    raise IsoEmissionNotImplemented(
                        "Line milling after drilling is not implemented yet."
                    )
                if top_profile_seen:
                    lines.extend(_emit_top_profile_milling_transition(operation))
                lines.extend(
                    _emit_line_milling(
                        source.state,
                        operation,
                        include_full_setup=not top_profile_seen,
                    )
                )
                top_profile_seen = True
                continue
            if isinstance(operation, sp.SlotMillingSpec):
                if previous is not None:
                    if previous.drilling.plane_name != "Top":
                        raise IsoEmissionNotImplemented(
                            "Slot milling after side drilling is not implemented yet."
                        )
                    lines.extend(_emit_top_drilling_to_slot_transition())
                    lines.extend(
                        _emit_slot_milling(
                            source.state,
                            operation,
                            include_full_setup=False,
                            include_observed_edge_cleanup=True,
                        )
                    )
                    previous = None
                    top_profile_seen = True
                    continue
                if top_profile_seen:
                    raise IsoEmissionNotImplemented(
                        "Slot milling after another profile operation is not implemented yet."
                    )
                lines.extend(_emit_slot_milling(source.state, operation))
                top_profile_seen = True
                continue
            if isinstance(operation, sp.PolylineMillingSpec):
                if previous is not None:
                    raise IsoEmissionNotImplemented(
                        "Polyline milling after drilling is not implemented yet."
                    )
                if top_profile_seen:
                    lines.extend(_emit_top_profile_milling_transition(operation))
                lines.extend(
                    _emit_polyline_milling(
                        source.state,
                        operation,
                        include_full_setup=not top_profile_seen,
                    )
                )
                top_profile_seen = True
                continue
            if isinstance(operation, sp.CircleMillingSpec):
                if previous is not None:
                    raise IsoEmissionNotImplemented(
                        "Circle milling after drilling is not implemented yet."
                    )
                if top_profile_seen:
                    lines.extend(_emit_top_profile_milling_transition(operation))
                lines.extend(
                    _emit_circle_milling(
                        source.state,
                        operation,
                        include_full_setup=not top_profile_seen,
                    )
                )
                top_profile_seen = True
                continue
            if isinstance(operation, sp.SquaringMillingSpec):
                if previous is not None:
                    raise IsoEmissionNotImplemented(
                        "Squaring after drilling is not implemented yet."
                    )
                if top_profile_seen:
                    raise IsoEmissionNotImplemented(
                        "Squaring after another profile operation is not implemented yet."
                    )
                lines.extend(_emit_squaring_milling(source.state, operation))
                top_profile_seen = True
                continue
            elif operation.plane_name == "Top":
                include_full_drilling_setup = True
                if top_profile_seen and previous is None:
                    lines.extend(_emit_top_profile_to_drilling_transition(source.state))
                    top_profile_seen = False
                    include_full_drilling_setup = False
                block_lines, previous = _emit_top_drilling(
                    source.state,
                    operation,
                    previous,
                    include_full_setup=include_full_drilling_setup,
                )
            else:
                if top_profile_seen and previous is None:
                    lines.extend(
                        _emit_top_profile_to_side_drilling_transition(
                            source.state,
                            operation.plane_name,
                        )
                    )
                    top_profile_seen = False
                    block_lines, previous = _emit_side_drilling(
                        source.state,
                        operation,
                        previous,
                        include_full_setup=False,
                    )
                else:
                    block_lines, previous = _emit_side_drilling(source.state, operation, previous)
            lines.extend(block_lines)
        last_operation = operations[-1]
        if isinstance(
            last_operation,
            (
                sp.LineMillingSpec,
                sp.PolylineMillingSpec,
                sp.CircleMillingSpec,
                sp.SquaringMillingSpec,
            ),
        ):
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
        if _is_disabled_working_step_entry(entry):
            continue
        working_step_name = entry.working_step_name.strip().upper()
        if working_step_name not in _SUPPORTED_IGNORED_STEP_NAMES:
            raise IsoEmissionNotImplemented(
                "Only administrative Xn ignored steps are supported by the "
                f"initial emitter; got {entry.working_step_name!r}."
            )
    supports_squaring_then_line = _supports_squaring_then(source, sp.LineMillingSpec)
    supports_squaring_then_polyline = _supports_squaring_then(
        source,
        sp.PolylineMillingSpec,
    )
    supports_squaring_then_circle = _supports_squaring_then(
        source,
        sp.CircleMillingSpec,
    )
    supports_squaring_then_drilling = _supports_squaring_then_drilling(source)
    supports_squaring_top_drilling_then_slot = (
        _supports_squaring_top_drilling_then_slot(source)
    )
    if source.adaptation.line_millings:
        if not supports_squaring_then_line and (
            len(source.adaptation.line_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.slot_millings
            or source.adaptation.polyline_millings
            or source.adaptation.squaring_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial line milling emitter supports one standalone line."
            )
        _validate_supported_line_milling(source.adaptation.line_millings[0])
    if source.adaptation.slot_millings:
        if not supports_squaring_top_drilling_then_slot and (
            len(source.adaptation.slot_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.line_millings
            or source.adaptation.polyline_millings
            or source.adaptation.squaring_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial slot milling emitter supports one standalone slot."
            )
        _validate_supported_slot_milling(source.adaptation.slot_millings[0])
    if source.adaptation.polyline_millings:
        if not supports_squaring_then_polyline and (
            len(source.adaptation.polyline_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.line_millings
            or source.adaptation.slot_millings
            or source.adaptation.squaring_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial polyline milling emitter supports one standalone polyline."
            )
        _validate_supported_polyline_milling(source.adaptation.polyline_millings[0])
    if source.adaptation.circle_millings:
        if not supports_squaring_then_circle and (
            len(source.adaptation.circle_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.line_millings
            or source.adaptation.slot_millings
            or source.adaptation.polyline_millings
            or source.adaptation.squaring_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial circle milling emitter supports one standalone circle."
            )
        _validate_supported_circle_milling(source.adaptation.circle_millings[0])
    if source.adaptation.squaring_millings:
        if not (
            supports_squaring_then_line
            or supports_squaring_then_polyline
            or supports_squaring_then_circle
            or supports_squaring_then_drilling
            or supports_squaring_top_drilling_then_slot
        ) and (
            len(source.adaptation.squaring_millings) != 1
            or source.adaptation.drillings
            or source.adaptation.drilling_patterns
            or source.adaptation.line_millings
            or source.adaptation.slot_millings
            or source.adaptation.polyline_millings
        ):
            raise IsoEmissionNotImplemented(
                "The initial squaring emitter supports one standalone squaring operation."
            )
        _validate_supported_squaring_milling(source.adaptation.squaring_millings[0])
    if source.adaptation.drilling_patterns:
        for pattern in source.adaptation.drilling_patterns:
            for drilling in _expand_drilling_pattern(pattern):
                _validate_supported_drilling(drilling)
    for drilling in source.adaptation.drillings:
        _validate_supported_drilling(drilling)


def _is_disabled_working_step_entry(entry: PgmxAdaptationEntry) -> bool:
    return (
        entry.entry_source == "working_step"
        and entry.status == "ignored"
        and any("deshabilitado" in reason for reason in entry.reasons)
    )


def _supports_squaring_then(
    source: PgmxIsoSource,
    next_type: (
        type[sp.LineMillingSpec]
        | type[sp.PolylineMillingSpec]
        | type[sp.CircleMillingSpec]
    ),
) -> bool:
    adaptation = source.adaptation
    if next_type is sp.LineMillingSpec:
        expected_next = len(adaptation.line_millings) == 1
        no_other_next = (
            not adaptation.polyline_millings
            and not adaptation.slot_millings
            and not adaptation.circle_millings
        )
    elif next_type is sp.PolylineMillingSpec:
        expected_next = len(adaptation.polyline_millings) == 1
        no_other_next = (
            not adaptation.line_millings
            and not adaptation.slot_millings
            and not adaptation.circle_millings
        )
    else:
        expected_next = len(adaptation.circle_millings) == 1
        no_other_next = (
            not adaptation.line_millings
            and not adaptation.slot_millings
            and not adaptation.polyline_millings
        )
    if (
        len(adaptation.squaring_millings) != 1
        or not expected_next
        or not no_other_next
        or adaptation.drillings
        or adaptation.drilling_patterns
    ):
        return False
    operations = [
        entry.spec
        for entry in adaptation.entries
        if entry.status == "adapted"
        and isinstance(entry.spec, (sp.SquaringMillingSpec, next_type))
    ]
    return (
        len(operations) == 2
        and isinstance(operations[0], sp.SquaringMillingSpec)
        and isinstance(operations[1], next_type)
    )


def _supports_squaring_then_drilling(source: PgmxIsoSource) -> bool:
    adaptation = source.adaptation
    if (
        len(adaptation.squaring_millings) != 1
        or not (adaptation.drillings or adaptation.drilling_patterns)
        or adaptation.line_millings
        or adaptation.slot_millings
        or adaptation.polyline_millings
        or adaptation.circle_millings
    ):
        return False
    operations = _ordered_operations(source)
    if len(operations) < 2 or not isinstance(operations[0], sp.SquaringMillingSpec):
        return False
    drillings = operations[1:]
    if not all(isinstance(operation, sp.DrillingSpec) for operation in drillings):
        return False
    first_plane = drillings[0].plane_name
    if first_plane == "Top":
        return True
    return all(drilling.plane_name == first_plane for drilling in drillings)


def _supports_squaring_top_drilling_then_slot(source: PgmxIsoSource) -> bool:
    adaptation = source.adaptation
    if (
        len(adaptation.squaring_millings) != 1
        or len(adaptation.slot_millings) != 1
        or not adaptation.drillings
        or adaptation.drilling_patterns
        or adaptation.line_millings
        or adaptation.polyline_millings
        or adaptation.circle_millings
    ):
        return False
    operations = _ordered_operations(source)
    if len(operations) < 3:
        return False
    return (
        isinstance(operations[0], sp.SquaringMillingSpec)
        and isinstance(operations[-1], sp.SlotMillingSpec)
        and all(
            isinstance(operation, sp.DrillingSpec) and operation.plane_name == "Top"
            for operation in operations[1:-1]
        )
    )


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
    if line_milling.side_of_feature not in {"Center", "Left", "Right"}:
        raise IsoEmissionNotImplemented(
            f"Unsupported line milling side {line_milling.side_of_feature!r}."
        )
    if _line_milling_axis(line_milling) is None:
        raise IsoEmissionNotImplemented("Line milling supports only axis-aligned lines.")
    if (
        line_milling.approach.is_enabled or line_milling.retract.is_enabled
    ) and not _line_milling_has_quote_lines(line_milling):
        raise IsoEmissionNotImplemented(
            "Line milling approach/retract curves are not implemented yet."
        )
    strategy = line_milling.milling_strategy
    if (
        strategy is None
        and line_milling.side_of_feature != "Center"
        and not _line_milling_has_quote_lines(line_milling)
    ):
        raise IsoEmissionNotImplemented(
            "Line milling side compensation needs the observed Line/Quote leads."
        )
    if strategy is None:
        return
    if isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        if (
            not strategy.allow_multiple_passes
            or strategy.axial_cutting_depth <= 0.0
            or strategy.axial_finish_cutting_depth != 0.0
        ):
            raise IsoEmissionNotImplemented(
                "Line milling supports only the observed bidirectional PH5 strategy."
            )
        return
    if not isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        raise IsoEmissionNotImplemented(
            "Line milling supports only observed uni/bidirectional multiple-pass strategies."
        )
    if (
        strategy.connection_mode not in {"InPiece", "SafetyHeight"}
        or not strategy.allow_multiple_passes
        or strategy.axial_cutting_depth <= 0.0
        or strategy.axial_finish_cutting_depth != 0.0
    ):
        raise IsoEmissionNotImplemented(
            "Line milling supports only the observed PH5 strategies."
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


def _validate_supported_polyline_milling(polyline_milling: sp.PolylineMillingSpec) -> None:
    _polyline_milling_tool(polyline_milling)
    if polyline_milling.plane_name != "Top":
        raise IsoEmissionNotImplemented("Polyline milling supports only the Top plane.")
    if polyline_milling.side_of_feature not in {"Center", "Left", "Right"}:
        raise IsoEmissionNotImplemented(
            f"Unsupported polyline side {polyline_milling.side_of_feature!r}."
        )
    if len(polyline_milling.points) < 2:
        raise IsoEmissionNotImplemented("Polyline milling needs at least two points.")
    if _polyline_is_closed(polyline_milling) and _polyline_has_default_leads(polyline_milling):
        raise IsoEmissionNotImplemented(
            "Closed polyline milling without leads is not implemented yet."
        )
    strategy = polyline_milling.milling_strategy
    has_supported_leads = (
        _polyline_has_default_leads(polyline_milling)
        or _polyline_has_quote_lines(polyline_milling)
        or _polyline_has_down_up_lines(polyline_milling)
        or _polyline_has_quote_arcs(polyline_milling)
        or _polyline_has_down_up_arcs(polyline_milling)
    )
    if not has_supported_leads:
        raise IsoEmissionNotImplemented(
            "Polyline milling supports only no leads or observed Line/Arc leads."
        )
    if strategy is not None:
        if _polyline_has_leads(polyline_milling):
            if not (
                _polyline_is_closed(polyline_milling)
                and _polyline_has_down_up_lines(polyline_milling)
            ):
                raise IsoEmissionNotImplemented(
                    "Polyline milling strategies with approach/retract are not implemented yet."
                )
        elif polyline_milling.side_of_feature != "Center":
            raise IsoEmissionNotImplemented(
                "Polyline milling strategies support only the observed Center side."
            )
        if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
            expected_connection = (
                "InPiece"
                if _polyline_is_closed(polyline_milling)
                and _polyline_has_down_up_lines(polyline_milling)
                else "SafetyHeight"
            )
            if (
                strategy.connection_mode != expected_connection
                or not strategy.allow_multiple_passes
                or strategy.axial_cutting_depth <= 0.0
                or strategy.axial_finish_cutting_depth != 0.0
            ):
                raise IsoEmissionNotImplemented(
                    "Polyline milling supports only the observed SafetyHeight PH5 strategy."
                )
        elif isinstance(strategy, sp.BidirectionalMillingStrategySpec):
            if (
                not strategy.allow_multiple_passes
                or strategy.axial_cutting_depth <= 0.0
                or strategy.axial_finish_cutting_depth != 0.0
            ):
                raise IsoEmissionNotImplemented(
                    "Polyline milling supports only the observed bidirectional PH5 strategy."
                )
        else:
            raise IsoEmissionNotImplemented(
                "Polyline milling supports only observed uni/bidirectional strategies."
            )
    if strategy is not None:
        return
    if polyline_milling.depth_spec.target_depth is None and not polyline_milling.depth_spec.is_through:
        raise IsoEmissionNotImplemented("Polyline milling needs a target depth.")


def _validate_supported_circle_milling(circle_milling: sp.CircleMillingSpec) -> None:
    _circle_milling_tool(circle_milling)
    if circle_milling.plane_name != "Top":
        raise IsoEmissionNotImplemented("Circle milling supports only the Top plane.")
    if circle_milling.side_of_feature not in {"Center", "Left", "Right"}:
        raise IsoEmissionNotImplemented(
            f"Unsupported circle side {circle_milling.side_of_feature!r}."
        )
    if circle_milling.winding not in {"Clockwise", "CounterClockwise"}:
        raise IsoEmissionNotImplemented(
            f"Unsupported circle winding {circle_milling.winding!r}."
        )
    if circle_milling.radius <= 0.0:
        raise IsoEmissionNotImplemented("Circle milling needs a positive radius.")
    if circle_milling.depth_spec.target_depth is None and not circle_milling.depth_spec.is_through:
        raise IsoEmissionNotImplemented("Circle milling needs a target depth.")
    has_supported_leads = (
        _circle_has_default_leads(circle_milling)
        or _circle_has_quote_lines(circle_milling)
        or _circle_has_down_up_lines(circle_milling)
        or _circle_has_quote_arcs(circle_milling)
        or _circle_has_down_up_arcs(circle_milling)
    )
    if not has_supported_leads:
        raise IsoEmissionNotImplemented(
            "Circle milling supports only no leads or observed Line/Arc leads."
        )
    if _circle_has_leads(circle_milling) and circle_milling.side_of_feature != "Center":
        raise IsoEmissionNotImplemented(
            "Circle milling leads support only the observed Center side."
        )
    strategy = circle_milling.milling_strategy
    if strategy is None:
        return
    if _circle_has_leads(circle_milling):
        raise IsoEmissionNotImplemented(
            "Circle milling strategies with approach/retract are not implemented yet."
        )
    if isinstance(strategy, sp.HelicalMillingStrategySpec):
        if (
            circle_milling.side_of_feature != "Center"
            or not strategy.allows_finish_cutting
            or strategy.axial_cutting_depth < 0.0
            or strategy.axial_finish_cutting_depth != 0.0
        ):
            raise IsoEmissionNotImplemented(
                "Circle milling supports only the observed center helical strategy."
            )
        return
    if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        if (
            strategy.connection_mode != "InPiece"
            or not strategy.allow_multiple_passes
            or strategy.axial_cutting_depth <= 0.0
            or strategy.axial_finish_cutting_depth != 0.0
        ):
            raise IsoEmissionNotImplemented(
                "Circle milling supports only the observed unidirectional PH5 strategy."
            )
        return
    if isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        if (
            not strategy.allow_multiple_passes
            or strategy.axial_cutting_depth <= 0.0
            or strategy.axial_finish_cutting_depth != 0.0
        ):
            raise IsoEmissionNotImplemented(
                "Circle milling supports only the observed bidirectional PH5 strategy."
            )
        return
    raise IsoEmissionNotImplemented(
        "Circle milling supports only observed uni/bidirectional/helical strategies."
    )


def _validate_supported_squaring_milling(squaring_milling: sp.SquaringMillingSpec) -> None:
    _squaring_milling_tool(squaring_milling)
    if squaring_milling.plane_name != "Top":
        raise IsoEmissionNotImplemented("Squaring supports only the Top plane.")
    if squaring_milling.start_edge not in {"Bottom", "Top", "Left", "Right"}:
        raise IsoEmissionNotImplemented(
            f"Unsupported squaring start edge {squaring_milling.start_edge!r}."
        )
    if squaring_milling.winding not in {"Clockwise", "CounterClockwise"}:
        raise IsoEmissionNotImplemented(
            f"Unsupported squaring winding {squaring_milling.winding!r}."
        )
    if not (
        _squaring_has_default_leads(squaring_milling)
        or _squaring_has_quote_arcs(squaring_milling)
        or _squaring_has_quote_lines(squaring_milling)
        or _squaring_has_down_up_arcs(squaring_milling)
        or _squaring_has_down_up_lines(squaring_milling)
    ):
        raise IsoEmissionNotImplemented(
            "Squaring supports only no leads or observed Line/Arc leads."
        )
    strategy = squaring_milling.milling_strategy
    if strategy is not None:
        if squaring_milling.start_edge != "Bottom" or not _squaring_has_quote_arcs(
            squaring_milling
        ):
            raise IsoEmissionNotImplemented(
                "Squaring strategies support only the observed Bottom Arc/Quote case."
            )
        if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
            if (
                strategy.connection_mode != "InPiece"
                or not strategy.allow_multiple_passes
                or strategy.axial_cutting_depth <= 0.0
                or strategy.axial_finish_cutting_depth != 0.0
            ):
                raise IsoEmissionNotImplemented(
                    "Squaring supports only the observed unidirectional InPiece strategy."
                )
        elif isinstance(strategy, sp.BidirectionalMillingStrategySpec):
            if (
                not strategy.allow_multiple_passes
                or strategy.axial_cutting_depth <= 0.0
                or strategy.axial_finish_cutting_depth != 0.0
            ):
                raise IsoEmissionNotImplemented(
                    "Squaring supports only the observed bidirectional strategy."
                )
        else:
            raise IsoEmissionNotImplemented(
                "Squaring supports only observed uni/bidirectional strategies."
            )
    if squaring_milling.depth_spec.target_depth is None and not squaring_milling.depth_spec.is_through:
        raise IsoEmissionNotImplemented("Squaring needs a target depth.")


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
        if isinstance(spec, sp.PolylineMillingSpec):
            raw.append(spec)
            continue
        if isinstance(spec, sp.CircleMillingSpec):
            raw.append(spec)
            continue
        if isinstance(spec, sp.SquaringMillingSpec):
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
        if plane_name == "Top":
            group = _order_top_drilling_runs(group)
        elif all(isinstance(operation, sp.DrillingSpec) for operation in group):
            group = _order_side_drilling_group(group)
        ordered.extend(group)
        index = end
    return tuple(ordered)


def _order_top_drilling_runs(group: list[_SupportedOperation]) -> list[_SupportedOperation]:
    ordered: list[_SupportedOperation] = []
    index = 0
    profile_seen = False
    while index < len(group):
        operation = group[index]
        if not isinstance(operation, sp.DrillingSpec):
            ordered.append(operation)
            if isinstance(operation, _TopProfileOperation):
                profile_seen = True
            index += 1
            continue
        end = index + 1
        while end < len(group) and isinstance(group[end], sp.DrillingSpec):
            end += 1
        drilling_run = group[index:end]
        if profile_seen:
            ordered.extend(_order_top_drilling_group(drilling_run))
        else:
            ordered.extend(drilling_run)
        index = end
    return ordered


def _order_top_drilling_group(
    group: list[_SupportedOperation],
) -> list[sp.DrillingSpec]:
    remaining = [operation for operation in group if isinstance(operation, sp.DrillingSpec)]
    ordered: list[sp.DrillingSpec] = []
    current = (0.0, 0.0)
    while remaining:
        next_drilling = min(
            remaining,
            key=lambda drilling: (
                _manhattan_distance(current, (drilling.center_x, drilling.center_y)),
                round(float(drilling.center_x), 3),
                round(float(drilling.center_y), 3),
            ),
        )
        remaining.remove(next_drilling)
        ordered.append(next_drilling)
        current = (next_drilling.center_x, next_drilling.center_y)
    return ordered


def _manhattan_distance(
    left: tuple[float, float],
    right: tuple[float, float],
) -> float:
    return abs(left[0] - right[0]) + abs(left[1] - right[1])


def _order_side_drilling_group(
    group: list[_SupportedOperation],
) -> list[sp.DrillingSpec]:
    drillings = [operation for operation in group if isinstance(operation, sp.DrillingSpec)]
    if not drillings:
        return []
    plane_name = drillings[0].plane_name
    return sorted(
        drillings,
        key=lambda drilling: round(float(drilling.center_x), 3),
        reverse=plane_name in {"Left", "Back"},
    )


def _source_park_x(source: PgmxIsoSource) -> tuple[float, float | None] | None:
    for step in reversed(source.snapshot.working_steps):
        if step.runtime_type != "Xn":
            continue
        reference = step.reference.strip()
        if reference and reference not in {"Absolute", "Absoluto"}:
            raise IsoEmissionNotImplemented(
                f"Xn reference {reference!r} is not supported for ISO parking."
            )
        return step.x, step.y
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
    include_top_profile_reset: bool = False,
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
    lines.extend(
        _emit_face_selection(
            state,
            plane_name,
            include_top_profile_reset=include_top_profile_reset,
        )
    )
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


def _emit_face_selection(
    state: sp.PgmxState,
    plane_name: str,
    *,
    include_top_profile_reset: bool = False,
) -> tuple[str, ...]:
    if plane_name == "Top":
        lines = [
            "?%ETK[8]=1",
            "G40",
            "?%ETK[8]=1",
            "G40",
            "?%ETK[8]=1",
            "G40",
        ]
        if include_top_profile_reset:
            lines.insert(4, "?%ETK[7]=0")
        return tuple(lines)
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
    *,
    include_full_setup: bool = True,
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
        if include_full_setup:
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
            if tool.spindle != 1:
                lines.append(f"?%ETK[6]={tool.spindle}")
            lines.extend(
                [
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
    if previous is None and include_full_setup:
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


def _emit_top_profile_to_drilling_transition(state: sp.PgmxState) -> tuple[str, ...]:
    return (
        "?%ETK[8]=1",
        "G40",
        "MLV=0",
        _safe_z_line(),
        "MLV=2",
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        _safe_z_line(),
        "G64",
        *_emit_operation_reentry(state),
    )


def _emit_top_drilling_to_slot_transition() -> tuple[str, ...]:
    return (
        "?%ETK[8]=1",
        "G40",
        "MLV=0",
        _safe_z_line(),
        "MLV=2",
        "?%ETK[0]=0",
    )


def _emit_top_profile_to_side_drilling_transition(
    state: sp.PgmxState,
    plane_name: str,
) -> tuple[str, ...]:
    side = load_machine_config().side_drill_tools.get(plane_name)
    if side is None:
        raise IsoEmissionNotImplemented(f"Unsupported drilling plane {plane_name!r}.")
    lines: list[str] = []
    if plane_name in {"Left", "Back"}:
        shf_x, shf_y = _side_plane_frame_shift(state, plane_name)
        lines.extend(
            [
                "MLV=1",
                f"SHF[X]={_format_mm(shf_x)}",
                f"SHF[Y]={_format_mm(shf_y)}",
                f"SHF[Z]={_format_mm(state.depth + state.origin_z)}+%ETK[114]/1000",
            ]
        )
    lines.extend(
        [
            f"?%ETK[8]={side.etk8}",
            "G40",
            "MLV=0",
            _safe_z_line(),
            "MLV=2",
            "G61",
            "MLV=0",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            _safe_z_line(),
            "G64",
            *_emit_operation_reentry(state),
        ]
    )
    return tuple(lines)


def _format_top_full_rapid(point: tuple[float, float, float]) -> str:
    x, y, z = point
    return f"G0 X{_format_mm(x)} Y{_format_mm(y)} Z{_format_mm(z)}"


def _emit_side_drilling(
    state: sp.PgmxState,
    drilling: sp.DrillingSpec,
    previous: _EmissionState | None,
    *,
    include_full_setup: bool = True,
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
        side_shf_z=tool.shf_z,
        side_group_from_top=(
            not include_full_setup
            or (
                previous is not None
                and (
                    previous.drilling.plane_name == "Top"
                    or (
                        previous.drilling.plane_name == drilling.plane_name
                        and previous.side_group_from_top
                    )
                )
            )
        ),
    )
    lines: list[str] = []
    if previous is None:
        lines.append(f"?%ETK[6]={tool.spindle}")
        if include_full_setup:
            lines.extend(
                [
                    f"%Or[0].ofX={_format_mm(-(state.length + (2.0 * state.origin_x)) * 1000.0)}",
                    _work_origin_y_line(),
                    f"%Or[0].ofZ={_format_mm((state.depth + state.origin_z) * 1000.0)}",
                    *_emit_primary_work_frame(state, drilling.plane_name),
                ]
            )
        lines.extend(
            [
                "MLV=2",
                f"SHF[X]={_format_mm(tool.shf_x)}",
                f"SHF[Y]={_format_mm(tool.shf_y)}",
                f"SHF[Z]={_format_mm(tool.shf_z)}",
                "?%ETK[17]=257",
                f"S{_format_spindle_speed(tool.spindle_speed)}M3",
                f"?%ETK[0]={tool.mask}",
            ]
        )
        if _side_uses_short_dwell(drilling) or (
            not include_full_setup and drilling.plane_name == "Left"
        ):
            lines.append("G4F0.500")
        lines.extend(_emit_side_position_lines(tool, rapid, fixed, drilling.center_y))
        lines.append("?%ETK[7]=3")
        if include_full_setup:
            lines.append("MLV=2")
    elif previous.drilling.plane_name == drilling.plane_name:
        lines.extend(_emit_operation_reentry(state))
        if drilling.plane_name in {"Front", "Back"}:
            lines.extend(["MLV=0", _safe_z_line(), "MLV=2"])
            if _side_needs_front_back_between_dwell(previous, drilling):
                lines.append("G4F0.500")
            lines.extend(_emit_side_position_lines(tool, rapid, fixed, drilling.center_y))
        else:
            lines.append(_format_side_full_rapid(previous.rapid_point))
            if drilling.plane_name == "Left" and _side_uses_short_dwell(drilling):
                lines.append("G4F0.500")
            if drilling.plane_name == "Right" and (
                _side_needs_right_between_dwell(previous, drilling)
                or _is_repeated_right_pattern(previous.drilling, drilling)
            ):
                lines.append("G4F0.500")
            lines.append(_format_side_full_rapid(current.rapid_point))
        lines.append("?%ETK[7]=3")
    else:
        if previous.drilling.plane_name == "Top" and drilling.plane_name in {"Front", "Right"}:
            lines.extend(_emit_top_to_side_face_change(state, drilling.plane_name))
        else:
            lines.extend(_emit_side_face_change(state, drilling.plane_name))
        lines.append(f"?%ETK[6]={tool.spindle}")
        lines.extend(
            [
                "MLV=0",
                f"G0 G53 Z{_format_mm(_side_g53_z(state, previous, tool))}",
                "MLV=2",
            ]
        )
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
        if previous.mask != tool.mask:
            lines.append(f"?%ETK[0]={tool.mask}")
        if previous.drilling.plane_name == "Top" or (
            drilling.plane_name == "Left" and _side_uses_short_dwell(drilling)
        ):
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


def _emit_top_to_side_face_change(state: sp.PgmxState, plane_name: str) -> tuple[str, ...]:
    side = load_machine_config().side_drill_tools[plane_name]
    return (
        f"?%ETK[8]={side.etk8}",
        "G40",
        *_emit_operation_reentry(state),
    )


def _side_uses_short_dwell(drilling: sp.DrillingSpec) -> bool:
    target_depth = drilling.depth_spec.target_depth
    if target_depth is None:
        return False
    if target_depth <= 10.0:
        return True
    if drilling.plane_name in {"Front", "Right"}:
        return True
    return drilling.plane_name == "Left" and target_depth <= 21.0


def _side_needs_right_between_dwell(
    previous: _EmissionState,
    drilling: sp.DrillingSpec,
) -> bool:
    if previous.side_group_from_top and _is_close_high_side_pair(previous.drilling, drilling):
        return False
    target_depth = drilling.depth_spec.target_depth
    return target_depth is not None and target_depth > 10.0


def _side_needs_front_back_between_dwell(
    previous: _EmissionState,
    drilling: sp.DrillingSpec,
) -> bool:
    if previous.side_group_from_top and _is_close_high_side_pair(previous.drilling, drilling):
        return False
    target_depth = drilling.depth_spec.target_depth
    if target_depth is None:
        return False
    if target_depth <= 21.0:
        return drilling.plane_name == "Front" or target_depth <= 10.0 or previous.side_group_from_top
    if drilling.plane_name == "Front":
        return target_depth >= 29.0
    return target_depth >= 29.0 and previous.side_group_from_top


def _is_close_high_side_pair(
    previous: sp.DrillingSpec,
    current: sp.DrillingSpec,
) -> bool:
    return (
        previous.plane_name == current.plane_name
        and current.plane_name in {"Front", "Back", "Right"}
        and previous.center_x > 100.0
        and abs(current.center_x - previous.center_x) <= 32.0
    )


def _side_g53_z(
    state: sp.PgmxState,
    previous: _EmissionState | None,
    tool: _SideDrillTool,
) -> float:
    involved_side_z = [tool.shf_z]
    if previous is not None and previous.side_shf_z is not None:
        involved_side_z.append(previous.side_shf_z)
    frame = load_machine_config().frame
    return (
        state.depth
        + state.origin_z
        + frame.side_g53_clearance
        + max(involved_side_z)
    )


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
    *,
    include_full_setup: bool = True,
) -> tuple[str, ...]:
    tool = _line_milling_tool(line_milling)
    rapid_z = line_milling.security_plane + tool.tool_offset_length
    cut_z = _line_milling_cut_z(state, line_milling)
    tool_radius = line_milling.tool_width / 2.0
    strategy = line_milling.milling_strategy
    quote_lines = _line_milling_has_quote_lines(line_milling)
    uses_coordinate_offset = strategy is not None and line_milling.side_of_feature != "Center"
    start_point, end_point = _line_milling_toolpath_points(
        line_milling,
        tool_radius if uses_coordinate_offset else 0.0,
    )
    unit_x, unit_y = _unit_vector(start_point, end_point)
    entry_point = (
        start_point[0] - (unit_x * line_milling.tool_width),
        start_point[1] - (unit_y * line_milling.tool_width),
    )
    exit_point = (
        end_point[0] + (unit_x * line_milling.tool_width),
        end_point[1] + (unit_y * line_milling.tool_width),
    )
    compensation = None if strategy is not None else _line_milling_compensation(line_milling)
    if quote_lines:
        if compensation is not None:
            rapid_point = (entry_point[0] - unit_x, entry_point[1] - unit_y)
        else:
            rapid_point = entry_point
    else:
        rapid_point = start_point
    lines: list[str] = [
        "MLV=0",
        f"T{tool.tool_number}",
        "SYN",
        "M06",
    ]
    if include_full_setup:
        lines.append(f"?%ETK[6]={tool.spindle}")
    lines.extend(
        [
            f"?%ETK[9]={tool.tool_code}",
            f"?%ETK[18]={tool.etk18}",
            f"S{_format_spindle_speed(tool.spindle_speed)}M3",
            "G17",
            "MLV=2",
        ]
    )
    if include_full_setup:
        lines.extend(
            [
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
            ]
        )
    else:
        lines.append("?%ETK[13]=1")
    lines.extend(
        [
        f"G0 X{_format_mm(rapid_point[0])} Y{_format_mm(rapid_point[1])}",
        f"G0 Z{_format_mm(rapid_z)}",
        "D1",
        f"SVL {_format_mm(rapid_z - line_milling.security_plane)}",
        f"VL6={_format_mm(rapid_z - line_milling.security_plane)}",
        f"SVR {_format_mm(tool_radius)}",
        f"VL7={_format_mm(tool_radius)}",
        ]
    )
    if strategy is None:
        if quote_lines:
            lines.extend(
                _emit_line_milling_quote_single_pass(
                    line_milling,
                    tool,
                    cut_z,
                    start_point,
                    end_point,
                    entry_point,
                    exit_point,
                    compensation,
                    (unit_x, unit_y),
                )
            )
        else:
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
        if quote_lines:
            lines.extend(
                _emit_line_milling_quote_passes(
                    line_milling,
                    tool,
                    cut_z,
                    strategy,
                    start_point,
                    end_point,
                    entry_point,
                    exit_point,
                )
            )
        else:
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


def _emit_line_milling_quote_single_pass(
    line_milling: sp.LineMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    entry_point: tuple[float, float],
    exit_point: tuple[float, float],
    compensation: str | None,
    unit: tuple[float, float],
) -> tuple[str, ...]:
    lines: list[str] = ["?%ETK[7]=4"]
    if compensation is not None:
        lines.append(compensation)
        lines.append(
            _format_polyline_xyz_move(
                entry_point,
                line_milling.security_plane,
                tool.plunge_feed,
            )
        )
    lines.append(f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}")
    lines.append(
        _emit_line_milling_point_move(
            line_milling,
            start_point,
            cut_z,
            tool.plunge_feed,
        )
    )
    lines.append(
        _emit_line_milling_point_move(
            line_milling,
            end_point,
            cut_z,
            tool.milling_feed,
        )
    )
    lines.append(
        _emit_line_milling_point_move(
            line_milling,
            exit_point,
            cut_z,
            tool.milling_feed,
        )
    )
    lines.append(
        f"G1 Z{_format_mm(line_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
    )
    if compensation is not None:
        lines.append("G40")
        clearance_point = (exit_point[0] + unit[0], exit_point[1] + unit[1])
        lines.append(
            _format_polyline_xyz_move(
                clearance_point,
                line_milling.security_plane,
                tool.milling_feed,
            )
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


def _emit_line_milling_quote_passes(
    line_milling: sp.LineMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.MillingStrategySpec,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    entry_point: tuple[float, float],
    exit_point: tuple[float, float],
) -> tuple[str, ...]:
    if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        if strategy.connection_mode != "SafetyHeight":
            raise IsoEmissionNotImplemented(
                "Quote line milling supports only SafetyHeight unidirectional strategy."
            )
        return _emit_line_milling_quote_safety_height_passes(
            line_milling,
            tool,
            final_depth,
            strategy,
            start_point,
            end_point,
            entry_point,
            exit_point,
        )
    if isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        return _emit_line_milling_quote_bidirectional_passes(
            line_milling,
            tool,
            final_depth,
            strategy,
            start_point,
            end_point,
            entry_point,
            exit_point,
        )
    raise IsoEmissionNotImplemented(
        "Line milling quote passes support only observed uni/bidirectional strategies."
    )


def _emit_line_milling_quote_safety_height_passes(
    line_milling: sp.LineMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.UnidirectionalMillingStrategySpec,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    entry_point: tuple[float, float],
    exit_point: tuple[float, float],
) -> tuple[str, ...]:
    lines: list[str] = []
    step = abs(float(strategy.axial_cutting_depth))
    depths = _line_milling_pass_depths(final_depth, step)
    for index, depth in enumerate(depths):
        lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        if index == 0:
            lines.append(
                _emit_line_milling_point_move(
                    line_milling,
                    start_point,
                    depth,
                    tool.milling_feed,
                )
            )
        lines.append(
            _emit_line_milling_point_move(
                line_milling,
                end_point,
                depth,
                tool.milling_feed,
            )
        )
        if index == len(depths) - 1:
            lines.append(
                _emit_line_milling_point_move(
                    line_milling,
                    exit_point,
                    depth,
                    tool.milling_feed,
                )
            )
            lines.append(
                f"G1 Z{_format_mm(line_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
            )
            continue
        lines.append(
            f"G1 Z{_format_mm(line_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
        )
        lines.append(
            _emit_line_milling_point_move(
                line_milling,
                start_point,
                line_milling.security_plane,
                tool.milling_feed,
            )
        )
    return tuple(lines)


def _emit_line_milling_quote_bidirectional_passes(
    line_milling: sp.LineMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.BidirectionalMillingStrategySpec,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    entry_point: tuple[float, float],
    exit_point: tuple[float, float],
) -> tuple[str, ...]:
    lines: list[str] = []
    step = abs(float(strategy.axial_cutting_depth))
    depths = _line_milling_pass_depths(final_depth, step)
    forward = True
    current_point = entry_point
    for index, depth in enumerate(depths):
        lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        is_last = index == len(depths) - 1
        if forward:
            if not _same_xy(current_point, start_point):
                lines.append(
                    _emit_line_milling_point_move(
                        line_milling,
                        start_point,
                        depth,
                        tool.milling_feed,
                    )
                )
            lines.append(
                _emit_line_milling_point_move(
                    line_milling,
                    end_point,
                    depth,
                    tool.milling_feed,
                )
            )
            current_point = end_point
            if is_last:
                lines.append(
                    _emit_line_milling_point_move(
                        line_milling,
                        exit_point,
                        depth,
                        tool.milling_feed,
                    )
                )
                current_point = exit_point
        else:
            if not _same_xy(current_point, end_point):
                lines.append(
                    _emit_line_milling_point_move(
                        line_milling,
                        end_point,
                        depth,
                        tool.milling_feed,
                    )
                )
            lines.append(
                _emit_line_milling_point_move(
                    line_milling,
                    start_point,
                    depth,
                    tool.milling_feed,
                )
            )
            current_point = start_point
            if is_last:
                lines.append(
                    _emit_line_milling_point_move(
                        line_milling,
                        entry_point,
                        depth,
                        tool.milling_feed,
                    )
                )
                current_point = entry_point
        forward = not forward
    lines.append(
        f"G1 Z{_format_mm(line_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
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


def _emit_line_milling_point_move(
    line_milling: sp.LineMillingSpec,
    point: tuple[float, float],
    z: float,
    feed: float,
) -> str:
    axis = _line_milling_axis(line_milling)
    if axis is None:
        raise IsoEmissionNotImplemented("Line milling supports only axis-aligned lines.")
    coordinate = point[0] if axis == "X" else point[1]
    return f"G1 {axis}{_format_mm(coordinate)} Z{_format_mm(z)} F{_format_mm(feed)}"


def _line_milling_axis(line_milling: sp.LineMillingSpec) -> str | None:
    if round(float(line_milling.start_y), 3) == round(float(line_milling.end_y), 3):
        return "X"
    if round(float(line_milling.start_x), 3) == round(float(line_milling.end_x), 3):
        return "Y"
    return None


def _line_milling_has_quote_lines(line_milling: sp.LineMillingSpec) -> bool:
    approach = line_milling.approach
    retract = line_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Line"
        and retract.retract_type == "Line"
        and approach.mode == "Quote"
        and retract.mode == "Quote"
        and round(float(approach.radius_multiplier), 3) == 2.0
        and round(float(retract.radius_multiplier), 3) == 2.0
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _line_milling_toolpath_points(
    line_milling: sp.LineMillingSpec,
    side_offset: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    start = (line_milling.start_x, line_milling.start_y)
    end = (line_milling.end_x, line_milling.end_y)
    if side_offset == 0.0 or line_milling.side_of_feature == "Center":
        return start, end
    unit_x, unit_y = _unit_vector(start, end)
    if line_milling.side_of_feature == "Left":
        normal = (-unit_y, unit_x)
    elif line_milling.side_of_feature == "Right":
        normal = (unit_y, -unit_x)
    else:
        raise IsoEmissionNotImplemented(
            f"Unsupported line milling side {line_milling.side_of_feature!r}."
        )
    offset_x = normal[0] * side_offset
    offset_y = normal[1] * side_offset
    return (
        (start[0] + offset_x, start[1] + offset_y),
        (end[0] + offset_x, end[1] + offset_y),
    )


def _line_milling_compensation(line_milling: sp.LineMillingSpec) -> str | None:
    if line_milling.side_of_feature == "Left":
        return "G41"
    if line_milling.side_of_feature == "Right":
        return "G42"
    return None


def _same_xy(
    first: tuple[float, float],
    second: tuple[float, float],
) -> bool:
    return (
        round(float(first[0]), 3) == round(float(second[0]), 3)
        and round(float(first[1]), 3) == round(float(second[1]), 3)
    )


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


def _emit_circle_milling(
    state: sp.PgmxState,
    circle_milling: sp.CircleMillingSpec,
    *,
    include_full_setup: bool = True,
) -> tuple[str, ...]:
    tool = _circle_milling_tool(circle_milling)
    rapid_z = circle_milling.security_plane + tool.tool_offset_length
    cut_z = _circle_milling_cut_z(state, circle_milling)
    tool_radius = circle_milling.tool_width / 2.0
    strategy = circle_milling.milling_strategy
    uses_coordinate_offset = (
        strategy is not None
        and not isinstance(strategy, sp.HelicalMillingStrategySpec)
        and circle_milling.side_of_feature != "Center"
    )
    radius = _circle_toolpath_radius(
        circle_milling,
        tool_radius if uses_coordinate_offset else 0.0,
    )
    start_point = _circle_start_point(circle_milling, radius)
    compensation = None if strategy is not None else _circle_compensation(circle_milling)
    rapid_point = _circle_rapid_point(circle_milling, radius, compensation)
    lines: list[str] = [
        "MLV=0",
        f"T{tool.tool_number}",
        "SYN",
        "M06",
    ]
    if include_full_setup:
        lines.append(f"?%ETK[6]={tool.spindle}")
    lines.extend(
        [
            f"?%ETK[9]={tool.tool_code}",
            f"?%ETK[18]={tool.etk18}",
            f"S{_format_spindle_speed(tool.spindle_speed)}M3",
            "G17",
            "MLV=2",
        ]
    )
    if include_full_setup:
        lines.extend(
            [
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
            ]
        )
    else:
        lines.append("?%ETK[13]=1")
    lines.extend(
        [
            f"G0 X{_format_mm(rapid_point[0])} Y{_format_mm(rapid_point[1])}",
            f"G0 Z{_format_mm(rapid_z)}",
            "D1",
            f"SVL {_format_mm(rapid_z - circle_milling.security_plane)}",
            f"VL6={_format_mm(rapid_z - circle_milling.security_plane)}",
            f"SVR {_format_mm(tool_radius)}",
            f"VL7={_format_mm(tool_radius)}",
        ]
    )
    if strategy is None:
        lines.extend(
            _emit_circle_single_pass(
                circle_milling,
                tool,
                cut_z,
                radius,
                rapid_point,
                start_point,
                compensation,
            )
        )
    elif isinstance(strategy, sp.HelicalMillingStrategySpec):
        lines.extend(
            _emit_circle_helical_passes(
                circle_milling,
                tool,
                cut_z,
                radius,
                strategy,
            )
        )
    else:
        lines.extend(
            _emit_circle_strategy_passes(
                circle_milling,
                tool,
                cut_z,
                radius,
                strategy,
            )
        )
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


def _emit_circle_single_pass(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    radius: float,
    rapid_point: tuple[float, float],
    start_point: tuple[float, float],
    compensation: str | None,
) -> tuple[str, ...]:
    if _circle_has_quote_arcs(circle_milling):
        return _emit_circle_arc_quote_single_pass(
            circle_milling,
            tool,
            cut_z,
            radius,
            rapid_point,
            start_point,
        )
    if _circle_has_quote_lines(circle_milling):
        return _emit_circle_line_quote_single_pass(
            circle_milling,
            tool,
            cut_z,
            radius,
            rapid_point,
            start_point,
        )
    if _circle_has_down_up_arcs(circle_milling):
        return _emit_circle_arc_down_up_single_pass(
            circle_milling,
            tool,
            cut_z,
            radius,
            rapid_point,
            start_point,
        )
    if _circle_has_down_up_lines(circle_milling):
        return _emit_circle_line_down_up_single_pass(
            circle_milling,
            tool,
            cut_z,
            radius,
            rapid_point,
            start_point,
        )
    if compensation is not None:
        return _emit_circle_compensated_single_pass(
            circle_milling,
            tool,
            cut_z,
            radius,
            rapid_point,
            start_point,
            compensation,
        )
    lines: list[str] = [
        f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
        "?%ETK[7]=4",
    ]
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.append(f"G0 Z{_format_mm(circle_milling.security_plane)}")
    return tuple(lines)


def _emit_circle_compensated_single_pass(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    radius: float,
    rapid_point: tuple[float, float],
    start_point: tuple[float, float],
    compensation: str,
) -> tuple[str, ...]:
    exit_point = _circle_clearance_exit_point(circle_milling, start_point)
    lines: list[str] = [
        "?%ETK[7]=4",
        compensation,
        _format_polyline_xyz_move(
            start_point,
            circle_milling.security_plane,
            tool.plunge_feed,
        ),
        f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
    ]
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.extend(
        [
            f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
            "G40",
            _format_polyline_xyz_move(
                exit_point,
                circle_milling.security_plane,
                tool.milling_feed,
            ),
        ]
    )
    return tuple(lines)


def _emit_circle_line_quote_single_pass(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    radius: float,
    rapid_point: tuple[float, float],
    start_point: tuple[float, float],
) -> tuple[str, ...]:
    exit_point = _circle_lead_exit_point(circle_milling, radius)
    lines: list[str] = [
        "?%ETK[7]=4",
        f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
        _format_polyline_cut_move(
            rapid_point,
            start_point,
            cut_z,
            tool.plunge_feed,
        ),
    ]
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.extend(
        [
            _format_polyline_cut_move(
                start_point,
                exit_point,
                cut_z,
                tool.milling_feed,
            ),
            f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
        ]
    )
    return tuple(lines)


def _emit_circle_line_down_up_single_pass(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    radius: float,
    rapid_point: tuple[float, float],
    start_point: tuple[float, float],
) -> tuple[str, ...]:
    exit_point = _circle_lead_exit_point(circle_milling, radius)
    lines: list[str] = [
        "?%ETK[7]=4",
        _format_polyline_cut_move(
            rapid_point,
            start_point,
            cut_z,
            tool.plunge_feed,
        ),
    ]
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.extend(
        [
            _format_polyline_cut_move(
                start_point,
                exit_point,
                circle_milling.security_plane,
                tool.milling_feed,
            ),
            f"G0 Z{_format_mm(circle_milling.security_plane)}",
        ]
    )
    return tuple(lines)


def _emit_circle_arc_quote_single_pass(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    radius: float,
    rapid_point: tuple[float, float],
    start_point: tuple[float, float],
) -> tuple[str, ...]:
    lead_center = _circle_arc_lead_center(circle_milling, radius)
    exit_point = _circle_lead_exit_point(circle_milling, radius)
    lines: list[str] = [
        "?%ETK[7]=4",
        f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
        _format_arc_move(
            _circle_arc_code(circle_milling),
            start_point,
            lead_center,
            tool.plunge_feed,
        ),
    ]
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.extend(
        [
            _format_arc_move(
                _circle_arc_code(circle_milling),
                exit_point,
                lead_center,
                tool.milling_feed,
            ),
            f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
        ]
    )
    return tuple(lines)


def _emit_circle_arc_down_up_single_pass(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    radius: float,
    rapid_point: tuple[float, float],
    start_point: tuple[float, float],
) -> tuple[str, ...]:
    lead_center = _circle_arc_lead_center(circle_milling, radius)
    exit_point = _circle_lead_exit_point(circle_milling, radius)
    lines: list[str] = [
        "?%ETK[7]=4",
        _format_arc_move(
            _circle_arc_code(circle_milling),
            start_point,
            lead_center,
            tool.plunge_feed,
            z=cut_z,
        ),
    ]
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.extend(
        [
            _format_arc_move(
                _circle_arc_code(circle_milling),
                exit_point,
                lead_center,
                tool.milling_feed,
                z=circle_milling.security_plane,
            ),
            f"G0 Z{_format_mm(circle_milling.security_plane)}",
        ]
    )
    return tuple(lines)


def _emit_circle_strategy_passes(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    radius: float,
    strategy: sp.MillingStrategySpec,
) -> tuple[str, ...]:
    if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        bidirectional = False
        step = abs(float(strategy.axial_cutting_depth))
    elif isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        bidirectional = True
        step = abs(float(strategy.axial_cutting_depth))
    else:
        raise IsoEmissionNotImplemented(
            "Circle milling supports only observed uni/bidirectional strategies."
        )
    lines: list[str] = [
        f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.plunge_feed)}",
        "?%ETK[7]=4",
    ]
    direction = circle_milling.winding
    for depth in _line_milling_pass_depths(final_depth, step):
        lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        lines.extend(
            _emit_circle_full_arcs(
                circle_milling,
                radius,
                tool.milling_feed,
                winding=direction,
            )
        )
        if bidirectional:
            direction = _opposite_winding(direction)
    lines.extend(
        [
            f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
            f"G0 Z{_format_mm(circle_milling.security_plane)}",
        ]
    )
    return tuple(lines)


def _emit_circle_helical_passes(
    circle_milling: sp.CircleMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    radius: float,
    strategy: sp.HelicalMillingStrategySpec,
) -> tuple[str, ...]:
    step = abs(float(strategy.axial_cutting_depth))
    pass_depths = (
        (final_depth,)
        if step <= 0.0
        else _line_milling_pass_depths(final_depth, step)
    )
    lines: list[str] = [
        f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.plunge_feed)}",
        "?%ETK[7]=4",
        f"G1 Z0.000 F{_format_mm(tool.milling_feed)}",
    ]
    current_depth = 0.0
    first_sign = 1.0 if circle_milling.winding == "CounterClockwise" else -1.0
    for depth in pass_depths:
        mid_depth = (current_depth + depth) / 2.0
        first_offset = _circle_helical_center_offset(
            radius,
            mid_depth - current_depth,
            truncate=step <= 0.0,
        )
        second_offset = _circle_helical_center_offset(
            radius,
            depth - mid_depth,
            truncate=step <= 0.0,
        )
        lines.append(
            _format_arc_move(
                _circle_arc_code(circle_milling),
                _circle_mid_point(circle_milling, radius),
                (circle_milling.center_x, circle_milling.center_y + (first_sign * first_offset)),
                tool.milling_feed,
                z=mid_depth,
            )
        )
        lines.append(
            _format_arc_move(
                _circle_arc_code(circle_milling),
                _circle_start_point(circle_milling, radius),
                (circle_milling.center_x, circle_milling.center_y - (first_sign * second_offset)),
                tool.milling_feed,
                z=depth,
            )
        )
        current_depth = depth
    lines.extend(_emit_circle_full_arcs(circle_milling, radius, tool.milling_feed))
    lines.extend(
        [
            f"G1 Z{_format_mm(circle_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
            f"G0 Z{_format_mm(circle_milling.security_plane)}",
        ]
    )
    return tuple(lines)


def _emit_circle_full_arcs(
    circle_milling: sp.CircleMillingSpec,
    radius: float,
    feed: float,
    *,
    winding: str | None = None,
) -> tuple[str, str]:
    code = _circle_arc_code(circle_milling, winding=winding)
    center = (circle_milling.center_x, circle_milling.center_y)
    return (
        _format_arc_move(code, _circle_mid_point(circle_milling, radius), center, feed),
        _format_arc_move(code, _circle_start_point(circle_milling, radius), center, feed),
    )


def _circle_milling_cut_z(
    state: sp.PgmxState,
    circle_milling: sp.CircleMillingSpec,
) -> float:
    if circle_milling.depth_spec.is_through:
        return -(state.depth + circle_milling.depth_spec.extra_depth)
    if circle_milling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Circle milling needs a target depth.")
    return -circle_milling.depth_spec.target_depth


def _circle_toolpath_radius(
    circle_milling: sp.CircleMillingSpec,
    side_offset: float,
) -> float:
    if side_offset == 0.0 or circle_milling.side_of_feature == "Center":
        return circle_milling.radius
    outside = (
        (circle_milling.winding == "CounterClockwise" and circle_milling.side_of_feature == "Right")
        or (circle_milling.winding == "Clockwise" and circle_milling.side_of_feature == "Left")
    )
    return circle_milling.radius + side_offset if outside else circle_milling.radius - side_offset


def _circle_start_point(
    circle_milling: sp.CircleMillingSpec,
    radius: float,
) -> tuple[float, float]:
    return circle_milling.center_x + radius, circle_milling.center_y


def _circle_mid_point(
    circle_milling: sp.CircleMillingSpec,
    radius: float,
) -> tuple[float, float]:
    return circle_milling.center_x - radius, circle_milling.center_y


def _circle_rapid_point(
    circle_milling: sp.CircleMillingSpec,
    radius: float,
    compensation: str | None,
) -> tuple[float, float]:
    start_point = _circle_start_point(circle_milling, radius)
    if _circle_has_quote_arcs(circle_milling) or _circle_has_down_up_arcs(circle_milling):
        lead_center = _circle_arc_lead_center(circle_milling, radius)
        tangent_x, tangent_y = _circle_start_tangent(circle_milling)
        lead_radius = _circle_lead_radius(circle_milling)
        return (
            lead_center[0] - (tangent_x * lead_radius),
            lead_center[1] - (tangent_y * lead_radius),
        )
    if _circle_has_quote_lines(circle_milling) or _circle_has_down_up_lines(circle_milling):
        tangent_x, tangent_y = _circle_start_tangent(circle_milling)
        lead_radius = _circle_lead_radius(circle_milling)
        return (
            start_point[0] - (tangent_x * lead_radius),
            start_point[1] - (tangent_y * lead_radius),
        )
    if compensation is not None:
        tangent_x, tangent_y = _circle_start_tangent(circle_milling)
        return start_point[0] - tangent_x, start_point[1] - tangent_y
    return start_point


def _circle_clearance_exit_point(
    circle_milling: sp.CircleMillingSpec,
    start_point: tuple[float, float],
) -> tuple[float, float]:
    tangent_x, tangent_y = _circle_start_tangent(circle_milling)
    return start_point[0] + tangent_x, start_point[1] + tangent_y


def _circle_lead_exit_point(
    circle_milling: sp.CircleMillingSpec,
    radius: float,
) -> tuple[float, float]:
    start_point = _circle_start_point(circle_milling, radius)
    tangent_x, tangent_y = _circle_start_tangent(circle_milling)
    lead_radius = _circle_lead_radius(circle_milling)
    if _circle_has_quote_arcs(circle_milling) or _circle_has_down_up_arcs(circle_milling):
        lead_center = _circle_arc_lead_center(circle_milling, radius)
        return (
            lead_center[0] + (tangent_x * lead_radius),
            lead_center[1] + (tangent_y * lead_radius),
        )
    return (
        start_point[0] + (tangent_x * lead_radius),
        start_point[1] + (tangent_y * lead_radius),
    )


def _circle_arc_lead_center(
    circle_milling: sp.CircleMillingSpec,
    radius: float,
) -> tuple[float, float]:
    start_point = _circle_start_point(circle_milling, radius)
    lead_radius = _circle_lead_radius(circle_milling)
    return start_point[0] - lead_radius, start_point[1]


def _circle_start_tangent(circle_milling: sp.CircleMillingSpec) -> tuple[float, float]:
    if circle_milling.winding == "CounterClockwise":
        return 0.0, 1.0
    if circle_milling.winding == "Clockwise":
        return 0.0, -1.0
    raise IsoEmissionNotImplemented(
        f"Unsupported circle winding {circle_milling.winding!r}."
    )


def _circle_arc_code(
    circle_milling: sp.CircleMillingSpec,
    *,
    winding: str | None = None,
) -> str:
    resolved = winding or circle_milling.winding
    if resolved == "CounterClockwise":
        return "G3"
    if resolved == "Clockwise":
        return "G2"
    raise IsoEmissionNotImplemented(f"Unsupported circle winding {resolved!r}.")


def _circle_compensation(circle_milling: sp.CircleMillingSpec) -> str | None:
    if circle_milling.side_of_feature == "Left":
        return "G41"
    if circle_milling.side_of_feature == "Right":
        return "G42"
    return None


def _circle_lead_radius(circle_milling: sp.CircleMillingSpec) -> float:
    if circle_milling.approach.is_enabled:
        return (circle_milling.tool_width / 2.0) * circle_milling.approach.radius_multiplier
    return circle_milling.tool_width / 2.0


def _circle_helical_center_offset(
    radius: float,
    delta_z: float,
    *,
    truncate: bool = False,
) -> float:
    offset = (abs(float(delta_z)) ** 2.0) / (8.0 * radius)
    if truncate:
        return int(offset * 1000.0) / 1000.0
    return offset


def _circle_has_leads(circle_milling: sp.CircleMillingSpec) -> bool:
    return circle_milling.approach.is_enabled or circle_milling.retract.is_enabled


def _circle_has_default_leads(circle_milling: sp.CircleMillingSpec) -> bool:
    return not circle_milling.approach.is_enabled and not circle_milling.retract.is_enabled


def _circle_has_quote_lines(circle_milling: sp.CircleMillingSpec) -> bool:
    return _circle_has_line_leads(circle_milling, approach_mode="Quote", retract_mode="Quote")


def _circle_has_down_up_lines(circle_milling: sp.CircleMillingSpec) -> bool:
    return _circle_has_line_leads(circle_milling, approach_mode="Down", retract_mode="Up")


def _circle_has_line_leads(
    circle_milling: sp.CircleMillingSpec,
    *,
    approach_mode: str,
    retract_mode: str,
) -> bool:
    approach = circle_milling.approach
    retract = circle_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Line"
        and retract.retract_type == "Line"
        and approach.mode == approach_mode
        and retract.mode == retract_mode
        and round(float(approach.radius_multiplier), 3) == 2.0
        and round(float(retract.radius_multiplier), 3) == 2.0
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _circle_has_quote_arcs(circle_milling: sp.CircleMillingSpec) -> bool:
    return _circle_has_arc_leads(circle_milling, approach_mode="Quote", retract_mode="Quote")


def _circle_has_down_up_arcs(circle_milling: sp.CircleMillingSpec) -> bool:
    return _circle_has_arc_leads(circle_milling, approach_mode="Down", retract_mode="Up")


def _circle_has_arc_leads(
    circle_milling: sp.CircleMillingSpec,
    *,
    approach_mode: str,
    retract_mode: str,
) -> bool:
    approach = circle_milling.approach
    retract = circle_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Arc"
        and retract.retract_type == "Arc"
        and approach.mode == approach_mode
        and retract.mode == retract_mode
        and approach.arc_side == "Automatic"
        and retract.arc_side == "Automatic"
        and round(float(approach.radius_multiplier), 3) == 2.0
        and round(float(retract.radius_multiplier), 3) == 2.0
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _emit_polyline_milling(
    state: sp.PgmxState,
    polyline_milling: sp.PolylineMillingSpec,
    *,
    include_full_setup: bool = True,
) -> tuple[str, ...]:
    tool = _polyline_milling_tool(polyline_milling)
    rapid_z = polyline_milling.security_plane + tool.tool_offset_length
    cut_z = _polyline_milling_cut_z(state, polyline_milling)
    tool_radius = polyline_milling.tool_width / 2.0
    strategy = polyline_milling.milling_strategy
    first_point = polyline_milling.points[0]
    exit_point = _polyline_exit_point(polyline_milling)
    compensation = None if strategy is not None else _polyline_compensation(polyline_milling)
    if (
        strategy is not None
        and _polyline_is_closed(polyline_milling)
        and _polyline_has_down_up_lines(polyline_milling)
    ):
        rapid_point = _closed_polyline_strategy_rapid_point(polyline_milling)
    else:
        rapid_point = _polyline_rapid_point(polyline_milling, compensation)
    lines: list[str] = [
        "MLV=0",
        f"T{tool.tool_number}",
        "SYN",
        "M06",
    ]
    if include_full_setup:
        lines.append(f"?%ETK[6]={tool.spindle}")
    lines.extend(
        [
            f"?%ETK[9]={tool.tool_code}",
            f"?%ETK[18]={tool.etk18}",
            f"S{_format_spindle_speed(tool.spindle_speed)}M3",
            "G17",
            "MLV=2",
        ]
    )
    if include_full_setup:
        lines.extend(
            [
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
            ]
        )
    else:
        lines.append("?%ETK[13]=1")
    lines.extend(
        [
        f"G0 X{_format_mm(rapid_point[0])} Y{_format_mm(rapid_point[1])}",
        f"G0 Z{_format_mm(rapid_z)}",
        "D1",
        f"SVL {_format_mm(rapid_z - polyline_milling.security_plane)}",
        f"VL6={_format_mm(rapid_z - polyline_milling.security_plane)}",
        f"SVR {_format_mm(tool_radius)}",
            f"VL7={_format_mm(tool_radius)}",
        ]
    )
    if strategy is not None:
        if _polyline_is_closed(polyline_milling) and _polyline_has_down_up_lines(
            polyline_milling
        ):
            lines.extend(
                _emit_closed_polyline_line_strategy_passes(
                    polyline_milling,
                    tool,
                    cut_z,
                    strategy,
                )
            )
        else:
            lines.extend(
                _emit_polyline_strategy_passes(
                    polyline_milling,
                    tool,
                    cut_z,
                    strategy,
                )
            )
    elif _polyline_has_quote_arcs(polyline_milling):
        lines.extend(
            _emit_polyline_arc_lead_single_pass(
                polyline_milling,
                tool,
                cut_z,
                rapid_point,
                compensation,
                quote_mode=True,
            )
        )
    elif _polyline_has_quote_lines(polyline_milling):
        lines.extend(
            _emit_polyline_line_lead_single_pass(
                polyline_milling,
                tool,
                cut_z,
                rapid_point,
                compensation,
                quote_mode=True,
            )
        )
    elif _polyline_has_down_up_arcs(polyline_milling):
        lines.extend(
            _emit_polyline_arc_lead_single_pass(
                polyline_milling,
                tool,
                cut_z,
                rapid_point,
                compensation,
                quote_mode=False,
            )
        )
    elif _polyline_has_down_up_lines(polyline_milling):
        lines.extend(
            _emit_polyline_line_lead_single_pass(
                polyline_milling,
                tool,
                cut_z,
                rapid_point,
                compensation,
                quote_mode=False,
            )
        )
    elif compensation is not None:
        lines.append("?%ETK[7]=4")
        lines.append(compensation)
        lines.append(
            _format_polyline_xyz_move(
                first_point,
                polyline_milling.security_plane,
                tool.plunge_feed,
            )
        )
        lines.append(f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}")
        previous_point = first_point
        for point in polyline_milling.points[1:]:
            lines.append(
                _format_polyline_cut_move(
                    previous_point,
                    point,
                    cut_z,
                    tool.milling_feed,
                    include_z=include_full_setup,
                )
            )
            previous_point = point
        lines.extend(
            [
                f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
                "G40",
                _format_polyline_xyz_move(
                    exit_point,
                    polyline_milling.security_plane,
                    tool.milling_feed,
                ),
            ]
        )
    else:
        lines.extend(
            [
                f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}",
            ]
        )
        if compensation is None:
            lines.append("?%ETK[7]=4")
        previous_point = first_point
        for point in polyline_milling.points[1:]:
            lines.append(
                _format_polyline_cut_move(
                    previous_point,
                    point,
                    cut_z,
                    tool.milling_feed,
                    include_z=include_full_setup,
                )
            )
            previous_point = point
        if compensation is not None:
            lines.extend(
                [
                    f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
                    "G40",
                    _format_polyline_xyz_move(
                        exit_point,
                        polyline_milling.security_plane,
                        tool.milling_feed,
                    ),
                ]
            )
        else:
            lines.append(f"G0 Z{_format_mm(polyline_milling.security_plane)}")
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


def _emit_polyline_strategy_passes(
    polyline_milling: sp.PolylineMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.MillingStrategySpec,
) -> tuple[str, ...]:
    if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        bidirectional = False
        step = abs(float(strategy.axial_cutting_depth))
    elif isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        bidirectional = True
        step = abs(float(strategy.axial_cutting_depth))
    else:
        raise IsoEmissionNotImplemented(
            "Polyline milling supports only observed uni/bidirectional strategies."
        )
    lines: list[str] = [
        f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.plunge_feed)}",
        "?%ETK[7]=4",
    ]
    points = polyline_milling.points
    forward = True
    depths = _line_milling_pass_depths(final_depth, step)
    for index, depth in enumerate(depths):
        lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        pass_points = points if forward else tuple(reversed(points))
        lines.extend(_emit_polyline_path_moves(pass_points, tool.milling_feed))
        is_last = index == len(depths) - 1
        if not bidirectional and not is_last:
            lines.append(
                f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
            )
            lines.extend(
                _emit_polyline_path_moves(
                    tuple(reversed(points)),
                    tool.milling_feed,
                )
            )
        if bidirectional:
            forward = not forward
    lines.extend(
        [
            f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
            f"G0 Z{_format_mm(polyline_milling.security_plane)}",
        ]
    )
    return tuple(lines)


def _emit_closed_polyline_line_strategy_passes(
    polyline_milling: sp.PolylineMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.MillingStrategySpec,
) -> tuple[str, ...]:
    if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        bidirectional = False
        step = abs(float(strategy.axial_cutting_depth))
    elif isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        bidirectional = True
        step = abs(float(strategy.axial_cutting_depth))
    else:
        raise IsoEmissionNotImplemented(
            "Closed polyline milling supports only observed uni/bidirectional strategies."
        )
    lines: list[str] = [
        f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.plunge_feed)}",
        "?%ETK[7]=4",
    ]
    forward = True
    final_path = _closed_polyline_toolpath(polyline_milling, forward=True)
    depths = _line_milling_pass_depths(final_depth, step)
    for index, depth in enumerate(depths):
        path = _closed_polyline_toolpath(polyline_milling, forward=forward)
        if index == 0:
            lead_start = _closed_polyline_strategy_lead_start(path, polyline_milling)
            lines.append(
                _format_polyline_cut_move(
                    lead_start,
                    path.start,
                    depth,
                    tool.milling_feed,
                )
            )
        else:
            lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        lines.extend(_emit_closed_polyline_toolpath_moves(path, depth, tool.milling_feed))
        final_path = path
        if bidirectional:
            forward = not forward
    lead_exit = _closed_polyline_strategy_lead_exit(final_path, polyline_milling)
    lines.extend(
        [
            _format_polyline_cut_move(
                final_path.start,
                lead_exit,
                polyline_milling.security_plane,
                tool.milling_feed,
            ),
            f"G0 Z{_format_mm(polyline_milling.security_plane)}",
        ]
    )
    return tuple(lines)


@dataclass(frozen=True)
class _ClosedPolylinePath:
    start: tuple[float, float]
    tangent: tuple[float, float]
    moves: tuple[tuple[str, tuple[float, float], tuple[float, float] | None], ...]


def _closed_polyline_strategy_rapid_point(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    path = _closed_polyline_toolpath(polyline_milling, forward=True)
    lead = _closed_polyline_strategy_lead_start(path, polyline_milling)
    return lead


def _closed_polyline_strategy_lead_start(
    path: _ClosedPolylinePath,
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    radius = _polyline_lead_radius(polyline_milling)
    tangent_x, tangent_y = path.tangent
    return path.start[0] - (tangent_x * radius), path.start[1] - (tangent_y * radius)


def _closed_polyline_strategy_lead_exit(
    path: _ClosedPolylinePath,
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    radius = _polyline_lead_radius(polyline_milling)
    tangent_x, tangent_y = path.tangent
    return path.start[0] + (tangent_x * radius), path.start[1] + (tangent_y * radius)


def _emit_closed_polyline_toolpath_moves(
    path: _ClosedPolylinePath,
    z: float,
    feed: float,
) -> tuple[str, ...]:
    lines: list[str] = []
    previous = path.start
    for kind, point, center in path.moves:
        if kind == "line":
            lines.append(_format_polyline_cut_move(previous, point, z, feed))
        else:
            assert center is not None
            lines.append(_format_arc_move(kind, point, center, feed))
        previous = point
    return tuple(lines)


def _closed_polyline_toolpath(
    polyline_milling: sp.PolylineMillingSpec,
    *,
    forward: bool,
) -> _ClosedPolylinePath:
    points = polyline_milling.points if forward else tuple(reversed(polyline_milling.points))
    tangent = _unit_vector(points[0], points[1])
    tool_radius = polyline_milling.tool_width / 2.0
    if polyline_milling.side_of_feature == "Center":
        return _ClosedPolylinePath(
            start=points[0],
            tangent=tangent,
            moves=tuple(("line", point, None) for point in points[1:]),
        )
    if _closed_polyline_uses_outside_offset(points, polyline_milling.side_of_feature):
        return _closed_polyline_outside_toolpath(points, polyline_milling.side_of_feature, tool_radius)
    return _closed_polyline_inside_toolpath(points, polyline_milling.side_of_feature, tool_radius)


def _closed_polyline_outside_toolpath(
    points: tuple[tuple[float, float], ...],
    side_of_feature: str,
    tool_radius: float,
) -> _ClosedPolylinePath:
    normals = _closed_polyline_side_normals(points, side_of_feature)
    tangent = _unit_vector(points[0], points[1])
    start = _offset_point(points[0], normals[0], tool_radius)
    arc_code = "G3" if _closed_polyline_signed_area(points) > 0.0 else "G2"
    moves: list[tuple[str, tuple[float, float], tuple[float, float] | None]] = []
    for index in range(len(points) - 1):
        end_point = points[index + 1]
        line_end = _offset_point(end_point, normals[index], tool_radius)
        moves.append(("line", line_end, None))
        if index + 1 < len(points) - 1:
            arc_end = _offset_point(end_point, normals[index + 1], tool_radius)
            moves.append((arc_code, arc_end, end_point))
    return _ClosedPolylinePath(start=start, tangent=tangent, moves=tuple(moves))


def _closed_polyline_inside_toolpath(
    points: tuple[tuple[float, float], ...],
    side_of_feature: str,
    tool_radius: float,
) -> _ClosedPolylinePath:
    normals = _closed_polyline_side_normals(points, side_of_feature)
    tangent = _unit_vector(points[0], points[1])
    start = _offset_point(points[0], normals[0], tool_radius)
    moves: list[tuple[str, tuple[float, float], tuple[float, float] | None]] = []
    for index in range(len(points) - 1):
        end_point = points[index + 1]
        if index + 1 < len(points) - 1:
            point = _offset_line_intersection(
                points[index],
                points[index + 1],
                normals[index],
                points[index + 1],
                points[index + 2],
                normals[index + 1],
                tool_radius,
            )
        else:
            point = start
        moves.append(("line", point, None))
    return _ClosedPolylinePath(start=start, tangent=tangent, moves=tuple(moves))


def _closed_polyline_side_normals(
    points: tuple[tuple[float, float], ...],
    side_of_feature: str,
) -> tuple[tuple[float, float], ...]:
    normals: list[tuple[float, float]] = []
    for index in range(len(points) - 1):
        unit_x, unit_y = _unit_vector(points[index], points[index + 1])
        if side_of_feature == "Left":
            normals.append((-unit_y, unit_x))
        elif side_of_feature == "Right":
            normals.append((unit_y, -unit_x))
        else:
            raise IsoEmissionNotImplemented(
                f"Unsupported polyline side {side_of_feature!r}."
            )
    return tuple(normals)


def _closed_polyline_uses_outside_offset(
    points: tuple[tuple[float, float], ...],
    side_of_feature: str,
) -> bool:
    area = _closed_polyline_signed_area(points)
    return (area > 0.0 and side_of_feature == "Right") or (
        area < 0.0 and side_of_feature == "Left"
    )


def _closed_polyline_signed_area(points: tuple[tuple[float, float], ...]) -> float:
    area = 0.0
    for first, second in zip(points, points[1:]):
        area += (first[0] * second[1]) - (second[0] * first[1])
    return area / 2.0


def _offset_point(
    point: tuple[float, float],
    normal: tuple[float, float],
    distance: float,
) -> tuple[float, float]:
    return point[0] + (normal[0] * distance), point[1] + (normal[1] * distance)


def _offset_line_intersection(
    first_start: tuple[float, float],
    first_end: tuple[float, float],
    first_normal: tuple[float, float],
    second_start: tuple[float, float],
    second_end: tuple[float, float],
    second_normal: tuple[float, float],
    distance: float,
) -> tuple[float, float]:
    p = _offset_point(first_start, first_normal, distance)
    r = (first_end[0] - first_start[0], first_end[1] - first_start[1])
    q = _offset_point(second_start, second_normal, distance)
    s = (second_end[0] - second_start[0], second_end[1] - second_start[1])
    cross = (r[0] * s[1]) - (r[1] * s[0])
    if abs(cross) <= 1e-9:
        raise IsoEmissionNotImplemented("Closed polyline has parallel consecutive segments.")
    qmp = (q[0] - p[0], q[1] - p[1])
    t = ((qmp[0] * s[1]) - (qmp[1] * s[0])) / cross
    return p[0] + (t * r[0]), p[1] + (t * r[1])


def _emit_polyline_path_moves(
    points: tuple[tuple[float, float], ...],
    feed: float,
    *,
    z: float = 0.0,
    include_z: bool = False,
) -> tuple[str, ...]:
    lines: list[str] = []
    previous = points[0]
    for point in points[1:]:
        lines.append(
            _format_polyline_cut_move(
                previous,
                point,
                z,
                feed,
                include_z=include_z,
            )
        )
        previous = point
    return tuple(lines)


def _emit_polyline_line_lead_single_pass(
    polyline_milling: sp.PolylineMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    rapid_point: tuple[float, float],
    compensation: str | None,
    *,
    quote_mode: bool,
) -> tuple[str, ...]:
    first_point = polyline_milling.points[0]
    lead_start = _polyline_line_lead_start(polyline_milling)
    lead_exit = _polyline_line_lead_exit(polyline_milling)
    closed = _polyline_is_closed(polyline_milling)
    lines: list[str] = ["?%ETK[7]=4"]
    if compensation is not None:
        lines.extend(
            [
                compensation,
                _format_polyline_xyz_move(
                    lead_start,
                    polyline_milling.security_plane,
                    tool.plunge_feed,
                ),
            ]
        )
    if quote_mode:
        lines.append(f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}")
        lines.append(
            _format_polyline_cut_move(
                lead_start,
                first_point,
                cut_z,
                tool.plunge_feed,
                include_z=closed,
            )
        )
    else:
        lines.append(
            _format_polyline_cut_move(
                lead_start,
                first_point,
                cut_z,
                tool.plunge_feed,
            )
        )
    lines.extend(
        _emit_polyline_path_moves(
            polyline_milling.points,
            tool.milling_feed,
            z=cut_z,
            include_z=closed,
        )
    )
    if quote_mode:
        lines.extend(
            [
                _format_polyline_cut_move(
                    polyline_milling.points[-1],
                    lead_exit,
                    cut_z,
                    tool.milling_feed,
                    include_z=closed,
                ),
                f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
            ]
        )
    else:
        lines.append(
            _format_polyline_cut_move(
                polyline_milling.points[-1],
                lead_exit,
                polyline_milling.security_plane,
                tool.milling_feed,
            )
        )
        if compensation is None:
            lines.append(f"G0 Z{_format_mm(polyline_milling.security_plane)}")
    if compensation is not None:
        lines.extend(
            [
                "G40",
                _format_polyline_xyz_move(
                    _polyline_line_compensation_exit(polyline_milling),
                    polyline_milling.security_plane,
                    tool.milling_feed,
                ),
            ]
        )
    return tuple(lines)


def _emit_polyline_arc_lead_single_pass(
    polyline_milling: sp.PolylineMillingSpec,
    tool: _LineMillingTool,
    cut_z: float,
    rapid_point: tuple[float, float],
    compensation: str | None,
    *,
    quote_mode: bool,
) -> tuple[str, ...]:
    first_point = polyline_milling.points[0]
    arc_start = _polyline_arc_lead_start(polyline_milling)
    entry_center = _polyline_arc_entry_center(polyline_milling)
    exit_center = _polyline_arc_exit_center(polyline_milling)
    arc_exit = _polyline_arc_lead_exit(polyline_milling)
    arc_code = _polyline_arc_lead_code(polyline_milling)
    closed = _polyline_is_closed(polyline_milling)
    lines: list[str] = ["?%ETK[7]=4"]
    if compensation is not None:
        lines.extend(
            [
                compensation,
                _format_polyline_xyz_move(
                    arc_start,
                    polyline_milling.security_plane,
                    tool.plunge_feed,
                ),
            ]
        )
    if quote_mode:
        lines.append(f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}")
        lines.append(_format_arc_move(arc_code, first_point, entry_center, tool.plunge_feed))
    else:
        lines.append(
            _format_arc_move(
                arc_code,
                first_point,
                entry_center,
                tool.plunge_feed,
                z=cut_z,
            )
        )
    lines.extend(
        _emit_polyline_path_moves(
            polyline_milling.points,
            tool.milling_feed,
            z=cut_z,
            include_z=closed,
        )
    )
    if quote_mode:
        lines.extend(
            [
                _format_arc_move(
                    arc_code,
                    arc_exit,
                    exit_center,
                    tool.milling_feed,
                ),
                f"G1 Z{_format_mm(polyline_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
            ]
        )
    else:
        lines.append(
            _format_arc_move(
                arc_code,
                arc_exit,
                exit_center,
                tool.milling_feed,
                z=polyline_milling.security_plane,
            )
        )
        if compensation is None:
            lines.append(f"G0 Z{_format_mm(polyline_milling.security_plane)}")
    if compensation is not None:
        lines.extend(
            [
                "G40",
                _format_polyline_xyz_move(
                    _polyline_arc_compensation_exit(polyline_milling),
                    polyline_milling.security_plane,
                    tool.milling_feed,
                ),
            ]
        )
    return tuple(lines)


def _emit_top_profile_milling_transition(
    next_operation: _TopProfileOperation,
) -> tuple[str, ...]:
    lines: list[str] = []
    if (
        isinstance(next_operation, sp.PolylineMillingSpec)
        and next_operation.milling_strategy is None
        and (
            _polyline_compensation(next_operation) is not None
            or _polyline_has_leads(next_operation)
        )
    ) or (
        isinstance(next_operation, sp.CircleMillingSpec)
        and (
            (
                next_operation.milling_strategy is None
                and _circle_compensation(next_operation) is not None
            )
            or _circle_has_leads(next_operation)
        )
    ) or (
        isinstance(next_operation, sp.LineMillingSpec)
        and next_operation.milling_strategy is None
    ):
        lines.append("?%ETK[7]=0")
    lines.extend(
        [
            "MLV=0",
            _safe_z_line(),
            "MLV=2",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            "M5",
            "MLV=0",
            _safe_z_line(),
        ]
    )
    return tuple(lines)


def _polyline_milling_cut_z(
    state: sp.PgmxState,
    polyline_milling: sp.PolylineMillingSpec,
) -> float:
    if polyline_milling.depth_spec.is_through:
        return -(state.depth + polyline_milling.depth_spec.extra_depth)
    if polyline_milling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Polyline milling needs a target depth.")
    return -polyline_milling.depth_spec.target_depth


def _polyline_entry_point(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    first_point = polyline_milling.points[0]
    if _polyline_compensation(polyline_milling) is None:
        return first_point
    unit_x, unit_y = _unit_vector(first_point, polyline_milling.points[1])
    return first_point[0] - unit_x, first_point[1] - unit_y


def _polyline_rapid_point(
    polyline_milling: sp.PolylineMillingSpec,
    compensation: str | None,
) -> tuple[float, float]:
    if _polyline_has_quote_arcs(polyline_milling) or _polyline_has_down_up_arcs(polyline_milling):
        arc_start = _polyline_arc_lead_start(polyline_milling)
        if compensation is None:
            return arc_start
        normal_x, normal_y = _polyline_first_right_normal(polyline_milling)
        side = _polyline_arc_side_sign(polyline_milling)
        return arc_start[0] + (normal_x * side), arc_start[1] + (normal_y * side)
    if _polyline_has_quote_lines(polyline_milling) or _polyline_has_down_up_lines(polyline_milling):
        lead_start = _polyline_line_lead_start(polyline_milling)
        if compensation is None:
            return lead_start
        tangent_x, tangent_y = _polyline_first_tangent(polyline_milling)
        return lead_start[0] - tangent_x, lead_start[1] - tangent_y
    return _polyline_entry_point(polyline_milling)


def _polyline_exit_point(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    previous_point = polyline_milling.points[-2]
    last_point = polyline_milling.points[-1]
    unit_x, unit_y = _unit_vector(previous_point, last_point)
    return last_point[0] + unit_x, last_point[1] + unit_y


def _polyline_first_tangent(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    return _unit_vector(polyline_milling.points[0], polyline_milling.points[1])


def _polyline_last_tangent(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    return _unit_vector(polyline_milling.points[-2], polyline_milling.points[-1])


def _polyline_first_right_normal(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    tangent_x, tangent_y = _polyline_first_tangent(polyline_milling)
    return tangent_y, -tangent_x


def _polyline_last_right_normal(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    tangent_x, tangent_y = _polyline_last_tangent(polyline_milling)
    return tangent_y, -tangent_x


def _polyline_lead_radius(polyline_milling: sp.PolylineMillingSpec) -> float:
    if polyline_milling.approach.is_enabled:
        return (polyline_milling.tool_width / 2.0) * polyline_milling.approach.radius_multiplier
    return polyline_milling.tool_width / 2.0


def _polyline_line_lead_start(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    first_point = polyline_milling.points[0]
    tangent_x, tangent_y = _polyline_first_tangent(polyline_milling)
    radius = _polyline_lead_radius(polyline_milling)
    return first_point[0] - (tangent_x * radius), first_point[1] - (tangent_y * radius)


def _polyline_line_lead_exit(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    last_point = polyline_milling.points[-1]
    tangent_x, tangent_y = _polyline_last_tangent(polyline_milling)
    radius = _polyline_lead_radius(polyline_milling)
    return last_point[0] + (tangent_x * radius), last_point[1] + (tangent_y * radius)


def _polyline_line_compensation_exit(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    lead_exit = _polyline_line_lead_exit(polyline_milling)
    tangent_x, tangent_y = _polyline_last_tangent(polyline_milling)
    return lead_exit[0] + tangent_x, lead_exit[1] + tangent_y


def _polyline_arc_side_sign(polyline_milling: sp.PolylineMillingSpec) -> float:
    return 1.0 if polyline_milling.side_of_feature == "Right" else -1.0


def _polyline_arc_lead_code(polyline_milling: sp.PolylineMillingSpec) -> str:
    return "G2" if _polyline_arc_side_sign(polyline_milling) > 0.0 else "G3"


def _polyline_arc_entry_center(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    first_point = polyline_milling.points[0]
    normal_x, normal_y = _polyline_first_right_normal(polyline_milling)
    radius = _polyline_lead_radius(polyline_milling)
    side = _polyline_arc_side_sign(polyline_milling)
    return first_point[0] + (normal_x * side * radius), first_point[1] + (normal_y * side * radius)


def _polyline_arc_exit_center(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    last_point = polyline_milling.points[-1]
    normal_x, normal_y = _polyline_last_right_normal(polyline_milling)
    radius = _polyline_lead_radius(polyline_milling)
    side = _polyline_arc_side_sign(polyline_milling)
    return last_point[0] + (normal_x * side * radius), last_point[1] + (normal_y * side * radius)


def _polyline_arc_lead_start(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    center = _polyline_arc_entry_center(polyline_milling)
    tangent_x, tangent_y = _polyline_first_tangent(polyline_milling)
    radius = _polyline_lead_radius(polyline_milling)
    return center[0] - (tangent_x * radius), center[1] - (tangent_y * radius)


def _polyline_arc_lead_exit(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    center = _polyline_arc_exit_center(polyline_milling)
    tangent_x, tangent_y = _polyline_last_tangent(polyline_milling)
    radius = _polyline_lead_radius(polyline_milling)
    return center[0] + (tangent_x * radius), center[1] + (tangent_y * radius)


def _polyline_arc_compensation_exit(
    polyline_milling: sp.PolylineMillingSpec,
) -> tuple[float, float]:
    arc_exit = _polyline_arc_lead_exit(polyline_milling)
    normal_x, normal_y = _polyline_last_right_normal(polyline_milling)
    side = _polyline_arc_side_sign(polyline_milling)
    return arc_exit[0] + (normal_x * side), arc_exit[1] + (normal_y * side)


def _unit_vector(
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float]:
    dx = float(end[0]) - float(start[0])
    dy = float(end[1]) - float(start[1])
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 1e-9:
        raise IsoEmissionNotImplemented("Polyline milling has duplicate consecutive points.")
    return dx / length, dy / length


def _polyline_compensation(polyline_milling: sp.PolylineMillingSpec) -> str | None:
    if polyline_milling.side_of_feature == "Left":
        return "G41"
    if polyline_milling.side_of_feature == "Right":
        return "G42"
    return None


def _polyline_has_leads(polyline_milling: sp.PolylineMillingSpec) -> bool:
    return polyline_milling.approach.is_enabled or polyline_milling.retract.is_enabled


def _polyline_has_default_leads(polyline_milling: sp.PolylineMillingSpec) -> bool:
    return not polyline_milling.approach.is_enabled and not polyline_milling.retract.is_enabled


def _polyline_has_quote_lines(polyline_milling: sp.PolylineMillingSpec) -> bool:
    return _polyline_has_line_leads(polyline_milling, approach_mode="Quote", retract_mode="Quote")


def _polyline_has_down_up_lines(polyline_milling: sp.PolylineMillingSpec) -> bool:
    return _polyline_has_line_leads(polyline_milling, approach_mode="Down", retract_mode="Up")


def _polyline_has_line_leads(
    polyline_milling: sp.PolylineMillingSpec,
    *,
    approach_mode: str,
    retract_mode: str,
) -> bool:
    approach = polyline_milling.approach
    retract = polyline_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Line"
        and retract.retract_type == "Line"
        and approach.mode == approach_mode
        and retract.mode == retract_mode
        and round(float(approach.radius_multiplier), 3) in {2.0, 4.0}
        and round(float(retract.radius_multiplier), 3) in {2.0, 4.0}
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _polyline_has_quote_arcs(polyline_milling: sp.PolylineMillingSpec) -> bool:
    return _polyline_has_arc_leads(polyline_milling, approach_mode="Quote", retract_mode="Quote")


def _polyline_has_down_up_arcs(polyline_milling: sp.PolylineMillingSpec) -> bool:
    return _polyline_has_arc_leads(polyline_milling, approach_mode="Down", retract_mode="Up")


def _polyline_has_arc_leads(
    polyline_milling: sp.PolylineMillingSpec,
    *,
    approach_mode: str,
    retract_mode: str,
) -> bool:
    approach = polyline_milling.approach
    retract = polyline_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Arc"
        and retract.retract_type == "Arc"
        and approach.mode == approach_mode
        and retract.mode == retract_mode
        and approach.arc_side == "Automatic"
        and retract.arc_side == "Automatic"
        and round(float(approach.radius_multiplier), 3) == 2.0
        and round(float(retract.radius_multiplier), 3) == 2.0
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _polyline_is_closed(polyline_milling: sp.PolylineMillingSpec) -> bool:
    first_point = polyline_milling.points[0]
    last_point = polyline_milling.points[-1]
    return (
        round(float(first_point[0]), 3) == round(float(last_point[0]), 3)
        and round(float(first_point[1]), 3) == round(float(last_point[1]), 3)
    )


def _format_polyline_xyz_move(
    point: tuple[float, float],
    z: float,
    feed: float,
) -> str:
    return (
        f"G1 X{_format_mm(point[0])} "
        f"Y{_format_mm(point[1])} "
        f"Z{_format_mm(z)} "
        f"F{_format_mm(feed)}"
    )


def _format_polyline_cut_move(
    previous: tuple[float, float],
    current: tuple[float, float],
    z: float,
    feed: float,
    *,
    include_z: bool = True,
) -> str:
    axes: list[str] = []
    if round(float(previous[0]), 3) != round(float(current[0]), 3):
        axes.append(f"X{_format_mm(current[0])}")
    if round(float(previous[1]), 3) != round(float(current[1]), 3):
        axes.append(f"Y{_format_mm(current[1])}")
    if not axes:
        raise IsoEmissionNotImplemented("Polyline milling has duplicate consecutive points.")
    if include_z:
        axes.append(f"Z{_format_mm(z)}")
    return f"G1 {' '.join(axes)} F{_format_mm(feed)}"


def _emit_squaring_milling(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
) -> tuple[str, ...]:
    tool = _squaring_milling_tool(squaring_milling)
    rapid_z = squaring_milling.security_plane + tool.tool_offset_length
    cut_z = _squaring_milling_cut_z(state, squaring_milling)
    tool_radius = squaring_milling.tool_width / 2.0
    points = _squaring_points(state, squaring_milling)
    first_point = points[0]
    has_quote_arcs = _squaring_has_quote_arcs(squaring_milling)
    has_quote_lines = _squaring_has_quote_lines(squaring_milling)
    has_down_up_arcs = _squaring_has_down_up_arcs(squaring_milling)
    has_down_up_lines = _squaring_has_down_up_lines(squaring_milling)
    strategy = squaring_milling.milling_strategy
    if strategy is not None:
        rapid_point = _squaring_strategy_rapid_point(squaring_milling, tool_radius)
        lead_point = first_point
        exit_arc_point = None
        exit_point = first_point
        arc_center = first_point
        arc_code = None
    elif has_quote_arcs or has_down_up_arcs:
        arc_radius = _squaring_arc_radius(squaring_milling)
        arc_center = _squaring_arc_center(state, squaring_milling, arc_radius)
        rapid_point = _squaring_arc_rapid_point(
            state,
            squaring_milling,
            arc_center,
            arc_radius,
        )
        lead_point = _squaring_arc_lead_point(
            state,
            squaring_milling,
            arc_center,
            arc_radius,
        )
        exit_arc_point = _squaring_arc_exit_point(
            state,
            squaring_milling,
            arc_center,
            arc_radius,
        )
        exit_point = _squaring_arc_clearance_point(squaring_milling, exit_arc_point)
        arc_code = _squaring_arc_code(squaring_milling)
    elif has_quote_lines or has_down_up_lines:
        line_radius = _squaring_arc_radius(squaring_milling)
        rapid_point = _squaring_line_rapid_point(points, line_radius)
        lead_point = _squaring_line_lead_point(points, line_radius)
        exit_arc_point = _squaring_line_exit_lead_point(points, line_radius)
        exit_point = _squaring_line_clearance_point(points, line_radius)
        arc_center = first_point
        arc_code = None
    else:
        rapid_point = _squaring_entry_point(points)
        lead_point = first_point
        exit_arc_point = None
        exit_point = _squaring_exit_point(points)
        arc_code = None
    compensation = _squaring_compensation(squaring_milling)
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
        f"G0 X{_format_mm(rapid_point[0])} Y{_format_mm(rapid_point[1])}",
        f"G0 Z{_format_mm(rapid_z)}",
        "D1",
        f"SVL {_format_mm(tool.tool_offset_length)}",
        f"VL6={_format_mm(tool.tool_offset_length)}",
        f"SVR {_format_mm(tool_radius)}",
        f"VL7={_format_mm(tool_radius)}",
    ]
    if strategy is not None:
        lines.extend(
            [
                f"G1 Z{_format_mm(squaring_milling.security_plane)} F{_format_mm(tool.plunge_feed)}",
                "?%ETK[7]=4",
                *_emit_squaring_strategy_passes(
                    state,
                    squaring_milling,
                    tool,
                    cut_z,
                    strategy,
                ),
                f"G0 Z{_format_mm(squaring_milling.security_plane)}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                "SVR 0.000",
                "VL7=0.000",
                "?%ETK[7]=0",
            ]
        )
        return tuple(lines)
    lines.extend(
        [
            "?%ETK[7]=4",
            compensation,
            _format_polyline_xyz_move(
                lead_point,
                squaring_milling.security_plane,
                tool.plunge_feed,
            ),
        ]
    )
    if has_down_up_arcs and arc_code is not None:
        lines.append(
            _format_arc_move(
                arc_code,
                first_point,
                arc_center,
                tool.plunge_feed,
                z=cut_z,
            )
        )
    elif has_down_up_lines:
        lines.append(
            _format_polyline_cut_move(
                lead_point,
                first_point,
                cut_z,
                tool.plunge_feed,
            )
        )
    else:
        lines.append(f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.plunge_feed)}")
    if has_quote_arcs and arc_code is not None:
        lines.append(
            _format_arc_move(
                arc_code,
                first_point,
                arc_center,
                tool.plunge_feed,
            )
        )
    elif has_quote_lines:
        lines.append(
            _format_polyline_cut_move(
                lead_point,
                first_point,
                cut_z,
                tool.plunge_feed,
            )
        )
    previous_point = first_point
    for point in points[1:]:
        lines.append(
            _format_polyline_cut_move(
                previous_point,
                point,
                cut_z,
                tool.milling_feed,
            )
        )
        previous_point = point
    if has_quote_arcs and arc_code is not None and exit_arc_point is not None:
        lines.append(
            _format_arc_move(
                arc_code,
                exit_arc_point,
                arc_center,
                tool.milling_feed,
            )
        )
    elif has_quote_lines and exit_arc_point is not None:
        lines.append(
            _format_polyline_cut_move(
                previous_point,
                exit_arc_point,
                cut_z,
                tool.milling_feed,
            )
        )
    elif has_down_up_arcs and arc_code is not None and exit_arc_point is not None:
        lines.append(
            _format_arc_move(
                arc_code,
                exit_arc_point,
                arc_center,
                tool.milling_feed,
                z=squaring_milling.security_plane,
            )
        )
    elif has_down_up_lines and exit_arc_point is not None:
        lines.append(
            _format_polyline_cut_move(
                previous_point,
                exit_arc_point,
                squaring_milling.security_plane,
                tool.milling_feed,
            )
        )
    if not (has_down_up_arcs or has_down_up_lines):
        lines.append(
            f"G1 Z{_format_mm(squaring_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
        )
    lines.extend(
        [
            "G40",
            _format_polyline_xyz_move(
                exit_point,
                squaring_milling.security_plane,
                tool.milling_feed,
            ),
            "D0",
            "SVL 0.000",
            "VL6=0.000",
            "SVR 0.000",
            "VL7=0.000",
            "?%ETK[7]=0",
        ]
    )
    return tuple(lines)


def _squaring_strategy_rapid_point(
    squaring_milling: sp.SquaringMillingSpec,
    tool_radius: float,
) -> tuple[float, float]:
    start_x = _squaring_start_x(squaring_milling)
    if squaring_milling.winding == "CounterClockwise":
        return start_x - tool_radius, -(2.0 * tool_radius)
    if squaring_milling.winding == "Clockwise":
        return start_x + tool_radius, -(2.0 * tool_radius)
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring winding {squaring_milling.winding!r}."
    )


def _emit_squaring_strategy_passes(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
    tool: _LineMillingTool,
    final_depth: float,
    strategy: sp.MillingStrategySpec,
) -> tuple[str, ...]:
    if isinstance(strategy, sp.UnidirectionalMillingStrategySpec):
        bidirectional = False
        step = abs(float(strategy.axial_cutting_depth))
    elif isinstance(strategy, sp.BidirectionalMillingStrategySpec):
        bidirectional = True
        step = abs(float(strategy.axial_cutting_depth))
    else:
        raise IsoEmissionNotImplemented(
            "Squaring supports only observed uni/bidirectional strategies."
        )
    lines: list[str] = []
    depths = _line_milling_pass_depths(final_depth, step)
    direction = squaring_milling.winding
    final_direction = direction
    for index, depth in enumerate(depths):
        lines.append(f"G1 Z{_format_mm(depth)} F{_format_mm(tool.milling_feed)}")
        if index == 0:
            lines.append(
                _format_arc_move(
                    _squaring_strategy_entry_arc_code(squaring_milling),
                    _squaring_strategy_start_point(squaring_milling),
                    _squaring_strategy_entry_center(squaring_milling),
                    tool.milling_feed,
                )
            )
        lines.extend(
            _emit_squaring_strategy_contour(
                state,
                squaring_milling,
                direction,
                depth,
                tool.milling_feed,
            )
        )
        final_direction = direction
        if bidirectional:
            direction = _opposite_winding(direction)
    lines.append(
        _format_arc_move(
            _squaring_strategy_exit_arc_code(
                squaring_milling,
                final_direction,
                bidirectional,
            ),
            _squaring_strategy_exit_point(
                squaring_milling,
                final_direction,
                bidirectional,
            ),
            _squaring_strategy_exit_center(
                squaring_milling,
                final_direction,
                bidirectional,
            ),
            tool.milling_feed,
        )
    )
    lines.append(
        f"G1 Z{_format_mm(squaring_milling.security_plane)} F{_format_mm(tool.milling_feed)}"
    )
    return tuple(lines)


def _emit_squaring_strategy_contour(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
    direction: str,
    z: float,
    feed: float,
) -> tuple[str, ...]:
    tool_radius = squaring_milling.tool_width / 2.0
    start_x = _squaring_start_x(squaring_milling)
    length = state.length
    width = state.width
    start = (start_x, -tool_radius)
    if direction == "CounterClockwise":
        moves: tuple[tuple[str, tuple[float, float], tuple[float, float] | None], ...] = (
            ("line", (length, -tool_radius), None),
            ("arc_g3", (length + tool_radius, 0.0), (length, 0.0)),
            ("line", (length + tool_radius, width), None),
            ("arc_g3", (length, width + tool_radius), (length, width)),
            ("line", (0.0, width + tool_radius), None),
            ("arc_g3", (-tool_radius, width), (0.0, width)),
            ("line", (-tool_radius, 0.0), None),
            ("arc_g3", (0.0, -tool_radius), (0.0, 0.0)),
            ("line", start, None),
        )
    elif direction == "Clockwise":
        moves = (
            ("line", (0.0, -tool_radius), None),
            ("arc_g2", (-tool_radius, 0.0), (0.0, 0.0)),
            ("line", (-tool_radius, width), None),
            ("arc_g2", (0.0, width + tool_radius), (0.0, width)),
            ("line", (length, width + tool_radius), None),
            ("arc_g2", (length + tool_radius, width), (length, width)),
            ("line", (length + tool_radius, 0.0), None),
            ("arc_g2", (length, -tool_radius), (length, 0.0)),
            ("line", start, None),
        )
    else:
        raise IsoEmissionNotImplemented(f"Unsupported squaring winding {direction!r}.")

    lines: list[str] = []
    previous = start
    for kind, point, center in moves:
        if kind == "line":
            lines.append(_format_polyline_cut_move(previous, point, z, feed))
        else:
            assert center is not None
            code = "G3" if kind == "arc_g3" else "G2"
            lines.append(_format_arc_move(code, point, center, feed))
        previous = point
    return tuple(lines)


def _squaring_strategy_entry_arc_code(
    squaring_milling: sp.SquaringMillingSpec,
) -> str:
    if squaring_milling.winding == "CounterClockwise":
        return "G2"
    if squaring_milling.winding == "Clockwise":
        return "G3"
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring winding {squaring_milling.winding!r}."
    )


def _squaring_strategy_start_point(
    squaring_milling: sp.SquaringMillingSpec,
) -> tuple[float, float]:
    return _squaring_start_x(squaring_milling), -(squaring_milling.tool_width / 2.0)


def _squaring_strategy_entry_center(
    squaring_milling: sp.SquaringMillingSpec,
) -> tuple[float, float]:
    return _squaring_start_x(squaring_milling), -squaring_milling.tool_width


def _squaring_strategy_exit_arc_code(
    squaring_milling: sp.SquaringMillingSpec,
    final_direction: str,
    bidirectional: bool,
) -> str:
    if bidirectional and final_direction != squaring_milling.winding:
        if final_direction == "CounterClockwise":
            return "G3"
        if final_direction == "Clockwise":
            return "G2"
    return _squaring_strategy_entry_arc_code(squaring_milling)


def _squaring_strategy_exit_point(
    squaring_milling: sp.SquaringMillingSpec,
    final_direction: str,
    bidirectional: bool,
) -> tuple[float, float]:
    start_x = _squaring_start_x(squaring_milling)
    tool_radius = squaring_milling.tool_width / 2.0
    if bidirectional and final_direction != squaring_milling.winding:
        if final_direction == "CounterClockwise":
            return start_x + tool_radius, 0.0
        if final_direction == "Clockwise":
            return start_x - tool_radius, 0.0
    if squaring_milling.winding == "CounterClockwise":
        return start_x + tool_radius, -squaring_milling.tool_width
    if squaring_milling.winding == "Clockwise":
        return start_x - tool_radius, -squaring_milling.tool_width
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring winding {squaring_milling.winding!r}."
    )


def _squaring_strategy_exit_center(
    squaring_milling: sp.SquaringMillingSpec,
    final_direction: str,
    bidirectional: bool,
) -> tuple[float, float]:
    if bidirectional and final_direction != squaring_milling.winding:
        return _squaring_start_x(squaring_milling), 0.0
    return _squaring_strategy_entry_center(squaring_milling)


def _squaring_start_x(squaring_milling: sp.SquaringMillingSpec) -> float:
    coordinate = getattr(squaring_milling, "start_coordinate", None)
    if coordinate is not None:
        return float(coordinate)
    return 0.0


def _opposite_winding(winding: str) -> str:
    if winding == "CounterClockwise":
        return "Clockwise"
    if winding == "Clockwise":
        return "CounterClockwise"
    raise IsoEmissionNotImplemented(f"Unsupported squaring winding {winding!r}.")


def _squaring_has_default_leads(squaring_milling: sp.SquaringMillingSpec) -> bool:
    return not squaring_milling.approach.is_enabled and not squaring_milling.retract.is_enabled


def _squaring_has_quote_arcs(squaring_milling: sp.SquaringMillingSpec) -> bool:
    return _squaring_has_arc_leads(
        squaring_milling,
        approach_mode="Quote",
        retract_mode="Quote",
    )


def _squaring_has_down_up_arcs(squaring_milling: sp.SquaringMillingSpec) -> bool:
    return _squaring_has_arc_leads(
        squaring_milling,
        approach_mode="Down",
        retract_mode="Up",
    )


def _squaring_has_arc_leads(
    squaring_milling: sp.SquaringMillingSpec,
    *,
    approach_mode: str,
    retract_mode: str,
) -> bool:
    approach = squaring_milling.approach
    retract = squaring_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Arc"
        and retract.retract_type == "Arc"
        and approach.mode == approach_mode
        and retract.mode == retract_mode
        and approach.arc_side == "Automatic"
        and retract.arc_side == "Automatic"
        and round(float(approach.radius_multiplier), 3) == 2.0
        and round(float(retract.radius_multiplier), 3) == 2.0
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _squaring_has_quote_lines(squaring_milling: sp.SquaringMillingSpec) -> bool:
    return _squaring_has_line_leads(
        squaring_milling,
        approach_mode="Quote",
        retract_mode="Quote",
    )


def _squaring_has_down_up_lines(squaring_milling: sp.SquaringMillingSpec) -> bool:
    return _squaring_has_line_leads(
        squaring_milling,
        approach_mode="Down",
        retract_mode="Up",
    )


def _squaring_has_line_leads(
    squaring_milling: sp.SquaringMillingSpec,
    *,
    approach_mode: str,
    retract_mode: str,
) -> bool:
    approach = squaring_milling.approach
    retract = squaring_milling.retract
    return (
        approach.is_enabled
        and retract.is_enabled
        and approach.approach_type == "Line"
        and retract.retract_type == "Line"
        and approach.mode == approach_mode
        and retract.mode == retract_mode
        and round(float(approach.radius_multiplier), 3) == 2.0
        and round(float(retract.radius_multiplier), 3) == 2.0
        and round(float(approach.speed), 3) == -1.0
        and round(float(retract.speed), 3) == -1.0
        and round(float(retract.overlap), 3) == 0.0
    )


def _squaring_milling_cut_z(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
) -> float:
    if squaring_milling.depth_spec.is_through:
        return -(state.depth + squaring_milling.depth_spec.extra_depth)
    if squaring_milling.depth_spec.target_depth is None:
        raise IsoEmissionNotImplemented("Squaring needs a target depth.")
    return -squaring_milling.depth_spec.target_depth


def _squaring_points(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
) -> tuple[tuple[float, float], ...]:
    length = state.length
    width = state.width
    bl = (0.0, 0.0)
    br = (length, 0.0)
    tr = (length, width)
    tl = (0.0, width)
    start_coordinate = getattr(squaring_milling, "start_coordinate", None)
    if start_coordinate is None:
        horizontal_start = length / 2.0
        vertical_start = width / 2.0
    else:
        horizontal_start = float(start_coordinate)
        vertical_start = float(start_coordinate)
    starts = {
        "Bottom": (horizontal_start, 0.0),
        "Top": (horizontal_start, width),
        "Right": (length, vertical_start),
        "Left": (0.0, vertical_start),
    }
    clockwise = {
        "Bottom": (bl, tl, tr, br),
        "Top": (tr, br, bl, tl),
        "Right": (br, bl, tl, tr),
        "Left": (tl, tr, br, bl),
    }
    counterclockwise = {
        "Bottom": (br, tr, tl, bl),
        "Top": (tl, bl, br, tr),
        "Right": (tr, tl, bl, br),
        "Left": (bl, br, tr, tl),
    }
    try:
        start = starts[squaring_milling.start_edge]
    except KeyError as exc:
        raise IsoEmissionNotImplemented(
            f"Unsupported squaring start edge {squaring_milling.start_edge!r}."
        ) from exc
    if squaring_milling.winding == "CounterClockwise":
        return (start, *counterclockwise[squaring_milling.start_edge], start)
    if squaring_milling.winding == "Clockwise":
        return (start, *clockwise[squaring_milling.start_edge], start)
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring winding {squaring_milling.winding!r}."
    )


def _squaring_entry_point(points: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    unit_x, unit_y = _unit_vector(points[0], points[1])
    return points[0][0] - unit_x, points[0][1] - unit_y


def _squaring_exit_point(points: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    unit_x, unit_y = _unit_vector(points[-2], points[-1])
    return points[-1][0] + unit_x, points[-1][1] + unit_y


def _squaring_line_lead_point(
    points: tuple[tuple[float, float], ...],
    lead_radius: float,
) -> tuple[float, float]:
    unit_x, unit_y = _unit_vector(points[0], points[1])
    return points[0][0] - (unit_x * lead_radius), points[0][1] - (unit_y * lead_radius)


def _squaring_line_rapid_point(
    points: tuple[tuple[float, float], ...],
    lead_radius: float,
) -> tuple[float, float]:
    lead_point = _squaring_line_lead_point(points, lead_radius)
    unit_x, unit_y = _unit_vector(points[0], points[1])
    return lead_point[0] - unit_x, lead_point[1] - unit_y


def _squaring_line_exit_lead_point(
    points: tuple[tuple[float, float], ...],
    lead_radius: float,
) -> tuple[float, float]:
    unit_x, unit_y = _unit_vector(points[-2], points[-1])
    return points[-1][0] + (unit_x * lead_radius), points[-1][1] + (unit_y * lead_radius)


def _squaring_line_clearance_point(
    points: tuple[tuple[float, float], ...],
    lead_radius: float,
) -> tuple[float, float]:
    lead_point = _squaring_line_exit_lead_point(points, lead_radius)
    unit_x, unit_y = _unit_vector(points[-2], points[-1])
    return lead_point[0] + unit_x, lead_point[1] + unit_y


def _squaring_arc_radius(squaring_milling: sp.SquaringMillingSpec) -> float:
    return (squaring_milling.tool_width / 2.0) * squaring_milling.approach.radius_multiplier


def _squaring_arc_center(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
    arc_radius: float,
) -> tuple[float, float]:
    start = _squaring_points(state, squaring_milling)[0]
    outward_x, outward_y = _squaring_outward_unit(squaring_milling)
    return start[0] + (outward_x * arc_radius), start[1] + (outward_y * arc_radius)


def _squaring_arc_lead_point(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
    center: tuple[float, float],
    arc_radius: float,
) -> tuple[float, float]:
    points = _squaring_points(state, squaring_milling)
    unit_x, unit_y = _unit_vector(points[0], points[-2])
    return center[0] + (unit_x * arc_radius), center[1] + (unit_y * arc_radius)


def _squaring_arc_exit_point(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
    center: tuple[float, float],
    arc_radius: float,
) -> tuple[float, float]:
    points = _squaring_points(state, squaring_milling)
    unit_x, unit_y = _unit_vector(points[0], points[1])
    return center[0] + (unit_x * arc_radius), center[1] + (unit_y * arc_radius)


def _squaring_arc_rapid_point(
    state: sp.PgmxState,
    squaring_milling: sp.SquaringMillingSpec,
    center: tuple[float, float],
    arc_radius: float,
) -> tuple[float, float]:
    lead_x, lead_y = _squaring_arc_lead_point(
        state,
        squaring_milling,
        center,
        arc_radius,
    )
    outward_x, outward_y = _squaring_outward_unit(squaring_milling)
    return lead_x + outward_x, lead_y + outward_y


def _squaring_arc_clearance_point(
    squaring_milling: sp.SquaringMillingSpec,
    point: tuple[float, float],
) -> tuple[float, float]:
    outward_x, outward_y = _squaring_outward_unit(squaring_milling)
    return point[0] + outward_x, point[1] + outward_y


def _squaring_outward_unit(
    squaring_milling: sp.SquaringMillingSpec,
) -> tuple[float, float]:
    if squaring_milling.start_edge == "Bottom":
        return 0.0, -1.0
    if squaring_milling.start_edge == "Top":
        return 0.0, 1.0
    if squaring_milling.start_edge == "Right":
        return 1.0, 0.0
    if squaring_milling.start_edge == "Left":
        return -1.0, 0.0
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring start edge {squaring_milling.start_edge!r}."
    )


def _squaring_arc_code(squaring_milling: sp.SquaringMillingSpec) -> str:
    if squaring_milling.winding == "CounterClockwise":
        return "G2"
    if squaring_milling.winding == "Clockwise":
        return "G3"
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring winding {squaring_milling.winding!r}."
    )


def _format_arc_move(
    code: str,
    point: tuple[float, float],
    center: tuple[float, float],
    feed: float,
    *,
    z: float | None = None,
) -> str:
    axes = f"{code} X{_format_mm(point[0])} Y{_format_mm(point[1])}"
    if z is not None:
        axes += f" Z{_format_mm(z)}"
    return (
        f"{axes} "
        f"I{_format_mm(center[0])} "
        f"J{_format_mm(center[1])} "
        f"F{_format_mm(feed)}"
    )


def _squaring_compensation(squaring_milling: sp.SquaringMillingSpec) -> str:
    if squaring_milling.winding == "CounterClockwise":
        return "G42"
    if squaring_milling.winding == "Clockwise":
        return "G41"
    raise IsoEmissionNotImplemented(
        f"Unsupported squaring winding {squaring_milling.winding!r}."
    )


def _emit_slot_milling(
    state: sp.PgmxState,
    slot_milling: sp.SlotMillingSpec,
    *,
    include_full_setup: bool = True,
    include_observed_edge_cleanup: bool = False,
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
    lines: list[str] = [
        f"?%ETK[6]={tool.spindle}",
        "G17",
    ]
    if include_full_setup:
        lines.extend(
            [
                "MLV=2",
                f"%Or[0].ofX={_format_mm(-(state.length + (2.0 * state.origin_x)) * 1000.0)}",
                _work_origin_y_line(),
                f"%Or[0].ofZ={_format_mm((state.depth + state.origin_z) * 1000.0)}",
                "MLV=1",
                f"SHF[X]={_format_mm(-(state.length + state.origin_x))}",
                f"SHF[Y]={_format_mm(_base_shf_y(state.origin_y))}",
                f"SHF[Z]={_format_mm(state.depth + state.origin_z)}",
                "MLV=2",
            ]
        )
    lines.extend(
        [
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
        ]
    )
    if include_observed_edge_cleanup:
        edge_reentry_x = start_x - 0.75
        lines.extend(
            [
                f"G1 Z{_format_mm(slot_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
                f"G1 X{_format_mm(edge_reentry_x)} Z{_format_mm(slot_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
                f"G1 X{_format_mm(start_x)} Z{_format_mm(slot_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
                f"G1 Z{_format_mm(slot_milling.security_plane)} F{_format_mm(tool.milling_feed)}",
                f"G1 Z{_format_mm(cut_z)} F{_format_mm(tool.milling_feed)}",
            ]
        )
    lines.extend(
        [
            f"G0 Z{_format_mm(slot_milling.security_plane)}",
            "D0",
            "SVL 0.000",
            "VL6=0.000",
            "SVR 0.000",
            "VL7=0.000",
            "?%ETK[7]=0",
        ]
    )
    return tuple(lines)


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
    if not tool_name:
        tool_name = _auto_top_drill_tool_name(drilling)
    normalized = _normalize_drill_tool_name(tool_name)
    tools = load_machine_config().top_drill_tools
    if normalized not in tools:
        raise IsoEmissionNotImplemented(
            f"Top drilling tool {drilling.tool_name or drilling.tool_id!r} is not supported yet."
        )
    return tools[normalized]


def _auto_top_drill_tool_name(drilling: sp.DrillingSpec) -> str:
    family = (drilling.drill_family or "Flat").strip() or "Flat"
    diameter = _compact_dimension_key(drilling.diameter)
    return _AUTO_TOP_DRILL_TOOL_NAMES.get((family, diameter), "")


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
    if tool.tool_name != "E004":
        raise IsoEmissionNotImplemented("Line milling supports only E004 for now.")
    if round(float(line_milling.tool_width), 3) != round(tool.tool_width, 3):
        raise IsoEmissionNotImplemented(
            f"{tool.tool_name} line milling expects {tool.tool_width:.3f} mm width."
        )
    return tool


def _polyline_milling_tool(polyline_milling: sp.PolylineMillingSpec) -> _LineMillingTool:
    tool_name = polyline_milling.tool_name.strip().upper()
    if not tool_name and polyline_milling.tool_id:
        tool_name = _tool_name_from_id(polyline_milling.tool_id)
    tool = load_machine_config().line_milling_tools.get(tool_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Polyline milling tool {polyline_milling.tool_name or polyline_milling.tool_id!r} "
            "is not supported yet."
        )
    if tool.tool_name not in {"E003", "E004"}:
        raise IsoEmissionNotImplemented("Polyline milling supports only E003/E004 for now.")
    if round(float(polyline_milling.tool_width), 3) != round(tool.tool_width, 3):
        raise IsoEmissionNotImplemented(
            f"{tool.tool_name} polyline milling expects {tool.tool_width:.3f} mm width."
        )
    return tool


def _circle_milling_tool(circle_milling: sp.CircleMillingSpec) -> _LineMillingTool:
    tool_name = circle_milling.tool_name.strip().upper()
    if not tool_name and circle_milling.tool_id:
        tool_name = _tool_name_from_id(circle_milling.tool_id)
    tool = load_machine_config().line_milling_tools.get(tool_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Circle milling tool {circle_milling.tool_name or circle_milling.tool_id!r} "
            "is not supported yet."
        )
    if tool.tool_name != "E004":
        raise IsoEmissionNotImplemented("Circle milling supports only E004 for now.")
    if round(float(circle_milling.tool_width), 3) != round(tool.tool_width, 3):
        raise IsoEmissionNotImplemented(
            f"{tool.tool_name} circle milling expects {tool.tool_width:.3f} mm width."
        )
    return tool


def _squaring_milling_tool(squaring_milling: sp.SquaringMillingSpec) -> _LineMillingTool:
    tool_name = squaring_milling.tool_name.strip().upper()
    if not tool_name and squaring_milling.tool_id:
        tool_name = _tool_name_from_id(squaring_milling.tool_id)
    tool = load_machine_config().line_milling_tools.get(tool_name)
    if tool is None:
        raise IsoEmissionNotImplemented(
            f"Squaring tool {squaring_milling.tool_name or squaring_milling.tool_id!r} "
            "is not supported yet."
        )
    if tool.tool_name != "E001":
        raise IsoEmissionNotImplemented("Squaring supports only E001 for now.")
    expected_width = tool.tool_width
    if round(float(squaring_milling.tool_width), 3) != round(expected_width, 3):
        raise IsoEmissionNotImplemented(
            f"E001 squaring expects {expected_width:.3f} mm tool width."
        )
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


def _compact_dimension_key(value: float) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else _format_mm(number).rstrip("0").rstrip(".")


def _tool_name_from_id(tool_id: str) -> str:
    return load_machine_config().tool_names_by_id.get(tool_id.strip(), "")


def _format_mm(value: float) -> str:
    return f"{float(value):.3f}"


def _format_spindle_speed(value: float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return _format_mm(number)
