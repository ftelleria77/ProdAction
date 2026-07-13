"""Fresado de POLILÍNEA de segmentos mixtos (rectas + arcos) — Eje B etapa 3 (2026-07-08).

Generaliza la polilínea recta (`PolylineMillingSpec`) y el arco suelto (`ArcMillingSpec`): un
punto de arranque + una lista de segmentos, cada uno una RECTA (solo endpoint) o un ARCO
(endpoint + centro + winding). La geometría del feature es la `GeomCompositeCurve` de miembros
mixtos observada en las piezas de producción reales (FrenteCurvo/Estante: rectángulo con dos
esquinas redondeadas = 5 rectas + 2 arcos). Reusa la maquinaria compartida de perfiles
(`_append_curve_profile_milling`), como `arc.py`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional, Sequence

from ..common.depth import MillingDepthSpec, _normalize_milling_depth_spec, build_milling_depth_spec
from ..common.geometry import (
    GeometryProfileSpec,
    _CurveSpec,
    _curve_spec_from_profile_geometry,
    _normalize_geometry_winding,
    _normalize_side_of_feature,
    _points_close_2d,
    build_arc_geometry_primitive,
    build_compensated_toolpath_profile,
    build_composite_geometry_profile,
    build_line_geometry_primitive,
)
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    _normalize_approach_spec,
    _normalize_retract_spec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.piece import _normalize_plane_name
from ..common.strategy import (
    BidirectionalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _build_bidirectional_open_profile_strategy_toolpath,
    _build_closed_profile_strategy_toolpath,
    _build_unidirectional_open_profile_strategy_toolpath,
    _ensure_milling_strategy_allowed,
    _normalize_milling_strategy_spec,
)
from ._common import _toolpath_cut_z

__all__ = [
    "PolylineSegment",
    "ArcPolylineMillingSpec",
    "PolylineMillingSpec",
    "build_arc_polyline_milling_spec",
    "build_polyline_milling_spec",
    "_HydratedArcPolylineMillingSpec",
    "_append_arc_polyline_milling",
    "_build_arc_polyline_toolpath_profile",
    "_hydrate_arc_polyline_milling_spec",
    "_normalize_arc_polyline_milling_spec",
]


@dataclass(frozen=True)
class PolylineSegment:
    """Un segmento de la polilínea: RECTA hasta (end_x, end_y), o ARCO si trae centro."""

    end_x: float
    end_y: float
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    winding: Optional[str] = None

    @property
    def is_arc(self) -> bool:
        return self.center_x is not None and self.center_y is not None


@dataclass(frozen=True)
class ArcPolylineMillingSpec:
    """Fresado sobre una polilínea de 2+ segmentos rectos y/o de arco."""

    start_x: float
    start_y: float
    segments: tuple[PolylineSegment, ...]
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

    @property
    def points(self) -> tuple[tuple[float, float], ...]:
        return ((self.start_x, self.start_y),
                *((s.end_x, s.end_y) for s in self.segments))

    @property
    def is_closed(self) -> bool:
        return _points_close_2d((self.start_x, self.start_y),
                                (self.segments[-1].end_x, self.segments[-1].end_y))


@dataclass(frozen=True)
class _HydratedArcPolylineMillingSpec:
    spec: ArcPolylineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "spec"), name)


def _normalize_segment(segment: PolylineSegment) -> PolylineSegment:
    if segment.is_arc:
        return replace(segment,
                       end_x=float(segment.end_x), end_y=float(segment.end_y),
                       center_x=float(segment.center_x), center_y=float(segment.center_y),
                       winding=_normalize_geometry_winding(segment.winding))
    return replace(segment, end_x=float(segment.end_x), end_y=float(segment.end_y),
                   center_x=None, center_y=None, winding=None)


def _normalize_arc_polyline_milling_spec(spec: ArcPolylineMillingSpec) -> ArcPolylineMillingSpec:
    if len(spec.segments) < 2:
        raise ValueError("Una polilínea de perfil necesita al menos 2 segmentos.")
    segments = tuple(_normalize_segment(s) for s in spec.segments)
    # Verificación de radios: cada arco debe tener start y end equidistantes del centro.
    current = (float(spec.start_x), float(spec.start_y))
    for seg in segments:
        if seg.is_arc:
            r0 = math.dist(current, (seg.center_x, seg.center_y))
            r1 = math.dist((seg.end_x, seg.end_y), (seg.center_x, seg.center_y))
            if r0 <= 1e-9 or not math.isclose(r0, r1, abs_tol=1e-6):
                raise ValueError(
                    f"Segmento de arco con radios inconsistentes (r_ini={r0:g}, r_fin={r1:g}).")
        current = (seg.end_x, seg.end_y)
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(spec.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="ArcPolylineMillingSpec",
    )
    normalized = replace(
        spec,
        start_x=float(spec.start_x),
        start_y=float(spec.start_y),
        segments=segments,
        plane_name=_normalize_plane_name(spec.plane_name),
        side_of_feature=_normalize_side_of_feature(spec.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(spec.depth_spec),
        approach=_normalize_approach_spec(spec.approach),
        retract=_normalize_retract_spec(spec.retract),
        milling_strategy=normalized_strategy,
    )
    _validate_postprocessable_by_maestro(normalized)
    return normalized


def _validate_postprocessable_by_maestro(spec: ArcPolylineMillingSpec) -> None:
    """Bloquea una combinación que Maestro NO logra postprocesar a ISO (heredada de la polilínea
    recta): perfil ABIERTO multi-segmento + estrategia multipasada + Alejamiento Arco «En subida».
    Usar Alejamiento Lineal+Up o Arco+En cota."""
    strategy = spec.milling_strategy
    retract = spec.retract
    if (not spec.is_closed
            and len(spec.segments) > 1
            and strategy is not None
            and getattr(strategy, "allow_multiple_passes", False)
            and retract.is_enabled
            and retract.retract_type == "Arc"
            and retract.mode == "Up"):
        raise ValueError(
            "Maestro no postprocesa polilineas abiertas de varios segmentos con "
            "estrategia multipasada PH y Retract Arc + Up. Usar Retract Line + Up "
            "o Arc + Quote para obtener ISO postprocesable."
        )


def _build_arc_polyline_geometry_profile(spec: ArcPolylineMillingSpec, z_value: float) -> GeometryProfileSpec:
    primitives = []
    cx, cy = float(spec.start_x), float(spec.start_y)
    for seg in spec.segments:
        if seg.is_arc:
            primitives.append(build_arc_geometry_primitive(
                cx, cy, seg.end_x, seg.end_y, seg.center_x, seg.center_y,
                z_value=z_value, winding=seg.winding))
        else:
            primitives.append(build_line_geometry_primitive(
                cx, cy, seg.end_x, seg.end_y, start_z=z_value, end_z=z_value))
        cx, cy = seg.end_x, seg.end_y
    return build_composite_geometry_profile(tuple(primitives))


def _build_arc_polyline_toolpath_profile(
    top_level: float,
    final_level: float,
    spec: ArcPolylineMillingSpec,
) -> GeometryProfileSpec:
    cut_z = float(final_level)
    nominal_profile = _build_arc_polyline_geometry_profile(spec, cut_z)
    # Con corrección, la traza compensada de una polilínea con esquinas VIVAS lleva arcos de
    # empalme en los vértices convexos — que Maestro GENERA al postprocesar (regenera desde el
    # feature/SideOfFeature, como en las líneas N031; validado byte a byte en N042 11/11: el ISO
    # sale compensado desde nuestra traza NOMINAL). La autoría no necesita compensar: guardamos
    # la traza nominal como placeholder y Maestro la regenera. (La compensación con inglete en la
    # autoría quedó descartada — Fermín 2026-07-10 — porque Maestro siempre regenera.)
    try:
        base_profile = build_compensated_toolpath_profile(
            nominal_profile,
            side_of_feature=spec.side_of_feature,
            tool_width=spec.tool_width,
            z_value=cut_z,
        )
    except ValueError:
        base_profile = nominal_profile
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if nominal_profile.is_closed:
        return _build_closed_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_open_profile_strategy_toolpath(
            float(top_level), cut_z, spec.security_plane, base_profile, strategy)
    return _build_bidirectional_open_profile_strategy_toolpath(float(top_level), cut_z, base_profile, strategy)


def _hydrate_arc_polyline_milling_spec(
    spec: ArcPolylineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedArcPolylineMillingSpec:
    return _HydratedArcPolylineMillingSpec(spec=_normalize_arc_polyline_milling_spec(spec))


def _append_arc_polyline_milling(root, state, spec: _HydratedArcPolylineMillingSpec) -> None:
    from .profile import _append_curve_profile_milling

    geometry_curve = spec.geometry_curve or _curve_spec_from_profile_geometry(
        _build_arc_polyline_geometry_profile(spec.spec, 0.0))
    generated_toolpath_profile = _build_arc_polyline_toolpath_profile(
        float(state.depth), _toolpath_cut_z(state, spec), spec.spec)
    _append_curve_profile_milling(root, state, spec, geometry_curve, generated_toolpath_profile)


def _segment(end, center=None, winding=None) -> PolylineSegment:
    if center is None:
        return PolylineSegment(end_x=float(end[0]), end_y=float(end[1]))
    return PolylineSegment(end_x=float(end[0]), end_y=float(end[1]),
                           center_x=float(center[0]), center_y=float(center[1]), winding=winding)


def build_arc_polyline_milling_spec(
    *,
    start: Optional[tuple[float, float]] = None,
    segments: Optional[Sequence] = None,
    points: Optional[Sequence[tuple[float, float]]] = None,
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
    is_enabled_expr: Optional[str] = None,
) -> ArcPolylineMillingSpec:
    """Construye una polilínea de perfil.

    ``segments``: cada elemento es un ``PolylineSegment``, o una tupla ``(end)`` para recta,
    o ``(end, center, winding)`` para arco (``end``/``center`` = pares ``(x, y)``).
    """

    # Dos formas de entrada equivalentes (una sola polilínea):
    #   points=[(x,y), ...]            → atajo RECTO (todos los segmentos son rectas)
    #   start=(x,y), segments=[...]    → forma general (rectas y/o arcos)
    if points is not None:
        if start is not None or segments is not None:
            raise ValueError("Usar `points` O (`start` + `segments`), no ambos.")
        pts = tuple((float(px), float(py)) for px, py in points)
        if len(pts) < 3:
            raise ValueError("Una polilínea necesita al menos 3 puntos (2 segmentos).")
        start = pts[0]
        segments = [(pt,) for pt in pts[1:]]
    if start is None or segments is None:
        raise ValueError("Falta la geometría: pasar `points` o (`start` + `segments`).")
    normalized_segments = []
    for seg in segments:
        if isinstance(seg, PolylineSegment):
            normalized_segments.append(seg)
        elif len(seg) == 1:
            normalized_segments.append(_segment(seg[0]))
        else:
            normalized_segments.append(_segment(seg[0], seg[1], seg[2] if len(seg) > 2 else None))
    return _normalize_arc_polyline_milling_spec(
        ArcPolylineMillingSpec(
            start_x=float(start[0]),
            start_y=float(start[1]),
            segments=tuple(normalized_segments),
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
            milling_strategy=milling_strategy,
            is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
        )
    )


# Nombre histórico de la polilínea RECTA: ahora es la MISMA polilínea unificada, con el atajo
# `points=`. Se conserva como alias hasta el rename global (etapa 2).
build_polyline_milling_spec = build_arc_polyline_milling_spec
PolylineMillingSpec = ArcPolylineMillingSpec
