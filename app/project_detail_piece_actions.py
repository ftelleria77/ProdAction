"""Side action buttons for the project detail piece inspection dialog."""

from dataclasses import dataclass

from PySide6.QtWidgets import QPushButton, QVBoxLayout

from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH


@dataclass
class ProjectDetailPieceActions:
    layout: QVBoxLayout
    add_piece_btn: QPushButton
    edit_piece_btn: QPushButton
    delete_piece_btn: QPushButton
    move_piece_up_btn: QPushButton
    move_piece_down_btn: QPushButton
    repair_pgmx_btn: QPushButton
    configure_en_juego_btn: QPushButton


def build_project_detail_piece_actions(
    *,
    add_piece,
    edit_piece,
    delete_piece,
    move_piece_up,
    move_piece_down,
    repair_pgmx,
    configure_en_juego,
) -> ProjectDetailPieceActions:
    actions_column = QVBoxLayout()
    actions_column.setContentsMargins(0, 0, 0, 0)
    actions_column.setSpacing(8)

    add_piece_btn = QPushButton("Nueva")
    add_piece_btn.setToolTip("Nueva Pieza")
    edit_piece_btn = QPushButton("Editar")
    edit_piece_btn.setToolTip("Editar Pieza")
    delete_piece_btn = QPushButton("Eliminar")
    delete_piece_btn.setToolTip("Eliminar Pieza")
    move_piece_up_btn = QPushButton("Subir")
    move_piece_down_btn = QPushButton("Bajar")
    repair_pgmx_btn = QPushButton("Corregir\nPGMX")
    repair_pgmx_btn.setToolTip("Seleccione una pieza con ranura no ejecutable.")
    repair_pgmx_btn.setEnabled(False)
    configure_en_juego_btn = QPushButton("Configurar\nEn Juego")
    configure_en_juego_btn.setToolTip("Configurar En Juego")

    for button in (
        add_piece_btn,
        edit_piece_btn,
        delete_piece_btn,
        move_piece_up_btn,
        move_piece_down_btn,
        repair_pgmx_btn,
        configure_en_juego_btn,
    ):
        button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        actions_column.addWidget(button)

    add_piece_btn.clicked.connect(add_piece)
    edit_piece_btn.clicked.connect(edit_piece)
    delete_piece_btn.clicked.connect(delete_piece)
    move_piece_up_btn.clicked.connect(move_piece_up)
    move_piece_down_btn.clicked.connect(move_piece_down)
    repair_pgmx_btn.clicked.connect(repair_pgmx)
    configure_en_juego_btn.clicked.connect(configure_en_juego)

    return ProjectDetailPieceActions(
        layout=actions_column,
        add_piece_btn=add_piece_btn,
        edit_piece_btn=edit_piece_btn,
        delete_piece_btn=delete_piece_btn,
        move_piece_up_btn=move_piece_up_btn,
        move_piece_down_btn=move_piece_down_btn,
        repair_pgmx_btn=repair_pgmx_btn,
        configure_en_juego_btn=configure_en_juego_btn,
    )
