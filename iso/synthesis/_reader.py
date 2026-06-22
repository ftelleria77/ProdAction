"""Lee un .pgmx y extrae la geometría y operaciones en el orden de Maestro.

Maestro reordena siempre: Router → Top drill → Side drill.
Dentro de Side drill: prioridad Front > Left > Right > Back (empírico N001).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis.drilling.single import DrillingSpec
from pgmx.synthesis.milling.line import LineMillingSpec

from ._machine import FACE_PRIORITY

Op = Union[DrillingSpec, LineMillingSpec]


@dataclass(frozen=True)
class PieceCtx:
    """Geometría de la pieza y parámetros de referencia."""
    piece_name: str
    length: float
    width: float
    depth: float
    origin_x: float
    origin_y: float
    origin_z: float

    @property
    def DX(self) -> float:  # noqa: N802
        return self.length + self.origin_x

    @property
    def DY(self) -> float:  # noqa: N802
        return self.width + self.origin_y

    @property
    def DZ(self) -> float:  # noqa: N802
        return self.origin_z + self.depth


@dataclass(frozen=True)
class ProgramOps:
    routers: tuple[LineMillingSpec, ...]
    top_drills: tuple[DrillingSpec, ...]
    side_drills: tuple[DrillingSpec, ...]


def read_pgmx(path: Path) -> tuple[PieceCtx, ProgramOps]:
    result = adapt_pgmx_path(path)
    state = result.snapshot.state

    ctx = PieceCtx(
        piece_name=state.piece_name,
        length=state.length,
        width=state.width,
        depth=state.depth,
        origin_x=state.origin_x,
        origin_y=state.origin_y,
        origin_z=state.origin_z,
    )

    routers: list[LineMillingSpec] = []
    top_drills: list[DrillingSpec] = []
    side_drills: list[DrillingSpec] = []

    for entry in result.adapted_entries:
        spec = entry.spec
        if isinstance(spec, LineMillingSpec):
            routers.append(spec)
        elif isinstance(spec, DrillingSpec):
            if spec.plane_name == "Top":
                top_drills.append(spec)
            else:
                side_drills.append(spec)

    # Sort side drills by face priority then by original order within face
    side_drills.sort(key=lambda s: FACE_PRIORITY.get(s.plane_name, 99))

    return ctx, ProgramOps(
        routers=tuple(routers),
        top_drills=tuple(top_drills),
        side_drills=tuple(side_drills),
    )
