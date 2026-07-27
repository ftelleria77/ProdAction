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

from pgmx.synthesis.milling.arc import ArcSpec
from pgmx.synthesis.milling.polyline import PolylineSpec
from pgmx.synthesis.milling.circle import CircleSpec
from pgmx.synthesis.milling.line import LineSpec

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


def _cutter_number(spec: LineSpec) -> int:
    """Número de fresa: E00N → N (= slot ATC y ETK[9])."""
    return int(spec.tool_name.lstrip("E"))


def _cut_segments(
    spec: LineSpec, depth: float, cut_feed: float,
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
    # Eventos combinados (N028 _coment: 2 rampas + 2 cambios de velocidad en una línea): se ordenan
    # por UPar; una rampa DESCIENDE/ASCIENDE linealmente hasta su profundidad alcanzándola en su
    # punto; un cambio de velocidad aplica DESPUÉS de su punto. El feed de un tramo es el vigente
    # al ENTRAR al tramo.
    events = sorted([(u, "S", v) for u, v in spec.speed_changes]
                    + [(u, "D", v) for u, v in spec.depth_changes])
    segs: list[tuple[float, float, float, float]] = []
    z, feed = -depth, cut_feed
    for upar, kind, val in events:
        mx, my = sx + upar * (ex - sx), sy + upar * (ey - sy)
        nz = -val if kind == "D" else z
        segs.append((mx, my, nz, feed))
        z = nz
        if kind == "S":
            feed = val * 1000.0
    segs.append((ex, ey, z, feed))
    # colapsar tramos duplicados en el mismo punto (evento doble en el mismo UPar)
    return [s_ for i, s_ in enumerate(segs) if i == len(segs) - 1 or (s_[0], s_[1]) != (segs[i+1][0], segs[i+1][1])]


def _lead_geometry(
    spec: LineSpec, lead: float, arc_side: str, at_start: bool,
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


def _mp_lead(spec: LineSpec, lead_spec) -> float:
    """Radio del lead en ARCO en MULTIPASADA/ZigZag (N034/N035): (w/2)×(RM−1) — NO w/2×RM como
    en single-pass. Con RM≤1 da ≤0 y el arco se OMITE (rm1 y rm05: cuerpo pelado). OJO: el lead
    LINEAL sí usa la fórmula single-pass w/2×RM (N035 mp_app_line: 4 con RM=2)."""
    return spec.tool_width / 2.0 * (lead_spec.radius_multiplier - 1.0)


def _mp_arc_side(spec: LineSpec, lead_spec) -> str:
    """Lado efectivo del arco del lead en estrategia: `Automatic` sigue el LADO de la corrección
    cuando hay lado (N035 mp_side_leads: Left→G3 sobre las coordenadas desplazadas); sin lado,
    espejado del single-pass (≡Right→G2, N034)."""
    if lead_spec.arc_side == "Automatic" and spec.side_of_feature != "Center":
        return spec.side_of_feature
    return lead_spec.arc_side


def _mp_lead_arc(
    anchor: tuple[float, float], u: tuple[float, float], lead: float, arc_side: str, at_start: bool,
) -> tuple[tuple[float, float], tuple[float, float], str]:
    """Geometría del lead en multipasada (N034): ESPEJADA respecto del single-pass —
    Automatic≡Right → rot90cw(û) y G2; Left → rot90ccw(û) y G3. El arco de salida se ancla al
    extremo final de la ÚLTIMA pasada, sobre su dirección de avance (cd6: pasadas pares salen
    por el start en −û)."""
    if arc_side == "Left":
        nx, ny, g = -u[1], u[0], "G3"
    else:  # Automatic o Right (byte-idénticos, N034 right)
        nx, ny, g = u[1], -u[0], "G2"
    cx, cy = anchor[0] + lead * nx, anchor[1] + lead * ny
    if at_start:
        px, py = cx - lead * u[0], cy - lead * u[1]
    else:
        px, py = cx + lead * u[0], cy + lead * u[1]
    return (px, py), (cx, cy), g


def _multipass_cuts(
    spec: LineSpec, depth: float, security: float, cut_feed: float,
) -> list[str]:
    """Pasadas de la estrategia multipasada (N025). Bidireccional: alterna el sentido y baja en
    el extremo donde quedó. Unidireccional: siempre start→end; entre pasadas retrae y vuelve en
    G1 a feed de corte — retorno a security (Automatic/SafetyHeight) o a z_pasada +
    MILLING_RETRACT (InPiece, sourced de Programaciones.settingsx).
    Leads programables (N034): arco de entrada tras el descenso a la primera pasada y arco de
    salida tras la última, ambos a feed de CORTE; radio (w/2)×(RM−1), lados espejados."""
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
    ux, uy = _unit_dir(spec)
    lines: list[str] = []
    pos = start
    for i, z in enumerate(depths):
        if i == 0 and spec.approach.is_enabled:
            lines += _strategy_lead_entry(spec, z, start, (ux, uy), cut_feed, security)
        else:
            lines.append(f"G1 Z{z:.3f} F{cut_feed:.3f}")
        target = end if pos == start else start
        lines.append(_g1_cut(pos[0], pos[1], target[0], target[1], z, cut_feed))
        pos = target
        if i < len(depths) - 1 and is_uni:
            ret = (z + MILLING_RETRACT) if in_piece else security
            lines.append(f"G1 Z{ret:.3f} F{cut_feed:.3f}")
            lines.append(_g1_cut(pos[0], pos[1], start[0], start[1], ret, cut_feed))
            pos = start
    if spec.retract.is_enabled:
        sign = 1.0 if pos == end else -1.0
        lines += _strategy_lead_exit(spec, depths[-1], pos, (sign * ux, sign * uy), cut_feed)
    return lines, pos


def _strategy_lead_entry(
    spec: LineSpec,
    first_z: float,
    start: tuple[float, float],
    u: tuple[float, float],
    cut_feed: float,
    security: float,
) -> list[str]:
    """Entrada del lead en ESTRATEGIA (N034/N035/N036): reemplaza el descenso inicial a la
    primera pasada (o superficie en ZigZag). Arco En cota: Z + arco (RM−1); Arco En bajada:
    plunge a (z+lead) y rampa recta; Lineal En cota: Z + línea w/2×RM; Lineal En bajada: SIN
    plunge, la línea desciende desde security. Todo a feed de corte (efectivo)."""
    ux, uy = u
    lead = _mp_lead(spec, spec.approach)
    lead_type = spec.approach.approach_type
    down = spec.approach.mode == "Down"
    if lead_type == "Arc" and down and lead > 1e-9:
        return [
            f"G1 Z{first_z + lead:.3f} F{cut_feed:.3f}",
            _g1_cut(start[0] - lead * ux, start[1] - lead * uy,
                    start[0], start[1], first_z, cut_feed, prev_z=first_z + lead),
        ]
    if lead_type == "Line":
        line_lead = spec.tool_width / 2.0 * spec.approach.radius_multiplier
        apx, apy = start[0] - line_lead * ux, start[1] - line_lead * uy
        if down:
            # N036 mp/side_app_line_down: la línea del lead DESCIENDE desde security a z1.
            return [_g1_cut(apx, apy, start[0], start[1], first_z, cut_feed, prev_z=security)]
        return [
            f"G1 Z{first_z:.3f} F{cut_feed:.3f}",
            _g1_cut(apx, apy, start[0], start[1], first_z, cut_feed, prev_z=first_z),
        ]
    lines = [f"G1 Z{first_z:.3f} F{cut_feed:.3f}"]
    if lead > 1e-9:
        _p, (acx, acy), ag = _mp_lead_arc(start, u, lead, _mp_arc_side(spec, spec.approach), True)
        lines.append(f"{ag} X{start[0]:.3f} Y{start[1]:.3f} "
                     f"I{acx:.3f} J{acy:.3f} F{cut_feed:.3f}")
    return lines


def _strategy_lead_exit(
    spec: LineSpec,
    last_z: float,
    pos: tuple[float, float],
    u: tuple[float, float],
    cut_feed: float,
) -> list[str]:
    """Salida del lead en ESTRATEGIA, anclada al extremo final de la ÚLTIMA pasada sobre su
    dirección. Arco En cota (RM−1); Arco En subida: rampa recta ascendente (+lead); Lineal:
    línea plana w/2×RM a profundidad. La velocidad propia del retract aplica SOLO acá (y a la
    retracción que sigue) — N036 mp_ret_sp."""
    ret_feed = _strategy_ret_feed(spec, cut_feed)
    lead = _mp_lead(spec, spec.retract)
    if spec.retract.retract_type == "Line":
        line_lead = spec.tool_width / 2.0 * spec.retract.radius_multiplier
        return [_g1_cut(pos[0], pos[1], pos[0] + line_lead * u[0], pos[1] + line_lead * u[1],
                        last_z, ret_feed, prev_z=last_z)]
    if lead <= 1e-9:
        return []
    if spec.retract.mode == "Up":
        return [_g1_cut(pos[0], pos[1], pos[0] + lead * u[0], pos[1] + lead * u[1],
                        last_z + lead, ret_feed, prev_z=last_z)]
    (rpx, rpy), (rcx, rcy), rg = _mp_lead_arc(pos, u, lead,
                                              _mp_arc_side(spec, spec.retract), False)
    return [f"{rg} X{rpx:.3f} Y{rpy:.3f} I{rcx:.3f} J{rcy:.3f} F{ret_feed:.3f}"]


def _strategy_ret_feed(spec: LineSpec, cut_feed: float) -> float:
    """Feed del lead-out y de la retracción final en estrategia: la velocidad propia del
    retract SOLO aplica ahí (no inunda el cuerpo como la del approach) — N036 mp_ret_sp."""
    if spec.retract.is_enabled and spec.retract.speed > 0:
        return spec.retract.speed * 1000.0
    return cut_feed


def _zigzag_cuts(spec: LineSpec, depth: float, cut_feed: float) -> list[str]:
    """ZigZag (N025 pa2/pr3/uh1): baja a Z0 (superficie) y corta EN RAMPA alternando el sentido —
    la ida baja `pasada avance`, la vuelta `pasada retorno` — clavado en (total − último hueco);
    luego la pasada del último hueco a −total y UNA pasada final plana."""
    st = spec.milling_strategy
    pa, pr = st.feed_cutting_depth, st.return_cutting_depth
    uh = st.axial_finish_cutting_depth
    start = (spec.start_x, spec.start_y)
    end = (spec.end_x, spec.end_y)
    ux, uy = _unit_dir(spec)
    if spec.approach.is_enabled:
        # Leads en ZigZag (N035/N036): mismas reglas que multipasada, ancladas en la SUPERFICIE
        # (Z0, la entrada del zigzag) — arco (RM−1) espejado, línea w/2×RM, bajada en rampa.
        lines = _strategy_lead_entry(spec, 0.0, start, (ux, uy), cut_feed, spec.security_plane)
    else:
        lines = [f"G1 Z0.000 F{cut_feed:.3f}"]
    pos, z = start, 0.0
    rough = -(depth - uh)
    while z > rough + 1e-9:
        step = pa if pos == start else pr
        nz = max(z - step, rough)
        target = end if pos == start else start
        lines.append(_g1_cut(pos[0], pos[1], target[0], target[1], nz, cut_feed, prev_z=z))
        pos, z = target, nz
    # Con último hueco > 0: pasada del hueco a −total + UNA pasada final plana. Con uh = 0
    # (N036 zz_uh0, regenerado en Maestro): las pasadas ya llegaron a −total → UNA sola plana.
    for nz in ((-depth, -depth) if uh > 1e-9 else (-depth,)):
        target = end if pos == start else start
        lines.append(_g1_cut(pos[0], pos[1], target[0], target[1], nz, cut_feed, prev_z=z))
        pos, z = target, nz
    if spec.retract.is_enabled:
        sign = 1.0 if pos == end else -1.0
        lines += _strategy_lead_exit(spec, -depth, pos, (sign * ux, sign * uy), cut_feed)
    return lines, pos


def _g1_cut(prev_x: float, prev_y: float, x: float, y: float, z: float, feed: float,
            prev_z: float | None = None) -> str:
    """G1 de corte de un tramo. Emite los ejes X/Y que se mueven; agrega Z cuando CAMBIA
    (rampa — incluso en diagonal: G1 X Y Z, N028 diag_prof10) o cuando se mueve UN solo eje
    del plano (ahí se repite aunque no cambie; la diagonal plana omite Z — N022 dir_diag)."""
    # Comparación con tolerancia sub-micrón: colapsa el ruido de punto flotante (p.ej. el
    # endpoint de un arco reconstruido por ángulos que alimenta una recta a eje — N041 lar_cw)
    # sin afectar geometría real (todo mm significativo difiere ≥0.001).
    parts: list[str] = []
    if abs(x - prev_x) > 1e-6:
        parts.append(f"X{x:.3f}")
    if abs(y - prev_y) > 1e-6:
        parts.append(f"Y{y:.3f}")
    if (prev_z is not None and abs(z - prev_z) > 1e-6) or len(parts) == 1:
        parts.append(f"Z{z:.3f}")
    return "G1 " + " ".join(parts) + f" F{feed:.3f}"


# Distancia de entrada/salida de la corrección (lead-in/out): 1 mm antes del start / después del
# end sobre la dirección de avance, donde se activa G41/G42 y se desactiva G40. Constante del
# ciclo de Maestro (N023: idéntica con E004 w=4 y E001 w=18.36 → no depende de la herramienta).
_COMP_LEAD: float = 1.0


def _unit_dir(spec: LineSpec) -> tuple[float, float]:
    dx, dy = spec.end_x - spec.start_x, spec.end_y - spec.start_y
    length = (dx * dx + dy * dy) ** 0.5
    return (dx / length, dy / length)


def _arc_tangent(px: float, py: float, cx: float, cy: float, g: str) -> tuple[float, float]:
    """Tangente unitaria del MOVIMIENTO en el punto P de un arco G2/G3 (sentido de recorrido)."""
    rx, ry = px - cx, py - cy
    r = (rx * rx + ry * ry) ** 0.5
    if g == "G3":   # CCW
        return (-ry / r, rx / r)
    return (ry / r, -rx / r)


def _comp_auto_arc_side(spec: LineSpec) -> str:
    """Con corrección G41/G42, el lado `Automatic` del lead elige el arco del lado LIBRE (el
    opuesto al material/compensación): G41 (Left) → arco derecha/G3; G42 (Right) → arco
    izquierda/G2. (N029 side_l_leads: G41+G3; inv_side_l_app: G42+G2.)"""
    return "Right" if spec.side_of_feature == "Left" else "Left"


def render_router(millings: list[LineSpec], ctx: PieceCtx) -> list[str]:
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
        svr = spec.tool_width / 2.0 + getattr(spec, "side_offset", 0.0)
        # Corrección de longitud (IsPrecise): acorta el recorrido el RADIO de la fresa en ambos
        # extremos (centro en [start+r·dir, end−r·dir] → el filo cubre justo el segmento). N023
        # _long: E004 ±2, E001 ±9.18. El resto del render usa los extremos ya corregidos (approach,
        # lead-in/out de la compensación y corte).
        if getattr(spec, "is_precise", False):
            r = spec.tool_width / 2.0
            ux, uy = _unit_dir(spec)
            spec = _dc_replace(
                spec,
                start_x=spec.start_x + r * ux, start_y=spec.start_y + r * uy,
                end_x=spec.end_x - r * ux, end_y=spec.end_y - r * uy,
            )
        plunge_feed = geom.feed_default       # bajada G1 Z (el override NO la cambia — N028)
        # Avanz./Rotación por operación (N028 F3_S12K): corte a F=Avanz×1000; S{Rotación}M3.
        _feedrate = getattr(spec, "feedrate", 0.0)
        cut_feed = _feedrate * 1000.0 if _feedrate > 0 else geom.feed_std
        # Velocidad del approach en ESTRATEGIA (N035 mp_app_sp + N036 zz_app_sp): pisa el feed
        # de TODO el cuerpo — pasadas, descensos e INCLUSO la bajada inicial a security (el
        # zz_app_sp con speed=3≠default lo discrimina: G1 Z20 F3000). La del retract NO (solo
        # el lead-out, mp_ret_sp).
        if (spec.milling_strategy is not None and spec.approach.is_enabled
                and spec.approach.speed > 0):
            cut_feed = spec.approach.speed * 1000.0
            plunge_feed = cut_feed
        _spindle = getattr(spec, "spindle", 0.0)
        spindle_eff = int(_spindle) if _spindle > 0 else geom.spindle_std
        is_last = (i == n - 1)
        # Corrección de herramienta (side_of_feature Left/Right): el control compensa el radio
        # (SVR) vía G41/G42; las coordenadas del corte NO cambian (N023). El lado es relativo
        # al avance: Left→G41, Right→G42.
        # Corrección CAD (ActivateCNCCorrection=false, sin estrategia): las coordenadas van
        # DESPLAZADAS radio×normal(lado) — izquierda=rot90ccw(û) — sin G41/G42 ni leads (N023 _CAD).
        # El MISMO desplazamiento aplica a la multipasada con lado (N029 mp_side_l: la estrategia
        # fuerza ACC=false y las pasadas corren en las coordenadas desplazadas, sin G41).
        # CÍRCULO (N038/N039), ARCO SUELTO (N040) y POLILÍNEA (N041/N042/N043): dispatch propio;
        # los bloques de línea no los tocan (el desplazamiento CAD de la POLILÍNEA es por-borde
        # con arcos de esquina — _poly_cad_moves — no el shift único de la línea).
        is_circle = isinstance(spec, CircleSpec)
        is_arc = isinstance(spec, ArcSpec)
        is_poly = isinstance(spec, PolylineSpec)
        _acc = getattr(spec, "activate_cnc_correction", True)
        cad = (not _acc) and spec.milling_strategy is None
        if (not _acc) and spec.side_of_feature != "Center" and not (is_circle or is_arc or is_poly):
            r_off = spec.tool_width / 2.0
            ux, uy = _unit_dir(spec)
            nx, ny = (-uy, ux) if spec.side_of_feature == "Left" else (uy, -ux)
            spec = _dc_replace(
                spec,
                start_x=spec.start_x + r_off * nx, start_y=spec.start_y + r_off * ny,
                end_x=spec.end_x + r_off * nx, end_y=spec.end_y + r_off * ny,
            )
        compensated = spec.side_of_feature != "Center" and _acc
        # Leads programables (N026/N027): entrada/salida en línea o arco tangente.
        has_app = spec.approach.is_enabled
        has_ret = spec.retract.is_enabled
        # Invertir trabajo (N023 _invert): swap start↔end y FLIP del lado (el lado es físico,
        # relativo a la pieza: Left con avance invertido emite G42).
        if getattr(spec, "invert_work", False):
            flip = {"Left": "Right", "Right": "Left"}.get(spec.side_of_feature, "Center")
            spec = _dc_replace(
                spec, start_x=spec.end_x, start_y=spec.end_y,
                end_x=spec.start_x, end_y=spec.start_y, side_of_feature=flip)
        ret_suppresses_g0 = has_ret   # default (Quote); el branch de leads lo ajusta
        lead_app = spec.tool_width / 2.0 * spec.approach.radius_multiplier
        lead_ret = spec.tool_width / 2.0 * spec.retract.radius_multiplier

        # Lead programable + compensación (N029 side_l_leads / N035): el lead se emite en
        # coordenadas de CONTORNO con G41/G42 activo; el 1 mm de la corrección se ancla al punto
        # EXTERIOR del lead, sobre su TANGENTE de entrada (arco) o sobre û (línea). El lado
        # explícito del arco se IGNORA con compensación (N035 arcleft): siempre el lado libre.
        # La velocidad propia aplica a plunge+lead (semántica N026); la activación va a plunge.
        comp_app = compensated and has_app and not is_circle and not is_arc and not is_poly
        if comp_app:
            comp_app_feed = ((spec.approach.speed * 1000.0) if spec.approach.speed > 0
                             else plunge_feed)
            if spec.approach.approach_type == "Line":
                _ux, _uy = _unit_dir(spec)
                capx = spec.start_x - lead_app * _ux
                capy = spec.start_y - lead_app * _uy
                catx, caty, cag = _ux, _uy, None
            else:
                (capx, capy), (cacx, cacy), cag = _lead_geometry(
                    spec, lead_app, _comp_auto_arc_side(spec), True)
                catx, caty = _arc_tangent(capx, capy, cacx, cacy, cag)

        # Punto de APROXIMACIÓN de la pasada (el G0 inicial y el destino del triple G0 de las
        # transiciones — N036 two_leads: apunta al punto exterior del lead, no al start).
        # CÍRCULO (N038/N039): entra por el ESTE (cx+r, cy); con leads/compensación, las mismas
        # reglas de línea con û = TANGENTE de entrada ((0,±1) según el sentido de giro).
        if is_arc:
            # ARCO SUELTO (N040): entra por el START real del arco (baseline; combos → guarda).
            entry_xy = (spec.start_x, spec.start_y)
        elif is_poly:
            # POLILÍNEA (N041 baseline / N042 corrección+entrada / N043 CAD): el punto de
            # aproximación sale de _poly_entry_xy (arranque, 1 mm antes con corrección,
            # exterior del arco, o el fin del último borde offseteado con CAD).
            entry_xy = _poly_entry_xy(spec, compensated, has_app, lead_app, cad)
        elif is_circle:
            entry_xy = _circle_entry_xy(spec, compensated, has_app, lead_app)
        elif comp_app:
            entry_xy = (capx - _COMP_LEAD * catx, capy - _COMP_LEAD * caty)
        elif compensated:
            ux, uy = _unit_dir(spec)
            entry_xy = (spec.start_x - _COMP_LEAD * ux, spec.start_y - _COMP_LEAD * uy)
        elif has_app:
            # Punto exterior del lead (línea: start − lead·û; arco: fuera del arco). En
            # estrategia y en CAD (N034/N035/N036): arco → radio (w/2)×(RM−1) espejado (≤0 lo
            # omite); Lineal → w/2×RM sobre û; En bajada → exterior a lead·û del start.
            ux, uy = _unit_dir(spec)
            if spec.milling_strategy is not None or cad:
                mp_lead = _mp_lead(spec, spec.approach)
                if spec.approach.approach_type == "Line":
                    line_lead = spec.tool_width / 2.0 * spec.approach.radius_multiplier
                    entry_xy = (spec.start_x - line_lead * ux, spec.start_y - line_lead * uy)
                elif mp_lead <= 1e-9:
                    entry_xy = (spec.start_x, spec.start_y)
                elif spec.approach.mode == "Down":
                    entry_xy = (spec.start_x - mp_lead * ux, spec.start_y - mp_lead * uy)
                else:
                    entry_xy, _c, _g = _mp_lead_arc(
                        (spec.start_x, spec.start_y), (ux, uy), mp_lead,
                        _mp_arc_side(spec, spec.approach), True)
            elif spec.approach.approach_type == "Arc":
                entry_xy, _c, _g = _lead_geometry(spec, lead_app, spec.approach.arc_side, True)
            else:
                entry_xy = (spec.start_x - lead_app * ux, spec.start_y - lead_app * uy)
        else:
            entry_xy = (spec.start_x, spec.start_y)

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
                f"G0 X{entry_xy[0]:.3f} Y{entry_xy[1]:.3f}",
                f"G0 Z{z_router_approach:.3f}",
            ]
        else:
            # Between passes (misma fresa): G17 + double G0 to new start. Si el husillo efectivo
            # cambia (override Rotación), va S{rpm}M3 ANTES del G17 (N028 F3_S12K).
            assert prev_end is not None
            prev_geom = tool_geometry(millings[i - 1].tool_name)
            _prev_sp = getattr(millings[i - 1], "spindle", 0.0)
            prev_spindle = int(_prev_sp) if _prev_sp > 0 else prev_geom.spindle_std
            if spindle_eff != prev_spindle:
                lines.append(f"S{spindle_eff}M3")
            lines += [
                "G17",
                "MLV=2",
                f"G0 X{prev_end[0]:.3f} Y{prev_end[1]:.3f} Z{z_router_approach:.3f}",
                f"G0 X{entry_xy[0]:.3f} Y{entry_xy[1]:.3f} Z{z_router_approach:.3f}",
                f"G0 X{entry_xy[0]:.3f} Y{entry_xy[1]:.3f} Z{z_router_approach:.3f}",
            ]

        # First pass: explicit approach; subsequent passes already positioned by triple G0
        if i == 0:
            lines += [
                f"G0 X{entry_xy[0]:.3f} Y{entry_xy[1]:.3f}",
                f"G0 Z{z_router_approach:.3f}",
            ]
        lines += [
            "D1",
            f"SVL {svl:.3f}",
            f"VL6={svl:.3f}",
        ]
        if svr != 0.0:
            lines += [f"SVR {svr:.3f}", f"VL7={svr:.3f}"]
        if is_arc:
            # ARCO SUELTO (N040, 10/10): plunge estilo línea y UN G3 (CCW) / G2 (CW) desde el
            # start al end con I/J ABSOLUTOS al centro. Pasante = -(espesor+extra).
            arc_g = "G3" if spec.winding == "CounterClockwise" else "G2"
            lines += [
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                "?%ETK[7]=4",
                f"{arc_g} X{spec.end_x:.3f} Y{spec.end_y:.3f} "
                f"I{spec.center_x:.3f} J{spec.center_y:.3f} F{cut_feed:.3f}",
            ]
            ret_suppresses_g0 = False
        elif is_poly:
            # POLILÍNEA (N041 baseline / N042 corrección+entrada): cuerpo estilo línea con la
            # cadena de segmentos. Corrección = G41/G42 + lead-in sobre el 1er segmento y
            # lead-out sobre el último; segmentos NOMINALES (el control empalma las esquinas).
            # CAD (N043 estilo B): polígono OFFSETEADO + arcos de esquina, sin G41 ni leads.
            if cad:
                body, ret_suppresses_g0, poly_end = _poly_cad_body(
                    spec, depth, security, plunge_feed, cut_feed, has_app, has_ret)
            else:
                body, ret_suppresses_g0, poly_end = _poly_body(
                    spec, depth, security, plunge_feed, cut_feed, compensated,
                    has_app, has_ret, lead_app, lead_ret)
            lines += body
            if compensated:
                lines += [
                    "D0",
                    "SVL 0.000",
                    "VL6=0.000",
                    *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
                    "?%ETK[7]=0",
                ]
                if not is_last:
                    lines.append("?%ETK[7]=0")
                prev_end = poly_end
                continue
        elif spec.milling_strategy is not None and not is_circle:
            # MULTIPASADA en Z (N025): bajada inicial a security en G1 a feed de PLUNGE; después
            # todo (descensos incluidos) a feed de CORTE. Pasadas z_i = -min(i·cd, total): pasos
            # de axial_cutting_depth, la última lleva el resto.
            lines += [
                f"G1 Z{security:.3f} F{plunge_feed:.3f}",
                "?%ETK[7]=4",
            ]
            if type(spec.milling_strategy).__name__.startswith("ZigZag"):
                cuts, strategy_end = _zigzag_cuts(spec, depth, cut_feed)
            else:
                cuts, strategy_end = _multipass_cuts(spec, depth, security, cut_feed)
            lines += cuts
            # La retracción final va al feed del retract si tiene velocidad propia (mp_ret_sp).
            lines.append(f"G1 Z{security:.3f} F{_strategy_ret_feed(spec, cut_feed):.3f}")
            # Los leads de multipasada retraen dentro del patrón (G1 Z + G0 Z del teardown
            # SIEMPRE presentes — N034 ret_only); no suprimen el G0 Z como el retract single-pass.
            ret_suppresses_g0 = False
        elif is_circle:
            body, ret_suppresses_g0, circle_out = _circle_body(
                spec, depth, security, plunge_feed, cut_feed, compensated, has_app, has_ret,
                lead_app, lead_ret)
            lines += body
            if compensated:
                # Salida compensada del círculo (mismo patrón que la línea): el cuerpo ya emitió
                # G40 y el 1 mm de salida; teardown propio + reset extra si no es la última.
                lines += [
                    "D0",
                    "SVL 0.000",
                    "VL6=0.000",
                    *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
                    "?%ETK[7]=0",
                ]
                if not is_last:
                    lines.append("?%ETK[7]=0")
                prev_end = circle_out
                continue
        else:
            if compensated:
                # ETK[7]=4 va ANTES de activar la corrección; el lead-in engancha G41/G42
                # moviéndose al start en el plano de seguridad, y recién ahí baja (plunge).
                # Con approach programable (arco): el 1 mm va sobre la tangente hasta el punto
                # exterior, plunge ahí, y el arco (a feed de plunge) desemboca en el start.
                lines += [
                    "?%ETK[7]=4",
                    "G41" if spec.side_of_feature == "Left" else "G42",
                ]
                if comp_app:
                    lines.append(f"G1 X{capx:.3f} Y{capy:.3f} Z{security:.3f} F{plunge_feed:.3f}")
                    if cag is None:
                        # Lead LINEAL con G41 (N035 side_app_line): plunge en el exterior y
                        # lead-in recto a profundidad. "En bajada" (N036 side_app_line_down):
                        # SIN plunge — la línea del lead DESCIENDE desde security.
                        if spec.approach.mode == "Down":
                            lines.append(_g1_cut(capx, capy, spec.start_x, spec.start_y, -depth,
                                                 comp_app_feed, prev_z=security))
                        else:
                            lines += [
                                f"G1 Z{-depth:.3f} F{comp_app_feed:.3f}",
                                _g1_cut(capx, capy, spec.start_x, spec.start_y, -depth,
                                        comp_app_feed, prev_z=-depth),
                            ]
                    elif spec.approach.mode == "Down":
                        # "En bajada" con G41 (N035 side_app_down): SIN plunge — arco helicoidal.
                        lines.append(f"{cag} X{spec.start_x:.3f} Y{spec.start_y:.3f} "
                                     f"Z{-depth:.3f} I{cacx:.3f} J{cacy:.3f} "
                                     f"F{comp_app_feed:.3f}")
                    else:
                        lines += [
                            f"G1 Z{-depth:.3f} F{comp_app_feed:.3f}",
                            f"{cag} X{spec.start_x:.3f} Y{spec.start_y:.3f} "
                            f"I{cacx:.3f} J{cacy:.3f} F{comp_app_feed:.3f}",
                        ]
                else:
                    lines += [
                        f"G1 X{spec.start_x:.3f} Y{spec.start_y:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                        f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                    ]
            elif has_app and not cad:
                # Approach programable: ETK[7]=4 antes del plunge; plunge en el punto exterior y
                # lead-in A PROFUNDIDAD hasta el start (recto o arco tangente). La velocidad del
                # lead (speed×1000) aplica al plunge Y al lead; sin speed usa el feed de plunge.
                # speed ≤ 0 (0 o el sentinel -1 del XML) = sin velocidad propia → feed de plunge.
                app_feed = (spec.approach.speed * 1000.0) if spec.approach.speed > 0 else plunge_feed
                down = spec.approach.mode == "Down"   # "En bajada": el lead DESCIENDE (sin plunge)
                assert not cad  # CAD + leads va por la rama cad (estilo estrategia, N036)
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
                # Con leads (N036 cad_leads): reglas de ESTRATEGIA — arco (RM−1), Automatic
                # sigue el lado — sobre las coordenadas desplazadas.
                lines += [
                    f"G1 Z{security:.3f} F{plunge_feed:.3f}",
                    "?%ETK[7]=4",
                ]
                if has_app:
                    lines += _strategy_lead_entry(
                        spec, -depth, (spec.start_x, spec.start_y), _unit_dir(spec),
                        cut_feed, security)
                else:
                    lines.append(f"G1 Z{-depth:.3f} F{cut_feed:.3f}")
            else:
                lines += [
                    f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                    "?%ETK[7]=4",
                ]
            px, py, pz = spec.start_x, spec.start_y, -depth
            last_feed = cut_feed
            for seg_x, seg_y, seg_z, seg_feed in _cut_segments(spec, depth, cut_feed):
                lines.append(_g1_cut(px, py, seg_x, seg_y, seg_z, seg_feed, prev_z=pz))
                px, py, pz = seg_x, seg_y, seg_z
                last_feed = seg_feed
            if cad:
                if has_ret:
                    ux, uy = _unit_dir(spec)
                    lines += _strategy_lead_exit(
                        spec, -depth, (spec.end_x, spec.end_y), (ux, uy), cut_feed)
                # La retracción sale al feed VIGENTE tras los cambios (N036 cad_vel/mp_vel: F1000).
                lines.append(f"G1 Z{security:.3f} F{last_feed:.3f}")
            if has_ret and not compensated and not cad:
                # Retract programable. "En cota" (Quote): lead-out A PROFUNDIDAD + retracción en
                # G1 (sin G0 Z). "En subida" (Up): el lead-out ASCIENDE a security (arco helicoidal
                # con Z) y el G0 Z del teardown vuelve (N030 sube). La velocidad propia del
                # retract aplica SOLO al lead-out (N030 sp). Con G41/G42 el lead-out se emite en
                # el bloque de salida compensada (abajo); con CAD, en su propia rama (arriba).
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
            # (1 mm después del end), todo a feed de corte. Con retract programable (arco): el
            # arco de salida va A PROFUNDIDAD antes de retraer — o ASCIENDE con Z en el arco si
            # el modo es "En subida" (N035 side_ret_up: sin G1 Z aparte) — y el 1 mm del G40
            # sale sobre la tangente desde el punto exterior del arco (N029 side_l_leads).
            comp_ret_up = has_ret and spec.retract.mode == "Up"
            if has_ret:
                comp_ret_feed = ((spec.retract.speed * 1000.0) if spec.retract.speed > 0
                                 else last_feed)
                if spec.retract.retract_type == "Line":
                    # Alejamiento LINEAL con G41 (N036 side_ret_line): línea a profundidad más
                    # allá del end (w/2×RM); el 1 mm del G40 sigue sobre û desde su extremo.
                    ux, uy = _unit_dir(spec)
                    crpx = spec.end_x + lead_ret * ux
                    crpy = spec.end_y + lead_ret * uy
                    lines.append(_g1_cut(spec.end_x, spec.end_y, crpx, crpy, -depth,
                                         comp_ret_feed, prev_z=-depth))
                    crtx, crty = ux, uy
                else:
                    (crpx, crpy), (crcx, crcy), crg = _lead_geometry(
                        spec, lead_ret, _comp_auto_arc_side(spec), False)
                    zpart = f"Z{security:.3f} " if comp_ret_up else ""
                    lines.append(f"{crg} X{crpx:.3f} Y{crpy:.3f} "
                                 f"{zpart}I{crcx:.3f} J{crcy:.3f} F{comp_ret_feed:.3f}")
                    crtx, crty = _arc_tangent(crpx, crpy, crcx, crcy, crg)
                ox, oy = crpx + _COMP_LEAD * crtx, crpy + _COMP_LEAD * crty
            else:
                ux, uy = _unit_dir(spec)
                ox, oy = spec.end_x + _COMP_LEAD * ux, spec.end_y + _COMP_LEAD * uy
            # La retracción y el 1 mm del G40 salen al feed VIGENTE tras los cambios de
            # velocidad (N036 side_vel: F1000).
            lines += [
                *(() if comp_ret_up else (f"G1 Z{security:.3f} F{last_feed:.3f}",)),
                "G40",
                f"G1 X{ox:.3f} Y{oy:.3f} Z{security:.3f} F{last_feed:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
                "?%ETK[7]=0",
            ]
            if not is_last:
                # Transición compensada → siguiente pasada (N036 two_side): un ?%ETK[7]=0
                # EXTRA tras el teardown de la salida (el G17/MLV=2/triple G0 lo emite la
                # iteración siguiente, anclada en el punto del G40).
                lines.append("?%ETK[7]=0")
            prev_end = (ox, oy)
            continue

        if not is_last:
            # Non-last pass: ?%ETK[7]=0 va PRIMERO — salvo que la op SIGUIENTE traiga atributos
            # de recorrido (cambios de velocidad/profundidad): ahí Maestro usa el orden de última
            # pasada, con el reset después de los ceros (N028 diag: op2→op3 ETK-primero, op3→op4
            # con atributos ETK-último; 5 transiciones consistentes).
            nxt = millings[i + 1]
            # ETK-último ⇔ la op ENTRANTE tiene override de Avanz./Rotación (8 transiciones de
            # N028 consistentes; la hipótesis previa por-atributos cayó con _coment).
            etk_last = (nxt.tool_name != spec.tool_name
                        and (getattr(nxt, "feedrate", 0) > 0 or getattr(nxt, "spindle", 0) > 0))
            # Op con leads C.N. (ETK[7]=4 movido antes del plunge): el teardown lleva ADEMÁS un
            # ?%ETK[7]=0 extra al final, antes de la transición (N036 two_leads — doble reset,
            # como la salida compensada de two_side).
            leads_style = (has_app and spec.milling_strategy is None
                           and _acc)
            lines += [
                *(() if etk_last else ("?%ETK[7]=0",)),
                f"G0 Z{security:.3f}",
                "D0",
                "SVL 0.000",
                "VL6=0.000",
                *(("SVR 0.000", "VL7=0.000") if svr != 0.0 else ()),
                *(("?%ETK[7]=0",) if (etk_last or leads_style) else ()),
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

        # Ancla del triple G0 de la transición siguiente: la última posición FÍSICA — el extremo
        # final de la última pasada en estrategia (N036 two_mp), el end en single-pass; el
        # CÍRCULO cierra donde empezó (N038 two: prev = su punto de entrada).
        if is_circle:
            prev_end = circle_out
        elif is_arc:
            prev_end = (spec.end_x, spec.end_y)
        elif is_poly:
            prev_end = poly_end
        else:
            prev_end = (strategy_end if spec.milling_strategy is not None
                        else (spec.end_x, spec.end_y))

    return lines


def _circle_frame(spec) -> tuple[tuple[float, float], tuple[float, float], str]:
    """Marco del círculo (N038/N039): entra por el ESTE (cx+r, cy); la TANGENTE de entrada es
    (0,+1) en antihorario y (0,−1) en horario; el 360° se emite G3/G2 según el sentido."""
    ccw = spec.winding == "CounterClockwise"
    east = (spec.center_x + spec.radius, spec.center_y)
    t_in = (0.0, 1.0) if ccw else (0.0, -1.0)
    return east, t_in, ("G3" if ccw else "G2")


def _circle_lead_arc(spec, anchor, u, at_start):
    """Lead en arco single-pass sobre círculo (N039 app_arc / side_l_leads): la regla de LÍNEA
    con û = tangente — Automatic ≡ Right → rot90ccw(û)/G3; con compensación, el lado LIBRE
    (side Right → rot90cw/G2)."""
    lead = spec.tool_width / 2.0 * (spec.approach if at_start else spec.retract).radius_multiplier
    if spec.side_of_feature == "Right":
        nx, ny, g = u[1], -u[0], "G2"
    else:
        nx, ny, g = -u[1], u[0], "G3"
    cx, cy = anchor[0] + lead * nx, anchor[1] + lead * ny
    if at_start:
        px, py = cx - lead * u[0], cy - lead * u[1]
    else:
        px, py = cx + lead * u[0], cy + lead * u[1]
    return (px, py), (cx, cy), g


def _circle_halves(spec, g, cut_feed, z_mid=None, z_end=None, j_off=0.0) -> list[str]:
    """Dos semicírculos este→oeste→este con I/J ABSOLUTOS al centro. Con z (helicoidal): la Z
    va antes de I/J y el centro J se descentra ±(radio3D − r) (N039 heli: J100.017/J99.983)."""
    east_x = spec.center_x + spec.radius
    west_x = spec.center_x - spec.radius
    if z_mid is None:
        return [
            f"{g} X{west_x:.3f} Y{spec.center_y:.3f} "
            f"I{spec.center_x:.3f} J{spec.center_y:.3f} F{cut_feed:.3f}",
            f"{g} X{east_x:.3f} Y{spec.center_y:.3f} "
            f"I{spec.center_x:.3f} J{spec.center_y:.3f} F{cut_feed:.3f}",
        ]
    return [
        f"{g} X{west_x:.3f} Y{spec.center_y:.3f} Z{z_mid:.3f} "
        f"I{spec.center_x:.3f} J{spec.center_y + j_off:.3f} F{cut_feed:.3f}",
        f"{g} X{east_x:.3f} Y{spec.center_y:.3f} Z{z_end:.3f} "
        f"I{spec.center_x:.3f} J{spec.center_y - j_off:.3f} F{cut_feed:.3f}",
    ]


def _circle_entry_xy(spec, compensated: bool, has_app: bool, lead_app: float):
    east, t_in, _g = _circle_frame(spec)
    if compensated and has_app:
        (apx, apy), (acx, acy), ag = _circle_lead_arc(spec, east, t_in, True)
        tx, ty = _arc_tangent(apx, apy, acx, acy, ag)
        return (apx - _COMP_LEAD * tx, apy - _COMP_LEAD * ty)
    if compensated:
        return (east[0] - _COMP_LEAD * t_in[0], east[1] - _COMP_LEAD * t_in[1])
    if has_app and spec.milling_strategy is not None:
        mp_lead = _mp_lead(spec, spec.approach)
        if mp_lead <= 1e-9:
            return east
        exterior, _c, _g2 = _mp_lead_arc(east, t_in, mp_lead, "Automatic", True)
        return exterior
    if has_app:
        if spec.approach.approach_type == "Arc":
            exterior, _c, _g2 = _circle_lead_arc(spec, east, t_in, True)
            return exterior
        return (east[0] - lead_app * t_in[0], east[1] - lead_app * t_in[1])
    return east


def _circle_body(spec, depth, security, plunge_feed, cut_feed,
                 compensated, has_app, has_ret, lead_app, lead_ret):
    """Cuerpo del fresado circular (N038/N039). Devuelve (líneas, ret_suprime_G0, salida_xy)."""
    east, t_in, g_wind = _circle_frame(spec)
    strategy = spec.milling_strategy
    lines: list[str] = []

    if compensated:
        # Corrección Interna/Externa C.N. (side_l/side_r): G41/G42 con las MISMAS coordenadas
        # (compensa el control); activación de 1 mm sobre la tangente; retracción G1 + G40 +
        # 1 mm de salida. Con leads (side_l_leads): anclado al arco del lead, como la línea.
        lines += ["?%ETK[7]=4", "G41" if spec.side_of_feature == "Left" else "G42"]
        if has_app:
            (apx, apy), (acx, acy), ag = _circle_lead_arc(spec, east, t_in, True)
            lines += [
                f"G1 X{apx:.3f} Y{apy:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                f"{ag} X{east[0]:.3f} Y{east[1]:.3f} I{acx:.3f} J{acy:.3f} F{plunge_feed:.3f}",
            ]
        else:
            lines += [
                f"G1 X{east[0]:.3f} Y{east[1]:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
            ]
        lines += _circle_halves(spec, g_wind, cut_feed)
        if has_ret:
            (rpx, rpy), (rcx, rcy), rg = _circle_lead_arc(spec, east, t_in, False)
            lines.append(f"{rg} X{rpx:.3f} Y{rpy:.3f} I{rcx:.3f} J{rcy:.3f} F{cut_feed:.3f}")
            tx, ty = _arc_tangent(rpx, rpy, rcx, rcy, rg)
            out = (rpx + _COMP_LEAD * tx, rpy + _COMP_LEAD * ty)
        else:
            out = (east[0] + _COMP_LEAD * t_in[0], east[1] + _COMP_LEAD * t_in[1])
        lines += [
            f"G1 Z{security:.3f} F{cut_feed:.3f}",
            "G40",
            f"G1 X{out[0]:.3f} Y{out[1]:.3f} Z{security:.3f} F{cut_feed:.3f}",
        ]
        return lines, False, out

    if strategy is not None:
        is_heli = type(strategy).__name__.startswith("Helical")
        cd = strategy.axial_cutting_depth
        lines += [f"G1 Z{security:.3f} F{plunge_feed:.3f}", "?%ETK[7]=4"]
        if is_heli:
            # HELICOIDAL (N039 heli — falló en líneas, el círculo es su caso natural): baja a la
            # SUPERFICIE y desciende cd por vuelta en medias vueltas con Z; el centro J se
            # descentra ±(hypot(r, dz/2) − r) (el radio 3D del arco inclinado); cierra con una
            # vuelta PLANA a profundidad total.
            lines.append(f"G1 Z0.000 F{cut_feed:.3f}")
            n_revs = max(1, math.ceil(depth / cd - 1e-9))
            levels = [-min(i * cd, depth) for i in range(1, n_revs + 1)]
            current = 0.0
            for level in levels:
                mid = (current + level) / 2.0
                dz_half = (current - level) / 2.0
                j_off = math.hypot(spec.radius, dz_half / 2.0) - spec.radius
                lines += _circle_halves(spec, g_wind, cut_feed, z_mid=mid, z_end=level,
                                        j_off=j_off)
                current = level
            lines += _circle_halves(spec, g_wind, cut_feed)
        else:
            # Bi/Uni sobre contorno CERRADO (N039): sin conexiones — el círculo termina donde
            # empieza y la pasada siguiente baja directo. El Bi ALTERNA el sentido de giro por
            # pasada (G3/G2/G3); el Uni repite el sentido.
            is_bi = type(strategy).__name__.startswith("Bidirectional")
            g_flip = "G2" if g_wind == "G3" else "G3"
            n_passes = max(1, math.ceil(depth / cd - 1e-9))
            depths = [-min(i * cd, depth) for i in range(1, n_passes + 1)]
            last_reversed = False
            for idx, z in enumerate(depths):
                lines.append(f"G1 Z{z:.3f} F{cut_feed:.3f}")
                if idx == 0 and has_app:
                    mp_lead = _mp_lead(spec, spec.approach)
                    if mp_lead > 1e-9:
                        _p, (acx, acy), ag = _mp_lead_arc(east, t_in, mp_lead, "Automatic", True)
                        lines.append(f"{ag} X{east[0]:.3f} Y{east[1]:.3f} "
                                     f"I{acx:.3f} J{acy:.3f} F{cut_feed:.3f}")
                reversed_pass = is_bi and idx % 2 == 1
                lines += _circle_halves(spec, g_flip if reversed_pass else g_wind, cut_feed)
                last_reversed = reversed_pass
            if has_ret:
                mp_lead = _mp_lead(spec, spec.retract)
                if mp_lead > 1e-9:
                    u_out = (-t_in[0], -t_in[1]) if last_reversed else t_in
                    (rpx, rpy), (rcx, rcy), rg = _mp_lead_arc(east, u_out, mp_lead,
                                                              "Automatic", False)
                    lines.append(f"{rg} X{rpx:.3f} Y{rpy:.3f} "
                                 f"I{rcx:.3f} J{rcy:.3f} F{cut_feed:.3f}")
        lines.append(f"G1 Z{security:.3f} F{cut_feed:.3f}")
        return lines, False, east

    if has_app or has_ret:
        # Leads single-pass (N039 app_arc/app_ret_arc/app_line): regla de línea con û=tangente;
        # plunge en el punto exterior a feed de plunge, lead a feed de plunge, círculo a corte;
        # el retract en arco retrae en G1 (suprime el G0 Z), como la línea.
        lines.append("?%ETK[7]=4")
        lines.append(f"G1 Z{-depth:.3f} F{plunge_feed:.3f}")
        if has_app:
            if spec.approach.approach_type == "Arc":
                _p, (acx, acy), ag = _circle_lead_arc(spec, east, t_in, True)
                lines.append(f"{ag} X{east[0]:.3f} Y{east[1]:.3f} "
                             f"I{acx:.3f} J{acy:.3f} F{plunge_feed:.3f}")
            else:
                exterior = (east[0] - lead_app * t_in[0], east[1] - lead_app * t_in[1])
                lines.append(_g1_cut(exterior[0], exterior[1], east[0], east[1], -depth,
                                     plunge_feed, prev_z=-depth))
        lines += _circle_halves(spec, g_wind, cut_feed)
        if has_ret:
            (rpx, rpy), (rcx, rcy), rg = _circle_lead_arc(spec, east, t_in, False)
            lines.append(f"{rg} X{rpx:.3f} Y{rpy:.3f} I{rcx:.3f} J{rcy:.3f} F{cut_feed:.3f}")
            lines.append(f"G1 Z{security:.3f} F{cut_feed:.3f}")
            return lines, True, east
        return lines, False, east

    # Círculo pelado (N038): plunge estilo línea y las dos mitades.
    lines += [f"G1 Z{-depth:.3f} F{plunge_feed:.3f}", "?%ETK[7]=4"]
    lines += _circle_halves(spec, g_wind, cut_feed)
    return lines, False, east


def _poly_start_and_segments(spec):
    """(start_xy, [(end_x, end_y, is_arc, cx, cy, winding), ...]) de una polilínea (una sola
    spec unificada: los segmentos son rectas y/o arcos)."""
    start = (spec.start_x, spec.start_y)
    segs = [(s.end_x, s.end_y, s.is_arc, s.center_x, s.center_y, s.winding)
            for s in spec.segments]
    return start, segs


def _lead_geometry_at(anchor, u, lead, arc_side, at_start):
    """`_lead_geometry` con ancla y dirección EXPLÍCITAS (para polilíneas: la dirección es la
    del primer/último segmento, no start→end). Convención single-pass: Left→G2, Automatic/
    Right→G3; centro a `lead` perpendicular al avance; punto exterior ∓ lead·û."""
    ux, uy = u
    if arc_side == "Left":
        nx, ny, g = uy, -ux, "G2"
    else:  # Automatic o Right
        nx, ny, g = -uy, ux, "G3"
    cx, cy = anchor[0] + lead * nx, anchor[1] + lead * ny
    if at_start:
        px, py = cx - lead * ux, cy - lead * uy
    else:
        px, py = cx + lead * ux, cy + lead * uy
    return (px, py), (cx, cy), g


def _seg_dir_from(anchor, seg):
    """Dirección unitaria de salida desde `anchor` a lo largo del segmento (tangente en el
    arranque si es arco; dir. de la recta si no)."""
    ex, ey, is_arc, cxx, cyy, wind = seg
    if is_arc:
        rx, ry = anchor[0] - cxx, anchor[1] - cyy
        r = math.hypot(rx, ry)
        return (-ry / r, rx / r) if wind == "CounterClockwise" else (ry / r, -rx / r)
    dx, dy = ex - anchor[0], ey - anchor[1]
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)


def _seg_dir_to(prev, seg):
    """Dirección unitaria de llegada al END del segmento (tangente en el fin si es arco)."""
    ex, ey, is_arc, cxx, cyy, wind = seg
    if is_arc:
        rx, ry = ex - cxx, ey - cyy
        r = math.hypot(rx, ry)
        return (-ry / r, rx / r) if wind == "CounterClockwise" else (ry / r, -rx / r)
    dx, dy = ex - prev[0], ey - prev[1]
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)


def _poly_first_last(start, segs):
    """(first_dir, last_end, last_dir) de la cadena de segmentos."""
    first_dir = _seg_dir_from(start, segs[0])
    prev = start
    for seg in segs[:-1]:
        prev = (seg[0], seg[1])
    last_dir = _seg_dir_to(prev, segs[-1])
    last_end = (segs[-1][0], segs[-1][1])
    return first_dir, last_end, last_dir


def _poly_cut_lines(start, segs, depth, cut_feed):
    """La cadena de segmentos como G-code: recta = _g1_cut, arco = G3/G2 con I/J al centro."""
    lines = []
    px, py = start
    for end_x, end_y, seg_is_arc, seg_cx, seg_cy, seg_wind in segs:
        if seg_is_arc:
            seg_g = "G3" if seg_wind == "CounterClockwise" else "G2"
            lines.append(f"{seg_g} X{end_x:.3f} Y{end_y:.3f} "
                         f"I{seg_cx:.3f} J{seg_cy:.3f} F{cut_feed:.3f}")
        else:
            lines.append(_g1_cut(px, py, end_x, end_y, -depth, cut_feed, prev_z=-depth))
        px, py = end_x, end_y
    return lines, (px, py)


def _line_intersection(p0, d0, p1, d1):
    """Punto donde se cruzan las rectas (p0 + t·d0) y (p1 + s·d1). d0/d1 no paralelos."""
    det = d1[0] * d0[1] - d0[0] * d1[1]
    t = (-(p1[0] - p0[0]) * d1[1] + d1[0] * (p1[1] - p0[1])) / det
    return (p0[0] + t * d0[0], p0[1] + t * d0[1])


def _poly_cad_moves(spec):
    """Traza CAD de un contorno CERRADO (N043 + N044, byte-validado). Cada borde corre
    OFFSETEADO r=w/2 hacia el lado (Right=rot90cw(û)/arcos G3, Left=rot90ccw(û)/arcos G2) y cada
    VÉRTICE se resuelve por el signo del giro cruzado con el lado:
    - offset que abre un HUECO (Right+giro-izq / Left+giro-der) → ARCO (centro=vértice nominal,
      radio=r; del punto de offset del borde entrante al del saliente — un cuarto en 90°, el
      ángulo del giro en general);
    - offset que SUPERPONE los bordes → ESQUINA VIVA (intersección de las dos rectas offseteadas,
      sin arco). Es la respuesta a "¿la cóncava es arco o viva?": viva (N044 cad_concava/interno).
    Fase de arranque: si el vértice inicial es arco, va PRIMERO con Right y ÚLTIMO con Left; si es
    vivo, la traza arranca en ese punto y el borde va primero. Devuelve (entry_xy, moves) con
    moves = [('line', (x,y)) | ('arc', (x,y)=p_out, (cx,cy)=vértice, 'G3'|'G2')]."""
    start, segs = _poly_start_and_segments(spec)
    verts = [start] + [(s[0], s[1]) for s in segs[:-1]]   # cerrado: el último end == start
    n = len(verts)
    r = spec.tool_width / 2.0
    right = spec.side_of_feature == "Right"
    g_arc = "G3" if right else "G2"
    dirs, offs = [], []   # dir unitaria del borde i, (a_i, b_i) = inicio/fin offseteados
    for i in range(n):
        vx, vy = verts[i]
        wx, wy = verts[(i + 1) % n]
        ux, uy = wx - vx, wy - vy
        length = math.hypot(ux, uy)
        ux, uy = ux / length, uy / length
        nx, ny = (uy, -ux) if right else (-uy, ux)   # rot90cw / rot90ccw
        dirs.append((ux, uy))
        offs.append(((vx + r * nx, vy + r * ny), (wx + r * nx, wy + r * ny)))
    corners = []   # ('arc', p_in, p_out) o ('live', p)
    for i in range(n):
        p = (i - 1) % n
        turn = dirs[p][0] * dirs[i][1] - dirs[p][1] * dirs[i][0]
        is_arc = (turn > 1e-9) if right else (turn < -1e-9)
        if is_arc:
            corners.append(("arc", offs[p][1], offs[i][0]))   # p_in=b_prev, p_out=a_i
        else:
            corners.append(("live", _line_intersection(offs[p][0], dirs[p], offs[i][0], dirs[i])))
    entry_of = lambda c: c[1]                       # arco: p_in ; vivo: p
    # Orden cíclico corner_0, edge_0, corner_1, edge_1, ... con la fase de arranque derivada.
    if corners[0][0] == "arc" and right:
        entry = corners[0][1]                       # p_in del arco inicial (va primero)
        order = [(0, "corner"), (0, "edge")] + [(i, k) for i in range(1, n) for k in ("corner", "edge")]
    elif corners[0][0] == "arc":
        entry = corners[0][2]                       # p_out del arco inicial (va último, Left)
        order = [(0, "edge")] + [(i, k) for i in range(1, n) for k in ("corner", "edge")] + [(0, "corner")]
    else:
        entry = corners[0][1]                       # esquina viva inicial
        order = [(0, "edge")] + [(i, k) for i in range(1, n) for k in ("corner", "edge")]
    moves = []
    for idx, kind in order:
        c = corners[idx]
        if kind == "corner":
            if c[0] == "arc":
                moves.append(("arc", c[2], verts[idx], g_arc))
        else:   # borde idx: hasta la ENTRADA del vértice siguiente
            moves.append(("line", entry_of(corners[(idx + 1) % n])))
    return entry, moves


def _cad_tangent(p, move, at_end):
    """Tangente de la traza CAD offseteada en un extremo de `move` (at_end=False → en su arranque
    `p`; True → en su punto final)."""
    if move[0] == "arc":
        qx, qy = move[1] if at_end else p
        cx, cy = move[2]
        rx, ry = qx - cx, qy - cy
        r = math.hypot(rx, ry)
        return (-ry / r, rx / r) if move[3] == "G3" else (ry / r, -rx / r)
    qx, qy = move[1]
    dx, dy = qx - p[0], qy - p[1]
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)


