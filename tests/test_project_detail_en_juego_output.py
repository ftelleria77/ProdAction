from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from app.project_detail_en_juego_output import (
    en_juego_creation_details,
    en_juego_output_path_for_config,
)


class EnJuegoOutputTests(unittest.TestCase):
    def test_output_path_for_config_prefers_module_relative_path(self):
        module_path = Path.cwd() / "module"
        output_path = module_path / "nested" / "EnJuego.pgmx"

        self.assertEqual(
            en_juego_output_path_for_config(output_path, module_path),
            "nested/EnJuego.pgmx",
        )

    def test_output_path_for_config_falls_back_to_original_path(self):
        module_path = Path.cwd() / "module"
        output_path = Path.cwd() / "other" / "EnJuego.pgmx"

        self.assertEqual(
            en_juego_output_path_for_config(output_path, module_path),
            str(output_path),
        )

    def test_creation_details_includes_fallback_count_only_when_present(self):
        result = SimpleNamespace(
            output_path="out.pgmx",
            board_width=100.0,
            board_height=50.5,
            board_thickness=18,
            instance_count=3,
            contour_count=4,
            fallback_contour_count=0,
        )

        self.assertEqual(
            en_juego_creation_details(result),
            [
                "Archivo generado: out.pgmx",
                "Tablero sintetizado: 100.00 x 50.50 x 18.00 mm",
                "Piezas ubicadas: 3",
                "Contornos generados: 4",
            ],
        )

        result.fallback_contour_count = 2
        self.assertEqual(
            en_juego_creation_details(result)[-1],
            "Contornos por rectángulo de respaldo: 2",
        )


if __name__ == "__main__":
    unittest.main()
