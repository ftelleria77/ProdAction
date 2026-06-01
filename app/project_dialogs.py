"""Dialogos de creacion y edicion de proyectos."""

import os
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.project_registry import _read_registry
from app.project_store import _normalize_project_locales, _save_project, _unregister_project
from app.qt_helpers import _exec_centered
from app.ui_constants import MAIN_ACTION_BUTTON_HEIGHT, MAIN_ACTION_BUTTON_WIDTH
from core.model import LocaleData, Project

class EditLocalesDialog(QDialog):
    """Ventana simple para visualizar la lista actual de locales."""

    def __init__(self, locales: list[LocaleData], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Locales")
        self.resize(420, 360)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Locales detectados en el proyecto:"))

        self.locales_list = QListWidget()
        for locale in locales:
            if isinstance(locale, LocaleData):
                label = f"{locale.name} | {locale.path} | {locale.modules_count} módulo(s)"
            else:
                label = str(locale).strip()
            if label:
                self.locales_list.addItem(label)
        layout.addWidget(self.locales_list)

        buttons_layout = QHBoxLayout()
        close_btn = QPushButton("Cerrar")
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        close_btn.clicked.connect(self.accept)

class EditProjectWindow(QMainWindow):
    """Ventana para editar nombre y carpeta raíz de un proyecto existente."""
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.locales = _normalize_project_locales(
            getattr(project, "locales", []),
            getattr(project, "local", ""),
        )
        self.setWindowTitle(f"Editar Proyecto: {project.name}")
        self.setGeometry(200, 200, 500, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Proyecto:"))
        self.name_field = QLineEdit(project.name)
        layout.addWidget(self.name_field)

        layout.addWidget(QLabel("Cliente:"))
        self.client_field = QLineEdit(project.client)
        layout.addWidget(self.client_field)

        locales_layout = QHBoxLayout()
        locales_layout.addWidget(QLabel("Locales:"))
        self.locales_summary = QLabel()
        locales_layout.addWidget(self.locales_summary, 1)
        self.locales_btn = QPushButton("Locales")
        locales_layout.addWidget(self.locales_btn)
        layout.addLayout(locales_layout)
        self.refresh_locales_summary()

        layout.addWidget(QLabel("Carpeta raíz:"))
        self.root_field = QLineEdit(project.root_directory)
        layout.addWidget(self.root_field)

        btn_select_folder = QPushButton("Seleccionar carpeta")
        btn_select_folder.clicked.connect(self.select_folder)
        layout.addWidget(btn_select_folder)

        button_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_cancel = QPushButton("Cancelar")
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_cancel)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        btn_save.clicked.connect(self.save_changes)
        btn_cancel.clicked.connect(self.close)
        self.locales_btn.clicked.connect(self.edit_locales)

    def refresh_locales_summary(self):
        if self.locales:
            preview = ", ".join(locale.name for locale in self.locales[:3])
            if len(self.locales) > 3:
                preview = f"{preview}..."
            self.locales_summary.setText(f"{len(self.locales)} local(es): {preview}")
        else:
            self.locales_summary.setText("Sin locales cargados")

    def edit_locales(self):
        dialog = EditLocalesDialog(self.locales, self)
        _exec_centered(dialog, self)

    def select_folder(self):
        """Seleccionar nueva carpeta raíz."""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta raíz")
        if folder:
            self.root_field.setText(folder)

    def save_changes(self):
        """Guardar cambios en el proyecto."""
        new_name = self.name_field.text().strip()
        new_client = self.client_field.text().strip()
        new_root = self.root_field.text().strip()

        if not new_name:
            QMessageBox.warning(self, "Error", "Ingrese un nombre de proyecto")
            return
        if not new_root or not os.path.isdir(new_root):
            QMessageBox.warning(self, "Error", "Seleccione una carpeta raíz válida")
            return
        registry = _read_registry()
        if new_name != self.project.name and any(
            str(entry.get("project_name") or "").strip().lower() == new_name.lower()
            for entry in registry
        ):
            QMessageBox.warning(self, "Error", "Proyecto con ese nombre ya existe")
            return

        # Actualizar proyecto
        old_name = self.project.name
        old_root = self.project.root_directory
        self.project.name = new_name
        self.project.client = new_client
        self.project.locales = list(self.locales)
        self.project.root_directory = new_root

        # Si cambió la carpeta, mover el archivo JSON
        if new_root != old_root:
            old_file = Path(old_root) / self.project.project_data_file
            new_file = Path(new_root) / self.project.project_data_file
            if old_file.exists():
                new_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_file), str(new_file))

        # Guardar proyecto actualizado
        _save_project(self.project)

        # Si cambió el nombre, eliminar registro antiguo
        if new_name != old_name:
            _unregister_project(old_name)

        QMessageBox.information(self, "OK", "Proyecto actualizado.")
        self.close()

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo proyecto")
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Complete los datos del proyecto."))

        label_width = max(
            QLabel("Proyecto").sizeHint().width(),
            QLabel("Cliente").sizeHint().width(),
            QLabel("Carpeta").sizeHint().width(),
        )

        project_row = QHBoxLayout()
        project_label = QLabel("Proyecto")
        project_label.setFixedWidth(label_width)
        project_row.addWidget(project_label)
        self.name_field = QLineEdit()
        project_row.addWidget(self.name_field, 1)
        layout.addLayout(project_row)

        client_row = QHBoxLayout()
        client_label = QLabel("Cliente")
        client_label.setFixedWidth(label_width)
        client_row.addWidget(client_label)
        self.client_field = QLineEdit()
        client_row.addWidget(self.client_field, 1)
        layout.addLayout(client_row)

        folder_row = QHBoxLayout()
        folder_label = QLabel("Carpeta")
        folder_label.setFixedWidth(label_width)
        folder_row.addWidget(folder_label)
        self.root_field = QLineEdit()
        folder_row.addWidget(self.root_field, 1)
        self.select_folder_button = QPushButton("Seleccionar")
        folder_row.addWidget(self.select_folder_button)
        layout.addLayout(folder_row)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch()
        self.accept_button = QPushButton("Aceptar")
        self.cancel_button = QPushButton("Cancelar")
        self.accept_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        self.cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        buttons_row.addWidget(self.accept_button)
        buttons_row.addWidget(self.cancel_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

        self.select_folder_button.clicked.connect(self.select_folder)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta del proyecto")
        if folder:
            self.root_field.setText(folder)

    def accept(self):
        project_name = self.name_field.text().strip()
        project_root = self.root_field.text().strip()

        if not project_name:
            QMessageBox.warning(self, "Error", "Ingrese un nombre de proyecto")
            return
        if not project_root or not os.path.isdir(project_root):
            QMessageBox.warning(self, "Error", "Seleccione una carpeta de proyecto válida")
            return

        super().accept()

    def project_data(self) -> dict:
        return {
            "name": self.name_field.text().strip(),
            "client": self.client_field.text().strip(),
            "root_directory": self.root_field.text().strip(),
        }
