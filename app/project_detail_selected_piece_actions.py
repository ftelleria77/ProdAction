"""Selected-piece actions for project detail inspection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, MutableMapping, Sequence

from PySide6.QtWidgets import QMessageBox

from app.project_detail_drawings import open_piece_drawing_dialog
from app.project_detail_programs import assign_program_source_to_row, select_pgmx_program_file


@dataclass
class SelectedPieceActionContext:
    parent: object
    project: object
    module_path: Path
    all_rows: list[dict]
    visible_row_indexes: Sequence[int]
    pieces_table: object
    persist_module_config: Callable[[], None]
    refresh_pieces_table: Callable[[], None]
    build_piece_from_row: Callable[[MutableMapping[str, object]], object]
    ensure_piece_drawing: Callable[..., Path | None]
    refresh_piece_drawing_file: Callable[..., Path | None]
    get_invalid_slot_issues_for_row: Callable[[dict], Sequence[object]]
    clear_invalid_slot_cache: Callable[..., None]
    refresh_repair_pgmx_button_state: Callable[[], None]
    program_dimensions_cache: MutableMapping


def _selected_visible_indexes(context: SelectedPieceActionContext, title: str) -> tuple[int, int] | None:
    current_row = context.pieces_table.currentRow()
    if current_row < 0:
        QMessageBox.warning(context.parent, title, "Seleccione una pieza de la lista.")
        return None
    if current_row >= len(context.visible_row_indexes):
        return None
    all_idx = context.visible_row_indexes[current_row]
    if all_idx < 0 or all_idx >= len(context.all_rows):
        return None
    return current_row, all_idx


def select_source_for_selected_piece(context: SelectedPieceActionContext) -> None:
    selected = _selected_visible_indexes(context, "Source")
    if selected is None:
        return
    current_row, all_idx = selected

    source_file = select_pgmx_program_file(context.parent, context.module_path)
    if not source_file:
        return

    piece_row = context.all_rows[all_idx]
    assign_program_source_to_row(piece_row, source_file, context.module_path)
    context.persist_module_config()
    context.refresh_pieces_table()
    context.pieces_table.selectRow(current_row)

    drawing_path = context.ensure_piece_drawing(piece_row, force_regenerate=True)
    if drawing_path is None:
        return

    piece_display_name = str(piece_row.get("name") or piece_row.get("id") or "pieza").strip()
    open_piece_drawing_dialog(context.parent, drawing_path, piece_display_name)


def repair_selected_invalid_pgmx(context: SelectedPieceActionContext) -> None:
    from pgmx.processing import (
        repair_invalid_slot_machining_by_rotating_ccw,
        resolve_piece_program_path,
    )

    selected = _selected_visible_indexes(context, "Corregir PGMX")
    if selected is None:
        return
    current_row, all_idx = selected

    piece_row = context.all_rows[all_idx]
    issues = context.get_invalid_slot_issues_for_row(piece_row)
    if not issues:
        QMessageBox.information(
            context.parent,
            "Corregir PGMX",
            "La pieza seleccionada no tiene ranuras no ejecutables detectadas.",
        )
        context.refresh_repair_pgmx_button_state()
        return

    piece_obj = context.build_piece_from_row(piece_row)
    source_path = resolve_piece_program_path(context.project, piece_obj, context.module_path)
    if source_path is None:
        QMessageBox.warning(
            context.parent,
            "Corregir PGMX",
            "No se encontro el archivo PGMX asociado a la pieza seleccionada.",
        )
        return

    issue_names = ", ".join(
        str(getattr(issue, "feature_name", None) or getattr(issue, "feature_id", None) or "ranura")
        for issue in issues
    )
    answer = QMessageBox.question(
        context.parent,
        "Corregir PGMX",
        (
            "Se detecto una ranura no ejecutable por la herramienta seleccionada.\n\n"
            f"Archivo: {source_path}\n"
            f"Ranura(s): {issue_names}\n\n"
            "El programa va a sintetizar el PGMX girandolo 90 grados antihorario "
            "y va a sobreescribir el archivo original. Continuar?"
        ),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if answer != QMessageBox.Yes:
        return

    try:
        result = repair_invalid_slot_machining_by_rotating_ccw(
            context.project,
            piece_obj,
            context.module_path,
        )
    except Exception as exc:
        QMessageBox.critical(
            context.parent,
            "Corregir PGMX",
            f"No se pudo corregir el PGMX.\n\n{exc}",
        )
        context.clear_invalid_slot_cache()
        context.refresh_pieces_table()
        _restore_current_row(context, current_row)
        return

    context.program_dimensions_cache.clear()
    context.clear_invalid_slot_cache()
    context.refresh_piece_drawing_file(piece_row, row_index=all_idx)
    context.persist_module_config()
    context.refresh_pieces_table()
    _restore_current_row(context, current_row)

    QMessageBox.information(
        context.parent,
        "Corregir PGMX",
        (
            "PGMX corregido correctamente.\n\n"
            f"Archivo: {result.source_path}\n"
            f"Dimensiones: {result.original_length:g} x {result.original_width:g} mm -> "
            f"{result.rotated_length:g} x {result.rotated_width:g} mm"
        ),
    )


def view_drawing_for_selected_piece(context: SelectedPieceActionContext) -> None:
    selected = _selected_visible_indexes(context, "Ver Dibujo")
    if selected is None:
        return
    _, all_idx = selected

    piece_row = context.all_rows[all_idx]
    piece_display_name = str(piece_row.get("name") or piece_row.get("id") or "pieza").strip()
    drawing_path = context.ensure_piece_drawing(piece_row, force_regenerate=False)

    if drawing_path is None or not drawing_path.is_file():
        QMessageBox.warning(
            context.parent,
            "Ver Dibujo",
            (
                "No se encontro el dibujo SVG para la pieza seleccionada.\n\n"
                f"Ruta esperada: {drawing_path}\n\n"
                "Procese el proyecto para generar los dibujos."
            ),
        )
        return

    open_piece_drawing_dialog(context.parent, drawing_path, piece_display_name)


def _restore_current_row(context: SelectedPieceActionContext, current_row: int) -> None:
    if current_row >= 0 and context.pieces_table.rowCount() > 0:
        context.pieces_table.selectRow(max(0, min(current_row, context.pieces_table.rowCount() - 1)))
