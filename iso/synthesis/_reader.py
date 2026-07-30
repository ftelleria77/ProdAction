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
from pgmx.synthesis.drilling.pattern import DrillPatternSpec
from pgmx.synthesis.drilling.single import DrillSpec
from pgmx.synthesis.milling.arc import ArcSpec
from pgmx.synthesis.milling.polyline import PolylineSpec, build_polyline_spec
from pgmx.synthesis.milling.circle import CircleSpec
from pgmx.synthesis.milling.contour import ContourSpec, _build_squaring_outline_points
from pgmx.synthesis.milling.line import LineSpec
from pgmx.synthesis.milling.channel import ChannelSpec
from pgmx.synthesis.milling.pocket import PocketSpec

from ._machine import (
    FACE_PRIORITY, SIDE_MAX_DEPTH, SIDE_SUPPORTED_FIELDS, SUPPORTED_FIELDS, resolve_top_tool,
)
from ._validation import UnsupportedOperationError, validate_entries

_EXECUTION_FIELD_RE = re.compile(r"<[^>]*ExecutionFields>([^<]*)</")


def _execution_field(path: Path) -> str:
    """Campo de trabajo elegido en Maestro, registrado en el .pgmx como
    <ExecutionFields>HG</ExecutionFields> (dentro de XilogHeaderParameters). El .pgmx es un ZIP
    con un .xml adentro. Determina el origen del campo (field_origin) y el espejado geométrico.
    Default "HG" si no aparece (el único campo calibrado hoy).

    Alias "A" → "AB": un programa hecho a mano SIN tocar «Parámetros de máquinas» queda con el
    área default y Maestro escribe ExecutionFields=A — pero su PROPIO postproceso emite el
    header `-AB` con los orígenes del campo AB (gemelos manuales de N047, byte-validados).
    Solo "A" tiene fixture; cualquier otro valor fuera de la grilla sigue rechazándose."""
    with zipfile.ZipFile(path) as z:
        xml_name = next((n for n in z.namelist() if n.endswith(".xml")), None)
        if xml_name is None:
            return "HG"
        xml = z.read(xml_name).decode("utf-8", errors="replace")
    m = _EXECUTION_FIELD_RE.search(xml)
    field = m.group(1).strip() if m and m.group(1).strip() else "HG"
    return {"A": "AB"}.get(field, field)

Op = Union[DrillSpec, LineSpec]


def side_effective_depth(drill: DrillSpec, ctx: "PieceCtx") -> float:
    """Profundidad real de un taladro lateral. Pasante: la dimensión cruzada del panel
    (Left/Right atraviesan el largo; Front/Back, el ancho). Ciego: target_depth."""
    if drill.depth_spec.is_through:
        return ctx.length if drill.plane_name in ("Left", "Right") else ctx.width
    return drill.depth_spec.target_depth or 0.0


def top_effective_depth(drill: DrillSpec, ctx: "PieceCtx") -> float:
    """Profundidad real de un taladro vertical. Pasante: el espesor del panel (atraviesa de
    la cara superior a la mesa). Ciego: target_depth."""
    if drill.depth_spec.is_through:
        return ctx.depth
    return drill.depth_spec.target_depth or 0.0


