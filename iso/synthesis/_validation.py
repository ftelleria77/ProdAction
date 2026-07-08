"""Validación fail-loud del converter PGMX→ISO.

El converter solo cubre un subconjunto de operaciones/parámetros (los validados en
los lotes N00x). Antes de convertir, esta capa detecta cualquier operación o
parámetro fuera de ese subconjunto y aborta con un mensaje claro y accionable,
en lugar de crashear con un KeyError o —peor— emitir ISO incompleto en silencio.

Cada límite referencia la fase del roadmap que lo levantará
(ver memoria project-converter-roadmap).
"""

from __future__ import annotations

from typing import Iterable

from pgmx.synthesis.drilling.pattern import DrillingPatternSpec
from pgmx.synthesis.drilling.single import DrillingSpec
from pgmx.synthesis.milling.arc import ArcMillingSpec
from pgmx.synthesis.milling.circle import CircleMillingSpec
from pgmx.synthesis.milling.line import LineMillingSpec
from pgmx.synthesis.milling.slot import SlotMillingSpec

from ._machine import SIDE_FACE, TOP_TOOL, TOP_TOOL_CONICAL, top_tool_or_none
from ._tool_catalog import tool_geometry

__all__ = ["UnsupportedOperationError", "validate_entries"]


class UnsupportedOperationError(ValueError):
    """El .pgmx contiene una operación o parámetro que el converter aún no soporta."""


_SUPPORTED_DRILL_FACES = frozenset({"Top", *SIDE_FACE})


def _top_tool_supported(spec: DrillingSpec) -> bool:
    """Soportada si resuelve a una herramienta vertical conocida (por la herramienta
    seleccionada o por punta+diámetro). Mismo criterio que el render."""
    return top_tool_or_none(spec.diameter, spec.drill_family, spec.tool_name) is not None


def validate_entries(entries: Iterable[object]) -> None:
    """Valida todas las entries del programa. Lanza ``UnsupportedOperationError``."""
    for entry in entries:
        spec = getattr(entry, "spec", entry)
        if isinstance(spec, DrillingSpec):
            _validate_drilling(spec)
        elif isinstance(spec, DrillingPatternSpec):
            _validate_drilling_pattern(spec)
        elif isinstance(spec, LineMillingSpec):
            _validate_line_milling(spec)
        elif isinstance(spec, SlotMillingSpec):
            _validate_slot_milling(spec)
        elif isinstance(spec, CircleMillingSpec):
            _validate_circle_milling(spec)
        elif isinstance(spec, ArcMillingSpec):
            _validate_arc_milling(spec)
        else:
            _fail(spec, f"operación de tipo {type(spec).__name__!r} no soportada "
                        f"(por ahora: taladro, fresado lineal/circular y canal). "
                        f"[Eje B del roadmap]")


def _fail(spec: object, detail: str) -> None:
    feat = getattr(spec, "feature_name", "?")
    raise UnsupportedOperationError(f"Feature '{feat}': {detail}")


def _validate_drilling(spec: DrillingSpec) -> None:
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


def _validate_drilling_pattern(spec: DrillingPatternSpec) -> None:
    """Un patrón se expande a taladros individuales idénticos al base (N008): validamos
    el agujero base con las mismas reglas. El adapter ya garantiza rectangular/0/90."""
    base = DrillingSpec(
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
    _validate_drilling(base)


def _validate_line_milling(spec: LineMillingSpec) -> None:
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


def _validate_slot_milling(spec: SlotMillingSpec) -> None:
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


def _validate_circle_milling(spec: CircleMillingSpec) -> None:
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


def _validate_arc_milling(spec: ArcMillingSpec) -> None:
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
