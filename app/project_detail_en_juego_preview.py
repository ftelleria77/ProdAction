"""Preview rendering helpers for the En-Juego layout dialog."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt as QtCoreQt
from PySide6.QtGui import QBrush, QColor as QColorGui, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
)

from app.project_detail_en_juego_layout import clamp, preview_dimensions_mm, safe_float, to_scene_y
from app.project_detail_en_juego_view import EnJuegoPieceItem, make_cosmetic_pen as make_pen
from core.pgmx_processing import parse_pgmx_for_piece, resolve_piece_grain_hatch_axis


def load_piece_drawing_data(
    project,
    module_path,
    piece_row: dict,
    piece_factory: Callable[[dict], Any],
    drawing_data_cache: dict[str, object | None],
):
    piece_id = str(piece_row.get("id") or "").strip()
    if piece_id in drawing_data_cache:
        return drawing_data_cache[piece_id]

    piece_obj = piece_factory(piece_row)
    if not piece_obj.cnc_source:
        drawing_data_cache[piece_id] = None
        return None

    try:
        drawing_data = parse_pgmx_for_piece(project, piece_obj, module_path)
    except Exception:
        drawing_data = None
    drawing_data_cache[piece_id] = drawing_data
    return drawing_data


def draw_chevron_marker(rect_item, marker, piece_height_mm: float, color: str, offset_mm: float = 0.0):
    if marker is None:
        return
    dx = float(getattr(marker, "dx", 0.0) or 0.0)
    dy = float(getattr(marker, "dy", 0.0) or 0.0)
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 1e-9:
        return
    unit_x = dx / length
    unit_y = -dy / length

    anchor_x = float(getattr(marker, "x", 0.0) or 0.0)
    anchor_y = to_scene_y(float(getattr(marker, "y", 0.0) or 0.0), piece_height_mm)
    if abs(offset_mm) > 1e-9:
        anchor_x += (-unit_y) * offset_mm
        anchor_y += unit_x * offset_mm

    chevron_length = 4.0
    chevron_half_width = 2.25
    back_x = anchor_x - (unit_x * chevron_length)
    back_y = anchor_y - (unit_y * chevron_length)
    left_x = back_x + ((-unit_y) * chevron_half_width)
    left_y = back_y + (unit_x * chevron_half_width)
    right_x = back_x - ((-unit_y) * chevron_half_width)
    right_y = back_y - (unit_x * chevron_half_width)

    left_segment = QGraphicsLineItem(left_x, left_y, anchor_x, anchor_y, rect_item)
    left_segment.setPen(make_pen(color, 1.3))
    left_segment.setAcceptedMouseButtons(QtCoreQt.NoButton)

    right_segment = QGraphicsLineItem(right_x, right_y, anchor_x, anchor_y, rect_item)
    right_segment.setPen(make_pen(color, 1.3))
    right_segment.setAcceptedMouseButtons(QtCoreQt.NoButton)


def draw_entry_marker(rect_item, entry_marker, piece_height_mm: float, color: str):
    draw_chevron_marker(rect_item, entry_marker, piece_height_mm, color)


def draw_grain_hatching(rect_item, piece_row: dict, width_mm: float, height_mm: float):
    hatch_axis = resolve_piece_grain_hatch_axis(
        piece_row.get("grain_direction"),
        safe_float(piece_row.get("width")),
        safe_float(piece_row.get("height")),
        width_mm,
        height_mm,
    )
    if hatch_axis not in {"vertical", "horizontal"}:
        return

    hatch_color = "#D8D2C7"
    hatch_spacing = 10.0
    hatch_margin = 0.0
    hatch_pen = make_pen(hatch_color, 0.7)

    if hatch_axis == "vertical":
        current_x = hatch_margin
        while current_x <= (width_mm - hatch_margin):
            hatch_line = QGraphicsLineItem(current_x, hatch_margin, current_x, height_mm - hatch_margin, rect_item)
            hatch_line.setPen(hatch_pen)
            hatch_line.setZValue(-1.0)
            hatch_line.setAcceptedMouseButtons(QtCoreQt.NoButton)
            current_x += hatch_spacing
        return

    current_y = hatch_margin
    while current_y <= (height_mm - hatch_margin):
        hatch_line = QGraphicsLineItem(hatch_margin, current_y, width_mm - hatch_margin, current_y, rect_item)
        hatch_line.setPen(hatch_pen)
        hatch_line.setZValue(-1.0)
        hatch_line.setAcceptedMouseButtons(QtCoreQt.NoButton)
        current_y += hatch_spacing


def build_piece_scene_item(
    piece_row: dict,
    scene_item_key: str,
    title_text: str,
    drawing_data,
    *,
    auto_spacing_adjustment_state: dict,
    effective_piece_spacing: Callable[[], float],
    nominal_scene_rect: Callable[[Any], Any],
    on_position_changed: Callable[[], None],
    scene_padding_mm: float,
    snap_distance_mm: float,
):
    piece_id = str(piece_row.get("id") or "").strip()
    width_mm, height_mm = preview_dimensions_mm(piece_row, drawing_data)
    width_mm = max(width_mm, 1.0)
    height_mm = max(height_mm, 1.0)

    def center_text_item(text_item, *, vertical_offset_mm: float = 0.0):
        scale_value = text_item.scale() if text_item.scale() > 0 else 1.0
        bounds = text_item.boundingRect()
        text_width = bounds.width() * scale_value
        text_height = bounds.height() * scale_value
        pos_x = (width_mm - text_width) / 2.0
        pos_y = ((height_mm - text_height) / 2.0) + vertical_offset_mm
        text_item.setPos(pos_x, pos_y)

    rect_item = EnJuegoPieceItem(
        0,
        0,
        width_mm,
        height_mm,
        auto_spacing_adjustment_state=auto_spacing_adjustment_state,
        effective_piece_spacing=effective_piece_spacing,
        nominal_scene_rect=nominal_scene_rect,
        on_position_changed=on_position_changed,
        scene_padding_mm=scene_padding_mm,
        snap_distance_mm=snap_distance_mm,
    )
    rect_item.setPen(make_pen("#2F4F4F", 1.3))
    rect_item.setBrush(QBrush(QColorGui("#FFFDF8")))
    rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
    rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
    rect_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
    rect_item.setTransformOriginPoint(width_mm / 2.0, height_mm / 2.0)
    rect_item.setData(0, scene_item_key)
    rect_item.setData(1, piece_id)

    title_item = QGraphicsSimpleTextItem(title_text, rect_item)
    title_item.setBrush(QBrush(QColorGui("#111111")))
    title_item.setScale(4.0)
    title_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
    title_item.setZValue(2.0)
    center_text_item(title_item)

    if drawing_data is None:
        empty_item = QGraphicsSimpleTextItem("(sin dibujo)", rect_item)
        empty_item.setBrush(QBrush(QColorGui("#666666")))
        empty_item.setScale(4.0)
        empty_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
        empty_item.setZValue(2.0)
        center_text_item(empty_item, vertical_offset_mm=18.0)
        draw_grain_hatching(rect_item, piece_row, width_mm, height_mm)
        return rect_item, width_mm, height_mm

    draw_grain_hatching(rect_item, piece_row, width_mm, height_mm)

    for path in drawing_data.milling_paths:
        if (path.face or "Top").strip().lower() != "top":
            continue
        if len(path.points) < 2:
            continue
        is_closed_path = len(path.points) >= 3 and path.points[0] == path.points[-1]
        painter_path = QPainterPath()
        first_x, first_y = path.points[0]
        painter_path.moveTo(first_x, to_scene_y(first_y, height_mm))
        for point_x, point_y in path.points[1:]:
            painter_path.lineTo(point_x, to_scene_y(point_y, height_mm))
        path_item = QGraphicsPathItem(painter_path, rect_item)
        path_color = "#C0392B" if not is_closed_path else "#0B7A75"
        path_item.setPen(make_pen(path_color, 1.0))
        path_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
        if not is_closed_path:
            draw_entry_marker(rect_item, path.entry_arrow, height_mm, path_color)

    for circle in drawing_data.milling_circles:
        face = (circle.face or "Top").strip().lower()
        if face not in {"top", "bottom"}:
            continue
        radius = max(1.0, float(circle.radius or 0.0))
        center_x = clamp(float(circle.center_x or 0.0), 0.0, width_mm)
        center_y = clamp(float(circle.center_y or 0.0), 0.0, height_mm)
        scene_y = to_scene_y(center_y, height_mm)
        ellipse_item = QGraphicsEllipseItem(
            center_x - radius,
            scene_y - radius,
            radius * 2.0,
            radius * 2.0,
            rect_item,
        )
        ellipse_item.setPen(make_pen("#0B7A75" if face == "top" else "#1F78B4", 1.0, dashed=(face == "bottom")))
        ellipse_item.setBrush(QBrush(QtCoreQt.transparent))
        ellipse_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
        if face == "top":
            draw_entry_marker(rect_item, circle.entry_arrow, height_mm, "#0B7A75")

    for operation in drawing_data.operations:
        face = (operation.face or "Top").strip().lower()
        op_x = clamp(float(operation.x or 0.0), 0.0, width_mm)
        op_y = clamp(float(operation.y or 0.0), 0.0, height_mm)
        scene_y = to_scene_y(op_y, height_mm)

        if face == "top":
            if operation.op_type == "drill":
                diameter = float(operation.diameter or 5.0)
                radius = max(1.0, diameter / 2.0)
                ellipse_item = QGraphicsEllipseItem(op_x - radius, scene_y - radius, radius * 2.0, radius * 2.0, rect_item)
                ellipse_item.setPen(make_pen("#C0392B", 1.0))
                ellipse_item.setBrush(QBrush(QColorGui("#C0392B")))
                ellipse_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
            elif operation.op_type == "slot":
                slot_w = max(2.0, float(operation.width or 5.0))
                slot_h = max(2.0, float(operation.height or 5.0))
                slot_item = QGraphicsRectItem(op_x, scene_y - slot_h, slot_w, slot_h, rect_item)
                slot_item.setPen(make_pen("#1F78B4", 0.9))
                slot_item.setBrush(QBrush(QtCoreQt.transparent))
                slot_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
        elif face == "bottom":
            diameter = float(operation.diameter or 5.0)
            radius = max(1.0, diameter / 2.0)
            ellipse_item = QGraphicsEllipseItem(op_x - radius, scene_y - radius, radius * 2.0, radius * 2.0, rect_item)
            ellipse_item.setPen(make_pen("#1F78B4", 1.0, dashed=True))
            ellipse_item.setBrush(QBrush(QtCoreQt.transparent))
            ellipse_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
        else:
            side_line = QGraphicsLineItem(op_x, scene_y, op_x + 10.0, scene_y, rect_item)
            side_line.setPen(make_pen("#1F78B4", 1.0, dashed=True))
            side_line.setAcceptedMouseButtons(QtCoreQt.NoButton)

    return rect_item, width_mm, height_mm
