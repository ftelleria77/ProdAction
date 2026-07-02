"""Line milling contracts for PGMX synthesis."""

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
    GeometryProfileSpec,
    _CurveSpec,
    _build_geometry_from_curve_spec,
    _build_line_description,
    _build_start_point,
    _build_toolpath,
    _build_toolpath_description,
    _curve_spec_from_profile_geometry,
    _curve_spec_from_toolpath_node,
    _parse_line_serialization,
    _profile_entry_exit_context,
    _profile_endpoint_points,
    _trimmed_curve_spec,
    build_compensated_toolpath_profile,
    build_line_geometry_profile,
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
    _build_bidirectional_line_strategy_profile,
    _build_milling_strategy_node,
    _build_unidirectional_line_strategy_profile,
    _normalize_milling_strategy_spec,
    _should_activate_cnc_correction,
    _strategy_comparison_key,
)
from ..common.piece import _workpiece_depth_name
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
    _build_depth_expression,
    _build_property_expression,
    _build_working_step,
    _compact_number,
    _find_plane_ref,
    _qname,
    _raw_text,
    _reserve_ids,
    _set_xmlns,
    _text,
    _xsi_type,
)
from ._common import (
    _build_profile_feature,
    _normalize_side_of_feature,
    _operation_overcut_length,
    _toolpath_cut_z,
    _uses_feature_depth_expressions,
)

__all__ = [
    "LineMillingSpec",
    "build_line_milling_spec",
    "_HydratedLineMillingSpec",
    "_append_line_milling",
    "_build_line_geometry",
    "_build_line_operation",
    "_build_line_toolpath_profile",
    "_can_hydrate_exact_serialization",
    "_extract_line_milling_template",
    "_hydrate_line_milling_spec",
    "_matches_line_geometry",
    "_normalize_line_milling_spec",
    "_offset_line_for_toolpath",
]


