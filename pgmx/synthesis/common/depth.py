"""Depth contracts and normalization for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Sequence

from .xml import _safe_float, _text, _xsi_type

__all__ = [
    "DepthSpec",
    "MillingDepthSpec",
    "build_depth_spec",
    "build_milling_depth_spec",
    "_extract_depth_spec_from_template",
    "_normalize_milling_depth_spec",
]


@dataclass(frozen=True)
class MillingDepthSpec:
    """Configuracion reutilizable de profundidad para un fresado."""

    is_through: bool = True
    target_depth: Optional[float] = None
    extra_depth: float = 0.0


DepthSpec = MillingDepthSpec


def build_milling_depth_spec(
    is_through: Optional[bool] = None,
    *,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
) -> MillingDepthSpec:
    """Construye un `MillingDepthSpec` reusable para Pasante/Extra/Profundidad.

    Reglas:
    - si no se pasa nada, devuelve el default observado en Maestro
    - si `is_through=True`, `extra_depth` representa `Extra`
    - si `is_through=False`, `target_depth` es obligatorio y `extra_depth` no aplica
    - Maestro permite `target_depth = 0` como estado manual neutro/default para
      un fresado no pasante recien creado; por eso se admite `0` al leer o
      construir plantillas
    """

    has_explicit_configuration = any(value is not None for value in (is_through, target_depth, extra_depth))
    if not has_explicit_configuration:
        return MillingDepthSpec()

    normalized_is_through = (target_depth is None) if is_through is None else bool(is_through)
    if normalized_is_through:
        extra_value = 0.0 if extra_depth is None else float(extra_depth)
        if extra_value < -1e-9:
            raise ValueError("ExtraDepth no puede ser negativo.")
        return MillingDepthSpec(is_through=True, target_depth=None, extra_depth=extra_value)

    if target_depth is None:
        raise ValueError("Para un fresado no pasante hay que indicar target_depth.")
    target_depth_value = float(target_depth)
    if target_depth_value < 0.0:
        raise ValueError("La profundidad no pasante debe ser mayor o igual a cero.")
    extra_value = 0.0 if extra_depth is None else float(extra_depth)
    if not math.isclose(extra_value, 0.0, abs_tol=1e-9):
        raise ValueError("ExtraDepth solo aplica a fresados pasantes.")
    return MillingDepthSpec(is_through=False, target_depth=target_depth_value, extra_depth=0.0)


def build_depth_spec(
    is_through: Optional[bool] = None,
    *,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
) -> DepthSpec:
    return build_milling_depth_spec(
        is_through=is_through,
        target_depth=target_depth,
        extra_depth=extra_depth,
    )


def _normalize_milling_depth_spec(depth_spec: Optional[MillingDepthSpec]) -> MillingDepthSpec:
    if depth_spec is None:
        return MillingDepthSpec()
    return build_milling_depth_spec(
        is_through=depth_spec.is_through,
        target_depth=depth_spec.target_depth,
        extra_depth=depth_spec.extra_depth,
    )


def _extract_depth_spec_from_template(
    feature: ET.Element,
    operation: ET.Element,
    matching_expressions: Sequence[ET.Element],
    depth_variable_name: str,
) -> MillingDepthSpec:
    expression_values = {
        _text(node, "./{*}Property/{*}InnerField/{*}Name"): _text(node, "./{*}Value")
        for node in matching_expressions
        if _text(node, "./{*}Property/{*}Name") == "Depth"
    }
    bottom_condition_type = _xsi_type(feature.find("./{*}BottomCondition"))
    overcut_length = _safe_float(_text(operation, "./{*}OvercutLength"), 0.0)
    if "ThroughMillingBottom" in bottom_condition_type or (
        expression_values.get("StartDepth") == depth_variable_name
        and expression_values.get("EndDepth") == depth_variable_name
    ):
        return build_milling_depth_spec(is_through=True, extra_depth=overcut_length)

    start_depth = _safe_float(_text(feature, "./{*}Depth/{*}StartDepth"), 0.0)
    end_depth = _safe_float(_text(feature, "./{*}Depth/{*}EndDepth"), 0.0)
    if not math.isclose(start_depth, end_depth, abs_tol=1e-6):
        raise ValueError("La plantilla usa profundidades distintas para StartDepth/EndDepth; caso no soportado aun.")
    return build_milling_depth_spec(is_through=False, target_depth=start_depth)
