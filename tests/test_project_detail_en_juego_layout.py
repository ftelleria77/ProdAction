from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.project_detail_en_juego_layout import (
    clamp,
    collect_en_juego_composition_data,
    collect_en_juego_instances,
    collect_en_juego_layout_data,
    composition_grain_axis,
    dimension_x_near_inner_edge,
    en_juego_instance_key,
    en_juego_quantity,
    enforce_scene_piece_spacing,
    has_horizontal_blocker,
    has_vertical_blocker,
    horizontal_overlap,
    initial_unsaved_layout_cursor,
    local_grain_axis,
    next_unsaved_piece_position,
    preview_dimensions_mm,
    safe_float,
    saved_layout_for_instance,
    saved_scene_placement,
    scene_piece_items_in_layout_order,
    to_scene_y,
    vertical_overlap,
)


class Rect:
    def __init__(self, left: float, top: float, right: float, bottom: float):
        self._left = left
        self._top = top
        self._right = right
        self._bottom = bottom

    def left(self) -> float:
        return self._left

    def top(self) -> float:
        return self._top

    def right(self) -> float:
        return self._right

    def bottom(self) -> float:
        return self._bottom

    def width(self) -> float:
        return self._right - self._left

    def height(self) -> float:
        return self._bottom - self._top


class Point:
    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y


class SceneItem:
    def __init__(
        self,
        *,
        piece_id: str,
        pos_x: float,
        pos_y: float,
        rect: Rect,
        nominal_rect: Rect,
        rotation: float = 0.0,
    ):
        self._piece_id = piece_id
        self._pos = Point(pos_x, pos_y)
        self._rect = rect
        self._nominal_rect = nominal_rect
        self._rotation = rotation

    def pos(self) -> Point:
        return self._pos

    def rotation(self) -> float:
        return self._rotation

    def rect(self) -> Rect:
        return self._rect

    def mapToScene(self, x: float, y: float) -> Point:
        return Point(self._pos.x() + x, self._pos.y() + y)

    def data(self, role: int):
        return self._piece_id if role == 1 else None

    def nominal_rect(self) -> Rect:
        return self._nominal_rect


class MovableSceneItem:
    def __init__(self, key: str, left: float, top: float, width: float, height: float):
        self._key = key
        self._pos = Point(left, top)
        self._width = width
        self._height = height

    def pos(self) -> Point:
        return self._pos

    def setPos(self, x: float, y: float) -> None:
        self._pos = Point(x, y)

    def data(self, role: int):
        return self._key if role == 0 else None

    def nominal_rect(self) -> Rect:
        return Rect(
            self._pos.x(),
            self._pos.y(),
            self._pos.x() + self._width,
            self._pos.y() + self._height,
        )


