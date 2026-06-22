"""Renderizado de bloques de fresado lineal (router E004) para ISO Xilog Plus."""

from __future__ import annotations

from pgmx.synthesis.milling.line import LineMillingSpec

from ._machine import (
    OR_OFX, OR_OFY,
    ROUTER_ATC_SLOT, ROUTER_ETK6, ROUTER_ETK9, ROUTER_ETK18, ROUTER_SPINDLE,
    ROUTER_SHF_X, ROUTER_SHF_Y, ROUTER_SHF_Z,
    ROUTER_TLC,
    SHF_Y_MACHINE,
)
from ._reader import PieceCtx


def render_router(millings: list[LineMillingSpec], ctx: PieceCtx) -> list[str]:
    lines: list[str] = []
    prev_end: tuple[float, float] | None = None
    n = len(millings)

    for i, spec in enumerate(millings):
        depth = spec.depth_spec.target_depth or 0.0
        security = spec.security_plane
        z_router_approach = ROUTER_TLC + security
        svl = z_router_approach - security
        svr = spec.tool_width / 2.0
        is_last = (i == n - 1)

        if i == 0:
            lines += _atc_header()
            lines += _first_pass_setup(ctx)
        else:
            # Between passes: G17 + double G0 to new start
            assert prev_end is not None
            lines += [
                "G17",
                "MLV=2",
                f"G0 X{prev_end[0]:.3f} Y{millings[i-1].start_y:.3f} Z{z_router_approach:.3f}",
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
            f"G1 Z{-depth:.3f} F2000.000",
            "?%ETK[7]=4",
            f"G1 X{spec.end_x:.3f} Z{-depth:.3f} F5000.000",
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


def _atc_header() -> list[str]:
    return [
        "MLV=0",
        f"T{ROUTER_ATC_SLOT}",
        "SYN",
        "M06",
        f"?%ETK[6]={ROUTER_ETK6}",
        f"?%ETK[9]={ROUTER_ETK9}",
        f"?%ETK[18]={ROUTER_ETK18}",
        f"S{ROUTER_SPINDLE}M3",
    ]


def _first_pass_setup(ctx: PieceCtx) -> list[str]:
    shf_y = SHF_Y_MACHINE + ctx.origin_y  # e.g. -1510.600
    return [
        "G17",
        "MLV=2",
        f"%Or[0].ofX={OR_OFX:.3f}",
        f"%Or[0].ofY={OR_OFY:.3f}",
        f"%Or[0].ofZ={ctx.DZ * 1000:.3f}",
        "MLV=1",
        f"SHF[X]=-{ctx.DX:.3f}",
        f"SHF[Y]={shf_y:.3f}",
        f"SHF[Z]={ctx.DZ:.3f}",   # NOTE: no +%ETK[114] for router (vs drill)
        "MLV=2",
        "?%ETK[13]=1",
        "MLV=2",
        f"SHF[X]={ROUTER_SHF_X:.3f}",
        f"SHF[Y]={ROUTER_SHF_Y:.3f}",
        f"SHF[Z]={ROUTER_SHF_Z:.3f}",
    ]
