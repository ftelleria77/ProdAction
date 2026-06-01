from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from core import production_sheet, summary
from core.model import ModuleData, Piece, Project


class SummaryExportsTests(unittest.TestCase):
    def test_export_summary_keeps_csv_contract_and_effective_quantity(self) -> None:
        project = Project(
            name="Demo",
            root_directory=".",
            modules=[
                ModuleData(
                    name="Manual",
                    path=".",
                    is_manual=True,
                    quantity=2,
                    pieces=[
                        Piece(id="M1", name="Manual 1", width=10, height=20, thickness=18, quantity=3),
                    ],
                ),
                ModuleData(
                    name="Auto",
                    path=".",
                    is_manual=False,
                    pieces=[
                        Piece(id="A1", width=30, height=40, thickness=18, quantity=1, grain_direction="alto"),
                        Piece(id="A0", width=1, height=1, thickness=0, quantity=1),
                    ],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = Path(temp_dir) / "resumen.csv"
            df = summary.export_summary(project, output_csv)
            saved = pd.read_csv(output_csv, sep=";")

        self.assertEqual(list(df["module"]), ["Auto", "Manual"])
        self.assertEqual(list(saved["quantity"]), [1, 6])
        self.assertEqual(list(saved["grain_direction"]), [1, 0])

    def test_summary_keeps_production_sheet_compatibility_facade(self) -> None:
        self.assertIs(summary.export_production_sheet, production_sheet.export_production_sheet)
        self.assertIs(summary.export_production_sheet_pdf, production_sheet.export_production_sheet_pdf)

    def test_export_production_sheet_writes_basic_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            module_dir = Path(temp_dir) / "Modulo"
            module_dir.mkdir()
            project = Project(
                name="Proyecto Demo",
                root_directory=temp_dir,
                client="Cliente Demo",
                modules=[
                    ModuleData(
                        name="Modulo",
                        path=str(module_dir),
                        quantity=2,
                        pieces=[
                            Piece(
                                id="P1",
                                name="Pieza 1",
                                width=100,
                                height=200,
                                thickness=18,
                                quantity=3,
                            ),
                        ],
                    ),
                ],
            )
            output_xlsx = Path(temp_dir) / "planilla.xlsx"

            production_sheet.export_production_sheet(project, output_xlsx)

            workbook = load_workbook(output_xlsx)
            sheet = workbook.active
            self.assertEqual(sheet["A1"].value, "Proyecto Demo")
            self.assertEqual(sheet["A2"].value, "Cliente: Cliente Demo")
            self.assertEqual(sheet["A6"].value, "Modulo")
            self.assertEqual(sheet["A8"].value, "Pieza 1")
            self.assertEqual(sheet["B8"].value, 6)


if __name__ == "__main__":
    unittest.main()
