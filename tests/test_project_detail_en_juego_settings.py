import unittest

from app.project_detail_en_juego_settings import (
    apply_en_juego_division_dialog_settings,
    apply_en_juego_squaring_dialog_settings,
    division_tool_hint_text,
    en_juego_depth_role_text,
    normalize_en_juego_dialog_settings,
    squaring_tool_hint_text,
)


class EnJuegoSettingsTests(unittest.TestCase):
    def test_depth_role_text_and_tool_hints(self):
        self.assertEqual(
            en_juego_depth_role_text(True, operation_label="división"),
            "Profundidad extra",
        )
        self.assertEqual(
            en_juego_depth_role_text(False, operation_label="escuadrado"),
            "Profundidad de escuadrado",
        )
        self.assertEqual(
            division_tool_hint_text(
                {"tool_type": "Fresa Helicoidal"},
                {"cutting_tool_id": "", "cutting_tool_diameter": 8},
                material_thickness_mm=18.0,
            ),
            "Herramienta preferente para dividir En-Juego. "
            "La separacion minima entre piezas contiguas sera de 8 mm.",
        )
        self.assertEqual(
            division_tool_hint_text(
                {"tool_type": "Fresa"},
                {"cutting_tool_id": "", "cutting_tool_diameter": 0},
                material_thickness_mm=18.0,
            ),
            "No hay una herramienta de corte disponible para definir la separacion.",
        )
        self.assertEqual(
            squaring_tool_hint_text({"diameter": "12"}),
            "Herramienta de escuadrado seleccionada: Ø 12 mm.",
        )
        self.assertEqual(
            squaring_tool_hint_text({"diameter": ""}),
            "No hay una herramienta disponible para el escuadrado.",
        )

    def test_apply_division_dialog_settings_updates_tool_and_cutting_fields(self):
        selected_tool = {
            "tool_id": "T1",
            "tool_code": "101",
            "tool_name": "Helicoidal",
            "diameter": "8",
        }

        updated = apply_en_juego_division_dialog_settings(
            {"cutting_depth_value": 1.0},
            selected_tool=selected_tool,
            origin_x="10",
            origin_y="20",
            origin_z="30",
            cutting_is_through=False,
            cutting_depth_value="5",
            cutting_multipass_enabled=True,
            cutting_path_mode="Bidirectional",
            cutting_pocket_depth="2.5",
            cutting_last_pocket="1.5",
            approach_enabled=True,
            approach_type="Line",
            approach_radius_multiplier="3",
            approach_mode="Down",
            retract_enabled=True,
            retract_type="Arc",
            retract_radius_multiplier="4",
            retract_mode="Up",
        )

        self.assertEqual(updated["origin_x"], 10)
        self.assertEqual(updated["origin_y"], 20)
        self.assertEqual(updated["origin_z"], 30)
        self.assertEqual(updated["cutting_tool_id"], "T1")
        self.assertEqual(updated["cutting_tool_code"], "101")
        self.assertEqual(updated["cutting_tool_name"], "Helicoidal")
        self.assertEqual(updated["cutting_tool_diameter"], 8)
        self.assertFalse(updated["cutting_is_through"])
        self.assertEqual(updated["cutting_depth_value"], 5)
        self.assertTrue(updated["cutting_multipass_enabled"])
        self.assertEqual(updated["cutting_path_mode"], "Bidirectional")
        self.assertEqual(updated["cutting_pocket_depth"], 2.5)
        self.assertEqual(updated["cutting_last_pocket"], 1.5)
        self.assertTrue(updated["approach_enabled"])
        self.assertEqual(updated["approach_type"], "Line")
        self.assertEqual(updated["approach_radius_multiplier"], 3)
        self.assertEqual(updated["approach_mode"], "Down")
        self.assertTrue(updated["retract_enabled"])
        self.assertEqual(updated["retract_type"], "Arc")
        self.assertEqual(updated["retract_radius_multiplier"], 4)
        self.assertEqual(updated["retract_mode"], "Up")

    def test_apply_squaring_dialog_settings_updates_tool_and_strategy_fields(self):
        selected_tool = {
            "tool_id": "SQ",
            "tool_code": "202",
            "tool_name": "Escuadradora",
            "diameter": "12",
        }

        updated = apply_en_juego_squaring_dialog_settings(
            {"squaring_depth_value": 1.0},
            selected_tool=selected_tool,
            squaring_is_through=True,
            squaring_depth_value="6",
            squaring_approach_enabled=True,
            squaring_approach_type="Line",
            squaring_approach_radius_multiplier="2.2",
            squaring_approach_mode="Quote",
            squaring_retract_enabled=False,
            squaring_retract_type="Arc",
            squaring_retract_radius_multiplier="3.3",
            squaring_retract_mode="Up",
            squaring_direction="CCW",
            squaring_unidirectional_multipass=True,
            squaring_pocket_depth="1.2",
            squaring_last_pocket="0.8",
        )

        self.assertEqual(updated["squaring_tool_id"], "SQ")
        self.assertEqual(updated["squaring_tool_code"], "202")
        self.assertEqual(updated["squaring_tool_name"], "Escuadradora")
        self.assertEqual(updated["squaring_tool_diameter"], 12)
        self.assertTrue(updated["squaring_is_through"])
        self.assertEqual(updated["squaring_depth_value"], 6)
        self.assertTrue(updated["squaring_approach_enabled"])
        self.assertEqual(updated["squaring_approach_type"], "Line")
        self.assertEqual(updated["squaring_approach_radius_multiplier"], 2.2)
        self.assertEqual(updated["squaring_approach_mode"], "Quote")
        self.assertFalse(updated["squaring_retract_enabled"])
        self.assertEqual(updated["squaring_retract_type"], "Arc")
        self.assertEqual(updated["squaring_retract_radius_multiplier"], 3.3)
        self.assertEqual(updated["squaring_retract_mode"], "Up")
        self.assertEqual(updated["squaring_direction"], "CCW")
        self.assertTrue(updated["squaring_unidirectional_multipass"])
        self.assertEqual(updated["squaring_pocket_depth"], 1.2)
        self.assertEqual(updated["squaring_last_pocket"], 0.8)

    def test_normalize_dialog_settings_applies_controls_and_defaults(self):
        settings = {
            "cutting_is_through": "no",
            "cutting_depth_value": "-2",
            "approach_type": "line",
            "approach_mode": "down",
            "retract_type": "arc",
            "retract_mode": "up",
            "squaring_approach_type": "line",
            "squaring_retract_type": "line",
        }

        normalized = normalize_en_juego_dialog_settings(
            settings,
            cut_mode="nesting",
            origin_x="10.5",
            origin_y="bad",
            origin_z="3",
            division_squaring_order="squaring_then_division",
        )

        self.assertEqual(normalized["cut_mode"], "nesting")
        self.assertEqual(normalized["origin_x"], 10.5)
        self.assertEqual(normalized["origin_y"], 0)
        self.assertEqual(normalized["origin_z"], 3)
        self.assertEqual(normalized["division_squaring_order"], "squaring_then_division")
        self.assertFalse(normalized["cutting_is_through"])
        self.assertEqual(normalized["cutting_depth_value"], 1)
        self.assertEqual(normalized["approach_type"], "Line")
        self.assertEqual(normalized["approach_mode"], "Down")
        self.assertEqual(normalized["retract_type"], "Arc")
        self.assertEqual(normalized["retract_mode"], "Up")
        self.assertEqual(normalized["squaring_approach_type"], "Line")
        self.assertEqual(normalized["squaring_retract_type"], "Line")
        self.assertIn("cutting_tool_id", normalized)
        self.assertIn("squaring_tool_id", normalized)

    def test_normalize_dialog_settings_rejects_unknown_modes_to_safe_defaults(self):
        normalized = normalize_en_juego_dialog_settings(
            {
                "approach_type": "weird",
                "approach_mode": "weird",
                "retract_type": "weird",
                "retract_mode": "weird",
                "squaring_approach_mode": "weird",
                "squaring_retract_mode": "weird",
            },
            cut_mode="manual",
            origin_x="",
            origin_y="",
            origin_z="",
            division_squaring_order="unknown",
        )

        self.assertEqual(normalized["cut_mode"], "manual")
        self.assertEqual(normalized["division_squaring_order"], "division_then_squaring")
        self.assertEqual(normalized["approach_type"], "Line")
        self.assertEqual(normalized["approach_mode"], "Down")
        self.assertEqual(normalized["retract_type"], "Line")
        self.assertEqual(normalized["retract_mode"], "Up")
        self.assertEqual(normalized["squaring_approach_mode"], "Down")
        self.assertEqual(normalized["squaring_retract_mode"], "Up")


if __name__ == "__main__":
    unittest.main()
