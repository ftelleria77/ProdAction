from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import app.project_registry as project_registry
from app.project_store import _load_project, _save_project
from core.model import LocaleData, Project


class ProjectStoreTests(unittest.TestCase):
    def test_save_and_load_project_with_saved_module_config(self) -> None:
        original_registry = project_registry.PROJECT_REGISTRY
        with tempfile.TemporaryDirectory(prefix="prodaction_project_store_") as temp_dir:
            temp_path = Path(temp_dir)
            project_registry.PROJECT_REGISTRY = temp_path / "projects_list.json"
            try:
                project_root = temp_path / "DemoProject"
                project = Project(
                    name="Demo",
                    client="Cliente",
                    root_directory=str(project_root),
                    project_data_file="project.json",
                    locales=[LocaleData(name="Cocina", path="Cocina", modules_count=0)],
                )

                _save_project(project)

                locale_path = project_root / "Cocina"
                module_path = locale_path / "Modulo 1"
                module_path.mkdir(parents=True)
                (locale_path / "local_config.json").write_text(
                    json.dumps(
                        {
                            "locale_name": "Cocina",
                            "path": "Cocina",
                            "modules": [
                                {
                                    "name": "Modulo 1",
                                    "path": "Modulo 1",
                                    "quantity": 2,
                                }
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                (module_path / "module_config.json").write_text(
                    json.dumps(
                        {
                            "module": "Modulo 1",
                            "pieces": [
                                {
                                    "id": "P1",
                                    "name": "Pieza 1",
                                    "quantity": "3",
                                    "width": "100",
                                    "height": "200",
                                    "thickness": "18",
                                    "grain_direction": "longitudinal",
                                    "source": "P1.pgmx",
                                }
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

                loaded = _load_project("Demo")

                self.assertEqual(loaded.name, "Demo")
                self.assertEqual(loaded.client, "Cliente")
                self.assertEqual(len(loaded.locales), 1)
                self.assertEqual(loaded.locales[0].modules_count, 2)
                self.assertEqual(len(loaded.modules), 1)
                self.assertEqual(loaded.modules[0].name, "Modulo 1")
                self.assertEqual(loaded.modules[0].quantity, 2)
                self.assertEqual(len(loaded.modules[0].pieces), 1)
                self.assertEqual(loaded.modules[0].pieces[0].id, "P1")
                self.assertEqual(loaded.modules[0].pieces[0].quantity, 3)
                self.assertEqual(loaded.modules[0].pieces[0].cnc_source, "P1.pgmx")
            finally:
                project_registry.PROJECT_REGISTRY = original_registry
