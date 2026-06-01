"""Editable selection dialogs used by project detail inspection."""

import json
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.qt_helpers import _exec_centered
from app.runtime import APP_SETTINGS_FILE
from app.settings import _read_app_settings


@dataclass(frozen=True)
class EditableSelectionConfig:
    settings_key: str
    default_items: tuple[str, ...]
    window_title: str
    heading: str
    new_title: str
    new_prompt: str
    edit_title: str
    edit_prompt: str
    select_warning: str


HERRAJES_SELECTOR_CONFIG = EditableSelectionConfig(
    settings_key="available_herrajes",
    default_items=(
        "Bisagras",
        "Guías correderas",
        "Manijas",
        "Cerraduras",
        "Tornillos",
        "Tuercas",
        "Pasadores",
        "Soportes",
        "Escuadras",
        "Bisagras ocultas",
        "Amortiguadores",
        "Tirador horizontal",
        "Tirador vertical",
        "Pivote",
        "Cierre magnético",
    ),
    window_title="Seleccionar Herrajes y Accesorios",
    heading="Gestionar Herrajes y Accesorios",
    new_title="Nuevo Herraje",
    new_prompt="Nombre del herraje:",
    edit_title="Editar Herraje",
    edit_prompt="Nombre del herraje:",
    select_warning="Seleccione un herraje.",
)


GUIAS_SELECTOR_CONFIG = EditableSelectionConfig(
    settings_key="available_guias",
    default_items=(
        "Guía de bolas",
        "Guía de rodillo",
        "Guía telescópica",
        "Bisagra de copa",
        "Bisagra de piano",
        "Bisagra invisible",
        "Bisagra de doble acción",
        "Pernio",
        "Soporte de estante",
        "Guía silenciosa",
        "Bisagra ajustable",
        "Bisagra basculante",
    ),
    window_title="Seleccionar Guías y Bisagras",
    heading="Gestionar Guías y Bisagras",
    new_title="Nueva Guía",
    new_prompt="Nombre de la guía:",
    edit_title="Editar Guía",
    edit_prompt="Nombre de la guía:",
    select_warning="Seleccione una guía.",
)


DETALLES_SELECTOR_CONFIG = EditableSelectionConfig(
    settings_key="available_detalles",
    default_items=(
        "Perforacion",
        "Canto de melamina",
        "Canto de madera",
        "Cubrejuntas",
        "Cantonera",
        "Taladro ciego",
        "Taladro pasante",
        "Ranura",
        "Rebaje",
        "Espiga",
        "Mortaja",
        "Machihembrado",
        "Chaflán",
        "Redondeado",
        "Pulido",
        "Acabado lacado",
        "Acabado teñido",
        "Estampado",
        "Incrustación",
        "Tallado",
    ),
    window_title="Seleccionar Detalles de Obra",
    heading="Gestionar Detalles de Obra",
    new_title="Nuevo Detalle",
    new_prompt="Nombre del detalle:",
    edit_title="Editar Detalle",
    edit_prompt="Nombre del detalle:",
    select_warning="Seleccione un detalle.",
)


def _available_items(config: EditableSelectionConfig) -> list[str]:
    settings = _read_app_settings()
    raw_items = settings.get(config.settings_key)
    if not isinstance(raw_items, list):
        return list(config.default_items)

    items = [str(item).strip() for item in raw_items if str(item).strip()]
    return items or list(config.default_items)


