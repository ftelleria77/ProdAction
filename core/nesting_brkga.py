"""BRKGA tail-preserving guillotine packer for cut nesting."""

from __future__ import annotations

import random

from core.nesting_geometry import occupied_span
from core.nesting_guillotine_sections import (
    build_main_cut_guides,
    build_section_placements,
    section_dimensions,
)
from core.nesting_model import (
    BRKGA_TAIL_ELITE_BIAS,
    BRKGA_TAIL_ELITE_FRACTION,
    BRKGA_TAIL_GENERATIONS,
    BRKGA_TAIL_MUTANT_FRACTION,
    BRKGA_TAIL_MUTATION_RATE,
    BRKGA_TAIL_MUTATION_SCALE,
    BRKGA_TAIL_POPULATION,
    BRKGA_TAIL_SEED,
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutBoard,
    CutPiece,
    CutPlacement,
    SectionCandidate,
    SectionSelection,
)
from core.nesting_strategy import (
    normalize_optimization_mode,
    orientation_options,
    uses_guillotine_mode,
)


def full_tail_section_metrics(board: CutBoard) -> tuple[float, float]:
    usable_width = max(0.0, float(board.board_width) - 2.0 * float(board.board_margin))
    usable_height = max(0.0, float(board.board_height) - 2.0 * float(board.board_margin))
    usable_right = float(board.board_width) - float(board.board_margin)
    usable_bottom = float(board.board_height) - float(board.board_margin)

    if not board.placements:
        return usable_width * usable_height, 0.0

    if board.main_cut_orientation == 'vertical':
        max_right = max(float(placement.x) + float(placement.width) for placement in board.placements)
        tail_width = max(0.0, usable_right - max_right)
        return tail_width * usable_height, tail_width

    if board.main_cut_orientation == 'horizontal':
        max_bottom = max(float(placement.y) + float(placement.height) for placement in board.placements)
        tail_height = max(0.0, usable_bottom - max_bottom)
        return tail_height * usable_width, tail_height

    return 0.0, 0.0


def preferred_primary_secondary(
    cut_piece: CutPiece,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float]:
    preferred_width, preferred_height, _ = orientation_options(cut_piece, optimization_mode, grain)[0]
    return section_dimensions(preferred_width, preferred_height, optimization_mode)


def order_group_pieces_for_brkga_tail(
    pieces: list[CutPiece],
    optimization_mode: str,
    grain: str,
) -> list[CutPiece]:
    def sort_key(cut_piece: CutPiece) -> tuple[float, float, float]:
        primary, secondary = preferred_primary_secondary(cut_piece, optimization_mode, grain)
        return (primary, cut_piece.width * cut_piece.height, secondary)

    return sorted(pieces, key=sort_key, reverse=True)


def matching_option_for_order_section(
    cut_piece: CutPiece,
    section_size: float,
    secondary_remaining: float,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float, bool, float, float] | None:
    candidates: list[tuple[float, float, float, float, float, bool]] = []
    for width, height, rotated in orientation_options(cut_piece, optimization_mode, grain):
        primary_span, secondary_span = section_dimensions(width, height, optimization_mode)
        if primary_span - section_size > 0.01:
            continue
        if secondary_span - secondary_remaining > 0.01:
            continue
        candidates.append(
            (
                abs(section_size - primary_span),
                -primary_span,
                -(width * height),
                width,
                height,
                rotated,
            )
        )

    if not candidates:
        return None

    _, _, _, width, height, rotated = min(candidates)
    primary_span, secondary_span = section_dimensions(width, height, optimization_mode)
    return width, height, rotated, primary_span, secondary_span


