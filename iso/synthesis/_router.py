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

from dataclasses import replace as _dc_replace

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


def _cut_segments(
    spec: LineMillingSpec, depth: float, cut_feed: float,
) -> list[tuple[float, float, float, float]]:
    """Tramos del corte: [(x_fin, y_fin, z_fin, feed), ...]. Sin cambios → un solo tramo al end.

    Cambios DURANTE el recorrido (N_RT_E001_Vel/_Prof, byte-validados):
    - speed_changes [(upar, speed)]: se parte en el punto UPar; el tramo posterior corre a
      F = speed×1000 (m/min → mm/min). La Z no cambia.
    - depth_changes [(upar, d2)]: RAMPA lineal desde la prof. de la operación (el plunge inicial)
      hasta d2, alcanzándola en el punto UPar (el G1 interpola X y Z); sigue plano a d2.
    El punto UPar es paramétrico sobre la línea: p = start + upar·(end-start).
    """
    sx, sy, ex, ey = spec.start_x, spec.start_y, spec.end_x, spec.end_y
    if spec.speed_changes:
        (upar, speed), = spec.speed_changes
        mx, my = sx + upar * (ex - sx), sy + upar * (ey - sy)
        return [(mx, my, -depth, cut_feed), (ex, ey, -depth, speed * 1000.0)]
    if spec.depth_changes:
        (upar, d2), = spec.depth_changes
        mx, my = sx + upar * (ex - sx), sy + upar * (ey - sy)
        return [(mx, my, -d2, cut_feed), (ex, ey, -d2, cut_feed)]
    return [(ex, ey, -depth, cut_feed)]


def _g1_cut(prev_x: float, prev_y: float, x: float, y: float, z: float, feed: float) -> str:
    """G1 de corte de un tramo. Emite los ejes X/Y que se mueven; agrega Z solo cuando se mueve
    UN eje del plano (la diagonal X+Y omite Z — quirk de Maestro, N022 dir_diag)."""
    parts: list[str] = []
    if x != prev_x:
        parts.append(f"X{x:.3f}")
    if y != prev_y:
        parts.append(f"Y{y:.3f}")
    if len(parts) == 1:
        parts.append(f"Z{z:.3f}")
    return "G1 " + " ".join(parts) + f" F{feed:.3f}"


# Distancia de entrada/salida de la corrección (lead-in/out): 1 mm antes del start / después del
# end sobre la dirección de avance, donde se activa G41/G42 y se desactiva G40. Constante del
# ciclo de Maestro (N023: idéntica con E004 w=4 y E001 w=18.36 → no depende de la herramienta).
_COMP_LEAD: float = 1.0


def _unit_dir(spec: LineMillingSpec) -> tuple[float, float]:
    dx, dy = spec.end_x - spec.start_x, spec.end_y - spec.start_y
    length = (dx * dx + dy * dy) ** 0.5
    return (dx / length, dy / length)


def render_router(millings: list[LineMillingSpec], ctx: PieceCtx) -> list[str]:
    lines: list[str] = []
    prev_end: tuple[float, float] | None = None
    n = len(millings)

    for i, spec in enumerate(millings):
        geom = tool_geometry(spec.tool_name)
        # Pasante: z = -(espesor + extra) — el fresado SÍ pasa la cara inferior (corta al
        # spoilboard), a diferencia del taladro vertical que para en la mesa (N024: -18/-20/-22).
        if spec.depth_spec.is_through:
            depth = ctx.depth + spec.depth_spec.extra_depth
        else:
            depth = spec.depth_spec.target_depth or 0.0
        security = spec.security_plane
        z_router_approach = geom.tool_offset_length + security
        svl = z_router_approach - security   # = tool_offset_length (TLC)
        # Rebaba (SideOffset del feature) suma al corrector de radio; si da 0 las líneas SVR se
        # OMITEN (setup y teardown) — Maestro no emite un corrector nulo (N024 rebm2).
        svr = spec.tool_width / 2.0 + spec.side_offset
        # Corrección de longitud (IsPrecise): acorta el recorrido el RADIO de la fresa en ambos
        # extremos (centro en [start+r·dir, end−r·dir] → el filo cubre justo el segmento). N023
        # _long: E004 ±2, E001 ±9.18. El resto del render usa los extremos ya corregidos (approach,
        # lead-in/out de la compensación y corte).
        if spec.is_precise:
            r = spec.tool_width / 2.0
            ux, uy = _unit_dir(spec)
            spec = _dc_replace(
                spec,
                start_x=spec.start_x + r * ux, start_y=spec.start_y + r * uy,
                end_x=spec.end_x - r * ux, end_y=spec.end_y - r * uy,
            )
        plunge_feed = geom.feed_default       # bajada G1 Z
        cut_feed = geom.feed_std              # corte lateral G1 X/Y
        is_last = (i == n - 1)
        # Corrección de herramienta (side_of_feature Left/Right): el control compensa el radio
        # (SVR) vía G41/G42; las coordenadas del corte NO cambian (N023). El lado es relativo
        # al avance: Left→G41, Right→G42.
        compensated = spec.side_of_feature != "Center"

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
            if compensated:
                # Aproxima al punto de lead-in (1 mm antes del start, sobre la dirección).
                ux, uy = _unit_dir(spec)
                ax, ay = spec.start_x - _COMP_LEAD * ux, spec.start_y - _COMP_LEAD * uy
                lines += [f"G0 X{ax:.3f} Y{ay:.3f}", f"G0 Z{z_router_approach:.3f}"]
            else:
                lines += [
                    f"G0 X{spec.start_x:.3f} Y{spec.start_y:.3f}",
                    f"G0 Z{z_router_approach:.3f}",
                ]
        lines += [
            "D1",
            f"SVL {svl:.3f}",
            f"VL6={svl:.3f}",
        ]
        if svr != 0.0:
            lines += [f"SVR {svr:.3f}", f"VL7={svr:.3f}"]
        if compensated:
            # ETK[7]=4 va ANTES de activar la corrección; el lead-in engancha G41/G42 moviéndose
            # al start en el plano de seguridad, y recién ahí baja (plunge).
            lines += [
                "?%ETK[7]=4",
                "G41" if spec.side_of_feature == "Left" else "G42",
                f"G1 X{spec.start_x:.3f} Y{spec.start_y:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
            ]
        else:
            lines += [
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                "?%ETK[7]=4",
            ]
        px, py = spec.start_x, spec.start_y
        for seg_x, seg_y, seg_z, seg_feed in _cut_segments(spec, depth, cut_feed):
            lines.append(_g1_cut(px, py, seg_x, seg_y, seg_z, seg_feed))
            px, py = seg_x, seg_y

        if compensated:
            # Salida: retrae en G1 (no G0), apaga la corrección y sale al punto de lead-out
            # (1 mm después del end), todo a feed de corte.
            ux, uy = _unit_dir(spec)
            ox, oy = spec.end_x + _COMP_LEAD * ux, spec.end_y + _COMP_LEAD * uy
            lines += [
                f"G1 Z{security:.3f} F{cut_feed:.3f}",
                "G40",
                f"G1 X{ox:.3f} Y{oy:.3f} Z{security:.3f} F{cut_feed:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
                "?%ETK[7]=0",
            ]
            prev_end = (spec.end_x, spec.end_y)
            continue

        if not is_last:
            # Non-last pass: ?%ETK[7]=0 before retract
            lines += [
                "?%ETK[7]=0",
                f"G0 Z{security:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
            ]
        else:
            # Last pass: retract first, ?%ETK[7]=0 after VL7
            lines += [
                f"G0 Z{security:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
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
