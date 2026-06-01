from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app.project_detail_selectors as selectors


class ProjectDetailSelectorsTests(unittest.TestCase):
    def test_available_items_uses_defaults_when_settings_are_missing(self) -> None:
        with mock.patch.object(selectors, "_read_app_settings", return_value={}):
            items = selectors._available_items(selectors.HERRAJES_SELECTOR_CONFIG)

        self.assertIn("Bisagras", items)
        self.assertIn("Cierre magnético", items)

    def test_available_items_normalizes_saved_entries(self) -> None:
        with mock.patch.object(
            selectors,
            "_read_app_settings",
            return_value={"available_herrajes": [" Bisagra ", "", 42]},
        ):
            items = selectors._available_items(selectors.HERRAJES_SELECTOR_CONFIG)

        self.assertEqual(items, ["Bisagra", "42"])

    def test_save_available_items_preserves_existing_settings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_project_detail_selectors_") as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            with mock.patch.object(
                selectors,
                "_read_app_settings",
                return_value={"existing": True},
            ), mock.patch.object(selectors, "APP_SETTINGS_FILE", settings_path):
                selectors._save_available_items(selectors.GUIAS_SELECTOR_CONFIG, ["Guía de bolas"])

            settings = json.loads(settings_path.read_text(encoding="utf-8"))

        self.assertEqual(settings["existing"], True)
        self.assertEqual(settings["available_guias"], ["Guía de bolas"])
