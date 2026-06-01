"""Color helpers for project detail piece editing."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from app.qt_helpers import _exec_centered
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import ModuleData, PIECE_GRAIN_CODE_NONE


def configured_board_colors(settings: dict, piece_thickness: float | None = None) -> list[str]:
    colors: list[str] = []
    seen: set[str] = set()
    for board in settings.get("available_boards", []):
        color = str(board.get("color") or "").strip()
        if not color:
            continue
        if piece_thickness is not None:
            try:
                board_thickness = float(board.get("thickness"))
            except (TypeError, ValueError):
                continue
            if abs(board_thickness - piece_thickness) > 0.001:
                continue
        color_key = color.lower()
        if color_key in seen:
            continue
        seen.add(color_key)
        colors.append(color)
    return colors


def module_locale_key(module: ModuleData, project_root: str | Path) -> str:
    locale_name = str(module.locale_name or "").strip()
    if locale_name:
        return locale_name.lower()

    relative_path = str(module.relative_path or "").strip()
    if relative_path:
        relative_parts = Path(relative_path).parts
        if relative_parts:
            return str(relative_parts[0]).strip().lower()

    try:
        root_path = Path(project_root).resolve()
        module_relative = Path(module.path).resolve().relative_to(root_path)
        if module_relative.parts:
            return str(module_relative.parts[0]).strip().lower()
    except Exception:
        pass

    return ""


def preferred_color_index(available_colors: list[str], *preferred_candidates: str | None) -> int:
    for candidate in preferred_candidates:
        normalized_candidate = str(candidate or "").strip()
        if not normalized_candidate:
            continue
        for color_index, color_value in enumerate(available_colors):
            if str(color_value or "").strip().lower() == normalized_candidate.lower():
                return color_index
    return 0


def open_board_color_picker(
    parent: QDialog,
    available_colors: list[str],
    *,
    current_color: str = "",
) -> str | None:
    selected_color, ok = QInputDialog.getItem(
        parent,
        "Seleccionar color",
        "Color:",
        available_colors,
        preferred_color_index(available_colors, current_color),
        False,
    )
    if not ok:
        return None
    return str(selected_color or "").strip()


def open_color_change_dialog(
    parent: QDialog,
    *,
    current_color: str,
    available_colors: list[str],
    locale_enabled: bool,
    preferred_color: str | None = None,
) -> tuple[str, str] | None:
    color_dialog = QDialog(parent)
    color_dialog.setWindowTitle("Cambiar color")
    color_layout = QVBoxLayout()
    color_layout.addWidget(
        QLabel(
            "Seleccione el nuevo color para la pieza.\n"
            f"Color actual: {current_color or '(sin color)'}"
        )
    )

    colors_list = QListWidget()
    for color in available_colors:
        colors_list.addItem(color)
    color_layout.addWidget(colors_list)

    scope_layout = QVBoxLayout()
    scope_layout.addWidget(QLabel("Aplicar a:"))
    only_piece_option = QRadioButton("Solo esta pieza")
    module_option = QRadioButton("Todas las piezas del mismo color de este modulo")
    locale_option = QRadioButton("Todas las piezas del mismo color de este local")
    only_piece_option.setChecked(True)
    locale_option.setEnabled(locale_enabled)
    scope_layout.addWidget(only_piece_option)
    scope_layout.addWidget(module_option)
    scope_layout.addWidget(locale_option)
    color_layout.addLayout(scope_layout)

    buttons_layout = QHBoxLayout()
    buttons_layout.addStretch(1)
    accept_button = QPushButton("Aceptar")
    cancel_button = QPushButton("Cancelar")
    accept_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    buttons_layout.addWidget(accept_button)
    buttons_layout.addWidget(cancel_button)
    color_layout.addLayout(buttons_layout)

    if colors_list.count() > 0:
        colors_list.setCurrentRow(preferred_color_index(available_colors, preferred_color, current_color))

    def accept_color_selection():
        if colors_list.currentItem() is None:
            QMessageBox.warning(color_dialog, "Cambiar color", "Seleccione un color.")
            return
        color_dialog.accept()

    accept_button.clicked.connect(accept_color_selection)
    cancel_button.clicked.connect(color_dialog.reject)
    colors_list.itemDoubleClicked.connect(lambda _item: accept_color_selection())

    color_dialog.setLayout(color_layout)
    if _exec_centered(color_dialog, parent) != QDialog.Accepted or colors_list.currentItem() is None:
        return None

    if locale_option.isChecked() and locale_option.isEnabled():
        scope = "locale"
    elif module_option.isChecked():
        scope = "module"
    else:
        scope = "piece"

    return colors_list.currentItem().text().strip() or None, scope


def apply_color_to_piece_row(row: dict, new_color: str | None, *, force_no_grain: bool = False) -> None:
    row["color"] = new_color
    if force_no_grain:
        row["grain_direction"] = PIECE_GRAIN_CODE_NONE


def apply_color_to_matching_rows(
    rows,
    current_color: str,
    new_color: str | None,
    *,
    force_no_grain: bool = False,
) -> int:
    changed = 0
    for row in rows:
        if str(row.get("color") or "") == current_color:
            apply_color_to_piece_row(row, new_color, force_no_grain=force_no_grain)
            changed += 1
    return changed


def apply_color_to_matching_pieces(
    pieces,
    current_color: str,
    new_color: str | None,
    *,
    force_no_grain: bool = False,
) -> int:
    changed = 0
    for piece in pieces:
        if str(piece.color or "") == current_color:
            piece.color = new_color
            if force_no_grain:
                piece.grain_direction = PIECE_GRAIN_CODE_NONE
            changed += 1
    return changed
