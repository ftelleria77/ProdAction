"""Standalone Qt3D module preview test window.

This prototype is intentionally outside the main application flow. It reads a
Maestro module CSV, converts the known piece types into simple 3D boxes, and
renders them with Qt3D.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QVector3D
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from .module_3d_preview_model import (
        DEFAULT_LIBRARY_ROOT,
        DEFAULT_SAMPLE_CODE,
        ModulePreviewModel,
        PreviewBox,
        build_model_from_source,
        choose_initial_csv,
        format_mm,
        print_model_self_test,
        print_scan_summary,
        scan_library_csvs,
    )
except ImportError:
    from module_3d_preview_model import (
        DEFAULT_LIBRARY_ROOT,
        DEFAULT_SAMPLE_CODE,
        ModulePreviewModel,
        PreviewBox,
        build_model_from_source,
        choose_initial_csv,
        format_mm,
        print_model_self_test,
        print_scan_summary,
        scan_library_csvs,
    )


class Module3DView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._model: ModulePreviewModel | None = None
        self._root_entity: Qt3DCore.QEntity | None = None

        self.view = Qt3DExtras.Qt3DWindow()
        self.view.defaultFrameGraph().setClearColor(QColor("#eef2f6"))
        self.container = QWidget.createWindowContainer(self.view)
        self.container.setMinimumSize(620, 520)
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

    def set_model(self, model: ModulePreviewModel) -> None:
        self._model = model
        old_root = self._root_entity
        root = Qt3DCore.QEntity()
        self._root_entity = root

        self._add_light(root, QVector3D(model.width, model.height * 1.4, -model.depth * 1.4))
        self._add_light(root, QVector3D(-model.width, model.height * 0.7, model.depth))
        self._add_floor(root, model)
        for box in model.boxes:
            self._add_box(root, box)

        camera = self.view.camera()
        camera.lens().setPerspectiveProjection(38.0, 16.0 / 9.0, 0.1, 10000.0)
        self._set_perspective_camera()

        controller = Qt3DExtras.QOrbitCameraController(root)
        controller.setLinearSpeed(600.0)
        controller.setLookSpeed(180.0)
        controller.setCamera(camera)

        self.view.setRootEntity(root)
        if old_root is not None:
            old_root.deleteLater()

    def _add_light(self, root: Qt3DCore.QEntity, position: QVector3D) -> None:
        light_entity = Qt3DCore.QEntity(root)
        light = Qt3DRender.QPointLight(light_entity)
        light.setColor(QColor("#ffffff"))
        light.setIntensity(0.75)
        transform = Qt3DCore.QTransform(light_entity)
        transform.setTranslation(position)
        light_entity.addComponent(light)
        light_entity.addComponent(transform)

    def _add_floor(self, root: Qt3DCore.QEntity, model: ModulePreviewModel) -> None:
        floor = PreviewBox(
            name="Floor",
            piece_type="",
            size_x=max(model.width * 1.22, 500.0),
            size_y=4.0,
            size_z=max(model.depth * 1.22, 500.0),
            center_x=0,
            center_y=-4.0,
            center_z=0,
            color="#cfd6dd",
            opacity=0.32,
        )
        self._add_box(root, floor)

    def _add_box(self, root: Qt3DCore.QEntity, box: PreviewBox) -> None:
        entity = Qt3DCore.QEntity(root)

        mesh = Qt3DExtras.QCuboidMesh(entity)
        mesh.setXExtent(float(box.size_x))
        mesh.setYExtent(float(box.size_y))
        mesh.setZExtent(float(box.size_z))

        color = QColor(box.color)
        if box.opacity < 0.98:
            material = Qt3DExtras.QPhongAlphaMaterial(entity)
            material.setAlpha(float(box.opacity))
        else:
            material = Qt3DExtras.QPhongMaterial(entity)
        material.setDiffuse(color)
        material.setAmbient(color.darker(115))
        material.setSpecular(QColor("#ffffff"))

        transform = Qt3DCore.QTransform(entity)
        transform.setTranslation(QVector3D(float(box.center_x), float(box.center_y), float(box.center_z)))

        entity.addComponent(mesh)
        entity.addComponent(material)
        entity.addComponent(transform)

    def _set_camera(self, position: QVector3D, view_center: QVector3D) -> None:
        camera = self.view.camera()
        camera.setPosition(position)
        camera.setViewCenter(view_center)
        camera.setUpVector(QVector3D(0, 1, 0))

    def _set_perspective_camera(self) -> None:
        if self._model is None:
            return
        model = self._model
        center = QVector3D(0, model.height / 2, 0)
        position = QVector3D(model.width * 0.95, model.height * 0.85, -model.depth * 1.55)
        self._set_camera(position, center)

    def set_named_view(self, view_name: str) -> None:
        if self._model is None:
            return
        model = self._model
        center = QVector3D(0, model.height / 2, 0)
        distance = max(model.width, model.height, model.depth) * 1.75
        if view_name == "front":
            self._set_camera(QVector3D(0, model.height / 2, -distance), center)
        elif view_name == "top":
            self._set_camera(QVector3D(0, distance, 0.01), center)
        elif view_name == "side":
            self._set_camera(QVector3D(distance, model.height / 2, 0), center)
        else:
            self._set_perspective_camera()


class Module3DPreviewTestWindow(QMainWindow):
    def __init__(self, module_paths: list[Path], initial_csv: Path | None = None):
        super().__init__()
        self.setWindowTitle("Prueba visualizacion 3D de modulos - Qt3D")
        self.module_paths = module_paths
        self.current_model: ModulePreviewModel | None = None

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(8)
        controls.setMinimumWidth(330)
        controls.setMaximumWidth(430)

        title = QLabel("Prueba 3D - Qt3D")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        controls_layout.addWidget(title)

        self.module_combo = QComboBox()
        self.module_combo.setMinimumHeight(30)
        if self.module_paths:
            for path in self.module_paths:
                self.module_combo.addItem(path.parent.name, str(path))
        else:
            self.module_combo.addItem(f"{DEFAULT_SAMPLE_CODE} (muestra interna)", "")
        controls_layout.addWidget(QLabel("Modulo"))
        controls_layout.addWidget(self.module_combo)

        self.show_internal_checkbox = QCheckBox("Mostrar piezas internas")
        self.show_internal_checkbox.setChecked(True)
        controls_layout.addWidget(self.show_internal_checkbox)

        camera_row = QHBoxLayout()
        for label, view_name in [
            ("Persp.", "perspective"),
            ("Frente", "front"),
            ("Superior", "top"),
            ("Lateral", "side"),
        ]:
            button = QPushButton(label)
            button.setMinimumHeight(30)
            button.clicked.connect(lambda _checked=False, name=view_name: self.preview.set_named_view(name))
            camera_row.addWidget(button)
        controls_layout.addLayout(camera_row)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        controls_layout.addWidget(separator)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        controls_layout.addWidget(self.info_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumHeight(260)
        controls_layout.addWidget(self.details_text, 1)

        controls_layout.addStretch(1)

        self.preview = Module3DView()
        splitter.addWidget(controls)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.module_combo.currentIndexChanged.connect(self._load_selected_module)
        self.show_internal_checkbox.toggled.connect(lambda *_: self._load_selected_module())

        if initial_csv is not None:
            for index, path in enumerate(self.module_paths):
                if path == initial_csv:
                    self.module_combo.setCurrentIndex(index)
                    break
        self._load_selected_module()

    def _load_selected_module(self) -> None:
        csv_path_text = self.module_combo.currentData()
        csv_path = Path(csv_path_text) if csv_path_text else None
        model = build_model_from_source(csv_path=csv_path, show_internal=self.show_internal_checkbox.isChecked())

        self.current_model = model
        self.preview.set_model(model)
        self._refresh_details(model)

    def _refresh_details(self, model: ModulePreviewModel) -> None:
        source = str(model.source_path) if model.source_path else "muestra interna"
        display_boxes = [box for box in model.boxes if box.name != "Floor"]
        internal_count = sum(1 for box in display_boxes if box.is_internal)
        visible_count = len(display_boxes)
        self.info_label.setText(
            f"{model.name}\n"
            f"Medidas nominales: {format_mm(model.width)} x {format_mm(model.height)} x {format_mm(model.depth)} mm\n"
            f"Piezas CSV: {model.pieces_count} ({len(model.represented_piece_keys)} con regla 3D, "
            f"{len(model.omitted_pieces)} sin regla)\n"
            f"Cajas 3D: {visible_count} ({internal_count} internas)\n"
            f"Fuente: {source}"
        )

        lines = ["Piezas representadas:"]
        for box in display_boxes:
            internal = " interna" if box.is_internal else ""
            lines.append(
                f"- {box.piece_type} {box.name}: "
                f"{format_mm(box.size_x)} x {format_mm(box.size_y)} x {format_mm(box.size_z)} mm{internal}"
            )
        if model.omitted_pieces:
            lines.append("")
            lines.append("Piezas sin regla 3D:")
            lines.extend(f"- {name}" for name in model.omitted_pieces)
        self.details_text.setPlainText("\n".join(lines))


def run_self_test(module_paths: list[Path], requested_csv: Path | None) -> int:
    selected_csv = choose_initial_csv(module_paths, requested_csv)
    model = build_model_from_source(csv_path=selected_csv)
    return print_model_self_test(model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open a standalone Qt3D module preview test window.")
    parser.add_argument("--root", type=Path, default=DEFAULT_LIBRARY_ROOT, help="Maestro library root to scan.")
    parser.add_argument("--csv", type=Path, default=None, help="Specific module CSV to open.")
    parser.add_argument("--self-test", action="store_true", help="Build a preview model without opening the UI.")
    parser.add_argument("--scan-summary", action="store_true", help="Print a library scan summary without opening the UI.")
    parser.add_argument("--limit", type=int, default=0, help="Limit modules printed by --scan-summary.")
    args = parser.parse_args(argv)

    module_paths = scan_library_csvs(args.root)
    initial_csv = choose_initial_csv(module_paths, args.csv)

    if args.self_test:
        return run_self_test(module_paths, args.csv)
    if args.scan_summary:
        print_scan_summary(module_paths, limit=args.limit)
        return 0

    app = QApplication(sys.argv)
    window = Module3DPreviewTestWindow(module_paths, initial_csv)
    window.resize(1240, 760)
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
