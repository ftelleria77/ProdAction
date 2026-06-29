"""Convertidor PGMX → ISO Xilog Plus (motor empírico, validado con lote N001)."""

from __future__ import annotations

from pathlib import Path

from pgmx.synthesis.drilling.single import DrillingSpec

from ._machine import ROUTER_SPINDLE, ROUTER_TLC, effective_top_feed_spindle, resolve_top_tool
from ._preamble import render_epilogue, render_preamble
from ._reader import ProgramOps, read_pgmx
from ._router import render_router
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

    # Preamble face specialization: only when side is the first (and only) family
    side_only = has_side and not has_router and not has_top
    first_side_face = ops.side_drills[0].plane_name if side_only else None

    lines: list[str] = []
    lines += render_preamble(ctx, first_side_face, has_router=has_router)

    if has_router:
        lines += render_router(list(ops.routers), ctx)

    if has_top:
        after_router_spindle = ROUTER_SPINDLE if has_router else 0
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
            top_spindle = ROUTER_SPINDLE
            prev_tlc = ROUTER_TLC
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
    )

    return "\n".join(lines) + "\n"


def _sort_side_drills(drills: list[DrillingSpec]) -> list[DrillingSpec]:
    """Sort side drills in Maestro execution order.

    Face priority: Front > Left > Right > Back.
    Within the same face Maestro appears to process holes by descending center_x
    for Left/Back (Y_pos = -center_x) and ascending center_x for Right/Front.
    This is empirical from B007 (Left, x=60 then x=140 in PGMX → 140 then 60 in ISO).
    """
    from ._machine import FACE_PRIORITY

    def sort_key(d: DrillingSpec) -> tuple[int, float]:
        fp = FACE_PRIORITY.get(d.plane_name, 99)
        # Faces where Y_pos = -center_x: higher center_x drilled first (descending)
        if d.plane_name in ("Left", "Back"):
            return (fp, -d.center_x)
        # Faces where Y_pos = +center_x or X_pos = center_x: ascending center_x
        return (fp, d.center_x)

    return sorted(drills, key=sort_key)
