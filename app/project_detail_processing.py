"""Mixin de procesamiento de proyectos/locales/modulos."""

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
from pgmx.processing import (
    generate_project_piece_drawings,
    resolve_piece_program_path,
)
from core.summary import export_production_sheet, export_production_sheet_pdf, export_summary
from iso_state_synthesis.emitter import emit_candidate_for_pgmx

class ProjectDetailProcessingMixin:
    def _prompt_new_locale_name(self, root_path: Path, title: str, prompt: str) -> str | None:
        while True:
            locale_name, ok = QInputDialog.getText(self, title, prompt)
            if not ok:
                return None

            locale_name = str(locale_name or "").strip()
            if not locale_name:
                QMessageBox.warning(self, title, "Ingrese un nombre de local válido.")
                continue

            if (
                locale_name in {".", ".."}
                or locale_name.rstrip(" .") != locale_name
                or any(char in locale_name for char in '<>:"/\\|?*')
            ):
                QMessageBox.warning(
                    self,
                    title,
                    "El nombre del local contiene caracteres no validos para una carpeta.",
                )
                continue

            existing_locale_keys = {
                value
                for locale in _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
                for value in {
                    str(locale.name or "").strip().lower(),
                    str(locale.path or "").strip().lower(),
                }
                if value
            }
            if locale_name.lower() in existing_locale_keys:
                QMessageBox.warning(self, title, "Ya existe un local con ese nombre.")
                continue

            locale_dir = root_path / locale_name
            if locale_dir.exists():
                QMessageBox.warning(
                    self,
                    title,
                    "Ya existe una carpeta con ese nombre. Ingrese un local nuevo para evitar mezclar contenido.",
                )
                continue

            return locale_name

    def add_locale(self):
        root_path = Path(self.project.root_directory)
        if not root_path.exists():
            QMessageBox.warning(self, "Agregar Local", "La carpeta raiz del proyecto no existe.")
            return

        locale_name = self._prompt_new_locale_name(
            root_path,
            "Agregar Local",
            "Nombre del nuevo local:",
        )
        if not locale_name:
            return

        new_locale = LocaleData(name=locale_name, path=locale_name, modules_count=0)
        current_locales = _normalize_project_locales(
            getattr(self.project, "locales", []),
            getattr(self.project, "local", ""),
        )
        updated_locales = sorted(
            current_locales + [new_locale],
            key=lambda locale: locale.name.lower(),
        )
        try:
            self._write_locale_config_files([new_locale])
            self.project.locales = updated_locales
            _save_project(self.project)
        except Exception as exc:
            QMessageBox.warning(self, "Agregar Local", f"No se pudo crear el local:\n{exc}")
            return

        self.refresh_project_header_info()
        QMessageBox.information(
            self,
            "Agregar Local",
            f"Local creado correctamente:\n{root_path / locale_name}",
        )

    def _move_loose_modules_to_locale(self, root_path: Path, locale_name: str, module_dirs: list[Path]) -> None:
        locale_dir = root_path / locale_name
        locale_dir.mkdir(parents=True, exist_ok=False)
        for module_dir in module_dirs:
            shutil.move(str(module_dir), str(locale_dir / module_dir.name))

    def _ensure_project_structure_ready(self, root_path: Path) -> bool:
        from core.parser import inspect_project_layout

        layout = inspect_project_layout(root_path)
        if not layout.loose_module_dirs:
            return True

        if not layout.locale_dirs:
            locale_name = self._prompt_new_locale_name(
                root_path,
                "Preparar proyecto",
                (
                    "No se encontraron carpetas de locales.\n"
                    "Ingrese el nombre del local que se creará para mover allí todos los módulos:"
                ),
            )
            if not locale_name:
                return False
            self._move_loose_modules_to_locale(root_path, locale_name, layout.loose_module_dirs)
            return True

        locale_name = self._prompt_new_locale_name(
            root_path,
            "Preparar proyecto",
            (
                "Se encontraron locales existentes y también módulos sueltos en la carpeta principal.\n"
                "Ingrese el nombre del nuevo local que recibirá únicamente esos módulos sueltos:"
            ),
        )
        if not locale_name:
            return False
        self._move_loose_modules_to_locale(root_path, locale_name, layout.loose_module_dirs)
        return True

    def process_project(self):
        """Procesar el proyecto: escanear subcarpetas y extraer piezas de archivos PGMX."""
        from pathlib import Path
        from core.parser import inspect_project_layout, scan_project, scan_project_structure
        from pgmx.processing import generate_project_piece_drawings

        progress_dialog: QProgressDialog | None = None
        progress_step = 0
        total_steps = 8

        def close_progress() -> None:
            nonlocal progress_dialog
            if progress_dialog is None:
                return
            progress_dialog.close()
            progress_dialog = None
            QApplication.processEvents()

        def start_progress(message: str = "Preparando procesamiento del proyecto...") -> None:
            nonlocal progress_dialog
            if progress_dialog is not None:
                progress_dialog.setLabelText(message)
                progress_dialog.show()
                QApplication.processEvents()
                return
            progress_dialog = QProgressDialog(message, "", 0, total_steps, self)
            progress_dialog.setWindowTitle("Procesar Seleccion")
            progress_dialog.setWindowModality(Qt.ApplicationModal)
            progress_dialog.setCancelButton(None)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            progress_dialog.setValue(progress_step)
            progress_dialog.show()
            QApplication.processEvents()

        def update_progress(message: str, *, advance: bool = True) -> None:
            nonlocal progress_step
            if progress_dialog is None:
                return
            if advance:
                progress_step = min(total_steps, progress_step + 1)
            progress_dialog.setLabelText(message)
            progress_dialog.setValue(progress_step)
            QApplication.processEvents()

        try:
            root_path = Path(self.project.root_directory)
            if not root_path.exists():
                QMessageBox.warning(self, "Error", "Carpeta raíz no existe")
                return

            if not self._ensure_project_structure_ready(root_path):
                return

            listed_locale_names = self._listed_locale_names()
            selected_locale_names = self._selected_locale_names()
            processed_locales: list[LocaleData]
            processed_modules: list[ModuleData]
            reprocessed_modules: list[ModuleData] = []

            if listed_locale_names:
                if not selected_locale_names:
                    QMessageBox.warning(
                        self,
                        "Procesar",
                        "Seleccione al menos un local en la lista para procesar.",
                    )
                    return

                start_progress()
                update_progress("Buscando locales seleccionados...", advance=False)
                layout = inspect_project_layout(root_path)
                selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names}
                locale_dirs = [
                    locale_dir
                    for locale_dir in layout.locale_dirs
                    if locale_dir.name.strip().lower() in selected_locale_keys
                ]
                if not locale_dirs:
                    close_progress()
                    QMessageBox.warning(
                        self,
                        "Procesar",
                        "No se encontraron carpetas disponibles para los locales seleccionados.",
                    )
                    return

                rescanned_locale_keys = {locale_dir.name.strip().lower() for locale_dir in locale_dirs}
                processed_locales = []
                processed_modules = []
                update_progress("Escaneando locales seleccionados.")
                for locale_dir in locale_dirs:
                    update_progress(f"Escaneando local {locale_dir.name}...", advance=False)
                    locale_modules = scan_project(locale_dir)
                    for module in locale_modules:
                        module.locale_name = locale_dir.name
                        module.relative_path = str(Path(module.path).relative_to(root_path)).replace("\\", "/")
                    close_progress()
                    resolved_modules = self._resolve_modules_for_processing(locale_modules)
                    if resolved_modules is None:
                        return
                    start_progress(f"Local {locale_dir.name} escaneado.")
                    locale_modules, locale_reprocessed_modules = resolved_modules
                    locale_modules = self._preserve_locale_module_order(locale_dir.name, locale_modules)
                    processed_locales.append(
                        LocaleData(
                            name=locale_dir.name,
                            path=str(locale_dir.relative_to(root_path)).replace("\\", "/"),
                            modules_count=_total_module_quantity(locale_modules),
                        )
                    )
                    processed_modules.extend(locale_modules)
                    reprocessed_modules.extend(locale_reprocessed_modules)

                preserved_locales = [
                    locale
                    for locale in _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
                    if locale.name.strip().lower() not in rescanned_locale_keys
                ]
                preserved_modules = [
                    module
                    for module in self.project.modules
                    if str(module.locale_name or "").strip().lower() not in rescanned_locale_keys
                ]

                self.project.locales = sorted(
                    preserved_locales + processed_locales,
                    key=lambda locale: locale.name.lower(),
                )
                self.project.modules = preserved_modules + processed_modules
            else:
                start_progress()
                update_progress("Escaneando estructura del proyecto...", advance=False)
                scanned_locales, scanned_modules = scan_project_structure(root_path)
                update_progress("Estructura del proyecto escaneada.")
                scanned_modules_by_locale: dict[str, list[ModuleData]] = {}
                for module in scanned_modules:
                    locale_key = str(module.locale_name or "").strip().lower()
                    scanned_modules_by_locale.setdefault(locale_key, []).append(module)

                processed_locales = []
                processed_modules = []
                for locale in scanned_locales:
                    locale_key = locale.name.strip().lower()
                    locale_modules = scanned_modules_by_locale.get(locale_key, [])
                    update_progress(f"Resolviendo local {locale.name}...", advance=False)
                    close_progress()
                    resolved_modules = self._resolve_modules_for_processing(locale_modules)
                    if resolved_modules is None:
                        return
                    start_progress(f"Local {locale.name} resuelto.")
                    locale_modules, locale_reprocessed_modules = resolved_modules
                    locale_modules = self._preserve_locale_module_order(locale.name, locale_modules)
                    locale.modules_count = _total_module_quantity(locale_modules)
                    processed_locales.append(locale)
                    processed_modules.extend(locale_modules)
                    reprocessed_modules.extend(locale_reprocessed_modules)

                self.project.locales = processed_locales
                self.project.modules = processed_modules

            # Normalizar thickness de todas las piezas procesadas
            update_progress("Normalizando piezas procesadas.")
            for module in reprocessed_modules:
                self._normalize_module_piece_thickness(module)

            update_progress("Revisando colores de piezas.")
            close_progress()
            if not self._resolve_processed_piece_colors(reprocessed_modules):
                return
            start_progress("Colores de piezas resueltos.")
            
            update_progress("Guardando configuracion de modulos.")
            self._write_module_config_files(reprocessed_modules)
            self._write_locale_config_files(processed_locales)
            
            # Recargar piezas desde los module_config.json recién generados
            for module in reprocessed_modules:
                self._reload_module_pieces_from_config(module)
            
            self._write_locale_config_files(processed_locales)
            _save_project(self.project)

            from core.summary import export_summary
            summary_csv_path = root_path / "resumen_piezas.csv"
            update_progress("Exportando resumen de piezas.")
            export_summary(self.project, summary_csv_path)

            processed_project = Project(
                name=self.project.name,
                root_directory=self.project.root_directory,
                project_data_file=self.project.project_data_file,
                client=self.project.client,
                created_at=self.project.created_at,
                locales=processed_locales,
                modules=reprocessed_modules,
                output_directory=self.project.output_directory,
            )
            update_progress("Generando dibujos SVG de piezas.")
            generated_drawings, skipped_drawings, pieces_with_machining = generate_project_piece_drawings(
                processed_project,
            )

            total_pieces = sum(self._valid_piece_count_in_module(module) for module in reprocessed_modules)
            module_breakdown = "\n".join([
                f"{module.name}: {self._valid_piece_count_in_module(module)}"
                for module in reprocessed_modules
            ])
            if not module_breakdown:
                module_breakdown = "(sin módulos reprocesados)"
            warning_parts = []
            for module in reprocessed_modules:
                if self._valid_piece_count_in_module(module) == 0:
                    warning_parts.append(module.name)

            self.refresh_project_header_info()
            self.update_modules_button()
            update_progress("Actualizando interfaz.")

            detail_text = (
                f"Locales procesados: {len(processed_locales)}\n"
                f"Módulos reprocesados: {len(reprocessed_modules)}\n"
                f"Módulos conservados desde configuración previa: {len(processed_modules) - len(reprocessed_modules)}\n"
                f"Piezas totales: {total_pieces}\n"
                f"Detalle:\n{module_breakdown}\n"
                f"Resumen guardado en: {summary_csv_path}\n"
                f"Dibujos SVG generados: {generated_drawings}\n"
                f"Piezas con mecanizados detectados: {pieces_with_machining}\n"
                f"Piezas sin PGMX utilizable: {skipped_drawings}\n"
                "Carpeta de dibujos: carpeta de cada módulo"
            )

            if warning_parts:
                detail_text += "\n\nAtención: algunos módulos no tienen piezas: " + ", ".join(warning_parts)

            update_progress("Procesamiento completado.")
            close_progress()
            QMessageBox.information(self, "Procesamiento completado", detail_text)
        except Exception as exc:
            close_progress()
            QMessageBox.warning(self, "Error", f"Error durante el procesamiento: {exc}")
