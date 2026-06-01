from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.model import Project
from core.production_sheet_images import (
    en_juego_sheet_replacement_enabled,
    normalize_en_juego_sheet_cut_mode,
    resolve_en_juego_output_path,
    sanitize_filename,
)


class ProductionSheetImagesTests(unittest.TestCase):
    def test_sanitize_filename_keeps_stable_fallback(self) -> None:
        self.assertEqual(sanitize_filename("A/B:C"), "A_B_C")
        self.assertEqual(sanitize_filename("..."), "pieza")

    def test_en_juego_replacement_requires_nesting_and_included_piece(self) -> None:
        self.assertEqual(normalize_en_juego_sheet_cut_mode("corte nesting"), "nesting")
        self.assertTrue(
            en_juego_sheet_replacement_enabled(
                {"en_juego_settings": {"cut_mode": "nesting"}},
                [{"en_juego": True, "include_in_sheet": True}],
            )
        )
        self.assertFalse(
            en_juego_sheet_replacement_enabled(
                {"en_juego_settings": {"cut_mode": "manual"}},
                [{"en_juego": True, "include_in_sheet": True}],
            )
        )

    def test_resolve_en_juego_output_path_checks_config_relative_to_module(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            module_dir = Path(temp_dir) / "Modulo"
            module_dir.mkdir()
            output_path = module_dir / "nested" / "out.pgmx"
            output_path.parent.mkdir()
            output_path.write_text("pgmx", encoding="utf-8")
            project = Project(name="Demo", root_directory=temp_dir)

            resolved = resolve_en_juego_output_path(
                project,
                module_dir,
                "Modulo",
                {"en_juego_output_path": "nested/out.pgmx"},
            )

        self.assertEqual(resolved, output_path)


if __name__ == "__main__":
    unittest.main()
