"""Piece geometry helpers for PGMX synthesis."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Protocol

from .xml import _text

__all__ = [
    "PieceGeometry",
    "_drilling_axis_span",
    "_drilling_axis_variable_name",
    "_drilling_entry_point_and_direction",
    "_normalize_plane_name",
    "_plane_local_dimensions",
    "_workpiece_depth_name",
    "_workpiece_length_name",
    "_workpiece_width_name",
]


class _PieceDimensions(Protocol):
    length: float
    width: float
    depth: float


class _FacePointSpec(Protocol):
    plane_name: str
    center_x: float
    center_y: float


@dataclass(frozen=True)
class PieceGeometry:
    """Geometria de pieza independiente del estado de programa Maestro."""

    length: float
    width: float
    depth: float
    origin_x: float = 0.0
    origin_y: float = 0.0
    origin_z: float = 0.0


def _normalize_plane_name(value: Optional[str]) -> str:
    raw = (value or "Top").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "top": "Top",
        "superior": "Top",
        "carasuperior": "Top",
        "front": "Front",
        "frontal": "Front",
        "caradelantera": "Front",
        "delantera": "Front",
        "back": "Back",
        "trasera": "Back",
        "caratrasera": "Back",
        "right": "Right",
        "derecha": "Right",
        "caraderecha": "Right",
        "left": "Left",
        "izquierda": "Left",
        "caraizquierda": "Left",
    }
    if raw not in mapping:
        raise ValueError(
            "PlaneName invalido. Valores admitidos: Top/Superior, Front/Delantera, "
            "Back/Trasera, Right/Derecha o Left/Izquierda."
        )
    return mapping[raw]


def _workpiece_depth_name(workpiece: Optional[ET.Element]) -> str:
    """Devuelve el nombre parametrico de espesor usado por la pieza.

    Maestro suele usar `dz1`, pero conviene leerlo del `WorkPiece` para no
    fijar la sintesis a un unico baseline.
    """

    return _text(workpiece, "./{*}DepthName", "dz1") or "dz1"


def _workpiece_length_name(workpiece: Optional[ET.Element]) -> str:
    return _text(workpiece, "./{*}LengthName", "dx1") or "dx1"


def _workpiece_width_name(workpiece: Optional[ET.Element]) -> str:
    return _text(workpiece, "./{*}WidthName", "dy1") or "dy1"


def _plane_local_dimensions(state: _PieceDimensions, plane_name: str) -> tuple[float, float]:
    normalized_plane_name = _normalize_plane_name(plane_name)
    mapping = {
        "Top": (state.length, state.width),
        "Front": (state.length, state.depth),
        "Back": (state.length, state.depth),
        "Right": (state.width, state.depth),
        "Left": (state.width, state.depth),
    }
    return mapping[normalized_plane_name]


def _drilling_axis_span(state: _PieceDimensions, plane_name: str) -> float:
    normalized_plane_name = _normalize_plane_name(plane_name)
    mapping = {
        "Top": state.depth,
        "Front": state.width,
        "Back": state.width,
        "Right": state.length,
        "Left": state.length,
    }
    return mapping[normalized_plane_name]


def _drilling_axis_variable_name(workpiece: Optional[ET.Element], plane_name: str) -> str:
    normalized_plane_name = _normalize_plane_name(plane_name)
    if normalized_plane_name == "Top":
        return _workpiece_depth_name(workpiece)
    if normalized_plane_name in {"Front", "Back"}:
        return _workpiece_width_name(workpiece)
    return _workpiece_length_name(workpiece)


def _drilling_entry_point_and_direction(
    state: _PieceDimensions,
    spec: _FacePointSpec,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    plane_name = spec.plane_name
    local_x = spec.center_x
    local_y = spec.center_y
    if plane_name == "Top":
        return (local_x, local_y, state.depth), (0.0, 0.0, -1.0)
    if plane_name == "Front":
        return (local_x, 0.0, local_y), (0.0, 1.0, 0.0)
    if plane_name == "Back":
        return (state.length - local_x, state.width, local_y), (0.0, -1.0, 0.0)
    if plane_name == "Right":
        return (state.length, local_x, local_y), (-1.0, 0.0, 0.0)
    if plane_name == "Left":
        return (0.0, state.width - local_x, local_y), (1.0, 0.0, 0.0)
    raise ValueError(f"No hay una transformacion de taladro validada para el plano '{plane_name}'.")
