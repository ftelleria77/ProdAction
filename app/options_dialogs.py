"""Dialogos de opciones generales de la app desktop."""

import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.options_helpers import parse_non_negative_measure
from app.project_detail_colors import configured_board_colors, preferred_color_index
from app.project_detail_piece_rows import parse_optional_piece_float
from app.qt_helpers import (
    _apply_responsive_window_size,
    _exec_centered,
    _scaled_int,
    _window_available_geometry,
)
from app.settings import (
    BOARD_GRAIN_OPTIONS,
    CUT_OPTIMIZATION_OPTIONS,
    DEFAULT_PATH_FIELDS,
    _compact_number,
    _load_tool_catalog_rows,
    _normalize_board_entry,
    _normalize_board_grain,
    _normalize_cut_optimization_option,
    _normalize_default_paths,
    _normalize_manual_piece_template_entry,
    _normalize_manual_piece_templates,
    _parse_piece_quantity_value,
    _persist_manual_piece_templates,
    _read_app_settings,
    _tool_usage_family_label,
    _tool_usage_label,
    _write_app_settings,
)
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import normalize_piece_grain_direction

class BoardEditDialog(QDialog):
    def __init__(self, board: dict | None = None, parent=None):
        super().__init__(parent)
        self.board_data: dict | None = None
        self.setWindowTitle("Editar tablero" if board else "Nuevo tablero")
        self.setModal(True)
        self.setMinimumWidth(420)

        board = dict(board or {})

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel("Complete los datos del tablero."))
        self.color_field = QLineEdit(str(board.get("color") or ""))
        self.length_field = QLineEdit(str(board.get("length") or "2750"))
        self.width_field = QLineEdit(str(board.get("width") or "1830"))
        self.thickness_field = QLineEdit(str(board.get("thickness") or "18"))
        self.margin_field = QLineEdit(str(board.get("margin") or "0"))
        self.grain_field = QComboBox()
        self.grain_field.addItems(BOARD_GRAIN_OPTIONS)
        current_grain = _normalize_board_grain(board.get("grain") or board.get("veta"))
        self.grain_field.setCurrentText(current_grain)

        label_width = 78
        field_width = 220
        self.color_field.setFixedWidth(field_width)
        self.length_field.setFixedWidth(field_width)
        self.width_field.setFixedWidth(field_width)
        self.thickness_field.setFixedWidth(field_width)
        self.margin_field.setFixedWidth(field_width)
        self.grain_field.setFixedWidth(field_width)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(6)

        def add_form_row(row_index: int, label_text: str, field: QWidget):
            label = QLabel(label_text)
            label.setFixedWidth(label_width)
            form_grid.addWidget(label, row_index, 0)
            form_grid.addWidget(field, row_index, 1, alignment=Qt.AlignLeft)

        add_form_row(0, "Color", self.color_field)
        add_form_row(1, "Longitud", self.length_field)
        add_form_row(2, "Ancho", self.width_field)
        add_form_row(3, "Espesor", self.thickness_field)
        add_form_row(4, "Margen", self.margin_field)
        add_form_row(5, "Veta", self.grain_field)
        layout.addLayout(form_grid)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, 0, 0)
        buttons_row.setSpacing(8)
        buttons_row.addStretch(1)
        save_button = QPushButton("Guardar")
        cancel_button = QPushButton("Cancelar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_board)
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(cancel_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def save_board(self):
        normalized = _normalize_board_entry(
            {
                "color": self.color_field.text().strip(),
                "length": self.length_field.text().strip(),
                "width": self.width_field.text().strip(),
                "thickness": self.thickness_field.text().strip(),
                "margin": self.margin_field.text().strip(),
                "grain": self.grain_field.currentText(),
            }
        )
        if normalized is None:
            QMessageBox.warning(self, "Tableros", "Complete Color, Longitud, Ancho, Espesor y Margen con valores válidos. El margen debe dejar área útil dentro del tablero.")
            return

        self.board_data = normalized
        self.accept()

class BoardsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tableros")
        self.setModal(True)
        self.resize(760, 420)
        self.settings = _read_app_settings()
        self.boards = list(self.settings.get("available_boards", []))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tableros disponibles para diagramas de corte."))

        self.boards_table = QTableWidget()
        self.boards_table.setColumnCount(6)
        self.boards_table.setHorizontalHeaderLabels([
            "Color",
            "Longitud",
            "Ancho",
            "Espesor",
            "Margen",
            "Veta",
        ])
        self.boards_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.boards_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.boards_table.setAlternatingRowColors(True)
        self.boards_table.horizontalHeader().setStretchLastSection(True)
        self.boards_table.setColumnWidth(0, 180)
        self.boards_table.setColumnWidth(1, 84)
        self.boards_table.setColumnWidth(2, 84)
        self.boards_table.setColumnWidth(3, 84)
        self.boards_table.setColumnWidth(4, 72)
        self.boards_table.itemDoubleClicked.connect(lambda _item: self.edit_board())

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(8)
        content_row.addWidget(self.boards_table, 1)

        buttons_column = QVBoxLayout()
        buttons_column.setContentsMargins(0, 0, 0, 0)
        buttons_column.setSpacing(8)
        new_button = QPushButton("Nuevo")
        edit_button = QPushButton("Editar")
        delete_button = QPushButton("Eliminar")
        close_button = QPushButton("Cerrar")
        for button in (new_button, edit_button, delete_button, close_button):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        new_button.clicked.connect(self.add_board)
        edit_button.clicked.connect(self.edit_board)
        delete_button.clicked.connect(self.delete_board)
        close_button.clicked.connect(self.accept)
        buttons_column.addWidget(new_button)
        buttons_column.addWidget(edit_button)
        buttons_column.addWidget(delete_button)
        buttons_column.addStretch(1)
        buttons_column.addWidget(close_button)
        content_row.addLayout(buttons_column)
        layout.addLayout(content_row, 1)

        self.setLayout(layout)
        self.refresh_boards_table()

    def _persist_boards(self):
        settings = _read_app_settings()
        settings["available_boards"] = self.boards
        _write_app_settings(settings)
        self.settings = settings

    def _selected_board_index(self) -> int:
        return self.boards_table.currentRow()

    def refresh_boards_table(self):
        self.boards_table.setRowCount(len(self.boards))
        for row_idx, board in enumerate(self.boards):
            self.boards_table.setItem(row_idx, 0, QTableWidgetItem(str(board.get("color") or "")))
            self.boards_table.setItem(row_idx, 1, QTableWidgetItem(str(board.get("length") or "")))
            self.boards_table.setItem(row_idx, 2, QTableWidgetItem(str(board.get("width") or "")))
            self.boards_table.setItem(row_idx, 3, QTableWidgetItem(str(board.get("thickness") or "")))
            self.boards_table.setItem(row_idx, 4, QTableWidgetItem(str(board.get("margin") or 0)))
            self.boards_table.setItem(row_idx, 5, QTableWidgetItem(str(board.get("grain") or "")))

    def add_board(self):
        dialog = BoardEditDialog(parent=self)
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.board_data is None:
            return

        self.boards.append(dialog.board_data)
        self._persist_boards()
        self.refresh_boards_table()
        self.boards_table.selectRow(len(self.boards) - 1)

    def edit_board(self):
        row_idx = self._selected_board_index()
        if row_idx < 0 or row_idx >= len(self.boards):
            QMessageBox.warning(self, "Tableros", "Seleccione un tablero para editar.")
            return

        dialog = BoardEditDialog(board=self.boards[row_idx], parent=self)
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.board_data is None:
            return

        self.boards[row_idx] = dialog.board_data
        self._persist_boards()
        self.refresh_boards_table()
        self.boards_table.selectRow(row_idx)

    def delete_board(self):
        row_idx = self._selected_board_index()
        if row_idx < 0 or row_idx >= len(self.boards):
            QMessageBox.warning(self, "Tableros", "Seleccione un tablero para eliminar.")
            return

        board = self.boards[row_idx]
        answer = QMessageBox.question(
            self,
            "Tableros",
            f"¿Eliminar el tablero '{board.get('color')}' de {board.get('thickness')} mm?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        del self.boards[row_idx]
        self._persist_boards()
        self.refresh_boards_table()

class ToolsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Herramientas")
        self.setModal(True)
        self.resize(1080, 480)
        self.tools = _load_tool_catalog_rows()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Herramientas disponibles en el catálogo y regla de uso por tipo."))

        self.tools_table = QTableWidget()
        self.tools_table.setColumnCount(10)
        self.tools_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Código",
                "Descripción",
                "Tipo",
                "Familia",
                "Uso permitido",
                "Porta",
                "Ø",
                "L. hund.",
                "Offset",
            ]
        )
        self.tools_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tools_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tools_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tools_table.setAlternatingRowColors(True)
        self.tools_table.verticalHeader().setVisible(False)
        header = self.tools_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        layout.addWidget(self.tools_table, 1)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        close_button = QPushButton("Cerrar")
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)
        self.refresh_tools_table()

    def refresh_tools_table(self):
        self.tools = _load_tool_catalog_rows()
        self.tools_table.setRowCount(len(self.tools))
        for row_idx, tool in enumerate(self.tools):
            row_values = [
                str(tool.get("tool_id") or ""),
                str(tool.get("name") or ""),
                str(tool.get("description") or ""),
                str(tool.get("type") or ""),
                _tool_usage_family_label(tool.get("type")),
                _tool_usage_label(tool.get("type")),
                str(tool.get("holder_key") or ""),
                str(tool.get("diameter") or ""),
                str(tool.get("sinking_length") or ""),
                str(tool.get("tool_offset_length") or ""),
            ]
            for column_idx, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if column_idx in {0, 7, 8, 9}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.tools_table.setItem(row_idx, column_idx, item)
        if self.tools:
            self.tools_table.selectRow(0)

class CutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cortes")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.settings = _read_app_settings()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración de cortes y separación."))

        label_width = 170
        field_width = 160

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(8)

        optimization_label = QLabel("Optimización de cortes")
        optimization_label.setFixedWidth(label_width)
        self.cut_optimization_field = QComboBox()
        self.cut_optimization_field.addItems(CUT_OPTIMIZATION_OPTIONS)
        self.cut_optimization_field.setCurrentText(
            _normalize_cut_optimization_option(self.settings.get("cut_optimization_mode"))
        )
        self.cut_optimization_field.setFixedWidth(field_width)
        form_grid.addWidget(optimization_label, 0, 0)
        form_grid.addWidget(self.cut_optimization_field, 0, 1, alignment=Qt.AlignLeft)

        squaring_label = QLabel("Adicional para escuadrado")
        squaring_label.setFixedWidth(label_width)
        self.cut_squaring_field = QLineEdit(
            str(_compact_number(self.settings.get("cut_squaring_allowance", 10)))
        )
        self.cut_squaring_field.setPlaceholderText("10")
        self.cut_squaring_field.setFixedWidth(field_width)
        form_grid.addWidget(squaring_label, 1, 0)
        form_grid.addWidget(self.cut_squaring_field, 1, 1, alignment=Qt.AlignLeft)

        saw_kerf_label = QLabel("Espesor de Sierra")
        saw_kerf_label.setFixedWidth(label_width)
        self.cut_saw_kerf_field = QLineEdit(
            str(_compact_number(self.settings.get("cut_saw_kerf", 4)))
        )
        self.cut_saw_kerf_field.setPlaceholderText("4")
        self.cut_saw_kerf_field.setFixedWidth(field_width)
        form_grid.addWidget(saw_kerf_label, 2, 0)
        form_grid.addWidget(self.cut_saw_kerf_field, 2, 1, alignment=Qt.AlignLeft)

        layout.addLayout(form_grid)

        buttons_row = QHBoxLayout()
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_settings)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def save_settings(self):
        squaring_raw = self.cut_squaring_field.text().strip() or "10"
        saw_kerf_raw = self.cut_saw_kerf_field.text().strip() or "4"

        def read_non_negative_measure(raw_value: str, field_name: str) -> float | None:
            parsed = parse_non_negative_measure(raw_value)
            if parsed.error == "invalid":
                QMessageBox.warning(self, "Cortes", f"{field_name} debe ser un número.")
                return None
            if parsed.error == "negative":
                QMessageBox.warning(self, "Cortes", f"{field_name} debe ser mayor o igual a cero.")
                return None
            return parsed.value

        squaring_allowance = read_non_negative_measure(squaring_raw, "El adicional para escuadrado")
        if squaring_allowance is None:
            return

        saw_kerf = read_non_negative_measure(saw_kerf_raw, "El espesor de sierra")
        if saw_kerf is None:
            return

        current_settings = _read_app_settings()
        current_settings["cut_squaring_allowance"] = _compact_number(squaring_allowance)
        current_settings["cut_saw_kerf"] = _compact_number(saw_kerf)
        current_settings["cut_optimization_mode"] = _normalize_cut_optimization_option(
            self.cut_optimization_field.currentText()
        )
        _write_app_settings(current_settings)
        self.settings = current_settings
        QMessageBox.information(self, "Cortes", "Configuración guardada.")

