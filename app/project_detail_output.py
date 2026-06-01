"""Mixin de diagramas, planillas y salida CNC/ISO."""

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

class ProjectDetailOutputMixin:
    def show_cuts(self):
        if not self.project.modules:
            QMessageBox.warning(self, "Diagramas de Cortes", "No hay módulos cargados. Procese el proyecto primero.")
            return

        selected_project = self._project_for_selected_locales("Diagramas de Cortes")
        if selected_project is None:
            return

        settings = _read_app_settings()
        board_width = float(settings.get("cut_board_width") or 1830)
        board_height = float(settings.get("cut_board_height") or 2750)
        piece_gap = float(settings.get("cut_piece_gap") or 0)
        squaring_allowance = float(settings.get("cut_squaring_allowance") or 10)
        saw_kerf = float(settings.get("cut_saw_kerf") or 4)
        board_definitions = settings.get("available_boards") or []
        optimization_mode = _normalize_cut_optimization_option(settings.get("cut_optimization_mode"))
        pdf_output_path = Path(self.project.root_directory) / "diagramas_corte_a4.pdf"

        try:
            from core.nesting import generate_cut_diagrams

            result = generate_cut_diagrams(
                selected_project,
                pdf_output_path,
                board_width=board_width,
                board_height=board_height,
                piece_gap=piece_gap,
                squaring_allowance=squaring_allowance,
                saw_kerf=saw_kerf,
                board_definitions=board_definitions,
                optimization_mode=optimization_mode,
            )

            skipped_count = len(result.get("skipped_pieces", []))
            missing_board_groups = result.get("missing_board_groups", [])
            pdf_file = result.get("pdf_file")
            total_boards = sum(int(group.get("board_count") or 0) for group in result.get("group_summaries", []))
            detail_lines = [
                "PDF de cortes generado correctamente.",
                "",
                f"Tableros incluidos: {total_boards}",
            ]
            if pdf_file:
                detail_lines.append(f"Archivo PDF: {pdf_file}")
            if result.get("used_configured_boards"):
                detail_lines.append("Origen dimensional: lista de tableros configurados.")
            else:
                detail_lines.append(f"Tablero base por defecto: {int(board_width)} x {int(board_height)} mm")
            detail_lines.append("Medidas de piezas: programa PGMX asociado cuando existe.")
            detail_lines.append(
                f"Adicional para escuadrado: {_compact_number(squaring_allowance)} mm | Espesor de sierra: {_compact_number(saw_kerf)} mm"
            )
            detail_lines.append(f"Modo de optimización: {optimization_mode}")
            if optimization_mode != "Sin optimizar":
                detail_lines.append(f"Metodo de guillotina: {result.get('guillotine_algorithm')}")
            if skipped_count:
                detail_lines.append(f"Piezas sin ubicar: {skipped_count}")
            if missing_board_groups:
                preview = ", ".join(
                    f"{group['material']} {group['thickness']}mm"
                    for group in missing_board_groups[:3]
                )
                detail_lines.append(f"Grupos sin tablero configurado: {preview}")

            QMessageBox.information(self, "Diagramas de Cortes", "\n".join(detail_lines))
        except Exception as exc:
            QMessageBox.warning(self, "Diagramas de Cortes", f"Error al generar diagramas: {exc}")

    def _default_output_start_dir(self, path_key: str) -> str:
        default_paths = _normalize_default_paths(_read_app_settings().get("default_paths"))
        configured_value = str(default_paths.get(path_key, "")).strip()
        configured_path = Path(configured_value) if configured_value else None
        if configured_path is not None and configured_path.is_dir():
            return str(configured_path)
        project_root = Path(getattr(self.project, "root_directory", "") or "")
        if str(project_root) and project_root.is_dir():
            return str(project_root)
        return str(Path.home())

    def _safe_output_filename(self, value: str, fallback: str) -> str:
        raw = str(value or "").strip() or fallback
        invalid_chars = '<>:"/\\|?*'
        cleaned = "".join("_" if char in invalid_chars or ord(char) < 32 else char for char in raw)
        return cleaned.strip(" ._") or fallback

    def _output_relative_path(self, value: str, fallback: str) -> Path:
        raw = str(value or "").strip()
        relative_path = Path(raw) if raw else Path(fallback)
        if relative_path.is_absolute():
            try:
                relative_path = relative_path.resolve().relative_to(Path(self.project.root_directory).resolve())
            except Exception:
                relative_path = Path(relative_path.name)
        parts = [
            self._safe_output_filename(part, "carpeta")
            for part in relative_path.parts
            if part not in {"", ".", ".."}
        ]
        if not parts:
            parts = [self._safe_output_filename(fallback, "carpeta")]
        return Path(*parts)

    def _project_cnc_output_root(self, selected_project: Project, output_root: Path) -> Path:
        project_root_name = Path(str(selected_project.root_directory or "")).name.strip()
        project_folder_name = self._safe_output_filename(
            project_root_name or selected_project.name,
            "Proyecto",
        )
        return output_root / project_folder_name

    def _create_plan_sheet_output_structure(self, selected_project: Project, output_root: Path) -> dict[str, Path]:
        project_output_root = self._project_cnc_output_root(selected_project, output_root)
        project_output_root.mkdir(parents=True, exist_ok=True)
        locale_dirs: dict[str, Path] = {}

        for locale in selected_project.locales:
            locale_dir = project_output_root / self._output_relative_path(locale.path, locale.name)
            locale_dir.mkdir(parents=True, exist_ok=True)
            locale_dirs[locale.name.strip().lower()] = locale_dir

        for module in selected_project.modules:
            module_dir = self._module_cnc_output_dir(selected_project, output_root, module)
            module_dir.mkdir(parents=True, exist_ok=True)

        return locale_dirs

    def _module_cnc_output_dir(self, selected_project: Project, output_root: Path, module: ModuleData) -> Path:
        project_output_root = self._project_cnc_output_root(selected_project, output_root)
        locales_by_key = {
            locale.name.strip().lower(): locale
            for locale in selected_project.locales
        }
        module_relative = str(module.relative_path or "").strip()
        if not module_relative:
            locale_key = str(module.locale_name or "").strip().lower()
            locale = locales_by_key.get(locale_key)
            locale_relative = self._output_relative_path(
                locale.path if locale is not None else module.locale_name,
                module.locale_name or "local",
            )
            module_relative = str(locale_relative / module.name)
        return project_output_root / self._output_relative_path(module_relative, module.name)

    def _unique_iso_output_path(
        self,
        module_output_dir: Path,
        pgmx_path: Path,
        used_stems: set[str],
        piece: Piece,
    ) -> Path:
        base_stem = self._safe_output_filename(pgmx_path.stem, "programa")
        stem = base_stem
        if stem.lower() in used_stems:
            piece_label = self._safe_output_filename(
                str(piece.id or piece.name or "").strip(),
                "",
            )
            if piece_label:
                stem = f"{base_stem}_{piece_label}"

        candidate_stem = stem
        suffix = 2
        while candidate_stem.lower() in used_stems:
            candidate_stem = f"{stem}_{suffix}"
            suffix += 1

        used_stems.add(candidate_stem.lower())
        return module_output_dir / f"{candidate_stem}.iso"

    def _export_project_iso_files(self, selected_project: Project, output_root: Path) -> dict:
        from pgmx.processing import resolve_piece_program_path
        from iso_state_synthesis.emitter import emit_candidate_for_pgmx

        generated_paths: list[Path] = []
        skipped_missing: list[dict] = []
        skipped_failed: list[dict] = []
        warnings: list[dict] = []
        duplicate_sources = 0
        used_stems_by_dir: dict[Path, set[str]] = {}
        converted_by_module_source: dict[tuple[str, str], Path] = {}

        for module in selected_project.modules:
            module_path = Path(module.path)
            module_output_dir = self._module_cnc_output_dir(selected_project, output_root, module)
            module_output_dir.mkdir(parents=True, exist_ok=True)
            used_stems = used_stems_by_dir.setdefault(module_output_dir, set())
            module_key = str(module.relative_path or module.path).strip().lower()

            for piece in module.pieces:
                source_value = str(piece.cnc_source or piece.f6_source or "").strip()
                if not source_value:
                    continue

                source_path = resolve_piece_program_path(selected_project, piece, module_path)
                piece_label = str(piece.id or piece.name or "").strip() or "(sin ID)"
                if source_path is None or source_path.suffix.lower() != ".pgmx":
                    skipped_missing.append(
                        {
                            "module": module.name,
                            "piece": piece_label,
                            "source": source_value,
                        }
                    )
                    continue

                try:
                    source_key = str(source_path.resolve()).lower()
                except OSError:
                    source_key = str(source_path).lower()
                conversion_key = (module_key, source_key)
                if conversion_key in converted_by_module_source:
                    duplicate_sources += 1
                    continue

                output_path = self._unique_iso_output_path(module_output_dir, source_path, used_stems, piece)
                try:
                    program = emit_candidate_for_pgmx(source_path, program_name=output_path.stem)
                    program.write_text(output_path)
                except Exception as exc:
                    skipped_failed.append(
                        {
                            "module": module.name,
                            "piece": piece_label,
                            "source": str(source_path),
                            "error": str(exc),
                        }
                    )
                    continue

                converted_by_module_source[conversion_key] = output_path
                generated_paths.append(output_path)
                for warning in program.warnings:
                    warnings.append(
                        {
                            "module": module.name,
                            "piece": piece_label,
                            "source": str(source_path),
                            "code": warning.code,
                            "message": warning.message,
                        }
                    )

        return {
            "generated_paths": generated_paths,
            "missing": skipped_missing,
            "failed": skipped_failed,
            "warnings": warnings,
            "duplicate_sources": duplicate_sources,
        }

    def _production_output_base_name(self, project: Project) -> str:
        name_parts = [str(project.name or "Proyecto").strip()]
        client_name = str(project.client or "").strip()
        if client_name:
            name_parts.append(client_name)
        return self._safe_output_filename(" - ".join(name_parts), "Proyecto")

    def _project_for_single_locale(self, selected_project: Project, locale: LocaleData) -> Project:
        locale_key = locale.name.strip().lower()
        locale_modules = [
            module
            for module in selected_project.modules
            if str(module.locale_name or "").strip().lower() == locale_key
        ]
        return Project(
            name=selected_project.name,
            root_directory=selected_project.root_directory,
            project_data_file=selected_project.project_data_file,
            client=selected_project.client,
            created_at=selected_project.created_at,
            locales=[locale],
            modules=locale_modules,
            output_directory=selected_project.output_directory,
        )

    def generate_sheets(self):
        if not self.project.modules:
            QMessageBox.warning(self, "Generar Planillas", "No hay módulos cargados. Procese el proyecto primero.")
            return

        selected_project = self._project_for_selected_locales("Generar Planillas")
        if selected_project is None:
            return

        output_root_value = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta raiz para estructura de archivos CNC",
            self._default_output_start_dir("cnc_files"),
        )
        if not output_root_value:
            return
        output_root = Path(output_root_value)

        # Loop para permitir reintentos
        while True:
            progress_dialog = None
            try:
                from pgmx.processing import generate_project_piece_drawings
                from core.summary import export_production_sheet, export_production_sheet_pdf

                locale_work_items = []
                for locale in selected_project.locales:
                    locale_project = self._project_for_single_locale(selected_project, locale)
                    if locale_project.modules:
                        locale_work_items.append((locale, locale_project))

                total_steps = max(1, 3 + len(locale_work_items))
                progress_step = 0
                progress_dialog = QProgressDialog(
                    "Preparando generación de archivos...",
                    "",
                    0,
                    total_steps,
                    self,
                )
                progress_dialog.setWindowTitle("Generar Planillas")
                progress_dialog.setWindowModality(Qt.ApplicationModal)
                progress_dialog.setCancelButton(None)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setAutoClose(False)
                progress_dialog.setAutoReset(False)
                progress_dialog.setValue(0)
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

                update_progress("Generando dibujos de piezas desde PGMX...", advance=False)
                generate_project_piece_drawings(selected_project)
                update_progress("Dibujos de piezas generados.")

                update_progress("Creando estructura de carpetas...", advance=False)
                project_output_root = self._project_cnc_output_root(selected_project, output_root)
                locale_dirs = self._create_plan_sheet_output_structure(selected_project, output_root)
                update_progress("Estructura de carpetas creada.")

                update_progress("Convirtiendo programas PGMX asociados a ISO...", advance=False)
                iso_result = self._export_project_iso_files(selected_project, output_root)
                update_progress("Conversion ISO finalizada.")

                base_name = self._production_output_base_name(selected_project)
                generated_pdf_paths: list[Path] = []
                for locale, locale_project in locale_work_items:
                    locale_key = locale.name.strip().lower()
                    locale_dir = locale_dirs.get(locale_key)
                    if locale_dir is None:
                        locale_dir = project_output_root / self._output_relative_path(locale.path, locale.name)
                        locale_dir.mkdir(parents=True, exist_ok=True)
                    pdf_base_name = self._safe_output_filename(
                        f"{base_name} - {locale.name}",
                        "Planilla",
                    )
                    update_progress(f"Generando PDF del local {locale.name}...", advance=False)
                    generated_pdf_paths.append(
                        export_production_sheet_pdf(
                            locale_project,
                            locale_dir / f"{pdf_base_name}.pdf",
                        )
                    )
                    update_progress(f"PDF del local {locale.name} generado.")

                if progress_dialog is not None:
                    progress_dialog.setLabelText("Estructura, ISO y PDF generados.")
                    progress_dialog.setValue(total_steps)
                    QApplication.processEvents()
                    progress_dialog.close()
                    progress_dialog = None

                excel_default_path = str(Path(self._default_output_start_dir("excel_sheets")) / f"{base_name}.xlsx")
                excel_output_file, _ = QFileDialog.getSaveFileName(
                    self,
                    "Guardar planilla Excel",
                    excel_default_path,
                    "Excel (*.xlsx)",
                )
                generated_excel_path = None
                if excel_output_file:
                    excel_output_path = Path(excel_output_file)
                    if excel_output_path.suffix.lower() != ".xlsx":
                        excel_output_path = excel_output_path.with_suffix(".xlsx")
                    generated_excel_path = export_production_sheet(
                        selected_project,
                        excel_output_path,
                    )

                detail_lines = [
                    "Planillas generadas correctamente.",
                    "",
                    f"Carpeta raiz seleccionada: {output_root}",
                    f"Carpeta proyecto CNC: {project_output_root}",
                ]
                if generated_excel_path is not None:
                    detail_lines.append(f"Excel: {generated_excel_path}")
                else:
                    detail_lines.append("Excel: no guardado.")
                if generated_pdf_paths:
                    detail_lines.append("PDF por local:")
                    detail_lines.extend(str(path) for path in generated_pdf_paths)
                generated_iso_paths = iso_result.get("generated_paths", [])
                missing_iso_sources = iso_result.get("missing", [])
                failed_iso_sources = iso_result.get("failed", [])
                iso_warnings = iso_result.get("warnings", [])
                duplicate_iso_sources = int(iso_result.get("duplicate_sources") or 0)
                detail_lines.append(f"ISO generados: {len(generated_iso_paths)}")
                if duplicate_iso_sources:
                    detail_lines.append(f"PGMX repetidos reutilizados: {duplicate_iso_sources}")
                if missing_iso_sources:
                    detail_lines.append(f"PGMX asociados no encontrados: {len(missing_iso_sources)}")
                if failed_iso_sources:
                    detail_lines.append(f"PGMX no convertidos a ISO: {len(failed_iso_sources)}")
                    for failed_item in failed_iso_sources[:5]:
                        detail_lines.append(
                            "  - "
                            f"{failed_item.get('module', '')} / {failed_item.get('piece', '')}: "
                            f"{failed_item.get('error', '')}"
                        )
                if iso_warnings:
                    detail_lines.append(f"Advertencias ISO: {len(iso_warnings)}")
                QMessageBox.information(
                    self,
                    "Generar Planillas",
                    "\n".join(detail_lines),
                )
                break  # Éxito, salir del loop
            except Exception as exc:
                if progress_dialog is not None:
                    progress_dialog.close()
                    progress_dialog = None
                # Mostrar error con opciones de reintentar
                error_msg = f"No se pudieron generar las planillas:\n\n{exc}"
                
                # Crear un diálogo personalizado con más opciones
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Generar Planillas - Error")
                dlg.setText(error_msg)
                dlg.setIcon(QMessageBox.Critical)
                
                retry_btn = dlg.addButton("Reintentar", QMessageBox.ActionRole)
                change_location_btn = dlg.addButton("Guardar en otro lugar", QMessageBox.ActionRole)
                cancel_btn = dlg.addButton("Cancelar", QMessageBox.RejectRole)
                
                _exec_centered(dlg, self)
                
                if dlg.clickedButton() == cancel_btn:
                    break  # Usuario cancela, salir del loop
                elif dlg.clickedButton() == change_location_btn:
                    new_output_root = QFileDialog.getExistingDirectory(
                        self,
                        "Seleccionar carpeta raiz para estructura de archivos CNC",
                        str(output_root),
                    )
                    if new_output_root:
                        output_root = Path(new_output_root)
                    else:
                        break
