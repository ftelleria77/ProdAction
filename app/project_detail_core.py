"""Mixin con estado, helpers y persistencia del detalle de proyecto."""

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
from core.production_sheet import export_production_sheet, export_production_sheet_pdf
from core.summary import export_summary
from iso_state_synthesis.emitter import emit_candidate_for_pgmx

class ProjectDetailCoreMixin:
    def refresh_project_header_info(self):
        """Actualizar los campos de cabecera de la ventana de proyecto."""
        self.lbl_name.setText(f"Proyecto: {self.project.name}")
        self.lbl_client.setText(f"Cliente: {self.project.client or '-'}")
        locales = _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
        locales_count = len(locales) if locales else (self.project.locales_count or 0)
        self.lbl_locales_count.setText(f"Cantidad de locales: {locales_count}")
        self.lbl_root.setText(f"Carpeta de proyecto: {self.project.root_directory}")

        project_file = _project_data_path(self.project)
        if project_file.exists():
            modified = datetime.datetime.fromtimestamp(project_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        else:
            modified = "-"

        created = self.project.created_at or "-"
        self.lbl_created.setText(f"Creado: {created}")
        self.lbl_modified.setText(f"Modificado: {modified}")

        self.locales_list.clear()
        if locales:
            for locale in locales:
                locale_modules = [
                    module
                    for module in self.project.modules
                    if str(module.locale_name or "").strip().lower() == locale.name.strip().lower()
                ]
                modules_count = _total_module_quantity(locale_modules)
                if modules_count <= 0:
                    try:
                        modules_count = int(locale.modules_count or 0)
                    except (TypeError, ValueError):
                        modules_count = 0

                item = QListWidgetItem(f"{locale.name} ({modules_count} módulo(s))")
                item.setData(Qt.UserRole, locale.name)
                item.setFlags(
                    Qt.ItemIsEnabled
                    | Qt.ItemIsSelectable
                    | Qt.ItemIsUserCheckable
                )
                item.setCheckState(Qt.Checked)
                self.locales_list.addItem(item)
        else:
            placeholder_item = QListWidgetItem("sin procesar")
            placeholder_item.setFlags(Qt.NoItemFlags)
            placeholder_item.setTextAlignment(Qt.AlignCenter)
            placeholder_item.setForeground(QColor("#777777"))
            self.locales_list.addItem(placeholder_item)

        self.update_modules_button()
        self.update_output_action_buttons()

    def _selected_locale_names(self) -> list[str]:
        selected_locales: list[str] = []
        for index in range(self.locales_list.count()):
            item = self.locales_list.item(index)
            if item is None:
                continue
            locale_name = str(item.data(Qt.UserRole) or "").strip()
            if not locale_name:
                continue
            if item.checkState() == Qt.Checked:
                selected_locales.append(locale_name)
        return selected_locales

    def _listed_locale_names(self) -> list[str]:
        locale_names: list[str] = []
        for index in range(self.locales_list.count()):
            item = self.locales_list.item(index)
            if item is None:
                continue
            locale_name = str(item.data(Qt.UserRole) or "").strip()
            if locale_name:
                locale_names.append(locale_name)
        return locale_names

    def _project_for_selected_locales(self, action_title: str) -> Project | None:
        selected_locale_names = self._selected_locale_names()
        if not selected_locale_names:
            QMessageBox.warning(
                self,
                action_title,
                "Seleccione al menos un local en la lista para continuar.",
            )
            return None

        selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names}
        filtered_locales = [
            locale
            for locale in _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
            if locale.name.strip().lower() in selected_locale_keys
        ]
        filtered_modules = [
            module
            for module in self.project.modules
            if str(module.locale_name or "").strip().lower() in selected_locale_keys
        ]

        if not filtered_modules:
            QMessageBox.warning(
                self,
                action_title,
                "No hay módulos cargados para los locales seleccionados.",
            )
            return None

        return Project(
            name=self.project.name,
            root_directory=self.project.root_directory,
            project_data_file=self.project.project_data_file,
            client=self.project.client,
            created_at=self.project.created_at,
            locales=filtered_locales,
            modules=filtered_modules,
            output_directory=self.project.output_directory,
        )

    def _normalize_module_piece_thickness(self, module: ModuleData) -> None:
        """Normaliza el espesor de todas las piezas en un módulo.
        
        Convierte strings vacíos a None para que sean excluidas del conteo,
        y asegura que los valores numéricos sean floats válidos.
        """
        if not module.pieces:
            return
        
        for piece in module.pieces:
            thickness_val = piece.thickness
            if thickness_val == "" or thickness_val is None:
                piece.thickness = None
            else:
                try:
                    piece.thickness = float(thickness_val)
                except (ValueError, TypeError):
                    piece.thickness = None

    def _reload_module_pieces_from_config(self, module: ModuleData) -> None:
        """Recarga las piezas de un módulo desde su module_config.json.
        
        Esto sincroniza module.pieces con el archivo de configuración,
        asegurando que siempre refleje el estado actual.
        """
        config_path = self._module_config_path(module)
        if not config_path.exists():
            return
        
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            pieces_data = config_data.get("pieces", [])
            
            module.pieces = []
            for piece_dict in pieces_data:
                # Extraer solo los campos definidos en Piece dataclass
                if "source" in piece_dict and "cnc_source" not in piece_dict:
                    piece_dict = dict(piece_dict)
                    piece_dict["cnc_source"] = piece_dict.get("source")
                piece_fields = {
                    'id', 'width', 'height', 'thickness', 'quantity', 
                    'color', 'grain_direction', 'name', 'module_name',
                    'cnc_source', 'f6_source', 'piece_type', 'program_width', 'program_height', 'program_thickness'
                }
                filtered_dict = {k: v for k, v in piece_dict.items() if k in piece_fields}
                filtered_dict["grain_direction"] = normalize_piece_grain_direction(filtered_dict.get("grain_direction"))
                
                _coerce_optional_piece_float_fields(
                    filtered_dict,
                    ("thickness", "program_width", "program_height", "program_thickness"),
                )
                _coerce_piece_quantity_field(filtered_dict)
                
                try:
                    piece = Piece(**filtered_dict)
                    module.pieces.append(piece)
                except Exception:
                    pass
        except Exception:
            pass

    def _is_valid_piece_for_count(self, piece) -> bool:
        """Regla única para conteo/visualización: debe tener espesor definido y > 0."""
        # Solo contar piezas con espesor válido (no None, no "" y > 0)
        if piece.thickness is None or piece.thickness == "":
            return False
        try:
            thickness_val = float(piece.thickness)
            return thickness_val > 0
        except (TypeError, ValueError):
            return False

    def _is_valid_thickness_value(self, thickness_value) -> bool:
        """Valida espesor > 0 para valores numéricos o string."""
        if thickness_value is None:
            return False
        try:
            return float(thickness_value) > 0
        except (TypeError, ValueError):
            return False

    def _module_config_path(self, module: ModuleData) -> Path:
        return Path(module.path) / "module_config.json"

    def _read_module_config(self, module: ModuleData) -> dict:
        config_path = self._module_config_path(module)
        if not config_path.exists():
            return {}
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _build_pgmx_index(self, module_path: Path):
        available_pgmx_names = set()
        available_pgmx_relpaths = set()
        if module_path.exists():
            for pgmx_file in module_path.rglob("*.pgmx"):
                available_pgmx_names.add(pgmx_file.name.lower())
                available_pgmx_relpaths.add(str(pgmx_file.relative_to(module_path)).replace("\\", "/").lower())
        return available_pgmx_names, available_pgmx_relpaths

    def _get_pgmx_status(self, source_value: str, available_pgmx_names: set, available_pgmx_relpaths: set) -> str:
        source_value = str(source_value or "").strip()
        if not source_value:
            return "✗"

        source_name = Path(source_value).name.lower()
        source_rel = source_value.replace("\\", "/").lower()
        if source_name in available_pgmx_names or source_rel in available_pgmx_relpaths:
            return "✓"
        return "✗"

    def _write_module_config_files(self, modules: list[ModuleData] | None = None):
        """Crear archivo de configuración por módulo con piezas y validación PGMX."""
        from pgmx.processing import persist_piece_program_dimensions

        program_dimensions_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
        target_modules = modules if modules is not None else self.project.modules
        for module in target_modules:
            module_path = Path(module.path)
            pgmx_names, pgmx_relpaths = self._build_pgmx_index(module_path)
            previous_config = self._read_module_config(module)
            previous_settings = previous_config.get("settings", {})
            previous_pieces = previous_config.get("pieces", []) if isinstance(previous_config, dict) else []
            previous_rows_by_id = {
                str(piece_row.get("id") or "").strip(): piece_row
                for piece_row in previous_pieces
                if isinstance(piece_row, dict) and str(piece_row.get("id") or "").strip()
            }

            rows = []
            for piece in module.pieces:
                persist_piece_program_dimensions(self.project, piece, module_path, cache=program_dimensions_cache)
                previous_row = previous_rows_by_id.get(str(piece.id or "").strip(), {})
                source_value = piece.cnc_source or ""
                pgmx_status = self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths)
                piece_quantity = _parse_piece_quantity_value(piece.quantity, default=1)
                rows.append(
                    {
                        "id": piece.id,
                        "name": piece.name or piece.id,
                        "quantity": piece_quantity,
                        "height": piece.height,
                        "width": piece.width,
                        "thickness": piece.thickness,
                        "color": piece.color,
                        "grain_direction": normalize_piece_grain_direction(piece.grain_direction),
                        "source": source_value,
                        "f6_source": piece.f6_source or previous_row.get("f6_source"),
                        "pgmx": pgmx_status,
                        "piece_type": piece.piece_type,
                        "program_width": piece.program_width,
                        "program_height": piece.program_height,
                        "program_thickness": piece.program_thickness,
                        "en_juego": bool(previous_row.get("en_juego", False)),
                        "include_in_sheet": bool(previous_row.get("include_in_sheet", previous_row.get("excel", False))),
                        "observations": normalize_piece_observations(previous_row.get("observations")),
                    }
                )

            config_data = {
                "module": module.name,
                "path": str(module_path),
                "generated_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                "en_juego_layout": previous_config.get("en_juego_layout", {}),
                "en_juego_output_path": previous_config.get("en_juego_output_path", ""),
                "en_juego_settings": _normalize_en_juego_settings(previous_config.get("en_juego_settings")),
                "settings": {
                    "x": previous_settings.get("x", ""),
                    "y": previous_settings.get("y", ""),
                    "z": previous_settings.get("z", ""),
                    "herrajes_y_accesorios": previous_settings.get("herrajes_y_accesorios", ""),
                    "guias_y_bisagras": previous_settings.get("guias_y_bisagras", ""),
                    "detalles_de_obra": previous_settings.get("detalles_de_obra", ""),
                },
                "pieces": rows,
            }
            config_path = self._module_config_path(module)
            config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _locale_config_path(self, locale: LocaleData) -> Path:
        return Path(self.project.root_directory) / locale.path / "local_config.json"

    def _safe_float_value(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _compact_dimension_value(self, value):
        parsed = self._safe_float_value(value)
        if parsed is None:
            return None
        return int(parsed) if parsed.is_integer() else round(parsed, 2)

    def _derive_module_dimensions_from_rows(self, module_name: str, pieces: list[dict]):
        import re

        raw = module_name or ""
        cleaned = re.sub(r"^\s*mod\.?\s*\d+\s*-\s*", "", raw, flags=re.IGNORECASE)
        parts = [part.strip() for part in cleaned.split("-")]

        numeric_parts = []
        for part in parts:
            if re.fullmatch(r"\d+(?:[\.,]\d+)?", part):
                try:
                    numeric_parts.append(float(part.replace(",", ".")))
                except ValueError:
                    continue

        x_named = numeric_parts[-2] if len(numeric_parts) >= 2 else (numeric_parts[0] if len(numeric_parts) == 1 else None)
        z_named = numeric_parts[-1] if len(numeric_parts) >= 2 else None

        widths = []
        heights = []
        thicknesses = []
        lateral_heights = []
        span_heights = []

        for piece in pieces:
            piece_name = str(piece.get("name") or piece.get("id") or "").lower()
            width = self._safe_float_value(piece.get("width"))
            height = self._safe_float_value(piece.get("height"))
            thickness = self._safe_float_value(piece.get("thickness"))

            if width is not None and width > 0:
                widths.append(width)
            if height is not None and height > 0:
                heights.append(height)
            if thickness is not None and thickness > 0:
                thicknesses.append(thickness)

            if "lateral" in piece_name and height is not None and height > 0:
                lateral_heights.append(height)

            if any(key in piece_name for key in ["fondo", "estante", "tapa", "puerta", "frente", "faja"]):
                if height is not None and height > 0:
                    span_heights.append(height)

        max_thickness = max(thicknesses) if thicknesses else 0.0

        if z_named is not None:
            z_val = z_named
        elif widths:
            z_val = max(widths)
        else:
            z_val = None

        if x_named is not None:
            x_val = x_named
        else:
            x_base = max(span_heights) if span_heights else (max(heights) if heights else None)
            x_val = x_base

        if lateral_heights:
            y_base = max(lateral_heights)
        elif heights:
            y_base = max(heights)
        else:
            y_base = None

        y_val = y_base + max_thickness if y_base is not None else None

        return (
            self._compact_dimension_value(x_val),
            self._compact_dimension_value(y_val),
            self._compact_dimension_value(z_val),
        )

    def _configured_board_colors(self, piece_thickness: float | None = None) -> list[str]:
        colors: list[str] = []
        seen: set[str] = set()
        for board in _read_app_settings().get("available_boards", []):
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

    def _prompt_processing_color_replacement(
        self,
        original_color: str,
        available_colors: list[str],
        affected_piece_count: int,
        affected_units_count: int,
    ) -> str | None:
        color_dialog = QDialog(self)
        color_dialog.setWindowTitle("Procesar proyecto")
        color_layout = QVBoxLayout()
        color_layout.addWidget(
            QLabel(
                "Se encontraron piezas con un color no configurado en los tableros.\n"
                f"Color detectado: {original_color or '(sin color)'}\n"
                f"Piezas afectadas: {affected_piece_count} | Unidades: {affected_units_count}\n"
                "Seleccione el color de tablero que se aplicará a todas ellas."
            )
        )

        colors_list = QListWidget()
        for color in available_colors:
            colors_list.addItem(color)
        color_layout.addWidget(colors_list)

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
            colors_list.setCurrentRow(0)

        def accept_color_selection():
            if colors_list.currentItem() is None:
                QMessageBox.warning(color_dialog, "Procesar proyecto", "Seleccione un color.")
                return
            color_dialog.accept()

        accept_button.clicked.connect(accept_color_selection)
        cancel_button.clicked.connect(color_dialog.reject)
        colors_list.itemDoubleClicked.connect(lambda _item: accept_color_selection())
        color_dialog.setLayout(color_layout)

        if _exec_centered(color_dialog, self) != QDialog.Accepted or colors_list.currentItem() is None:
            return None
        return colors_list.currentItem().text().strip() or None

    def _resolve_processed_piece_colors(self, processed_modules: list[ModuleData]) -> bool:
        available_colors = self._configured_board_colors()
        available_color_map = {color.strip().lower(): color for color in available_colors if str(color).strip()}

        unresolved_groups: dict[str, dict] = {}
        for module in processed_modules:
            for piece in getattr(module, "pieces", []):
                if not self._is_valid_piece_for_count(piece):
                    continue

                raw_color = str(piece.color or "").strip()
                color_key = raw_color.lower()
                if color_key in available_color_map:
                    piece.color = available_color_map[color_key]
                    continue

                group = unresolved_groups.setdefault(
                    color_key,
                    {
                        "display": raw_color,
                        "pieces": [],
                        "piece_count": 0,
                        "units_count": 0,
                    },
                )
                group["pieces"].append(piece)
                group["piece_count"] += 1
                group["units_count"] += _parse_piece_quantity_value(
                    getattr(piece, "quantity", None),
                    default=1,
                )

        if not unresolved_groups:
            return True

        if not available_colors:
            missing_labels = ", ".join(
                sorted(group["display"] or "(sin color)" for group in unresolved_groups.values())
            )
            QMessageBox.warning(
                self,
                "Procesar",
                "Hay piezas con colores que no coinciden con ningún tablero configurado,\n"
                "pero no hay colores disponibles para reasignar.\n\n"
                f"Colores detectados: {missing_labels}",
            )
            return False

        for group in sorted(
            unresolved_groups.values(),
            key=lambda item: (str(item["display"] or "").strip().lower(), item["piece_count"]),
        ):
            selected_color = self._prompt_processing_color_replacement(
                str(group["display"] or "").strip(),
                available_colors,
                int(group["piece_count"] or 0),
                int(group["units_count"] or 0),
            )
            if not selected_color:
                return False
            for piece in group["pieces"]:
                piece.color = selected_color

        return True

    def _resolve_module_nominal_dimensions(self, module: ModuleData) -> dict:
        config_data = self._read_module_config(module)
        settings = config_data.get("settings", {}) if isinstance(config_data, dict) else {}
        pieces = config_data.get("pieces", []) if isinstance(config_data, dict) else []
        if not isinstance(pieces, list):
            pieces = []

        x_inferred, y_inferred, z_inferred = self._derive_module_dimensions_from_rows(module.name, pieces)
        x_value = self._compact_dimension_value(settings.get("x")) or x_inferred
        y_value = self._compact_dimension_value(settings.get("y")) or y_inferred
        z_value = self._compact_dimension_value(settings.get("z")) or z_inferred

        return {
            "x": x_value,
            "y": y_value,
            "z": z_value,
        }

    def _module_path_processing_key(self, module: ModuleData) -> str:
        try:
            return str(Path(module.path).resolve()).lower()
        except Exception:
            return str(module.path or "").strip().lower()

    def _preserve_locale_module_order(
        self,
        locale_name: str,
        modules: list[ModuleData],
    ) -> list[ModuleData]:
        locale_key = str(locale_name or "").strip().lower()
        modules_by_path: dict[str, ModuleData] = {}
        scanned_order: list[str] = []
        for module in modules:
            module_key = self._module_path_processing_key(module)
            if module_key not in modules_by_path:
                scanned_order.append(module_key)
            modules_by_path[module_key] = module

        ordered_modules: list[ModuleData] = []
        used_keys: set[str] = set()
        for module in self.project.modules:
            if str(module.locale_name or "").strip().lower() != locale_key:
                continue
            module_key = self._module_path_processing_key(module)
            ordered_module = modules_by_path.get(module_key)
            if ordered_module is None or module_key in used_keys:
                continue
            ordered_modules.append(ordered_module)
            used_keys.add(module_key)

        for module_key in scanned_order:
            if module_key not in used_keys:
                ordered_modules.append(modules_by_path[module_key])

        return ordered_modules

    def _resolve_modules_for_processing(
        self,
        scanned_modules: list[ModuleData],
    ) -> tuple[list[ModuleData], list[ModuleData]] | None:
        existing_modules_by_path = {
            self._module_path_processing_key(module): module
            for module in getattr(self.project, "modules", [])
        }

        resolved_modules: list[ModuleData] = []
        modules_to_reprocess: list[ModuleData] = []

        for scanned_module in scanned_modules:
            existing_module = existing_modules_by_path.get(self._module_path_processing_key(scanned_module))
            if existing_module is not None:
                scanned_module.quantity = _parse_piece_quantity_value(
                    getattr(existing_module, "quantity", None),
                    default=1,
                )

            config_path = self._module_config_path(scanned_module)
            if not config_path.exists():
                resolved_modules.append(scanned_module)
                modules_to_reprocess.append(scanned_module)
                continue

            module_label = (
                f"{scanned_module.locale_name} / {scanned_module.name}"
                if str(scanned_module.locale_name or "").strip()
                else scanned_module.name
            )
            answer = QMessageBox.question(
                self,
                "Procesar",
                (
                    f"El módulo '{module_label}' ya tiene una configuración previa.\n\n"
                    "¿Desea reprocesarlo?"
                ),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No,
            )
            if answer == QMessageBox.Cancel:
                return None
            if answer == QMessageBox.Yes:
                resolved_modules.append(scanned_module)
                modules_to_reprocess.append(scanned_module)
                continue

            if existing_module is None:
                existing_module = ModuleData(
                    name=scanned_module.name,
                    path=scanned_module.path,
                    locale_name=scanned_module.locale_name,
                    relative_path=scanned_module.relative_path,
                    quantity=_parse_piece_quantity_value(getattr(scanned_module, "quantity", None), default=1),
                    is_manual=scanned_module.is_manual,
                    pieces=[],
                )
            else:
                existing_module.name = scanned_module.name
                existing_module.path = scanned_module.path
                existing_module.locale_name = scanned_module.locale_name
                existing_module.relative_path = scanned_module.relative_path
                existing_module.is_manual = scanned_module.is_manual

            self._reload_module_pieces_from_config(existing_module)
            self._normalize_module_piece_thickness(existing_module)
            resolved_modules.append(existing_module)

        return resolved_modules, modules_to_reprocess

    def _write_locale_config_files(self, locales: list[LocaleData] | None = None):
        target_locales = locales if locales is not None else self.project.locales
        for locale in target_locales:
            locale_path = Path(self.project.root_directory) / locale.path
            locale_path.mkdir(parents=True, exist_ok=True)

            locale_modules = [
                module
                for module in self.project.modules
                if module.locale_name == locale.name
            ]
            locale.modules_count = _total_module_quantity(locale_modules)

            rows = []
            for module in locale_modules:
                module_path = Path(module.path)
                try:
                    relative_module_path = str(module_path.relative_to(locale_path)).replace("\\", "/")
                except ValueError:
                    relative_module_path = module.relative_path or module.name

                rows.append(
                    {
                        "name": module.name,
                        "path": relative_module_path,
                        "quantity": _parse_piece_quantity_value(getattr(module, "quantity", None), default=1),
                        "dimensions": self._resolve_module_nominal_dimensions(module),
                    }
                )

            config_data = {
                "locale_name": locale.name,
                "path": locale.path,
                "modules_count": locale.modules_count,
                "modules": rows,
            }
            self._locale_config_path(locale).write_text(
                json.dumps(config_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _valid_pieces_in_module(self, module):
        return [piece for piece in module.pieces if self._is_valid_piece_for_count(piece)]

    def _piece_quantity(self, piece) -> int:
        """Cantidad numérica de la pieza."""
        return _parse_piece_quantity_value(getattr(piece, "quantity", None), default=1)

    def _valid_piece_count_in_module(self, module) -> int:
        """Total de piezas (unidades) válidas en el módulo."""
        return sum(self._piece_quantity(piece) for piece in module.pieces if self._is_valid_piece_for_count(piece))

    def edit_project(self):
        """Abrir ventana de edición del proyecto."""
        edit_window = EditProjectWindow(self.project)
        _show_centered(edit_window, self)
        self.edit_window = edit_window
