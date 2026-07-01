"""Lectura del catálogo de herramientas (derivado del def.tlgx) para el converter.

Las longitudes y límites que entran en las fórmulas de traza/recorrido/profundidad NO
deben ser constantes internas del converter: salen del mismo `tool_catalog.csv` que usa el
sintetizador pgmx (que a su vez deriva del `def.tlgx`). Acá se exponen por nombre de
herramienta (= ETK[6] con padding: '001'..'007', '058'..'061', 'E004', ...).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache

from pgmx.synthesis.common.tools import TOOL_CATALOG_PATH


@dataclass(frozen=True)
class ToolGeometry:
    tool_offset_length: float  # mm — referencia de longitud (tlc vertical / cut lateral / router)
    sinking_length: float      # mm — hundimiento máximo (límite de profundidad/espesor)
    feed_max: float            # mm/min — tope de avance (feed_rate_max × 1000)
    spindle_max: int           # rpm — tope de husillo
    spindle_std: int           # rpm — husillo por defecto (spindle_speed_std; fiable, a diferencia
                               # del feed_std, que no lo es para D4/D5/cónica/lateral)


@lru_cache(maxsize=1)
def _catalog_by_name() -> dict[str, dict[str, str]]:
    with TOOL_CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    return {
        (row.get("name") or "").strip(): row
        for row in rows
        if (row.get("name") or "").strip()
    }


def tool_geometry(name: str) -> ToolGeometry:
    """Geometría/límites de una herramienta por nombre (ETK[6] con padding). Del catálogo."""
    row = _catalog_by_name().get(name)
    if row is None:
        raise KeyError(f"herramienta {name!r} no está en {TOOL_CATALOG_PATH.name}")
    return ToolGeometry(
        tool_offset_length=float(row["tool_offset_length"]),
        sinking_length=float(row["sinking_length"]),
        feed_max=float(row["feed_rate_max"]) * 1000.0,
        spindle_max=int(float(row["spindle_speed_max"])),
        spindle_std=int(float(row["spindle_speed_std"])),
    )
