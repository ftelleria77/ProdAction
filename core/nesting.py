"""Algoritmos básicos de nesting/optimización de corte para tableros."""

import math
import random
import re
from pathlib import Path
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
from core.nesting_pdf import build_cut_diagram_pdf
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


def _full_tail_section_metrics(board: CutBoard) -> tuple[float, float]:
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


def _preferred_primary_secondary(
    cut_piece: CutPiece,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float]:
    preferred_width, preferred_height, _ = _orientation_options(cut_piece, optimization_mode, grain)[0]
    return _section_dimensions(preferred_width, preferred_height, optimization_mode)


def _order_group_pieces_for_brkga_tail(
    pieces: list[CutPiece],
    optimization_mode: str,
    grain: str,
) -> list[CutPiece]:
    def sort_key(cut_piece: CutPiece) -> tuple[float, float, float]:
        primary, secondary = _preferred_primary_secondary(cut_piece, optimization_mode, grain)
        return (primary, cut_piece.width * cut_piece.height, secondary)

    return sorted(pieces, key=sort_key, reverse=True)


def _matching_option_for_order_section(
    cut_piece: CutPiece,
    section_size: float,
    secondary_remaining: float,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float, bool, float, float] | None:
    candidates: list[tuple[float, float, float, float, float, bool]] = []
    for width, height, rotated in _orientation_options(cut_piece, optimization_mode, grain):
        primary_span, secondary_span = _section_dimensions(width, height, optimization_mode)
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
    primary_span, secondary_span = _section_dimensions(width, height, optimization_mode)
    return width, height, rotated, primary_span, secondary_span


def _first_order_section_leader(
    remaining: list[CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    optimization_mode: str,
    grain: str,
) -> tuple[float, int] | None:
    for idx, cut_piece in enumerate(remaining):
        for width, height, _ in _orientation_options(cut_piece, optimization_mode, grain):
            primary_span, secondary_span = _section_dimensions(width, height, optimization_mode)
            if primary_span - primary_remaining <= 0.01 and secondary_span - secondary_capacity <= 0.01:
                return primary_span, idx
    return None


def _build_order_driven_section(
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

    selections: list[SectionSelection] = []
    used_secondary = 0.0
    used_area = 0.0

    for idx, cut_piece in enumerate(remaining):
        secondary_remaining = secondary_capacity - used_secondary
        if selections:
            secondary_remaining -= piece_spacing
        if secondary_remaining <= 0.01:
            break

        option = _matching_option_for_order_section(
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


def _pack_group_into_boards_order_driven_guillotine(
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
    normalized_mode = _normalize_optimization_mode(optimization_mode)
    if not _uses_guillotine_mode(normalized_mode):
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

            leader = _first_order_section_leader(
                remaining,
                primary_remaining,
                secondary_capacity,
                normalized_mode,
                grain,
            )
            if leader is None:
                break

            section_size, _ = leader
            section = _build_order_driven_section(
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
                _build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = _build_main_cut_guides(
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


def _decode_random_key_order(
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


def _initial_order_keys(count: int) -> list[float]:
    if count <= 1:
        return [0.0] * count
    return [index / float(count - 1) for index in range(count)]


def _mutate_random_keys(
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


def _brkga_tail_fitness(
    boards: list[CutBoard],
    skipped: list[CutPiece],
) -> tuple[float, float, float, float, float, float]:
    tail_areas = [_full_tail_section_metrics(board)[0] for board in boards]
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


def _pack_group_into_boards_guillotine_brkga_tail(
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

    normalized_mode = _normalize_optimization_mode(optimization_mode)
    if not _uses_guillotine_mode(normalized_mode):
        raise ValueError('El packer genetico requiere modo longitudinal o transversal.')

    base_pieces = _order_group_pieces_for_brkga_tail(pieces, normalized_mode, grain)
    rng = random.Random(BRKGA_TAIL_SEED + len(base_pieces) * 1009 + int(round(float(thickness) * 100)))
    population_size = max(6, BRKGA_TAIL_POPULATION)
    generations = max(1, BRKGA_TAIL_GENERATIONS)
    elite_count = max(1, int(round(population_size * BRKGA_TAIL_ELITE_FRACTION)))
    mutant_count = max(1, int(round(population_size * BRKGA_TAIL_MUTANT_FRACTION)))
    offspring_count = max(0, population_size - elite_count - mutant_count)

    count = len(base_pieces)
    base_keys = _initial_order_keys(count)
    population: list[list[float]] = [base_keys]
    if count > 1:
        population.append(list(reversed(base_keys)))
    while len(population) < population_size:
        population.append([rng.random() for _ in range(count)])

    best_boards: list[CutBoard] = []
    best_skipped: list[CutPiece] = list(base_pieces)
    best_score: tuple[float, float, float, float, float, float] | None = None

    def evaluate(keys: list[float]):
        ordered_pieces = _decode_random_key_order(base_pieces, keys)
        boards, skipped = _pack_group_into_boards_order_driven_guillotine(
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
        return _brkga_tail_fitness(boards, skipped), boards, skipped

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
            next_population.append(_mutate_random_keys(child, rng))

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


def _sections_lower_bound_width(remaining: list[CutPiece], secondary_capacity: float) -> float:
    remaining_area = sum(piece.width * piece.height for piece in remaining)
    if secondary_capacity <= 0:
        return float('inf')
    return remaining_area / secondary_capacity


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
    guillotine_algorithm: str = CUT_GUILLOTINE_ALGORITHM_PREFERRED,
) -> tuple[list[CutBoard], list[CutPiece]]:
    if _uses_guillotine_mode(optimization_mode):
        resolved_algorithm = _normalize_guillotine_algorithm(guillotine_algorithm)
        if resolved_algorithm == CUT_GUILLOTINE_ALGORITHM_BRKGA_TAIL:
            return _pack_group_into_boards_guillotine_brkga_tail(
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
    guillotine_algorithm: str = CUT_GUILLOTINE_ALGORITHM_PREFERRED,
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

    pdf_file = build_cut_diagram_pdf(
        pdf_output_path,
        all_boards,
        production_name=str(project.name or "").strip(),
        client_name=str(project.client or "").strip(),
    )
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
