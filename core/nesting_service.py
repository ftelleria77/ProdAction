"""Public cut diagram generation service."""

from __future__ import annotations

from pathlib import Path

from core.model import Project
from core.nesting_boards import apply_board_margin, normalize_board_definition, resolve_board_definition
from core.nesting_dispatch import pack_group_into_boards
from core.nesting_model import CUT_GUILLOTINE_ALGORITHM_PREFERRED, CUT_OPTIMIZATION_NONE, CutBoard
from core.nesting_pdf import build_cut_diagram_pdf
from core.nesting_pieces import expand_project_pieces, safe_float
from core.nesting_strategy import normalize_guillotine_algorithm, normalize_optimization_mode, order_group_pieces


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

    resolved_piece_gap = max(0.0, safe_float(piece_gap) or 0.0)
    resolved_squaring_allowance = max(0.0, safe_float(squaring_allowance) or 0.0)
    resolved_saw_kerf = max(0.0, safe_float(saw_kerf) or 0.0)
    piece_spacing = resolved_piece_gap + resolved_saw_kerf

    grouped_pieces = expand_project_pieces(project, squaring_allowance=resolved_squaring_allowance)
    if not grouped_pieces:
        raise ValueError('No hay piezas válidas para diagramas de corte.')

    skipped_labels: list[str] = []
    group_summaries: list[dict] = []
    missing_board_groups: list[dict] = []
    all_boards: list[CutBoard] = []
    normalized_board_definitions = [
        definition
        for definition in (normalize_board_definition(item) for item in (board_definitions or []))
        if definition is not None
    ]
    use_configured_boards = bool(normalized_board_definitions)
    resolved_optimization_mode = normalize_optimization_mode(optimization_mode)
    resolved_guillotine_algorithm = normalize_guillotine_algorithm(guillotine_algorithm)

    for material, thickness in sorted(grouped_pieces.keys(), key=lambda item: (item[1], item[0])):
        board_definition = resolve_board_definition(material, thickness, normalized_board_definitions) if use_configured_boards else None
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
        ordered_pieces = order_group_pieces(
            grouped_pieces[(material, thickness)],
            resolved_optimization_mode,
            resolved_grain,
        )

        boards, skipped = pack_group_into_boards(
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
        boards = apply_board_margin(boards, resolved_board_width, resolved_board_height, resolved_board_margin)
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


__all__ = ["generate_cut_diagrams"]
