"""Motor COMPARTIDO de autoría de perfiles curvos (PGMX).

`_append_curve_profile_milling` arma feature + geometría + operación + working step para
cualquier fresado basado en una curva (línea, arco, círculo, polilínea, galceado). Lo usan
`arc.py`, `circle.py`, `poly_profile.py` y `squaring.py`.

(La antigua `PolylineMillingSpec` — polilínea RECTA — vivía acá; quedó unificada dentro de la
polilínea general de `poly_profile.py`, que acepta el atajo `points=`.)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

from ..common.geometry import (
    GeometryProfileSpec,
    _CurveSpec,
    _build_geometry_from_curve_spec,
    _curve_spec_from_profile_geometry,
    _geometry_object_type,
    _profile_entry_exit_context,
)
from ..common.leads import (
    _build_generated_approach_curve_for_profile,
    _build_generated_lift_curve_for_profile,
)
from ..common.piece import _workpiece_depth_name
from ..common.xml import (
    _build_depth_expression,
    _build_property_expression,
    _build_working_step,
    _find_plane_ref,
    _reserve_ids,
    _text,
)
from ._common import _build_profile_feature, _uses_feature_depth_expressions
from .line import _build_line_operation

__all__ = ["_append_curve_profile_milling"]


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
    has_enabled_expr = getattr(spec, "is_enabled_expr", None) is not None

    geometry_member_count = len(generated_geometry_curve.member_serializations)
    n_extra = (2 if uses_depth_expressions else 0) + has_enabled_expr
    reserved_ids = _reserve_ids(
        root,
        geometry_member_count + 4 + n_extra,
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
    j = operation_index + 3
    start_expression_id = end_expression_id = None
    if uses_depth_expressions:
        start_expression_id = reserved_ids[j]; j += 1
        end_expression_id = reserved_ids[j]; j += 1
    enabled_expr_id = reserved_ids[j] if has_enabled_expr else None
    last_reserved_id = enabled_expr_id or end_expression_id or step_id

    generated_trajectory_curve = _curve_spec_from_profile_geometry(generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or generated_trajectory_curve
    start_point, end_point, _, _ = _profile_entry_exit_context(generated_toolpath_profile)

    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)

    next_generated_aux_id = int(last_reserved_id) + 1
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
    if has_enabled_expr and enabled_expr_id is not None:
        expressions.append(
            _build_property_expression(
                enabled_expr_id,
                step_id,
                "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep",
                "IsEnabled",
                getattr(spec, "is_enabled_expr"),
            )
        )