class PieceTemplateEditDialog(QDialog):
    def __init__(self, template_entry: dict | None = None, parent=None):
        super().__init__(parent)
        self.template_data: dict | None = None
        self.original_template = dict(template_entry or {})
        self.setWindowTitle("Editar plantilla" if template_entry else "Nueva plantilla")
        self.setModal(True)
        editor_scale, _, _ = _apply_responsive_window_size(
            self,
            720,
            400,
            width_ratio=0.84,
            height_ratio=0.80,
        )

        normalized_template = _normalize_manual_piece_template_entry(template_entry or {}) or {}

        self.id_field = QLineEdit(str(normalized_template.get("id") or ""))
        self.name_field = QLineEdit(str(normalized_template.get("name") or ""))
        self.quantity_field = QLineEdit(
            str(_parse_piece_quantity_value(normalized_template.get("quantity"), default=1))
        )
        self.height_field = QLineEdit(
            "" if normalized_template.get("height") is None else str(normalized_template.get("height"))
        )
        self.width_field = QLineEdit(
            "" if normalized_template.get("width") is None else str(normalized_template.get("width"))
        )
        self.thickness_field = QLineEdit(
            "" if normalized_template.get("thickness") is None else str(normalized_template.get("thickness"))
        )
        self.color_field = QLineEdit(str(normalized_template.get("color") or ""))
        self.grain_field = QComboBox()
        self.source_field = QLineEdit(str(normalized_template.get("source") or ""))

        self.grain_field.addItem("Sin veta", "0")
        self.grain_field.addItem("Alto", "1")
        self.grain_field.addItem("Ancho", "2")
        current_grain = normalize_piece_grain_direction(normalized_template.get("grain_direction"))
        if current_grain == "1":
            self.grain_field.setCurrentIndex(1)
        elif current_grain == "2":
            self.grain_field.setCurrentIndex(2)
        else:
            self.grain_field.setCurrentIndex(0)

        editor_inline_button_width = MAIN_ACTION_BUTTON_WIDTH
        editor_inline_button_height = MAIN_ACTION_BUTTON_HEIGHT
        top_fields_spacing = 8
        editor_field_block_spacing = 1
        editor_label_height = QLabel("X").sizeHint().height()
        editor_field_height = max(
            self.id_field.sizeHint().height(),
            self.grain_field.sizeHint().height(),
            self.source_field.sizeHint().height(),
        )
        editor_field_row_height = editor_label_height + editor_field_block_spacing + editor_field_height
        editor_inline_row_height = editor_label_height + editor_field_block_spacing + editor_inline_button_height
        id_field_width = _scaled_int(120, max(editor_scale, 0.82), 90)
        quantity_field_width = _scaled_int(80, max(editor_scale, 0.82), 60)
        dimension_field_width = _scaled_int(90, max(editor_scale, 0.82), 68)
        color_grain_field_width = _scaled_int(104, max(editor_scale, 0.82), 82)

        self.id_field.setFixedWidth(id_field_width)
        self.quantity_field.setFixedWidth(quantity_field_width)
        self.height_field.setFixedWidth(dimension_field_width)
        self.width_field.setFixedWidth(dimension_field_width)
        self.thickness_field.setFixedWidth(dimension_field_width)
        self.name_field.setFixedWidth((dimension_field_width * 3) + (top_fields_spacing * 2))
        self.color_field.setMinimumWidth(color_grain_field_width)
        self.grain_field.setMinimumWidth(color_grain_field_width)
        self.color_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.grain_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.source_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        def build_labeled_field_widget(
            label_text: str,
            field: QWidget,
            row_height: int = editor_field_row_height,
        ) -> QWidget:
            label = QLabel(label_text)
            label.setFixedHeight(editor_label_height)
            column_layout = QVBoxLayout()
            column_layout.setSpacing(editor_field_block_spacing)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.addStretch(1)
            column_layout.addWidget(label)
            column_layout.addWidget(field)
            column_widget = QWidget()
            column_widget.setFixedHeight(row_height)
            column_widget.setLayout(column_layout)
            return column_widget

        def select_color_from_boards():
            piece_thickness = parse_optional_piece_float(self.thickness_field.text())
            available_colors = configured_board_colors(
                _read_app_settings(),
                piece_thickness=piece_thickness,
            )
            if not available_colors:
                thickness_label = (
                    f" para espesor {int(piece_thickness) if float(piece_thickness).is_integer() else piece_thickness} mm"
                    if piece_thickness is not None
                    else ""
                )
                QMessageBox.warning(
                    self,
                    "Piezas",
                    f"No hay colores disponibles en los tableros configurados{thickness_label}.",
                )
                return

            current_color = self.color_field.text().strip()
            selected_index = preferred_color_index(available_colors, current_color)

            selected_color, ok = QInputDialog.getItem(
                self,
                "Seleccionar color",
                "Color:",
                available_colors,
                selected_index,
                False,
            )
            if ok:
                self.color_field.setText(str(selected_color or "").strip())

        def select_source():
            source_file, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar programa asociado",
                "",
                "Programas PGMX (*.pgmx);;Todos los archivos (*.*)",
            )
            if source_file:
                self.source_field.setText(source_file)

        top_fields_grid = QGridLayout()
        top_fields_grid.setHorizontalSpacing(top_fields_spacing)
        top_fields_grid.setVerticalSpacing(2)
        top_fields_grid.setContentsMargins(0, 0, 0, 0)

        id_column = build_labeled_field_widget("ID:", self.id_field)
        name_column = build_labeled_field_widget("Nombre:", self.name_field)
        height_column = build_labeled_field_widget("Alto:", self.height_field)
        width_column = build_labeled_field_widget("Ancho:", self.width_field)
        thickness_column = build_labeled_field_widget("Espesor:", self.thickness_field)
        qty_column = build_labeled_field_widget("Cantidad:", self.quantity_field)

        top_fields_grid.addWidget(id_column, 0, 0)
        top_fields_grid.addWidget(name_column, 0, 1, 1, 3)
        top_fields_grid.addWidget(qty_column, 1, 0)
        top_fields_grid.addWidget(height_column, 1, 1)
        top_fields_grid.addWidget(width_column, 1, 2)
        top_fields_grid.addWidget(thickness_column, 1, 3)
        top_fields_grid.setColumnStretch(4, 1)

        select_color_btn = QPushButton("Seleccionar")
        select_color_btn.setFixedSize(editor_inline_button_width, editor_inline_button_height)
        select_color_btn.setDefault(False)
        select_color_btn.setAutoDefault(False)
        select_color_btn.setFocusPolicy(Qt.NoFocus)
        select_color_btn.clicked.connect(select_color_from_boards)

        color_column = build_labeled_field_widget(
            "Color:",
            self.color_field,
            row_height=editor_inline_row_height,
        )
        grain_column = build_labeled_field_widget(
            "Veta:",
            self.grain_field,
            row_height=editor_inline_row_height,
        )
        color_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grain_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        color_grain_row = QHBoxLayout()
        color_grain_row.setSpacing(top_fields_spacing)
        color_grain_row.setContentsMargins(0, 0, 0, 0)
        color_grain_row.addWidget(color_column, 1, Qt.AlignTop)
        color_grain_row.addWidget(grain_column, 1, Qt.AlignTop)
        select_button_label = QLabel("")
        select_button_label.setFixedHeight(editor_label_height)
        select_button_column = QVBoxLayout()
        select_button_column.setSpacing(editor_field_block_spacing)
        select_button_column.setContentsMargins(0, 0, 0, 0)
        select_button_column.addWidget(select_button_label)
        select_button_column.addWidget(select_color_btn, 0, Qt.AlignRight)
        select_button_widget = QWidget()
        select_button_widget.setFixedWidth(editor_inline_button_width)
        select_button_widget.setFixedHeight(editor_inline_row_height)
        select_button_widget.setLayout(select_button_column)
        color_grain_row.addWidget(select_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
        color_grain_widget = QWidget()
        color_grain_widget.setFixedHeight(editor_inline_row_height)
        color_grain_widget.setLayout(color_grain_row)
        top_fields_grid.addWidget(color_grain_widget, 2, 0, 1, 4)

        source_field_widget = build_labeled_field_widget(
            "Programa asociado (opcional):",
            self.source_field,
            row_height=editor_inline_row_height,
        )
        source_field_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        select_source_btn = QPushButton("Seleccionar")
        select_source_btn.setFixedSize(editor_inline_button_width, editor_inline_button_height)
        select_source_btn.clicked.connect(select_source)
        source_row = QHBoxLayout()
        source_row.setSpacing(top_fields_spacing)
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.addWidget(source_field_widget, 1, Qt.AlignTop)
        source_button_label = QLabel("")
        source_button_label.setFixedHeight(editor_label_height)
        source_button_column = QVBoxLayout()
        source_button_column.setSpacing(editor_field_block_spacing)
        source_button_column.setContentsMargins(0, 0, 0, 0)
        source_button_column.addWidget(source_button_label)
        source_button_column.addWidget(select_source_btn, 0, Qt.AlignRight)
        source_button_widget = QWidget()
        source_button_widget.setFixedWidth(editor_inline_button_width)
        source_button_widget.setFixedHeight(editor_inline_row_height)
        source_button_widget.setLayout(source_button_column)
        source_row.addWidget(source_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
        source_widget = QWidget()
        source_widget.setFixedHeight(editor_inline_row_height)
        source_widget.setLayout(source_row)
        top_fields_grid.addWidget(source_widget, 3, 0, 1, 4)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addLayout(top_fields_grid)

        form_panel = QWidget()
        form_panel_horizontal_margin = 4
        form_panel_layout = QVBoxLayout()
        form_panel_layout.setContentsMargins(
            form_panel_horizontal_margin,
            0,
            form_panel_horizontal_margin,
            0,
        )
        form_panel_layout.setSpacing(0)
        form_panel_layout.addLayout(form_layout)
        form_panel.setLayout(form_panel_layout)
        form_panel_width_hint = form_panel.sizeHint().width()
        form_panel.setFixedWidth(form_panel_width_hint)
        form_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, form_panel_horizontal_margin, 0)
        buttons_row.setSpacing(8)
        buttons_row.addStretch(1)
        save_button = QPushButton("Aceptar")
        cancel_button = QPushButton("Cancelar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.setDefault(True)
        save_button.setAutoDefault(True)
        cancel_button.setDefault(False)
        cancel_button.setAutoDefault(False)
        select_source_btn.setDefault(False)
        select_source_btn.setAutoDefault(False)
        select_source_btn.setFocusPolicy(Qt.NoFocus)
        save_button.clicked.connect(self.save_template)
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(cancel_button)

        buttons_widget = QWidget()
        buttons_widget.setFixedWidth(form_panel_width_hint)
        buttons_widget.setContentsMargins(0, 0, 0, 0)
        buttons_widget.setLayout(buttons_row)
        buttons_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel("Complete los datos de la plantilla de pieza."))
        layout.addWidget(form_panel, 0, Qt.AlignTop | Qt.AlignLeft)
        layout.addSpacing(_scaled_int(14, max(editor_scale, 0.82), 10))
        layout.addWidget(buttons_widget, 0, Qt.AlignTop | Qt.AlignLeft)
        layout.addStretch(1)
        self.setLayout(layout)
        self.layout().activate()
        compact_dialog_width = self.sizeHint().width()
        compact_dialog_height = self.sizeHint().height()
        available_geometry = _window_available_geometry(self)
        if available_geometry is not None:
            compact_dialog_width = min(
                compact_dialog_width,
                max(420, int(available_geometry.width() * 0.94)),
            )
            compact_dialog_height = min(
                compact_dialog_height,
                max(300, int(available_geometry.height() * 0.90)),
            )
        self.setMinimumSize(compact_dialog_width, compact_dialog_height)
        self.resize(compact_dialog_width, compact_dialog_height)

    def save_template(self):
        template_id = self.id_field.text().strip()
        if not template_id:
            QMessageBox.warning(self, "Piezas", "El campo ID es obligatorio.")
            return

        raw_template = {
            "id": template_id,
            "name": self.name_field.text().strip() or template_id,
            "quantity": self.quantity_field.text().strip() or "1",
            "height": self.height_field.text().strip(),
            "width": self.width_field.text().strip(),
            "thickness": self.thickness_field.text().strip(),
            "color": self.color_field.text().strip(),
            "grain_direction": self.grain_field.currentData(),
            "source": self.source_field.text().strip(),
            "f6_source": self.original_template.get("f6_source"),
            "piece_type": self.original_template.get("piece_type"),
            "saved_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
        }
        normalized_template = _normalize_manual_piece_template_entry(raw_template)
        if normalized_template is None:
            QMessageBox.warning(self, "Piezas", "No se pudo guardar la plantilla con los datos ingresados.")
            return

        self.template_data = normalized_template
        self.accept()

class PieceTemplatesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Piezas")
        self.setModal(True)
        self.resize(900, 460)
        self.templates = _normalize_manual_piece_templates(_read_app_settings().get("manual_piece_templates"))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Plantillas de piezas agregadas manualmente."))

        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(6)
        self.templates_table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Cantidad", "Color", "Espesor", "Programa"]
        )
        self.templates_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.templates_table.setSelectionMode(QTableWidget.SingleSelection)
        self.templates_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.templates_table.setAlternatingRowColors(True)
        self.templates_table.verticalHeader().setVisible(False)
        header = self.templates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.templates_table.itemDoubleClicked.connect(lambda _item: self.edit_template())

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(8)
        content_row.addWidget(self.templates_table, 1)

        buttons_column = QVBoxLayout()
        buttons_column.setContentsMargins(0, 0, 0, 0)
        buttons_column.setSpacing(8)
        new_button = QPushButton("Nuevo")
        edit_button = QPushButton("Editar")
        delete_button = QPushButton("Eliminar")
        close_button = QPushButton("Cerrar")
        for button in (new_button, edit_button, delete_button, close_button):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        new_button.clicked.connect(self.add_template)
        edit_button.clicked.connect(self.edit_template)
        delete_button.clicked.connect(self.delete_template)
        close_button.clicked.connect(self.accept)
        buttons_column.addWidget(new_button)
        buttons_column.addWidget(edit_button)
        buttons_column.addWidget(delete_button)
        buttons_column.addStretch(1)
        buttons_column.addWidget(close_button)
        content_row.addLayout(buttons_column)
        layout.addLayout(content_row, 1)

        self.setLayout(layout)
        self.refresh_templates_table()

    def _persist_templates(self):
        self.templates = _persist_manual_piece_templates(self.templates)

    def _selected_template_index(self) -> int:
        return self.templates_table.currentRow()

    def refresh_templates_table(self):
        self.templates = _normalize_manual_piece_templates(self.templates)
        self.templates_table.setRowCount(len(self.templates))
        for row_idx, template_entry in enumerate(self.templates):
            row_values = [
                str(template_entry.get("id") or ""),
                str(template_entry.get("name") or ""),
                str(_parse_piece_quantity_value(template_entry.get("quantity"), default=1)),
                str(template_entry.get("color") or ""),
                "" if template_entry.get("thickness") is None else str(template_entry.get("thickness")),
                Path(str(template_entry.get("source") or "")).name,
            ]
            for column_idx, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if column_idx in {2, 4}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.templates_table.setItem(row_idx, column_idx, item)
        if self.templates:
            self.templates_table.selectRow(0)

    def add_template(self):
        dialog = PieceTemplateEditDialog(parent=self)
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.template_data is None:
            return
        self.templates.append(dialog.template_data)
        self._persist_templates()
        self.refresh_templates_table()
        self.templates_table.selectRow(len(self.templates) - 1)

    def edit_template(self):
        row_idx = self._selected_template_index()
        if row_idx < 0 or row_idx >= len(self.templates):
            QMessageBox.warning(self, "Piezas", "Seleccione una plantilla para editar.")
            return
        dialog = PieceTemplateEditDialog(template_entry=self.templates[row_idx], parent=self)
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.template_data is None:
            return
        self.templates[row_idx] = dialog.template_data
        self._persist_templates()
        self.refresh_templates_table()
        self.templates_table.selectRow(row_idx)

    def delete_template(self):
        row_idx = self._selected_template_index()
        if row_idx < 0 or row_idx >= len(self.templates):
            QMessageBox.warning(self, "Piezas", "Seleccione una plantilla para eliminar.")
            return
        template_entry = self.templates[row_idx]
        template_label = str(template_entry.get("name") or template_entry.get("id") or "pieza").strip()
        answer = QMessageBox.question(
            self,
            "Piezas",
            f'¿Eliminar la plantilla "{template_label}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        del self.templates[row_idx]
        self._persist_templates()
        self.refresh_templates_table()

class PathsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rutas")
        self.setModal(True)
        self.setMinimumWidth(720)
        self.settings = _read_app_settings()
        self.path_fields: dict[str, QLineEdit] = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Rutas predeterminadas para abrir selectores de carpetas y archivos."))

        paths_grid = QGridLayout()
        paths_grid.setColumnStretch(1, 1)
        default_paths = _normalize_default_paths(self.settings.get("default_paths"))
        for row_index, (path_key, label_text) in enumerate(DEFAULT_PATH_FIELDS):
            label = QLabel(label_text)
            field = QLineEdit(default_paths.get(path_key, ""))
            field.setMinimumWidth(440)
            browse_button = QPushButton("...")
            browse_button.setFixedSize(40, MAIN_ACTION_BUTTON_HEIGHT)
            browse_button.clicked.connect(
                lambda _checked=False, key=path_key: self.select_folder(key)
            )
            self.path_fields[path_key] = field
            paths_grid.addWidget(label, row_index, 0)
            paths_grid.addWidget(field, row_index, 1)
            paths_grid.addWidget(browse_button, row_index, 2)
        layout.addLayout(paths_grid)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_paths)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def _field_label(self, path_key: str) -> str:
        return dict(DEFAULT_PATH_FIELDS).get(path_key, "Ruta")

    def _selector_start_dir(self, path_key: str) -> str:
        raw_path = self.path_fields[path_key].text().strip()
        current_path = Path(raw_path) if raw_path else None
        if current_path is not None and current_path.is_dir():
            return str(current_path)
        return str(Path.home())

    def select_folder(self, path_key: str):
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            f"Seleccionar carpeta - {self._field_label(path_key)}",
            self._selector_start_dir(path_key),
        )
        if selected_folder:
            self.path_fields[path_key].setText(selected_folder)

    def save_paths(self):
        normalized_paths = {}
        for path_key, field in self.path_fields.items():
            path_value = field.text().strip()
            if path_value and not Path(path_value).is_dir():
                QMessageBox.warning(
                    self,
                    "Rutas",
                    f"La ruta de {self._field_label(path_key)} no existe o no es una carpeta.",
                )
                return
            normalized_paths[path_key] = path_value

        current_settings = _read_app_settings()
        current_settings["default_paths"] = normalized_paths
        _write_app_settings(current_settings)
        self.settings = _read_app_settings()
        QMessageBox.information(self, "Rutas", "Rutas guardadas.")

