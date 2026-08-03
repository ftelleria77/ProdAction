"""Validación fail-loud del converter PGMX→ISO.

El converter solo cubre un subconjunto de operaciones/parámetros (los validados en
los lotes N00x). Antes de convertir, esta capa detecta cualquier operación o
parámetro fuera de ese subconjunto y aborta con un mensaje claro y accionable,
en lugar de crashear con un KeyError o —peor— emitir ISO incompleto en silencio.

Cada límite referencia la fase del roadmap que lo levantará
(ver memoria project-converter-roadmap).
"""

from __future__ import annotations

import math
from typing import Iterable

from pgmx.synthesis.drilling.pattern import DrillPatternSpec
from pgmx.synthesis.drilling.single import DrillSpec
from pgmx.synthesis.common.strategy import ZigZagMillingStrategySpec
from pgmx.synthesis.milling.arc import ArcSpec
from pgmx.synthesis.milling.polyline import PolylineSpec
from pgmx.synthesis.milling.circle import CircleSpec
from pgmx.synthesis.milling.line import LineSpec
from pgmx.synthesis.milling.channel import ChannelSpec
from pgmx.synthesis.milling.pocket import PocketSpec

from ._machine import SIDE_FACE, TOP_TOOL, TOP_TOOL_CONICAL, top_tool_or_none
from ._tool_catalog import tool_geometry

__all__ = ["UnsupportedOperationError", "validate_entries"]


class UnsupportedOperationError(ValueError):
    """El .pgmx contiene una operación o parámetro que el converter aún no soporta."""


_SUPPORTED_DRILL_FACES = frozenset({"Top", *SIDE_FACE})


def _top_tool_supported(spec: DrillSpec) -> bool:
    """Soportada si resuelve a una herramienta vertical conocida (por la herramienta
    seleccionada o por punta+diámetro). Mismo criterio que el render."""
    return top_tool_or_none(spec.diameter, spec.drill_family, spec.tool_name) is not None


def validate_entries(entries: Iterable[object]) -> None:
    """Valida todas las entries del programa. Lanza ``UnsupportedOperationError``."""
    for entry in entries:
        spec = getattr(entry, "spec", entry)
        if isinstance(spec, DrillSpec):
            _validate_drill(spec)
        elif isinstance(spec, DrillPatternSpec):
            _validate_drill_pattern(spec)
        elif isinstance(spec, LineSpec):
            _validate_line(spec)
        elif isinstance(spec, ChannelSpec):
            _validate_channel(spec)
        elif isinstance(spec, CircleSpec):
            _validate_circle(spec)
        elif isinstance(spec, ArcSpec):
            _validate_arc(spec)
        elif isinstance(spec, PolylineSpec):
            _validate_polyline(spec)
        elif isinstance(spec, PocketSpec):
            _validate_pocket(spec)
        else:
            _fail(spec, f"operación de tipo {type(spec).__name__!r} no soportada "
                        f"(por ahora: taladro, fresado lineal/circular, canal y vaciado). "
                        f"[Eje B del roadmap]")


def _fail(spec: object, detail: str) -> None:
    feat = getattr(spec, "feature_name", "?")
    raise UnsupportedOperationError(f"Feature '{feat}': {detail}")


def _validate_drill(spec: DrillSpec) -> None:
    if spec.plane_name not in _SUPPORTED_DRILL_FACES:
        _fail(spec, f"cara de taladro {spec.plane_name!r} no soportada "
                    f"(soportadas: {sorted(_SUPPORTED_DRILL_FACES)}).")
    if spec.plane_name == "Top" and not _top_tool_supported(spec):
        _fail(spec, f"herramienta vertical no soportada (Ø{spec.diameter:g}, "
                    f"tool {spec.tool_name!r}). Planas: {sorted(TOP_TOOL)}; "
                    f"cónicas: {sorted(TOP_TOOL_CONICAL)}. [A1]")
    # Top-pasante: soportado (z_cut = cara inferior). Lateral-pasante: soportado si la
    # dimensión cruzada ≤ hundimiento máximo; el límite se valida en _reader con la geometría
    # (side_effective_depth vs SIDE_MAX_DEPTH). Maestro ignora extra_depth en el vertical
    # (no baja de la mesa, N005), así que no lo rechazamos.
    if not spec.depth_spec.is_through and spec.depth_spec.extra_depth:
        _fail(spec, "extra_depth en taladro ciego no soportado aún. [A1/A2]")
    # Lateral: el husillo no hace peck → un solo corte (Maestro ignora step_number/step_depth).
    # No se rechaza; el render lateral ya emite un corte único.
    if spec.taper_height:
        _fail(spec, "taper_height (avellanado paramétrico) no soportado: requiere "
                    "reinstalar herramientas (cambia config + def.tlgx). [A1+]")
    # feedrate/spindle por operación: Top clampa al máximo de la tool (N009/N010); lateral
    # aplica feed (clampado a SIDE_FEED_MAX) e ignora el spindle (husillo fijo). (N011)
    # Ambos casos están soportados → no se rechaza.
    if spec.center_x_expr or spec.center_y_expr or spec.is_enabled_expr:
        _fail(spec, "posiciones/habilitación paramétricas (expr) no soportadas aún. [Eje C]")


def _validate_drill_pattern(spec: DrillPatternSpec) -> None:
    """Un patrón se expande a taladros individuales idénticos al base (N008): validamos
    el agujero base con las mismas reglas. El adapter ya garantiza rectangular/0/90."""
    base = DrillSpec(
        center_x=spec.center_x,
        center_y=spec.center_y,
        diameter=spec.diameter,
        feature_name=spec.feature_name,
        plane_name=spec.plane_name,
        security_plane=spec.security_plane,
        depth_spec=spec.depth_spec,
        drill_family=spec.drill_family,
        tool_resolution=spec.tool_resolution,
        tool_id=spec.tool_id,
        tool_name=spec.tool_name,
        is_enabled_expr=spec.is_enabled_expr,
    )
    _validate_drill(base)


