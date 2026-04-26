"""Standalone 3D module preview test window.

This prototype is intentionally outside the main application flow. It reads a
Maestro module CSV, converts the known piece types into simple 3D boxes, and
renders them with Qt3D.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
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


DEFAULT_LIBRARY_ROOT = Path(r"S:\Maestro\Projects\01 - Mobile STD\01 - BM - Bajomesada")
DEFAULT_SAMPLE_CODE = "BM-2P-PC-800"
DEFAULT_HEIGHT_MM = 742.0
DEFAULT_DEPTH_MM = 580.0
DEFAULT_THICKNESS_MM = 18.0


@dataclass
class CsvPiece:
    row_code: str
    piece_type: str
    name: str
    quantity: int
    dim_a: float
    dim_b: float
    thickness: float
    material: str
    grain: str
    source: str


@dataclass
class PreviewBox:
    name: str
    piece_type: str
    size_x: float
    size_y: float
    size_z: float
    center_x: float
    center_y: float
    center_z: float
    color: str
    opacity: float = 1.0
    is_internal: bool = False


@dataclass
class ModulePreviewModel:
    name: str
    width: float
    height: float
    depth: float
    boxes: list[PreviewBox] = field(default_factory=list)
    omitted_pieces: list[str] = field(default_factory=list)
    source_path: Path | None = None


def _safe_float(value, default: float = 0.0) -> float:
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _safe_int(value, default: int = 1) -> int:
    try:
        return max(int(round(_safe_float(value, default))), 1)
    except (TypeError, ValueError):
        return default


def _format_mm(value: float) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.1f}"


def _extract_nominal_numbers(module_name: str) -> list[float]:
    return [_safe_float(match) for match in re.findall(r"(?<![A-Za-z])(\d+(?:[.,]\d+)?)(?![A-Za-z])", module_name)]


def _read_maestro_csv(csv_path: Path) -> list[CsvPiece]:
    pieces: list[CsvPiece] = []
    with csv_path.open("r", encoding="latin-1", newline="") as file:
        for row in csv.reader(file, delimiter=";"):
            if len(row) < 11:
                continue
            pieces.append(
                CsvPiece(
                    row_code=str(row[0]).strip(),
                    piece_type=str(row[1]).strip(),
                    name=str(row[2]).strip(),
                    quantity=_safe_int(row[3]),
                    dim_a=_safe_float(row[5]),
                    dim_b=_safe_float(row[6]),
                    thickness=_safe_float(row[7]),
                    material=str(row[8]).strip(),
                    grain=str(row[9]).strip(),
                    source=str(row[10]).strip(),
                )
            )
    return pieces


def _builtin_sample_pieces() -> list[CsvPiece]:
    raw_rows = [
        ("1FSX", "F1", "Lateral_Izq", 1, 742, 580, 18, "BCO18", "0", "Lateral_Izq.pgmx"),
        ("2FDX", "F2", "Lateral_Der", 1, 742, 580, 18, "BCO18", "0", "Lateral_Der.pgmx"),
        ("3CP", "T", "Tapa", 1, 764, 580, 0, "BCO00", "0", "Tapa.pgmx"),
        ("4BS", "B", "Fondo", 1, 799.1, 580, 18, "BCO18", "0", "Fondo.pgmx"),
        ("5RP", "R", "Estante", 1, 764, 547, 18, "BCO18", "0", "Estante.pgmx"),
        ("6ANSX", "A1", "Puerta_Izq", 1, 723.1, 396.1, 18, "GAUDI18", "1", "Puerta_Izq.pgmx"),
        ("7ANDX", "A2", "Puerta_Der", 1, 723.1, 396.1, 18, "GAUDI18", "1", "Puerta_Der.pgmx"),
        ("8SCH", "S", "Trasera", 1, 717, 784, 3, "BCO3", "0", "Trasera.pgmx"),
        ("9PBF", "D2", "Faja frontal", 2, 70, 764, 18, "BCO18", "0", "Faja frontal.pgmx"),
    ]
    return [
        CsvPiece(
            row_code=row_code,
            piece_type=piece_type,
            name=name,
            quantity=int(quantity),
            dim_a=float(dim_a),
            dim_b=float(dim_b),
            thickness=float(thickness),
            material=material,
            grain=grain,
            source=source,
        )
        for row_code, piece_type, name, quantity, dim_a, dim_b, thickness, material, grain, source in raw_rows
    ]


def _scan_library_csvs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*.csv")
        if path.parent.name.casefold() == path.stem.casefold()
    )


def _infer_dimensions(module_name: str, pieces: list[CsvPiece]) -> tuple[float, float, float]:
    nominal_numbers = _extract_nominal_numbers(module_name)
    width = nominal_numbers[-1] if nominal_numbers else 0.0
    depth = DEFAULT_DEPTH_MM

    if len(nominal_numbers) >= 2 and nominal_numbers[-2] < 300 <= nominal_numbers[-1]:
        width = nominal_numbers[-2]
        depth = nominal_numbers[-1]

    laterals = [piece for piece in pieces if piece.piece_type in {"F1", "F2"}]
    height_candidates = [piece.dim_a for piece in laterals if piece.dim_a > 0]
    depth_candidates = [piece.dim_b for piece in laterals if piece.dim_b > 0]

    height = max(height_candidates) if height_candidates else DEFAULT_HEIGHT_MM
    if depth_candidates:
        depth = max(depth_candidates)

    if width <= 0:
        width_candidates = []
        for piece in pieces:
            if piece.piece_type in {"B", "S", "T", "R"}:
                width_candidates.extend([piece.dim_a, piece.dim_b])
        width = max(width_candidates) if width_candidates else 800.0

    return float(width), float(height), float(depth)


def _panel_thickness(piece: CsvPiece) -> float:
    return piece.thickness if piece.thickness > 0 else DEFAULT_THICKNESS_MM


def _material_color(material: str, piece_type: str) -> str:
    normalized = str(material or "").casefold()
    if "gaudi" in normalized:
        return "#b47d48"
    if "bc" in normalized or "bco" in normalized:
        if piece_type in {"S", "E"}:
            return "#d9dde3"
        return "#f3f1e9"
    if piece_type in {"A1", "A2", "H"}:
        return "#aa7a4b"
    return "#ccd4dd"


def _append_box(
    model: ModulePreviewModel,
    piece: CsvPiece,
    *,
    size_x: float,
    size_y: float,
    size_z: float,
    center_x: float,
    center_y: float,
    center_z: float,
    opacity: float = 1.0,
    is_internal: bool = False,
    suffix: str = "",
) -> None:
    model.boxes.append(
        PreviewBox(
            name=f"{piece.name}{suffix}",
            piece_type=piece.piece_type,
            size_x=max(float(size_x), 1.0),
            size_y=max(float(size_y), 1.0),
            size_z=max(float(size_z), 1.0),
            center_x=float(center_x),
            center_y=float(center_y),
            center_z=float(center_z),
            color=_material_color(piece.material, piece.piece_type),
            opacity=float(opacity),
            is_internal=is_internal,
        )
    )


def _front_panel_entries(pieces: list[CsvPiece]) -> list[tuple[CsvPiece, float, float]]:
    fronts: list[tuple[CsvPiece, float, float]] = []
    for piece in pieces:
        is_door = piece.piece_type in {"A1", "A2"} and "puerta" in piece.name.casefold()
        if not is_door:
            continue
        for _ in range(piece.quantity):
            fronts.append((piece, piece.dim_b, piece.dim_a))
    return fronts


def _drawer_front_entries(pieces: list[CsvPiece]) -> list[tuple[CsvPiece, float, float]]:
    fronts: list[tuple[CsvPiece, float, float]] = []
    for piece in pieces:
        normalized_name = piece.name.casefold()
        if piece.piece_type != "H" or "cajon" not in normalized_name:
            continue
        for _ in range(piece.quantity):
            fronts.append((piece, piece.dim_b, piece.dim_a))
    return fronts


def build_preview_model(
    module_name: str,
    pieces: list[CsvPiece],
    source_path: Path | None = None,
    *,
    show_internal: bool = True,
) -> ModulePreviewModel:
    width, height, depth = _infer_dimensions(module_name, pieces)
    model = ModulePreviewModel(module_name, width, height, depth, source_path=source_path)

    for piece in pieces:
        t = _panel_thickness(piece)
        piece_type = piece.piece_type
        normalized_name = piece.name.casefold()

        if piece_type == "F1":
            _append_box(
                model,
                piece,
                size_x=t,
                size_y=piece.dim_a or height,
                size_z=piece.dim_b or depth,
                center_x=-width / 2 + t / 2,
                center_y=(piece.dim_a or height) / 2,
                center_z=0,
            )
            continue

        if piece_type == "F2":
            _append_box(
                model,
                piece,
                size_x=t,
                size_y=piece.dim_a or height,
                size_z=piece.dim_b or depth,
                center_x=width / 2 - t / 2,
                center_y=(piece.dim_a or height) / 2,
                center_z=0,
            )
            continue

        if piece_type == "T":
            _append_box(
                model,
                piece,
                size_x=piece.dim_a or max(width - 2 * t, 1),
                size_y=t,
                size_z=piece.dim_b or depth,
                center_x=0,
                center_y=height - t / 2,
                center_z=0,
                is_internal=True,
            )
            continue

        if piece_type == "B":
            _append_box(
                model,
                piece,
                size_x=piece.dim_a or width,
                size_y=t,
                size_z=piece.dim_b or depth,
                center_x=0,
                center_y=t / 2,
                center_z=0,
                is_internal=True,
            )
            continue

        if piece_type == "R":
            for index in range(piece.quantity):
                step = height / (piece.quantity + 1)
                y = step * (index + 1)
                _append_box(
                    model,
                    piece,
                    size_x=piece.dim_a or max(width - 2 * t, 1),
                    size_y=t,
                    size_z=piece.dim_b or max(depth - 30, 1),
                    center_x=0,
                    center_y=y,
                    center_z=0,
                    opacity=0.82,
                    is_internal=True,
                    suffix=f" {index + 1}" if piece.quantity > 1 else "",
                )
            continue

        if piece_type == "S":
            _append_box(
                model,
                piece,
                size_x=piece.dim_b or max(width - 16, 1),
                size_y=piece.dim_a or max(height - 25, 1),
                size_z=max(t, 3),
                center_x=0,
                center_y=(piece.dim_a or height) / 2,
                center_z=depth / 2 - max(t, 3) / 2,
                opacity=0.45,
                is_internal=True,
            )
            continue

        if piece_type in {"D1", "D2"} and "faja" in normalized_name:
            faja_height = piece.dim_a if piece.dim_a < piece.dim_b else piece.dim_b
            faja_width = piece.dim_b if piece.dim_b >= piece.dim_a else piece.dim_a
            positions = [height - faja_height / 2]
            if piece.quantity > 1:
                positions = [faja_height / 2, height - faja_height / 2]
            for index, y in enumerate(positions[: piece.quantity]):
                _append_box(
                    model,
                    piece,
                    size_x=faja_width,
                    size_y=faja_height,
                    size_z=t,
                    center_x=0,
                    center_y=y,
                    center_z=-depth / 2 - t / 2,
                    opacity=0.72,
                    is_internal=True,
                    suffix=f" {index + 1}" if len(positions) > 1 else "",
                )
            continue

    door_entries = _front_panel_entries(pieces)
    if door_entries:
        total_width = sum(entry[1] for entry in door_entries)
        x = -total_width / 2
        for piece, door_width, door_height in door_entries:
            t = _panel_thickness(piece)
            x += door_width / 2
            _append_box(
                model,
                piece,
                size_x=door_width,
                size_y=door_height,
                size_z=t,
                center_x=x,
                center_y=door_height / 2,
                center_z=-depth / 2 - t / 2,
                opacity=0.86,
            )
            x += door_width / 2

    drawer_entries = _drawer_front_entries(pieces)
    if drawer_entries:
        gap = 4.0
        total_height = sum(entry[2] for entry in drawer_entries) + gap * (len(drawer_entries) - 1)
        y = max((height - total_height) / 2, gap)
        for piece, front_width, front_height in drawer_entries:
            t = _panel_thickness(piece)
            y += front_height / 2
            _append_box(
                model,
                piece,
                size_x=front_width,
                size_y=front_height,
                size_z=t,
                center_x=0,
                center_y=y,
                center_z=-depth / 2 - t / 2,
                opacity=0.88,
            )
            y += front_height / 2 + gap

    represented_names = {box.name.split(" ")[0] for box in model.boxes}
    for piece in pieces:
        if piece.name not in represented_names and piece.piece_type not in {"A1", "A2", "H"}:
            if show_internal:
                model.omitted_pieces.append(f"{piece.piece_type} {piece.name}")
            continue

    if not show_internal:
        model.boxes = [box for box in model.boxes if not box.is_internal]

    return model


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
        self.setWindowTitle("Prueba visualizacion 3D de modulos")
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

        title = QLabel("Prueba 3D")
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
        show_internal = self.show_internal_checkbox.isChecked()

        if csv_path is not None and csv_path.is_file():
            pieces = _read_maestro_csv(csv_path)
            model = build_preview_model(csv_path.parent.name, pieces, csv_path, show_internal=show_internal)
        else:
            pieces = _builtin_sample_pieces()
            model = build_preview_model(DEFAULT_SAMPLE_CODE, pieces, None, show_internal=show_internal)

        self.current_model = model
        self.preview.set_model(model)
        self._refresh_details(model)

    def _refresh_details(self, model: ModulePreviewModel) -> None:
        source = str(model.source_path) if model.source_path else "muestra interna"
        internal_count = sum(1 for box in model.boxes if box.is_internal)
        visible_count = len(model.boxes)
        self.info_label.setText(
            f"{model.name}\n"
            f"Medidas nominales: {_format_mm(model.width)} x {_format_mm(model.height)} x {_format_mm(model.depth)} mm\n"
            f"Cajas 3D: {visible_count} ({internal_count} internas)\n"
            f"Fuente: {source}"
        )

        lines = ["Piezas representadas:"]
        for box in model.boxes:
            if box.name == "Floor":
                continue
            internal = " interna" if box.is_internal else ""
            lines.append(
                f"- {box.piece_type} {box.name}: "
                f"{_format_mm(box.size_x)} x {_format_mm(box.size_y)} x {_format_mm(box.size_z)} mm{internal}"
            )
        if model.omitted_pieces:
            lines.append("")
            lines.append("Piezas sin regla 3D:")
            lines.extend(f"- {name}" for name in model.omitted_pieces)
        self.details_text.setPlainText("\n".join(lines))


def _choose_initial_csv(module_paths: list[Path], requested_csv: Path | None) -> Path | None:
    if requested_csv is not None and requested_csv.is_file():
        return requested_csv
    for path in module_paths:
        if path.stem.casefold() == DEFAULT_SAMPLE_CODE.casefold():
            return path
    return module_paths[0] if module_paths else None


def run_self_test(module_paths: list[Path], requested_csv: Path | None) -> int:
    selected_csv = _choose_initial_csv(module_paths, requested_csv)
    if selected_csv is not None:
        pieces = _read_maestro_csv(selected_csv)
        model = build_preview_model(selected_csv.parent.name, pieces, selected_csv)
    else:
        pieces = _builtin_sample_pieces()
        model = build_preview_model(DEFAULT_SAMPLE_CODE, pieces, None)
    print(f"module={model.name}")
    print(f"dimensions={_format_mm(model.width)}x{_format_mm(model.height)}x{_format_mm(model.depth)}")
    print(f"source={model.source_path or 'builtin'}")
    print(f"boxes={len(model.boxes)}")
    print(f"omitted={len(model.omitted_pieces)}")
    return 0 if model.boxes else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open a standalone Qt3D module preview test window.")
    parser.add_argument("--root", type=Path, default=DEFAULT_LIBRARY_ROOT, help="Maestro library root to scan.")
    parser.add_argument("--csv", type=Path, default=None, help="Specific module CSV to open.")
    parser.add_argument("--self-test", action="store_true", help="Build a preview model without opening the UI.")
    args = parser.parse_args(argv)

    module_paths = _scan_library_csvs(args.root)
    initial_csv = _choose_initial_csv(module_paths, args.csv)

    if args.self_test:
        return run_self_test(module_paths, args.csv)

    app = QApplication(sys.argv)
    window = Module3DPreviewTestWindow(module_paths, initial_csv)
    window.resize(1240, 760)
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
