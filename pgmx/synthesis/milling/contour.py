"""Squaring milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ..common.geometry import (
    GeometryPrimitiveSpec,
    GeometryProfileSpec,
    _CurveSpec,
    _build_parameterized_line_geometry_primitive,
    _curve_spec_from_profile_geometry,
    build_compensated_toolpath_profile,
    build_composite_geometry_profile,
    build_line_geometry_primitive,
)
from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    _normalize_approach_spec,
    _normalize_retract_spec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.strategy import (
    BidirectionalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _build_closed_profile_strategy_toolpath,
    _normalize_milling_strategy_spec,
)
from ._common import _normalize_geometry_winding, _toolpath_cut_z
from ._curve_profile import _append_curve_profile_milling

if TYPE_CHECKING:
    from ..common.program import PgmxState

__all__ = [
    "ContourSpec",
    "build_contour_spec",
    "_HydratedContourSpec",
    "_append_contour",
    "_hydrate_contour_spec",
    "_normalize_contour_spec",
    "_normalize_squaring_start_edge",
    "_with_line_direction_hint",
    "_reparameterize_squaring_toolpath_profile",
    "_reparameterize_line_primitive_from_end",
    "_build_squaring_outline_points",
    "_build_squaring_geometry_profile",
    "_build_squaring_toolpath_profile",
]


@dataclass(frozen=True)
class ContourSpec:
    """Escuadrado exterior del contorno de la pieza sobre el plano `Top`."""

    start_edge: str = "Bottom"
    winding: str = "CounterClockwise"
    start_coordinate: Optional[float] = None
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    tool_id: str = "1900"
    tool_name: str = "E001"
    tool_width: float = 18.36
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=lambda: MillingDepthSpec(is_through=True, extra_depth=1.0))
    approach: ApproachSpec = field(
        default_factory=lambda: ApproachSpec(
            is_enabled=True,
            approach_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
        )
    )
    retract: RetractSpec = field(
        default_factory=lambda: RetractSpec(
            is_enabled=True,
            retract_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
            overlap=0.0,
        )
    )
    milling_strategy: Optional[MillingStrategySpec] = None
    is_enabled_expr: Optional[str] = None

    @property
    def side_of_feature(self) -> str:
        normalized_winding = _normalize_geometry_winding(self.winding)
        return "Right" if normalized_winding == "CounterClockwise" else "Left"


@dataclass(frozen=True)
class _HydratedContourSpec:
    """Datos internos de serializacion para un `ContourSpec`."""

    spec: ContourSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def start_edge(self) -> str:
        return self.spec.start_edge

    @property
    def winding(self) -> str:
        return self.spec.winding

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


def _build_squaring_outline_points(
    length: float,
    width: float,
    *,
    start_edge: str,
    winding: str,
) -> tuple[tuple[float, float], ...]:
    length_value = float(length)
    width_value = float(width)
    if length_value <= 1e-9 or width_value <= 1e-9:
        raise ValueError("El escuadrado necesita una pieza con largo y ancho mayores que cero.")

    bottom_left = (0.0, 0.0)
    bottom_right = (length_value, 0.0)
    top_right = (length_value, width_value)
    top_left = (0.0, width_value)
    mid_bottom = (length_value / 2.0, 0.0)
    mid_right = (length_value, width_value / 2.0)
    mid_top = (length_value / 2.0, width_value)
    mid_left = (0.0, width_value / 2.0)

    normalized_start_edge = _normalize_squaring_start_edge(start_edge)
    normalized_winding = _normalize_geometry_winding(winding)
    if normalized_winding == "CounterClockwise":
        mapping = {
            "Bottom": (mid_bottom, bottom_right, top_right, top_left, bottom_left, mid_bottom),
            "Right": (mid_right, top_right, top_left, bottom_left, bottom_right, mid_right),
            "Top": (mid_top, top_left, bottom_left, bottom_right, top_right, mid_top),
            "Left": (mid_left, bottom_left, bottom_right, top_right, top_left, mid_left),
        }
    else:
        mapping = {
            "Bottom": (mid_bottom, bottom_left, top_left, top_right, bottom_right, mid_bottom),
            "Right": (mid_right, bottom_right, bottom_left, top_left, top_right, mid_right),
            "Top": (mid_top, top_right, bottom_right, bottom_left, top_left, mid_top),
            "Left": (mid_left, top_left, top_right, bottom_right, bottom_left, mid_left),
        }
    return mapping[normalized_start_edge]


def _build_squaring_geometry_profile(
    state: PgmxState,
    spec: _HydratedContourSpec,
    *,
    z_value: float = 0.0,
) -> GeometryProfileSpec:
    points = _build_squaring_outline_points(
        state.length,
        state.width,
        start_edge=spec.start_edge,
        winding=spec.winding,
    )
    length_value = float(state.length)
    width_value = float(state.width)
    target_z = float(z_value)
    edge_length = length_value if spec.start_edge in {"Bottom", "Top"} else width_value

    parameterized_edge_map: dict[tuple[str, str], tuple[tuple[float, float, float], tuple[float, float, float]]] = {
        ("CounterClockwise", "Bottom"): ((0.0, 0.0, target_z), (1.0, 0.0, 0.0)),
        ("CounterClockwise", "Right"): ((length_value, 0.0, target_z), (0.0, 1.0, 0.0)),
        ("CounterClockwise", "Top"): ((length_value, width_value, target_z), (-1.0, 0.0, 0.0)),
        ("CounterClockwise", "Left"): ((0.0, width_value, target_z), (0.0, -1.0, 0.0)),
        ("Clockwise", "Bottom"): ((length_value, 0.0, target_z), (-1.0, 0.0, 0.0)),
        ("Clockwise", "Right"): ((length_value, width_value, target_z), (0.0, -1.0, 0.0)),
        ("Clockwise", "Top"): ((0.0, width_value, target_z), (1.0, 0.0, 0.0)),
        ("Clockwise", "Left"): ((0.0, 0.0, target_z), (0.0, 1.0, 0.0)),
    }
    edge_origin, edge_direction = parameterized_edge_map[(spec.winding, spec.start_edge)]
    midpoint_parameter = edge_length / 2.0

    primitives = [
        _build_parameterized_line_geometry_primitive(
            edge_origin,
            edge_direction,
            midpoint_parameter,
            edge_length,
        ),
        build_line_geometry_primitive(points[1][0], points[1][1], points[2][0], points[2][1], start_z=target_z, end_z=target_z),
        build_line_geometry_primitive(points[2][0], points[2][1], points[3][0], points[3][1], start_z=target_z, end_z=target_z),
        build_line_geometry_primitive(points[3][0], points[3][1], points[4][0], points[4][1], start_z=target_z, end_z=target_z),
        _build_parameterized_line_geometry_primitive(
            edge_origin,
            edge_direction,
            0.0,
            midpoint_parameter,
        ),
    ]
    return build_composite_geometry_profile(tuple(primitives))

def _reparameterize_line_primitive_from_end(primitive: GeometryPrimitiveSpec) -> GeometryPrimitiveSpec:
    """Reexpresa una linea con origen en su punto final y rango `[-length, 0]`.

    Maestro tiende a reserializar asi los dos tramos partidos del borde inicial
    en `TrajectoryPath` de escuadrados. La geometria efectiva no cambia; solo
    cambia la parametrizacion textual de la recta.
    """

    if primitive.primitive_type != "Line":
        return primitive
    length = math.dist(primitive.start_point, primitive.end_point)
    if length <= 1e-9:
        return primitive
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=primitive.start_point,
        end_point=primitive.end_point,
        parameter_start=-length,
        parameter_end=-0.0,
        direction_hint=primitive.direction_hint,
    )


def _with_line_direction_hint(
    primitive: GeometryPrimitiveSpec,
    *,
    z_negative_zero: bool = False,
) -> GeometryPrimitiveSpec:
    """Anota signos preferidos para componentes nulas de direccion en lineas."""

    if primitive.primitive_type != "Line":
        return primitive
    dx = primitive.end_point[0] - primitive.start_point[0]
    dy = primitive.end_point[1] - primitive.start_point[1]
    dz = primitive.end_point[2] - primitive.start_point[2]
    length = math.dist(primitive.start_point, primitive.end_point)
    if length <= 1e-9:
        return primitive
    direction_z = -0.0 if z_negative_zero and math.isclose(dz, 0.0, abs_tol=1e-12) else (dz / length)
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=primitive.start_point,
        end_point=primitive.end_point,
        parameter_start=primitive.parameter_start,
        parameter_end=primitive.parameter_end,
        direction_hint=(dx / length, dy / length, direction_z),
    )


def _reparameterize_squaring_toolpath_profile(profile: GeometryProfileSpec) -> GeometryProfileSpec:
    """Alinea parametrizacion y signos de direccion del escuadrado con Maestro."""

    if profile.geometry_type != "GeomCompositeCurve" or len(profile.primitives) < 2:
        return profile
    primitives = list(profile.primitives)
    bbox = profile.bounding_box
    min_y = bbox[1] if bbox is not None else None
    max_vertical_length = max(
        (
            math.dist(primitive.start_point, primitive.end_point)
            for primitive in primitives
            if primitive.primitive_type == "Line"
            and math.isclose(primitive.start_point[0], primitive.end_point[0], abs_tol=1e-6)
        ),
        default=0.0,
    )
    if primitives[0].primitive_type == "Line":
        primitives[0] = _reparameterize_line_primitive_from_end(primitives[0])
        if min_y is not None and math.isclose(primitives[0].start_point[1], min_y, abs_tol=1e-6):
            primitives[0] = _with_line_direction_hint(primitives[0], z_negative_zero=True)
    if primitives[-1].primitive_type == "Line":
        primitives[-1] = _reparameterize_line_primitive_from_end(primitives[-1])
        if min_y is not None and math.isclose(primitives[-1].start_point[1], min_y, abs_tol=1e-6):
            primitives[-1] = _with_line_direction_hint(primitives[-1], z_negative_zero=True)
    if max_vertical_length > 0.0:
        for index, primitive in enumerate(primitives):
            if primitive.primitive_type != "Line":
                continue
            dx = primitive.end_point[0] - primitive.start_point[0]
            dy = primitive.end_point[1] - primitive.start_point[1]
            length = math.dist(primitive.start_point, primitive.end_point)
            if (
                math.isclose(dx, 0.0, abs_tol=1e-6)
                and dy < 0.0
                and math.isclose(length, max_vertical_length, abs_tol=1e-6)
            ):
                primitives[index] = _with_line_direction_hint(primitive, z_negative_zero=True)
    return build_composite_geometry_profile(tuple(primitives))


def _build_squaring_toolpath_profile(
    state: "PgmxState",
    final_level: float,
    spec: ContourSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para un escuadrado exterior."""

    cut_z = float(final_level)
    nominal_profile = _build_squaring_geometry_profile(state, spec, z_value=cut_z)
    toolpath_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    toolpath_profile = _reparameterize_squaring_toolpath_profile(toolpath_profile)
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return toolpath_profile
    return _build_closed_profile_strategy_toolpath(float(state.depth), cut_z, toolpath_profile, strategy)


