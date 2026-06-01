from __future__ import annotations

from pgmx.synthesis import core as sp

from .depth import VaciadoDepth
from .geometry import PolylineContour, VaciadoGeometry
from .strategy import VaciadoStrategy


def from_pocket_milling_spec(
    spec: sp.PocketMillingSpec,
) -> tuple[VaciadoGeometry, VaciadoStrategy, VaciadoDepth]:
    strategy_spec = spec.milling_strategy
    if not isinstance(strategy_spec, sp.ContourParallelMillingStrategySpec):
        raise TypeError("Vaciado V2 requires ContourParallelMillingStrategySpec.")
    target_depth = spec.depth_spec.target_depth
    if target_depth is None:
        raise ValueError("Vaciado V2 requires an explicit target depth.")

    geometry = VaciadoGeometry(
        outer=_contour(spec.contour_points),
        physical_islands=tuple(_contour(points) for points in spec.boss_contours),
        route_seeds=tuple(_contour(points) for points in spec.resolved_boss_route_seed_contours),
    )
    strategy = VaciadoStrategy(
        tool_width=float(spec.tool_width),
        overlap=float(strategy_spec.overlap),
        allowance_side=float(spec.allowance_side),
        rotation_direction=strategy_spec.rotation_direction,
        inside_to_outside=bool(strategy_spec.inside_to_outside),
        stroke_connection_strategy=strategy_spec.stroke_connection_strategy,
        is_helic_strategy=bool(strategy_spec.is_helic_strategy),
    )
    depth = VaciadoDepth(
        target_depth=float(target_depth),
        allow_multiple_passes=bool(strategy_spec.allow_multiple_passes),
        axial_cutting_depth=float(strategy_spec.axial_cutting_depth),
        axial_finish_cutting_depth=float(strategy_spec.axial_finish_cutting_depth),
    )
    return geometry, strategy, depth


def _contour(points: tuple[tuple[float, float], ...]) -> PolylineContour:
    return PolylineContour(tuple((float(x), float(y)) for x, y in points))
