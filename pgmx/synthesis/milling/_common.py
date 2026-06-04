"""Shared helpers for PGMX milling family modules."""

from __future__ import annotations

from ..common.depth import _normalize_milling_depth_spec
from ..common.geometry import (
    _normalize_geometry_winding,
    _normalize_side_of_feature,
)

__all__ = [
    "_normalize_geometry_winding",
    "_normalize_side_of_feature",
    "_feature_bottom_condition_type",
    "_feature_depth_value",
    "_tool_total_milling_depth",
    "_toolpath_cut_z",
]


def _feature_depth_value(state, spec) -> float:
    # En Maestro, un pasante deja `Depth.StartDepth/EndDepth` igual al espesor
    # actual de la pieza y luego agrega expresiones parametricas hacia `DepthName`.
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    if depth_spec.target_depth > state.depth + 1e-9:
        raise ValueError("La profundidad del fresado no pasante no puede superar el espesor de la pieza.")
    return depth_spec.target_depth


def _tool_total_milling_depth(state, spec) -> float:
    """Calcula la profundidad total efectiva que debe alcanzar la herramienta."""

    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth + depth_spec.extra_depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    return depth_spec.target_depth


def _toolpath_cut_z(state, spec) -> float:
    # Regla validada en Maestro:
    # - no pasante: `cut_z = espesor - target_depth`
    # - pasante: `cut_z = -extra_depth`
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return -depth_spec.extra_depth
    return state.depth - _feature_depth_value(state, spec)


def _feature_bottom_condition_type(spec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return "a:ThroughMillingBottom" if depth_spec.is_through else "a:GeneralMillingBottom"