def _save_available_items(config: EditableSelectionConfig, items: list[str]) -> None:
    settings = _read_app_settings()
    settings[config.settings_key] = items
    APP_SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def open_editable_selection_dialog(
    parent: QDialog,
    target_field: QLineEdit,
    config: EditableSelectionConfig,
) -> None:
    current_text = target_field.text().strip()
    current_selected = [item.strip() for item in current_text.split("-") if item.strip()]

    dialog = QDialog(parent)
    dialog.setWindowTitle(config.window_title)
    dialog.setMinimumSize(700, 400)

    main_layout = QVBoxLayout()
    main_layout.addWidget(QLabel(config.heading))

    content_layout = QHBoxLayout()

    left_layout = QVBoxLayout()
    left_layout.addWidget(QLabel("Disponibles:"))
    available_list = QListWidget()
    available_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    left_layout.addWidget(available_list)

    edit_buttons_layout = QHBoxLayout()
    btn_new = QPushButton("Nuevo")
    btn_edit = QPushButton("Editar")
    btn_delete = QPushButton("Eliminar")
    edit_buttons_layout.addWidget(btn_new)
    edit_buttons_layout.addWidget(btn_edit)
    edit_buttons_layout.addWidget(btn_delete)
    left_layout.addLayout(edit_buttons_layout)

    center_layout = QVBoxLayout()
    center_layout.addStretch()
    btn_right = QPushButton("→")
    btn_right.setMaximumWidth(40)
    btn_left = QPushButton("←")
    btn_left.setMaximumWidth(40)
    center_layout.addWidget(btn_right)
    center_layout.addWidget(btn_left)
    center_layout.addStretch()

    right_layout = QVBoxLayout()
    right_layout.addWidget(QLabel("Seleccionados:"))
    selected_list = QListWidget()
    selected_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    right_layout.addWidget(selected_list)

    content_layout.addLayout(left_layout, 1)
    content_layout.addLayout(center_layout, 0)
    content_layout.addLayout(right_layout, 1)
    main_layout.addLayout(content_layout)

    dialog_buttons = QHBoxLayout()
    ok_btn = QPushButton("OK")
    cancel_btn = QPushButton("Cancelar")
    dialog_buttons.addStretch()
    dialog_buttons.addWidget(ok_btn)
    dialog_buttons.addWidget(cancel_btn)
    main_layout.addLayout(dialog_buttons)
    dialog.setLayout(main_layout)

    def refresh_available_list() -> None:
        available_list.clear()
        for item in _available_items(config):
            if item not in current_selected:
                available_list.addItem(item)

    def refresh_selected_list() -> None:
        selected_list.clear()
        for item in current_selected:
            selected_list.addItem(item)

    def move_to_selected() -> None:
        current_item = available_list.currentItem()
        if current_item:
            item_text = current_item.text()
            if item_text not in current_selected:
                current_selected.append(item_text)
                refresh_selected_list()
                refresh_available_list()

    def remove_from_selected() -> None:
        current_item = selected_list.currentItem()
        if current_item:
            item_text = current_item.text()
            if item_text in current_selected:
                current_selected.remove(item_text)
                refresh_selected_list()
                refresh_available_list()

    def add_new_item() -> None:
        text, ok = QInputDialog.getText(dialog, config.new_title, config.new_prompt)
        if ok and text.strip():
            saved = _available_items(config)
            new_text = text.strip()
            if new_text not in saved:
                saved.append(new_text)
                _save_available_items(config, saved)
                refresh_available_list()

    def edit_item() -> None:
        current_item = available_list.currentItem()
        if not current_item:
            QMessageBox.warning(dialog, "Editar", config.select_warning)
            return
        old_text = current_item.text()
        text, ok = QInputDialog.getText(dialog, config.edit_title, config.edit_prompt, text=old_text)
        if ok and text.strip():
            saved = _available_items(config)
            if old_text in saved:
                idx = saved.index(old_text)
                saved[idx] = text.strip()
                _save_available_items(config, saved)
                if old_text in current_selected:
                    idx_sel = current_selected.index(old_text)
                    current_selected[idx_sel] = text.strip()
                refresh_selected_list()
                refresh_available_list()

    def delete_item() -> None:
        current_item = available_list.currentItem()
        if not current_item:
            QMessageBox.warning(dialog, "Eliminar", config.select_warning)
            return
        text = current_item.text()
        saved = _available_items(config)
        if text in saved:
            saved.remove(text)
            _save_available_items(config, saved)
            if text in current_selected:
                current_selected.remove(text)
            refresh_selected_list()
            refresh_available_list()

    def apply_selection() -> None:
        target_field.setText(" - ".join(current_selected) if current_selected else "")
        dialog.accept()

    refresh_available_list()
    refresh_selected_list()

    btn_right.clicked.connect(move_to_selected)
    btn_left.clicked.connect(remove_from_selected)
    btn_new.clicked.connect(add_new_item)
    btn_edit.clicked.connect(edit_item)
    btn_delete.clicked.connect(delete_item)
    available_list.itemDoubleClicked.connect(move_to_selected)
    selected_list.itemDoubleClicked.connect(remove_from_selected)
    ok_btn.clicked.connect(apply_selection)
    cancel_btn.clicked.connect(dialog.reject)

    _exec_centered(dialog, parent)
