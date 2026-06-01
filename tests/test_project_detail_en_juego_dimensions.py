import unittest

from app.project_detail_en_juego_dimensions import EnJuegoDimensionAnnotator


class FakeScene:
    def __init__(self):
        self.removed = []

    def removeItem(self, item):
        self.removed.append(item)


class EnJuegoDimensionAnnotatorTests(unittest.TestCase):
    def test_label_uses_compact_number_callback(self):
        annotator = EnJuegoDimensionAnnotator(
            scene=FakeScene(),
            parent_dialog=None,
            item_by_instance_id={},
            effective_piece_spacing=lambda: 10.0,
            auto_spacing_adjustment_state={},
            update_scene_bounds=lambda: None,
            compact_number=lambda value: f"compact:{value}",
        )

        self.assertEqual(annotator.label(-12.34), "compact:12.3 mm")

    def test_clear_removes_tracked_annotation_items(self):
        scene = FakeScene()
        annotator = EnJuegoDimensionAnnotator(
            scene=scene,
            parent_dialog=None,
            item_by_instance_id={},
            effective_piece_spacing=lambda: 10.0,
            auto_spacing_adjustment_state={},
            update_scene_bounds=lambda: None,
            compact_number=str,
        )
        annotator.items.extend(["line", "label"])

        annotator.clear()

        self.assertEqual(scene.removed, ["line", "label"])
        self.assertEqual(annotator.items, [])


if __name__ == "__main__":
    unittest.main()
