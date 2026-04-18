"""Lectura integral y normalizada de archivos `.pgmx` existentes.

La meta de este modulo es exponer una vista estable del archivo Maestro ya
existente para poder:

- inspeccionarlo sin volver a bajar al XML crudo cada vez
- relacionar geometrias, features, operaciones y workplan
- reutilizar esos datos al refactorizar hacia el sintetizador
- dejar base para futuras modificaciones puntuales sobre un `.pgmx`
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Optional
import xml.etree.ElementTree as ET

from tools import synthesize_pgmx as sp

__all__ = [
    "PgmxObjectRefSnapshot",
    "PgmxPlacementSnapshot",
    "PgmxVariableSnapshot",
    "PgmxExpressionSnapshot",
    "PgmxCurveSnapshot",
    "PgmxVectorSnapshot",
    "PgmxToolpathSnapshot",
    "PgmxTechnologySnapshot",
    "PgmxMachineFunctionSnapshot",
    "PgmxGeometrySnapshot",
    "PgmxWorkpieceSnapshot",
    "PgmxPlaneSnapshot",
    "PgmxFeatureSnapshot",
    "PgmxOperationSnapshot",
    "PgmxWorkingStepSnapshot",
    "PgmxSnapshot",
    "read_pgmx_snapshot",
    "snapshot_to_dict",
    "write_pgmx_snapshot_json",
]


@dataclass(frozen=True)
class PgmxObjectRefSnapshot:
    id: str
    object_type: str
    name: str = ""


@dataclass(frozen=True)
class PgmxPlacementSnapshot:
    is_absolute: bool
    plane_ref: PgmxObjectRefSnapshot
    x_n: float
    x_p: float
    x_vx: float
    y_n: float
    y_p: float
    y_vx: float
    z_n: float
    z_p: float
    z_vx: float


@dataclass(frozen=True)
class PgmxVariableSnapshot:
    id: str
    object_type: str
    name: str
    description: str
    physical_unit_type: str
    is_read_only: bool
    scope: str
    value_type: str
    value_runtime_type: str
    value_text: str
    value_number: Optional[float]


@dataclass(frozen=True)
class PgmxExpressionSnapshot:
    id: str
    object_type: str
    name: str
    property_type: str
    field_path: tuple[str, ...]
    referenced_object: Optional[PgmxObjectRefSnapshot]
    value: str


@dataclass(frozen=True)
class PgmxCurveSnapshot:
    geometry_type: str
    serialization: Optional[str] = None
    member_keys: tuple[str, ...] = ()
    member_serializations: tuple[str, ...] = ()
    sampled_points: tuple[tuple[float, float, float], ...] = ()


@dataclass(frozen=True)
class PgmxVectorSnapshot:
    is_absolute: bool
    plane_ref: PgmxObjectRefSnapshot
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class PgmxToolpathSnapshot:
    path_type: str
    priority: bool
    direction: bool
    curve: Optional[PgmxCurveSnapshot]
    tool_axis: Optional[PgmxVectorSnapshot]


@dataclass(frozen=True)
class PgmxTechnologySnapshot:
    runtime_type: str
    feedrate: float
    cut_speed: float
    spindle: float


@dataclass(frozen=True)
class PgmxMachineFunctionSnapshot:
    runtime_type: str
    values: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PgmxGeometrySnapshot:
    id: str
    object_type: str
    name: str
    geometry_type: str
    is_absolute: bool
    plane_ref: Optional[PgmxObjectRefSnapshot]
    profile: Optional[sp.GeometryProfileSpec]
    curve: Optional[PgmxCurveSnapshot]
    point: Optional[tuple[float, float, float]]


@dataclass(frozen=True)
class PgmxWorkpieceSnapshot:
    id: str
    object_type: str
    name: str
    length: float
    width: float
    depth: float
    length_name: str
    width_name: str
    depth_name: str
    geometry_type: str


@dataclass(frozen=True)
class PgmxPlaneSnapshot:
    id: str
    object_type: str
    name: str
    plane_type: str
    generator_ref: Optional[PgmxObjectRefSnapshot]
    is_right_handed: bool
    placement: Optional[PgmxPlacementSnapshot]
    workpiece_ref: Optional[PgmxObjectRefSnapshot]
    x_dimension: float
    y_dimension: float


@dataclass(frozen=True)
class PgmxFeatureSnapshot:
    id: str
    object_type: str
    name: str
    feature_type: str
    geometry_ref: Optional[PgmxObjectRefSnapshot]
    operation_refs: tuple[PgmxObjectRefSnapshot, ...]
    workpiece_ref: Optional[PgmxObjectRefSnapshot]
    bottom_condition_type: str
    depth_start: Optional[float]
    depth_end: Optional[float]
    depth_spec: Optional[sp.MillingDepthSpec]
    plane_name: Optional[str]
    side_of_feature: str
    material_position: str
    side_offset: Optional[float]
    tool_width: Optional[float]
    diameter: Optional[float]
    taper_height: Optional[float]
    is_geom_same_direction: Optional[bool]
    is_precise: Optional[bool]


@dataclass(frozen=True)
class PgmxOperationSnapshot:
    id: str
    object_type: str
    name: str
    operation_type: str
    activate_cnc_correction: bool
    toolpath_priority: bool
    approach_security_plane: float
    retract_security_plane: float
    head_rotation: float
    start_point: Optional[tuple[float, float, float]]
    technology: Optional[PgmxTechnologySnapshot]
    tool_key: Optional[PgmxObjectRefSnapshot]
    overcut_length: float
    cutting_depth: Optional[float]
    approach: Optional[sp.ApproachSpec]
    retract: Optional[sp.RetractSpec]
    milling_strategy: Optional[sp.MillingStrategySpec]
    allowance_bottom: Optional[float]
    allowance_side: Optional[float]
    toolpaths: tuple[PgmxToolpathSnapshot, ...]
    machine_functions: tuple[PgmxMachineFunctionSnapshot, ...]


@dataclass(frozen=True)
class PgmxWorkingStepSnapshot:
    id: str
    object_type: str
    name: str
    description: str
    is_enabled: bool
    priority: int
    manufacturing_feature_ref: Optional[PgmxObjectRefSnapshot]
    operation_ref: Optional[PgmxObjectRefSnapshot]


@dataclass(frozen=True)
class PgmxSnapshot:
    source_path: Path
    xml_entry_name: str
    container_entries: tuple[str, ...]
    project_name: str
    state: sp.PgmxState
    workpiece: Optional[PgmxWorkpieceSnapshot]
    variables: tuple[PgmxVariableSnapshot, ...]
    expressions: tuple[PgmxExpressionSnapshot, ...]
    planes: tuple[PgmxPlaneSnapshot, ...]
    geometries: tuple[PgmxGeometrySnapshot, ...]
    features: tuple[PgmxFeatureSnapshot, ...]
    operations: tuple[PgmxOperationSnapshot, ...]
    working_steps: tuple[PgmxWorkingStepSnapshot, ...]
    xml_text: Optional[str] = None

    @property
    def geometry_by_id(self) -> dict[str, PgmxGeometrySnapshot]:
        return {item.id: item for item in self.geometries}

    @property
    def feature_by_id(self) -> dict[str, PgmxFeatureSnapshot]:
        return {item.id: item for item in self.features}

    @property
    def operation_by_id(self) -> dict[str, PgmxOperationSnapshot]:
        return {item.id: item for item in self.operations}

    @property
    def working_step_by_id(self) -> dict[str, PgmxWorkingStepSnapshot]:
        return {item.id: item for item in self.working_steps}

    @property
    def plane_by_id(self) -> dict[str, PgmxPlaneSnapshot]:
        return {item.id: item for item in self.planes}


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _first_child(node: Optional[ET.Element], local_name: str) -> Optional[ET.Element]:
    if node is None:
        return None
    for child in list(node):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _child_text(node: Optional[ET.Element], local_name: str, default: str = "") -> str:
    child = _first_child(node, local_name)
    if child is None or child.text is None:
        return default
    return str(child.text).strip()


def _object_ref(node: Optional[ET.Element]) -> Optional[PgmxObjectRefSnapshot]:
    if node is None:
        return None
    return PgmxObjectRefSnapshot(
        id=_child_text(node, "ID"),
        object_type=_child_text(node, "ObjectType"),
        name=_child_text(node, "Name"),
    )


def _float_text(node: Optional[ET.Element], local_name: str, default: float = 0.0) -> float:
    return sp._safe_float(_child_text(node, local_name), default)


def _optional_float_text(node: Optional[ET.Element], local_name: str) -> Optional[float]:
    child = _first_child(node, local_name)
    if child is None or child.text is None:
        return None
    return sp._safe_float(child.text, 0.0)


def _bool_text(node: Optional[ET.Element], local_name: str, default: bool = False) -> bool:
    return sp._safe_bool(_child_text(node, local_name), default)


def _tuple_point(node: Optional[ET.Element]) -> Optional[tuple[float, float, float]]:
    if node is None:
        return None
    return (
        _float_text(node, "_x"),
        _float_text(node, "_y"),
        _float_text(node, "_z"),
    )


def _field_path(property_node: Optional[ET.Element]) -> tuple[str, ...]:
    names: list[str] = []
    current = property_node
    while current is not None:
        name = _child_text(current, "Name")
        if name:
            names.append(name)
        current = _first_child(current, "InnerField")
    return tuple(names)


def _curve_snapshot_from_node(node: Optional[ET.Element]) -> Optional[PgmxCurveSnapshot]:
    if node is None:
        return None
    curve_type = sp._xsi_type(node)
    if "GeomTrimmedCurve" in curve_type:
        serialization = sp._raw_text(node, "./{*}_serializationGeometryDescription")
        curve_spec = sp._trimmed_curve_spec(serialization)
    elif "GeomCircle" in curve_type:
        serialization = sp._raw_text(node, "./{*}_serializationGeometryDescription")
        curve_spec = sp._circle_curve_spec(serialization)
    elif "GeomCompositeCurve" in curve_type:
        member_keys = tuple(
            (_child.text or "").strip()
            for _child in node.findall("./{*}_serializingKeys/{*}unsignedInt")
        )
        member_serializations = tuple(
            (_child.text or "")
            for _child in node.findall("./{*}_serializingMembers/{*}string")
        )
        curve_spec = sp._composite_curve_spec(member_serializations, member_keys)
    else:
        return None

    sampled_points = tuple(sp._curve_spec_points(curve_spec) or ())
    return PgmxCurveSnapshot(
        geometry_type=curve_spec.geometry_type,
        serialization=curve_spec.serialization,
        member_keys=curve_spec.member_keys,
        member_serializations=curve_spec.member_serializations,
        sampled_points=sampled_points,
    )


def _placement_snapshot(node: Optional[ET.Element]) -> Optional[PgmxPlacementSnapshot]:
    if node is None:
        return None
    return PgmxPlacementSnapshot(
        is_absolute=_bool_text(node, "IsAbsolute"),
        plane_ref=_object_ref(_first_child(node, "PlaneID")) or PgmxObjectRefSnapshot("", ""),
        x_n=_float_text(node, "_xN"),
        x_p=_float_text(node, "_xP"),
        x_vx=_float_text(node, "_xVx"),
        y_n=_float_text(node, "_yN"),
        y_p=_float_text(node, "_yP"),
        y_vx=_float_text(node, "_yVx"),
        z_n=_float_text(node, "_zN"),
        z_p=_float_text(node, "_zP"),
        z_vx=_float_text(node, "_zVx"),
    )


def _vector_snapshot(node: Optional[ET.Element]) -> Optional[PgmxVectorSnapshot]:
    if node is None:
        return None
    return PgmxVectorSnapshot(
        is_absolute=_bool_text(node, "IsAbsolute"),
        plane_ref=_object_ref(_first_child(node, "PlaneID")) or PgmxObjectRefSnapshot("", ""),
        x=_float_text(node, "_x"),
        y=_float_text(node, "_y"),
        z=_float_text(node, "_z"),
    )


def _toolpath_snapshot(node: ET.Element) -> PgmxToolpathSnapshot:
    return PgmxToolpathSnapshot(
        path_type=_child_text(node, "Type"),
        priority=_bool_text(node, "Priority"),
        direction=_bool_text(node, "Direction"),
        curve=_curve_snapshot_from_node(_first_child(node, "BasicCurve")),
        tool_axis=_vector_snapshot(_first_child(node, "ToolAxis")),
    )


def _technology_snapshot(node: Optional[ET.Element]) -> Optional[PgmxTechnologySnapshot]:
    if node is None:
        return None
    return PgmxTechnologySnapshot(
        runtime_type=sp._xsi_type(node),
        feedrate=_float_text(node, "Feedrate"),
        cut_speed=_float_text(node, "CutSpeed"),
        spindle=_float_text(node, "Spindle"),
    )


def _machine_function_snapshot(node: ET.Element) -> PgmxMachineFunctionSnapshot:
    values: list[tuple[str, str]] = []
    for child in list(node):
        values.append((_local_name(child.tag), (child.text or "").strip()))
    return PgmxMachineFunctionSnapshot(
        runtime_type=sp._xsi_type(node),
        values=tuple(values),
    )


def _parse_feature_depth_spec(
    feature: ET.Element,
    operation: Optional[ET.Element],
    matching_expressions: list[ET.Element],
    depth_variable_name: str,
    plane_span: float,
) -> Optional[sp.MillingDepthSpec]:
    if operation is None:
        return None
    expression_values = {
        sp._text(node, "./{*}Property/{*}InnerField/{*}Name"): sp._text(node, "./{*}Value")
        for node in matching_expressions
        if sp._text(node, "./{*}Property/{*}Name") == "Depth"
    }
    bottom_condition_type = sp._xsi_type(_first_child(feature, "BottomCondition"))
    overcut_length = sp._safe_float(sp._text(operation, "./{*}OvercutLength"), 0.0)
    if "ThroughMillingBottom" in bottom_condition_type or (
        expression_values.get("StartDepth") == depth_variable_name
        and expression_values.get("EndDepth") == depth_variable_name
    ):
        return sp.build_milling_depth_spec(is_through=True, extra_depth=overcut_length)

    depth_node = _first_child(feature, "Depth")
    start_depth = _optional_float_text(depth_node, "StartDepth")
    end_depth = _optional_float_text(depth_node, "EndDepth")
    if start_depth is None or end_depth is None:
        return None
    if not abs(start_depth - end_depth) <= 1e-6:
        return None
    if start_depth > plane_span + 1e-6:
        inferred_extra = max(overcut_length, start_depth - plane_span)
        return sp.build_milling_depth_spec(is_through=True, extra_depth=inferred_extra)
    return sp.build_milling_depth_spec(is_through=False, target_depth=start_depth)


def _operation_specs(operation: ET.Element) -> tuple[Optional[sp.ApproachSpec], Optional[sp.RetractSpec]]:
    approach_node = _first_child(operation, "Approach")
    retract_node = _first_child(operation, "Retract")
    approach = None
    retract = None
    if approach_node is not None:
        approach = sp.build_approach_spec(
            enabled=_bool_text(approach_node, "IsEnabled"),
            approach_type=_child_text(approach_node, "ApproachType", "Line"),
            mode=_child_text(approach_node, "ApproachMode", "Down"),
            radius_multiplier=_float_text(approach_node, "RadiusMultiplier", 1.2),
            speed=_float_text(approach_node, "Speed"),
            arc_side=_child_text(approach_node, "ApproachArcSide", "Automatic"),
        )
    if retract_node is not None:
        retract = sp.build_retract_spec(
            enabled=_bool_text(retract_node, "IsEnabled"),
            retract_type=_child_text(retract_node, "RetractType", "Line"),
            mode=_child_text(retract_node, "RetractMode", "Up"),
            radius_multiplier=_float_text(retract_node, "RadiusMultiplier", 1.2),
            speed=_float_text(retract_node, "Speed"),
            arc_side=_child_text(retract_node, "RetractArcSide", "Automatic"),
            overlap=_float_text(retract_node, "OverLap"),
        )
    return approach, retract


def read_pgmx_snapshot(path: Path, *, include_xml_text: bool = False) -> PgmxSnapshot:
    """Lee un `.pgmx` y devuelve una foto normalizada de sus entidades."""

    root, entries, xml_entry_name = sp._load_pgmx_container(path)
    state = sp.read_pgmx_state(path)

    workpiece_node = root.find("./{*}Workpieces/{*}WorkPiece")
    workpiece = None
    if workpiece_node is not None:
        workpiece = PgmxWorkpieceSnapshot(
            id=sp._text(workpiece_node, "./{*}Key/{*}ID"),
            object_type=sp._text(workpiece_node, "./{*}Key/{*}ObjectType"),
            name=sp._text(workpiece_node, "./{*}Name"),
            length=sp._safe_float(sp._text(workpiece_node, "./{*}Length"), 0.0),
            width=sp._safe_float(sp._text(workpiece_node, "./{*}Width"), 0.0),
            depth=sp._safe_float(sp._text(workpiece_node, "./{*}Depth"), 0.0),
            length_name=sp._text(workpiece_node, "./{*}LengthName"),
            width_name=sp._text(workpiece_node, "./{*}WidthName"),
            depth_name=sp._text(workpiece_node, "./{*}DepthName"),
            geometry_type=sp._xsi_type(_first_child(workpiece_node, "Geometry")),
        )

    variables: list[PgmxVariableSnapshot] = []
    for variable in root.findall("./{*}Variables/{*}Variable"):
        value_node = _first_child(variable, "Value")
        value_text = (value_node.text or "").strip() if value_node is not None and value_node.text is not None else ""
        variables.append(
            PgmxVariableSnapshot(
                id=sp._text(variable, "./{*}Key/{*}ID"),
                object_type=sp._text(variable, "./{*}Key/{*}ObjectType"),
                name=sp._text(variable, "./{*}Name"),
                description=sp._text(variable, "./{*}Description"),
                physical_unit_type=sp._text(variable, "./{*}FisicalUnitType"),
                is_read_only=sp._safe_bool(sp._text(variable, "./{*}IsReadOnly"), False),
                scope=sp._text(variable, "./{*}Scope"),
                value_type=sp._text(variable, "./{*}Type"),
                value_runtime_type=sp._xsi_type(value_node),
                value_text=value_text,
                value_number=sp._safe_float(value_text, 0.0) if value_text else None,
            )
        )

    expressions: list[PgmxExpressionSnapshot] = []
    expressions_by_ref_id: dict[str, list[ET.Element]] = {}
    for expression in root.findall("./{*}Expressions/{*}Expression"):
        referenced_object_node = _first_child(expression, "ReferencedObject")
        referenced_object = _object_ref(referenced_object_node)
        if referenced_object is not None and referenced_object.id:
            expressions_by_ref_id.setdefault(referenced_object.id, []).append(expression)
        property_node = _first_child(expression, "Property")
        expressions.append(
            PgmxExpressionSnapshot(
                id=sp._text(expression, "./{*}Key/{*}ID"),
                object_type=sp._text(expression, "./{*}Key/{*}ObjectType"),
                name=sp._text(expression, "./{*}Name"),
                property_type=sp._xsi_type(property_node),
                field_path=_field_path(property_node),
                referenced_object=referenced_object,
                value=sp._text(expression, "./{*}Value"),
            )
        )

    planes: list[PgmxPlaneSnapshot] = []
    plane_name_by_id: dict[str, str] = {}
    for plane in root.findall("./{*}Planes/{*}Plane"):
        plane_id = sp._text(plane, "./{*}Key/{*}ID")
        plane_name = sp._text(plane, "./{*}Name")
        plane_type = sp._text(plane, "./{*}Type") or plane_name
        plane_name_by_id[plane_id] = plane_type
        planes.append(
            PgmxPlaneSnapshot(
                id=plane_id,
                object_type=sp._text(plane, "./{*}Key/{*}ObjectType"),
                name=plane_name,
                plane_type=plane_type,
                generator_ref=_object_ref(_first_child(plane, "GeneratorKey")),
                is_right_handed=sp._safe_bool(sp._text(plane, "./{*}IsRightHanded"), False),
                placement=_placement_snapshot(_first_child(plane, "Placement")),
                workpiece_ref=_object_ref(_first_child(plane, "WorkpieceID")),
                x_dimension=sp._safe_float(sp._text(plane, "./{*}XDimension"), 0.0),
                y_dimension=sp._safe_float(sp._text(plane, "./{*}YDimension"), 0.0),
            )
        )

    geometries: list[PgmxGeometrySnapshot] = []
    geometry_plane_name_by_id: dict[str, str] = {}
    for geometry in root.findall("./{*}Geometries/{*}GeomGeometry"):
        geometry_id = sp._text(geometry, "./{*}Key/{*}ID")
        plane_ref = _object_ref(_first_child(geometry, "PlaneID"))
        if plane_ref is not None and plane_ref.id:
            geometry_plane_name_by_id[geometry_id] = plane_name_by_id.get(plane_ref.id, "")
        profile = sp._extract_geometry_profile(geometry)
        point = None
        if profile is not None and profile.geometry_type == "GeomCartesianPoint":
            point = profile.center_point
        geometries.append(
            PgmxGeometrySnapshot(
                id=geometry_id,
                object_type=sp._text(geometry, "./{*}Key/{*}ObjectType"),
                name=sp._text(geometry, "./{*}Name"),
                geometry_type=sp._xsi_type(geometry),
                is_absolute=sp._safe_bool(sp._text(geometry, "./{*}IsAbsolute"), False),
                plane_ref=plane_ref,
                profile=profile,
                curve=_curve_snapshot_from_node(geometry),
                point=point,
            )
        )

    operations_raw = {
        sp._text(operation, "./{*}Key/{*}ID"): operation
        for operation in root.findall("./{*}Operations/{*}Operation")
    }

    operations: list[PgmxOperationSnapshot] = []
    for operation in operations_raw.values():
        approach, retract = _operation_specs(operation)
        machine_functions_node = _first_child(operation, "MachineFunctions")
        machine_functions = ()
        if machine_functions_node is not None:
            machine_functions = tuple(
                _machine_function_snapshot(node)
                for node in list(machine_functions_node)
            )
        toolpaths = tuple(
            _toolpath_snapshot(node)
            for node in operation.findall("./{*}ToolpathList/{*}Toolpath")
        )
        operations.append(
            PgmxOperationSnapshot(
                id=sp._text(operation, "./{*}Key/{*}ID"),
                object_type=sp._text(operation, "./{*}Key/{*}ObjectType"),
                name=sp._text(operation, "./{*}Name"),
                operation_type=sp._xsi_type(operation),
                activate_cnc_correction=sp._safe_bool(sp._text(operation, "./{*}ActivateCNCCorrection"), False),
                toolpath_priority=sp._safe_bool(sp._text(operation, "./{*}ToolpathPriority"), False),
                approach_security_plane=sp._safe_float(sp._text(operation, "./{*}ApproachSecurityPlane"), 0.0),
                retract_security_plane=sp._safe_float(sp._text(operation, "./{*}RetractSecurityPlane"), 0.0),
                head_rotation=sp._safe_float(sp._text(operation, "./{*}HeadRotation"), 0.0),
                start_point=_tuple_point(_first_child(operation, "StartPoint")),
                technology=_technology_snapshot(_first_child(operation, "Technology")),
                tool_key=_object_ref(_first_child(operation, "ToolKey")),
                overcut_length=sp._safe_float(sp._text(operation, "./{*}OvercutLength"), 0.0),
                cutting_depth=_optional_float_text(operation, "CuttingDepth"),
                approach=approach,
                retract=retract,
                milling_strategy=sp._extract_milling_strategy_spec_from_operation(operation),
                allowance_bottom=_optional_float_text(operation, "AllowanceBottom"),
                allowance_side=_optional_float_text(operation, "AllowanceSide"),
                toolpaths=toolpaths,
                machine_functions=machine_functions,
            )
        )

    features: list[PgmxFeatureSnapshot] = []
    depth_variable_name = workpiece.depth_name if workpiece is not None else "dz1"
    for feature in root.findall("./{*}Features/{*}ManufacturingFeature"):
        feature_id = sp._text(feature, "./{*}Key/{*}ID")
        geometry_ref = _object_ref(_first_child(feature, "GeometryID"))
        operation_refs = tuple(
            _object_ref(node) or PgmxObjectRefSnapshot("", "")
            for node in feature.findall("./{*}OperationIDs/{*}ReferenceKey")
        )
        linked_operation = None
        for operation_ref in operation_refs:
            linked_operation = operations_raw.get(operation_ref.id)
            if linked_operation is not None:
                break
        geometry_plane_name = None
        if geometry_ref is not None:
            geometry_plane_name = geometry_plane_name_by_id.get(geometry_ref.id) or None
        plane_name_for_depth = geometry_plane_name or "Top"
        plane_span = sp._drilling_axis_span(state, plane_name_for_depth)
        depth_variable_name_for_plane = (
            sp._drilling_axis_variable_name(workpiece_node, plane_name_for_depth)
            if workpiece_node is not None
            else depth_variable_name
        )
        features.append(
            PgmxFeatureSnapshot(
                id=feature_id,
                object_type=sp._text(feature, "./{*}Key/{*}ObjectType"),
                name=sp._text(feature, "./{*}Name"),
                feature_type=sp._xsi_type(feature),
                geometry_ref=geometry_ref,
                operation_refs=operation_refs,
                workpiece_ref=_object_ref(_first_child(feature, "WorkpieceID")),
                bottom_condition_type=sp._xsi_type(_first_child(feature, "BottomCondition")),
                depth_start=_optional_float_text(_first_child(feature, "Depth"), "StartDepth"),
                depth_end=_optional_float_text(_first_child(feature, "Depth"), "EndDepth"),
                depth_spec=_parse_feature_depth_spec(
                    feature,
                    linked_operation,
                    expressions_by_ref_id.get(feature_id, []),
                    depth_variable_name_for_plane,
                    plane_span,
                ),
                plane_name=geometry_plane_name,
                side_of_feature=sp._text(feature, "./{*}SideOfFeature"),
                material_position=sp._text(feature, "./{*}MaterialPosition"),
                side_offset=_optional_float_text(feature, "SideOffset"),
                tool_width=_optional_float_text(_first_child(feature, "SweptShape"), "Width"),
                diameter=_optional_float_text(feature, "Diameter"),
                taper_height=_optional_float_text(feature, "TaperHeight"),
                is_geom_same_direction=(
                    sp._safe_bool(sp._text(feature, "./{*}IsGeomSameDirection"), False)
                    if _first_child(feature, "IsGeomSameDirection") is not None
                    else None
                ),
                is_precise=(
                    sp._safe_bool(sp._text(feature, "./{*}IsPrecise"), False)
                    if _first_child(feature, "IsPrecise") is not None
                    else None
                ),
            )
        )

    working_steps: list[PgmxWorkingStepSnapshot] = []
    for step in root.findall("./{*}Workplans/{*}MainWorkplan/{*}Elements/{*}Executable"):
        working_steps.append(
            PgmxWorkingStepSnapshot(
                id=sp._text(step, "./{*}Key/{*}ID"),
                object_type=sp._text(step, "./{*}Key/{*}ObjectType"),
                name=sp._text(step, "./{*}Name"),
                description=sp._text(step, "./{*}Description"),
                is_enabled=sp._safe_bool(sp._text(step, "./{*}IsEnabled"), False),
                priority=int(sp._safe_float(sp._text(step, "./{*}Priority"), 0.0)),
                manufacturing_feature_ref=_object_ref(_first_child(step, "ManufacturingFeatureID")),
                operation_ref=_object_ref(_first_child(step, "OperationID")),
            )
        )

    xml_text = None
    if include_xml_text:
        xml_text = entries[xml_entry_name].decode("utf-8", errors="ignore")

    return PgmxSnapshot(
        source_path=path,
        xml_entry_name=xml_entry_name,
        container_entries=tuple(sorted(entries.keys())),
        project_name=sp._text(root, "./{*}Name"),
        state=state,
        workpiece=workpiece,
        variables=tuple(variables),
        expressions=tuple(expressions),
        planes=tuple(planes),
        geometries=tuple(geometries),
        features=tuple(features),
        operations=tuple(operations),
        working_steps=tuple(working_steps),
        xml_text=xml_text,
    )


def snapshot_to_dict(snapshot: PgmxSnapshot) -> dict[str, Any]:
    """Convierte un snapshot a un diccionario JSON-friendly."""

    def convert(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if is_dataclass(value):
            return {
                field.name: convert(getattr(value, field.name))
                for field in fields(value)
            }
        if isinstance(value, tuple):
            return [convert(item) for item in value]
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        return value

    return convert(snapshot)


def write_pgmx_snapshot_json(
    snapshot: PgmxSnapshot,
    output_path: Path,
    *,
    indent: int = 2,
) -> Path:
    output_path.write_text(
        json.dumps(snapshot_to_dict(snapshot), indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vuelca un snapshot integral de un archivo .pgmx.")
    parser.add_argument("pgmx_path", help="Ruta al archivo .pgmx a inspeccionar.")
    parser.add_argument(
        "--output",
        help="Ruta de salida JSON. Si no se indica, imprime por stdout.",
    )
    parser.add_argument(
        "--include-xml-text",
        action="store_true",
        help="Incluye tambien el XML completo normalizado dentro del snapshot.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentacion del JSON de salida.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    snapshot = read_pgmx_snapshot(
        Path(args.pgmx_path),
        include_xml_text=bool(args.include_xml_text),
    )
    payload = json.dumps(
        snapshot_to_dict(snapshot),
        indent=int(args.indent),
        ensure_ascii=False,
    )
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
