"""Preamble y epilogue del ISO Xilog Plus (validados contra N001)."""

from __future__ import annotations

from ._machine import (
    SIDE_FACE, Z_PARK,
    edk_field, or_ofx, or_ofy, shf_x, shf_y, side_shf,
)
from ._reader import PieceCtx


def render_preamble(
    ctx: PieceCtx,
    first_side_face: str | None,
    has_router: bool,
    router_compensated: bool = False,
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
        f";H DX={dx:.3f} DY={dy:.3f} DZ={dz:.3f} BX=0.000 BY=0.000 BZ=0.000 -{ctx.field} V=0 *MM C=0 T=0 ",
        "?%ETK[500]=100",
        "",
        "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )",
        "",
        "G0 G53 Z %ax[2].pa[22]/1000",
        "M58",
        "G71",
        "MLV=0",
        f"%Or[0].ofX={or_ofx(ctx, block=False):.3f}",
        f"%Or[0].ofY={or_ofy(ctx, block=False):.3f}",
        f"%Or[0].ofZ={dz * 1000:.3f}",
        "?%EDK[0].0=0",
        "?%EDK[1].0=0",
        "MLV=1",
        f"SHF[X]={shf_x(ctx, block=False):.3f}",
        f"SHF[Y]={shf_y(ctx, block=False):.3f}",
        f"SHF[Z]={dz:.3f}+%ETK[114]/1000",
    ]

    # Three G40 blocks; third one may be face-specific for side-first programs.
    lines += ["?%ETK[8]=1", "G40", "?%ETK[8]=1", "G40"]
    if ctx.park_at_start:
        # Xn al INICIO del programa (manual Rebaba_negativa 2026-07-30): el park se emite
        # ENTRE el segundo y el tercer par ETK[8]/G40 del preamble, SIN M5 (el husillo aún
        # no giró); el footer de este programa va sin M5/park (ver render_epilogue).
        lines += [
            "G61",
            "MLV=0",
            "D0",
            f"G0 G53 Z{Z_PARK:.3f}",
            f"G0 G53 X{ctx.park_x:.3f}"
            # `+ 0.0`: park_y = −Xn.y, y con Xn.y=0 el −0.0 emitiría `Y-0.000`; Maestro
            # escribe `Y0.000` (Cazaux, ensayo 2026-08-05 — misma regla del cero negativo
            # que el manual Rebaba_negativa / _pos3 y el `-v+0.0` de spindle_shf).
            + (f" Y{ctx.park_y + 0.0:.3f}" if ctx.park_y is not None else ""),
            "G64",
        ]
    if router_compensated:
        # Router con corrección de herramienta (G41/G42): Maestro resetea ?%ETK[7] acá (N023).
        lines.append("?%ETK[7]=0")
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

    if face in ("Left", "Back"):
        sx, sy = side_shf(ctx, face)
        return [
            "MLV=1",
            f"SHF[X]={sx:.3f}",
            f"SHF[Y]={sy:.3f}",
            f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
            f"?%ETK[8]={SIDE_FACE[face].etk8}",
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
    has_saw: bool = False,
) -> list[str]:
    """Genera el epilogue ISO.

    last_side_face: cara lateral del último taladro lateral. Solo relevante cuando
        has_side_drill=True.  Left y Back necesitan un bloque de restauración SHF
        completo; Right y Front usan solo G61/D0.
    has_router: True cuando hay router (cambia el bloque de shutdown).
    has_top: True cuando hay taladro vertical (solo router no lo tiene).
    """
    dz = ctx.DZ
    # Park del footer: X (y opcional Y) de la operación nula Xn del .pgmx (N015). El Z es
    # machine config (Z_PARK). Maestro pone X e Y en el MISMO bloque G53 cuando hay Y.
    # El Xn (Operación Nula) se RENDERIZA como `M5` + `G0 G53 X{park}`: pide retirar la cabina de
    # seguridad para que el operario acceda a la pieza. Sin Xn (`park_x is None`) NO se emite
    # ninguno de los dos — nadie lo pidió (N043, .pgmx hechos a mano en Maestro). Con Xn al
    # INICIO (park_at_start) el park ya salió en el PREAMBLE y el footer va igual de pelado
    # (manual Rebaba_negativa 2026-07-30).
    has_xn = ctx.park_x is not None and not ctx.park_at_start
    # `+ 0.0` en Y: normaliza el cero negativo (ver el bloque de park del preamble).
    park_lines = [f"G0 G53 X{ctx.park_x:.3f}" + (
        f" Y{ctx.park_y + 0.0:.3f}" if ctx.park_y is not None else "")] if has_xn else []
    m5_lines = ["M5"] if has_xn else []

    syn_block = [
        "SYN",
        "?%ETK[0]=0",
        "?%ETK[1]=0",
        "?%ETK[2]=0",
        "?%ETK[13]=0",
        "?%ETK[17]=0",
        "?%ETK[18]=0",
        "?%ETK[19]=0",
        f"?%EDK[{edk_field(ctx)}].0=1",
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
        f"?%EDK[{edk_field(ctx)}].0=0",
        "M2",
    ]

    # Sierra-only (N037): shutdown propio — limpia ?%ETK[1] (seteado a 16 en el header) y
    # ?%ETK[17], con dwell G4F1.200 antes del M5 (como los taladros, que limpian ETK[0]).
    if has_saw and not has_router and not has_top and not has_side_drill:
        saw_shutdown = [
            "G61",
            "MLV=0",
            "?%ETK[1]=0",
            "?%ETK[17]=0",
            "G4F1.200",
            *m5_lines,
            "D0",
            f"G0 G53 Z{Z_PARK:.3f}",
            *park_lines,
            "G64",
        ]
        return saw_shutdown + syn_block

    # Router-only (no top drill, no side drill): different shutdown sequence
    if has_router and not has_top and not has_side_drill:
        router_shutdown = [
            "G61",
            "MLV=0",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            *m5_lines,
            "D0",
            f"G0 G53 Z{Z_PARK:.3f}",
            *park_lines,
            "G64",
        ]
        return router_shutdown + syn_block

    standard_start = [
        "G61",
        "MLV=0",
        "?%ETK[0]=0",
        "?%ETK[17]=0",
        "G4F1.200",
        *m5_lines,
        "D0",
        f"G0 G53 Z{Z_PARK:.3f}",
        *park_lines,
        "G64",
    ]

    if not has_side_drill:
        return standard_start + syn_block

    # Side drill programs: standard start + restoration block + SYN
    needs_shf_restoration = last_side_face in ("Left", "Back")
    if needs_shf_restoration:
        rest_x, rest_y = side_shf(ctx, "Front")  # marco por defecto (no Left/Back) del campo
        restoration = [
            "MLV=1",
            f"SHF[X]={rest_x:.3f}",
            f"SHF[Y]={rest_y:.3f}",
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
