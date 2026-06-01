"""Mixin de listado y edicion tabular de modulos."""

from __future__ import annotations

import datetime
import json
import os
import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.project_dialogs import EditProjectWindow
from app.project_store import (
    _coerce_optional_piece_float_fields,
    _coerce_piece_quantity_field,
    _normalize_project_locales,
    _project_data_path,
    _save_project,
    _total_module_quantity,
)
from app.qt_helpers import _exec_centered
from app.settings import (
    _compact_number,
    _default_en_juego_settings,
    _normalize_cut_optimization_option,
    _normalize_default_paths,
    _normalize_en_juego_settings,
    _parse_piece_quantity_value,
    _read_app_settings,
)
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import (
    LocaleData,
    ModuleData,
    Piece,
    Project,
    normalize_piece_grain_direction,
    normalize_piece_observations,
)
from core.nesting import generate_cut_diagrams
from core.parser import inspect_project_layout, scan_project, scan_project_structure
from core.pgmx_processing import (
    generate_project_piece_drawings,
    resolve_piece_program_path,
)
from core.summary import export_production_sheet, export_production_sheet_pdf, export_summary
from iso_state_synthesis.emitter import emit_candidate_for_pgmx

class ProjectDetailModulesMixin:
    def _project_has_locales_and_modules(self) -> bool:
        locales = _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
        return bool(locales) and bool(getattr(self.project, "modules", []))

    def _project_has_module_window_context(self) -> bool:
        locales = _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
        return bool(locales) or bool(getattr(self.project, "modules", []))

    def update_modules_button(self):
        """Habilitar boton Modulos si hay un local o modulos cargados."""
        enabled = self._project_has_module_window_context()
        self.btn_modules.setEnabled(enabled)
        self.btn_modules.setToolTip("" if enabled else "Agregue un local o procese el proyecto.")

    def update_output_action_buttons(self):
        enabled = self._project_has_locales_and_modules()
        tooltip = "" if enabled else "Procese el proyecto y asegure que tenga locales y modulos."
        for button in (self.btn_sheets, self.btn_cuts):
            button.setEnabled(enabled)
            button.setToolTip(tooltip)

    def show_modules(self):
        """Mostrar lista de módulos en una ventana modal"""
        selected_locale_names: list[str] = []
        seen_locale_keys: set[str] = set()
        for item in self.locales_list.selectedItems():
            locale_name = str(item.data(Qt.UserRole) or "").strip()
            locale_key = locale_name.lower()
            if not locale_name or locale_key in seen_locale_keys:
                continue
            seen_locale_keys.add(locale_key)
            selected_locale_names.append(locale_name)

        if not selected_locale_names:
            current_locale_item = self.locales_list.currentItem()
            current_locale_name = str(current_locale_item.data(Qt.UserRole) or "").strip() if current_locale_item else ""
            if current_locale_name:
                selected_locale_names.append(current_locale_name)

        available_locale_names = self._listed_locale_names()
        if available_locale_names and not selected_locale_names:
            if len(available_locale_names) == 1:
                selected_locale_names = list(available_locale_names)
            else:
                QMessageBox.warning(
                    self,
                    "Módulos",
                    "Seleccione un local en la lista para ver sus módulos.",
                )
                return
        if not selected_locale_names and not self.project.modules:
            QMessageBox.warning(
                self,
                "Módulos",
                "Agregue un local o procese el proyecto para continuar.",
            )
            return

        selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names if locale_name.strip()}
        def filtered_modules_for_dialog() -> list[ModuleData]:
            return [
                module
                for module in self.project.modules
                if not selected_locale_keys or str(module.locale_name or "").strip().lower() in selected_locale_keys
            ]

        dialog = QDialog(self)
        if len(selected_locale_names) == 1:
            dialog.setWindowTitle(f"Local: {selected_locale_names[0]}")
        else:
            dialog.setWindowTitle("Locales")
        dialog.resize(760, 400)

        dlg_layout = QVBoxLayout()
        self.modules_list = QTableWidget()
        self.modules_list.setColumnCount(3)
        self.modules_list.setHorizontalHeaderLabels(["Cantidad", "Módulo", "Piezas"])
        self.modules_list.verticalHeader().setVisible(False)
        self.modules_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.modules_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.modules_list.setSelectionMode(QTableWidget.SingleSelection)
        self.modules_list.setAlternatingRowColors(True)
        modules_header = self.modules_list.horizontalHeader()
        modules_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        modules_header.setSectionResizeMode(1, QHeaderView.Stretch)
        modules_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        def refresh_modules_list_view(
            selected_module_key: str | None = None,
            *,
            focus_selected_row: bool = False,
        ):
            current_visible_modules = filtered_modules_for_dialog()
            current_selected_key = str(selected_module_key or "").strip()
            if not current_selected_key and self.modules_list.currentRow() >= 0:
                selected_item = self.modules_list.item(self.modules_list.currentRow(), 1)
                if selected_item is not None:
                    current_selected_key = str(selected_item.data(Qt.UserRole) or "").strip()
            # Recargar piezas desde module_config.json y normalizar thickness
            for module in current_visible_modules:
                self._reload_module_pieces_from_config(module)
                self._normalize_module_piece_thickness(module)
            
            self.modules_list.setRowCount(len(current_visible_modules))
            selected_row = -1
            for row_idx, module in enumerate(current_visible_modules):
                valid_count = self._valid_piece_count_in_module(module)
                module_label = f"{module.locale_name} / {module.name}" if module.locale_name else module.name
                module_key = module.relative_path or module.path
                module_item = QTableWidgetItem(module_label)
                module_item.setData(Qt.UserRole, module_key)
                quantity_item = QTableWidgetItem(
                    str(_parse_piece_quantity_value(getattr(module, "quantity", None), default=1))
                )
                quantity_item.setTextAlignment(Qt.AlignCenter)
                pieces_item = QTableWidgetItem(str(valid_count))
                pieces_item.setTextAlignment(Qt.AlignCenter)
                self.modules_list.setItem(row_idx, 0, quantity_item)
                self.modules_list.setItem(row_idx, 1, module_item)
                self.modules_list.setItem(row_idx, 2, pieces_item)
                if current_selected_key and str(module_key).strip() == current_selected_key:
                    selected_row = row_idx

            if self.modules_list.rowCount() > 0:
                if selected_row < 0:
                    selected_row = 0
                self.modules_list.clearSelection()
                self.modules_list.setCurrentCell(selected_row, 1)
                self.modules_list.selectRow(selected_row)
                selected_item = self.modules_list.item(selected_row, 1)
                if selected_item is not None:
                    self.modules_list.scrollToItem(selected_item)
                if focus_selected_row:
                    self.modules_list.setFocus(Qt.OtherFocusReason)
            refresh_inspect_button_state()
            refresh_module_order_button_state()

        dlg_layout.addWidget(QLabel("Módulos encontrados:"))
        modules_and_actions_row = QHBoxLayout()
        modules_and_actions_row.addWidget(self.modules_list, 1)

        new_btn = QPushButton("Nuevo\nMódulo")
        inspect_btn = QPushButton("Abrir\nMódulo")
        move_up_btn = QPushButton("Subir")
        move_down_btn = QPushButton("Bajar")
        close_btn = QPushButton("Cerrar")
        for button in (new_btn, inspect_btn, move_up_btn, move_down_btn, close_btn):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

        def refresh_inspect_button_state():
            current_row = self.modules_list.currentRow()
            enabled = 0 <= current_row < self.modules_list.rowCount()
            inspect_btn.setEnabled(enabled)
            inspect_btn.setToolTip("" if enabled else "Seleccione un módulo para abrirlo.")

        def module_at_table_row(row: int) -> ModuleData | None:
            if row < 0 or row >= self.modules_list.rowCount():
                return None
            module_item = self.modules_list.item(row, 1)
            module_key = str(module_item.data(Qt.UserRole) or "").strip() if module_item is not None else ""
            if not module_key:
                return None
            for module in self.project.modules:
                if str(module.relative_path or module.path).strip() == module_key:
                    return module
            return None

        def module_locale_key(module: ModuleData | None) -> str:
            return str(getattr(module, "locale_name", "") or "").strip().lower()

        def can_move_selected_module(delta: int) -> bool:
            current_row = self.modules_list.currentRow()
            target_row = current_row + delta
            current_module = module_at_table_row(current_row)
            target_module = module_at_table_row(target_row)
            return (
                current_module is not None
                and target_module is not None
                and module_locale_key(current_module) == module_locale_key(target_module)
            )

        def refresh_module_order_button_state():
            move_up_btn.setEnabled(can_move_selected_module(-1))
            move_down_btn.setEnabled(can_move_selected_module(1))
            move_up_btn.setToolTip("" if move_up_btn.isEnabled() else "Seleccione un modulo que pueda subir.")
            move_down_btn.setToolTip("" if move_down_btn.isEnabled() else "Seleccione un modulo que pueda bajar.")

        def module_project_index(module: ModuleData) -> int | None:
            module_key = str(module.relative_path or module.path).strip()
            for index, current_module in enumerate(self.project.modules):
                if str(current_module.relative_path or current_module.path).strip() == module_key:
                    return index
            return None

        def persist_module_order(module: ModuleData) -> None:
            locale_key = module_locale_key(module)
            target_locale = next(
                (
                    locale
                    for locale in self.project.locales
                    if str(locale.name or "").strip().lower() == locale_key
                ),
                None,
            )
            if target_locale is not None:
                self._write_locale_config_files([target_locale])
            _save_project(self.project)

        def move_selected_module(delta: int) -> None:
            current_row = self.modules_list.currentRow()
            target_row = current_row + delta
            current_module = module_at_table_row(current_row)
            target_module = module_at_table_row(target_row)
            if (
                current_module is None
                or target_module is None
                or module_locale_key(current_module) != module_locale_key(target_module)
            ):
                return

            current_index = module_project_index(current_module)
            target_index = module_project_index(target_module)
            if current_index is None or target_index is None:
                return

            self.project.modules[current_index], self.project.modules[target_index] = (
                self.project.modules[target_index],
                self.project.modules[current_index],
            )
            persist_module_order(current_module)
            moved_module_key = str(current_module.relative_path or current_module.path).strip()
            refresh_modules_list_view(moved_module_key, focus_selected_row=True)

        self.modules_list.itemSelectionChanged.connect(refresh_inspect_button_state)
        self.modules_list.itemSelectionChanged.connect(refresh_module_order_button_state)
        refresh_modules_list_view()

        actions_column = QVBoxLayout()
        actions_column.setContentsMargins(0, 0, 0, 0)
        actions_column.addWidget(new_btn)
        actions_column.addWidget(inspect_btn)
        actions_column.addWidget(move_up_btn)
        actions_column.addWidget(move_down_btn)
        actions_column.addStretch(1)
        actions_column.addWidget(close_btn)

        modules_and_actions_row.addLayout(actions_column)
        dlg_layout.addLayout(modules_and_actions_row, 1)

        dialog.setLayout(dlg_layout)

        def create_manual_module():
            module_name, ok = QInputDialog.getText(
                dialog,
                "Nuevo módulo",
                "Nombre del módulo:",
                text="Aplicados",
            )
            if not ok:
                return

            module_name = (module_name or "").strip()
            if not module_name:
                QMessageBox.warning(dialog, "Nuevo módulo", "Ingrese un nombre de módulo válido.")
                return

            if selected_locale_keys:
                locale_options = [
                    locale.name
                    for locale in self.project.locales
                    if locale.name.strip().lower() in selected_locale_keys
                ]
            else:
                locale_options = [locale.name for locale in self.project.locales]
            if not locale_options:
                locale_name = self._prompt_new_locale_name(
                    Path(self.project.root_directory),
                    "Nuevo local",
                    "Nombre del local para el nuevo módulo:",
                )
                if not locale_name:
                    return
                locale_dir = Path(self.project.root_directory) / locale_name
                try:
                    locale_dir.mkdir(parents=True, exist_ok=False)
                except Exception as exc:
                    QMessageBox.warning(dialog, "Nuevo local", f"No se pudo crear la carpeta del local: {exc}")
                    return
                selected_locale = LocaleData(name=locale_name, path=locale_name, modules_count=0)
                self.project.locales.append(selected_locale)
            elif len(locale_options) == 1:
                selected_locale = next(locale for locale in self.project.locales if locale.name == locale_options[0])
            else:
                selected_locale_name, ok_locale = QInputDialog.getItem(
                    dialog,
                    "Nuevo módulo",
                    "Local:",
                    locale_options,
                    0,
                    False,
                )
                if not ok_locale:
                    return
                selected_locale = next(
                    locale for locale in self.project.locales if locale.name == str(selected_locale_name).strip()
                )

            existing_names = {
                module.name.lower()
                for module in self.project.modules
                if module.locale_name.lower() == selected_locale.name.lower()
            }
            if module_name.lower() in existing_names:
                QMessageBox.warning(dialog, "Nuevo módulo", "Ya existe un módulo con ese nombre.")
                return

            module_path = Path(self.project.root_directory) / selected_locale.path / module_name
            try:
                module_path.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                QMessageBox.warning(dialog, "Nuevo módulo", "La carpeta del módulo ya existe.")
                return
            except Exception as exc:
                QMessageBox.warning(dialog, "Nuevo módulo", f"No se pudo crear la carpeta: {exc}")
                return

            new_module = ModuleData(
                name=module_name,
                path=str(module_path),
                locale_name=selected_locale.name,
                relative_path=str(module_path.relative_to(Path(self.project.root_directory))).replace("\\", "/"),
                quantity=1,
                pieces=[],
                is_manual=True,
            )
            self.project.modules.append(new_module)
            selected_locale.modules_count += 1

            # Crear configuración base para habilitar inspección del módulo manual.
            config_path = self._module_config_path(new_module)
            config_data = {
                "module": new_module.name,
                "path": str(module_path),
                "generated_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                "en_juego_layout": {},
                "en_juego_output_path": "",
                "en_juego_settings": _default_en_juego_settings(),
                "settings": {
                    "x": "",
                    "y": "",
                    "z": "",
                    "herrajes_y_accesorios": "",
                    "guias_y_bisagras": "",
                    "detalles_de_obra": "",
                },
                "pieces": [],
            }
            config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")
            self._write_locale_config_files([selected_locale])

            _save_project(self.project)
            self.refresh_project_header_info()
            refresh_modules_list_view()
            QMessageBox.information(dialog, "Nuevo módulo", f"Módulo '{module_name}' creado correctamente.")

        new_btn.clicked.connect(create_manual_module)
        inspect_btn.clicked.connect(lambda: self.inspect_module(dialog, refresh_modules_list_view))
        move_up_btn.clicked.connect(lambda: move_selected_module(-1))
        move_down_btn.clicked.connect(lambda: move_selected_module(1))
        self.modules_list.cellDoubleClicked.connect(lambda *_: self.inspect_module(dialog, refresh_modules_list_view))
        close_btn.clicked.connect(dialog.accept)

        _exec_centered(dialog, self)
