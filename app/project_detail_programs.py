"""Helpers for piece-associated PGMX program files."""

import os
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.project_detail_piece_rows import infer_companion_f6_source, normalize_source_path
from core.pgmx_processing import resolve_piece_program_path


PGMX_FILE_FILTER = "Programas PGMX (*.pgmx);;Todos los archivos (*.*)"


def select_pgmx_program_file(parent, module_path: Path) -> str | None:
    source_file, _ = QFileDialog.getOpenFileName(
        parent,
        "Seleccionar programa asociado",
        str(module_path),
        PGMX_FILE_FILTER,
    )
    return source_file or None


def assign_program_source_to_row(piece_row: dict, source_file: str, module_path: Path) -> None:
    normalized_source = normalize_source_path(source_file, module_path)
    piece_row["source"] = normalized_source
    piece_row["f6_source"] = infer_companion_f6_source(normalized_source, module_path)


def clear_program_metadata(piece_row: dict) -> None:
    piece_row["f6_source"] = None
    piece_row["program_width"] = None
    piece_row["program_height"] = None
    piece_row["program_thickness"] = None


def open_piece_program_in_default_app(parent, project, piece_obj, module_path: Path) -> bool:
    if not str(getattr(piece_obj, "cnc_source", "") or "").strip():
        QMessageBox.warning(
            parent,
            "Editar programa",
            "La pieza no tiene un programa asociado.",
        )
        return False

    source_path = resolve_piece_program_path(project, piece_obj, module_path)
    if source_path is None:
        QMessageBox.warning(
            parent,
            "Editar programa",
            "No se encontro el archivo PGMX asociado a la pieza seleccionada.",
        )
        return False

    try:
        os.startfile(str(source_path))
    except OSError as exc:
        QMessageBox.critical(
            parent,
            "Editar programa",
            (
                "No se pudo abrir el programa asociado.\n\n"
                "Verifique que Maestro este instalado o que los archivos PGMX "
                "tengan una aplicacion predeterminada.\n\n"
                f"{exc}"
            ),
        )
        return False
    return True
