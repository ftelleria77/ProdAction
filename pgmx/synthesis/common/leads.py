"""Approach and retract contracts for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = [
    "ApproachSpec",
    "RetractSpec",
    "build_approach_spec",
    "build_retract_spec",
    "_normalize_approach_arc_side",
    "_normalize_approach_mode",
    "_normalize_approach_spec",
    "_normalize_approach_type",
    "_normalize_retract_arc_side",
    "_normalize_retract_mode",
    "_normalize_retract_spec",
    "_normalize_retract_type",
]


@dataclass(frozen=True)
class ApproachSpec:
    """Configuracion reutilizable del approach de un fresado."""

    is_enabled: bool = False
    approach_type: str = "Line"
    mode: str = "Down"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"


@dataclass(frozen=True)
class RetractSpec:
    """Configuracion reutilizable del retract de un fresado."""

    is_enabled: bool = False
    retract_type: str = "Line"
    mode: str = "Up"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"
    overlap: float = 0.0


def _normalize_approach_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("ApproachType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_approach_mode(value: Optional[str]) -> str:
    raw = (value or "Down").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "down": "Down",
        "vertical": "Down",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("ApproachMode invalido. Valores admitidos: Down o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_approach_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("ApproachArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def _normalize_retract_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("RetractType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_retract_mode(value: Optional[str]) -> str:
    raw = (value or "Up").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "up": "Up",
        "subida": "Up",
        "vertical": "Up",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("RetractMode invalido. Valores admitidos: Up o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_retract_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("RetractArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def build_approach_spec(
    enabled: Optional[bool] = None,
    *,
    approach_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
) -> ApproachSpec:
    """Construye un `ApproachSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Approach` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, approach_type, mode, radius_multiplier, speed, arc_side)
    )
    if not has_explicit_configuration:
        return ApproachSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Down"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return ApproachSpec(
        is_enabled=is_enabled,
        approach_type=_normalize_approach_type(approach_type or "Line"),
        mode=_normalize_approach_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_approach_arc_side(arc_side or "Automatic"),
    )


def build_retract_spec(
    enabled: Optional[bool] = None,
    *,
    retract_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
    overlap: Optional[float] = None,
) -> RetractSpec:
    """Construye un `RetractSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Retract` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, retract_type, mode, radius_multiplier, speed, arc_side, overlap)
    )
    if not has_explicit_configuration:
        return RetractSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Up"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return RetractSpec(
        is_enabled=is_enabled,
        retract_type=_normalize_retract_type(retract_type or "Line"),
        mode=_normalize_retract_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_retract_arc_side(arc_side or "Automatic"),
        overlap=0.0 if overlap is None else float(overlap),
    )


def _normalize_approach_spec(approach: Optional[ApproachSpec]) -> ApproachSpec:
    if approach is None:
        return ApproachSpec()
    return build_approach_spec(
        enabled=approach.is_enabled,
        approach_type=approach.approach_type,
        mode=approach.mode,
        radius_multiplier=approach.radius_multiplier,
        speed=approach.speed,
        arc_side=approach.arc_side,
    )


def _normalize_retract_spec(retract: Optional[RetractSpec]) -> RetractSpec:
    if retract is None:
        return RetractSpec()
    return build_retract_spec(
        enabled=retract.is_enabled,
        retract_type=retract.retract_type,
        mode=retract.mode,
        radius_multiplier=retract.radius_multiplier,
        speed=retract.speed,
        arc_side=retract.arc_side,
        overlap=retract.overlap,
    )
