"""Row rendering helpers for project inspection piece tables."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from app.project_detail_pgmx import invalid_slot_message
from app.project_detail_piece_table import (
    PIECES_COL_COLOR,
    PIECES_COL_EN_JUEGO,
    PIECES_COL_EXCEL,
    PIECES_COL_GRAIN,
    PIECES_COL_HEIGHT,
    PIECES_COL_ID,
    PIECES_COL_NAME,
    PIECES_COL_NOTES,
    PIECES_COL_PROGRAM,
    PIECES_COL_QUANTITY,
    PIECES_COL_SWAP,
    PIECES_COL_THICKNESS,
    PIECES_COL_WIDTH,
    create_centered_checkbox,
    create_centered_swap_button,
)
from app.settings import _parse_piece_quantity_value
from core.model import build_piece_observations_display, piece_grain_direction_label


PGMX_OK_STATUS = "\u2713"


@dataclass(frozen=True)
class PieceTableProgramDisplay:
    text: str
    tooltip: str
    color: str


def clear_piece_table_widgets(pieces_table: QTableWidget) -> None:
    for old_row in range(pieces_table.rowCount()):
        for old_column in range(pieces_table.columnCount()):
            old_widget = pieces_table.cellWidget(old_row, old_column)
            if old_widget is None:
                continue
            pieces_table.removeCellWidget(old_row, old_column)
            old_widget.deleteLater()


def filtered_piece_table_rows(
    piece_rows: Iterable[dict],
    is_valid_thickness_value: Callable[[object], bool],
) -> list[tuple[int, dict]]:
    return [
        (idx, row_data)
        for idx, row_data in enumerate(piece_rows)
        if is_valid_thickness_value(row_data.get("thickness"))
    ]


def visible_piece_all_index(
    current_row: int,
    visible_row_indexes: Sequence[int],
    *,
    all_rows_count: int | None = None,
) -> int | None:
    if current_row < 0 or current_row >= len(visible_row_indexes):
        return None
    all_idx = visible_row_indexes[current_row]
    if all_rows_count is not None and not 0 <= all_idx < all_rows_count:
        return None
    return all_idx


def visible_piece_row_for_all_index(all_idx: int, visible_row_indexes: Sequence[int]) -> int | None:
    try:
        return list(visible_row_indexes).index(all_idx)
    except ValueError:
        return None


def visible_piece_row_for_id(
    piece_id: str,
    piece_rows: Sequence[dict],
    visible_row_indexes: Sequence[int],
) -> int | None:
    normalized_id = str(piece_id or "").strip()
    if not normalized_id:
        return None

    for row_idx, all_idx in enumerate(visible_row_indexes):
        if all_idx < 0 or all_idx >= len(piece_rows):
            continue
        if str(piece_rows[all_idx].get("id") or "").strip() == normalized_id:
            return row_idx
    return None


def bounded_table_row(row_idx: int | None, row_count: int) -> int | None:
    if row_idx is None or row_count <= 0:
        return None
    return max(0, min(row_idx, row_count - 1))


def can_move_visible_piece(
    current_row: int,
    row_count: int,
    visible_row_indexes: Sequence[int],
    delta: int,
) -> bool:
    target_row = current_row + delta
    return (
        0 <= current_row < row_count
        and 0 <= target_row < row_count
        and current_row < len(visible_row_indexes)
        and target_row < len(visible_row_indexes)
    )


def piece_table_program_display(
    source_value,
    pgmx_status: str,
    *,
    has_invalid_slots: bool,
    invalid_slot_note: str,
) -> PieceTableProgramDisplay:
    normalized_source = str(source_value or "").strip()
    program_filename = Path(normalized_source).name if normalized_source else "(ninguno)"
    program_prefix = "!" if has_invalid_slots else pgmx_status
    color = "#E65100" if has_invalid_slots else "#4CAF50" if pgmx_status == PGMX_OK_STATUS else "#B71C1C"
    tooltip = normalized_source or "(ninguno)"
    if invalid_slot_note:
        tooltip = f"{tooltip}\n{invalid_slot_note}"
    return PieceTableProgramDisplay(
        text=f"{program_prefix} {program_filename}",
        tooltip=tooltip,
        color=color,
    )


def piece_table_observations_text(
    piece_row: dict,
    program_dimension_note: str,
    invalid_slot_note: str,
) -> str:
    observations_text = build_piece_observations_display(
        piece_row.get("observations"),
        program_dimension_note,
    )
    if invalid_slot_note:
        observations_text = "\n".join(
            item for item in (observations_text, invalid_slot_note) if item
        )
    return observations_text


def set_piece_table_observations_item(
    pieces_table: QTableWidget,
    row_idx: int,
    observations_text: str,
) -> None:
    dimension_item = QTableWidgetItem(observations_text)
    dimension_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    dimension_item.setToolTip(observations_text)
    if observations_text:
        dimension_item.setForeground(QColor("#B71C1C"))
    pieces_table.setItem(row_idx, PIECES_COL_NOTES, dimension_item)


def render_piece_table_rows(
    pieces_table: QTableWidget,
    filtered_rows: Sequence[tuple[int, dict]],
    program_dimension_notes: Sequence[str],
    *,
    pgmx_status_for_source: Callable[[str], str],
    invalid_slot_issues_for_row: Callable[[dict], Iterable[object]],
    swap_piece_dimensions: Callable[[int, int], None],
    update_piece_flag: Callable[[int, str, int], None],
    compact_scale: float,
) -> int:
    invalid_slot_row_count = 0

    for row_idx, (all_idx, piece_row) in enumerate(filtered_rows):
        source_value = str(piece_row.get("source", "")).strip()
        pgmx_status = pgmx_status_for_source(source_value)
        program_dimension_note = (
            program_dimension_notes[row_idx]
            if row_idx < len(program_dimension_notes)
            else ""
        )
        invalid_slot_issues = list(invalid_slot_issues_for_row(piece_row) or [])
        invalid_slot_note = invalid_slot_message(invalid_slot_issues)
        has_invalid_slots = bool(invalid_slot_issues)
        if has_invalid_slots:
            invalid_slot_row_count += 1

        piece_row["pgmx"] = pgmx_status
        piece_row["quantity"] = _parse_piece_quantity_value(piece_row.get("quantity"), default=1)
        en_juego = bool(piece_row.get("en_juego", False))
        piece_row["en_juego"] = en_juego
        include_in_sheet = bool(piece_row.get("include_in_sheet", piece_row.get("excel", False)))
        piece_row["include_in_sheet"] = include_in_sheet

        pieces_table.setItem(row_idx, PIECES_COL_ID, QTableWidgetItem(str(piece_row.get("id", ""))))
        pieces_table.setItem(row_idx, PIECES_COL_NAME, QTableWidgetItem(str(piece_row.get("name", ""))))
        quantity_item = QTableWidgetItem(str(piece_row["quantity"]))
        quantity_item.setTextAlignment(Qt.AlignCenter)
        pieces_table.setItem(row_idx, PIECES_COL_QUANTITY, quantity_item)
        pieces_table.setItem(row_idx, PIECES_COL_HEIGHT, QTableWidgetItem(str(piece_row.get("height", ""))))
        pieces_table.setCellWidget(
            row_idx,
            PIECES_COL_SWAP,
            create_centered_swap_button(
                lambda _checked=False, idx=all_idx, visible_idx=row_idx: swap_piece_dimensions(idx, visible_idx),
                "Intercambiar alto y ancho de esta pieza",
                compact_scale=compact_scale,
            ),
        )
        pieces_table.setItem(row_idx, PIECES_COL_WIDTH, QTableWidgetItem(str(piece_row.get("width", ""))))
        pieces_table.setItem(row_idx, PIECES_COL_THICKNESS, QTableWidgetItem(str(piece_row.get("thickness", ""))))
        pieces_table.setItem(row_idx, PIECES_COL_COLOR, QTableWidgetItem(str(piece_row.get("color", ""))))
        pieces_table.setItem(
            row_idx,
            PIECES_COL_GRAIN,
            QTableWidgetItem(piece_grain_direction_label(piece_row.get("grain_direction"))),
        )

        program_display = piece_table_program_display(
            source_value,
            pgmx_status,
            has_invalid_slots=has_invalid_slots,
            invalid_slot_note=invalid_slot_note,
        )
        program_item = QTableWidgetItem(program_display.text)
        program_item.setForeground(QColor(program_display.color))
        program_item.setToolTip(program_display.tooltip)
        pieces_table.setItem(row_idx, PIECES_COL_PROGRAM, program_item)

        set_piece_table_observations_item(
            pieces_table,
            row_idx,
            piece_table_observations_text(piece_row, program_dimension_note, invalid_slot_note),
        )

        pieces_table.setCellWidget(
            row_idx,
            PIECES_COL_EN_JUEGO,
            create_centered_checkbox(
                en_juego,
                lambda state, idx=all_idx: update_piece_flag(idx, "en_juego", state),
            ),
        )
        pieces_table.setCellWidget(
            row_idx,
            PIECES_COL_EXCEL,
            create_centered_checkbox(
                include_in_sheet,
                lambda state, idx=all_idx: update_piece_flag(idx, "include_in_sheet", state),
            ),
        )

    return invalid_slot_row_count
