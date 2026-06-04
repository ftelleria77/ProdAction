"""Approach and retract contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

from .geometry import (
    GeometryProfileSpec,
    _CurveSpec,
    _build_oriented_maestro_arc_serialization,
    _build_toolpath_description,
    _composite_curve_spec,
    _normalize_side_of_feature,
    _profile_endpoint_points_3d,
    _profile_entry_exit_context,
    _resolve_toolpath_direction,
    _trimmed_curve_spec,
)
from .xml import _safe_bool, _safe_float, _text

__all__ = [
    "ApproachSpec",
    "RetractSpec",
    "build_approach_spec",
    "build_retract_spec",
    "_extract_approach_spec_from_operation",
    "_extract_retract_spec_from_operation",
    "_build_down_arc_entry_curve",
    "_build_down_line_entry_curve",
    "_build_generated_approach_curve",
    "_build_generated_approach_curve_for_profile",
    "_build_generated_lift_curve",
    "_build_generated_lift_curve_for_profile",
    "_build_oriented_maestro_arc_basis",
    "_build_quote_arc_entry_curve",
    "_build_quote_arc_exit_curve",
    "_build_up_arc_exit_curve",
    "_build_up_line_exit_curve",
    "_build_vertical_toolpath_curve",
    "_dominant_component_sign_2d",
    "_linear_lead_distance",
    "_normalize_approach_arc_side",
    "_normalize_approach_mode",
    "_normalize_approach_spec",
    "_normalize_approach_type",
    "_normalize_retract_arc_side",
    "_normalize_retract_mode",
    "_normalize_retract_spec",
    "_normalize_retract_type",
    "_preferred_side_for_arc",
    "_quote_arc_radius",
    "_side_normal_for_direction",
]


@dataclass(frozen=True)
class ApproachSpec:
    """Configuracion reutilizable del approach de un fresado."""

    is_enabled: bool = False
    approach_type: str = "Line"
    mode: str = "Down"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"


@dataclass(frozen=True)
class RetractSpec:
    """Configuracion reutilizable del retract de un fresado."""

    is_enabled: bool = False
    retract_type: str = "Line"
    mode: str = "Up"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"
    overlap: float = 0.0


def _normalize_approach_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("ApproachType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_approach_mode(value: Optional[str]) -> str:
    raw = (value or "Down").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "down": "Down",
        "vertical": "Down",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("ApproachMode invalido. Valores admitidos: Down o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_approach_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("ApproachArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def _normalize_retract_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("RetractType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_retract_mode(value: Optional[str]) -> str:
    raw = (value or "Up").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "up": "Up",
        "subida": "Up",
        "vertical": "Up",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("RetractMode invalido. Valores admitidos: Up o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_retract_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("RetractArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def build_approach_spec(
    enabled: Optional[bool] = None,
    *,
    approach_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
) -> ApproachSpec:
    """Construye un `ApproachSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Approach` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, approach_type, mode, radius_multiplier, speed, arc_side)
    )
    if not has_explicit_configuration:
        return ApproachSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Down"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return ApproachSpec(
        is_enabled=is_enabled,
        approach_type=_normalize_approach_type(approach_type or "Line"),
        mode=_normalize_approach_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_approach_arc_side(arc_side or "Automatic"),
    )


