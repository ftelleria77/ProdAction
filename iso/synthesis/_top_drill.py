"""Renderizado de bloques de taladro vertical (Top Drill) para ISO Xilog Plus."""

from __future__ import annotations

from dataclasses import dataclass
from pgmx.synthesis.drilling.single import DrillingSpec

from ._machine import OR_OFX, OR_OFY, SHF_Y_MACHINE, TOP_TOOL
from ._reader import PieceCtx


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
        tool = TOP_TOOL[drill.diameter]
        depth = drill.depth_spec.target_depth or 0.0
        z_top_surface = tool.tlc + ctx.depth
        z_cut = z_top_surface - depth
        z_top_security = z_top_surface + drill.security_plane

        same_tool = (state.etk6 == tool.etk6)

        if i == 0 and after_router:
            lines += _first_hole_after_router(drill, ctx, tool, state, z_cut, z_top_security)
        elif i == 0:
            lines += _first_hole_no_prior(drill, ctx, tool, state, z_cut, z_top_security)
        elif same_tool:
            lines += _same_tool_hole(drill, ctx, tool, state, z_cut, z_top_security)
        else:
            lines += _tool_change_hole(drill, ctx, tool, state, z_cut, z_top_security)

        state.etk6 = tool.etk6
        state.spindle = tool.spindle
        state.prev_x = drill.center_x
        state.prev_y = drill.center_y

    return lines


# ---------------------------------------------------------------------------
# First hole when top drill is first family (no router before)
# ---------------------------------------------------------------------------

def _first_hole_no_prior(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, z_cut: float,
    z_top_security: float,
) -> list[str]:
    shf_y = SHF_Y_MACHINE + ctx.origin_y
    lines = [
        f"?%ETK[6]={tool.etk6}",
        f"%Or[0].ofX={OR_OFX:.3f}",
        f"%Or[0].ofY={OR_OFY:.3f}",
        f"%Or[0].ofZ={ctx.DZ * 1000:.3f}",
        "MLV=1",
        f"SHF[X]=-{ctx.DX:.3f}",
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
    lines += _cut_block(drill, ctx, tool, z_cut, z_top_security)
    return lines


# ---------------------------------------------------------------------------
# First hole when router preceded top drill (router->top transition)
# ---------------------------------------------------------------------------

def _first_hole_after_router(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, z_cut: float,
    z_top_security: float,
) -> list[str]:
    """Transition from router to top drill + first hole."""
    lines = [
        "MLV=0",
        "G0 G53 Z201.000",
        "MLV=2",
        "G61",
        "MLV=0",
        "?%ETK[13]=0",
        "?%ETK[18]=0",
        "G0 G53 Z201.000",
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
    lines += _cut_block_no_mlv2(drill, ctx, tool, z_cut, z_top_security)
    return lines


# ---------------------------------------------------------------------------
# Same tool, additional hole
# ---------------------------------------------------------------------------

def _same_tool_hole(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, z_cut: float,
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
        f"G1 G9 Z{z_cut:.3f} F{tool.feed:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
    return lines


# ---------------------------------------------------------------------------
# Tool change to different diameter
# ---------------------------------------------------------------------------

def _tool_change_hole(
    drill: DrillingSpec, ctx: PieceCtx, tool, state: _TopDrillState, z_cut: float,
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
        f"G1 G9 Z{z_cut:.3f} F{tool.feed:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
    return lines


# ---------------------------------------------------------------------------
# Cut blocks (used by first holes only — same/tool-change have inline cuts)
# ---------------------------------------------------------------------------

def _cut_block(
    drill: DrillingSpec, ctx: PieceCtx, tool, z_cut: float, z_top_security: float,
) -> list[str]:
    """First cut when top drill is first family (needs MLV=2 before G1 G9)."""
    return [
        f"G0 X{drill.center_x:.3f} Y{drill.center_y:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "?%ETK[7]=3",
        "MLV=2",
        f"G1 G9 Z{z_cut:.3f} F{tool.feed:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]


def _cut_block_no_mlv2(
    drill: DrillingSpec, ctx: PieceCtx, tool, z_cut: float, z_top_security: float,
) -> list[str]:
    """First cut after router→top transition (no MLV=2 before G1 G9)."""
    return [
        f"G0 X{drill.center_x:.3f} Y{drill.center_y:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "?%ETK[7]=3",
        f"G1 G9 Z{z_cut:.3f} F{tool.feed:.3f}",
        f"G0 Z{z_top_security:.3f}",
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