def _cad_lead_dirs(entry, moves):
    """(û de entrada, û de salida) de la traza CAD: las tangentes en el arranque del primer move
    y en el fin del último. En un contorno cerrado ambos extremos caen en el mismo punto."""
    p = entry
    for move in moves[:-1]:
        p = move[1]
    return _cad_tangent(entry, moves[0], False), _cad_tangent(p, moves[-1], True)


def _poly_cad_body(spec, depth, security, plunge_feed, cut_feed, has_app=False, has_ret=False):
    """Cuerpo CAD del contorno cerrado (N043/N044): bajada a security a feed de PLUNGE, ETK[7]=4,
    plunge a feed de CORTE (patrón CAD de la línea), y la cadena de arcos de esquina + bordes
    offseteados (arcos con I/J ABSOLUTOS al vértice nominal, F en todos los movimientos), cerrando
    donde arrancó; retracción final a feed de corte (el G0 Z del teardown queda).

    Leads (N045): anclados a la traza OFFSETEADA (no a la nominal) sobre su tangente, tras el
    plunge el de entrada y antes de la retracción el de salida, todos a feed de CORTE. Arco =
    la geometría de estrategia `_mp_lead_arc` (Right→G2/rot90cw), radio (w/2)×(RM−1); Línea =
    tramo recto de (w/2)×RM sobre la tangente."""
    entry, moves = _poly_cad_moves(spec)
    u_in, u_out = _cad_lead_dirs(entry, moves)
    lines = [
        f"G1 Z{security:.3f} F{plunge_feed:.3f}",
        "?%ETK[7]=4",
        f"G1 Z{-depth:.3f} F{cut_feed:.3f}",
    ]
    if has_app:
        lines += _cad_lead_moves(spec, spec.approach, spec.approach.approach_type,
                                 entry, u_in, depth, cut_feed, True)
    px, py = entry
    for move in moves:
        if move[0] == "arc":
            (ax, ay), (cx, cy), g = move[1], move[2], move[3]
            lines.append(f"{g} X{ax:.3f} Y{ay:.3f} I{cx:.3f} J{cy:.3f} F{cut_feed:.3f}")
            px, py = ax, ay
        else:
            ex, ey = move[1]
            lines.append(_g1_cut(px, py, ex, ey, -depth, cut_feed, prev_z=-depth))
            px, py = ex, ey
    if has_ret:
        lines += _cad_lead_moves(spec, spec.retract, spec.retract.retract_type,
                                 (px, py), u_out, depth, cut_feed, False)
        px, py = _cad_lead_end(spec, spec.retract, spec.retract.retract_type,
                               (px, py), u_out, False)
    lines.append(f"G1 Z{security:.3f} F{cut_feed:.3f}")
    return lines, False, (px, py)