def _validate_line(spec: LineSpec) -> None:
    if spec.plane_name != "Top":
        _fail(spec, f"fresado lineal en cara {spec.plane_name!r} no soportado "
                    f"(solo Top). [A3]")
    # Cualquier herramienta del cabezal: no se distingue tipo (fresa o sierra). Solo hace falta
    # que exista en el catálogo (para sourcear sus params) y que su nombre sea E00N (slot/ETK[9]).
    try:
        tool_geometry(spec.tool_name)
        int(spec.tool_name.lstrip("E"))
    except (KeyError, ValueError):
        _fail(spec, f"fresa {spec.tool_name!r} no está en el catálogo o su nombre no es E00N. [A3]")
    # Pasante: soportado (N024, z = -(espesor+extra)). El límite de hundimiento se valida en
    # _reader (necesita el espesor de la pieza).
    # Rebaba (SideOffset del feature): SVR = width/2 + rebaba (N024, Center/L/R/xrev, ±2).
    if spec.allowance_side or spec.allowance_bottom:
        _fail(spec, f"Allowance side/bottom={spec.allowance_side:g}/{spec.allowance_bottom:g} en "
                    f"fresado lineal: sin uso conocido (la rebaba de línea es SideOffset). [A3]")
    if spec.tool_width / 2.0 + spec.side_offset < 0.0:
        _fail(spec, f"rebaba {spec.side_offset:g} deja el corrector de radio negativo "
                    f"(width/2 + rebaba < 0): sin fixture de referencia. [A3]")
    # Corrección de longitud (IsPrecise): acorta el recorrido width/2 en cada extremo. Validada
    # (N023 _long) en líneas a eje, ambos sentidos, con y sin G41/G42, E004 y E001. Con cambios
    # de recorrido (N036 long_vel): el UPar corre sobre el recorrido ACORTADO (X98.8 = 22+0.3·256).
    if spec.is_precise:
        length = abs(spec.end_x - spec.start_x) + abs(spec.end_y - spec.start_y)
        if length <= spec.tool_width:
            _fail(spec, f"corrección de longitud: la línea ({length:g} mm) no supera el ancho "
                        f"de la fresa ({spec.tool_width:g} mm) — recorrido degenerado. [A3]")
    # Corrección CAD (N023 _CAD + N036): coordenadas desplazadas radio×normal(lado) — el
    # desplazamiento usa w/2, la rebaba solo suma al SVR (cad_reb2) —, sin G41, entrada/salida Z
    # estilo security; cambios de recorrido (cad_vel/mp_vel: la retracción sale al feed vigente),
    # pasante (cad_th) y leads estilo-estrategia (cad_leads, solo Arco/En cota/sin velocidad)
    # validados. CAD + longitud y CAD + invertir: derivados de los fixtures REGENERADOS en Maestro
    # (2026-07-07): el acorte ±w/2 y el swap SÍ aplican sobre las coordenadas desplazadas
    # (cad_long: X22→278 en y102; inv_cad: 280→20 en y102) — los eco previos mentían.
    if not spec.activate_cnc_correction and spec.milling_strategy is None:
        for label, lead in (("acercamiento", spec.approach), ("alejamiento", spec.retract)):
            if not lead.is_enabled:
                continue
            lead_type = getattr(lead, "approach_type", None) or getattr(lead, "retract_type", None)
            if lead_type != "Arc" or lead.mode != "Quote" or lead.speed > 0 \
                    or lead.arc_side != "Automatic":
                _fail(spec, f"Corrección CAD + {label} no Arco/En cota/Automatic/sin velocidad: "
                            "sin fixture (N036 valida la forma base). [A3]")
    # Corrección de herramienta (side Left/Right → G41/G42, radio del SVR): validada en N023;
    # con cambios de recorrido (N036 side_vel): la retracción y el 1mm del G40 salen al feed
    # VIGENTE tras el cambio.
    if spec.side_of_feature not in ("Center", "Left", "Right"):
        _fail(spec, f"side_of_feature={spec.side_of_feature!r} desconocido. [A3]")
    # Cambios de recorrido + leads programables: interacción de feeds sin fixture (agujero
    # detectado en N036; ninguna combinación la cubre).
    if (spec.speed_changes or spec.depth_changes) and (
            spec.approach.is_enabled or spec.retract.is_enabled):
        _fail(spec, "cambios en el recorrido + acercamiento/alejamiento: sin fixture de "
                    "referencia. [A3]")
    # Invertir trabajo (N023 _invert + N036): validado con cambios de recorrido (inv_vel: el
    # UPar corre sobre el recorrido invertido), longitud (inv_long: acorta y después invierte)
    # y rebaba (inv_reb2). PENDIENTE DE REGENERACIÓN (eco): invertir + estrategia (inv_mp) e
    # invertir + CAD (arriba).
    # Invertir + estrategia: derivado del inv_mp REGENERADO (2026-07-07): las pasadas alternan
    # desde el extremo intercambiado (280→20 Z-4, 20→280 Z-8, …) — swap antes de la estrategia.
    # Avanz./Rotación por operación (N028 F3_S12K): F=Avanz×1000 en el corte; S{Rotación}M3.
    # El comportamiento en el TOPE (clamp tipo taladro) no está validado → fail-loud si excede.
    if spec.feedrate > 0 or spec.spindle > 0:
        _g = tool_geometry(spec.tool_name)
        if spec.feedrate * 1000.0 > _g.feed_max:
            _fail(spec, f"Avanz. {spec.feedrate:g} supera el tope de la fresa "
                        f"({_g.feed_max/1000:g} m/min): clamp sin fixture. [A3]")
        if spec.spindle > _g.spindle_max:
            _fail(spec, f"Rotación {spec.spindle:g} supera el tope ({_g.spindle_max} rpm): "
                        f"clamp sin fixture. [A3]")
    # Combos derivados de los cuerpos completos de N029 (2026-07-05):
    # - MULTIPASADA + LADO (mp_side_l): la estrategia fuerza ACC=false → coordenadas desplazadas
    #   estilo CAD, sin G41; soportado SOLO Bidireccional (único fixtured).
    # - LADO C.N. + LEADS (side_l_leads / inv_side_l_app): arco de contorno con G41/G42 activo;
    #   el 1 mm de la corrección se ancla a la TANGENTE del arco; Automatic elige el lado LIBRE.
    #   Soportado solo la forma fixtured: Arco / En cota / sin velocidad / Automatic.
    # - MULTIPASADA + LEADS (mp_leads): REGLA DISTINTA observada (radio w/2 en vez de w/2×RM y
    #   lado espejado con Automatic) — fórmula subdeterminada con un solo fixture → N034.
    if spec.side_of_feature != "Center" and spec.milling_strategy is not None:
        # Lado + estrategia: Bi (N029 mp_side_l), Uni y ZigZag (N035 uni/zz_side_l) validados —
        # coordenadas desplazadas estilo CAD, sin G41.
        if spec.activate_cnc_correction:
            _fail(spec, "multipasada + lado con Corrección C.N. activa: Maestro fuerza CAD "
                        "(ACC=false); combinación sin fixture. [A3]")
    # ESTRATEGIA + LEADS (N034 9/9 + N035): arco r=(w/2)×(RM−1) — ≤0 lo omite (rm1/rm05) —,
    # lados espejados (Automatic sigue el lado de la corrección si hay lado); Lineal (approach)
    # usa w/2×RM; En bajada/subida = rampas rectas de largo `lead`; la velocidad del approach
    # PISA el feed de todo el cuerpo. Formas sin fixture → fail-loud.
    if spec.milling_strategy is not None and (
            spec.approach.is_enabled or spec.retract.is_enabled):
        # Reglas UNIFORMES Bi/Uni/ZigZag (N034 + N035 + N036: los 5 casos zz_* calzan las
        # fórmulas de multipasada exactas): Lineal en app/ret (w/2×RM), En bajada (rampa o
        # línea descendente), En subida (rampa), velocidad del app (pisa el cuerpo) y del ret
        # (solo lead-out). Triple con lado: Bi + Left/Right, Arco/En cota, velocidad OK.
        if spec.side_of_feature != "Center":
            if not type(spec.milling_strategy).__name__.startswith("Bidirectional"):
                _fail(spec, "estrategia no-Bi + lado + leads: sin fixture de referencia. [A3]")
            for lead in (spec.approach, spec.retract):
                if lead.is_enabled and (
                        (getattr(lead, "approach_type", None)
                         or getattr(lead, "retract_type", None)) != "Arc"
                        or lead.mode != "Quote" or lead.arc_side != "Automatic"):
                    _fail(spec, "triple lado+leads+estrategia: solo Arco/En cota/Automatic "
                                "(N035/N036). [A3]")
    # LADO C.N. + LEADS (N029/N035/N036): Arco o Lineal, En cota/En bajada(app)/En subida(ret),
    # velocidad propia (semántica N026) — el lado explícito del arco se IGNORA con compensación
    # (N035 arcleft: siempre el lado libre). El alejamiento Lineal (side_ret_line) y el Lineal
    # En bajada (side_app_line_down) quedaron validados en N036 — sin guardas residuales acá.
    # Estrategia MULTIPASADA en Z (N025): Uni/Bidireccional con allow_multiple_passes (con el
    # multipaso DESHABILITADO la op equivale a un fresado plano — N036 strat_single, el adapter
    # la anula). Lo no validado → fail-loud.
    strategy = spec.milling_strategy
    if strategy is not None:
        is_zigzag = type(strategy).__name__.startswith("ZigZag")
        if is_zigzag:
            # ZigZag (N025 + N036): pa/pr > 0; último hueco = 0 validado (zz_uh0, regenerado:
            # UNA sola pasada plana final); diagonal validada (zz_diag, regenerado).
            if (getattr(strategy, "feed_cutting_depth", 0.0) <= 0.0
                    or getattr(strategy, "return_cutting_depth", 0.0) <= 0.0):
                _fail(spec, "ZigZag sin pasada avance/retorno > 0. [A3]")
        elif getattr(strategy, "axial_cutting_depth", 0.0) <= 0.0:
            _fail(spec, "estrategia multipasada sin axial_cutting_depth > 0. [A3]")
        finish = 0.0 if is_zigzag else getattr(strategy, "axial_finish_cutting_depth", 0.0)
        if finish:
            # Terminación (N027 bi_cd4_f2): desbaste hasta total−finish + una pasada final.
            if finish >= (spec.depth_spec.target_depth or 0.0):
                _fail(spec, f"terminación ({finish:g}) ≥ profundidad total: sin sentido. [A3]")
        if spec.speed_changes or spec.depth_changes:
            # PERMANENTE: Maestro lo prohíbe en la UI ("No es posible aplicar una estrategia a
            # un trabajo con atributos asociados", N036 mp_vel) — un pgmx real nunca lo trae.
            _fail(spec, "estrategia + cambios en el recorrido: Maestro no permite la "
                        "combinación (N036). [A3]")
        # Pasante con estrategia: validado (N036 mp_th, pasos de cd hasta espesor+extra).
    # Approach/Retract programables (N026/N027): lead = (width/2)×radius_multiplier; arco
    # tangente (Automatic≡Right→G3, Left→G2); overlap INERTE en líneas (ov 0/0.25/5 idénticos).
    # Pasante + leads: validado (N036 leads_th). Lo no validado → fail-loud.
    if spec.approach.is_enabled or spec.retract.is_enabled:
        for lead in (spec.approach, spec.retract):
            if lead.is_enabled and lead.mode not in ("Quote", "Down", "Up"):
                _fail(spec, f"lead con mode={lead.mode!r} desconocido. [A3]")
            if lead.is_enabled and lead.arc_side not in ("Automatic", "Left", "Right"):
                _fail(spec, f"lead con arc_side={lead.arc_side!r} desconocido. [A3]")
    # Cambios durante el recorrido: validados con UN cambio por tipo, no combinados (N_RT_E001_Vel/
    # _Prof). Lo no validado → fail-loud hasta tener fixture de referencia.
    for upar, _val in (*spec.speed_changes, *spec.depth_changes):
        if not 0.0 < upar < 1.0:
            _fail(spec, f"cambio en el recorrido con UPar={upar} fuera de (0,1). [A3]")


