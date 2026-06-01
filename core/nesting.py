"""Compatibility facade for cut nesting services and helpers."""

import re
from typing import List

from core.model import Piece, Project
from core.nesting_boards import (
    apply_board_margin as _apply_board_margin,
    normalize_board_definition as _normalize_board_definition,
    resolve_board_definition as _resolve_board_definition,
)
from core.nesting_geometry import (
    occupied_span as _occupied_span,
    prune_free_rectangles as _prune_free_rectangles,
    rectangles_intersect as _rectangles_intersect,
    split_free_rectangle as _split_free_rectangle,
)
from core.nesting_free_rectangles import (
    pack_group_into_boards_free_rectangles as _pack_group_into_boards_free_rectangles,
    placement_score as _placement_score,
)
from core.nesting_guillotine_sections import (
    board_state_score as _board_state_score,
    build_main_cut_guides as _build_main_cut_guides,
    build_section_candidate as _build_section_candidate,
    build_section_placements as _build_section_placements,
    dimension_scan_state_score as _dimension_scan_state_score,
    section_axes_for_mode as _section_axes_for_mode,
    section_build_score as _section_build_score,
    section_candidate_score as _section_candidate_score,
    section_dimensions as _section_dimensions,
    section_leader_dimensions as _section_leader_dimensions,
    section_selection_sort_key as _section_selection_sort_key,
    section_similarity_metrics as _section_similarity_metrics,
    selection_dimension_rank as _selection_dimension_rank,
)
from core.nesting_guillotine import (
    pack_group_into_boards_guillotine as _pack_group_into_boards_guillotine,
    pack_group_into_boards_guillotine_dimension_scan as _pack_group_into_boards_guillotine_dimension_scan,
)
from core.nesting_brkga import (
    brkga_tail_fitness as _brkga_tail_fitness,
    build_order_driven_section as _build_order_driven_section,
    decode_random_key_order as _decode_random_key_order,
    first_order_section_leader as _first_order_section_leader,
    full_tail_section_metrics as _full_tail_section_metrics,
    initial_order_keys as _initial_order_keys,
    matching_option_for_order_section as _matching_option_for_order_section,
    mutate_random_keys as _mutate_random_keys,
    order_group_pieces_for_brkga_tail as _order_group_pieces_for_brkga_tail,
    pack_group_into_boards_guillotine_brkga_tail as _pack_group_into_boards_guillotine_brkga_tail,
    pack_group_into_boards_order_driven_guillotine as _pack_group_into_boards_order_driven_guillotine,
    preferred_primary_secondary as _preferred_primary_secondary,
)
from core.nesting_dispatch import pack_group_into_boards as _pack_group_into_boards
from core.nesting_pdf import build_cut_diagram_pdf
from core.nesting_service import generate_cut_diagrams
from core.nesting_pieces import (
    build_en_juego_cut_piece as _build_en_juego_cut_piece,
    composition_grain_axes as _composition_grain_axes,
    composition_layout_rect as _composition_layout_rect,
    composition_layout_rect_from_footprints as _composition_layout_rect_from_footprints,
    composition_layout_rect_from_scene as _composition_layout_rect_from_scene,
    derived_grain_axis_for_layout as _derived_grain_axis_for_layout,
    expand_project_pieces as _expand_project_pieces,
    has_valid_cut_dimensions as _has_valid_cut_dimensions,
    is_valid_piece as _is_valid_piece,
    layout_has_footprint as _layout_has_footprint,
    layout_piece_id as _layout_piece_id,
    layout_rotation_degrees as _layout_rotation_degrees,
    legacy_layout_scene_rect as _legacy_layout_scene_rect,
    module_short_name as _module_short_name,
    normalize_piece_grain_mode as _normalize_piece_grain_mode,
    piece_can_rotate as _piece_can_rotate,
    read_module_config as _read_module_config,
    resolve_cut_piece_dimensions as _resolve_cut_piece_dimensions,
    resolve_layout_drawing_dimensions as _resolve_layout_drawing_dimensions,
    resolve_piece_source_value as _resolve_piece_source_value,
    row_by_piece_id as _row_by_piece_id,
    safe_float as _safe_float,
    safe_quantity as _safe_quantity,
    stored_layout_dimensions as _stored_layout_dimensions,
    unique_nonempty_values as _unique_nonempty_values,
)
from core.nesting_strategy import (
    normalize_board_grain_axis as _normalize_board_grain_axis,
    normalize_guillotine_algorithm as _normalize_guillotine_algorithm,
    normalize_optimization_mode as _normalize_optimization_mode,
    order_group_pieces as _order_group_pieces,
    orientation_options as _orientation_options,
    uses_guillotine_mode as _uses_guillotine_mode,
)
from core.nesting_model import (
    BOARD_GRAIN_NONE,
    BRKGA_TAIL_ELITE_BIAS,
    BRKGA_TAIL_ELITE_FRACTION,
    BRKGA_TAIL_GENERATIONS,
    BRKGA_TAIL_MUTANT_FRACTION,
    BRKGA_TAIL_MUTATION_RATE,
    BRKGA_TAIL_MUTATION_SCALE,
    BRKGA_TAIL_POPULATION,
    BRKGA_TAIL_SEED,
    CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL,
    CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN,
    CUT_GUILLOTINE_ALGORITHM_PREFERRED,
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_NONE,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutBoard,
    CutPiece,
    CutPlacement,
    SectionCandidate,
    SectionSelection,
)


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return cleaned.strip("._") or "diagrama"


def first_fit_2d(pieces: List[Piece], board_width: float, board_height: float, allow_rotate: bool = True):
    """Wrapper simple de compatibilidad para obtener ubicaciones en un solo tablero."""

    cut_pieces = [
        CutPiece(
            piece=piece,
            label=str(piece.name or piece.id or 'pieza'),
            width=float(piece.width),
            height=float(piece.height),
            thickness=float(piece.thickness or 0),
            color=str(piece.color or ''),
            allow_rotate=allow_rotate,
            grain_mode=_normalize_piece_grain_mode(piece.grain_direction),
            final_width=float(piece.width),
            final_height=float(piece.height),
        )
        for piece in pieces
        if _is_valid_piece(piece)
    ]
    boards, _ = _pack_group_into_boards('TEMP', 0.0, cut_pieces, float(board_width), float(board_height), 0.0, 0.0)
    if not boards:
        return []

    return [
        {
            'piece_id': placement.cut_piece.piece.id,
            'x': placement.x,
            'y': placement.y,
            'width': placement.width,
            'height': placement.height,
        }
        for placement in boards[0].placements
    ]
