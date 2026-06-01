from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.project_detail_colors import (
    apply_color_to_matching_pieces,
    apply_color_to_matching_rows,
    configured_board_colors,
    module_locale_key,
    preferred_color_index,
)
from core.model import ModuleData, PIECE_GRAIN_CODE_NONE, Piece


class ProjectDetailColorsTests(unittest.TestCase):
    def test_configured_board_colors_filters_by_thickness_and_deduplicates(self) -> None:
        settings = {
            "available_boards": [
                {"color": "Blanco", "thickness": "18"},
                {"color": "blanco", "thickness": "18"},
                {"color": "Roble", "thickness": "15"},
                {"color": "", "thickness": "18"},
            ]
        }

        self.assertEqual(configured_board_colors(settings, piece_thickness=18), ["Blanco"])
        self.assertEqual(configured_board_colors(settings), ["Blanco", "Roble"])

    def test_module_locale_key_prefers_locale_name_then_relative_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_project_detail_colors_") as temp_dir:
            root = Path(temp_dir)
            module_path = root / "Cocina" / "Modulo 1"
            module_path.mkdir(parents=True)

            self.assertEqual(
                module_locale_key(ModuleData(name="M", path=str(module_path), locale_name="Living"), root),
                "living",
            )
            self.assertEqual(
                module_locale_key(ModuleData(name="M", path=str(module_path), relative_path="Cocina/Modulo 1"), root),
                "cocina",
            )
            self.assertEqual(module_locale_key(ModuleData(name="M", path=str(module_path)), root), "cocina")

    def test_preferred_color_index_uses_first_matching_candidate(self) -> None:
        colors = ["Blanco", "Roble", "Negro"]

        self.assertEqual(preferred_color_index(colors, "", "roble"), 1)
        self.assertEqual(preferred_color_index(colors, "NEGRO", "roble"), 2)
        self.assertEqual(preferred_color_index(colors, "Inexistente"), 0)

    def test_apply_color_to_matching_rows_sets_no_grain_when_needed(self) -> None:
        rows = [
            {"color": "Blanco", "grain_direction": "1"},
            {"color": "Roble", "grain_direction": "2"},
        ]

        changed = apply_color_to_matching_rows(rows, "Blanco", "Negro", force_no_grain=True)

        self.assertEqual(changed, 1)
        self.assertEqual(rows[0]["color"], "Negro")
        self.assertEqual(rows[0]["grain_direction"], PIECE_GRAIN_CODE_NONE)
        self.assertEqual(rows[1]["color"], "Roble")

    def test_apply_color_to_matching_pieces_sets_no_grain_when_needed(self) -> None:
        pieces = [
            Piece(id="P1", name="P1", width=1, height=1, color="Blanco", grain_direction="1"),
            Piece(id="P2", name="P2", width=1, height=1, color="Roble", grain_direction="2"),
        ]

        changed = apply_color_to_matching_pieces(pieces, "Blanco", "Negro", force_no_grain=True)

        self.assertEqual(changed, 1)
        self.assertEqual(pieces[0].color, "Negro")
        self.assertEqual(pieces[0].grain_direction, PIECE_GRAIN_CODE_NONE)
        self.assertEqual(pieces[1].color, "Roble")
