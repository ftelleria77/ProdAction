"""Laboratorio experimental para comparar ordenamientos de guillotina.

Este modulo no participa del flujo principal de la aplicacion. Usa APIs internas
de `core.nesting` para poder experimentar rapido con criterios de orden y
compararlos contra un packer guillotina simple, guiado por el orden recibido.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from typing import Iterable

from app.ui import _load_project, _normalize_cut_optimization_option, _read_app_settings
from core import nesting


DEFAULT_STRATEGIES = (
    "current",
    "no-grain-major-side",
    "area-desc",
    "area-primary-desc",
    "max-side-desc",
    "primary-area-desc",
    "input",
)

BRKGA_TAIL_POPULATION = 24
BRKGA_TAIL_GENERATIONS = 24
BRKGA_TAIL_ELITE_FRACTION = 0.25
BRKGA_TAIL_MUTANT_FRACTION = 0.20
BRKGA_TAIL_ELITE_BIAS = 0.70
BRKGA_TAIL_MUTATION_RATE = 0.08
BRKGA_TAIL_MUTATION_SCALE = 0.18
BRKGA_TAIL_SEED = 40727


@dataclass(frozen=True)
class ExperimentContext:
    project_name: str
    material: str
    thickness: float
    optimization_mode: str
    board_width: float
    board_height: float
    board_margin: float
    usable_board_width: float
    usable_board_height: float
    grain: str
    piece_spacing: float
    saw_kerf: float


@dataclass(frozen=True)
class MeasureEntry:
    remaining_index: int
    cut_piece: nesting.CutPiece
    width: float
    height: float
    rotated: bool
    primary_span: float
    secondary_span: float
    area: float


@dataclass(frozen=True)
class LocalPlacement:
    cut_piece: nesting.CutPiece
    primary: float
    secondary: float
    width: float
    height: float
    rotated: bool
    area: float


@dataclass(frozen=True)
class PackedMeasureSection:
    section_size: float
    occupied_primary: float
    used_area: float
    used_indexes: frozenset[int]
    placements: tuple[LocalPlacement, ...]


def _piece_area(cut_piece: nesting.CutPiece) -> float:
    return float(cut_piece.width) * float(cut_piece.height)


def _full_tail_section_metrics(board: nesting.CutBoard) -> tuple[float, float]:
    usable_width = max(0.0, float(board.board_width) - 2.0 * float(board.board_margin))
    usable_height = max(0.0, float(board.board_height) - 2.0 * float(board.board_margin))
    usable_right = float(board.board_width) - float(board.board_margin)
    usable_bottom = float(board.board_height) - float(board.board_margin)

    if not board.placements:
        return usable_width * usable_height, 0.0

    if board.main_cut_orientation == "vertical":
        max_right = max(float(placement.x) + float(placement.width) for placement in board.placements)
        tail_width = max(0.0, usable_right - max_right)
        return tail_width * usable_height, tail_width

    if board.main_cut_orientation == "horizontal":
        max_bottom = max(float(placement.y) + float(placement.height) for placement in board.placements)
        tail_height = max(0.0, usable_bottom - max_bottom)
        return tail_height * usable_width, tail_height

    return 0.0, 0.0


def _cut_axes_are_swapped_from_final(cut_piece: nesting.CutPiece) -> bool:
    final_width = cut_piece.final_width
    final_height = cut_piece.final_height
    if final_width is None or final_height is None:
        return False

    cut_width = float(cut_piece.width)
    cut_height = float(cut_piece.height)
    final_width = float(final_width)
    final_height = float(final_height)
    normal_error = abs(cut_width - final_width) + abs(cut_height - final_height)
    swapped_error = abs(cut_width - final_height) + abs(cut_height - final_width)
    return swapped_error + 0.01 < normal_error


def _grain_axis_board_alignment(
    cut_piece: nesting.CutPiece,
    rotated: bool,
    board_grain_axis: str,
) -> str:
    final_axes_swapped = _cut_axes_are_swapped_from_final(cut_piece)
    if cut_piece.grain_mode == nesting.PIECE_GRAIN_HEIGHT_AXIS:
        base_axis = "x" if final_axes_swapped else "y"
    elif cut_piece.grain_mode == nesting.PIECE_GRAIN_WIDTH_AXIS:
        base_axis = "y" if final_axes_swapped else "x"
    else:
        return board_grain_axis

    if base_axis == "x":
        return nesting.BOARD_GRAIN_LENGTH if rotated else nesting.BOARD_GRAIN_WIDTH
    return nesting.BOARD_GRAIN_WIDTH if rotated else nesting.BOARD_GRAIN_LENGTH


def _orientation_options(
    cut_piece: nesting.CutPiece,
    optimization_mode: str,
    grain: str,
) -> list[tuple[float, float, bool]]:
    options = [(cut_piece.width, cut_piece.height, False)]
    if cut_piece.allow_rotate and abs(cut_piece.width - cut_piece.height) > 0.01:
        options.append((cut_piece.height, cut_piece.width, True))

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    board_grain_axis = nesting._normalize_board_grain_axis(grain)
    if cut_piece.grain_mode == nesting.PIECE_GRAIN_LOCKED:
        options = [option for option in options if not option[2]]
    elif cut_piece.grain_mode != nesting.PIECE_GRAIN_NONE and board_grain_axis != nesting.BOARD_GRAIN_NONE:
        filtered_options = [
            option
            for option in options
            if _grain_axis_board_alignment(cut_piece, option[2], board_grain_axis) == board_grain_axis
        ]
        if filtered_options:
            options = filtered_options

    if normalized_mode == nesting.CUT_OPTIMIZATION_LONGITUDINAL:
        return sorted(options, key=lambda item: (-item[1], item[0], item[2]))
    if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL:
        return sorted(options, key=lambda item: (-item[0], item[1], item[2]))
    return sorted(options, key=lambda item: (item[2], -max(item[0], item[1]), -min(item[0], item[1])))


def _preferred_option(
    cut_piece: nesting.CutPiece,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float, bool]:
    return _orientation_options(cut_piece, optimization_mode, grain)[0]


def _preferred_primary_secondary(
    cut_piece: nesting.CutPiece,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float]:
    width, height, _ = _preferred_option(cut_piece, optimization_mode, grain)
    return nesting._section_dimensions(width, height, optimization_mode)


def order_pieces(
    pieces: Iterable[nesting.CutPiece],
    strategy: str,
    optimization_mode: str,
    grain: str,
) -> list[nesting.CutPiece]:
    """Devuelve una copia ordenada de las piezas segun una estrategia experimental."""

    piece_list = list(pieces)
    normalized_strategy = str(strategy or "").strip().lower()

    if normalized_strategy == "input":
        return piece_list

    if normalized_strategy == "current":
        return nesting._order_group_pieces(piece_list, optimization_mode, grain)

    def metrics(cut_piece: nesting.CutPiece) -> dict[str, float]:
        primary, secondary = _preferred_primary_secondary(cut_piece, optimization_mode, grain)
        area = _piece_area(cut_piece)
        major = max(float(cut_piece.width), float(cut_piece.height))
        minor = min(float(cut_piece.width), float(cut_piece.height))
        preferred_width, preferred_height, _ = _preferred_option(cut_piece, optimization_mode, grain)
        return {
            "primary": primary,
            "secondary": secondary,
            "area": area,
            "major": major,
            "minor": minor,
            "preferred_width": preferred_width,
            "preferred_height": preferred_height,
        }

    if normalized_strategy == "no-grain-major-side":
        def key(cut_piece: nesting.CutPiece) -> tuple[float, float, float]:
            if (
                nesting._normalize_optimization_mode(optimization_mode)
                in {nesting.CUT_OPTIMIZATION_LONGITUDINAL, nesting.CUT_OPTIMIZATION_TRANSVERSAL}
                and cut_piece.grain_mode == nesting.PIECE_GRAIN_NONE
            ):
                return (
                    metrics(cut_piece)["major"],
                    metrics(cut_piece)["minor"],
                    metrics(cut_piece)["area"],
                )

            primary, secondary = _preferred_primary_secondary(cut_piece, optimization_mode, grain)
            return (primary, secondary, metrics(cut_piece)["area"])

        return sorted(piece_list, key=key, reverse=True)

    if normalized_strategy == "area-desc":
        return sorted(
            piece_list,
            key=lambda item: (
                metrics(item)["area"],
                metrics(item)["major"],
                metrics(item)["minor"],
                metrics(item)["primary"],
            ),
            reverse=True,
        )

    if normalized_strategy == "area-primary-desc":
        return sorted(
            piece_list,
            key=lambda item: (
                metrics(item)["area"],
                metrics(item)["primary"],
                metrics(item)["secondary"],
                metrics(item)["major"],
            ),
            reverse=True,
        )

    if normalized_strategy == "max-side-desc":
        return sorted(
            piece_list,
            key=lambda item: (
                metrics(item)["major"],
                metrics(item)["area"],
                metrics(item)["minor"],
                metrics(item)["primary"],
            ),
            reverse=True,
        )

    if normalized_strategy == "primary-area-desc":
        return sorted(
            piece_list,
            key=lambda item: (
                metrics(item)["primary"],
                metrics(item)["area"],
                metrics(item)["secondary"],
            ),
            reverse=True,
        )

    if normalized_strategy == "secondary-area-desc":
        return sorted(
            piece_list,
            key=lambda item: (
                metrics(item)["secondary"],
                metrics(item)["area"],
                metrics(item)["primary"],
            ),
            reverse=True,
        )

    raise ValueError(f"Estrategia de ordenamiento no soportada: {strategy}")


def _matching_option_for_section(
    cut_piece: nesting.CutPiece,
    section_size: float,
    secondary_remaining: float,
    optimization_mode: str,
    grain: str,
) -> tuple[float, float, bool, float, float] | None:
    candidates: list[tuple[float, float, float, float, float, bool]] = []
    for width, height, rotated in _orientation_options(cut_piece, optimization_mode, grain):
        primary_span, secondary_span = nesting._section_dimensions(width, height, optimization_mode)
        if primary_span - section_size > 0.01:
            continue
        if secondary_span - secondary_remaining > 0.01:
            continue
        candidates.append(
            (
                abs(section_size - primary_span),
                -primary_span,
                -_piece_area(cut_piece),
                width,
                height,
                rotated,
            )
        )

    if not candidates:
        return None

    _, _, _, width, height, rotated = min(candidates)
    primary_span, secondary_span = nesting._section_dimensions(width, height, optimization_mode)
    return width, height, rotated, primary_span, secondary_span


def _first_section_leader(
    remaining: list[nesting.CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    optimization_mode: str,
    grain: str,
) -> tuple[float, int] | None:
    for idx, cut_piece in enumerate(remaining):
        for width, height, _ in _orientation_options(cut_piece, optimization_mode, grain):
            primary_span, secondary_span = nesting._section_dimensions(width, height, optimization_mode)
            if primary_span - primary_remaining <= 0.01 and secondary_span - secondary_capacity <= 0.01:
                return primary_span, idx
    return None


def _build_order_driven_section(
    remaining: list[nesting.CutPiece],
    section_size: float,
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> nesting.SectionCandidate | None:
    occupied_primary = nesting._occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    selections: list[nesting.SectionSelection] = []
    used_secondary = 0.0
    used_area = 0.0

    for idx, cut_piece in enumerate(remaining):
        secondary_remaining = secondary_capacity - used_secondary
        if selections:
            secondary_remaining -= piece_spacing
        if secondary_remaining <= 0.01:
            break

        option = _matching_option_for_section(
            cut_piece,
            section_size,
            secondary_remaining,
            optimization_mode,
            grain,
        )
        if option is None:
            continue

        width, height, rotated, primary_span, secondary_span = option
        used_secondary = (
            secondary_span
            if not selections
            else used_secondary + piece_spacing + secondary_span
        )
        selection = nesting.SectionSelection(
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

    return nesting.SectionCandidate(
        section_size=section_size,
        occupied_primary=occupied_primary,
        used_secondary=used_secondary,
        used_area=used_area,
        selections=selections,
    )


def _section_options_for_piece(
    cut_piece: nesting.CutPiece,
    section_size: float,
    secondary_capacity: float,
    optimization_mode: str,
    grain: str,
) -> list[tuple[float, float, bool, float, float]]:
    options: list[tuple[float, float, bool, float, float]] = []
    for width, height, rotated in _orientation_options(cut_piece, optimization_mode, grain):
        primary_span, secondary_span = nesting._section_dimensions(width, height, optimization_mode)
        if primary_span - section_size > 0.01:
            continue
        if secondary_span - secondary_capacity > 0.01:
            continue
        options.append((width, height, rotated, primary_span, secondary_span))
    return options


def _measure_entries(
    remaining: list[nesting.CutPiece],
    primary_limit: float,
    secondary_limit: float,
    optimization_mode: str,
    grain: str,
) -> list[MeasureEntry]:
    entries: list[MeasureEntry] = []
    for idx, cut_piece in enumerate(remaining):
        for width, height, rotated in _orientation_options(cut_piece, optimization_mode, grain):
            primary_span, secondary_span = nesting._section_dimensions(width, height, optimization_mode)
            if primary_span - primary_limit > 0.01:
                continue
            if secondary_span - secondary_limit > 0.01:
                continue
            entries.append(
                MeasureEntry(
                    remaining_index=idx,
                    cut_piece=cut_piece,
                    width=width,
                    height=height,
                    rotated=rotated,
                    primary_span=primary_span,
                    secondary_span=secondary_span,
                    area=width * height,
                )
            )

    return sorted(
        entries,
        key=lambda entry: (
            entry.primary_span,
            entry.area,
            entry.secondary_span,
            -entry.remaining_index,
        ),
        reverse=True,
    )


def _selection_from_measure_entry(entry: MeasureEntry) -> nesting.SectionSelection:
    return nesting.SectionSelection(
        remaining_index=entry.remaining_index,
        cut_piece=entry.cut_piece,
        width=entry.width,
        height=entry.height,
        rotated=entry.rotated,
        primary_span=entry.primary_span,
        secondary_span=entry.secondary_span,
        area=entry.area,
    )


def _entry_fit_score(
    entry: MeasureEntry,
    free_rect: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    free_primary, free_secondary = free_rect[2], free_rect[3]
    return (
        round(free_primary - entry.primary_span, 4),
        round(free_secondary - entry.secondary_span, 4),
        round(free_primary * free_secondary - entry.primary_span * entry.secondary_span, 4),
        free_rect[1],
    )


def _best_free_rect_for_entry(
    entry: MeasureEntry,
    free_rectangles: list[tuple[float, float, float, float]],
) -> tuple[int, tuple[float, float, float, float]] | None:
    fits: list[tuple[tuple[float, float, float, float], int, tuple[float, float, float, float]]] = []
    for idx, free_rect in enumerate(free_rectangles):
        _, _, free_primary, free_secondary = free_rect
        if entry.primary_span - free_primary > 0.01:
            continue
        if entry.secondary_span - free_secondary > 0.01:
            continue
        fits.append((_entry_fit_score(entry, free_rect), idx, free_rect))

    if not fits:
        return None

    _, idx, free_rect = min(fits)
    return idx, free_rect


def _best_entry_for_active_free_rectangles(
    remaining: list[nesting.CutPiece],
    section_size: float,
    secondary_capacity: float,
    used_indexes: set[int],
    free_rectangles: list[tuple[float, float, float, float]],
    optimization_mode: str,
    grain: str,
) -> tuple[MeasureEntry, int, tuple[float, float, float, float]] | None:
    entries = _measure_entries(
        remaining,
        section_size,
        secondary_capacity,
        optimization_mode,
        grain,
    )
    ordered_rectangles = sorted(
        enumerate(free_rectangles),
        key=lambda item: (
            round(item[1][1], 4),
            round(item[1][0], 4),
            round(item[1][2] * item[1][3], 4),
        ),
    )

    for rect_idx, free_rect in ordered_rectangles:
        _, _, free_primary, free_secondary = free_rect
        matches: list[tuple[tuple[float, float, float, float, int], MeasureEntry]] = []
        for entry_order, entry in enumerate(entries):
            if entry.remaining_index in used_indexes:
                continue
            if entry.primary_span - free_primary > 0.01:
                continue
            if entry.secondary_span - free_secondary > 0.01:
                continue
            primary_gap = free_primary - entry.primary_span
            secondary_gap = free_secondary - entry.secondary_span
            free_area_gap = free_primary * free_secondary - entry.area
            matches.append(
                (
                    (
                        round(primary_gap, 4),
                        round(secondary_gap, 4),
                        round(free_area_gap, 4),
                        -entry.area,
                        entry_order,
                    ),
                    entry,
                )
            )

        if matches:
            _, selected_entry = min(matches)
            return selected_entry, rect_idx, free_rect

    return None


def _split_local_free_rect(
    free_rect: tuple[float, float, float, float],
    entry: MeasureEntry,
    piece_spacing: float,
) -> list[tuple[float, float, float, float]]:
    free_primary_start, free_secondary_start, free_primary, free_secondary = free_rect
    spacing_primary = piece_spacing if free_primary - entry.primary_span > 0.01 else 0.0
    spacing_secondary = piece_spacing if free_secondary - entry.secondary_span > 0.01 else 0.0
    next_primary = free_primary_start + entry.primary_span + spacing_primary
    next_secondary = free_secondary_start + entry.secondary_span + spacing_secondary
    right_width = free_primary_start + free_primary - next_primary
    below_height = free_secondary_start + free_secondary - next_secondary

    rectangles: list[tuple[float, float, float, float]] = []
    if right_width > 0.01:
        rectangles.append(
            (
                next_primary,
                free_secondary_start,
                right_width,
                entry.secondary_span,
            )
        )
    if below_height > 0.01:
        rectangles.append(
            (
                free_primary_start,
                next_secondary,
                free_primary,
                below_height,
            )
        )
    return rectangles


def _place_measure_entry_in_section(
    placements: list[LocalPlacement],
    used_indexes: set[int],
    selected_entry: MeasureEntry,
    selected_rect: tuple[float, float, float, float],
) -> float:
    placements.append(
        LocalPlacement(
            cut_piece=selected_entry.cut_piece,
            primary=selected_rect[0],
            secondary=selected_rect[1],
            width=selected_entry.width,
            height=selected_entry.height,
            rotated=selected_entry.rotated,
            area=selected_entry.area,
        )
    )
    used_indexes.add(selected_entry.remaining_index)
    return selected_entry.area


def _build_measure_split_section(
    remaining: list[nesting.CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> PackedMeasureSection | None:
    leader_entries = _measure_entries(
        remaining,
        primary_remaining,
        secondary_capacity,
        optimization_mode,
        grain,
    )
    if not leader_entries:
        return None

    leader = leader_entries[0]
    section_size = leader.primary_span
    occupied_primary = nesting._occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    free_rectangles: list[tuple[float, float, float, float]] = [
        (0.0, 0.0, section_size, secondary_capacity)
    ]
    placements: list[LocalPlacement] = []
    used_indexes: set[int] = set()
    used_area = 0.0

    while True:
        selected_entry: MeasureEntry | None = None
        selected_rect_idx: int | None = None
        selected_rect: tuple[float, float, float, float] | None = None
        for entry in _measure_entries(
            remaining,
            section_size,
            secondary_capacity,
            optimization_mode,
            grain,
        ):
            if entry.remaining_index in used_indexes:
                continue
            match = _best_free_rect_for_entry(entry, free_rectangles)
            if match is None:
                continue
            selected_rect_idx, selected_rect = match
            selected_entry = entry
            break

        if selected_entry is None or selected_rect_idx is None or selected_rect is None:
            break

        placements.append(
            LocalPlacement(
                cut_piece=selected_entry.cut_piece,
                primary=selected_rect[0],
                secondary=selected_rect[1],
                width=selected_entry.width,
                height=selected_entry.height,
                rotated=selected_entry.rotated,
                area=selected_entry.area,
            )
        )
        used_indexes.add(selected_entry.remaining_index)
        used_area += selected_entry.area
        replacement_rectangles = _split_local_free_rect(
            selected_rect,
            selected_entry,
            piece_spacing,
        )
        free_rectangles = (
            free_rectangles[:selected_rect_idx]
            + free_rectangles[selected_rect_idx + 1:]
            + replacement_rectangles
        )

    if not placements:
        return None

    return PackedMeasureSection(
        section_size=section_size,
        occupied_primary=occupied_primary,
        used_area=used_area,
        used_indexes=frozenset(used_indexes),
        placements=tuple(placements),
    )


def _build_measure_match_split_section(
    remaining: list[nesting.CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> PackedMeasureSection | None:
    leader_entries = _measure_entries(
        remaining,
        primary_remaining,
        secondary_capacity,
        optimization_mode,
        grain,
    )
    if not leader_entries:
        return None

    leader = leader_entries[0]
    section_size = leader.primary_span
    occupied_primary = nesting._occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    free_rectangles: list[tuple[float, float, float, float]] = [
        (0.0, 0.0, section_size, secondary_capacity)
    ]
    placements: list[LocalPlacement] = []
    used_indexes: set[int] = set()
    used_area = 0.0

    leader_rect = free_rectangles.pop(0)
    used_area += _place_measure_entry_in_section(
        placements,
        used_indexes,
        leader,
        leader_rect,
    )
    free_rectangles.extend(_split_local_free_rect(leader_rect, leader, piece_spacing))

    while free_rectangles:
        match = _best_entry_for_active_free_rectangles(
            remaining,
            section_size,
            secondary_capacity,
            used_indexes,
            free_rectangles,
            optimization_mode,
            grain,
        )
        if match is None:
            break

        selected_entry, selected_rect_idx, selected_rect = match
        used_area += _place_measure_entry_in_section(
            placements,
            used_indexes,
            selected_entry,
            selected_rect,
        )
        replacement_rectangles = _split_local_free_rect(
            selected_rect,
            selected_entry,
            piece_spacing,
        )
        free_rectangles = (
            free_rectangles[:selected_rect_idx]
            + free_rectangles[selected_rect_idx + 1:]
            + replacement_rectangles
        )

    return PackedMeasureSection(
        section_size=section_size,
        occupied_primary=occupied_primary,
        used_area=used_area,
        used_indexes=frozenset(used_indexes),
        placements=tuple(placements),
    )


def _build_surface_fit_section(
    remaining: list[nesting.CutPiece],
    leader_index: int,
    leader_option: tuple[float, float, bool, float, float],
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> nesting.SectionCandidate | None:
    """Arma una seccion incluyendo la pieza lider y minimizando sobrante."""

    section_size = leader_option[3]
    occupied_primary = nesting._occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    scale = 10
    capacity_units = int(round((secondary_capacity + piece_spacing) * scale))

    leader_piece = remaining[leader_index]
    leader_selection = nesting.SectionSelection(
        remaining_index=leader_index,
        cut_piece=leader_piece,
        width=leader_option[0],
        height=leader_option[1],
        rotated=leader_option[2],
        primary_span=leader_option[3],
        secondary_span=leader_option[4],
        area=leader_option[0] * leader_option[1],
    )
    leader_units = int(round((leader_selection.secondary_span + piece_spacing) * scale))
    if leader_units > capacity_units:
        return None

    states: dict[int, tuple[float, tuple[nesting.SectionSelection, ...]]] = {
        leader_units: (leader_selection.area, (leader_selection,))
    }

    for idx, cut_piece in enumerate(remaining):
        if idx == leader_index:
            continue

        options = _section_options_for_piece(
            cut_piece,
            section_size,
            secondary_capacity,
            optimization_mode,
            grain,
        )
        if not options:
            continue

        next_states = dict(states)
        for used_units, (used_area, chosen_items) in states.items():
            for width, height, rotated, primary_span, secondary_span in options:
                item_units = int(round((secondary_span + piece_spacing) * scale))
                new_units = used_units + item_units
                if new_units > capacity_units:
                    continue
                selection = nesting.SectionSelection(
                    remaining_index=idx,
                    cut_piece=cut_piece,
                    width=width,
                    height=height,
                    rotated=rotated,
                    primary_span=primary_span,
                    secondary_span=secondary_span,
                    area=width * height,
                )
                new_area = used_area + selection.area
                existing = next_states.get(new_units)
                if existing is None or new_area > existing[0]:
                    next_states[new_units] = (new_area, chosen_items + (selection,))
        states = next_states

    best_units, (best_area, best_items) = max(
        states.items(),
        key=lambda item: (
            item[0],
            item[1][0],
            len(item[1][1]),
        ),
    )
    used_secondary = (best_units / scale) - piece_spacing
    return nesting.SectionCandidate(
        section_size=section_size,
        occupied_primary=occupied_primary,
        used_secondary=used_secondary,
        used_area=best_area,
        selections=list(best_items),
    )


def _best_surface_fit_section(
    remaining: list[nesting.CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> nesting.SectionCandidate | None:
    for leader_index, leader_piece in enumerate(remaining):
        leader_options = [
            option
            for option in _section_options_for_piece(
                leader_piece,
                primary_remaining,
                secondary_capacity,
                optimization_mode,
                grain,
            )
            if abs(option[3]) > 0.01
        ]
        if not leader_options:
            continue

        candidates = [
            candidate
            for candidate in (
                _build_surface_fit_section(
                    remaining,
                    leader_index,
                    option,
                    primary_remaining,
                    secondary_capacity,
                    piece_spacing,
                    section_kerf,
                    grain,
                    optimization_mode,
                )
                for option in leader_options
            )
            if candidate is not None
        ]
        if not candidates:
            continue

        return min(
            candidates,
            key=lambda candidate: (
                round(secondary_capacity - candidate.used_secondary, 4),
                -candidate.used_area,
                -len(candidate.selections),
                candidate.occupied_primary,
            ),
        )

    return None


def _build_measure_driven_section(
    remaining: list[nesting.CutPiece],
    primary_remaining: float,
    secondary_capacity: float,
    piece_spacing: float,
    section_kerf: float,
    grain: str,
    optimization_mode: str,
) -> nesting.SectionCandidate | None:
    leader_entries = _measure_entries(
        remaining,
        primary_remaining,
        secondary_capacity,
        optimization_mode,
        grain,
    )
    if not leader_entries:
        return None

    leader = leader_entries[0]
    section_size = leader.primary_span
    occupied_primary = nesting._occupied_span(section_size, primary_remaining, section_kerf)
    if occupied_primary - primary_remaining > 0.01:
        return None

    selections = [_selection_from_measure_entry(leader)]
    used_indexes = {leader.remaining_index}
    used_secondary = leader.secondary_span
    used_area = leader.area

    while True:
        secondary_remaining = secondary_capacity - used_secondary
        if selections:
            secondary_remaining -= piece_spacing
        if secondary_remaining <= 0.01:
            break

        candidate_entries = [
            entry
            for entry in _measure_entries(
                remaining,
                section_size,
                secondary_remaining,
                optimization_mode,
                grain,
            )
            if entry.remaining_index not in used_indexes
        ]
        if not candidate_entries:
            break

        selected_entry = candidate_entries[0]
        selections.append(_selection_from_measure_entry(selected_entry))
        used_indexes.add(selected_entry.remaining_index)
        used_secondary += piece_spacing + selected_entry.secondary_span
        used_area += selected_entry.area

    return nesting.SectionCandidate(
        section_size=section_size,
        occupied_primary=occupied_primary,
        used_secondary=used_secondary,
        used_area=used_area,
        selections=selections,
    )


def pack_order_driven_guillotine(
    material: str,
    thickness: float,
    pieces: list[nesting.CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    *,
    grain: str = "",
    optimization_mode: str = nesting.CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    """Packer experimental: cada seccion nace de la primera pieza restante."""

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    if not nesting._uses_guillotine_mode(normalized_mode):
        raise ValueError("El packer de prueba requiere modo longitudinal o transversal.")

    primary_capacity = float(board_height) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    remaining = list(pieces)
    boards: list[nesting.CutBoard] = []
    skipped: list[nesting.CutPiece] = []
    board_index = 1

    while remaining:
        sections: list[nesting.SectionCandidate] = []
        current_primary = 0.0
        used_area = 0.0

        while remaining:
            primary_remaining = primary_capacity - current_primary
            if primary_remaining <= 0.01:
                break

            leader = _first_section_leader(
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
            remaining = [
                cut_piece
                for idx, cut_piece in enumerate(remaining)
                if idx not in used_indexes
            ]

        if not sections:
            skipped.extend(remaining)
            break

        placements: list[nesting.CutPlacement] = []
        primary_offset = 0.0
        for section in sections:
            placements.extend(
                nesting._build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = nesting._build_main_cut_guides(
            sections,
            normalized_mode,
            primary_capacity,
        )

        boards.append(
            nesting.CutBoard(
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
    pieces: list[nesting.CutPiece],
    keys: list[float],
) -> list[nesting.CutPiece]:
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
    boards: list[nesting.CutBoard],
    skipped: list[nesting.CutPiece],
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


def pack_brkga_tail_guillotine(
    material: str,
    thickness: float,
    pieces: list[nesting.CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    *,
    grain: str = "",
    optimization_mode: str = nesting.CUT_OPTIMIZATION_LONGITUDINAL,
    population_size: int = BRKGA_TAIL_POPULATION,
    generations: int = BRKGA_TAIL_GENERATIONS,
    seed: int = BRKGA_TAIL_SEED,
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    """BRKGA experimental: evoluciona orden para conservar franjas completas.

    El cromosoma son claves aleatorias. El decoder ordena las piezas y delega en
    el packer `order-driven`, manteniendo la busqueda genetica fuera del motor.
    """

    if not pieces:
        return [], []

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    if not nesting._uses_guillotine_mode(normalized_mode):
        raise ValueError("El packer genetico requiere modo longitudinal o transversal.")

    rng = random.Random(seed + len(pieces) * 1009 + int(round(float(thickness) * 100)))
    population_size = max(6, int(population_size))
    generations = max(1, int(generations))
    elite_count = max(1, int(round(population_size * BRKGA_TAIL_ELITE_FRACTION)))
    mutant_count = max(1, int(round(population_size * BRKGA_TAIL_MUTANT_FRACTION)))
    offspring_count = max(0, population_size - elite_count - mutant_count)

    count = len(pieces)
    base_keys = _initial_order_keys(count)
    population: list[list[float]] = [base_keys]
    if count > 1:
        population.append(list(reversed(base_keys)))
    while len(population) < population_size:
        population.append([rng.random() for _ in range(count)])

    best_boards: list[nesting.CutBoard] = []
    best_skipped: list[nesting.CutPiece] = list(pieces)
    best_score: tuple[float, float, float, float, float, float] | None = None

    def evaluate(keys: list[float]):
        ordered_pieces = _decode_random_key_order(pieces, keys)
        boards, skipped = pack_order_driven_guillotine(
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


def _build_boards_from_sections(
    material: str,
    thickness: float,
    board_width: float,
    board_height: float,
    grain: str,
    board_index: int,
    sections: list[nesting.SectionCandidate],
    used_area: float,
    optimization_mode: str,
    piece_spacing: float,
    primary_capacity: float,
) -> nesting.CutBoard:
    placements: list[nesting.CutPlacement] = []
    primary_offset = 0.0
    for section in sections:
        placements.extend(
            nesting._build_section_placements(
                section,
                primary_offset,
                optimization_mode,
                piece_spacing,
            )
        )
        primary_offset += section.occupied_primary

    main_cut_positions, main_cut_orientation = nesting._build_main_cut_guides(
        sections,
        optimization_mode,
        primary_capacity,
    )

    return nesting.CutBoard(
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


def _build_board_from_packed_measure_sections(
    material: str,
    thickness: float,
    board_width: float,
    board_height: float,
    grain: str,
    board_index: int,
    sections: list[PackedMeasureSection],
    used_area: float,
    optimization_mode: str,
    primary_capacity: float,
) -> nesting.CutBoard:
    placements: list[nesting.CutPlacement] = []
    primary_offset = 0.0
    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)

    for section in sections:
        for local in section.placements:
            if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL:
                x = local.secondary
                y = primary_offset + local.primary
            else:
                x = primary_offset + local.primary
                y = local.secondary
            placements.append(
                nesting.CutPlacement(
                    cut_piece=local.cut_piece,
                    x=x,
                    y=y,
                    width=local.width,
                    height=local.height,
                    rotated=local.rotated,
                )
            )
        primary_offset += section.occupied_primary

    if normalized_mode == nesting.CUT_OPTIMIZATION_LONGITUDINAL:
        main_cut_orientation = "vertical"
    elif normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL:
        main_cut_orientation = "horizontal"
    else:
        main_cut_orientation = ""

    main_cut_positions: list[float] = []
    primary_offset = 0.0
    if main_cut_orientation:
        for section in sections:
            cut_position = primary_offset + section.section_size
            primary_offset += section.occupied_primary
            if cut_position < float(primary_capacity) - 0.5:
                main_cut_positions.append(cut_position)

    return nesting.CutBoard(
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


def pack_measure_driven_guillotine(
    material: str,
    thickness: float,
    pieces: list[nesting.CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    *,
    grain: str = "",
    optimization_mode: str = nesting.CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    """Packer experimental basado en lista descendente de medidas."""

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    if not nesting._uses_guillotine_mode(normalized_mode):
        raise ValueError("El packer de prueba requiere modo longitudinal o transversal.")

    primary_capacity = float(board_height) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    remaining = list(pieces)
    boards: list[nesting.CutBoard] = []
    skipped: list[nesting.CutPiece] = []
    board_index = 1

    while remaining:
        sections: list[nesting.SectionCandidate] = []
        current_primary = 0.0
        used_area = 0.0

        while remaining:
            primary_remaining = primary_capacity - current_primary
            if primary_remaining <= 0.01:
                break

            section = _build_measure_driven_section(
                remaining,
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
            remaining = [
                cut_piece
                for idx, cut_piece in enumerate(remaining)
                if idx not in used_indexes
            ]

        if not sections:
            skipped.extend(remaining)
            break

        boards.append(
            _build_boards_from_sections(
                material,
                thickness,
                board_width,
                board_height,
                grain,
                board_index,
                sections,
                used_area,
                normalized_mode,
                piece_spacing,
                primary_capacity,
            )
        )
        board_index += 1

    return boards, skipped


def pack_measure_split_guillotine(
    material: str,
    thickness: float,
    pieces: list[nesting.CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    *,
    grain: str = "",
    optimization_mode: str = nesting.CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    """Packer experimental con medidas descendentes y subsecciones locales."""

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    if not nesting._uses_guillotine_mode(normalized_mode):
        raise ValueError("El packer de prueba requiere modo longitudinal o transversal.")

    primary_capacity = float(board_height) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    remaining = list(pieces)
    boards: list[nesting.CutBoard] = []
    skipped: list[nesting.CutPiece] = []
    board_index = 1

    while remaining:
        sections: list[PackedMeasureSection] = []
        current_primary = 0.0
        used_area = 0.0

        while remaining:
            primary_remaining = primary_capacity - current_primary
            if primary_remaining <= 0.01:
                break

            section = _build_measure_split_section(
                remaining,
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
            remaining = [
                cut_piece
                for idx, cut_piece in enumerate(remaining)
                if idx not in section.used_indexes
            ]

        if not sections:
            skipped.extend(remaining)
            break

        boards.append(
            _build_board_from_packed_measure_sections(
                material,
                thickness,
                board_width,
                board_height,
                grain,
                board_index,
                sections,
                used_area,
                normalized_mode,
                primary_capacity,
            )
        )
        board_index += 1

    return boards, skipped


def pack_measure_match_split_guillotine(
    material: str,
    thickness: float,
    pieces: list[nesting.CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    *,
    grain: str = "",
    optimization_mode: str = nesting.CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    """Packer experimental por medidas descendentes y mejor coincidencia local."""

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    if not nesting._uses_guillotine_mode(normalized_mode):
        raise ValueError("El packer de prueba requiere modo longitudinal o transversal.")

    primary_capacity = float(board_height) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    remaining = list(pieces)
    boards: list[nesting.CutBoard] = []
    skipped: list[nesting.CutPiece] = []
    board_index = 1

    while remaining:
        sections: list[PackedMeasureSection] = []
        current_primary = 0.0
        used_area = 0.0

        while remaining:
            primary_remaining = primary_capacity - current_primary
            if primary_remaining <= 0.01:
                break

            section = _build_measure_match_split_section(
                remaining,
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
            remaining = [
                cut_piece
                for idx, cut_piece in enumerate(remaining)
                if idx not in section.used_indexes
            ]

        if not sections:
            skipped.extend(remaining)
            break

        boards.append(
            _build_board_from_packed_measure_sections(
                material,
                thickness,
                board_width,
                board_height,
                grain,
                board_index,
                sections,
                used_area,
                normalized_mode,
                primary_capacity,
            )
        )
        board_index += 1

    return boards, skipped


def pack_surface_fit_guillotine(
    material: str,
    thickness: float,
    pieces: list[nesting.CutPiece],
    board_width: float,
    board_height: float,
    piece_spacing: float,
    section_kerf: float,
    *,
    grain: str = "",
    optimization_mode: str = nesting.CUT_OPTIMIZATION_LONGITUDINAL,
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    """Packer experimental: lider por superficie y seccion con menor sobrante."""

    normalized_mode = nesting._normalize_optimization_mode(optimization_mode)
    if not nesting._uses_guillotine_mode(normalized_mode):
        raise ValueError("El packer de prueba requiere modo longitudinal o transversal.")

    primary_capacity = float(board_height) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_width)
    secondary_capacity = float(board_width) if normalized_mode == nesting.CUT_OPTIMIZATION_TRANSVERSAL else float(board_height)
    remaining = list(pieces)
    boards: list[nesting.CutBoard] = []
    skipped: list[nesting.CutPiece] = []
    board_index = 1

    while remaining:
        sections: list[nesting.SectionCandidate] = []
        current_primary = 0.0
        used_area = 0.0

        while remaining:
            primary_remaining = primary_capacity - current_primary
            if primary_remaining <= 0.01:
                break

            section = _best_surface_fit_section(
                remaining,
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
            remaining = [
                cut_piece
                for idx, cut_piece in enumerate(remaining)
                if idx not in used_indexes
            ]

        if not sections:
            skipped.extend(remaining)
            break

        placements: list[nesting.CutPlacement] = []
        primary_offset = 0.0
        for section in sections:
            placements.extend(
                nesting._build_section_placements(
                    section,
                    primary_offset,
                    normalized_mode,
                    piece_spacing,
                )
            )
            primary_offset += section.occupied_primary

        main_cut_positions, main_cut_orientation = nesting._build_main_cut_guides(
            sections,
            normalized_mode,
            primary_capacity,
        )

        boards.append(
            nesting.CutBoard(
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


def _load_context(
    project_name: str,
    material: str,
    thickness: float,
    optimization_mode: str | None,
) -> tuple[ExperimentContext, list[nesting.CutPiece]]:
    project = _load_project(project_name)
    settings = _read_app_settings()
    resolved_optimization_mode = _normalize_cut_optimization_option(
        optimization_mode or settings.get("cut_optimization_mode")
    )
    board_definitions = [
        definition
        for definition in (
            nesting._normalize_board_definition(item)
            for item in (settings.get("available_boards") or [])
        )
        if definition is not None
    ]
    board_definition = nesting._resolve_board_definition(material, thickness, board_definitions)

    if board_definition is None:
        board_width = float(settings.get("cut_board_width") or 1830)
        board_height = float(settings.get("cut_board_height") or 2750)
        board_margin = 0.0
        grain = ""
    else:
        board_width = float(board_definition["width"])
        board_height = float(board_definition["length"])
        board_margin = float(board_definition.get("margin") or 0.0)
        grain = str(board_definition.get("grain") or "")

    squaring_allowance = float(settings.get("cut_squaring_allowance") or 10)
    saw_kerf = max(0.0, float(settings.get("cut_saw_kerf") or 4))
    piece_gap = max(0.0, float(settings.get("cut_piece_gap") or 0))
    grouped_pieces = nesting._expand_project_pieces(project, squaring_allowance=squaring_allowance)
    group_key = (material, round(float(thickness), 2))
    pieces = grouped_pieces.get(group_key, [])
    if not pieces:
        raise ValueError(f"No hay piezas para el grupo {material} {thickness:g} mm.")

    context = ExperimentContext(
        project_name=project.name,
        material=material,
        thickness=float(thickness),
        optimization_mode=resolved_optimization_mode,
        board_width=board_width,
        board_height=board_height,
        board_margin=board_margin,
        usable_board_width=board_width - board_margin * 2.0,
        usable_board_height=board_height - board_margin * 2.0,
        grain=grain,
        piece_spacing=piece_gap + saw_kerf,
        saw_kerf=saw_kerf,
    )
    return context, pieces


def _pack_with_current_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = nesting._pack_group_into_boards(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _pack_with_order_driven_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = pack_order_driven_guillotine(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _pack_with_brkga_tail_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = pack_brkga_tail_guillotine(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _pack_with_surface_fit_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = pack_surface_fit_guillotine(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _pack_with_measure_driven_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = pack_measure_driven_guillotine(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _pack_with_measure_split_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = pack_measure_split_guillotine(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _pack_with_measure_match_split_algorithm(
    context: ExperimentContext,
    ordered_pieces: list[nesting.CutPiece],
) -> tuple[list[nesting.CutBoard], list[nesting.CutPiece]]:
    boards, skipped = pack_measure_match_split_guillotine(
        context.material,
        context.thickness,
        ordered_pieces,
        context.usable_board_width,
        context.usable_board_height,
        context.piece_spacing,
        context.saw_kerf,
        grain=context.grain,
        optimization_mode=context.optimization_mode,
    )
    return nesting._apply_board_margin(
        boards,
        context.board_width,
        context.board_height,
        context.board_margin,
    ), skipped


def _board_summary(board: nesting.CutBoard, show_pieces: bool = False) -> dict:
    full_tail_area, full_tail_span = _full_tail_section_metrics(board)
    summary = {
        "index": board.index,
        "placements": len(board.placements),
        "utilization": round(float(board.utilization), 4),
        "main_cut_orientation": board.main_cut_orientation,
        "main_cut_positions": [round(float(position), 2) for position in board.main_cut_positions],
        "full_tail_area": round(float(full_tail_area), 2),
        "full_tail_area_m2": round(float(full_tail_area) / 1_000_000.0, 4),
        "full_tail_span": round(float(full_tail_span), 2),
    }
    if show_pieces:
        summary["pieces"] = [
            {
                "label": placement.cut_piece.label,
                "cut": [round(float(placement.width), 2), round(float(placement.height), 2)],
                "final": [
                    round(float(placement.cut_piece.final_width or placement.cut_piece.width), 2),
                    round(float(placement.cut_piece.final_height or placement.cut_piece.height), 2),
                ],
                "xy": [round(float(placement.x), 2), round(float(placement.y), 2)],
                "rotated": bool(placement.rotated),
                "area": round(_piece_area(placement.cut_piece), 2),
            }
            for placement in board.placements
        ]
    return summary


def run_experiments(
    project_name: str,
    material: str,
    thickness: float,
    strategies: Iterable[str],
    packers: Iterable[str],
    optimization_mode: str | None = None,
    show_board: int | None = None,
) -> dict:
    context, pieces = _load_context(project_name, material, thickness, optimization_mode)
    results = []
    packer_map = {
        "brkga-tail": _pack_with_brkga_tail_algorithm,
        "current": _pack_with_current_algorithm,
        "measure-driven": _pack_with_measure_driven_algorithm,
        "measure-match-split": _pack_with_measure_match_split_algorithm,
        "measure-split": _pack_with_measure_split_algorithm,
        "order-driven": _pack_with_order_driven_algorithm,
        "surface-fit": _pack_with_surface_fit_algorithm,
    }

    for strategy in strategies:
        ordered_pieces = order_pieces(pieces, strategy, context.optimization_mode, context.grain)
        ordered_preview = [
            {
                "label": cut_piece.label,
                "cut": [round(float(cut_piece.width), 2), round(float(cut_piece.height), 2)],
                "area": round(_piece_area(cut_piece), 2),
            }
            for cut_piece in ordered_pieces[:10]
        ]
        for packer_name in packers:
            packer = packer_map.get(str(packer_name).strip().lower())
            if packer is None:
                raise ValueError(f"Packer no soportado: {packer_name}")
            boards, skipped = packer(context, ordered_pieces)
            selected_board = None
            if show_board is not None:
                selected_board = next((board for board in boards if board.index == show_board), None)
            board_summaries = [_board_summary(board) for board in boards]
            results.append(
                {
                    "strategy": strategy,
                    "packer": packer_name,
                    "board_count": len(boards),
                    "skipped_count": len(skipped),
                    "total_utilization": round(
                        sum(board.utilization for board in boards) / max(1, len(boards)),
                        4,
                    ),
                    "total_full_tail_area_m2": round(
                        sum(board_summary["full_tail_area"] for board_summary in board_summaries) / 1_000_000.0,
                        4,
                    ),
                    "ordered_preview": ordered_preview,
                    "boards": board_summaries,
                    "selected_board": _board_summary(selected_board, show_pieces=True)
                    if selected_board is not None
                    else None,
                }
            )

    return {
        "context": context.__dict__,
        "piece_count": len(pieces),
        "results": results,
    }


def _print_text_report(report: dict) -> None:
    context = report["context"]
    print(
        f"Proyecto: {context['project_name']} | Grupo: {context['material']} "
        f"{context['thickness']:g} mm | Modo: {context['optimization_mode']}"
    )
    print(
        f"Tablero: {context['board_width']:g} x {context['board_height']:g} "
        f"| Margen: {context['board_margin']:g} | Veta: {context['grain'] or '-'}"
    )
    print(f"Piezas del grupo: {report['piece_count']}")
    print()

    for result in report["results"]:
        print(
            f"[{result['packer']}] {result['strategy']}: "
            f"{result['board_count']} placas, "
            f"{result['skipped_count']} sin ubicar, "
            f"utilizacion media {result['total_utilization']}, "
            f"seccion libre completa {result['total_full_tail_area_m2']} m2"
        )
        preview = ", ".join(
            f"{item['label']} ({item['cut'][0]:g}x{item['cut'][1]:g})"
            for item in result["ordered_preview"][:5]
        )
        print(f"  orden inicial: {preview}")
        selected_board = result.get("selected_board")
        if selected_board is not None:
            print(
                f"  placa {selected_board['index']}: "
                f"{selected_board['placements']} piezas, cortes {selected_board['main_cut_positions']}"
            )
            for piece in selected_board.get("pieces", []):
                print(
                    f"    - {piece['label']}: corte {piece['cut'][0]:g}x{piece['cut'][1]:g}, "
                    f"final {piece['final'][0]:g}x{piece['final'][1]:g}, "
                    f"xy {piece['xy'][0]:g},{piece['xy'][1]:g}"
                )
        print()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara ordenamientos experimentales para guillotina de diagramas de corte."
    )
    parser.add_argument("--project-name", required=True, help="Nombre del proyecto registrado.")
    parser.add_argument("--material", required=True, help="Color/material del grupo a analizar.")
    parser.add_argument("--thickness", required=True, type=float, help="Espesor del grupo en mm.")
    parser.add_argument(
        "--strategy",
        dest="strategies",
        action="append",
        choices=(
            "current",
            "input",
            "area-desc",
            "area-primary-desc",
            "max-side-desc",
            "no-grain-major-side",
            "primary-area-desc",
            "secondary-area-desc",
        ),
        help="Estrategia de orden. Se puede repetir. Default: set comparativo base.",
    )
    parser.add_argument(
        "--packer",
        dest="packers",
        action="append",
        choices=(
            "current",
            "brkga-tail",
            "measure-driven",
            "measure-match-split",
            "measure-split",
            "order-driven",
            "surface-fit",
        ),
        help="Packer a ejecutar. Se puede repetir. Default: current y order-driven.",
    )
    parser.add_argument(
        "--optimization-mode",
        help="Modo de optimizacion a forzar. Si se omite, usa app_settings.json.",
    )
    parser.add_argument("--show-board", type=int, help="Incluye detalle de una placa puntual.")
    parser.add_argument("--json", action="store_true", help="Imprime el reporte como JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    report = run_experiments(
        args.project_name,
        args.material,
        args.thickness,
        args.strategies or DEFAULT_STRATEGIES,
        args.packers or ("current", "order-driven"),
        optimization_mode=args.optimization_mode,
        show_board=args.show_board,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
