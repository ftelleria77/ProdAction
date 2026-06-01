"""Shared data structures and constants for cut nesting."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.model import Piece


CUT_OPTIMIZATION_NONE = "none"
CUT_OPTIMIZATION_LONGITUDINAL = "longitudinal"
CUT_OPTIMIZATION_TRANSVERSAL = "transversal"

CUT_GUILLOTINE_ALGORITHM_CURRENT = "current"
CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN = "dimension-scan"
CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL = "brkga-tail"
CUT_GUILLOTINE_ALGORITHM_PREFERRED = CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL
PRINT_FONT_SCALE = 1.5

BRKGA_TAIL_POPULATION = 24
BRKGA_TAIL_GENERATIONS = 24
BRKGA_TAIL_ELITE_FRACTION = 0.25
BRKGA_TAIL_MUTANT_FRACTION = 0.20
BRKGA_TAIL_ELITE_BIAS = 0.70
BRKGA_TAIL_MUTATION_RATE = 0.08
BRKGA_TAIL_MUTATION_SCALE = 0.18
BRKGA_TAIL_SEED = 40727

PIECE_GRAIN_NONE = "none"
PIECE_GRAIN_HEIGHT_AXIS = "height_axis"
PIECE_GRAIN_WIDTH_AXIS = "width_axis"
PIECE_GRAIN_LOCKED = "locked"

BOARD_GRAIN_NONE = "none"
BOARD_GRAIN_LENGTH = "length"
BOARD_GRAIN_WIDTH = "width"

A4_LANDSCAPE_MM = (297.0, 210.0)
A4_PORTRAIT_MM = (210.0, 297.0)
A4_EXPORT_DPI = 180
EXACT_SECTION_DIMENSION_TOLERANCE = 0.5
SIMILAR_SECTION_DIMENSION_TOLERANCE = 8.0


@dataclass
class CutPiece:
    piece: Piece
    label: str
    width: float
    height: float
    thickness: float
    color: str
    allow_rotate: bool
    grain_mode: str = PIECE_GRAIN_NONE
    final_width: float | None = None
    final_height: float | None = None


@dataclass
class CutPlacement:
    cut_piece: CutPiece
    x: float
    y: float
    width: float
    height: float
    rotated: bool = False


@dataclass
class CutBoard:
    material: str
    thickness: float
    board_width: float
    board_height: float
    board_margin: float
    grain: str
    index: int
    placements: list[CutPlacement] = field(default_factory=list)
    utilization: float = 0.0
    main_cut_positions: list[float] = field(default_factory=list)
    main_cut_orientation: str = ""


@dataclass
class SectionSelection:
    remaining_index: int
    cut_piece: CutPiece
    width: float
    height: float
    rotated: bool
    primary_span: float
    secondary_span: float
    area: float


@dataclass
class SectionCandidate:
    section_size: float
    occupied_primary: float
    used_secondary: float
    used_area: float
    selections: list[SectionSelection] = field(default_factory=list)


__all__ = [
    "A4_EXPORT_DPI",
    "A4_LANDSCAPE_MM",
    "A4_PORTRAIT_MM",
    "BOARD_GRAIN_LENGTH",
    "BOARD_GRAIN_NONE",
    "BOARD_GRAIN_WIDTH",
    "BRKGA_TAIL_ELITE_BIAS",
    "BRKGA_TAIL_ELITE_FRACTION",
    "BRKGA_TAIL_GENERATIONS",
    "BRKGA_TAIL_MUTANT_FRACTION",
    "BRKGA_TAIL_MUTATION_RATE",
    "BRKGA_TAIL_MUTATION_SCALE",
    "BRKGA_TAIL_POPULATION",
    "BRKGA_TAIL_SEED",
    "CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL",
    "CUT_GUILLOTINE_ALGORITHM_CURRENT",
    "CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN",
    "CUT_GUILLOTINE_ALGORITHM_PREFERRED",
    "CUT_OPTIMIZATION_LONGITUDINAL",
    "CUT_OPTIMIZATION_NONE",
    "CUT_OPTIMIZATION_TRANSVERSAL",
    "CutBoard",
    "CutPiece",
    "CutPlacement",
    "EXACT_SECTION_DIMENSION_TOLERANCE",
    "PIECE_GRAIN_HEIGHT_AXIS",
    "PIECE_GRAIN_LOCKED",
    "PIECE_GRAIN_NONE",
    "PIECE_GRAIN_WIDTH_AXIS",
    "PRINT_FONT_SCALE",
    "SIMILAR_SECTION_DIMENSION_TOLERANCE",
    "SectionCandidate",
    "SectionSelection",
]
