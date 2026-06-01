import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.project_detail_module_persistence import (
    build_module_settings_payload,
    persist_inspected_module_config,
    sync_piece_program_dimensions_from_rows,
)
from core.model import ModuleData, Project


class ProjectDetailModulePersistenceTests(unittest.TestCase):
    def test_build_module_settings_payload_normalizes_dimensions_and_text(self):
        payload = build_module_settings_payload(
            x="100,0",
            y="100,125",
            z="",
            herrajes_y_accesorios="  tirador  ",
            guias_y_bisagras="  guia  ",
            detalles_de_obra=None,
        )

        self.assertEqual(payload["x"], 100)
        self.assertEqual(payload["y"], 100.12)
        self.assertEqual(payload["z"], "")
        self.assertEqual(payload["herrajes_y_accesorios"], "tirador")
        self.assertEqual(payload["guias_y_bisagras"], "guia")
        self.assertEqual(payload["detalles_de_obra"], "")

    def test_sync_piece_program_dimensions_from_rows_writes_values_back(self):
        rows = [{"id": "P1"}]
        cache = {}
        calls = []

        def build_piece(_row):
            return SimpleNamespace(program_width=None, program_height=None, program_thickness=None)

        def persist_program_dimensions(project, piece, module_path, cache=None):
            calls.append((project, module_path, cache))
            piece.program_width = 10
            piece.program_height = 20
            piece.program_thickness = 18

        sync_piece_program_dimensions_from_rows(
            project="project",
            module_path=Path("Modulo"),
            piece_rows=rows,
            build_piece_from_row=build_piece,
            cache=cache,
            persist_program_dimensions=persist_program_dimensions,
        )

        self.assertEqual(rows[0]["program_width"], 10)
        self.assertEqual(rows[0]["program_height"], 20)
        self.assertEqual(rows[0]["program_thickness"], 18)
        self.assertEqual(calls, [("project", Path("Modulo"), cache)])

    def test_persist_inspected_module_config_updates_config_module_and_callbacks(self):
        with tempfile.TemporaryDirectory(prefix="prodaction_module_persistence_") as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            project = Project(name="Proyecto", root_directory=temp_dir)
            selected_module = ModuleData(name="Modulo", path=temp_dir)
            rows = [
                {
                    "id": "P1",
                    "name": "Pieza",
                    "quantity": "",
                    "height": "100",
                    "width": "200",
                    "thickness": "18",
                    "excel": True,
                }
            ]
            events = []

            def build_piece(row):
                return SimpleNamespace(
                    program_width=None,
                    program_height=None,
                    program_thickness=None,
                )

            def persist_program_dimensions(_project, piece, _module_path, cache=None):
                piece.program_width = 100
                piece.program_height = 200
                piece.program_thickness = 18

            persist_inspected_module_config(
                project=project,
                selected_module=selected_module,
                config_path=config_path,
                config_data={},
                piece_rows=rows,
                module_settings={"x": 1},
                module_quantity="3",
                module_path=Path(temp_dir),
                build_piece_from_row=build_piece,
                program_dimensions_cache={},
                write_locale_config_files=lambda: events.append("locale"),
                save_project=lambda saved_project: events.append(saved_project.name),
                on_module_updated=lambda: events.append("updated"),
                generated_at="2026-01-02 03:04:05",
                persist_program_dimensions=persist_program_dimensions,
            )

            self.assertEqual(selected_module.quantity, 3)
            self.assertEqual(rows[0]["quantity"], 1)
            self.assertEqual(rows[0]["program_width"], 100)
            self.assertNotIn("excel", rows[0])
            self.assertEqual(len(selected_module.pieces), 1)
            self.assertEqual(events, ["locale", "Proyecto", "updated"])
            self.assertIn('"generated_at": "2026-01-02 03:04:05"', config_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
