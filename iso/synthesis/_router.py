"""Renderizado de bloques de fresado lineal (router) para ISO Xilog Plus.

Soporta TODAS las herramientas del cabezal (fresas E001/E003.. y la sierra E002; el converter no
distingue tipo — decisión de Fermín) y líneas en cualquier dirección/sentido. Derivado de N022:
- número de fresa N = E00N → `T{N}` y `ETK[9]={N}`. ETK[6]/ETK[18] son del cabezal (constantes).
- spindle = spindle_std, TLC/plunge/cut del catálogo (spindle_std / tool_offset_length / feed_default /
  feed_std). SHF = offset del cabezal (Cabeza 3, constante), no de la fresa.
- trayectoria: corte a (end_x,end_y); el sentido es automático. Ejes que se mueven → X/Y; Z solo se
  repite si se mueve UN eje (diagonal omite Z). Ver `_cut_line`.
"""

from __future__ import annotations

from pgmx.synthesis.milling.line import LineMillingSpec

from ._machine import (
    ROUTER_ETK6, ROUTER_ETK18,
    ROUTER_SHF_X, ROUTER_SHF_Y, ROUTER_SHF_Z,
    or_ofx, or_ofy, shf_x, shf_y,
)
from ._tool_catalog import tool_geometry
from ._reader import PieceCtx


def _cutter_number(spec: LineMillingSpec) -> int:
    """Número de fresa: E00N → N (= slot ATC y ETK[9])."""
    return int(spec.tool_name.lstrip("E"))


def _cut_line(spec: LineMillingSpec, depth: float, cut_feed: float) -> str:
    """G1 de corte hasta (end_x, end_y). Emite los ejes que se mueven; repite Z solo si se mueve
    UN eje (la diagonal, con X e Y, omite Z). El sentido es implícito (va al end)."""
    parts: list[str] = []
    if spec.end_x != spec.start_x:
        parts.append(f"X{spec.end_x:.3f}")
    if spec.end_y != spec.start_y:
        parts.append(f"Y{spec.end_y:.3f}")
    if len(parts) == 1:
        parts.append(f"Z{-depth:.3f}")
    return "G1 " + " ".join(parts) + f" F{cut_feed:.3f}"


def render_router(millings: list[LineMillingSpec], ctx: PieceCtx) -> list[str]:
    lines: list[str] = []
    prev_end: tuple[float, float] | None = None
    n = len(millings)

    for i, spec in enumerate(millings):
        geom = tool_geometry(spec.tool_name)
        depth = spec.depth_spec.target_depth or 0.0
        security = spec.security_plane
        z_router_approach = geom.tool_offset_length + security
        svl = z_router_approach - security   # = tool_offset_length (TLC)
        svr = spec.tool_width / 2.0
        plunge_feed = geom.feed_default       # bajada G1 Z
        cut_feed = geom.feed_std              # corte lateral G1 X/Y
        is_last = (i == n - 1)

        if i == 0:
            lines += _atc_header(spec)
            lines += _first_pass_setup(ctx)
        else:
            # Between passes: G17 + double G0 to new start
            assert prev_end is not None
            lines += [
                "G17",
                "MLV=2",
                f"G0 X{prev_end[0]:.3f} Y{prev_end[1]:.3f} Z{z_router_approach:.3f}",
                f"G0 X{spec.start_x:.3f} Y{spec.start_y:.3f} Z{z_router_approach:.3f}",
                f"G0 X{spec.start_x:.3f} Y{spec.start_y:.3f} Z{z_router_approach:.3f}",
            ]

        # First pass: explicit approach; subsequent passes already positioned by triple G0
        if i == 0:
            lines += [
                f"G0 X{spec.start_x:.3f} Y{spec.start_y:.3f}",
                f"G0 Z{z_router_approach:.3f}",
            ]
        lines += [
            "D1",
            f"SVL {svl:.3f}",
            f"VL6={svl:.3f}",
            f"SVR {svr:.3f}",
            f"VL7={svr:.3f}",
            f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
            "?%ETK[7]=4",
            _cut_line(spec, depth, cut_feed),
        ]

        if not is_last:
            # Non-last pass: ?%ETK[7]=0 before retract
            lines += [
                "?%ETK[7]=0",
                f"G0 Z{security:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                "SVR 0.000",
                "VL7=0.000",
            ]
        else:
            # Last pass: retract first, ?%ETK[7]=0 after VL7
            lines += [
                f"G0 Z{security:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                "SVR 0.000",
                "VL7=0.000",
                "?%ETK[7]=0",
            ]

        prev_end = (spec.end_x, spec.end_y)

    return lines


def _atc_header(spec: LineMillingSpec) -> list[str]:
    n = _cutter_number(spec)
    spindle = tool_geometry(spec.tool_name).spindle_std
    return [
        "MLV=0",
        f"T{n}",
        "SYN",
        "M06",
        f"?%ETK[6]={ROUTER_ETK6}",
        f"?%ETK[9]={n}",
        f"?%ETK[18]={ROUTER_ETK18}",
        f"S{spindle}M3",
    ]


def _first_pass_setup(ctx: PieceCtx) -> list[str]:
    return [
        "G17",
        "MLV=2",
        f"%Or[0].ofX={or_ofx(ctx, block=True):.3f}",
        f"%Or[0].ofY={or_ofy(ctx, block=True):.3f}",
        f"%Or[0].ofZ={ctx.DZ * 1000:.3f}",
        "MLV=1",
        f"SHF[X]={shf_x(ctx, block=True):.3f}",
        f"SHF[Y]={shf_y(ctx, block=True):.3f}",
        f"SHF[Z]={ctx.DZ:.3f}",   # NOTE: no +%ETK[114] for router (vs drill)
        "MLV=2",
        "?%ETK[13]=1",
        "MLV=2",
        f"SHF[X]={ROUTER_SHF_X:.3f}",
        f"SHF[Y]={ROUTER_SHF_Y:.3f}",
        f"SHF[Z]={ROUTER_SHF_Z:.3f}",
    ]