class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.settings = _read_app_settings()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración general de la aplicación."))

        minimum_dimension_row = QHBoxLayout()
        minimum_dimension_label = QLabel("Mínima dimensión mecanizable")
        self.minimum_dimension_field = QLineEdit(
            str(self.settings.get("minimum_machinable_dimension", 150))
        )
        self.minimum_dimension_field.setPlaceholderText("150")
        minimum_dimension_row.addWidget(minimum_dimension_label)
        minimum_dimension_row.addWidget(self.minimum_dimension_field)
        layout.addLayout(minimum_dimension_row)

        paths_row = QHBoxLayout()
        paths_row.addWidget(QLabel("Rutas predeterminadas"))
        paths_button = QPushButton("Rutas")
        paths_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        paths_button.clicked.connect(self.open_paths_dialog)
        paths_row.addWidget(paths_button)
        layout.addLayout(paths_row)

        cuts_row = QHBoxLayout()
        cuts_row.addWidget(QLabel("Configuración de cortes"))
        cuts_button = QPushButton("Cortes")
        cuts_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cuts_button.clicked.connect(self.open_cuts_dialog)
        cuts_row.addWidget(cuts_button)
        layout.addLayout(cuts_row)

        boards_row = QHBoxLayout()
        boards_row.addWidget(QLabel("Tableros disponibles"))
        boards_button = QPushButton("Tableros")
        boards_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        boards_button.clicked.connect(self.open_boards_dialog)
        boards_row.addWidget(boards_button)
        layout.addLayout(boards_row)

        tools_row = QHBoxLayout()
        tools_row.addWidget(QLabel("Herramientas de corte"))
        tools_button = QPushButton("Herramientas")
        tools_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        tools_button.clicked.connect(self.open_tools_dialog)
        tools_row.addWidget(tools_button)
        layout.addLayout(tools_row)

        pieces_row = QHBoxLayout()
        pieces_row.addWidget(QLabel("Plantillas de piezas"))
        pieces_button = QPushButton("Piezas")
        pieces_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        pieces_button.clicked.connect(self.open_pieces_dialog)
        pieces_row.addWidget(pieces_button)
        layout.addLayout(pieces_row)

        buttons_row = QHBoxLayout()
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_settings)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def open_boards_dialog(self):
        dialog = BoardsDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def open_paths_dialog(self):
        dialog = PathsDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def open_cuts_dialog(self):
        dialog = CutsDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def open_tools_dialog(self):
        dialog = ToolsDialog(self)
        _exec_centered(dialog, self)

    def open_pieces_dialog(self):
        dialog = PieceTemplatesDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def save_settings(self):
        minimum_dimension_raw = self.minimum_dimension_field.text().strip() or "150"

        try:
            minimum_dimension = int(minimum_dimension_raw)
        except ValueError:
            QMessageBox.warning(self, "Opciones", "La mínima dimensión mecanizable debe ser un número entero.")
            return

        if minimum_dimension <= 0:
            QMessageBox.warning(self, "Opciones", "La mínima dimensión mecanizable debe ser mayor que cero.")
            return

        current_settings = _read_app_settings()
        current_settings["minimum_machinable_dimension"] = minimum_dimension
        _write_app_settings(current_settings)
        self.settings = current_settings
        QMessageBox.information(self, "Opciones", "Configuración guardada.")
