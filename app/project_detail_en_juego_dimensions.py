"""Dimension annotation controller for the En-Juego layout dialog."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsLineItem, QInputDialog

from app.project_detail_en_juego_layout import (
    dimension_x_near_inner_edge,
    has_horizontal_blocker,
    has_vertical_blocker,
    horizontal_overlap,
    vertical_overlap,
)
from app.project_detail_en_juego_view import (
    DimensionLabelBackgroundItem,
    DimensionLabelTextItem,
    make_cosmetic_pen,
)


class EnJuegoDimensionAnnotator:
    def __init__(
        self,
        *,
        scene,
        parent_dialog,
        item_by_instance_id: dict,
        effective_piece_spacing: Callable[[], float],
        auto_spacing_adjustment_state: dict,
        update_scene_bounds: Callable[[], None],
        compact_number: Callable[[float], str],
        tolerance_mm: float = 0.1,
    ):
        self.scene = scene
        self.parent_dialog = parent_dialog
        self.item_by_instance_id = item_by_instance_id
        self.effective_piece_spacing = effective_piece_spacing
        self.auto_spacing_adjustment_state = auto_spacing_adjustment_state
        self.update_scene_bounds = update_scene_bounds
        self.compact_number = compact_number
        self.tolerance_mm = tolerance_mm
        self.items = []
        self.ready = False

    def set_ready(self, ready: bool = True) -> None:
        self.ready = bool(ready)

    def nominal_scene_rect(self, scene_item):
        return scene_item.mapRectToScene(scene_item.rect())

    def clear(self) -> None:
        for annotation_item in self.items:
            self.scene.removeItem(annotation_item)
        self.items.clear()

    def add_annotation_item(self, annotation_item, *, interactive: bool = False, z_value: float = 20.0):
        annotation_item.setAcceptedMouseButtons(Qt.LeftButton if interactive else Qt.NoButton)
        annotation_item.setZValue(z_value)
        self.scene.addItem(annotation_item)
        self.items.append(annotation_item)
        return annotation_item

    def add_line_item(self, x1: float, y1: float, x2: float, y2: float, *, dashed: bool = False):
        line_item = QGraphicsLineItem(float(x1), float(y1), float(x2), float(y2))
        line_item.setPen(make_cosmetic_pen("#7A4E00", 1.0, dashed=dashed))
        return self.add_annotation_item(line_item)

    def move_target(self, target_key: str, axis: str, delta_mm: float) -> None:
        if abs(delta_mm) <= self.tolerance_mm:
            return
        target_item = self.item_by_instance_id.get(target_key)
        if target_item is None:
            return
        current_pos = target_item.pos()
        self.auto_spacing_adjustment_state["active"] = True
        try:
            if axis == "x":
                target_item.setPos(current_pos.x() + delta_mm, current_pos.y())
            else:
                target_item.setPos(current_pos.x(), current_pos.y() + delta_mm)
        finally:
            self.auto_spacing_adjustment_state["active"] = False
        self.update()
        self.update_scene_bounds()
        self.scene.clearSelection()
        target_item.setSelected(True)

    def edit_value(
        self,
        current_value_mm: float,
        *,
        target_key: str,
        axis: str,
        minimum_value_mm: float = 0.0,
    ) -> None:
        current_abs_value = round(abs(float(current_value_mm)), 1)
        new_value, ok = QInputDialog.getDouble(
            self.parent_dialog,
            "Editar cota",
            "Medida en mm:",
            current_abs_value,
            float(minimum_value_mm),
            100000.0,
            1,
        )
        if not ok:
            return
        direction = -1.0 if current_value_mm < 0 else 1.0
        desired_value = direction * float(new_value)
        self.move_target(target_key, axis, desired_value - float(current_value_mm))

    def add_text(self, text: str, x: float, y: float, on_edit=None):
        text_item = DimensionLabelTextItem(text, on_edit)
        text_item.setBrush(QBrush(QColor("#2A2418")))
        text_item.setScale(1.35)
        bounds = text_item.boundingRect()
        text_width = bounds.width() * text_item.scale()
        text_height = bounds.height() * text_item.scale()
        background_item = DimensionLabelBackgroundItem(
            x - (text_width / 2.0) - 3.0,
            y - (text_height / 2.0) - 2.0,
            text_width + 6.0,
            text_height + 4.0,
            on_edit,
        )
        background_item.setPen(QPen(Qt.NoPen))
        background_item.setBrush(QBrush(QColor("#FFFDF8")))
        self.add_annotation_item(background_item, interactive=on_edit is not None, z_value=19.5)
        text_item.setPos(x - (text_width / 2.0), y - (text_height / 2.0))
        text_item.setToolTip("Editar medida")
        background_item.setToolTip("Editar medida")
        return self.add_annotation_item(text_item, interactive=on_edit is not None)

    def label(self, value_mm: float) -> str:
        return f"{self.compact_number(round(abs(float(value_mm)), 1))} mm"

    def add_horizontal_dimension(
        self,
        x1: float,
        x2: float,
        y: float,
        label_value: float,
        *,
        target_key: str | None = None,
        minimum_value_mm: float = 0.0,
    ) -> None:
        if abs(x2 - x1) <= self.tolerance_mm:
            return
        tick = 7.0
        self.add_line_item(x1, y, x2, y)
        self.add_line_item(x1, y - tick, x1, y + tick)
        self.add_line_item(x2, y - tick, x2, y + tick)
        on_edit = None
        if target_key:
            on_edit = lambda value=label_value, key=target_key, minimum=minimum_value_mm: self.edit_value(
                value,
                target_key=key,
                axis="x",
                minimum_value_mm=minimum,
            )
        self.add_text(self.label(label_value), (x1 + x2) / 2.0, y - 18.0, on_edit)

    def add_vertical_dimension(
        self,
        x: float,
        y1: float,
        y2: float,
        label_value: float,
        *,
        target_key: str | None = None,
        minimum_value_mm: float = 0.0,
    ) -> None:
        if abs(y2 - y1) <= self.tolerance_mm:
            return
        tick = 7.0
        self.add_line_item(x, y1, x, y2)
        self.add_line_item(x - tick, y1, x + tick, y1)
        self.add_line_item(x - tick, y2, x + tick, y2)
        on_edit = None
        if target_key:
            on_edit = lambda value=label_value, key=target_key, minimum=minimum_value_mm: self.edit_value(
                value,
                target_key=key,
                axis="y",
                minimum_value_mm=minimum,
            )
        self.add_text(self.label(label_value), x + 22.0, (y1 + y2) / 2.0, on_edit)

    def add_vertical_edge_offsets(self, left_rect, right_rect, right_key: str) -> None:
        gap = right_rect.left() - left_rect.right()
        if gap < -self.tolerance_mm:
            return
        top_offset = right_rect.top() - left_rect.top()
        bottom_offset = right_rect.bottom() - left_rect.bottom()
        if abs(top_offset) > self.tolerance_mm:
            lower_top_rect = left_rect if left_rect.top() > right_rect.top() else right_rect
            self.add_vertical_dimension(
                dimension_x_near_inner_edge(lower_top_rect, left_side_piece=lower_top_rect is left_rect),
                left_rect.top(),
                right_rect.top(),
                top_offset,
                target_key=right_key,
            )
        if (
            abs(bottom_offset) > self.tolerance_mm
            and abs(abs(bottom_offset) - abs(top_offset)) > self.tolerance_mm
        ):
            higher_bottom_rect = left_rect if left_rect.bottom() < right_rect.bottom() else right_rect
            self.add_vertical_dimension(
                dimension_x_near_inner_edge(
                    higher_bottom_rect,
                    left_side_piece=higher_bottom_rect is left_rect,
                ),
                left_rect.bottom(),
                right_rect.bottom(),
                bottom_offset,
                target_key=right_key,
            )

    def add_horizontal_edge_offsets(self, upper_rect, lower_rect, lower_key: str) -> None:
        gap = lower_rect.top() - upper_rect.bottom()
        if gap < -self.tolerance_mm:
            return
        dimension_y = upper_rect.bottom() + (max(gap, 0.0) / 2.0)
        left_offset = lower_rect.left() - upper_rect.left()
        right_offset = lower_rect.right() - upper_rect.right()
        if abs(left_offset) > self.tolerance_mm:
            self.add_horizontal_dimension(
                upper_rect.left(),
                lower_rect.left(),
                dimension_y,
                left_offset,
                target_key=lower_key,
            )
        if (
            abs(right_offset) > self.tolerance_mm
            and abs(abs(right_offset) - abs(left_offset)) > self.tolerance_mm
        ):
            self.add_horizontal_dimension(
                upper_rect.right(),
                lower_rect.right(),
                dimension_y,
                right_offset,
                target_key=lower_key,
            )

    def update(self) -> None:
        if not self.ready:
            return
        self.clear()
        rect_entries = [
            (instance_key, scene_item, self.nominal_scene_rect(scene_item))
            for instance_key, scene_item in self.item_by_instance_id.items()
        ]
        if len(rect_entries) < 2:
            return
        spacing_mm = self.effective_piece_spacing()
        for current_index, (first_key, _, first_rect) in enumerate(rect_entries):
            for second_key, _, second_rect in rect_entries[current_index + 1 :]:
                if vertical_overlap(first_rect, second_rect) > self.tolerance_mm:
                    left_key, left_rect, right_key, right_rect = (
                        (first_key, first_rect, second_key, second_rect)
                        if first_rect.right() <= second_rect.left()
                        else (second_key, second_rect, first_key, first_rect)
                    )
                    gap = right_rect.left() - left_rect.right()
                    if gap >= -self.tolerance_mm and not has_horizontal_blocker(
                        rect_entries,
                        left_key,
                        right_key,
                        left_rect,
                        right_rect,
                        self.tolerance_mm,
                    ):
                        overlap_top = max(left_rect.top(), right_rect.top())
                        overlap_bottom = min(left_rect.bottom(), right_rect.bottom())
                        if gap > spacing_mm + self.tolerance_mm:
                            self.add_horizontal_dimension(
                                left_rect.right(),
                                right_rect.left(),
                                (overlap_top + overlap_bottom) / 2.0,
                                gap,
                                target_key=right_key,
                                minimum_value_mm=spacing_mm,
                            )
                        self.add_vertical_edge_offsets(left_rect, right_rect, right_key)

                if horizontal_overlap(first_rect, second_rect) > self.tolerance_mm:
                    upper_key, upper_rect, lower_key, lower_rect = (
                        (first_key, first_rect, second_key, second_rect)
                        if first_rect.bottom() <= second_rect.top()
                        else (second_key, second_rect, first_key, first_rect)
                    )
                    gap = lower_rect.top() - upper_rect.bottom()
                    if gap >= -self.tolerance_mm and not has_vertical_blocker(
                        rect_entries,
                        upper_key,
                        lower_key,
                        upper_rect,
                        lower_rect,
                        self.tolerance_mm,
                    ):
                        overlap_left = max(upper_rect.left(), lower_rect.left())
                        overlap_right = min(upper_rect.right(), lower_rect.right())
                        if gap > spacing_mm + self.tolerance_mm:
                            self.add_vertical_dimension(
                                (overlap_left + overlap_right) / 2.0,
                                upper_rect.bottom(),
                                lower_rect.top(),
                                gap,
                                target_key=lower_key,
                                minimum_value_mm=spacing_mm,
                            )
                        self.add_horizontal_edge_offsets(upper_rect, lower_rect, lower_key)