def first_order_section_leader(
    remaining: list[CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    optimization_mode: str,
    grain: str,
) -> tuple[float, int] | None:
    for idx, cut_piece in enumerate(remaining):
        for width, height, _ in orientation_options(cut_piece, optimization_mode, grain):
            primary_span, secondary_span = section_dimensions(width, height, optimization_mode)
            if primary_span - primary_remaining <= 0.01 and secondary_span - secondary_capacity <= 0.01:
                return primary_span, idx
    return None


def build_order_driven_section(
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

    selections: list[SectionSelection] = []
    used_secondary = 0.0
    used_area = 0.0

    for idx, cut_piece in enumerate(remaining):
        secondary_remaining = secondary_capacity - used_secondary
        if selections:
            secondary_remaining -= piece_spacing
        if secondary_remaining <= 0.01:
            break

        option = matching_option_for_order_section(
            cut_piece,
            section_size,
            secondary_remaining,
            optimization_mode,
            grain,
        )
        if option is None:
            continue

        width, height, rotated, primary_span, secondary_span = option
        used_secondary = secondary_span if not selections else used_secondary + piece_spacing + secondary_span
        selection = SectionSelection(
            remaining_index=idx,
            cut_piece=cut_piece,
            width=width,
            height=height,
            rotated=rotated,
            primary_span=primary_span,
            secondary_span=secondary_span,
            area=width * height,
        )
        selections.append(selection)
        used_area += selection.area

    if not selections:
        return None

    return SectionCandidate(
        section_size=section_size,
        occupied_primary=occupied_primary,
        used_secondary=used_secondary,
        used_area=used_area,
        selections=selections,
    )


def pack_group_into_boards_order_driven_guillotine(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str = '',
    optimization_mode: str = CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[CutBoard], list[CutPiece]]:
    normalized_mode = normalize_optimization_mode(optimization_mode)
    if not uses_guillotine_mode(normalized_mode):
        raise ValueError('El packer genetico requiere modo longitudinal o transversal.')

    primary_capacity = float(board_height) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    remaining = list(pieces)
    boards: list[CutBoard] = []
    skipped: list[CutPiece] = []
    board_index = 1

    while remaining:
        sections: list[SectionCandidate] = []
        current_primary = 0.0
        used_area = 0.0

        while remaining:
            primary_remaining = primary_capacity - current_primary
            if primary_remaining <= 0.01:
                break

            leader = first_order_section_leader(
                remaining,
                primary_remaining,
                secondary_capacity,
                normalized_mode,
                grain,
            )
            if leader is None:
                break

            section_size, _ = leader
            section = build_order_driven_section(
                remaining,
                section_size,
                primary_remaining,
                secondary_capacity,
                piece_spacing,
                section_kerf,
                grain,
                normalized_mode,
            )
            if section is None:
                break

            sections.append(section)
            current_primary += section.occupied_primary
            used_area += section.used_area
            used_indexes = {selection.remaining_index for selection in section.selections}
            remaining = [piece for idx, piece in enumerate(remaining) if idx not in used_indexes]

        if not sections:
            skipped.extend(remaining)
            break

        placements: list[CutPlacement] = []
        primary_offset = 0.0
        for section in sections:
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
            sections,
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
                utilization=used_area / float(board_width * board_height),
                main_cut_positions=main_cut_positions,
                main_cut_orientation=main_cut_orientation,
            )
        )
        board_index += 1

    return boards, skipped


def decode_random_key_order(
    pieces: list[CutPiece],
    keys: list[float],
) -> list[CutPiece]:
    return [
        piece
        for _, _, piece in sorted(
            (float(key), index, piece)
            for index, (key, piece) in enumerate(zip(keys, pieces))
        )
    ]


def initial_order_keys(count: int) -> list[float]:
    if count <= 1:
        return [0.0] * count
    return [index / float(count - 1) for index in range(count)]


def mutate_random_keys(
    keys: list[float],
    rng: random.Random,
    *,
    mutation_rate: float = BRKGA_TAIL_MUTATION_RATE,
    mutation_scale: float = BRKGA_TAIL_MUTATION_SCALE,
) -> list[float]:
    mutated = list(keys)
    for index, value in enumerate(mutated):
        if rng.random() < mutation_rate:
            value += rng.uniform(-mutation_scale, mutation_scale)
            mutated[index] = min(1.0, max(0.0, value))

    if len(mutated) >= 2 and rng.random() < mutation_rate:
        first = rng.randrange(len(mutated))
        second = rng.randrange(len(mutated))
        mutated[first], mutated[second] = mutated[second], mutated[first]

    return mutated