def _validate_channel(spec: ChannelSpec) -> None:
    """Canal con la Sierra Vertical X (082) — derivado de N037 (9/9 byte-idéntico).

    Restricciones físicas (Fermín): cara superior, dirección X (Maestro NORMALIZA el sentido
    a −x: xfwd salió byte-idéntico al base), no pasante, profundidad ≤ hundimiento (10 mm).
    Lo no fixtureado → fail-loud."""
    from ._tool_catalog import _catalog_by_name

    if spec.plane_name != "Top":
        _fail(spec, f"canal en cara {spec.plane_name!r} no soportado (solo Top). [B]")
    row = _catalog_by_name().get(spec.tool_name)
    if row is None:
        _fail(spec, f"sierra {spec.tool_name!r} no está en el catálogo. [B]")
    if (row.get("type") or "").strip() != "Sierra Vertical X":
        _fail(spec, f"el canal requiere una Sierra Vertical X: {spec.tool_name!r} figura "
                    f"como {(row.get('type') or 'sin tipo')!r}. [B]")
    if spec.start_y != spec.end_y:
        _fail(spec, "canal no horizontal (la 082 solo corta en dirección X). [B]")
    if spec.depth_spec.is_through:
        _fail(spec, "canal pasante: la 082 no atraviesa (hundimiento máx 10). [B]")
    depth = spec.depth_spec.target_depth or 0.0
    geom = tool_geometry(spec.tool_name)
    if depth <= 0.0:
        _fail(spec, "canal sin profundidad. [B]")
    if depth > geom.sinking_length + 1e-9:
        _fail(spec, f"profundidad {depth:g} supera el hundimiento de la sierra "
                    f"({geom.sinking_length:g} mm). [B]")
    if spec.approach.is_enabled or spec.retract.is_enabled:
        _fail(spec, "canal + acercamiento/alejamiento: sin fixture de referencia. [B]")
    if spec.side_offset:
        _fail(spec, f"canal con rebaba {spec.side_offset:g}: sin fixture de referencia. [B]")
    if spec.side_of_feature != "Center":
        _fail(spec, f"canal con lado {spec.side_of_feature!r}: sin fixture de referencia. [B]")
    if spec.material_position != "Left":
        _fail(spec, f"canal con material_position={spec.material_position!r}: sin fixture. [B]")
    if abs(spec.end_radius - 60.0) > 1e-6 or abs(spec.slot_angle - 1.5707963267948966) > 1e-9:
        _fail(spec, "canal con end_radius/slot_angle no estándar: sin fixture de referencia. [B]")


