"""Fresado de ARCO SUELTO para la síntesis PGMX — Eje B etapa 2 (2026-07-08).

Forma derivada de las piezas de producción reales (FrenteCurvo/Módulo Curvo del corpus): la
geometría del feature es una `GeomCompositeCurve` cuyos miembros serializan arcos como
``8 {áng_ini} {áng_fin}\\n2 {cx} {cy} {cz} {n̂} {û} {v̂} {r}`` (ángulos en la base û/v̂ de
Maestro). El arco suelto se autora como composite de UN miembro; el feature es el
`GeneralProfileFeature` estándar y la operación `BottomAndSideFinishMilling` — todo vía la
maquinaria compartida de perfiles (`_append_curve_profile_milling`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from ..common.depth import MillingDepthSpec, _normalize_milling_depth_spec, build_milling_depth_spec
from ..common.geometry import (
    GeometryProfileSpec,
    _CurveSpec,
    _curve_spec_from_profile_geometry,
    _normalize_geometry_winding,
    _normalize_side_of_feature,
    build_arc_geometry_primitive,
    build_compensated_toolpath_profile,
    build_composite_geometry_profile,
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
    _build_unidirectional_open_profile_strategy_toolpath,
    _ensure_milling_strategy_allowed,
    _normalize_milling_strategy_spec,
)
from ._common import _toolpath_cut_z

__all__ = [
    "ArcSpec",
    "build_arc_spec",
    "_HydratedArcSpec",
    "_append_arc",
    "_build_arc_toolpath_profile",
    "_hydrate_arc_spec",
    "_normalize_arc_spec",
]


@dataclass(frozen=True)
class ArcSpec:
    """Fresado sobre un arco suelto (start → end alrededor de center, según winding)."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    center_x: float
    center_y: float
    winding: str = "CounterClockwise"
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


@dataclass(frozen=True)
class _HydratedArcSpec:
    """Datos internos de serialización que complementan un `ArcSpec`."""

    spec: ArcSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "spec"), name)


def _normalize_arc_spec(arc_milling: ArcSpec) -> ArcSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(arc_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="ArcSpec",
    )
    start_r = math.dist((arc_milling.start_x, arc_milling.start_y),
                        (arc_milling.center_x, arc_milling.center_y))
    end_r = math.dist((arc_milling.end_x, arc_milling.end_y),
                      (arc_milling.center_x, arc_milling.center_y))
    if start_r <= 1e-9 or not math.isclose(start_r, end_r, abs_tol=1e-6):
        raise ValueError(
            "El arco requiere start y end EQUIDISTANTES del centro (radio > 0): "
            f"r_inicio={start_r:g}, r_fin={end_r:g}."
        )
    return replace(
        arc_milling,
        winding=_normalize_geometry_winding(arc_milling.winding),
        plane_name=_normalize_plane_name(arc_milling.plane_name),
        side_of_feature=_normalize_side_of_feature(arc_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(arc_milling.depth_spec),
        approach=_normalize_approach_spec(arc_milling.approach),
        retract=_normalize_retract_spec(arc_milling.retract),
        milling_strategy=normalized_strategy,
    )


def _build_arc_geometry_profile(spec: ArcSpec, z_value: float) -> GeometryProfileSpec:
    primitive = build_arc_geometry_primitive(
        spec.start_x, spec.start_y, spec.end_x, spec.end_y,
        spec.center_x, spec.center_y,
        z_value=z_value, winding=spec.winding,
    )
    return build_composite_geometry_profile((primitive,))


def _build_arc_toolpath_profile(
    top_level: float,
    final_level: float,
    spec: ArcSpec,
) -> GeometryProfileSpec:
    """Trayectoria del arco: el perfil compensado a la cota de corte; con estrategia, las
    pasadas de perfil ABIERTO (Uni/Bi) sobre el arco."""

    cut_z = float(final_level)
    nominal_profile = _build_arc_geometry_profile(spec, cut_z)
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_open_profile_strategy_toolpath(
            float(top_level), cut_z, spec.security_plane, base_profile, strategy)
    return _build_bidirectional_open_profile_strategy_toolpath(
        float(top_level), cut_z, base_profile, strategy)


def _hydrate_arc_spec(
    arc_milling: ArcSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedArcSpec:
    # Sin reutilización de plantillas (no hay corpus de arcos sueltos): siempre autoría fresca.
    return _HydratedArcSpec(spec=_normalize_arc_spec(arc_milling))


def _append_arc(root, state, spec: _HydratedArcSpec) -> None:
    from ._curve_profile import _append_curve_profile_milling

    geometry_curve = spec.geometry_curve or _curve_spec_from_profile_geometry(
        _build_arc_geometry_profile(spec.spec, 0.0))
    generated_toolpath_profile = _build_arc_toolpath_profile(
        float(state.depth), _toolpath_cut_z(state, spec), spec.spec)
    _append_curve_profile_milling(root, state, spec, geometry_curve, generated_toolpath_profile)


def build_arc_spec(
    *,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    center_x: float,
    center_y: float,
    winding: Optional[str] = None,
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
) -> ArcSpec:
    """Construye un `ArcSpec` reusable para un fresado de arco suelto."""

    return _normalize_arc_spec(
        ArcSpec(
            start_x=float(start_x),
            start_y=float(start_y),
            end_x=float(end_x),
            end_y=float(end_y),
            center_x=float(center_x),
            center_y=float(center_y),
            winding=_normalize_geometry_winding(winding),
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
