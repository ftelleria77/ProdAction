"""Milling strategy contracts and normalization for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    "_normalize_milling_strategy_spec",
    "_normalize_strategy_connection_mode",
    "_strategy_is_multilevel",
    "_strategy_comparison_key",
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
