from __future__ import annotations

import unittest
from pathlib import Path

from app.project_detail_drawings import (
    build_piece_drawing_path,
    refresh_piece_drawing_file,
    remove_piece_drawing_file,
)


class ProjectDetailDrawingsTests(unittest.TestCase):
    def test_build_piece_drawing_path_uses_sanitized_name(self) -> None:
        drawing_path = build_piece_drawing_path(Path("Modulo"), {"name": "Pieza 1/2", "id": "P1"})

        self.assertEqual(drawing_path, Path("Modulo") / "Pieza_1_2.svg")

    def test_build_piece_drawing_path_falls_back_to_id_and_default_name(self) -> None:
        self.assertEqual(build_piece_drawing_path(Path("Modulo"), {"id": "P1"}), Path("Modulo") / "P1.svg")
        self.assertEqual(build_piece_drawing_path(Path("Modulo"), {}), Path("Modulo") / "pieza.svg")

    def test_remove_piece_drawing_file_keeps_shared_drawing(self) -> None:
        with self.subTest("shared"):
            module_path = self._make_temp_module()
            drawing_path = module_path / "P1.svg"
            drawing_path.write_text("<svg />", encoding="utf-8")
            remove_piece_drawing_file(
                module_path,
                {"id": "P1", "source": ""},
                [{"id": "P1", "source": "P1.pgmx"}],
            )
            self.assertTrue(drawing_path.exists())

        with self.subTest("unshared"):
            module_path = self._make_temp_module()
            drawing_path = module_path / "P1.svg"
            drawing_path.write_text("<svg />", encoding="utf-8")
            remove_piece_drawing_file(module_path, {"id": "P1", "source": ""}, [])
            self.assertFalse(drawing_path.exists())

    def test_refresh_piece_drawing_file_removes_drawing_without_source(self) -> None:
        module_path = self._make_temp_module()
        drawing_path = module_path / "P1.svg"
        drawing_path.write_text("<svg />", encoding="utf-8")

        result = refresh_piece_drawing_file(
            None,
            None,
            module_path,
            {"id": "P1", "source": ""},
            [],
            lambda row: row,
        )

        self.assertIsNone(result)
        self.assertFalse(drawing_path.exists())

    def _make_temp_module(self) -> Path:
        temp_dir = self.addCleanupTempDir()
        return temp_dir

    def addCleanupTempDir(self) -> Path:
        import tempfile

        temp_dir = tempfile.TemporaryDirectory(prefix="prodaction_project_detail_drawings_")
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)
