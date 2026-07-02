"""Lee un .pgmx y extrae la geometría y operaciones en el orden de Maestro.

Maestro reordena siempre: Router → Top drill → Side drill.
Dentro de Side drill: prioridad Front > Left > Right > Back (empírico N001).
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis.drilling.pattern import DrillingPatternSpec
from pgmx.synthesis.drilling.single import DrillingSpec
from pgmx.synthesis.milling.line import LineMillingSpec

from ._machine import (
    FACE_PRIORITY, SIDE_MAX_DEPTH, SIDE_SUPPORTED_FIELDS, SUPPORTED_FIELDS, X_PARK, resolve_top_tool,
)
from ._validation import UnsupportedOperationError, validate_entries

_EXECUTION_FIELD_RE = re.compile(r"<[^>]*ExecutionFields>([^<]*)</")


def _execution_field(path: Path) -> str:
    """Campo de trabajo elegido en Maestro, registrado en el .pgmx como
    <ExecutionFields>HG</ExecutionFields> (dentro de XilogHeaderParameters). El .pgmx es un ZIP
    con un .xml adentro. Determina el origen del campo (field_origin) y el espejado geométrico.
    Default "HG" si no aparece (el único campo calibrado hoy)."""
    with zipfile.ZipFile(path) as z:
        xml_name = next((n for n in z.namelist() if n.endswith(".xml")), None)
        if xml_name is None:
            return "HG"
        xml = z.read(xml_name).decode("utf-8", errors="replace")
    m = _EXECUTION_FIELD_RE.search(xml)
    return m.group(1).strip() if m and m.group(1).strip() else "HG"

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
    # Campo de trabajo elegido en Maestro (de <ExecutionFields> del .pgmx): AB/DC/EF/HG. Determina
    # el origen (field_origin) y el espejado de direcciones del 2×2. Hoy solo HG está validado.
    field: str = "HG"
    # Park del footer (G53, coord. de máquina): X (y opcional Y) salen de la operación nula Xn
    # del .pgmx; sin Xn, el default de Maestro. El Z del park es machine config (Z_PARK). (N015)
    park_x: float = X_PARK
    park_y: float | None = None

    @property
    def DX(self) -> float:  # noqa: N802
        return self.length + self.origin_x

    @property
    def DY(self) -> float:  # noqa: N802
        return self.width + self.origin_y

    @property
    def DZ(self) -> float:  # noqa: N802
        return self.origin_z + self.depth


def _xn_park(snapshot) -> tuple[float, float | None]:
    """(park_x, park_y) del footer a partir del Xn del programa. park_x = Xn.x; park_y = -Xn.y
    (la cama va 0..-1500 en pgmx → 0..+1500 en máquina); sin Xn → default. (N015)"""
    xns = [op for op in getattr(snapshot, "machine_operations", ())
           if getattr(op, "runtime_type", "") == "Xn" or "Xn" in getattr(op, "object_type", "")]
    if not xns:
        return X_PARK, None
    xn = xns[-1]
    return float(xn.x), (None if xn.y is None else -float(xn.y))


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

    field = _execution_field(path)
    # Fail-loud: campo fuera de la grilla 2×2 conocida (AB/DC/EF/HG). El modelo de origen/SHF/EDK
    # está derivado y byte-validado para esos 4 (N019/N020/N021). ⚠️ EF/AB/DC están descalibrados:
    # los valores que emite son los de la fields.cfg ACTUAL (stale); al recalibrar + re-snapshotear
    # fields.cfg, entran solos. La guarda de CARAS laterales va aparte (abajo).
    if field not in SUPPORTED_FIELDS:
        raise UnsupportedOperationError(
            f"Campo de trabajo '{field}' no soportado (conocidos: {SUPPORTED_FIELDS}).")

    park_x, park_y = _xn_park(result.snapshot)
    ctx = PieceCtx(
        # Maestro usa el nombre del ARCHIVO .pgmx para el comentario "% x.pgm" del ISO, no el
        # piece_name interno (evidencia: N007 _not_selected renombrados y N_RT_E001_Vel/_Prof,
        # copias con piece_name viejo adentro).
        piece_name=path.stem,
        length=state.length,
        width=state.width,
        depth=state.depth,
        origin_x=state.origin_x,
        origin_y=state.origin_y,
        origin_z=state.origin_z,
        field=field,
        park_x=park_x,
        park_y=park_y,
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

    # Fail-loud: taladros laterales solo en HG por ahora. El SHF por-cara espejado (Left/Right/
    # Front/Back) para EF/AB/DC todavía no está derivado; el modelo actual solo cubre origen/SHF de
    # top/router. (Top y router SÍ andan en los 4 campos.)
    if side_drills and field not in SIDE_SUPPORTED_FIELDS:
        raise UnsupportedOperationError(
            f"Taladros laterales en el campo '{field}' no soportados todavía (solo "
            f"{SIDE_SUPPORTED_FIELDS}): falta derivar el SHF por-cara espejado. Top/router sí andan.")

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

    # Fail-loud por hundimiento del FRESADO: profundidad efectiva (pasante → espesor+extra;
    # ciego → target) vs SinkingLength de la fresa (espejo de la guarda de taladros). N024: el
    # borde inclusivo pasa (E004 sink=22, espesor 18 + extra 4 = 22 OK en Maestro).
    from ._tool_catalog import tool_geometry as _tool_geometry
    for milling in routers:
        eff = (ctx.depth + milling.depth_spec.extra_depth if milling.depth_spec.is_through
               else (milling.depth_spec.target_depth or 0.0))
        sink = _tool_geometry(milling.tool_name).sinking_length
        if eff > sink:
            kind = "pasante (espesor+extra)" if milling.depth_spec.is_through else "ciego"
            raise UnsupportedOperationError(
                f"Fresado lineal {kind} con {milling.tool_name}: profundidad efectiva {eff:g} mm "
                f"supera el hundimiento máximo de la fresa ({sink:g} mm, def.tlgx SinkingLength). [A3]")

    # Sort side drills by face priority then by original order within face
    side_drills.sort(key=lambda s: FACE_PRIORITY.get(s.plane_name, 99))

    return ctx, ProgramOps(
        routers=tuple(routers),
        top_drills=tuple(top_drills),
        side_drills=tuple(side_drills),
    )
