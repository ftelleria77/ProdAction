from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from app.project_detail_pgmx import (
    clear_invalid_slot_cache_entries,
    invalid_slot_cache_key,
    invalid_slot_message,
)


class ProjectDetailPgmxTests(unittest.TestCase):
    def test_invalid_slot_cache_key_normalizes_source_text(self) -> None:
        self.assertEqual(
            invalid_slot_cache_key(Path("Modulo"), " P1.pgmx "),
            ("Modulo", "P1.pgmx"),
        )

    def test_clear_invalid_slot_cache_entries_can_remove_one_source_or_all(self) -> None:
        cache = {
            ("m", "P1.pgmx"): ("issue",),
            ("m", "P2.pgmx"): ("issue",),
        }

        clear_invalid_slot_cache_entries(cache, "P1.pgmx")
        self.assertEqual(cache, {("m", "P2.pgmx"): ("issue",)})

        clear_invalid_slot_cache_entries(cache)
        self.assertEqual(cache, {})

    def test_invalid_slot_message_prefers_feature_name_then_id(self) -> None:
        self.assertEqual(invalid_slot_message(()), "")
        self.assertIn(
            "Ranura A",
            invalid_slot_message([SimpleNamespace(feature_name="Ranura A", feature_id="E1")]),
        )
        self.assertIn(
            "E2",
            invalid_slot_message([SimpleNamespace(feature_name="", feature_id="E2")]),
        )