def _validate_circle(spec: CircleSpec) -> None:
    """Fresado CIRCULAR — derivado de N038 (10/10) + N039 combos (12/12).

    Baseline: entrada por el este, dos semicírculos G3/G2 con I/J al centro, pasante ✓.
    N039: corrección Interna/Externa C.N. (side L/R, con CW/pasante/leads), estrategias
    Bi/Uni/HELICOIDAL sobre contorno cerrado, leads con û=tangente. Lo no fixtureado → fail."""
    if spec.plane_name != "Top":
        _fail(spec, f"fresado circular en cara {spec.plane_name!r} no soportado (solo Top). [B]")
    try:
        tool_geometry(spec.tool_name)
        int(spec.tool_name.lstrip("E"))
    except (KeyError, ValueError):
        _fail(spec, f"fresa {spec.tool_name!r} no está en el catálogo o su nombre no es "
                    f"E00N. [B]")
    if spec.radius <= 0.0:
        _fail(spec, f"círculo con radio {spec.radius:g}: degenerado. [B]")
    if spec.winding not in ("Clockwise", "CounterClockwise"):
        _fail(spec, f"winding={spec.winding!r} desconocido. [B]")
    if spec.side_of_feature not in ("Center", "Left", "Right"):
        _fail(spec, f"side_of_feature={spec.side_of_feature!r} desconocido. [B]")
    strategy = spec.milling_strategy
    has_leads = spec.approach.is_enabled or spec.retract.is_enabled
    if spec.side_of_feature != "Center" and strategy is not None:
        _fail(spec, "círculo con corrección + estrategia: sin fixture de referencia. [B]")
    for label, lead in (("acercamiento", spec.approach), ("alejamiento", spec.retract)):
        if not lead.is_enabled:
            continue
        lead_type = getattr(lead, "approach_type", None) or getattr(lead, "retract_type", None)
        if lead.mode != "Quote":
            _fail(spec, f"círculo + {label} En bajada/subida: sin fixture de referencia. [B]")
        if lead.speed > 0:
            _fail(spec, f"círculo + velocidad propia del {label}: sin fixture. [B]")
        if lead.arc_side != "Automatic":
            _fail(spec, f"círculo + lado explícito del arco del {label}: sin fixture "
                        "(N039 valida Automatic). [B]")
        if lead_type == "Line" and label == "alejamiento":
            _fail(spec, "círculo + alejamiento Lineal: sin fixture (N039 valida approach). [B]")
        if lead_type == "Line" and (spec.side_of_feature != "Center" or strategy is not None):
            _fail(spec, "círculo + lead Lineal con corrección/estrategia: sin fixture. [B]")
    if strategy is not None:
        name = type(strategy).__name__
        if name.startswith("Helical"):
            # HELICOIDAL (N039 heli): validada CCW, cd por vuelta, cierre con vuelta plana.
            if spec.winding != "CounterClockwise":
                _fail(spec, "helicoidal en sentido horario: sin fixture de referencia. [B]")
            if getattr(strategy, "axial_cutting_depth", 0.0) <= 0.0:
                _fail(spec, "helicoidal sin profundidad de pasada > 0. [B]")
            if getattr(strategy, "axial_finish_cutting_depth", 0.0) > 0.0:
                _fail(spec, "helicoidal con terminación: sin fixture de referencia. [B]")
            if has_leads:
                _fail(spec, "helicoidal + leads: sin fixture de referencia. [B]")
        elif name.startswith(("Bidirectional", "Unidirectional")):
            if getattr(strategy, "axial_cutting_depth", 0.0) <= 0.0:
                _fail(spec, "estrategia multipasada sin axial_cutting_depth > 0. [B]")
            if getattr(strategy, "axial_finish_cutting_depth", 0.0) > 0.0:
                _fail(spec, "círculo + terminación de estrategia: sin fixture de "
                            "referencia. [B]")
            if has_leads and name.startswith("Unidirectional"):
                _fail(spec, "círculo Uni + leads: sin fixture (N039 valida Bi). [B]")
        else:
            _fail(spec, f"estrategia {name} en círculo: sin fixture de referencia. [B]")
        if spec.depth_spec.is_through:
            _fail(spec, "círculo con estrategia + pasante: sin fixture de referencia. [B]")


def _validate_arc(spec: ArcSpec) -> None:
    """Fresado de ARCO SUELTO — derivado de N040 (10/10 byte-idéntico).

    Baseline: op de familia ROUTER; entrada por el start real, UN G3 (CCW) / G2 (CW) al end
    con I/J al centro, pasante ✓. Corrección Int/Ext, leads y estrategia → lote de combos."""
    if spec.plane_name != "Top":
        _fail(spec, f"fresado de arco en cara {spec.plane_name!r} no soportado (solo Top). [B]")
    try:
        tool_geometry(spec.tool_name)
        int(spec.tool_name.lstrip("E"))
    except (KeyError, ValueError):
        _fail(spec, f"fresa {spec.tool_name!r} no está en el catálogo o su nombre no es "
                    f"E00N. [B]")
    import math
    start_r = math.dist((spec.start_x, spec.start_y), (spec.center_x, spec.center_y))
    end_r = math.dist((spec.end_x, spec.end_y), (spec.center_x, spec.center_y))
    if start_r <= 1e-9 or not math.isclose(start_r, end_r, abs_tol=1e-6):
        _fail(spec, f"arco con radios inconsistentes (r_ini={start_r:g}, r_fin={end_r:g}) "
                    "o degenerado. [B]")
    if spec.winding not in ("Clockwise", "CounterClockwise"):
        _fail(spec, f"winding={spec.winding!r} desconocido. [B]")
    if spec.side_of_feature != "Center":
        _fail(spec, f"arco con corrección {spec.side_of_feature!r} (Interna/Externa): "
                    "sin fixture de referencia aún (lote de combos). [B]")
    if spec.approach.is_enabled or spec.retract.is_enabled:
        _fail(spec, "arco + acercamiento/alejamiento: sin fixture de referencia. [B]")
    if spec.milling_strategy is not None:
        _fail(spec, "arco + estrategia multipasada: sin fixture de referencia. [B]")


