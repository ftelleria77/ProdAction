"""Pocket milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Sequence

from ..common.depth import (
    MillingDepthSpec,
    _extract_depth_spec_from_template,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.geometry import (
    _CurveSpec,
    _build_boundary_curve_holder,
    _build_closed_polyline_geometry_profile,
    _build_geometry_from_curve_spec,
    _build_maestro_arc_serialization,
    _build_start_point,
    _build_toolpath,
    _build_toolpath_description,
    _composite_curve_spec,
    _curve_spec_from_composite_curve_node,
    _curve_spec_from_profile_geometry,
    _curve_spec_from_toolpath_node,
    _curve_spec_points,
    _geometry_object_type,
    _is_closed_polyline_points,
    _trimmed_curve_spec,
)
from ..common.hydration import _load_pgmx_container
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.piece import _normalize_plane_name, _workpiece_depth_name
from ..common.strategy import (
    ContourParallelMillingStrategySpec,
    _extract_milling_strategy_spec_from_operation,
    _build_milling_strategy_node,
    _strategy_comparison_key,
    build_contour_parallel_milling_strategy_spec,
)
from ..common.xml import (
    BASE_MODEL_NS,
    MILLING_NS,
    PGMX_NS,
    STRATEGY_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _build_depth_expression,
    _build_property_expression,
    _build_working_step,
    _compact_number,
    _find_plane_ref,
    _qname,
    _reserve_ids,
    _safe_float,
    _set_xmlns,
    _text,
    _xsi_type,
)
from ._common import _feature_depth_value, _operation_overcut_length, _uses_feature_depth_expressions
from .pocket_rectangular import generate_rectangular_contour_parallel_xyz_path
from .pocket_trace import generate_contour_parallel_pocket_trace

if TYPE_CHECKING:
    from ..common.program import PgmxState

__all__ = [
    "PocketBossRouteSeedSpec",
    "PocketMillingSpec",
    "build_pocket_boss_route_seed_spec",
    "build_pocket_milling_spec",
    "_HydratedPocketMillingSpec",
    "_SingleSeedMultiloopRoute",
    "_append_pocket_milling",
    "_build_closed_pocket_boss",
    "_build_closed_pocket_feature",
    "_build_contour_parallel_xyz_path",
    "_build_pocket_operation",
    "_build_pocket_trajectory_curve_specs",
    "_build_pocket_trajectory_xyz_sequences",
    "_build_trace_engine_pocket_curve_specs",
    "_build_trace_engine_pocket_plan",
    "_build_trace_engine_pocket_xyz_sequences",
    "_build_single_seed_base_loop_xyz_sequences",
    "_build_single_seed_bridge_only_curve_and_sequence",
    "_build_single_seed_multiloop_curve_and_sequence",
    "_curve_spec_from_xyz_path",
    "_curve_spec_from_trace_resolved_sequence",
    "_points_are_close_3d",
    "_rounded_kernel_loop_curve_spec",
    "_rounded_kernel_loop_xy",
    "_rounded_kernel_multi_loop_curve_spec",
    "_same_xy_bbox",
    "_single_seed_base_loop_radii",
    "_single_seed_exterior_rectangle_loops_xyz",
    "_supported_single_seed_base_loop_route_seed",
    "_supported_single_seed_base_loop_seed",
    "_supported_single_seed_multiloop_route",
    "_supported_single_seed_route_seed",
    "_xy_bbox_minmax",
    "_can_hydrate_pocket_template_trace",
    "_extract_pocket_milling_template",
    "_hydrate_pocket_milling_spec",
    "_same_xy_contours",
    "_same_xy_points",
]


@dataclass(frozen=True)
class PocketBossRouteSeedSpec:
    """Referencia de `BossList.GeometryID` usada por Maestro como semilla de ruta.

    `contour_points` queda vacio cuando el `GeometryID` no se pudo resolver en
    el archivo. La isla fisica sigue viviendo en `PocketMillingSpec.boss_contours`.
    """

    geometry_id: str
    object_type: str = ""
    name: str = ""
    contour_points: tuple[tuple[float, float], ...] = ()

    @property
    def is_resolved(self) -> bool:
        return bool(self.contour_points)


@dataclass(frozen=True)
class PocketMillingSpec:
    """Vaciado superior observado como `ClosedPocket` + `ContourParallel`.

    El subset productivo validado cubre contornos rectangulares lineales sobre
    `Top`, con trayectorias `ContourParallel` equivalentes a Maestro.
    """

    contour_points: tuple[tuple[float, float], ...]
    feature_name: str = "Vaciado"
    plane_name: str = "Top"
    tool_id: str = "1900"
    tool_name: str = "E001"
    tool_width: float = 18.36
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    milling_strategy: ContourParallelMillingStrategySpec = field(
        default_factory=ContourParallelMillingStrategySpec
    )
    allowance_bottom: float = 0.0
    allowance_side: float = 0.0
    boss_contours: tuple[tuple[tuple[float, float], ...], ...] = ()
    boss_route_seeds: tuple[PocketBossRouteSeedSpec, ...] = ()
    is_enabled_expr: Optional[str] = None

    @property
    def effective_contour_offset(self) -> float:
        return (float(self.tool_width) / 2.0) + float(self.allowance_side)

    @property
    def radial_step(self) -> float:
        return float(self.tool_width) * (1.0 - float(self.milling_strategy.overlap))

    @property
    def has_bosses(self) -> bool:
        return bool(self.boss_contours)

    @property
    def has_boss_route_seeds(self) -> bool:
        return bool(self.boss_route_seeds)

    @property
    def resolved_boss_route_seed_contours(self) -> tuple[tuple[tuple[float, float], ...], ...]:
        return tuple(seed.contour_points for seed in self.boss_route_seeds if seed.is_resolved)


@dataclass(frozen=True)
class _HydratedPocketMillingSpec:
    """Datos internos de serializacion para un `PocketMillingSpec` rectangular."""

    spec: PocketMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    trajectory_curves: tuple[_CurveSpec, ...] = ()
    trajectory_sequences: tuple[tuple[tuple[float, float, float], ...], ...] = ()

    @property
    def contour_points(self) -> tuple[tuple[float, float], ...]:
        return self.spec.contour_points

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract

    @property
    def milling_strategy(self) -> ContourParallelMillingStrategySpec:
        return self.spec.milling_strategy

    @property
    def allowance_bottom(self) -> float:
        return self.spec.allowance_bottom

    @property
    def allowance_side(self) -> float:
        return self.spec.allowance_side

    @property
    def boss_contours(self) -> tuple[tuple[tuple[float, float], ...], ...]:
        return self.spec.boss_contours

    @property
    def boss_route_seeds(self) -> tuple[PocketBossRouteSeedSpec, ...]:
        return self.spec.boss_route_seeds

    @property
    def effective_contour_offset(self) -> float:
        return self.spec.effective_contour_offset

    @property
    def radial_step(self) -> float:
        return self.spec.radial_step

    @property
    def is_enabled_expr(self) -> Optional[str]:
        return self.spec.is_enabled_expr


def _append_pocket_milling(root: ET.Element, state: PgmxState, spec: _HydratedPocketMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el Vaciado.")

    if not _is_closed_polyline_points(spec.contour_points):
        raise ValueError("PocketMillingSpec requiere un contorno cerrado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)
    has_enabled_expr = spec.is_enabled_expr is not None
    depth_block = 2 if uses_depth_expressions else 0
    enabled_block = 1 if has_enabled_expr else 0

    trajectory_sequences = _build_pocket_trajectory_xyz_sequences(state, spec)
    boundary_curve = spec.geometry_curve or _curve_spec_from_profile_geometry(
        _build_closed_polyline_geometry_profile(spec.contour_points, z_value=0.0)
    )
    boundary_member_count = len(boundary_curve.member_serializations)
    boss_geometry_curves = tuple(
        _curve_spec_from_profile_geometry(_build_closed_polyline_geometry_profile(boss_contour, z_value=0.0))
        for boss_contour in spec.boss_contours
    )
    boss_geometry_member_count = sum(len(curve.member_serializations) for curve in boss_geometry_curves)
    route_seed_curves = tuple(
        _curve_spec_from_profile_geometry(_build_closed_polyline_geometry_profile(seed.contour_points, z_value=0.0))
        for seed in spec.boss_route_seeds
        if seed.is_resolved
    )
    route_seed_member_count = sum(1 + len(curve.member_serializations) for curve in route_seed_curves)
    trajectory_curves = _build_pocket_trajectory_curve_specs(spec, trajectory_sequences)
    trajectory_member_counts = tuple(len(curve.member_serializations) for curve in trajectory_curves)
    trajectory_member_count = sum(trajectory_member_counts)
    reserve_count = (
        1
        + boundary_member_count
        + boss_geometry_member_count
        + route_seed_member_count
        + 3
        + depth_block
        + enabled_block
        + trajectory_member_count
    )
    reserved_ids = _reserve_ids(root, reserve_count, spec.preferred_id_start)
    geometry_id = reserved_ids[0]
    boundary_member_keys = tuple(reserved_ids[1 : 1 + boundary_member_count])
    cursor = 1 + boundary_member_count
    boss_geometry_specs: list[tuple[_CurveSpec, tuple[str, ...]]] = []
    for boss_curve in boss_geometry_curves:
        boss_member_keys = tuple(reserved_ids[cursor : cursor + len(boss_curve.member_serializations)])
        cursor += len(boss_curve.member_serializations)
        boss_geometry_specs.append((boss_curve, boss_member_keys))
    route_seed_geometry_specs: list[tuple[PocketBossRouteSeedSpec, str, _CurveSpec, tuple[str, ...]]] = []
    for seed, curve in zip((seed for seed in spec.boss_route_seeds if seed.is_resolved), route_seed_curves):
        seed_geometry_id = reserved_ids[cursor]
        cursor += 1
        seed_member_keys = tuple(reserved_ids[cursor : cursor + len(curve.member_serializations)])
        cursor += len(curve.member_serializations)
        route_seed_geometry_specs.append((seed, seed_geometry_id, curve, seed_member_keys))
    operation_index = cursor
    operation_id = reserved_ids[operation_index]
    feature_id = reserved_ids[operation_index + 1]
    step_id = reserved_ids[operation_index + 2]
    start_expression_id = reserved_ids[operation_index + 3] if uses_depth_expressions else None
    end_expression_id = reserved_ids[operation_index + 4] if uses_depth_expressions else None
    enabled_expr_id = reserved_ids[operation_index + 3 + depth_block] if has_enabled_expr else None
    trajectory_index = operation_index + 3 + depth_block + enabled_block
    trajectory_member_keys: list[tuple[str, ...]] = []
    cursor = trajectory_index
    for member_count in trajectory_member_counts:
        trajectory_member_keys.append(tuple(reserved_ids[cursor : cursor + member_count]))
        cursor += member_count

    geometries.append(
        _build_geometry_from_curve_spec(
            geometry_id,
            plane_id,
            plane_object_type,
            boundary_curve,
            generated_member_keys=boundary_curve.member_keys or boundary_member_keys,
        )
    )
    for _seed, seed_geometry_id, seed_curve, seed_member_keys in route_seed_geometry_specs:
        geometries.append(
            _build_geometry_from_curve_spec(
                seed_geometry_id,
                plane_id,
                plane_object_type,
                seed_curve,
                generated_member_keys=seed_curve.member_keys or seed_member_keys,
            )
        )
    features.append(
        _build_closed_pocket_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            _geometry_object_type(boundary_curve.geometry_type),
            boundary_curve,
            boundary_curve.member_keys or boundary_member_keys,
            boss_geometry_curves=tuple(
                (boss_curve, boss_curve.member_keys or boss_member_keys)
                for boss_curve, boss_member_keys in boss_geometry_specs
            ),
            boss_route_seed_refs=tuple(
                (
                    seed,
                    seed_geometry_id,
                    _geometry_object_type(seed_curve.geometry_type),
                )
                for seed, seed_geometry_id, seed_curve, _seed_member_keys in route_seed_geometry_specs
            ),
        )
    )
    operations.append(
        _build_pocket_operation(
            state,
            spec,
            operation_id,
            trajectory_curves,
            tuple(
                trajectory_curve.member_keys or member_keys
                for trajectory_curve, member_keys in zip(trajectory_curves, trajectory_member_keys)
            ),
            trajectory_sequences,
        )
    )
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.ClosedPocket",
            operation_object_type="ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideRoughMilling",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))
    if has_enabled_expr and enabled_expr_id is not None:
        expressions.append(
            _build_property_expression(
                enabled_expr_id,
                step_id,
                "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep",
                "IsEnabled",
                spec.is_enabled_expr,
            )
        )


def _build_closed_pocket_feature(
    state,
    spec: _HydratedPocketMillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    geometry_object_type: str,
    boundary_curve: _CurveSpec,
    boundary_member_keys: Sequence[str],
    boss_geometry_curves: Sequence[tuple[_CurveSpec, Sequence[str]]] = (),
    boss_route_seed_refs: Sequence[tuple[PocketBossRouteSeedSpec, str, str]] = (),
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:ClosedPocket"},
    )
    _set_xmlns(feature, "a", BASE_MODEL_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.ClosedPocket")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(feature, PGMX_NS, "GeometryID", geometry_id, geometry_object_type)
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideRoughMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": "a:PlanarPocketBottomCondition"},
    )
    _set_xmlns(bottom_condition, "a", BASE_MODEL_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    boss_geometry_list = _append_node(feature, BASE_MODEL_NS, "BossGeometryList")
    for boss_curve, boss_member_keys in boss_geometry_curves:
        boss_geometry_list.append(_build_boundary_curve_holder(boss_curve, boss_member_keys))
    boss_list = _append_node(feature, BASE_MODEL_NS, "BossList")
    for route_seed, route_seed_geometry_id, route_seed_object_type in boss_route_seed_refs:
        boss_list.append(
            _build_closed_pocket_boss(
                route_seed,
                route_seed_geometry_id,
                route_seed_object_type,
                workpiece_id,
                workpiece_object_type,
            )
        )
    boundary_list = _append_node(feature, BASE_MODEL_NS, "BoundaryGeometryList")
    boundary_list.append(_build_boundary_curve_holder(boundary_curve, boundary_member_keys))
    _append_node(feature, BASE_MODEL_NS, "OrthogonalRadius", "0")
    _append_node(feature, BASE_MODEL_NS, "PlanarRadius", "0")
    _append_node(feature, BASE_MODEL_NS, "Slope", "0")
    return feature


def _build_closed_pocket_boss(
    route_seed: PocketBossRouteSeedSpec,
    geometry_id: str,
    geometry_object_type: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    boss = ET.Element(_qname(BASE_MODEL_NS, "Boss"))
    _append_key(boss, "0", "System.Object")
    _append_blank_name(boss).text = route_seed.name or "Boss"
    _append_object_ref(boss, PGMX_NS, "GeometryID", geometry_id, geometry_object_type)
    _append_node(boss, PGMX_NS, "OperationIDs")
    _append_object_ref(boss, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    _append_node(boss, PGMX_NS, "BottomCondition", attrib={f"{{{XSI_NS}}}nil": "true"})
    depth = _append_node(boss, PGMX_NS, "Depth")
    _append_node(depth, PGMX_NS, "EndDepth", "0")
    _append_node(depth, PGMX_NS, "StartDepth", "0")
    _append_node(boss, BASE_MODEL_NS, "Slope", "0")
    return boss


def _build_pocket_operation(
    state,
    spec: _HydratedPocketMillingSpec,
    operation_id: str,
    trajectory_curves: Sequence[_CurveSpec],
    trajectory_curve_member_keys: Sequence[Sequence[str]],
    trajectory_sequences: Sequence[Sequence[tuple[float, float, float]]],
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:BottomAndSideRoughMilling"},
    )
    _set_xmlns(operation, "a", MILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideRoughMilling")
    _append_blank_name(operation)
    _append_node(operation, PGMX_NS, "ActivateCNCCorrection", "false")
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)

    if not trajectory_sequences:
        raise ValueError("La estrategia ContourParallel no genero trayectoria para el Vaciado.")
    first_sequence = trajectory_sequences[0]
    last_sequence = trajectory_sequences[-1]
    if not first_sequence or not last_sequence:
        raise ValueError("La estrategia ContourParallel genero una trayectoria vacia para el Vaciado.")
    first_point = first_sequence[0]
    last_point = last_sequence[-1]
    clearance_z = state.depth + spec.security_plane
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            _trimmed_curve_spec(
                _build_toolpath_description(
                    (first_point[0], first_point[1], clearance_z),
                    first_point,
                )
            ),
        )
    )
    if len(trajectory_curves) != len(trajectory_curve_member_keys):
        raise ValueError("Cantidad inconsistente de curvas y claves de trayectoria para Vaciado.")
    for trajectory_curve, member_keys in zip(trajectory_curves, trajectory_curve_member_keys):
        toolpath_list.append(
            _build_toolpath(
                "TrajectoryPath",
                trajectory_curve,
                generated_member_keys=member_keys,
            )
        )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            _trimmed_curve_spec(
                _build_toolpath_description(
                    last_point,
                    (last_point[0], last_point[1], clearance_z),
                )
            ),
        )
    )
    _append_node(operation, PGMX_NS, "ToolpathPriority", "true")
    _append_node(operation, PGMX_NS, "AdditionalToolKeys", "")
    _append_node(operation, PGMX_NS, "ApproachSecurityPlane", _compact_number(spec.security_plane))
    _append_node(operation, PGMX_NS, "Head", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(operation, PGMX_NS, "HeadRotation", "0")
    _append_node(operation, PGMX_NS, "MachineFunctions", "")
    _append_node(operation, PGMX_NS, "RetractSecurityPlane", _compact_number(spec.security_plane))
    operation.append(_build_start_point(0.0, 0.0, 0.0))
    technology = _append_node(
        operation,
        PGMX_NS,
        "Technology",
        attrib={f"{{{XSI_NS}}}type": "MillingTechnology"},
    )
    _append_node(technology, PGMX_NS, "Feedrate", "0")
    _append_node(technology, PGMX_NS, "CutSpeed", "0")
    _append_node(technology, PGMX_NS, "Spindle", "0")
    _append_object_ref(
        operation,
        PGMX_NS,
        "ToolKey",
        spec.tool_id,
        "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
        include_name=True,
        name_text=spec.tool_name,
    )
    _append_node(operation, PGMX_NS, "OvercutLength", _compact_number(_operation_overcut_length(spec)))
    approach = _append_node(
        operation,
        PGMX_NS,
        "Approach",
        attrib={f"{{{XSI_NS}}}type": "b:BaseApproachStrategy"},
    )
    _set_xmlns(approach, "b", STRATEGY_NS)
    _append_node(approach, STRATEGY_NS, "ApproachArcSide", spec.approach.arc_side)
    _append_node(approach, STRATEGY_NS, "ApproachMode", spec.approach.mode)
    _append_node(approach, STRATEGY_NS, "ApproachType", spec.approach.approach_type)
    _append_node(approach, STRATEGY_NS, "IsEnabled", "true" if spec.approach.is_enabled else "false")
    _append_node(approach, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.approach.radius_multiplier))
    _append_node(approach, STRATEGY_NS, "Speed", _compact_number(spec.approach.speed))
    retract = _append_node(
        operation,
        PGMX_NS,
        "Retract",
        attrib={f"{{{XSI_NS}}}type": "b:BaseRetractStrategy"},
    )
    _set_xmlns(retract, "b", STRATEGY_NS)
    _append_node(retract, STRATEGY_NS, "IsEnabled", "true" if spec.retract.is_enabled else "false")
    _append_node(retract, STRATEGY_NS, "OverLap", _compact_number(spec.retract.overlap))
    _append_node(retract, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.retract.radius_multiplier))
    _append_node(retract, STRATEGY_NS, "RetractArcSide", spec.retract.arc_side)
    _append_node(retract, STRATEGY_NS, "RetractMode", spec.retract.mode)
    _append_node(retract, STRATEGY_NS, "RetractType", spec.retract.retract_type)
    _append_node(retract, STRATEGY_NS, "Speed", _compact_number(spec.retract.speed))
    operation.append(_build_milling_strategy_node(spec))
    _append_node(operation, PGMX_NS, "AllowanceBottom", _compact_number(spec.allowance_bottom))
    _append_node(operation, PGMX_NS, "AllowanceSide", _compact_number(spec.allowance_side))
    return operation


def _build_contour_parallel_xyz_path(
    state,
    spec: _HydratedPocketMillingSpec,
) -> tuple[tuple[float, float, float], ...]:
    strategy = spec.milling_strategy
    return generate_rectangular_contour_parallel_xyz_path(
        length=state.length,
        width=state.width,
        depth=state.depth,
        contour_points=spec.contour_points,
        tool_width=spec.tool_width,
        target_depth=float(_feature_depth_value(state, spec)),
        security_plane=spec.security_plane,
        allowance_side=spec.allowance_side,
        overlap=strategy.overlap,
        radial_cutting_depth=strategy.radial_cutting_depth,
        rotation_direction=strategy.rotation_direction,
        inside_to_outside=strategy.inside_to_outside,
        stroke_connection_strategy=strategy.stroke_connection_strategy,
        allow_multiple_passes=strategy.allow_multiple_passes,
        axial_cutting_depth=strategy.axial_cutting_depth,
        axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
    )


def _build_trace_engine_pocket_xyz_sequences(
    state,
    spec: _HydratedPocketMillingSpec,
) -> Optional[tuple[tuple[tuple[float, float, float], ...], ...]]:
    plan = _build_trace_engine_pocket_plan(spec, surface_z=state.depth)
    if plan is None or not plan.trajectory_sequences:
        return None
    return plan.trajectory_sequences


def _build_trace_engine_pocket_curve_specs(
    spec: _HydratedPocketMillingSpec,
    trajectory_sequences: Sequence[Sequence[tuple[float, float, float]]],
) -> Optional[tuple[_CurveSpec, ...]]:
    if not trajectory_sequences:
        return None
    plan = _build_trace_engine_pocket_plan(spec, surface_z=0.0)
    if plan is None:
        return None
    if len(plan.resolved_sequences) != len(trajectory_sequences):
        return None

    curve_specs: list[_CurveSpec] = []
    for resolved_sequence, trajectory_sequence in zip(plan.resolved_sequences, trajectory_sequences):
        if not trajectory_sequence:
            return None
        z_value = float(trajectory_sequence[0][2])
        curve_specs.append(_curve_spec_from_trace_resolved_sequence(resolved_sequence, z_value))
    return tuple(curve_specs)


def _build_trace_engine_pocket_plan(
    spec: _HydratedPocketMillingSpec,
    *,
    surface_z: float,
):
    plan = generate_contour_parallel_pocket_trace(spec, surface_z=surface_z)
    if plan.pending_stages:
        return None
    if not plan.resolved_sequences:
        return None
    return plan


def _curve_spec_from_trace_resolved_sequence(resolved_sequence, z_value: float) -> _CurveSpec:
    descriptions: list[str] = []
    for primitive in resolved_sequence.primitives:
        start = (primitive.start[0], primitive.start[1], z_value)
        end = (primitive.end[0], primitive.end[1], z_value)
        if primitive.primitive_type == "Line":
            descriptions.append(_build_toolpath_description(start, end))
            continue
        if primitive.primitive_type == "Arc":
            if primitive.center is None:
                raise ValueError("La primitiva Arc de Vaciado requiere centro.")
            normal_z = -1.0 if primitive.orientation == "Clockwise" else 1.0
            descriptions.append(
                _build_maestro_arc_serialization(
                    start,
                    end,
                    primitive.center,
                    normal_z,
                    z_value,
                    radius=primitive.radius,
                )
            )
            continue
        raise ValueError(f"Tipo de primitiva de Vaciado no soportado: {primitive.primitive_type}")
    if not descriptions:
        raise ValueError("La secuencia resuelta de Vaciado no contiene primitivas serializables.")
    return _composite_curve_spec(descriptions)


def _build_single_seed_base_loop_xyz_sequences(
    state,
    spec: _HydratedPocketMillingSpec,
) -> Optional[tuple[tuple[tuple[float, float, float], ...], ...]]:
    seed = _supported_single_seed_base_loop_route_seed(spec)
    if seed is None:
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    radii = _single_seed_base_loop_radii(spec, seed)
    cut_z = state.depth - float(_feature_depth_value(state, spec))

    exterior = _single_seed_exterior_rectangle_loops_xyz(
        (contour_min_x, contour_max_x, contour_min_y, contour_max_y),
        radii,
        cut_z,
    )
    island = tuple(
        (x, y, cut_z)
        for radius in radii
        for x, y in _rounded_kernel_loop_xy(
            (seed_min_x, seed_max_x, seed_min_y, seed_max_y),
            radius,
        )
    )
    return (exterior, island)


def _rounded_kernel_loop_curve_spec(
    kernel_bbox: tuple[float, float, float, float],
    radius: float,
    z_value: float,
) -> _CurveSpec:
    min_x, max_x, min_y, max_y = kernel_bbox
    diagonal = radius / math.sqrt(2.0)
    p0 = (min_x - radius, min_y, z_value)
    p1 = (min_x - radius, max_y, z_value)
    p2 = (min_x, max_y + radius, z_value)
    p3 = (max_x, max_y + radius, z_value)
    p4 = (max_x + diagonal, max_y + diagonal, z_value)
    p5 = (max_x + radius, max_y, z_value)
    p6 = (max_x + radius, min_y, z_value)
    p7 = (max_x, min_y - radius, z_value)
    p8 = (min_x, min_y - radius, z_value)

    return _composite_curve_spec(
        [
            _build_toolpath_description(p0, p1),
            _build_maestro_arc_serialization(p1, p2, (min_x, max_y), -1.0, z_value),
            _build_toolpath_description(p2, p3),
            _build_maestro_arc_serialization(p3, p4, (max_x, max_y), -1.0, z_value),
            _build_maestro_arc_serialization(p4, p5, (max_x, max_y), -1.0, z_value),
            _build_toolpath_description(p5, p6),
            _build_maestro_arc_serialization(p6, p7, (max_x, min_y), -1.0, z_value),
            _build_toolpath_description(p7, p8),
            _build_maestro_arc_serialization(p8, p0, (min_x, min_y), -1.0, z_value),
        ]
    )


def _rounded_kernel_multi_loop_curve_spec(
    kernel_bbox: tuple[float, float, float, float],
    radii: Sequence[float],
    z_value: float,
) -> _CurveSpec:
    descriptions: list[str] = []
    previous_start: Optional[tuple[float, float, float]] = None
    min_x, _max_x, min_y, _max_y = kernel_bbox
    for radius in radii:
        loop_start = (min_x - radius, min_y, z_value)
        if previous_start is not None:
            descriptions.append(_build_toolpath_description(previous_start, loop_start))
        loop_curve = _rounded_kernel_loop_curve_spec(kernel_bbox, radius, z_value)
        descriptions.extend(loop_curve.member_serializations)
        previous_start = loop_start
    return _composite_curve_spec(descriptions)


def _single_seed_exterior_rectangle_loops_xyz(
    contour_bbox: tuple[float, float, float, float],
    radii: Sequence[float],
    cut_z: float,
) -> tuple[tuple[float, float, float], ...]:
    contour_min_x, contour_max_x, contour_min_y, contour_max_y = contour_bbox
    points: list[tuple[float, float, float]] = []
    for index, radius in enumerate(radii):
        left = contour_min_x + radius
        right = contour_max_x - radius
        bottom = contour_min_y + radius
        top = contour_max_y - radius
        next_radius = radii[index + 1] if index + 1 < len(radii) else None

        if not points:
            points.append((left, top, cut_z))
        if next_radius is not None:
            points.append((left, contour_max_y - next_radius, cut_z))
        points.extend(
            (
                (left, bottom, cut_z),
                (right, bottom, cut_z),
                (right, top, cut_z),
                (left, top, cut_z),
            )
        )
        if next_radius is not None:
            next_left = contour_min_x + next_radius
            next_top = contour_max_y - next_radius
            points.extend(
                (
                    (left, next_top, cut_z),
                    (next_left, next_top, cut_z),
                )
            )
    return tuple(points)


def _supported_single_seed_base_loop_route_seed(
    spec: _HydratedPocketMillingSpec,
) -> Optional[PocketBossRouteSeedSpec]:
    seed = _supported_single_seed_base_loop_seed(spec)
    if seed is None:
        return None
    if not _single_seed_base_loop_radii(spec, seed):
        return None
    return seed


def _supported_single_seed_base_loop_seed(
    spec: _HydratedPocketMillingSpec,
) -> Optional[PocketBossRouteSeedSpec]:
    if len(spec.boss_contours) != 1 or len(spec.boss_route_seeds) != 1:
        return None
    seed = spec.boss_route_seeds[0]
    if not seed.is_resolved:
        return None
    if not _same_xy_bbox(spec.boss_contours[0], seed.contour_points):
        return None
    if spec.plane_name != "Top" or spec.milling_strategy.allow_multiple_passes:
        return None
    if spec.milling_strategy.inside_to_outside:
        if spec.milling_strategy.stroke_connection_strategy != "LiftShiftPlunge":
            return None
    elif spec.milling_strategy.stroke_connection_strategy != "Straghtline":
        return None
    return seed


def _single_seed_base_loop_radii(
    spec: _HydratedPocketMillingSpec,
    seed: PocketBossRouteSeedSpec,
) -> tuple[float, ...]:
    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    if not math.isclose(seed_max_x - seed_min_x, 50.0, abs_tol=1e-6):
        return ()
    if not math.isclose(seed_max_y - seed_min_y, 50.0, abs_tol=1e-6):
        return ()
    clearances = (
        seed_min_x - contour_min_x,
        contour_max_x - seed_max_x,
        seed_min_y - contour_min_y,
        contour_max_y - seed_max_y,
    )
    if min(clearances) <= 0.0:
        return ()
    if not math.isclose(clearances[0], clearances[1], abs_tol=1e-6):
        return ()
    if not math.isclose(clearances[2], clearances[3], abs_tol=1e-6):
        return ()

    half_min_clearance = min(clearances) / 2.0
    radial_step = spec.radial_step
    if radial_step <= 0.0:
        return ()
    if not math.isclose(radial_step, 40.0, abs_tol=1e-6):
        return ()
    if radial_step > half_min_clearance + 1e-6:
        return ()
    count = int(math.floor((half_min_clearance + 1e-6) / radial_step))
    if count < 1:
        return ()
    return tuple(radial_step * multiplier for multiplier in range(1, count + 1))


def _rounded_kernel_loop_xy(
    kernel_bbox: tuple[float, float, float, float],
    radius: float,
) -> tuple[tuple[float, float], ...]:
    min_x, max_x, min_y, max_y = kernel_bbox
    diagonal = radius / math.sqrt(2.0)
    return (
        (min_x - radius, min_y),
        (min_x - radius, max_y),
        (min_x, max_y + radius),
        (max_x, max_y + radius),
        (max_x + diagonal, max_y + diagonal),
        (max_x + radius, max_y),
        (max_x + radius, min_y),
        (max_x, min_y - radius),
        (min_x, min_y - radius),
        (min_x - radius, min_y),
    )


def _xy_bbox_minmax(points: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    if not xs or not ys:
        raise ValueError("No se puede calcular bbox de una geometria vacia.")
    return (min(xs), max(xs), min(ys), max(ys))


def _same_xy_bbox(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return all(
        math.isclose(left, right, abs_tol=tolerance)
        for left, right in zip(_xy_bbox_minmax(first), _xy_bbox_minmax(second))
    )


@dataclass(frozen=True)
class _SingleSeedMultiloopRoute:
    seed: PocketBossRouteSeedSpec
    complete_radii: tuple[float, ...]
    partial_radii: tuple[float, ...]
    beta_angle: float
    bridge_radius: Optional[float] = None
    edge_boundary: bool = False


def _build_single_seed_multiloop_curve_and_sequence(
    spec: _HydratedPocketMillingSpec,
    cut_z: float,
) -> Optional[tuple[_CurveSpec, tuple[tuple[float, float, float], ...]]]:
    route = _supported_single_seed_multiloop_route(spec)
    if route is None:
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(route.seed.contour_points)
    max_complete = route.complete_radii[-1]
    min_partial = route.partial_radii[0] if route.partial_radii else None
    max_partial = route.partial_radii[-1] if route.partial_radii else None
    bridge_radius = route.bridge_radius
    if bridge_radius is not None and not route.partial_radii and not route.edge_boundary:
        return _build_single_seed_bridge_only_curve_and_sequence(route, cut_z, spec.contour_points)
    anchor_radius = bridge_radius if bridge_radius is not None else (max_partial or max_complete)
    anchor_x = contour_min_x + anchor_radius

    descriptions: list[str] = []
    points: list[tuple[float, float, float]] = [
        (anchor_x, contour_min_y + anchor_radius, cut_z)
    ]

    def point(x_value: float, y_value: float) -> tuple[float, float, float]:
        return (float(x_value), float(y_value), cut_z)

    def add_line(end_point: tuple[float, float, float]) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_toolpath_description(start_point, end_point))
        points.append(end_point)

    def add_arc(
        end_point: tuple[float, float, float],
        center_point: tuple[float, float],
    ) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_maestro_arc_serialization(start_point, end_point, center_point, -1.0, cut_z))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def beta_point(radius: float) -> tuple[float, float, float]:
        return point(
            seed_min_x + (radius * math.cos(route.beta_angle)),
            seed_min_y - (radius * math.sin(route.beta_angle)),
        )

    def add_complete_loop_from_right_bottom(radius: float) -> None:
        diagonal = radius / math.sqrt(2.0)

        add_line(point(seed_min_x, seed_min_y - radius))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y))
        add_line(point(seed_max_x, seed_max_y + radius))
        add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y))
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
        add_line(point(seed_max_x + radius, seed_min_y))
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y))

    if bridge_radius is not None:
        bridge_bottom_y = contour_min_y + bridge_radius
        bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - anchor_x) ** 2)))
        add_line(point(left_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y))
        add_arc(point(anchor_x, seed_min_y - bridge_y_delta), (seed_min_x, seed_min_y))
        add_line(point(anchor_x, bridge_bottom_y))
        add_line(point(anchor_x, contour_min_y + max_partial))

    for index, radius in enumerate(reversed(route.partial_radii)):
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        left_boundary_x = contour_min_x + radius
        next_radii = tuple(reversed(route.partial_radii))[index + 1 :]

        add_line(point(left_intersection_x(radius, seed_min_y, bottom_y), bottom_y))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(left_intersection_x(radius, seed_max_y, top_y), top_y), (seed_min_x, seed_max_y))
        add_line(point(left_boundary_x, top_y))
        if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
            add_line(point(left_boundary_x, contour_max_y - bridge_radius))
        add_line(point(left_boundary_x, bottom_y))
        add_line(point(anchor_x, bottom_y))
        if next_radii:
            add_line(point(anchor_x, contour_min_y + next_radii[0]))

    add_line(point(anchor_x, contour_min_y + max_complete))
    if route.edge_boundary:
        add_line(point(seed_max_x, contour_min_y + max_complete))
        add_complete_loop_from_right_bottom(max_complete)
    for index, radius in enumerate(reversed(route.complete_radii)):
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        right_x = contour_max_x - radius
        left_x = contour_min_x + radius
        remaining = tuple(reversed(route.complete_radii))[index + 1 :]

        add_line(point(right_x, bottom_y))
        add_line(point(right_x, top_y))
        if min_partial is not None and math.isclose(radius, max_complete, abs_tol=1e-6):
            add_line(point(contour_max_x - min_partial, top_y))
        add_line(point(left_x, top_y))
        add_line(point(left_x, bottom_y))
        add_line(point(anchor_x, bottom_y))
        if remaining:
            add_line(point(anchor_x, contour_min_y + remaining[0]))

    for radius in route.complete_radii[1:]:
        add_line(point(anchor_x, contour_min_y + radius))

    if route.edge_boundary:
        if min_partial is None or max_partial is None:
            return (_composite_curve_spec(descriptions), tuple(points))

        add_line(point(seed_max_x, contour_min_y + max_complete))
        add_complete_loop_from_right_bottom(max_complete)
        for radius in reversed(route.complete_radii[:-1]):
            add_line(point(seed_max_x, seed_min_y - radius))
            add_complete_loop_from_right_bottom(radius)
        for radius in route.complete_radii[1:]:
            add_line(point(seed_max_x, seed_min_y - radius))

        add_line(point(contour_max_x - max_complete, contour_min_y + max_complete))
        add_line(point(contour_max_x - max_complete, contour_max_y - max_complete))
        add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
        add_line(point(contour_max_x - min_partial, contour_max_y - min_partial))

        for index, radius in enumerate(route.partial_radii):
            top_y = contour_max_y - radius
            bottom_y = contour_min_y + radius
            right_boundary_x = contour_max_x - radius
            next_radii = route.partial_radii[index + 1 :]

            if next_radii:
                add_line(point(contour_max_x - next_radii[0], top_y))
            if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
                add_line(point(contour_max_x - bridge_radius, top_y))
            add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
            diagonal = radius / math.sqrt(2.0)
            diagonal_point = point(seed_max_x + diagonal, seed_max_y + diagonal)
            if top_y >= seed_max_y + diagonal - 1e-6:
                if math.hypot(diagonal_point[0] - points[-1][0], diagonal_point[1] - points[-1][1]) > 2.0:
                    add_arc(diagonal_point, (seed_max_x, seed_max_y))
                else:
                    add_line(diagonal_point)
            add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
            add_line(point(seed_max_x + radius, seed_min_y))
            add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
            add_line(point(right_boundary_x, bottom_y))
            if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
                bridge_anchor_x = contour_max_x - bridge_radius
                bridge_top_y = contour_max_y - bridge_radius
                bridge_bottom_y = contour_min_y + bridge_radius
                bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((bridge_anchor_x - seed_max_x) ** 2)))
                add_line(point(right_boundary_x, bridge_bottom_y))
                add_line(point(right_boundary_x, top_y))
                add_line(point(bridge_anchor_x, top_y))
                add_line(point(bridge_anchor_x, bridge_top_y))
                add_line(point(right_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y))
                add_arc(point(bridge_anchor_x, seed_max_y + bridge_y_delta), (seed_max_x, seed_max_y))
                add_line(point(bridge_anchor_x, bridge_top_y))
                add_line(point(bridge_anchor_x, top_y))
                add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
                add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
                add_line(point(seed_max_x + radius, seed_min_y))
                add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
                add_line(point(right_boundary_x, bottom_y))
                add_line(point(right_boundary_x, bridge_bottom_y))
                add_line(point(bridge_anchor_x, bridge_bottom_y))
                add_line(point(bridge_anchor_x, seed_min_y - bridge_y_delta))
                add_arc(
                    point(right_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y),
                    (seed_max_x, seed_min_y),
                )
                add_line(point(bridge_anchor_x, bridge_bottom_y))
                add_line(point(right_boundary_x, bridge_bottom_y))
            add_line(point(right_boundary_x, top_y))
            if next_radii:
                add_line(point(contour_max_x - next_radii[0], top_y))
                add_line(point(contour_max_x - next_radii[0], contour_max_y - next_radii[0]))

        for high_radius, low_radius in zip(reversed(route.partial_radii[1:]), reversed(route.partial_radii[:-1])):
            add_line(point(contour_max_x - high_radius, contour_max_y - low_radius))
            add_line(point(contour_max_x - low_radius, contour_max_y - low_radius))

        add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
        add_line(point(contour_min_x + max_complete, contour_max_y - max_complete))
        add_line(point(contour_min_x + max_complete, contour_min_y + max_complete))
        add_line(point(anchor_x, contour_min_y + max_complete))
        add_line(point(anchor_x, contour_min_y + min_partial))
        for radius in route.partial_radii[1:]:
            add_line(point(anchor_x, contour_min_y + radius))

        radius = max_partial
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        left_boundary_x = contour_min_x + radius
        add_line(point(left_intersection_x(radius, seed_min_y, bottom_y), bottom_y))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(left_intersection_x(radius, seed_max_y, top_y), top_y), (seed_min_x, seed_max_y))
        add_line(point(left_boundary_x, top_y))

        if bridge_radius is not None:
            bridge_top_y = contour_max_y - bridge_radius
            bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - anchor_x) ** 2)))
            add_line(point(left_boundary_x, bridge_top_y))
            add_line(point(anchor_x, bridge_top_y))
            add_line(point(anchor_x, seed_max_y + bridge_y_delta))
            add_arc(
                point(left_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y),
                (seed_min_x, seed_max_y),
            )
            add_line(point(anchor_x, bridge_top_y))

        return (_composite_curve_spec(descriptions), tuple(points))

    add_line(point(contour_max_x - max_complete, contour_min_y + max_complete))
    add_line(point(contour_max_x - max_complete, contour_max_y - max_complete))
    add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
    add_line(point(contour_max_x - min_partial, contour_max_y - min_partial))

    for index, radius in enumerate(route.partial_radii):
        top_y = contour_max_y - radius
        bottom_y = contour_min_y + radius
        right_boundary_x = contour_max_x - radius
        next_radii = route.partial_radii[index + 1 :]

        if next_radii:
            add_line(point(contour_max_x - next_radii[0], top_y))
        if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
            add_line(point(contour_max_x - bridge_radius, top_y))
        add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
        diagonal = radius / math.sqrt(2.0)
        diagonal_point = point(seed_max_x + diagonal, seed_max_y + diagonal)
        if top_y >= seed_max_y + diagonal - 1e-6:
            if math.hypot(diagonal_point[0] - points[-1][0], diagonal_point[1] - points[-1][1]) > 2.0:
                add_arc(diagonal_point, (seed_max_x, seed_max_y))
            else:
                add_line(diagonal_point)
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
        add_line(point(seed_max_x + radius, seed_min_y))
        add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
        add_line(point(right_boundary_x, bottom_y))
        if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
            bridge_anchor_x = contour_max_x - bridge_radius
            bridge_top_y = contour_max_y - bridge_radius
            bridge_bottom_y = contour_min_y + bridge_radius
            bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((bridge_anchor_x - seed_max_x) ** 2)))
            add_line(point(right_boundary_x, bridge_bottom_y))
            add_line(point(right_boundary_x, top_y))
            add_line(point(bridge_anchor_x, top_y))
            add_line(point(bridge_anchor_x, bridge_top_y))
            add_line(point(right_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y))
            add_arc(point(bridge_anchor_x, seed_max_y + bridge_y_delta), (seed_max_x, seed_max_y))
            add_line(point(bridge_anchor_x, bridge_top_y))
            add_line(point(bridge_anchor_x, top_y))
            add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
            add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
            add_line(point(seed_max_x + radius, seed_min_y))
            add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
            add_line(point(right_boundary_x, bottom_y))
            add_line(point(right_boundary_x, bridge_bottom_y))
            add_line(point(bridge_anchor_x, bridge_bottom_y))
            add_line(point(bridge_anchor_x, seed_min_y - bridge_y_delta))
            add_arc(point(right_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y), (seed_max_x, seed_min_y))
            add_line(point(bridge_anchor_x, bridge_bottom_y))
            add_line(point(right_boundary_x, bridge_bottom_y))
        add_line(point(right_boundary_x, top_y))
        if next_radii:
            add_line(point(contour_max_x - next_radii[0], top_y))
            add_line(point(contour_max_x - next_radii[0], contour_max_y - next_radii[0]))

    for high_radius, low_radius in zip(reversed(route.partial_radii[1:]), reversed(route.partial_radii[:-1])):
        add_line(point(contour_max_x - high_radius, contour_max_y - low_radius))
        add_line(point(contour_max_x - low_radius, contour_max_y - low_radius))

    add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
    add_line(point(contour_max_x - max_complete, contour_max_y - max_complete))
    add_line(point(contour_max_x - max_complete, contour_min_y + max_complete))
    add_line(point(anchor_x, contour_min_y + max_complete))
    add_line(point(anchor_x, contour_min_y + min_partial))
    add_line(point(left_intersection_x(min_partial, seed_min_y, contour_min_y + min_partial), contour_min_y + min_partial))
    add_line(beta_point(max_complete))

    for index, radius in enumerate(reversed(route.complete_radii)):
        next_radii = tuple(reversed(route.complete_radii))[index + 1 :]
        diagonal = radius / math.sqrt(2.0)

        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y))
        add_line(point(seed_max_x, seed_max_y + radius))
        add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y))
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
        add_line(point(seed_max_x + radius, seed_min_y))
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y))
        add_line(point(seed_min_x, seed_min_y - radius))
        add_arc(beta_point(radius), (seed_min_x, seed_min_y))
        if next_radii:
            add_line(beta_point(next_radii[0]))

    if bridge_radius is not None:
        for radius in route.complete_radii[1:]:
            add_line(beta_point(radius))

        add_line(point(left_intersection_x(min_partial, seed_min_y, contour_min_y + min_partial), contour_min_y + min_partial))
        add_line(point(anchor_x, contour_min_y + min_partial))
        for radius in route.partial_radii[1:]:
            add_line(point(anchor_x, contour_min_y + radius))

        radius = max_partial
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        left_boundary_x = contour_min_x + radius
        add_line(point(left_intersection_x(radius, seed_min_y, bottom_y), bottom_y))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(left_intersection_x(radius, seed_max_y, top_y), top_y), (seed_min_x, seed_max_y))
        add_line(point(left_boundary_x, top_y))

        bridge_top_y = contour_max_y - bridge_radius
        bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - anchor_x) ** 2)))
        add_line(point(left_boundary_x, bridge_top_y))
        add_line(point(anchor_x, bridge_top_y))
        add_line(point(anchor_x, seed_max_y + bridge_y_delta))
        add_arc(point(left_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y), (seed_min_x, seed_max_y))
        add_line(point(anchor_x, bridge_top_y))

    return (_composite_curve_spec(descriptions), tuple(points))


def _build_single_seed_bridge_only_curve_and_sequence(
    route: _SingleSeedMultiloopRoute,
    cut_z: float,
    contour_points: Sequence[tuple[float, float]],
) -> tuple[_CurveSpec, tuple[tuple[float, float, float], ...]]:
    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(route.seed.contour_points)
    radius = route.complete_radii[-1]
    bridge_radius = route.bridge_radius
    if bridge_radius is None:
        raise ValueError("La ruta bridge-only requiere bridge_radius.")

    left_anchor_x = contour_min_x + bridge_radius
    right_anchor_x = contour_max_x - bridge_radius
    left_boundary_x = contour_min_x + radius
    right_boundary_x = contour_max_x - radius
    bottom_y = contour_min_y + radius
    top_y = contour_max_y - radius
    bridge_bottom_y = contour_min_y + bridge_radius
    bridge_top_y = contour_max_y - bridge_radius
    bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - left_anchor_x) ** 2)))
    diagonal = radius / math.sqrt(2.0)
    radius_angle_x = seed_min_x + (radius * ((left_anchor_x - seed_min_x) / bridge_radius))
    radius_angle_top_y = seed_max_y + (radius * (bridge_y_delta / bridge_radius))

    descriptions: list[str] = []
    points: list[tuple[float, float, float]] = [
        (left_anchor_x, bridge_top_y, cut_z)
    ]

    def point(x_value: float, y_value: float) -> tuple[float, float, float]:
        return (float(x_value), float(y_value), cut_z)

    def add_line(end_point: tuple[float, float, float]) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_toolpath_description(start_point, end_point))
        points.append(end_point)

    def add_arc(
        end_point: tuple[float, float, float],
        center_point: tuple[float, float],
    ) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_maestro_arc_serialization(start_point, end_point, center_point, -1.0, cut_z))
        points.append(end_point)

    def left_intersection_x(radius_value: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius_value * radius_value) - (delta_y * delta_y)))

    def right_intersection_x(radius_value: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius_value * radius_value) - (delta_y * delta_y)))

    add_line(point(left_anchor_x, seed_max_y + bridge_y_delta))
    add_arc(
        point(left_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y),
        (seed_min_x, seed_max_y),
    )
    add_line(point(left_anchor_x, bridge_top_y))
    add_line(point(left_boundary_x, bridge_top_y))
    add_line(point(left_boundary_x, bottom_y))
    add_line(point(left_anchor_x, bottom_y))
    add_line(point(right_boundary_x, bottom_y))
    add_line(point(right_boundary_x, bridge_bottom_y))
    add_line(point(right_boundary_x, top_y))
    add_line(point(right_anchor_x, top_y))
    add_line(point(left_boundary_x, top_y))
    add_line(point(left_boundary_x, bridge_top_y))
    add_line(point(left_boundary_x, bottom_y))
    add_line(point(left_anchor_x, bottom_y))

    add_line(point(left_anchor_x, bridge_bottom_y))
    add_line(point(left_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y))
    add_arc(point(left_anchor_x, seed_min_y - bridge_y_delta), (seed_min_x, seed_min_y))
    add_line(point(left_anchor_x, bridge_bottom_y))
    add_line(point(left_anchor_x, bottom_y))

    add_line(point(right_boundary_x, bottom_y))
    add_line(point(right_boundary_x, bridge_bottom_y))
    add_line(point(right_anchor_x, bridge_bottom_y))
    add_line(point(right_anchor_x, seed_min_y - bridge_y_delta))
    add_arc(
        point(right_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y),
        (seed_max_x, seed_min_y),
    )
    add_line(point(right_anchor_x, bridge_bottom_y))
    add_line(point(right_boundary_x, bridge_bottom_y))

    add_line(point(right_boundary_x, top_y))
    add_line(point(right_anchor_x, top_y))
    add_line(point(right_anchor_x, bridge_top_y))
    add_line(point(right_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y))
    add_arc(point(right_anchor_x, seed_max_y + bridge_y_delta), (seed_max_x, seed_max_y))
    add_line(point(right_anchor_x, bridge_top_y))
    add_line(point(right_anchor_x, top_y))

    add_line(point(left_boundary_x, top_y))
    add_line(point(left_boundary_x, bridge_top_y))
    add_line(point(left_anchor_x, bridge_top_y))
    add_line(point(left_anchor_x, seed_max_y + bridge_y_delta))
    add_line(point(radius_angle_x, radius_angle_top_y))

    add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y))
    add_line(point(seed_max_x, seed_max_y + radius))
    add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y))
    add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
    add_line(point(seed_max_x + radius, seed_min_y))
    add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y))
    add_line(point(seed_min_x, seed_min_y - radius))
    add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
    add_line(point(seed_min_x - radius, seed_max_y))
    add_arc(point(radius_angle_x, radius_angle_top_y), (seed_min_x, seed_max_y))

    return (_composite_curve_spec(descriptions), tuple(points))


def _supported_single_seed_multiloop_route(
    spec: _HydratedPocketMillingSpec,
) -> Optional[_SingleSeedMultiloopRoute]:
    seed = _supported_single_seed_route_seed(spec)
    if seed is None:
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    left_clearance = seed_min_x - contour_min_x
    right_clearance = contour_max_x - seed_max_x
    bottom_clearance = seed_min_y - contour_min_y
    top_clearance = contour_max_y - seed_max_y
    horizontal_half_clearance = min(left_clearance, right_clearance) / 2.0
    vertical_half_clearance = min(bottom_clearance, top_clearance) / 2.0
    radial_step = spec.radial_step
    if radial_step <= 0.0:
        return None

    radius_count = int(math.floor((horizontal_half_clearance + 1e-6) / radial_step))
    radii = tuple(radial_step * multiplier for multiplier in range(1, radius_count + 1))
    complete_radii = tuple(radius for radius in radii if radius <= vertical_half_clearance + 1e-6)
    partial_radii = tuple(radius for radius in radii if radius > vertical_half_clearance + 1e-6)
    if not complete_radii:
        return None
    edge_boundary = math.isclose(complete_radii[-1], vertical_half_clearance, abs_tol=1e-6)

    next_radius = radial_step * (radius_count + 1)
    bridge_radius = None
    if 0.0 < (next_radius - horizontal_half_clearance) <= 2.0:
        bridge_radius = next_radius
    if not partial_radii and not edge_boundary and bridge_radius is None:
        return None

    beta_angle = 0.0
    if partial_radii:
        min_partial = partial_radii[0]
        partial_bottom_y = contour_min_y + min_partial
        sin_beta = (seed_min_y - partial_bottom_y) / min_partial
        if sin_beta <= -1.0 or sin_beta >= 1.0:
            return None
        beta_angle = math.pi - math.asin(sin_beta)
    return _SingleSeedMultiloopRoute(
        seed=seed,
        complete_radii=complete_radii,
        partial_radii=partial_radii,
        beta_angle=beta_angle,
        bridge_radius=bridge_radius,
        edge_boundary=edge_boundary,
    )


def _supported_single_seed_route_seed(
    spec: _HydratedPocketMillingSpec,
) -> Optional[PocketBossRouteSeedSpec]:
    if len(spec.boss_contours) != 1 or len(spec.boss_route_seeds) != 1:
        return None
    seed = spec.boss_route_seeds[0]
    if not seed.is_resolved:
        return None
    if not _same_xy_bbox(spec.boss_contours[0], seed.contour_points):
        return None
    if spec.plane_name != "Top" or spec.milling_strategy.allow_multiple_passes:
        return None
    if not spec.milling_strategy.inside_to_outside:
        return None
    if spec.milling_strategy.stroke_connection_strategy != "LiftShiftPlunge":
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    clearances = (
        seed_min_x - contour_min_x,
        contour_max_x - seed_max_x,
        seed_min_y - contour_min_y,
        contour_max_y - seed_max_y,
    )
    if min(clearances) <= 0.0:
        return None
    if not math.isclose(clearances[0], clearances[1], abs_tol=1e-6):
        return None
    if not math.isclose(clearances[2], clearances[3], abs_tol=1e-6):
        return None
    return seed


def _points_are_close_3d(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    *,
    tolerance: float = 1e-9,
) -> bool:
    return (
        math.isclose(first[0], second[0], abs_tol=tolerance)
        and math.isclose(first[1], second[1], abs_tol=tolerance)
        and math.isclose(first[2], second[2], abs_tol=tolerance)
    )


def _build_pocket_trajectory_xyz_sequences(
    state,
    spec: _HydratedPocketMillingSpec,
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    if spec.trajectory_sequences:
        return spec.trajectory_sequences

    if not spec.boss_contours and not spec.boss_route_seeds:
        return (_build_contour_parallel_xyz_path(state, spec),)

    trace_engine_sequences = _build_trace_engine_pocket_xyz_sequences(state, spec)
    if trace_engine_sequences is not None:
        return trace_engine_sequences

    controlled_sequences = _build_single_seed_base_loop_xyz_sequences(state, spec)
    if controlled_sequences is not None:
        return controlled_sequences

    cut_z = state.depth - float(_feature_depth_value(state, spec))
    controlled_multiloop = _build_single_seed_multiloop_curve_and_sequence(spec, cut_z)
    if controlled_multiloop is not None:
        _curve_spec, sequence = controlled_multiloop
        return (sequence,)

    raise NotImplementedError(
        "PocketMillingSpec con islas/BossGeometryList o semillas BossList.GeometryID "
        "se adapta para lectura, pero la serializacion productiva de Vaciado con islas "
        "todavia no esta implementada para esta configuracion."
    )


def _build_pocket_trajectory_curve_specs(
    spec: _HydratedPocketMillingSpec,
    trajectory_sequences: Sequence[Sequence[tuple[float, float, float]]],
) -> tuple[_CurveSpec, ...]:
    if spec.trajectory_curves and len(spec.trajectory_curves) == len(trajectory_sequences):
        return spec.trajectory_curves

    if not spec.boss_contours and not spec.boss_route_seeds:
        return tuple(_curve_spec_from_xyz_path(sequence) for sequence in trajectory_sequences)

    trace_engine_curves = _build_trace_engine_pocket_curve_specs(spec, trajectory_sequences)
    if trace_engine_curves is not None:
        return trace_engine_curves

    seed = _supported_single_seed_base_loop_route_seed(spec)
    if seed is not None and len(trajectory_sequences) == 2:
        cut_z = trajectory_sequences[1][0][2]
        seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
        radii = _single_seed_base_loop_radii(spec, seed)
        return (
            _curve_spec_from_xyz_path(trajectory_sequences[0]),
            _rounded_kernel_multi_loop_curve_spec(
                (seed_min_x, seed_max_x, seed_min_y, seed_max_y),
                radii,
                cut_z,
            ),
        )

    if len(trajectory_sequences) == 1 and trajectory_sequences[0]:
        cut_z = trajectory_sequences[0][0][2]
        controlled_multiloop = _build_single_seed_multiloop_curve_and_sequence(spec, cut_z)
        if controlled_multiloop is not None:
            curve_spec, _sequence = controlled_multiloop
            return (curve_spec,)

    return tuple(_curve_spec_from_xyz_path(sequence) for sequence in trajectory_sequences)


def _curve_spec_from_xyz_path(points: Sequence[tuple[float, float, float]]) -> _CurveSpec:
    descriptions: list[str] = []
    for start_point, end_point in zip(points, points[1:]):
        if _points_are_close_3d(start_point, end_point):
            continue
        descriptions.append(_build_toolpath_description(start_point, end_point))
    if not descriptions:
        raise ValueError("La trayectoria de Vaciado no contiene segmentos serializables.")
    return _composite_curve_spec(descriptions)


def _normalize_closed_contour(
    points: Sequence[tuple[float, float]],
    *,
    label: str,
) -> tuple[tuple[float, float], ...]:
    normalized = tuple((float(x), float(y)) for x, y in points)
    if len(normalized) < 4:
        raise ValueError(f"{label} requiere un contorno cerrado con al menos 4 puntos.")
    if not (
        math.isclose(normalized[0][0], normalized[-1][0], abs_tol=1e-6)
        and math.isclose(normalized[0][1], normalized[-1][1], abs_tol=1e-6)
    ):
        raise ValueError(f"{label} requiere que el primer y ultimo punto coincidan.")
    return normalized


def build_pocket_boss_route_seed_spec(
    *,
    geometry_id: str,
    object_type: Optional[str] = None,
    name: Optional[str] = None,
    contour_points: Optional[Sequence[tuple[float, float]]] = None,
) -> PocketBossRouteSeedSpec:
    """Construye una referencia de `BossList.GeometryID` para un `Vaciado`."""

    normalized_geometry_id = str(geometry_id).strip()
    if not normalized_geometry_id:
        raise ValueError("PocketBossRouteSeedSpec requiere geometry_id.")

    normalized_points = (
        _normalize_closed_contour(
            contour_points,
            label="La semilla de ruta de Vaciado",
        )
        if contour_points
        else ()
    )

    return PocketBossRouteSeedSpec(
        geometry_id=normalized_geometry_id,
        object_type=(object_type or "").strip(),
        name=(name or "").strip(),
        contour_points=normalized_points,
    )


def build_pocket_milling_spec(
    *,
    contour_points: Sequence[tuple[float, float]],
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    approach_enabled: Optional[bool] = None,
    approach_type: Optional[str] = None,
    approach_mode: Optional[str] = None,
    approach_radius_multiplier: Optional[float] = None,
    approach_speed: Optional[float] = None,
    approach_arc_side: Optional[str] = None,
    retract_enabled: Optional[bool] = None,
    retract_type: Optional[str] = None,
    retract_mode: Optional[str] = None,
    retract_radius_multiplier: Optional[float] = None,
    retract_speed: Optional[float] = None,
    retract_arc_side: Optional[str] = None,
    retract_overlap: Optional[float] = None,
    milling_strategy: Optional[ContourParallelMillingStrategySpec] = None,
    allowance_bottom: Optional[float] = None,
    allowance_side: Optional[float] = None,
    boss_contours: Optional[Sequence[Sequence[tuple[float, float]]]] = None,
    boss_route_seeds: Optional[Sequence[PocketBossRouteSeedSpec]] = None,
    is_enabled_expr: Optional[str] = None,
) -> PocketMillingSpec:
    """Construye la spec publica de `Vaciado` para lectura/adaptacion."""

    normalized_points = _normalize_closed_contour(
        contour_points,
        label="PocketMillingSpec",
    )
    normalized_boss_contours = [
        _normalize_closed_contour(
            boss_contour,
            label="Cada isla de PocketMillingSpec",
        )
        for boss_contour in boss_contours or ()
    ]
    normalized_boss_route_seeds = tuple(
        build_pocket_boss_route_seed_spec(
            geometry_id=seed.geometry_id,
            object_type=seed.object_type,
            name=seed.name,
            contour_points=seed.contour_points,
        )
        for seed in boss_route_seeds or ()
    )

    normalized_strategy = (
        build_contour_parallel_milling_strategy_spec()
        if milling_strategy is None
        else build_contour_parallel_milling_strategy_spec(
            rotation_direction=milling_strategy.rotation_direction,
            stroke_connection_strategy=milling_strategy.stroke_connection_strategy,
            inside_to_outside=milling_strategy.inside_to_outside,
            overlap=milling_strategy.overlap,
            is_helic_strategy=milling_strategy.is_helic_strategy,
            allow_multiple_passes=milling_strategy.allow_multiple_passes,
            axial_cutting_depth=milling_strategy.axial_cutting_depth,
            axial_finish_cutting_depth=milling_strategy.axial_finish_cutting_depth,
            cutmode=milling_strategy.cutmode,
            is_internal=milling_strategy.is_internal,
            radial_cutting_depth=milling_strategy.radial_cutting_depth,
            radial_finish_cutting_depth=milling_strategy.radial_finish_cutting_depth,
            allows_bidirectional=milling_strategy.allows_bidirectional,
            allows_finish_cutting=milling_strategy.allows_finish_cutting,
        )
    )
    has_explicit_depth = any(value is not None for value in (is_through, target_depth, extra_depth))
    depth_spec = (
        build_milling_depth_spec(is_through=False, target_depth=10.0)
        if not has_explicit_depth
        else build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        )
    )
    return PocketMillingSpec(
        contour_points=normalized_points,
        feature_name=(feature_name or "Vaciado").strip() or "Vaciado",
        plane_name=_normalize_plane_name(plane_name),
        tool_id=(tool_id or "1900").strip() or "1900",
        tool_name=(tool_name or "E001").strip() or "E001",
        tool_width=18.36 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        approach=build_approach_spec(
            enabled=approach_enabled,
            approach_type=approach_type,
            mode=approach_mode,
            radius_multiplier=approach_radius_multiplier,
            speed=approach_speed,
            arc_side=approach_arc_side,
        ),
        retract=build_retract_spec(
            enabled=retract_enabled,
            retract_type=retract_type,
            mode=retract_mode,
            radius_multiplier=retract_radius_multiplier,
            speed=retract_speed,
            arc_side=retract_arc_side,
            overlap=retract_overlap,
        ),
        milling_strategy=normalized_strategy,
        allowance_bottom=0.0 if allowance_bottom is None else float(allowance_bottom),
        allowance_side=0.0 if allowance_side is None else float(allowance_side),
        boss_contours=tuple(normalized_boss_contours),
        boss_route_seeds=normalized_boss_route_seeds,
        is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
    )


def _extract_pocket_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

    def extract_curve_xy_points(node) -> tuple[tuple[float, float], ...]:
        points = _curve_spec_points(_curve_spec_from_composite_curve_node(node)) or ()
        return tuple((point[0], point[1]) for point in points)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomCompositeCurve" in _xsi_type(node)
        ),
        None,
    )
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "ClosedPocket" in _xsi_type(node)
        ),
        None,
    )
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideRoughMilling" in _xsi_type(node)
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de Vaciado compatible.")

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    depth_variable_name = _workpiece_depth_name(workpiece)
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id
    geometries_by_id = {
        _text(node, "./{*}Key/{*}ID"): node
        for node in root.findall("./{*}Geometries/{*}GeomGeometry")
    }
    boss_contours = tuple(
        extract_curve_xy_points(node)
        for node in feature.findall("./{*}BossGeometryList/{*}GeomCompositeCurve")
    )
    boss_route_seed_contours: list[tuple[tuple[float, float], ...]] = []
    for boss_node in feature.findall("./{*}BossList/{*}Boss"):
        route_geometry_id = _text(boss_node, "./{*}GeometryID/{*}ID")
        route_geometry = geometries_by_id.get(route_geometry_id)
        if route_geometry is not None:
            boss_route_seed_contours.append(extract_curve_xy_points(route_geometry))
    trajectory_curves = tuple(
        _curve_spec_from_toolpath_node(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
        if _text(toolpath, "./{*}Type") == "TrajectoryPath"
    )
    trajectory_sequences = tuple(
        points
        for points in (_curve_spec_points(curve) for curve in trajectory_curves)
        if points is not None
    )
    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(
            feature,
            operation,
            matching_expressions,
            depth_variable_name,
        ),
        "geometry_curve": _curve_spec_from_composite_curve_node(geometry),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "security_plane": _safe_float(_text(operation, "./{*}ApproachSecurityPlane"), 0.0),
        "milling_strategy": _extract_milling_strategy_spec_from_operation(operation),
        "allowance_bottom": _safe_float(_text(operation, "./{*}AllowanceBottom"), 0.0),
        "allowance_side": _safe_float(_text(operation, "./{*}AllowanceSide"), 0.0),
        "boss_contours": boss_contours,
        "boss_route_seed_contours": tuple(boss_route_seed_contours),
        "trajectory_curves": trajectory_curves,
        "trajectory_sequences": trajectory_sequences,
    }


def _same_xy_points(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return len(first) == len(second) and all(
        math.isclose(left[0], right[0], abs_tol=tolerance)
        and math.isclose(left[1], right[1], abs_tol=tolerance)
        for left, right in zip(first, second)
    )


def _same_xy_contours(
    first: Sequence[Sequence[tuple[float, float]]],
    second: Sequence[Sequence[tuple[float, float]]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return len(first) == len(second) and all(
        _same_xy_points(left, right, tolerance=tolerance)
        for left, right in zip(first, second)
    )


def _can_hydrate_pocket_template_trace(
    template: dict[str, object],
    spec: PocketMillingSpec,
    *,
    tolerance: float = 1e-6,
) -> bool:
    geometry_curve = template.get("geometry_curve")
    if not isinstance(geometry_curve, _CurveSpec):
        return False
    template_points = _curve_spec_points(geometry_curve)
    if template_points is None:
        return False
    expected_points = tuple((x, y, 0.0) for x, y in spec.contour_points)
    if len(template_points) != len(expected_points):
        return False
    if not all(
        math.isclose(actual[0], expected[0], abs_tol=tolerance)
        and math.isclose(actual[1], expected[1], abs_tol=tolerance)
        for actual, expected in zip(template_points, expected_points)
    ):
        return False
    template_tool_width = float(template.get("tool_width") or 0.0)
    if template_tool_width > 0.0 and not math.isclose(template_tool_width, spec.tool_width, abs_tol=tolerance):
        return False
    if str(template.get("tool_id") or "") != spec.tool_id:
        return False
    if str(template.get("tool_name") or "") != spec.tool_name:
        return False
    strategy = template.get("milling_strategy")
    if not isinstance(strategy, ContourParallelMillingStrategySpec):
        return False
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != _normalize_milling_depth_spec(
        spec.depth_spec
    ):
        return False
    if not math.isclose(float(template.get("security_plane") or 0.0), spec.security_plane, abs_tol=tolerance):
        return False
    if not math.isclose(float(template.get("allowance_bottom") or 0.0), spec.allowance_bottom, abs_tol=tolerance):
        return False
    if not math.isclose(float(template.get("allowance_side") or 0.0), spec.allowance_side, abs_tol=tolerance):
        return False
    template_boss_contours = template.get("boss_contours") if isinstance(template.get("boss_contours"), tuple) else ()
    if not _same_xy_contours(template_boss_contours, spec.boss_contours, tolerance=tolerance):
        return False
    template_route_seed_contours = (
        template.get("boss_route_seed_contours")
        if isinstance(template.get("boss_route_seed_contours"), tuple)
        else ()
    )
    if len(spec.boss_route_seeds) != len(spec.resolved_boss_route_seed_contours):
        return False
    if not _same_xy_contours(
        template_route_seed_contours,
        spec.resolved_boss_route_seed_contours,
        tolerance=tolerance,
    ):
        return False
    return (
        _strategy_comparison_key(strategy, is_closed_profile=True)
        == _strategy_comparison_key(spec.milling_strategy, is_closed_profile=True)
        and bool(template.get("trajectory_curves"))
        and bool(template.get("trajectory_sequences"))
        and len(template.get("trajectory_curves") or ()) == len(template.get("trajectory_sequences") or ())
    )


def _hydrate_pocket_milling_spec(
    spec: PocketMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedPocketMillingSpec:
    if source_pgmx_path is None:
        return _HydratedPocketMillingSpec(spec)
    try:
        template = _extract_pocket_milling_template(source_pgmx_path)
    except ValueError:
        return _HydratedPocketMillingSpec(spec)
    can_hydrate_trace = _can_hydrate_pocket_template_trace(template, spec)
    return _HydratedPocketMillingSpec(
        spec,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_curve=template.get("geometry_curve") if isinstance(template.get("geometry_curve"), _CurveSpec) else None,
        trajectory_curves=(
            template.get("trajectory_curves")
            if can_hydrate_trace and isinstance(template.get("trajectory_curves"), tuple)
            else ()
        ),
        trajectory_sequences=(
            template.get("trajectory_sequences")
            if can_hydrate_trace and isinstance(template.get("trajectory_sequences"), tuple)
            else ()
        ),
    )
