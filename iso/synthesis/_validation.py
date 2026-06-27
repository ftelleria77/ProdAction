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

__all__ = ["UnsupportedOperationError", "validate_entries"]


class UnsupportedOperationError(ValueError):
    """El .pgmx contiene una operación o parámetro que el converter aún no soporta."""


_SUPPORTED_DRILL_FACES = frozenset({"Top", *SIDE_FACE})
_ROUTER_TOOL = "E004"


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
    if spec.tool_name != _ROUTER_TOOL:
        _fail(spec, f"fresa {spec.tool_name!r} no soportada (solo {_ROUTER_TOOL}). [A3]")
    if spec.depth_spec.is_through:
        _fail(spec, "fresado lineal pasante (is_through) no soportado aún. [A3]")
    if spec.side_of_feature != "Center":
        _fail(spec, f"side_of_feature={spec.side_of_feature!r} no soportado aún "
                    f"(solo Center). [A3]")
    if spec.milling_strategy is not None:
        _fail(spec, "milling_strategy en fresado lineal no soportada aún. [A3]")