def _cad_lead_moves(spec, lead_spec, lead_type, anchor, u, depth, cut_feed, at_start):
    """El G-code de UN lead CAD. Arco: G2/G3 con I/J absolutos al centro (entrada: desde el punto
    exterior al ancla; salida: del ancla al exterior). Línea: un G1 a feed de corte."""
    px, py = _cad_lead_end(spec, lead_spec, lead_type, anchor, u, at_start)
    if (px, py) == anchor:
        return []
    if lead_type == "Line":
        if at_start:
            return [_g1_cut(px, py, anchor[0], anchor[1], -depth, cut_feed, prev_z=-depth)]
        return [_g1_cut(anchor[0], anchor[1], px, py, -depth, cut_feed, prev_z=-depth)]
    _p, (cx, cy), g = _mp_lead_arc(anchor, u, _mp_lead(spec, lead_spec),
                                   _mp_arc_side(spec, lead_spec), at_start)
    tx, ty = anchor if at_start else (px, py)
    return [f"{g} X{tx:.3f} Y{ty:.3f} I{cx:.3f} J{cy:.3f} F{cut_feed:.3f}"]


def _cad_lead_end(spec, lead_spec, lead_type, anchor, u, at_start):
    """Punto EXTERIOR de un lead CAD (de donde entra el acercamiento, o adonde sale el
    alejamiento). Largo: Arco (w/2)×(RM−1) — con RM≤1 el arco se OMITE y el punto es el ancla
    misma (cad_leads_rm1) —; Línea (w/2)×RM sobre la tangente, hacia atrás en la entrada y hacia
    adelante en la salida."""
    if lead_type == "Line":
        lead = spec.tool_width / 2.0 * lead_spec.radius_multiplier
        sign = -1.0 if at_start else 1.0
        return (anchor[0] + sign * lead * u[0], anchor[1] + sign * lead * u[1])
    lead = _mp_lead(spec, lead_spec)
    if lead <= 1e-9:
        return anchor
    (px, py), _c, _g = _mp_lead_arc(anchor, u, lead, _mp_arc_side(spec, lead_spec), at_start)
    return (px, py)