def _append_contour(root: ET.Element, state, spec: _HydratedContourSpec) -> None:
    generated_geometry_profile = _build_squaring_geometry_profile(state, spec, z_value=0.0)
    generated_toolpath_profile = _build_squaring_toolpath_profile(state, _toolpath_cut_z(state, spec), spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        spec.geometry_curve or _curve_spec_from_profile_geometry(generated_geometry_profile),
        generated_toolpath_profile,
    )


def _hydrate_contour_spec(
    squaring_milling: ContourSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedContourSpec:
    del source_pgmx_path
    return _HydratedContourSpec(spec=_normalize_contour_spec(squaring_milling))


def _normalize_squaring_start_edge(value: Optional[str]) -> str:
    raw = (value or "Bottom").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "bottom": "Bottom",
        "inferior": "Bottom",
        "bordeinferior": "Bottom",
        "right": "Right",
        "derecho": "Right",
        "bordederecho": "Right",
        "top": "Top",
        "superior": "Top",
        "bordesuperior": "Top",
        "left": "Left",
        "izquierdo": "Left",
        "bordeizquierdo": "Left",
    }
    if raw not in mapping:
        raise ValueError("StartEdge invalido. Valores admitidos: Bottom/Inferior, Right/Derecho, Top/Superior o Left/Izquierdo.")
    return mapping[raw]