@dataclass(frozen=True)
class LineMillingSpec:
    """Descripcion reutilizable de un fresado lineal sobre un plano."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
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
    is_enabled_expr: Optional[str] = None
    # Cambios DURANTE el recorrido (Maestro: OperationAttribute anclado a UPar 0..1 normalizado):
    # - speed_changes: (UPar, Speed m/min) — desde ese punto el avance pasa a Speed.
    # - depth_changes: (UPar, Depth mm) — rampa lineal desde la prof. de la operación en el inicio
    #   hasta Depth, alcanzándola en UPar; sigue a Depth. (N_RT_E001_Vel/_Prof, hechos por Fermín.)
    # Solo LECTURA por ahora: la autoría del sintetizador no los serializa (los .pgmx los genera
    # Maestro). Ver iso/synthesis/_router.py para el render ISO.
    speed_changes: tuple[tuple[float, float], ...] = ()
    depth_changes: tuple[tuple[float, float], ...] = ()
    # Rebaba (N024): en el fresado LINEAL Maestro la guarda como <SideOffset> del
    # ManufacturingFeature (igual que el slot; NO usa AllowanceSide, que queda 0). En el ISO suma
    # al corrector de radio: SVR = width/2 + rebaba (si da 0, las líneas SVR se omiten). Admite
    # negativo. Solo LECTURA (la autoría hornea 0; los .pgmx con rebaba los genera Maestro).
    side_offset: float = 0.0
    # Allowance* de la operación: sin uso conocido en línea (siempre 0); si llegan ≠0 → fail-loud.
    allowance_side: float = 0.0
    allowance_bottom: float = 0.0
    # Corrección de longitud (<IsPrecise> del feature, N023 _long): el recorrido se ACORTA el radio
    # de la fresa en ambos extremos (centro viaja [start+r·dir, end−r·dir]) para que el FILO cubra
    # exactamente el segmento programado. Solo LECTURA (la autoría hornea false).
    is_precise: bool = False


@dataclass(frozen=True)
class _HydratedLineMillingSpec:
    """Datos internos de serializacion que complementan un `LineMillingSpec`."""

    spec: LineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_serialization: Optional[str] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def start_x(self) -> float:
        return self.spec.start_x

    @property
    def start_y(self) -> float:
        return self.spec.start_y

    @property
    def end_x(self) -> float:
        return self.spec.end_x

    @property
    def end_y(self) -> float:
        return self.spec.end_y

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

    @property
    def is_enabled_expr(self) -> Optional[str]:
        return self.spec.is_enabled_expr


def _normalize_line_milling_spec(line_milling: LineMillingSpec) -> LineMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(line_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="LineMillingSpec",
    )
    return replace(
        line_milling,
        side_of_feature=_normalize_side_of_feature(line_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(line_milling.depth_spec),
        approach=_normalize_approach_spec(line_milling.approach),
        retract=_normalize_retract_spec(line_milling.retract),
        milling_strategy=normalized_strategy,
    )


def _build_line_toolpath_profile(
    top_level: float,
    final_level: float,
    spec: LineMillingSpec,
) -> GeometryProfileSpec:
    """Construye el perfil de trayectoria efectivo para un fresado lineal."""

    cut_z = float(final_level)
    nominal_profile = build_line_geometry_profile(
        spec.start_x,
        spec.start_y,
        spec.end_x,
        spec.end_y,
        start_z=cut_z,
        end_z=cut_z,
    )
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_line_strategy_profile(
            float(top_level),
            cut_z,
            spec.security_plane,
            base_profile,
            strategy,
        )
    if isinstance(strategy, BidirectionalMillingStrategySpec):
        return _build_bidirectional_line_strategy_profile(float(top_level), cut_z, base_profile, strategy)
    return base_profile


def _offset_line_for_toolpath(spec: LineMillingSpec) -> tuple[tuple[float, float], tuple[float, float]]:
    toolpath_profile = build_compensated_toolpath_profile(
        build_line_geometry_profile(spec.start_x, spec.start_y, spec.end_x, spec.end_y),
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
    )
    return _profile_endpoint_points(toolpath_profile)


def _build_line_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    spec: _HydratedLineMillingSpec,
):
    return _build_geometry_from_curve_spec(
        geometry_id,
        plane_id,
        plane_object_type,
        _trimmed_curve_spec(
            spec.geometry_serialization or _build_line_description(spec.start_x, spec.start_y, spec.end_x, spec.end_y),
        ),
    )


def _build_line_operation(
    state,
    spec,
    operation_id: str,
    approach_curve: _CurveSpec,
    approach_curve_member_keys: Sequence[str] = (),
    lift_curve: Optional[_CurveSpec] = None,
    lift_curve_member_keys: Sequence[str] = (),
    trajectory_curve: Optional[_CurveSpec] = None,
    trajectory_curve_member_keys: Sequence[str] = (),
    toolpath_start: Optional[tuple[float, float]] = None,
    toolpath_end: Optional[tuple[float, float]] = None,
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:BottomAndSideFinishMilling"},
    )
    _set_xmlns(operation, "a", MILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling")
    _append_blank_name(operation)
    _append_node(
        operation,
        PGMX_NS,
        "ActivateCNCCorrection",
        "true" if _should_activate_cnc_correction(spec) else "false",
    )
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)
    clearance_z = state.depth + spec.security_plane
    cut_z = _toolpath_cut_z(state, spec)
    if toolpath_start is None or toolpath_end is None:
        (toolpath_start_x, toolpath_start_y), (toolpath_end_x, toolpath_end_y) = _offset_line_for_toolpath(spec)
    else:
        toolpath_start_x, toolpath_start_y = toolpath_start
        toolpath_end_x, toolpath_end_y = toolpath_end
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            approach_curve,
            generated_member_keys=approach_curve_member_keys,
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "TrajectoryPath",
            trajectory_curve
            or spec.trajectory_curve
            or _trimmed_curve_spec(
                _build_toolpath_description(
                    (toolpath_start_x, toolpath_start_y, cut_z),
                    (toolpath_end_x, toolpath_end_y, cut_z),
                )
            ),
            generated_member_keys=trajectory_curve_member_keys,
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            lift_curve
            or spec.lift_curve
            or _trimmed_curve_spec(
                _build_toolpath_description(
                    (toolpath_end_x, toolpath_end_y, cut_z),
                    (toolpath_end_x, toolpath_end_y, clearance_z),
                )
            ),
            generated_member_keys=lift_curve_member_keys,
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
    _append_node(operation, PGMX_NS, "AllowanceBottom", "0")
    _append_node(operation, PGMX_NS, "AllowanceSide", "0")
    return operation


def _append_line_milling(root: ET.Element, state, spec: _HydratedLineMillingSpec) -> None:
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
    has_enabled_expr = spec.is_enabled_expr is not None
    n_total = 4 + (2 if uses_depth_expressions else 0) + has_enabled_expr
    reserved_ids = _reserve_ids(root, n_total, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    i = 4
    start_expression_id = end_expression_id = None
    if uses_depth_expressions:
        start_expression_id = reserved_ids[i]; i += 1
        end_expression_id = reserved_ids[i]; i += 1
    enabled_expr_id = reserved_ids[i] if has_enabled_expr else None
    last_reserved_id = enabled_expr_id or end_expression_id or step_id
    generated_toolpath_profile = _build_line_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    trajectory_curve_member_keys: tuple[str, ...] = ()
    next_generated_aux_id = int(last_reserved_id) + 1
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
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

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
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
            toolpath_start=toolpath_start,
            toolpath_end=toolpath_end,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
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


def _matches_line_geometry(template: dict[str, object], spec: LineMillingSpec, tolerance: float = 1e-6) -> bool:
    parsed = _parse_line_serialization(str(template.get("geometry_serialization") or ""))
    if parsed is None:
        return False
    start, end = parsed
    expected = (spec.start_x, spec.start_y, 0.0, spec.end_x, spec.end_y, 0.0)
    direct = (start[0], start[1], start[2], end[0], end[1], end[2])
    reverse = (end[0], end[1], end[2], start[0], start[1], start[2])

    def close(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
        return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(a, b))

    return close(direct, expected) or close(reverse, expected)


def _can_hydrate_exact_serialization(template: dict[str, object], spec: LineMillingSpec) -> bool:
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
    if _strategy_comparison_key(source_strategy, is_closed_profile=False) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=False,
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
    if not _matches_line_geometry(template, spec):
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


def _extract_line_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomTrimmedCurve" in _xsi_type(node)
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
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado lineal compatible.")

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
        "geometry_serialization": _raw_text(geometry, "./{*}_serializationGeometryDescription"),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_line_milling_spec(
    line_milling: LineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedLineMillingSpec:
    normalized_line_milling = _normalize_line_milling_spec(line_milling)
    if source_pgmx_path is None:
        return _HydratedLineMillingSpec(spec=normalized_line_milling)
    template = _extract_line_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_serialization(template, normalized_line_milling):
        return _HydratedLineMillingSpec(spec=normalized_line_milling)
    return _HydratedLineMillingSpec(
        spec=normalized_line_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_serialization=str(template["geometry_serialization"]),
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def build_line_milling_spec(
    line_x1: Optional[float],
    line_y1: Optional[float],
    line_x2: Optional[float],
    line_y2: Optional[float],
    line_feature_name: Optional[str],
    line_tool_id: Optional[str],
    line_tool_name: Optional[str],
    line_tool_width: Optional[float],
    line_security_plane: Optional[float],
    line_side_of_feature: Optional[str] = None,
    line_is_through: Optional[bool] = None,
    line_target_depth: Optional[float] = None,
    line_extra_depth: Optional[float] = None,
    line_approach_enabled: Optional[bool] = None,
    line_approach_type: Optional[str] = None,
    line_approach_mode: Optional[str] = None,
    line_approach_radius_multiplier: Optional[float] = None,
    line_approach_speed: Optional[float] = None,
    line_approach_arc_side: Optional[str] = None,
    line_retract_enabled: Optional[bool] = None,
    line_retract_type: Optional[str] = None,
    line_retract_mode: Optional[str] = None,
    line_retract_radius_multiplier: Optional[float] = None,
    line_retract_speed: Optional[float] = None,
    line_retract_arc_side: Optional[str] = None,
    line_retract_overlap: Optional[float] = None,
    line_milling_strategy: Optional[MillingStrategySpec] = None,
    is_enabled_expr: Optional[str] = None,
) -> Optional[LineMillingSpec]:
    """Construye un `LineMillingSpec` reusable para un fresado lineal.

    Devuelve `None` si la linea no viene informada, lo que simplifica el uso
    desde CLI y desde capas superiores que quieren tratar este mecanizado como
    opcional.
    """

    values = [line_x1, line_y1, line_x2, line_y2]
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("Para sintetizar el fresado lineal hay que indicar x1, y1, x2 e y2.")
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(line_milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="LineMillingSpec",
    )
    return LineMillingSpec(
        start_x=float(line_x1),
        start_y=float(line_y1),
        end_x=float(line_x2),
        end_y=float(line_y2),
        feature_name=(line_feature_name or "Fresado").strip() or "Fresado",
        side_of_feature=_normalize_side_of_feature(line_side_of_feature),
        tool_id=(line_tool_id or "1902").strip() or "1902",
        tool_name=(line_tool_name or "E003").strip() or "E003",
        tool_width=9.52 if line_tool_width is None else float(line_tool_width),
        security_plane=20.0 if line_security_plane is None else float(line_security_plane),
        depth_spec=build_milling_depth_spec(
            is_through=line_is_through,
            target_depth=line_target_depth,
            extra_depth=line_extra_depth,
        ),
        approach=build_approach_spec(
            enabled=line_approach_enabled,
            approach_type=line_approach_type,
            mode=line_approach_mode,
            radius_multiplier=line_approach_radius_multiplier,
            speed=line_approach_speed,
            arc_side=line_approach_arc_side,
        ),
        retract=build_retract_spec(
            enabled=line_retract_enabled,
            retract_type=line_retract_type,
            mode=line_retract_mode,
            radius_multiplier=line_retract_radius_multiplier,
            speed=line_retract_speed,
            arc_side=line_retract_arc_side,
            overlap=line_retract_overlap,
        ),
        milling_strategy=normalized_strategy,
        is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
    )
