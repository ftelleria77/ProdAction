"""Mixin de inspeccion y edicion de modulos del detalle de proyecto."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from app.project_store import _save_project
from app.project_detail_module_persistence import (
    build_module_settings_payload,
    persist_inspected_module_config,
    sync_piece_program_dimensions_from_rows,
)
from app.project_detail_module_settings_panel import build_project_detail_module_settings_panel
from app.project_detail_drawings import (
    build_piece_drawing_path,
    ensure_piece_drawing_file,
    refresh_piece_drawing_file as refresh_piece_drawing_file_for_row,
    remove_piece_drawing_file as remove_piece_drawing_file_for_row,
)
from app.project_detail_piece_editor_dialog import PieceEditorDialogContext, open_piece_editor_dialog
from app.project_detail_piece_actions import build_project_detail_piece_actions
from app.project_detail_piece_table import (
    PIECES_COL_ID,
    configure_piece_table,
    create_piece_table,
)
from app.project_detail_piece_table_rows import (
    bounded_table_row,
    can_move_visible_piece,
    clear_piece_table_widgets,
    filtered_piece_table_rows,
    piece_table_observations_text,
    render_piece_table_rows,
    set_piece_table_observations_item,
    visible_piece_all_index,
    visible_piece_row_for_all_index,
    visible_piece_row_for_id,
)
from app.project_detail_pgmx import (
    clear_invalid_slot_cache_entries,
    get_cached_invalid_slot_issues,
    invalid_slot_message,
)
from app.project_detail_selected_piece_actions import (
    SelectedPieceActionContext,
    edit_selected_piece as edit_selected_piece_action,
    remove_selected_piece as remove_selected_piece_action,
    repair_selected_invalid_pgmx as repair_selected_invalid_pgmx_action,
    select_source_for_selected_piece as select_source_for_selected_piece_action,
    view_drawing_for_selected_piece as view_drawing_for_selected_piece_action,
)
from app.project_detail_en_juego_state import (
    clear_persistent_en_juego_info as clear_persistent_en_juego_config_info,
    has_configurable_en_juego_pieces as rows_have_configurable_en_juego_pieces,
    has_persistent_en_juego_info as config_has_persistent_en_juego_info,
    sync_en_juego_observations as sync_en_juego_observations_for_rows,
)
from app.project_detail_en_juego_configuration import (
    open_en_juego_configuration_dialog as open_en_juego_configuration_dialog_flow,
)
from app.project_detail_color_changes import apply_scoped_color_change
from app.project_detail_colors import (
    configured_board_colors,
    module_locale_key,
    open_color_change_dialog,
)
from app.project_detail_dialog_lifecycle import (
    close_dialog_if_confirmed,
    confirm_save_before_close,
    install_reject_confirmation,
)
from app.project_detail_piece_rows import (
    build_orphan_program_row,
    build_piece_from_row as build_piece_from_row_data,
    find_orphan_pgmx_files,
    infer_companion_f6_source as infer_companion_f6_source_for_module,
    normalize_piece_row_flags,
    normalize_source_path as normalize_module_source_path,
    orphan_program_preview_text,
)
from app.qt_helpers import (
    _apply_responsive_window_size,
    _exec_centered,
)
from app.settings import (
    _board_color_has_no_grain,
    _normalize_en_juego_settings,
    _read_app_settings,
)
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import (
    ModuleData,
    set_piece_en_juego_observation,
)
from pgmx.processing import get_pgmx_program_dimension_notes


class ProjectDetailInspectionMixin:
    def inspect_module(self, parent_dialog, on_module_updated=None):
        """Mostrar piezas del módulo seleccionado"""
        selected_item = None
        if isinstance(self.modules_list, QTableWidget):
            current_row = self.modules_list.currentRow()
            if current_row >= 0:
                selected_item = self.modules_list.item(current_row, 1)
        else:
            selected_item = self.modules_list.currentItem()
        if not selected_item:
            QMessageBox.warning(parent_dialog, "Inspeccionar", "Seleccione un módulo primero.")
            return

        # Extraer nombre del módulo del texto del item
        module_key = str(selected_item.data(Qt.UserRole) or "").strip()
        
        # Encontrar el módulo correspondiente
        selected_module = None
        for module in self.project.modules:
            current_key = module.relative_path or module.path
            if current_key == module_key:
                selected_module = module
                break

        module_name = selected_module.name if selected_module else selected_item.text().split(" (")[0]
        
        if not selected_module:
            QMessageBox.warning(parent_dialog, "Error", "Módulo no encontrado.")
            return

        # Crear ventana de inspección
        inspect_dialog = QDialog(parent_dialog)
        inspect_dialog.setWindowTitle(f"Piezas - {module_name}")
        inspect_scale, inspect_width, _ = _apply_responsive_window_size(
            inspect_dialog,
            1600,
            640,
            width_ratio=0.96,
            height_ratio=0.90,
        )
        compact_scale = max(inspect_scale, 0.82)

        config_path = self._module_config_path(selected_module)
        if not config_path.exists():
            QMessageBox.warning(
                parent_dialog,
                "Inspeccionar",
                "No existe el archivo de configuración del módulo. Procese el proyecto para generarlo.",
            )
            return

        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config_data.get("en_juego_layout"), dict):
            config_data["en_juego_layout"] = {}
        config_data["en_juego_settings"] = _normalize_en_juego_settings(config_data.get("en_juego_settings"))
        settings = config_data.get("settings", {})
        raw_rows = config_data.get("pieces", [])
        if not isinstance(raw_rows, list):
            raw_rows = []

        all_rows = [
            normalize_piece_row_flags(piece_row)
            for piece_row in raw_rows
            if isinstance(piece_row, dict)
        ]
        module_path = Path(selected_module.path)
        pgmx_names, pgmx_relpaths = self._build_pgmx_index(module_path)

        def normalize_source_path(file_path: str) -> str:
            return normalize_module_source_path(file_path, module_path)

        def orphan_pgmx_files() -> list[Path]:
            return find_orphan_pgmx_files(module_path, all_rows)

        def row_for_orphan_program(program_path: Path) -> dict:
            return build_orphan_program_row(
                project=self.project,
                module_path=module_path,
                module_name=selected_module.name,
                program_path=program_path,
                existing_rows=all_rows,
                pgmx_status=lambda source_value: self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths),
            )

        def prompt_add_orphan_programs() -> bool:
            orphan_files = orphan_pgmx_files()
            if not orphan_files:
                return False

            answer = QMessageBox.question(
                inspect_dialog,
                "Programas no asociados",
                (
                    "Se encontraron programas PGMX en la carpeta del modulo "
                    "que no estan asociados a ninguna pieza.\n\n"
                    f"{orphan_program_preview_text(orphan_files, module_path)}\n\n"
                    "Desea agregarlos a la lista de piezas?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                return False

            for program_path in orphan_files:
                all_rows.append(row_for_orphan_program(program_path))
            return True

        added_orphan_program_rows = prompt_add_orphan_programs()

        layout = QVBoxLayout()
        has_unsaved_changes = False

        def mark_unsaved_changes(*_):
            nonlocal has_unsaved_changes
            has_unsaved_changes = True

        module_settings_panel = build_project_detail_module_settings_panel(
            parent_dialog=inspect_dialog,
            target_layout=layout,
            settings=settings,
            module_quantity=getattr(selected_module, "quantity", None),
            compact_scale=compact_scale,
            on_changed=mark_unsaved_changes,
        )
        dim_x_field = module_settings_panel.dim_x_field
        dim_y_field = module_settings_panel.dim_y_field
        dim_z_field = module_settings_panel.dim_z_field
        module_quantity_field = module_settings_panel.module_quantity_field
        herrajes_field = module_settings_panel.herrajes_field
        guias_field = module_settings_panel.guias_field
        detalles_field = module_settings_panel.detalles_field

        pieces_title = QLabel("")
        layout.addWidget(pieces_title)
        pgmx_repair_warning_label = QLabel("")
        pgmx_repair_warning_label.setWordWrap(True)
        pgmx_repair_warning_label.setStyleSheet("color: #B71C1C; font-weight: 600;")
        pgmx_repair_warning_label.hide()
        layout.addWidget(pgmx_repair_warning_label)

        pieces_table = create_piece_table()
        visible_row_indexes = []
        refreshing_pieces_table = False
        program_dimensions_cache = {}
        configure_en_juego_btn = None
        repair_pgmx_btn = None
        move_piece_up_btn = None
        move_piece_down_btn = None
        invalid_slot_cache = {}

        def build_piece_from_row(piece_row):
            return build_piece_from_row_data(piece_row, selected_module.name)

        def selected_piece_all_index(warning_title: str | None = None):
            current_row = pieces_table.currentRow()
            if current_row < 0:
                if warning_title:
                    QMessageBox.warning(inspect_dialog, warning_title, "Seleccione una pieza de la lista.")
                return None
            return visible_piece_all_index(current_row, visible_row_indexes)

        def select_piece_table_row(row_idx: int, *, focus_selected_row: bool = False) -> None:
            if row_idx < 0 or row_idx >= pieces_table.rowCount():
                return
            pieces_table.clearSelection()
            pieces_table.setCurrentCell(row_idx, PIECES_COL_ID)
            pieces_table.selectRow(row_idx)
            selected_item = pieces_table.item(row_idx, PIECES_COL_ID)
            if selected_item is not None:
                pieces_table.scrollToItem(selected_item)
            if focus_selected_row:
                pieces_table.setFocus(Qt.OtherFocusReason)

        def select_visible_piece_by_all_index(all_idx: int, *, focus_selected_row: bool = False) -> bool:
            visible_row = visible_piece_row_for_all_index(all_idx, visible_row_indexes)
            if visible_row is None:
                return False
            select_piece_table_row(visible_row, focus_selected_row=focus_selected_row)
            return True

        def select_visible_piece_by_id(piece_id: str, fallback_row: int | None = None):
            visible_row = visible_piece_row_for_id(piece_id, all_rows, visible_row_indexes)
            if visible_row is not None:
                select_piece_table_row(visible_row)
                return

            fallback_visible_row = bounded_table_row(fallback_row, pieces_table.rowCount())
            if fallback_visible_row is not None:
                select_piece_table_row(fallback_visible_row)

        def infer_companion_f6_source(source_value: str):
            return infer_companion_f6_source_for_module(source_value, module_path)

        def clear_invalid_slot_cache(source_value: str | None = None):
            clear_invalid_slot_cache_entries(invalid_slot_cache, source_value)

        def get_invalid_slot_issues_for_row(piece_row: dict):
            return get_cached_invalid_slot_issues(
                invalid_slot_cache,
                project=self.project,
                module_path=module_path,
                piece_row=piece_row,
                build_piece=build_piece_from_row,
            )

        def refresh_repair_pgmx_button_state():
            if repair_pgmx_btn is None:
                return
            all_idx = selected_piece_all_index()
            if all_idx is None:
                repair_pgmx_btn.setEnabled(False)
                repair_pgmx_btn.setToolTip("Seleccione una pieza con ranura no ejecutable.")
                return
            issues = get_invalid_slot_issues_for_row(all_rows[all_idx])
            repair_pgmx_btn.setEnabled(bool(issues))
            repair_pgmx_btn.setToolTip(
                "Corregir PGMX girandolo 90 grados antihorario"
                if issues
                else "La pieza seleccionada no tiene ranuras no ejecutables detectadas."
            )

        def can_move_selected_piece(delta: int) -> bool:
            return can_move_visible_piece(
                pieces_table.currentRow(),
                pieces_table.rowCount(),
                visible_row_indexes,
                delta,
            )

        def refresh_piece_order_button_state():
            if move_piece_up_btn is None or move_piece_down_btn is None:
                return
            move_piece_up_btn.setEnabled(can_move_selected_piece(-1))
            move_piece_down_btn.setEnabled(can_move_selected_piece(1))
            move_piece_up_btn.setToolTip(
                "" if move_piece_up_btn.isEnabled() else "Seleccione una pieza que pueda subir."
            )
            move_piece_down_btn.setToolTip(
                "" if move_piece_down_btn.isEnabled() else "Seleccione una pieza que pueda bajar."
            )

        def swap_piece_dimensions(all_idx: int, visible_row: int | None = None):
            if all_idx < 0 or all_idx >= len(all_rows):
                return
            piece_row = all_rows[all_idx]
            piece_row["height"], piece_row["width"] = piece_row.get("width"), piece_row.get("height")
            mark_unsaved_changes()
            refresh_pieces_table()
            if visible_row is not None and pieces_table.rowCount() > 0:
                pieces_table.selectRow(max(0, min(visible_row, pieces_table.rowCount() - 1)))

        def swap_all_piece_dimensions():
            if not all_rows:
                return
            current_row = pieces_table.currentRow()
            for piece_row in all_rows:
                piece_row["height"], piece_row["width"] = piece_row.get("width"), piece_row.get("height")
            mark_unsaved_changes()
            refresh_pieces_table()
            if current_row >= 0 and pieces_table.rowCount() > 0:
                pieces_table.selectRow(max(0, min(current_row, pieces_table.rowCount() - 1)))

        def update_piece_flag(all_idx: int, field_name: str, state: int):
            if refreshing_pieces_table:
                return
            normalized_state = Qt.CheckState(state) == Qt.CheckState.Checked
            all_rows[all_idx][field_name] = normalized_state
            mark_unsaved_changes()
            if field_name == "en_juego":
                all_rows[all_idx]["observations"] = set_piece_en_juego_observation(
                    all_rows[all_idx].get("observations"),
                    normalized_state,
                )
                refresh_visible_piece_observations(all_idx)
                refresh_configure_en_juego_button_state()
                if not normalized_state:
                    prompt_clear_persistent_en_juego_info_if_needed()

        def has_configurable_en_juego_pieces() -> bool:
            return rows_have_configurable_en_juego_pieces(all_rows)

        def has_persistent_en_juego_info() -> bool:
            return config_has_persistent_en_juego_info(config_data)

        def clear_persistent_en_juego_info():
            clear_persistent_en_juego_config_info(config_data)
            mark_unsaved_changes()

        def prompt_clear_persistent_en_juego_info_if_needed():
            if has_configurable_en_juego_pieces() or not has_persistent_en_juego_info():
                return
            answer = QMessageBox.question(
                inspect_dialog,
                "Eliminar En-Juego",
                (
                    "Ya no hay piezas marcadas como En-Juego en este modulo.\n\n"
                    "Existe informacion guardada de En-Juego para este modulo. "
                    "Desea eliminar toda esa informacion?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer == QMessageBox.Yes:
                clear_persistent_en_juego_info()

        def refresh_configure_en_juego_button_state():
            if configure_en_juego_btn is None:
                return
            enabled = has_configurable_en_juego_pieces()
            configure_en_juego_btn.setEnabled(enabled)
            configure_en_juego_btn.setToolTip(
                "Configurar En Juego"
                if enabled
                else "Marque al menos una pieza en la columna En-Juego."
            )

        def refresh_visible_piece_observations(all_idx: int):
            if all_idx not in visible_row_indexes:
                return
            row_idx = visible_row_indexes.index(all_idx)
            if row_idx < 0 or row_idx >= pieces_table.rowCount():
                return

            piece_row = all_rows[all_idx]
            notes = get_pgmx_program_dimension_notes(
                self.project,
                [build_piece_from_row(piece_row)],
                module_path,
                cache=program_dimensions_cache,
            )
            program_dimension_note = notes[0] if notes else ""
            invalid_slot_note = invalid_slot_message(get_invalid_slot_issues_for_row(piece_row))
            set_piece_table_observations_item(
                pieces_table,
                row_idx,
                piece_table_observations_text(
                    piece_row,
                    program_dimension_note,
                    invalid_slot_note,
                ),
            )

        def sync_en_juego_observations():
            sync_en_juego_observations_for_rows(all_rows)

        def refresh_pieces_table():
            nonlocal refreshing_pieces_table
            clear_piece_table_widgets(pieces_table)

            sync_piece_program_dimensions_from_rows(
                project=self.project,
                module_path=module_path,
                piece_rows=all_rows,
                build_piece_from_row=build_piece_from_row,
                cache=program_dimensions_cache,
            )

            visible_row_indexes.clear()
            filtered = filtered_piece_table_rows(all_rows, self._is_valid_thickness_value)
            for all_idx, _ in filtered:
                visible_row_indexes.append(all_idx)

            pieces_title.setText(f"Piezas del módulo '{module_name}' ({len(filtered)} piezas):")
            pieces_table.setRowCount(len(filtered))
            refreshing_pieces_table = True
            filtered_piece_objects = [build_piece_from_row(piece_row) for _, piece_row in filtered]
            filtered_program_notes = get_pgmx_program_dimension_notes(
                self.project,
                filtered_piece_objects,
                module_path,
                cache=program_dimensions_cache,
            )
            invalid_slot_row_count = render_piece_table_rows(
                pieces_table,
                filtered,
                filtered_program_notes,
                pgmx_status_for_source=lambda source_value: self._get_pgmx_status(
                    source_value,
                    pgmx_names,
                    pgmx_relpaths,
                ),
                invalid_slot_issues_for_row=get_invalid_slot_issues_for_row,
                swap_piece_dimensions=swap_piece_dimensions,
                update_piece_flag=update_piece_flag,
                compact_scale=compact_scale,
            )

            if invalid_slot_row_count:
                pgmx_repair_warning_label.setText(
                    f"Se detectaron {invalid_slot_row_count} pieza(s) con ranuras no ejecutables. "
                    "Seleccione una fila y use 'Corregir PGMX' para sintetizar el archivo rotado."
                )
                pgmx_repair_warning_label.show()
            else:
                pgmx_repair_warning_label.clear()
                pgmx_repair_warning_label.hide()
            refreshing_pieces_table = False
            refresh_configure_en_juego_button_state()
            refresh_repair_pgmx_button_state()
            refresh_piece_order_button_state()

        refresh_pieces_table()

        configure_piece_table(
            pieces_table,
            compact_scale=compact_scale,
            inspect_width=inspect_width,
            swap_all_piece_dimensions=swap_all_piece_dimensions,
        )

        def persist_module_config():
            nonlocal has_unsaved_changes

            persist_inspected_module_config(
                project=self.project,
                selected_module=selected_module,
                config_path=config_path,
                config_data=config_data,
                piece_rows=all_rows,
                module_settings=build_module_settings_payload(
                    x=dim_x_field.text(),
                    y=dim_y_field.text(),
                    z=dim_z_field.text(),
                    herrajes_y_accesorios=herrajes_field.text(),
                    guias_y_bisagras=guias_field.text(),
                    detalles_de_obra=detalles_field.text(),
                ),
                module_quantity=module_quantity_field.text().strip(),
                module_path=module_path,
                build_piece_from_row=build_piece_from_row,
                program_dimensions_cache=program_dimensions_cache,
                write_locale_config_files=self._write_locale_config_files,
                save_project=_save_project,
                on_module_updated=on_module_updated,
            )
            has_unsaved_changes = False

        if added_orphan_program_rows:
            persist_module_config()

        def move_selected_piece(delta: int) -> None:
            current_row = pieces_table.currentRow()
            target_row = current_row + delta
            if not can_move_selected_piece(delta):
                return
            current_all_idx = visible_piece_all_index(current_row, visible_row_indexes, all_rows_count=len(all_rows))
            target_all_idx = visible_piece_all_index(target_row, visible_row_indexes, all_rows_count=len(all_rows))
            if current_all_idx is None or target_all_idx is None:
                return

            all_rows[current_all_idx], all_rows[target_all_idx] = all_rows[target_all_idx], all_rows[current_all_idx]
            persist_module_config()
            refresh_pieces_table()
            select_visible_piece_by_all_index(target_all_idx, focus_selected_row=True)
            refresh_piece_order_button_state()

        def piece_from_row(piece_row):
            return build_piece_from_row(piece_row)

        def drawing_path_for_piece_row(piece_row):
            return build_piece_drawing_path(module_path, piece_row)

        def ensure_piece_drawing(piece_row, force_regenerate=False, show_warning=True):
            return ensure_piece_drawing_file(
                inspect_dialog,
                self.project,
                module_path,
                piece_row,
                piece_from_row,
                force_regenerate=force_regenerate,
                show_warning=show_warning,
            )

        def remove_piece_drawing_file(piece_row, ignore_row_index: int | None = None):
            remove_piece_drawing_file_for_row(
                module_path,
                piece_row,
                all_rows,
                ignore_row_index=ignore_row_index,
            )

        def refresh_piece_drawing_file(piece_row, row_index: int | None = None):
            return refresh_piece_drawing_file_for_row(
                inspect_dialog,
                self.project,
                module_path,
                piece_row,
                all_rows,
                piece_from_row,
                row_index=row_index,
            )

        def selected_piece_action_context():
            return SelectedPieceActionContext(
                parent=inspect_dialog,
                project=self.project,
                module_path=module_path,
                all_rows=all_rows,
                visible_row_indexes=visible_row_indexes,
                pieces_table=pieces_table,
                persist_module_config=persist_module_config,
                refresh_pieces_table=refresh_pieces_table,
                build_piece_from_row=build_piece_from_row,
                ensure_piece_drawing=ensure_piece_drawing,
                refresh_piece_drawing_file=refresh_piece_drawing_file,
                remove_piece_drawing_file=remove_piece_drawing_file,
                select_visible_piece_by_id=select_visible_piece_by_id,
                get_invalid_slot_issues_for_row=get_invalid_slot_issues_for_row,
                clear_invalid_slot_cache=clear_invalid_slot_cache,
                refresh_repair_pgmx_button_state=refresh_repair_pgmx_button_state,
                program_dimensions_cache=program_dimensions_cache,
            )

        def select_source_for_selected_piece():
            select_source_for_selected_piece_action(selected_piece_action_context())

        def repair_selected_invalid_pgmx():
            repair_selected_invalid_pgmx_action(selected_piece_action_context())

        def open_piece_editor(piece_row=None, row_index=None):
            return open_piece_editor_dialog(
                PieceEditorDialogContext(
                    owner=self,
                    inspect_dialog=inspect_dialog,
                    module_path=module_path,
                    all_rows=all_rows,
                    pieces_table=pieces_table,
                    pgmx_names=pgmx_names,
                    pgmx_relpaths=pgmx_relpaths,
                    normalize_source_path=normalize_source_path,
                    infer_companion_f6_source=infer_companion_f6_source,
                    build_piece_from_row=build_piece_from_row,
                    ensure_piece_drawing=ensure_piece_drawing,
                    apply_color_change=apply_color_change,
                    configured_board_colors=_configured_board_colors,
                    persist_module_config=persist_module_config,
                    drawing_path_for_piece_row=drawing_path_for_piece_row,
                    remove_piece_drawing_file=remove_piece_drawing_file,
                    refresh_piece_drawing_file=refresh_piece_drawing_file,
                    refresh_pieces_table=refresh_pieces_table,
                    select_visible_piece_by_id=select_visible_piece_by_id,
                ),
                piece_row=piece_row,
                row_index=row_index,
            )

        def add_manual_piece():
            open_piece_editor()

        def edit_selected_piece():
            edit_selected_piece_action(selected_piece_action_context(), open_piece_editor)

        def edit_piece_from_table_double_click(row: int, _column: int):
            if row < 0 or row >= pieces_table.rowCount():
                return
            pieces_table.selectRow(row)
            edit_selected_piece()

        def remove_selected_piece():
            remove_selected_piece_action(selected_piece_action_context())

        def _configured_board_colors(piece_thickness: float | None = None) -> list[str]:
            return configured_board_colors(_read_app_settings(), piece_thickness=piece_thickness)

        def _module_locale_key(module: ModuleData) -> str:
            return module_locale_key(module, self.project.root_directory)

        def _prompt_color_change(
            current_color: str,
            preferred_color: str | None = None,
            piece_thickness: float | None = None,
        ):
            available_colors = _configured_board_colors(piece_thickness=piece_thickness)
            if not available_colors:
                thickness_label = (
                    f" para espesor {int(piece_thickness) if float(piece_thickness).is_integer() else piece_thickness} mm"
                    if piece_thickness is not None
                    else ""
                )
                QMessageBox.warning(
                    inspect_dialog,
                    "Cambiar color",
                    f"No hay colores disponibles en los tableros configurados{thickness_label}.",
                )
                return None

            return open_color_change_dialog(
                inspect_dialog,
                current_color=current_color,
                available_colors=available_colors,
                locale_enabled=bool(_module_locale_key(selected_module)),
                preferred_color=preferred_color,
            )

        def apply_color_change(
            current_color: str,
            target_row_index: int | None = None,
            preferred_color: str | None = None,
            piece_thickness: float | None = None,
        ):
            selection = _prompt_color_change(
                current_color,
                preferred_color=preferred_color,
                piece_thickness=piece_thickness,
            )
            if selection is None:
                return None

            new_color_val, scope = selection
            new_color_has_no_grain = _board_color_has_no_grain(new_color_val, piece_thickness)

            selected_piece_id = ""
            fallback_row = pieces_table.currentRow()
            if target_row_index is not None and 0 <= target_row_index < len(all_rows):
                selected_piece_id = str(all_rows[target_row_index].get("id") or "").strip()

            result = apply_scoped_color_change(
                project_modules=self.project.modules,
                selected_module=selected_module,
                current_rows=all_rows,
                current_color=current_color,
                new_color=new_color_val,
                scope=scope,
                target_row_index=target_row_index,
                force_no_grain=new_color_has_no_grain,
                project_root=self.project.root_directory,
                module_config_path=self._module_config_path,
                persist_current_module=persist_module_config,
            )
            if not result.applied:
                return None

            refresh_pieces_table()
            if selected_piece_id:
                select_visible_piece_by_id(selected_piece_id, fallback_row=fallback_row)
            return new_color_val

        def view_drawing_for_selected_piece():
            view_drawing_for_selected_piece_action(selected_piece_action_context())

        def open_en_juego_configuration_dialog():
            open_en_juego_configuration_dialog_flow(
                parent_dialog=inspect_dialog,
                project=self.project,
                module_name=module_name,
                module_path=module_path,
                all_rows=all_rows,
                config_data=config_data,
                piece_from_row=piece_from_row,
                is_valid_thickness_value=self._is_valid_thickness_value,
                persist_module_config=persist_module_config,
                sync_en_juego_observations=sync_en_juego_observations,
                refresh_pieces_table=refresh_pieces_table,
            )

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.addWidget(pieces_table, 1)

        piece_actions = build_project_detail_piece_actions(
            add_piece=add_manual_piece,
            edit_piece=edit_selected_piece,
            delete_piece=remove_selected_piece,
            move_piece_up=lambda: move_selected_piece(-1),
            move_piece_down=lambda: move_selected_piece(1),
            repair_pgmx=repair_selected_invalid_pgmx,
            configure_en_juego=open_en_juego_configuration_dialog,
        )
        actions_column = piece_actions.layout
        repair_pgmx_btn = piece_actions.repair_pgmx_btn
        move_piece_up_btn = piece_actions.move_piece_up_btn
        move_piece_down_btn = piece_actions.move_piece_down_btn
        configure_en_juego_btn = piece_actions.configure_en_juego_btn
        refresh_configure_en_juego_button_state()

        content_row.addLayout(actions_column)
        layout.addLayout(content_row, 1)

        pieces_table.cellDoubleClicked.connect(edit_piece_from_table_double_click)
        pieces_table.itemSelectionChanged.connect(refresh_repair_pgmx_button_state)
        pieces_table.itemSelectionChanged.connect(refresh_piece_order_button_state)
        refresh_repair_pgmx_button_state()
        refresh_piece_order_button_state()

        def save_module_settings(show_feedback=True):
            persist_module_config()
            if show_feedback:
                QMessageBox.information(inspect_dialog, "Configuración", "Configuración del módulo guardada.")

        def can_close_inspection_dialog() -> bool:
            return confirm_save_before_close(
                inspect_dialog,
                lambda: has_unsaved_changes,
                save_module_settings,
            )

        install_reject_confirmation(inspect_dialog, can_close_inspection_dialog)

        actions_column.addStretch(1)

        save_btn = QPushButton("Guardar")
        save_btn.setToolTip("Guardar Configuración")
        save_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_btn.clicked.connect(save_module_settings)
        close_btn = QPushButton("Cerrar")
        close_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_btn.clicked.connect(lambda: close_dialog_if_confirmed(inspect_dialog, can_close_inspection_dialog))

        actions_column.addWidget(save_btn)
        actions_column.addWidget(close_btn)

        inspect_dialog.setLayout(layout)
        _exec_centered(inspect_dialog, parent_dialog)
