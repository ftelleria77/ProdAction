"""Slot milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.geometry import (
    _CurveSpec,
    _build_identity_profile_placement,
    _curve_spec_from_profile_geometry,
    _profile_entry_exit_context,
)
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    _build_generated_approach_curve_for_profile,
    _build_generated_lift_curve_for_profile,
    _normalize_approach_spec,
    _normalize_retract_spec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.piece import _normalize_plane_name, _workpiece_depth_name
from ..common.xml import (
    MILLING_NS,
    PGMX_NS,
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
    _set_xmlns,
    _text,
)
from ._common import (
    _feature_bottom_condition_type,
    _feature_depth_value,
    _normalize_side_of_feature,
    _toolpath_cut_z,
    _uses_feature_depth_expressions,
)
from .line import _build_line_geometry, _build_line_operation, _build_line_toolpath_profile

__all__ = [
    "ChannelSpec",
    "build_channel_spec",
    "_HydratedChannelSpec",
    "_append_channel",
    "_build_slot_side_feature",
    "_hydrate_channel_spec",
    "_normalize_channel_spec",
]


@dataclass(frozen=True)
class ChannelSpec:
    """Ranura lineal `SlotSide` validada para Sierra Vertical X sobre `Top`."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    feature_name: str = "Canal"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1899"
    tool_name: str = "082"
    tool_width: float = 3.8
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(
        default_factory=lambda: MillingDepthSpec(
            is_through=False,
            target_depth=10.0,
            extra_depth=0.0,
        )
    )
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    material_position: str = "Left"
    side_offset: float = 0.0
    end_radius: float = 60.0
    slot_angle: float = 1.5707963267948966
    is_enabled_expr: Optional[str] = None

    @property
    def milling_strategy(self) -> None:
        return None


@dataclass(frozen=True)
class _HydratedChannelSpec:
    """Datos internos de serializacion que complementan un `ChannelSpec`."""

    spec: ChannelSpec
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
    def milling_strategy(self) -> None:
        return None

    @property
    def material_position(self) -> str:
        return self.spec.material_position

    @property
    def side_offset(self) -> float:
        return self.spec.side_offset

    @property
    def end_radius(self) -> float:
        return self.spec.end_radius

    @property
    def slot_angle(self) -> float:
        return self.spec.slot_angle

    @property
    def is_enabled_expr(self) -> Optional[str]:
        return self.spec.is_enabled_expr


def _normalize_channel_spec(slot_milling: ChannelSpec) -> ChannelSpec:
    if math.isclose(float(slot_milling.start_x), float(slot_milling.end_x), abs_tol=1e-9) and math.isclose(
        float(slot_milling.start_y),
        float(slot_milling.end_y),
        abs_tol=1e-9,
    ):
        raise ValueError("La ranura no puede tener longitud cero.")
    end_radius = float(slot_milling.end_radius)
    if end_radius < 0.0:
        raise ValueError("El radio de extremo de la ranura no puede ser negativo.")
    return replace(
        slot_milling,
        start_x=float(slot_milling.start_x),
        start_y=float(slot_milling.start_y),
        end_x=float(slot_milling.end_x),
        end_y=float(slot_milling.end_y),
        plane_name=_normalize_plane_name(slot_milling.plane_name),
        side_of_feature=_normalize_side_of_feature(slot_milling.side_of_feature),
        tool_id=(slot_milling.tool_id or "1899").strip() or "1899",
        tool_name=(slot_milling.tool_name or "082").strip() or "082",
        tool_width=float(slot_milling.tool_width),
        security_plane=float(slot_milling.security_plane),
        depth_spec=_normalize_milling_depth_spec(slot_milling.depth_spec),
        approach=_normalize_approach_spec(slot_milling.approach),
        retract=_normalize_retract_spec(slot_milling.retract),
        material_position=(slot_milling.material_position or "Left").strip() or "Left",
        side_offset=float(slot_milling.side_offset),
        end_radius=end_radius,
        slot_angle=float(slot_milling.slot_angle),
    )


