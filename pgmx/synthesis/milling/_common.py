"""Shared helpers for PGMX milling family modules."""

from __future__ import annotations

from typing import Optional

__all__ = [
    "_normalize_geometry_winding",
    "_normalize_side_of_feature",
]


def _normalize_geometry_winding(value: Optional[str]) -> str:
    raw = (value or "CounterClockwise").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "counterclockwise": "CounterClockwise",
        "ccw": "CounterClockwise",
        "antihorario": "CounterClockwise",
        "clockwise": "Clockwise",
        "cw": "Clockwise",
        "horario": "Clockwise",
    }
    if raw not in mapping:
        raise ValueError("Winding invalido. Valores admitidos: CounterClockwise/Antihorario o Clockwise/Horario.")
    return mapping[raw]


def _normalize_side_of_feature(value: Optional[str]) -> str:
    raw = (value or "Center").strip().lower()
    mapping = {
        "center": "Center",
        "centre": "Center",
        "central": "Center",
        "right": "Right",
        "derecha": "Right",
        "left": "Left",
        "izquierda": "Left",
    }
    if raw not in mapping:
        raise ValueError("SideOfFeature invalido. Valores admitidos: Center, Right, Left.")
    return mapping[raw]