def _poly_entry_xy(spec, compensated, has_app, lead_app, cad=False):
    """Punto de APROXIMACIÓN (G0) de una polilínea (N042). Con corrección: 1 mm antes del
    arranque sobre la dir. del primer segmento (o sobre la tangente del arco de acercamiento).
    Con acercamiento sin corrección: el punto exterior del arco. CAD (N043/N044): el punto de
    arranque de la traza offseteada. Baseline: el arranque."""
    if cad:
        entry, moves = _poly_cad_moves(spec)
        if not has_app:
            return entry
        # Con acercamiento (N045) el G0 va al punto EXTERIOR del lead, sobre la tangente de la
        # traza offseteada (con RM≤1 el arco se omite y el punto vuelve a ser el arranque).
        u_in, _u_out = _cad_lead_dirs(entry, moves)
        return _cad_lead_end(spec, spec.approach, spec.approach.approach_type, entry, u_in, True)
    start, segs = _poly_start_and_segments(spec)
    first_dir = _seg_dir_from(start, segs[0])
    if compensated and has_app and spec.approach.approach_type == "Line":
        # Lead-in lineal (N044): 1 mm antes del punto exterior (start − lead·û), sobre û.
        return (start[0] - (lead_app + _COMP_LEAD) * first_dir[0],
                start[1] - (lead_app + _COMP_LEAD) * first_dir[1])
    if compensated and has_app:
        (apx, apy), (acx, acy), ag = _lead_geometry_at(
            start, first_dir, lead_app, _comp_auto_arc_side(spec), True)
        tx, ty = _arc_tangent(apx, apy, acx, acy, ag)
        return (apx - _COMP_LEAD * tx, apy - _COMP_LEAD * ty)
    if compensated:
        return (start[0] - _COMP_LEAD * first_dir[0], start[1] - _COMP_LEAD * first_dir[1])
    if has_app:
        (apx, apy), _c, _g = _lead_geometry_at(start, first_dir, lead_app,
                                               spec.approach.arc_side, True)
        return (apx, apy)
    return start


