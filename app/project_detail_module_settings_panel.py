"""Module settings panel for the project detail inspection dialog."""

from dataclasses import dataclass

from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QWidget

from app.project_detail_selectors import (
    DETALLES_SELECTOR_CONFIG,
    GUIAS_SELECTOR_CONFIG,
    HERRAJES_SELECTOR_CONFIG,
    open_editable_selection_dialog,
)
from app.qt_helpers import _scaled_int
from app.settings import _parse_piece_quantity_value


@dataclass
class ProjectDetailModuleSettingsPanel:
    dim_x_field: QLineEdit
    dim_y_field: QLineEdit
    dim_z_field: QLineEdit
    module_quantity_field: QLineEdit
    herrajes_field: QLineEdit
    guias_field: QLineEdit
    detalles_field: QLineEdit


def build_project_detail_module_settings_panel(
    *,
    parent_dialog,
    target_layout,
    settings: dict,
    module_quantity,
    compact_scale: float,
    on_changed,
) -> ProjectDetailModuleSettingsPanel:
    target_layout.addWidget(QLabel("Configuración del módulo:"))

    dim_x_field = QLineEdit(str(settings.get("x", "") or ""))
    dim_y_field = QLineEdit(str(settings.get("y", "") or ""))
    dim_z_field = QLineEdit(str(settings.get("z", "") or ""))
    module_quantity_field = QLineEdit(
        str(_parse_piece_quantity_value(module_quantity, default=1))
    )

    field_width = _scaled_int(100, compact_scale, 72)
    quantity_field_width = _scaled_int(80, compact_scale, 60)
    quantity_button_width = _scaled_int(14, compact_scale, 11)
    quantity_button_height = _scaled_int(12, compact_scale, 10)
    quantity_button_font_size = _scaled_int(7, compact_scale, 6)
    dim_x_field.setFixedWidth(field_width)
    dim_y_field.setFixedWidth(field_width)
    dim_z_field.setFixedWidth(field_width)
    module_quantity_field.setFixedWidth(quantity_field_width)

    def style_quantity_micro_button(button: QPushButton) -> None:
        button.setContentsMargins(0, 0, 0, 0)
        button.setStyleSheet(
            "QPushButton {"
            f"font-size: {quantity_button_font_size}px;"
            "padding: 0px;"
            "margin: 0px;"
            "text-align: center;"
            "}"
        )

    def adjust_module_quantity(delta: int) -> None:
        current_value = _parse_piece_quantity_value(
            module_quantity_field.text().strip(),
            default=1,
        )
        target_value = max(1, current_value + int(delta))
        if target_value != current_value:
            module_quantity_field.setText(str(target_value))

    module_quantity_buttons = QWidget()
    module_quantity_buttons_layout = QVBoxLayout(module_quantity_buttons)
    module_quantity_buttons_layout.setContentsMargins(0, 0, 0, 0)
    module_quantity_buttons_layout.setSpacing(0)

    module_quantity_plus_btn = QPushButton("+", module_quantity_buttons)
    module_quantity_plus_btn.setToolTip("Incrementar cantidad del módulo")
    module_quantity_plus_btn.setFixedSize(quantity_button_width, quantity_button_height)
    style_quantity_micro_button(module_quantity_plus_btn)
    module_quantity_plus_btn.clicked.connect(lambda: adjust_module_quantity(+1))

    module_quantity_minus_btn = QPushButton("-", module_quantity_buttons)
    module_quantity_minus_btn.setToolTip("Disminuir cantidad del módulo")
    module_quantity_minus_btn.setFixedSize(quantity_button_width, quantity_button_height)
    style_quantity_micro_button(module_quantity_minus_btn)
    module_quantity_minus_btn.clicked.connect(lambda: adjust_module_quantity(-1))

    module_quantity_buttons_layout.addWidget(module_quantity_plus_btn)
    module_quantity_buttons_layout.addWidget(module_quantity_minus_btn)
    module_quantity_buttons.setFixedSize(quantity_button_width, quantity_button_height * 2)

    module_quantity_widget = QWidget()
    module_quantity_layout = QHBoxLayout(module_quantity_widget)
    module_quantity_layout.setContentsMargins(0, 0, 0, 0)
    module_quantity_layout.setSpacing(2)
    module_quantity_layout.addWidget(module_quantity_field)
    module_quantity_layout.addWidget(module_quantity_buttons)

    xyz_layout = QHBoxLayout()
    xyz_layout.addWidget(QLabel("X: "))
    xyz_layout.addWidget(dim_x_field)
    xyz_layout.addWidget(QLabel("Y: "))
    xyz_layout.addWidget(dim_y_field)
    xyz_layout.addWidget(QLabel("Z: "))
    xyz_layout.addWidget(dim_z_field)
    xyz_layout.addStretch(1)
    xyz_layout.addWidget(QLabel("Cantidad: "))
    xyz_layout.addWidget(module_quantity_widget)
    target_layout.addLayout(xyz_layout)

    herrajes_field = QLineEdit(str(settings.get("herrajes_y_accesorios", "")))
    guias_field = QLineEdit(str(settings.get("guias_y_bisagras", "")))
    detalles_field = QLineEdit(str(settings.get("detalles_de_obra", "")))

    for field in (
        dim_x_field,
        dim_y_field,
        dim_z_field,
        module_quantity_field,
        herrajes_field,
        guias_field,
        detalles_field,
    ):
        field.textChanged.connect(on_changed)

    def add_selector_row(label: str, field: QLineEdit, selector_config) -> None:
        target_layout.addWidget(QLabel(label))
        row_layout = QHBoxLayout()
        row_layout.addWidget(field)

        select_btn = QPushButton("...")
        select_btn.setMaximumWidth(50)
        select_btn.clicked.connect(
            lambda: open_editable_selection_dialog(
                parent_dialog,
                field,
                selector_config,
            )
        )
        row_layout.addWidget(select_btn)
        target_layout.addLayout(row_layout)

    add_selector_row("Herrajes y accesorios:", herrajes_field, HERRAJES_SELECTOR_CONFIG)
    add_selector_row("Guías y bisagras:", guias_field, GUIAS_SELECTOR_CONFIG)
    add_selector_row("Detalles de Obra:", detalles_field, DETALLES_SELECTOR_CONFIG)

    return ProjectDetailModuleSettingsPanel(
        dim_x_field=dim_x_field,
        dim_y_field=dim_y_field,
        dim_z_field=dim_z_field,
        module_quantity_field=module_quantity_field,
        herrajes_field=herrajes_field,
        guias_field=guias_field,
        detalles_field=detalles_field,
    )