class ProjectDetailEnJuegoLayoutTests(unittest.TestCase):
    def test_safe_float_and_clamp_helpers(self) -> None:
        self.assertEqual(safe_float("10,5".replace(",", ".")), 10.5)
        self.assertIsNone(safe_float("abc"))
        self.assertEqual(clamp(20, 0, 10), 10)
        self.assertEqual(to_scene_y(25, 100), 75)

    def test_en_juego_quantity_and_instance_key(self) -> None:
        self.assertEqual(en_juego_quantity({"quantity": "3"}), 3)
        self.assertEqual(en_juego_quantity({"quantity": ""}), 1)
        self.assertEqual(en_juego_instance_key("P1", 2), "P1#2")

    def test_saved_layout_for_instance_supports_v2_and_legacy_keys(self) -> None:
        stored, key = saved_layout_for_instance({"P1#2": {"x": 2}}, "P1", 2)
        self.assertEqual(stored, {"x": 2})
        self.assertEqual(key, "P1#2")

        stored, key = saved_layout_for_instance({"P1": {"x": 1}}, "P1", 1)
        self.assertEqual(stored, {"x": 1})
        self.assertEqual(key, "P1#1")

        stored, key = saved_layout_for_instance({}, "P1", 1)
        self.assertIsNone(stored)
        self.assertEqual(key, "P1#1")

    def test_saved_scene_placement_supports_current_and_legacy_fields(self) -> None:
        self.assertEqual(
            saved_scene_placement(
                {"P1#2": {"scene_x": "10", "scene_y": "20", "rotation_deg": "90"}},
                "P1",
                2,
            ),
            (10.0, 20.0, 90.0),
        )
        self.assertEqual(
            saved_scene_placement({"P1": {"x": "1", "y": "2", "rotation": "45"}}, "P1", 1),
            (1.0, 2.0, 45.0),
        )
        self.assertEqual(saved_scene_placement({}, "P1", 1), (None, None, None))

    def test_collect_en_juego_instances_expands_piece_quantities(self) -> None:
        rows = [
            {"id": "P1", "name": "Lateral", "quantity": "2"},
            {"id": "P2", "name": "Base", "quantity": "1"},
            {"id": "", "name": "Sin id", "quantity": "4"},
        ]

        instances = collect_en_juego_instances(rows)

        self.assertEqual([item["instance_key"] for item in instances], ["P1#1", "P1#2", "P2#1"])
        self.assertEqual([item["title_text"] for item in instances], ["Lateral #1", "Lateral #2", "Base"])

    def test_initial_unsaved_layout_cursor_starts_after_saved_instances(self) -> None:
        instances = collect_en_juego_instances(
            [
                {"id": "P1", "name": "Lateral", "quantity": "2", "width": "100"},
                {"id": "P2", "name": "Base", "quantity": "1", "width": "200"},
            ]
        )
        saved_layout = {
            "P1#1": {"scene_x": "10", "scene_y": "20"},
            "P2#1": {"scene_x": "300", "scene_y": "40"},
        }

        cursor = initial_unsaved_layout_cursor(
            instances,
            saved_layout,
            lambda piece_row: float(piece_row["width"]),
            12.0,
        )

        self.assertEqual(cursor, (512.0, 0.0, 0.0))

    def test_next_unsaved_piece_position_wraps_when_piece_exceeds_row_width(self) -> None:
        self.assertEqual(
            next_unsaved_piece_position(
                2300.0,
                0.0,
                120.0,
                200.0,
                80.0,
                gap_mm=10.0,
                wrap_mm=2400.0,
            ),
            (0.0, 130.0, 210.0, 130.0, 80.0),
        )
        self.assertEqual(
            next_unsaved_piece_position(
                0.0,
                0.0,
                0.0,
                100.0,
                80.0,
                gap_mm=10.0,
                wrap_mm=2400.0,
            ),
            (0.0, 0.0, 110.0, 0.0, 80.0),
        )

    def test_preview_dimensions_prefers_top_face_then_program_then_piece_dimensions(self) -> None:
        drawing_data = SimpleNamespace(face_dimensions={"Top": (300, 200)})
        self.assertEqual(preview_dimensions_mm({}, drawing_data), (300.0, 200.0))
        self.assertEqual(
            preview_dimensions_mm({"program_width": "120", "program_height": "80", "width": "10", "height": "20"}),
            (120.0, 80.0),
        )
        self.assertEqual(preview_dimensions_mm({"width": "10", "height": "20"}), (10.0, 20.0))

    def test_scene_piece_items_in_layout_order_sorts_by_position_then_key(self) -> None:
        item_a = MovableSceneItem("B", 20, 10, 50, 50)
        item_b = MovableSceneItem("A", 10, 10, 50, 50)
        item_c = MovableSceneItem("C", 0, 0, 50, 50)

        ordered = scene_piece_items_in_layout_order(
            {"B": item_a, "A": item_b, "C": item_c},
            lambda item: item.nominal_rect(),
        )

        self.assertEqual([item.data(0) for item in ordered], ["C", "A", "B"])

    def test_enforce_scene_piece_spacing_pushes_overlapping_piece(self) -> None:
        fixed_item = MovableSceneItem("A", 0, 0, 100, 50)
        movable_item = MovableSceneItem("B", 80, 10, 100, 50)

        moved = enforce_scene_piece_spacing(
            {"A": fixed_item, "B": movable_item},
            lambda item: item.nominal_rect(),
            10.0,
        )

        self.assertTrue(moved)
        self.assertEqual(movable_item.pos().x(), 110)
        self.assertEqual(movable_item.pos().y(), 10)

    def test_enforce_scene_piece_spacing_ignores_non_positive_spacing(self) -> None:
        fixed_item = MovableSceneItem("A", 0, 0, 100, 50)
        movable_item = MovableSceneItem("B", 80, 10, 100, 50)

        moved = enforce_scene_piece_spacing(
            {"A": fixed_item, "B": movable_item},
            lambda item: item.nominal_rect(),
            0.0,
        )

        self.assertFalse(moved)
        self.assertEqual(movable_item.pos().x(), 80)

    def test_dimension_geometry_helpers_detect_overlaps_and_blockers(self) -> None:
        left = Rect(0, 0, 100, 50)
        right = Rect(140, 10, 220, 60)
        blocker = Rect(105, 15, 130, 45)
        upper = Rect(0, 0, 50, 100)
        lower = Rect(10, 140, 60, 230)
        vertical_blocker = Rect(15, 105, 45, 130)

        self.assertEqual(vertical_overlap(left, right), 40)
        self.assertEqual(horizontal_overlap(upper, lower), 40)
        self.assertTrue(
            has_horizontal_blocker(
                [("left", None, left), ("right", None, right), ("blocker", None, blocker)],
                "left",
                "right",
                left,
                right,
            )
        )
        self.assertTrue(
            has_vertical_blocker(
                [("upper", None, upper), ("lower", None, lower), ("blocker", None, vertical_blocker)],
                "upper",
                "lower",
                upper,
                lower,
            )
        )
        self.assertEqual(dimension_x_near_inner_edge(Rect(10, 0, 110, 20), left_side_piece=True), 82.0)
        self.assertEqual(dimension_x_near_inner_edge(Rect(10, 0, 20, 20), left_side_piece=False), 15.0)

    def test_collect_en_juego_layout_data_serializes_scene_items(self) -> None:
        item = SceneItem(
            piece_id="P1",
            pos_x=10.123,
            pos_y=20.456,
            rect=Rect(0, 0, 100, 50),
            nominal_rect=Rect(10.123, 20.456, 110.123, 70.456),
            rotation=90.0,
        )

        layout_data = collect_en_juego_layout_data(
            {"P1#1": item},
            [{"id": "P1", "width": "100", "height": "50", "grain_direction": "2", "color": "Roble"}],
            lambda scene_item: scene_item.nominal_rect(),
        )

        stored = layout_data["P1#1"]
        self.assertEqual(stored["piece_id"], "P1")
        self.assertEqual(stored["scene_x"], 10.12)
        self.assertEqual(stored["scene_y"], 20.46)
        self.assertEqual(stored["rotation_deg"], 90.0)
        self.assertEqual(stored["x_mm"], 0.0)
        self.assertEqual(stored["y_mm"], 0.0)
        self.assertEqual(stored["footprint_width_mm"], 100)
        self.assertEqual(stored["footprint_height_mm"], 50)
        self.assertEqual(stored["color"], "Roble")
        self.assertEqual(stored["grain_axis_composition"], "y")

    def test_grain_axis_helpers_and_composition_summary(self) -> None:
        self.assertEqual(local_grain_axis("horizontal"), "x")
        self.assertEqual(local_grain_axis("vertical"), "y")
        self.assertEqual(composition_grain_axis("x", 90), "y")
        self.assertEqual(composition_grain_axis("y", 180), "y")

        self.assertEqual(
            collect_en_juego_composition_data({})["composition_grain_axis"],
            "none",
        )
        self.assertEqual(
            collect_en_juego_composition_data({"P1#1": {"grain_axis_composition": "x"}})["composition_grain_direction"],
            "2",
        )
        self.assertEqual(
            collect_en_juego_composition_data(
                {
                    "P1#1": {"grain_axis_composition": "x"},
                    "P2#1": {"grain_axis_composition": "y"},
                }
            )["composition_grain_status"],
            "mixed",
        )
