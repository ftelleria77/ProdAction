"""Ventana principal de seleccion de proyectos."""

import datetime

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.options_dialogs import OptionsDialog
from app.project_dialogs import NewProjectDialog
from app.project_registry import _find_registry_entry, _read_registry
from app.project_store import (
    _load_project,
    _project_data_path_from_registry_entry,
    _registry_entry_is_accessible,
    _save_project,
    _unregister_project,
)
from app.qt_helpers import _exec_centered, _show_centered
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import Project

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProdAction")
        self.setGeometry(100, 100, 640, 420)
        self.current_project = None

        layout = QVBoxLayout()

        top_row = QHBoxLayout()
        top_row.addStretch()
        self.btn_options = QPushButton("\u2699")
        self.btn_options.setToolTip("Opciones")
        self.btn_options.setFixedSize(40, 40)
        top_row.addWidget(self.btn_options)
        layout.addLayout(top_row)

        content_column = QVBoxLayout()
        content_column.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Proyectos")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        content_column.addWidget(title)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        self.project_list = QListWidget()
        content_row.addWidget(self.project_list, 1)

        buttons_column = QVBoxLayout()
        buttons_column.setContentsMargins(0, 0, 0, 0)
        self.btn_new = QPushButton("Nuevo")
        self.btn_open = QPushButton("Abrir")
        self.btn_delete = QPushButton("Eliminar")
        self.btn_close = QPushButton("Cerrar")

        buttons_column.addWidget(self.btn_new)
        buttons_column.addWidget(self.btn_open)
        buttons_column.addWidget(self.btn_delete)
        buttons_column.addStretch()
        buttons_column.addWidget(self.btn_close)

        content_row.addLayout(buttons_column)
        content_column.addLayout(content_row, 1)
        layout.addLayout(content_column, 1)

        for button in (
            self.btn_new,
            self.btn_open,
            self.btn_delete,
            self.btn_close,
        ):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.btn_new.clicked.connect(self.create_project)
        self.btn_open.clicked.connect(self.open_project)
        self.btn_delete.clicked.connect(self.delete_project)
        self.btn_options.clicked.connect(self.open_options)
        self.btn_close.clicked.connect(self.close_application)
        self.project_list.itemDoubleClicked.connect(lambda _: self.open_project())
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.refresh_shortcut.activated.connect(self.refresh_project_list)
        self.project_list.installEventFilter(self)

        self.refresh_project_list()

    def eventFilter(self, watched, event):
        if (
            watched is self.project_list
            and event.type() == QEvent.KeyPress
            and event.key() == Qt.Key_F5
        ):
            self.refresh_project_list()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self.refresh_project_list()
            event.accept()
            return
        super().keyPressEvent(event)

    def open_options(self):
        dialog = OptionsDialog(self)
        _exec_centered(dialog, self)

    def close_application(self):
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def refresh_project_list(self):
        selected_project_name = None
        current_item = self.project_list.currentItem()
        if current_item is not None:
            selected_project_name = current_item.data(Qt.UserRole)

        self.project_list.clear()
        registry = _read_registry()
        for entry in sorted(registry, key=lambda item: str(item.get("project_name") or "").lower()):
            project_name = str(entry.get("project_name") or "").strip()
            client_name = str(entry.get("client_name") or "-").strip() or "-"
            item = QListWidgetItem(f"{project_name} - {client_name}")
            item.setData(Qt.UserRole, project_name)
            item.setData(Qt.UserRole + 1, _registry_entry_is_accessible(entry))
            if not item.data(Qt.UserRole + 1):
                item.setForeground(QColor("#777777"))
                item.setToolTip("Proyecto temporalmente inaccesible")
            self.project_list.addItem(item)
            if selected_project_name and project_name == selected_project_name:
                self.project_list.setCurrentItem(item)

    def _select_project_list_item(self, project_name: str):
        normalized_name = str(project_name or "").strip().lower()
        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if str(item.data(Qt.UserRole) or "").strip().lower() == normalized_name:
                self.project_list.setCurrentItem(item)
                return item
        return None

    def create_project(self):
        dialog = NewProjectDialog(self)
        while True:
            if _exec_centered(dialog, self) != QDialog.Accepted:
                return

            project_data = dialog.project_data()
            project_name = project_data["name"]
            project_client = project_data["client"]
            project_root = project_data["root_directory"]

            if any(
                str(entry.get("project_name") or "").strip().lower() == project_name.lower()
                for entry in _read_registry()
            ):
                QMessageBox.warning(dialog, "Error", "Proyecto ya existe")
                continue
            break

        created_at = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        project = Project(
            name=project_name,
            root_directory=project_root,
            project_data_file="project.json",
            client=project_client.strip(),
            locales=[],
            created_at=created_at,
        )
        _save_project(project)
        self.current_project = project
        self.refresh_project_list()
        QMessageBox.information(self, "OK", f"Proyecto '{project_name}' creado.")

    def open_project(self):
        item = self.project_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Seleccione un proyecto")
            return
        project_name = item.data(Qt.UserRole) or item.text().split(" - ")[0]
        self.refresh_project_list()
        item = self._select_project_list_item(project_name)
        if not item:
            QMessageBox.warning(self, "Error", "Proyecto no encontrado")
            return
        if item.data(Qt.UserRole + 1) is False:
            QMessageBox.warning(
                self,
                "Proyecto inaccesible",
                "La carpeta principal de este proyecto no está disponible en este momento.",
            )
            return
        try:
            project = _load_project(project_name)
            self.current_project = project
            from app.ui import ProjectDetailWindow

            detail_window = ProjectDetailWindow(project, return_window=self)
            _show_centered(detail_window, self)
            self.detail_window = detail_window
            self.hide()
        except Exception as exc:
            self.refresh_project_list()
            QMessageBox.warning(self, "Error", f"No se pudo abrir el proyecto: {exc}")

    def delete_project(self):
        item = self.project_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Seleccione un proyecto")
            return
        project_name = item.data(Qt.UserRole) or item.text().split(" - ")[0]
        response = QMessageBox.question(
            self,
            "Eliminar",
            f"¿Desea eliminar el proyecto '{project_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return

        registry_entry = _find_registry_entry(project_name)
        if registry_entry is None:
            QMessageBox.warning(self, "Error", "Proyecto no encontrado")
            return

        project_path = _project_data_path_from_registry_entry(registry_entry)
        if project_path.exists():
            project_path.unlink()
        _unregister_project(project_name)
        self.refresh_project_list()
        QMessageBox.information(self, "Ok", "Proyecto eliminado")