def _validate_polyline(spec: PolylineSpec) -> None:
    """Polilínea de segmentos mixtos (rectas + arcos) — derivado de N041 (baseline) + N042
    (corrección + acercamiento, abiertas y cerradas, 11/11 byte-idéntico).

    Baseline: un G-code por segmento en orden. Corrección izq/der (N042): G41/G42 + coordenadas
    NOMINALES + lead-in 1 mm sobre el 1er segmento, lead-out sobre el último (el control empalma
    las esquinas). Acercamiento: arco tangente anclado al 1er vértice. Abierta y cerrada = mismo
    mecanismo; el punto inicial (esquina o medio de segmento) y el sentido salen del orden de los
    segmentos. Lo NO fixtureado → fail-loud."""
    if spec.plane_name != "Top":
        _fail(spec, f"polilínea en cara {spec.plane_name!r} no soportada (solo Top). [B]")
    try:
        tool_geometry(spec.tool_name)
        int(spec.tool_name.lstrip("E"))
    except (KeyError, ValueError):
        _fail(spec, f"fresa {spec.tool_name!r} no está en el catálogo o su nombre no es "
                    f"E00N. [B]")
    if len(spec.segments) < 2:
        _fail(spec, "polilínea con menos de 2 segmentos. [B]")
    if spec.side_of_feature not in ("Center", "Left", "Right"):
        _fail(spec, f"polilínea con side_of_feature={spec.side_of_feature!r} desconocido. [B]")
    acc = getattr(spec, "activate_cnc_correction", True)
    if spec.milling_strategy is not None:
        # ZigZag + CAD (N046 zz_d9/d13/d18): la ÚNICA estrategia derivada sobre polilíneas —
        # la estrategia fuerza ACC=false y el render lee la Z de la curva almacenada. El resto
        # (Uni/Bi en polilínea, ZigZag con ACC=true) sigue sin fixture.
        if isinstance(spec.milling_strategy, ZigZagMillingStrategySpec) and not acc:
            _validate_polyline_cad_zigzag(spec)
            return
        _fail(spec, "polilínea + estrategia multipasada: solo ZigZag con corrección CAD tiene "
                    "fixture (N046). [B]")
    # CAD (ActivateCNCCorrection=false) tiene su propia validación (offset + arcos de esquina,
    # N043/N044). Se chequea aparte y no pasa por las reglas de leads C.N.
    if not acc:
        _validate_polyline_cad(spec)
        return
    # Corrección/lead sobre el PRIMER o ÚLTIMO segmento cuando es ARCO: sin fixture (en N042/N044
    # los extremos son siempre rectas; el lead ancla en la tangente del arco, sin derivar).
    if spec.side_of_feature != "Center" or spec.approach.is_enabled or spec.retract.is_enabled:
        if spec.segments[0].is_arc or spec.segments[-1].is_arc:
            _fail(spec, "corrección/lead con primer o último segmento en ARCO: sin "
                        "fixture de referencia. [B]")
    # Acercamiento: N042 validó Arco/En cota/Automatic/sin velocidad; N044 sumó Línea En cota/En
    # bajada, con corrección (compensado). Alejamiento (N044): Línea En cota/En subida, compensado.
    if spec.approach.is_enabled:
        _validate_poly_lead(spec, spec.approach, spec.approach.approach_type, "acercamiento")
    if spec.retract.is_enabled:
        _validate_poly_lead(spec, spec.retract, spec.retract.retract_type, "alejamiento")


def _validate_poly_lead(spec: PolylineSpec, lead, lead_type: str, name: str) -> None:
    """Un lead de polilínea (acercamiento/alejamiento). Arco: solo acercamiento En cota/Automatic
    (N042). Línea: En cota o En bajada/subida, siempre CON corrección (N044 son compensados; el
    render lineal sin corrección no está derivado). Sin velocidad propia en ningún caso."""
    if lead.speed > 0:
        _fail(spec, f"polilínea + {name} con velocidad propia: sin fixture. [B]")
    if lead_type == "Arc":
        if lead.mode != "Quote" or lead.arc_side != "Automatic":
            _fail(spec, f"polilínea + {name} Arco no En cota/Automatic: sin fixture. [B]")
        # Alejamiento en arco: solo compensado (N044 enjuego). El acercamiento en arco sí está
        # en Center (N042 closed_app).
        if name == "alejamiento" and spec.side_of_feature == "Center":
            _fail(spec, "polilínea + alejamiento en Arco SIN corrección: sin fixture (N044 "
                        "enjuego es compensado). [B]")
    elif lead_type == "Line":
        ok_mode = "Down" if name == "acercamiento" else "Up"
        if lead.mode not in ("Quote", ok_mode):
            _fail(spec, f"polilínea + {name} Línea en modo {lead.mode!r}: sin fixture "
                        f"(N044 validó En cota y {ok_mode}). [B]")
        if spec.side_of_feature == "Center":
            _fail(spec, f"polilínea + {name} Línea SIN corrección: sin fixture (N044 son "
                        f"compensados). [B]")
    else:
        _fail(spec, f"polilínea + {name} de tipo {lead_type!r} desconocido. [B]")


def _validate_polyline_cad(spec: PolylineSpec) -> None:
    """Polilínea con corrección CAD (ActivateCNCCorrection=false) — estilo B (N043 + N044): polígono
    OFFSETEADO r=w/2 hacia el lado, con ARCO en la esquina donde el offset abre un hueco (convexa
    hacia afuera) y ESQUINA VIVA donde superpone los bordes (cóncava, o convexa con offset interior).
    Byte-validado: contorno CERRADO de rectas, Right o Left, cualquier ángulo convexo, cóncavas
    como esquina viva (N044 cad_concava/interno/cw_left/chaflan). SIN fixture (los CAD los hace
    Fermín en Maestro — con ACC=false la traza almacenada ya trae el offset, autorarla sería
    circular): leads, segmentos de arco, contorno abierto, y el ARCO sobre una esquina CÓNCAVA
    (giro reflex sin derivar). Eso → fail-loud."""
    if spec.approach.is_enabled:
        _validate_cad_lead(spec, spec.approach, spec.approach.approach_type, "acercamiento")
    if spec.retract.is_enabled:
        _validate_cad_lead(spec, spec.retract, spec.retract.retract_type, "alejamiento")
    if any(seg.is_arc for seg in spec.segments):
        _fail(spec, "CAD (ACC=false) con segmentos de ARCO: el offset de un arco no tiene "
                    "fixture de referencia. [B4]")
    if not spec.is_closed:
        _fail(spec, "CAD (ACC=false) en polilínea ABIERTA: sin fixture de referencia (N043/N044 "
                    "solo cubren el contorno cerrado). [B4]")
    if spec.side_of_feature not in ("Right", "Left"):
        _fail(spec, f"CAD (ACC=false) con side_of_feature={spec.side_of_feature!r}: Center no "
                    f"define lado de offset. Solo Right/Left tienen fixture (N044). [B4]")
    _cad_contour_edge_dirs(spec)


