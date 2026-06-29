"""Preamble y epilogue del ISO Xilog Plus (validados contra N001)."""

from __future__ import annotations

from ._machine import OR_OFY, SIDE_FACE, SHF_Y_MACHINE, Z_PARK
from ._reader import PieceCtx


def render_preamble(
    ctx: PieceCtx,
    first_side_face: str | None,
    has_router: bool,
) -> list[str]:
    """Genera el preamble ISO.

    first_side_face: cara lateral cuyo G40 aparece en el tercer bloque del preamble.
        Solo aplica cuando side drill es la primera familia (no hay router ni top).
        Pass None para emitir tres bloques genéricos ?%ETK[8]=1.

    has_router: si hay router, se omite el footer MLV=2/G17 (el router lo gestiona).
    """
    dx, dy, dz = ctx.DX, ctx.DY, ctx.DZ
    lines: list[str] = [
        f"% {ctx.piece_name.lower()}.pgm",
        f";H DX={dx:.3f} DY={dy:.3f} DZ={dz:.3f} BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 ",
        "?%ETK[500]=100",
        "",
        "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )",
        "",
        "G0 G53 Z %ax[2].pa[22]/1000",
        "M58",
        "G71",
        "MLV=0",
        f"%Or[0].ofX={-dx * 1000:.3f}",
        f"%Or[0].ofY={OR_OFY:.3f}",
        f"%Or[0].ofZ={dz * 1000:.3f}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]=-{dx:.3f}",
        f"SHF[Y]={SHF_Y_MACHINE:.3f}",
        f"SHF[Z]={dz:.3f}+%ETK[114]/1000",
    ]

    # Three G40 blocks; third one may be face-specific for side-first programs.
    lines += ["?%ETK[8]=1", "G40", "?%ETK[8]=1", "G40"]
    lines += _last_g40_block(ctx, first_side_face)

    # Footer: only for non-router programs (router handles its own MLV entry).
    if not has_router:
        lines += [
            "MLV=1",
            f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
            "MLV=2",
            "G17",
        ]

    return lines


def _last_g40_block(ctx: PieceCtx, face: str | None) -> list[str]:
    """Third G40 block of the preamble."""
    if face is None:
        return ["?%ETK[8]=1", "G40"]

    if face == "Left":
        shf_y = SHF_Y_MACHINE + ctx.DY
        return [
            "MLV=1",
            f"SHF[X]=-{ctx.DX:.3f}",
            f"SHF[Y]={shf_y:.3f}",
            f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
            f"?%ETK[8]={SIDE_FACE['Left'].etk8}",
            "G40",
        ]
    if face == "Back":
        shf_y = SHF_Y_MACHINE + ctx.origin_y
        return [
            "MLV=1",
            f"SHF[X]=-{ctx.origin_x:.3f}",
            f"SHF[Y]={shf_y:.3f}",
            f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
            f"?%ETK[8]={SIDE_FACE['Back'].etk8}",
            "G40",
        ]
    # Right or Front: only ETK[8] changes, no SHF re-setup
    return [f"?%ETK[8]={SIDE_FACE[face].etk8}", "G40"]


def render_epilogue(
    ctx: PieceCtx,
    has_side_drill: bool,
    last_side_face: str | None = None,
    has_router: bool = False,
    has_top: bool = False,
) -> list[str]:
    """Genera el epilogue ISO.

    last_side_face: cara lateral del último taladro lateral. Solo relevante cuando
        has_side_drill=True.  Left y Back necesitan un bloque de restauración SHF
        completo; Right y Front usan solo G61/D0.
    has_router: True cuando hay router (cambia el bloque de shutdown).
    has_top: True cuando hay taladro vertical (solo router no lo tiene).
    """
    dx, dz = ctx.DX, ctx.DZ
    shf_y = SHF_Y_MACHINE + ctx.origin_y  # e.g. -1510.600
    # Park del footer: X (y opcional Y) de la operación nula Xn del .pgmx (N015). El Z es
    # machine config (Z_PARK). Maestro pone X e Y en el MISMO bloque G53 cuando hay Y.
    park_xy = f"G0 G53 X{ctx.park_x:.3f}" + (
        f" Y{ctx.park_y:.3f}" if ctx.park_y is not None else "")

    syn_block = [
        "SYN",
        "?%ETK[0]=0",
        "?%ETK[1]=0",
        "?%ETK[2]=0",
        "?%ETK[13]=0",
        "?%ETK[17]=0",
        "?%ETK[18]=0",
        "?%ETK[19]=0",
        "?%EDK[13].0=1",
        "MLV=1",
        "SHF[X]=0",
        "SHF[Y]=0",
        "SHF[Z]=0",
        "MLV=2",
        "SHF[X]=0",
        "SHF[Y]=0",
        "SHF[Z]=0",
        "MLV=0",
        "VL6=0",
        "VL7=0",
        "?%EDK[13].0=0",
        "M2",
    ]

    # Router-only (no top drill, no side drill): different shutdown sequence
    if has_router and not has_top and not has_side_drill:
        router_shutdown = [
            "G61",
            "MLV=0",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            "M5",
            "D0",
            f"G0 G53 Z{Z_PARK:.3f}",
            park_xy,
            "G64",
        ]
        return router_shutdown + syn_block

    standard_start = [
        "G61",
        "MLV=0",
        "?%ETK[0]=0",
        "?%ETK[17]=0",
        "G4F1.200",
        "M5",
        "D0",
        f"G0 G53 Z{Z_PARK:.3f}",
        park_xy,
        "G64",
    ]

    if not has_side_drill:
        return standard_start + syn_block

    # Side drill programs: standard start + restoration block + SYN
    needs_shf_restoration = last_side_face in ("Left", "Back")
    if needs_shf_restoration:
        restoration = [
            "MLV=1",
            f"SHF[X]=-{dx:.3f}",
            f"SHF[Y]={shf_y:.3f}",
            f"SHF[Z]={dz:.3f}+%ETK[114]/1000",
            "G61",
            "MLV=0",
            "D0",
            f"G0 G53 Z{Z_PARK:.3f}",
            "G64",
        ]
    else:
        restoration = [
            "G61",
            "D0",
            f"G0 G53 Z{Z_PARK:.3f}",
            "G64",
        ]

    return standard_start + restoration + syn_block
