"""Algoritmos básicos de nesting/optimización de corte para tableros."""

import hashlib
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import List

from core.model import PIECE_TYPE_ORDER, Piece, Project


CUT_OPTIMIZATION_NONE = 'none'
CUT_OPTIMIZATION_LONGITUDINAL = 'longitudinal'
CUT_OPTIMIZATION_TRANSVERSAL = 'transversal'

CUT_GUILLOTINE_ALGORITHM_CURRENT = 'current'
CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN = 'dimension-scan'

PIECE_GRAIN_NONE = 'none'
PIECE_GRAIN_LONG_SIDE = 'long_side'
PIECE_GRAIN_SHORT_SIDE = 'short_side'
PIECE_GRAIN_LOCKED = 'locked'

BOARD_GRAIN_NONE = 'none'
BOARD_GRAIN_LENGTH = 'length'
BOARD_GRAIN_WIDTH = 'width'

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
    main_cut_orientation: str = ''


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


def _format_dimension(value: float) -> str:
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return cleaned.strip("._") or "diagrama"


def _safe_quantity(value) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return 1
    return parsed if parsed > 0 else 1


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _has_valid_cut_dimensions(width: float, height: float, thickness: float) -> bool:
    try:
        return float(width) > 0 and float(height) > 0 and float(thickness or 0) > 0
    except (TypeError, ValueError):
        return False


def _normalize_piece_grain_mode(value) -> str:
    raw = str(value or '').strip().lower()
    if not raw or raw in {'0', '0 - sin veta', 'sin veta', 'no veta'}:
        return PIECE_GRAIN_NONE
    if raw in {'1', '1 - longitudinal', 'a lo largo', 'longitudinal'}:
        return PIECE_GRAIN_LONG_SIDE
    if raw in {'2', '2 - transversal', 'a lo ancho', 'transversal'}:
        return PIECE_GRAIN_SHORT_SIDE
    if 'sin veta' in raw or 'no veta' in raw:
        return PIECE_GRAIN_NONE
    if 'a lo largo' in raw or 'longitudinal' in raw:
        return PIECE_GRAIN_LONG_SIDE
    if 'a lo ancho' in raw or 'transversal' in raw:
        return PIECE_GRAIN_SHORT_SIDE
    if 'veta' in raw:
        return PIECE_GRAIN_LOCKED
    return PIECE_GRAIN_NONE


def _normalize_board_grain_axis(value) -> str:
    raw = str(value or '').strip().lower()
    if not raw or raw in {'0', '0 - sin veta', 'sin veta', 'no veta'}:
        return BOARD_GRAIN_NONE
    if raw in {'1', '1 - longitudinal', 'longitudinal'}:
        return BOARD_GRAIN_LENGTH
    if raw in {'2', '2 - transversal', 'transversal'}:
        return BOARD_GRAIN_WIDTH
    if 'sin veta' in raw or 'no veta' in raw:
        return BOARD_GRAIN_NONE
    if 'longitudinal' in raw:
        return BOARD_GRAIN_LENGTH
    if 'transversal' in raw:
        return BOARD_GRAIN_WIDTH
    return BOARD_GRAIN_NONE


def _is_valid_piece(piece: Piece) -> bool:
    return _has_valid_cut_dimensions(piece.width, piece.height, piece.thickness or 0)


def _piece_can_rotate(piece: Piece) -> bool:
    return _normalize_piece_grain_mode(piece.grain_direction) != PIECE_GRAIN_LOCKED


def _resolve_piece_source_value(
    piece: Piece,
    module_path: Path,
    module_metadata_cache: dict[str, dict[str, dict]],
) -> str:
    source_value = str(piece.cnc_source or '').strip()
    if source_value:
        return source_value

    module_key = str(module_path)
    if module_key not in module_metadata_cache:
        from core.parser import load_module_summary

        module_metadata_cache[module_key] = load_module_summary(module_path)

    metadata_entry = module_metadata_cache.get(module_key, {}).get(str(piece.id or '').strip())
    if not isinstance(metadata_entry, dict):
        return ''
    return str(metadata_entry.get('source') or '').strip()


def _resolve_cut_piece_dimensions(
    project: Project,
    piece: Piece,
    module_path: Path,
    squaring_allowance: float,
    dimension_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]],
    module_metadata_cache: dict[str, dict[str, dict]],
) -> tuple[float, float, float, int]:
    resolved_width = _safe_float(piece.width) or 0.0
    resolved_height = _safe_float(piece.height) or 0.0
    resolved_thickness = _safe_float(piece.thickness) or 0.0
    program_piece_yield = 1
    source_value = _resolve_piece_source_value(piece, module_path, module_metadata_cache)

    if source_value:
        from core.pgmx_processing import get_program_piece_yield_count, resolve_piece_program_dimensions

        source_piece = piece if source_value == str(piece.cnc_source or '').strip() else replace(piece, cnc_source=source_value)
        program_width, program_height, program_thickness = resolve_piece_program_dimensions(
            project,
            source_piece,
            module_path,
            cache=dimension_cache,
            prefer_stored=True,
        )
        if program_width is not None and program_width > 0 and program_height is not None and program_height > 0:
            resolved_width = float(program_width)
            resolved_height = float(program_height)
            program_piece_yield = get_program_piece_yield_count(
                _safe_float(piece.width),
                _safe_float(piece.height),
                program_width,
                program_height,
            )
        if program_thickness is not None and program_thickness > 0:
            resolved_thickness = float(program_thickness)

    if resolved_width > 0 and resolved_height > 0 and squaring_allowance > 0:
        resolved_width += squaring_allowance
        resolved_height += squaring_allowance

    return resolved_width, resolved_height, resolved_thickness, program_piece_yield


def _module_short_name(module_name: str) -> str:
    raw = str(module_name or "").strip()
    if not raw:
        return ""
    return raw.split("-", 1)[0].strip() or raw


def _normalize_optimization_mode(value) -> str:
    raw = str(value or '').strip().lower()
    if raw in {CUT_OPTIMIZATION_LONGITUDINAL, 'optimización longitudinal', 'optimizacion longitudinal'}:
        return CUT_OPTIMIZATION_LONGITUDINAL
    if raw in {CUT_OPTIMIZATION_TRANSVERSAL, 'optimización transversal', 'optimizacion transversal'}:
        return CUT_OPTIMIZATION_TRANSVERSAL
    return CUT_OPTIMIZATION_NONE