def _normalize_contour_spec(squaring_milling: ContourSpec) -> ContourSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(squaring_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="ContourSpec",
    )
    return replace(
        squaring_milling,
        start_edge=_normalize_squaring_start_edge(squaring_milling.start_edge),
        winding=_normalize_geometry_winding(squaring_milling.winding),
        depth_spec=_normalize_milling_depth_spec(squaring_milling.depth_spec),
        approach=_normalize_approach_spec(squaring_milling.approach),
        retract=_normalize_retract_spec(squaring_milling.retract),
        milling_strategy=normalized_strategy,
    )


def build_contour_spec(
    *,
    start_edge: Optional[str] = None,
    winding: Optional[str] = None,
    start_coordinate: Optional[float] = None,
    feature_name: Optional[str] = None,
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
    milling_strategy: Optional[MillingStrategySpec] = None,
    is_enabled_expr: Optional[str] = None,
) -> ContourSpec:
    """Construye un `ContourSpec` reusable para escuadrar la pieza."""

    has_explicit_depth = any(value is not None for value in (is_through, target_depth, extra_depth))
    depth_spec = (
        build_milling_depth_spec(is_through=True, extra_depth=1.0)
        if not has_explicit_depth
        else build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        )
    )

    has_explicit_approach = any(
        value is not None
        for value in (
            approach_enabled,
            approach_type,
            approach_mode,
            approach_radius_multiplier,
            approach_speed,
            approach_arc_side,
        )
    )
    approach_spec = (
        build_approach_spec(
            enabled=True,
            approach_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
        )
        if not has_explicit_approach
        else build_approach_spec(
            enabled=approach_enabled,
            approach_type=approach_type,
            mode=approach_mode,
            radius_multiplier=approach_radius_multiplier,
            speed=approach_speed,
            arc_side=approach_arc_side,
        )
    )

    has_explicit_retract = any(
        value is not None
        for value in (
            retract_enabled,
            retract_type,
            retract_mode,
            retract_radius_multiplier,
            retract_speed,
            retract_arc_side,
            retract_overlap,
        )
    )
    retract_spec = (
        build_retract_spec(
            enabled=True,
            retract_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
            overlap=0.0,
        )
        if not has_explicit_retract
        else build_retract_spec(
            enabled=retract_enabled,
            retract_type=retract_type,
            mode=retract_mode,
            radius_multiplier=retract_radius_multiplier,
            speed=retract_speed,
            arc_side=retract_arc_side,
            overlap=retract_overlap,
        )
    )

    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="ContourSpec",
    )
    return ContourSpec(
        start_edge=_normalize_squaring_start_edge(start_edge),
        winding=_normalize_geometry_winding(winding),
        start_coordinate=None if start_coordinate is None else float(start_coordinate),
        feature_name=(feature_name or "Fresado").strip() or "Fresado",
        tool_id=(tool_id or "1900").strip() or "1900",
        tool_name=(tool_name or "E001").strip() or "E001",
        tool_width=18.36 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        approach=approach_spec,
        retract=retract_spec,
        milling_strategy=normalized_strategy,
        is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
    )
