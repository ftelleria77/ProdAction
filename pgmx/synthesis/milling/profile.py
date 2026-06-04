"""Polyline/profile milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
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
    GeometryProfileSpec,
    _build_closed_polyline_geometry_profile,
    _build_geometry_from_curve_spec,
    _build_open_polyline_descriptions,
    _build_open_polyline_geometry_profile,
    _composite_curve_spec,
    _curve_spec_from_profile_geometry,
    _curve_spec_from_composite_curve_node,
    _curve_spec_from_toolpath_node,
    _curve_spec_points,
    _geometry_object_type,
    _is_closed_polyline_points,
    _normalize_polyline_points,
    _profile_entry_exit_context,
    build_compensated_toolpath_profile,
)
from ..common.hydration import _load_pgmx_container
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    _build_generated_approach_curve_for_profile,
    _build_generated_lift_curve_for_profile,
    _extract_approach_spec_from_operation,
    _extract_retract_spec_from_operation,
    _normalize_approach_spec,
    _normalize_retract_spec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.strategy import (
    BidirectionalMillingStrategySpec,
    ContourParallelMillingStrategySpec,
    HelicalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _extract_milling_strategy_spec_from_operation,
    _build_bidirectional_open_profile_strategy_toolpath,
    _build_closed_profile_strategy_toolpath,
    _build_unidirectional_open_profile_strategy_toolpath,
    _normalize_milling_strategy_spec,
    _strategy_comparison_key,
)
from ..common.piece import _workpiece_depth_name
from ..common.xml import (
    _build_depth_expression,
    _build_working_step,
    _find_plane_ref,
    _reserve_ids,
    _text,
    _xsi_type,
)
from ._common import _build_profile_feature, _normalize_side_of_feature, _toolpath_cut_z, _uses_feature_depth_expressions
from .line import _build_line_operation

__all__ = [
    "PolylineMillingSpec",
    "build_polyline_milling_spec",
    "_HydratedPolylineMillingSpec",
    "_append_curve_profile_milling",
    "_append_polyline_milling",
    "_build_polyline_toolpath_profile",
    "_can_hydrate_exact_polyline_serialization",
    "_extract_polyline_milling_template",
    "_hydrate_polyline_milling_spec",
    "_is_closed_polyline_points",
    "_matches_polyline_geometry",
    "_normalize_polyline_milling_spec",
    "_normalize_polyline_points",
    "_validate_polyline_postprocessable_by_maestro",
]


@dataclass(frozen=True)
class PolylineMillingSpec:
    """Descripcion reutilizable de un fresado asociado a una polilinea lineal.

    Si `points` termina en el mismo punto en el que empieza, se interpreta como
    contorno cerrado.
    """

    points: tuple[tuple[float, float], ...]
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1902"
    tool_name: str = "E003"
    tool_width: float = 9.52
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    milling_strategy: Optional[MillingStrategySpec] = None


@dataclass(frozen=True)
class _HydratedPolylineMillingSpec:
    """Datos internos de serializacion que complementan un `PolylineMillingSpec`."""

    spec: PolylineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def points(self) -> tuple[tuple[float, float], ...]:
        return self.spec.points

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

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
    def milling_strategy(self) -> Optional[MillingStrategySpec]:
        return self.spec.milling_strategy


def _validate_polyline_postprocessable_by_maestro(spec: PolylineMillingSpec) -> None:
    """Bloquea una combinacion que Maestro no logra postprocesar a ISO."""

    points = _normalize_polyline_points(spec.points)
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    retract = _normalize_retract_spec(spec.retract)
    is_open_multisegment = len(points) > 2 and not _is_closed_polyline_points(points)
    has_ph_multipass = bool(strategy and strategy.allow_multiple_passes)
    uses_arc_up_retract = (
        retract.is_enabled
        and retract.retract_type == "Arc"
        and retract.mode == "Up"
    )
    if is_open_multisegment and has_ph_multipass and uses_arc_up_retract:
        raise ValueError(
            "Maestro no postprocesa polilineas abiertas de varios segmentos con "
            "estrategia multipasada PH y Retract Arc + Up. Usar Retract Line + Up "
            "o Arc + Quote para obtener ISO postprocesable."
        )


def _normalize_polyline_milling_spec(polyline_milling: PolylineMillingSpec) -> PolylineMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(polyline_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="PolylineMillingSpec",
    )
    normalized_spec = replace(
        polyline_milling,
        points=_normalize_polyline_points(polyline_milling.points),
        side_of_feature=_normalize_side_of_feature(polyline_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(polyline_milling.depth_spec),
        approach=_normalize_approach_spec(polyline_milling.approach),
        retract=_normalize_retract_spec(polyline_milling.retract),
        milling_strategy=normalized_strategy,
    )
    _validate_polyline_postprocessable_by_maestro(normalized_spec)
    return normalized_spec


def _build_polyline_toolpath_profile(
    top_level: float,
    final_level: float,
    spec: PolylineMillingSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para una polilinea abierta o cerrada."""

    cut_z = float(final_level)
    if _is_closed_polyline_points(spec.points):
        nominal_profile = _build_closed_polyline_geometry_profile(spec.points, z_value=cut_z)
    else:
        nominal_profile = _build_open_polyline_geometry_profile(spec.points, z_value=cut_z)
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if nominal_profile.is_closed:
        return _build_closed_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_open_profile_strategy_toolpath(
            float(top_level),
            cut_z,
            spec.security_plane,
            base_profile,
            strategy,
        )
    return _build_bidirectional_open_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)


