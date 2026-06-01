from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.project_detail_programs import assign_program_source_to_row, clear_program_metadata


class ProjectDetailProgramsTests(unittest.TestCase):
    def test_assign_program_source_to_row_stores_relative_source_and_f6_companion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_project_detail_programs_") as temp_dir:
            module_path = Path(temp_dir)
            program_path = module_path / "P1.pgmx"
            companion_path = module_path / "P1F6.pgmx"
            program_path.write_text("<xml />", encoding="utf-8")
            companion_path.write_text("<xml />", encoding="utf-8")

            row = {}
            assign_program_source_to_row(row, str(program_path), module_path)

        self.assertEqual(row["source"], "P1.pgmx")
        self.assertEqual(row["f6_source"], "P1F6.pgmx")

    def test_clear_program_metadata_removes_derived_program_fields(self) -> None:
        row = {
            "source": "P1.pgmx",
            "f6_source": "P1F6.pgmx",
            "program_width": 100,
            "program_height": 200,
            "program_thickness": 18,
        }

        clear_program_metadata(row)

        self.assertEqual(row["source"], "P1.pgmx")
        self.assertIsNone(row["f6_source"])
        self.assertIsNone(row["program_width"])
        self.assertIsNone(row["program_height"])
        self.assertIsNone(row["program_thickness"])
