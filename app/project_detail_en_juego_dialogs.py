"""Small helpers shared by En-Juego settings dialogs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.project_detail_en_juego_settings import (
    apply_en_juego_division_dialog_settings,
    apply_en_juego_squaring_dialog_settings,
    division_tool_hint_text,
    en_juego_depth_role_text,
    squaring_tool_hint_text,
)
from app.qt_helpers import _apply_responsive_window_size, _exec_centered, _scaled_int
from app.settings import (
    _coerce_setting_bool,
    _coerce_setting_number,
    _compact_number,
    _normalize_en_juego_cut_mode,
    _normalize_en_juego_operation_order,
    _resolve_en_juego_cutting_tool,
)
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH


EMPTY_TOOL_LABEL = "(sin herramientas disponibles)"


@dataclass
class EnJuegoControlsPanel:
    widget: QWidget
    pieces_list: QListWidget
    origin_group: QGroupBox
    operation_order_group: QGroupBox
    manual_cut_radio: QRadioButton
    nesting_cut_radio: QRadioButton
    spacing_hint_label: QLabel
    configure_division_btn: QPushButton
    configure_squaring_btn: QPushButton
    origin_x_field: QLineEdit
    origin_y_field: QLineEdit
    origin_z_field: QLineEdit
    divide_then_square_radio: QRadioButton
    square_then_divide_radio: QRadioButton


@dataclass
class EnJuegoViewToolbar:
    layout: QHBoxLayout
    create_en_juego_btn: QPushButton
    save_layout_btn: QPushButton
    close_layout_btn: QPushButton


def en_juego_tool_combo_entries(available_cutting_tools: Iterable[dict]) -> list[tuple[str, Any]]:
    entries = []
    for tool_data in available_cutting_tools or ():
        label = str(
            tool_data.get("label")
            or tool_data.get("tool_name")
            or tool_data.get("tool_code")
            or tool_data.get("tool_id")
            or ""
        ).strip()
        entries.append((label or "(herramienta sin nombre)", tool_data.get("tool_id") or ""))
    return entries


def en_juego_selected_tool_index(available_cutting_tools: Iterable[dict], selected_tool_id) -> int:
    selected_id = str(selected_tool_id or "").strip()
    for index, tool_data in enumerate(available_cutting_tools or ()):
        if str(tool_data.get("tool_id") or "").strip() == selected_id:
            return index
    return 0


def populate_en_juego_tool_combo(
    tool_combo,
    available_cutting_tools: Iterable[dict],
    selected_tool_id,
    *,
    empty_label: str = EMPTY_TOOL_LABEL,
) -> None:
    tools = list(available_cutting_tools or ())
    for label, tool_id in en_juego_tool_combo_entries(tools):
        tool_combo.addItem(label, tool_id)

    if tool_combo.count() > 0:
        tool_combo.setCurrentIndex(en_juego_selected_tool_index(tools, selected_tool_id))
        tool_combo.setEnabled(True)
        return

    tool_combo.addItem(empty_label, "")
    tool_combo.setEnabled(False)


def set_widgets_enabled(widgets: Iterable[Any], enabled: bool) -> None:
    for widget in widgets:
        widget.setEnabled(bool(enabled))


def build_en_juego_controls_panel(
    *,
    en_juego_settings: dict,
    config_scale: float,
) -> EnJuegoControlsPanel:
    left_panel = QWidget()
    left_panel_layout = QVBoxLayout()
    left_panel_layout.setContentsMargins(0, 0, 0, 0)
    left_panel_layout.setSpacing(8)

    pieces_list = QListWidget()
    left_panel_width = _scaled_int(250, max(config_scale, 0.82), 180)
    pieces_list.setFixedWidth(left_panel_width)
    pieces_list.setFixedHeight(_scaled_int(220, max(config_scale, 0.82), 170))
    left_panel_layout.addWidget(pieces_list, 0)

    origin_group = QGroupBox("Origen")
    origin_layout = QGridLayout()
    origin_layout.setContentsMargins(8, 8, 8, 8)
    origin_layout.setHorizontalSpacing(8)
    origin_layout.setVerticalSpacing(6)
    origin_x_field = QLineEdit(str(en_juego_settings.get("origin_x", 0)))
    origin_y_field = QLineEdit(str(en_juego_settings.get("origin_y", 0)))
    origin_z_field = QLineEdit(str(en_juego_settings.get("origin_z", 0)))
    origin_layout.addWidget(QLabel("Origen X"), 0, 0)
    origin_layout.addWidget(origin_x_field, 0, 1)
    origin_layout.addWidget(QLabel("Origen Y"), 1, 0)
    origin_layout.addWidget(origin_y_field, 1, 1)
    origin_layout.addWidget(QLabel("Origen Z"), 2, 0)
    origin_layout.addWidget(origin_z_field, 2, 1)
    origin_group.setLayout(origin_layout)

    operation_order_group = QGroupBox("Orden")
    operation_order_layout = QVBoxLayout()
    operation_order_layout.setContentsMargins(8, 8, 8, 8)
    operation_order_layout.setSpacing(6)
    divide_then_square_radio = QRadioButton("Dividir -> Escuadrar")
    square_then_divide_radio = QRadioButton("Escuadrar -> Dividir")
    current_operation_order = _normalize_en_juego_operation_order(
        en_juego_settings.get("division_squaring_order")
    )
    divide_then_square_radio.setChecked(current_operation_order == "division_then_squaring")
    square_then_divide_radio.setChecked(current_operation_order == "squaring_then_division")
    operation_order_layout.addWidget(divide_then_square_radio)
    operation_order_layout.addWidget(square_then_divide_radio)
    operation_order_group.setLayout(operation_order_layout)

    options_group = QGroupBox("Opciones")
    options_group.setFixedWidth(left_panel_width)
    options_layout = QVBoxLayout()
    options_layout.setContentsMargins(8, 8, 8, 8)
    options_layout.setSpacing(8)
    manual_cut_radio = QRadioButton("Corte Manual")
    nesting_cut_radio = QRadioButton("Corte Nesting")
    manual_cut_radio.setChecked(
        _normalize_en_juego_cut_mode(en_juego_settings.get("cut_mode")) == "manual"
    )
    nesting_cut_radio.setChecked(not manual_cut_radio.isChecked())
    spacing_hint_label = QLabel()
    spacing_hint_label.setWordWrap(True)
    configure_division_btn = QPushButton("Configurar\nDivisiones")
    configure_squaring_btn = QPushButton("Configurar\nEscuadrado")
    configure_division_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    configure_squaring_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    configure_buttons_row = QHBoxLayout()
    configure_buttons_row.setContentsMargins(0, 0, 0, 0)
    configure_buttons_row.setSpacing(8)
    configure_buttons_row.addStretch(1)
    configure_buttons_row.addWidget(configure_squaring_btn)
    configure_buttons_row.addWidget(configure_division_btn)
    configure_buttons_row.addStretch(1)
    options_layout.addWidget(manual_cut_radio)
    options_layout.addWidget(nesting_cut_radio)
    options_layout.addWidget(spacing_hint_label)
    options_layout.addWidget(origin_group)
    options_layout.addWidget(operation_order_group)
    options_layout.addLayout(configure_buttons_row)
    options_group.setLayout(options_layout)

    left_panel_layout.addWidget(options_group, 0)
    left_panel_layout.addStretch(1)
    left_panel.setFixedWidth(left_panel_width)
    left_panel.setLayout(left_panel_layout)

    return EnJuegoControlsPanel(
        widget=left_panel,
        pieces_list=pieces_list,
        origin_group=origin_group,
        operation_order_group=operation_order_group,
        manual_cut_radio=manual_cut_radio,
        nesting_cut_radio=nesting_cut_radio,
        spacing_hint_label=spacing_hint_label,
        configure_division_btn=configure_division_btn,
        configure_squaring_btn=configure_squaring_btn,
        origin_x_field=origin_x_field,
        origin_y_field=origin_y_field,
        origin_z_field=origin_z_field,
        divide_then_square_radio=divide_then_square_radio,
        square_then_divide_radio=square_then_divide_radio,
    )


def build_en_juego_view_toolbar(
    *,
    fit_view,
    rotate_left,
    rotate_right,
    create_en_juego,
    save_layout,
    close_layout,
) -> EnJuegoViewToolbar:
    view_buttons_layout = QHBoxLayout()
    view_buttons_layout.setContentsMargins(0, 0, 0, 0)
    view_buttons_layout.setSpacing(8)

    fit_view_btn = QPushButton("Ajustar\nVista")
    rotate_left_btn = QPushButton("Rotar\n-90°")
    rotate_right_btn = QPushButton("Rotar\n+90°")
    for button in (fit_view_btn, rotate_left_btn, rotate_right_btn):
        button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

    fit_view_btn.clicked.connect(fit_view)
    rotate_left_btn.clicked.connect(rotate_left)
    rotate_right_btn.clicked.connect(rotate_right)
    view_buttons_layout.addWidget(fit_view_btn)
    view_buttons_layout.addWidget(rotate_left_btn)
    view_buttons_layout.addWidget(rotate_right_btn)

    create_en_juego_btn = QPushButton("Crear\nEn-Juego")
    save_layout_btn = QPushButton("Guardar\nDisposición")
    close_layout_btn = QPushButton("Cerrar")
    for button in (create_en_juego_btn, save_layout_btn, close_layout_btn):
        button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

    create_en_juego_btn.clicked.connect(create_en_juego)
    save_layout_btn.clicked.connect(save_layout)
    close_layout_btn.clicked.connect(close_layout)
    view_buttons_layout.addStretch()
    view_buttons_layout.addWidget(create_en_juego_btn)
    view_buttons_layout.addWidget(save_layout_btn)
    view_buttons_layout.addWidget(close_layout_btn)

    return EnJuegoViewToolbar(
        layout=view_buttons_layout,
        create_en_juego_btn=create_en_juego_btn,
        save_layout_btn=save_layout_btn,
        close_layout_btn=close_layout_btn,
    )


def open_en_juego_division_settings_dialog(
    *,
    parent_dialog,
    en_juego_settings: dict,
    available_cutting_tools: Iterable[dict],
    compact_scale: float,
    material_thickness_mm: float,
    origin_x_field,
    origin_y_field,
    origin_z_field,
    persist_settings,
    refresh_cut_mode_controls,
) -> None:
    settings_dialog = QDialog(parent_dialog)
    settings_dialog.setWindowTitle("Configurar Divisiones")
    _apply_responsive_window_size(
        settings_dialog,
        780,
        460,
        width_ratio=0.66,
        height_ratio=0.6,
    )
    settings_layout = QVBoxLayout()
    settings_layout.setContentsMargins(12, 12, 12, 12)
    settings_layout.setSpacing(10)
    settings_layout.addWidget(
        QLabel(
            "Defina las opciones de divisiones del En-Juego para este módulo.\n"
            "Por ahora, la herramienta elegida define la separación mínima en el panel."
        )
    )

    tool_group = QGroupBox("Herramienta de corte")
    tool_layout = QVBoxLayout()
    tool_layout.setContentsMargins(8, 8, 8, 8)
    tool_layout.setSpacing(6)
    tool_combo = QComboBox()
    populate_en_juego_tool_combo(
        tool_combo,
        available_cutting_tools,
        en_juego_settings.get("cutting_tool_id"),
    )
    tool_hint_label = QLabel()
    tool_hint_label.setWordWrap(True)
    tool_layout.addWidget(tool_combo)
    tool_layout.addWidget(tool_hint_label)
    tool_group.setLayout(tool_layout)
    settings_layout.addWidget(tool_group)

    depth_group = QGroupBox("Profundidad de división")
    depth_layout = QGridLayout()
    depth_layout.setContentsMargins(8, 6, 8, 6)
    depth_layout.setHorizontalSpacing(8)
    depth_layout.setVerticalSpacing(4)
    through_checkbox = QCheckBox("Pasante")
    through_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("cutting_is_through"), True)
    )
    depth_role_label = QLabel()
    depth_value_field = QLineEdit(str(en_juego_settings.get("cutting_depth_value", 1.0)))
    depth_layout.addWidget(through_checkbox, 0, 0, 1, 2)
    depth_layout.addWidget(depth_role_label, 1, 0)
    depth_layout.addWidget(depth_value_field, 1, 1)
    depth_group.setLayout(depth_layout)
    depth_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

    strategy_group = QGroupBox("Estrategia")
    strategy_layout = QGridLayout()
    strategy_layout.setContentsMargins(8, 8, 8, 8)
    strategy_layout.setHorizontalSpacing(8)
    strategy_layout.setVerticalSpacing(6)
    cutting_multipass_checkbox = QCheckBox("Multipasada")
    cutting_multipass_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("cutting_multipass_enabled"), False)
    )
    cutting_path_mode_combo = QComboBox()
    cutting_path_mode_combo.addItem("Unidireccional", "Unidirectional")
    cutting_path_mode_combo.addItem("Bidireccional", "Bidirectional")
    cutting_path_mode_combo.setCurrentIndex(
        1
        if str(en_juego_settings.get("cutting_path_mode") or "Unidirectional") == "Bidirectional"
        else 0
    )
    cutting_pocket_depth_field = QLineEdit(str(en_juego_settings.get("cutting_pocket_depth", 0.0)))
    cutting_last_pocket_field = QLineEdit(str(en_juego_settings.get("cutting_last_pocket", 0.0)))
    strategy_layout.addWidget(cutting_multipass_checkbox, 0, 0, 1, 2)
    strategy_layout.addWidget(QLabel("Recorrido"), 1, 0)
    strategy_layout.addWidget(cutting_path_mode_combo, 1, 1)
    strategy_layout.addWidget(QLabel("Profundidad de Hueco"), 2, 0)
    strategy_layout.addWidget(cutting_pocket_depth_field, 2, 1)
    strategy_layout.addWidget(QLabel("Último Hueco"), 3, 0)
    strategy_layout.addWidget(cutting_last_pocket_field, 3, 1)
    strategy_group.setLayout(strategy_layout)
    strategy_group.setMinimumHeight(_scaled_int(138, compact_scale, 108))

    lead_group = QGroupBox("Acercamiento y Alejamiento")
    lead_layout = QGridLayout()
    lead_layout.setContentsMargins(8, 8, 8, 8)
    lead_layout.setHorizontalSpacing(8)
    lead_layout.setVerticalSpacing(6)

    approach_checkbox = QCheckBox("Acercamiento")
    approach_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("approach_enabled"), False)
    )
    approach_type_combo = QComboBox()
    approach_type_combo.addItem("Arco", "Arc")
    approach_type_combo.addItem("Lineal", "Line")
    approach_type_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("approach_type") or "Arc") == "Arc" else 1
    )
    approach_radius_field = QLineEdit(str(en_juego_settings.get("approach_radius_multiplier", 2.0)))
    approach_mode_combo = QComboBox()
    approach_mode_combo.addItem("En cota", "Quote")
    approach_mode_combo.addItem("En bajada", "Down")
    approach_mode_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("approach_mode") or "Quote") == "Quote" else 1
    )

    retract_checkbox = QCheckBox("Alejamiento")
    retract_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("retract_enabled"), False)
    )
    retract_type_combo = QComboBox()
    retract_type_combo.addItem("Arco", "Arc")
    retract_type_combo.addItem("Lineal", "Line")
    retract_type_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("retract_type") or "Arc") == "Arc" else 1
    )
    retract_radius_field = QLineEdit(str(en_juego_settings.get("retract_radius_multiplier", 2.0)))
    retract_mode_combo = QComboBox()
    retract_mode_combo.addItem("En cota", "Quote")
    retract_mode_combo.addItem("En subida", "Up")
    retract_mode_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("retract_mode") or "Quote") == "Quote" else 1
    )

    lead_layout.addWidget(approach_checkbox, 0, 0, 1, 2)
    lead_layout.addWidget(QLabel("Entrada"), 1, 0)
    lead_layout.addWidget(approach_type_combo, 1, 1)
    lead_layout.addWidget(QLabel("Multipl radio"), 2, 0)
    lead_layout.addWidget(approach_radius_field, 2, 1)
    lead_layout.addWidget(QLabel("Acercamiento"), 3, 0)
    lead_layout.addWidget(approach_mode_combo, 3, 1)
    lead_layout.addWidget(retract_checkbox, 4, 0, 1, 2)
    lead_layout.addWidget(QLabel("Salida"), 5, 0)
    lead_layout.addWidget(retract_type_combo, 5, 1)
    lead_layout.addWidget(QLabel("Multipl radio"), 6, 0)
    lead_layout.addWidget(retract_radius_field, 6, 1)
    lead_layout.addWidget(QLabel("Alejamiento"), 7, 0)
    lead_layout.addWidget(retract_mode_combo, 7, 1)
    lead_group.setLayout(lead_layout)

    left_column_layout = QVBoxLayout()
    left_column_layout.setContentsMargins(0, 0, 0, 0)
    left_column_layout.setSpacing(8)
    left_column_layout.addWidget(depth_group, 0, Qt.AlignTop)
    left_column_layout.addWidget(strategy_group, 1)
    left_column_widget = QWidget()
    left_column_widget.setLayout(left_column_layout)

    depth_and_lead_row = QHBoxLayout()
    depth_and_lead_row.setContentsMargins(0, 0, 0, 0)
    depth_and_lead_row.setSpacing(8)
    depth_and_lead_row.addWidget(left_column_widget, 1)
    depth_and_lead_row.addWidget(lead_group, 1)
    settings_layout.addLayout(depth_and_lead_row)

    buttons_row = QHBoxLayout()
    buttons_row.addStretch(1)
    save_settings_btn = QPushButton("Guardar")
    cancel_settings_btn = QPushButton("Cancelar")
    save_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    cancel_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    buttons_row.addWidget(save_settings_btn)
    buttons_row.addWidget(cancel_settings_btn)
    settings_layout.addLayout(buttons_row)
    settings_dialog.setLayout(settings_layout)

    def refresh_tool_hint():
        current_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
        current_settings = dict(en_juego_settings)
        current_settings["cutting_tool_id"] = str(current_tool.get("tool_id") or "").strip()
        current_settings["cutting_tool_diameter"] = _compact_number(
            _coerce_setting_number(current_tool.get("diameter"), 0.0, minimum=0.0)
        )
        current_settings["cutting_is_through"] = through_checkbox.isChecked()
        current_settings["cutting_depth_value"] = _compact_number(
            _coerce_setting_number(
                depth_value_field.text().strip(),
                en_juego_settings.get("cutting_depth_value", 1.0),
                minimum=0.0,
            )
        )
        depth_role_label.setText(
            en_juego_depth_role_text(
                current_settings["cutting_is_through"],
                operation_label="división",
            )
        )
        tool_hint_label.setText(
            division_tool_hint_text(
                current_tool,
                current_settings,
                material_thickness_mm=material_thickness_mm,
            )
        )

    def refresh_lead_controls():
        approach_enabled = approach_checkbox.isChecked()
        set_widgets_enabled(
            (approach_type_combo, approach_radius_field, approach_mode_combo),
            approach_enabled,
        )

        retract_enabled = retract_checkbox.isChecked()
        set_widgets_enabled(
            (retract_type_combo, retract_radius_field, retract_mode_combo),
            retract_enabled,
        )

        multipass_enabled = cutting_multipass_checkbox.isChecked()
        set_widgets_enabled(
            (
                cutting_path_mode_combo,
                cutting_pocket_depth_field,
                cutting_last_pocket_field,
            ),
            multipass_enabled,
        )

        depth_role_label.setText(
            en_juego_depth_role_text(
                through_checkbox.isChecked(),
                operation_label="división",
            )
        )

    refresh_lead_controls()
    refresh_tool_hint()
    tool_combo.currentIndexChanged.connect(lambda *_: refresh_tool_hint())
    through_checkbox.toggled.connect(lambda *_: refresh_tool_hint())
    depth_value_field.textChanged.connect(lambda *_: refresh_tool_hint())
    through_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
    approach_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
    retract_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
    cutting_multipass_checkbox.toggled.connect(lambda *_: refresh_lead_controls())

    def save_settings_dialog():
        selected_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
        en_juego_settings.update(
            apply_en_juego_division_dialog_settings(
                en_juego_settings,
                selected_tool=selected_tool,
                origin_x=origin_x_field.text().strip(),
                origin_y=origin_y_field.text().strip(),
                origin_z=origin_z_field.text().strip(),
                cutting_is_through=through_checkbox.isChecked(),
                cutting_depth_value=depth_value_field.text().strip(),
                cutting_multipass_enabled=cutting_multipass_checkbox.isChecked(),
                cutting_path_mode=cutting_path_mode_combo.currentData(),
                cutting_pocket_depth=cutting_pocket_depth_field.text().strip(),
                cutting_last_pocket=cutting_last_pocket_field.text().strip(),
                approach_enabled=approach_checkbox.isChecked(),
                approach_type=approach_type_combo.currentData(),
                approach_radius_multiplier=approach_radius_field.text().strip(),
                approach_mode=approach_mode_combo.currentData(),
                retract_enabled=retract_checkbox.isChecked(),
                retract_type=retract_type_combo.currentData(),
                retract_radius_multiplier=retract_radius_field.text().strip(),
                retract_mode=retract_mode_combo.currentData(),
            )
        )
        persist_settings()
        refresh_cut_mode_controls()
        settings_dialog.accept()

    save_settings_btn.clicked.connect(save_settings_dialog)
    cancel_settings_btn.clicked.connect(settings_dialog.reject)
    _exec_centered(settings_dialog, parent_dialog)


def open_en_juego_squaring_settings_dialog(
    *,
    parent_dialog,
    en_juego_settings: dict,
    available_cutting_tools: Iterable[dict],
    compact_scale: float,
    persist_settings,
    refresh_cut_mode_controls,
) -> None:
    settings_dialog = QDialog(parent_dialog)
    settings_dialog.setWindowTitle("Configurar Escuadrado")
    _apply_responsive_window_size(
        settings_dialog,
        780,
        420,
        width_ratio=0.64,
        height_ratio=0.58,
    )
    settings_layout = QVBoxLayout()
    settings_layout.setContentsMargins(12, 12, 12, 12)
    settings_layout.setSpacing(10)
    settings_layout.addWidget(
        QLabel(
            "Defina las opciones de escuadrado del En-Juego para este módulo.\n"
            "Estas opciones se guardan junto con la disposición del módulo."
        )
    )

    tool_group = QGroupBox("Herramienta de escuadrado")
    tool_layout = QVBoxLayout()
    tool_layout.setContentsMargins(8, 8, 8, 8)
    tool_layout.setSpacing(6)
    tool_combo = QComboBox()
    populate_en_juego_tool_combo(
        tool_combo,
        available_cutting_tools,
        en_juego_settings.get("squaring_tool_id"),
    )
    tool_hint_label = QLabel()
    tool_hint_label.setWordWrap(True)
    tool_layout.addWidget(tool_combo)
    tool_layout.addWidget(tool_hint_label)
    tool_group.setLayout(tool_layout)
    settings_layout.addWidget(tool_group)

    depth_group = QGroupBox("Profundidad de escuadrado")
    depth_layout = QGridLayout()
    depth_layout.setContentsMargins(8, 6, 8, 6)
    depth_layout.setHorizontalSpacing(8)
    depth_layout.setVerticalSpacing(4)
    through_checkbox = QCheckBox("Pasante")
    through_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("squaring_is_through"), True)
    )
    depth_role_label = QLabel()
    depth_value_field = QLineEdit(str(en_juego_settings.get("squaring_depth_value", 1.0)))
    depth_layout.addWidget(through_checkbox, 0, 0, 1, 2)
    depth_layout.addWidget(depth_role_label, 1, 0)
    depth_layout.addWidget(depth_value_field, 1, 1)
    depth_group.setLayout(depth_layout)
    depth_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

    strategy_group = QGroupBox("Estrategia")
    strategy_layout = QGridLayout()
    strategy_layout.setContentsMargins(8, 8, 8, 8)
    strategy_layout.setSpacing(6)
    strategy_layout.setHorizontalSpacing(8)
    strategy_layout.setVerticalSpacing(6)
    direction_combo = QComboBox()
    direction_combo.addItem("Horario", "CW")
    direction_combo.addItem("Antihorario", "CCW")
    direction_combo.setCurrentIndex(
        1 if str(en_juego_settings.get("squaring_direction") or "CW") == "CCW" else 0
    )
    unidirectional_multipass_checkbox = QCheckBox("Multipasada Unidireccional")
    unidirectional_multipass_checkbox.setChecked(
        _coerce_setting_bool(
            en_juego_settings.get("squaring_unidirectional_multipass"),
            False,
        )
    )
    pocket_depth_field = QLineEdit(str(en_juego_settings.get("squaring_pocket_depth", 0.0)))
    last_pocket_field = QLineEdit(str(en_juego_settings.get("squaring_last_pocket", 0.0)))
    strategy_layout.addWidget(QLabel("Sentido"), 0, 0)
    strategy_layout.addWidget(direction_combo, 0, 1)
    strategy_layout.addWidget(unidirectional_multipass_checkbox, 1, 0, 1, 2)
    strategy_layout.addWidget(QLabel("Profundidad de Hueco"), 2, 0)
    strategy_layout.addWidget(pocket_depth_field, 2, 1)
    strategy_layout.addWidget(QLabel("Último Hueco"), 3, 0)
    strategy_layout.addWidget(last_pocket_field, 3, 1)
    strategy_group.setLayout(strategy_layout)
    strategy_group.setMinimumHeight(_scaled_int(138, compact_scale, 108))

    lead_group = QGroupBox("Acercamiento y Alejamiento")
    lead_layout = QGridLayout()
    lead_layout.setContentsMargins(8, 8, 8, 8)
    lead_layout.setHorizontalSpacing(8)
    lead_layout.setVerticalSpacing(6)

    approach_checkbox = QCheckBox("Acercamiento")
    approach_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("squaring_approach_enabled"), False)
    )
    approach_type_combo = QComboBox()
    approach_type_combo.addItem("Arco", "Arc")
    approach_type_combo.addItem("Lineal", "Line")
    approach_type_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("squaring_approach_type") or "Arc") == "Arc" else 1
    )
    approach_radius_field = QLineEdit(
        str(en_juego_settings.get("squaring_approach_radius_multiplier", 2.0))
    )
    approach_mode_combo = QComboBox()
    approach_mode_combo.addItem("En cota", "Quote")
    approach_mode_combo.addItem("En bajada", "Down")
    approach_mode_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("squaring_approach_mode") or "Quote") == "Quote" else 1
    )

    retract_checkbox = QCheckBox("Alejamiento")
    retract_checkbox.setChecked(
        _coerce_setting_bool(en_juego_settings.get("squaring_retract_enabled"), False)
    )
    retract_type_combo = QComboBox()
    retract_type_combo.addItem("Arco", "Arc")
    retract_type_combo.addItem("Lineal", "Line")
    retract_type_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("squaring_retract_type") or "Arc") == "Arc" else 1
    )
    retract_radius_field = QLineEdit(
        str(en_juego_settings.get("squaring_retract_radius_multiplier", 2.0))
    )
    retract_mode_combo = QComboBox()
    retract_mode_combo.addItem("En cota", "Quote")
    retract_mode_combo.addItem("En subida", "Up")
    retract_mode_combo.setCurrentIndex(
        0 if str(en_juego_settings.get("squaring_retract_mode") or "Quote") == "Quote" else 1
    )

    lead_layout.addWidget(approach_checkbox, 0, 0, 1, 2)
    lead_layout.addWidget(QLabel("Entrada"), 1, 0)
    lead_layout.addWidget(approach_type_combo, 1, 1)
    lead_layout.addWidget(QLabel("Multipl radio"), 2, 0)
    lead_layout.addWidget(approach_radius_field, 2, 1)
    lead_layout.addWidget(QLabel("Acercamiento"), 3, 0)
    lead_layout.addWidget(approach_mode_combo, 3, 1)
    lead_layout.addWidget(retract_checkbox, 4, 0, 1, 2)
    lead_layout.addWidget(QLabel("Salida"), 5, 0)
    lead_layout.addWidget(retract_type_combo, 5, 1)
    lead_layout.addWidget(QLabel("Multipl radio"), 6, 0)
    lead_layout.addWidget(retract_radius_field, 6, 1)
    lead_layout.addWidget(QLabel("Alejamiento"), 7, 0)
    lead_layout.addWidget(retract_mode_combo, 7, 1)
    lead_group.setLayout(lead_layout)

    left_column_layout = QVBoxLayout()
    left_column_layout.setContentsMargins(0, 0, 0, 0)
    left_column_layout.setSpacing(8)
    left_column_layout.addWidget(depth_group, 0, Qt.AlignTop)
    left_column_layout.addWidget(strategy_group, 1)
    left_column_widget = QWidget()
    left_column_widget.setLayout(left_column_layout)

    depth_and_lead_row = QHBoxLayout()
    depth_and_lead_row.setContentsMargins(0, 0, 0, 0)
    depth_and_lead_row.setSpacing(8)
    depth_and_lead_row.addWidget(left_column_widget, 1)
    depth_and_lead_row.addWidget(lead_group, 1)
    settings_layout.addLayout(depth_and_lead_row)

    buttons_row = QHBoxLayout()
    buttons_row.addStretch(1)
    save_settings_btn = QPushButton("Guardar")
    cancel_settings_btn = QPushButton("Cancelar")
    save_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    cancel_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
    buttons_row.addWidget(save_settings_btn)
    buttons_row.addWidget(cancel_settings_btn)
    settings_layout.addLayout(buttons_row)
    settings_dialog.setLayout(settings_layout)

    def refresh_tool_hint():
        current_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
        depth_role_label.setText(
            en_juego_depth_role_text(
                through_checkbox.isChecked(),
                operation_label="escuadrado",
            )
        )
        tool_hint_label.setText(squaring_tool_hint_text(current_tool))

    def refresh_lead_controls():
        set_widgets_enabled(
            (approach_type_combo, approach_radius_field, approach_mode_combo),
            approach_checkbox.isChecked(),
        )
        set_widgets_enabled(
            (retract_type_combo, retract_radius_field, retract_mode_combo),
            retract_checkbox.isChecked(),
        )
        multipass_enabled = unidirectional_multipass_checkbox.isChecked()
        set_widgets_enabled((pocket_depth_field, last_pocket_field), multipass_enabled)
        depth_role_label.setText(
            en_juego_depth_role_text(
                through_checkbox.isChecked(),
                operation_label="escuadrado",
            )
        )

    refresh_lead_controls()
    refresh_tool_hint()
    tool_combo.currentIndexChanged.connect(lambda *_: refresh_tool_hint())
    through_checkbox.toggled.connect(lambda *_: refresh_tool_hint())
    through_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
    approach_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
    retract_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
    unidirectional_multipass_checkbox.toggled.connect(lambda *_: refresh_lead_controls())

    def save_settings_dialog():
        selected_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
        en_juego_settings.update(
            apply_en_juego_squaring_dialog_settings(
                en_juego_settings,
                selected_tool=selected_tool,
                squaring_is_through=through_checkbox.isChecked(),
                squaring_depth_value=depth_value_field.text().strip(),
                squaring_approach_enabled=approach_checkbox.isChecked(),
                squaring_approach_type=approach_type_combo.currentData(),
                squaring_approach_radius_multiplier=approach_radius_field.text().strip(),
                squaring_approach_mode=approach_mode_combo.currentData(),
                squaring_retract_enabled=retract_checkbox.isChecked(),
                squaring_retract_type=retract_type_combo.currentData(),
                squaring_retract_radius_multiplier=retract_radius_field.text().strip(),
                squaring_retract_mode=retract_mode_combo.currentData(),
                squaring_direction=direction_combo.currentData(),
                squaring_unidirectional_multipass=unidirectional_multipass_checkbox.isChecked(),
                squaring_pocket_depth=pocket_depth_field.text().strip(),
                squaring_last_pocket=last_pocket_field.text().strip(),
            )
        )
        persist_settings()
        refresh_cut_mode_controls()
        settings_dialog.accept()

    save_settings_btn.clicked.connect(save_settings_dialog)
    cancel_settings_btn.clicked.connect(settings_dialog.reject)
    _exec_centered(settings_dialog, parent_dialog)