def expand_drilling_pattern(pattern: DrillPatternSpec) -> list[DrillSpec]:
    """Expande un patrón rectangular a taladros individuales (idénticos al base).

    Geometría (N008): center = esquina mínima (primer agujero); columnas en +X por
    `spacing`, filas en +Y por `row_spacing`. Orden = row-major (fila Y exterior
    ascendente, columna X interior ascendente).
    """
    row_spacing = pattern.spacing if pattern.row_spacing is None else pattern.row_spacing
    holes: list[DrillSpec] = []
    for r in range(int(pattern.rows)):
        for c in range(int(pattern.columns)):
            holes.append(DrillSpec(
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
    # del .pgmx. El Z del park es machine config (Z_PARK). (N015)
    # `park_x = None` ⟺ el programa NO tiene Xn ⟺ el footer NO lleva `M5` ni park X (N043).
    park_x: float | None = None
    park_y: float | None = None
    # El Xn es POSICIONAL: si el paso Xn viene ANTES de todos los mecanizados, el park se
    # emite en el PREAMBLE (bloque G61/MLV=0/D0/G0 G53 Z/G0 G53 X/G64, SIN M5 — el husillo
    # aún no giró) y el footer va SIN M5/park (manual Rebaba_negativa 2026-07-30).
    park_at_start: bool = False

    @property
    def DX(self) -> float:  # noqa: N802
        return self.length + self.origin_x

    @property
    def DY(self) -> float:  # noqa: N802
        return self.width + self.origin_y

    @property
    def DZ(self) -> float:  # noqa: N802
        return self.origin_z + self.depth


def _xn_park(snapshot) -> tuple[float, float | None, bool] | None:
    """(park_x, park_y, at_start) del Xn del programa, o None si NO hay Xn. `at_start`:
    el paso Xn viene ANTES de todos los mecanizados en el workplan → el park va en el
    PREAMBLE y el footer queda sin M5/park (manual Rebaba_negativa 2026-07-30); si no,
    el modelo clásico del footer (N015). Xn en el MEDIO → fail-loud.

    El Xn (Operación Nula) desplaza el cabezal para que la cabina de seguridad libere la zona de
    trabajo y el operario pueda acceder a la pieza — la misma función que el Park. En el ISO se
    RENDERIZA como `M5` + `G0 G53 X{park}` en el footer: si nadie pide retirar la cabina, esas
    líneas NO se emiten (N043: los .pgmx hechos a mano en Maestro no traen Xn y su ISO no las
    tiene). ⚠️ Esto MATIZA N015 ("sin Xn → el default de Maestro"): los 346 fixtures de N001–N042
    tienen Xn porque los generó NUESTRO sintetizador, que siempre lo escribía — el corpus nunca
    pudo ver el caso sin Xn. Hoy se sintetiza sin Xn con `xn=None`.

    park_x = Xn.x; park_y = -Xn.y (la cama va 0..-1500 en pgmx → 0..+1500 en máquina). Maestro
    admite VARIOS Xn y el flujo real los usa (cara A → Xn+Xmsg para girar la pieza → cara B → Xn
    para retirarla): el Xn es POSICIONAL, no una propiedad de la pieza. Este modelo de
    "park del footer" solo es válido mientras haya UNO SOLO al final — que es lo único que hay en
    los fixtures. Un programa con varios se rechaza. Ver iso/docs/experiments/xn_operacion_nula.md
    """
    steps = getattr(snapshot, "working_steps", ())
    xn_indices = [i for i, s in enumerate(steps)
                  if getattr(s, "runtime_type", "") == "Xn"
                  or "Xn" in getattr(s, "object_type", "")]
    if not xn_indices:
        return None
    if len(xn_indices) > 1:
        raise UnsupportedOperationError(
            f"El programa tiene {len(xn_indices)} operaciones Xn y solo está derivado el caso de "
            f"UNA. El Xn es POSICIONAL: ocurre en un punto del programa (flujo real: mecanizar la "
            f"cara A → Xn+Xmsg para que el operario GIRE la pieza → mecanizar la cara B → Xn para "
            f"retirarla). Fixturados: UNO al final (footer M5+park, N015) y UNO al inicio "
            f"(preamble sin M5, manual 2026-07-30). Falta derivar los intermedios/múltiples. "
            f"Ver iso/docs/experiments/xn_operacion_nula.md [Eje C].")
    xn_index = xn_indices[0]
    machining_indices = [i for i, s in enumerate(steps)
                         if getattr(s, "manufacturing_feature_ref", None) is not None]
    at_start = bool(machining_indices) and xn_index < min(machining_indices)
    if machining_indices and not at_start and xn_index < max(machining_indices):
        raise UnsupportedOperationError(
            "El Xn está en el MEDIO del programa (entre mecanizados): sin fixture — solo "
            "están derivados el Xn al FINAL (footer M5+park) y al INICIO (preamble sin M5). "
            "[Eje C]")
    xn = steps[xn_index]
    return float(xn.x), (None if xn.y is None else -float(xn.y)), at_start


@dataclass(frozen=True)
class ProgramOps:
    routers: tuple[LineSpec, ...]
    top_drills: tuple[DrillSpec, ...]
    side_drills: tuple[DrillSpec, ...]
    saw_channels: tuple[ChannelSpec, ...] = ()


def _contour_to_polyline(spec: ContourSpec, length: float, width: float) -> PolylineSpec:
    """Un ContourSpec (Galceado/Escuadrado, forma canónica de En-Juego) ES una polilínea CERRADA
    del perímetro — el galceado NO es una feature nueva del ISO (N043). El converter lo mapea a
    PolylineSpec para reusar el render de perfil (arranque a mitad de borde + leads, N044 enjuego).
    ContourSpec se conserva como spec de AUTORÍA de la App (decisión de Fermín); esto es solo la
    traducción de LECTURA del converter."""
    points = _build_squaring_outline_points(
        length, width, start_edge=spec.start_edge, winding=spec.winding)
    return build_polyline_spec(
        points=[(float(x), float(y)) for x, y in points],
        feature_name=spec.feature_name,
        tool_id=spec.tool_id, tool_name=spec.tool_name, tool_width=spec.tool_width,
        security_plane=spec.security_plane,
        side_of_feature=spec.side_of_feature,
        is_through=spec.depth_spec.is_through,
        target_depth=spec.depth_spec.target_depth,
        extra_depth=spec.depth_spec.extra_depth,
        approach_enabled=spec.approach.is_enabled,
        approach_type=spec.approach.approach_type,
        approach_mode=spec.approach.mode,
        approach_radius_multiplier=spec.approach.radius_multiplier,
        approach_speed=spec.approach.speed,
        approach_arc_side=spec.approach.arc_side,
        retract_enabled=spec.retract.is_enabled,
        retract_type=spec.retract.retract_type,
        retract_mode=spec.retract.mode,
        retract_radius_multiplier=spec.retract.radius_multiplier,
        retract_speed=spec.retract.speed,
        retract_arc_side=spec.retract.arc_side,
        retract_overlap=spec.retract.overlap,
        milling_strategy=spec.milling_strategy,
        activate_cnc_correction=True,   # la forma En-Juego siempre emite ACC=true (N043)
    )


def read_pgmx(path: Path) -> tuple[PieceCtx, ProgramOps]:
    result = adapt_pgmx_path(path)
    state = result.snapshot.state

    # Fail-loud: aborta si hay alguna operación/parámetro fuera del subconjunto soportado,
    # en lugar de ignorarla en silencio o crashear más adelante. OJO: las entries que el ADAPTER
    # no pudo adaptar no llegan a adapted_entries — sin este chequeo se DROPEABAN en silencio
    # (ISO incompleto; detectado con el primer ZigZag).
    unsupported = getattr(result, "unsupported_entries", ())
    if unsupported:
        reasons = "; ".join(
            f"{e.feature_name or e.feature_id}: {', '.join(e.reasons) or 'sin detalle'}"
            for e in unsupported[:3])
        raise UnsupportedOperationError(
            f"El .pgmx tiene {len(unsupported)} operación(es) que el adapter no pudo adaptar "
            f"(se omitirían en silencio): {reasons}")
    # ContourSpec (Galceado/Escuadrado forma App) → polilínea del perímetro para el render; se
    # valida y enruta como una polilínea más (N043/N044). ContourSpec sigue siendo la spec de
    # autoría de la App; esto es solo la lectura del converter.
    specs = [
        _contour_to_polyline(e.spec, state.length, state.width)
        if isinstance(e.spec, ContourSpec) else e.spec
        for e in result.adapted_entries
    ]
    validate_entries(specs)

    field = _execution_field(path)
    # Fail-loud: campo fuera de la grilla 2×2 conocida (AB/DC/EF/HG). El modelo de origen/SHF/EDK
    # está derivado y byte-validado para esos 4 (N019/N020/N021). ⚠️ EF/AB/DC están descalibrados:
    # los valores que emite son los de la fields.cfg ACTUAL (stale); al recalibrar + re-snapshotear
    # fields.cfg, entran solos. La guarda de CARAS laterales va aparte (abajo).
    if field not in SUPPORTED_FIELDS:
        raise UnsupportedOperationError(
            f"Campo de trabajo '{field}' no soportado (conocidos: {SUPPORTED_FIELDS}).")

    park = _xn_park(result.snapshot)
    park_x, park_y, park_at_start = park if park is not None else (None, None, False)
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
        park_at_start=park_at_start,
    )

    routers: list[LineSpec] = []
    top_drills: list[DrillSpec] = []
    side_drills: list[DrillSpec] = []
    saw_channels: list[ChannelSpec] = []

    for spec in specs:
        if isinstance(spec, DrillPatternSpec):
            drills = expand_drilling_pattern(spec)
        elif isinstance(spec, DrillSpec):
            drills = [spec]
        elif isinstance(spec, (LineSpec, CircleSpec, ArcSpec,
                               PolylineSpec, PocketSpec)):
            # Círculo (N038), arco suelto (N040), polilínea mixta (N041) y VACIADO (N047)
            # son ops de la familia ROUTER: mismo header/transición/teardown que las líneas.
            routers.append(spec)
            continue
        elif isinstance(spec, ChannelSpec):
            saw_channels.append(spec)
            continue
        else:
            continue
        for drill in drills:
            if drill.plane_name == "Top":
                top_drills.append(drill)
            else:
                side_drills.append(drill)

    # Fail-loud: sin Xn, el footer omite `M5` y el park X — derivado del lote N043, cuyos 5
    # archivos (hechos a mano en Maestro) son todos ROUTER-ONLY. Para los demás cabezales no hay
    # fixture sin Xn: los 346 de N001–N042 tienen Xn porque los generó nuestro sintetizador, que
    # siempre lo escribía. Antes que aproximar en silencio, se rechaza. (Hoy ya se puede generar
    # el lote que lo cierre: `build_synthesis_request(..., xn=None)`.)
    if park_x is None and (top_drills or side_drills or saw_channels):
        raise UnsupportedOperationError(
            "Programa SIN operación Xn que no es solo-router: el footer sin Xn (sin `M5` ni park X) "
            "solo está derivado para router (N043). Falta fixture para taladro/sierra sin Xn.")

    # Fail-loud: Xn al INICIO solo está derivado para programas solo-router (manual
    # Rebaba_negativa 2026-07-30, vaciado). Con taladros/sierra no hay fixture del preamble.
    if park_at_start and (top_drills or side_drills or saw_channels):
        raise UnsupportedOperationError(
            "Programa con Xn al INICIO que no es solo-router: el bloque de park en el preamble "
            "solo está derivado para router (manual 2026-07-30). [Eje C]")

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

    # Fail-loud: familias del router (línea / círculo / arco / polilínea / vaciado)
    # MEZCLADAS en un programa — las transiciones mixtas no tienen fixture (cada lote two-*
    # es de una sola familia: N028/N036 líneas, N038 círculos, N040 arcos, N041 polilíneas).
    router_families = {type(m).__name__ for m in routers}
    if len(router_families) > 1:
        raise UnsupportedOperationError(
            "fresado de familias mezcladas (línea/círculo/arco/polilínea/vaciado) en el "
            f"mismo programa: sin fixture de referencia aún ({sorted(router_families)}). [B]")

    # Fail-loud: VARIOS vaciados en un programa — la transición entre pockets no tiene
    # fixture (N047 es todo single-op). [B5]
    if sum(isinstance(m, PocketSpec) for m in routers) > 1:
        raise UnsupportedOperationError(
            "varios vaciados en el mismo programa: la transición entre pockets no tiene "
            "fixture de referencia aún (N047 es single-op). [B5]")

    # Fail-loud: canal de sierra MEZCLADO con otras familias — el orden/las transiciones
    # entre el cabezal sierra y router/taladros no tienen fixture (N037 es sierra-only). [B]
    if saw_channels and (routers or top_drills or side_drills):
        raise UnsupportedOperationError(
            "canal de sierra combinado con fresado/taladros en el mismo programa: "
            "sin fixture de referencia aún (N037 valida programas solo-sierra). [B]")

    # Sort side drills by face priority then by original order within face
    side_drills.sort(key=lambda s: FACE_PRIORITY.get(s.plane_name, 99))

    return ctx, ProgramOps(
        routers=tuple(routers),
        top_drills=tuple(top_drills),
        side_drills=tuple(side_drills),
        saw_channels=tuple(saw_channels),
    )
