from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QMessageBox

from app.project_detail_selected_piece_actions import (
    SelectedPieceActionContext,
    edit_selected_piece,
    remove_selected_piece,
    select_source_for_selected_piece,
    view_drawing_for_selected_piece,
)


class FakePiecesTable:
    def __init__(self, current_row: int = 0, row_count: int = 1) -> None:
        self._current_row = current_row
        self._row_count = row_count
        self.selected_rows: list[int] = []

    def currentRow(self) -> int:
        return self._current_row

    def rowCount(self) -> int:
        return self._row_count

    def selectRow(self, row: int) -> None:
        self.selected_rows.append(row)


class SelectedPieceActionsTests(unittest.TestCase):
    def test_select_source_assigns_program_persists_refreshes_and_opens_drawing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_selected_piece_actions_") as temp_dir:
            module_path = Path(temp_dir)
            program_path = module_path / "P1.pgmx"
            drawing_path = module_path / "P1.svg"
            program_path.write_text("<xml />", encoding="utf-8")
            drawing_path.write_text("<svg />", encoding="utf-8")
            calls: list[str] = []
            table = FakePiecesTable()
            rows = [{"id": "P1", "name": "P1"}]

            context = self._context(
                module_path=module_path,
                rows=rows,
                table=table,
                persist=lambda: calls.append("persist"),
                refresh=lambda: calls.append("refresh"),
                ensure=lambda row, **_: drawing_path,
            )

            with (
                mock.patch(
                    "app.project_detail_selected_piece_actions.select_pgmx_program_file",
                    return_value=str(program_path),
                ),
                mock.patch("app.project_detail_selected_piece_actions.open_piece_drawing_dialog") as open_drawing,
            ):
                select_source_for_selected_piece(context)

        self.assertEqual(rows[0]["source"], "P1.pgmx")
        self.assertEqual(calls, ["persist", "refresh"])
        self.assertEqual(table.selected_rows, [0])
        open_drawing.assert_called_once_with(None, drawing_path, "P1")

    def test_view_drawing_opens_existing_drawing_for_selected_piece(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prodaction_selected_piece_actions_") as temp_dir:
            drawing_path = Path(temp_dir) / "P1.svg"
            drawing_path.write_text("<svg />", encoding="utf-8")
            context = self._context(
                module_path=Path(temp_dir),
                rows=[{"id": "P1", "name": "Pieza Uno"}],
                ensure=lambda row, **_: drawing_path,
            )

            with mock.patch("app.project_detail_selected_piece_actions.open_piece_drawing_dialog") as open_drawing:
                view_drawing_for_selected_piece(context)

        open_drawing.assert_called_once_with(None, drawing_path, "Pieza Uno")

    def test_edit_selected_piece_opens_editor_for_selected_row(self) -> None:
        table = FakePiecesTable(current_row=1, row_count=2)
        rows = [{"id": "P1"}, {"id": "P2"}]
        editor_calls = []
        context = self._context(module_path=Path("."), rows=rows, table=table)

        edit_selected_piece(context, lambda row, **kwargs: editor_calls.append((row, kwargs)))

        self.assertEqual(editor_calls, [(rows[1], {"row_index": 1})])

    def test_remove_selected_piece_removes_row_persists_refreshes_and_restores_selection(self) -> None:
        table = FakePiecesTable(current_row=0, row_count=2)
        rows = [{"id": "P1", "name": "Pieza Uno"}, {"id": "P2"}]
        calls = []
        context = self._context(
            module_path=Path("."),
            rows=rows,
            table=table,
            persist=lambda: calls.append("persist"),
            refresh=lambda: calls.append("refresh"),
            remove=lambda row, **_: calls.append(("remove", row["id"])),
            select=lambda piece_id, **kwargs: calls.append(("select", piece_id, kwargs)),
        )

        with mock.patch(
            "app.project_detail_selected_piece_actions.QMessageBox.question",
            return_value=QMessageBox.Yes,
        ):
            remove_selected_piece(context)

        self.assertEqual(rows, [{"id": "P2"}])
        self.assertEqual(
            calls,
            [
                ("remove", "P1"),
                "persist",
                "refresh",
                ("select", "", {"fallback_row": 0}),
            ],
        )

    def _context(
        self,
        *,
        module_path: Path,
        rows: list[dict],
        table: FakePiecesTable | None = None,
        persist=lambda: None,
        refresh=lambda: None,
        ensure=lambda row, **_: None,
        remove=lambda row, **_: None,
        select=lambda piece_id, **kwargs: None,
    ) -> SelectedPieceActionContext:
        return SelectedPieceActionContext(
            parent=None,
            project=None,
            module_path=module_path,
            all_rows=rows,
            visible_row_indexes=list(range(len(rows))),
            pieces_table=table or FakePiecesTable(),
            persist_module_config=persist,
            refresh_pieces_table=refresh,
            build_piece_from_row=lambda row: row,
            ensure_piece_drawing=ensure,
            refresh_piece_drawing_file=lambda row, **_: None,
            remove_piece_drawing_file=remove,
            select_visible_piece_by_id=select,
            get_invalid_slot_issues_for_row=lambda row: (),
            clear_invalid_slot_cache=lambda *args, **kwargs: None,
            refresh_repair_pgmx_button_state=lambda: None,
            program_dimensions_cache={},
        )


if __name__ == "__main__":
    unittest.main()