def _cad_contour_edge_dirs(spec: PolylineSpec,
                           allow_collinear_pass: bool = False) -> list[tuple[float, float]]:
    """Direcciones unitarias de los bordes del contorno CAD cerrado, validando la geometría
    degenerada (borde de largo 0; vértice colineal, que dejaría las rectas offseteadas paralelas
    con intersección indefinida). Compartido entre el CAD single-pass y el ZigZag CAD.

    `allow_collinear_pass`: el vértice colineal en el MISMO sentido (arranque a mitad de borde,
    forma nativa del Perfilado) es pass-through — las offseteadas coinciden y no hay esquina.
    Fixtureado SOLO en la ruta ZigZag CAD (Galceado.pgmx op1); el single-pass lo sigue
    rechazando (N043/N044 arrancan en esquina). El colineal en sentido OPUESTO (espiga de ida y
    vuelta) es degenerado siempre."""
    verts = spec.points[:-1]  # cerrado: points[-1] == points[0]
    n = len(verts)
    dirs: list[tuple[float, float]] = []
    for i in range(n):
        ax, ay = verts[i]
        bx, by = verts[(i + 1) % n]
        ux, uy = bx - ax, by - ay
        lu = math.hypot(ux, uy)
        if lu <= 1e-9:
            _fail(spec, "CAD (ACC=false) con segmento degenerado (largo 0). [B4]")
        dirs.append((ux / lu, uy / lu))
    for i in range(n):
        px, py = dirs[(i - 1) % n]
        ux, uy = dirs[i]
        if abs(px * uy - py * ux) <= 1e-6:
            if allow_collinear_pass and (px * ux + py * uy) > 0.0:
                continue
            _fail(spec, "CAD (ACC=false) con vértice colineal (esquina de 180°): sin fixture y "
                        "geometría degenerada para el offset. [B4]")
    return dirs


def _validate_polyline_cad_zigzag(spec: PolylineSpec) -> None:
    """ZigZag sobre contorno CAD (N046 zz_d9/d13/d18 + Galceado.pgmx op1, byte-validado): la
    estrategia fuerza ACC=false, Maestro GENERA la Z en la curva almacenada y el ISO la COPIA
    (N046) — el converter LEE esa Z (spec.stored_trajectory) y recomputa el XY offseteado.
    Fixtureado: rectángulo CCW+Right (bordes a un eje, esquinas-arco, arranque en esquina o a
    MITAD de borde), Climb, sin Sobreposición, sin leads, con rampa (pa/pr/uh de N046, ciego y
    pasante) o UNA vuelta plana a profundidad (pa=pr=uh=0, Galceado.pgmx op1). Lo NO fixtureado
    → fail-loud."""
    strategy = spec.milling_strategy
    if strategy.cutmode != "Climb":
        _fail(spec, f"ZigZag CAD con Cutmode={strategy.cutmode!r}: solo Climb tiene fixture "
                    f"(N046). [B4]")
    if strategy.overlap:
        _fail(spec, "ZigZag CAD con Sobreposición: sin fixture (N046 usa 0). [B4]")
    if not strategy.allow_multiple_passes:
        _fail(spec, "ZigZag CAD sin multipasada: sin fixture (N046). [B4]")
    if spec.approach.is_enabled or spec.retract.is_enabled:
        _fail(spec, "ZigZag CAD + acercamiento/alejamiento: sin fixture (los zz de N046 van "
                    "pelados). [B4]")
    if any(seg.is_arc for seg in spec.segments):
        _fail(spec, "ZigZag CAD con segmentos de ARCO: sin fixture de referencia. [B4]")
    if not spec.is_closed:
        _fail(spec, "ZigZag CAD en polilínea ABIERTA: sin fixture (N046 solo cubre el contorno "
                    "cerrado). [B4]")
    if spec.side_of_feature != "Right":
        _fail(spec, f"ZigZag CAD con side_of_feature={spec.side_of_feature!r}: solo Right tiene "
                    f"fixture (N046). [B4]")
    if not getattr(spec, "stored_trajectory", ()):
        _fail(spec, "ZigZag CAD sin TrajectoryPath almacenado parseable: la rampa Z la genera "
                    "Maestro y el converter la LEE de la curva almacenada (N046). ¿El .pgmx "
                    "pasó por Maestro (agregar estrategia + Aceptar + Guardar)? [B4]")
    dirs = _cad_contour_edge_dirs(spec, allow_collinear_pass=True)
    # Lo que el zigzag agrega sobre el CAD single-pass: solo bordes paralelos a los ejes (la
    # emisión de Z en rampa sobre una DIAGONAL no está derivada) y esquinas ARCO o COLINEALES
    # pass-through (una esquina VIVA de verdad — offset que superpone — no tiene fixture en
    # vueltas alternadas).
    for ux, uy in dirs:
        if abs(ux) > 1e-9 and abs(uy) > 1e-9:
            _fail(spec, "ZigZag CAD con borde DIAGONAL: sin fixture (N046/Galceado son "
                        "rectángulos a ejes). [B4]")
    right = spec.side_of_feature == "Right"
    for i in range(len(dirs)):
        px, py = dirs[i - 1]
        ux, uy = dirs[i]
        turn = px * uy - py * ux
        if abs(turn) <= 1e-9:
            continue   # colineal pass-through (arranque a mitad de borde, Galceado.pgmx op1)
        if not (turn > 1e-9 if right else turn < -1e-9):
            _fail(spec, "ZigZag CAD con esquina VIVA (offset que superpone los bordes): sin "
                        "fixture — N046/Galceado solo cubren esquinas-arco (contorno "
                        "exterior). [B4]")