def _append_polyline_milling(root: ET.Element, state, spec: _HydratedPolylineMillingSpec) -> None:
    if spec.geometry_curve is not None:
        generated_geometry_curve = spec.geometry_curve
    elif _is_closed_polyline_points(spec.points):
        generated_geometry_curve = _curve_spec_from_profile_geometry(
            _build_closed_polyline_geometry_profile(spec.points, z_value=0.0)
        )
    else:
        generated_geometry_curve = _composite_curve_spec(_build_open_polyline_descriptions(spec.points))
    generated_toolpath_profile = _build_polyline_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        generated_geometry_curve,
        generated_toolpath_profile,
    )


def _append_curve_profile_milling(
    root: ET.Element,
    state,
    spec,
    generated_geometry_curve: _CurveSpec,
    generated_toolpath_profile: GeometryProfileSpec,
) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)

    geometry_member_count = len(generated_geometry_curve.member_serializations)
    reserved_ids = _reserve_ids(
        root,
        geometry_member_count + (6 if uses_depth_expressions else 4),
        spec.preferred_id_start,
    )
    geometry_id = reserved_ids[0]
    generated_geometry_member_keys: tuple[str, ...] = ()
    if generated_geometry_curve.geometry_type == "GeomCompositeCurve" and not generated_geometry_curve.member_keys:
        generated_geometry_member_keys = tuple(reserved_ids[1 : 1 + geometry_member_count])

    operation_index = 1 + geometry_member_count
    operation_id = reserved_ids[operation_index]
    feature_id = reserved_ids[operation_index + 1]
    step_id = reserved_ids[operation_index + 2]
    start_expression_id = reserved_ids[operation_index + 3] if uses_depth_expressions else None
    end_expression_id = reserved_ids[operation_index + 4] if uses_depth_expressions else None

    generated_trajectory_curve = _curve_spec_from_profile_geometry(generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or generated_trajectory_curve
    start_point, end_point, _, _ = _profile_entry_exit_context(generated_toolpath_profile)

    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)

    next_generated_aux_id = int(end_expression_id or step_id) + 1
    trajectory_curve_member_keys: tuple[str, ...] = ()
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
        if trajectory_curve.member_serializations == generated_geometry_curve.member_serializations:
            trajectory_curve_member_keys = generated_geometry_curve.member_keys or generated_geometry_member_keys
        else:
            member_count = len(trajectory_curve.member_serializations)
            trajectory_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
            next_generated_aux_id += member_count

    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(
        _build_geometry_from_curve_spec(
            geometry_id,
            plane_id,
            plane_object_type,
            generated_geometry_curve,
            generated_member_keys=generated_geometry_member_keys,
        )
    )
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            _geometry_object_type(generated_geometry_curve.geometry_type),
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys or trajectory_curve_member_keys,
            toolpath_start=start_point,
            toolpath_end=end_point,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _matches_polyline_geometry(template: dict[str, object], spec: PolylineMillingSpec, tolerance: float = 1e-6) -> bool:
    geometry_curve = template.get("geometry_curve")
    if not isinstance(geometry_curve, _CurveSpec):
        return False
    parsed_points = _curve_spec_points(geometry_curve)
    if parsed_points is None:
        return False
    expected_points = tuple((point[0], point[1], 0.0) for point in spec.points)
    if len(parsed_points) != len(expected_points):
        return False
    return all(
        math.isclose(parsed_point[0], expected_point[0], abs_tol=tolerance)
        and math.isclose(parsed_point[1], expected_point[1], abs_tol=tolerance)
        and math.isclose(parsed_point[2], expected_point[2], abs_tol=tolerance)
        for parsed_point, expected_point in zip(parsed_points, expected_points)
    )


