"""Piece table widgets and column configuration for project inspection."""

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QHeaderView, QPushButton, QTableWidget, QWidget

from app.qt_helpers import _scaled_int
from app.ui_constants import MAIN_ACTION_BUTTON_WIDTH


PIECES_COL_ID = 0
PIECES_COL_NAME = 1
PIECES_COL_QUANTITY = 2
PIECES_COL_HEIGHT = 3
PIECES_COL_SWAP = 4
PIECES_COL_WIDTH = 5
PIECES_COL_THICKNESS = 6
PIECES_COL_COLOR = 7
PIECES_COL_GRAIN = 8
PIECES_COL_PROGRAM = 9
PIECES_COL_NOTES = 10
PIECES_COL_EN_JUEGO = 11
PIECES_COL_EXCEL = 12

PIECE_TABLE_HEADERS = [
    "ID",
    "Nombre",
    "Cantidad",
    "Alto",
    "",
    "Ancho",
    "Espesor",
    "Color",
    "Veta",
    "Programa",
    "Observaciones",
    "En juego",
    "Excel",
]

PIECE_TABLE_AUTO_COLUMNS = {
    PIECES_COL_QUANTITY,
    PIECES_COL_HEIGHT,
    PIECES_COL_WIDTH,
    PIECES_COL_THICKNESS,
}


@dataclass(frozen=True)
class PieceTableSwapButtonMetrics:
    width: int
    height: int
    font_size: int


def piece_table_fixed_column_widths(compact_scale: float) -> dict[int, int]:
    return {
        PIECES_COL_ID: 50,
        PIECES_COL_NAME: _scaled_int(180, compact_scale, 120),
        PIECES_COL_SWAP: _scaled_int(18, compact_scale, 14),
        PIECES_COL_COLOR: _scaled_int(110, compact_scale, 90),
        PIECES_COL_GRAIN: _scaled_int(110, compact_scale, 90),
        PIECES_COL_PROGRAM: _scaled_int(250, compact_scale, 170),
        PIECES_COL_NOTES: _scaled_int(320, compact_scale, 180),
        PIECES_COL_EN_JUEGO: _scaled_int(90, compact_scale, 68),
        PIECES_COL_EXCEL: _scaled_int(70, compact_scale, 60),
    }


def piece_table_swap_button_metrics(compact_scale: float) -> PieceTableSwapButtonMetrics:
    return PieceTableSwapButtonMetrics(
        width=_scaled_int(14, compact_scale, 11),
        height=_scaled_int(20, compact_scale, 16),
        font_size=_scaled_int(8, compact_scale, 6),
    )


def create_piece_table() -> QTableWidget:
    pieces_table = QTableWidget()
    pieces_table.setColumnCount(len(PIECE_TABLE_HEADERS))
    pieces_table.setHorizontalHeaderLabels(PIECE_TABLE_HEADERS)
    return pieces_table


def create_centered_checkbox(checked: bool, on_changed):
    container = QWidget()
    checkbox_layout = QHBoxLayout(container)
    checkbox_layout.setContentsMargins(0, 0, 0, 0)
    checkbox_layout.setSpacing(0)
    checkbox = QCheckBox(container)
    checkbox.setChecked(bool(checked))
    checkbox_layout.addStretch(1)
    checkbox_layout.addWidget(checkbox, 0, Qt.AlignCenter)
    checkbox_layout.addStretch(1)
    checkbox.stateChanged.connect(on_changed)
    return container


def create_centered_swap_button(on_clicked, tooltip: str, *, compact_scale: float):
    metrics = piece_table_swap_button_metrics(compact_scale)
    container = QWidget()
    button_layout = QHBoxLayout(container)
    button_layout.setContentsMargins(0, 0, 0, 0)
    button_layout.setSpacing(0)
    swap_button = QPushButton("↔", container)
    swap_button.setToolTip(tooltip)
    swap_button.setFixedSize(metrics.width, metrics.height)
    swap_button.setContentsMargins(0, 0, 0, 0)
    swap_button.setStyleSheet(
        "QPushButton {"
        f"font-size: {metrics.font_size}px;"
        "padding: 0px;"
        "margin: 0px;"
        "text-align: center;"
        "}"
    )
    swap_button.clicked.connect(on_clicked)
    button_layout.addStretch(1)
    button_layout.addWidget(swap_button, 0, Qt.AlignCenter)
    button_layout.addStretch(1)
    return container


def configure_piece_table(
    pieces_table: QTableWidget,
    *,
    compact_scale: float,
    inspect_width: int,
    swap_all_piece_dimensions,
) -> None:
    header = pieces_table.horizontalHeader()
    fixed_column_widths = piece_table_fixed_column_widths(compact_scale)
    for column_idx in range(pieces_table.columnCount()):
        if column_idx in PIECE_TABLE_AUTO_COLUMNS:
            header.setSectionResizeMode(column_idx, QHeaderView.ResizeToContents)
        else:
            header.setSectionResizeMode(column_idx, QHeaderView.Fixed)
            pieces_table.setColumnWidth(column_idx, fixed_column_widths[column_idx])

    metrics = piece_table_swap_button_metrics(compact_scale)
    swap_all_dimensions_btn = QPushButton("↔", header)
    swap_all_dimensions_btn.setToolTip("Intercambiar alto y ancho de todas las piezas")
    swap_all_dimensions_btn.setFixedHeight(metrics.height)
    swap_all_dimensions_btn.setContentsMargins(0, 0, 0, 0)
    swap_all_dimensions_btn.setStyleSheet(
        "QPushButton {"
        f"font-size: {metrics.font_size}px;"
        "padding: 0px;"
        "margin: 0px;"
        "text-align: center;"
        "}"
    )
    swap_all_dimensions_btn.clicked.connect(swap_all_piece_dimensions)

    def position_swap_all_dimensions_button(*_):
        section_width = header.sectionSize(PIECES_COL_SWAP)
        if section_width <= 0:
            swap_all_dimensions_btn.hide()
            return
        button_width = max(9, min(metrics.width, section_width - 2))
        button_height = max(16, min(metrics.height, header.height() - 2))
        x_position = header.sectionViewportPosition(PIECES_COL_SWAP) + max(
            0,
            (section_width - button_width) // 2,
        )
        y_position = max(0, (header.height() - button_height) // 2)
        swap_all_dimensions_btn.setGeometry(x_position, y_position, button_width, button_height)
        swap_all_dimensions_btn.show()
        swap_all_dimensions_btn.raise_()

    header.sectionResized.connect(position_swap_all_dimensions_button)
    header.geometriesChanged.connect(position_swap_all_dimensions_button)
    pieces_table.horizontalScrollBar().valueChanged.connect(position_swap_all_dimensions_button)
    position_swap_all_dimensions_button()

    actions_column_reserved_width = MAIN_ACTION_BUTTON_WIDTH + 36
    pieces_table.setMinimumWidth(
        max(
            320,
            min(
                sum(fixed_column_widths.values()) + 520,
                inspect_width - actions_column_reserved_width,
            ),
        )
    )
    pieces_table.verticalHeader().setDefaultSectionSize(_scaled_int(30, compact_scale, 22))

    pieces_table.setAlternatingRowColors(True)
    pieces_table.setEditTriggers(QTableWidget.NoEditTriggers)
    pieces_table.setSelectionBehavior(QTableWidget.SelectRows)
    pieces_table.setSelectionMode(QTableWidget.SingleSelection)
