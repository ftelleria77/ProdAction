"""Single drilling contracts for PGMX synthesis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Optional

from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.piece import _normalize_plane_name
from ..common.tools import _normalize_tool_resolution

__all__ = [
    "DrillingSpec",
    "build_drilling_spec",
    "_default_drill_family",
    "_normalize_drill_family",
    "_normalize_drilling_spec",
]


@dataclass(frozen=True)
class DrillingSpec:
    """Descripcion reutilizable de un taladro puntual sobre una cara de la pieza."""

    center_x: float
    center_y: float
    diameter: float
    feature_name: str = "Taladrado"
    plane_name: str = "Top"
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    drill_family: str = "Flat"
    tool_resolution: str = "Auto"
    tool_id: str = "0"
    tool_name: str = ""


def _normalize_drill_family(value: Optional[str]) -> str:
    raw = (value or "Flat").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "flat": "Flat",
        "plana": "Flat",
        "plano": "Flat",
        "conical": "Conical",
        "conica": "Conical",
        "conico": "Conical",
        "lanza": "Conical",
        "puntadelanza": "Conical",
        "countersunk": "Countersunk",
        "abocinado": "Countersunk",
        "abocinada": "Countersunk",
    }
    if raw not in mapping:
        raise ValueError(
            "DrillFamily invalido. Valores admitidos: Flat/Plana, Conical/Lanza o Countersunk/Abocinado."
        )
    return mapping[raw]


def _default_drill_family(
    plane_name: str,
    diameter: float,
    depth_spec: MillingDepthSpec,
    requested_family: Optional[str],
) -> str:
    if requested_family is not None:
        return _normalize_drill_family(requested_family)
    if depth_spec.is_through and plane_name == "Top" and math.isclose(float(diameter), 5.0, abs_tol=1e-9):
        return "Conical"
    return "Flat"


def _normalize_drilling_spec(drilling: DrillingSpec) -> DrillingSpec:
    normalized_plane_name = _normalize_plane_name(drilling.plane_name)
    normalized_depth_spec = _normalize_milling_depth_spec(drilling.depth_spec)
    normalized_drill_family = _normalize_drill_family(drilling.drill_family)
    if normalized_drill_family == "Countersunk":
        raise ValueError(
            "La familia `Countersunk/Abocinado` todavia no tiene un caso manual validado en Maestro."
        )
    if normalized_drill_family == "Conical":
        if normalized_plane_name != "Top":
            raise ValueError("La broca conica solo esta validada por ahora sobre la cara `Top`.")
        if not math.isclose(float(drilling.diameter), 5.0, abs_tol=1e-9):
            raise ValueError("La broca conica relevada hasta ahora solo existe en `D5`.")
    diameter_value = float(drilling.diameter)
    if diameter_value <= 0.0:
        raise ValueError("El diametro del taladro debe ser mayor que cero.")
    security_plane_value = float(drilling.security_plane)
    if security_plane_value < 0.0:
        raise ValueError("SecurityPlane no puede ser negativo.")
    return replace(
        drilling,
        center_x=float(drilling.center_x),
        center_y=float(drilling.center_y),
        diameter=diameter_value,
        feature_name=(drilling.feature_name or "Taladrado").strip() or "Taladrado",
        plane_name=normalized_plane_name,
        security_plane=security_plane_value,
        depth_spec=normalized_depth_spec,
        drill_family=normalized_drill_family,
        tool_resolution=_normalize_tool_resolution(drilling.tool_resolution),
        tool_id=(drilling.tool_id or "").strip() or "0",
        tool_name=(drilling.tool_name or "").strip(),
    )


def build_drilling_spec(
    *,
    center_x: float,
    center_y: float,
    diameter: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    security_plane: Optional[float] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    drill_family: Optional[str] = None,
    tool_resolution: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> DrillingSpec:
    """Construye un `DrillingSpec` reusable para taladros puntuales."""

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
    return DrillingSpec(
        center_x=float(center_x),
        center_y=float(center_y),
        diameter=float(diameter),
        feature_name=(feature_name or "Taladrado").strip() or "Taladrado",
        plane_name=normalized_plane_name,
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        drill_family=effective_drill_family,
        tool_resolution=_normalize_tool_resolution(tool_resolution or "Auto"),
        tool_id=(tool_id or "0").strip() or "0",
        tool_name=(tool_name or "").strip(),
    )