def build_retract_spec(
    enabled: Optional[bool] = None,
    *,
    retract_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
    overlap: Optional[float] = None,
) -> RetractSpec:
    """Construye un `RetractSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Retract` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, retract_type, mode, radius_multiplier, speed, arc_side, overlap)
    )
    if not has_explicit_configuration:
        return RetractSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Up"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return RetractSpec(
        is_enabled=is_enabled,
        retract_type=_normalize_retract_type(retract_type or "Line"),
        mode=_normalize_retract_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_retract_arc_side(arc_side or "Automatic"),
        overlap=0.0 if overlap is None else float(overlap),
    )


def _normalize_approach_spec(approach: Optional[ApproachSpec]) -> ApproachSpec:
    if approach is None:
        return ApproachSpec()
    return build_approach_spec(
        enabled=approach.is_enabled,
        approach_type=approach.approach_type,
        mode=approach.mode,
        radius_multiplier=approach.radius_multiplier,
        speed=approach.speed,
        arc_side=approach.arc_side,
    )


def _normalize_retract_spec(retract: Optional[RetractSpec]) -> RetractSpec:
    if retract is None:
        return RetractSpec()
    return build_retract_spec(
        enabled=retract.is_enabled,
        retract_type=retract.retract_type,
        mode=retract.mode,
        radius_multiplier=retract.radius_multiplier,
        speed=retract.speed,
        arc_side=retract.arc_side,
        overlap=retract.overlap,
    )


def _extract_approach_spec_from_operation(operation: ET.Element) -> ApproachSpec:
    return build_approach_spec(
        enabled=_safe_bool(_text(operation, "./{*}Approach/{*}IsEnabled"), False),
        approach_type=_text(operation, "./{*}Approach/{*}ApproachType", "Line"),
        mode=_text(operation, "./{*}Approach/{*}ApproachMode", "Down"),
        radius_multiplier=_safe_float(_text(operation, "./{*}Approach/{*}RadiusMultiplier"), 1.2),
        speed=_safe_float(_text(operation, "./{*}Approach/{*}Speed"), 0.0),
        arc_side=_text(operation, "./{*}Approach/{*}ApproachArcSide", "Automatic"),
    )


def _extract_retract_spec_from_operation(operation: ET.Element) -> RetractSpec:
    return build_retract_spec(
        enabled=_safe_bool(_text(operation, "./{*}Retract/{*}IsEnabled"), False),
        retract_type=_text(operation, "./{*}Retract/{*}RetractType", "Line"),
        mode=_text(operation, "./{*}Retract/{*}RetractMode", "Up"),
        radius_multiplier=_safe_float(_text(operation, "./{*}Retract/{*}RadiusMultiplier"), 1.2),
        speed=_safe_float(_text(operation, "./{*}Retract/{*}Speed"), 0.0),
        arc_side=_text(operation, "./{*}Retract/{*}RetractArcSide", "Automatic"),
        overlap=_safe_float(_text(operation, "./{*}Retract/{*}OverLap"), 0.0),
    )


def _preferred_side_for_arc(side_of_feature: str, arc_side: str) -> str:
    normalized_side = _normalize_side_of_feature(side_of_feature)
    if normalized_side != "Center":
        return normalized_side
    normalized_arc_side = _normalize_approach_arc_side(arc_side)
    if normalized_arc_side in {"Left", "Right"}:
        return normalized_arc_side
    return "Right"


def _side_normal_for_direction(
    direction_x: float,
    direction_y: float,
    side_of_feature: str,
    arc_side: str,
) -> tuple[tuple[float, float], float]:
    right_normal = (direction_y, -direction_x)
    left_normal = (-right_normal[0], -right_normal[1])
    preferred_side = _preferred_side_for_arc(side_of_feature, arc_side)
    if preferred_side == "Left":
        return left_normal, 1.0
    return right_normal, -1.0


def _build_vertical_toolpath_curve(
    x_value: float,
    y_value: float,
    start_z: float,
    end_z: float,
) -> _CurveSpec:
    # Maestro mantiene un toolpath vertical en Approach/Lift aunque la estrategia este deshabilitada.
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (x_value, y_value, start_z),
            (x_value, y_value, end_z),
        )
    )


def _quote_arc_radius(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * max(radius_multiplier - 1.0, 0.0)


def _linear_lead_distance(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * radius_multiplier


def _dominant_component_sign_2d(vector: tuple[float, float]) -> float:
    x_value, y_value = vector
    if abs(x_value) >= abs(y_value):
        if not math.isclose(x_value, 0.0, abs_tol=1e-15):
            return 1.0 if x_value > 0.0 else -1.0
    if not math.isclose(y_value, 0.0, abs_tol=1e-15):
        return 1.0 if y_value > 0.0 else -1.0
    return 1.0


def _build_oriented_maestro_arc_basis(
    direction: tuple[float, float],
    side_normal: tuple[float, float],
    normal_z: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    # Maestro serializa estos arcos con una base 3D orientada y pequenos epsilon
    # en algunos componentes. Mantener esta estructura ayuda a que el XML sintetizado
    # se parezca mas al guardado manualmente desde Maestro.
    epsilon = math.ulp(0.5)
    direction_x, direction_y = direction
    side_x, side_y = side_normal
    u_vector = (
        0.0 if math.isclose(side_x, 0.0, abs_tol=1e-15) else (normal_z * side_x),
        normal_z * side_y,
        epsilon * normal_z,
    )
    v_vector = (
        -normal_z * direction_x,
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-normal_z * direction_y),
        0.0,
    )
    normal_vector = (
        (-0.0 if normal_z > 0.0 else 0.0)
        if math.isclose(direction_y, 0.0, abs_tol=1e-15)
        else (epsilon * direction_y),
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-epsilon * direction_x),
        normal_z,
    )
    return normal_vector, u_vector, v_vector


def _build_quote_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. bajada vertical en el punto inicial del acercamiento
    # 2. cuarto de arco en la cota de corte hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = entry_point[0] + (side_normal[0] * arc_radius)
    center_y = entry_point[1] + (side_normal[1] * arc_radius)
    plunge_x = center_x - (direction_x * arc_radius)
    plunge_y = center_y - (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = (1.5 * math.pi) if normal_z < 0.0 else (0.5 * math.pi)
    end_angle = (2.0 * math.pi) if normal_z < 0.0 else math.pi

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, cut_z),
            ),
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
        ]
    )


def _build_down_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Down:
    # 1. bajada vertical hasta `cut_z + radio`
    # 2. cuarto de arco en un plano vertical hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    right_normal_x = direction_y
    right_normal_y = -direction_x
    pre_entry_z = cut_z + arc_radius
    plunge_x = entry_point[0] - (direction_x * arc_radius)
    plunge_y = entry_point[1] - (direction_y * arc_radius)

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, pre_entry_z),
            ),
            _build_oriented_maestro_arc_serialization(
                1.5 * math.pi,
                2.0 * math.pi,
                (entry_point[0], entry_point[1], pre_entry_z),
                (right_normal_x, right_normal_y, 0.0),
                (0.0, 0.0, -1.0),
                (direction_x, direction_y, 0.0),
                arc_radius,
                z_value=pre_entry_z,
            ),
        ]
    )


def _build_down_line_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Down:
    # una sola bajada oblicua desde un punto previo desplazado
    # en la direccion opuesta al avance del toolpath.
    pre_entry_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    pre_entry_x = entry_point[0] - (direction_x * pre_entry_distance)
    pre_entry_y = entry_point[1] - (direction_y * pre_entry_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (pre_entry_x, pre_entry_y, clearance_z),
            (entry_point[0], entry_point[1], cut_z),
        )
    )


def _build_up_line_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Up:
    # una sola subida oblicua hacia un punto final desplazado
    # sobre la direccion de salida del toolpath.
    post_exit_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    post_exit_x = exit_point[0] + (direction_x * post_exit_distance)
    post_exit_y = exit_point[1] + (direction_y * post_exit_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (exit_point[0], exit_point[1], cut_z),
            (post_exit_x, post_exit_y, clearance_z),
        )
    )


def _build_quote_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. cuarto de arco en la cota de corte desde el punto de salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = exit_point[0] + (side_normal[0] * arc_radius)
    center_y = exit_point[1] + (side_normal[1] * arc_radius)
    lift_x = center_x + (direction_x * arc_radius)
    lift_y = center_y + (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = 0.0 if normal_z < 0.0 else math.pi
    end_angle = (0.5 * math.pi) if normal_z < 0.0 else (1.5 * math.pi)

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, cut_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _build_up_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Up:
    # 1. cuarto de arco en un plano vertical desde la salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    plane_normal = (
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else direction_y,
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-direction_x),
    )
    basis_sign = _dominant_component_sign_2d(plane_normal)
    center_z = cut_z + arc_radius
    lift_x = exit_point[0] + (direction_x * arc_radius)
    lift_y = exit_point[1] + (direction_y * arc_radius)
    lift_z = center_z
    tangent_vector = (
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-basis_sign * direction_x),
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-basis_sign * direction_y),
        0.0,
    )

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                math.pi if basis_sign > 0.0 else 0.0,
                (1.5 * math.pi) if basis_sign > 0.0 else (0.5 * math.pi),
                exit_point,
                (plane_normal[0], plane_normal[1], 0.0),
                (0.0, 0.0, basis_sign),
                tangent_vector,
                arc_radius,
                z_value=center_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, lift_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _build_generated_approach_curve(
    state,
    spec,
    toolpath_start: tuple[float, float, float],
    toolpath_end: tuple[float, float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    approach = _normalize_approach_spec(spec.approach)
    clearance_z = state.depth + spec.security_plane
    cut_z = toolpath_start[2]
    direction_x, direction_y = _resolve_toolpath_direction(
        (toolpath_start[0], toolpath_start[1]),
        (toolpath_end[0], toolpath_end[1]),
        direction=direction,
    )
    if not approach.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_start[0], toolpath_start[1], clearance_z, cut_z)

    if approach.approach_type == "Line" and approach.mode == "Quote":
        pre_entry_distance = _linear_lead_distance(spec.tool_width, approach.radius_multiplier)
        pre_entry_x = toolpath_start[0] - (direction_x * pre_entry_distance)
        pre_entry_y = toolpath_start[1] - (direction_y * pre_entry_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, clearance_z),
                    (pre_entry_x, pre_entry_y, cut_z),
                ),
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, cut_z),
                    (toolpath_start[0], toolpath_start[1], cut_z),
                ),
            ]
        )

    if approach.approach_type == "Line" and approach.mode == "Down":
        return _build_down_line_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Quote":
        return _build_quote_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=approach.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Down":
        return _build_down_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un approach habilitado con "
        f"type={approach.approach_type} y mode={approach.mode}."
    )


def _build_generated_approach_curve_for_profile(
    state,
    spec,
    toolpath_profile: GeometryProfileSpec,
) -> _CurveSpec:
    """Construye el approach a partir de una trayectoria efectiva y su tangente de entrada."""

    toolpath_start, toolpath_end = _profile_endpoint_points_3d(toolpath_profile)
    _, _, start_direction, _ = _profile_entry_exit_context(toolpath_profile)
    return _build_generated_approach_curve(
        state,
        spec,
        toolpath_start,
        toolpath_end,
        direction=start_direction,
    )


def _build_generated_lift_curve(
    state,
    spec,
    toolpath_start: tuple[float, float, float],
    toolpath_end: tuple[float, float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    retract = _normalize_retract_spec(spec.retract)
    clearance_z = state.depth + spec.security_plane
    cut_z = toolpath_end[2]
    direction_x, direction_y = _resolve_toolpath_direction(
        (toolpath_start[0], toolpath_start[1]),
        (toolpath_end[0], toolpath_end[1]),
        direction=direction,
    )
    if not retract.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_end[0], toolpath_end[1], cut_z, clearance_z)

    if retract.retract_type == "Line" and retract.mode == "Quote":
        post_exit_distance = (spec.tool_width / 2.0) * retract.radius_multiplier
        post_exit_x = toolpath_end[0] + (direction_x * post_exit_distance)
        post_exit_y = toolpath_end[1] + (direction_y * post_exit_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (toolpath_end[0], toolpath_end[1], cut_z),
                    (post_exit_x, post_exit_y, cut_z),
                ),
                _build_toolpath_description(
                    (post_exit_x, post_exit_y, cut_z),
                    (post_exit_x, post_exit_y, clearance_z),
                ),
            ]
        )

    if retract.retract_type == "Line" and retract.mode == "Up":
        return _build_up_line_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Quote":
        return _build_quote_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=retract.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Up":
        return _build_up_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un retract habilitado con "
        f"type={retract.retract_type} y mode={retract.mode}."
    )


def _build_generated_lift_curve_for_profile(
    state,
    spec,
    toolpath_profile: GeometryProfileSpec,
) -> _CurveSpec:
    """Construye el lift a partir de una trayectoria efectiva y su tangente de salida."""

    toolpath_start, toolpath_end = _profile_endpoint_points_3d(toolpath_profile)
    _, _, _, end_direction = _profile_entry_exit_context(toolpath_profile)
    return _build_generated_lift_curve(
        state,
        spec,
        toolpath_start,
        toolpath_end,
        direction=end_direction,
    )
