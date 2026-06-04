"""Shared helpers for PGMX milling family modules."""

from __future__ import annotations

from typing import Optional

__all__ = [
    "_normalize_side_of_feature",
]


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