def _validate_pocket(spec: PocketSpec) -> None:
    """Vaciado (`ClosedPocket` + `BottomAndSideRoughMilling` + `ContourParallel`) — derivado
    de N047 (11 sintetizados + 2 gemelos manuales, byte-idéntico). El postprocesador COPIA la
    trayectoria ALMACENADA (los 2 envenenados salieron al ISO con el veneno) ⇒ el render LEE
    `stored_trajectories` y emite un G1 por miembro a feed de corte. Fixtureado: contorno
    rectangular a ejes, estrategia con defaults (Antihorario, LiftShiftPlunge, dentro→afuera,
    Sobreposición 50%, Climb, sin helicoidal) con o sin multipaso (cd/uh), ciego, sin
    rebaba/allowance, sin leads, sin islas, UNA trayectoria. Lo NO fixtureado → fail-loud."""
    if spec.plane_name != "Top":
        _fail(spec, f"vaciado en cara {spec.plane_name!r} no soportado (solo Top; regla de "
                    f"dominio: no hay herramental de vaciado en otras caras). [B5]")
    try:
        tool_geometry(spec.tool_name)
        int(spec.tool_name.lstrip("E"))
    except (KeyError, ValueError):
        _fail(spec, f"fresa {spec.tool_name!r} no está en el catálogo o su nombre no es "
                    f"E00N. [B5]")
    if spec.depth_spec.is_through:
        _fail(spec, "vaciado PASANTE: sin fixture de referencia (N047 es todo ciego). [B5]")
    if not (spec.depth_spec.target_depth or 0.0) > 0.0:
        _fail(spec, "vaciado sin profundidad objetivo. [B5]")
    # Leads: LEVANTADOS para Línea «En bajada»/«En subida» (Experimento-01, 2026-08-03):
    # rampa XY+Z que reemplaza el plunge/retracción vertical. Arco y los demás modos
    # siguen sin fixture.
    if spec.approach.is_enabled and not (spec.approach.approach_type == "Line"
                                         and spec.approach.mode == "Down"):
        _fail(spec, f"vaciado + acercamiento {spec.approach.approach_type}/"
                    f"{spec.approach.mode}: solo Línea En bajada tiene fixture. [B5]")
    if spec.retract.is_enabled and not (spec.retract.retract_type == "Line"
                                        and spec.retract.mode == "Up"):
        _fail(spec, f"vaciado + alejamiento {spec.retract.retract_type}/"
                    f"{spec.retract.mode}: solo Línea En subida tiene fixture. [B5]")
    if ((spec.approach.is_enabled and spec.approach.speed > 0)
            or (spec.retract.is_enabled and spec.retract.speed > 0)):
        _fail(spec, "vaciado + lead con velocidad propia: sin fixture. [B5]")
    # Avanz./Rotación de «Parámetros de trabajo» (captura UI 2026-07-29): la ventana los
    # expone pero no hay fixture ISO — sin esta guarda, un vaciado real con Avanz. cargado
    # convertía con el feed del catálogo EN SILENCIO.
    if getattr(spec, "feedrate", 0.0) > 0.0 or getattr(spec, "spindle", 0.0) > 0.0:
        _fail(spec, "vaciado con Avanz./Rotación (Parámetros de trabajo): sin fixture de "
                    "referencia aún. [B5]")
    # Rebaba (AllowanceSide) LEVANTADA por N048 (reb_p20/reb_m20, ±20 con E006): el campo
    # solo corre los anillos de la trayectoria ALMACENADA, que el render copia — no toca
    # ninguna convención de emisión. AllowanceBottom sigue sin fixture (¿la UI lo expone?
    # pregunta abierta del checklist de capturas).
    if spec.allowance_bottom:
        _fail(spec, "vaciado con AllowanceBottom: sin fixture (no sabemos si la ventana "
                    "Vaciado lo expone — checklist de capturas). [B5]")
    # ISLAS: levantada para la forma fixtureada (manual 2026-07-30, isla RECTANGULAR con
    # dos trayectorias, byte-idéntico): el render copia las trayectorias almacenadas y la
    # isla solo aporta anillos con arcos planos — la forma de la isla no toca convenciones.
    # Una isla NO rectangular (circular = polilínea muestreada en boss_contours) sigue
    # fail-loud hasta que su lote la derive.
    for boss in spec.boss_contours:
        issue = _rect_contour_issue(boss)
        if issue is not None:
            _fail(spec, f"vaciado con ISLA no rectangular a ejes ({issue}): sin fixture "
                        f"(el manual 2026-07-30 solo cubre la isla rectangular). [B5]")
    # Parámetros de la estrategia LEVANTADOS por N048 (uno aislado por fixture, 8/8
    # byte-idéntico): Dirección del recorrido (Horario/Antihorario), Conexión entre huecos
    # (LiftShiftPlunge/Straghtline — con multipaso, que es donde difieren: las transiciones
    # van DENTRO de la trayectoria almacenada), Dirección de vaciado (dentro↔afuera),
    # Sobreposición (50% y 25%) y Habilitar helicoidal (flag INVISIBLE: ni la trayectoria
    # almacenada ni el ISO cambian — Vaciado_013 ya lo vio a nivel .pgmx). Todos mediados
    # por la trayectoria copiada; ninguno toca las convenciones (feeds/orden/G-codes).
    strategy = spec.milling_strategy
    if strategy.cutmode != "Climb":
        _fail(spec, f"vaciado con Cutmode {strategy.cutmode!r}: solo Climb aparece en todo "
                    f"el corpus (sin UI conocida — checklist de capturas). [B5]")
    if strategy.allow_multiple_passes and not strategy.axial_cutting_depth > 0.0:
        _fail(spec, "vaciado multipaso sin Profundidad de hueco (AxialCuttingDepth) > 0. [B5]")
    # Contorno: cerrado, rectas, rectángulo a ejes (se toleran puntos colineales extra sobre
    # el perímetro — arranque a mitad de borde, y ruido flotante del corpus). El XY del ISO
    # sale de la trayectoria ALMACENADA, pero solo la forma rectangular tiene fixture.
    primitives = getattr(spec, "contour_primitives", ())
    if primitives:
        # Contorno de polilínea CON ARCOS — DERIVADO por Experimento-01 (2026-08-03,
        # rectángulo de esquinas redondeadas): el render copia la trayectoria almacenada
        # (rectas + arcos G2/G3) igual que en el rectangular; lo único propio son los
        # leads lineales en rampa. Fixtureado: rectas a ejes + 4 arcos CCW del MISMO radio
        # en las esquinas (la forma que la UI produce al redondear un rectángulo).
        arcs = [p for p in primitives if p.primitive_type == "Arc"]
        if len(arcs) != 4 or len({round(float(a.radius), 6) for a in arcs}) != 1:
            _fail(spec, "vaciado con contorno de arcos que NO es el rectángulo de 4 "
                        "esquinas redondeadas del mismo radio: sin fixture "
                        "(Experimento-01). [B5]")
        if any((a.normal_vector or (0.0, 0.0, 1.0))[2] <= 0.0 for a in arcs):
            _fail(spec, "vaciado con contorno de esquinas redondeadas en sentido HORARIO: "
                        "sin fixture (Experimento-01 es CCW). [B5]")
        for p in primitives:
            if (p.primitive_type == "Line"
                    and abs(p.start_point[0] - p.end_point[0]) > 1e-6
                    and abs(p.start_point[1] - p.end_point[1]) > 1e-6):
                _fail(spec, "vaciado de esquinas redondeadas con borde DIAGONAL: sin "
                            "fixture. [B5]")
    circle = getattr(spec, "contour_circle", None)
    if circle is not None:
        # Contorno CIRCULAR (manual 2026-07-30): fixtureado como ANILLO concéntrico —
        # contorno círculo + UNA isla círculo con el mismo centro. Su fixture cierra
        # FUNCIONALMENTE idéntico (143/144 líneas byte; 1 delta de 0.001 en un J que NO
        # es equidistante de los endpoints redondeados — ruido de coma flotante del
        # emisor de Maestro, confirmado por Fermín 2026-07-31: Maestro suma/resta
        # milésimas sin razón aparente y la máquina tiene precisión de 0.1 mm). La
        # clasificación byte/funcional vive en iso.synthesis.compare.
        boss_circles = getattr(spec, "boss_circles", ())
        if len(boss_circles) != 1 or spec.boss_contours:
            _fail(spec, "vaciado de contorno CIRCULAR: solo el ANILLO (círculo + UNA isla "
                        "circular) tiene fixture (manual 2026-07-30); círculo pleno o con "
                        "otras islas → sin referencia. [B5]")
        bc = boss_circles[0]
        if math.hypot(bc[0] - circle[0], bc[1] - circle[1]) > 1e-6:
            _fail(spec, "vaciado anillo con isla circular NO concéntrica: sin fixture "
                        "(el manual 2026-07-30 es concéntrico). [B5]")
        if not bc[2] < circle[2]:
            _fail(spec, "vaciado anillo con isla de radio >= contorno: geometría "
                        "inválida. [B5]")
    elif primitives:
        if getattr(spec, "boss_circles", ()) or spec.boss_contours:
            _fail(spec, "vaciado de esquinas redondeadas CON ISLAS: sin fixture "
                        "(Experimento-01 va sin islas). [B5]")
    else:
        if getattr(spec, "boss_circles", ()):
            _fail(spec, "vaciado rectangular con isla CIRCULAR: sin fixture (el manual "
                        "2026-07-30 solo cubre isla circular en contorno circular). [B5]")
        issue = _rect_contour_issue(spec.contour_points)
        if issue is not None:
            _fail(spec, f"vaciado con contorno NO rectangular a ejes ({issue}): solo el "
                        f"rectángulo (pleno o parcial, con colineales tolerados — "
                        f"N047/N049) y el círculo (anillo, manual 2026-07-30) tienen "
                        f"fixture. [B5]")
    trajectories = getattr(spec, "stored_trajectories", ())
    if not (1 <= len(trajectories) <= 2) or not all(trajectories):
        _fail(spec, f"vaciado con {len(trajectories)} trayectorias almacenadas parseables: "
                    f"hay fixture de UNA (N047) y de DOS (isla rectangular, manual "
                    f"2026-07-30); más que eso o vacías → sin referencia. ¿El .pgmx tiene "
                    f"TrajectoryPath materializado? [B5]")


