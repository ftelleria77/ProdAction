"""Milling strategy contracts and normalization for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

from .geometry import (
    GeometryPrimitiveSpec,
    GeometryProfileSpec,
    _is_closed_polyline_points,
    _line_primitive_3d,
    _primitive_start_tangent_2d,
    _profile_at_z,
    _profile_endpoint_points,
    _reverse_profile_geometry,
    _vertical_transition_primitive,
    build_composite_geometry_profile,
)
from .xml import (
    PGMX_NS,
    STRATEGY_NS,
    XSI_NS,
    _append_node,
    _compact_number,
    _qname,
    _safe_bool,
    _safe_float,
    _set_xmlns,
    _text,
    _xsi_type,
)

__all__ = [
    "BidirectionalMillingStrategySpec",
    "ContourParallelMillingStrategySpec",
    "HelicalMillingStrategySpec",
    "MillingStrategySpec",
    "UnidirectionalMillingStrategySpec",
    "build_bidirectional_milling_strategy_spec",
    "build_contour_parallel_milling_strategy_spec",
    "build_helical_milling_strategy_spec",
    "build_unidirectional_milling_strategy_spec",
    "_ensure_milling_strategy_allowed",
    "_extract_milling_strategy_spec_from_operation",
    "_build_milling_strategy_node",
    "_build_bidirectional_line_strategy_profile",
    "_build_bidirectional_open_profile_strategy_toolpath",
    "_build_closed_profile_strategy_toolpath",
    "_build_helical_arc_primitive",
    "_build_helical_circle_strategy_toolpath",
    "_build_unidirectional_line_strategy_profile",
    "_build_unidirectional_open_profile_strategy_toolpath",
    "_normalize_milling_strategy_spec",
    "_normalize_strategy_connection_mode",
    "_helical_rough_end_levels",
    "_strategy_is_multilevel",
    "_strategy_comparison_key",
    "_strategy_pass_levels",
    "_should_activate_cnc_correction",
    "_spec_uses_closed_profile",
    "_serialize_unidirectional_connection_mode",
    "_resolve_unidirectional_connection_mode",
]


@dataclass(frozen=True)
class UnidirectionalMillingStrategySpec:
    """Estrategia `Unidireccional` observada en Maestro para fresados."""

    connection_mode: str = "Automatic"
    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0


@dataclass(frozen=True)
class BidirectionalMillingStrategySpec:
    """Estrategia `Bidireccional` observada en Maestro para fresados."""

    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0


@dataclass(frozen=True)
class HelicalMillingStrategySpec:
    """Estrategia `Helicoidal` observada en Maestro para fresados circulares."""

    axial_cutting_depth: float = 0.0
    allows_finish_cutting: bool = True
    axial_finish_cutting_depth: float = 0.0


@dataclass(frozen=True)
class ContourParallelMillingStrategySpec:
    """Estrategia `Paralela al perfil/contorno` observada para vaciados."""

    rotation_direction: str = "CounterClockwise"
    stroke_connection_strategy: str = "LiftShiftPlunge"
    inside_to_outside: bool = True
    overlap: float = 0.5
    is_helic_strategy: bool = False
    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0
    cutmode: str = "Climb"
    is_internal: bool = True
    radial_cutting_depth: float = 0.0
    radial_finish_cutting_depth: float = 0.0
    allows_bidirectional: bool = False
    allows_finish_cutting: bool = False


MillingStrategySpec = (
    UnidirectionalMillingStrategySpec
    | BidirectionalMillingStrategySpec
    | HelicalMillingStrategySpec
    | ContourParallelMillingStrategySpec
)


def _normalize_strategy_connection_mode(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "salidaacotadeseguridad": "SafetyHeight",
        "salidacota": "SafetyHeight",
        "securityheight": "SafetyHeight",
        "safetyheight": "SafetyHeight",
        "liftshiftplunge": "SafetyHeight",
        "enlapieza": "InPiece",
        "inpiece": "InPiece",
        "straightline": "InPiece",
        "straghtline": "InPiece",
    }
    if raw not in mapping:
        raise ValueError(
            "ConnectionMode invalido. Valores admitidos: Automatic, SafetyHeight/SalidaCota o InPiece/EnLaPieza."
        )
    return mapping[raw]


def _normalize_nonnegative_strategy_depth(value: Optional[float], field_name: str) -> float:
    normalized = 0.0 if value is None else float(value)
    if normalized < -1e-9:
        raise ValueError(f"{field_name} no puede ser negativo.")
    return normalized


def _normalize_contour_rotation_direction(value: Optional[str]) -> str:
    raw = (value or "CounterClockwise").strip()
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "counterclockwise": "CounterClockwise",
        "anticlockwise": "CounterClockwise",
        "antihorario": "CounterClockwise",
        "clockwise": "Clockwise",
        "horario": "Clockwise",
    }
    return mapping.get(normalized, raw)


def _normalize_contour_stroke_connection_strategy(value: Optional[str]) -> str:
    raw = (value or "LiftShiftPlunge").strip()
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "liftshiftplunge": "LiftShiftPlunge",
        "salidaacotadeseguridad": "LiftShiftPlunge",
        "salidacotadeseguridad": "LiftShiftPlunge",
        "safetyheight": "LiftShiftPlunge",
        "straghtline": "Straghtline",
        "straightline": "Straghtline",
        "enlapieza": "Straghtline",
        "inpiece": "Straghtline",
    }
    return mapping.get(normalized, raw)


def _normalize_contour_cutmode(value: Optional[str]) -> str:
    raw = (value or "Climb").strip()
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "climb": "Climb",
        "concordante": "Climb",
        "conventional": "Conventional",
        "convencional": "Conventional",
    }
    return mapping.get(normalized, raw)


def build_unidirectional_milling_strategy_spec(
    *,
    connection_mode: Optional[str] = None,
    allow_multiple_passes: Optional[bool] = None,
    axial_cutting_depth: Optional[float] = None,
    axial_finish_cutting_depth: Optional[float] = None,
) -> UnidirectionalMillingStrategySpec:
    """Construye una estrategia publica `Unidireccional`.

    `connection_mode` usa nombres canonicos orientados a API:
    - `Automatic`
    - `SafetyHeight` (UI Maestro: Salida a cota de seguridad)
    - `InPiece` (UI Maestro: En la pieza)
    """

    normalized_axial_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_cutting_depth,
        "AxialCuttingDepth",
    )
    normalized_axial_finish_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_finish_cutting_depth,
        "AxialFinishCuttingDepth",
    )
    inferred_allow_multiple_passes = (
        normalized_axial_cutting_depth > 0.0 or normalized_axial_finish_cutting_depth > 0.0
    )
    normalized_allow_multiple_passes = (
        inferred_allow_multiple_passes if allow_multiple_passes is None else bool(allow_multiple_passes)
    )
    if not normalized_allow_multiple_passes and inferred_allow_multiple_passes:
        raise ValueError(
            "No se puede deshabilitar AllowMultiplePasses si AxialCuttingDepth o "
            "AxialFinishCuttingDepth son mayores que cero."
        )
    return UnidirectionalMillingStrategySpec(
        connection_mode=_normalize_strategy_connection_mode(connection_mode),
        allow_multiple_passes=normalized_allow_multiple_passes,
        axial_cutting_depth=normalized_axial_cutting_depth,
        axial_finish_cutting_depth=normalized_axial_finish_cutting_depth,
    )


def build_bidirectional_milling_strategy_spec(
    *,
    allow_multiple_passes: Optional[bool] = None,
    axial_cutting_depth: Optional[float] = None,
    axial_finish_cutting_depth: Optional[float] = None,
) -> BidirectionalMillingStrategySpec:
    """Construye una estrategia publica `Bidireccional`."""

    normalized_axial_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_cutting_depth,
        "AxialCuttingDepth",
    )
    normalized_axial_finish_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_finish_cutting_depth,
        "AxialFinishCuttingDepth",
    )
    inferred_allow_multiple_passes = (
        normalized_axial_cutting_depth > 0.0 or normalized_axial_finish_cutting_depth > 0.0
    )
    normalized_allow_multiple_passes = (
        inferred_allow_multiple_passes if allow_multiple_passes is None else bool(allow_multiple_passes)
    )
    if not normalized_allow_multiple_passes and inferred_allow_multiple_passes:
        raise ValueError(
            "No se puede deshabilitar AllowMultiplePasses si AxialCuttingDepth o "
            "AxialFinishCuttingDepth son mayores que cero."
        )
    return BidirectionalMillingStrategySpec(
        allow_multiple_passes=normalized_allow_multiple_passes,
        axial_cutting_depth=normalized_axial_cutting_depth,
        axial_finish_cutting_depth=normalized_axial_finish_cutting_depth,
    )


def build_helical_milling_strategy_spec(
    *,
    axial_cutting_depth: Optional[float] = None,
    allows_finish_cutting: Optional[bool] = None,
    axial_finish_cutting_depth: Optional[float] = None,
) -> HelicalMillingStrategySpec:
    """Construye una estrategia publica `Helicoidal`.

    Por ahora esta familia queda validada solo para `CircleMillingSpec`.
    """

    normalized_axial_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_cutting_depth,
        "AxialCuttingDepth",
    )
    normalized_axial_finish_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_finish_cutting_depth,
        "AxialFinishCuttingDepth",
    )
    normalized_allows_finish_cutting = True if allows_finish_cutting is None else bool(allows_finish_cutting)
    if not normalized_allows_finish_cutting and normalized_axial_finish_cutting_depth > 0.0:
        raise ValueError(
            "No se puede definir AxialFinishCuttingDepth mayor que cero si AllowsFinishCutting esta deshabilitado."
        )
    return HelicalMillingStrategySpec(
        axial_cutting_depth=normalized_axial_cutting_depth,
        allows_finish_cutting=normalized_allows_finish_cutting,
        axial_finish_cutting_depth=normalized_axial_finish_cutting_depth,
    )


def build_contour_parallel_milling_strategy_spec(
    *,
    rotation_direction: Optional[str] = None,
    stroke_connection_strategy: Optional[str] = None,
    inside_to_outside: Optional[bool] = None,
    overlap: Optional[float] = None,
    is_helic_strategy: Optional[bool] = None,
    allow_multiple_passes: Optional[bool] = None,
    axial_cutting_depth: Optional[float] = None,
    axial_finish_cutting_depth: Optional[float] = None,
    cutmode: Optional[str] = None,
    is_internal: Optional[bool] = None,
    radial_cutting_depth: Optional[float] = None,
    radial_finish_cutting_depth: Optional[float] = None,
    allows_bidirectional: Optional[bool] = None,
    allows_finish_cutting: Optional[bool] = None,
) -> ContourParallelMillingStrategySpec:
    """Construye una estrategia `Paralela al perfil/contorno` para lectura.

    La serializacion productiva de esta estrategia todavia no esta habilitada.
    """

    normalized_overlap = 0.5 if overlap is None else float(overlap)
    if normalized_overlap < -1e-9:
        raise ValueError("Overlap no puede ser negativo.")
    return ContourParallelMillingStrategySpec(
        rotation_direction=_normalize_contour_rotation_direction(rotation_direction),
        stroke_connection_strategy=_normalize_contour_stroke_connection_strategy(stroke_connection_strategy),
        inside_to_outside=True if inside_to_outside is None else bool(inside_to_outside),
        overlap=normalized_overlap,
        is_helic_strategy=False if is_helic_strategy is None else bool(is_helic_strategy),
        allow_multiple_passes=False if allow_multiple_passes is None else bool(allow_multiple_passes),
        axial_cutting_depth=_normalize_nonnegative_strategy_depth(axial_cutting_depth, "AxialCuttingDepth"),
        axial_finish_cutting_depth=_normalize_nonnegative_strategy_depth(
            axial_finish_cutting_depth,
            "AxialFinishCuttingDepth",
        ),
        cutmode=_normalize_contour_cutmode(cutmode),
        is_internal=True if is_internal is None else bool(is_internal),
        radial_cutting_depth=_normalize_nonnegative_strategy_depth(radial_cutting_depth, "RadialCuttingDepth"),
        radial_finish_cutting_depth=_normalize_nonnegative_strategy_depth(
            radial_finish_cutting_depth,
            "RadialFinishCuttingDepth",
        ),
        allows_bidirectional=False if allows_bidirectional is None else bool(allows_bidirectional),
        allows_finish_cutting=False if allows_finish_cutting is None else bool(allows_finish_cutting),
    )


def _strategy_is_multilevel(strategy: Optional[MillingStrategySpec]) -> bool:
    normalized_strategy = _normalize_milling_strategy_spec(strategy)
    if normalized_strategy is None:
        return False
    if isinstance(normalized_strategy, HelicalMillingStrategySpec):
        return True
    if not normalized_strategy.allow_multiple_passes:
        return False
    return (
        normalized_strategy.axial_cutting_depth > 0.0
        or normalized_strategy.axial_finish_cutting_depth > 0.0
    )


def _should_activate_cnc_correction(spec) -> bool:
    return not _strategy_is_multilevel(spec.milling_strategy)


def _spec_uses_closed_profile(spec) -> bool:
    if type(spec).__name__ in {
        "_HydratedCircleMillingSpec",
        "CircleMillingSpec",
        "_HydratedSquaringMillingSpec",
        "SquaringMillingSpec",
    }:
        return True
    points = getattr(spec, "points", None)
    if points is None:
        return False
    return _is_closed_polyline_points(points)


def _resolve_unidirectional_connection_mode(
    strategy: UnidirectionalMillingStrategySpec,
    *,
    is_closed_profile: bool,
) -> str:
    if strategy.connection_mode != "Automatic":
        return strategy.connection_mode
    return "InPiece" if is_closed_profile else "SafetyHeight"


def _serialize_unidirectional_connection_mode(connection_mode: str) -> str:
    normalized_connection_mode = _normalize_strategy_connection_mode(connection_mode)
    return {
        "Automatic": "LiftShiftPlunge",
        "SafetyHeight": "LiftShiftPlunge",
        "InPiece": "Straghtline",
    }[normalized_connection_mode]


def _build_milling_strategy_node(spec) -> ET.Element:
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return ET.Element(_qname(PGMX_NS, "MachiningStrategy"), {f"{{{XSI_NS}}}nil": "true"})
    if isinstance(strategy, ContourParallelMillingStrategySpec):
        node = ET.Element(
            _qname(PGMX_NS, "MachiningStrategy"),
            {f"{{{XSI_NS}}}type": "b:ContourParallel"},
        )
        _set_xmlns(node, "b", STRATEGY_NS)
        _append_node(node, PGMX_NS, "AllowMultiplePasses", "true" if strategy.allow_multiple_passes else "false")
        _append_node(node, PGMX_NS, "Overlap", _compact_number(strategy.overlap))
        _append_node(node, STRATEGY_NS, "AllowsBidirectional", "true" if strategy.allows_bidirectional else "false")
        _append_node(node, STRATEGY_NS, "AllowsFinishCutting", "true" if strategy.allows_finish_cutting else "false")
        _append_node(node, STRATEGY_NS, "AxialCuttingDepth", _compact_number(strategy.axial_cutting_depth))
        _append_node(node, STRATEGY_NS, "AxialFinishCuttingDepth", _compact_number(strategy.axial_finish_cutting_depth))
        _append_node(node, STRATEGY_NS, "Cutmode", strategy.cutmode)
        _append_node(node, STRATEGY_NS, "InsideToOutSide", "true" if strategy.inside_to_outside else "false")
        _append_node(node, STRATEGY_NS, "IsHelicStrategy", "true" if strategy.is_helic_strategy else "false")
        _append_node(node, STRATEGY_NS, "IsInternal", "true" if strategy.is_internal else "false")
        _append_node(node, STRATEGY_NS, "RadialCuttingDepth", _compact_number(strategy.radial_cutting_depth))
        _append_node(node, STRATEGY_NS, "RadialFinishCuttingDepth", _compact_number(strategy.radial_finish_cutting_depth))
        _append_node(node, STRATEGY_NS, "RotationDirection", strategy.rotation_direction)
        _append_node(node, STRATEGY_NS, "StrokeConnectionStrategy", strategy.stroke_connection_strategy)
        return node

    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        strategy_type = "b:UnidirectionalMilling"
        stroke_connection_strategy = _serialize_unidirectional_connection_mode(
            _resolve_unidirectional_connection_mode(
                strategy,
                is_closed_profile=_spec_uses_closed_profile(spec),
            )
        )
    elif isinstance(strategy, BidirectionalMillingStrategySpec):
        strategy_type = "b:BidirectionalMilling"
        stroke_connection_strategy = "Straghtline"
    else:
        strategy_type = "b:HelicMilling"
        stroke_connection_strategy = "Straghtline"

    node = ET.Element(
        _qname(PGMX_NS, "MachiningStrategy"),
        {f"{{{XSI_NS}}}type": strategy_type},
    )
    _set_xmlns(node, "b", STRATEGY_NS)
    if isinstance(strategy, HelicalMillingStrategySpec):
        _append_node(node, PGMX_NS, "AllowMultiplePasses", "false")
    else:
        _append_node(node, PGMX_NS, "AllowMultiplePasses", "true" if strategy.allow_multiple_passes else "false")
    _append_node(node, PGMX_NS, "Overlap", "0")
    if isinstance(strategy, HelicalMillingStrategySpec):
        _append_node(node, STRATEGY_NS, "AllowsFinishCutting", "true" if strategy.allows_finish_cutting else "false")
    _append_node(node, STRATEGY_NS, "AxialCuttingDepth", _compact_number(strategy.axial_cutting_depth))
    _append_node(node, STRATEGY_NS, "AxialFinishCuttingDepth", _compact_number(strategy.axial_finish_cutting_depth))
    _append_node(node, STRATEGY_NS, "Cutmode", "Climb")
    _append_node(node, STRATEGY_NS, "RadialCuttingDepth", "0")
    _append_node(node, STRATEGY_NS, "RadialFinishCuttingDepth", "0")
    _append_node(node, STRATEGY_NS, "StrokeConnectionStrategy", stroke_connection_strategy)
    return node


def _strategy_comparison_key(
    strategy: Optional[MillingStrategySpec],
    *,
    is_closed_profile: bool,
) -> Optional[tuple[object, ...]]:
    normalized_strategy = _normalize_milling_strategy_spec(strategy)
    if normalized_strategy is None:
        return None
    if isinstance(normalized_strategy, UnidirectionalMillingStrategySpec):
        return (
            "Unidirectional",
            _resolve_unidirectional_connection_mode(
                normalized_strategy,
                is_closed_profile=is_closed_profile,
            ),
            normalized_strategy.allow_multiple_passes,
            normalized_strategy.axial_cutting_depth,
            normalized_strategy.axial_finish_cutting_depth,
        )
    if isinstance(normalized_strategy, HelicalMillingStrategySpec):
        return (
            "Helical",
            normalized_strategy.allows_finish_cutting,
            normalized_strategy.axial_cutting_depth,
            normalized_strategy.axial_finish_cutting_depth,
        )
    if isinstance(normalized_strategy, ContourParallelMillingStrategySpec):
        return (
            "ContourParallel",
            normalized_strategy.rotation_direction,
            normalized_strategy.stroke_connection_strategy,
            normalized_strategy.inside_to_outside,
            normalized_strategy.overlap,
            normalized_strategy.is_helic_strategy,
            normalized_strategy.allow_multiple_passes,
            normalized_strategy.axial_cutting_depth,
            normalized_strategy.axial_finish_cutting_depth,
            normalized_strategy.cutmode,
            normalized_strategy.is_internal,
            normalized_strategy.radial_cutting_depth,
            normalized_strategy.radial_finish_cutting_depth,
            normalized_strategy.allows_bidirectional,
            normalized_strategy.allows_finish_cutting,
        )
    return (
        "Bidirectional",
        normalized_strategy.allow_multiple_passes,
        normalized_strategy.axial_cutting_depth,
        normalized_strategy.axial_finish_cutting_depth,
    )


def _extract_milling_strategy_spec_from_operation(
    operation: ET.Element,
) -> Optional[MillingStrategySpec]:
    strategy_node = operation.find("./{*}MachiningStrategy")
    if strategy_node is None:
        return None
    if (strategy_node.get(f"{{{XSI_NS}}}nil") or "").strip().lower() == "true":
        return None

    strategy_type = _xsi_type(strategy_node)
    allow_multiple_passes = _safe_bool(_text(strategy_node, "./{*}AllowMultiplePasses"), False)
    allows_finish_cutting = _safe_bool(_text(strategy_node, "./{*}AllowsFinishCutting"), True)
    axial_cutting_depth = _safe_float(_text(strategy_node, "./{*}AxialCuttingDepth"), 0.0)
    axial_finish_cutting_depth = _safe_float(_text(strategy_node, "./{*}AxialFinishCuttingDepth"), 0.0)
    stroke_connection_strategy = _text(strategy_node, "./{*}StrokeConnectionStrategy", "Automatic")

    if "ContourParallel" in strategy_type:
        return build_contour_parallel_milling_strategy_spec(
            rotation_direction=_text(strategy_node, "./{*}RotationDirection", "CounterClockwise"),
            stroke_connection_strategy=stroke_connection_strategy,
            inside_to_outside=_safe_bool(_text(strategy_node, "./{*}InsideToOutSide"), True),
            overlap=_safe_float(_text(strategy_node, "./{*}Overlap"), 0.5),
            is_helic_strategy=_safe_bool(_text(strategy_node, "./{*}IsHelicStrategy"), False),
            allow_multiple_passes=allow_multiple_passes,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
            cutmode=_text(strategy_node, "./{*}Cutmode", "Climb"),
            is_internal=_safe_bool(_text(strategy_node, "./{*}IsInternal"), True),
            radial_cutting_depth=_safe_float(_text(strategy_node, "./{*}RadialCuttingDepth"), 0.0),
            radial_finish_cutting_depth=_safe_float(_text(strategy_node, "./{*}RadialFinishCuttingDepth"), 0.0),
            allows_bidirectional=_safe_bool(_text(strategy_node, "./{*}AllowsBidirectional"), False),
            allows_finish_cutting=_safe_bool(_text(strategy_node, "./{*}AllowsFinishCutting"), False),
        )
    if "UnidirectionalMilling" in strategy_type:
        return build_unidirectional_milling_strategy_spec(
            connection_mode=stroke_connection_strategy,
            allow_multiple_passes=allow_multiple_passes,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    if "BidirectionalMilling" in strategy_type:
        return build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=allow_multiple_passes,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    if "HelicMilling" in strategy_type:
        return build_helical_milling_strategy_spec(
            axial_cutting_depth=axial_cutting_depth,
            allows_finish_cutting=allows_finish_cutting,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    return None


def _strategy_pass_levels(
    top_level: float,
    final_level: float,
    strategy: UnidirectionalMillingStrategySpec | BidirectionalMillingStrategySpec,
) -> tuple[float, ...]:
    if not strategy.allow_multiple_passes:
        return (float(final_level),)

    top_level_value = float(top_level)
    final_level_value = float(final_level)
    rough_step = float(strategy.axial_cutting_depth)
    finish_step = float(strategy.axial_finish_cutting_depth)
    finish_start = final_level_value + finish_step if finish_step > 0.0 else None
    levels: list[float] = []

    if rough_step > 0.0:
        current_level = top_level_value - rough_step
        rough_stop_level = finish_start if finish_start is not None else final_level_value
        while current_level > rough_stop_level + 1e-9:
            levels.append(current_level)
            current_level -= rough_step

    if finish_start is not None and finish_start > final_level_value + 1e-9:
        if not levels or not math.isclose(levels[-1], finish_start, abs_tol=1e-9):
            levels.append(finish_start)

    if not levels or not math.isclose(levels[-1], final_level_value, abs_tol=1e-9):
        levels.append(final_level_value)
    return tuple(levels)


def _helical_rough_end_levels(
    top_level: float,
    final_level: float,
    strategy: HelicalMillingStrategySpec,
) -> tuple[float, ...]:
    top_level_value = float(top_level)
    final_level_value = float(final_level)
    rough_step = float(strategy.axial_cutting_depth)
    finish_step = float(strategy.axial_finish_cutting_depth)
    helical_end_level = final_level_value
    if strategy.allows_finish_cutting and finish_step > 0.0:
        helical_end_level = final_level_value + finish_step

    levels: list[float] = []
    if rough_step > 0.0:
        current_level = top_level_value - rough_step
        while current_level > helical_end_level + 1e-9:
            levels.append(current_level)
            current_level -= rough_step

    if not levels or not math.isclose(levels[-1], helical_end_level, abs_tol=1e-9):
        levels.append(helical_end_level)
    return tuple(levels)


def _build_unidirectional_line_strategy_profile(
    top_level: float,
    final_level: float,
    security_plane: float,
    base_profile: GeometryProfileSpec,
    strategy: UnidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(top_level, final_level, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    start_xy, end_xy = _profile_endpoint_points(base_profile)
    connection_mode = _resolve_unidirectional_connection_mode(strategy, is_closed_profile=False)
    clearance_level = float(top_level) + float(security_plane)
    in_piece_lift = float(security_plane) / 2.0
    primitives: list[GeometryPrimitiveSpec] = []

    for index, current_level in enumerate(pass_levels):
        primitives.append(
            _line_primitive_3d(
                (start_xy[0], start_xy[1], current_level),
                (end_xy[0], end_xy[1], current_level),
            )
        )
        if index == len(pass_levels) - 1:
            continue
        reconnect_level = (
            clearance_level
            if connection_mode == "SafetyHeight"
            else current_level + in_piece_lift
        )
        primitives.append(_vertical_transition_primitive(end_xy, current_level, reconnect_level))
        primitives.append(
            _line_primitive_3d(
                (end_xy[0], end_xy[1], reconnect_level),
                (start_xy[0], start_xy[1], reconnect_level),
            )
        )
        primitives.append(_vertical_transition_primitive(start_xy, reconnect_level, pass_levels[index + 1]))

    return build_composite_geometry_profile(tuple(primitives))


def _build_bidirectional_line_strategy_profile(
    top_level: float,
    final_level: float,
    base_profile: GeometryProfileSpec,
    strategy: BidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(top_level, final_level, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    start_xy, end_xy = _profile_endpoint_points(base_profile)
    primitives: list[GeometryPrimitiveSpec] = []
    current_forward = True

    for index, current_level in enumerate(pass_levels):
        current_start = start_xy if current_forward else end_xy
        current_end = end_xy if current_forward else start_xy
        primitives.append(
            _line_primitive_3d(
                (current_start[0], current_start[1], current_level),
                (current_end[0], current_end[1], current_level),
            )
        )
        if index == len(pass_levels) - 1:
            continue
        primitives.append(
            _vertical_transition_primitive(
                current_end,
                current_level,
                pass_levels[index + 1],
            )
        )
        current_forward = not current_forward

    return build_composite_geometry_profile(tuple(primitives))


def _build_unidirectional_open_profile_strategy_toolpath(
    top_level: float,
    final_level: float,
    security_plane: float,
    base_profile: GeometryProfileSpec,
    strategy: UnidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(top_level, final_level, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    connection_mode = _resolve_unidirectional_connection_mode(strategy, is_closed_profile=False)
    clearance_level = float(top_level) + float(security_plane)
    in_piece_lift = float(security_plane) / 2.0
    primitives: list[GeometryPrimitiveSpec] = []

    for index, current_level in enumerate(pass_levels):
        forward_profile = _profile_at_z(base_profile, current_level)
        primitives.extend(forward_profile.primitives)
        if index == len(pass_levels) - 1:
            continue

        forward_end = forward_profile.primitives[-1].end_point
        reverse_reconnect_level = (
            clearance_level
            if connection_mode == "SafetyHeight"
            else current_level + in_piece_lift
        )
        primitives.append(
            _vertical_transition_primitive(
                (forward_end[0], forward_end[1]),
                current_level,
                reverse_reconnect_level,
            )
        )

        reverse_profile = _reverse_profile_geometry(_profile_at_z(base_profile, reverse_reconnect_level))
        primitives.extend(reverse_profile.primitives)
        reverse_end = reverse_profile.primitives[-1].end_point
        primitives.append(
            _vertical_transition_primitive(
                (reverse_end[0], reverse_end[1]),
                reverse_reconnect_level,
                pass_levels[index + 1],
            )
        )

    return build_composite_geometry_profile(tuple(primitives))


def _build_bidirectional_open_profile_strategy_toolpath(
    top_level: float,
    final_level: float,
    base_profile: GeometryProfileSpec,
    strategy: BidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(top_level, final_level, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    primitives: list[GeometryPrimitiveSpec] = []
    current_forward = True

    for index, current_level in enumerate(pass_levels):
        current_profile = _profile_at_z(base_profile, current_level)
        if not current_forward:
            current_profile = _reverse_profile_geometry(current_profile)
        primitives.extend(current_profile.primitives)
        if index == len(pass_levels) - 1:
            continue

        current_end = current_profile.primitives[-1].end_point
        primitives.append(
            _vertical_transition_primitive(
                (current_end[0], current_end[1]),
                current_level,
                pass_levels[index + 1],
            )
        )
        current_forward = not current_forward

    return build_composite_geometry_profile(tuple(primitives))


def _build_closed_profile_strategy_toolpath(
    top_level: float,
    final_level: float,
    base_profile: GeometryProfileSpec,
    strategy: UnidirectionalMillingStrategySpec | BidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(top_level, final_level, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    primitives: list[GeometryPrimitiveSpec] = []
    for index, current_level in enumerate(pass_levels):
        loop_profile = _profile_at_z(base_profile, current_level)
        if isinstance(strategy, BidirectionalMillingStrategySpec) and index % 2 == 1:
            loop_profile = _reverse_profile_geometry(loop_profile)
        primitives.extend(loop_profile.primitives)
        if index == len(pass_levels) - 1:
            continue
        loop_end = loop_profile.primitives[-1].end_point
        primitives.append(
            _vertical_transition_primitive(
                (loop_end[0], loop_end[1]),
                current_level,
                pass_levels[index + 1],
            )
        )
    return build_composite_geometry_profile(tuple(primitives))


def _build_helical_arc_primitive(
    flat_arc: GeometryPrimitiveSpec,
    *,
    start_z: float,
    end_z: float,
) -> GeometryPrimitiveSpec:
    if (
        flat_arc.primitive_type != "Arc"
        or flat_arc.center_point is None
        or flat_arc.radius is None
    ):
        raise ValueError("La estrategia helicoidal sobre circulo requiere primitivas de arco planas.")

    tangent_xy = _primitive_start_tangent_2d(flat_arc)
    if tangent_xy is None:
        raise ValueError("No se pudo resolver la tangente de arranque del arco helicoidal.")

    center_x = flat_arc.center_point[0]
    center_y = flat_arc.center_point[1]
    center_z = (float(start_z) + float(end_z)) / 2.0
    radius_3d = math.hypot(float(flat_arc.radius), (float(start_z) - float(end_z)) / 2.0)
    if radius_3d <= 1e-9:
        raise ValueError("El arco helicoidal requiere radio 3D positivo.")

    start_angle = float(flat_arc.parameter_start)
    start_point = (flat_arc.start_point[0], flat_arc.start_point[1], float(start_z))
    end_point = (flat_arc.end_point[0], flat_arc.end_point[1], float(end_z))
    radial_start = (
        (start_point[0] - center_x) / radius_3d,
        (start_point[1] - center_y) / radius_3d,
        (start_point[2] - center_z) / radius_3d,
    )
    tangent_start = (tangent_xy[0], tangent_xy[1], 0.0)
    cos_start = math.cos(start_angle)
    sin_start = math.sin(start_angle)
    u_vector = (
        (radial_start[0] * cos_start) - (tangent_start[0] * sin_start),
        (radial_start[1] * cos_start) - (tangent_start[1] * sin_start),
        (radial_start[2] * cos_start) - (tangent_start[2] * sin_start),
    )
    v_vector = (
        (radial_start[0] * sin_start) + (tangent_start[0] * cos_start),
        (radial_start[1] * sin_start) + (tangent_start[1] * cos_start),
        (radial_start[2] * sin_start) + (tangent_start[2] * cos_start),
    )
    normal_vector = (
        (u_vector[1] * v_vector[2]) - (u_vector[2] * v_vector[1]),
        (u_vector[2] * v_vector[0]) - (u_vector[0] * v_vector[2]),
        (u_vector[0] * v_vector[1]) - (u_vector[1] * v_vector[0]),
    )
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=flat_arc.parameter_start,
        parameter_end=flat_arc.parameter_end,
        center_point=(center_x, center_y, center_z),
        radius=radius_3d,
        normal_vector=normal_vector,
        u_vector=u_vector,
        v_vector=v_vector,
    )


def _build_helical_circle_strategy_toolpath(
    top_level: float,
    final_level: float,
    base_profile: GeometryProfileSpec,
    strategy: HelicalMillingStrategySpec,
) -> GeometryProfileSpec:
    if (
        base_profile.geometry_type != "GeomCompositeCurve"
        or len(base_profile.primitives) != 2
        or any(primitive.primitive_type != "Arc" for primitive in base_profile.primitives)
    ):
        raise ValueError(
            "La estrategia Helicoidal hoy espera un circulo compensado compuesto por dos semicircunferencias."
        )

    final_level_value = float(final_level)
    rough_end_levels = _helical_rough_end_levels(top_level, final_level_value, strategy)
    current_level = float(top_level)
    primitives: list[GeometryPrimitiveSpec] = []

    for rough_end_level in rough_end_levels:
        midpoint_level = (current_level + rough_end_level) / 2.0
        primitives.append(
            _build_helical_arc_primitive(
                base_profile.primitives[0],
                start_z=current_level,
                end_z=midpoint_level,
            )
        )
        primitives.append(
            _build_helical_arc_primitive(
                base_profile.primitives[1],
                start_z=midpoint_level,
                end_z=rough_end_level,
            )
        )
        current_level = rough_end_level

    if strategy.allows_finish_cutting:
        loop_end_point = primitives[-1].end_point
        if not math.isclose(current_level, final_level_value, abs_tol=1e-9):
            primitives.append(
                _vertical_transition_primitive(
                    (loop_end_point[0], loop_end_point[1]),
                    current_level,
                    final_level_value,
                )
            )
        primitives.extend(_profile_at_z(base_profile, final_level_value).primitives)

    return build_composite_geometry_profile(tuple(primitives))


def _normalize_milling_strategy_spec(
    strategy: Optional[MillingStrategySpec],
) -> Optional[MillingStrategySpec]:
    if strategy is None:
        return None
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return build_unidirectional_milling_strategy_spec(
            connection_mode=strategy.connection_mode,
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
    if isinstance(strategy, BidirectionalMillingStrategySpec):
        return build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
    if isinstance(strategy, HelicalMillingStrategySpec):
        return build_helical_milling_strategy_spec(
            axial_cutting_depth=strategy.axial_cutting_depth,
            allows_finish_cutting=strategy.allows_finish_cutting,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
    if isinstance(strategy, ContourParallelMillingStrategySpec):
        return build_contour_parallel_milling_strategy_spec(
            rotation_direction=strategy.rotation_direction,
            stroke_connection_strategy=strategy.stroke_connection_strategy,
            inside_to_outside=strategy.inside_to_outside,
            overlap=strategy.overlap,
            is_helic_strategy=strategy.is_helic_strategy,
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
            cutmode=strategy.cutmode,
            is_internal=strategy.is_internal,
            radial_cutting_depth=strategy.radial_cutting_depth,
            radial_finish_cutting_depth=strategy.radial_finish_cutting_depth,
            allows_bidirectional=strategy.allows_bidirectional,
            allows_finish_cutting=strategy.allows_finish_cutting,
        )
    raise ValueError(f"Tipo de estrategia de fresado no soportado: {type(strategy)!r}")


def _ensure_milling_strategy_allowed(
    strategy: Optional[MillingStrategySpec],
    *,
    allowed_types: tuple[type, ...],
    context: str,
) -> Optional[MillingStrategySpec]:
    if strategy is None:
        return None
    if isinstance(strategy, allowed_types):
        return strategy
    admitted = ", ".join(sorted(strategy_type.__name__ for strategy_type in allowed_types))
    raise ValueError(
        f"La estrategia {type(strategy).__name__} no esta validada para {context}. "
        f"Estrategias admitidas: {admitted}."
    )
