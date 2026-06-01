"""Qt graphics item helpers for the En-Juego layout dialog."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)


def make_cosmetic_pen(color: str, width: float = 1.2, dashed: bool = False) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCosmetic(True)
    if dashed:
        pen.setStyle(Qt.DashLine)
    return pen


def set_padded_scene_rect(graphics_scene, padding_mm: float) -> bool:
    items_rect = graphics_scene.itemsBoundingRect()
    if items_rect.isNull():
        return False
    padded_rect = items_rect.adjusted(-padding_mm, -padding_mm, padding_mm, padding_mm)
    graphics_scene.setSceneRect(padded_rect)
    return True


def fit_scene_items_in_view(
    view,
    graphics_scene,
    *,
    padding_mm: float = 80.0,
    aspect_mode=Qt.KeepAspectRatio,
) -> bool:
    items_rect = graphics_scene.itemsBoundingRect()
    if items_rect.isNull():
        return False
    padded_rect = items_rect.adjusted(-padding_mm, -padding_mm, padding_mm, padding_mm)
    view.fitInView(padded_rect, aspect_mode)
    return True


def selected_en_juego_scene_item(graphics_scene, pieces_list, item_by_instance_id: dict):
    selected_items = [
        item
        for item in graphics_scene.selectedItems()
        if str(item.data(0) or "").strip()
    ]
    if selected_items:
        return selected_items[0]

    current_item = pieces_list.currentItem()
    if current_item is None:
        return None
    instance_key = str(current_item.data(Qt.UserRole) or "")
    return item_by_instance_id.get(instance_key)


def focus_en_juego_piece_from_list(graphics_scene, pieces_list, item_by_instance_id: dict, view) -> bool:
    current_item = pieces_list.currentItem()
    if current_item is None:
        return False
    instance_key = str(current_item.data(Qt.UserRole) or "")
    scene_item = item_by_instance_id.get(instance_key)
    if scene_item is None:
        return False
    graphics_scene.clearSelection()
    scene_item.setSelected(True)
    view.centerOn(scene_item)
    return True


def rotate_en_juego_scene_item(scene_item, delta: float) -> float:
    new_rotation = (scene_item.rotation() + delta) % 360
    scene_item.setRotation(new_rotation)
    return new_rotation


class EnJuegoGraphicsView(QGraphicsView):
    def __init__(self, graphics_scene, parent=None):
        super().__init__(graphics_scene, parent)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.angleDelta().y() == 0:
            super().wheelEvent(event)
            return
        scale_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(scale_factor, scale_factor)


class DimensionLabelTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text: str, on_click):
        super().__init__(text)
        self._on_click = on_click

    def mousePressEvent(self, event):
        if self._on_click is not None:
            self._on_click()
            event.accept()
            return
        super().mousePressEvent(event)


class DimensionLabelBackgroundItem(QGraphicsRectItem):
    def __init__(self, x: float, y: float, width: float, height: float, on_click):
        super().__init__(x, y, width, height)
        self._on_click = on_click

    def mousePressEvent(self, event):
        if self._on_click is not None:
            self._on_click()
            event.accept()
            return
        super().mousePressEvent(event)


class EnJuegoPieceItem(QGraphicsRectItem):
    def __init__(
        self,
        *rect_args,
        auto_spacing_adjustment_state: dict,
        effective_piece_spacing: Callable[[], float],
        nominal_scene_rect: Callable[[Any], Any],
        on_position_changed: Callable[[], None],
        scene_padding_mm: float,
        snap_distance_mm: float,
    ):
        super().__init__(*rect_args)
        self._auto_spacing_adjustment_state = auto_spacing_adjustment_state
        self._effective_piece_spacing = effective_piece_spacing
        self._nominal_scene_rect = nominal_scene_rect
        self._on_position_changed = on_position_changed
        self._scene_padding_mm = float(scene_padding_mm)
        self._snap_distance_mm = float(snap_distance_mm)

    def itemChange(self, change, value):
        if (
            change == QGraphicsItem.ItemPositionChange
            and self._auto_spacing_adjustment_state.get("active")
        ):
            return QPointF(value)

        if change == QGraphicsItem.ItemPositionChange and self.scene() is not None:
            proposed_pos = QPointF(value)
            current_pos = self.pos()
            current_rect = self._nominal_scene_rect(self)
            delta_x = proposed_pos.x() - current_pos.x()
            delta_y = proposed_pos.y() - current_pos.y()
            candidate_rect = current_rect.translated(delta_x, delta_y)

            target_xs = []
            target_ys = []
            spacing_mm = self._effective_piece_spacing()
            for other_item in self.scene().items():
                if other_item is self or not str(other_item.data(0) or "").strip():
                    continue
                other_rect = self._nominal_scene_rect(other_item)
                target_xs.extend(
                    [
                        other_rect.left() - candidate_rect.left(),
                        other_rect.right() - candidate_rect.right(),
                        other_rect.right() + spacing_mm - candidate_rect.left(),
                        other_rect.left() - spacing_mm - candidate_rect.right(),
                    ]
                )
                target_ys.extend(
                    [
                        other_rect.top() - candidate_rect.top(),
                        other_rect.bottom() - candidate_rect.bottom(),
                        other_rect.bottom() + spacing_mm - candidate_rect.top(),
                        other_rect.top() - spacing_mm - candidate_rect.bottom(),
                    ]
                )

            snapped_delta_x = None
            for candidate_delta_x in target_xs:
                if abs(candidate_delta_x) > self._snap_distance_mm:
                    continue
                if snapped_delta_x is None or abs(candidate_delta_x) < abs(snapped_delta_x):
                    snapped_delta_x = candidate_delta_x

            snapped_delta_y = None
            for candidate_delta_y in target_ys:
                if abs(candidate_delta_y) > self._snap_distance_mm:
                    continue
                if snapped_delta_y is None or abs(candidate_delta_y) < abs(snapped_delta_y):
                    snapped_delta_y = candidate_delta_y

            if snapped_delta_x is not None:
                proposed_pos.setX(proposed_pos.x() + snapped_delta_x)
            if snapped_delta_y is not None:
                proposed_pos.setY(proposed_pos.y() + snapped_delta_y)
            return proposed_pos

        if change == QGraphicsItem.ItemPositionHasChanged and self.scene() is not None:
            self._on_position_changed()
            set_padded_scene_rect(self.scene(), self._scene_padding_mm)

        return super().itemChange(change, value)