def brkga_tail_fitness(
    boards: list[CutBoard],
    skipped: list[CutPiece],
) -> tuple[float, float, float, float, float, float]:
    tail_areas = [full_tail_section_metrics(board)[0] for board in boards]
    total_tail_area = sum(tail_areas)
    max_tail_area = max(tail_areas) if tail_areas else 0.0
    average_utilization = sum(board.utilization for board in boards) / max(1, len(boards))
    min_utilization = min((board.utilization for board in boards), default=0.0)
    return (
        float(len(skipped)),
        float(len(boards)),
        -total_tail_area,
        -max_tail_area,
        -average_utilization,
        -min_utilization,
    )


def pack_group_into_boards_guillotine_brkga_tail(
    material: str,
    thickness: float,
    pieces: list[CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str = '',
    optimization_mode: str = CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[CutBoard], list[CutPiece]]:
    if not pieces:
        return [], []

    normalized_mode = normalize_optimization_mode(optimization_mode)
    if not uses_guillotine_mode(normalized_mode):
        raise ValueError('El packer genetico requiere modo longitudinal o transversal.')

    base_pieces = order_group_pieces_for_brkga_tail(pieces, normalized_mode, grain)
    rng = random.Random(BRKGA_TAIL_SEED + len(base_pieces) * 1009 + int(round(float(thickness) * 100)))
    population_size = max(6, BRKGA_TAIL_POPULATION)
    generations = max(1, BRKGA_TAIL_GENERATIONS)
    elite_count = max(1, int(round(population_size * BRKGA_TAIL_ELITE_FRACTION)))
    mutant_count = max(1, int(round(population_size * BRKGA_TAIL_MUTANT_FRACTION)))
    offspring_count = max(0, population_size - elite_count - mutant_count)

    count = len(base_pieces)
    base_keys = initial_order_keys(count)
    population: list[list[float]] = [base_keys]
    if count > 1:
        population.append(list(reversed(base_keys)))
    while len(population) < population_size:
        population.append([rng.random() for _ in range(count)])

    best_boards: list[CutBoard] = []
    best_skipped: list[CutPiece] = list(base_pieces)
    best_score: tuple[float, float, float, float, float, float] | None = None

    def evaluate(keys: list[float]):
        ordered_pieces = decode_random_key_order(base_pieces, keys)
        boards, skipped = pack_group_into_boards_order_driven_guillotine(
            material,
            thickness,
            ordered_pieces,
            board_width,
            board_height,
            piece_spacing,
            section_kerf,
            grain=grain,
            optimization_mode=normalized_mode,
        )
        return brkga_tail_fitness(boards, skipped), boards, skipped

    for _ in range(generations):
        ranked = []
        for keys in population:
            score, boards, skipped = evaluate(keys)
            ranked.append((score, keys, boards, skipped))
            if best_score is None or score < best_score:
                best_score = score
                best_boards = boards
                best_skipped = skipped

        ranked.sort(key=lambda item: item[0])
        elites = [list(keys) for _, keys, _, _ in ranked[:elite_count]]
        non_elites = [list(keys) for _, keys, _, _ in ranked[elite_count:]] or elites
        next_population = [list(keys) for keys in elites]

        for _ in range(offspring_count):
            elite_parent = rng.choice(elites)
            other_parent = rng.choice(non_elites)
            child = [
                elite_gene if rng.random() < BRKGA_TAIL_ELITE_BIAS else other_gene
                for elite_gene, other_gene in zip(elite_parent, other_parent)
            ]
            next_population.append(mutate_random_keys(child, rng))

        while len(next_population) < population_size:
            next_population.append([rng.random() for _ in range(count)])

        population = next_population

    for keys in population:
        score, boards, skipped = evaluate(keys)
        if best_score is None or score < best_score:
            best_score = score
            best_boards = boards
            best_skipped = skipped

    return best_boards, best_skipped


__all__ = [
    "brkga_tail_fitness",
    "build_order_driven_section",
    "decode_random_key_order",
    "first_order_section_leader",
    "full_tail_section_metrics",
    "initial_order_keys",
    "matching_option_for_order_section",
    "mutate_random_keys",
    "order_group_pieces_for_brkga_tail",
    "pack_group_into_boards_guillotine_brkga_tail",
    "pack_group_into_boards_order_driven_guillotine",
    "preferred_primary_secondary",
]
