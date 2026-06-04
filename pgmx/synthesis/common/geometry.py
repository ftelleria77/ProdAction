"""Reusable geometry contracts for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = [
    "GeometryPrimitiveSpec",
    "GeometryProfileSpec",
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
