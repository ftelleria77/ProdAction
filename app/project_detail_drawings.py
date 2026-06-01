"""Drawing helpers for project detail inspection."""

from pathlib import Path
from typing import Callable, Mapping, Sequence

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.qt_helpers import _apply_responsive_window_size, _exec_centered, _scaled_int
from core.pgmx_processing import _sanitize_filename, build_piece_svg, parse_pgmx_for_piece


def build_piece_drawing_path(module_path: Path, piece_row: Mapping[str, object]) -> Path:
    piece_display_name = str(piece_row.get("name") or piece_row.get("id") or "pieza").strip()
    piece_slug = _sanitize_filename(piece_display_name)
    return module_path / f"{piece_slug}.svg"


def open_piece_drawing_dialog(parent: QDialog, drawing_path: Path, piece_display_name: str) -> None:
    drawing_dialog = QDialog(parent)
    drawing_dialog.setWindowTitle(f"Dibujo - {piece_display_name}")

    drawing_layout = QVBoxLayout()
    drawing_layout.addWidget(QLabel(f"Archivo: {drawing_path}"))

    svg_widget = QSvgWidget()
    svg_widget.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
    svg_widget.load(str(drawing_path))
    svg_widget.setMinimumSize(300, 300)
    drawing_layout.addWidget(svg_widget, 1)

    close_drawing_btn = QPushButton("Cerrar")
    close_drawing_btn.clicked.connect(drawing_dialog.accept)
    drawing_layout.addWidget(close_drawing_btn)

    drawing_dialog.setLayout(drawing_layout)
    drawing_scale, _, _ = _apply_responsive_window_size(
        drawing_dialog,
        1000,
        800,
        width_ratio=0.92,
        height_ratio=0.92,
    )
    svg_min = _scaled_int(300, max(drawing_scale, 0.82), 220)
    svg_widget.setMinimumSize(svg_min, svg_min)
    _exec_centered(drawing_dialog, parent)


def ensure_piece_drawing_file(
    parent: QDialog,
    project,
    module_path: Path,
    piece_row: Mapping[str, object],
    build_piece: Callable[[Mapping[str, object]], object],
    *,
    force_regenerate: bool = False,
    show_warning: bool = True,
) -> Path | None:
    drawing_path = build_piece_drawing_path(module_path, piece_row)
    piece_obj = build_piece(piece_row)

    if force_regenerate or not drawing_path.is_file():
        drawing_data = parse_pgmx_for_piece(project, piece_obj, module_path)
        if drawing_data is None:
            if show_warning:
                QMessageBox.warning(
                    parent,
                    "Ver Dibujo",
                    "No se pudo generar el dibujo para la pieza seleccionada. Verifique el PGMX asociado.",
                )
            return None
        build_piece_svg(piece_obj, drawing_data, drawing_path)

    return drawing_path


def remove_piece_drawing_file(
    module_path: Path,
    piece_row: Mapping[str, object],
    all_rows: Sequence[Mapping[str, object]],
    *,
    ignore_row_index: int | None = None,
) -> None:
    drawing_path = build_piece_drawing_path(module_path, piece_row)
    if not drawing_path.is_file():
        return
    for other_idx, other_row in enumerate(all_rows):
        if ignore_row_index is not None and other_idx == ignore_row_index:
            continue
        if not str(other_row.get("source") or "").strip():
            continue
        if build_piece_drawing_path(module_path, other_row) == drawing_path:
            return
    try:
        drawing_path.unlink()
    except OSError:
        pass


def refresh_piece_drawing_file(
    parent: QDialog,
    project,
    module_path: Path,
    piece_row: Mapping[str, object],
    all_rows: Sequence[Mapping[str, object]],
    build_piece: Callable[[Mapping[str, object]], object],
    *,
    row_index: int | None = None,
) -> Path | None:
    if not str(piece_row.get("source") or "").strip():
        remove_piece_drawing_file(module_path, piece_row, all_rows, ignore_row_index=row_index)
        return None

    drawing_path = ensure_piece_drawing_file(
        parent,
        project,
        module_path,
        piece_row,
        build_piece,
        force_regenerate=True,
        show_warning=False,
    )
    if drawing_path is None or not drawing_path.is_file():
        remove_piece_drawing_file(module_path, piece_row, all_rows, ignore_row_index=row_index)
        return None
    return drawing_path
