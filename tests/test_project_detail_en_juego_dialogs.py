import unittest

from app.project_detail_en_juego_dialogs import (
    EMPTY_TOOL_LABEL,
    en_juego_selected_tool_index,
    en_juego_tool_combo_entries,
    populate_en_juego_tool_combo,
    set_widgets_enabled,
)


class FakeCombo:
    def __init__(self):
        self.items = []
        self.current_index = None
        self.enabled = True

    def addItem(self, label, value):
        self.items.append((label, value))

    def count(self):
        return len(self.items)

    def setCurrentIndex(self, index):
        self.current_index = index

    def setEnabled(self, enabled):
        self.enabled = enabled


class FakeWidget:
    def __init__(self):
        self.enabled = None

    def setEnabled(self, enabled):
        self.enabled = enabled


class EnJuegoDialogHelpersTests(unittest.TestCase):
    def test_tool_entries_preserve_labels_and_use_fallbacks(self):
        entries = en_juego_tool_combo_entries(
            [
                {"label": "Fresa 8", "tool_id": "T8"},
                {"tool_name": "Helicoidal", "tool_id": "TH"},
                {"tool_id": "TID"},
                {"tool_id": ""},
            ]
        )

        self.assertEqual(
            entries,
            [
                ("Fresa 8", "T8"),
                ("Helicoidal", "TH"),
                ("TID", "TID"),
                ("(herramienta sin nombre)", ""),
            ],
        )

    def test_selected_tool_index_matches_trimmed_ids_and_falls_back_to_first(self):
        tools = [{"tool_id": "A"}, {"tool_id": " B "}]

        self.assertEqual(en_juego_selected_tool_index(tools, "B"), 1)
        self.assertEqual(en_juego_selected_tool_index(tools, "missing"), 0)

    def test_populate_tool_combo_selects_existing_tool(self):
        combo = FakeCombo()

        populate_en_juego_tool_combo(
            combo,
            [{"label": "Uno", "tool_id": "1"}, {"label": "Dos", "tool_id": "2"}],
            "2",
        )

        self.assertEqual(combo.items, [("Uno", "1"), ("Dos", "2")])
        self.assertEqual(combo.current_index, 1)
        self.assertTrue(combo.enabled)

    def test_populate_tool_combo_disables_empty_combo(self):
        combo = FakeCombo()

        populate_en_juego_tool_combo(combo, [], "")

        self.assertEqual(combo.items, [(EMPTY_TOOL_LABEL, "")])
        self.assertIsNone(combo.current_index)
        self.assertFalse(combo.enabled)

    def test_set_widgets_enabled_forwards_boolean_state(self):
        widgets = [FakeWidget(), FakeWidget()]

        set_widgets_enabled(widgets, True)
        self.assertEqual([widget.enabled for widget in widgets], [True, True])

        set_widgets_enabled(widgets, False)
        self.assertEqual([widget.enabled for widget in widgets], [False, False])


if __name__ == "__main__":
    unittest.main()
