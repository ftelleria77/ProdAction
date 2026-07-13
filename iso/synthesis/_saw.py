"""Render del CANAL con la Sierra Vertical X (082, cabezal perforador) — derivado de N037.

Programa sierra (byte-validado, 9 fixtures): header SIN ATC — la sierra vive fija en el
mandril 82 del cabezal perforador — con `?%ETK[6]={mandril}`, el bloque Or/SHF de primera
pasada (idéntico al router), `?%ETK[17]=257`, `S{spindle_std}M3`, `?%ETK[1]=16` y el SHF del
mandril de spindles.cfg con el MEDIO ANCHO de la hoja restado en Y (128.85 − w/2 = 126.95:
la referencia del corte es la CARA de la hoja, no su centro).

Cuerpo por canal: G0 al extremo de X MAYOR (Maestro NORMALIZA el sentido a −x: el fixture
xfwd autorado en +x salió byte-idéntico al base) → D1/SVL{TLC}/SVR{w/2} → plunge a
profundidad a feed de descenso → `?%ETK[7]=1` (la sierra usa 1, el router 4) → corte en −x a
feed_std → G0 Z{security} → teardown. Transición entre canales (two): `?%ETK[8]=1 / G40 /
G17 / MLV=2` + DOBLE G0 (última posición → siguiente inicio, ambos a TLC+sp; el router usa
triple). Epílogo propio: `?%ETK[1]=0 / ?%ETK[17]=0 / G4F1.200` (dwell) antes del M5.

Números pendientes de procedencia (Tier B, libro mayor): ETK[17]=257, ETK[1]=16, ETK[7]=1 y
el dwell G4F1.200 — constantes empíricas del ciclo sierra hasta ubicarlas en machine config.
"""

from __future__ import annotations

from ._machine import or_ofx, or_ofy, shf_x, shf_y, spindle_shf
from ._reader import PieceCtx
from ._router import _g1_cut
from ._tool_catalog import tool_geometry

SAW_ETK17 = 257
SAW_ETK1 = 16


def _saw_mandrel(tool_name: str) -> int:
    return int(tool_name.lstrip("0") or "0")


def render_saw(channels, ctx: PieceCtx) -> list[str]:
    lines: list[str] = []
    prev_end: tuple[float, float] | None = None

    for i, spec in enumerate(channels):
        geom = tool_geometry(spec.tool_name)
        depth = spec.depth_spec.target_depth or 0.0
        security = spec.security_plane
        z_approach = geom.tool_offset_length + security
        svl = geom.tool_offset_length
        svr = spec.tool_width / 2.0
        # Sentido físico de la 082: SIEMPRE del X mayor al menor (N037 xfwd normalizado).
        x_start = max(spec.start_x, spec.end_x)
        x_end = min(spec.start_x, spec.end_x)
        y = spec.start_y

        if i == 0:
            lines += _saw_header(spec, ctx, geom)
            lines += [
                f"G0 X{x_start:.3f} Y{y:.3f}",
                f"G0 Z{z_approach:.3f}",
            ]
        else:
            assert prev_end is not None
            lines += [
                "?%ETK[8]=1",
                "G40",
                "G17",
                "MLV=2",
                f"G0 X{prev_end[0]:.3f} Y{prev_end[1]:.3f} Z{z_approach:.3f}",
                f"G0 X{x_start:.3f} Y{y:.3f} Z{z_approach:.3f}",
            ]
        lines += [
            "D1",
            f"SVL {svl:.3f}",
            f"VL6={svl:.3f}",
            f"SVR {svr:.3f}",
            f"VL7={svr:.3f}",
            f"G1 Z{-depth:.3f} F{geom.feed_default:.3f}",
            "?%ETK[7]=1",
            _g1_cut(x_start, y, x_end, y, -depth, geom.feed_std, prev_z=-depth),
            f"G0 Z{security:.3f}",
            "D0",
            "SVL 0.000",
            "VL6=0.000",
            "SVR 0.000",
            "VL7=0.000",
            "?%ETK[7]=0",
        ]
        prev_end = (x_end, y)

    return lines


def _saw_header(spec, ctx: PieceCtx, geom) -> list[str]:
    mandrel = _saw_mandrel(spec.tool_name)
    sx, sy, sz = spindle_shf(mandrel)
    return [
        f"?%ETK[6]={mandrel}",
        "G17",
        "MLV=2",
        f"%Or[0].ofX={or_ofx(ctx, block=True):.3f}",
        f"%Or[0].ofY={or_ofy(ctx, block=True):.3f}",
        f"%Or[0].ofZ={ctx.DZ * 1000:.3f}",
        "MLV=1",
        f"SHF[X]={shf_x(ctx, block=True):.3f}",
        f"SHF[Y]={shf_y(ctx, block=True):.3f}",
        f"SHF[Z]={ctx.DZ:.3f}",
        "MLV=2",
        f"?%ETK[17]={SAW_ETK17}",
        f"S{geom.spindle_std}M3",
        f"?%ETK[1]={SAW_ETK1}",
        "MLV=2",
        f"SHF[X]={sx:.3f}",
        f"SHF[Y]={sy - spec.tool_width / 2.0:.3f}",
        f"SHF[Z]={sz:.3f}",
    ]
