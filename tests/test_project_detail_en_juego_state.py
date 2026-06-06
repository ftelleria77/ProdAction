from __future__ import annotations

import unittest

from app.project_detail_en_juego_state import (
    clear_persistent_en_juego_info,
    configurable_en_juego_rows,
    config_section_has_data,
    en_juego_material_thickness_mm,
    has_configurable_en_juego_pieces,
    has_persistent_en_juego_info,
    normalized_en_juego_layout,
    store_en_juego_composition_layout,
    sync_en_juego_observations,
)
from app.settings import _default_en_juego_settings


class ProjectDetailEnJuegoStateTests(unittest.TestCase):
    def test_has_configurable_en_juego_pieces_checks_rows(self) -> None:
        self.assertFalse(has_configurable_en_juego_pieces([{"en_juego": False}]))
        self.assertTrue(has_configurable_en_juego_pieces([{"en_juego": False}, {"en_juego": True}]))

    def test_configurable_en_juego_rows_requires_flag_and_valid_thickness(self) -> None:
        rows = [
            {"id": "A", "en_juego": True, "thickness": "18"},
            {"id": "B", "en_juego": True, "thickness": ""},
            {"id": "C", "en_juego": False, "thickness": "18"},
        ]

        self.assertEqual(
            configurable_en_juego_rows(rows, lambda value: bool(value)),
            [rows[0]],
        )

    def test_en_juego_material_thickness_uses_max_valid_thickness(self) -> None:
        self.assertEqual(
            en_juego_material_thickness_mm(
                [
                    {"thickness": "18"},
                    {"thickness": "25.5"},
                    {"thickness": "bad"},
                ]
            ),
            25.5,
        )
        self.assertEqual(en_juego_material_thickness_mm([]), 0.0)

    def test_normalized_en_juego_layout_accepts_only_dicts(self) -> None:
        layout = {"P1": {"x": 1}}

        self.assertIs(normalized_en_juego_layout({"en_juego_layout": layout}), layout)
        self.assertEqual(normalized_en_juego_layout({"en_juego_layout": []}), {})
        self.assertEqual(normalized_en_juego_layout({}), {})

    def test_store_en_juego_composition_layout_updates_layout_and_summary(self) -> None:
        config = {}
        layout = {"P1#1": {"grain_axis_composition": "x"}}

        store_en_juego_composition_layout(config, layout)

        self.assertIs(config["en_juego_layout"], layout)
        self.assertEqual(config["en_juego_composition"]["layout_version"], 2)
        self.assertEqual(config["en_juego_composition"]["composition_grain_axis"], "x")

    def test_config_section_has_data_handles_empty_containers_and_scalars(self) -> None:
        self.assertFalse(config_section_has_data({}))
        self.assertFalse(config_section_has_data([]))
        self.assertFalse(config_section_has_data(""))
        self.assertTrue(config_section_has_data({"x": 1}))
        self.assertTrue(config_section_has_data("archivo.pgmx"))

    def test_has_persistent_en_juego_info_detects_layout_output_and_non_default_settings(self) -> None:
        self.assertFalse(has_persistent_en_juego_info({"en_juego_settings": _default_en_juego_settings()}))
        self.assertTrue(has_persistent_en_juego_info({"en_juego_layout": {"P1": {"x": 1}}}))
        self.assertTrue(has_persistent_en_juego_info({"en_juego_output_path": "out.pgmx"}))

        settings = _default_en_juego_settings()
        settings["origin_x"] = 10
        self.assertTrue(has_persistent_en_juego_info({"en_juego_settings": settings}))

    def test_clear_persistent_en_juego_info_resets_config_sections(self) -> None:
        config = {
            "en_juego_layout": {"P1": {}},
            "en_juego_composition": {"items": []},
            "en_juego_output_path": "out.pgmx",
            "en_juego_settings": {"origin_x": 10},
        }

        clear_persistent_en_juego_info(config)

        self.assertEqual(config["en_juego_layout"], {})
        self.assertEqual(config["en_juego_composition"], {})
        self.assertNotIn("en_juego_output_path", config)
        self.assertEqual(config["en_juego_settings"], _default_en_juego_settings())

    def test_sync_en_juego_observations_updates_rows(self) -> None:
        rows = [
            {"observations": "", "en_juego": True},
            {"observations": "En-Juego", "en_juego": False},
        ]

        sync_en_juego_observations(rows)

        self.assertIn("En-Juego", rows[0]["observations"])
        self.assertNotIn("En-Juego", rows[1]["observations"])
