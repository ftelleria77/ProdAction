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
from pgmx.synthesis.milling.line import LineMillingSpec

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
        else:
            _fail(spec, f"operación de tipo {type(spec).__name__!r} no soportada "
                        f"(por ahora: taladro y fresado lineal). [Eje B del roadmap]")


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
    # (N023 _long) en líneas a eje, ambos sentidos, con y sin G41/G42, E004 y E001.
    if spec.is_precise:
        if spec.speed_changes or spec.depth_changes:
            _fail(spec, "corrección de longitud + cambios en el recorrido: base del UPar "
                        "ambigua. Sin fixture de referencia aún. [A3]")
        length = abs(spec.end_x - spec.start_x) + abs(spec.end_y - spec.start_y)
        if length <= spec.tool_width:
            _fail(spec, f"corrección de longitud: la línea ({length:g} mm) no supera el ancho "
                        f"de la fresa ({spec.tool_width:g} mm) — recorrido degenerado. [A3]")
    # Corrección CAD (ActivateCNCCorrection=false) CON lado elegido: la trayectoria viene
    # calculada al eje de la herramienta — EN INVESTIGACIÓN (todo lo validado es C.N.=true).
    # Emitir estilo C.N. sería una trayectoria incorrecta → fail-loud hasta derivarla (N029).
    # Con corrección CENTRADA el flag es irrelevante (no hay nada que compensar): el sintetizador
    # escribe false con estrategia multipaso y esos fixtures están byte-validados.
    # Corrección CAD (N023 _CAD, 6/6): coordenadas desplazadas radio×normal(lado), sin G41/leads,
    # entrada/salida Z estilo security. Validada en líneas a eje, single-pass, ciega. Combos → fail.
    if not spec.activate_cnc_correction and spec.milling_strategy is None:
        if spec.side_offset or spec.is_precise:
            _fail(spec, "Corrección CAD + rebaba/corrección de longitud: sin fixture. [A3]")
        if spec.approach.is_enabled or spec.retract.is_enabled:
            _fail(spec, "Corrección CAD + acercamiento/alejamiento: sin fixture. [A3]")
        if spec.speed_changes or spec.depth_changes:
            _fail(spec, "Corrección CAD + cambios en el recorrido: sin fixture. [A3]")
        if spec.depth_spec.is_through:
            _fail(spec, "Corrección CAD + pasante: sin fixture. [A3]")
    # Corrección de herramienta (side Left/Right → G41/G42, radio del SVR): validada en N023 sobre
    # líneas alineadas a eje, ambos sentidos, sin combinar con cambios de recorrido.
    if spec.side_of_feature not in ("Center", "Left", "Right"):
        _fail(spec, f"side_of_feature={spec.side_of_feature!r} desconocido. [A3]")
    if spec.side_of_feature != "Center":
        if spec.speed_changes or spec.depth_changes:
            _fail(spec, "corrección de herramienta combinada con cambios de velocidad/profundidad "
                        "en el recorrido: sin fixture de referencia aún. [A3]")
    # Invertir trabajo (N023 _invert): validado en Center y lados C.N. (incl. E001/Y/xrev).
    if spec.invert_work and (
            spec.speed_changes or spec.depth_changes or spec.milling_strategy is not None
            or spec.is_precise or spec.side_offset or not spec.activate_cnc_correction):
        _fail(spec, "Invertir trabajo combinado con cambios/estrategia/leads/longitud/rebaba/CAD: "
                    "sin fixture de referencia. [A3]")
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
        if not type(spec.milling_strategy).__name__.startswith("Bidirectional"):
            _fail(spec, "corrección de lado + estrategia no Bidireccional: sin fixture "
                        "(N029 valida solo Bi). [A3]")
        if spec.activate_cnc_correction:
            _fail(spec, "multipasada + lado con Corrección C.N. activa: Maestro fuerza CAD "
                        "(ACC=false); combinación sin fixture. [A3]")
    if spec.milling_strategy is not None and (
            spec.approach.is_enabled or spec.retract.is_enabled):
        _fail(spec, "multipasada + acercamiento/alejamiento: regla de lead distinta observada "
                    "(N029 mp_leads: radio w/2, lado espejado) — subdeterminada; derivar con "
                    "N034. [A3]")
    if spec.side_of_feature != "Center" and spec.activate_cnc_correction:
        for lead in (spec.approach, spec.retract):
            if not lead.is_enabled:
                continue
            lead_type = getattr(lead, "approach_type", None) or getattr(lead, "retract_type", None)
            if lead_type != "Arc":
                _fail(spec, "lado C.N. + lead Lineal: sin fixture (N029 valida Arco). [A3]")
            if lead.mode != "Quote":
                _fail(spec, "lado C.N. + lead En bajada/subida: sin fixture "
                            "(N029 valida En cota). [A3]")
            if lead.speed > 0:
                _fail(spec, "lado C.N. + velocidad propia del lead: sin fixture. [A3]")
            if lead.arc_side != "Automatic":
                _fail(spec, "lado C.N. + lado explícito del arco del lead: sin fixture "
                            "(N029 valida Automatic → lado libre). [A3]")
    # Estrategia MULTIPASADA en Z (N025): Uni/Bidireccional con allow_multiple_passes. Lo no
    # validado → fail-loud.
    strategy = spec.milling_strategy
    if strategy is not None:
        if not getattr(strategy, "allow_multiple_passes", False):
            _fail(spec, "estrategia sin allow_multiple_passes (modo 'pre-cast' de una pasada): "
                        "sin fixture de referencia. [A3]")
        is_zigzag = type(strategy).__name__.startswith("ZigZag")
        if is_zigzag:
            # ZigZag (N025): validado con pa/pr/uh > 0 sobre línea a eje.
            if (getattr(strategy, "feed_cutting_depth", 0.0) <= 0.0
                    or getattr(strategy, "return_cutting_depth", 0.0) <= 0.0):
                _fail(spec, "ZigZag sin pasada avance/retorno > 0. [A3]")
            if getattr(strategy, "axial_finish_cutting_depth", 0.0) <= 0.0:
                _fail(spec, "ZigZag con último hueco = 0: sin fixture de referencia. [A3]")
        elif getattr(strategy, "axial_cutting_depth", 0.0) <= 0.0:
            _fail(spec, "estrategia multipasada sin axial_cutting_depth > 0. [A3]")
        finish = 0.0 if is_zigzag else getattr(strategy, "axial_finish_cutting_depth", 0.0)
        if finish:
            # Terminación (N027 bi_cd4_f2): desbaste hasta total−finish + una pasada final.
            if finish >= (spec.depth_spec.target_depth or 0.0):
                _fail(spec, f"terminación ({finish:g}) ≥ profundidad total: sin sentido. [A3]")
        if is_zigzag and spec.start_x != spec.end_x and spec.start_y != spec.end_y:
            _fail(spec, "ZigZag sobre línea DIAGONAL: sin fixture de referencia. [A3]")
        if spec.speed_changes or spec.depth_changes:
            _fail(spec, "multipasada + cambios en el recorrido: sin fixture de referencia. [A3]")
        if spec.depth_spec.is_through:
            _fail(spec, "multipasada + pasante: sin fixture de referencia. [A3]")
    # Approach/Retract programables (N026/N027): lead = (width/2)×radius_multiplier; arco
    # tangente (Automatic≡Right→G3, Left→G2); overlap INERTE en líneas (ov 0/0.25/5 idénticos).
    # Lo no validado → fail-loud.
    if spec.approach.is_enabled or spec.retract.is_enabled:
        if spec.depth_spec.is_through:
            _fail(spec, "approach/retract + pasante: sin fixture de referencia. [A3]")
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
