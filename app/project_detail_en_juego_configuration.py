"""Main En-Juego layout configuration dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsScene,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.project_detail_en_juego_dimensions import EnJuegoDimensionAnnotator
from app.project_detail_en_juego_dialogs import (
    apply_en_juego_cut_mode_controls,
    build_en_juego_controls_panel,
    build_en_juego_view_toolbar,
    open_en_juego_division_settings_dialog,
    open_en_juego_squaring_settings_dialog,
)
from app.project_detail_en_juego_layout import (
    collect_en_juego_instances,
    collect_en_juego_layout_data,
    enforce_scene_piece_spacing,
    initial_unsaved_layout_cursor,
    next_unsaved_piece_position,
    preview_dimensions_mm,
    saved_scene_placement,
)
from app.project_detail_en_juego_output import (
    create_en_juego_pgmx_from_dialog as create_en_juego_pgmx_from_dialog_flow,
)
from app.project_detail_en_juego_preview import (
    build_piece_scene_item,
    load_piece_drawing_data,
)
from app.project_detail_en_juego_settings import (
    en_juego_effective_piece_spacing_mm,
    normalize_en_juego_dialog_settings,
)
from app.project_detail_en_juego_state import (
    configurable_en_juego_rows,
    en_juego_material_thickness_mm,
    normalized_en_juego_layout,
    store_en_juego_composition_layout,
)
from app.project_detail_en_juego_view import (
    EnJuegoGraphicsView,
    fit_scene_items_in_view,
    focus_en_juego_piece_from_list,
    rotate_en_juego_scene_item,
    selected_en_juego_scene_item,
    set_padded_scene_rect,
)
from app.qt_helpers import _apply_responsive_window_size, _exec_centered
from app.settings import (
    _compact_number,
    _load_en_juego_cutting_tools,
    _normalize_en_juego_settings,
    _read_app_settings,
)


def open_en_juego_configuration_dialog(
    *,
    parent_dialog,
    project,
    module_name: str,
    module_path,
    all_rows: list[dict],
    config_data: dict,
    piece_from_row,
    is_valid_thickness_value,
    persist_module_config,
    sync_en_juego_observations,
    refresh_pieces_table,
) -> None:
    en_juego_rows = configurable_en_juego_rows(all_rows, is_valid_thickness_value)
    if not en_juego_rows:
        QMessageBox.warning(
            parent_dialog,
            "Configurar En Juego",
            "No hay piezas marcadas como 'En juego' en este módulo.",
        )
        return

    app_cut_settings = _read_app_settings()
    scene_padding_mm = 400.0
    snap_distance_mm = 18.0
    en_juego_settings = dict(_normalize_en_juego_settings(config_data.get("en_juego_settings")))
    available_cutting_tools = _load_en_juego_cutting_tools()
    material_thickness_mm = en_juego_material_thickness_mm(en_juego_rows)

    saved_layout = normalized_en_juego_layout(config_data)
    auto_spacing_adjustment_state = {"active": False}

    config_dialog = QDialog(parent_dialog)
    config_dialog.setWindowTitle(f"Configurar En Juego - {module_name}")
    config_scale, _, _ = _apply_responsive_window_size(
        config_dialog,
        1320,
        760,
        width_ratio=0.96,
        height_ratio=0.92,
    )

    main_layout = QVBoxLayout()
    main_layout.addWidget(
        QLabel(
            "Arrastre las piezas en juego para definir su disposición relativa.\n"
            "Cada unidad se muestra por separado según su cantidad y se identifica con #.\n"
            "La posición se guarda en el módulo para reutilizarla más adelante."
        )
    )

    content_layout = QHBoxLayout()
    controls_panel = build_en_juego_controls_panel(
        en_juego_settings=en_juego_settings,
        config_scale=config_scale,
    )
    pieces_list = controls_panel.pieces_list
    manual_cut_radio = controls_panel.manual_cut_radio
    nesting_cut_radio = controls_panel.nesting_cut_radio
    configure_division_btn = controls_panel.configure_division_btn
    configure_squaring_btn = controls_panel.configure_squaring_btn
    origin_x_field = controls_panel.origin_x_field
    origin_y_field = controls_panel.origin_y_field
    origin_z_field = controls_panel.origin_z_field
    square_then_divide_radio = controls_panel.square_then_divide_radio
    content_layout.addWidget(controls_panel.widget, 0, Qt.AlignTop)

    def effective_piece_spacing_mm() -> float:
        return en_juego_effective_piece_spacing_mm(
            cut_mode="nesting" if nesting_cut_radio.isChecked() else "manual",
            app_cut_settings=app_cut_settings,
            en_juego_settings=en_juego_settings,
            material_thickness_mm=material_thickness_mm,
        )

    preview_gap_mm = effective_piece_spacing_mm()

    scene = QGraphicsScene(config_dialog)
    view = EnJuegoGraphicsView(scene)
    view_panel = QWidget()
    view_panel_layout = QVBoxLayout()
    view_panel_layout.setContentsMargins(0, 0, 0, 0)
    view_panel_layout.setSpacing(8)
    view_panel_layout.addWidget(view, 1)
    view_panel.setLayout(view_panel_layout)
    content_layout.addWidget(view_panel, 1)
    main_layout.addLayout(content_layout)

    drawing_data_cache: dict[str, object | None] = {}

    def piece_drawing_data(piece_row: dict):
        return load_piece_drawing_data(
            project,
            module_path,
            piece_row,
            piece_from_row,
            drawing_data_cache,
        )

    item_by_instance_id: dict[str, object] = {}

    def update_scene_bounds():
        set_padded_scene_rect(scene, scene_padding_mm)

    dimension_annotator = EnJuegoDimensionAnnotator(
        scene=scene,
        parent_dialog=config_dialog,
        item_by_instance_id=item_by_instance_id,
        effective_piece_spacing=effective_piece_spacing_mm,
        auto_spacing_adjustment_state=auto_spacing_adjustment_state,
        update_scene_bounds=update_scene_bounds,
        compact_number=_compact_number,
    )
    nominal_scene_rect = dimension_annotator.nominal_scene_rect
    update_dimension_annotations = dimension_annotator.update

    en_juego_instances = collect_en_juego_instances(en_juego_rows)

    layout_wrap_mm = 2400.0
    current_unsaved_x_mm, current_unsaved_y_mm, current_row_max_h_mm = initial_unsaved_layout_cursor(
        en_juego_instances,
        saved_layout,
        lambda piece_row: preview_dimensions_mm(piece_row, piece_drawing_data(piece_row))[0],
        preview_gap_mm,
    )

    for instance in en_juego_instances:
        piece_row = instance["piece_row"]
        piece_id = instance["piece_id"]
        copy_index = instance["copy_index"]
        instance_key = instance["instance_key"]
        title_text = instance["title_text"]

        rect_item, width_mm, height_mm = build_piece_scene_item(
            piece_row,
            instance_key,
            title_text,
            piece_drawing_data(piece_row),
            auto_spacing_adjustment_state=auto_spacing_adjustment_state,
            effective_piece_spacing=effective_piece_spacing_mm,
            nominal_scene_rect=nominal_scene_rect,
            on_position_changed=update_dimension_annotations,
            scene_padding_mm=scene_padding_mm,
            snap_distance_mm=snap_distance_mm,
        )

        stored_x_mm, stored_y_mm, stored_rotation = saved_scene_placement(
            saved_layout,
            piece_id,
            copy_index,
        )
        if stored_x_mm is not None and stored_y_mm is not None:
            pos_x_mm = stored_x_mm
            pos_y_mm = stored_y_mm
        else:
            (
                pos_x_mm,
                pos_y_mm,
                current_unsaved_x_mm,
                current_unsaved_y_mm,
                current_row_max_h_mm,
            ) = next_unsaved_piece_position(
                current_unsaved_x_mm,
                current_unsaved_y_mm,
                current_row_max_h_mm,
                width_mm,
                height_mm,
                gap_mm=preview_gap_mm,
                wrap_mm=layout_wrap_mm,
            )

        rect_item.setPos(pos_x_mm, pos_y_mm)
        if stored_rotation is not None:
            rect_item.setRotation(stored_rotation)
        scene.addItem(rect_item)

        list_text = f"{title_text} | {int(round(width_mm))} x {int(round(height_mm))}"
        list_item = QListWidgetItem(list_text)
        list_item.setData(Qt.UserRole, instance_key)
        pieces_list.addItem(list_item)
        item_by_instance_id[instance_key] = rect_item

    def enforce_minimum_piece_spacing(*, fit_view_after: bool = True):
        spacing_mm = effective_piece_spacing_mm()
        if spacing_mm <= 0:
            return

        selected_instance_key = None
        selected_items = [
            item for item in scene.selectedItems() if str(item.data(0) or "").strip()
        ]
        if selected_items:
            selected_instance_key = str(selected_items[0].data(0) or "")

        moved_any = False
        auto_spacing_adjustment_state["active"] = True
        try:
            moved_any = enforce_scene_piece_spacing(
                item_by_instance_id,
                nominal_scene_rect,
                spacing_mm,
            )
        finally:
            auto_spacing_adjustment_state["active"] = False

        if not moved_any:
            return

        update_dimension_annotations()
        update_scene_bounds()
        if fit_view_after:
            fit_scene_items_in_view(view, scene)

        if selected_instance_key:
            restored_item = item_by_instance_id.get(selected_instance_key)
            if restored_item is not None:
                scene.clearSelection()
                restored_item.setSelected(True)

    def focus_selected_piece():
        focus_en_juego_piece_from_list(scene, pieces_list, item_by_instance_id, view)

    pieces_list.currentItemChanged.connect(lambda *_: focus_selected_piece())

    if pieces_list.count() > 0:
        pieces_list.setCurrentRow(0)

    dimension_annotator.set_ready(True)
    update_dimension_annotations()
    update_scene_bounds()
    fit_scene_items_in_view(view, scene)

    def selected_scene_item():
        return selected_en_juego_scene_item(scene, pieces_list, item_by_instance_id)

    def rotate_selected_piece(delta: float):
        scene_item = selected_scene_item()
        if scene_item is None:
            QMessageBox.warning(
                config_dialog,
                "Configurar En Juego",
                "Seleccione una pieza para rotarla.",
            )
            return
        rotate_en_juego_scene_item(scene_item, delta)
        update_dimension_annotations()
        update_scene_bounds()
        view.centerOn(scene_item)

    def sync_en_juego_settings_from_controls():
        en_juego_settings.update(
            normalize_en_juego_dialog_settings(
                en_juego_settings,
                cut_mode="nesting" if nesting_cut_radio.isChecked() else "manual",
                origin_x=origin_x_field.text().strip(),
                origin_y=origin_y_field.text().strip(),
                origin_z=origin_z_field.text().strip(),
                division_squaring_order=(
                    "squaring_then_division"
                    if square_then_divide_radio.isChecked()
                    else "division_then_squaring"
                ),
            )
        )

    def persist_en_juego_settings():
        sync_en_juego_settings_from_controls()
        config_data["en_juego_settings"] = dict(en_juego_settings)
        persist_module_config()

    def open_en_juego_settings_dialog_v2():
        if not nesting_cut_radio.isChecked():
            return
        open_en_juego_division_settings_dialog(
            parent_dialog=config_dialog,
            en_juego_settings=en_juego_settings,
            available_cutting_tools=available_cutting_tools,
            compact_scale=config_scale,
            material_thickness_mm=material_thickness_mm,
            origin_x_field=origin_x_field,
            origin_y_field=origin_y_field,
            origin_z_field=origin_z_field,
            persist_settings=persist_en_juego_settings,
            refresh_cut_mode_controls=refresh_cut_mode_controls,
        )

    def open_en_juego_squaring_settings_dialog_v2():
        if not nesting_cut_radio.isChecked():
            return
        open_en_juego_squaring_settings_dialog(
            parent_dialog=config_dialog,
            en_juego_settings=en_juego_settings,
            available_cutting_tools=available_cutting_tools,
            compact_scale=config_scale,
            persist_settings=persist_en_juego_settings,
            refresh_cut_mode_controls=refresh_cut_mode_controls,
        )

    def collect_layout_data():
        return collect_en_juego_layout_data(
            item_by_instance_id,
            en_juego_rows,
            nominal_scene_rect,
        )

    def save_en_juego_composition_layout():
        store_en_juego_composition_layout(config_data, collect_layout_data())

    def save_en_juego_layout():
        sync_en_juego_settings_from_controls()
        save_en_juego_composition_layout()
        config_data["en_juego_settings"] = dict(en_juego_settings)
        persist_module_config()
        config_dialog.accept()

    def create_en_juego_pgmx_from_dialog():
        create_en_juego_pgmx_from_dialog_flow(
            parent_dialog=config_dialog,
            project=project,
            module_name=module_name,
            module_path=module_path,
            piece_rows=all_rows,
            config_data=config_data,
            en_juego_settings=en_juego_settings,
            sync_settings_from_controls=sync_en_juego_settings_from_controls,
            save_composition_layout=save_en_juego_composition_layout,
            sync_en_juego_observations=sync_en_juego_observations,
            persist_module_config=persist_module_config,
            refresh_pieces_table=refresh_pieces_table,
        )

    configure_division_btn.clicked.connect(open_en_juego_settings_dialog_v2)
    configure_squaring_btn.clicked.connect(open_en_juego_squaring_settings_dialog_v2)
    view_toolbar = build_en_juego_view_toolbar(
        fit_view=lambda: fit_scene_items_in_view(view, scene),
        rotate_left=lambda: rotate_selected_piece(-90.0),
        rotate_right=lambda: rotate_selected_piece(90.0),
        create_en_juego=create_en_juego_pgmx_from_dialog,
        save_layout=save_en_juego_layout,
        close_layout=config_dialog.reject,
    )
    create_en_juego_btn = view_toolbar.create_en_juego_btn
    view_panel_layout.addLayout(view_toolbar.layout)

    def refresh_cut_mode_controls(*, enforce_spacing: bool = False):
        sync_en_juego_settings_from_controls()
        is_nesting_mode = en_juego_settings.get("cut_mode") == "nesting"
        apply_en_juego_cut_mode_controls(
            controls_panel,
            create_en_juego_btn,
            is_nesting_mode=is_nesting_mode,
            spacing_mm=effective_piece_spacing_mm(),
        )
        if enforce_spacing:
            enforce_minimum_piece_spacing()
        update_dimension_annotations()

    manual_cut_radio.toggled.connect(lambda *_: refresh_cut_mode_controls(enforce_spacing=True))
    nesting_cut_radio.toggled.connect(lambda *_: refresh_cut_mode_controls(enforce_spacing=True))
    refresh_cut_mode_controls()

    config_dialog.setLayout(main_layout)
    _exec_centered(config_dialog, parent_dialog)
