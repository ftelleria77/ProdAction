"""Reusable geometry contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, Sequence

from .hydration import _load_pgmx_container
from .xml import _raw_text, _text, _xsi_type

__all__ = [
    "GeometryPrimitiveSpec",
    "GeometryProfileSpec",
    "_CurveSpec",
    "build_arc_geometry_primitive",
    "build_circle_geometry_profile",
    "build_composite_geometry_profile",
    "build_line_geometry_primitive",
    "build_line_geometry_profile",
    "build_point_geometry_profile",
    "read_pgmx_geometries",
    "_build_maestro_arc_serialization",
    "_build_maestro_line_serialization",
    "_build_oriented_maestro_arc_serialization",
    "_build_parameterized_line_geometry_primitive",
    "_build_profile_geometry_spec",
    "_build_toolpath_description",
    "_circle_curve_spec",
    "_composite_curve_spec",
    "_curve_spec_from_profile_geometry",
    "_extract_geometry_profile",
    "_format_maestro_number",
    "_format_maestro_orientation_number",
    "_normalize_curve_serialization_text",
    "_normalize_geometry_winding",
    "_parse_circle_geometry_profile",
    "_parse_geometry_primitive",
    "_parse_trimmed_curve_arc",
    "_parse_trimmed_curve_line",
    "_points_close_2d",
    "_points_close_3d",
    "_primitive_end_tangent_2d",
    "_primitive_sample_points_2d",
    "_primitive_start_tangent_2d",
    "_primitive_to_serialization",
    "_profile_bounding_box",
    "_profile_signed_area",
    "_sample_arc_point",
    "_trimmed_curve_spec",
]


@dataclass(frozen=True)
class GeometryPrimitiveSpec:
    """Primitiva geometrica 2D/3D reusable para perfiles Maestro."""

    primitive_type: str
    start_point: tuple[float, float, float]
    end_point: tuple[float, float, float]
    parameter_start: float = 0.0
    parameter_end: float = 0.0
    center_point: Optional[tuple[float, float, float]] = None
    radius: Optional[float] = None
    normal_vector: Optional[tuple[float, float, float]] = None
    u_vector: Optional[tuple[float, float, float]] = None
    v_vector: Optional[tuple[float, float, float]] = None
    direction_hint: Optional[tuple[float, float, float]] = None


@dataclass(frozen=True)
class GeometryProfileSpec:
    """Perfil geometrico identificado o construido para futura sintesis."""

    geometry_type: str
    family: str
    primitives: tuple[GeometryPrimitiveSpec, ...] = ()
    is_closed: bool = False
    winding: Optional[str] = None
    start_mode: Optional[str] = None
    has_arcs: bool = False
    corner_radii: tuple[float, ...] = ()
    bounding_box: Optional[tuple[float, float, float, float]] = None
    center_point: Optional[tuple[float, float, float]] = None
    radius: Optional[float] = None
    serialization: Optional[str] = None
    member_serializations: tuple[str, ...] = ()

    @property
    def classification_key(self) -> str:
        if self.winding:
            return f"{self.family}_{self.winding}"
        return self.family

    @property
    def primitive_count(self) -> int:
        return len(self.primitives)


@dataclass(frozen=True)
class _CurveSpec:
    """Serializacion XML de una curva usada en geometria o toolpaths."""

    geometry_type: str = "GeomTrimmedCurve"
    serialization: Optional[str] = None
    member_keys: tuple[str, ...] = ()
    member_serializations: tuple[str, ...] = ()


def _normalize_geometry_winding(value: Optional[str]) -> str:
    raw = (value or "CounterClockwise").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "counterclockwise": "CounterClockwise",
        "ccw": "CounterClockwise",
        "antihorario": "CounterClockwise",
        "clockwise": "Clockwise",
        "cw": "Clockwise",
        "horario": "Clockwise",
    }
    if raw not in mapping:
        raise ValueError("Winding invalido. Valores admitidos: CounterClockwise/Antihorario o Clockwise/Horario.")
    return mapping[raw]


def build_line_geometry_primitive(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    *,
    start_z: float = 0.0,
    end_z: float = 0.0,
) -> GeometryPrimitiveSpec:
    """Construye una primitiva lineal reusable para perfiles Maestro."""

    start_point = (float(start_x), float(start_y), float(start_z))
    end_point = (float(end_x), float(end_y), float(end_z))
    length = math.dist(start_point, end_point)
    if length <= 1e-9:
        raise ValueError("Una primitiva lineal necesita longitud mayor que cero.")
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=start_point,
        end_point=end_point,
        parameter_start=0.0,
        parameter_end=length,
    )


def _build_parameterized_line_geometry_primitive(
    origin_point: tuple[float, float, float],
    direction: tuple[float, float, float],
    parameter_start: float,
    parameter_end: float,
) -> GeometryPrimitiveSpec:
    direction_length = math.sqrt(
        (direction[0] * direction[0]) + (direction[1] * direction[1]) + (direction[2] * direction[2])
    )
    if direction_length <= 1e-9:
        raise ValueError("La direccion de una linea parametrizada no puede ser nula.")
    unit_direction = (
        direction[0] / direction_length,
        direction[1] / direction_length,
        direction[2] / direction_length,
    )
    start_value = float(parameter_start)
    end_value = float(parameter_end)
    if math.isclose(start_value, end_value, abs_tol=1e-9):
        raise ValueError("Una linea parametrizada necesita un rango no nulo.")
    start_point = (
        origin_point[0] + (unit_direction[0] * start_value),
        origin_point[1] + (unit_direction[1] * start_value),
        origin_point[2] + (unit_direction[2] * start_value),
    )
    end_point = (
        origin_point[0] + (unit_direction[0] * end_value),
        origin_point[1] + (unit_direction[1] * end_value),
        origin_point[2] + (unit_direction[2] * end_value),
    )
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=start_point,
        end_point=end_point,
        parameter_start=start_value,
        parameter_end=end_value,
    )


def build_arc_geometry_primitive(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    center_x: float,
    center_y: float,
    *,
    z_value: float = 0.0,
    winding: Optional[str] = None,
) -> GeometryPrimitiveSpec:
    """Construye una primitiva de arco en XY reusable para perfiles Maestro."""

    normalized_winding = _normalize_geometry_winding(winding)
    normal_z = 1.0 if normalized_winding == "CounterClockwise" else -1.0
    normal_y = -0.0 if normalized_winding == "CounterClockwise" else 0.0
    v_x = -0.0 if normalized_winding == "CounterClockwise" else 0.0
    start_point = (float(start_x), float(start_y), float(z_value))
    end_point = (float(end_x), float(end_y), float(z_value))
    center_point = (float(center_x), float(center_y), float(z_value))
    start_radius = math.dist(start_point, center_point)
    end_radius = math.dist(end_point, center_point)
    if start_radius <= 1e-9 or end_radius <= 1e-9:
        raise ValueError("Una primitiva de arco necesita radio mayor que cero.")
    if not math.isclose(start_radius, end_radius, abs_tol=1e-6):
        raise ValueError("Los puntos inicial y final del arco deben estar al mismo radio del centro.")
    start_angle = _point_to_maestro_basis_angle((center_point[0], center_point[1]), (start_point[0], start_point[1]), normal_z)
    end_angle = _point_to_maestro_basis_angle((center_point[0], center_point[1]), (end_point[0], end_point[1]), normal_z)
    end_angle = _unwrap_maestro_arc_end_angle(start_angle, end_angle)
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=start_angle,
        parameter_end=end_angle,
        center_point=center_point,
        radius=start_radius,
        normal_vector=(0.0, normal_y, normal_z),
        u_vector=(1.0, 0.0, 0.0),
        v_vector=(v_x, normal_z, 0.0),
    )


def build_line_geometry_profile(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    *,
    start_z: float = 0.0,
    end_z: float = 0.0,
) -> GeometryProfileSpec:
    """Construye un perfil geometrico lineal ya serializado para Maestro."""

    primitive = build_line_geometry_primitive(
        start_x,
        start_y,
        end_x,
        end_y,
        start_z=start_z,
        end_z=end_z,
    )
    return _build_profile_geometry_spec(
        geometry_type="GeomTrimmedCurve",
        primitives=(primitive,),
    )


def build_point_geometry_profile(
    point_x: float,
    point_y: float,
    *,
    z_value: float = 0.0,
) -> GeometryProfileSpec:
    """Construye un punto geometrico Maestro listo para inspeccion o futura sintesis."""

    point = (float(point_x), float(point_y), float(z_value))
    primitive = GeometryPrimitiveSpec(
        primitive_type="Point",
        start_point=point,
        end_point=point,
    )
    return _build_profile_geometry_spec(
        geometry_type="GeomCartesianPoint",
        primitives=(primitive,),
    )


def build_circle_geometry_profile(
    center_x: float,
    center_y: float,
    radius: float,
    *,
    z_value: float = 0.0,
    winding: Optional[str] = None,
) -> GeometryProfileSpec:
    """Construye un perfil circular Maestro listo para futura sintesis."""

    normalized_winding = _normalize_geometry_winding(winding)
    radius_value = float(radius)
    if radius_value <= 1e-9:
        raise ValueError("Un perfil circular necesita radio mayor que cero.")
    normal_z = 1.0 if normalized_winding == "CounterClockwise" else -1.0
    serialization = _build_circle_geometry_serialization(
        center_point=(float(center_x), float(center_y), float(z_value)),
        radius=radius_value,
        normal_z=normal_z,
    )
    return GeometryProfileSpec(
        geometry_type="GeomCircle",
        family="Circle",
        is_closed=True,
        winding=normalized_winding,
        has_arcs=True,
        corner_radii=(radius_value,),
        bounding_box=(
            float(center_x) - radius_value,
            float(center_y) - radius_value,
            float(center_x) + radius_value,
            float(center_y) + radius_value,
        ),
        center_point=(float(center_x), float(center_y), float(z_value)),
        radius=radius_value,
        serialization=serialization,
    )


def build_composite_geometry_profile(
    primitives: Sequence[GeometryPrimitiveSpec],
) -> GeometryProfileSpec:
    """Construye un perfil compuesto reusable a partir de lineas y arcos."""

    normalized_primitives = tuple(primitives)
    if not normalized_primitives:
        raise ValueError("Un perfil compuesto necesita al menos una primitiva.")
    return _build_profile_geometry_spec(
        geometry_type="GeomCompositeCurve",
        primitives=normalized_primitives,
    )


def _build_toolpath_description(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    return _build_maestro_line_serialization(start_point, end_point)


def _format_maestro_number(value: float) -> str:
    number = float(value)
    if number == 0.0:
        return "-0" if math.copysign(1.0, number) < 0.0 else "0"
    if math.isclose(number, 0.0, abs_tol=1e-15):
        return "0"
    if number.is_integer():
        return str(int(number))
    return format(number, ".17g")


def _format_maestro_orientation_number(value: float) -> str:
    number = float(value)
    if number == 0.0:
        return "-0" if math.copysign(1.0, number) < 0.0 else "0"
    if number.is_integer():
        return str(int(number))
    text = format(number, ".17g")
    if "e" not in text and "E" not in text:
        return text
    mantissa, exponent = text.lower().split("e", 1)
    sign = exponent[:1]
    digits = exponent[1:].rjust(3, "0")
    return f"{mantissa}e{sign}{digits}"


def _normalize_curve_serialization_text(text: str) -> str:
    raw_text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = raw_text.split("\n")

    while lines and lines[0] == "":
        lines.pop(0)

    trailing_newline = raw_text.endswith("\n")
    while lines and lines[-1] == "":
        lines.pop()
        trailing_newline = True

    normalized = "\n".join(lines)
    if trailing_newline and normalized:
        return f"{normalized}\n"
    return normalized


def _build_parameterized_maestro_line_serialization(
    *,
    parameter_start: float,
    parameter_end: float,
    origin_point: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> str:
    return (
        f"8 {_format_maestro_number(parameter_start)} {_format_maestro_number(parameter_end)}\n"
        f"1 {_format_maestro_number(origin_point[0])} {_format_maestro_number(origin_point[1])} {_format_maestro_number(origin_point[2])} "
        f"{_format_maestro_orientation_number(direction[0])} {_format_maestro_orientation_number(direction[1])} {_format_maestro_orientation_number(direction[2])} \n"
    )


def _build_maestro_line_serialization(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    dz = end_point[2] - start_point[2]
    length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if length <= 1e-9:
        raise ValueError("No se puede serializar un segmento de longitud cero.")

    return _build_parameterized_maestro_line_serialization(
        parameter_start=0.0,
        parameter_end=length,
        origin_point=start_point,
        direction=(dx / length, dy / length, dz / length),
    )


def _points_close_2d(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    tolerance: float = 1e-9,
) -> bool:
    return math.isclose(point_a[0], point_b[0], abs_tol=tolerance) and math.isclose(
        point_a[1], point_b[1], abs_tol=tolerance
    )


def _normalize_positive_angle(angle: float) -> float:
    normalized = math.fmod(angle, 2.0 * math.pi)
    if normalized < 0.0:
        normalized += 2.0 * math.pi
    if math.isclose(normalized, 0.0, abs_tol=1e-12):
        return 0.0
    if math.isclose(normalized, 2.0 * math.pi, abs_tol=1e-12):
        return 0.0
    return normalized


def _point_to_maestro_basis_angle(
    center_point: tuple[float, float],
    point: tuple[float, float],
    normal_z: float,
) -> float:
    relative_x = point[0] - center_point[0]
    relative_y = point[1] - center_point[1]
    return _normalize_positive_angle(math.atan2(relative_y * normal_z, relative_x))


def _unwrap_maestro_arc_end_angle(start_angle: float, end_angle: float) -> float:
    """Desenvuelve el parametro final para preservar el avance real del arco."""

    if math.isclose(start_angle, end_angle, abs_tol=1e-12):
        return end_angle
    unwrapped_end = end_angle
    while unwrapped_end <= start_angle:
        unwrapped_end += 2.0 * math.pi
    return unwrapped_end


def _build_maestro_arc_serialization(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    center_point: tuple[float, float],
    normal_z: float,
    z_value: float = 0.0,
    radius: Optional[float] = None,
) -> str:
    resolved_radius = (
        math.hypot(start_point[0] - center_point[0], start_point[1] - center_point[1])
        if radius is None
        else float(radius)
    )
    if resolved_radius <= 1e-9:
        raise ValueError("No se puede serializar un arco de radio cero.")

    start_angle = _point_to_maestro_basis_angle(center_point, start_point, normal_z)
    end_angle = _point_to_maestro_basis_angle(center_point, end_point, normal_z)
    end_angle = _unwrap_maestro_arc_end_angle(start_angle, end_angle)

    return (
        f"8 {_format_maestro_number(start_angle)} {_format_maestro_number(end_angle)}\n"
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(z_value)} "
        f"0 0 {_format_maestro_number(normal_z)} 1 0 0 0 {_format_maestro_number(normal_z)} 0 {_format_maestro_number(resolved_radius)} \n"
    )


def _build_oriented_maestro_arc_serialization(
    start_angle: float,
    end_angle: float,
    center_point: tuple[float, float],
    normal_vector: tuple[float, float, float],
    u_vector: tuple[float, float, float],
    v_vector: tuple[float, float, float],
    radius: float,
    z_value: float = 0.0,
) -> str:
    if radius <= 1e-9:
        raise ValueError("No se puede serializar un arco de radio cero.")
    return (
        f"8 {_format_maestro_number(start_angle)} {_format_maestro_number(end_angle)}\n"
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(z_value)} "
        f"{_format_maestro_orientation_number(normal_vector[0])} {_format_maestro_orientation_number(normal_vector[1])} {_format_maestro_orientation_number(normal_vector[2])} "
        f"{_format_maestro_orientation_number(u_vector[0])} {_format_maestro_orientation_number(u_vector[1])} {_format_maestro_orientation_number(u_vector[2])} "
        f"{_format_maestro_orientation_number(v_vector[0])} {_format_maestro_orientation_number(v_vector[1])} {_format_maestro_orientation_number(v_vector[2])} "
        f"{_format_maestro_number(radius)} \n"
    )


def _build_circle_geometry_serialization(
    *,
    center_point: tuple[float, float, float],
    radius: float,
    normal_z: float,
) -> str:
    return (
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(center_point[2])} "
        f"0 0 {_format_maestro_orientation_number(normal_z)} 1 0 0 0 {_format_maestro_orientation_number(normal_z)} 0 "
        f"{_format_maestro_number(radius)}\n"
    )


def _points_close_3d(
    point_a: tuple[float, float, float],
    point_b: tuple[float, float, float],
    tolerance: float = 1e-6,
) -> bool:
    return (
        math.isclose(point_a[0], point_b[0], abs_tol=tolerance)
        and math.isclose(point_a[1], point_b[1], abs_tol=tolerance)
        and math.isclose(point_a[2], point_b[2], abs_tol=tolerance)
    )


def _normalize_vector_2d(
    vector: tuple[float, float],
    tolerance: float = 1e-9,
) -> Optional[tuple[float, float]]:
    length = math.hypot(vector[0], vector[1])
    if length <= tolerance:
        return None
    return (vector[0] / length, vector[1] / length)


def _vectors_parallel_same_direction_2d(
    vector_a: tuple[float, float],
    vector_b: tuple[float, float],
    tolerance: float = 1e-6,
) -> bool:
    normalized_a = _normalize_vector_2d(vector_a, tolerance=tolerance)
    normalized_b = _normalize_vector_2d(vector_b, tolerance=tolerance)
    if normalized_a is None or normalized_b is None:
        return False
    return math.isclose(normalized_a[0], normalized_b[0], abs_tol=tolerance) and math.isclose(
        normalized_a[1], normalized_b[1], abs_tol=tolerance
    )


def _sample_arc_point(
    center_point: tuple[float, float, float],
    u_vector: tuple[float, float, float],
    v_vector: tuple[float, float, float],
    radius: float,
    angle: float,
) -> tuple[float, float, float]:
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    return (
        center_point[0] + (radius * ((u_vector[0] * cos_angle) + (v_vector[0] * sin_angle))),
        center_point[1] + (radius * ((u_vector[1] * cos_angle) + (v_vector[1] * sin_angle))),
        center_point[2] + (radius * ((u_vector[2] * cos_angle) + (v_vector[2] * sin_angle))),
    )


def _arc_tangent_vector(
    primitive: GeometryPrimitiveSpec,
    angle: float,
) -> Optional[tuple[float, float]]:
    if primitive.radius is None or primitive.u_vector is None or primitive.v_vector is None:
        return None
    parameter_delta = primitive.parameter_end - primitive.parameter_start
    travel_sign = 1.0 if parameter_delta >= 0.0 else -1.0
    tangent_x = (
        (-primitive.u_vector[0] * math.sin(angle)) + (primitive.v_vector[0] * math.cos(angle))
    ) * primitive.radius * travel_sign
    tangent_y = (
        (-primitive.u_vector[1] * math.sin(angle)) + (primitive.v_vector[1] * math.cos(angle))
    ) * primitive.radius * travel_sign
    return _normalize_vector_2d((tangent_x, tangent_y))


def _primitive_start_tangent_2d(primitive: GeometryPrimitiveSpec) -> Optional[tuple[float, float]]:
    if primitive.primitive_type == "Line":
        return _normalize_vector_2d(
            (
                primitive.end_point[0] - primitive.start_point[0],
                primitive.end_point[1] - primitive.start_point[1],
            )
        )
    if primitive.primitive_type == "Arc":
        return _arc_tangent_vector(primitive, primitive.parameter_start)
    return None


def _primitive_end_tangent_2d(primitive: GeometryPrimitiveSpec) -> Optional[tuple[float, float]]:
    if primitive.primitive_type == "Line":
        return _normalize_vector_2d(
            (
                primitive.end_point[0] - primitive.start_point[0],
                primitive.end_point[1] - primitive.start_point[1],
            )
        )
    if primitive.primitive_type == "Arc":
        return _arc_tangent_vector(primitive, primitive.parameter_end)
    return None


def _primitive_sample_points_2d(primitive: GeometryPrimitiveSpec) -> tuple[tuple[float, float], ...]:
    if primitive.primitive_type == "Arc":
        if primitive.center_point is None or primitive.radius is None or primitive.u_vector is None or primitive.v_vector is None:
            return (
                (primitive.start_point[0], primitive.start_point[1]),
                (primitive.end_point[0], primitive.end_point[1]),
            )
        midpoint_angle = primitive.parameter_start + ((primitive.parameter_end - primitive.parameter_start) / 2.0)
        midpoint = _sample_arc_point(
            primitive.center_point,
            primitive.u_vector,
            primitive.v_vector,
            primitive.radius,
            midpoint_angle,
        )
        return (
            (primitive.start_point[0], primitive.start_point[1]),
            (midpoint[0], midpoint[1]),
            (primitive.end_point[0], primitive.end_point[1]),
        )
    return (
        (primitive.start_point[0], primitive.start_point[1]),
        (primitive.end_point[0], primitive.end_point[1]),
    )


def _profile_bounding_box(
    primitives: Sequence[GeometryPrimitiveSpec],
    *,
    circle_center: Optional[tuple[float, float, float]] = None,
    circle_radius: Optional[float] = None,
) -> Optional[tuple[float, float, float, float]]:
    if circle_center is not None and circle_radius is not None:
        return (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius,
        )

    sample_points: list[tuple[float, float]] = []
    for primitive in primitives:
        for point in _primitive_sample_points_2d(primitive):
            sample_points.append(point)
    if not sample_points:
        return None
    xs = [point[0] for point in sample_points]
    ys = [point[1] for point in sample_points]
    return (min(xs), min(ys), max(xs), max(ys))


def _profile_signed_area(primitives: Sequence[GeometryPrimitiveSpec]) -> float:
    sampled_points: list[tuple[float, float]] = []
    for primitive in primitives:
        primitive_points = list(_primitive_sample_points_2d(primitive))
        if not primitive_points:
            continue
        if sampled_points and _points_close_2d(sampled_points[-1], primitive_points[0]):
            primitive_points = primitive_points[1:]
        sampled_points.extend(primitive_points)
    if len(sampled_points) < 3:
        return 0.0
    if not _points_close_2d(sampled_points[0], sampled_points[-1]):
        sampled_points.append(sampled_points[0])
    double_area = 0.0
    for start_point, end_point in zip(sampled_points, sampled_points[1:]):
        double_area += (start_point[0] * end_point[1]) - (end_point[0] * start_point[1])
    return double_area / 2.0


def _primitive_to_serialization(primitive: GeometryPrimitiveSpec) -> str:
    if primitive.primitive_type == "Line":
        dx = primitive.end_point[0] - primitive.start_point[0]
        dy = primitive.end_point[1] - primitive.start_point[1]
        dz = primitive.end_point[2] - primitive.start_point[2]
        length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
        if length <= 1e-9:
            raise ValueError("No se puede serializar un segmento de longitud cero.")
        direction = (dx / length, dy / length, dz / length)
        if primitive.direction_hint is not None:
            direction = primitive.direction_hint
        origin_point = (
            primitive.start_point[0] - (direction[0] * primitive.parameter_start),
            primitive.start_point[1] - (direction[1] * primitive.parameter_start),
            primitive.start_point[2] - (direction[2] * primitive.parameter_start),
        )
        return _build_parameterized_maestro_line_serialization(
            parameter_start=primitive.parameter_start,
            parameter_end=primitive.parameter_end,
            origin_point=origin_point,
            direction=direction,
        )
    if primitive.primitive_type != "Arc":
        raise ValueError(f"Tipo de primitiva no soportado: {primitive.primitive_type}")
    if (
        primitive.center_point is None
        or primitive.radius is None
        or primitive.normal_vector is None
        or primitive.u_vector is None
        or primitive.v_vector is None
    ):
        raise ValueError("Una primitiva de arco necesita centro, radio y base orientada.")
    return _build_oriented_maestro_arc_serialization(
        primitive.parameter_start,
        primitive.parameter_end,
        (primitive.center_point[0], primitive.center_point[1]),
        primitive.normal_vector,
        primitive.u_vector,
        primitive.v_vector,
        primitive.radius,
        z_value=primitive.center_point[2],
    )


def _build_profile_geometry_spec(
    *,
    geometry_type: str,
    primitives: Sequence[GeometryPrimitiveSpec],
    serialization: Optional[str] = None,
    member_serializations: Sequence[str] = (),
) -> GeometryProfileSpec:
    normalized_primitives = tuple(primitives)
    if geometry_type != "GeomCircle" and not normalized_primitives:
        raise ValueError("El perfil geometrico necesita al menos una primitiva.")

    normalized_member_serializations = tuple(
        _normalize_curve_serialization_text(member_serialization)
        for member_serialization in member_serializations
    )
    normalized_serialization = (
        _normalize_curve_serialization_text(serialization)
        if serialization is not None
        else None
    )

    if geometry_type == "GeomCartesianPoint":
        if len(normalized_primitives) != 1 or normalized_primitives[0].primitive_type != "Point":
            raise ValueError("Un GeomCartesianPoint requiere exactamente una primitiva Point.")
        point = normalized_primitives[0].start_point
        if not _points_close_3d(normalized_primitives[0].start_point, normalized_primitives[0].end_point):
            raise ValueError("La primitiva Point debe usar el mismo punto como inicio y fin.")
        return GeometryProfileSpec(
            geometry_type="GeomCartesianPoint",
            family="Point",
            primitives=normalized_primitives,
            is_closed=False,
            winding=None,
            start_mode=None,
            has_arcs=False,
            corner_radii=(),
            bounding_box=(point[0], point[1], point[0], point[1]),
            center_point=point,
        )

    if geometry_type == "GeomTrimmedCurve":
        primitive = normalized_primitives[0]
        if primitive.primitive_type == "Line":
            delta_x = primitive.end_point[0] - primitive.start_point[0]
            delta_y = primitive.end_point[1] - primitive.start_point[1]
            if math.isclose(delta_x, 0.0, abs_tol=1e-6) and not math.isclose(delta_y, 0.0, abs_tol=1e-6):
                family = "LineVertical"
            elif math.isclose(delta_y, 0.0, abs_tol=1e-6) and not math.isclose(delta_x, 0.0, abs_tol=1e-6):
                family = "LineHorizontal"
            else:
                family = "Line"
            winding = None
            has_arcs = False
            corner_radii: tuple[float, ...] = ()
        else:
            family = "Arc"
            winding = (
                "CounterClockwise"
                if (primitive.normal_vector is None or primitive.normal_vector[2] >= 0.0)
                else "Clockwise"
            )
            has_arcs = True
            corner_radii = (float(primitive.radius),) if primitive.radius is not None else ()
        return GeometryProfileSpec(
            geometry_type="GeomTrimmedCurve",
            family=family,
            primitives=normalized_primitives,
            is_closed=False,
            winding=winding,
            start_mode=None,
            has_arcs=has_arcs,
            corner_radii=corner_radii,
            bounding_box=_profile_bounding_box(normalized_primitives),
            serialization=normalized_serialization or _primitive_to_serialization(primitive),
        )

    if geometry_type != "GeomCompositeCurve":
        raise ValueError(f"Tipo de perfil geometrico no soportado: {geometry_type}")

    is_closed = _points_close_3d(
        normalized_primitives[0].start_point,
        normalized_primitives[-1].end_point,
    )
    has_arcs = any(primitive.primitive_type == "Arc" for primitive in normalized_primitives)
    start_mode = None
    if is_closed:
        first_tangent = _primitive_start_tangent_2d(normalized_primitives[0])
        last_tangent = _primitive_end_tangent_2d(normalized_primitives[-1])
        if first_tangent is not None and last_tangent is not None and _vectors_parallel_same_direction_2d(first_tangent, last_tangent):
            start_mode = "MidEdge"
        else:
            start_mode = "Corner"

    if not is_closed:
        family = "OpenCompositeCurve" if has_arcs else "OpenPolyline"
        winding = None
    else:
        signed_area = _profile_signed_area(normalized_primitives)
        winding = "CounterClockwise" if signed_area >= 0.0 else "Clockwise"
        if has_arcs:
            family = "ClosedPolylineMidEdgeStartRounded" if start_mode == "MidEdge" else "ClosedPolylineRounded"
        else:
            family = "ClosedPolylineMidEdgeStart" if start_mode == "MidEdge" else "ClosedPolylineCornerStart"

    return GeometryProfileSpec(
        geometry_type="GeomCompositeCurve",
        family=family,
        primitives=normalized_primitives,
        is_closed=is_closed,
        winding=winding,
        start_mode=start_mode,
        has_arcs=has_arcs,
        corner_radii=tuple(
            sorted(
                {
                    round(float(primitive.radius), 6)
                    for primitive in normalized_primitives
                    if primitive.radius is not None and primitive.primitive_type == "Arc"
                }
            )
        ),
        bounding_box=_profile_bounding_box(normalized_primitives),
        member_serializations=normalized_member_serializations
        or tuple(_primitive_to_serialization(primitive) for primitive in normalized_primitives),
    )


def _trimmed_curve_spec(serialization: str) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomTrimmedCurve",
        serialization=_normalize_curve_serialization_text(serialization),
    )


def _circle_curve_spec(serialization: str) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomCircle",
        serialization=_normalize_curve_serialization_text(serialization),
    )


def _composite_curve_spec(
    member_serializations: Sequence[str],
    member_keys: Sequence[str] = (),
) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomCompositeCurve",
        member_keys=tuple(member_keys),
        member_serializations=tuple(_normalize_curve_serialization_text(serialization) for serialization in member_serializations),
    )


def _curve_spec_from_profile_geometry(profile: GeometryProfileSpec) -> _CurveSpec:
    if profile.geometry_type == "GeomCartesianPoint":
        raise ValueError("El perfil Point no puede convertirse en una curva/toolpath.")
    if profile.geometry_type == "GeomTrimmedCurve":
        if profile.serialization is None:
            raise ValueError("El perfil lineal/arco necesita serialization para convertirse en curva.")
        return _trimmed_curve_spec(profile.serialization)
    if profile.geometry_type == "GeomCircle":
        if profile.serialization is None:
            raise ValueError("El perfil circular necesita serialization para convertirse en curva.")
        return _circle_curve_spec(profile.serialization)
    if profile.geometry_type == "GeomCompositeCurve":
        return _composite_curve_spec(profile.member_serializations)
    raise ValueError(f"Tipo de perfil geometrico no soportado: {profile.geometry_type}")


def _parse_trimmed_curve_line(text: str) -> Optional[GeometryPrimitiveSpec]:
    lines = [line.strip().split() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    header = lines[0]
    body = lines[1]
    if len(header) < 3 or len(body) < 7 or header[0] != "8" or body[0] != "1":
        return None
    try:
        parameter_start = float(header[1])
        parameter_end = float(header[2])
        origin_x = float(body[1])
        origin_y = float(body[2])
        origin_z = float(body[3])
        direction_x = float(body[4])
        direction_y = float(body[5])
        direction_z = float(body[6])
    except ValueError:
        return None

    # Maestro puede trimar la misma recta con parametros crecientes o decrecientes.
    # Para leer horario/antihorario sin perder informacion hay que evaluar ambos
    # puntos sobre la recta base, en vez de asumir `8 0 longitud`.
    start_point = (
        origin_x + (direction_x * parameter_start),
        origin_y + (direction_y * parameter_start),
        origin_z + (direction_z * parameter_start),
    )
    end_point = (
        origin_x + (direction_x * parameter_end),
        origin_y + (direction_y * parameter_end),
        origin_z + (direction_z * parameter_end),
    )
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=start_point,
        end_point=end_point,
        parameter_start=parameter_start,
        parameter_end=parameter_end,
    )


def _parse_trimmed_curve_arc(text: str) -> Optional[GeometryPrimitiveSpec]:
    lines = [line.strip().split() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    header = lines[0]
    body = lines[1]
    if len(header) < 3 or len(body) < 14 or header[0] != "8" or body[0] != "2":
        return None
    try:
        parameter_start = float(header[1])
        parameter_end = float(header[2])
        center_x = float(body[1])
        center_y = float(body[2])
        center_z = float(body[3])
        normal_vector = (float(body[4]), float(body[5]), float(body[6]))
        u_vector = (float(body[7]), float(body[8]), float(body[9]))
        v_vector = (float(body[10]), float(body[11]), float(body[12]))
        radius = float(body[13])
    except ValueError:
        return None
    center_point = (center_x, center_y, center_z)
    start_point = _sample_arc_point(center_point, u_vector, v_vector, radius, parameter_start)
    end_point = _sample_arc_point(center_point, u_vector, v_vector, radius, parameter_end)
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=parameter_start,
        parameter_end=parameter_end,
        center_point=center_point,
        radius=radius,
        normal_vector=normal_vector,
        u_vector=u_vector,
        v_vector=v_vector,
    )


def _parse_geometry_primitive(text: str) -> Optional[GeometryPrimitiveSpec]:
    return _parse_trimmed_curve_line(text) or _parse_trimmed_curve_arc(text)


def _parse_circle_geometry_profile(text: str) -> Optional[GeometryProfileSpec]:
    parts = (text or "").strip().split()
    if len(parts) < 14 or parts[0] != "2":
        return None
    try:
        center_x = float(parts[1])
        center_y = float(parts[2])
        center_z = float(parts[3])
        normal_z = float(parts[6])
        radius = float(parts[13])
    except ValueError:
        return None
    winding = "CounterClockwise" if normal_z >= 0.0 else "Clockwise"
    return replace(
        build_circle_geometry_profile(
            center_x,
            center_y,
            radius,
            z_value=center_z,
            winding=winding,
        ),
        serialization=_normalize_curve_serialization_text(text),
    )


def _parse_cartesian_point_geometry_profile(node: ET.Element) -> Optional[GeometryProfileSpec]:
    point_x_text = _text(node, "./{*}_x")
    point_y_text = _text(node, "./{*}_y")
    point_z_text = _text(node, "./{*}_z", "0")
    if not point_x_text or not point_y_text:
        return None
    try:
        point_x = float(point_x_text)
        point_y = float(point_y_text)
        point_z = float(point_z_text)
    except ValueError:
        return None
    return build_point_geometry_profile(point_x, point_y, z_value=point_z)


def _extract_geometry_profile(node: ET.Element) -> Optional[GeometryProfileSpec]:
    geometry_type = _xsi_type(node)
    if "GeomCartesianPoint" in geometry_type:
        return _parse_cartesian_point_geometry_profile(node)
    if "GeomCircle" in geometry_type:
        return _parse_circle_geometry_profile(_raw_text(node, "./{*}_serializationGeometryDescription"))
    if "GeomTrimmedCurve" in geometry_type:
        serialization = _raw_text(node, "./{*}_serializationGeometryDescription")
        primitive = _parse_geometry_primitive(serialization)
        if primitive is None:
            return None
        return _build_profile_geometry_spec(
            geometry_type="GeomTrimmedCurve",
            primitives=(primitive,),
            serialization=serialization,
        )
    if "GeomCompositeCurve" in geometry_type:
        member_serializations = [member.text or "" for member in node.findall("./{*}_serializingMembers/{*}string")]
        primitives = []
        for member_serialization in member_serializations:
            primitive = _parse_geometry_primitive(member_serialization)
            if primitive is None:
                return None
            primitives.append(primitive)
        return _build_profile_geometry_spec(
            geometry_type="GeomCompositeCurve",
            primitives=tuple(primitives),
            member_serializations=member_serializations,
        )
    return None


def read_pgmx_geometries(path: Path) -> tuple[GeometryProfileSpec, ...]:
    """Lee y clasifica las geometrías presentes en la sección `Geometries`.

    Esta API se usa para inventariar familias manuales de Maestro y para dejar
    una base explicita de sintesis futura sin depender del nombre del archivo.
    """

    root, _, _ = _load_pgmx_container(path)
    profiles: list[GeometryProfileSpec] = []
    for geometry in root.findall("./{*}Geometries/{*}GeomGeometry"):
        profile = _extract_geometry_profile(geometry)
        if profile is not None:
            profiles.append(profile)
    return tuple(profiles)