def _hydrate_channel_spec(
    slot_milling: ChannelSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedChannelSpec:
    del source_pgmx_path
    return _HydratedChannelSpec(spec=_normalize_channel_spec(slot_milling))


def _build_slot_side_feature(
    state,
    spec: _HydratedChannelSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:SlotSide"},
    )
    _set_xmlns(feature, "a", MILLING_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Milling.SlotSide")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _feature_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", MILLING_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    end_conditions = _append_node(feature, PGMX_NS, "EndConditions")
    for _ in range(2):
        slot_end = _append_node(
            end_conditions,
            MILLING_NS,
            "SlotEndType",
            attrib={f"{{{XSI_NS}}}type": "a:WoodruffSlotEndType"},
        )
        _set_xmlns(slot_end, "a", MILLING_NS)
        _append_node(slot_end, MILLING_NS, "Radius", _compact_number(spec.end_radius))
    _append_node(feature, PGMX_NS, "IsGeomSameDirection", "true")
    _append_node(feature, PGMX_NS, "IsPrecise", "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", spec.material_position)
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", "0")
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", "0")
    _append_node(feature, PGMX_NS, "SideOfFeature", spec.side_of_feature)
    _append_node(feature, PGMX_NS, "SideOffset", _compact_number(spec.side_offset))
    swept_shape = _append_node(
        feature,
        PGMX_NS,
        "SweptShape",
        attrib={f"{{{XSI_NS}}}type": "a:SquareUProfile"},
    )
    _set_xmlns(swept_shape, "a", MILLING_NS)
    swept_shape.append(_build_identity_profile_placement())
    _append_node(swept_shape, MILLING_NS, "FirstAngle", "0")
    _append_node(swept_shape, MILLING_NS, "FirstRadius", "0")
    _append_node(swept_shape, MILLING_NS, "SecondAngle", "0")
    _append_node(swept_shape, MILLING_NS, "SecondRadius", "0")
    _append_node(swept_shape, MILLING_NS, "Width", _compact_number(spec.tool_width))
    _append_node(feature, PGMX_NS, "Angle", str(float(spec.slot_angle)))
    return feature


def _append_channel(root: ET.Element, state, spec: _HydratedChannelSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar la ranura.")

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
    generated_toolpath_profile = _build_line_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    # Claves de miembro para curvas compuestas GENERADAS (leads con arco): mismo mecanismo
    # que line.py — sin esto, un canal con Acercamiento/Alejamiento crasheaba al serializar
    # («GeomCompositeCurve requiere una clave por cada miembro», detectado generando N055).
    next_generated_aux_id = int(reserved_ids[n_total - 1]) + 1
    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(
            str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count
    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(
            str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_slot_side_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
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
            trajectory_curve_member_keys=trajectory_curve.member_keys,
            toolpath_start=toolpath_start,
            toolpath_end=toolpath_end,
        )
    )
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.Milling.SlotSide",
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


def build_channel_spec(
    *,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    side_of_feature: Optional[str] = None,
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
    material_position: Optional[str] = None,
    side_offset: Optional[float] = None,
    end_radius: Optional[float] = None,
    slot_angle: Optional[float] = None,
    is_enabled_expr: Optional[str] = None,
) -> ChannelSpec:
    """Construye una ranura lineal `SlotSide` compatible con Sierra Vertical X."""

    depth_spec = build_milling_depth_spec(
        is_through=False if is_through is None and target_depth is None and extra_depth is None else is_through,
        target_depth=10.0 if is_through is None and target_depth is None and extra_depth is None else target_depth,
        extra_depth=extra_depth,
    )
    return _normalize_channel_spec(
        ChannelSpec(
            start_x=float(start_x),
            start_y=float(start_y),
            end_x=float(end_x),
            end_y=float(end_y),
            feature_name=(feature_name or "Canal").strip() or "Canal",
            plane_name=_normalize_plane_name(plane_name),
            side_of_feature=_normalize_side_of_feature(side_of_feature),
            tool_id=(tool_id or "1899").strip() or "1899",
            tool_name=(tool_name or "082").strip() or "082",
            tool_width=3.8 if tool_width is None else float(tool_width),
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
            material_position=(material_position or "Left").strip() or "Left",
            side_offset=0.0 if side_offset is None else float(side_offset),
            end_radius=60.0 if end_radius is None else float(end_radius),
            slot_angle=1.5707963267948966 if slot_angle is None else float(slot_angle),
            is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
        )
    )
