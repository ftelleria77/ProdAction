"""Renderizado de bloques de taladro vertical (Top Drill) para ISO Xilog Plus."""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from pgmx.synthesis.drilling.single import DrillingSpec

from ._machine import (
    OR_OFX, OR_OFY, SHF_X_MACHINE, SHF_Y_MACHINE, Z_PARK,
    effective_top_feed_spindle, resolve_top_tool,
)
from ._reader import PieceCtx


def _peck_depths(z_top_surface: float, z_cut: float, step_number: int,
                 step_depth: float) -> list[float]:
    """Profundidades de corte z₁…zₙ (la última == z_cut).

    Sin escalonado (step_number==0 y step_depth==0) → una sola pasada [z_cut].
    Con escalonado → n pasos iguales: n = step_number, o n = ceil(total/step_depth)
    (step_depth es un máximo). Validado N006.
    """
    total = z_top_surface - z_cut
    if step_number > 0:
        n = step_number
    elif step_depth > 0.0:
        n = max(1, math.ceil(total / step_depth - 1e-9))
    else:
        return [z_cut]
    step = total / n
    depths = [z_top_surface - step * i for i in range(1, n)]
    depths.append(z_cut)   # exacto, sin arrastre de float
    return depths


def _cut_motion(cx: float, cy: float, security: float, feed: float,
                depths: list[float]) -> list[str]:
    """Movimiento de corte de un agujero (pasada simple o peck). Validado N006.

    Asume el husillo ya posicionado en (cx, cy) sobre la pieza.
    """
    if len(depths) == 1:
        return [f"G1 G9 Z{depths[0]:.3f} F{feed:.3f}", f"G0 Z{security:.3f}"]
    n = len(depths)
    lines = [
        f"G1 G9 Z{depths[0]:.3f} F{feed:.3f}",
        f"G0 X{cx:.3f} Y{cy:.3f} Z{security:.3f}",   # retracción total tras pass 1
    ]
    for i in range(1, n):
        prev = depths[i - 1]
        lines.append(f"G0 Z{prev + 1.0:.3f}")                 # aproxima 1 mm sobre la previa
        lines.append(f"G1 G9 Z{depths[i]:.3f} F{feed:.3f}")
        if i < n - 1:
            lines.append(f"G0 Z{prev:.3f}")                   # retrae a la profundidad previa
    lines.append(f"G0 X{cx:.3f} Y{cy:.3f} Z{security:.3f}")    # retracción total final
    return lines


@dataclass
class _TopDrillState:
    spindle: int = 0       # current rpm (0 = unknown after router or start)
    etk6: int | None = None
    prev_x: float = 0.0
    prev_y: float = 0.0


def render_top_drill(
    drills: list[DrillingSpec],
    ctx: PieceCtx,
    after_router: bool,
    router_spindle: int,
) -> list[str]:
    """Render all top drill holes.

    after_router: True when router preceded this block (changes first-hole setup).
    router_spindle: spindle speed left active by router (only relevant when after_router).
    """
    if not drills:
        return []

    state = _TopDrillState(spindle=router_spindle if after_router else 0)
    lines: list[str] = []

    for i, drill in enumerate(drills):
        base_tool = resolve_top_tool(drill.diameter, drill.drill_family, drill.tool_name)
        eff_feed, eff_spindle = effective_top_feed_spindle(
            base_tool, drill.feedrate, drill.spindle)
        tool = dataclasses.replace(base_tool, feed=eff_feed, spindle=eff_spindle)
        depth = drill.depth_spec.target_depth or 0.0
        z_top_surface = tool.tlc + ctx.depth
        # Pasante: el taladro vertical para en la cara inferior (mesa, z=tlc); no baja
        # más (chocaría el bancal), por eso Maestro ignora extra_depth. (N005)
        z_cut = tool.tlc if drill.depth_spec.is_through else z_top_surface - depth
        z_top_security = z_top_surface + drill.security_plane
        depths = _peck_depths(z_top_surface, z_cut, drill.step_number, drill.step_depth)

        same_tool = (state.etk6 == tool.etk6)

        if i == 0 and after_router:
            lines += _first_hole_after_router(drill, ctx, tool, state, depths, z_top_security)
        elif i == 0:
            lines += _first_hole_no_prior(drill, ctx, tool, state, depths, z_top_security)
        elif same_tool:
            lines += _same_tool_hole(drill, ctx, tool, state, depths, z_top_security)
        else:
            lines += _tool_change_hole(drill, ctx, tool, state, depths, z_top_security)

        state.etk6 = tool.etk6
        state.spindle = tool.spindle
        state.prev_x = drill.center_x
        state.prev_y = drill.center_y

    return lines


# ---------------------------------------------------------------------------
# First hole when top drill is first family (no router before)
# ---------------------------------------------------------------------------

