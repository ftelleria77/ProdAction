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

import math

from ._machine import (
    MILLING_RETRACT,
    ROUTER_ETK6, ROUTER_ETK18,
    ROUTER_SHF_X, ROUTER_SHF_Y, ROUTER_SHF_Z,
    Z_PARK,
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


def _lead_geometry(
    spec: LineMillingSpec, lead: float, arc_side: str, at_start: bool,
) -> tuple[tuple[float, float], tuple[float, float], str]:
    """Geometría del lead (N026/N027): devuelve (punto exterior, centro del arco, G2|G3).

    lead = (width/2) × radius_multiplier. El centro del arco está a `lead` del punto de anclaje
    (start o end), perpendicular al avance: Automatic≡Right → rot90ccw(û) y G3; Left → rot90cw(û)
    y G2. El punto exterior del approach es centro − lead·û; el del retract es centro + lead·û.
    Para lead tipo Line, el punto exterior es anclaje ∓ lead·û (sin centro).
    """
    ux, uy = _unit_dir(spec)
    if arc_side == "Left":
        nx, ny, g = uy, -ux, "G2"
    else:  # Automatic o Right (byte-idénticos, N027)
        nx, ny, g = -uy, ux, "G3"
    ax_, ay_ = (spec.start_x, spec.start_y) if at_start else (spec.end_x, spec.end_y)
    cx, cy = ax_ + lead * nx, ay_ + lead * ny
    if at_start:
        px, py = cx - lead * ux, cy - lead * uy
    else:
        px, py = cx + lead * ux, cy + lead * uy
    return (px, py), (cx, cy), g


def _multipass_cuts(
    spec: LineMillingSpec, depth: float, security: float, cut_feed: float,
) -> list[str]:
    """Pasadas de la estrategia multipasada (N025). Bidireccional: alterna el sentido y baja en
    el extremo donde quedó. Unidireccional: siempre start→end; entre pasadas retrae y vuelve en
    G1 a feed de corte — retorno a security (Automatic/SafetyHeight) o a z_pasada +
    MILLING_RETRACT (InPiece, sourced de Programaciones.settingsx)."""
    strategy = spec.milling_strategy
    cd = strategy.axial_cutting_depth
    # Terminación (N027 bi_cd4_f2): desbaste en pasos de cd hasta (total − finish), la última
    # del desbaste lleva el resto; después UNA pasada final a la profundidad total.
    finish = getattr(strategy, "axial_finish_cutting_depth", 0.0)
    rough_total = depth - finish
    n_rough = max(1, math.ceil(rough_total / cd - 1e-9))
    depths = [-min(i * cd, rough_total) for i in range(1, n_rough + 1)]
    if finish:
        depths.append(-depth)
    is_uni = type(strategy).__name__.startswith("Unidirectional")
    in_piece = is_uni and getattr(strategy, "connection_mode", "") == "InPiece"
    start = (spec.start_x, spec.start_y)
    end = (spec.end_x, spec.end_y)
    lines: list[str] = []
    pos = start
    for i, z in enumerate(depths):
        lines.append(f"G1 Z{z:.3f} F{cut_feed:.3f}")
        target = end if pos == start else start
        lines.append(_g1_cut(pos[0], pos[1], target[0], target[1], z, cut_feed))
        pos = target
        if i < len(depths) - 1 and is_uni:
            ret = (z + MILLING_RETRACT) if in_piece else security
            lines.append(f"G1 Z{ret:.3f} F{cut_feed:.3f}")
            lines.append(_g1_cut(pos[0], pos[1], start[0], start[1], ret, cut_feed))
            pos = start
    return lines


def _zigzag_cuts(spec: LineMillingSpec, depth: float, cut_feed: float) -> list[str]:
    """ZigZag (N025 pa2/pr3/uh1): baja a Z0 (superficie) y corta EN RAMPA alternando el sentido —
    la ida baja `pasada avance`, la vuelta `pasada retorno` — clavado en (total − último hueco);
    luego la pasada del último hueco a −total y UNA pasada final plana."""
    st = spec.milling_strategy
    pa, pr = st.feed_cutting_depth, st.return_cutting_depth
    uh = st.axial_finish_cutting_depth
    start = (spec.start_x, spec.start_y)
    end = (spec.end_x, spec.end_y)
    lines = [f"G1 Z0.000 F{cut_feed:.3f}"]
    pos, z = start, 0.0
    rough = -(depth - uh)
    while z > rough + 1e-9:
        step = pa if pos == start else pr
        nz = max(z - step, rough)
        target = end if pos == start else start
        lines.append(_g1_cut(pos[0], pos[1], target[0], target[1], nz, cut_feed, prev_z=z))
        pos, z = target, nz
    for nz in (-depth, -depth):   # pasada del último hueco + pasada final plana
        target = end if pos == start else start
        lines.append(_g1_cut(pos[0], pos[1], target[0], target[1], nz, cut_feed, prev_z=z))
        pos, z = target, nz
    return lines


def _g1_cut(prev_x: float, prev_y: float, x: float, y: float, z: float, feed: float,
            prev_z: float | None = None) -> str:
    """G1 de corte de un tramo. Emite los ejes X/Y que se mueven; agrega Z cuando CAMBIA
    (rampa — incluso en diagonal: G1 X Y Z, N028 diag_prof10) o cuando se mueve UN solo eje
    del plano (ahí se repite aunque no cambie; la diagonal plana omite Z — N022 dir_diag)."""
    parts: list[str] = []
    if x != prev_x:
        parts.append(f"X{x:.3f}")
    if y != prev_y:
        parts.append(f"Y{y:.3f}")
    if (prev_z is not None and z != prev_z) or len(parts) == 1:
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
        plunge_feed = geom.feed_default       # bajada G1 Z (el override NO la cambia — N028)
        # Avanz./Rotación por operación (N028 F3_S12K): corte a F=Avanz×1000; S{Rotación}M3.
        cut_feed = spec.feedrate * 1000.0 if spec.feedrate > 0 else geom.feed_std
        spindle_eff = int(spec.spindle) if spec.spindle > 0 else geom.spindle_std
        is_last = (i == n - 1)
        # Corrección de herramienta (side_of_feature Left/Right): el control compensa el radio
        # (SVR) vía G41/G42; las coordenadas del corte NO cambian (N023). El lado es relativo
        # al avance: Left→G41, Right→G42.
        # Corrección CAD (ActivateCNCCorrection=false, sin estrategia): las coordenadas van
        # DESPLAZADAS radio×normal(lado) — izquierda=rot90ccw(û) — sin G41/G42 ni leads (N023 _CAD).
        cad = (not spec.activate_cnc_correction) and spec.milling_strategy is None
        if cad and spec.side_of_feature != "Center":
            r_off = spec.tool_width / 2.0
            ux, uy = _unit_dir(spec)
            nx, ny = (-uy, ux) if spec.side_of_feature == "Left" else (uy, -ux)
            spec = _dc_replace(
                spec,
                start_x=spec.start_x + r_off * nx, start_y=spec.start_y + r_off * ny,
                end_x=spec.end_x + r_off * nx, end_y=spec.end_y + r_off * ny,
            )
        compensated = spec.side_of_feature != "Center" and spec.activate_cnc_correction
        # Leads programables (N026/N027): entrada/salida en línea o arco tangente.
        has_app = spec.approach.is_enabled
        has_ret = spec.retract.is_enabled
        ret_suppresses_g0 = has_ret   # default (Quote); el branch de leads lo ajusta
        lead_app = spec.tool_width / 2.0 * spec.approach.radius_multiplier
        lead_ret = spec.tool_width / 2.0 * spec.retract.radius_multiplier

        if i == 0:
            lines += _atc_header(spec)
            lines += _first_pass_setup(ctx)
        elif spec.tool_name != millings[i - 1].tool_name:
            # CAMBIO DE HERRAMIENTA entre pasadas (N028): shutdown con doble park Z + header ATC
            # nuevo (sin ?%ETK[6], que solo va en el primero) + ?%ETK[13]=1 SIN re-setup de
            # SHF/Or, y posicionamiento a la pasada nueva.
            tn = _cutter_number(spec)
            lines += [
                "MLV=0",
                f"G0 G53 Z{Z_PARK:.3f}",
                "MLV=2",
                "?%ETK[13]=0",
                "?%ETK[18]=0",
                "M5",
                "MLV=0",
                f"G0 G53 Z{Z_PARK:.3f}",
                "MLV=0",
                f"T{tn}",
                "SYN",
                "M06",
                f"?%ETK[9]={tn}",
                f"?%ETK[18]={ROUTER_ETK18}",
                f"S{spindle_eff}M3",
                "G17",
                "MLV=2",
                "?%ETK[13]=1",
                f"G0 X{spec.start_x:.3f} Y{spec.start_y:.3f}",
                f"G0 Z{z_router_approach:.3f}",
            ]
        else:
            # Between passes (misma fresa): G17 + double G0 to new start. Si el husillo efectivo
            # cambia (override Rotación), va S{rpm}M3 ANTES del G17 (N028 F3_S12K).
            assert prev_end is not None
            prev_geom = tool_geometry(millings[i - 1].tool_name)
            prev_spindle = (int(millings[i - 1].spindle) if millings[i - 1].spindle > 0
                            else prev_geom.spindle_std)
            if spindle_eff != prev_spindle:
                lines.append(f"S{spindle_eff}M3")
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
            elif has_app:
                # Aproxima al punto exterior del lead (línea: start − lead·û; arco: fuera del arco).
                if spec.approach.approach_type == "Arc":
                    (apx, apy), _c, _g = _lead_geometry(spec, lead_app, spec.approach.arc_side, True)
                else:
                    ux, uy = _unit_dir(spec)
                    apx, apy = spec.start_x - lead_app * ux, spec.start_y - lead_app * uy
                lines += [f"G0 X{apx:.3f} Y{apy:.3f}", f"G0 Z{z_router_approach:.3f}"]
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
        if spec.milling_strategy is not None:
            # MULTIPASADA en Z (N025): bajada inicial a security en G1 a feed de PLUNGE; después
            # todo (descensos incluidos) a feed de CORTE. Pasadas z_i = -min(i·cd, total): pasos
            # de axial_cutting_depth, la última lleva el resto.
            lines += [
                f"G1 Z{security:.3f} F{plunge_feed:.3f}",
                "?%ETK[7]=4",
            ]
            if type(spec.milling_strategy).__name__.startswith("ZigZag"):
                lines += _zigzag_cuts(spec, depth, cut_feed)
            else:
                lines += _multipass_cuts(spec, depth, security, cut_feed)
            lines.append(f"G1 Z{security:.3f} F{cut_feed:.3f}")
        else:
            if compensated:
                # ETK[7]=4 va ANTES de activar la corrección; el lead-in engancha G41/G42
                # moviéndose al start en el plano de seguridad, y recién ahí baja (plunge).
                lines += [
                    "?%ETK[7]=4",
                    "G41" if spec.side_of_feature == "Left" else "G42",
                    f"G1 X{spec.start_x:.3f} Y{spec.start_y:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                    f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                ]
            elif has_app:
                # Approach programable: ETK[7]=4 antes del plunge; plunge en el punto exterior y
                # lead-in A PROFUNDIDAD hasta el start (recto o arco tangente). La velocidad del
                # lead (speed×1000) aplica al plunge Y al lead; sin speed usa el feed de plunge.
                # speed ≤ 0 (0 o el sentinel -1 del XML) = sin velocidad propia → feed de plunge.
                app_feed = (spec.approach.speed * 1000.0) if spec.approach.speed > 0 else plunge_feed
                down = spec.approach.mode == "Down"   # "En bajada": el lead DESCIENDE (sin plunge)
                lines.append("?%ETK[7]=4")
                if not down:
                    lines.append(f"G1 Z{-depth:.3f} F{app_feed:.3f}")
                if spec.approach.approach_type == "Arc":
                    (apx, apy), (acx, acy), ag = _lead_geometry(
                        spec, lead_app, spec.approach.arc_side, True)
                    zpart = f"Z{-depth:.3f} " if down else ""   # arco helicoidal (N030 baja)
                    lines.append(f"{ag} X{spec.start_x:.3f} Y{spec.start_y:.3f} "
                                 f"{zpart}I{acx:.3f} J{acy:.3f} F{app_feed:.3f}")
                else:
                    ux, uy = _unit_dir(spec)
                    apx, apy = spec.start_x - lead_app * ux, spec.start_y - lead_app * uy
                    lines.append(_g1_cut(apx, apy, spec.start_x, spec.start_y, -depth, app_feed))
            elif cad:
                # CAD: bajada a security a feed de PLUNGE, ETK[7]=4, plunge a feed de CORTE
                # (mismo patrón Z que la multipasada — ambos ActivateCNCCorrection=false).
                lines += [
                    f"G1 Z{security:.3f} F{plunge_feed:.3f}",
                    "?%ETK[7]=4",
                    f"G1 Z{-depth:.3f} F{cut_feed:.3f}",
                ]
            else:
                lines += [
                    f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                    "?%ETK[7]=4",
                ]
            px, py, pz = spec.start_x, spec.start_y, -depth
            for seg_x, seg_y, seg_z, seg_feed in _cut_segments(spec, depth, cut_feed):
                lines.append(_g1_cut(px, py, seg_x, seg_y, seg_z, seg_feed, prev_z=pz))
                px, py, pz = seg_x, seg_y, seg_z
            if cad:
                lines.append(f"G1 Z{security:.3f} F{cut_feed:.3f}")
            if has_ret:
                # Retract programable. "En cota" (Quote): lead-out A PROFUNDIDAD + retracción en
                # G1 (sin G0 Z). "En subida" (Up): el lead-out ASCIENDE a security (arco helicoidal
                # con Z) y el G0 Z del teardown vuelve (N030 sube). La velocidad propia del
                # retract aplica SOLO al lead-out (N030 sp).
                up = spec.retract.mode == "Up"
                ret_feed = (spec.retract.speed * 1000.0) if spec.retract.speed > 0 else cut_feed
                lead_z = security if up else -depth
                if spec.retract.retract_type == "Arc":
                    (rpx, rpy), (rcx, rcy), rg = _lead_geometry(
                        spec, lead_ret, spec.retract.arc_side, False)
                    zpart = f"Z{security:.3f} " if up else ""
                    lines.append(f"{rg} X{rpx:.3f} Y{rpy:.3f} "
                                 f"{zpart}I{rcx:.3f} J{rcy:.3f} F{ret_feed:.3f}")
                else:
                    ux, uy = _unit_dir(spec)
                    rpx, rpy = spec.end_x + lead_ret * ux, spec.end_y + lead_ret * uy
                    lines.append(_g1_cut(spec.end_x, spec.end_y, rpx, rpy, lead_z, ret_feed))
                if not up:
                    lines.append(f"G1 Z{security:.3f} F{cut_feed:.3f}")
                    ret_suppresses_g0 = True
                else:
                    ret_suppresses_g0 = False
            else:
                ret_suppresses_g0 = False

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
            # Non-last pass: ?%ETK[7]=0 va PRIMERO — salvo que la op SIGUIENTE traiga atributos
            # de recorrido (cambios de velocidad/profundidad): ahí Maestro usa el orden de última
            # pasada, con el reset después de los ceros (N028 diag: op2→op3 ETK-primero, op3→op4
            # con atributos ETK-último; 5 transiciones consistentes).
            nxt = millings[i + 1]
            etk_last = bool(nxt.speed_changes or nxt.depth_changes)
            lines += [
                *(() if etk_last else ("?%ETK[7]=0",)),
                f"G0 Z{security:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
                *(("?%ETK[7]=0",) if etk_last else ()),
            ]
        else:
            # Last pass: retract first, ?%ETK[7]=0 after VL7. Con retract programable la
            # retracción ya se emitió en G1 (no va el G0 Z).
            lines += [
                *(() if (has_ret and ret_suppresses_g0) else (f"G0 Z{security:.3f}",)),
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
    g = tool_geometry(spec.tool_name)
    spindle = int(spec.spindle) if spec.spindle > 0 else g.spindle_std
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
