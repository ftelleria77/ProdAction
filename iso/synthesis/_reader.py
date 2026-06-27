"""Lee un .pgmx y extrae la geometría y operaciones en el orden de Maestro.

Maestro reordena siempre: Router → Top drill → Side drill.
Dentro de Side drill: prioridad Front > Left > Right > Back (empírico N001).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis.drilling.pattern import DrillingPatternSpec
from pgmx.synthesis.drilling.single import DrillingSpec
from pgmx.synthesis.milling.line import LineMillingSpec

from ._machine import FACE_PRIORITY, SIDE_MAX_DEPTH, resolve_top_tool
from ._validation import UnsupportedOperationError, validate_entries

Op = Union[DrillingSpec, LineMillingSpec]


def side_effective_depth(drill: DrillingSpec, ctx: "PieceCtx") -> float:
    """Profundidad real de un taladro lateral. Pasante: la dimensión cruzada del panel
    (Left/Right atraviesan el largo; Front/Back, el ancho). Ciego: target_depth."""
    if drill.depth_spec.is_through:
        return ctx.length if drill.plane_name in ("Left", "Right") else ctx.width
    return drill.depth_spec.target_depth or 0.0


def top_effective_depth(drill: DrillingSpec, ctx: "PieceCtx") -> float:
    """Profundidad real de un taladro vertical. Pasante: el espesor del panel (atraviesa de
    la cara superior a la mesa). Ciego: target_depth."""
    if drill.depth_spec.is_through:
        return ctx.depth
    return drill.depth_spec.target_depth or 0.0


def expand_drilling_pattern(pattern: DrillingPatternSpec) -> list[DrillingSpec]:
    """Expande un patrón rectangular a taladros individuales (idénticos al base).

    Geometría (N008): center = esquina mínima (primer agujero); columnas en +X por
    `spacing`, filas en +Y por `row_spacing`. Orden = row-major (fila Y exterior
    ascendente, columna X interior ascendente).
    """
    row_spacing = pattern.spacing if pattern.row_spacing is None else pattern.row_spacing
    holes: list[DrillingSpec] = []
    for r in range(int(pattern.rows)):
        for c in range(int(pattern.columns)):
            holes.append(DrillingSpec(
                center_x=pattern.center_x + c * pattern.spacing,
                center_y=pattern.center_y + r * row_spacing,
                diameter=pattern.diameter,
                feature_name=pattern.feature_name,
                plane_name=pattern.plane_name,
                security_plane=pattern.security_plane,
                depth_spec=pattern.depth_spec,
                drill_family=pattern.drill_family,
                tool_resolution=pattern.tool_resolution,
                tool_id=pattern.tool_id,
                tool_name=pattern.tool_name,
            ))
    return holes


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

    # Fail-loud: aborta si hay alguna operación/parámetro fuera del subconjunto soportado,
    # en lugar de ignorarla en silencio o crashear más adelante.
    validate_entries(result.adapted_entries)

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
        if isinstance(spec, DrillingPatternSpec):
            drills = expand_drilling_pattern(spec)
        elif isinstance(spec, DrillingSpec):
            drills = [spec]
        elif isinstance(spec, LineMillingSpec):
            routers.append(spec)
            continue
        else:
            continue
        for drill in drills:
            if drill.plane_name == "Top":
                top_drills.append(drill)
            else:
                side_drills.append(drill)

    # Fail-loud por hundimiento: la profundidad efectiva (ciego o pasante) no puede superar el
    # hundimiento máximo de la herramienta (def.tlgx SinkingLength). Es lo que valida el propio
    # sintetizador pgmx al autorar; el converter lo repite defensivamente (pgmx hand-editado).
    for drill in top_drills:
        eff = top_effective_depth(drill, ctx)
        tool = resolve_top_tool(drill.diameter, drill.drill_family, drill.tool_name)
        if eff > tool.max_sink:
            kind = "pasante (espesor)" if drill.depth_spec.is_through else "ciego"
            raise UnsupportedOperationError(
                f"Taladro vertical {kind} Ø{drill.diameter:g}: profundidad efectiva {eff:g} mm "
                f"supera el hundimiento máximo de la broca ({tool.max_sink:g} mm, "
                f"def.tlgx SinkingLength). [A1]")
    for drill in side_drills:
        eff = side_effective_depth(drill, ctx)
        if eff > SIDE_MAX_DEPTH:
            kind = "pasante" if drill.depth_spec.is_through else "ciego"
            raise UnsupportedOperationError(
                f"Taladro lateral {kind} en cara {drill.plane_name!r}: profundidad efectiva "
                f"{eff:g} mm supera el hundimiento máximo de la broca lateral "
                f"({SIDE_MAX_DEPTH:g} mm, def.tlgx SinkingLength). [A2]")

    # Sort side drills by face priority then by original order within face
    side_drills.sort(key=lambda s: FACE_PRIORITY.get(s.plane_name, 99))

    return ctx, ProgramOps(
        routers=tuple(routers),
        top_drills=tuple(top_drills),
        side_drills=tuple(side_drills),
    )
