"""Convertidor PGMX → ISO Xilog Plus (motor empírico, validado con lote N001)."""

from __future__ import annotations

from pathlib import Path

from pgmx.synthesis.drilling.single import DrillSpec

from ._machine import effective_top_feed_spindle, resolve_top_tool
from ._preamble import render_epilogue, render_preamble
from ._reader import ProgramOps, read_pgmx
from ._validation import UnsupportedOperationError
from ._router import render_router
from ._tool_catalog import tool_geometry
from ._saw import render_saw
from ._side_drill import render_side_drill
from ._top_drill import render_top_drill


def convert(pgmx_path: Path) -> str:
    """Lee un .pgmx y devuelve su representación ISO como string.

    El orden de familias sigue la reordenación empírica de Maestro:
    Router → Top drill → Side drill.
    """
    ctx, ops = read_pgmx(pgmx_path)

    has_router = bool(ops.routers)
    has_top = bool(ops.top_drills)
    has_side = bool(ops.side_drills)
    has_saw = bool(ops.saw_channels)

    # Preamble face specialization: only when side is the first (and only) family
    side_only = has_side and not has_router and not has_top
    first_side_face = ops.side_drills[0].plane_name if side_only else None

    # El preamble lleva ?%ETK[7]=0 cuando el router mueve el ETK[7]=4 antes del plunge:
    # con corrección de herramienta (N023) o con approach programable single-pass (N026).
    # En MULTIPASADA el ETK[7]=4 conserva su posición (tras el descenso a security) aunque
    # haya leads -> SIN reset (N034: ETK[8]=1 pelado en el tercer bloque).
    # Lo decide la PRIMERA op del router, no cualquiera (Galceado.pgmx: op1 ZigZag CAD +
    # op2 compensada con leads → el preamble va SIN reset; el estado de la op2 lo maneja la
    # transición con su doble ?%ETK[7]=0). Todo el corpus previo tenía la op compensada
    # primera, así que any≡first hasta ese fixture.
    router_compensated = bool(ops.routers) and (
        (getattr(ops.routers[0], "side_of_feature", "Center") != "Center"
         and getattr(ops.routers[0], "activate_cnc_correction", True))
        or (ops.routers[0].approach.is_enabled and ops.routers[0].milling_strategy is None
            and getattr(ops.routers[0], "activate_cnc_correction", True)))
    # Programas MULTI-fresado (N036 two_side/two_mp/two_leads, byte-validados): compensación,
    # estrategia y approach conviven con las transiciones (triple G0 al punto de aproximación;
    # la salida compensada no-última agrega un ?%ETK[7]=0 extra). El RETRACT programable en la
    # op ÚLTIMA convive con el teardown normal (Galceado.pgmx: op2 con leads Line Down/Up tras
    # el cambio de herramienta, byte-validado); en una op NO-última sigue sin fixture
    # (interacción retracción-G1 vs transición).
    # Alejamiento en una op NO-última: derivado cuando la op siguiente CAMBIA de
    # herramienta (Experimento-01, 2026-08-03: el contorno perimetral con retract Arco
    # cierra normal — arco, G1 Z, G40, 1 mm — y recién ahí arranca el cambio de fresa de
    # N028). Con la MISMA fresa sigue sin fixture (interacción retracción-G1 vs el triple
    # G0 de la transición).
    for index, milling in enumerate(ops.routers[:-1]):
        if milling.retract.is_enabled and milling.tool_name == ops.routers[index + 1].tool_name:
            raise UnsupportedOperationError(
                "alejamiento programable en un fresado NO-último del programa SIN cambio "
                "de herramienta: sin fixture de referencia aún. [A3]")

    # Xn al INICIO + router compensado: el orden del ?%ETK[7]=0 del preamble respecto del
    # bloque de park no tiene fixture (el manual 2026-07-30 es un vaciado, sin corrección).
    if ctx.park_at_start and router_compensated:
        raise UnsupportedOperationError(
            "Xn al INICIO en un programa con router compensado: el orden del reset ?%ETK[7]=0 "
            "respecto del bloque de park no tiene fixture aún. [Eje C]")

    lines: list[str] = []
    # La sierra maneja su propia entrada MLV (como el router): el preamble no emite el footer.
    lines += render_preamble(
        ctx, first_side_face, has_router=has_router or has_saw,
        router_compensated=router_compensated)

    if has_router:
        lines += render_router(list(ops.routers), ctx)

    if has_saw:
        lines += render_saw(list(ops.saw_channels), ctx)

    if has_top:
        after_router_spindle = (
            tool_geometry(ops.routers[-1].tool_name).spindle_std if has_router else 0)
        lines += render_top_drill(
            list(ops.top_drills),
            ctx,
            after_router=has_router,
            router_spindle=after_router_spindle,
        )

    if has_side:
        side_drills = _sort_side_drills(list(ops.side_drills))

        if has_top:
            prev_family = "top"
            last_top = ops.top_drills[-1]
            last_tool = resolve_top_tool(
                last_top.diameter, last_top.drill_family, last_top.tool_name)
            _, top_spindle = effective_top_feed_spindle(
                last_tool, last_top.feedrate, last_top.spindle)
            prev_tlc = last_tool.tlc  # piso del g53 = longitud del tool que se retrae
        elif has_router:
            prev_family = "router"
            router_geom = tool_geometry(ops.routers[-1].tool_name)  # última fresa del router
            top_spindle = router_geom.spindle_std
            prev_tlc = router_geom.tool_offset_length
        else:
            prev_family = None
            top_spindle = 0
            prev_tlc = 0.0

        lines += render_side_drill(
            side_drills,
            ctx,
            prev_family=prev_family,
            top_spindle=top_spindle,
            prev_tlc=prev_tlc,
        )

        last_side_face: str | None = side_drills[-1].plane_name
    else:
        last_side_face = None

    lines += render_epilogue(
        ctx,
        has_side_drill=has_side,
        last_side_face=last_side_face,
        has_router=has_router,
        has_top=has_top,
        has_saw=has_saw,
    )

    return "\n".join(lines) + "\n"


