from __future__ import annotations

import unittest

from core.model import (
    PIECE_EN_JUEGO_OBSERVATION,
    PIECE_GRAIN_CODE_HEIGHT,
    PIECE_GRAIN_CODE_NONE,
    PIECE_GRAIN_CODE_WIDTH,
    LocaleData,
    Project,
    build_piece_observations_display,
    normalize_piece_grain_direction,
    normalize_piece_observations,
    set_piece_en_juego_observation,
)


class CoreModelTests(unittest.TestCase):
    def test_normalize_piece_grain_direction_accepts_codes_and_labels(self) -> None:
        self.assertEqual(normalize_piece_grain_direction("sin veta"), PIECE_GRAIN_CODE_NONE)
        self.assertEqual(normalize_piece_grain_direction("longitudinal"), PIECE_GRAIN_CODE_HEIGHT)
        self.assertEqual(normalize_piece_grain_direction("a lo ancho"), PIECE_GRAIN_CODE_WIDTH)
        self.assertEqual(normalize_piece_grain_direction("valor desconocido"), PIECE_GRAIN_CODE_NONE)

    def test_observations_are_deduplicated_and_en_juego_is_toggled(self) -> None:
        normalized = normalize_piece_observations(" Laca | laca\nTapacanto ")
        self.assertEqual(normalized, "Laca | Tapacanto")

        enabled = set_piece_en_juego_observation(normalized, True)
        self.assertEqual(enabled, f"Laca | Tapacanto | {PIECE_EN_JUEGO_OBSERVATION}")

        disabled = set_piece_en_juego_observation(enabled, False)
        self.assertEqual(disabled, "Laca | Tapacanto")

    def test_build_piece_observations_display_combines_manual_and_program_notes(self) -> None:
        self.assertEqual(
            build_piece_observations_display("Manual | manual", "PGMX"),
            "Manual | PGMX",
        )

    def test_project_to_dict_keeps_public_persistence_contract(self) -> None:
        project = Project(
            name="Demo",
            root_directory=".",
            client="Cliente",
            created_at="2026-06-06",
            locales=[LocaleData(name="Cocina", path="Cocina", modules_count=2)],
        )

        self.assertEqual(project.local, "Cocina")
        self.assertEqual(project.locales_count, 1)
        self.assertEqual(
            project.to_dict(),
            {
                "project_name": "Demo",
                "client_name": "Cliente",
                "created_at": "2026-06-06",
                "locales": [
                    {
                        "name": "Cocina",
                        "path": "Cocina",
                        "modules_count": 2,
                    }
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
