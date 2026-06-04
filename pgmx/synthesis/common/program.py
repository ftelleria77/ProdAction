"""Program-level contracts for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from ..drilling.pattern import DrillingPatternSpec
from ..drilling.single import DrillingSpec
from ..milling.circle import CircleMillingSpec
from ..milling.line import LineMillingSpec
from ..milling.pocket import PocketMillingSpec
from ..milling.profile import PolylineMillingSpec
from ..milling.slot import SlotMillingSpec
from ..milling.squaring import SquaringMillingSpec

__all__ = [
    "DEFAULT_MACHINING_ORDER",
    "MachiningSpec",
    "PgmxState",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "XnSpec",
]


DEFAULT_MACHINING_ORDER = ("line", "slot", "polyline", "circle", "squaring", "pocket", "drilling", "drilling_pattern")


@dataclass(frozen=True)
class PgmxState:
    """Descripcion de la pieza final a sintetizar."""

    piece_name: str
    length: float
    width: float
    depth: float
    origin_x: float
    origin_y: float
    origin_z: float
    execution_fields: str = "HG"


MachiningSpec = Union[
    LineMillingSpec,
    SlotMillingSpec,
    PolylineMillingSpec,
    CircleMillingSpec,
    SquaringMillingSpec,
    PocketMillingSpec,
    DrillingSpec,
    DrillingPatternSpec,
]


@dataclass(frozen=True)
class XnSpec:
    """Configuracion publica de `Xn`, la operacion nula final del workplan."""

    reference: str = "Absolute"
    x: float = -3700.0
    y: Optional[float] = None


@dataclass(frozen=True)
class PgmxSynthesisRequest:
    """Solicitud completa para sintetizar un `.pgmx` reutilizable desde la app."""

    baseline_path: Path
    output_path: Path
    piece: PgmxState
    source_pgmx_path: Optional[Path] = None
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = DEFAULT_MACHINING_ORDER
    xn: XnSpec = field(default_factory=XnSpec)


@dataclass(frozen=True)
class PgmxSynthesisResult:
    """Resultado de una sintesis ya escrita a disco."""

    output_path: Path
    piece: PgmxState
    sha256: str
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = DEFAULT_MACHINING_ORDER
    xn: XnSpec = field(default_factory=XnSpec)
