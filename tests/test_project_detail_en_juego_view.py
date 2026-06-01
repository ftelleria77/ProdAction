import unittest

from PySide6.QtCore import Qt

from app.project_detail_en_juego_view import (
    fit_scene_items_in_view,
    focus_en_juego_piece_from_list,
    make_cosmetic_pen,
    rotate_en_juego_scene_item,
    selected_en_juego_scene_item,
    set_padded_scene_rect,
)


class FakeRect:
    def __init__(self, *, null: bool = False, adjusted_value=None):
        self._null = null
        self.adjusted_calls = []
        self.adjusted_value = adjusted_value or object()

    def isNull(self):
        return self._null

    def adjusted(self, *args):
        self.adjusted_calls.append(args)
        return self.adjusted_value


class FakeScene:
    def __init__(self, rect):
        self.rect = rect
        self.scene_rect = None
        self.selection_cleared = False
        self.selected_items = []

    def itemsBoundingRect(self):
        return self.rect

    def setSceneRect(self, rect):
        self.scene_rect = rect

    def selectedItems(self):
        return self.selected_items

    def clearSelection(self):
        self.selection_cleared = True


class FakeView:
    def __init__(self):
        self.fit_calls = []
        self.centered_on = None

    def fitInView(self, rect, aspect_mode):
        self.fit_calls.append((rect, aspect_mode))

    def centerOn(self, item):
        self.centered_on = item


class FakeListItem:
    def __init__(self, value):
        self.value = value

    def data(self, role):
        return self.value if role == Qt.UserRole else None


class FakeList:
    def __init__(self, current_item=None):
        self._current_item = current_item

    def currentItem(self):
        return self._current_item


class FakeSceneItem:
    def __init__(self, key="", rotation=0):
        self.key = key
        self._rotation = rotation
        self.selected = False

    def data(self, role):
        return self.key if role == 0 else None

    def setSelected(self, selected):
        self.selected = selected

    def rotation(self):
        return self._rotation

    def setRotation(self, rotation):
        self._rotation = rotation


class EnJuegoViewTests(unittest.TestCase):
    def test_make_cosmetic_pen_configures_width_and_dash_style(self):
        pen = make_cosmetic_pen("#123456", 2.5, dashed=True)

        self.assertTrue(pen.isCosmetic())
        self.assertAlmostEqual(pen.widthF(), 2.5)
        self.assertEqual(pen.style(), Qt.DashLine)

    def test_set_padded_scene_rect_applies_symmetric_padding(self):
        padded_rect = object()
        rect = FakeRect(adjusted_value=padded_rect)
        scene = FakeScene(rect)

        result = set_padded_scene_rect(scene, 12.5)

        self.assertTrue(result)
        self.assertEqual(rect.adjusted_calls, [(-12.5, -12.5, 12.5, 12.5)])
        self.assertIs(scene.scene_rect, padded_rect)

    def test_set_padded_scene_rect_skips_empty_scene(self):
        rect = FakeRect(null=True)
        scene = FakeScene(rect)

        result = set_padded_scene_rect(scene, 12.5)

        self.assertFalse(result)
        self.assertEqual(rect.adjusted_calls, [])
        self.assertIsNone(scene.scene_rect)

    def test_fit_scene_items_in_view_uses_padded_items_rect(self):
        padded_rect = object()
        rect = FakeRect(adjusted_value=padded_rect)
        scene = FakeScene(rect)
        view = FakeView()

        result = fit_scene_items_in_view(view, scene, padding_mm=20)

        self.assertTrue(result)
        self.assertEqual(rect.adjusted_calls, [(-20, -20, 20, 20)])
        self.assertEqual(view.fit_calls, [(padded_rect, Qt.KeepAspectRatio)])

    def test_fit_scene_items_in_view_skips_empty_scene(self):
        scene = FakeScene(FakeRect(null=True))
        view = FakeView()

        result = fit_scene_items_in_view(view, scene)

        self.assertFalse(result)
        self.assertEqual(view.fit_calls, [])

    def test_selected_scene_item_prefers_graphics_selection(self):
        selected_item = FakeSceneItem("P1#1")
        scene = FakeScene(FakeRect())
        scene.selected_items = [FakeSceneItem(""), selected_item]

        result = selected_en_juego_scene_item(
            scene,
            FakeList(FakeListItem("P2#1")),
            {"P2#1": FakeSceneItem("P2#1")},
        )

        self.assertIs(result, selected_item)

    def test_selected_scene_item_falls_back_to_current_list_item(self):
        fallback_item = FakeSceneItem("P2#1")
        scene = FakeScene(FakeRect())

        result = selected_en_juego_scene_item(
            scene,
            FakeList(FakeListItem("P2#1")),
            {"P2#1": fallback_item},
        )

        self.assertIs(result, fallback_item)

    def test_focus_piece_from_list_selects_and_centers_scene_item(self):
        scene = FakeScene(FakeRect())
        view = FakeView()
        scene_item = FakeSceneItem("P1#1")

        result = focus_en_juego_piece_from_list(
            scene,
            FakeList(FakeListItem("P1#1")),
            {"P1#1": scene_item},
            view,
        )

        self.assertTrue(result)
        self.assertTrue(scene.selection_cleared)
        self.assertTrue(scene_item.selected)
        self.assertIs(view.centered_on, scene_item)

    def test_rotate_scene_item_wraps_degrees(self):
        scene_item = FakeSceneItem("P1#1", rotation=315)

        self.assertEqual(rotate_en_juego_scene_item(scene_item, 90), 45)
        self.assertEqual(scene_item.rotation(), 45)


if __name__ == "__main__":
    unittest.main()
