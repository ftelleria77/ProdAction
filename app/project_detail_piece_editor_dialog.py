"""Qt dialog for adding and editing project detail pieces."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtSvgWidgets import QSvgWidget

from app.project_detail_colors import open_board_color_picker
from app.project_detail_piece_editor import (
    PieceEditorValues,
    build_piece_editor_row as build_piece_editor_row_data,
    manual_piece_template_label,
    optional_field_text,
)
from app.project_detail_piece_rows import parse_optional_piece_float
from app.project_detail_programs import (
    clear_program_metadata,
    open_piece_program_in_default_app,
    select_pgmx_program_file,
)
from app.qt_helpers import (
    _apply_responsive_window_size,
    _exec_centered,
    _scaled_int,
    _window_available_geometry,
)
from app.settings import (
    _board_color_has_no_grain,
    _normalize_manual_piece_template_entry,
    _normalize_manual_piece_templates,
    _parse_piece_quantity_value,
    _read_app_settings,
    _save_manual_piece_template,
)
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import PIECE_GRAIN_CODE_NONE, normalize_piece_grain_direction


@dataclass
class PieceEditorDialogContext:
    owner: object
    inspect_dialog: QDialog
    module_path: Path
    all_rows: list[dict]
    pieces_table: object
    pgmx_names: object
    pgmx_relpaths: object
    normalize_source_path: Callable[[str], str]
    infer_companion_f6_source: Callable[[str], str | None]
    build_piece_from_row: Callable[[dict], object]
    ensure_piece_drawing: Callable[..., object]
    apply_color_change: Callable[..., str | None]
    configured_board_colors: Callable[[float | None], list[str]]
    persist_module_config: Callable[[], None]
    drawing_path_for_piece_row: Callable[[dict], Path]
    remove_piece_drawing_file: Callable[..., None]
    refresh_piece_drawing_file: Callable[..., object]
    refresh_pieces_table: Callable[[], None]
    select_visible_piece_by_id: Callable[..., None]


def open_piece_editor_dialog(context: PieceEditorDialogContext, piece_row=None, row_index=None):
    self = context.owner
    inspect_dialog = context.inspect_dialog
    module_path = context.module_path
    all_rows = context.all_rows
    pieces_table = context.pieces_table
    pgmx_names = context.pgmx_names
    pgmx_relpaths = context.pgmx_relpaths
    normalize_source_path = context.normalize_source_path
    infer_companion_f6_source = context.infer_companion_f6_source
    build_piece_from_row = context.build_piece_from_row
    ensure_piece_drawing = context.ensure_piece_drawing
    apply_color_change = context.apply_color_change
    _configured_board_colors = context.configured_board_colors
    persist_module_config = context.persist_module_config
    drawing_path_for_piece_row = context.drawing_path_for_piece_row
    remove_piece_drawing_file = context.remove_piece_drawing_file
    refresh_piece_drawing_file = context.refresh_piece_drawing_file
    refresh_pieces_table = context.refresh_pieces_table
    select_visible_piece_by_id = context.select_visible_piece_by_id
    is_new_piece = piece_row is None
    base_piece_row = dict(piece_row or {})
    editor_dialog = QDialog(inspect_dialog)
    editor_dialog.setWindowTitle("Agregar pieza manual" if is_new_piece else "Editar pieza")
    editor_scale, _, _ = _apply_responsive_window_size(
        editor_dialog,
        1100,
        620,
        width_ratio=0.94,
        height_ratio=0.92,
    )
    editor_inline_button_width = MAIN_ACTION_BUTTON_WIDTH

    editor_layout = QVBoxLayout()
    content_layout = QHBoxLayout()
    content_layout.setSpacing(8)
    content_layout.setContentsMargins(0, 0, 0, 0)

    form_layout = QVBoxLayout()
    form_layout.setSpacing(6)
    form_layout.setContentsMargins(0, 0, 0, 0)

    id_field = QLineEdit(str(base_piece_row.get("id") or ""))
    name_field = QLineEdit(str(base_piece_row.get("name") or ""))
    base_piece_quantity = _parse_piece_quantity_value(base_piece_row.get("quantity"), default=1)
    qty_field = QLineEdit(str(base_piece_quantity))
    height_field = QLineEdit(str(base_piece_row.get("height") or ""))
    width_field = QLineEdit(str(base_piece_row.get("width") or ""))
    thickness_field = QLineEdit(str(base_piece_row.get("thickness") or ""))
    color_field = QLineEdit(str(base_piece_row.get("color") or ""))
    grain_field = QComboBox()
    source_field = QLineEdit(str(base_piece_row.get("source") or ""))
    id_field.setFixedWidth(_scaled_int(120, max(editor_scale, 0.82), 90))
    qty_field.setFixedWidth(_scaled_int(80, max(editor_scale, 0.82), 60))
    dimension_field_width = _scaled_int(90, max(editor_scale, 0.82), 68)
    color_grain_field_width = _scaled_int(104, max(editor_scale, 0.82), 82)
    top_fields_spacing = 8
    editor_inline_button_height = MAIN_ACTION_BUTTON_HEIGHT
    editor_field_block_spacing = 2
    editor_label_height = QLabel("X").sizeHint().height()
    editor_grid_row_height = editor_label_height + editor_field_block_spacing + editor_inline_button_height
    name_field.setFixedWidth((dimension_field_width * 3) + (top_fields_spacing * 2))
    height_field.setFixedWidth(dimension_field_width)
    width_field.setFixedWidth(dimension_field_width)
    thickness_field.setFixedWidth(dimension_field_width)
    color_field.setMinimumWidth(color_grain_field_width)
    grain_field.setMinimumWidth(color_grain_field_width)
    color_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    grain_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    source_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    grain_field.addItem("Sin veta", "0")
    grain_field.addItem("Alto", "1")
    grain_field.addItem("Ancho", "2")
    current_grain_code = normalize_piece_grain_direction(base_piece_row.get("grain_direction"))
    if current_grain_code == "1":
        grain_field.setCurrentIndex(1)
    elif current_grain_code == "2":
        grain_field.setCurrentIndex(2)
    else:
        grain_field.setCurrentIndex(0)
    manual_piece_templates = _normalize_manual_piece_templates(
        _read_app_settings().get("manual_piece_templates")
    )
    template_combo = None
    if is_new_piece:
        template_combo = QComboBox()
        template_combo.addItem("(sin plantilla)", None)
        for template_entry in manual_piece_templates:
            template_combo.addItem(manual_piece_template_label(template_entry), template_entry)

    def build_labeled_field_widget(label_text: str, field: QWidget) -> QWidget:
        label = QLabel(label_text)
        label.setFixedHeight(editor_label_height)
        column_layout = QVBoxLayout()
        column_layout.setSpacing(editor_field_block_spacing)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.addStretch(1)
        column_layout.addWidget(label)
        column_layout.addWidget(field)
        column_widget = QWidget()
        column_widget.setFixedHeight(editor_grid_row_height)
        column_widget.setLayout(column_layout)
        return column_widget

    top_fields_grid = QGridLayout()
    top_fields_grid.setHorizontalSpacing(top_fields_spacing)
    top_fields_grid.setVerticalSpacing(4)
    top_fields_grid.setContentsMargins(0, 0, 0, 0)

    if template_combo is not None:
        template_column = build_labeled_field_widget("Plantilla:", template_combo)
        top_fields_grid.addWidget(template_column, 0, 0, 1, 4)

    id_column = build_labeled_field_widget("ID:", id_field)
    name_column = build_labeled_field_widget("Nombre:", name_field)
    height_column = build_labeled_field_widget("Alto:", height_field)
    width_column = build_labeled_field_widget("Ancho:", width_field)
    thickness_column = build_labeled_field_widget("Espesor:", thickness_field)
    qty_column = build_labeled_field_widget("Cantidad:", qty_field)

    top_row_offset = 1 if template_combo is not None else 0
    top_fields_grid.addWidget(id_column, 0 + top_row_offset, 0)
    top_fields_grid.addWidget(name_column, 0 + top_row_offset, 1, 1, 3)
    top_fields_grid.addWidget(qty_column, 1 + top_row_offset, 0)
    top_fields_grid.addWidget(height_column, 1 + top_row_offset, 1)
    top_fields_grid.addWidget(width_column, 1 + top_row_offset, 2)
    top_fields_grid.addWidget(thickness_column, 1 + top_row_offset, 3)
    top_fields_grid.setColumnStretch(4, 1)
    for top_fields_row in range(5 if template_combo is not None else 4):
        top_fields_grid.setRowMinimumHeight(top_fields_row, editor_grid_row_height)

    form_layout.insertLayout(0, top_fields_grid)

    apply_color_btn = None
    if not is_new_piece:
        apply_color_btn = QPushButton("Cambiar")
        apply_color_btn.setFixedSize(editor_inline_button_width, editor_inline_button_height)
    select_color_btn = None
    if is_new_piece:
        select_color_btn = QPushButton("Seleccionar")
        select_color_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

    color_column = build_labeled_field_widget("Color:", color_field)
    grain_column = build_labeled_field_widget("Veta:", grain_field)
    color_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    grain_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    color_grain_row = QHBoxLayout()
    color_grain_row.setSpacing(top_fields_spacing)
    color_grain_row.setContentsMargins(0, 0, 0, 0)
    color_grain_row.addWidget(color_column, 1, Qt.AlignTop)
    color_grain_row.addWidget(grain_column, 1, Qt.AlignTop)
    if select_color_btn is not None:
        select_button_label = QLabel("")
        select_button_label.setFixedHeight(editor_label_height)
        select_button_column = QVBoxLayout()
        select_button_column.setSpacing(editor_field_block_spacing)
        select_button_column.setContentsMargins(0, 0, 0, 0)
        select_button_column.addWidget(select_button_label)
        select_button_column.addWidget(select_color_btn, 0, Qt.AlignRight)
        select_button_widget = QWidget()
        select_button_widget.setFixedWidth(editor_inline_button_width)
        select_button_widget.setFixedHeight(editor_grid_row_height)
        select_button_widget.setLayout(select_button_column)
        color_grain_row.addWidget(select_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
    if apply_color_btn is not None:
        change_button_label = QLabel("")
        change_button_label.setFixedHeight(editor_label_height)
        change_button_column = QVBoxLayout()
        change_button_column.setSpacing(editor_field_block_spacing)
        change_button_column.setContentsMargins(0, 0, 0, 0)
        change_button_column.addWidget(change_button_label)
        change_button_column.addWidget(apply_color_btn, 0, Qt.AlignRight)
        change_button_widget = QWidget()
        change_button_widget.setFixedWidth(editor_inline_button_width)
        change_button_widget.setFixedHeight(editor_grid_row_height)
        change_button_widget.setLayout(change_button_column)
        color_grain_row.addWidget(change_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
    color_grain_widget = QWidget()
    color_grain_widget.setFixedHeight(editor_grid_row_height)
    color_grain_widget.setLayout(color_grain_row)
    top_fields_grid.addWidget(color_grain_widget, 2 + top_row_offset, 0, 1, 4)

    source_field_widget = build_labeled_field_widget("Programa asociado (opcional):", source_field)
    source_field_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    select_source_btn = QPushButton("Seleccionar")
    select_source_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    edit_source_editor_btn = QPushButton("Editar\nPrograma")
    edit_source_editor_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    remove_source_editor_btn = QPushButton("Quitar\nPrograma")
    remove_source_editor_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    source_row = QHBoxLayout()
    source_row.setSpacing(top_fields_spacing)
    source_row.setContentsMargins(0, 0, 0, 0)
    source_row.addWidget(source_field_widget, 1, Qt.AlignTop)
    source_button_label = QLabel("")
    source_button_label.setFixedHeight(editor_label_height)
    source_buttons_column = QVBoxLayout()
    source_buttons_column.setSpacing(top_fields_spacing)
    source_buttons_column.setContentsMargins(0, 0, 0, 0)
    source_buttons_column.addWidget(select_source_btn)
    source_buttons_column.addWidget(edit_source_editor_btn)
    source_buttons_column.addWidget(remove_source_editor_btn)
    source_buttons_widget = QWidget()
    source_buttons_widget.setFixedWidth(editor_inline_button_width)
    source_buttons_widget.setLayout(source_buttons_column)
    source_button_column = QVBoxLayout()
    source_button_column.setSpacing(editor_field_block_spacing)
    source_button_column.setContentsMargins(0, 0, 0, 0)
    source_button_column.addWidget(source_button_label)
    source_button_column.addWidget(source_buttons_widget, 0, Qt.AlignRight)
    source_buttons_stack_height = (
        editor_label_height
        + editor_field_block_spacing
        + (MAIN_ACTION_BUTTON_HEIGHT * 3)
        + (top_fields_spacing * 2)
    )
    source_button_widget = QWidget()
    source_button_widget.setFixedWidth(editor_inline_button_width)
    source_button_widget.setFixedHeight(source_buttons_stack_height)
    source_button_widget.setLayout(source_button_column)
    source_row.addWidget(source_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
    source_widget = QWidget()
    source_widget.setFixedHeight(source_buttons_stack_height)
    source_widget.setLayout(source_row)
    top_fields_grid.addWidget(source_widget, 3 + top_row_offset, 0, 1, 4)

    form_panel = QWidget()
    form_panel_layout = QVBoxLayout()
    form_panel_layout.setContentsMargins(4, 0, 4, 0)
    form_panel_layout.setSpacing(0)
    form_panel_layout.addLayout(form_layout)
    form_panel.setLayout(form_panel_layout)
    form_panel_width_hint = form_panel.sizeHint().width()
    form_panel_height_hint = form_panel.minimumSizeHint().height()
    form_panel.setFixedWidth(form_panel_width_hint)
    form_panel.setFixedHeight(form_panel_height_hint)
    form_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    preview_panel_width = form_panel_width_hint
    preview_canvas_min_height = preview_panel_width

    preview_layout = QVBoxLayout()
    preview_layout.setSpacing(6)
    preview_layout.setContentsMargins(0, 0, 0, 0)
    preview_title_label = QLabel("Vista previa: (ninguno)")
    preview_title_label.setWordWrap(True)
    preview_layout.addWidget(preview_title_label)

    preview_svg = QSvgWidget()
    preview_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
    preview_svg.setFixedSize(preview_panel_width, preview_canvas_min_height)
    preview_svg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    preview_layout.addWidget(preview_svg, 1)

    preview_placeholder = QLabel("Sin dibujo disponible para esta pieza.")
    preview_placeholder.setAlignment(Qt.AlignCenter)
    preview_placeholder.setWordWrap(True)
    preview_placeholder.setStyleSheet("color: #666; border: 1px dashed #999; padding: 12px;")
    preview_placeholder.setFixedSize(preview_panel_width, preview_canvas_min_height)
    preview_layout.addWidget(preview_placeholder, 1)

    preview_panel = QWidget()
    preview_panel.setFixedWidth(preview_panel_width)
    preview_panel.setMinimumHeight(
        preview_title_label.sizeHint().height()
        + preview_layout.spacing()
        + preview_canvas_min_height
    )
    preview_panel.setLayout(preview_layout)

    def refresh_source_button_state():
        has_source = bool(source_field.text().strip())
        edit_source_editor_btn.setEnabled(has_source)
        remove_source_editor_btn.setEnabled(has_source)

    def build_editor_piece_row():
        return build_piece_editor_row_data(
            base_piece_row=base_piece_row,
            values=PieceEditorValues(
                piece_id=id_field.text(),
                name=name_field.text(),
                quantity=qty_field.text(),
                height=height_field.text(),
                width=width_field.text(),
                thickness=thickness_field.text(),
                color=color_field.text(),
                grain_direction=grain_field.currentData(),
                source=source_field.text(),
            ),
            normalize_source=normalize_source_path,
            infer_companion_f6_source=infer_companion_f6_source,
            pgmx_status=lambda source_value: self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths),
            color_has_no_grain=_board_color_has_no_grain,
        )

    def set_editor_grain_to_no_grain_if_color_requires(color_value: str | None = None) -> bool:
        selected_color = color_field.text().strip() if color_value is None else str(color_value or "").strip()
        selected_thickness = parse_optional_piece_float(thickness_field.text())
        if not _board_color_has_no_grain(selected_color, selected_thickness):
            return False
        if grain_field.currentData() != PIECE_GRAIN_CODE_NONE:
            grain_field.setCurrentIndex(0)
        base_piece_row["grain_direction"] = PIECE_GRAIN_CODE_NONE
        return True

    def set_preview_canvas_height(canvas_height: int) -> None:
        normalized_height = max(int(round(canvas_height)), 1)
        preview_svg.setFixedSize(preview_panel_width, normalized_height)
        preview_placeholder.setFixedSize(preview_panel_width, normalized_height)
        preview_panel.setMinimumHeight(
            preview_title_label.sizeHint().height()
            + preview_layout.spacing()
            + normalized_height
        )

    def refresh_piece_preview():
        refresh_source_button_state()
        preview_piece_row = build_editor_piece_row()
        preview_source = str(preview_piece_row.get("source") or "").strip()
        preview_title_label.setText(
            f"Vista previa: {Path(preview_source).name if preview_source else '(ninguno)'}"
        )

        set_preview_canvas_height(preview_canvas_min_height)
        preview_svg.hide()
        preview_placeholder.show()

        if not preview_source:
            preview_placeholder.setText("La pieza no tiene un programa PGMX asociado.")
            return

        drawing_path = ensure_piece_drawing(
            preview_piece_row,
            force_regenerate=True,
            show_warning=False,
        )
        if drawing_path is None or not drawing_path.is_file():
            preview_placeholder.setText(
                "No se pudo generar la imagen del PGMX asociado. Verifique el archivo seleccionado."
            )
            return

        preview_svg.load(str(drawing_path))
        svg_default_size = preview_svg.renderer().defaultSize()
        if svg_default_size.width() > 0 and svg_default_size.height() > 0:
            aspect_height = round(preview_panel_width * (svg_default_size.height() / svg_default_size.width()))
            set_preview_canvas_height(aspect_height)
        preview_placeholder.hide()
        preview_svg.show()

    def refresh_piece_preview_and_layout(*_args):
        refresh_piece_preview()
        sync_editor_panel_heights()
        sync_editor_dialog_height()

    def sync_editor_panel_heights():
        editor_dialog.layout().activate()
        preview_height = max(preview_panel.sizeHint().height(), preview_panel.minimumSizeHint().height())
        right_panel_height = max(preview_height, right_panel.minimumSizeHint().height())
        right_panel.setFixedHeight(right_panel_height)
        right_panel.updateGeometry()
        content_panel.updateGeometry()

    def sync_editor_dialog_height():
        editor_dialog.layout().activate()
        target_height = max(editor_dialog.minimumHeight(), editor_dialog.sizeHint().height())
        available_editor_geometry = _window_available_geometry(editor_dialog)
        if available_editor_geometry is not None:
            target_height = min(
                target_height,
                max(editor_dialog.minimumHeight(), int(available_editor_geometry.height() * 0.92)),
            )
        if target_height > 0 and editor_dialog.height() != target_height:
            editor_dialog.resize(editor_dialog.width(), target_height)

    def select_source_from_editor():
        source_file = select_pgmx_program_file(editor_dialog, module_path)
        if not source_file:
            return
        source_field.setText(normalize_source_path(source_file))
        refresh_piece_preview_and_layout()

    def edit_source_from_editor():
        open_piece_program_in_default_app(
            editor_dialog,
            self.project,
            build_piece_from_row(build_editor_piece_row()),
            module_path,
        )

    def remove_source_from_editor():
        source_field.clear()
        clear_program_metadata(base_piece_row)
        refresh_piece_preview_and_layout()

    def apply_color_from_editor():
        if is_new_piece or row_index is None:
            return
        current_color = str(base_piece_row.get("color") or "")
        preferred_color = color_field.text().strip() or None
        piece_thickness = parse_optional_piece_float(thickness_field.text())
        new_color_val = apply_color_change(
            current_color,
            target_row_index=row_index,
            preferred_color=preferred_color,
            piece_thickness=piece_thickness,
        )
        if new_color_val is None:
            return
        base_piece_row["color"] = new_color_val
        color_field.setText(new_color_val or "")
        if set_editor_grain_to_no_grain_if_color_requires(new_color_val):
            base_piece_row["grain_direction"] = PIECE_GRAIN_CODE_NONE

    def select_color_from_boards_for_editor():
        piece_thickness = parse_optional_piece_float(thickness_field.text())
        available_colors = _configured_board_colors(piece_thickness=piece_thickness)
        if not available_colors:
            thickness_label = (
                f" para espesor {int(piece_thickness) if float(piece_thickness).is_integer() else piece_thickness} mm"
                if piece_thickness is not None
                else ""
            )
            QMessageBox.warning(
                editor_dialog,
                "Seleccionar color",
                f"No hay colores disponibles en los tableros configurados{thickness_label}.",
            )
            return

        selected_color = open_board_color_picker(
            editor_dialog,
            available_colors,
            current_color=color_field.text().strip(),
        )
        if selected_color is None:
            return
        color_field.setText(selected_color)
        set_editor_grain_to_no_grain_if_color_requires(selected_color)

    def apply_template_to_editor(template_entry: dict) -> None:
        normalized_template = _normalize_manual_piece_template_entry(template_entry)
        if normalized_template is None:
            return

        base_piece_row["piece_type"] = normalized_template.get("piece_type")
        base_piece_row["f6_source"] = normalized_template.get("f6_source")
        base_piece_row["program_width"] = None
        base_piece_row["program_height"] = None
        base_piece_row["program_thickness"] = None

        id_field.setText(str(normalized_template.get("id") or ""))
        name_field.setText(str(normalized_template.get("name") or ""))
        qty_field.setText(str(_parse_piece_quantity_value(normalized_template.get("quantity"), default=1)))
        height_field.setText(optional_field_text(normalized_template.get("height")))
        width_field.setText(optional_field_text(normalized_template.get("width")))
        thickness_field.setText(optional_field_text(normalized_template.get("thickness")))
        color_field.setText(str(normalized_template.get("color") or ""))
        previous_grain_block = grain_field.blockSignals(True)
        normalized_grain = normalize_piece_grain_direction(normalized_template.get("grain_direction"))
        if normalized_grain == "1":
            grain_field.setCurrentIndex(1)
        elif normalized_grain == "2":
            grain_field.setCurrentIndex(2)
        else:
            grain_field.setCurrentIndex(0)
        grain_field.blockSignals(previous_grain_block)
        source_field.setText(str(normalized_template.get("source") or ""))
        refresh_piece_preview_and_layout()

    def on_template_changed(_index: int) -> None:
        if template_combo is None:
            return
        selected_template = template_combo.currentData()
        if selected_template is None:
            return
        apply_template_to_editor(selected_template)

    def save_piece_changes():
        piece_id = id_field.text().strip()
        if not piece_id:
            QMessageBox.warning(editor_dialog, "Editar pieza", "El campo ID es obligatorio.")
            return

        set_editor_grain_to_no_grain_if_color_requires()
        updated_piece = build_editor_piece_row()
        save_as_template = False
        template_selected = bool(template_combo is not None and template_combo.currentData() is not None)
        if is_new_piece and not template_selected:
            piece_display_name = str(updated_piece.get("name") or updated_piece.get("id") or "pieza").strip()
            template_answer = QMessageBox.question(
                editor_dialog,
                "Guardar plantilla",
                f'¿Desea guardar la pieza "{piece_display_name}" como plantilla?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            save_as_template = template_answer == QMessageBox.Yes
        fallback_row = pieces_table.currentRow()
        previous_piece = None if is_new_piece or row_index is None else dict(all_rows[row_index])
        if is_new_piece:
            all_rows.append(updated_piece)
            target_row_index = len(all_rows) - 1
        else:
            all_rows[row_index] = updated_piece
            target_row_index = row_index

        persist_module_config()
        if previous_piece is not None and drawing_path_for_piece_row(previous_piece) != drawing_path_for_piece_row(updated_piece):
            remove_piece_drawing_file(previous_piece, ignore_row_index=target_row_index)
        refresh_piece_drawing_file(updated_piece, row_index=target_row_index)
        if save_as_template:
            try:
                _save_manual_piece_template(updated_piece)
            except Exception as exc:
                QMessageBox.warning(
                    editor_dialog,
                    "Guardar plantilla",
                    f"No se pudo guardar la pieza como plantilla:\n{exc}",
                )
        refresh_pieces_table()
        select_visible_piece_by_id(updated_piece["id"], fallback_row=fallback_row)
        editor_dialog.accept()

    editor_buttons = QHBoxLayout()
    editor_buttons.setContentsMargins(0, 0, 0, 0)
    editor_buttons.setSpacing(8)
    editor_buttons.addStretch(1)
    btn_save_piece = QPushButton("Aceptar")
    btn_cancel_piece = QPushButton("Cancelar")
    btn_save_piece.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    btn_cancel_piece.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    btn_save_piece.setDefault(True)
    btn_save_piece.setAutoDefault(True)
    btn_cancel_piece.setAutoDefault(False)
    for auxiliary_button in (
        apply_color_btn,
        select_color_btn,
        select_source_btn,
        edit_source_editor_btn,
        remove_source_editor_btn,
        btn_cancel_piece,
    ):
        if auxiliary_button is not None:
            auxiliary_button.setDefault(False)
            auxiliary_button.setAutoDefault(False)
            auxiliary_button.setFocusPolicy(Qt.NoFocus)
    btn_save_piece.clicked.connect(save_piece_changes)
    btn_cancel_piece.clicked.connect(editor_dialog.reject)
    editor_buttons.addWidget(btn_save_piece)
    editor_buttons.addWidget(btn_cancel_piece)

    buttons_widget = QWidget()
    buttons_widget.setFixedWidth(form_panel_width_hint)
    buttons_widget.setContentsMargins(0, 0, 0, 0)
    buttons_widget.setLayout(editor_buttons)
    buttons_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sync_editor_grainless_color_rule():
        if set_editor_grain_to_no_grain_if_color_requires():
            refresh_piece_preview_and_layout()

    editor_buttons_top_gap = _scaled_int(155, max(editor_scale, 0.82), 96)
    right_panel = QWidget()
    right_panel.setFixedWidth(form_panel_width_hint)
    right_panel_layout = QVBoxLayout()
    right_panel_layout.setContentsMargins(0, 0, 0, 0)
    right_panel_layout.setSpacing(8)
    right_panel_layout.addWidget(form_panel, 0, Qt.AlignTop | Qt.AlignLeft)
    right_panel_layout.addSpacing(editor_buttons_top_gap)
    right_panel_layout.addWidget(buttons_widget, 0, Qt.AlignTop | Qt.AlignRight)
    right_panel_layout.addStretch(1)
    right_panel.setLayout(right_panel_layout)

    content_layout.addWidget(preview_panel, 0, Qt.AlignTop | Qt.AlignLeft)
    content_layout.addWidget(right_panel, 0, Qt.AlignTop | Qt.AlignLeft)
    content_panel = QWidget()
    content_panel.setLayout(content_layout)
    editor_layout.addWidget(content_panel, 0)

    select_source_btn.clicked.connect(select_source_from_editor)
    edit_source_editor_btn.clicked.connect(edit_source_from_editor)
    remove_source_editor_btn.clicked.connect(remove_source_from_editor)
    color_field.editingFinished.connect(sync_editor_grainless_color_rule)
    thickness_field.editingFinished.connect(sync_editor_grainless_color_rule)
    source_field.textChanged.connect(lambda *_: refresh_source_button_state())
    source_field.editingFinished.connect(refresh_piece_preview_and_layout)
    grain_field.currentIndexChanged.connect(refresh_piece_preview_and_layout)
    if template_combo is not None:
        template_combo.currentIndexChanged.connect(on_template_changed)
    if select_color_btn is not None:
        select_color_btn.clicked.connect(select_color_from_boards_for_editor)
    if apply_color_btn is not None:
        apply_color_btn.clicked.connect(apply_color_from_editor)
    editor_dialog.setLayout(editor_layout)
    refresh_piece_preview_and_layout()
    editor_dialog.layout().activate()
    compact_editor_width = editor_dialog.sizeHint().width()
    compact_editor_height = editor_dialog.minimumSizeHint().height()
    available_editor_geometry = _window_available_geometry(editor_dialog)
    if available_editor_geometry is not None:
        compact_editor_width = min(
            compact_editor_width,
            max(420, int(available_editor_geometry.width() * 0.94)),
        )
    editor_dialog.setMinimumHeight(compact_editor_height)
    editor_dialog.resize(compact_editor_width, compact_editor_height)
    _exec_centered(editor_dialog, inspect_dialog)