def _can_hydrate_exact_polyline_serialization(template: dict[str, object], spec: PolylineMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    source_strategy = template.get("milling_strategy") if isinstance(
        template.get("milling_strategy"),
        (
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
            ContourParallelMillingStrategySpec,
        ),
    ) else None
    is_closed_profile = _is_closed_polyline_points(spec.points)
    if _strategy_comparison_key(source_strategy, is_closed_profile=is_closed_profile) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=is_closed_profile,
    ):
        return False
    requested_side = _normalize_side_of_feature(spec.side_of_feature)
    source_side = str(template["side_of_feature"])
    if requested_side != source_side:
        return False
    source_approach = _normalize_approach_spec(template.get("approach") if isinstance(template.get("approach"), ApproachSpec) else None)
    requested_approach = _normalize_approach_spec(spec.approach)
    if source_approach != requested_approach:
        return False
    source_retract = _normalize_retract_spec(template.get("retract") if isinstance(template.get("retract"), RetractSpec) else None)
    requested_retract = _normalize_retract_spec(spec.retract)
    if source_retract != requested_retract:
        return False
    if not _matches_polyline_geometry(template, spec):
        return False
    if requested_side == "Center":
        return True

    source_tool_width = float(template["tool_width"])
    source_tool_id = str(template["tool_id"])
    source_tool_name = str(template["tool_name"])
    return (
        math.isclose(spec.tool_width, source_tool_width, abs_tol=1e-6)
        and spec.tool_id == source_tool_id
        and spec.tool_name == source_tool_name
    )


def _extract_polyline_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

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
            if "GeneralProfileFeature" in _xsi_type(node)
        ),
        None,
    )
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado por polilinea compatible.")

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    depth_variable_name = _workpiece_depth_name(workpiece)
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): _curve_spec_from_toolpath_node(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
    }
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id

    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(
            feature,
            operation,
            matching_expressions,
            depth_variable_name,
        ),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "milling_strategy": _extract_milling_strategy_spec_from_operation(operation),
        "approach": _extract_approach_spec_from_operation(operation),
        "retract": _extract_retract_spec_from_operation(operation),
        "geometry_curve": _curve_spec_from_composite_curve_node(geometry),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_polyline_milling_spec(
    polyline_milling: PolylineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedPolylineMillingSpec:
    normalized_polyline_milling = _normalize_polyline_milling_spec(polyline_milling)
    if source_pgmx_path is None:
        return _HydratedPolylineMillingSpec(spec=normalized_polyline_milling)
    template = _extract_polyline_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_polyline_serialization(template, normalized_polyline_milling):
        return _HydratedPolylineMillingSpec(spec=normalized_polyline_milling)
    return _HydratedPolylineMillingSpec(
        spec=normalized_polyline_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_curve=template.get("geometry_curve") if isinstance(template.get("geometry_curve"), _CurveSpec) else None,
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def build_polyline_milling_spec(
    points: Sequence[tuple[float, float]],
    feature_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    side_of_feature: Optional[str] = None,
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
    milling_strategy: Optional[MillingStrategySpec] = None,
) -> PolylineMillingSpec:
    """Construye un `PolylineMillingSpec` reusable para una polilinea lineal.

    Si `points` cierra sobre su primer punto, la polilinea se interpreta como
    contorno cerrado.
    """

    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="PolylineMillingSpec",
    )
    normalized_spec = PolylineMillingSpec(
        points=_normalize_polyline_points(points),
        feature_name=(feature_name or "Fresado").strip() or "Fresado",
        side_of_feature=_normalize_side_of_feature(side_of_feature),
        tool_id=(tool_id or "1902").strip() or "1902",
        tool_name=(tool_name or "E003").strip() or "E003",
        tool_width=9.52 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        ),
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
    )
    _validate_polyline_postprocessable_by_maestro(normalized_spec)
    return normalized_spec
