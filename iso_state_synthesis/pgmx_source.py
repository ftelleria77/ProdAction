"""Build state synthesis plans from Maestro `.pgmx` snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

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
    for resolved_step in snapshot.resolved_working_steps:
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
    feature = resolved_step.feature
    operation = resolved_step.operation
    step = resolved_step.step
    assert feature is not None
    assert operation is not None

    tool = _embedded_tool_for_operation(snapshot, operation)
    spindle = _embedded_spindle_for_tool(snapshot, tool, operation)
    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "top_drill", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", feature.plane_name or "Top", f"features[{feature.id}].plane_name"),
        _pgmx_value(snapshot, "trabajo", "feature_depth", feature.depth_end, f"features[{feature.id}].depth_end"),
        _pgmx_value(snapshot, "trabajo", "security_plane", operation.approach_security_plane, f"operations[{operation.id}].approach_security_plane"),
        _contract_value("salida", "xiso_statement", "B", "Taladro/foratura XISO candidata."),
    ]
    prepare_values.extend(_tool_values(snapshot, operation, tool, spindle))

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
        trace=_trace_moves(snapshot, operation, tool),
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
                StateValue("herramienta", "tool_name", tool.name, source),
                StateValue("herramienta", "tool_key", tool.tool_key, source),
                StateValue("herramienta", "tool_offset_length", tool.tool_offset_length, source),
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
                StateValue("herramienta", "shf_x", _negative(spindle.translation_x), source),
                StateValue("herramienta", "shf_y", _negative(spindle.translation_y), source),
                StateValue("herramienta", "shf_z", _negative(spindle.translation_z), source),
            ]
        )
    return values


def _trace_moves(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
) -> tuple[TraceMove, ...]:
    offset = tool.tool_offset_length if tool is not None else None
    feed = None
    if tool is not None and tool.technology.descent_speed_standard is not None:
        feed = tool.technology.descent_speed_standard * 1000.0

    moves: list[TraceMove] = []
    for toolpath in operation.toolpaths:
        source = _pgmx_source(snapshot, f"operations[{operation.id}].toolpaths[{toolpath.path_type}]")
        points: list[TracePoint] = []
        if toolpath.curve is not None:
            for point in toolpath.curve.sampled_points:
                local_z = point[2]
                iso_z = local_z + offset if offset is not None else None
                points.append(
                    TracePoint(
                        x=point[0],
                        y=point[1],
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


def _is_top_drilling(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    if feature is None or operation is None:
        return False
    if "RoundHole" not in feature.feature_type:
        return False
    if "DrillingOperation" not in operation.operation_type:
        return False
    return (feature.plane_name or "Top") == "Top"


def _embedded_tool_for_operation(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
) -> Optional[PgmxEmbeddedToolSnapshot]:
    tool_key = operation.tool_key
    if tool_key is None:
        return None
    candidates = (tool_key.id, tool_key.name)
    for tool in snapshot.embedded_tools:
        if tool.id in candidates or tool.name in candidates or tool.tool_key in candidates:
            return tool
    return None


def _embedded_spindle_for_tool(
    snapshot: PgmxSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    operation: PgmxOperationSnapshot,
) -> Optional[PgmxEmbeddedSpindleSnapshot]:
    ref_ids = []
    if tool is not None:
        ref_ids.append(tool.id)
    if operation.tool_key is not None:
        ref_ids.append(operation.tool_key.id)
    for spindle in snapshot.embedded_spindles:
        if spindle.ref_tool_id in ref_ids:
            return spindle
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
) -> StateValue:
    return StateValue(layer, key, value, _pgmx_source(snapshot, field), confidence, note)


def _rule_value(layer: str, key: str, value: object, note: str) -> StateValue:
    return StateValue(
        layer=layer,
        key=key,
        value=value,
        source=EvidenceSource(
            "observed_rule",
            "iso_state_synthesis/experiments/001_top_drill_state_table.md",
            key,
            note,
        ),
        confidence="confirmed",
        note=note,
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
