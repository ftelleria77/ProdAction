import unittest
from types import SimpleNamespace

import app.project_detail_en_juego_preview as preview


class EnJuegoPreviewTests(unittest.TestCase):
    def test_load_piece_drawing_data_returns_none_for_rows_without_cnc_source(self):
        cache = {}
        calls = []

        def piece_factory(piece_row):
            calls.append(piece_row)
            return SimpleNamespace(cnc_source="")

        result = preview.load_piece_drawing_data(
            object(),
            "module.mod",
            {"id": "P1"},
            piece_factory,
            cache,
        )

        self.assertIsNone(result)
        self.assertEqual(cache, {"P1": None})
        self.assertEqual(len(calls), 1)

    def test_load_piece_drawing_data_caches_successful_parse(self):
        cache = {}
        drawing_data = object()
        parse_calls = []
        original_parse = preview.parse_pgmx_for_piece

        def piece_factory(_piece_row):
            return SimpleNamespace(cnc_source="piece.pgmx")

        def fake_parse(project, piece_obj, module_path):
            parse_calls.append((project, piece_obj.cnc_source, module_path))
            return drawing_data

        try:
            preview.parse_pgmx_for_piece = fake_parse
            first = preview.load_piece_drawing_data(
                "project",
                "module.mod",
                {"id": "P1"},
                piece_factory,
                cache,
            )
            second = preview.load_piece_drawing_data(
                "project",
                "module.mod",
                {"id": "P1"},
                piece_factory,
                cache,
            )
        finally:
            preview.parse_pgmx_for_piece = original_parse

        self.assertIs(first, drawing_data)
        self.assertIs(second, drawing_data)
        self.assertEqual(cache, {"P1": drawing_data})
        self.assertEqual(parse_calls, [("project", "piece.pgmx", "module.mod")])

    def test_load_piece_drawing_data_caches_parse_failures_as_empty_preview(self):
        cache = {}
        original_parse = preview.parse_pgmx_for_piece

        def piece_factory(_piece_row):
            return SimpleNamespace(cnc_source="piece.pgmx")

        def fake_parse(_project, _piece_obj, _module_path):
            raise ValueError("bad program")

        try:
            preview.parse_pgmx_for_piece = fake_parse
            result = preview.load_piece_drawing_data(
                "project",
                "module.mod",
                {"id": "P1"},
                piece_factory,
                cache,
            )
        finally:
            preview.parse_pgmx_for_piece = original_parse

        self.assertIsNone(result)
        self.assertEqual(cache, {"P1": None})


if __name__ == "__main__":
    unittest.main()
