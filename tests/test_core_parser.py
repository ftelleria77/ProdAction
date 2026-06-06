from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.model import PIECE_GRAIN_CODE_HEIGHT, PIECE_GRAIN_CODE_WIDTH
from core.parser import (
    inspect_project_layout,
    load_module_summary,
    parse_cnc_file,
    scan_project,
    scan_project_structure,
)


class CoreParserTests(unittest.TestCase):
    def test_load_module_summary_respects_header_names_and_column_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_parser_") as temp_dir:
            module_dir = Path(temp_dir) / "Modulo"
            module_dir.mkdir()
            (module_dir / "resumen.csv").write_text(
                "\n".join(
                    [
                        "piece_name;source;color;thickness;grain_direction;quantity;height;width;piece_id;unused;piece_type",
                        "Lateral A;programas/A.pgmx;Roble;18,5;alto;2;700;300;P1;x;F1",
                    ]
                ),
                encoding="utf-8",
            )

            metadata = load_module_summary(module_dir)

        self.assertEqual(set(metadata), {"P1"})
        self.assertEqual(metadata["P1"]["name"], "Lateral A")
        self.assertEqual(metadata["P1"]["source"], "programas/A.pgmx")
        self.assertEqual(metadata["P1"]["piece_type"], "F1")
        self.assertEqual(metadata["P1"]["quantity"], "2")
        self.assertEqual(float(metadata["P1"]["width"]), 300.0)
        self.assertEqual(float(metadata["P1"]["height"]), 700.0)
        self.assertEqual(float(metadata["P1"]["thickness"]), 18.5)
        self.assertEqual(metadata["P1"]["grain_direction"], PIECE_GRAIN_CODE_HEIGHT)

    def test_load_module_summary_keeps_legacy_positional_csv_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_parser_") as temp_dir:
            module_dir = Path(temp_dir) / "Modulo"
            module_dir.mkdir()
            (module_dir / "piezas.csv").write_text(
                "\n".join(
                    [
                        "P1;F1;Lateral A;2;x;700;300;18;Blanco;2;A.pgmx",
                        "P1;F1;Lateral A;3;x;700;300;18;Blanco;2;",
                    ]
                ),
                encoding="utf-8",
            )

            metadata = load_module_summary(module_dir)

        self.assertEqual(metadata["P1"]["quantity"], "5")
        self.assertEqual(metadata["P1"]["name"], "Lateral A")
        self.assertEqual(metadata["P1"]["source"], "A.pgmx")
        self.assertEqual(metadata["P1"]["grain_direction"], PIECE_GRAIN_CODE_WIDTH)
        self.assertEqual(float(metadata["P1"]["width"]), 300.0)
        self.assertEqual(float(metadata["P1"]["height"]), 700.0)

    def test_parse_cnc_file_uses_metadata_when_program_contains_piece_lines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_parser_") as temp_dir:
            program_path = Path(temp_dir) / "pieza.pgmx"
            program_path.write_text("PIEZA P1 300 700 18\n", encoding="utf-8")

            pieces = parse_cnc_file(
                program_path,
                metadata={
                    "P1": {
                        "name": "Lateral A",
                        "color": "Roble",
                        "grain_direction": "alto",
                        "piece_type": "F1",
                    }
                },
            )

        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0].name, "Lateral A")
        self.assertEqual(pieces[0].color, "Roble")
        self.assertEqual(pieces[0].piece_type, "F1")
        self.assertEqual(pieces[0].grain_direction, PIECE_GRAIN_CODE_HEIGHT)

    def test_scan_project_builds_modules_from_csv_only_module(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_parser_") as temp_dir:
            root = Path(temp_dir)
            module_dir = root / "Modulo"
            module_dir.mkdir()
            (module_dir / "resumen.csv").write_text(
                "piece_id;piece_name;quantity;height;width;thickness;color;grain_direction;source\n"
                "P1;Lateral A;2;700;300;18;Roble;alto;A.pgmx\n",
                encoding="utf-8",
            )

            modules = scan_project(root)

        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0].name, "Modulo")
        self.assertEqual(len(modules[0].pieces), 1)
        self.assertEqual(modules[0].pieces[0].quantity, 2)
        self.assertEqual(modules[0].pieces[0].thickness, 18.0)
        self.assertEqual(modules[0].pieces[0].cnc_source, "A.pgmx")

    def test_project_layout_separates_locales_from_loose_modules(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_parser_") as temp_dir:
            root = Path(temp_dir)
            locale_module = root / "Cocina" / "Modulo A"
            locale_module.mkdir(parents=True)
            (locale_module / "module_config.json").write_text("{}", encoding="utf-8")
            loose_module = root / "Modulo Suelto"
            loose_module.mkdir()
            (loose_module / "module_config.json").write_text("{}", encoding="utf-8")

            layout = inspect_project_layout(root)
            locales, modules = scan_project_structure(root)

        self.assertEqual([path.name for path in layout.locale_dirs], ["Cocina"])
        self.assertEqual([path.name for path in layout.loose_module_dirs], ["Modulo Suelto"])
        self.assertEqual([locale.name for locale in locales], ["Cocina"])
        self.assertEqual([module.relative_path for module in modules], ["Cocina/Modulo A"])


if __name__ == "__main__":
    unittest.main()
