from __future__ import annotations

import json
import os
import tempfile
import unittest
import warnings

from cnc_traceability import viewer_xp as cnc


class CncTraceabilityHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            message=r"codecs\.open\(\) is deprecated.*",
        )

    def test_normalize_index_accepts_project_aliases(self) -> None:
        projects = cnc.normalize_index(
            {
                "projects": [
                    {
                        "name": "Proyecto A",
                        "client": "Cliente",
                        "source_folder": "origen",
                        "output_root": "salida",
                    }
                ]
            }
        )

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["project_name"], "Proyecto A")
        self.assertEqual(projects[0]["client_name"], "Cliente")
        self.assertTrue(projects[0]["source_folder"].endswith("origen"))
        self.assertTrue(projects[0]["cnc_output_root"].endswith("salida"))
        self.assertTrue(projects[0]["project_id"])

    def test_scan_iso_files_preserves_local_and_module_from_output_tree(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            module_dir = os.path.join(root, "Cocina", "Bajo mesada")
            os.makedirs(module_dir)
            iso_path = os.path.join(module_dir, "Pieza_001.iso")
            with open(iso_path, "w", encoding="utf-8") as handle:
                handle.write("ISO")
            with open(os.path.join(module_dir, "ignorado.txt"), "w", encoding="utf-8") as handle:
                handle.write("TXT")

            items = cnc.scan_iso_files(root)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Pieza_001.iso")
        self.assertEqual(items[0]["local_name"], "Cocina")
        self.assertEqual(items[0]["module_name"], "Bajo mesada")
        self.assertEqual(items[0]["rel_path"], os.path.join("Cocina", "Bajo mesada", "Pieza_001.iso"))

    def test_build_project_rows_resolves_piece_metadata_and_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            source_root = os.path.join(temp_root, "source")
            output_root = os.path.join(temp_root, "cnc")
            source_module = os.path.join(source_root, "Local", "Modulo")
            output_module = os.path.join(output_root, "Local", "Modulo")
            os.makedirs(source_module)
            os.makedirs(output_module)

            with open(os.path.join(output_module, "A001.iso"), "w", encoding="utf-8") as handle:
                handle.write("ISO")
            with open(os.path.join(source_module, "module_config.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "pieces": [
                            {
                                "id": "A001",
                                "name": "Costado",
                                "program_width": 400,
                                "program_height": 350,
                                "program_thickness": 18,
                                "observations": "Canto visto",
                            }
                        ]
                    },
                    handle,
                )

            project = cnc.normalize_project(
                {
                    "project_name": "Proyecto",
                    "source_folder": source_root,
                    "cnc_output_root": output_root,
                },
                0,
            )
            progress = cnc.progress_template(project)
            cnc.update_item_status(
                progress,
                os.path.join("Local", "Modulo", "A001.iso"),
                "A001.iso",
                "copiado_a_usbmix",
                {"observations": "Listo para ejecutar"},
            )

            rows = cnc.build_project_rows(project, progress)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["piece_name"], "Costado")
        self.assertEqual(rows[0]["dimensions"], "400 x 350 x 18")
        self.assertEqual(rows[0]["observations"], "Listo para ejecutar")
        self.assertEqual(rows[0]["state"], "copiado_a_usbmix")


if __name__ == "__main__":
    unittest.main()
