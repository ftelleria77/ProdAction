from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.project_detail_output import ProjectDetailOutputMixin
from core.model import LocaleData, ModuleData, Piece, Project


class _OutputHarness(ProjectDetailOutputMixin):
    def __init__(self, project: Project) -> None:
        self.project = project


class ProjectDetailOutputTests(unittest.TestCase):
    def test_safe_output_filename_removes_invalid_path_characters(self) -> None:
        harness = _OutputHarness(Project("Proyecto", root_directory="."))

        self.assertEqual(harness._safe_output_filename(' A<B:C* ', "fallback"), "A_B_C")
        self.assertEqual(harness._safe_output_filename("...", "fallback"), "fallback")

    def test_output_relative_path_keeps_project_internal_absolute_paths_relative(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_output_") as temp_dir:
            project_root = Path(temp_dir) / "Proyecto"
            nested_path = project_root / "Cocina" / "Modulo:1"
            harness = _OutputHarness(Project("Proyecto", root_directory=str(project_root)))

            self.assertEqual(
                harness._output_relative_path(str(nested_path), "Modulo"),
                Path("Cocina") / "Modulo_1",
            )

    def test_output_relative_path_falls_back_to_filename_for_external_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_output_") as temp_dir:
            project_root = Path(temp_dir) / "Proyecto"
            external_path = Path(temp_dir) / "Externo" / "Modulo.pgmx"
            harness = _OutputHarness(Project("Proyecto", root_directory=str(project_root)))

            self.assertEqual(harness._output_relative_path(str(external_path), "Modulo"), Path("Modulo.pgmx"))

    def test_module_cnc_output_dir_uses_module_relative_path_when_present(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_output_") as temp_dir:
            output_root = Path(temp_dir) / "Salida"
            project_root = Path(temp_dir) / "Proyecto Real"
            project = Project(
                "Proyecto",
                root_directory=str(project_root),
                locales=[LocaleData("Cocina", "Cocina")],
            )
            module = ModuleData(
                "Modulo Uno",
                path=str(project_root / "Cocina" / "Modulo Uno"),
                locale_name="Cocina",
                relative_path="Cocina/Modulo:Uno",
            )
            harness = _OutputHarness(project)

            self.assertEqual(
                harness._module_cnc_output_dir(project, output_root, module),
                output_root / "Proyecto Real" / "Cocina" / "Modulo_Uno",
            )

    def test_unique_iso_output_path_deduplicates_by_piece_label_and_suffix(self) -> None:
        harness = _OutputHarness(Project("Proyecto", root_directory="."))
        used_stems = {"pieza", "pieza_lateral"}
        piece = Piece(id="Lateral", name="Lateral", width=1, height=1, cnc_source="Pieza.pgmx")

        output_path = harness._unique_iso_output_path(
            Path("Salida"),
            Path("Pieza.pgmx"),
            used_stems,
            piece,
        )

        self.assertEqual(output_path, Path("Salida") / "Pieza_Lateral_2.iso")
        self.assertIn("pieza_lateral_2", used_stems)


if __name__ == "__main__":
    unittest.main()
