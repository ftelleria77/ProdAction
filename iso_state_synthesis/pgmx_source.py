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
    if _is_side_drilling(resolved_step):
        return _side_drill_stages(snapshot, resolved_step, order_index), ()
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
        trace=_trace_moves(snapshot, operation, tool, feature),
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
        _pgmx_value(snapshot, "trabajo", "side_of_feature", feature.side_of_feature, f"features[{feature.id}].side_of_feature"),
        _pgmx_value(snapshot, "trabajo", "tool_width", tool_width, f"features[{feature.id}].tool_width"),
        _pgmx_value(snapshot, "trabajo", "security_plane", security_plane, f"operations[{operation.id}].approach_security_plane"),
        _pgmx_value(snapshot, "trabajo", "strategy", type(strategy).__name__ if strategy else "", f"operations[{operation.id}].milling_strategy"),
        _pgmx_value(snapshot, "trabajo", "overcut_length", operation.overcut_length, f"operations[{operation.id}].overcut_length", required=True),
        _pgmx_value(snapshot, "trabajo", "approach_enabled", operation.approach.is_enabled, f"operations[{operation.id}].approach.enabled", required=True),
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
    step = resolved_step.step
    assert feature is not None
    assert operation is not None

    plane_name = feature.plane_name or ""
    policy = _SIDE_DRILL_POLICIES[plane_name]
    spindle = _embedded_spindle_by_number(snapshot, int(policy["spindle"]))
    tool = _embedded_tool_for_spindle(snapshot, spindle)
    center_x, center_y, _ = geometry.point if geometry and geometry.point else (0.0, 0.0, 0.0)
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
    fixed = float(policy["coordinate_sign"]) * center_x
    z = center_y
    feed = _drill_descent_feed(tool, spindle)

    prepare_values = [
        _pgmx_value(snapshot, "trabajo", "family", "side_drill", f"features[{feature.id}]"),
        _pgmx_value(snapshot, "trabajo", "plane", plane_name, f"features[{feature.id}].plane_name"),
        _pgmx_value(snapshot, "trabajo", "feature_depth", target_depth, f"features[{feature.id}].depth_spec.target_depth"),
        _pgmx_value(snapshot, "trabajo", "diameter", feature.diameter, f"features[{feature.id}].diameter"),
        _pgmx_value(snapshot, "trabajo", "security_plane", operation.approach_security_plane, f"operations[{operation.id}].approach_security_plane"),
        _side_policy_value("trabajo", "side_etk8", policy["etk8"], plane_name),
        _side_policy_value("herramienta", "spindle", policy["spindle"], plane_name),
        _side_policy_value("salida", "etk_0_mask", policy["mask"], plane_name),
        _side_policy_value("movimiento", "side_axis", policy["axis"], plane_name),
        _side_policy_value("movimiento", "side_direction", policy["direction"], plane_name),
        _side_policy_value("movimiento", "side_coordinate_sign", policy["coordinate_sign"], plane_name),
        _contract_value("salida", "xiso_statement", "B", "Taladro lateral XISO candidato."),
    ]
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
                _rule_value("movimiento", "side_rapid", rapid, "Cota rapida lateral calculada.", path=SIDE_DRILL_RULE_PATH),
                _rule_value("movimiento", "side_cut", cut, "Cota de corte lateral calculada.", path=SIDE_DRILL_RULE_PATH),
                _pgmx_value(snapshot, "movimiento", "side_fixed", fixed, f"geometries[{geometry.id if geometry else ''}].point[0]"),
                _pgmx_value(snapshot, "movimiento", "side_z", z, f"geometries[{geometry.id if geometry else ''}].point[1]"),
                _rule_value("movimiento", "side_feed", feed, "Feed lateral desde DescentSpeed.Standard * 1000.", path=SIDE_DRILL_RULE_PATH),
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


def _trace_moves(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
    tool: Optional[PgmxEmbeddedToolSnapshot],
    feature=None,
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


def _top_drill_iso_z(local_z: float, offset: Optional[float], feature) -> Optional[float]:
    if offset is None:
        return None
    effective_z = local_z
    if feature is not None and feature.depth_spec is not None and feature.depth_spec.is_through:
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
    if "RoundHole" not in feature.feature_type:
        return False
    if "DrillingOperation" not in operation.operation_type:
        return False
    return (feature.plane_name or "Top") == "Top"


def _is_side_drilling(resolved_step: PgmxResolvedWorkingStepSnapshot) -> bool:
    feature = resolved_step.feature
    operation = resolved_step.operation
    if feature is None or operation is None:
        return False
    if "RoundHole" not in feature.feature_type:
        return False
    if "DrillingOperation" not in operation.operation_type:
        return False
    if (feature.plane_name or "") not in _SIDE_DRILL_POLICIES:
        return False
    return round(float(feature.diameter or 0.0), 3) == 8.0


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
    if profile_family not in {"OpenPolyline", "Circle"}:
        return False
    if (feature.side_of_feature or "Center") != "Center":
        return False
    if operation.milling_strategy is not None:
        return False
    if operation.approach.is_enabled or operation.retract.is_enabled:
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
    return float(feature.depth_end or 0.0)


def _extra_depth(feature) -> float:
    if feature.depth_spec is not None:
        return float(feature.depth_spec.extra_depth or 0.0)
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
