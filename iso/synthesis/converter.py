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
from ._channel import render_channel
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
    router_compensated = any(
        (m.side_of_feature != "Center" and getattr(m, "activate_cnc_correction", True))
        or (m.approach.is_enabled and m.milling_strategy is None
            and getattr(m, "activate_cnc_correction", True))
        for m in ops.routers)
    # Programas MULTI-fresado (N036 two_side/two_mp/two_leads, byte-validados): compensación,
    # estrategia y approach conviven con las transiciones (triple G0 al punto de aproximación;
    # la salida compensada no-última agrega un ?%ETK[7]=0 extra). El RETRACT programable en
    # multi-op sigue sin fixture (interacción retracción-G1 vs transición).
    if len(ops.routers) > 1 and any(m.retract.is_enabled for m in ops.routers):
        raise UnsupportedOperationError(
            "alejamiento programable con varios fresados en el programa: sin fixture "
            "de referencia aún. [A3]")

    lines: list[str] = []
    # La sierra maneja su propia entrada MLV (como el router): el preamble no emite el footer.
    lines += render_preamble(
        ctx, first_side_face, has_router=has_router or has_saw,
        router_compensated=router_compensated)

    if has_router:
        lines += render_router(list(ops.routers), ctx)

    if has_saw:
        lines += render_channel(list(ops.saw_channels), ctx)

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


def _sort_side_drills(drills: list[DrillSpec]) -> list[DrillSpec]:
    """Sort side drills in Maestro execution order.

    Face priority: Front > Left > Right > Back.
    Within the same face Maestro appears to process holes by descending center_x
    for Left/Back (Y_pos = -center_x) and ascending center_x for Right/Front.
    This is empirical from B007 (Left, x=60 then x=140 in PGMX → 140 then 60 in ISO).
    """
    from ._machine import FACE_PRIORITY

    def sort_key(d: DrillSpec) -> tuple[int, float]:
        fp = FACE_PRIORITY.get(d.plane_name, 99)
        # Faces where Y_pos = -center_x: higher center_x drilled first (descending)
        if d.plane_name in ("Left", "Back"):
            return (fp, -d.center_x)
        # Faces where Y_pos = +center_x or X_pos = center_x: ascending center_x
        return (fp, d.center_x)

    return sorted(drills, key=sort_key)
