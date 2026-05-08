"""Build state synthesis plans from Maestro `.pgmx` snapshots."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

from tools import synthesize_pgmx as sp
from tools.pgmx_snapshot import (
    PgmxEmbeddedSpindleSnapshot,
    PgmxEmbeddedToolSnapshot,
    PgmxOperationSnapshot,
    PgmxResolvedWorkingStepSnapshot,
    PgmxSnapshot,
    read_pgmx_snapshot,
)

from .model import (
    EvidenceSource,
    IsoStatePlan,
    IsoStateWarning,
    StateStage,
    StateValue,
    StateVector,
    TraceMove,
    TracePoint,
)

NCI_CFG_PATH = "iso_state_synthesis/machine_config/snapshot/xilog_plus/Cfg/NCI.CFG"
NCI_ORI_CFG_PATH = "iso_state_synthesis/machine_config/snapshot/xilog_plus/Cfg/NCI_ORI.CFG"
XISO_CONTRACT_PATH = "iso_state_synthesis/contracts/xiso_intermediate_contract.md"
SIDE_DRILL_RULE_PATH = "iso_state_synthesis/experiments/004_side_drill_state_table.md"
LINE_MILLING_RULE_PATH = "iso_state_synthesis/experiments/005_line_e004_state_table.md"
PROFILE_MILLING_RULE_PATH = "iso_state_synthesis/experiments/006_profile_e001_state_table.md"
PHEADS_CFG_PATH = "iso_state_synthesis/machine_config/snapshot/xilog_plus/Cfg/pheads.cfg"

_SIDE_DRILL_POLICIES = {
    "Left": {
        "etk8": 3,
        "spindle": 61,
        "mask": 2147483648,
        "axis": "X",
        "direction": -1,
        "coordinate_sign": -1,
    },
    "Right": {
        "etk8": 2,
        "spindle": 60,
        "mask": 2147483648,
        "axis": "X",
        "direction": 1,
        "coordinate_sign": 1,
    },
    "Front": {
        "etk8": 5,
        "spindle": 58,
        "mask": 1073741824,
        "axis": "Y",
        "direction": -1,
        "coordinate_sign": 1,
    },
    "Back": {
        "etk8": 4,
        "spindle": 59,
        "mask": 1073741824,
        "axis": "Y",
        "direction": 1,
        "coordinate_sign": -1,
    },
}


def build_state_plan_from_pgmx(path: Path) -> IsoStatePlan:
    """Read a `.pgmx` and build the first state-oriented internal plan."""

    return build_state_plan_from_snapshot(read_pgmx_snapshot(Path(path)))


def build_state_plan_from_snapshot(snapshot: PgmxSnapshot) -> IsoStatePlan:
    """Build a state-oriented plan from a normalized PGMX snapshot."""

    warnings: list[IsoStateWarning] = []
    stages: list[StateStage] = [
        _program_header_stage(snapshot),
        _machine_preamble_stage(snapshot),
    ]

    order_index = 100
    for resolved_step in _ordered_resolved_working_steps(snapshot):
        step_stages, step_warnings = _stages_for_working_step(snapshot, resolved_step, order_index)
        stages.extend(step_stages)
        warnings.extend(step_warnings)
        order_index += 10

    return IsoStatePlan(
        source_path=snapshot.source_path,
        project_name=snapshot.project_name or snapshot.state.piece_name,
        initial_state=_piece_initial_state(snapshot),
        stages=tuple(stages),
        warnings=tuple(warnings),
    )


def _ordered_resolved_working_steps(snapshot: PgmxSnapshot) -> tuple[PgmxResolvedWorkingStepSnapshot, ...]:
    steps = tuple(snapshot.resolved_working_steps)
    families = {
        family
        for family in (_resolved_step_family(step) for step in steps)
        if family not in {"program_close", "unsupported"}
    }
    if len(families) <= 1:
        return steps

    steps = _ordered_mixed_drill_neighborhoods(steps)

    ordered: list[PgmxResolvedWorkingStepSnapshot] = []
    index = 0
    while index < len(steps):
        step = steps[index]
        family = _resolved_step_family(step)
        if family == "top_drill":
            top_block: list[PgmxResolvedWorkingStepSnapshot] = []
            while index < len(steps) and _resolved_step_family(steps[index]) == "top_drill":
                top_block.append(steps[index])
                index += 1
            ordered.extend(_ordered_top_drill_block(top_block))
            continue
        if family == "side_drill":
            side_block: list[PgmxResolvedWorkingStepSnapshot] = []
            while index < len(steps) and _resolved_step_family(steps[index]) == "side_drill":
                side_block.append(steps[index])
                index += 1
            ordered.extend(_ordered_side_drill_block(side_block))
            continue
        else:
            ordered.append(step)
            index += 1
            continue
    return tuple(ordered)


def _ordered_mixed_drill_neighborhoods(
    steps: tuple[PgmxResolvedWorkingStepSnapshot, ...],
) -> tuple[PgmxResolvedWorkingStepSnapshot, ...]:
    ordered: list[PgmxResolvedWorkingStepSnapshot] = []
    index = 0
    while index < len(steps):
        first_side, after_first_side = _side_plane_block(steps, index)
        if not first_side:
            ordered.append(steps[index])
            index += 1
            continue

        top_block, after_top = _family_block(steps, after_first_side, "top_drill")
        second_side, after_second_side = _side_plane_block(steps, after_top)
        if (
            top_block
            and second_side
            and _same_side_drill_plane(first_side, second_side)
            and _side_block_extent(first_side) < _side_block_extent(second_side)
        ):
            ordered.extend(second_side)
            ordered.extend(top_block)
            ordered.extend(first_side)
            index = after_second_side
            continue

        ordered.extend(first_side)
        index = after_first_side

    return tuple(ordered)


def _side_plane_block(
    steps: tuple[PgmxResolvedWorkingStepSnapshot, ...],
    start: int,
) -> tuple[list[PgmxResolvedWorkingStepSnapshot], int]:
    if start >= len(steps) or _resolved_step_family(steps[start]) != "side_drill":
        return [], start
    plane = _side_drill_plane(steps[start])
    block: list[PgmxResolvedWorkingStepSnapshot] = []
    index = start
    while (
        index < len(steps)
        and _resolved_step_family(steps[index]) == "side_drill"
        and _side_drill_plane(steps[index]) == plane
    ):
        block.append(steps[index])
        index += 1
    return block, index


def _family_block(
    steps: tuple[PgmxResolvedWorkingStepSnapshot, ...],
    start: int,
    family: str,
) -> tuple[list[PgmxResolvedWorkingStepSnapshot], int]:
    block: list[PgmxResolvedWorkingStepSnapshot] = []
    index = start
    while index < len(steps) and _resolved_step_family(steps[index]) == family:
        block.append(steps[index])
        index += 1
    return block, index


def _same_side_drill_plane(
    first: list[PgmxResolvedWorkingStepSnapshot],
    second: list[PgmxResolvedWorkingStepSnapshot],
) -> bool:
    first_planes = {_side_drill_plane(step) for step in first}
    second_planes = {_side_drill_plane(step) for step in second}
    return len(first_planes) == 1 and first_planes == second_planes and "" not in first_planes


def _side_drill_plane(resolved_step: PgmxResolvedWorkingStepSnapshot) -> str:
    return (resolved_step.feature.plane_name if resolved_step.feature is not None else "") or ""


def _side_block_extent(block: list[PgmxResolvedWorkingStepSnapshot]) -> float:
    values = [abs(_side_drill_fixed_value(step)) for step in block]
    return max(values) if values else 0.0


def _side_drill_fixed_value(resolved_step: PgmxResolvedWorkingStepSnapshot) -> float:
    feature = resolved_step.feature
    operation = resolved_step.operation
    plane = (feature.plane_name if feature is not None else "") or ""
    policy = _SIDE_DRILL_POLICIES.get(plane)
    if operation is None or policy is None:
        return 0.0
    return _side_fixed_from_toolpath(operation, policy)


def _resolved_step_family(resolved_step: PgmxResolvedWorkingStepSnapshot) -> str:
    step = resolved_step.step
    if resolved_step.feature is None or resolved_step.operation is None:
        return "program_close" if step.runtime_type == "Xn" else "unsupported"
    if _is_top_drilling(resolved_step):
        return "top_drill"
    if _is_side_drilling(resolved_step):
        return "side_drill"
    if _is_slot_milling(resolved_step):
        return "slot_milling"
    if _is_line_milling(resolved_step):
        return "line_milling"
    if _is_profile_milling_e001(resolved_step):
        return "profile_milling"
    return "unsupported"


def _ordered_top_drill_block(
    block: list[PgmxResolvedWorkingStepSnapshot],
) -> tuple[PgmxResolvedWorkingStepSnapshot, ...]:
    by_x: dict[float, list[PgmxResolvedWorkingStepSnapshot]] = {}
    for step in block:
        x, _, _, _ = _top_drill_step_sort_key(step)
        by_x.setdefault(x, []).append(step)

    ordered: list[PgmxResolvedWorkingStepSnapshot] = []
    for column_index, x in enumerate(sorted(by_x)):
        column = by_x[x]
        descending_y = bool(column_index % 2)
        ordered.extend(sorted(column, key=lambda step: _top_drill_column_sort_key(step, descending_y)))
    return tuple(ordered)


def _top_drill_step_sort_key(resolved_step: PgmxResolvedWorkingStepSnapshot) -> tuple[float, float, str, str]:
    geometry = resolved_step.geometry
    x, y = (float("inf"), float("inf"))
    if geometry is not None and geometry.point is not None:
        x, y, _ = geometry.point
    operation = resolved_step.operation
    tool_name = operation.tool_key.name if operation is not None and operation.tool_key is not None else ""
    return (round(float(x), 6), round(float(y), 6), tool_name, resolved_step.step.id)


def _top_drill_column_sort_key(
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    descending_y: bool,
) -> tuple[float, str, str]:
    _, y, tool_name, step_id = _top_drill_step_sort_key(resolved_step)
    return ((-y if descending_y else y), tool_name, step_id)


def _ordered_side_drill_block(
    block: list[PgmxResolvedWorkingStepSnapshot],
) -> tuple[PgmxResolvedWorkingStepSnapshot, ...]:
    by_plane: dict[str, list[PgmxResolvedWorkingStepSnapshot]] = {}
    plane_order: list[str] = []
    for step in block:
        plane = (step.feature.plane_name if step.feature is not None else "") or ""
        if plane not in by_plane:
            by_plane[plane] = []
            plane_order.append(plane)
        by_plane[plane].append(step)

    ordered: list[PgmxResolvedWorkingStepSnapshot] = []
    for plane in plane_order:
        ordered.extend(sorted(by_plane[plane], key=_side_drill_step_sort_key))
    return tuple(ordered)


def _side_drill_step_sort_key(resolved_step: PgmxResolvedWorkingStepSnapshot) -> tuple[float, str]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    plane = (feature.plane_name if feature is not None else "") or ""
    policy = _SIDE_DRILL_POLICIES.get(plane)
    fixed = 0.0
    if operation is not None and policy is not None:
        fixed = _side_fixed_from_toolpath(operation, policy)
    return (round(float(fixed), 6), resolved_step.step.id)


def _stages_for_working_step(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> tuple[tuple[StateStage, ...], tuple[IsoStateWarning, ...]]:
    step = resolved_step.step
    feature = resolved_step.feature
    operation = resolved_step.operation
    if not step.is_enabled:
        return (), (
            IsoStateWarning(
                code="disabled_working_step",
                message="El working step esta deshabilitado y no se incorpora al plan.",
                source=step.name or step.id,
            ),
        )

    if feature is None or operation is None:
        if step.runtime_type == "Xn":
            return (_program_close_stage(snapshot, resolved_step, order_index),), ()
        return (), (
            IsoStateWarning(
                code="unresolved_working_step",
                message="El working step no resuelve feature y operacion.",
                source=step.name or step.id,
            ),
        )

    if _is_top_drilling(resolved_step):
        return _top_drill_stages(snapshot, resolved_step, order_index), ()
    if _is_side_drilling(resolved_step):
        return _side_drill_stages(snapshot, resolved_step, order_index), ()
    if _is_slot_milling(resolved_step):
        return _slot_milling_stages(snapshot, resolved_step, order_index), ()
    if _is_line_milling(resolved_step):
        return _line_milling_stages(snapshot, resolved_step, order_index), ()
    if _is_profile_milling_e001(resolved_step):
        return _profile_milling_stages(snapshot, resolved_step, order_index), ()

    return (), (
        IsoStateWarning(
            code="unsupported_stage_family",
            message=(
                "La estructura de estados inicial solo materializa taladro "
                "superior; esta familia queda para ampliar por capas."
            ),
            source=feature.name or step.name or feature.id,
        ),
    )


def _piece_initial_state(snapshot: PgmxSnapshot) -> StateVector:
    state = snapshot.state
    values = [
        _pgmx_value(snapshot, "pieza", "name", state.piece_name, "state.piece_name"),
        _pgmx_value(snapshot, "pieza", "length", state.length, "state.length"),
        _pgmx_value(snapshot, "pieza", "width", state.width, "state.width"),
        _pgmx_value(snapshot, "pieza", "depth", state.depth, "state.depth"),
        _pgmx_value(snapshot, "pieza", "origin_x", state.origin_x, "state.origin_x"),
        _pgmx_value(snapshot, "pieza", "origin_y", state.origin_y, "state.origin_y"),
        _pgmx_value(snapshot, "pieza", "origin_z", state.origin_z, "state.origin_z"),
        _pgmx_value(
            snapshot,
            "pieza",
            "execution_fields",
            state.execution_fields,
            "state.execution_fields",
        ),
    ]
    if snapshot.tooling_entry_name:
        values.append(
            StateValue(
                layer="herramienta",
                key="tooling_entry_name",
                value=snapshot.tooling_entry_name,
                source=_pgmx_source(snapshot, "container_entries"),
                confidence="observed",
                note="Fuente primaria de herramientas para este trabajo concreto.",
            )
        )
    return StateVector(tuple(values))


def _program_header_stage(snapshot: PgmxSnapshot) -> StateStage:
    state = snapshot.state
    target = StateVector(
        (
            _rule_value(
                "pieza",
                "header_dx",
                state.length + state.origin_x,
                "DX = length + origin_x",
            ),
            _rule_value(
                "pieza",
                "header_dy",
                state.width + state.origin_y,
                "DY = width + origin_y",
            ),
            _rule_value(
                "pieza",
                "header_dz",
                state.depth + state.origin_z,
                "DZ = depth + origin_z",
            ),
            _pgmx_value(
                snapshot,
                "pieza",
                "execution_fields",
                state.execution_fields,
                "state.execution_fields",
            ),
            _contract_value("salida", "xiso_statement", "H", "Cabecera XISO candidata."),
        )
    )
    return StateStage(
        key="program_header",
        family="program",
        order_index=0,
        target_state=target,
        xiso_statement="H",
        notes=("Cabecera derivada de estado de pieza; no emite ISO final todavia.",),
    )


def _machine_preamble_stage(snapshot: PgmxSnapshot) -> StateStage:
    target = StateVector(
        (
            StateValue(
                layer="maquina",
                key="preamble_template",
                value="$GEN_INIT",
                source=EvidenceSource("machine_config", NCI_CFG_PATH, "$GEN_INIT"),
                confidence="observed",
                note="Plantilla de preambulo observada en NCI.CFG.",
                required=True,
            ),
            StateValue(
                layer="maquina",
                key="metric_mode",
                value="G71",
                source=EvidenceSource(
                    "observed_rule",
                    "iso_state_synthesis/experiments/001_top_drill_state_table.md",
                    "Lineas 3-9 - Preambulo De Maquina",
                ),
                confidence="hypothesis",
                note="Asociado al entorno metrico; fuente causal pendiente.",
                required=True,
            ),
        )
    )
    return StateStage(
        key="machine_preamble",
        family="machine",
        order_index=10,
        target_state=target,
        notes=("Preambulo de maquina, separado de pieza y trabajo.",),
    )


def _program_close_stage(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> StateStage:
    step = resolved_step.step
    target = StateVector(
        (
            _pgmx_value(
                snapshot,
                "movimiento",
                "program_close_reference",
                step.reference,
                f"working_steps[{step.id}].reference",
            ),
            _pgmx_value(
                snapshot,
                "movimiento",
                "program_close_x",
                step.x,
                f"working_steps[{step.id}].x",
            ),
            _pgmx_value(
                snapshot,
                "movimiento",
                "program_close_y",
                step.y,
                f"working_steps[{step.id}].y",
            ),
        )
    )
    return StateStage(
        key="program_close",
        family="program",
        order_index=order_index,
        target_state=target,
        working_step_id=step.id,
        notes=("Paso administrativo final Xn usado como cierre/parqueo candidato.",),
    )


def _top_drill_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> tuple[StateStage, ...]:
    geometry = resolved_step.geometry
    feature = resolved_step.feature
    if feature is not None and feature.replication_pattern is not None and geometry is not None:
        base_x, base_y, _ = geometry.point if geometry.point else (0.0, 0.0, 0.0)
        stages: list[StateStage] = []
        for replication_index, (x, y) in enumerate(_replicated_top_points(feature, geometry)):
            stages.extend(
                _single_top_drill_stages(
                    snapshot,
                    resolved_step,
                    order_index + (replication_index * 3),
                    xy_delta=(x - float(base_x), y - float(base_y)),
                )
            )
        return tuple(stages)
    return _single_top_drill_stages(snapshot, resolved_step, order_index)


def _single_top_drill_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
    *,
    xy_delta: tuple[float, float] = (0.0, 0.0),
) -> tuple[StateStage, ...]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    step = resolved_step.step
    assert feature is not None
    assert operation is not None

    tool = _embedded_tool_for_operation(snapshot, operation) or _embedded_top_drill_tool_for_feature(snapshot, feature)
    spindle = _embedded_spindle_for_tool(snapshot, tool, operation)
    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "top_drill", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", feature.plane_name or "Top", f"features[{feature.id}].plane_name"),
        _pgmx_value(snapshot, "trabajo", "feature_depth", _target_depth(feature), f"features[{feature.id}].depth_end"),
        _pgmx_value(snapshot, "trabajo", "security_plane", operation.approach_security_plane, f"operations[{operation.id}].approach_security_plane"),
        _contract_value("salida", "xiso_statement", "B", "Taladro/foratura XISO candidata."),
    ]
    prepare_values.extend(_tool_values(snapshot, operation, tool, spindle))
    prepare_values.extend(_top_drill_output_values(spindle))

    prepare_stage = StateStage(
        key="top_drill_prepare",
        family="top_drill",
        order_index=order_index,
        target_state=StateVector(tuple(prepare_values)),
        xiso_statement="B",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Preparacion de estado antes de ejecutar la traza de taladro superior.",),
    )

    trace_stage = StateStage(
        key="top_drill_trace",
        family="top_drill",
        order_index=order_index + 1,
        target_state=StateVector(
            (
                _pgmx_value(snapshot, "movimiento", "toolpath_count", len(operation.toolpaths), f"operations[{operation.id}].toolpaths"),
                _rule_value(
                    "movimiento",
                    "iso_z_rule",
                    "local_z + ToolOffsetLength",
                    "Regla confirmada en fixture Top Drill 001.",
                ),
            )
        ),
        trace=_trace_moves(snapshot, operation, tool, feature, xy_delta=xy_delta),
        xiso_statement="B",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Traza derivada de toolpaths Maestro; conserva Z local y Z ISO calculada.",),
    )

    reset_stage = StateStage(
        key="top_drill_reset",
        family="top_drill",
        order_index=order_index + 2,
        target_state=StateVector(),
        reset_state=StateVector(
            (
                StateValue(
                    layer="salida",
                    key="etk_17",
                    value=0,
                    source=EvidenceSource(
                        "machine_config",
                        NCI_CFG_PATH,
                        "$GEN_END ?%%ETK[17]=0",
                        note=NCI_ORI_CFG_PATH,
                    ),
                    confidence="observed",
                    note="Reset comun confirmado para salida de estado de cabezal.",
                    required=True,
                ),
                StateValue(
                    layer="herramienta",
                    key="active",
                    value=False,
                    source=EvidenceSource(
                        "observed_rule",
                        "iso_state_synthesis/experiments/001_top_drill_state_table.md",
                        "top_drill_reset",
                    ),
                    confidence="observed",
                ),
            )
        ),
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Reset posterior observado para taladro superior.",),
    )
    return prepare_stage, trace_stage, reset_stage


def _line_milling_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> tuple[StateStage, ...]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    step = resolved_step.step
    assert feature is not None
    assert operation is not None

    tool = _embedded_tool_for_operation(snapshot, operation)
    head_shf = _router_head_shifts()
    start_point, end_point = _line_points(geometry)
    tool_offset = float(tool.tool_offset_length if tool and tool.tool_offset_length is not None else 0.0)
    tool_width = float(feature.tool_width or (tool.diameter if tool and tool.diameter is not None else 0.0))
    tool_radius = tool_width / 2.0
    security_plane = operation.approach_security_plane
    rapid_z = security_plane + tool_offset
    cut_z = _line_cut_z(snapshot, feature)
    plunge_feed = _descent_speed(tool, None)
    milling_feed = _feed_speed(tool)
    strategy = operation.milling_strategy

    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "line_milling", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", feature.plane_name or "Top", f"features[{feature.id}].plane_name"),
        _pgmx_value(snapshot, "trabajo", "side_of_feature", feature.side_of_feature, f"features[{feature.id}].side_of_feature", required=True),
        _pgmx_value(snapshot, "trabajo", "tool_width", tool_width, f"features[{feature.id}].tool_width"),
        _pgmx_value(snapshot, "trabajo", "security_plane", security_plane, f"operations[{operation.id}].approach_security_plane"),
        _pgmx_value(snapshot, "trabajo", "strategy", type(strategy).__name__ if strategy else "", f"operations[{operation.id}].milling_strategy"),
        _pgmx_value(snapshot, "trabajo", "overcut_length", operation.overcut_length, f"operations[{operation.id}].overcut_length", required=True),
        _pgmx_value(snapshot, "trabajo", "approach_enabled", operation.approach.is_enabled, f"operations[{operation.id}].approach.enabled", required=True),
        _pgmx_value(snapshot, "trabajo", "approach_type", operation.approach.approach_type, f"operations[{operation.id}].approach.type", required=True),
        _pgmx_value(snapshot, "trabajo", "approach_mode", operation.approach.mode, f"operations[{operation.id}].approach.mode", required=True),
        _pgmx_value(snapshot, "trabajo", "approach_radius_multiplier", operation.approach.radius_multiplier, f"operations[{operation.id}].approach.radius_multiplier", required=True),
        _pgmx_value(snapshot, "trabajo", "retract_enabled", operation.retract.is_enabled, f"operations[{operation.id}].retract.enabled", required=True),
        _pgmx_value(snapshot, "trabajo", "retract_type", operation.retract.retract_type, f"operations[{operation.id}].retract.type", required=True),
        _pgmx_value(snapshot, "trabajo", "retract_mode", operation.retract.mode, f"operations[{operation.id}].retract.mode", required=True),
        _pgmx_value(snapshot, "trabajo", "retract_radius_multiplier", operation.retract.radius_multiplier, f"operations[{operation.id}].retract.radius_multiplier", required=True),
        _contract_value("salida", "xiso_statement", "G1", "Fresado lineal XISO candidato."),
    ]
    prepare_values.extend(_router_tool_values(snapshot, operation, tool, head_shf))

    prepare_stage = StateStage(
        key="line_milling_prepare",
        family="line_milling",
        order_index=order_index,
        target_state=StateVector(tuple(prepare_values)),
        xiso_statement="G1",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Preparacion de router E004 antes de ejecutar fresado lineal.",),
    )

    trace_stage = StateStage(
        key="line_milling_trace",
        family="line_milling",
        order_index=order_index + 1,
        target_state=StateVector(
            (
                _pgmx_value(snapshot, "movimiento", "toolpath_count", len(operation.toolpaths), f"operations[{operation.id}].toolpaths"),
                _pgmx_value(snapshot, "movimiento", "profile_family", geometry.profile.family if geometry and geometry.profile else "", f"geometries[{geometry.id if geometry else ''}].profile.family", required=True),
                _pgmx_value(snapshot, "movimiento", "profile_winding", geometry.profile.winding if geometry and geometry.profile else "", f"geometries[{geometry.id if geometry else ''}].profile.winding"),
                _pgmx_value(snapshot, "movimiento", "circle_center_x", _profile_center_x(geometry), f"geometries[{geometry.id if geometry else ''}].profile.center.x"),
                _pgmx_value(snapshot, "movimiento", "circle_center_y", _profile_center_y(geometry), f"geometries[{geometry.id if geometry else ''}].profile.center.y"),
                _pgmx_value(snapshot, "movimiento", "contour_points", _profile_xy_points(geometry), f"geometries[{geometry.id if geometry else ''}].curve.sampled_points", required=True),
                _pgmx_value(snapshot, "movimiento", "approach_primitives", _toolpath_primitive_records(operation, "Approach"), f"operations[{operation.id}].toolpaths[Approach]"),
                _pgmx_value(snapshot, "movimiento", "trajectory_primitives", _toolpath_primitive_records(operation, "TrajectoryPath"), f"operations[{operation.id}].toolpaths[TrajectoryPath]"),
                _pgmx_value(snapshot, "movimiento", "lift_primitives", _toolpath_primitive_records(operation, "Lift"), f"operations[{operation.id}].toolpaths[Lift]"),
                _pgmx_value(snapshot, "herramienta", "tool_offset_length", tool_offset, f"operations[{operation.id}].tool_offset_length", required=True),
                _rule_value("movimiento", "rapid_z", rapid_z, "Z rapida = security_plane + ToolOffsetLength.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "cut_z", cut_z, "Z de corte E004 desde profundidad PGMX.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "security_z", security_plane, "Plano de seguridad E004.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("herramienta", "tool_radius", tool_radius, "Radio E004 = ancho / 2.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "plunge_feed", (plunge_feed or 0.0) * 1000.0, "DescentSpeed.Standard * 1000.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "milling_feed", (milling_feed or 0.0) * 1000.0, "FeedRate.Standard * 1000.", path=LINE_MILLING_RULE_PATH, required=True),
                _pgmx_value(snapshot, "movimiento", "start_x", start_point[0], f"geometries[{geometry.id if geometry else ''}].profile.start.x", required=True),
                _pgmx_value(snapshot, "movimiento", "start_y", start_point[1], f"geometries[{geometry.id if geometry else ''}].profile.start.y", required=True),
                _pgmx_value(snapshot, "movimiento", "end_x", end_point[0], f"geometries[{geometry.id if geometry else ''}].profile.end.x", required=True),
                _pgmx_value(snapshot, "movimiento", "end_y", end_point[1], f"geometries[{geometry.id if geometry else ''}].profile.end.y", required=True),
            )
        ),
        trace=_line_trace_moves(snapshot, operation),
        xiso_statement="G1",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Traza lineal derivada de toolpaths Maestro.",),
    )

    reset_stage = StateStage(
        key="line_milling_reset",
        family="line_milling",
        order_index=order_index + 2,
        target_state=StateVector(),
        reset_state=StateVector(
            (
                StateValue(
                    layer="herramienta",
                    key="active",
                    value=False,
                    source=EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "line_milling_reset"),
                    confidence="observed",
                ),
                StateValue(
                    layer="salida",
                    key="etk_7",
                    value=0,
                    source=EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "line_milling_reset"),
                    confidence="observed",
                ),
            )
        ),
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Reset posterior observado para fresado lineal E004.",),
    )
    return prepare_stage, trace_stage, reset_stage


def _slot_milling_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> tuple[StateStage, ...]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    step = resolved_step.step
    assert feature is not None
    assert operation is not None
    assert geometry is not None

    tool = _embedded_tool_for_operation(snapshot, operation)
    spindle_number = int((operation.tool_key.name if operation.tool_key else "82") or 82)
    spindle = _embedded_spindle_by_number(snapshot, spindle_number)
    start_point, end_point = _line_points(geometry)
    tool_offset = float(tool.tool_offset_length if tool and tool.tool_offset_length is not None else 0.0)
    tool_width = float(feature.tool_width or (spindle.radius * 2.0 if spindle and spindle.radius is not None else 0.0))
    tool_radius = tool_width / 2.0
    security_plane = operation.approach_security_plane
    rapid_z = security_plane + tool_offset
    cut_z = _line_cut_z(snapshot, feature)
    plunge_feed = _descent_speed(tool, spindle)
    milling_feed = _feed_speed(tool)
    trace_points = tuple(
        (float(point[0]), float(point[1]), float(point[2]))
        for toolpath in operation.toolpaths
        if toolpath.path_type == "TrajectoryPath" and toolpath.curve is not None
        for point in toolpath.curve.sampled_points
    )
    if trace_points:
        rapid_x = max(point[0] for point in trace_points)
        cut_x = min(point[0] for point in trace_points)
        rapid_y = trace_points[0][1]
    else:
        rapid_x = max(float(start_point[0]), float(end_point[0]))
        cut_x = min(float(start_point[0]), float(end_point[0]))
        rapid_y = float(start_point[1])

    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "slot_milling", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", feature.plane_name or "Top", f"features[{feature.id}].plane_name"),
        _pgmx_value(snapshot, "trabajo", "side_of_feature", feature.side_of_feature, f"features[{feature.id}].side_of_feature"),
        _pgmx_value(snapshot, "trabajo", "tool_width", tool_width, f"features[{feature.id}].tool_width"),
        _pgmx_value(snapshot, "trabajo", "security_plane", security_plane, f"operations[{operation.id}].approach_security_plane"),
        _contract_value("salida", "xiso_statement", "G1", "Ranura SlotSide XISO candidata."),
    ]
    prepare_values.extend(_slot_tool_values(snapshot, operation, tool, spindle, tool_radius))

    prepare_stage = StateStage(
        key="slot_milling_prepare",
        family="slot_milling",
        order_index=order_index,
        target_state=StateVector(tuple(prepare_values)),
        xiso_statement="G1",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Preparacion de sierra vertical SlotSide antes de ejecutar ranura.",),
    )

    trace_stage = StateStage(
        key="slot_milling_trace",
        family="slot_milling",
        order_index=order_index + 1,
        target_state=StateVector(
            (
                _pgmx_value(snapshot, "movimiento", "toolpath_count", len(operation.toolpaths), f"operations[{operation.id}].toolpaths"),
                _rule_value("movimiento", "rapid_x", rapid_x, "La sierra vertical entra desde X maximo observado.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "rapid_y", rapid_y, "Y de ranura desde toolpath compensado.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "cut_x", cut_x, "La sierra vertical corta hacia X minimo observado.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "rapid_z", rapid_z, "Z rapida = security_plane + ToolOffsetLength.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "cut_z", cut_z, "Z de ranura desde profundidad PGMX.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "security_z", security_plane, "Plano de seguridad SlotSide.", path=LINE_MILLING_RULE_PATH, required=True),
                _pgmx_value(snapshot, "herramienta", "tool_offset_length", tool_offset, f"operations[{operation.id}].tool_offset_length", required=True),
                _rule_value("herramienta", "tool_radius", tool_radius, "Radio efectivo de sierra = ancho SlotSide / 2.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "plunge_feed", (plunge_feed or 0.0) * 1000.0, "DescentSpeed.Standard * 1000.", path=LINE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "milling_feed", (milling_feed or 0.0) * 1000.0, "FeedRate.Standard * 1000.", path=LINE_MILLING_RULE_PATH, required=True),
            )
        ),
        trace=_line_trace_moves(snapshot, operation),
        xiso_statement="G1",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Traza de ranura SlotSide derivada del toolpath compensado.",),
    )

    reset_stage = StateStage(
        key="slot_milling_reset",
        family="slot_milling",
        order_index=order_index + 2,
        target_state=StateVector(),
        reset_state=StateVector(
            (
                StateValue("herramienta", "active", False, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "slot_milling_reset"), confidence="observed"),
                StateValue("salida", "etk_7", 0, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "slot_milling_reset"), confidence="observed"),
                StateValue("salida", "etk_1", 0, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "slot_milling_reset"), confidence="observed"),
                StateValue("salida", "etk_17", 0, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "slot_milling_reset"), confidence="observed"),
            )
        ),
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Reset posterior observado para ranura con sierra vertical.",),
    )
    return prepare_stage, trace_stage, reset_stage


def _profile_milling_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> tuple[StateStage, ...]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    step = resolved_step.step
    assert feature is not None
    assert operation is not None

    tool = _embedded_tool_for_operation(snapshot, operation)
    head_shf = _router_head_shifts()
    contour_points = _profile_contour_points(geometry)
    tool_offset = float(tool.tool_offset_length if tool and tool.tool_offset_length is not None else 0.0)
    tool_width = float(feature.tool_width or (tool.diameter if tool and tool.diameter is not None else 0.0))
    tool_radius = tool_width / 2.0
    overcut_length = float(operation.overcut_length or 0.0)
    security_plane = operation.approach_security_plane
    rapid_z = security_plane + tool_offset
    cut_z = _line_cut_z(snapshot, feature)
    plunge_feed = _descent_speed(tool, None)
    milling_feed = _feed_speed(tool)
    start_x = float(contour_points[0][0])
    start_y = float(contour_points[0][1])
    side_of_feature = feature.side_of_feature or "Right"
    direction_sign = -1.0 if side_of_feature == "Right" else 1.0
    if operation.approach.is_enabled:
        lead_distance = 2.0 * tool_radius
    else:
        lead_distance = 0.0
    if operation.approach.is_enabled and operation.approach.approach_type == "Arc":
        entry_y = start_y - (2.0 * tool_radius)
        rapid_y = entry_y - overcut_length
        rapid_extra_x = 0.0
    else:
        entry_y = start_y
        rapid_y = start_y
        rapid_extra_x = overcut_length
    entry_x = start_x + (direction_sign * lead_distance)
    rapid_x = entry_x + (direction_sign * rapid_extra_x)
    exit_x = start_x - (direction_sign * lead_distance)
    exit_y = entry_y
    if operation.retract.is_enabled and operation.retract.retract_type == "Arc":
        leadout_y = entry_y - overcut_length
        leadout_extra_x = 0.0
    else:
        leadout_y = start_y
        leadout_extra_x = overcut_length
    leadout_x = exit_x - (direction_sign * leadout_extra_x)
    center_i = start_x
    center_j = entry_y
    compensation_code = "G42" if side_of_feature == "Right" else "G41"
    arc_code = "G2" if compensation_code == "G42" else "G3"

    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "profile_milling", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", feature.plane_name or "Top", f"features[{feature.id}].plane_name"),
        _pgmx_value(snapshot, "trabajo", "side_of_feature", feature.side_of_feature, f"features[{feature.id}].side_of_feature"),
        _pgmx_value(snapshot, "trabajo", "tool_width", tool_width, f"features[{feature.id}].tool_width"),
        _pgmx_value(snapshot, "trabajo", "security_plane", security_plane, f"operations[{operation.id}].approach_security_plane"),
        _pgmx_value(snapshot, "trabajo", "strategy", type(operation.milling_strategy).__name__ if operation.milling_strategy else "", f"operations[{operation.id}].milling_strategy", required=True),
        _pgmx_value(snapshot, "trabajo", "approach_mode", operation.approach.mode, f"operations[{operation.id}].approach.mode"),
        _pgmx_value(snapshot, "trabajo", "retract_mode", operation.retract.mode, f"operations[{operation.id}].retract.mode"),
        _pgmx_value(snapshot, "trabajo", "overcut_length", overcut_length, f"operations[{operation.id}].overcut_length"),
        _contract_value("salida", "xiso_statement", "G1", "Fresado de perfil XISO candidato."),
    ]
    prepare_values.extend(_router_tool_values(snapshot, operation, tool, head_shf))

    prepare_stage = StateStage(
        key="profile_milling_prepare",
        family="profile_milling",
        order_index=order_index,
        target_state=StateVector(tuple(prepare_values)),
        xiso_statement="G1",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Preparacion de router E001 antes de ejecutar perfil cerrado.",),
    )

    trace_stage = StateStage(
        key="profile_milling_trace",
        family="profile_milling",
        order_index=order_index + 1,
        target_state=StateVector(
            (
                _pgmx_value(snapshot, "movimiento", "toolpath_count", len(operation.toolpaths), f"operations[{operation.id}].toolpaths"),
                _rule_value("movimiento", "rapid_z", rapid_z, "Z rapida = security_plane + ToolOffsetLength.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "cut_z", cut_z, "Z de corte E001 desde profundidad PGMX.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "security_z", security_plane, "Plano de seguridad E001.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("herramienta", "tool_radius", tool_radius, "Radio E001 = ancho / 2.", path=PROFILE_MILLING_RULE_PATH, required=True),
                StateValue("herramienta", "tool_offset_length", tool_offset, _tool_source(snapshot, tool, "CoreTool"), required=True),
                _rule_value("movimiento", "plunge_feed", (plunge_feed or 0.0) * 1000.0, "DescentSpeed.Standard * 1000.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "milling_feed", (milling_feed or 0.0) * 1000.0, "FeedRate.Standard * 1000.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "contour_points", tuple((float(x), float(y)) for x, y, _ in contour_points), "Perfil nominal cerrado usado con compensacion.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _pgmx_value(snapshot, "movimiento", "approach_primitives", _toolpath_primitive_records(operation, "Approach"), f"operations[{operation.id}].toolpaths[Approach]", required=True),
                _pgmx_value(snapshot, "movimiento", "trajectory_primitives", _toolpath_primitive_records(operation, "TrajectoryPath"), f"operations[{operation.id}].toolpaths[TrajectoryPath]"),
                _pgmx_value(snapshot, "movimiento", "lift_primitives", _toolpath_primitive_records(operation, "Lift"), f"operations[{operation.id}].toolpaths[Lift]", required=True),
                _rule_value("movimiento", "rapid_x", rapid_x, "X rapida antes de entrada.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "rapid_y", rapid_y, "Y rapida antes del arco de entrada.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "entry_x", entry_x, "X de entrada compensada.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "entry_y", entry_y, "Y de entrada compensada.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "exit_x", exit_x, "X de salida compensada.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "exit_y", exit_y, "Y de salida compensada.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "leadout_x", leadout_x, "X de alejamiento.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "leadout_y", leadout_y, "Y de alejamiento.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "arc_i", center_i, "Centro I de arcos de entrada/salida.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("movimiento", "arc_j", center_j, "Centro J de arcos de entrada/salida.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "approach_enabled", operation.approach.is_enabled, "Acercamiento E001 habilitado.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "approach_type", operation.approach.approach_type, "Tipo de acercamiento E001.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "approach_mode", operation.approach.mode, "Modo de acercamiento E001.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "strategy", type(operation.milling_strategy).__name__ if operation.milling_strategy else "", "Estrategia E001.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "retract_enabled", operation.retract.is_enabled, "Alejamiento E001 habilitado.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "retract_type", operation.retract.retract_type, "Tipo de alejamiento E001.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("trabajo", "retract_mode", operation.retract.mode, "Modo de alejamiento E001.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("salida", "compensation_code", compensation_code, "Compensacion lateral del perfil.", path=PROFILE_MILLING_RULE_PATH, required=True),
                _rule_value("salida", "arc_code", arc_code, "Sentido de arco de entrada/salida.", path=PROFILE_MILLING_RULE_PATH, required=True),
            )
        ),
        trace=_line_trace_moves(snapshot, operation),
        xiso_statement="G1",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Traza de perfil cerrado E001 derivada de geometria nominal y toolpaths Maestro.",),
    )

    reset_stage = StateStage(
        key="profile_milling_reset",
        family="profile_milling",
        order_index=order_index + 2,
        target_state=StateVector(),
        reset_state=StateVector(
            (
                StateValue(
                    layer="herramienta",
                    key="active",
                    value=False,
                    source=EvidenceSource("observed_rule", PROFILE_MILLING_RULE_PATH, "profile_milling_reset"),
                    confidence="observed",
                ),
                StateValue(
                    layer="salida",
                    key="etk_7",
                    value=0,
                    source=EvidenceSource("observed_rule", PROFILE_MILLING_RULE_PATH, "profile_milling_reset"),
                    confidence="observed",
                ),
            )
        ),
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Reset posterior observado para fresado de perfil E001.",),
    )
    return prepare_stage, trace_stage, reset_stage


def _side_drill_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
) -> tuple[StateStage, ...]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    if feature is not None and feature.replication_pattern is not None and operation is not None:
        stages: list[StateStage] = []
        for replication_index, fixed in enumerate(_replicated_side_fixed_values(feature, operation)):
            stages.extend(
                _single_side_drill_stages(
                    snapshot,
                    resolved_step,
                    order_index + (replication_index * 3),
                    fixed_override=fixed,
                    replication_index=replication_index,
                )
            )
        return tuple(stages)
    return _single_side_drill_stages(snapshot, resolved_step, order_index)


def _single_side_drill_stages(
    snapshot: PgmxSnapshot,
    resolved_step: PgmxResolvedWorkingStepSnapshot,
    order_index: int,
    *,
    fixed_override: Optional[float] = None,
    replication_index: Optional[int] = None,
) -> tuple[StateStage, ...]:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    step = resolved_step.step
    assert feature is not None
    assert operation is not None

    plane_name = feature.plane_name or ""
    policy = _SIDE_DRILL_POLICIES[plane_name]
    spindle = _embedded_spindle_by_number(snapshot, int(policy["spindle"]))
    tool = _embedded_tool_for_spindle(snapshot, spindle)
    _, center_y, _ = geometry.point if geometry and geometry.point else (0.0, 0.0, 0.0)
    target_depth = _target_depth(feature)
    extra_depth = _extra_depth(feature)
    tool_offset = _tool_offset_for_side(tool, spindle)
    rapid = float(policy["direction"]) * _side_axis_rapid_base(snapshot, policy, tool_offset)
    cut = float(policy["direction"]) * _side_axis_cut_base(
        snapshot,
        policy,
        target_depth,
        extra_depth,
        tool_offset,
    )
    fixed = fixed_override if fixed_override is not None else _side_fixed_from_toolpath(operation, policy)
    z = center_y
    feed = _drill_descent_feed(tool, spindle)

    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "side_drill", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", plane_name, f"features[{feature.id}].plane_name", required=True),
        _pgmx_value(snapshot, "trabajo", "feature_depth", target_depth, f"features[{feature.id}].depth_spec.target_depth"),
        _pgmx_value(snapshot, "trabajo", "diameter", _feature_diameter(feature), f"features[{feature.id}].diameter"),
        _pgmx_value(snapshot, "trabajo", "security_plane", operation.approach_security_plane, f"operations[{operation.id}].approach_security_plane"),
        _side_policy_value("trabajo", "side_etk8", policy["etk8"], plane_name, required=True),
        _side_policy_value("herramienta", "spindle", policy["spindle"], plane_name, required=True),
        _side_policy_value("salida", "etk_0_mask", policy["mask"], plane_name, required=True),
        _side_policy_value("movimiento", "side_axis", policy["axis"], plane_name, required=True),
        _side_policy_value("movimiento", "side_direction", policy["direction"], plane_name),
        _side_policy_value("movimiento", "side_coordinate_sign", policy["coordinate_sign"], plane_name),
        _contract_value("salida", "xiso_statement", "B", "Taladro lateral XISO candidato."),
    ]
    if replication_index is not None:
        prepare_values.append(
            _rule_value(
                "trabajo",
                "replication_index",
                replication_index,
                "Indice expandido desde ReplicateFeature lateral.",
                path=SIDE_DRILL_RULE_PATH,
                required=True,
            )
        )
    prepare_values.extend(_side_tool_values(snapshot, tool, spindle))

    prepare_stage = StateStage(
        key="side_drill_prepare",
        family="side_drill",
        order_index=order_index,
        target_state=StateVector(tuple(prepare_values)),
        xiso_statement="B",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Preparacion de estado antes de ejecutar la traza de taladro lateral.",),
    )

    trace_stage = StateStage(
        key="side_drill_trace",
        family="side_drill",
        order_index=order_index + 1,
        target_state=StateVector(
            (
                _pgmx_value(snapshot, "movimiento", "toolpath_count", len(operation.toolpaths), f"operations[{operation.id}].toolpaths"),
                _rule_value(
                    "movimiento",
                    "side_iso_rule",
                    "axis rapid/cut from side spindle and local point",
                    "Regla candidata para fixtures Side Drill 010..013.",
                    path=SIDE_DRILL_RULE_PATH,
                ),
                _side_policy_value("movimiento", "side_axis", policy["axis"], plane_name, required=True),
                _rule_value("movimiento", "side_rapid", rapid, "Cota rapida lateral calculada.", path=SIDE_DRILL_RULE_PATH, required=True),
                _rule_value("movimiento", "side_cut", cut, "Cota de corte lateral calculada.", path=SIDE_DRILL_RULE_PATH, required=True),
                _rule_value("movimiento", "side_fixed", fixed, "Cota fija lateral desde toolpath Maestro.", path=SIDE_DRILL_RULE_PATH, required=True),
                _pgmx_value(snapshot, "movimiento", "side_z", z, f"geometries[{geometry.id if geometry else ''}].point[1]", required=True),
                _rule_value("movimiento", "side_feed", feed, "Feed lateral desde DescentSpeed.Standard * 1000.", path=SIDE_DRILL_RULE_PATH, required=True),
            )
        ),
        trace=_side_trace_moves(snapshot, operation, rapid, cut, fixed, z, feed),
        xiso_statement="B",
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Traza lateral derivada de punto/plano PGMX y spindle lateral D8.",),
    )

    reset_stage = StateStage(
        key="side_drill_reset",
        family="side_drill",
        order_index=order_index + 2,
        target_state=StateVector(),
        reset_state=StateVector(
            (
                StateValue(
                    layer="salida",
                    key="etk_17",
                    value=0,
                    source=EvidenceSource(
                        "machine_config",
                        NCI_CFG_PATH,
                        "$GEN_END ?%%ETK[17]=0",
                        note=NCI_ORI_CFG_PATH,
                    ),
                    confidence="observed",
                    note="Reset comun confirmado para salida de estado de cabezal.",
                    required=True,
                ),
                StateValue(
                    layer="herramienta",
                    key="active",
                    value=False,
                    source=EvidenceSource(
                        "observed_rule",
                        SIDE_DRILL_RULE_PATH,
                        "side_drill_reset",
                    ),
                    confidence="observed",
                ),
            )
        ),
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id,
        notes=("Reset posterior observado para taladro lateral.",),
    )
    return prepare_stage, trace_stage, reset_stage


def _tool_values(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> list[StateValue]:
    values: list[StateValue] = []
    tool_key = operation.tool_key
    if tool_key is not None:
        values.extend(
            [
                _pgmx_value(snapshot, "herramienta", "operation_tool_id", tool_key.id, f"operations[{operation.id}].tool_key.id"),
                _pgmx_value(snapshot, "herramienta", "operation_tool_name", tool_key.name, f"operations[{operation.id}].tool_key.name"),
            ]
        )
    if tool is not None:
        source = _tool_source(snapshot, tool, "CoreTool")
        spindle_speed = tool.technology.spindle_speed_standard
        values.extend(
            [
                StateValue("herramienta", "tool_id", tool.id, source),
                StateValue("herramienta", "tool_name", tool.name, source, required=True),
                StateValue("herramienta", "tool_key", tool.tool_key, source),
                StateValue("herramienta", "tool_offset_length", tool.tool_offset_length, source, required=True),
                StateValue("herramienta", "pilot_length", tool.pilot_length, source),
                StateValue("herramienta", "diameter", tool.diameter, source),
                StateValue(
                    "herramienta",
                    "spindle_speed_standard",
                    spindle_speed,
                    source,
                ),
                StateValue(
                    "herramienta",
                    "feed_rate_standard",
                    tool.technology.feed_rate_standard,
                    source,
                ),
                StateValue(
                    "herramienta",
                    "descent_speed_standard",
                    tool.technology.descent_speed_standard,
                    source,
                ),
            ]
        )
        if spindle_speed is not None and tool.kind == "XilogBoringUnitTool":
            values.append(
                StateValue(
                    "maquina",
                    "boring_head_speed",
                    spindle_speed,
                    source,
                    confidence="confirmed",
                    note=(
                        "Velocidad activa requerida por el BooringUnitHead; "
                        "el diferencial decide si debe emitir ETK[17]=257 y S...M3."
                    ),
                )
            )
    else:
        values.append(
            StateValue(
                layer="herramienta",
                key="embedded_tool_resolved",
                value=False,
                source=_pgmx_source(snapshot, f"operations[{operation.id}].tool_key"),
                confidence="observed",
                note="La operacion no pudo vincularse con una herramienta embebida.",
            )
        )

    if spindle is not None:
        source = _tool_source(snapshot, tool, "SpindleComponent") if tool else _pgmx_source(snapshot, "embedded_spindles")
        values.extend(
            [
                StateValue("herramienta", "spindle", spindle.spindle, source),
                StateValue("herramienta", "spindle_ref_tool_id", spindle.ref_tool_id, source),
                StateValue("herramienta", "spindle_translation_x", spindle.translation_x, source),
                StateValue("herramienta", "spindle_translation_y", spindle.translation_y, source),
                StateValue("herramienta", "spindle_translation_z", spindle.translation_z, source),
                StateValue("herramienta", "shf_x", _negative(spindle.translation_x), source, required=True),
                StateValue("herramienta", "shf_y", _negative(spindle.translation_y), source, required=True),
                StateValue("herramienta", "shf_z", _negative(spindle.translation_z), source, required=True),
            ]
        )
    return values


def _top_drill_output_values(
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> list[StateValue]:
    if spindle is None:
        return []
    return [
        StateValue(
            "salida",
            "etk_0_mask",
            2 ** (int(spindle.spindle) - 1),
            EvidenceSource(
                "observed_rule",
                "iso_state_synthesis/experiments/001_top_drill_state_table.md",
                "top_drill_etk_0_mask",
            ),
            confidence="confirmed",
            note="Mascara de agregado vertical: ETK[0] = 2 ** (spindle - 1).",
            required=True,
        )
    ]


def _side_tool_values(
    snapshot: PgmxSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> list[StateValue]:
    values: list[StateValue] = []
    source = _tool_source(snapshot, tool, "BooringUnitHead")
    if tool is not None:
        spindle_speed = _tool_spindle_speed(tool, spindle)
        values.extend(
            [
                StateValue("herramienta", "tool_id", tool.id, source),
                StateValue("herramienta", "tool_name", tool.name, source),
                StateValue("herramienta", "tool_key", tool.tool_key, source),
                StateValue("herramienta", "tool_offset_length", _tool_offset_for_side(tool, spindle), source),
                StateValue("herramienta", "pilot_length", tool.pilot_length, source),
                StateValue("herramienta", "diameter", tool.diameter, source),
                StateValue("herramienta", "spindle_speed_standard", spindle_speed, source),
                StateValue("herramienta", "feed_rate_standard", tool.technology.feed_rate_standard, source),
                StateValue("herramienta", "descent_speed_standard", _descent_speed(tool, spindle), source),
            ]
        )
        if spindle_speed is not None and tool.kind == "XilogBoringUnitTool":
            values.append(
                StateValue(
                    "maquina",
                    "boring_head_speed",
                    spindle_speed,
                    source,
                    confidence="confirmed",
                    note="Velocidad activa requerida por el BooringUnitHead lateral.",
                )
            )
    else:
        values.append(
            StateValue(
                layer="herramienta",
                key="embedded_tool_resolved",
                value=False,
                source=_pgmx_source(snapshot, "embedded_tools"),
                confidence="observed",
                note="No se encontro herramienta embebida para el spindle lateral.",
            )
        )

    if spindle is not None:
        values.extend(
            [
                StateValue("herramienta", "spindle_ref_tool_id", spindle.ref_tool_id, source),
                StateValue("herramienta", "spindle_translation_x", spindle.translation_x, source),
                StateValue("herramienta", "spindle_translation_y", spindle.translation_y, source),
                StateValue("herramienta", "spindle_translation_z", spindle.translation_z, source),
                StateValue("herramienta", "shf_x", _negative(spindle.translation_x), source, required=True),
                StateValue("herramienta", "shf_y", _negative(spindle.translation_y), source, required=True),
                StateValue("herramienta", "shf_z", _negative(spindle.translation_z), source, required=True),
            ]
        )
    return values


def _router_tool_values(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    head_shf: tuple[float, float, float],
) -> list[StateValue]:
    values: list[StateValue] = []
    source = _tool_source(snapshot, tool, "CoreTool")
    tool_name = (tool.name if tool is not None else operation.tool_key.name if operation.tool_key else "").upper()
    tool_number = int(tool_name.removeprefix("E")) if tool_name.startswith("E") else 0
    values.extend(
        [
            _pgmx_value(snapshot, "herramienta", "operation_tool_id", operation.tool_key.id if operation.tool_key else "", f"operations[{operation.id}].tool_key.id"),
            _pgmx_value(snapshot, "herramienta", "operation_tool_name", operation.tool_key.name if operation.tool_key else "", f"operations[{operation.id}].tool_key.name"),
            StateValue("herramienta", "tool_id", tool.id if tool else "", source),
            StateValue("herramienta", "tool_name", tool_name, source),
            StateValue("herramienta", "tool_number", tool_number, source, required=True),
            StateValue("herramienta", "spindle", 1, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "router_spindle"), confidence="confirmed", required=True),
            StateValue("salida", "etk_9", tool_number, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "router_tool_code"), confidence="confirmed", required=True),
            StateValue("salida", "etk_18", 1, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "router_etk18"), confidence="confirmed", required=True),
            StateValue("herramienta", "tool_offset_length", tool.tool_offset_length if tool else None, source, required=True),
            StateValue("herramienta", "diameter", tool.diameter if tool else None, source),
            StateValue("herramienta", "spindle_speed_standard", tool.technology.spindle_speed_standard if tool else None, source, required=True),
            StateValue("herramienta", "feed_rate_standard", tool.technology.feed_rate_standard if tool else None, source),
            StateValue("herramienta", "descent_speed_standard", tool.technology.descent_speed_standard if tool else None, source),
            StateValue("herramienta", "shf_x", head_shf[0], EvidenceSource("machine_config", PHEADS_CFG_PATH, "pheads[308]"), confidence="observed", required=True),
            StateValue("herramienta", "shf_y", head_shf[1], EvidenceSource("machine_config", PHEADS_CFG_PATH, "pheads[309]"), confidence="observed", required=True),
            StateValue("herramienta", "shf_z", head_shf[2], EvidenceSource("machine_config", PHEADS_CFG_PATH, "pheads[310]"), confidence="observed", required=True),
        ]
    )
    return values


def _slot_tool_values(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
    tool_radius: float,
) -> list[StateValue]:
    values: list[StateValue] = []
    source = _tool_source(snapshot, tool, "SlotSideTool")
    tool_name = tool.name if tool is not None else operation.tool_key.name if operation.tool_key else "082"
    spindle_number = spindle.spindle if spindle is not None else int(tool_name or 82)
    translation_x = float(spindle.translation_x if spindle is not None else 0.0)
    translation_y = float(spindle.translation_y if spindle is not None else 0.0)
    translation_z = float(spindle.translation_z if spindle is not None else 0.0)
    values.extend(
        [
            _pgmx_value(snapshot, "herramienta", "operation_tool_id", operation.tool_key.id if operation.tool_key else "", f"operations[{operation.id}].tool_key.id"),
            _pgmx_value(snapshot, "herramienta", "operation_tool_name", operation.tool_key.name if operation.tool_key else "", f"operations[{operation.id}].tool_key.name"),
            StateValue("herramienta", "tool_id", tool.id if tool else "", source),
            StateValue("herramienta", "tool_name", tool_name, source),
            StateValue("herramienta", "tool_number", int(tool_name), source, required=True),
            StateValue("herramienta", "spindle", spindle_number, source, required=True),
            StateValue("salida", "etk_1", 16, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "slot_saw_etk1"), confidence="confirmed", required=True),
            StateValue("salida", "etk_17", 257, EvidenceSource("observed_rule", LINE_MILLING_RULE_PATH, "slot_saw_speed_activation"), confidence="confirmed", required=True),
            StateValue("herramienta", "tool_offset_length", tool.tool_offset_length if tool else None, source, required=True),
            StateValue("herramienta", "diameter", tool.diameter if tool else None, source),
            StateValue("herramienta", "spindle_speed_standard", _tool_spindle_speed(tool, spindle), source, required=True),
            StateValue("herramienta", "feed_rate_standard", tool.technology.feed_rate_standard if tool else None, source),
            StateValue("herramienta", "descent_speed_standard", _descent_speed(tool, spindle), source),
            StateValue("herramienta", "shf_x", -translation_x, source, required=True),
            StateValue("herramienta", "shf_y", -translation_y - float(tool_radius), source, required=True),
            StateValue("herramienta", "shf_z", -translation_z, source, required=True),
        ]
    )
    return values


def _trace_moves(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    feature=None,
    *,
    xy_delta: tuple[float, float] = (0.0, 0.0),
) -> tuple[TraceMove, ...]:
    offset = tool.tool_offset_length if tool is not None else None
    feed = None
    if tool is not None:
        feed_candidates = [
            value
            for value in (
                tool.technology.feed_rate_standard,
                tool.technology.descent_speed_standard,
            )
            if value is not None
        ]
        if feed_candidates:
            feed = min(feed_candidates) * 1000.0

    moves: list[TraceMove] = []
    for toolpath in operation.toolpaths:
        source = _pgmx_source(snapshot, f"operations[{operation.id}].toolpaths[{toolpath.path_type}]")
        points: list[TracePoint] = []
        if toolpath.curve is not None:
            for point in toolpath.curve.sampled_points:
                local_z = point[2]
                iso_z = _top_drill_iso_z(local_z, offset, feature)
                points.append(
                    TracePoint(
                        x=float(point[0]) + float(xy_delta[0]),
                        y=float(point[1]) + float(xy_delta[1]),
                        local_z=local_z,
                        iso_z=iso_z,
                        source=source,
                    )
                )
        moves.append(
            TraceMove(
                name=toolpath.path_type,
                points=tuple(points),
                feed=feed if toolpath.path_type == "TrajectoryPath" else None,
                source=source,
            )
        )
    return tuple(moves)


def _top_drill_iso_z(local_z: float, offset: Optional[float], feature) -> Optional[float]:
    if offset is None:
        return None
    effective_z = local_z
    if _is_through_drill_feature(feature):
        effective_z = max(0.0, float(local_z))
    return effective_z + offset


def _side_trace_moves(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    rapid: float,
    cut: float,
    fixed: float,
    z: float,
    feed: Optional[float],
) -> tuple[TraceMove, ...]:
    moves: list[TraceMove] = []
    source = _pgmx_source(snapshot, f"operations[{operation.id}].toolpaths")
    moves.append(
        TraceMove(
            name="Approach",
            points=(TracePoint(rapid, fixed, z, z, source),),
            source=source,
        )
    )
    moves.append(
        TraceMove(
            name="TrajectoryPath",
            points=(TracePoint(cut, fixed, z, z, source),),
            feed=feed,
            source=source,
        )
    )
    moves.append(
        TraceMove(
            name="Lift",
            points=(TracePoint(rapid, fixed, z, z, source),),
            source=source,
        )
    )
    return tuple(moves)


def _line_trace_moves(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
) -> tuple[TraceMove, ...]:
    moves: list[TraceMove] = []
    for toolpath in operation.toolpaths:
        source = _pgmx_source(snapshot, f"operations[{operation.id}].toolpaths[{toolpath.path_type}]")
        points: list[TracePoint] = []
        if toolpath.curve is not None:
            for point in toolpath.curve.sampled_points:
                points.append(
                    TracePoint(
                        x=point[0],
                        y=point[1],
                        local_z=point[2],
                        iso_z=point[2] - snapshot.state.depth,
                        source=source,
                    )
                )
        moves.append(TraceMove(name=toolpath.path_type, points=tuple(points), source=source))
    return tuple(moves)


def _router_head_shifts() -> tuple[float, float, float]:
    path = Path(PHEADS_CFG_PATH)
    if not path.exists():
        path = Path(__file__).resolve().parent.parent / PHEADS_CFG_PATH

    numeric_values: list[float] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = raw_line.strip().replace(",", ".")
        if not text:
            continue
        try:
            numeric_values.append(float(text))
        except ValueError:
            continue

    if len(numeric_values) <= 310:
        raise ValueError(f"No se pudieron leer offsets router en {PHEADS_CFG_PATH}.")

    return (
        _negative(numeric_values[308]),
        _negative(numeric_values[309]),
        _negative(numeric_values[310]),
    )


def _line_points(geometry) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if geometry is None or geometry.profile is None or not geometry.profile.primitives:
        if geometry is not None and geometry.curve is not None and geometry.curve.sampled_points:
            points = geometry.curve.sampled_points
            return points[0], points[-1]
        raise ValueError("La geometria lineal E004 no contiene perfil/primitiva.")
    primitive = geometry.profile.primitives[0]
    if primitive.primitive_type != "Line":
        if geometry.curve is not None and geometry.curve.sampled_points:
            points = geometry.curve.sampled_points
            return points[0], points[-1]
        raise ValueError(f"Primitiva E004 no soportada: {primitive.primitive_type}.")
    return primitive.start_point, primitive.end_point


def _profile_center_x(geometry) -> Optional[float]:
    if geometry is None or geometry.profile is None or geometry.profile.center_point is None:
        return None
    return float(geometry.profile.center_point[0])


def _profile_center_y(geometry) -> Optional[float]:
    if geometry is None or geometry.profile is None or geometry.profile.center_point is None:
        return None
    return float(geometry.profile.center_point[1])


def _profile_contour_points(geometry) -> tuple[tuple[float, float, float], ...]:
    if geometry is None or geometry.curve is None or not geometry.curve.sampled_points:
        raise ValueError("La geometria de perfil no contiene puntos muestreados.")
    return tuple((float(x), float(y), float(z)) for x, y, z in geometry.curve.sampled_points)


def _profile_xy_points(geometry) -> tuple[tuple[float, float], ...]:
    return tuple((float(x), float(y)) for x, y, _ in _profile_contour_points(geometry))


def _toolpath_primitive_records(
    operation: PgmxOperationSnapshot,
    path_type: str,
) -> tuple[tuple[object, ...], ...]:
    for toolpath in operation.toolpaths:
        if toolpath.path_type != path_type or toolpath.curve is None:
            continue
        serializations = toolpath.curve.member_serializations
        if not serializations and toolpath.curve.serialization:
            serializations = (toolpath.curve.serialization,)
        records: list[tuple[object, ...]] = []
        for serialization in serializations:
            primitive = sp._parse_geometry_primitive(serialization)
            if primitive is None:
                continue
            center = primitive.center_point or (None, None, None)
            normal = primitive.normal_vector or (None, None, None)
            records.append(
                (
                    primitive.primitive_type,
                    float(primitive.start_point[0]),
                    float(primitive.start_point[1]),
                    float(primitive.start_point[2]),
                    float(primitive.end_point[0]),
                    float(primitive.end_point[1]),
                    float(primitive.end_point[2]),
                    None if center[0] is None else float(center[0]),
                    None if center[1] is None else float(center[1]),
                    None if center[2] is None else float(center[2]),
                    None if primitive.radius is None else float(primitive.radius),
                    None if normal[0] is None else float(normal[0]),
                    None if normal[1] is None else float(normal[1]),
                    None if normal[2] is None else float(normal[2]),
                )
            )
        return tuple(records)
    return ()


def _line_cut_z(snapshot: PgmxSnapshot, feature) -> float:
    if feature.depth_spec is not None:
        extra_depth = float(feature.depth_spec.extra_depth or 0.0)
        if feature.depth_spec.is_through:
            return -(float(snapshot.state.depth) + extra_depth)
        if feature.depth_spec.target_depth is not None:
            return -float(feature.depth_spec.target_depth)
    return -float(feature.depth_end or snapshot.state.depth)


def _is_top_drilling(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    if feature is None or operation is None:
        return False
    if not _is_round_hole_feature(feature):
        return False
    if "DrillingOperation" not in operation.operation_type:
        return False
    return (feature.plane_name or "Top") == "Top"


def _is_side_drilling(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    if feature is None or operation is None:
        return False
    if not _is_round_hole_feature(feature):
        return False
    if "DrillingOperation" not in operation.operation_type:
        return False
    if (feature.plane_name or "") not in _SIDE_DRILL_POLICIES:
        return False
    return round(float(_feature_diameter(feature) or 0.0), 3) == 8.0


def _is_slot_milling(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    if feature is None or operation is None or geometry is None:
        return False
    if "SlotSide" not in feature.feature_type and "SlotSide" not in feature.object_type:
        return False
    if (feature.plane_name or "Top") != "Top":
        return False
    if "Milling" not in operation.operation_type:
        return False
    if operation.tool_key is None or (operation.tool_key.name or "") != "082":
        return False
    if geometry.profile is None or not geometry.profile.family.startswith("Line"):
        return False
    start_point, end_point = _line_points(geometry)
    if abs(float(start_point[1]) - float(end_point[1])) >= 0.0005:
        return False
    if (feature.side_of_feature or "Center") not in {"Center", "Left", "Right"}:
        return False
    if operation.milling_strategy is not None:
        return False
    return not operation.approach.is_enabled and not operation.retract.is_enabled


def _is_line_milling(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    if feature is None or operation is None or geometry is None:
        return False
    if (feature.plane_name or "Top") != "Top":
        return False
    if not _is_router_milling_tool(operation):
        return False
    if geometry.profile is None:
        return False
    profile_family = geometry.profile.family
    if profile_family.startswith("Line"):
        return "Milling" in operation.operation_type
    is_closed_polyline = profile_family.startswith("ClosedPolyline")
    if profile_family not in {"OpenPolyline", "Circle"} and not is_closed_polyline:
        return False
    side_of_feature = feature.side_of_feature or "Center"
    if side_of_feature not in {"Center", "Left", "Right"}:
        return False
    if is_closed_polyline:
        tool_name = (operation.tool_key.name or "").upper() if operation.tool_key else ""
        if tool_name == "E001":
            return False
        if operation.milling_strategy is not None:
            return (
                operation.approach.is_enabled
                and operation.retract.is_enabled
                and operation.approach.approach_type == "Line"
                and operation.retract.retract_type == "Line"
                and operation.approach.mode == "Down"
                and operation.retract.mode == "Up"
                and "Milling" in operation.operation_type
            )
        if operation.approach.is_enabled or operation.retract.is_enabled:
            return (
                side_of_feature == "Center"
                and operation.approach.is_enabled
                and operation.retract.is_enabled
                and operation.approach.approach_type in {"Line", "Arc"}
                and operation.retract.retract_type in {"Line", "Arc"}
                and operation.approach.mode in {"Quote", "Down"}
                and operation.retract.mode in {"Quote", "Up"}
                and "Milling" in operation.operation_type
            )
        return "Milling" in operation.operation_type
    if profile_family == "Circle":
        if operation.milling_strategy is not None:
            return not operation.approach.is_enabled and not operation.retract.is_enabled and "Milling" in operation.operation_type
        if operation.approach.is_enabled or operation.retract.is_enabled:
            return (
                side_of_feature == "Center"
                and operation.approach.is_enabled
                and operation.retract.is_enabled
                and operation.approach.approach_type in {"Line", "Arc"}
                and operation.retract.retract_type in {"Line", "Arc"}
                and operation.approach.mode in {"Quote", "Down"}
                and operation.retract.mode in {"Quote", "Up"}
                and "Milling" in operation.operation_type
            )
        return "Milling" in operation.operation_type
    if operation.milling_strategy is not None:
        return (
            profile_family == "OpenPolyline"
            and side_of_feature == "Center"
            and not operation.approach.is_enabled
            and not operation.retract.is_enabled
            and operation.approach.approach_type == "Line"
            and operation.retract.retract_type == "Line"
            and operation.approach.mode == "Down"
            and operation.retract.mode == "Up"
            and "Milling" in operation.operation_type
        )
    if operation.approach.is_enabled or operation.retract.is_enabled:
        if profile_family != "OpenPolyline":
            return False
        if not operation.approach.is_enabled or not operation.retract.is_enabled:
            return False
        if operation.approach.approach_type not in {"Line", "Arc"}:
            return False
        if operation.retract.retract_type not in {"Line", "Arc"}:
            return False
        if side_of_feature == "Center":
            return (
                operation.approach.mode in {"Quote", "Down"}
                and operation.retract.mode in {"Quote", "Up"}
                and "Milling" in operation.operation_type
            )
        if side_of_feature not in {"Left", "Right"}:
            return False
        if operation.approach.mode != "Down" or operation.retract.mode != "Up":
            return False
    return "Milling" in operation.operation_type


def _is_router_milling_tool(operation: PgmxOperationSnapshot) -> bool:
    if operation.tool_key is None:
        return False
    tool_name = (operation.tool_key.name or "").upper()
    if not tool_name.startswith("E") or not tool_name[1:].isdigit():
        return False
    return "Milling" in operation.operation_type


def _is_profile_milling_e001(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    geometry = resolved_step.geometry
    if feature is None or operation is None or geometry is None:
        return False
    if (feature.plane_name or "Top") != "Top":
        return False
    if operation.tool_key is None or (operation.tool_key.name or "").upper() != "E001":
        return False
    if "Milling" not in operation.operation_type:
        return False
    if geometry.profile is None or geometry.profile.family != "ClosedPolylineMidEdgeStart":
        return False
    if operation.approach.is_enabled and operation.approach.approach_type not in {"Arc", "Line"}:
        return False
    if operation.retract.is_enabled and operation.retract.retract_type not in {"Arc", "Line"}:
        return False
    try:
        points = _profile_contour_points(geometry)
    except ValueError:
        return False
    if len(points) < 3:
        return False
    return True


def _embedded_tool_for_operation(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
) -> Optional[PgmxEmbeddedToolSnapshot]:
    tool_key = operation.tool_key
    if tool_key is None:
        return None
    tool_id = (tool_key.id or "").strip()
    tool_name = (tool_key.name or "").strip()
    if tool_name:
        name_matches = [tool for tool in snapshot.embedded_tools if tool.name == tool_name]
        if len(name_matches) == 1:
            return name_matches[0]
        key_matches = [tool for tool in snapshot.embedded_tools if tool.tool_key == tool_name]
        if len(key_matches) == 1:
            return key_matches[0]
    if tool_id:
        id_matches = [tool for tool in snapshot.embedded_tools if tool.id == tool_id]
        if len(id_matches) == 1:
            return id_matches[0]
    return None


def _embedded_top_drill_tool_for_feature(
    snapshot: PgmxSnapshot,
    feature,
) -> Optional[PgmxEmbeddedToolSnapshot]:
    diameter = _feature_diameter(feature)
    if diameter is None:
        return None
    matching_spindles = [
        spindle
        for spindle in snapshot.embedded_spindles
        if 1 <= int(spindle.spindle) < 50
        and spindle.radius is not None
        and round(float(spindle.radius) * 2.0, 3) == round(float(diameter), 3)
    ]
    if not matching_spindles:
        return None
    return _embedded_tool_for_spindle(snapshot, sorted(matching_spindles, key=lambda item: item.spindle)[0])


def _embedded_spindle_for_tool(
    snapshot: PgmxSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    operation: PgmxOperationSnapshot,
) -> Optional[PgmxEmbeddedSpindleSnapshot]:
    ref_ids = []
    if tool is not None:
        ref_ids.append(tool.id)
    elif operation.tool_key is not None:
        ref_ids.append(operation.tool_key.id)
    for spindle in snapshot.embedded_spindles:
        if spindle.ref_tool_id in ref_ids:
            return spindle
    return None


def _embedded_spindle_by_number(
    snapshot: PgmxSnapshot,
    spindle_number: int,
) -> Optional[PgmxEmbeddedSpindleSnapshot]:
    for spindle in snapshot.embedded_spindles:
        if spindle.spindle == spindle_number:
            return spindle
    return None


def _embedded_tool_for_spindle(
    snapshot: PgmxSnapshot,
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> Optional[PgmxEmbeddedToolSnapshot]:
    if spindle is None:
        return None
    for tool in snapshot.embedded_tools:
        if tool.id == spindle.ref_tool_id:
            return tool
    return None


def _pgmx_source(snapshot: PgmxSnapshot, field: str, note: str = "") -> EvidenceSource:
    return EvidenceSource("pgmx", str(snapshot.source_path), field, note)


def _pgmx_value(
    snapshot: PgmxSnapshot,
    layer: str,
    key: str,
    value: object,
    field: str,
    *,
    confidence: str = "observed",
    note: str = "",
    required: bool = False,
) -> StateValue:
    return StateValue(layer, key, value, _pgmx_source(snapshot, field), confidence, note, required)


def _rule_value(
    layer: str,
    key: str,
    value: object,
    note: str,
    *,
    path: str = "iso_state_synthesis/experiments/001_top_drill_state_table.md",
    required: bool = False,
) -> StateValue:
    return StateValue(
        layer=layer,
        key=key,
        value=value,
        source=EvidenceSource(
            "observed_rule",
            path,
            key,
            note,
        ),
        confidence="confirmed",
        note=note,
        required=required,
    )


def _contract_value(layer: str, key: str, value: object, note: str) -> StateValue:
    return StateValue(
        layer=layer,
        key=key,
        value=value,
        source=EvidenceSource("contract", XISO_CONTRACT_PATH, key),
        confidence="candidate",
        note=note,
        required=True,
    )


def _side_policy_value(
    layer: str,
    key: str,
    value: object,
    plane_name: str,
    *,
    required: bool = False,
) -> StateValue:
    return StateValue(
        layer=layer,
        key=key,
        value=value,
        source=EvidenceSource("observed_rule", SIDE_DRILL_RULE_PATH, plane_name),
        confidence="confirmed",
        note=f"Politica ISO lateral observada para {plane_name}.",
        required=required,
    )


def _tool_source(
    snapshot: PgmxSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    field: str,
) -> EvidenceSource:
    entry_name = snapshot.tooling_entry_name or "def.tlgx"
    tool_name = tool.name if tool is not None else ""
    return EvidenceSource(
        kind="pgmx_embedded_tooling",
        path=f"{snapshot.source_path}!/{entry_name}",
        field=field,
        note=tool_name,
    )


def _negative(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return -float(value)


def _target_depth(feature) -> float:
    if feature.depth_spec is not None and feature.depth_spec.target_depth is not None:
        return float(feature.depth_spec.target_depth)
    if feature.base_feature is not None and feature.base_feature.depth_end is not None:
        return float(feature.base_feature.depth_end)
    return float(feature.depth_end or 0.0)


def _extra_depth(feature) -> float:
    if feature.depth_spec is not None:
        return float(feature.depth_spec.extra_depth or 0.0)
    return 0.0


def _feature_diameter(feature) -> Optional[float]:
    if feature is None:
        return None
    if feature.diameter is not None:
        return float(feature.diameter)
    if feature.base_feature is not None and feature.base_feature.diameter is not None:
        return float(feature.base_feature.diameter)
    return None


def _is_round_hole_feature(feature) -> bool:
    if "RoundHole" in (feature.feature_type or "") or "RoundHole" in (feature.object_type or ""):
        return True
    return feature.base_feature is not None and "RoundHole" in (feature.base_feature.feature_type or "")


def _is_through_drill_feature(feature) -> bool:
    if feature is None:
        return False
    if feature.depth_spec is not None:
        return bool(feature.depth_spec.is_through)
    if feature.base_feature is not None:
        return "ThroughHoleBottom" in (feature.base_feature.bottom_condition_type or "")
    return False


def _replicated_top_points(feature, geometry) -> tuple[tuple[float, float], ...]:
    base_x, base_y, _ = geometry.point if geometry and geometry.point else (0.0, 0.0, 0.0)
    pattern = feature.replication_pattern
    if pattern is None:
        return ((float(base_x), float(base_y)),)
    column_angle = math.radians(float(pattern.rotation_angle or 0.0))
    row_angle = math.radians(float(pattern.row_layout_angle or 90.0))
    points: list[tuple[float, float]] = []
    for row in range(max(1, int(pattern.number_of_rows or 1))):
        for column in range(max(1, int(pattern.number_of_columns or 1))):
            dx = math.cos(column_angle) * float(pattern.spacing or 0.0) * column
            dy = math.sin(column_angle) * float(pattern.spacing or 0.0) * column
            dx += math.cos(row_angle) * float(pattern.row_spacing or 0.0) * row
            dy += math.sin(row_angle) * float(pattern.row_spacing or 0.0) * row
            points.append((float(base_x) + dx, float(base_y) + dy))
    return tuple(points)


def _replicated_side_fixed_values(
    feature,
    operation: PgmxOperationSnapshot,
) -> tuple[float, ...]:
    plane_name = feature.plane_name or ""
    policy = _SIDE_DRILL_POLICIES[plane_name]
    base = _side_fixed_raw_from_toolpath(operation, policy)
    pattern = feature.replication_pattern
    if pattern is None:
        return (float(policy["coordinate_sign"]) * base,)
    mirror = -1.0 if plane_name in {"Back", "Left"} else 1.0
    values: list[float] = []
    for row in range(max(1, int(pattern.number_of_rows or 1))):
        for column in range(max(1, int(pattern.number_of_columns or 1))):
            raw = base + mirror * float(pattern.spacing or 0.0) * column
            raw += mirror * float(pattern.row_spacing or 0.0) * row
            values.append(float(policy["coordinate_sign"]) * raw)
    return tuple(values)


def _side_fixed_from_toolpath(
    operation: PgmxOperationSnapshot,
    policy: dict[str, object],
) -> float:
    return float(policy["coordinate_sign"]) * _side_fixed_raw_from_toolpath(operation, policy)


def _side_fixed_raw_from_toolpath(
    operation: PgmxOperationSnapshot,
    policy: dict[str, object],
) -> float:
    for toolpath in operation.toolpaths:
        if toolpath.path_type != "Approach" or toolpath.curve is None or not toolpath.curve.sampled_points:
            continue
        point = toolpath.curve.sampled_points[0]
        if str(policy["axis"]) == "X":
            return float(point[1])
        return float(point[0])
    return 0.0


def _tool_offset_for_side(
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> float:
    if spindle is not None and spindle.pilot_length is not None:
        return float(spindle.pilot_length)
    if tool is not None and tool.pilot_length is not None:
        return float(tool.pilot_length)
    if tool is not None and tool.tool_offset_length is not None:
        return float(tool.tool_offset_length)
    return 0.0


def _tool_spindle_speed(
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> Optional[float]:
    if spindle is not None and spindle.technology.spindle_speed_standard is not None:
        return spindle.technology.spindle_speed_standard
    if tool is not None:
        return tool.technology.spindle_speed_standard
    return None


def _descent_speed(
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> Optional[float]:
    if spindle is not None and spindle.technology.descent_speed_standard is not None:
        return spindle.technology.descent_speed_standard
    if tool is not None:
        return tool.technology.descent_speed_standard
    return None


def _feed_speed(tool: Optional[PgmxEmbeddedToolSnapshot]) -> Optional[float]:
    if tool is not None:
        return tool.technology.feed_rate_standard
    return None


def _drill_descent_feed(
    tool: Optional[PgmxEmbeddedToolSnapshot],
    spindle: Optional[PgmxEmbeddedSpindleSnapshot],
) -> Optional[float]:
    descent = _descent_speed(tool, spindle)
    if descent is None:
        return None
    return descent * 1000.0


def _side_axis_rapid_base(snapshot: PgmxSnapshot, policy: dict[str, object], offset: float) -> float:
    state = snapshot.state
    clearance = 20.0 + offset
    if int(policy["direction"]) > 0:
        return (state.length if policy["axis"] == "X" else state.width) + clearance
    return clearance


def _side_axis_cut_base(
    snapshot: PgmxSnapshot,
    policy: dict[str, object],
    target_depth: float,
    extra_depth: float,
    offset: float,
) -> float:
    state = snapshot.state
    clearance = offset - target_depth - extra_depth
    if int(policy["direction"]) > 0:
        return (state.length if policy["axis"] == "X" else state.width) + clearance
    return clearance