def _normalize_guillotine_algorithm(value) -> str:
    raw = str(value or '').strip().lower()
    if raw in {CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN, 'dimension_scan', 'scan', 'escaneo-dimensiones'}:
        return CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN
    return CUT_GUILLOTINE_ALGORITHM_CURRENT


def _expand_project_pieces(project: Project, squaring_allowance: float = 0.0) -> dict[tuple[str, float], list[CutPiece]]:
    grouped: dict[tuple[str, float], list[CutPiece]] = {}
    dimension_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
    module_metadata_cache: dict[str, dict[str, dict]] = {}
    resolved_squaring_allowance = max(0.0, _safe_float(squaring_allowance) or 0.0)
    piece_type_rank = {piece_type: index for index, piece_type in enumerate(PIECE_TYPE_ORDER)}

    for module in project.modules:
        from core.pgmx_processing import get_pgmx_program_dimension_annotations

        module_tag = _module_short_name(module.name)
        module_path = Path(module.path)
        ordered_module_pieces = sorted(
            [piece for piece in module.pieces if (_safe_float(piece.thickness) or 0.0) > 0],
            key=lambda piece: piece_type_rank.get(str(piece.piece_type or "").strip(), len(PIECE_TYPE_ORDER)),
        )
        program_annotations = get_pgmx_program_dimension_annotations(
            project,
            ordered_module_pieces,
            module_path,
            cache=dimension_cache,
        )

        for piece, program_annotation in zip(ordered_module_pieces, program_annotations):
            if bool(program_annotation.get("exclude_from_cut_diagrams")):
                continue

            resolved_width, resolved_height, resolved_thickness, program_piece_yield = _resolve_cut_piece_dimensions(
                project,
                piece,
                module_path,
                resolved_squaring_allowance,
                dimension_cache,
                module_metadata_cache,
            )
            if not _has_valid_cut_dimensions(resolved_width, resolved_height, resolved_thickness):
                continue
            material = str(piece.color or "SIN_COLOR").strip() or "SIN_COLOR"
            thickness = float(resolved_thickness)
            base_label = str(piece.name or piece.id or "pieza").strip()
            quantity = _safe_quantity(piece.quantity)
            if program_piece_yield > 1:
                quantity = max(1, (quantity + program_piece_yield - 1) // program_piece_yield)
            grain_mode = _normalize_piece_grain_mode(piece.grain_direction)
            allow_rotate = _piece_can_rotate(piece)
            group_key = (material, round(thickness, 2))

            for copy_index in range(quantity):
                label = base_label
                if quantity > 1:
                    label = f"{label} #{copy_index + 1}"
                if module_tag:
                    label = f"{label} ({module_tag})"

                grouped.setdefault(group_key, []).append(
                    CutPiece(
                        piece=piece,
                        label=label,
                        width=resolved_width,
                        height=resolved_height,
                        thickness=thickness,
                        color=material,
                        allow_rotate=allow_rotate,
                        grain_mode=grain_mode,
                    )
                )

    return grouped


def _orientation_options(
    cut_piece: CutPiece,
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
    board_grain: str = '',
) -> list[tuple[float, float, bool]]:
    options = [(cut_piece.width, cut_piece.height, False)]
    if cut_piece.allow_rotate and abs(cut_piece.width - cut_piece.height) > 0.01:
        options.append((cut_piece.height, cut_piece.width, True))

    optimization_mode = _normalize_optimization_mode(optimization_mode)
    board_grain_axis = _normalize_board_grain_axis(board_grain)

    if cut_piece.grain_mode != PIECE_GRAIN_NONE and board_grain_axis != BOARD_GRAIN_NONE:
        filtered_options: list[tuple[float, float, bool]] = []
        for width, height, rotated in options:
            if cut_piece.grain_mode == PIECE_GRAIN_LONG_SIDE:
                aligned = height >= width if board_grain_axis == BOARD_GRAIN_LENGTH else width >= height
            elif cut_piece.grain_mode == PIECE_GRAIN_SHORT_SIDE:
                aligned = height <= width if board_grain_axis == BOARD_GRAIN_LENGTH else width <= height
            else:
                aligned = not rotated
            if aligned:
                filtered_options.append((width, height, rotated))
        if filtered_options:
            options = filtered_options

    if optimization_mode == CUT_OPTIMIZATION_LONGITUDINAL:
        return sorted(options, key=lambda item: (-item[1], item[0], item[2]))
    if optimization_mode == CUT_OPTIMIZATION_TRANSVERSAL:
        return sorted(options, key=lambda item: (-item[0], item[1], item[2]))
    return sorted(options, key=lambda item: (item[2], -max(item[0], item[1]), -min(item[0], item[1])))


def _order_group_pieces(pieces: list[CutPiece], optimization_mode: str, board_grain: str = '') -> list[CutPiece]:
    optimization_mode = _normalize_optimization_mode(optimization_mode)

    def sort_key(cut_piece: CutPiece):
        preferred_width, preferred_height, _ = _orientation_options(cut_piece, optimization_mode, board_grain)[0]
        if optimization_mode == CUT_OPTIMIZATION_LONGITUDINAL:
            primary = preferred_height
            secondary = preferred_width
        elif optimization_mode == CUT_OPTIMIZATION_TRANSVERSAL:
            primary = preferred_width
            secondary = preferred_height
        else:
            primary = preferred_width * preferred_height
            secondary = max(preferred_width, preferred_height)
        return (
            primary,
            secondary,
            preferred_width * preferred_height,
        )

    return sorted(pieces, key=sort_key, reverse=True)


def _uses_guillotine_mode(optimization_mode: str) -> bool:
    normalized = _normalize_optimization_mode(optimization_mode)
    return normalized in {CUT_OPTIMIZATION_LONGITUDINAL, CUT_OPTIMIZATION_TRANSVERSAL}


def _section_axes_for_mode(optimization_mode: str) -> tuple[float, float]:
    normalized = _normalize_optimization_mode(optimization_mode)
    if normalized == CUT_OPTIMIZATION_TRANSVERSAL:
        return (1.0, 0.0)
    return (0.0, 1.0)


def _section_dimensions(width: float, height: float, optimization_mode: str) -> tuple[float, float]:
    normalized = _normalize_optimization_mode(optimization_mode)
    if normalized == CUT_OPTIMIZATION_TRANSVERSAL:
        return height, width
    return width, height


def _section_candidate_score(candidate: SectionCandidate, optimization_mode: str) -> tuple[float, float, float, float]:
    normalized = _normalize_optimization_mode(optimization_mode)
    unused_secondary = candidate.used_secondary
    if normalized == CUT_OPTIMIZATION_LONGITUDINAL:
        axis_bias = -candidate.section_size
    elif normalized == CUT_OPTIMIZATION_TRANSVERSAL:
        axis_bias = candidate.section_size
    else:
        axis_bias = -candidate.section_size
    return (
        -candidate.used_area,
        -(len(candidate.selections)),
        unused_secondary,
        axis_bias,
    )


def _board_state_score(
    grouped_area: float,
    used_area: float,
    current_primary: float,
    placements_count: int,
) -> tuple[float, float, float, float]:
    return (-grouped_area, -used_area, placements_count, current_primary)


def _dimension_scan_state_score(
    placed_count: int,
    used_area: float,
    current_primary: float,
    section_count: int,
) -> tuple[float, float, float, float]:
    return (-placed_count, section_count, current_primary, -used_area)


def _section_similarity_metrics(candidate: SectionCandidate) -> tuple[float, int, float, int, float]:
    if not candidate.selections:
        return 0.0, 0, 0.0, 0, float(candidate.section_size)

    exact_selections = [
        selection
        for selection in candidate.selections
        if abs(candidate.section_size - selection.primary_span) <= EXACT_SECTION_DIMENSION_TOLERANCE
    ]
    exact_area = sum(selection.area for selection in exact_selections)
    exact_count = len(exact_selections)

    similar_selections = [
        selection
        for selection in candidate.selections
        if abs(candidate.section_size - selection.primary_span) <= SIMILAR_SECTION_DIMENSION_TOLERANCE
    ]
    similar_area = sum(selection.area for selection in similar_selections)
    similar_count = len(similar_selections)
    average_slack = sum(max(0.0, candidate.section_size - selection.primary_span) for selection in candidate.selections) / len(candidate.selections)
    return exact_area, exact_count, similar_area, similar_count, average_slack


def _selection_dimension_rank(selection: SectionSelection) -> tuple[float, float]:
    first = max(float(selection.cut_piece.width), float(selection.cut_piece.height))
    second = min(float(selection.cut_piece.width), float(selection.cut_piece.height))
    return first, second


def _section_leader_dimensions(candidate: SectionCandidate) -> tuple[float, float]:
    exact_selections = [
        selection
        for selection in candidate.selections
        if abs(candidate.section_size - selection.primary_span) <= EXACT_SECTION_DIMENSION_TOLERANCE
    ]
    base = exact_selections or list(candidate.selections)
    if not base:
        return 0.0, 0.0
    return max((_selection_dimension_rank(selection) for selection in base), default=(0.0, 0.0))


def _section_build_score(candidate: SectionCandidate, secondary_capacity: float) -> tuple[float, float, float, float]:
    fill_ratio = candidate.used_secondary / secondary_capacity if secondary_capacity > 0 else 0.0
    section_area = candidate.section_size * max(candidate.used_secondary, 0.0)
    efficiency = candidate.used_area / section_area if section_area > 0 else 0.0
    exact_area, exact_count, similar_area, similar_count, average_slack = _section_similarity_metrics(candidate)
    leader_major, leader_minor = _section_leader_dimensions(candidate)
    return (-leader_major, -leader_minor, -exact_area, -exact_count, -similar_area, -similar_count, average_slack, -efficiency, -fill_ratio, -candidate.used_area, candidate.section_size)


def _section_selection_sort_key(candidate: SectionCandidate, selection: SectionSelection) -> tuple[int, float, float, float]:
    exact_match = abs(candidate.section_size - selection.primary_span) <= EXACT_SECTION_DIMENSION_TOLERANCE
    similar_match = abs(candidate.section_size - selection.primary_span) <= SIMILAR_SECTION_DIMENSION_TOLERANCE
    return (
        0 if exact_match else 1,
        0 if similar_match else 1,
        -selection.secondary_span,
        -(selection.area),
    )


def _build_section_candidate(
    remaining: list[CutPiece],
    section_size: float,
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> SectionCandidate | None:
    occupied_primary = _occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    scale = 10
    capacity_units = int(round((secondary_capacity + piece_spacing) * scale))
    item_candidates: list[SectionSelection] = []

    for idx, cut_piece in enumerate(remaining):
        matching_option = None
        for width, height, rotated in _orientation_options(cut_piece, optimization_mode, grain):
            current_section_size, secondary_span = _section_dimensions(width, height, optimization_mode)
            if current_section_size - section_size > 0.01:
                continue
            if secondary_span - secondary_capacity > 0.01:
                continue
            candidate_option = SectionSelection(
                remaining_index=idx,
                cut_piece=cut_piece,
                width=width,
                height=height,
                rotated=rotated,
                primary_span=current_section_size,
                secondary_span=secondary_span,
                area=width * height,
            )
            if matching_option is None:
                matching_option = candidate_option
                continue

            if candidate_option.secondary_span < matching_option.secondary_span - 0.01:
                matching_option = candidate_option
                continue

            if (
                abs(candidate_option.secondary_span - matching_option.secondary_span) <= 0.01
                and candidate_option.primary_span > matching_option.primary_span + 0.01
            ):
                matching_option = candidate_option
        if matching_option is not None:
            item_candidates.append(matching_option)

    if not item_candidates:
        return None

    states: dict[int, tuple[float, tuple[SectionSelection, ...]]] = {0: (0.0, tuple())}
    for item in item_candidates:
        item_units = int(round((item.secondary_span + piece_spacing) * scale))
        next_states = dict(states)
        for used_units, (used_area, chosen_items) in states.items():
            new_units = used_units + item_units
            if new_units > capacity_units:
                continue
            if any(existing.remaining_index == item.remaining_index for existing in chosen_items):
                continue
            new_area = used_area + item.area
            existing = next_states.get(new_units)
            if existing is None or new_area > existing[0]:
                next_states[new_units] = (new_area, chosen_items + (item,))
        states = next_states

    best_candidate: SectionCandidate | None = None
    for used_units, (used_area, chosen_items) in states.items():
        if not chosen_items:
            continue
        used_secondary = (used_units / scale) - piece_spacing
        candidate = SectionCandidate(
            section_size=section_size,
            occupied_primary=occupied_primary,
            used_secondary=used_secondary,
            used_area=used_area,
            selections=list(chosen_items),
        )
        candidate.selections = sorted(candidate.selections, key=lambda item: _section_selection_sort_key(candidate, item))
        if best_candidate is None or _section_candidate_score(candidate, optimization_mode) < _section_candidate_score(best_candidate, optimization_mode):
            best_candidate = candidate

    return best_candidate


def _build_section_placements(
    candidate: SectionCandidate,
    primary_offset: float,
    optimization_mode: str,
    piece_spacing: float,
) -> list[CutPlacement]:
    placements: list[CutPlacement] = []
    secondary_cursor = 0.0
    normalized = _normalize_optimization_mode(optimization_mode)

    for selection in candidate.selections:
        if normalized == CUT_OPTIMIZATION_TRANSVERSAL:
            x = secondary_cursor
            y = primary_offset
        else:
            x = primary_offset
            y = secondary_cursor

        placements.append(
            CutPlacement(
                cut_piece=selection.cut_piece,
                x=x,
                y=y,
                width=selection.width,
                height=selection.height,
                rotated=selection.rotated,
            )
        )
        secondary_cursor += selection.secondary_span + piece_spacing

    return placements


def _build_main_cut_guides(
    sections: list[SectionCandidate],
    optimization_mode: str,
    board_primary_capacity: float,
) -> tuple[list[float], str]:
    normalized = _normalize_optimization_mode(optimization_mode)
    if normalized == CUT_OPTIMIZATION_LONGITUDINAL:
        orientation = 'vertical'
    elif normalized == CUT_OPTIMIZATION_TRANSVERSAL:
        orientation = 'horizontal'
    else:
        return [], ''

    positions: list[float] = []
    primary_offset = 0.0
    for section in sections:
        cut_position = primary_offset + section.section_size
        primary_offset += section.occupied_primary
        if cut_position < float(board_primary_capacity) - 0.5:
            positions.append(cut_position)

    return positions, orientation


def _sections_lower_bound_width(remaining: list[CutPiece], secondary_capacity: float) -> float:
    remaining_area = sum(piece.width * piece.height for piece in remaining)
    if secondary_capacity <= 0:
        return float('inf')
    return remaining_area / secondary_capacity


def _pack_group_into_boards_guillotine(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str = '',
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
) -> tuple[list[CutBoard], list[CutPiece]]:
    remaining = list(pieces)
    boards: list[CutBoard] = []
    skipped: list[CutPiece] = []
    board_index = 1
    normalized_mode = _normalize_optimization_mode(optimization_mode)
    primary_capacity = float(board_height) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    board_grain_axis = _normalize_board_grain_axis(grain)
    beam_width = 12 if board_grain_axis == BOARD_GRAIN_NONE else 6
    candidates_per_state = 5 if board_grain_axis == BOARD_GRAIN_NONE else 3
    max_section_sizes = 8 if board_grain_axis == BOARD_GRAIN_NONE else 5

    while remaining:
        initial_state = {
            'remaining': list(remaining),
            'sections': [],
            'grouped_area': 0.0,
            'used_area': 0.0,
            'current_primary': 0.0,
        }
        active_states = [initial_state]
        completed_states: list[dict] = []

        while active_states:
            next_states: list[dict] = []
            for state in active_states:
                primary_remaining = primary_capacity - state['current_primary']
                if primary_remaining <= 0.01 or not state['remaining']:
                    completed_states.append(state)
                    continue

                section_sizes = {
                    round(_section_dimensions(width, height, normalized_mode)[0], 2)
                    for cut_piece in state['remaining']
                    for width, height, _ in _orientation_options(cut_piece, normalized_mode, grain)
                    if _section_dimensions(width, height, normalized_mode)[0] - primary_remaining <= 0.01
                }
                candidates: list[SectionCandidate] = []
                for section_size in sorted(section_sizes, reverse=True)[:max_section_sizes]:
                    candidate = _build_section_candidate(
                        state['remaining'],
                        float(section_size),
                        primary_remaining,
                        secondary_capacity,
                        piece_spacing,
                        section_kerf,
                        grain,
                        normalized_mode,
                    )
                    if candidate is not None:
                        candidates.append(candidate)

                if not candidates:
                    completed_states.append(state)
                    continue

                candidates.sort(key=lambda item: _section_build_score(item, secondary_capacity))
                for candidate in candidates[:candidates_per_state]:
                    used_indexes = {selection.remaining_index for selection in candidate.selections}
                    new_remaining = [piece for idx, piece in enumerate(state['remaining']) if idx not in used_indexes]
                    exact_area, _, _, _, _ = _section_similarity_metrics(candidate)
                    next_states.append(
                        {
                            'remaining': new_remaining,
                            'sections': list(state['sections']) + [candidate],
                            'grouped_area': state['grouped_area'] + exact_area,
                            'used_area': state['used_area'] + candidate.used_area,
                            'current_primary': state['current_primary'] + candidate.occupied_primary,
                        }
                    )

            if not next_states:
                break

            next_states.sort(
                key=lambda state: _board_state_score(
                    state['grouped_area'],
                    state['used_area'],
                    state['current_primary'],
                    len(state['sections']),
                )
            )
            active_states = next_states[:beam_width]

        terminal_states = completed_states or active_states or [initial_state]
        terminal_states.sort(
            key=lambda state: _board_state_score(
                state['grouped_area'],
                state['used_area'],
                state['current_primary'],
                len(state['sections']),
            )
        )
        best_state = terminal_states[0]

        if not best_state['sections']:
            skipped.extend(remaining)
            break

        placements: list[CutPlacement] = []
        primary_offset = 0.0
        for section in best_state['sections']:
            placements.extend(
                _build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = _build_main_cut_guides(
            best_state['sections'],
            normalized_mode,
            primary_capacity,
        )

        boards.append(
            CutBoard(
                material=material,
                thickness=thickness,
                board_width=board_width,
                board_height=board_height,
                board_margin=0.0,
                grain=grain,
                index=board_index,
                placements=placements,
                utilization=best_state['used_area'] / float(board_width * board_height),
                main_cut_positions=main_cut_positions,
                main_cut_orientation=main_cut_orientation,
            )
        )
        remaining = list(best_state['remaining'])
        board_index += 1

    return boards, skipped


def _pack_group_into_boards_guillotine_dimension_scan(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str = '',
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
) -> tuple[list[CutBoard], list[CutPiece]]:
    remaining = list(pieces)
    boards: list[CutBoard] = []
    skipped: list[CutPiece] = []
    board_index = 1
    normalized_mode = _normalize_optimization_mode(optimization_mode)
    primary_capacity = float(board_height) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    board_grain_axis = _normalize_board_grain_axis(grain)
    beam_width = 18 if board_grain_axis == BOARD_GRAIN_NONE else 8
    candidates_per_state = 8 if board_grain_axis == BOARD_GRAIN_NONE else 4
    max_section_sizes = 16 if board_grain_axis == BOARD_GRAIN_NONE else 8

    while remaining:
        initial_state = {
            'remaining': list(remaining),
            'sections': [],
            'used_area': 0.0,
            'current_primary': 0.0,
            'placed_count': 0,
        }
        active_states = [initial_state]
        completed_states: list[dict] = []

        while active_states:
            next_states: list[dict] = []
            for state in active_states:
                primary_remaining = primary_capacity - state['current_primary']
                if primary_remaining <= 0.01 or not state['remaining']:
                    completed_states.append(state)
                    continue

                section_sizes = {
                    round(_section_dimensions(width, height, normalized_mode)[0], 2)
                    for cut_piece in state['remaining']
                    for width, height, _ in _orientation_options(cut_piece, normalized_mode, grain)
                    if _section_dimensions(width, height, normalized_mode)[0] - primary_remaining <= 0.01
                }
                candidates: list[SectionCandidate] = []
                for section_size in sorted(section_sizes, reverse=True)[:max_section_sizes]:
                    candidate = _build_section_candidate(
                        state['remaining'],
                        float(section_size),
                        primary_remaining,
                        secondary_capacity,
                        piece_spacing,
                        section_kerf,
                        grain,
                        normalized_mode,
                    )
                    if candidate is not None:
                        candidates.append(candidate)

                if not candidates:
                    completed_states.append(state)
                    continue

                candidates.sort(key=lambda item: _section_build_score(item, secondary_capacity))
                for candidate in candidates[:candidates_per_state]:
                    used_indexes = {selection.remaining_index for selection in candidate.selections}
                    new_remaining = [piece for idx, piece in enumerate(state['remaining']) if idx not in used_indexes]
                    next_states.append(
                        {
                            'remaining': new_remaining,
                            'sections': list(state['sections']) + [candidate],
                            'used_area': state['used_area'] + candidate.used_area,
                            'current_primary': state['current_primary'] + candidate.occupied_primary,
                            'placed_count': state['placed_count'] + len(candidate.selections),
                        }
                    )

            if not next_states:
                break

            next_states.sort(
                key=lambda state: _dimension_scan_state_score(
                    state['placed_count'],
                    state['used_area'],
                    state['current_primary'],
                    len(state['sections']),
                )
            )
            active_states = next_states[:beam_width]

        terminal_states = completed_states or active_states or [initial_state]
        terminal_states.sort(
            key=lambda state: _dimension_scan_state_score(
                state['placed_count'],
                state['used_area'],
                state['current_primary'],
                len(state['sections']),
            )
        )
        best_state = terminal_states[0]

        if not best_state['sections']:
            skipped.extend(remaining)
            break

        placements: list[CutPlacement] = []
        primary_offset = 0.0
        for section in best_state['sections']:
            placements.extend(
                _build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = _build_main_cut_guides(
            best_state['sections'],
            normalized_mode,
            primary_capacity,
        )

        boards.append(
            CutBoard(
                material=material,
                thickness=thickness,
                board_width=board_width,
                board_height=board_height,
                board_margin=0.0,
                grain=grain,
                index=board_index,
                placements=placements,
                utilization=best_state['used_area'] / float(board_width * board_height),
                main_cut_positions=main_cut_positions,
                main_cut_orientation=main_cut_orientation,
            )
        )
        remaining = list(best_state['remaining'])
        board_index += 1

    return boards, skipped


def _rectangles_intersect(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> bool:
    first_x, first_y, first_w, first_h = first
    second_x, second_y, second_w, second_h = second
    return not (
        second_x >= first_x + first_w
        or second_x + second_w <= first_x
        or second_y >= first_y + first_h
        or second_y + second_h <= first_y
    )


def _split_free_rectangle(
    free_rect: tuple[float, float, float, float],
    used_rect: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    free_x, free_y, free_w, free_h = free_rect
    used_x, used_y, used_w, used_h = used_rect
    results: list[tuple[float, float, float, float]] = []

    if used_x > free_x:
        results.append((free_x, free_y, used_x - free_x, free_h))
    if used_x + used_w < free_x + free_w:
        results.append((used_x + used_w, free_y, free_x + free_w - (used_x + used_w), free_h))
    if used_y > free_y:
        results.append((free_x, free_y, free_w, used_y - free_y))
    if used_y + used_h < free_y + free_h:
        results.append((free_x, used_y + used_h, free_w, free_y + free_h - (used_y + used_h)))

    return [rect for rect in results if rect[2] > 0.01 and rect[3] > 0.01]


def _prune_free_rectangles(
    rectangles: list[tuple[float, float, float, float]],
) -> list[tuple[float, float, float, float]]:
    pruned: list[tuple[float, float, float, float]] = []
    for idx, rect in enumerate(rectangles):
        x, y, width, height = rect
        contained = False
        for other_idx, other in enumerate(rectangles):
            if idx == other_idx:
                continue
            other_x, other_y, other_width, other_height = other
            if (
                x >= other_x
                and y >= other_y
                and x + width <= other_x + other_width
                and y + height <= other_y + other_height
            ):
                contained = True
                break
        if not contained:
            pruned.append(rect)
    return pruned


def _occupied_span(size: float, free_size: float, spacing: float) -> float:
    if free_size - size <= 0.01:
        return size
    return size + spacing


def _placement_score(
    free_rect: tuple[float, float, float, float],
    occupied_width: float,
    occupied_height: float,
    optimization_mode: str,
) -> tuple[float, float, float, float]:
    _, _, free_width, free_height = free_rect
    waste_area = free_width * free_height - occupied_width * occupied_height
    short_side = min(free_width - occupied_width, free_height - occupied_height)
    long_side = max(free_width - occupied_width, free_height - occupied_height)
    if optimization_mode == CUT_OPTIMIZATION_LONGITUDINAL:
        axis_fit = free_height - occupied_height
    elif optimization_mode == CUT_OPTIMIZATION_TRANSVERSAL:
        axis_fit = free_width - occupied_width
    else:
        axis_fit = min(free_width - occupied_width, free_height - occupied_height)
    return (round(waste_area, 4), round(axis_fit, 4), round(short_side, 4), round(long_side, 4))


def _pack_group_into_boards_free_rectangles(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    grain: str = "",
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
) -> tuple[list[CutBoard], list[CutPiece]]:
    remaining = list(pieces)
    boards: list[CutBoard] = []
    skipped: list[CutPiece] = []
    board_index = 1
    optimization_mode = _normalize_optimization_mode(optimization_mode)

    while remaining:
        placements: list[CutPlacement] = []
        used_area = 0.0
        free_rectangles: list[tuple[float, float, float, float]] = [(0.0, 0.0, float(board_width), float(board_height))]

        while True:
            found: tuple[int, float, float, bool, tuple[float, float, float, float], tuple[float, float, float, float], tuple[float, float, float, float]] | None = None
            for idx, cut_piece in enumerate(remaining):
                for width, height, rotated in _orientation_options(cut_piece, optimization_mode, grain):
                    for free_rect in free_rectangles:
                        _, _, free_width, free_height = free_rect
                        occupied_width = _occupied_span(width, free_width, piece_spacing)
                        occupied_height = _occupied_span(height, free_height, piece_spacing)
                        if occupied_width > free_width or occupied_height > free_height:
                            continue
                        score = _placement_score(free_rect, occupied_width, occupied_height, optimization_mode)
                        candidate = (
                            idx,
                            width,
                            height,
                            rotated,
                            free_rect,
                            (free_rect[0], free_rect[1], occupied_width, occupied_height),
                            score,
                        )
                        if found is None or candidate[-1] < found[-1]:
                            found = candidate

            if found is not None:
                idx, width, height, rotated, free_rect, used_rect, _ = found
                cut_piece = remaining.pop(idx)
                placements.append(
                    CutPlacement(
                        cut_piece=cut_piece,
                        x=free_rect[0],
                        y=free_rect[1],
                        width=width,
                        height=height,
                        rotated=rotated,
                    )
                )
                used_area += cut_piece.width * cut_piece.height

                updated_rectangles: list[tuple[float, float, float, float]] = []
                for free_rect_candidate in free_rectangles:
                    if not _rectangles_intersect(free_rect_candidate, used_rect):
                        updated_rectangles.append(free_rect_candidate)
                        continue
                    updated_rectangles.extend(_split_free_rectangle(free_rect_candidate, used_rect))
                free_rectangles = _prune_free_rectangles(updated_rectangles)
                continue

            break

        if not placements:
            skipped.extend(remaining)
            break

        boards.append(
            CutBoard(
                material=material,
                thickness=thickness,
                board_width=board_width,
                board_height=board_height,
                board_margin=0.0,
                grain=grain,
                index=board_index,
                placements=placements,
                utilization=used_area / float(board_width * board_height),
            )
        )
        board_index += 1

    return boards, skipped


def _pack_group_into_boards(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str = "",
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
    guillotine_algorithm: str = CUT_GUILLOTINE_ALGORITHM_CURRENT,
) -> tuple[list[CutBoard], list[CutPiece]]:
    if _uses_guillotine_mode(optimization_mode):
        resolved_algorithm = _normalize_guillotine_algorithm(guillotine_algorithm)
        if resolved_algorithm == CUT_GUILLOTINE_ALGORITHM_DIMENSION_SCAN:
            return _pack_group_into_boards_guillotine_dimension_scan(
                material,
                thickness,
                pieces,
                board_width,
                board_height,
                piece_spacing,
                section_kerf,
                grain=grain,
                optimization_mode=optimization_mode,
            )
        return _pack_group_into_boards_guillotine(
            material,
            thickness,
            pieces,
            board_width,
            board_height,
            piece_spacing,
            section_kerf,
            grain=grain,
            optimization_mode=optimization_mode,
        )

    return _pack_group_into_boards_free_rectangles(
        material,
        thickness,
        pieces,
        board_width,
        board_height,
        piece_spacing,
        grain=grain,
        optimization_mode=optimization_mode,
    )


def _color_from_material(material: str) -> str:
    digest = hashlib.md5(material.encode("utf-8")).digest()
    red = 120 + (digest[0] % 80)
    green = 120 + (digest[1] % 80)
    blue = 120 + (digest[2] % 80)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _page_size_for_board(board: CutBoard) -> tuple[float, float]:
    if float(board.board_width) >= float(board.board_height):
        return A4_LANDSCAPE_MM
    return A4_PORTRAIT_MM


def _mm_to_pixels(value_mm: float, dpi: int = A4_EXPORT_DPI) -> int:
    return int(round(float(value_mm) / 25.4 * float(dpi)))


def _load_print_font(image_font_module, size_px: int, bold: bool = False):
    font_candidates = [
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        'arialbd.ttf' if bold else 'arial.ttf',
        'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
    ]
    for candidate in font_candidates:
        try:
            return image_font_module.truetype(candidate, size_px)
        except OSError:
            continue
    return image_font_module.load_default()


def _piece_display_name(cut_piece: CutPiece) -> str:
    return str(cut_piece.piece.name or cut_piece.piece.id or cut_piece.label).strip() or cut_piece.label


def _build_piece_text_overlay(image_module, image_draw_module, image_font_module, placement: CutPlacement, width_px: int, height_px: int):
    piece_name = _piece_display_name(placement.cut_piece)
    if not piece_name or width_px <= 8 or height_px <= 8:
        return None

    rotate_text = height_px > width_px
    dimension_label = f'{_format_dimension(placement.cut_piece.width)} x {_format_dimension(placement.cut_piece.height)}'
    base_lines = [piece_name]
    if min(width_px, height_px) >= 28 and max(width_px, height_px) >= 90:
        base_lines.append(dimension_label)

    measure_image = image_module.new('RGBA', (1, 1), (255, 255, 255, 0))
    measure_draw = image_draw_module.Draw(measure_image)
    available_width = max(1, width_px - 8)
    available_height = max(1, height_px - 8)
    start_font_size = max(4, min(24, int(min(width_px, height_px) * 0.62)))
    chosen_text = None
    chosen_font = None
    chosen_bbox = None
    chosen_spacing = 0

    for candidate_lines in (base_lines, [piece_name]):
        candidate_text = '\n'.join(candidate_lines)
        for font_size in range(start_font_size, 3, -1):
            font = _load_print_font(image_font_module, font_size, bold=True)
            spacing = max(1, font_size // 5)
            bbox = measure_draw.multiline_textbbox((0, 0), candidate_text, font=font, spacing=spacing, align='center')
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            oriented_width = text_height if rotate_text else text_width
            oriented_height = text_width if rotate_text else text_height
            if oriented_width <= available_width and oriented_height <= available_height:
                chosen_text = candidate_text
                chosen_font = font
                chosen_bbox = bbox
                chosen_spacing = spacing
                break
        if chosen_font is not None:
            break

    if chosen_font is None or chosen_bbox is None or chosen_text is None:
        return None

    text_width = int(round(chosen_bbox[2] - chosen_bbox[0]))
    text_height = int(round(chosen_bbox[3] - chosen_bbox[1]))
    font_size = int(getattr(chosen_font, 'size', 8))
    padding = max(2, font_size // 4)
    overlay = image_module.new('RGBA', (text_width + padding * 2, text_height + padding * 2), (255, 255, 255, 0))
    overlay_draw = image_draw_module.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(0, 0), (overlay.width - 1, overlay.height - 1)],
        radius=max(2, padding),
        fill=(255, 255, 255, 185),
    )
    overlay_draw.multiline_text(
        (padding - chosen_bbox[0], padding - chosen_bbox[1]),
        chosen_text,
        fill=(17, 17, 17, 255),
        font=chosen_font,
        spacing=chosen_spacing,
        align='center',
    )
    if rotate_text:
        overlay = overlay.rotate(90, expand=True)
    return overlay


def _draw_dashed_guide(draw, start: tuple[int, int], end: tuple[int, int], color: str, width: int = 3, dash: int = 18, gap: int = 10):
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        current = min(y1, y2)
        limit = max(y1, y2)
        while current < limit:
            segment_end = min(current + dash, limit)
            draw.line([(x1, current), (x2, segment_end)], fill=color, width=width)
            current = segment_end + gap
        return

    if y1 == y2:
        current = min(x1, x2)
        limit = max(x1, x2)
        while current < limit:
            segment_end = min(current + dash, limit)
            draw.line([(current, y1), (segment_end, y2)], fill=color, width=width)
            current = segment_end + gap


def _build_board_print_image(board: CutBoard):
    from PIL import Image, ImageColor, ImageDraw, ImageFont

    page_width_mm, page_height_mm = _page_size_for_board(board)
    page_width_px = _mm_to_pixels(page_width_mm)
    page_height_px = _mm_to_pixels(page_height_mm)
    margin_px = _mm_to_pixels(10.0)
    header_h_px = _mm_to_pixels(20.0)
    board_top_px = margin_px + header_h_px
    available_width_px = page_width_px - margin_px * 2
    available_height_px = page_height_px - board_top_px - margin_px
    scale = min(available_width_px / board.board_width, available_height_px / board.board_height)
    scale = max(0.01, scale)

    board_width_px = int(round(board.board_width * scale))
    board_height_px = int(round(board.board_height * scale))
    board_left_px = margin_px + max(0, (available_width_px - board_width_px) // 2)
    fill_color = ImageColor.getrgb(_color_from_material(board.material))
    image = Image.new('RGB', (page_width_px, page_height_px), 'white')
    draw = ImageDraw.Draw(image)

    title_font = _load_print_font(ImageFont, 34, bold=True)
    subtitle_font = _load_print_font(ImageFont, 18)
    draw.text(
        (margin_px, _mm_to_pixels(5.0)),
        f'{board.material} - {_format_dimension(board.thickness)} mm - Tablero {board.index}',
        fill='#111111',
        font=title_font,
    )
    draw.text(
        (margin_px, _mm_to_pixels(12.0)),
        f'Aprovechamiento: {board.utilization * 100:.1f}% | Tablero base: {_format_dimension(board.board_width)} x {_format_dimension(board.board_height)} mm | Margen: {_format_dimension(board.board_margin)} mm | Veta: {board.grain or "-"} | Hoja: {"A4 horizontal" if page_width_mm > page_height_mm else "A4 vertical"}',
        fill='#4f4f4f',
        font=subtitle_font,
    )
    draw.rounded_rectangle(
        [
            (board_left_px, board_top_px),
            (board_left_px + board_width_px, board_top_px + board_height_px),
        ],
        radius=max(8, _mm_to_pixels(1.8)),
        fill='#fffdf8',
        outline='#2f2f2f',
        width=2,
    )

    for placement in board.placements:
        x_px = int(round(board_left_px + placement.x * scale))
        y_px = int(round(board_top_px + placement.y * scale))
        width_px = int(round(placement.width * scale))
        height_px = int(round(placement.height * scale))

        draw.rectangle(
            [
                (x_px, y_px),
                (x_px + width_px, y_px + height_px),
            ],
            fill=fill_color,
            outline='#222222',
            width=2,
        )

        text_overlay = _build_piece_text_overlay(Image, ImageDraw, ImageFont, placement, width_px, height_px)
        if text_overlay is not None:
            paste_x = x_px + max(0, (width_px - text_overlay.width) // 2)
            paste_y = y_px + max(0, (height_px - text_overlay.height) // 2)
            image.paste(text_overlay, (paste_x, paste_y), text_overlay)

    guide_color = '#d14b38'
    for cut_position in board.main_cut_positions:
        if board.main_cut_orientation == 'vertical':
            x_px = int(round(board_left_px + cut_position * scale))
            _draw_dashed_guide(
                draw,
                (x_px, board_top_px),
                (x_px, board_top_px + board_height_px),
                guide_color,
            )
        elif board.main_cut_orientation == 'horizontal':
            y_px = int(round(board_top_px + cut_position * scale))
            _draw_dashed_guide(
                draw,
                (board_left_px, y_px),
                (board_left_px + board_width_px, y_px),
                guide_color,
            )

    return image


def _build_printable_pdf(pdf_path: Path, boards: list[CutBoard]) -> Path | None:
    if not boards:
        return None

    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(f'No se pudo generar el PDF A4: {exc}') from exc

    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page_images: list[Image.Image] = []

    try:
        for board in boards:
            page_images.append(_build_board_print_image(board))

        first_page, *other_pages = page_images
        first_page.save(
            pdf_path,
            'PDF',
            resolution=float(A4_EXPORT_DPI),
            save_all=True,
            append_images=other_pages,
        )
    finally:
        for image in page_images:
            image.close()

    return pdf_path


def _normalize_board_definition(board_definition: dict) -> dict | None:
    if not isinstance(board_definition, dict):
        return None

    color = str(board_definition.get("color") or "").strip()
    grain = str(board_definition.get("grain") or board_definition.get("veta") or "").strip()
    length = _safe_float(board_definition.get("length"))
    width = _safe_float(board_definition.get("width"))
    thickness = _safe_float(board_definition.get("thickness"))
    margin = _safe_float(board_definition.get("margin"))

    if margin is None:
        margin = 0.0

    if not color or length is None or width is None or thickness is None:
        return None
    if length <= 0 or width <= 0 or thickness <= 0 or margin < 0:
        return None
    if margin * 2 >= min(length, width):
        return None

    return {
        "color": color,
        "length": length,
        "width": width,
        "thickness": thickness,
        "grain": grain,
        "margin": margin,
    }


def _apply_board_margin(boards: list[CutBoard], board_width: float, board_height: float, board_margin: float) -> list[CutBoard]:
    normalized_margin = max(0.0, float(board_margin))
    board_area = float(board_width * board_height)

    for board in boards:
        if normalized_margin > 0:
            for placement in board.placements:
                placement.x += normalized_margin
                placement.y += normalized_margin
            board.main_cut_positions = [position + normalized_margin for position in board.main_cut_positions]

        board.board_width = float(board_width)
        board.board_height = float(board_height)
        board.board_margin = normalized_margin

        used_area = sum(placement.width * placement.height for placement in board.placements)
        board.utilization = used_area / board_area if board_area > 0 else 0.0

    return boards


def _resolve_board_definition(material: str, thickness: float, board_definitions: list[dict]) -> dict | None:
    matches: list[dict] = []
    material_key = str(material or "").strip().lower()
    for raw_definition in board_definitions:
        definition = _normalize_board_definition(raw_definition)
        if definition is None:
            continue
        if str(definition["color"]).strip().lower() != material_key:
            continue
        if abs(float(definition["thickness"]) - float(thickness)) > 0.01:
            continue
        matches.append(definition)

    if not matches:
        return None

    return max(matches, key=lambda item: (float(item["length"]) * float(item["width"]), float(item["length"]), float(item["width"])))


def generate_cut_diagrams(
    project: Project,
    output_path: Path,
    board_width: float = 1830.0,
    board_height: float = 2750.0,
    piece_gap: float = 10.0,
    squaring_allowance: float = 0.0,
    saw_kerf: float = 0.0,
    board_definitions: list[dict] | None = None,
    optimization_mode: str = CUT_OPTIMIZATION_NONE,
    guillotine_algorithm: str = CUT_GUILLOTINE_ALGORITHM_CURRENT,
) -> dict:
    """Genera un PDF de corte agrupado por color y espesor."""

    output_path = Path(output_path)
    if output_path.suffix.lower() == '.pdf':
        pdf_output_path = output_path
    else:
        pdf_output_path = output_path / 'diagramas_corte_a4.pdf'

    resolved_piece_gap = max(0.0, _safe_float(piece_gap) or 0.0)
    resolved_squaring_allowance = max(0.0, _safe_float(squaring_allowance) or 0.0)
    resolved_saw_kerf = max(0.0, _safe_float(saw_kerf) or 0.0)
    piece_spacing = resolved_piece_gap + resolved_saw_kerf

    grouped_pieces = _expand_project_pieces(project, squaring_allowance=resolved_squaring_allowance)
    if not grouped_pieces:
        raise ValueError('No hay piezas válidas para diagramas de corte.')

    skipped_labels: list[str] = []
    group_summaries: list[dict] = []
    missing_board_groups: list[dict] = []
    all_boards: list[CutBoard] = []
    normalized_board_definitions = [
        definition
        for definition in (_normalize_board_definition(item) for item in (board_definitions or []))
        if definition is not None
    ]
    use_configured_boards = bool(normalized_board_definitions)
    resolved_optimization_mode = _normalize_optimization_mode(optimization_mode)
    resolved_guillotine_algorithm = _normalize_guillotine_algorithm(guillotine_algorithm)

    for material, thickness in sorted(grouped_pieces.keys(), key=lambda item: (item[1], item[0])):
        board_definition = _resolve_board_definition(material, thickness, normalized_board_definitions) if use_configured_boards else None
        if use_configured_boards and board_definition is None:
            missing_board_groups.append(
                {
                    "material": material,
                    "thickness": thickness,
                    "piece_count": len(grouped_pieces[(material, thickness)]),
                }
            )
            skipped_labels.extend(cut_piece.label for cut_piece in grouped_pieces[(material, thickness)])
            group_summaries.append(
                {
                    "material": material,
                    "thickness": thickness,
                    "board_count": 0,
                    "piece_count": len(grouped_pieces[(material, thickness)]),
                    "board_width": None,
                    "board_height": None,
                    "grain": "",
                }
            )
            continue

        resolved_board_width = float(board_definition["width"]) if board_definition else float(board_width)
        resolved_board_height = float(board_definition["length"]) if board_definition else float(board_height)
        resolved_board_margin = float(board_definition.get("margin") or 0.0) if board_definition else 0.0
        resolved_grain = str(board_definition.get("grain") or "") if board_definition else ""
        usable_board_width = resolved_board_width - (resolved_board_margin * 2.0)
        usable_board_height = resolved_board_height - (resolved_board_margin * 2.0)
        ordered_pieces = _order_group_pieces(
            grouped_pieces[(material, thickness)],
            resolved_optimization_mode,
            resolved_grain,
        )

        boards, skipped = _pack_group_into_boards(
            material,
            thickness,
            ordered_pieces,
            usable_board_width,
            usable_board_height,
            piece_spacing,
            resolved_saw_kerf,
            grain=resolved_grain,
            optimization_mode=resolved_optimization_mode,
            guillotine_algorithm=resolved_guillotine_algorithm,
        )
        boards = _apply_board_margin(boards, resolved_board_width, resolved_board_height, resolved_board_margin)
        all_boards.extend(boards)

        skipped_labels.extend(cut_piece.label for cut_piece in skipped)
        group_summaries.append(
            {
                'material': material,
                'thickness': thickness,
                'board_count': len(boards),
                'piece_count': len(grouped_pieces[(material, thickness)]),
                'board_width': resolved_board_width,
                'board_height': resolved_board_height,
                'board_margin': resolved_board_margin,
                'grain': resolved_grain,
            }
        )

    pdf_file = _build_printable_pdf(pdf_output_path, all_boards)
    return {
        'pdf_file': pdf_file,
        'skipped_pieces': skipped_labels,
        'group_summaries': group_summaries,
        'missing_board_groups': missing_board_groups,
        'used_configured_boards': use_configured_boards,
        'optimization_mode': resolved_optimization_mode,
        'guillotine_algorithm': resolved_guillotine_algorithm,
        'piece_gap': resolved_piece_gap,
        'squaring_allowance': resolved_squaring_allowance,
        'saw_kerf': resolved_saw_kerf,
    }


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
