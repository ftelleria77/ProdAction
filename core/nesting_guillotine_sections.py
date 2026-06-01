"""Section helpers shared by guillotine cut nesting packers."""

from __future__ import annotations

from core.nesting_geometry import occupied_span
from core.nesting_model import (
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_TRANSVERSAL,
    EXACT_SECTION_DIMENSION_TOLERANCE,
    SIMILAR_SECTION_DIMENSION_TOLERANCE,
    CutPiece,
    CutPlacement,
    SectionCandidate,
    SectionSelection,
)
from core.nesting_strategy import normalize_optimization_mode, orientation_options


def section_axes_for_mode(optimization_mode: str) -> tuple[float, float]:
    normalized = normalize_optimization_mode(optimization_mode)
    if normalized == CUT_OPTIMIZATION_TRANSVERSAL:
        return (1.0, 0.0)
    return (0.0, 1.0)


def section_dimensions(width: float, height: float, optimization_mode: str) -> tuple[float, float]:
    normalized = normalize_optimization_mode(optimization_mode)
    if normalized == CUT_OPTIMIZATION_TRANSVERSAL:
        return height, width
    return width, height


def section_candidate_score(
    candidate: SectionCandidate,
    optimization_mode: str,
) -> tuple[float, float, float, float]:
    normalized = normalize_optimization_mode(optimization_mode)
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


def board_state_score(
    grouped_area: float,
    used_area: float,
    current_primary: float,
    placements_count: int,
) -> tuple[float, float, float, float]:
    return (-grouped_area, -used_area, placements_count, current_primary)


def dimension_scan_state_score(
    placed_count: int,
    used_area: float,
    current_primary: float,
    section_count: int,
) -> tuple[float, float, float, float]:
    return (-placed_count, section_count, current_primary, -used_area)


def section_similarity_metrics(candidate: SectionCandidate) -> tuple[float, int, float, int, float]:
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


def selection_dimension_rank(selection: SectionSelection) -> tuple[float, float]:
    first = max(float(selection.cut_piece.width), float(selection.cut_piece.height))
    second = min(float(selection.cut_piece.width), float(selection.cut_piece.height))
    return first, second


def section_leader_dimensions(candidate: SectionCandidate) -> tuple[float, float]:
    exact_selections = [
        selection
        for selection in candidate.selections
        if abs(candidate.section_size - selection.primary_span) <= EXACT_SECTION_DIMENSION_TOLERANCE
    ]
    base = exact_selections or list(candidate.selections)
    if not base:
        return 0.0, 0.0
    return max((selection_dimension_rank(selection) for selection in base), default=(0.0, 0.0))


def section_build_score(candidate: SectionCandidate, secondary_capacity: float) -> tuple[float, ...]:
    fill_ratio = candidate.used_secondary / secondary_capacity if secondary_capacity > 0 else 0.0
    section_area = candidate.section_size * max(candidate.used_secondary, 0.0)
    efficiency = candidate.used_area / section_area if section_area > 0 else 0.0
    exact_area, exact_count, similar_area, similar_count, average_slack = section_similarity_metrics(candidate)
    leader_major, leader_minor = section_leader_dimensions(candidate)
    return (-leader_major, -leader_minor, -exact_area, -exact_count, -similar_area, -similar_count, average_slack, -efficiency, -fill_ratio, -candidate.used_area, candidate.section_size)


def section_selection_sort_key(
    candidate: SectionCandidate,
    selection: SectionSelection,
) -> tuple[int, int, float, float]:
    exact_match = abs(candidate.section_size - selection.primary_span) <= EXACT_SECTION_DIMENSION_TOLERANCE
    similar_match = abs(candidate.section_size - selection.primary_span) <= SIMILAR_SECTION_DIMENSION_TOLERANCE
    return (
        0 if exact_match else 1,
        0 if similar_match else 1,
        -selection.secondary_span,
        -(selection.area),
    )


def build_section_candidate(
    remaining: list[CutPiece],
    section_size: float,
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> SectionCandidate | None:
    occupied_primary = occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    scale = 10
    capacity_units = int(round((secondary_capacity + piece_spacing) * scale))
    item_candidates: list[SectionSelection] = []

    for idx, cut_piece in enumerate(remaining):
        matching_option = None
        for width, height, rotated in orientation_options(cut_piece, optimization_mode, grain):
            current_section_size, secondary_span = section_dimensions(width, height, optimization_mode)
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
        candidate.selections = sorted(candidate.selections, key=lambda item: section_selection_sort_key(candidate, item))
        if best_candidate is None or section_candidate_score(candidate, optimization_mode) < section_candidate_score(best_candidate, optimization_mode):
            best_candidate = candidate

    return best_candidate


def build_section_placements(
    candidate: SectionCandidate,
    primary_offset: float,
    optimization_mode: str,
    piece_spacing: float,
) -> list[CutPlacement]:
    placements: list[CutPlacement] = []
    secondary_cursor = 0.0
    normalized = normalize_optimization_mode(optimization_mode)

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


def build_main_cut_guides(
    sections: list[SectionCandidate],
    optimization_mode: str,
    board_primary_capacity: float,
) -> tuple[list[float], str]:
    normalized = normalize_optimization_mode(optimization_mode)
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


__all__ = [
    "board_state_score",
    "build_main_cut_guides",
    "build_section_candidate",
    "build_section_placements",
    "dimension_scan_state_score",
    "section_axes_for_mode",
    "section_build_score",
    "section_candidate_score",
    "section_dimensions",
    "section_leader_dimensions",
    "section_selection_sort_key",
    "section_similarity_metrics",
    "selection_dimension_rank",
]