def _first_hole_no_prior(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, depths: list[float],
    z_top_security: float,
) -> list[str]:
    shf_y = SHF_Y_MACHINE + ctx.origin_y
    lines = [
        f"?%ETK[6]={tool.etk6}",
        f"%Or[0].ofX={OR_OFX:.3f}",
        f"%Or[0].ofY={OR_OFY:.3f}",
        f"%Or[0].ofZ={ctx.DZ * 1000:.3f}",
        "MLV=1",
        f"SHF[X]={SHF_X_MACHINE - ctx.DX:.3f}",
        f"SHF[Y]={shf_y:.3f}",
        f"SHF[Z]={ctx.origin_z:.3f}",
        "MLV=2",
        "MLV=2",
        f"SHF[X]={tool.shf_x:.3f}",
        f"SHF[Y]={tool.shf_y:.3f}",
        f"SHF[Z]={tool.shf_z:.3f}",
        "?%ETK[17]=257",
        f"S{tool.spindle}M3",
        f"?%ETK[0]={tool.etk0}",
    ]
    lines += _cut_block(drill, ctx, tool, depths, z_top_security)
    return lines


# ---------------------------------------------------------------------------
# First hole when router preceded top drill (router->top transition)
# ---------------------------------------------------------------------------

def _first_hole_after_router(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, depths: list[float],
    z_top_security: float,
) -> list[str]:
    """Transition from router to top drill + first hole."""
    lines = [
        "MLV=0",
        f"G0 G53 Z{Z_PARK:.3f}",
        "MLV=2",
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        f"G0 G53 Z{Z_PARK:.3f}",
        "G64",
        "MLV=1",
        f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={tool.etk6}",
        "MLV=2",
        f"SHF[X]={tool.shf_x:.3f}",
        f"SHF[Y]={tool.shf_y:.3f}",
        f"SHF[Z]={tool.shf_z:.3f}",
        "?%ETK[17]=257",
        f"S{tool.spindle}M3",
        f"?%ETK[0]={tool.etk0}",
    ]
    lines += _cut_block_no_mlv2(drill, ctx, tool, depths, z_top_security)
    return lines


# ---------------------------------------------------------------------------
# Same tool, additional hole
# ---------------------------------------------------------------------------

def _same_tool_hole(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, depths: list[float],
    z_top_security: float,
) -> list[str]:
    lines = [
        "MLV=1",
        f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"G0 X{state.prev_x:.3f} Y{state.prev_y:.3f} Z{z_top_security:.3f}",
        f"G0 X{drill.center_x:.3f} Y{drill.center_y:.3f} Z{z_top_security:.3f}",
        "?%ETK[7]=3",
        *_cut_motion(drill.center_x, drill.center_y, z_top_security, tool.feed, depths),
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
    return lines


# ---------------------------------------------------------------------------
# Tool change to different diameter
# ---------------------------------------------------------------------------

def _tool_change_hole(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, depths: list[float],
    z_top_security: float,
) -> list[str]:
    lines = [
        "MLV=1",
        f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={tool.etk6}",
        f"G0 X{state.prev_x:.3f} Y{state.prev_y:.3f} Z{z_top_security:.3f}",
        "MLV=2",
        f"SHF[X]={tool.shf_x:.3f}",
        f"SHF[Y]={tool.shf_y:.3f}",
        f"SHF[Z]={tool.shf_z:.3f}",
    ]
    if tool.spindle != state.spindle:
        lines += ["?%ETK[17]=257", f"S{tool.spindle}M3"]
    lines += [f"?%ETK[0]={tool.etk0}"]
    lines += [
        f"G0 X{drill.center_x:.3f} Y{drill.center_y:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "?%ETK[7]=3",
        *_cut_motion(drill.center_x, drill.center_y, z_top_security, tool.feed, depths),
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
    return lines


# ---------------------------------------------------------------------------
# Cut blocks (used by first holes only — same/tool-change have inline cuts)
# ---------------------------------------------------------------------------

def _cut_block(
    drill: DrillingSpec, ctx: PieceCtx, tool, depths: list[float], z_top_security: float,
) -> list[str]:
    """First cut when top drill is first family (needs MLV=2 before G1 G9)."""
    return [
        f"G0 X{drill.center_x:.3f} Y{drill.center_y:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "?%ETK[7]=3",
        "MLV=2",
        *_cut_motion(drill.center_x, drill.center_y, z_top_security, tool.feed, depths),
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]


def _cut_block_no_mlv2(
    drill: DrillingSpec, ctx: PieceCtx, tool, depths: list[float], z_top_security: float,
) -> list[str]:
    """First cut after router→top transition (no MLV=2 before G1 G9)."""
    return [
        f"G0 X{drill.center_x:.3f} Y{drill.center_y:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "?%ETK[7]=3",
        *_cut_motion(drill.center_x, drill.center_y, z_top_security, tool.feed, depths),
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