def _sorted_face_run(run: list[DrillSpec]) -> list[DrillSpec]:
    """Orden DENTRO de una cara (B007, sin cambios): descendente en center_x para
    Left/Back (Y_pos = −center_x → coordenada de máquina ascendente), ascendente
    para Right/Front."""
    if run and run[0].plane_name in ("Left", "Back"):
        return sorted(run, key=lambda d: -d.center_x)
    return sorted(run, key=lambda d: d.center_x)


def _sort_side_drills(drills: list[DrillSpec]) -> list[DrillSpec]:
    """Orden de CARAS laterales = regla B-BH-005 parcial, portada del emisor viejo
    (`iso_state_synthesis/pgmx_source.py::_ordered_side_drill_block`) el 2026-08-05.

    Las caras salen en ORDEN DE APARICIÓN de la fuente (corridas contiguas por cara;
    las corridas repetidas de una cara se funden en su primera aparición), NO por una
    prioridad fija. La `FACE_PRIORITY` anterior (Front>Left>Right>Back) era un artefacto
    del corpus propio: el sintetizador PRE-ORDENA las caras al serializar (`_apply_drills`
    Front→Back→Left→Right), así que ningún fixture N pudo contradecirla — el testigo es
    `N_B008_left_then_front.pgmx`, autorado Left→Front pero SERIALIZADO Front→Left
    (CLAUDE.md §5, tercer punto ciego del corpus). La refutó Cazaux `Faja frontal`:
    fuente Right→Left, ISO Right→Left (prioridad habría emitido Left primero).

    ROTACIÓN DE TANDA (≥3 corridas con la MISMA cara al inicio y al final): la última
    corrida pasa adelante y la primera al final — validada por el emisor viejo en Cazaux
    con Back→Front→Back. ⚠️ ACOTADA a caras Y (Front/Back): Haeublein `Divisor_Horiz1`
    mostró que Right→Left→Right NO rota (experiments/024 del emisor viejo — quedó como
    su único operativo sin explicar). El límite exacto es HIPÓTESIS con dos puntos de
    evidencia; el ensayo general lo re-mide en cada corrida."""
    runs: list[tuple[str, list[DrillSpec]]] = []
    for drill in drills:
        if not runs or runs[-1][0] != drill.plane_name:
            runs.append((drill.plane_name, [drill]))
        else:
            runs[-1][1].append(drill)

    if (len(runs) >= 3 and runs[0][0] == runs[-1][0]
            and runs[0][0] in ("Front", "Back")):
        rotated = [runs[-1], *runs[1:-1], runs[0]]
        return [d for _, run in rotated for d in _sorted_face_run(run)]

    by_plane: dict[str, list[DrillSpec]] = {}
    plane_order: list[str] = []
    for drill in drills:
        if drill.plane_name not in by_plane:
            by_plane[drill.plane_name] = []
            plane_order.append(drill.plane_name)
        by_plane[drill.plane_name].append(drill)
    return [d for plane in plane_order for d in _sorted_face_run(by_plane[plane])]