def _poly_body(spec, depth, security, plunge_feed, cut_feed, compensated, has_app, has_ret,
               lead_app, lead_ret):
    """Cuerpo de una polilínea (N041 baseline + N042/N044 corrección/leads). Devuelve
    (líneas, ret_suprime_G0, salida_xy). Corrección = modelo de la LÍNEA con lead-in sobre el
    primer segmento y lead-out sobre el último; los segmentos van NOMINALES (G41/G42 delega el
    empalme de esquinas al control). Leads Arco (N042) o Línea con modo En cota/En bajada/En
    subida (N044)."""
    start, segs = _poly_start_and_segments(spec)
    first_dir, last_end, last_dir = _poly_first_last(start, segs)
    cut, cut_end = _poly_cut_lines(start, segs, depth, cut_feed)

    if compensated:
        lines = ["?%ETK[7]=4", "G41" if spec.side_of_feature == "Left" else "G42"]
        if has_app and spec.approach.approach_type == "Line":
            # Lead-in LINEAL (N044): al punto exterior (start − lead·û) a security, y línea al
            # start. "En bajada" (Down) = rampa (baja mientras avanza, sin plunge aparte); "En
            # cota" (Quote) = plunge vertical + línea plana. Todo a feed de plunge.
            ux, uy = first_dir
            apx, apy = start[0] - lead_app * ux, start[1] - lead_app * uy
            lines.append(f"G1 X{apx:.3f} Y{apy:.3f} Z{security:.3f} F{plunge_feed:.3f}")
            if spec.approach.mode == "Down":
                lines.append(_g1_cut(apx, apy, start[0], start[1], -depth, plunge_feed, prev_z=security))
            else:
                lines.append(f"G1 Z{-depth:.3f} F{plunge_feed:.3f}")
                lines.append(_g1_cut(apx, apy, start[0], start[1], -depth, plunge_feed, prev_z=-depth))
        elif has_app:
            (apx, apy), (acx, acy), ag = _lead_geometry_at(
                start, first_dir, lead_app, _comp_auto_arc_side(spec), True)
            lines += [
                f"G1 X{apx:.3f} Y{apy:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
                f"{ag} X{start[0]:.3f} Y{start[1]:.3f} I{acx:.3f} J{acy:.3f} F{plunge_feed:.3f}",
            ]
        else:
            lines += [
                f"G1 X{start[0]:.3f} Y{start[1]:.3f} Z{security:.3f} F{plunge_feed:.3f}",
                f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
            ]
        lines += cut
        if has_ret and spec.retract.retract_type == "Line":
            # Lead-out LINEAL (N044): línea al punto exterior (end + lead·û); "En subida" (Up)
            # sube a security en la misma rampa (sin G1 Z aparte), "En cota" (Quote) sale a
            # profundidad + G1 Z. El 1 mm del G40 sigue sobre û. Todo a feed de corte.
            ux, uy = last_dir
            rpx, rpy = last_end[0] + lead_ret * ux, last_end[1] + lead_ret * uy
            out = (rpx + _COMP_LEAD * ux, rpy + _COMP_LEAD * uy)
            if spec.retract.mode == "Up":
                lines.append(_g1_cut(last_end[0], last_end[1], rpx, rpy, security, cut_feed, prev_z=-depth))
                lines += ["G40", f"G1 X{out[0]:.3f} Y{out[1]:.3f} Z{security:.3f} F{cut_feed:.3f}"]
            else:
                lines.append(_g1_cut(last_end[0], last_end[1], rpx, rpy, -depth, cut_feed, prev_z=-depth))
                lines += [
                    f"G1 Z{security:.3f} F{cut_feed:.3f}",
                    "G40",
                    f"G1 X{out[0]:.3f} Y{out[1]:.3f} Z{security:.3f} F{cut_feed:.3f}",
                ]
        elif has_ret and spec.retract.retract_type == "Arc":
            # Alejamiento en ARCO compensado (N044 enjuego): arco de salida A PROFUNDIDAD sobre el
            # lado LIBRE, G1 Z a security, G40 y 1 mm sobre la tangente. Mismo patrón que la línea.
            (rpx, rpy), (rcx, rcy), rg = _lead_geometry_at(
                last_end, last_dir, lead_ret, _comp_auto_arc_side(spec), False)
            rtx, rty = _arc_tangent(rpx, rpy, rcx, rcy, rg)
            out = (rpx + _COMP_LEAD * rtx, rpy + _COMP_LEAD * rty)
            lines += [
                f"{rg} X{rpx:.3f} Y{rpy:.3f} I{rcx:.3f} J{rcy:.3f} F{cut_feed:.3f}",
                f"G1 Z{security:.3f} F{cut_feed:.3f}",
                "G40",
                f"G1 X{out[0]:.3f} Y{out[1]:.3f} Z{security:.3f} F{cut_feed:.3f}",
            ]
        else:
            out = (last_end[0] + _COMP_LEAD * last_dir[0], last_end[1] + _COMP_LEAD * last_dir[1])
            lines += [
                f"G1 Z{security:.3f} F{cut_feed:.3f}",
                "G40",
                f"G1 X{out[0]:.3f} Y{out[1]:.3f} Z{security:.3f} F{cut_feed:.3f}",
            ]
        return lines, False, out

    if has_app:
        # Acercamiento sin corrección (Center): plunge y arco tangente anclado al 1er vértice.
        (apx, apy), (acx, acy), ag = _lead_geometry_at(
            start, first_dir, lead_app, spec.approach.arc_side, True)
        lines = [
            "?%ETK[7]=4",
            f"G1 Z{-depth:.3f} F{plunge_feed:.3f}",
            f"{ag} X{start[0]:.3f} Y{start[1]:.3f} I{acx:.3f} J{acy:.3f} F{plunge_feed:.3f}",
        ]
        lines += cut
        return lines, False, cut_end

    lines = [f"G1 Z{-depth:.3f} F{plunge_feed:.3f}", "?%ETK[7]=4"] + cut
    return lines, False, cut_end


def _atc_header(spec: LineSpec) -> list[str]:
    n = _cutter_number(spec)
    g = tool_geometry(spec.tool_name)
    _sp = getattr(spec, "spindle", 0.0)
    spindle = int(_sp) if _sp > 0 else g.spindle_std
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
