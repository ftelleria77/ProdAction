import json
import tempfile
import unittest
from pathlib import Path

from app.project_detail_color_changes import apply_scoped_color_change, is_same_module
from core.model import ModuleData, PIECE_GRAIN_CODE_NONE, Piece


class ProjectDetailColorChangesTests(unittest.TestCase):
    def test_piece_scope_changes_target_row_only(self):
        rows = [
            {"color": "Blanco", "grain_direction": "1"},
            {"color": "Roble", "grain_direction": "2"},
        ]
        persisted = []

        result = apply_scoped_color_change(
            project_modules=[],
            selected_module=ModuleData(name="A", path="A"),
            current_rows=rows,
            current_color="Blanco",
            new_color="Negro",
            scope="piece",
            target_row_index=1,
            force_no_grain=True,
            project_root=".",
            module_config_path=lambda _module: Path("missing.json"),
            persist_current_module=lambda: persisted.append("current"),
        )

        self.assertTrue(result.applied)
        self.assertEqual(rows[0]["color"], "Blanco")
        self.assertEqual(rows[1]["color"], "Negro")
        self.assertEqual(rows[1]["grain_direction"], PIECE_GRAIN_CODE_NONE)
        self.assertEqual(persisted, ["current"])

    def test_piece_scope_rejects_missing_target(self):
        persisted = []

        result = apply_scoped_color_change(
            project_modules=[],
            selected_module=ModuleData(name="A", path="A"),
            current_rows=[],
            current_color="Blanco",
            new_color="Negro",
            scope="piece",
            target_row_index=-1,
            force_no_grain=False,
            project_root=".",
            module_config_path=lambda _module: Path("missing.json"),
            persist_current_module=lambda: persisted.append("current"),
        )

        self.assertFalse(result.applied)
        self.assertEqual(persisted, [])

    def test_locale_scope_updates_current_rows_matching_modules_and_configs(self):
        with tempfile.TemporaryDirectory(prefix="prodaction_color_changes_") as temp_dir:
            root = Path(temp_dir)
            selected = ModuleData(name="A", path=str(root / "Cocina" / "A"), relative_path="Cocina/A")
            same_locale = ModuleData(
                name="B",
                path=str(root / "Cocina" / "B"),
                relative_path="Cocina/B",
                pieces=[Piece(id="P1", name="P1", width=1, height=1, color="Blanco", grain_direction="1")],
            )
            other_locale = ModuleData(
                name="C",
                path=str(root / "Living" / "C"),
                relative_path="Living/C",
                pieces=[Piece(id="P2", name="P2", width=1, height=1, color="Blanco", grain_direction="1")],
            )
            config_path = root / "same_locale_config.json"
            config_path.write_text(
                json.dumps({"pieces": [{"color": "Blanco", "grain_direction": "1"}]}),
                encoding="utf-8",
            )
            current_rows = [
                {"color": "Blanco", "grain_direction": "1"},
                {"color": "Roble", "grain_direction": "2"},
            ]
            persisted = []

            result = apply_scoped_color_change(
                project_modules=[selected, same_locale, other_locale],
                selected_module=selected,
                current_rows=current_rows,
                current_color="Blanco",
                new_color="Negro",
                scope="locale",
                target_row_index=None,
                force_no_grain=True,
                project_root=root,
                module_config_path=lambda module: config_path if module is same_locale else root / "missing.json",
                persist_current_module=lambda: persisted.append("current"),
                generated_at="2026-01-02 03:04:05",
            )

            self.assertTrue(result.applied)
            self.assertEqual(current_rows[0]["color"], "Negro")
            self.assertEqual(current_rows[0]["grain_direction"], PIECE_GRAIN_CODE_NONE)
            self.assertEqual(current_rows[1]["color"], "Roble")
            self.assertEqual(same_locale.pieces[0].color, "Negro")
            self.assertEqual(same_locale.pieces[0].grain_direction, PIECE_GRAIN_CODE_NONE)
            self.assertEqual(other_locale.pieces[0].color, "Blanco")
            self.assertEqual(persisted, ["current"])

            updated_config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_config["pieces"][0]["color"], "Negro")
            self.assertEqual(updated_config["pieces"][0]["grain_direction"], PIECE_GRAIN_CODE_NONE)
            self.assertEqual(updated_config["generated_at"], "2026-01-02 03:04:05")

    def test_is_same_module_uses_relative_path_when_available(self):
        self.assertTrue(
            is_same_module(
                ModuleData(name="A", path="old", relative_path="Cocina/A"),
                ModuleData(name="A", path="new", relative_path="Cocina/A"),
            )
        )
        self.assertFalse(
            is_same_module(
                ModuleData(name="A", path="old", relative_path="Cocina/A"),
                ModuleData(name="B", path="old", relative_path="Cocina/B"),
            )
        )


if __name__ == "__main__":
    unittest.main()
