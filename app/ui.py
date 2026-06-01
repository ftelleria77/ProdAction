"""Interfaz gráfica principal para gestión de proyectos CNC.

Contiene ventana principal con creación, apertura, limpieza,
archivado y selección de carpeta raíz de proyecto.
Incluye ventana de detalle de proyecto con edición.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from app.project_detail_core import ProjectDetailCoreMixin
from app.project_detail_inspection import ProjectDetailInspectionMixin
from app.project_detail_modules import ProjectDetailModulesMixin
from app.project_detail_output import ProjectDetailOutputMixin
from app.project_detail_processing import ProjectDetailProcessingMixin
from app.qt_helpers import _show_centered

from core.model import Project


class ProjectDetailWindow(
    ProjectDetailCoreMixin,
    ProjectDetailProcessingMixin,
    ProjectDetailModulesMixin,
    ProjectDetailInspectionMixin,
    ProjectDetailOutputMixin,
    QMainWindow,
):
    def __init__(self, project: Project, return_window=None):
        super().__init__()
        self.project = project
        self.return_window = return_window
        self.setWindowTitle(f"Proyecto: {project.name}")
        self.setGeometry(120, 120, 640, 420)

        layout = QVBoxLayout()
        self.lbl_name = QLabel()
        self.lbl_client = QLabel()
        self.lbl_root = QLabel()
        self.lbl_root.setWordWrap(True)
        self.lbl_created = QLabel()
        self.lbl_modified = QLabel()
        self.lbl_locales_count = QLabel()
        self.locales_list = QListWidget()
        self.locales_list.setMinimumHeight(120)

        header_row = QHBoxLayout()
        self.lbl_client.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_row.addWidget(self.lbl_name)
        header_row.addStretch(1)
        header_row.addWidget(self.lbl_client)

        dates_row = QHBoxLayout()
        dates_row.addWidget(self.lbl_created)
        dates_row.addStretch(1)
        dates_row.addWidget(self.lbl_modified)

        btn_process = QPushButton("Procesar\nSelección")
        btn_add_locale = QPushButton("Nuevo\nLocal")
        btn_modules = QPushButton("Abrir\nLocal")
        btn_sheets = QPushButton("Generar\nPlanillas")
        btn_cuts = QPushButton("Diagramas\nde Corte")
        btn_close = QPushButton("Cerrar")

        for button in (
            btn_process,
            btn_add_locale,
            btn_modules,
            btn_sheets,
            btn_cuts,
            btn_close,
        ):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

        layout.addLayout(header_row)
        layout.addWidget(self.lbl_root)
        layout.addLayout(dates_row)
        layout.addWidget(self.lbl_locales_count)

        locales_and_actions_row = QHBoxLayout()
        locales_and_actions_row.addWidget(self.locales_list, 1)

        actions_column = QVBoxLayout()
        actions_column.setContentsMargins(0, 0, 0, 0)
        actions_column.addWidget(btn_process)
        actions_column.addWidget(btn_add_locale)
        actions_column.addWidget(btn_modules)
        actions_column.addWidget(btn_sheets)
        actions_column.addWidget(btn_cuts)
        actions_column.addStretch(1)
        actions_column.addWidget(btn_close)

        locales_and_actions_row.addLayout(actions_column)
        layout.addLayout(locales_and_actions_row, 1)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.btn_modules = btn_modules
        self.btn_sheets = btn_sheets
        self.btn_cuts = btn_cuts
        self.btn_modules.clicked.connect(self.show_modules)
        self.locales_list.itemDoubleClicked.connect(lambda *_: self.show_modules())

        btn_process.clicked.connect(self.process_project)
        btn_add_locale.clicked.connect(self.add_locale)
        btn_sheets.clicked.connect(self.generate_sheets)
        btn_cuts.clicked.connect(self.show_cuts)
        btn_close.clicked.connect(self.close)

        self.refresh_project_header_info()
        self.update_modules_button()
        self.update_output_action_buttons()

    def _show_return_window(self):
        if self.return_window is None:
            return
        self.return_window.show()
        self.return_window.raise_()
        self.return_window.activateWindow()

    def closeEvent(self, event):
        self._show_return_window()
        super().closeEvent(event)


def run_app():
    app = QApplication([])
    from app.main_window import MainWindow

    window = MainWindow()
    _show_centered(window)
    app.exec()
