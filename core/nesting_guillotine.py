"""Guillotine packers for cut nesting."""

from __future__ import annotations

from core.nesting_guillotine_sections import (
    board_state_score,
    build_main_cut_guides,
    build_section_candidate,
    build_section_placements,
    dimension_scan_state_score,
    section_build_score,
    section_dimensions,
    section_similarity_metrics,
)
from core.nesting_model import (
    BOARD_GRAIN_NONE,
    CUT_OPTIMIZATION_NONE,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutBoard,
    CutPiece,
    CutPlacement,
    SectionCandidate,
)
from core.nesting_strategy import (
    normalize_board_grain_axis,
    normalize_optimization_mode,
    orientation_options,
)


def pack_group_into_boards_guillotine(
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
    normalized_mode = normalize_optimization_mode(optimization_mode)
    primary_capacity = float(board_height) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    board_grain_axis = normalize_board_grain_axis(grain)
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
                    round(section_dimensions(width, height, normalized_mode)[0], 2)
                    for cut_piece in state['remaining']
                    for width, height, _ in orientation_options(cut_piece, normalized_mode, grain)
                    if section_dimensions(width, height, normalized_mode)[0] - primary_remaining <= 0.01
                }
                candidates: list[SectionCandidate] = []
                for section_size in sorted(section_sizes, reverse=True)[:max_section_sizes]:
                    candidate = build_section_candidate(
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

                candidates.sort(key=lambda item: section_build_score(item, secondary_capacity))
                for candidate in candidates[:candidates_per_state]:
                    used_indexes = {selection.remaining_index for selection in candidate.selections}
                    new_remaining = [piece for idx, piece in enumerate(state['remaining']) if idx not in used_indexes]
                    exact_area, _, _, _, _ = section_similarity_metrics(candidate)
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
                key=lambda state: board_state_score(
                    state['grouped_area'],
                    state['used_area'],
                    state['current_primary'],
                    len(state['sections']),
                )
            )
            active_states = next_states[:beam_width]

        terminal_states = completed_states or active_states or [initial_state]
        terminal_states.sort(
            key=lambda state: board_state_score(
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
                build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = build_main_cut_guides(
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


def pack_group_into_boards_guillotine_dimension_scan(
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
    normalized_mode = normalize_optimization_mode(optimization_mode)
    primary_capacity = float(board_height) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    board_grain_axis = normalize_board_grain_axis(grain)
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
                    round(section_dimensions(width, height, normalized_mode)[0], 2)
                    for cut_piece in state['remaining']
                    for width, height, _ in orientation_options(cut_piece, normalized_mode, grain)
                    if section_dimensions(width, height, normalized_mode)[0] - primary_remaining <= 0.01
                }
                candidates: list[SectionCandidate] = []
                for section_size in sorted(section_sizes, reverse=True)[:max_section_sizes]:
                    candidate = build_section_candidate(
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

                candidates.sort(key=lambda item: section_build_score(item, secondary_capacity))
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
                key=lambda state: dimension_scan_state_score(
                    state['placed_count'],
                    state['used_area'],
                    state['current_primary'],
                    len(state['sections']),
                )
            )
            active_states = next_states[:beam_width]

        terminal_states = completed_states or active_states or [initial_state]
        terminal_states.sort(
            key=lambda state: dimension_scan_state_score(
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
                build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = build_main_cut_guides(
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


__all__ = [
    "pack_group_into_boards_guillotine",
    "pack_group_into_boards_guillotine_dimension_scan",
]
