"""Pocket milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

from ..common.depth import MillingDepthSpec, build_milling_depth_spec
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.piece import _normalize_plane_name
from ..common.strategy import (
    ContourParallelMillingStrategySpec,
    build_contour_parallel_milling_strategy_spec,
)

__all__ = [
    "PocketBossRouteSeedSpec",
    "PocketMillingSpec",
    "build_pocket_boss_route_seed_spec",
    "build_pocket_milling_spec",
]


@dataclass(frozen=True)
class PocketBossRouteSeedSpec:
    """Referencia de `BossList.GeometryID` usada por Maestro como semilla de ruta.

    `contour_points` queda vacio cuando el `GeometryID` no se pudo resolver en
    el archivo. La isla fisica sigue viviendo en `PocketMillingSpec.boss_contours`.
    """

    geometry_id: str
    object_type: str = ""
    name: str = ""
    contour_points: tuple[tuple[float, float], ...] = ()

    @property
    def is_resolved(self) -> bool:
        return bool(self.contour_points)


@dataclass(frozen=True)
class PocketMillingSpec:
    """Vaciado superior observado como `ClosedPocket` + `ContourParallel`.

    El subset productivo validado cubre contornos rectangulares lineales sobre
    `Top`, con trayectorias `ContourParallel` equivalentes a Maestro.
    """

    contour_points: tuple[tuple[float, float], ...]
    feature_name: str = "Vaciado"
    plane_name: str = "Top"
    tool_id: str = "1900"
    tool_name: str = "E001"
    tool_width: float = 18.36
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    milling_strategy: ContourParallelMillingStrategySpec = field(
        default_factory=ContourParallelMillingStrategySpec
    )
    allowance_bottom: float = 0.0
    allowance_side: float = 0.0
    boss_contours: tuple[tuple[tuple[float, float], ...], ...] = ()
    boss_route_seeds: tuple[PocketBossRouteSeedSpec, ...] = ()

    @property
    def effective_contour_offset(self) -> float:
        return (float(self.tool_width) / 2.0) + float(self.allowance_side)

    @property
    def radial_step(self) -> float:
        return float(self.tool_width) * (1.0 - float(self.milling_strategy.overlap))

    @property
    def has_bosses(self) -> bool:
        return bool(self.boss_contours)

    @property
    def has_boss_route_seeds(self) -> bool:
        return bool(self.boss_route_seeds)

    @property
    def resolved_boss_route_seed_contours(self) -> tuple[tuple[tuple[float, float], ...], ...]:
        return tuple(seed.contour_points for seed in self.boss_route_seeds if seed.is_resolved)


def _normalize_closed_contour(
    points: Sequence[tuple[float, float]],
    *,
    label: str,
) -> tuple[tuple[float, float], ...]:
    normalized = tuple((float(x), float(y)) for x, y in points)
    if len(normalized) < 4:
        raise ValueError(f"{label} requiere un contorno cerrado con al menos 4 puntos.")
    if not (
        math.isclose(normalized[0][0], normalized[-1][0], abs_tol=1e-6)
        and math.isclose(normalized[0][1], normalized[-1][1], abs_tol=1e-6)
    ):
        raise ValueError(f"{label} requiere que el primer y ultimo punto coincidan.")
    return normalized


def build_pocket_boss_route_seed_spec(
    *,
    geometry_id: str,
    object_type: Optional[str] = None,
    name: Optional[str] = None,
    contour_points: Optional[Sequence[tuple[float, float]]] = None,
) -> PocketBossRouteSeedSpec:
    """Construye una referencia de `BossList.GeometryID` para un `Vaciado`."""

    normalized_geometry_id = str(geometry_id).strip()
    if not normalized_geometry_id:
        raise ValueError("PocketBossRouteSeedSpec requiere geometry_id.")

    normalized_points = (
        _normalize_closed_contour(
            contour_points,
            label="La semilla de ruta de Vaciado",
        )
        if contour_points
        else ()
    )

    return PocketBossRouteSeedSpec(
        geometry_id=normalized_geometry_id,
        object_type=(object_type or "").strip(),
        name=(name or "").strip(),
        contour_points=normalized_points,
    )


def build_pocket_milling_spec(
    *,
    contour_points: Sequence[tuple[float, float]],
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
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
    milling_strategy: Optional[ContourParallelMillingStrategySpec] = None,
    allowance_bottom: Optional[float] = None,
    allowance_side: Optional[float] = None,
    boss_contours: Optional[Sequence[Sequence[tuple[float, float]]]] = None,
    boss_route_seeds: Optional[Sequence[PocketBossRouteSeedSpec]] = None,
) -> PocketMillingSpec:
    """Construye la spec publica de `Vaciado` para lectura/adaptacion."""

    normalized_points = _normalize_closed_contour(
        contour_points,
        label="PocketMillingSpec",
    )
    normalized_boss_contours = [
        _normalize_closed_contour(
            boss_contour,
            label="Cada isla de PocketMillingSpec",
        )
        for boss_contour in boss_contours or ()
    ]
    normalized_boss_route_seeds = tuple(
        build_pocket_boss_route_seed_spec(
            geometry_id=seed.geometry_id,
            object_type=seed.object_type,
            name=seed.name,
            contour_points=seed.contour_points,
        )
        for seed in boss_route_seeds or ()
    )

    normalized_strategy = (
        build_contour_parallel_milling_strategy_spec()
        if milling_strategy is None
        else build_contour_parallel_milling_strategy_spec(
            rotation_direction=milling_strategy.rotation_direction,
            stroke_connection_strategy=milling_strategy.stroke_connection_strategy,
            inside_to_outside=milling_strategy.inside_to_outside,
            overlap=milling_strategy.overlap,
            is_helic_strategy=milling_strategy.is_helic_strategy,
            allow_multiple_passes=milling_strategy.allow_multiple_passes,
            axial_cutting_depth=milling_strategy.axial_cutting_depth,
            axial_finish_cutting_depth=milling_strategy.axial_finish_cutting_depth,
            cutmode=milling_strategy.cutmode,
            is_internal=milling_strategy.is_internal,
            radial_cutting_depth=milling_strategy.radial_cutting_depth,
            radial_finish_cutting_depth=milling_strategy.radial_finish_cutting_depth,
            allows_bidirectional=milling_strategy.allows_bidirectional,
            allows_finish_cutting=milling_strategy.allows_finish_cutting,
        )
    )
    has_explicit_depth = any(value is not None for value in (is_through, target_depth, extra_depth))
    depth_spec = (
        build_milling_depth_spec(is_through=False, target_depth=10.0)
        if not has_explicit_depth
        else build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        )
    )
    return PocketMillingSpec(
        contour_points=normalized_points,
        feature_name=(feature_name or "Vaciado").strip() or "Vaciado",
        plane_name=_normalize_plane_name(plane_name),
        tool_id=(tool_id or "1900").strip() or "1900",
        tool_name=(tool_name or "E001").strip() or "E001",
        tool_width=18.36 if tool_width is None else float(tool_width),
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
        milling_strategy=normalized_strategy,
        allowance_bottom=0.0 if allowance_bottom is None else float(allowance_bottom),
        allowance_side=0.0 if allowance_side is None else float(allowance_side),
        boss_contours=tuple(normalized_boss_contours),
        boss_route_seeds=normalized_boss_route_seeds,
    )
