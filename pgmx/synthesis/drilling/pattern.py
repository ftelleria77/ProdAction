"""Drilling pattern contracts for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from ..common.depth import MillingDepthSpec, build_milling_depth_spec
from ..common.piece import _normalize_plane_name
from ..common.tools import _normalize_tool_resolution
from .single import DrillingSpec, _default_drill_family, _normalize_drilling_spec

__all__ = [
    "DrillingPatternSpec",
    "build_drilling_pattern_spec",
    "_normalize_drilling_pattern_spec",
]


@dataclass(frozen=True)
class DrillingPatternSpec:
    """Repeticion rectangular de taladros iguales usando `ReplicateFeature`."""

    center_x: float
    center_y: float
    diameter: float
    columns: int
    rows: int
    spacing: float
    row_spacing: Optional[float] = None
    feature_name: str = "Taladrado"
    plane_name: str = "Top"
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    drill_family: str = "Flat"
    tool_resolution: str = "Auto"
    tool_id: str = "0"
    tool_name: str = ""


def _normalize_drilling_pattern_spec(pattern: DrillingPatternSpec) -> DrillingPatternSpec:
    base_drilling = _normalize_drilling_spec(
        DrillingSpec(
            center_x=pattern.center_x,
            center_y=pattern.center_y,
            diameter=pattern.diameter,
            feature_name=pattern.feature_name,
            plane_name=pattern.plane_name,
            security_plane=pattern.security_plane,
            depth_spec=pattern.depth_spec,
            drill_family=pattern.drill_family,
            tool_resolution=pattern.tool_resolution,
            tool_id=pattern.tool_id,
            tool_name=pattern.tool_name,
        )
    )
    columns = int(pattern.columns)
    rows = int(pattern.rows)
    if columns < 1 or rows < 1:
        raise ValueError("`DrillingPatternSpec` requiere `columns` y `rows` mayores o iguales a 1.")
    if columns * rows < 2:
        raise ValueError("Para un unico taladro use `DrillingSpec`; el patron requiere al menos 2 huecos.")

    spacing = float(pattern.spacing)
    row_spacing = spacing if pattern.row_spacing is None else float(pattern.row_spacing)
    if spacing < 0.0 or row_spacing < 0.0:
        raise ValueError("Las separaciones de `DrillingPatternSpec` no pueden ser negativas.")
    if columns > 1 and spacing <= 0.0:
        raise ValueError("Un patron con mas de una columna requiere `spacing` mayor que cero.")
    if rows > 1 and row_spacing <= 0.0:
        raise ValueError("Un patron con mas de una fila requiere `row_spacing` mayor que cero.")

    return replace(
        pattern,
        center_x=base_drilling.center_x,
        center_y=base_drilling.center_y,
        diameter=base_drilling.diameter,
        columns=columns,
        rows=rows,
        spacing=spacing,
        row_spacing=row_spacing,
        feature_name=base_drilling.feature_name,
        plane_name=base_drilling.plane_name,
        security_plane=base_drilling.security_plane,
        depth_spec=base_drilling.depth_spec,
        drill_family=base_drilling.drill_family,
        tool_resolution=base_drilling.tool_resolution,
        tool_id=base_drilling.tool_id,
        tool_name=base_drilling.tool_name,
    )


def build_drilling_pattern_spec(
    center_x: float,
    center_y: float,
    diameter: float,
    columns: int,
    rows: int,
    spacing: float,
    feature_name: Optional[str] = None,
    *,
    row_spacing: Optional[float] = None,
    plane_name: str = "Top",
    security_plane: Optional[float] = None,
    is_through: bool = True,
    target_depth: Optional[float] = None,
    extra_depth: float = 0.0,
    drill_family: Optional[str] = None,
    tool_resolution: str = "Auto",
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> DrillingPatternSpec:
    """Construye una repeticion rectangular Maestro (`ReplicateFeature`)."""

    normalized_plane_name = _normalize_plane_name(plane_name)
    depth_spec = build_milling_depth_spec(
        is_through=is_through,
        target_depth=target_depth,
        extra_depth=extra_depth,
    )
    effective_drill_family = _default_drill_family(
        normalized_plane_name,
        float(diameter),
        depth_spec,
        drill_family,
    )
    return _normalize_drilling_pattern_spec(
        DrillingPatternSpec(
            center_x=float(center_x),
            center_y=float(center_y),
            diameter=float(diameter),
            columns=int(columns),
            rows=int(rows),
            spacing=float(spacing),
            row_spacing=row_spacing,
            feature_name=(feature_name or "Taladrado").strip() or "Taladrado",
            plane_name=normalized_plane_name,
            security_plane=20.0 if security_plane is None else float(security_plane),
            depth_spec=depth_spec,
            drill_family=effective_drill_family,
            tool_resolution=_normalize_tool_resolution(tool_resolution or "Auto"),
            tool_id=(tool_id or "0").strip() or "0",
            tool_name=(tool_name or "").strip(),
        )
    )
