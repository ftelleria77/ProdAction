"""Pocket milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from ..common.depth import (
    MillingDepthSpec,
    _extract_depth_spec_from_template,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.geometry import (
    _CurveSpec,
    _build_boundary_curve_holder,
    _build_start_point,
    _build_toolpath,
    _build_toolpath_description,
    _curve_spec_from_composite_curve_node,
    _curve_spec_from_toolpath_node,
    _curve_spec_points,
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
    _compact_number,
    _qname,
    _safe_float,
    _set_xmlns,
    _text,
    _xsi_type,
)
from ._common import _feature_depth_value, _operation_overcut_length

__all__ = [
    "PocketBossRouteSeedSpec",
    "PocketMillingSpec",
    "build_pocket_boss_route_seed_spec",
    "build_pocket_milling_spec",
    "_HydratedPocketMillingSpec",
    "_build_closed_pocket_boss",
    "_build_closed_pocket_feature",
    "_build_contour_parallel_xyz_path",
    "_build_pocket_operation",
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
    from pgmx.vaciado_lab.contour_parallel import generate_rectangular_contour_parallel_xyz_path

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