def _rect_contour_issue(points) -> "str | None":
    """None si `points` es un contorno rectangular a ejes CERRADO (se toleran vértices
    colineales extra sobre el perímetro — arranque a mitad de borde, ruido flotante del
    corpus); si no, la descripción del problema. Compartido entre el contorno del vaciado
    y sus islas."""
    if len(points) < 4 or math.dist(points[0], points[-1]) > 1e-6:
        return "abierto o degenerado"
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        if abs(bx - ax) > 1e-6 and abs(by - ay) > 1e-6:
            return "borde diagonal"
    xs = [x for x, _y in points]
    ys = [y for _x, y in points]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    if max_x - min_x <= 1e-6 or max_y - min_y <= 1e-6:
        return "sin área"
    for x, y in points:
        if not (abs(x - min_x) <= 1e-6 or abs(x - max_x) <= 1e-6
                or abs(y - min_y) <= 1e-6 or abs(y - max_y) <= 1e-6):
            return "vértice interior (forma L/muesca)"
    return None


def _validate_cad_lead(spec: PolylineSpec, lead, lead_type: str, name: str) -> None:
    """Un lead de contorno CAD (N045, 6/6 byte-idéntico). Derivado: Arco y Línea, En cota,
    Automatic, sin velocidad propia, con side_of_feature=Right — barrido de RM (1/2/3) y de fresa
    (E001/E003/E004). El lead se ancla a la traza OFFSETEADA y usa las fórmulas de estrategia:
    Arco (w/2)×(RM−1) (RM=1 lo omite), Línea (w/2)×RM. Lo NO fixtureado → fail-loud."""
    if lead.speed > 0:
        _fail(spec, f"CAD (ACC=false) + {name} con velocidad propia: sin fixture. [B4]")
    if lead.mode != "Quote":
        _fail(spec, f"CAD (ACC=false) + {name} en modo {lead.mode!r}: N045 solo fixturea En cota "
                    f"(En bajada/subida sobre la traza offseteada sin derivar). [B4]")
    if lead_type not in ("Arc", "Line"):
        _fail(spec, f"CAD (ACC=false) + {name} de tipo {lead_type!r} desconocido. [B4]")
    if lead_type == "Arc" and lead.arc_side != "Automatic":
        _fail(spec, f"CAD (ACC=false) + {name} en Arco con lado {lead.arc_side!r} explícito: "
                    f"N045 solo fixturea Automatic. [B4]")
    # Automatic SIGUE el lado del offset (_mp_arc_side); con Left el arco espeja a G3 sobre la
    # traza offseteada del otro lado, y eso no tiene fixture (los 6 de N045 son Right).
    if spec.side_of_feature != "Right":
        _fail(spec, f"CAD (ACC=false) + {name} con side_of_feature={spec.side_of_feature!r}: "
                    f"solo Right tiene fixture (N045). [B4]")


