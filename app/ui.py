"""Interfaz gráfica principal para gestión de proyectos CNC.

Contiene ventana principal con creación, apertura, limpieza,
archivado y selección de carpeta raíz de proyecto.
Incluye ventana de detalle de proyecto con edición.
"""

import datetime
import json
import os
import shutil
from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QLineEdit,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QCheckBox,
    QRadioButton,
)
from PySide6.QtSvgWidgets import QSvgWidget

from core.model import LocaleData, Project, ModuleData, Piece

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_REGISTRY = BASE_DIR / "projects_list.json"
APP_SETTINGS_FILE = BASE_DIR / "app_settings.json"
ARCHIVE_DIR = BASE_DIR / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)

MAIN_ACTION_BUTTON_WIDTH = 96
MAIN_ACTION_BUTTON_HEIGHT = 40

BOARD_GRAIN_OPTIONS = [
    "0 - Sin Veta",
    "1 - Longitudinal",
    "2 - Transversal",
]

CUT_OPTIMIZATION_OPTIONS = [
    "Sin optimizar",
    "Optimización longitudinal",
    "Optimización transversal",
]


def _normalize_registry_entries(raw_registry) -> list[dict]:
    entries: list[dict] = []

    if isinstance(raw_registry, dict):
        for project_name, raw_entry in raw_registry.items():
            if not isinstance(raw_entry, dict):
                continue
            entries.append(
                {
                    "project_name": str(raw_entry.get("name") or project_name).strip() or str(project_name).strip(),
                    "client_name": str(raw_entry.get("client") or "").strip(),
                    "source_folder": str(raw_entry.get("root_directory") or "").strip(),
                    "project_data_file": str(raw_entry.get("project_data_file") or f"{project_name}.json").strip(),
                }
            )
        return entries

    if isinstance(raw_registry, list):
        for raw_entry in raw_registry:
            if not isinstance(raw_entry, dict):
                continue
            project_name = str(raw_entry.get("project_name") or raw_entry.get("name") or "").strip()
            source_folder = str(raw_entry.get("source_folder") or raw_entry.get("root_directory") or "").strip()
            project_data_file = str(raw_entry.get("project_data_file") or "").strip()
            if not project_name or not source_folder or not project_data_file:
                continue
            entries.append(
                {
                    "project_name": project_name,
                    "client_name": str(raw_entry.get("client_name") or raw_entry.get("client") or "").strip(),
                    "source_folder": source_folder,
                    "project_data_file": project_data_file,
                }
            )
    return entries


def _read_registry() -> list[dict]:
    """Leer el archivo de registro de proyectos existentes."""
    if not PROJECT_REGISTRY.exists():
        return []
    with PROJECT_REGISTRY.open("r", encoding="utf-8") as f:
        return _normalize_registry_entries(json.load(f))


def _write_registry(registry: list[dict]):
    """Actualizar el archivo de registro de proyectos."""
    with PROJECT_REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def _find_registry_entry(project_name: str) -> dict | None:
    normalized_name = str(project_name or "").strip().lower()
    for entry in _read_registry():
        if str(entry.get("project_name") or "").strip().lower() == normalized_name:
            return entry
    return None


def _default_app_settings() -> dict:
    """Configuración por defecto de la aplicación."""
    return {
        "minimum_machinable_dimension": 150,
        "cut_board_width": 1830,
        "cut_board_height": 2750,
        "cut_piece_gap": 0,
        "cut_squaring_allowance": 10,
        "cut_saw_kerf": 4,
        "cut_optimization_mode": CUT_OPTIMIZATION_OPTIONS[0],
        "available_boards": [],
    }


def _compact_number(value):
    number = float(value)
    return int(number) if number.is_integer() else round(number, 2)


def _coerce_setting_number(value, default: float, minimum: float | None = None) -> float:
    raw = "" if value is None else str(value).strip()
    if not raw:
        return float(default)
    try:
        number = float(raw.replace(",", "."))
    except ValueError:
        return float(default)
    if minimum is not None and number < minimum:
        return float(default)
    return number


def _normalize_board_grain(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"0", "0 - sin veta", "sin veta"}:
        return BOARD_GRAIN_OPTIONS[0]
    if raw in {"1", "1 - longitudinal", "longitudinal"}:
        return BOARD_GRAIN_OPTIONS[1]
    if raw in {"2", "2 - transversal", "transversal"}:
        return BOARD_GRAIN_OPTIONS[2]
    return BOARD_GRAIN_OPTIONS[0]


def _normalize_cut_optimization_option(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"optimización longitudinal", "optimizacion longitudinal", "longitudinal"}:
        return CUT_OPTIMIZATION_OPTIONS[1]
    if raw in {"optimización transversal", "optimizacion transversal", "transversal"}:
        return CUT_OPTIMIZATION_OPTIONS[2]
    return CUT_OPTIMIZATION_OPTIONS[0]


def _normalize_board_entry(board_data: dict) -> dict | None:
    if not isinstance(board_data, dict):
        return None

    color = str(board_data.get("color") or "").strip()
    grain = _normalize_board_grain(board_data.get("grain") or board_data.get("veta"))
    margin = _coerce_setting_number(board_data.get("margin"), 0.0, minimum=0.0)

    try:
        length = float(str(board_data.get("length") or "").replace(",", "."))
        width = float(str(board_data.get("width") or "").replace(",", "."))
        thickness = float(str(board_data.get("thickness") or "").replace(",", "."))
    except (TypeError, ValueError):
        return None

    if not color or length <= 0 or width <= 0 or thickness <= 0:
        return None
    if margin * 2 >= min(length, width):
        return None

    return {
        "color": color,
        "length": _compact_number(length),
        "width": _compact_number(width),
        "thickness": _compact_number(thickness),
        "grain": grain,
        "margin": _compact_number(margin),
    }


def _normalize_available_boards(raw_boards) -> list[dict]:
    boards: list[dict] = []
    for board_data in raw_boards or []:
        normalized = _normalize_board_entry(board_data)
        if normalized is not None:
            boards.append(normalized)
    return boards


def _read_app_settings() -> dict:
    """Leer configuración general de la aplicación."""
    settings = _default_app_settings()
    if not APP_SETTINGS_FILE.exists():
        return settings
    try:
        saved_settings = json.loads(APP_SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return settings
    settings.update(saved_settings)
    settings["available_boards"] = _normalize_available_boards(settings.get("available_boards"))
    settings["cut_optimization_mode"] = _normalize_cut_optimization_option(settings.get("cut_optimization_mode"))
    settings["cut_piece_gap"] = _compact_number(_coerce_setting_number(settings.get("cut_piece_gap"), 0.0, minimum=0.0))
    settings["cut_squaring_allowance"] = _compact_number(_coerce_setting_number(settings.get("cut_squaring_allowance"), 10.0, minimum=0.0))
    settings["cut_saw_kerf"] = _compact_number(_coerce_setting_number(settings.get("cut_saw_kerf"), 4.0, minimum=0.0))
    return settings


def _write_app_settings(settings: dict):
    """Persistir configuración general de la aplicación."""
    merged_settings = _default_app_settings()
    merged_settings.update(settings)
    merged_settings["available_boards"] = _normalize_available_boards(merged_settings.get("available_boards"))
    merged_settings["cut_optimization_mode"] = _normalize_cut_optimization_option(merged_settings.get("cut_optimization_mode"))
    merged_settings["cut_piece_gap"] = _compact_number(_coerce_setting_number(merged_settings.get("cut_piece_gap"), 0.0, minimum=0.0))
    merged_settings["cut_squaring_allowance"] = _compact_number(_coerce_setting_number(merged_settings.get("cut_squaring_allowance"), 10.0, minimum=0.0))
    merged_settings["cut_saw_kerf"] = _compact_number(_coerce_setting_number(merged_settings.get("cut_saw_kerf"), 4.0, minimum=0.0))
    APP_SETTINGS_FILE.write_text(
        json.dumps(merged_settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _normalize_project_locales(value, legacy_local: str = "") -> list[LocaleData]:
    locales: list[LocaleData] = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, LocaleData):
                name = str(item.name or "").strip()
                path = str(item.path or name).strip()
                try:
                    modules_count = int(item.modules_count or 0)
                except (TypeError, ValueError):
                    modules_count = 0
                if name and path:
                    locales.append(LocaleData(name=name, path=path, modules_count=max(0, modules_count)))
            elif isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                path = str(item.get("path") or name).strip()
                modules_count = item.get("modules_count", 0)
                try:
                    modules_count = int(modules_count or 0)
                except (TypeError, ValueError):
                    modules_count = 0
                if name and path:
                    locales.append(LocaleData(name=name, path=path, modules_count=max(0, modules_count)))
            else:
                name = str(item or "").strip()
                if name:
                    locales.append(LocaleData(name=name, path=name, modules_count=0))

    legacy_local = str(legacy_local or "").strip()
    if not locales and legacy_local:
        locales = [LocaleData(name=legacy_local, path=legacy_local, modules_count=0)]

    return locales


def _project_data_path(project: Project) -> Path:
    return Path(project.root_directory) / project.project_data_file


def _project_data_path_from_registry_entry(entry: dict) -> Path:
    return Path(str(entry.get("source_folder") or "").strip()) / str(entry.get("project_data_file") or "").strip()


def _registry_entry_is_accessible(entry: dict) -> bool:
    source_folder = str(entry.get("source_folder") or "").strip()
    if not source_folder:
        return False
    try:
        return Path(source_folder).exists()
    except OSError:
        return False


def _window_available_geometry(widget: QWidget):
    screen = None
    try:
        screen = widget.screen()
    except Exception:
        screen = None

    if screen is None:
        try:
            parent_widget = widget.parentWidget()
        except Exception:
            parent_widget = None
        if parent_widget is not None:
            try:
                screen = parent_widget.screen()
            except Exception:
                screen = None

    if screen is None:
        try:
            handle = widget.windowHandle()
        except Exception:
            handle = None
        if handle is not None:
            screen = handle.screen()

    if screen is None:
        app = QApplication.instance()
        if app is not None:
            screen = app.primaryScreen()

    return None if screen is None else screen.availableGeometry()


def _scaled_int(value: int | float, scale: float, minimum: int | None = None) -> int:
    scaled_value = int(round(float(value) * float(scale)))
    if minimum is not None:
        return max(int(minimum), scaled_value)
    return scaled_value


def _apply_responsive_window_size(
    widget: QWidget,
    desired_width: int,
    desired_height: int,
    *,
    width_ratio: float = 0.94,
    height_ratio: float = 0.90,
    min_font_size: float = 8.0,
) -> tuple[float, int, int]:
    available = _window_available_geometry(widget)
    target_width = int(desired_width)
    target_height = int(desired_height)
    if available is not None:
        target_width = min(target_width, max(360, int(available.width() * width_ratio)))
        target_height = min(target_height, max(280, int(available.height() * height_ratio)))

    scale = min(
        target_width / max(1, int(desired_width)),
        target_height / max(1, int(desired_height)),
        1.0,
    )

    current_font = widget.font()
    current_size = current_font.pointSizeF()
    if current_size <= 0:
        current_size = float(current_font.pointSize() if current_font.pointSize() > 0 else 9.0)

    font_scale = max(scale, 0.82)
    scaled_font_size = max(float(min_font_size), round(current_size * font_scale, 1))
    if scaled_font_size < current_size:
        current_font.setPointSizeF(scaled_font_size)
        widget.setFont(current_font)

    widget.resize(target_width, target_height)
    return scale, target_width, target_height


def _register_project(project: Project):
    """Agregar o actualizar un proyecto al registro global."""
    registry = _read_registry()
    registry = [
        entry
        for entry in registry
        if str(entry.get("project_name") or "").strip().lower() != project.name.strip().lower()
    ]
    registry.append(
        {
            "project_name": project.name,
            "client_name": project.client,
            "source_folder": project.root_directory,
            "project_data_file": project.project_data_file,
        }
    )
    _write_registry(registry)


def _unregister_project(project_name: str):
    """Eliminar un proyecto del registro global."""
    normalized_name = str(project_name or "").strip().lower()
    registry = [
        entry
        for entry in _read_registry()
        if str(entry.get("project_name") or "").strip().lower() != normalized_name
    ]
    _write_registry(registry)


def _save_project(project: Project):
    """Guardar proyecto en su carpeta raíz y actualizar registro global."""
    project.locales = _normalize_project_locales(getattr(project, "locales", []))
    for locale in project.locales:
        try:
            locale.modules_count = int(locale.modules_count or 0)
        except (TypeError, ValueError):
            locale.modules_count = 0
    project_file = _project_data_path(project)
    project_file.parent.mkdir(parents=True, exist_ok=True)
    project_file.write_text(
        json.dumps(project.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _register_project(project)


def _coerce_optional_piece_float_fields(piece_data: dict, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        if field_name not in piece_data:
            continue
        field_value = piece_data[field_name]
        if field_value == "" or field_value is None:
            piece_data[field_name] = None
            continue
        try:
            piece_data[field_name] = float(field_value)
        except (ValueError, TypeError):
            piece_data[field_name] = None


def _read_json_file(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _coerce_required_piece_float_fields(piece_data: dict, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        raw_value = piece_data.get(field_name)
        if raw_value == "" or raw_value is None:
            piece_data[field_name] = 0.0
            continue
        try:
            piece_data[field_name] = float(raw_value)
        except (ValueError, TypeError):
            piece_data[field_name] = 0.0


def _coerce_piece_quantity_field(piece_data: dict, field_name: str = "quantity") -> None:
    raw_value = piece_data.get(field_name)
    if raw_value == "" or raw_value is None:
        piece_data[field_name] = 1
        return
    try:
        quantity = int(float(raw_value))
    except (ValueError, TypeError):
        quantity = 1
    piece_data[field_name] = quantity if quantity > 0 else 1


def _load_pieces_from_config_rows(piece_rows, module_name: str) -> list[Piece]:
    pieces: list[Piece] = []
    if not isinstance(piece_rows, list):
        return pieces

    piece_fields = {
        "id", "width", "height", "thickness", "quantity",
        "color", "grain_direction", "name", "module_name",
        "cnc_source", "f6_source", "piece_type", "program_width", "program_height", "program_thickness",
    }

    for piece_row in piece_rows:
        if not isinstance(piece_row, dict):
            continue

        normalized_row = dict(piece_row)
        if "source" in normalized_row and "cnc_source" not in normalized_row:
            normalized_row["cnc_source"] = normalized_row.get("source")
        if not str(normalized_row.get("module_name") or "").strip():
            normalized_row["module_name"] = module_name

        filtered_row = {key: value for key, value in normalized_row.items() if key in piece_fields}
        _coerce_required_piece_float_fields(filtered_row, ("width", "height"))
        _coerce_optional_piece_float_fields(
            filtered_row,
            ("thickness", "program_width", "program_height", "program_thickness"),
        )
        _coerce_piece_quantity_field(filtered_row)

        piece_id = str(filtered_row.get("id") or "").strip()
        if not piece_id:
            continue
        filtered_row["id"] = piece_id

        try:
            pieces.append(Piece(**filtered_row))
        except Exception:
            continue

    return pieces


def _module_relative_path(project_root: Path, module_path: Path, fallback: str = "") -> str:
    try:
        return str(module_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return fallback


def _load_module_from_saved_config(
    *,
    project_root: Path,
    module_path: Path,
    locale_name: str = "",
    module_name_hint: str = "",
    relative_path_hint: str = "",
) -> ModuleData:
    config_path = module_path / "module_config.json"
    config_data = _read_json_file(config_path)
    if not isinstance(config_data, dict):
        config_data = {}

    module_name = str(config_data.get("module") or module_name_hint or module_path.name).strip() or module_path.name
    relative_path = _module_relative_path(project_root, module_path, relative_path_hint) or relative_path_hint
    pieces = _load_pieces_from_config_rows(config_data.get("pieces", []), module_name)

    return ModuleData(
        name=module_name,
        path=str(module_path),
        locale_name=locale_name,
        relative_path=relative_path,
        pieces=pieces,
    )


def _load_saved_modules_for_locale(project_root: Path, locale: LocaleData) -> list[ModuleData]:
    locale_path = project_root / locale.path
    modules_by_key: dict[str, ModuleData] = {}

    local_config_data = _read_json_file(locale_path / "local_config.json")
    if isinstance(local_config_data, dict):
        saved_modules = local_config_data.get("modules", [])
        if isinstance(saved_modules, list):
            for module_row in saved_modules:
                if not isinstance(module_row, dict):
                    continue
                module_name = str(module_row.get("name") or "").strip()
                module_relative_from_locale = str(module_row.get("path") or module_name).strip()
                if not module_relative_from_locale:
                    continue

                module_path = locale_path / module_relative_from_locale
                relative_path_hint = str((Path(locale.path) / module_relative_from_locale)).replace("\\", "/")
                module = _load_module_from_saved_config(
                    project_root=project_root,
                    module_path=module_path,
                    locale_name=locale.name,
                    module_name_hint=module_name,
                    relative_path_hint=relative_path_hint,
                )
                module_key = (module.relative_path or str(module.path)).lower()
                modules_by_key[module_key] = module

    if locale_path.exists():
        for child in sorted(locale_path.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir() or not (child / "module_config.json").exists():
                continue
            module = _load_module_from_saved_config(
                project_root=project_root,
                module_path=child,
                locale_name=locale.name,
            )
            module_key = (module.relative_path or str(module.path)).lower()
            modules_by_key.setdefault(module_key, module)

    return sorted(
        modules_by_key.values(),
        key=lambda module: ((module.locale_name or "").lower(), module.name.lower()),
    )


def _discover_saved_locales(project_root: Path, locales: list[LocaleData]) -> list[LocaleData]:
    locale_map: dict[str, LocaleData] = {}

    for locale in _normalize_project_locales(locales):
        locale_key = str(locale.path or locale.name).strip().lower()
        if not locale_key:
            continue
        locale_map[locale_key] = locale

    if project_root.exists():
        for child in sorted(project_root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir():
                continue
            has_local_config = (child / "local_config.json").exists()
            has_saved_modules = any(
                grandchild.is_dir() and (grandchild / "module_config.json").exists()
                for grandchild in child.iterdir()
            )
            if not has_local_config and not has_saved_modules:
                continue

            locale_path = str(child.relative_to(project_root)).replace("\\", "/")
            locale_key = locale_path.lower()
            if locale_key not in locale_map:
                locale_map[locale_key] = LocaleData(name=child.name, path=locale_path, modules_count=0)

    return sorted(locale_map.values(), key=lambda locale: locale.name.lower())


def _load_saved_modules(project_root: Path, locales: list[LocaleData]) -> tuple[list[LocaleData], list[ModuleData]]:
    resolved_locales = _discover_saved_locales(project_root, locales)
    modules: list[ModuleData] = []

    for locale in resolved_locales:
        locale_modules = _load_saved_modules_for_locale(project_root, locale)
        locale.modules_count = len(locale_modules)
        modules.extend(locale_modules)

    if not resolved_locales and project_root.exists():
        loose_modules: list[ModuleData] = []
        for child in sorted(project_root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir() or not (child / "module_config.json").exists():
                continue
            loose_modules.append(
                _load_module_from_saved_config(
                    project_root=project_root,
                    module_path=child,
                )
            )
        return resolved_locales, loose_modules

    return resolved_locales, modules


def _load_project(name: str) -> Project:
    """Cargar proyecto desde su archivo JSON en disco usando el registro global."""
    registry_entry = _find_registry_entry(name)
    if registry_entry is None:
        raise FileNotFoundError(f"Proyecto '{name}' no encontrado en registro")

    project_root = str(registry_entry.get("source_folder") or "").strip()
    project_data_file = str(registry_entry.get("project_data_file") or "").strip()
    project_file = _project_data_path_from_registry_entry(registry_entry)
    if not project_file.exists():
        raise FileNotFoundError(project_file)

    data = json.loads(project_file.read_text(encoding="utf-8"))
    project_name = str(data.get("project_name") or data.get("name") or name).strip()
    client_name = str(data.get("client_name") or data.get("client") or registry_entry.get("client_name") or "").strip()
    locales = _normalize_project_locales(data.get("locales"), data.get("local", ""))

    project = Project(
        name=project_name,
        root_directory=project_root,
        project_data_file=project_data_file,
        client=client_name,
        created_at=data.get("created_at", ""),
        locales=locales,
        modules=[],
    )

    saved_locales, saved_modules = _load_saved_modules(Path(project.root_directory), project.locales)
    if saved_locales:
        project.locales = saved_locales
    project.modules = saved_modules

    return project


class ProjectDetailWindow(QMainWindow):
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

        btn_edit = QPushButton("Editar")
        btn_process = QPushButton("Procesar")
        btn_modules = QPushButton("Ver\nmódulos")
        btn_drawings = QPushButton("Generar\nImágenes")
        btn_sheets = QPushButton("Generar\nPlanillas")
        btn_cuts = QPushButton("Diagramas\nde Corte")
        btn_close = QPushButton("Cerrar")

        for button in (
            btn_edit,
            btn_process,
            btn_modules,
            btn_sheets,
            btn_cuts,
            btn_drawings,
            btn_close,
        ):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

        top_action_row = QHBoxLayout()
        top_action_row.addWidget(btn_edit)
        top_action_row.addWidget(btn_process)
        top_action_row.addStretch(1)

        layout.addLayout(header_row)
        layout.addWidget(self.lbl_root)
        layout.addLayout(dates_row)
        layout.addLayout(top_action_row)
        layout.addWidget(self.lbl_locales_count)

        locales_and_actions_row = QHBoxLayout()
        locales_and_actions_row.addWidget(self.locales_list, 1)

        actions_column = QVBoxLayout()
        actions_column.setContentsMargins(0, 0, 0, 0)
        actions_column.addWidget(btn_modules)
        actions_column.addWidget(btn_drawings)
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
        self.btn_modules.clicked.connect(self.show_modules)
        self.locales_list.itemDoubleClicked.connect(lambda *_: self.show_modules())

        btn_edit.clicked.connect(self.edit_project)
        btn_process.clicked.connect(self.process_project)
        btn_sheets.clicked.connect(self.generate_sheets)
        btn_cuts.clicked.connect(self.show_cuts)
        btn_drawings.clicked.connect(self.generate_drawings_only)
        btn_close.clicked.connect(self.close)

        self.refresh_project_header_info()
        self.update_modules_button()

    def _show_return_window(self):
        if self.return_window is None:
            return
        self.return_window.show()
        self.return_window.raise_()
        self.return_window.activateWindow()

    def closeEvent(self, event):
        self._show_return_window()
        super().closeEvent(event)

    def refresh_project_header_info(self):
        """Actualizar los campos de cabecera de la ventana de proyecto."""
        self.lbl_name.setText(f"Proyecto: {self.project.name}")
        self.lbl_client.setText(f"Cliente: {self.project.client or '-'}")
        locales = _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
        locales_count = len(locales) if locales else (self.project.locales_count or 0)
        self.lbl_locales_count.setText(f"Cantidad de locales: {locales_count}")
        self.lbl_root.setText(f"Carpeta de proyecto: {self.project.root_directory}")

        project_file = _project_data_path(self.project)
        if project_file.exists():
            modified = datetime.datetime.fromtimestamp(project_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        else:
            modified = "-"

        created = self.project.created_at or "-"
        self.lbl_created.setText(f"Creado: {created}")
        self.lbl_modified.setText(f"Modificado: {modified}")

        self.locales_list.clear()
        if locales:
            for locale in locales:
                modules_count = len(
                    [
                        module
                        for module in self.project.modules
                        if str(module.locale_name or "").strip().lower() == locale.name.strip().lower()
                    ]
                )
                if modules_count <= 0:
                    try:
                        modules_count = int(locale.modules_count or 0)
                    except (TypeError, ValueError):
                        modules_count = 0

                item = QListWidgetItem(f"{locale.name} ({modules_count} módulo(s))")
                item.setData(Qt.UserRole, locale.name)
                item.setFlags(
                    Qt.ItemIsEnabled
                    | Qt.ItemIsSelectable
                    | Qt.ItemIsUserCheckable
                )
                item.setCheckState(Qt.Checked)
                self.locales_list.addItem(item)
        else:
            placeholder_item = QListWidgetItem("sin procesar")
            placeholder_item.setFlags(Qt.NoItemFlags)
            placeholder_item.setTextAlignment(Qt.AlignCenter)
            placeholder_item.setForeground(QColor("#777777"))
            self.locales_list.addItem(placeholder_item)

    def _selected_locale_names(self) -> list[str]:
        selected_locales: list[str] = []
        for index in range(self.locales_list.count()):
            item = self.locales_list.item(index)
            if item is None:
                continue
            locale_name = str(item.data(Qt.UserRole) or "").strip()
            if not locale_name:
                continue
            if item.checkState() == Qt.Checked:
                selected_locales.append(locale_name)
        return selected_locales

    def _listed_locale_names(self) -> list[str]:
        locale_names: list[str] = []
        for index in range(self.locales_list.count()):
            item = self.locales_list.item(index)
            if item is None:
                continue
            locale_name = str(item.data(Qt.UserRole) or "").strip()
            if locale_name:
                locale_names.append(locale_name)
        return locale_names

    def _project_for_selected_locales(self, action_title: str) -> Project | None:
        selected_locale_names = self._selected_locale_names()
        if not selected_locale_names:
            QMessageBox.warning(
                self,
                action_title,
                "Seleccione al menos un local en la lista para continuar.",
            )
            return None

        selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names}
        filtered_locales = [
            locale
            for locale in _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
            if locale.name.strip().lower() in selected_locale_keys
        ]
        filtered_modules = [
            module
            for module in self.project.modules
            if str(module.locale_name or "").strip().lower() in selected_locale_keys
        ]

        if not filtered_modules:
            QMessageBox.warning(
                self,
                action_title,
                "No hay módulos cargados para los locales seleccionados.",
            )
            return None

        return Project(
            name=self.project.name,
            root_directory=self.project.root_directory,
            project_data_file=self.project.project_data_file,
            client=self.project.client,
            created_at=self.project.created_at,
            locales=filtered_locales,
            modules=filtered_modules,
            output_directory=self.project.output_directory,
        )

    def _normalize_module_piece_thickness(self, module: ModuleData) -> None:
        """Normaliza el espesor de todas las piezas en un módulo.
        
        Convierte strings vacíos a None para que sean excluidas del conteo,
        y asegura que los valores numéricos sean floats válidos.
        """
        if not module.pieces:
            return
        
        for piece in module.pieces:
            thickness_val = piece.thickness
            if thickness_val == "" or thickness_val is None:
                piece.thickness = None
            else:
                try:
                    piece.thickness = float(thickness_val)
                except (ValueError, TypeError):
                    piece.thickness = None

    def _reload_module_pieces_from_config(self, module: ModuleData) -> None:
        """Recarga las piezas de un módulo desde su module_config.json.
        
        Esto sincroniza module.pieces con el archivo de configuración,
        asegurando que siempre refleje el estado actual.
        """
        config_path = self._module_config_path(module)
        if not config_path.exists():
            return
        
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            pieces_data = config_data.get("pieces", [])
            
            module.pieces = []
            for piece_dict in pieces_data:
                # Extraer solo los campos definidos en Piece dataclass
                if "source" in piece_dict and "cnc_source" not in piece_dict:
                    piece_dict = dict(piece_dict)
                    piece_dict["cnc_source"] = piece_dict.get("source")
                piece_fields = {
                    'id', 'width', 'height', 'thickness', 'quantity', 
                    'color', 'grain_direction', 'name', 'module_name',
                    'cnc_source', 'f6_source', 'piece_type', 'program_width', 'program_height', 'program_thickness'
                }
                filtered_dict = {k: v for k, v in piece_dict.items() if k in piece_fields}
                
                _coerce_optional_piece_float_fields(
                    filtered_dict,
                    ("thickness", "program_width", "program_height", "program_thickness"),
                )
                
                try:
                    piece = Piece(**filtered_dict)
                    module.pieces.append(piece)
                except Exception:
                    pass
        except Exception:
            pass

    def _is_valid_piece_for_count(self, piece) -> bool:
        """Regla única para conteo/visualización: debe tener espesor definido y > 0."""
        # Solo contar piezas con espesor válido (no None, no "" y > 0)
        if piece.thickness is None or piece.thickness == "":
            return False
        try:
            thickness_val = float(piece.thickness)
            return thickness_val > 0
        except (TypeError, ValueError):
            return False

    def _is_valid_thickness_value(self, thickness_value) -> bool:
        """Valida espesor > 0 para valores numéricos o string."""
        if thickness_value is None:
            return False
        try:
            return float(thickness_value) > 0
        except (TypeError, ValueError):
            return False

    def _module_config_path(self, module: ModuleData) -> Path:
        return Path(module.path) / "module_config.json"

    def _read_module_config(self, module: ModuleData) -> dict:
        config_path = self._module_config_path(module)
        if not config_path.exists():
            return {}
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _build_pgmx_index(self, module_path: Path):
        available_pgmx_names = set()
        available_pgmx_relpaths = set()
        if module_path.exists():
            for pgmx_file in module_path.rglob("*.pgmx"):
                available_pgmx_names.add(pgmx_file.name.lower())
                available_pgmx_relpaths.add(str(pgmx_file.relative_to(module_path)).replace("\\", "/").lower())
        return available_pgmx_names, available_pgmx_relpaths

    def _get_pgmx_status(self, source_value: str, available_pgmx_names: set, available_pgmx_relpaths: set) -> str:
        source_value = str(source_value or "").strip()
        if not source_value:
            return "✗"

        source_name = Path(source_value).name.lower()
        source_rel = source_value.replace("\\", "/").lower()
        if source_name in available_pgmx_names or source_rel in available_pgmx_relpaths:
            return "✓"
        return "✗"

    def _write_module_config_files(self, modules: list[ModuleData] | None = None):
        """Crear archivo de configuración por módulo con piezas y validación PGMX."""
        from core.pgmx_processing import persist_piece_program_dimensions

        program_dimensions_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
        target_modules = modules if modules is not None else self.project.modules
        for module in target_modules:
            module_path = Path(module.path)
            pgmx_names, pgmx_relpaths = self._build_pgmx_index(module_path)
            previous_config = self._read_module_config(module)
            previous_settings = previous_config.get("settings", {})
            previous_pieces = previous_config.get("pieces", []) if isinstance(previous_config, dict) else []
            previous_rows_by_id = {
                str(piece_row.get("id") or "").strip(): piece_row
                for piece_row in previous_pieces
                if isinstance(piece_row, dict) and str(piece_row.get("id") or "").strip()
            }

            rows = []
            for piece in module.pieces:
                persist_piece_program_dimensions(self.project, piece, module_path, cache=program_dimensions_cache)
                previous_row = previous_rows_by_id.get(str(piece.id or "").strip(), {})
                source_value = piece.cnc_source or ""
                pgmx_status = self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths)
                rows.append(
                    {
                        "id": piece.id,
                        "name": piece.name or piece.id,
                        "quantity": piece.quantity,
                        "height": piece.height,
                        "width": piece.width,
                        "thickness": piece.thickness,
                        "color": piece.color,
                        "grain_direction": piece.grain_direction,
                        "source": source_value,
                        "f6_source": piece.f6_source or previous_row.get("f6_source"),
                        "pgmx": pgmx_status,
                        "piece_type": piece.piece_type,
                        "program_width": piece.program_width,
                        "program_height": piece.program_height,
                        "program_thickness": piece.program_thickness,
                        "en_juego": bool(previous_row.get("en_juego", False)),
                        "include_in_sheet": bool(previous_row.get("include_in_sheet", False)),
                    }
                )

            config_data = {
                "module": module.name,
                "path": str(module_path),
                "generated_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                "en_juego_layout": previous_config.get("en_juego_layout", {}),
                "settings": {
                    "x": previous_settings.get("x", ""),
                    "y": previous_settings.get("y", ""),
                    "z": previous_settings.get("z", ""),
                    "herrajes_y_accesorios": previous_settings.get("herrajes_y_accesorios", ""),
                    "guias_y_bisagras": previous_settings.get("guias_y_bisagras", ""),
                    "detalles_de_obra": previous_settings.get("detalles_de_obra", ""),
                },
                "pieces": rows,
            }
            config_path = self._module_config_path(module)
            config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _locale_config_path(self, locale: LocaleData) -> Path:
        return Path(self.project.root_directory) / locale.path / "local_config.json"

    def _safe_float_value(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _compact_dimension_value(self, value):
        parsed = self._safe_float_value(value)
        if parsed is None:
            return None
        return int(parsed) if parsed.is_integer() else round(parsed, 2)

    def _derive_module_dimensions_from_rows(self, module_name: str, pieces: list[dict]):
        import re

        raw = module_name or ""
        cleaned = re.sub(r"^\s*mod\.?\s*\d+\s*-\s*", "", raw, flags=re.IGNORECASE)
        parts = [part.strip() for part in cleaned.split("-")]

        numeric_parts = []
        for part in parts:
            if re.fullmatch(r"\d+(?:[\.,]\d+)?", part):
                try:
                    numeric_parts.append(float(part.replace(",", ".")))
                except ValueError:
                    continue

        x_named = numeric_parts[-2] if len(numeric_parts) >= 2 else (numeric_parts[0] if len(numeric_parts) == 1 else None)
        z_named = numeric_parts[-1] if len(numeric_parts) >= 2 else None

        widths = []
        heights = []
        thicknesses = []
        lateral_heights = []
        span_heights = []

        for piece in pieces:
            piece_name = str(piece.get("name") or piece.get("id") or "").lower()
            width = self._safe_float_value(piece.get("width"))
            height = self._safe_float_value(piece.get("height"))
            thickness = self._safe_float_value(piece.get("thickness"))

            if width is not None and width > 0:
                widths.append(width)
            if height is not None and height > 0:
                heights.append(height)
            if thickness is not None and thickness > 0:
                thicknesses.append(thickness)

            if "lateral" in piece_name and height is not None and height > 0:
                lateral_heights.append(height)

            if any(key in piece_name for key in ["fondo", "estante", "tapa", "puerta", "frente", "faja"]):
                if height is not None and height > 0:
                    span_heights.append(height)

        max_thickness = max(thicknesses) if thicknesses else 0.0

        if z_named is not None:
            z_val = z_named
        elif widths:
            z_val = max(widths)
        else:
            z_val = None

        if x_named is not None:
            x_val = x_named
        else:
            x_base = max(span_heights) if span_heights else (max(heights) if heights else None)
            x_val = x_base

        if lateral_heights:
            y_base = max(lateral_heights)
        elif heights:
            y_base = max(heights)
        else:
            y_base = None

        y_val = y_base + max_thickness if y_base is not None else None

        return (
            self._compact_dimension_value(x_val),
            self._compact_dimension_value(y_val),
            self._compact_dimension_value(z_val),
        )

    def _resolve_module_nominal_dimensions(self, module: ModuleData) -> dict:
        config_data = self._read_module_config(module)
        settings = config_data.get("settings", {}) if isinstance(config_data, dict) else {}
        pieces = config_data.get("pieces", []) if isinstance(config_data, dict) else []
        if not isinstance(pieces, list):
            pieces = []

        x_inferred, y_inferred, z_inferred = self._derive_module_dimensions_from_rows(module.name, pieces)
        x_value = self._compact_dimension_value(settings.get("x")) or x_inferred
        y_value = self._compact_dimension_value(settings.get("y")) or y_inferred
        z_value = self._compact_dimension_value(settings.get("z")) or z_inferred

        return {
            "x": x_value,
            "y": y_value,
            "z": z_value,
        }

    def _write_locale_config_files(self, locales: list[LocaleData] | None = None):
        target_locales = locales if locales is not None else self.project.locales
        for locale in target_locales:
            locale_path = Path(self.project.root_directory) / locale.path
            locale_path.mkdir(parents=True, exist_ok=True)

            locale_modules = [
                module
                for module in self.project.modules
                if module.locale_name == locale.name
            ]
            locale.modules_count = len(locale_modules)

            rows = []
            for module in sorted(locale_modules, key=lambda item: item.name.lower()):
                module_path = Path(module.path)
                try:
                    relative_module_path = str(module_path.relative_to(locale_path)).replace("\\", "/")
                except ValueError:
                    relative_module_path = module.relative_path or module.name

                rows.append(
                    {
                        "name": module.name,
                        "path": relative_module_path,
                        "dimensions": self._resolve_module_nominal_dimensions(module),
                    }
                )

            config_data = {
                "locale_name": locale.name,
                "path": locale.path,
                "modules_count": len(rows),
                "modules": rows,
            }
            self._locale_config_path(locale).write_text(
                json.dumps(config_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _valid_pieces_in_module(self, module):
        return [piece for piece in module.pieces if self._is_valid_piece_for_count(piece)]

    def _piece_quantity(self, piece) -> int:
        """Cantidad numérica de la pieza, con fallback seguro a 1."""
        try:
            qty = int(piece.quantity)
            return qty if qty > 0 else 1
        except (TypeError, ValueError):
            return 1

    def _valid_piece_count_in_module(self, module) -> int:
        """Total de piezas (unidades) válidas en el módulo."""
        return sum(self._piece_quantity(piece) for piece in module.pieces if self._is_valid_piece_for_count(piece))

    def edit_project(self):
        """Abrir ventana de edición del proyecto."""
        edit_window = EditProjectWindow(self.project)
        edit_window.show()
        self.edit_window = edit_window

    def _prompt_new_locale_name(self, root_path: Path, title: str, prompt: str) -> str | None:
        while True:
            locale_name, ok = QInputDialog.getText(self, title, prompt)
            if not ok:
                return None

            locale_name = str(locale_name or "").strip()
            if not locale_name:
                QMessageBox.warning(self, title, "Ingrese un nombre de local válido.")
                continue

            locale_dir = root_path / locale_name
            if locale_dir.exists():
                QMessageBox.warning(
                    self,
                    title,
                    "Ya existe una carpeta con ese nombre. Ingrese un local nuevo para evitar mezclar contenido.",
                )
                continue

            return locale_name

    def _move_loose_modules_to_locale(self, root_path: Path, locale_name: str, module_dirs: list[Path]) -> None:
        locale_dir = root_path / locale_name
        locale_dir.mkdir(parents=True, exist_ok=False)
        for module_dir in module_dirs:
            shutil.move(str(module_dir), str(locale_dir / module_dir.name))

    def _ensure_project_structure_ready(self, root_path: Path) -> bool:
        from core.parser import inspect_project_layout

        layout = inspect_project_layout(root_path)
        if not layout.loose_module_dirs:
            return True

        if not layout.locale_dirs:
            locale_name = self._prompt_new_locale_name(
                root_path,
                "Preparar proyecto",
                (
                    "No se encontraron carpetas de locales.\n"
                    "Ingrese el nombre del local que se creará para mover allí todos los módulos:"
                ),
            )
            if not locale_name:
                return False
            self._move_loose_modules_to_locale(root_path, locale_name, layout.loose_module_dirs)
            return True

        locale_name = self._prompt_new_locale_name(
            root_path,
            "Preparar proyecto",
            (
                "Se encontraron locales existentes y también módulos sueltos en la carpeta principal.\n"
                "Ingrese el nombre del nuevo local que recibirá únicamente esos módulos sueltos:"
            ),
        )
        if not locale_name:
            return False
        self._move_loose_modules_to_locale(root_path, locale_name, layout.loose_module_dirs)
        return True

    def process_project(self):
        """Procesar el proyecto: escanear subcarpetas y extraer piezas de archivos PGMX."""
        from pathlib import Path
        from core.parser import inspect_project_layout, scan_project, scan_project_structure
        from core.pgmx_processing import generate_project_piece_drawings

        try:
            root_path = Path(self.project.root_directory)
            if not root_path.exists():
                QMessageBox.warning(self, "Error", "Carpeta raíz no existe")
                return

            if not self._ensure_project_structure_ready(root_path):
                return

            listed_locale_names = self._listed_locale_names()
            selected_locale_names = self._selected_locale_names()
            processed_locales: list[LocaleData]
            processed_modules: list[ModuleData]

            if listed_locale_names:
                if not selected_locale_names:
                    QMessageBox.warning(
                        self,
                        "Procesar",
                        "Seleccione al menos un local en la lista para procesar.",
                    )
                    return

                layout = inspect_project_layout(root_path)
                selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names}
                locale_dirs = [
                    locale_dir
                    for locale_dir in layout.locale_dirs
                    if locale_dir.name.strip().lower() in selected_locale_keys
                ]
                if not locale_dirs:
                    QMessageBox.warning(
                        self,
                        "Procesar",
                        "No se encontraron carpetas disponibles para los locales seleccionados.",
                    )
                    return

                rescanned_locale_keys = {locale_dir.name.strip().lower() for locale_dir in locale_dirs}
                processed_locales = []
                processed_modules = []
                for locale_dir in locale_dirs:
                    locale_modules = scan_project(locale_dir)
                    for module in locale_modules:
                        module.locale_name = locale_dir.name
                        module.relative_path = str(Path(module.path).relative_to(root_path)).replace("\\", "/")
                    processed_locales.append(
                        LocaleData(
                            name=locale_dir.name,
                            path=str(locale_dir.relative_to(root_path)).replace("\\", "/"),
                            modules_count=len(locale_modules),
                        )
                    )
                    processed_modules.extend(locale_modules)

                preserved_locales = [
                    locale
                    for locale in _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
                    if locale.name.strip().lower() not in rescanned_locale_keys
                ]
                preserved_modules = [
                    module
                    for module in self.project.modules
                    if str(module.locale_name or "").strip().lower() not in rescanned_locale_keys
                ]

                self.project.locales = sorted(
                    preserved_locales + processed_locales,
                    key=lambda locale: locale.name.lower(),
                )
                self.project.modules = sorted(
                    preserved_modules + processed_modules,
                    key=lambda module: (str(module.locale_name or "").lower(), module.name.lower()),
                )
            else:
                self.project.locales, self.project.modules = scan_project_structure(root_path)
                processed_locales = list(self.project.locales)
                processed_modules = list(self.project.modules)

            # Normalizar thickness de todas las piezas procesadas
            for module in processed_modules:
                self._normalize_module_piece_thickness(module)
            
            self._write_module_config_files(processed_modules)
            self._write_locale_config_files(processed_locales)
            
            # Recargar piezas desde los module_config.json recién generados
            for module in processed_modules:
                self._reload_module_pieces_from_config(module)
            
            self._write_locale_config_files(processed_locales)
            _save_project(self.project)

            from core.summary import export_summary
            summary_csv_path = root_path / "resumen_piezas.csv"
            export_summary(self.project, summary_csv_path)

            processed_project = Project(
                name=self.project.name,
                root_directory=self.project.root_directory,
                project_data_file=self.project.project_data_file,
                client=self.project.client,
                created_at=self.project.created_at,
                locales=processed_locales,
                modules=processed_modules,
                output_directory=self.project.output_directory,
            )
            generated_drawings, skipped_drawings, pieces_with_machining = generate_project_piece_drawings(
                processed_project,
            )

            total_pieces = sum(self._valid_piece_count_in_module(module) for module in processed_modules)
            module_breakdown = "\n".join([
                f"{module.name}: {self._valid_piece_count_in_module(module)}"
                for module in processed_modules
            ])
            warning_parts = []
            for module in processed_modules:
                if self._valid_piece_count_in_module(module) == 0:
                    warning_parts.append(module.name)

            self.refresh_project_header_info()
            self.update_modules_button()

            detail_text = (
                f"Locales procesados: {len(processed_locales)}\n"
                f"Módulos procesados: {len(processed_modules)}\n"
                f"Piezas totales: {total_pieces}\n"
                f"Detalle:\n{module_breakdown}\n"
                f"Resumen guardado en: {summary_csv_path}\n"
                f"Dibujos SVG generados: {generated_drawings}\n"
                f"Piezas con mecanizados detectados: {pieces_with_machining}\n"
                f"Piezas sin PGMX utilizable: {skipped_drawings}\n"
                "Carpeta de dibujos: carpeta de cada módulo"
            )

            if warning_parts:
                detail_text += "\n\nAtención: algunos módulos no tienen piezas: " + ", ".join(warning_parts)

            QMessageBox.information(self, "Procesamiento completado", detail_text)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Error durante el procesamiento: {exc}")

    def update_modules_button(self):
        """Habilitar botón Módulos si el proyecto fue procesado o hay resumen."""
        project_root = Path(self.project.root_directory)
        summary_path = project_root / "resumen_piezas.csv"
        has_modules = bool(self.project.modules) or summary_path.exists()
        self.btn_modules.setEnabled(has_modules)

    def show_modules(self):
        """Mostrar lista de módulos en una ventana modal"""
        if not self.project.modules:
            QMessageBox.warning(self, "Módulos", "No hay módulos cargados. Procese el proyecto primero.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Módulos - {self.project.name}")
        dialog.resize(500, 400)

        dlg_layout = QVBoxLayout()
        self.modules_list = QListWidget()

        def refresh_modules_list_view():
            # Recargar piezas desde module_config.json y normalizar thickness
            for module in self.project.modules:
                self._reload_module_pieces_from_config(module)
                self._normalize_module_piece_thickness(module)
            
            self.modules_list.clear()
            for module in self.project.modules:
                valid_count = self._valid_piece_count_in_module(module)
                module_label = f"{module.locale_name} / {module.name}" if module.locale_name else module.name
                item = QListWidgetItem(f"{module_label} ({valid_count} piezas)")
                item.setData(Qt.UserRole, module.relative_path or module.path)
                self.modules_list.addItem(item)

        refresh_modules_list_view()

        dlg_layout.addWidget(QLabel("Módulos encontrados:"))
        dlg_layout.addWidget(self.modules_list)

        button_layout = QHBoxLayout()
        new_btn = QPushButton("Nuevo")
        inspect_btn = QPushButton("Inspeccionar")
        close_btn = QPushButton("Cerrar")
        button_layout.addWidget(new_btn)
        button_layout.addWidget(inspect_btn)
        button_layout.addWidget(close_btn)

        dlg_layout.addLayout(button_layout)

        dialog.setLayout(dlg_layout)

        def create_manual_module():
            module_name, ok = QInputDialog.getText(
                dialog,
                "Nuevo módulo",
                "Nombre del módulo:",
                text="Aplicados",
            )
            if not ok:
                return

            module_name = (module_name or "").strip()
            if not module_name:
                QMessageBox.warning(dialog, "Nuevo módulo", "Ingrese un nombre de módulo válido.")
                return

            locale_options = [locale.name for locale in self.project.locales]
            if not locale_options:
                locale_name = self._prompt_new_locale_name(
                    Path(self.project.root_directory),
                    "Nuevo local",
                    "Nombre del local para el nuevo módulo:",
                )
                if not locale_name:
                    return
                locale_dir = Path(self.project.root_directory) / locale_name
                try:
                    locale_dir.mkdir(parents=True, exist_ok=False)
                except Exception as exc:
                    QMessageBox.warning(dialog, "Nuevo local", f"No se pudo crear la carpeta del local: {exc}")
                    return
                selected_locale = LocaleData(name=locale_name, path=locale_name, modules_count=0)
                self.project.locales.append(selected_locale)
            elif len(locale_options) == 1:
                selected_locale = next(locale for locale in self.project.locales if locale.name == locale_options[0])
            else:
                selected_locale_name, ok_locale = QInputDialog.getItem(
                    dialog,
                    "Nuevo módulo",
                    "Local:",
                    locale_options,
                    0,
                    False,
                )
                if not ok_locale:
                    return
                selected_locale = next(
                    locale for locale in self.project.locales if locale.name == str(selected_locale_name).strip()
                )

            existing_names = {
                module.name.lower()
                for module in self.project.modules
                if module.locale_name.lower() == selected_locale.name.lower()
            }
            if module_name.lower() in existing_names:
                QMessageBox.warning(dialog, "Nuevo módulo", "Ya existe un módulo con ese nombre.")
                return

            module_path = Path(self.project.root_directory) / selected_locale.path / module_name
            try:
                module_path.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                QMessageBox.warning(dialog, "Nuevo módulo", "La carpeta del módulo ya existe.")
                return
            except Exception as exc:
                QMessageBox.warning(dialog, "Nuevo módulo", f"No se pudo crear la carpeta: {exc}")
                return

            new_module = ModuleData(
                name=module_name,
                path=str(module_path),
                locale_name=selected_locale.name,
                relative_path=str(module_path.relative_to(Path(self.project.root_directory))).replace("\\", "/"),
                pieces=[],
                is_manual=True,
            )
            self.project.modules.append(new_module)
            selected_locale.modules_count += 1

            # Crear configuración base para habilitar inspección del módulo manual.
            config_path = self._module_config_path(new_module)
            config_data = {
                "module": new_module.name,
                "path": str(module_path),
                "generated_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                "en_juego_layout": {},
                "settings": {
                    "x": "",
                    "y": "",
                    "z": "",
                    "herrajes_y_accesorios": "",
                    "guias_y_bisagras": "",
                    "detalles_de_obra": "",
                },
                "pieces": [],
            }
            config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")

            _save_project(self.project)
            self.refresh_project_header_info()
            refresh_modules_list_view()
            QMessageBox.information(dialog, "Nuevo módulo", f"Módulo '{module_name}' creado correctamente.")

        new_btn.clicked.connect(create_manual_module)
        inspect_btn.clicked.connect(lambda: self.inspect_module(dialog, refresh_modules_list_view))
        self.modules_list.itemDoubleClicked.connect(lambda _: self.inspect_module(dialog, refresh_modules_list_view))
        close_btn.clicked.connect(dialog.accept)

        dialog.exec()

    def inspect_module(self, parent_dialog, on_module_updated=None):
        """Mostrar piezas del módulo seleccionado"""
        selected_item = self.modules_list.currentItem()
        if not selected_item:
            QMessageBox.warning(parent_dialog, "Inspeccionar", "Seleccione un módulo primero.")
            return

        # Extraer nombre del módulo del texto del item
        module_key = str(selected_item.data(Qt.UserRole) or "").strip()
        
        # Encontrar el módulo correspondiente
        selected_module = None
        for module in self.project.modules:
            current_key = module.relative_path or module.path
            if current_key == module_key:
                selected_module = module
                break

        module_name = selected_module.name if selected_module else selected_item.text().split(" (")[0]
        
        if not selected_module:
            QMessageBox.warning(parent_dialog, "Error", "Módulo no encontrado.")
            return

        # Crear ventana de inspección
        inspect_dialog = QDialog(parent_dialog)
        inspect_dialog.setWindowTitle(f"Piezas - {module_name}")
        inspect_scale, inspect_width, _ = _apply_responsive_window_size(
            inspect_dialog,
            1600,
            640,
            width_ratio=0.96,
            height_ratio=0.90,
        )
        compact_scale = max(inspect_scale, 0.82)

        config_path = self._module_config_path(selected_module)
        if not config_path.exists():
            QMessageBox.warning(
                parent_dialog,
                "Inspeccionar",
                "No existe el archivo de configuración del módulo. Procese el proyecto para generarlo.",
            )
            return

        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config_data.get("en_juego_layout"), dict):
            config_data["en_juego_layout"] = {}
        settings = config_data.get("settings", {})
        all_rows = config_data.get("pieces", [])
        module_path = Path(selected_module.path)
        pgmx_names, pgmx_relpaths = self._build_pgmx_index(module_path)

        def normalize_source_path(file_path: str) -> str:
            """Guardar source en formato relativo al módulo cuando sea posible."""
            if not file_path:
                return ""
            try:
                relative = Path(file_path).resolve().relative_to(module_path.resolve())
                return str(relative).replace("\\", "/")
            except Exception:
                return file_path

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración del módulo:"))

        dim_x_field = QLineEdit(str(settings.get("x", "") or ""))
        dim_y_field = QLineEdit(str(settings.get("y", "") or ""))
        dim_z_field = QLineEdit(str(settings.get("z", "") or ""))
        field_width = _scaled_int(100, compact_scale, 72)
        dim_x_field.setFixedWidth(field_width)
        dim_y_field.setFixedWidth(field_width)
        dim_z_field.setFixedWidth(field_width)

        xyz_layout = QHBoxLayout()
        xyz_layout.setAlignment(Qt.AlignLeft)
        xyz_layout.addWidget(QLabel("X: "))
        xyz_layout.addWidget(dim_x_field)
        xyz_layout.addWidget(QLabel("Y: "))
        xyz_layout.addWidget(dim_y_field)
        xyz_layout.addWidget(QLabel("Z: "))
        xyz_layout.addWidget(dim_z_field)
        xyz_layout.addStretch(1)

        herrajes_field = QLineEdit(str(settings.get("herrajes_y_accesorios", "")))
        guias_field = QLineEdit(str(settings.get("guias_y_bisagras", "")))
        detalles_field = QLineEdit(str(settings.get("detalles_de_obra", "")))
        has_unsaved_changes = False

        def mark_unsaved_changes(*_):
            nonlocal has_unsaved_changes
            has_unsaved_changes = True

        dim_x_field.textChanged.connect(mark_unsaved_changes)
        dim_y_field.textChanged.connect(mark_unsaved_changes)
        dim_z_field.textChanged.connect(mark_unsaved_changes)
        herrajes_field.textChanged.connect(mark_unsaved_changes)
        guias_field.textChanged.connect(mark_unsaved_changes)
        detalles_field.textChanged.connect(mark_unsaved_changes)

        layout.addLayout(xyz_layout)

        layout.addWidget(QLabel("Herrajes y accesorios:"))
        herrajes_layout = QHBoxLayout()
        herrajes_layout.addWidget(herrajes_field)
        
        def get_available_herrajes():
            """Obtener lista persistente de herrajes desde configuración."""
            settings = _read_app_settings()
            default_herrajes = [
                "Bisagras", "Guías correderas", "Manijas", "Cerraduras", "Tornillos",
                "Tuercas", "Pasadores", "Soportes", "Escuadras", "Bisagras ocultas",
                "Amortiguadores", "Tirador horizontal", "Tirador vertical", "Pivote",
                "Cierre magnético",
            ]
            return settings.get("available_herrajes", default_herrajes)
        
        def save_available_herrajes(herrajes_list):
            """Guardar lista persistente de herrajes en configuración."""
            settings = _read_app_settings()
            settings["available_herrajes"] = herrajes_list
            APP_SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        
        def open_herrajes_selector():
            """Abre ventana de selección con dos paneles y lista editable."""
            from PySide6.QtWidgets import QListWidget, QListWidgetItem
            from PySide6.QtCore import Qt
            
            # Obtener datos
            available_herrajes = get_available_herrajes()
            current_text = herrajes_field.text().strip()
            current_selected = [x.strip() for x in current_text.split("-") if x.strip()]
            
            # Crear diálogo
            dialog = QDialog(inspect_dialog)
            dialog.setWindowTitle("Seleccionar Herrajes y Accesorios")
            dialog.setMinimumSize(700, 400)
            
            main_layout = QVBoxLayout()
            
            # Título
            main_layout.addWidget(QLabel("Gestionar Herrajes y Accesorios"))
            
            # Contenedor horizontal para las dos listas
            content_layout = QHBoxLayout()
            
            # PANEL IZQUIERDO: Disponibles
            left_layout = QVBoxLayout()
            left_layout.addWidget(QLabel("Disponibles:"))
            available_list = QListWidget()
            available_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            left_layout.addWidget(available_list)
            
            # Botones para editar disponibles
            edit_buttons_layout = QHBoxLayout()
            btn_new = QPushButton("Nuevo")
            btn_edit = QPushButton("Editar")
            btn_delete = QPushButton("Eliminar")
            edit_buttons_layout.addWidget(btn_new)
            edit_buttons_layout.addWidget(btn_edit)
            edit_buttons_layout.addWidget(btn_delete)
            left_layout.addLayout(edit_buttons_layout)
            
            # PANEL DE BOTONES CENTRALES
            center_layout = QVBoxLayout()
            center_layout.addStretch()
            btn_right = QPushButton("→")
            btn_right.setMaximumWidth(40)
            btn_left = QPushButton("←")
            btn_left.setMaximumWidth(40)
            center_layout.addWidget(btn_right)
            center_layout.addWidget(btn_left)
            center_layout.addStretch()
            
            # PANEL DERECHO: Seleccionados
            right_layout = QVBoxLayout()
            right_layout.addWidget(QLabel("Seleccionados:"))
            selected_list = QListWidget()
            selected_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            right_layout.addWidget(selected_list)
            
            # Agregar paneles al contenedor horizontal
            content_layout.addLayout(left_layout, 1)
            content_layout.addLayout(center_layout, 0)
            content_layout.addLayout(right_layout, 1)
            
            main_layout.addLayout(content_layout)
            
            # Botones OK/Cancelar
            dialog_buttons = QHBoxLayout()
            ok_btn = QPushButton("OK")
            cancel_btn = QPushButton("Cancelar")
            dialog_buttons.addStretch()
            dialog_buttons.addWidget(ok_btn)
            dialog_buttons.addWidget(cancel_btn)
            main_layout.addLayout(dialog_buttons)
            
            dialog.setLayout(main_layout)
            
            # Funciones helpers
            def refresh_available_list():
                """Actualizar lista disponible, filtrando los seleccionados."""
                available_list.clear()
                saved_herrajes = get_available_herrajes()
                for herraje in saved_herrajes:
                    if herraje not in current_selected:
                        available_list.addItem(herraje)
            
            def refresh_selected_list():
                """Actualizar lista de seleccionados."""
                selected_list.clear()
                for item in current_selected:
                    selected_list.addItem(item)
            
            # Cargar listas iniciales
            refresh_available_list()
            refresh_selected_list()
            
            # Funciones para botones de movimiento
            def move_to_selected():
                """Mover elemento de disponibles a seleccionados."""
                current_item = available_list.currentItem()
                if current_item:
                    item_text = current_item.text()
                    if item_text not in current_selected:
                        current_selected.append(item_text)
                        refresh_selected_list()
                        refresh_available_list()
            
            def remove_from_selected():
                """Remover elemento de seleccionados."""
                current_item = selected_list.currentItem()
                if current_item:
                    item_text = current_item.text()
                    if item_text in current_selected:
                        current_selected.remove(item_text)
                        refresh_selected_list()
                        refresh_available_list()
            
            # Funciones para editar disponibles
            def add_new_herraje():
                """Agregar nuevo herraje a la lista disponible."""
                text, ok = QInputDialog.getText(dialog, "Nuevo Herraje", "Nombre del herraje:")
                if ok and text.strip():
                    saved = get_available_herrajes()
                    if text.strip() not in saved:
                        saved.append(text.strip())
                        save_available_herrajes(saved)
                        refresh_available_list()
            
            def edit_herraje():
                """Editar herraje seleccionado."""
                current_item = available_list.currentItem()
                if not current_item:
                    QMessageBox.warning(dialog, "Editar", "Seleccione un herraje.")
                    return
                old_text = current_item.text()
                text, ok = QInputDialog.getText(dialog, "Editar Herraje", "Nombre del herraje:", text=old_text)
                if ok and text.strip():
                    saved = get_available_herrajes()
                    if old_text in saved:
                        idx = saved.index(old_text)
                        saved[idx] = text.strip()
                        save_available_herrajes(saved)
                        # Si estaba en seleccionados, actualizar también
                        if old_text in current_selected:
                            idx_sel = current_selected.index(old_text)
                            current_selected[idx_sel] = text.strip()
                        refresh_selected_list()
                        refresh_available_list()
            
            def delete_herraje():
                """Eliminar herraje de la lista disponible."""
                current_item = available_list.currentItem()
                if not current_item:
                    QMessageBox.warning(dialog, "Eliminar", "Seleccione un herraje.")
                    return
                text = current_item.text()
                saved = get_available_herrajes()
                if text in saved:
                    saved.remove(text)
                    save_available_herrajes(saved)
                    # Si estaba seleccionado, removerlo también
                    if text in current_selected:
                        current_selected.remove(text)
                    refresh_selected_list()
                    refresh_available_list()
            
            # Conectar botones
            btn_right.clicked.connect(move_to_selected)
            btn_left.clicked.connect(remove_from_selected)
            btn_new.clicked.connect(add_new_herraje)
            btn_edit.clicked.connect(edit_herraje)
            btn_delete.clicked.connect(delete_herraje)
            
            # Doble click para mover
            available_list.itemDoubleClicked.connect(move_to_selected)
            selected_list.itemDoubleClicked.connect(remove_from_selected)
            
            # OK/Cancelar
            def apply_selection():
                result_text = " - ".join(current_selected) if current_selected else ""
                herrajes_field.setText(result_text)
                dialog.accept()
            
            ok_btn.clicked.connect(apply_selection)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
        
        btn_select_herrajes = QPushButton("...")
        btn_select_herrajes.setMaximumWidth(50)
        btn_select_herrajes.clicked.connect(open_herrajes_selector)
        herrajes_layout.addWidget(btn_select_herrajes)
        layout.addLayout(herrajes_layout)
        
        # GUÍAS Y BISAGRAS con selector similar
        def get_available_guias():
            """Obtener lista persistente de guías desde configuración."""
            settings = _read_app_settings()
            default_guias = [
                "Guía de bolas", "Guía de rodillo", "Guía telescópica", "Bisagra de copa",
                "Bisagra de piano", "Bisagra invisible", "Bisagra de doble acción", "Pernio",
                "Soporte de estante", "Guía silenciosa", "Bisagra ajustable", "Bisagra basculante",
            ]
            return settings.get("available_guias", default_guias)
        
        def save_available_guias(guias_list):
            """Guardar lista persistente de guías en configuración."""
            settings = _read_app_settings()
            settings["available_guias"] = guias_list
            APP_SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        
        def open_guias_selector():
            """Abre ventana de selección con dos paneles y lista editable para guías."""
            from PySide6.QtWidgets import QListWidget, QListWidgetItem
            from PySide6.QtCore import Qt
            
            # Obtener datos
            available_guias = get_available_guias()
            current_text = guias_field.text().strip()
            current_selected = [x.strip() for x in current_text.split("-") if x.strip()]
            
            # Crear diálogo
            dialog = QDialog(inspect_dialog)
            dialog.setWindowTitle("Seleccionar Guías y Bisagras")
            dialog.setMinimumSize(700, 400)
            
            main_layout = QVBoxLayout()
            
            # Título
            main_layout.addWidget(QLabel("Gestionar Guías y Bisagras"))
            
            # Contenedor horizontal para las dos listas
            content_layout = QHBoxLayout()
            
            # PANEL IZQUIERDO: Disponibles
            left_layout = QVBoxLayout()
            left_layout.addWidget(QLabel("Disponibles:"))
            available_list = QListWidget()
            available_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            left_layout.addWidget(available_list)
            
            # Botones para editar disponibles
            edit_buttons_layout = QHBoxLayout()
            btn_new = QPushButton("Nuevo")
            btn_edit = QPushButton("Editar")
            btn_delete = QPushButton("Eliminar")
            edit_buttons_layout.addWidget(btn_new)
            edit_buttons_layout.addWidget(btn_edit)
            edit_buttons_layout.addWidget(btn_delete)
            left_layout.addLayout(edit_buttons_layout)
            
            # PANEL DE BOTONES CENTRALES
            center_layout = QVBoxLayout()
            center_layout.addStretch()
            btn_right = QPushButton("→")
            btn_right.setMaximumWidth(40)
            btn_left = QPushButton("←")
            btn_left.setMaximumWidth(40)
            center_layout.addWidget(btn_right)
            center_layout.addWidget(btn_left)
            center_layout.addStretch()
            
            # PANEL DERECHO: Seleccionados
            right_layout = QVBoxLayout()
            right_layout.addWidget(QLabel("Seleccionados:"))
            selected_list = QListWidget()
            selected_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            right_layout.addWidget(selected_list)
            
            # Agregar paneles al contenedor horizontal
            content_layout.addLayout(left_layout, 1)
            content_layout.addLayout(center_layout, 0)
            content_layout.addLayout(right_layout, 1)
            
            main_layout.addLayout(content_layout)
            
            # Botones OK/Cancelar
            dialog_buttons = QHBoxLayout()
            ok_btn = QPushButton("OK")
            cancel_btn = QPushButton("Cancelar")
            dialog_buttons.addStretch()
            dialog_buttons.addWidget(ok_btn)
            dialog_buttons.addWidget(cancel_btn)
            main_layout.addLayout(dialog_buttons)
            
            dialog.setLayout(main_layout)
            
            # Funciones helpers
            def refresh_available_list():
                """Actualizar lista disponible, filtrando los seleccionados."""
                available_list.clear()
                saved_guias = get_available_guias()
                for guia in saved_guias:
                    if guia not in current_selected:
                        available_list.addItem(guia)
            
            def refresh_selected_list():
                """Actualizar lista de seleccionados."""
                selected_list.clear()
                for item in current_selected:
                    selected_list.addItem(item)
            
            # Cargar listas iniciales
            refresh_available_list()
            refresh_selected_list()
            
            # Funciones para botones de movimiento
            def move_to_selected():
                """Mover elemento de disponibles a seleccionados."""
                current_item = available_list.currentItem()
                if current_item:
                    item_text = current_item.text()
                    if item_text not in current_selected:
                        current_selected.append(item_text)
                        refresh_selected_list()
                        refresh_available_list()
            
            def remove_from_selected():
                """Remover elemento de seleccionados."""
                current_item = selected_list.currentItem()
                if current_item:
                    item_text = current_item.text()
                    if item_text in current_selected:
                        current_selected.remove(item_text)
                        refresh_selected_list()
                        refresh_available_list()
            
            # Funciones para editar disponibles
            def add_new_guia():
                """Agregar nueva guía a la lista disponible."""
                text, ok = QInputDialog.getText(dialog, "Nueva Guía", "Nombre de la guía:")
                if ok and text.strip():
                    saved = get_available_guias()
                    if text.strip() not in saved:
                        saved.append(text.strip())
                        save_available_guias(saved)
                        refresh_available_list()
            
            def edit_guia():
                """Editar guía seleccionada."""
                current_item = available_list.currentItem()
                if not current_item:
                    QMessageBox.warning(dialog, "Editar", "Seleccione una guía.")
                    return
                old_text = current_item.text()
                text, ok = QInputDialog.getText(dialog, "Editar Guía", "Nombre de la guía:", text=old_text)
                if ok and text.strip():
                    saved = get_available_guias()
                    if old_text in saved:
                        idx = saved.index(old_text)
                        saved[idx] = text.strip()
                        save_available_guias(saved)
                        # Si estaba en seleccionados, actualizar también
                        if old_text in current_selected:
                            idx_sel = current_selected.index(old_text)
                            current_selected[idx_sel] = text.strip()
                        refresh_selected_list()
                        refresh_available_list()
            
            def delete_guia():
                """Eliminar guía de la lista disponible."""
                current_item = available_list.currentItem()
                if not current_item:
                    QMessageBox.warning(dialog, "Eliminar", "Seleccione una guía.")
                    return
                text = current_item.text()
                saved = get_available_guias()
                if text in saved:
                    saved.remove(text)
                    save_available_guias(saved)
                    # Si estaba seleccionada, removerla también
                    if text in current_selected:
                        current_selected.remove(text)
                    refresh_selected_list()
                    refresh_available_list()
            
            # Conectar botones
            btn_right.clicked.connect(move_to_selected)
            btn_left.clicked.connect(remove_from_selected)
            btn_new.clicked.connect(add_new_guia)
            btn_edit.clicked.connect(edit_guia)
            btn_delete.clicked.connect(delete_guia)
            
            # Doble click para mover
            available_list.itemDoubleClicked.connect(move_to_selected)
            selected_list.itemDoubleClicked.connect(remove_from_selected)
            
            # OK/Cancelar
            def apply_selection():
                result_text = " - ".join(current_selected) if current_selected else ""
                guias_field.setText(result_text)
                dialog.accept()
            
            ok_btn.clicked.connect(apply_selection)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
        
        layout.addWidget(QLabel("Guías y bisagras:"))
        guias_layout = QHBoxLayout()
        guias_layout.addWidget(guias_field)
        btn_select_guias = QPushButton("...")
        btn_select_guias.setMaximumWidth(50)
        btn_select_guias.clicked.connect(open_guias_selector)
        guias_layout.addWidget(btn_select_guias)
        layout.addLayout(guias_layout)
        
        # DETALLES DE OBRA con selector similar
        def get_available_detalles():
            """Obtener lista persistente de detalles de obra desde configuración."""
            settings = _read_app_settings()
            default_detalles = [
                "Perforacion", "Canto de melamina", "Canto de madera", "Cubrejuntas", "Cantonera",
                "Taladro ciego", "Taladro pasante", "Ranura", "Rebaje", "Espiga",
                "Mortaja", "Machihembrado", "Chaflán", "Redondeado", "Pulido",
                "Acabado lacado", "Acabado teñido", "Estampado", "Incrustación", "Tallado",
            ]
            return settings.get("available_detalles", default_detalles)
        
        def save_available_detalles(detalles_list):
            """Guardar lista persistente de detalles en configuración."""
            settings = _read_app_settings()
            settings["available_detalles"] = detalles_list
            APP_SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        
        def open_detalles_selector():
            """Abre ventana de selección con dos paneles y lista editable para detalles."""
            from PySide6.QtWidgets import QListWidget, QListWidgetItem
            from PySide6.QtCore import Qt
            
            # Obtener datos
            available_detalles = get_available_detalles()
            current_text = detalles_field.text().strip()
            current_selected = [x.strip() for x in current_text.split("-") if x.strip()]
            
            # Crear diálogo
            dialog = QDialog(inspect_dialog)
            dialog.setWindowTitle("Seleccionar Detalles de Obra")
            dialog.setMinimumSize(700, 400)
            
            main_layout = QVBoxLayout()
            
            # Título
            main_layout.addWidget(QLabel("Gestionar Detalles de Obra"))
            
            # Contenedor horizontal para las dos listas
            content_layout = QHBoxLayout()
            
            # PANEL IZQUIERDO: Disponibles
            left_layout = QVBoxLayout()
            left_layout.addWidget(QLabel("Disponibles:"))
            available_list = QListWidget()
            available_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            left_layout.addWidget(available_list)
            
            # Botones para editar disponibles
            edit_buttons_layout = QHBoxLayout()
            btn_new = QPushButton("Nuevo")
            btn_edit = QPushButton("Editar")
            btn_delete = QPushButton("Eliminar")
            edit_buttons_layout.addWidget(btn_new)
            edit_buttons_layout.addWidget(btn_edit)
            edit_buttons_layout.addWidget(btn_delete)
            left_layout.addLayout(edit_buttons_layout)
            
            # PANEL DE BOTONES CENTRALES
            center_layout = QVBoxLayout()
            center_layout.addStretch()
            btn_right = QPushButton("→")
            btn_right.setMaximumWidth(40)
            btn_left = QPushButton("←")
            btn_left.setMaximumWidth(40)
            center_layout.addWidget(btn_right)
            center_layout.addWidget(btn_left)
            center_layout.addStretch()
            
            # PANEL DERECHO: Seleccionados
            right_layout = QVBoxLayout()
            right_layout.addWidget(QLabel("Seleccionados:"))
            selected_list = QListWidget()
            selected_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            right_layout.addWidget(selected_list)
            
            # Agregar paneles al contenedor horizontal
            content_layout.addLayout(left_layout, 1)
            content_layout.addLayout(center_layout, 0)
            content_layout.addLayout(right_layout, 1)
            
            main_layout.addLayout(content_layout)
            
            # Botones OK/Cancelar
            dialog_buttons = QHBoxLayout()
            ok_btn = QPushButton("OK")
            cancel_btn = QPushButton("Cancelar")
            dialog_buttons.addStretch()
            dialog_buttons.addWidget(ok_btn)
            dialog_buttons.addWidget(cancel_btn)
            main_layout.addLayout(dialog_buttons)
            
            dialog.setLayout(main_layout)
            
            # Funciones helpers
            def refresh_available_list():
                """Actualizar lista disponible, filtrando los seleccionados."""
                available_list.clear()
                saved_detalles = get_available_detalles()
                for detalle in saved_detalles:
                    if detalle not in current_selected:
                        available_list.addItem(detalle)
            
            def refresh_selected_list():
                """Actualizar lista de seleccionados."""
                selected_list.clear()
                for item in current_selected:
                    selected_list.addItem(item)
            
            # Cargar listas iniciales
            refresh_available_list()
            refresh_selected_list()
            
            # Funciones para botones de movimiento
            def move_to_selected():
                """Mover elemento de disponibles a seleccionados."""
                current_item = available_list.currentItem()
                if current_item:
                    item_text = current_item.text()
                    if item_text not in current_selected:
                        current_selected.append(item_text)
                        refresh_selected_list()
                        refresh_available_list()
            
            def remove_from_selected():
                """Remover elemento de seleccionados."""
                current_item = selected_list.currentItem()
                if current_item:
                    item_text = current_item.text()
                    if item_text in current_selected:
                        current_selected.remove(item_text)
                        refresh_selected_list()
                        refresh_available_list()
            
            # Funciones para editar disponibles
            def add_new_detalle():
                """Agregar nuevo detalle a la lista disponible."""
                text, ok = QInputDialog.getText(dialog, "Nuevo Detalle", "Nombre del detalle:")
                if ok and text.strip():
                    saved = get_available_detalles()
                    if text.strip() not in saved:
                        saved.append(text.strip())
                        save_available_detalles(saved)
                        refresh_available_list()
            
            def edit_detalle():
                """Editar detalle seleccionado."""
                current_item = available_list.currentItem()
                if not current_item:
                    QMessageBox.warning(dialog, "Editar", "Seleccione un detalle.")
                    return
                old_text = current_item.text()
                text, ok = QInputDialog.getText(dialog, "Editar Detalle", "Nombre del detalle:", text=old_text)
                if ok and text.strip():
                    saved = get_available_detalles()
                    if old_text in saved:
                        idx = saved.index(old_text)
                        saved[idx] = text.strip()
                        save_available_detalles(saved)
                        # Si estaba en seleccionados, actualizar también
                        if old_text in current_selected:
                            idx_sel = current_selected.index(old_text)
                            current_selected[idx_sel] = text.strip()
                        refresh_selected_list()
                        refresh_available_list()
            
            def delete_detalle():
                """Eliminar detalle de la lista disponible."""
                current_item = available_list.currentItem()
                if not current_item:
                    QMessageBox.warning(dialog, "Eliminar", "Seleccione un detalle.")
                    return
                text = current_item.text()
                saved = get_available_detalles()
                if text in saved:
                    saved.remove(text)
                    save_available_detalles(saved)
                    # Si estaba seleccionado, removerlo también
                    if text in current_selected:
                        current_selected.remove(text)
                    refresh_selected_list()
                    refresh_available_list()
            
            # Conectar botones
            btn_right.clicked.connect(move_to_selected)
            btn_left.clicked.connect(remove_from_selected)
            btn_new.clicked.connect(add_new_detalle)
            btn_edit.clicked.connect(edit_detalle)
            btn_delete.clicked.connect(delete_detalle)
            
            # Doble click para mover
            available_list.itemDoubleClicked.connect(move_to_selected)
            selected_list.itemDoubleClicked.connect(remove_from_selected)
            
            # OK/Cancelar
            def apply_selection():
                result_text = " - ".join(current_selected) if current_selected else ""
                detalles_field.setText(result_text)
                dialog.accept()
            
            ok_btn.clicked.connect(apply_selection)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
        
        layout.addWidget(QLabel("Detalles de Obra:"))
        detalles_layout = QHBoxLayout()
        detalles_layout.addWidget(detalles_field)
        btn_select_detalles = QPushButton("...")
        btn_select_detalles.setMaximumWidth(50)
        btn_select_detalles.clicked.connect(open_detalles_selector)
        detalles_layout.addWidget(btn_select_detalles)
        layout.addLayout(detalles_layout)

        pieces_title = QLabel("")
        layout.addWidget(pieces_title)

        pieces_table = QTableWidget()
        pieces_table.setColumnCount(11)
        pieces_table.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Cantidad",
            "Alto",
            "Ancho",
            "Espesor",
            "Color",
            "Programa",
            "Observaciones",
            "En juego",
            "Excel",
        ])
        visible_row_indexes = []
        refreshing_pieces_table = False
        program_dimensions_cache = {}

        def build_piece_from_row(piece_row):
            thickness_val = piece_row.get("thickness")
            if thickness_val == "" or thickness_val is None:
                thickness = None
            else:
                try:
                    thickness = float(thickness_val)
                except (ValueError, TypeError):
                    thickness = None

            quantity_raw = str(piece_row.get("quantity") or "").strip()
            quantity = int(quantity_raw) if quantity_raw.isdigit() else 1

            def parse_dimension(raw_value):
                raw_text = "" if raw_value is None else str(raw_value).strip().replace(",", ".")
                if not raw_text:
                    return 0.0
                try:
                    return float(raw_text)
                except (ValueError, TypeError):
                    return 0.0

            def parse_optional_dimension(raw_value):
                raw_text = "" if raw_value is None else str(raw_value).strip().replace(",", ".")
                if not raw_text:
                    return None
                try:
                    parsed = float(raw_text)
                except (ValueError, TypeError):
                    return None
                return parsed if parsed > 0 else None

            return Piece(
                id=str(piece_row.get("id") or "").strip() or str(piece_row.get("name") or "pieza").strip(),
                name=str(piece_row.get("name") or piece_row.get("id") or "pieza").strip(),
                quantity=quantity,
                height=parse_dimension(piece_row.get("height")),
                width=parse_dimension(piece_row.get("width")),
                thickness=thickness,
                color=piece_row.get("color"),
                grain_direction=piece_row.get("grain_direction"),
                module_name=selected_module.name,
                cnc_source=str(piece_row.get("source") or "").strip() or None,
                f6_source=str(piece_row.get("f6_source") or "").strip() or None,
                piece_type=piece_row.get("piece_type"),
                program_width=parse_optional_dimension(piece_row.get("program_width")),
                program_height=parse_optional_dimension(piece_row.get("program_height")),
                program_thickness=parse_optional_dimension(piece_row.get("program_thickness")),
            )

        def sync_program_dimensions_from_rows():
            from core.pgmx_processing import persist_piece_program_dimensions

            for piece_row in all_rows:
                piece_obj = build_piece_from_row(piece_row)
                persist_piece_program_dimensions(self.project, piece_obj, module_path, cache=program_dimensions_cache)
                piece_row["program_width"] = piece_obj.program_width
                piece_row["program_height"] = piece_obj.program_height
                piece_row["program_thickness"] = piece_obj.program_thickness

        def parse_optional_piece_float(raw_value: str):
            raw_text = (raw_value or "").strip().replace(",", ".")
            if not raw_text:
                return None
            try:
                return float(raw_text)
            except ValueError:
                return None

        def selected_piece_all_index(warning_title: str | None = None):
            current_row = pieces_table.currentRow()
            if current_row < 0:
                if warning_title:
                    QMessageBox.warning(inspect_dialog, warning_title, "Seleccione una pieza de la lista.")
                return None
            if current_row >= len(visible_row_indexes):
                return None
            return visible_row_indexes[current_row]

        def select_visible_piece_by_id(piece_id: str, fallback_row: int | None = None):
            normalized_id = str(piece_id or "").strip()
            if normalized_id:
                for row_idx, all_idx in enumerate(visible_row_indexes):
                    if str(all_rows[all_idx].get("id") or "").strip() == normalized_id:
                        pieces_table.selectRow(row_idx)
                        return

            if fallback_row is not None and pieces_table.rowCount() > 0:
                pieces_table.selectRow(max(0, min(fallback_row, pieces_table.rowCount() - 1)))

        def infer_companion_f6_source(source_value: str):
            normalized_source = str(source_value or "").strip()
            if not normalized_source:
                return None

            source_path = Path(normalized_source)
            if not source_path.is_absolute():
                source_path = module_path / source_path

            if source_path.stem.lower().endswith("f6"):
                return None

            f6_candidate = source_path.with_name(f"{source_path.stem}F6{source_path.suffix}")
            if f6_candidate.is_file():
                return normalize_source_path(str(f6_candidate))
            return None

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

        def update_piece_flag(all_idx: int, field_name: str, state: int):
            if refreshing_pieces_table:
                return
            all_rows[all_idx][field_name] = state == Qt.Checked
            persist_module_config()

        def refresh_pieces_table():
            nonlocal refreshing_pieces_table
            from core.model import PIECE_TYPE_ORDER
            from core.pgmx_processing import get_pgmx_program_dimension_notes

            _type_rank = {t: i for i, t in enumerate(PIECE_TYPE_ORDER)}

            sync_program_dimensions_from_rows()

            visible_row_indexes.clear()
            filtered = []
            for idx, row_data in enumerate(all_rows):
                if self._is_valid_thickness_value(row_data.get("thickness")):
                    filtered.append((idx, row_data))

            filtered.sort(key=lambda pair: _type_rank.get(pair[1].get("piece_type") or "", len(PIECE_TYPE_ORDER)))

            for all_idx, _ in filtered:
                visible_row_indexes.append(all_idx)

            pieces_title.setText(f"Piezas del módulo '{module_name}' ({len(filtered)} piezas):")
            pieces_table.setRowCount(len(filtered))
            refreshing_pieces_table = True
            filtered_piece_objects = [build_piece_from_row(piece_row) for _, piece_row in filtered]
            filtered_program_notes = get_pgmx_program_dimension_notes(
                self.project,
                filtered_piece_objects,
                module_path,
                cache=program_dimensions_cache,
            )

            for row_idx, (all_idx, piece_row) in enumerate(filtered):
                source_value = str(piece_row.get("source", "")).strip()
                pgmx_status = self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths)
                program_dimension_note = filtered_program_notes[row_idx]
                piece_row["pgmx"] = pgmx_status
                en_juego = bool(piece_row.get("en_juego", False))
                piece_row["en_juego"] = en_juego
                include_in_sheet = bool(piece_row.get("include_in_sheet", False))
                piece_row["include_in_sheet"] = include_in_sheet

                pieces_table.setItem(row_idx, 0, QTableWidgetItem(str(piece_row.get("id", ""))))
                pieces_table.setItem(row_idx, 1, QTableWidgetItem(str(piece_row.get("name", ""))))
                pieces_table.setItem(row_idx, 2, QTableWidgetItem(str(piece_row.get("quantity", ""))))
                pieces_table.setItem(row_idx, 3, QTableWidgetItem(str(piece_row.get("height", ""))))
                pieces_table.setItem(row_idx, 4, QTableWidgetItem(str(piece_row.get("width", ""))))
                pieces_table.setItem(row_idx, 5, QTableWidgetItem(str(piece_row.get("thickness", ""))))
                pieces_table.setItem(row_idx, 6, QTableWidgetItem(str(piece_row.get("color", ""))))
                program_filename = Path(source_value).name if source_value else "(ninguno)"
                program_item = QTableWidgetItem(f"{pgmx_status} {program_filename}")
                if pgmx_status == "✓":
                    program_item.setForeground(QColor("#4CAF50"))
                else:
                    program_item.setForeground(QColor("#B71C1C"))
                program_item.setToolTip(source_value or "(ninguno)")
                pieces_table.setItem(row_idx, 7, program_item)

                dimension_item = QTableWidgetItem(program_dimension_note)
                dimension_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if program_dimension_note:
                    dimension_item.setForeground(QColor("#B71C1C"))
                pieces_table.setItem(row_idx, 8, dimension_item)

                pieces_table.setCellWidget(
                    row_idx,
                    9,
                    create_centered_checkbox(
                        en_juego,
                        lambda state, idx=all_idx: update_piece_flag(idx, "en_juego", state),
                    ),
                )

                pieces_table.setCellWidget(
                    row_idx,
                    10,
                    create_centered_checkbox(
                        include_in_sheet,
                        lambda state, idx=all_idx: update_piece_flag(idx, "include_in_sheet", state),
                    ),
                )

            refreshing_pieces_table = False

        refresh_pieces_table()

        header = pieces_table.horizontalHeader()
        auto_columns = {0, 2, 3, 4, 5}
        fixed_column_widths = {
            1: _scaled_int(180, compact_scale, 120),
            6: _scaled_int(110, compact_scale, 90),
            7: _scaled_int(250, compact_scale, 170),
            8: _scaled_int(320, compact_scale, 180),
            9: _scaled_int(90, compact_scale, 68),
            10: _scaled_int(70, compact_scale, 60),
        }
        for column_idx in range(pieces_table.columnCount()):
            if column_idx in auto_columns:
                header.setSectionResizeMode(column_idx, QHeaderView.ResizeToContents)
            else:
                header.setSectionResizeMode(column_idx, QHeaderView.Fixed)
                pieces_table.setColumnWidth(column_idx, fixed_column_widths[column_idx])
        actions_column_reserved_width = MAIN_ACTION_BUTTON_WIDTH + 36
        pieces_table.setMinimumWidth(
            max(320, min(sum(fixed_column_widths.values()) + 520, inspect_width - actions_column_reserved_width))
        )
        pieces_table.verticalHeader().setDefaultSectionSize(_scaled_int(30, compact_scale, 22))

        pieces_table.setAlternatingRowColors(True)
        pieces_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pieces_table.setSelectionBehavior(QTableWidget.SelectRows)

        def persist_module_config():
            nonlocal has_unsaved_changes

            def parse_dimension(value: str):
                raw = (value or "").strip().replace(",", ".")
                if not raw:
                    return ""
                try:
                    number = float(raw)
                    return int(number) if number.is_integer() else round(number, 2)
                except ValueError:
                    return raw

            config_data["settings"] = {
                "x": parse_dimension(dim_x_field.text()),
                "y": parse_dimension(dim_y_field.text()),
                "z": parse_dimension(dim_z_field.text()),
                "herrajes_y_accesorios": herrajes_field.text().strip(),
                "guias_y_bisagras": guias_field.text().strip(),
                "detalles_de_obra": detalles_field.text().strip(),
            }
            sync_program_dimensions_from_rows()
            config_data["pieces"] = all_rows
            config_data["generated_at"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
            config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")
            # Actualizar el objeto ModuleData en memoria para que refleje las piezas guardadas
            selected_module.pieces = []
            for row in all_rows:
                piece_dict = dict(row)
                # Mapear 'source' a 'cnc_source' para compatibilidad con Piece
                if "source" in piece_dict:
                    piece_dict["cnc_source"] = piece_dict.pop("source")
                # Mapear 'module_name' si no existe
                if "module_name" not in piece_dict:
                    piece_dict["module_name"] = selected_module.name
                # Remover campos no esperados por Piece
                piece_dict.pop("pgmx", None)
                piece_dict.pop("en_juego", None)
                piece_dict.pop("include_in_sheet", None)
                
                # Validar y procesar thickness: convertir string vacío a None
                thickness_val = piece_dict.get("thickness")
                if thickness_val == "" or thickness_val is None:
                    piece_dict["thickness"] = None
                else:
                    try:
                        piece_dict["thickness"] = float(thickness_val)
                    except (ValueError, TypeError):
                        piece_dict["thickness"] = None
                
                # Validar height y width
                for dim in ["height", "width"]:
                    dim_val = piece_dict.get(dim)
                    if dim_val in ["", None]:
                        piece_dict[dim] = 0.0
                    else:
                        try:
                            piece_dict[dim] = float(dim_val)
                        except (ValueError, TypeError):
                            piece_dict[dim] = 0.0

                _coerce_optional_piece_float_fields(
                    piece_dict,
                    ("program_width", "program_height", "program_thickness"),
                )
                
                try:
                    piece = Piece(**piece_dict)
                    selected_module.pieces.append(piece)
                except Exception:
                    pass  # Ignorar piezas que no se puedan parsear correctamente
            self._write_locale_config_files()
            _save_project(self.project)
            if on_module_updated:
                on_module_updated()
            has_unsaved_changes = False

        def piece_from_row(piece_row):
            return build_piece_from_row(piece_row)

        def drawing_path_for_piece_row(piece_row):
            from core.pgmx_processing import _sanitize_filename

            piece_display_name = str(piece_row.get("name") or piece_row.get("id") or "pieza").strip()
            piece_slug = _sanitize_filename(piece_display_name)
            return module_path / f"{piece_slug}.svg"

        def open_drawing_dialog(drawing_path, piece_display_name):
            drawing_dialog = QDialog(inspect_dialog)
            drawing_dialog.setWindowTitle(f"Dibujo - {piece_display_name}")

            drawing_layout = QVBoxLayout()
            drawing_layout.addWidget(QLabel(f"Archivo: {drawing_path}"))

            svg_widget = QSvgWidget()
            svg_widget.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
            svg_widget.load(str(drawing_path))
            
            # Permitir que el widget se redimensione manteniendo aspect ratio
            svg_widget.setMinimumSize(300, 300)
            drawing_layout.addWidget(svg_widget, 1)  # stretch factor 1 para llenar espacio
            
            close_drawing_btn = QPushButton("Cerrar")
            close_drawing_btn.clicked.connect(drawing_dialog.accept)
            drawing_layout.addWidget(close_drawing_btn)

            drawing_dialog.setLayout(drawing_layout)
            drawing_scale, _, _ = _apply_responsive_window_size(
                drawing_dialog,
                1000,
                800,
                width_ratio=0.92,
                height_ratio=0.92,
            )
            svg_min = _scaled_int(300, max(drawing_scale, 0.82), 220)
            svg_widget.setMinimumSize(svg_min, svg_min)
            drawing_dialog.exec()

        def ensure_piece_drawing(piece_row, force_regenerate=False, show_warning=True):
            from core.pgmx_processing import build_piece_svg, parse_pgmx_for_piece

            drawing_path = drawing_path_for_piece_row(piece_row)
            piece_obj = piece_from_row(piece_row)

            if force_regenerate or not drawing_path.is_file():
                drawing_data = parse_pgmx_for_piece(self.project, piece_obj, module_path)
                if drawing_data is None:
                    if show_warning:
                        QMessageBox.warning(
                            inspect_dialog,
                            "Ver Dibujo",
                            "No se pudo generar el dibujo para la pieza seleccionada. Verifique el PGMX asociado.",
                        )
                    return None
                build_piece_svg(piece_obj, drawing_data, drawing_path)

            return drawing_path

        def select_source_for_selected_piece():
            current_row = pieces_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(inspect_dialog, "Source", "Seleccione una pieza de la lista.")
                return
            if current_row >= len(visible_row_indexes):
                return

            source_file, _ = QFileDialog.getOpenFileName(
                inspect_dialog,
                "Seleccionar programa asociado",
                str(module_path),
                "Programas PGMX (*.pgmx);;Todos los archivos (*.*)",
            )
            if not source_file:
                return

            all_idx = visible_row_indexes[current_row]
            source_path = Path(source_file)
            all_rows[all_idx]["source"] = normalize_source_path(source_file)
            companion_f6_source = ""
            if not source_path.stem.lower().endswith("f6"):
                f6_candidate = source_path.with_name(f"{source_path.stem}F6{source_path.suffix}")
                if f6_candidate.is_file():
                    companion_f6_source = normalize_source_path(str(f6_candidate))
            all_rows[all_idx]["f6_source"] = companion_f6_source or None
            persist_module_config()
            refresh_pieces_table()
            pieces_table.selectRow(current_row)

            drawing_path = ensure_piece_drawing(all_rows[all_idx], force_regenerate=True)
            if drawing_path is None:
                return

            piece_display_name = str(all_rows[all_idx].get("name") or all_rows[all_idx].get("id") or "pieza").strip()
            open_drawing_dialog(drawing_path, piece_display_name)

        def remove_source_for_selected_piece():
            current_row = pieces_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(inspect_dialog, "Quitar programa", "Seleccione una pieza de la lista.")
                return
            if current_row >= len(visible_row_indexes):
                return

            all_idx = visible_row_indexes[current_row]
            all_rows[all_idx]["source"] = ""
            all_rows[all_idx]["f6_source"] = None
            all_rows[all_idx]["program_width"] = None
            all_rows[all_idx]["program_height"] = None
            all_rows[all_idx]["program_thickness"] = None
            all_rows[all_idx]["pgmx"] = "✗"
            persist_module_config()
            refresh_pieces_table()
            pieces_table.selectRow(current_row)

        def open_piece_editor(piece_row=None, row_index=None):
            is_new_piece = piece_row is None
            base_piece_row = dict(piece_row or {})
            editor_dialog = QDialog(inspect_dialog)
            editor_dialog.setWindowTitle("Agregar pieza manual" if is_new_piece else "Editar pieza")
            editor_scale, _, _ = _apply_responsive_window_size(
                editor_dialog,
                1100,
                620,
                width_ratio=0.94,
                height_ratio=0.92,
            )
            editor_inline_button_width = _scaled_int(110, max(editor_scale, 0.82), 90)

            editor_layout = QVBoxLayout()
            content_layout = QHBoxLayout()
            content_layout.setSpacing(16)

            form_layout = QVBoxLayout()
            form_layout.setSpacing(6)

            id_field = QLineEdit(str(base_piece_row.get("id") or ""))
            name_field = QLineEdit(str(base_piece_row.get("name") or ""))
            qty_field = QLineEdit(str(base_piece_row.get("quantity") or "1"))
            height_field = QLineEdit(str(base_piece_row.get("height") or ""))
            width_field = QLineEdit(str(base_piece_row.get("width") or ""))
            thickness_field = QLineEdit(str(base_piece_row.get("thickness") or ""))
            color_field = QLineEdit(str(base_piece_row.get("color") or ""))
            grain_field = QLineEdit(str(base_piece_row.get("grain_direction") or ""))
            source_field = QLineEdit(str(base_piece_row.get("source") or ""))

            for label_text, field in (
                ("ID:", id_field),
                ("Nombre:", name_field),
                ("Cantidad:", qty_field),
                ("Alto:", height_field),
                ("Ancho:", width_field),
                ("Espesor:", thickness_field),
                ("Veta / Grain direction:", grain_field),
            ):
                form_layout.addWidget(QLabel(label_text))
                form_layout.addWidget(field)

            form_layout.addWidget(QLabel("Color:"))
            color_row = QHBoxLayout()
            color_row.addWidget(color_field, 1)
            apply_color_btn = None
            if not is_new_piece:
                apply_color_btn = QPushButton("Cambiar")
                apply_color_btn.setFixedSize(editor_inline_button_width, MAIN_ACTION_BUTTON_HEIGHT)
                color_row.addWidget(apply_color_btn)
            form_layout.addLayout(color_row)

            form_layout.addWidget(QLabel("Programa asociado (opcional):"))
            source_row = QHBoxLayout()
            select_source_btn = QPushButton("Seleccionar")
            select_source_btn.setFixedSize(editor_inline_button_width, MAIN_ACTION_BUTTON_HEIGHT)
            source_row.addWidget(source_field, 1)
            source_row.addWidget(select_source_btn)
            form_layout.addLayout(source_row)

            content_layout.addLayout(form_layout, 1)

            preview_layout = QVBoxLayout()
            preview_layout.setSpacing(8)
            preview_layout.addWidget(QLabel("Vista previa del programa asociado:"))

            preview_info_label = QLabel("")
            preview_info_label.setWordWrap(True)
            preview_layout.addWidget(preview_info_label)

            preview_svg = QSvgWidget()
            preview_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
            preview_min_size = _scaled_int(360, max(editor_scale, 0.82), 220)
            preview_svg.setMinimumSize(preview_min_size, preview_min_size)
            preview_layout.addWidget(preview_svg, 1)

            preview_placeholder = QLabel("Sin dibujo disponible para esta pieza.")
            preview_placeholder.setAlignment(Qt.AlignCenter)
            preview_placeholder.setWordWrap(True)
            preview_placeholder.setStyleSheet("color: #666; border: 1px dashed #999; padding: 12px;")
            preview_layout.addWidget(preview_placeholder, 1)

            refresh_preview_btn = QPushButton("Actualizar Vista")
            refresh_preview_btn.setFixedHeight(MAIN_ACTION_BUTTON_HEIGHT)
            preview_layout.addWidget(refresh_preview_btn)

            content_layout.addLayout(preview_layout, 1)
            editor_layout.addLayout(content_layout, 1)

            def build_editor_piece_row():
                piece_id = id_field.text().strip()
                source_value = source_field.text().strip()
                normalized_source = normalize_source_path(source_value) if source_value else ""

                updated_piece = dict(base_piece_row)
                updated_piece.update(
                    {
                        "id": piece_id,
                        "name": name_field.text().strip() or piece_id,
                        "quantity": int(qty_field.text().strip()) if qty_field.text().strip().isdigit() else 1,
                        "height": parse_optional_piece_float(height_field.text()),
                        "width": parse_optional_piece_float(width_field.text()),
                        "thickness": parse_optional_piece_float(thickness_field.text()),
                        "color": color_field.text().strip() or None,
                        "grain_direction": grain_field.text().strip() or None,
                        "source": normalized_source,
                        "f6_source": infer_companion_f6_source(normalized_source),
                        "pgmx": self._get_pgmx_status(normalized_source, pgmx_names, pgmx_relpaths),
                        "program_width": base_piece_row.get("program_width"),
                        "program_height": base_piece_row.get("program_height"),
                        "program_thickness": base_piece_row.get("program_thickness"),
                        "en_juego": bool(base_piece_row.get("en_juego", False)),
                        "include_in_sheet": bool(base_piece_row.get("include_in_sheet", False)),
                    }
                )
                return updated_piece

            def refresh_piece_preview():
                preview_piece_row = build_editor_piece_row()
                preview_source = str(preview_piece_row.get("source") or "").strip()
                preview_info_label.setText(
                    f"Programa asociado: {preview_source or '(ninguno)'}"
                )

                preview_svg.hide()
                preview_placeholder.show()

                if not preview_source:
                    preview_placeholder.setText("La pieza no tiene un programa PGMX asociado.")
                    return

                drawing_path = ensure_piece_drawing(
                    preview_piece_row,
                    force_regenerate=True,
                    show_warning=False,
                )
                if drawing_path is None or not drawing_path.is_file():
                    preview_placeholder.setText(
                        "No se pudo generar la imagen del PGMX asociado. Verifique el archivo seleccionado."
                    )
                    return

                preview_svg.load(str(drawing_path))
                preview_placeholder.hide()
                preview_svg.show()

            def select_source_from_editor():
                source_file, _ = QFileDialog.getOpenFileName(
                    editor_dialog,
                    "Seleccionar programa asociado",
                    str(module_path),
                    "Programas PGMX (*.pgmx);;Todos los archivos (*.*)",
                )
                if not source_file:
                    return
                source_field.setText(normalize_source_path(source_file))
                refresh_piece_preview()

            def apply_color_from_editor():
                if is_new_piece or row_index is None:
                    return
                current_color = str(base_piece_row.get("color") or "")
                preferred_color = color_field.text().strip() or None
                piece_thickness = parse_optional_piece_float(thickness_field.text())
                new_color_val = apply_color_change(
                    current_color,
                    target_row_index=row_index,
                    preferred_color=preferred_color,
                    piece_thickness=piece_thickness,
                )
                if new_color_val is None:
                    return
                base_piece_row["color"] = new_color_val
                color_field.setText(new_color_val or "")

            def save_piece_changes():
                piece_id = id_field.text().strip()
                if not piece_id:
                    QMessageBox.warning(editor_dialog, "Editar pieza", "El campo ID es obligatorio.")
                    return

                updated_piece = build_editor_piece_row()
                fallback_row = pieces_table.currentRow()
                if is_new_piece:
                    all_rows.append(updated_piece)
                else:
                    all_rows[row_index] = updated_piece

                persist_module_config()
                refresh_pieces_table()
                select_visible_piece_by_id(updated_piece["id"], fallback_row=fallback_row)
                editor_dialog.accept()

            editor_buttons = QHBoxLayout()
            editor_buttons.addStretch(1)
            btn_save_piece = QPushButton("Guardar")
            btn_cancel_piece = QPushButton("Cancelar")
            btn_save_piece.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            btn_cancel_piece.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            btn_save_piece.clicked.connect(save_piece_changes)
            btn_cancel_piece.clicked.connect(editor_dialog.reject)
            editor_buttons.addWidget(btn_save_piece)
            editor_buttons.addWidget(btn_cancel_piece)
            editor_layout.addLayout(editor_buttons)

            select_source_btn.clicked.connect(select_source_from_editor)
            if apply_color_btn is not None:
                apply_color_btn.clicked.connect(apply_color_from_editor)
            refresh_preview_btn.clicked.connect(refresh_piece_preview)
            editor_dialog.setLayout(editor_layout)
            refresh_piece_preview()
            editor_dialog.exec()

        def add_manual_piece():
            open_piece_editor()

        def edit_selected_piece():
            all_idx = selected_piece_all_index("Editar pieza")
            if all_idx is None:
                return
            open_piece_editor(all_rows[all_idx], row_index=all_idx)

        def remove_selected_piece():
            current_row = pieces_table.currentRow()
            all_idx = selected_piece_all_index("Eliminar pieza")
            if all_idx is None:
                return

            piece_row = all_rows[all_idx]
            piece_display_name = str(piece_row.get("name") or piece_row.get("id") or "pieza").strip()
            answer = QMessageBox.question(
                inspect_dialog,
                "Eliminar pieza",
                f'¿Desea eliminar la pieza "{piece_display_name}"?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

            all_rows.pop(all_idx)
            persist_module_config()
            refresh_pieces_table()
            select_visible_piece_by_id("", fallback_row=current_row)

        def _legacy_apply_color_change_unused(current_color: str, new_color_val, target_row_index: int | None = None) -> bool:
            scope_box = QMessageBox(inspect_dialog)
            scope_box.setWindowTitle("Cambiar color")
            scope_box.setText(
                f"¿Dónde aplicar el cambio de color?\n\n"
                f"Color anterior: {current_color or '(sin color)'}\n"
                f"Color nuevo: {new_color_val or '(sin color)'}"
            )
            btn_solo = scope_box.addButton("Solo esta pieza", QMessageBox.ActionRole)
            btn_modulo = scope_box.addButton("Todas en este módulo", QMessageBox.ActionRole)
            btn_proyecto = scope_box.addButton("Todas en el proyecto", QMessageBox.ActionRole)
            scope_box.addButton("Cancelar", QMessageBox.RejectRole)
            scope_box.exec()
            clicked = scope_box.clickedButton()

            if clicked is None or clicked not in (btn_solo, btn_modulo, btn_proyecto):
                return False

            if clicked == btn_solo:
                if target_row_index is None or target_row_index >= len(all_rows):
                    return False
                all_rows[target_row_index]["color"] = new_color_val
                persist_module_config()

            elif clicked == btn_modulo:
                for row in all_rows:
                    if str(row.get("color") or "") == current_color:
                        row["color"] = new_color_val
                persist_module_config()

            elif clicked == btn_proyecto:
                # Aplicar en el módulo actual (en memoria)
                for row in all_rows:
                    if str(row.get("color") or "") == current_color:
                        row["color"] = new_color_val
                persist_module_config()

                # Aplicar en todos los demás módulos del proyecto
                for mod in self.project.modules:
                    if (mod.relative_path or mod.path) == (selected_module.relative_path or selected_module.path):
                        continue
                    other_config_path = self._module_config_path(mod)
                    if not other_config_path.exists():
                        continue
                    try:
                        other_config = json.loads(other_config_path.read_text(encoding="utf-8"))
                        changed = False
                        for row in other_config.get("pieces", []):
                            if str(row.get("color") or "") == current_color:
                                row["color"] = new_color_val
                                changed = True
                        if changed:
                            other_config["generated_at"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
                            other_config_path.write_text(
                                json.dumps(other_config, indent=2, ensure_ascii=False), encoding="utf-8"
                            )
                    except Exception:
                        pass

            refresh_pieces_table()
            return True

        def _configured_board_colors(piece_thickness: float | None = None) -> list[str]:
            colors: list[str] = []
            seen: set[str] = set()
            for board in _read_app_settings().get("available_boards", []):
                color = str(board.get("color") or "").strip()
                if not color:
                    continue
                if piece_thickness is not None:
                    try:
                        board_thickness = float(board.get("thickness"))
                    except (TypeError, ValueError):
                        continue
                    if abs(board_thickness - piece_thickness) > 0.001:
                        continue
                color_key = color.lower()
                if color_key in seen:
                    continue
                seen.add(color_key)
                colors.append(color)
            return colors

        def _module_locale_key(module: ModuleData) -> str:
            locale_name = str(module.locale_name or "").strip()
            if locale_name:
                return locale_name.lower()

            relative_path = str(module.relative_path or "").strip()
            if relative_path:
                relative_parts = Path(relative_path).parts
                if relative_parts:
                    return str(relative_parts[0]).strip().lower()

            try:
                root_path = Path(self.project.root_directory).resolve()
                module_relative = Path(module.path).resolve().relative_to(root_path)
                if module_relative.parts:
                    return str(module_relative.parts[0]).strip().lower()
            except Exception:
                pass

            return ""

        def _prompt_color_change(
            current_color: str,
            preferred_color: str | None = None,
            piece_thickness: float | None = None,
        ):
            available_colors = _configured_board_colors(piece_thickness=piece_thickness)
            if not available_colors:
                thickness_label = (
                    f" para espesor {int(piece_thickness) if float(piece_thickness).is_integer() else piece_thickness} mm"
                    if piece_thickness is not None
                    else ""
                )
                QMessageBox.warning(
                    inspect_dialog,
                    "Cambiar color",
                    f"No hay colores disponibles en los tableros configurados{thickness_label}.",
                )
                return None

            color_dialog = QDialog(inspect_dialog)
            color_dialog.setWindowTitle("Cambiar color")
            color_layout = QVBoxLayout()
            color_layout.addWidget(
                QLabel(
                    "Seleccione el nuevo color para la pieza.\n"
                    f"Color actual: {current_color or '(sin color)'}"
                )
            )

            colors_list = QListWidget()
            for color in available_colors:
                colors_list.addItem(color)
            color_layout.addWidget(colors_list)

            locale_key = _module_locale_key(selected_module)
            scope_layout = QVBoxLayout()
            scope_layout.addWidget(QLabel("Aplicar a:"))
            only_piece_option = QRadioButton("Solo esta pieza")
            module_option = QRadioButton("Todas las piezas del mismo color de este modulo")
            locale_option = QRadioButton("Todas las piezas del mismo color de este local")
            only_piece_option.setChecked(True)
            locale_option.setEnabled(bool(locale_key))
            scope_layout.addWidget(only_piece_option)
            scope_layout.addWidget(module_option)
            scope_layout.addWidget(locale_option)
            color_layout.addLayout(scope_layout)

            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch(1)
            accept_button = QPushButton("Aceptar")
            cancel_button = QPushButton("Cancelar")
            accept_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            buttons_layout.addWidget(accept_button)
            buttons_layout.addWidget(cancel_button)
            color_layout.addLayout(buttons_layout)

            preferred_candidates = [
                str(preferred_color or "").strip(),
                str(current_color or "").strip(),
            ]
            selected_row = 0
            for candidate in preferred_candidates:
                if not candidate:
                    continue
                for row_idx in range(colors_list.count()):
                    item = colors_list.item(row_idx)
                    if item is not None and item.text().strip().lower() == candidate.lower():
                        selected_row = row_idx
                        break
                else:
                    continue
                break
            if colors_list.count() > 0:
                colors_list.setCurrentRow(selected_row)

            def accept_color_selection():
                if colors_list.currentItem() is None:
                    QMessageBox.warning(color_dialog, "Cambiar color", "Seleccione un color.")
                    return
                color_dialog.accept()

            accept_button.clicked.connect(accept_color_selection)
            cancel_button.clicked.connect(color_dialog.reject)
            colors_list.itemDoubleClicked.connect(lambda _item: accept_color_selection())

            color_dialog.setLayout(color_layout)
            if color_dialog.exec() != QDialog.Accepted or colors_list.currentItem() is None:
                return None

            if locale_option.isChecked() and locale_option.isEnabled():
                scope = "locale"
            elif module_option.isChecked():
                scope = "module"
            else:
                scope = "piece"

            return colors_list.currentItem().text().strip() or None, scope

        def apply_color_change(
            current_color: str,
            target_row_index: int | None = None,
            preferred_color: str | None = None,
            piece_thickness: float | None = None,
        ):
            selection = _prompt_color_change(
                current_color,
                preferred_color=preferred_color,
                piece_thickness=piece_thickness,
            )
            if selection is None:
                return None

            new_color_val, scope = selection
            selected_piece_id = ""
            fallback_row = pieces_table.currentRow()
            if target_row_index is not None and 0 <= target_row_index < len(all_rows):
                selected_piece_id = str(all_rows[target_row_index].get("id") or "").strip()

            if scope == "piece":
                if target_row_index is None or target_row_index >= len(all_rows):
                    return None
                all_rows[target_row_index]["color"] = new_color_val
                persist_module_config()

            elif scope == "module":
                for row in all_rows:
                    if str(row.get("color") or "") == current_color:
                        row["color"] = new_color_val
                persist_module_config()

            else:
                for row in all_rows:
                    if str(row.get("color") or "") == current_color:
                        row["color"] = new_color_val
                persist_module_config()

                current_locale_key = _module_locale_key(selected_module)
                for mod in self.project.modules:
                    if (mod.relative_path or mod.path) == (selected_module.relative_path or selected_module.path):
                        continue
                    if _module_locale_key(mod) != current_locale_key:
                        continue

                    for piece in getattr(mod, "pieces", []):
                        if str(piece.color or "") == current_color:
                            piece.color = new_color_val

                    other_config_path = self._module_config_path(mod)
                    if not other_config_path.exists():
                        continue
                    try:
                        other_config = json.loads(other_config_path.read_text(encoding="utf-8"))
                        changed = False
                        for row in other_config.get("pieces", []):
                            if str(row.get("color") or "") == current_color:
                                row["color"] = new_color_val
                                changed = True
                        if changed:
                            other_config["generated_at"] = datetime.datetime.now().isoformat(
                                sep=" ",
                                timespec="seconds",
                            )
                            other_config_path.write_text(
                                json.dumps(other_config, indent=2, ensure_ascii=False),
                                encoding="utf-8",
                            )
                    except Exception:
                        pass

            refresh_pieces_table()
            if selected_piece_id:
                select_visible_piece_by_id(selected_piece_id, fallback_row=fallback_row)
            return new_color_val

        def view_drawing_for_selected_piece():
            current_row = pieces_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(inspect_dialog, "Ver Dibujo", "Seleccione una pieza de la lista.")
                return
            if current_row >= len(visible_row_indexes):
                return

            all_idx = visible_row_indexes[current_row]
            piece_row = all_rows[all_idx]
            piece_display_name = str(piece_row.get("name") or piece_row.get("id") or "pieza").strip()
            drawing_path = ensure_piece_drawing(piece_row, force_regenerate=False)

            if drawing_path is None or not drawing_path.is_file():
                QMessageBox.warning(
                    inspect_dialog,
                    "Ver Dibujo",
                    (
                        "No se encontró el dibujo SVG para la pieza seleccionada.\n\n"
                        f"Ruta esperada: {drawing_path}\n\n"
                        "Procese el proyecto para generar los dibujos."
                    ),
                )
                return

            open_drawing_dialog(drawing_path, piece_display_name)

        def open_en_juego_configuration_dialog():
            en_juego_rows = [
                row
                for row in all_rows
                if bool(row.get("en_juego", False)) and self._is_valid_thickness_value(row.get("thickness"))
            ]
            if not en_juego_rows:
                QMessageBox.warning(
                    inspect_dialog,
                    "Configurar En Juego",
                    "No hay piezas marcadas como 'En juego' en este módulo.",
                )
                return

            from PySide6.QtCore import QPointF, Qt as QtCoreQt
            from PySide6.QtGui import QBrush, QColor as QColorGui, QPainter, QPainterPath, QPen
            from PySide6.QtWidgets import (
                QGraphicsEllipseItem,
                QGraphicsItem,
                QGraphicsLineItem,
                QGraphicsPathItem,
                QGraphicsRectItem,
                QGraphicsScene,
                QGraphicsSimpleTextItem,
                QGraphicsView,
            )

            preview_gap_mm = 120.0
            scene_padding_mm = 400.0
            snap_distance_mm = 18.0
            en_juego_saw_kerf_mm = _coerce_setting_number(
                _read_app_settings().get("cut_saw_kerf"),
                4.0,
                minimum=0.0,
            )
            saved_layout = config_data.get("en_juego_layout", {})
            if not isinstance(saved_layout, dict):
                saved_layout = {}

            class EnJuegoGraphicsView(QGraphicsView):
                def __init__(self, graphics_scene, parent=None):
                    super().__init__(graphics_scene, parent)
                    self.setRenderHint(QPainter.Antialiasing, True)
                    self.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    self.setDragMode(QGraphicsView.ScrollHandDrag)
                    self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
                    self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

                def wheelEvent(self, event):
                    if event.angleDelta().y() == 0:
                        super().wheelEvent(event)
                        return
                    scale_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
                    self.scale(scale_factor, scale_factor)

            config_dialog = QDialog(inspect_dialog)
            config_dialog.setWindowTitle(f"Configurar En Juego - {module_name}")
            config_scale, _, _ = _apply_responsive_window_size(
                config_dialog,
                1500,
                900,
                width_ratio=0.96,
                height_ratio=0.92,
            )

            main_layout = QVBoxLayout()
            main_layout.addWidget(
                QLabel(
                    "Arrastre las piezas en juego para definir su disposición relativa.\n"
                    "Cada unidad se muestra por separado según su cantidad y se identifica con #.\n"
                    "La posición se guarda en el módulo para reutilizarla más adelante."
                )
            )

            content_layout = QHBoxLayout()
            pieces_list = QListWidget()
            pieces_list.setMinimumWidth(_scaled_int(320, max(config_scale, 0.82), 220))
            content_layout.addWidget(pieces_list)

            scene = QGraphicsScene(config_dialog)
            view = EnJuegoGraphicsView(scene)
            content_layout.addWidget(view, 1)
            main_layout.addLayout(content_layout)

            def safe_float(value):
                if value is None:
                    return None
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

            def en_juego_quantity(piece_row: dict) -> int:
                quantity_raw = str(piece_row.get("quantity") or "").strip()
                try:
                    quantity = int(quantity_raw)
                except (TypeError, ValueError):
                    return 1
                return quantity if quantity > 0 else 1

            def en_juego_instance_key(piece_id: str, copy_index: int) -> str:
                return f"{piece_id}#{copy_index}"

            def saved_layout_for_instance(piece_id: str, copy_index: int):
                instance_key = en_juego_instance_key(piece_id, copy_index)
                stored = saved_layout.get(instance_key)
                if isinstance(stored, dict):
                    return stored, instance_key

                legacy_stored = saved_layout.get(piece_id) if copy_index == 1 else None
                if isinstance(legacy_stored, dict):
                    return legacy_stored, instance_key

                return None, instance_key

            def preview_dimensions_mm(piece_row: dict, drawing_data=None) -> tuple[float, float]:
                if drawing_data is not None:
                    top_dimensions = drawing_data.face_dimensions.get("Top")
                    if top_dimensions and top_dimensions[0] > 0 and top_dimensions[1] > 0:
                        return float(top_dimensions[0]), float(top_dimensions[1])
                program_width = safe_float(piece_row.get("program_width")) or 0.0
                program_height = safe_float(piece_row.get("program_height")) or 0.0
                if program_width > 0 and program_height > 0:
                    return program_width, program_height
                return safe_float(piece_row.get("width")) or 0.0, safe_float(piece_row.get("height")) or 0.0

            drawing_data_cache: dict[str, object | None] = {}

            def piece_drawing_data(piece_row: dict):
                from core.pgmx_processing import parse_pgmx_for_piece

                piece_id = str(piece_row.get("id") or "").strip()
                if piece_id in drawing_data_cache:
                    return drawing_data_cache[piece_id]

                piece_obj = piece_from_row(piece_row)
                if not piece_obj.cnc_source:
                    drawing_data_cache[piece_id] = None
                    return None

                try:
                    drawing_data = parse_pgmx_for_piece(self.project, piece_obj, module_path)
                except Exception:
                    drawing_data = None
                drawing_data_cache[piece_id] = drawing_data
                return drawing_data

            def make_pen(color: str, width: float = 1.2, dashed: bool = False):
                pen = QPen(QColorGui(color))
                pen.setWidthF(width)
                pen.setCosmetic(True)
                if dashed:
                    pen.setStyle(QtCoreQt.DashLine)
                return pen

            def clamp(value: float, lower: float, upper: float) -> float:
                return max(lower, min(upper, value))

            def to_scene_y(y_mm: float, piece_height_mm: float) -> float:
                return piece_height_mm - y_mm

            class EnJuegoPieceItem(QGraphicsRectItem):
                def itemChange(self, change, value):
                    if change == QGraphicsItem.ItemPositionChange and self.scene() is not None:
                        proposed_pos = QPointF(value)
                        current_pos = self.pos()
                        current_rect = self.sceneBoundingRect()
                        delta_x = proposed_pos.x() - current_pos.x()
                        delta_y = proposed_pos.y() - current_pos.y()
                        candidate_rect = current_rect.translated(delta_x, delta_y)

                        target_xs = []
                        target_ys = []
                        for other_item in self.scene().items():
                            if other_item is self or not str(other_item.data(0) or "").strip():
                                continue
                            other_rect = other_item.sceneBoundingRect()
                            target_xs.extend([
                                other_rect.left() - candidate_rect.left(),
                                other_rect.right() - candidate_rect.right(),
                                other_rect.right() + en_juego_saw_kerf_mm - candidate_rect.left(),
                                other_rect.left() - en_juego_saw_kerf_mm - candidate_rect.right(),
                            ])
                            target_ys.extend([
                                other_rect.top() - candidate_rect.top(),
                                other_rect.bottom() - candidate_rect.bottom(),
                                other_rect.bottom() + en_juego_saw_kerf_mm - candidate_rect.top(),
                                other_rect.top() - en_juego_saw_kerf_mm - candidate_rect.bottom(),
                            ])

                        snapped_delta_x = None
                        for candidate_delta_x in target_xs:
                            if abs(candidate_delta_x) > snap_distance_mm:
                                continue
                            if snapped_delta_x is None or abs(candidate_delta_x) < abs(snapped_delta_x):
                                snapped_delta_x = candidate_delta_x

                        snapped_delta_y = None
                        for candidate_delta_y in target_ys:
                            if abs(candidate_delta_y) > snap_distance_mm:
                                continue
                            if snapped_delta_y is None or abs(candidate_delta_y) < abs(snapped_delta_y):
                                snapped_delta_y = candidate_delta_y

                        if snapped_delta_x is not None:
                            proposed_pos.setX(proposed_pos.x() + snapped_delta_x)
                        if snapped_delta_y is not None:
                            proposed_pos.setY(proposed_pos.y() + snapped_delta_y)
                        return proposed_pos

                    if change == QGraphicsItem.ItemPositionHasChanged and self.scene() is not None:
                        items_rect = self.scene().itemsBoundingRect()
                        if not items_rect.isNull():
                            padded_rect = items_rect.adjusted(
                                -scene_padding_mm,
                                -scene_padding_mm,
                                scene_padding_mm,
                                scene_padding_mm,
                            )
                            self.scene().setSceneRect(padded_rect)

                    return super().itemChange(change, value)

            def build_piece_scene_item(piece_row: dict, scene_item_key: str, title_text: str):
                piece_id = str(piece_row.get("id") or "").strip()
                drawing_data = piece_drawing_data(piece_row)
                width_mm, height_mm = preview_dimensions_mm(piece_row, drawing_data)
                width_mm = max(width_mm, 1.0)
                height_mm = max(height_mm, 1.0)

                rect_item = EnJuegoPieceItem(0, 0, width_mm, height_mm)
                rect_item.setPen(make_pen("#2F4F4F", 1.3))
                rect_item.setBrush(QBrush(QColorGui("#FFFDF8")))
                rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                rect_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                rect_item.setTransformOriginPoint(width_mm / 2.0, height_mm / 2.0)
                rect_item.setData(0, scene_item_key)
                rect_item.setData(1, piece_id)

                title_item = QGraphicsSimpleTextItem(title_text, rect_item)
                title_item.setBrush(QBrush(QColorGui("#111111")))
                title_item.setScale(4.0)
                title_item.setPos(6.0, 6.0)
                title_item.setAcceptedMouseButtons(QtCoreQt.NoButton)

                if drawing_data is None:
                    empty_item = QGraphicsSimpleTextItem("(sin dibujo)", rect_item)
                    empty_item.setBrush(QBrush(QColorGui("#666666")))
                    empty_item.setScale(4.0)
                    empty_item.setPos(6.0, 26.0)
                    empty_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    return rect_item, width_mm, height_mm

                for path in drawing_data.milling_paths:
                    if (path.face or "Top").strip().lower() != "top":
                        continue
                    if len(path.points) < 2:
                        continue
                    painter_path = QPainterPath()
                    first_x, first_y = path.points[0]
                    painter_path.moveTo(first_x, to_scene_y(first_y, height_mm))
                    for point_x, point_y in path.points[1:]:
                        painter_path.lineTo(point_x, to_scene_y(point_y, height_mm))
                    path_item = QGraphicsPathItem(painter_path, rect_item)
                    path_item.setPen(make_pen("#0B7A75", 1.0))
                    path_item.setAcceptedMouseButtons(QtCoreQt.NoButton)

                for operation in drawing_data.operations:
                    face = (operation.face or "Top").strip().lower()
                    op_x = clamp(float(operation.x or 0.0), 0.0, width_mm)
                    op_y = clamp(float(operation.y or 0.0), 0.0, height_mm)
                    scene_y = to_scene_y(op_y, height_mm)

                    if face == "top":
                        if operation.op_type == "drill":
                            diameter = float(operation.diameter or 5.0)
                            radius = max(1.0, diameter / 2.0)
                            ellipse_item = QGraphicsEllipseItem(op_x - radius, scene_y - radius, radius * 2.0, radius * 2.0, rect_item)
                            ellipse_item.setPen(make_pen("#C0392B", 1.0))
                            ellipse_item.setBrush(QBrush(QColorGui("#C0392B")))
                            ellipse_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                        elif operation.op_type == "slot":
                            slot_w = max(2.0, float(operation.width or 5.0))
                            slot_h = max(2.0, float(operation.height or 5.0))
                            slot_item = QGraphicsRectItem(op_x, scene_y - slot_h, slot_w, slot_h, rect_item)
                            slot_item.setPen(make_pen("#1F78B4", 0.9))
                            slot_item.setBrush(QBrush(QtCoreQt.transparent))
                            slot_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    elif face == "bottom":
                        diameter = float(operation.diameter or 5.0)
                        radius = max(1.0, diameter / 2.0)
                        ellipse_item = QGraphicsEllipseItem(op_x - radius, scene_y - radius, radius * 2.0, radius * 2.0, rect_item)
                        ellipse_item.setPen(make_pen("#1F78B4", 1.0, dashed=True))
                        ellipse_item.setBrush(QBrush(QtCoreQt.transparent))
                        ellipse_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    else:
                        side_line = QGraphicsLineItem(op_x, scene_y, op_x + 10.0, scene_y, rect_item)
                        side_line.setPen(make_pen("#1F78B4", 1.0, dashed=True))
                        side_line.setAcceptedMouseButtons(QtCoreQt.NoButton)

                return rect_item, width_mm, height_mm

            en_juego_instances = []
            for piece_row in en_juego_rows:
                piece_id = str(piece_row.get("id") or "").strip()
                if not piece_id:
                    continue
                base_title = str(piece_row.get("name") or piece_id).strip() or piece_id
                for copy_index in range(1, en_juego_quantity(piece_row) + 1):
                    en_juego_instances.append(
                        {
                            "piece_id": piece_id,
                            "piece_row": piece_row,
                            "copy_index": copy_index,
                            "instance_key": en_juego_instance_key(piece_id, copy_index),
                            "title_text": f"{base_title} #{copy_index}",
                        }
                    )

            current_unsaved_x_mm = 0.0
            current_unsaved_y_mm = 0.0
            current_row_max_h_mm = 0.0
            layout_wrap_mm = 2400.0
            for instance in en_juego_instances:
                piece_row = instance["piece_row"]
                piece_id = instance["piece_id"]
                copy_index = instance["copy_index"]
                stored, _ = saved_layout_for_instance(piece_id, copy_index)
                if not isinstance(stored, dict):
                    continue
                stored_x = safe_float(stored.get("x"))
                stored_y = safe_float(stored.get("y"))
                if stored_x is not None and stored_y is not None:
                    width_mm, _ = preview_dimensions_mm(piece_row, piece_drawing_data(piece_row))
                    current_unsaved_x_mm = max(current_unsaved_x_mm, stored_x + width_mm + preview_gap_mm)

            item_by_instance_id: dict[str, object] = {}

            for instance in en_juego_instances:
                piece_row = instance["piece_row"]
                piece_id = instance["piece_id"]
                copy_index = instance["copy_index"]
                instance_key = instance["instance_key"]
                title_text = instance["title_text"]

                rect_item, width_mm, height_mm = build_piece_scene_item(piece_row, instance_key, title_text)

                stored, _ = saved_layout_for_instance(piece_id, copy_index)
                stored_x_mm = safe_float(stored.get("x")) if isinstance(stored, dict) else None
                stored_y_mm = safe_float(stored.get("y")) if isinstance(stored, dict) else None
                stored_rotation = safe_float(stored.get("rotation")) if isinstance(stored, dict) else None
                if stored_x_mm is not None and stored_y_mm is not None:
                    pos_x_mm = stored_x_mm
                    pos_y_mm = stored_y_mm
                else:
                    if current_unsaved_x_mm > 0 and current_unsaved_x_mm + width_mm > layout_wrap_mm:
                        current_unsaved_x_mm = 0.0
                        current_unsaved_y_mm += current_row_max_h_mm + preview_gap_mm
                        current_row_max_h_mm = 0.0

                    pos_x_mm = current_unsaved_x_mm
                    pos_y_mm = current_unsaved_y_mm
                    current_unsaved_x_mm += width_mm + preview_gap_mm
                    current_row_max_h_mm = max(current_row_max_h_mm, height_mm)

                rect_item.setPos(pos_x_mm, pos_y_mm)
                if stored_rotation is not None:
                    rect_item.setRotation(stored_rotation)
                scene.addItem(rect_item)

                list_text = f"{title_text} | {int(round(width_mm))} x {int(round(height_mm))}"
                list_item = QListWidgetItem(list_text)
                list_item.setData(Qt.UserRole, instance_key)
                pieces_list.addItem(list_item)
                item_by_instance_id[instance_key] = rect_item

            def update_scene_bounds():
                items_rect = scene.itemsBoundingRect()
                if items_rect.isNull():
                    return
                padded_rect = items_rect.adjusted(-scene_padding_mm, -scene_padding_mm, scene_padding_mm, scene_padding_mm)
                scene.setSceneRect(padded_rect)

            def focus_selected_piece():
                current_item = pieces_list.currentItem()
                if current_item is None:
                    return
                instance_key = str(current_item.data(Qt.UserRole) or "")
                scene_item = item_by_instance_id.get(instance_key)
                if scene_item is None:
                    return
                scene.clearSelection()
                scene_item.setSelected(True)
                view.centerOn(scene_item)

            pieces_list.currentItemChanged.connect(lambda *_: focus_selected_piece())

            if pieces_list.count() > 0:
                pieces_list.setCurrentRow(0)

            update_scene_bounds()
            items_rect = scene.itemsBoundingRect()
            if not items_rect.isNull():
                view.fitInView(items_rect.adjusted(-80, -80, 80, 80), Qt.KeepAspectRatio)

            def selected_scene_item():
                selected_items = [item for item in scene.selectedItems() if str(item.data(0) or "").strip()]
                if selected_items:
                    return selected_items[0]
                current_item = pieces_list.currentItem()
                if current_item is None:
                    return None
                instance_key = str(current_item.data(Qt.UserRole) or "")
                return item_by_instance_id.get(instance_key)

            def rotate_selected_piece(delta: float):
                scene_item = selected_scene_item()
                if scene_item is None:
                    QMessageBox.warning(config_dialog, "Configurar En Juego", "Seleccione una pieza para rotarla.")
                    return
                scene_item.setRotation((scene_item.rotation() + delta) % 360)
                update_scene_bounds()
                view.centerOn(scene_item)

            def collect_en_juego_layout_data():
                layout_data = {}
                for instance_key, scene_item in item_by_instance_id.items():
                    layout_data[instance_key] = {
                        "x": round(scene_item.pos().x(), 2),
                        "y": round(scene_item.pos().y(), 2),
                        "rotation": round(scene_item.rotation(), 2),
                    }
                return layout_data

            def save_en_juego_layout():
                config_data["en_juego_layout"] = collect_en_juego_layout_data()
                persist_module_config()
                config_dialog.accept()

            def create_en_juego_pgmx_from_dialog():
                from core.en_juego_pgmx import create_en_juego_pgmx

                default_name = f"{module_name}_EnJuego.pgmx"
                default_path = module_path / default_name
                output_file, _ = QFileDialog.getSaveFileName(
                    config_dialog,
                    "Crear En-Juego",
                    str(default_path),
                    "Programas PGMX (*.pgmx);;Todos los archivos (*.*)",
                )
                if not output_file:
                    return

                config_data["en_juego_layout"] = collect_en_juego_layout_data()
                persist_module_config()

                try:
                    result = create_en_juego_pgmx(
                        project=self.project,
                        module_name=module_name,
                        module_path=module_path,
                        piece_rows=all_rows,
                        saved_layout=config_data.get("en_juego_layout", {}),
                        output_path=Path(output_file),
                    )
                except Exception as exc:
                    QMessageBox.critical(
                        config_dialog,
                        "Crear En-Juego",
                        f"No se pudo generar el archivo En-Juego.\n\n{exc}",
                    )
                    return

                details = [
                    f"Archivo generado: {result.output_path}",
                    f"Tablero sintetizado: {result.board_width:.2f} x {result.board_height:.2f} x {result.board_thickness:.2f} mm",
                    f"Piezas ubicadas: {result.instance_count}",
                    f"Contornos generados: {result.contour_count}",
                ]
                if result.fallback_contour_count:
                    details.append(
                        "Contornos por rectángulo de respaldo: "
                        f"{result.fallback_contour_count}"
                    )
                QMessageBox.information(
                    config_dialog,
                    "Crear En-Juego",
                    "\n".join(details),
                )

            buttons_layout = QHBoxLayout()
            create_en_juego_btn = QPushButton("Crear En-Juego")
            fit_view_btn = QPushButton("Ajustar vista")
            rotate_left_btn = QPushButton("Rotar -90°")
            rotate_right_btn = QPushButton("Rotar +90°")
            save_layout_btn = QPushButton("Guardar disposición")
            close_layout_btn = QPushButton("Cerrar")
            fit_view_btn.clicked.connect(lambda: view.fitInView(scene.itemsBoundingRect().adjusted(-80, -80, 80, 80), Qt.KeepAspectRatio))
            rotate_left_btn.clicked.connect(lambda: rotate_selected_piece(-90.0))
            rotate_right_btn.clicked.connect(lambda: rotate_selected_piece(90.0))
            create_en_juego_btn.clicked.connect(create_en_juego_pgmx_from_dialog)
            save_layout_btn.clicked.connect(save_en_juego_layout)
            close_layout_btn.clicked.connect(config_dialog.reject)
            buttons_layout.addWidget(fit_view_btn)
            buttons_layout.addWidget(rotate_left_btn)
            buttons_layout.addWidget(rotate_right_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(create_en_juego_btn)
            buttons_layout.addWidget(save_layout_btn)
            buttons_layout.addWidget(close_layout_btn)
            main_layout.addLayout(buttons_layout)

            config_dialog.setLayout(main_layout)
            config_dialog.exec()

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.addWidget(pieces_table, 1)

        actions_column = QVBoxLayout()
        actions_column.setContentsMargins(0, 0, 0, 0)
        actions_column.setSpacing(8)

        add_piece_btn = QPushButton("Nueva\nPieza")
        add_piece_btn.setToolTip("Nueva Pieza")
        edit_piece_btn = QPushButton("Editar\nPieza")
        edit_piece_btn.setToolTip("Editar Pieza")
        delete_piece_btn = QPushButton("Eliminar\nPieza")
        delete_piece_btn.setToolTip("Eliminar Pieza")
        remove_source_btn = QPushButton("Quitar\nPrograma")
        remove_source_btn.setToolTip("Quitar programa")
        configure_en_juego_btn = QPushButton("Configurar\nEn Juego")
        configure_en_juego_btn.setToolTip("Configurar En Juego")

        for button in (
            add_piece_btn,
            edit_piece_btn,
            delete_piece_btn,
            configure_en_juego_btn,
            remove_source_btn,
        ):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

        actions_column.addWidget(add_piece_btn)
        actions_column.addWidget(edit_piece_btn)
        actions_column.addWidget(delete_piece_btn)
        actions_column.addWidget(remove_source_btn)
        actions_column.addWidget(configure_en_juego_btn)
        actions_column.addStretch(1)

        content_row.addLayout(actions_column)
        layout.addLayout(content_row, 1)

        add_piece_btn.clicked.connect(add_manual_piece)
        edit_piece_btn.clicked.connect(edit_selected_piece)
        delete_piece_btn.clicked.connect(remove_selected_piece)
        remove_source_btn.clicked.connect(remove_source_for_selected_piece)
        configure_en_juego_btn.clicked.connect(open_en_juego_configuration_dialog)

        def save_module_settings(show_feedback=True):
            persist_module_config()
            if show_feedback:
                QMessageBox.information(inspect_dialog, "Configuración", "Configuración del módulo guardada.")

        def ask_save_before_close() -> bool:
            if not has_unsaved_changes:
                return True

            answer = QMessageBox.question(
                inspect_dialog,
                "Cambios sin guardar",
                "Hay cambios sin guardar en la configuración del módulo. ¿Desea guardarlos antes de cerrar?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes,
            )

            if answer == QMessageBox.Yes:
                save_module_settings(show_feedback=False)
                return True
            if answer == QMessageBox.No:
                return True
            return False

        def request_close_dialog():
            if ask_save_before_close():
                inspect_dialog.accept()

        original_reject = inspect_dialog.reject

        def reject_with_confirmation():
            if ask_save_before_close():
                original_reject()

        inspect_dialog.reject = reject_with_confirmation

        footer_buttons = QHBoxLayout()
        save_btn = QPushButton("Guardar Configuración")
        save_btn.clicked.connect(save_module_settings)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(request_close_dialog)

        footer_buttons.addWidget(save_btn)
        footer_buttons.addWidget(close_btn)
        layout.addLayout(footer_buttons)

        inspect_dialog.setLayout(layout)
        inspect_dialog.exec()

    def show_cuts(self):
        if not self.project.modules:
            QMessageBox.warning(self, "Diagramas de Cortes", "No hay módulos cargados. Procese el proyecto primero.")
            return

        selected_project = self._project_for_selected_locales("Diagramas de Cortes")
        if selected_project is None:
            return

        settings = _read_app_settings()
        board_width = float(settings.get("cut_board_width") or 1830)
        board_height = float(settings.get("cut_board_height") or 2750)
        piece_gap = float(settings.get("cut_piece_gap") or 0)
        squaring_allowance = float(settings.get("cut_squaring_allowance") or 10)
        saw_kerf = float(settings.get("cut_saw_kerf") or 4)
        board_definitions = settings.get("available_boards") or []
        optimization_mode = _normalize_cut_optimization_option(settings.get("cut_optimization_mode"))
        pdf_output_path = Path(self.project.root_directory) / "diagramas_corte_a4.pdf"

        try:
            from core.nesting import generate_cut_diagrams

            result = generate_cut_diagrams(
                selected_project,
                pdf_output_path,
                board_width=board_width,
                board_height=board_height,
                piece_gap=piece_gap,
                squaring_allowance=squaring_allowance,
                saw_kerf=saw_kerf,
                board_definitions=board_definitions,
                optimization_mode=optimization_mode,
            )

            skipped_count = len(result.get("skipped_pieces", []))
            missing_board_groups = result.get("missing_board_groups", [])
            pdf_file = result.get("pdf_file")
            total_boards = sum(int(group.get("board_count") or 0) for group in result.get("group_summaries", []))
            detail_lines = [
                "PDF de cortes generado correctamente.",
                "",
                f"Tableros incluidos: {total_boards}",
            ]
            if pdf_file:
                detail_lines.append(f"Archivo PDF: {pdf_file}")
            if result.get("used_configured_boards"):
                detail_lines.append("Origen dimensional: lista de tableros configurados.")
            else:
                detail_lines.append(f"Tablero base por defecto: {int(board_width)} x {int(board_height)} mm")
            detail_lines.append("Medidas de piezas: programa PGMX asociado cuando existe.")
            detail_lines.append(
                f"Adicional para escuadrado: {_compact_number(squaring_allowance)} mm | Espesor de sierra: {_compact_number(saw_kerf)} mm"
            )
            detail_lines.append(f"Modo de optimización: {optimization_mode}")
            if skipped_count:
                detail_lines.append(f"Piezas sin ubicar: {skipped_count}")
            if missing_board_groups:
                preview = ", ".join(
                    f"{group['material']} {group['thickness']}mm"
                    for group in missing_board_groups[:3]
                )
                detail_lines.append(f"Grupos sin tablero configurado: {preview}")

            QMessageBox.information(self, "Diagramas de Cortes", "\n".join(detail_lines))
        except Exception as exc:
            QMessageBox.warning(self, "Diagramas de Cortes", f"Error al generar diagramas: {exc}")

    def generate_sheets(self):
        if not self.project.modules:
            QMessageBox.warning(self, "Generar Planillas", "No hay módulos cargados. Procese el proyecto primero.")
            return

        selected_project = self._project_for_selected_locales("Generar Planillas")
        if selected_project is None:
            return

        default_name = f"{self.project.name} - {self.project.client}.xlsx"
        default_output = str(Path(self.project.root_directory) / default_name)
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar planilla de producción",
            default_output,
            "Excel (*.xlsx)",
        )
        if not output_file:
            return

        # Loop para permitir reintentos
        while True:
            try:
                from core.summary import export_production_sheet

                generated_path = export_production_sheet(
                    selected_project,
                    Path(output_file),
                )
                QMessageBox.information(
                    self,
                    "Generar Planillas",
                    f"Planilla generada correctamente en:\n{generated_path}",
                )
                break  # Éxito, salir del loop
            except Exception as exc:
                # Mostrar error con opciones de reintentar
                error_msg = f"No se pudo generar la planilla:\n\n{exc}"
                
                # Crear un diálogo personalizado con más opciones
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Generar Planillas - Error")
                dlg.setText(error_msg)
                dlg.setIcon(QMessageBox.Critical)
                
                retry_btn = dlg.addButton("Reintentar", QMessageBox.ActionRole)
                change_location_btn = dlg.addButton("Guardar en otro lugar", QMessageBox.ActionRole)
                cancel_btn = dlg.addButton("Cancelar", QMessageBox.RejectRole)
                
                dlg.exec()
                
                if dlg.clickedButton() == cancel_btn:
                    break  # Usuario cancela, salir del loop
                elif dlg.clickedButton() == change_location_btn:
                    # Permitir elegir otro archivo
                    new_output, _ = QFileDialog.getSaveFileName(
                        self,
                        "Guardar planilla de producción",
                        default_output,
                        "Excel (*.xlsx)",
                    )
                    if new_output:
                        output_file = new_output
                    else:
                        break  # Usuario cancela el diálogo de archivo
                # Si presiona Retry, el loop continúa con el mismo archivo

    def generate_drawings_only(self):
        """Regenerar todas las imágenes sin afectar el resto de configuraciones."""
        if not self.project.modules:
            QMessageBox.warning(self, "Generar imágenes", "No hay módulos cargados. Procese el proyecto primero.")
            return

        selected_project = self._project_for_selected_locales("Generar imágenes")
        if selected_project is None:
            return

        try:
            from core.pgmx_processing import generate_project_piece_drawings

            generated_drawings, skipped_drawings, pieces_with_machining = generate_project_piece_drawings(
                selected_project,
            )

            detail_text = (
                f"Imágenes regeneradas correctamente:\n\n"
                f"Dibujos SVG generados: {generated_drawings}\n"
                f"Piezas con mecanizados detectados: {pieces_with_machining}\n"
                f"Piezas sin PGMX utilizable: {skipped_drawings}\n"
                f"Ubicación: Carpeta de cada módulo"
            )

            QMessageBox.information(self, "Generar imágenes", detail_text)
        except Exception as exc:
            QMessageBox.warning(self, "Generar imágenes", f"Error al generar imágenes: {exc}")


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
        dialog.exec()

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

        project_row = QHBoxLayout()
        project_row.addWidget(QLabel("Proyecto"))
        self.name_field = QLineEdit()
        project_row.addWidget(self.name_field)
        layout.addLayout(project_row)

        client_row = QHBoxLayout()
        client_row.addWidget(QLabel("Cliente"))
        self.client_field = QLineEdit()
        client_row.addWidget(self.client_field)
        layout.addLayout(client_row)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Carpeta"))
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
        dialog.exec()

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
            if dialog.exec() != QDialog.Accepted:
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
            detail_window = ProjectDetailWindow(project, return_window=self)
            detail_window.show()
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


class BoardEditDialog(QDialog):
    def __init__(self, board: dict | None = None, parent=None):
        super().__init__(parent)
        self.board_data: dict | None = None
        self.setWindowTitle("Editar tablero" if board else "Nuevo tablero")
        self.setModal(True)
        self.setMinimumWidth(420)

        board = dict(board or {})

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Complete los datos del tablero."))

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color"))
        self.color_field = QLineEdit(str(board.get("color") or ""))
        color_row.addWidget(self.color_field)
        layout.addLayout(color_row)

        length_row = QHBoxLayout()
        length_row.addWidget(QLabel("Longitud"))
        self.length_field = QLineEdit(str(board.get("length") or "2750"))
        length_row.addWidget(self.length_field)
        layout.addLayout(length_row)

        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Ancho"))
        self.width_field = QLineEdit(str(board.get("width") or "1830"))
        width_row.addWidget(self.width_field)
        layout.addLayout(width_row)

        thickness_row = QHBoxLayout()
        thickness_row.addWidget(QLabel("Espesor"))
        self.thickness_field = QLineEdit(str(board.get("thickness") or "18"))
        thickness_row.addWidget(self.thickness_field)
        layout.addLayout(thickness_row)

        margin_row = QHBoxLayout()
        margin_row.addWidget(QLabel("Margen"))
        self.margin_field = QLineEdit(str(board.get("margin") or "0"))
        margin_row.addWidget(self.margin_field)
        layout.addLayout(margin_row)

        grain_row = QHBoxLayout()
        grain_row.addWidget(QLabel("Veta"))
        self.grain_field = QComboBox()
        self.grain_field.addItems(BOARD_GRAIN_OPTIONS)
        current_grain = _normalize_board_grain(board.get("grain") or board.get("veta"))
        self.grain_field.setCurrentText(current_grain)
        grain_row.addWidget(self.grain_field)
        layout.addLayout(grain_row)

        buttons_row = QHBoxLayout()
        save_button = QPushButton("Guardar")
        cancel_button = QPushButton("Cancelar")
        save_button.clicked.connect(self.save_board)
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(cancel_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def save_board(self):
        normalized = _normalize_board_entry(
            {
                "color": self.color_field.text().strip(),
                "length": self.length_field.text().strip(),
                "width": self.width_field.text().strip(),
                "thickness": self.thickness_field.text().strip(),
                "margin": self.margin_field.text().strip(),
                "grain": self.grain_field.currentText(),
            }
        )
        if normalized is None:
            QMessageBox.warning(self, "Tableros", "Complete Color, Longitud, Ancho, Espesor y Margen con valores válidos. El margen debe dejar área útil dentro del tablero.")
            return

        self.board_data = normalized
        self.accept()


class BoardsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tableros")
        self.setModal(True)
        self.resize(760, 420)
        self.settings = _read_app_settings()
        self.boards = list(self.settings.get("available_boards", []))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tableros disponibles para diagramas de corte."))

        self.boards_table = QTableWidget()
        self.boards_table.setColumnCount(6)
        self.boards_table.setHorizontalHeaderLabels([
            "Color",
            "Longitud",
            "Ancho",
            "Espesor",
            "Margen",
            "Veta",
        ])
        self.boards_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.boards_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.boards_table.setAlternatingRowColors(True)
        self.boards_table.horizontalHeader().setStretchLastSection(True)
        self.boards_table.setColumnWidth(0, 180)
        self.boards_table.setColumnWidth(1, 100)
        self.boards_table.setColumnWidth(2, 100)
        self.boards_table.setColumnWidth(3, 100)
        self.boards_table.setColumnWidth(4, 90)
        self.boards_table.itemDoubleClicked.connect(lambda _item: self.edit_board())
        layout.addWidget(self.boards_table)

        buttons_row = QHBoxLayout()
        new_button = QPushButton("Nuevo")
        edit_button = QPushButton("Editar")
        delete_button = QPushButton("Eliminar")
        close_button = QPushButton("Cerrar")
        new_button.clicked.connect(self.add_board)
        edit_button.clicked.connect(self.edit_board)
        delete_button.clicked.connect(self.delete_board)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(new_button)
        buttons_row.addWidget(edit_button)
        buttons_row.addWidget(delete_button)
        buttons_row.addStretch(1)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)
        self.refresh_boards_table()

    def _persist_boards(self):
        settings = _read_app_settings()
        settings["available_boards"] = self.boards
        _write_app_settings(settings)
        self.settings = settings

    def _selected_board_index(self) -> int:
        return self.boards_table.currentRow()

    def refresh_boards_table(self):
        self.boards_table.setRowCount(len(self.boards))
        for row_idx, board in enumerate(self.boards):
            self.boards_table.setItem(row_idx, 0, QTableWidgetItem(str(board.get("color") or "")))
            self.boards_table.setItem(row_idx, 1, QTableWidgetItem(str(board.get("length") or "")))
            self.boards_table.setItem(row_idx, 2, QTableWidgetItem(str(board.get("width") or "")))
            self.boards_table.setItem(row_idx, 3, QTableWidgetItem(str(board.get("thickness") or "")))
            self.boards_table.setItem(row_idx, 4, QTableWidgetItem(str(board.get("margin") or 0)))
            self.boards_table.setItem(row_idx, 5, QTableWidgetItem(str(board.get("grain") or "")))

    def add_board(self):
        dialog = BoardEditDialog(parent=self)
        if dialog.exec() != QDialog.Accepted or dialog.board_data is None:
            return

        self.boards.append(dialog.board_data)
        self._persist_boards()
        self.refresh_boards_table()
        self.boards_table.selectRow(len(self.boards) - 1)

    def edit_board(self):
        row_idx = self._selected_board_index()
        if row_idx < 0 or row_idx >= len(self.boards):
            QMessageBox.warning(self, "Tableros", "Seleccione un tablero para editar.")
            return

        dialog = BoardEditDialog(board=self.boards[row_idx], parent=self)
        if dialog.exec() != QDialog.Accepted or dialog.board_data is None:
            return

        self.boards[row_idx] = dialog.board_data
        self._persist_boards()
        self.refresh_boards_table()
        self.boards_table.selectRow(row_idx)

    def delete_board(self):
        row_idx = self._selected_board_index()
        if row_idx < 0 or row_idx >= len(self.boards):
            QMessageBox.warning(self, "Tableros", "Seleccione un tablero para eliminar.")
            return

        board = self.boards[row_idx]
        answer = QMessageBox.question(
            self,
            "Tableros",
            f"¿Eliminar el tablero '{board.get('color')}' de {board.get('thickness')} mm?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        del self.boards[row_idx]
        self._persist_boards()
        self.refresh_boards_table()


class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.settings = _read_app_settings()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración general de la aplicación."))

        minimum_dimension_row = QHBoxLayout()
        minimum_dimension_label = QLabel("Mínima dimensión mecanizable")
        self.minimum_dimension_field = QLineEdit(
            str(self.settings.get("minimum_machinable_dimension", 150))
        )
        self.minimum_dimension_field.setPlaceholderText("150")
        minimum_dimension_row.addWidget(minimum_dimension_label)
        minimum_dimension_row.addWidget(self.minimum_dimension_field)
        layout.addLayout(minimum_dimension_row)

        optimization_row = QHBoxLayout()
        optimization_row.addWidget(QLabel("Optimización de cortes"))
        self.cut_optimization_field = QComboBox()
        self.cut_optimization_field.addItems(CUT_OPTIMIZATION_OPTIONS)
        self.cut_optimization_field.setCurrentText(
            _normalize_cut_optimization_option(self.settings.get("cut_optimization_mode"))
        )
        optimization_row.addWidget(self.cut_optimization_field)
        layout.addLayout(optimization_row)

        squaring_row = QHBoxLayout()
        squaring_row.addWidget(QLabel("Adicional para escuadrado"))
        self.cut_squaring_field = QLineEdit(
            str(_compact_number(self.settings.get("cut_squaring_allowance", 10)))
        )
        self.cut_squaring_field.setPlaceholderText("10")
        squaring_row.addWidget(self.cut_squaring_field)
        layout.addLayout(squaring_row)

        saw_kerf_row = QHBoxLayout()
        saw_kerf_row.addWidget(QLabel("Espesor de Sierra"))
        self.cut_saw_kerf_field = QLineEdit(
            str(_compact_number(self.settings.get("cut_saw_kerf", 4)))
        )
        self.cut_saw_kerf_field.setPlaceholderText("4")
        saw_kerf_row.addWidget(self.cut_saw_kerf_field)
        layout.addLayout(saw_kerf_row)

        boards_row = QHBoxLayout()
        boards_row.addWidget(QLabel("Tableros disponibles"))
        boards_button = QPushButton("Tableros")
        boards_button.clicked.connect(self.open_boards_dialog)
        boards_row.addWidget(boards_button)
        layout.addLayout(boards_row)

        buttons_row = QHBoxLayout()
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.clicked.connect(self.save_settings)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def open_boards_dialog(self):
        dialog = BoardsDialog(self)
        dialog.exec()
        self.settings = _read_app_settings()

    def save_settings(self):
        minimum_dimension_raw = self.minimum_dimension_field.text().strip() or "150"
        squaring_raw = self.cut_squaring_field.text().strip() or "10"
        saw_kerf_raw = self.cut_saw_kerf_field.text().strip() or "4"

        def parse_non_negative_measure(raw_value: str, field_name: str) -> float | None:
            try:
                value = float(raw_value.replace(",", "."))
            except ValueError:
                QMessageBox.warning(self, "Opciones", f"{field_name} debe ser un número.")
                return None
            if value < 0:
                QMessageBox.warning(self, "Opciones", f"{field_name} debe ser mayor o igual a cero.")
                return None
            return value

        try:
            minimum_dimension = int(minimum_dimension_raw)
        except ValueError:
            QMessageBox.warning(self, "Opciones", "La mínima dimensión mecanizable debe ser un número entero.")
            return

        if minimum_dimension <= 0:
            QMessageBox.warning(self, "Opciones", "La mínima dimensión mecanizable debe ser mayor que cero.")
            return

        squaring_allowance = parse_non_negative_measure(squaring_raw, "El adicional para escuadrado")
        if squaring_allowance is None:
            return

        saw_kerf = parse_non_negative_measure(saw_kerf_raw, "El espesor de sierra")
        if saw_kerf is None:
            return

        current_settings = _read_app_settings()
        current_settings["minimum_machinable_dimension"] = minimum_dimension
        current_settings["cut_squaring_allowance"] = _compact_number(squaring_allowance)
        current_settings["cut_saw_kerf"] = _compact_number(saw_kerf)
        current_settings["cut_optimization_mode"] = _normalize_cut_optimization_option(
            self.cut_optimization_field.currentText()
        )
        _write_app_settings(current_settings)
        self.settings = current_settings
        QMessageBox.information(self, "Opciones", "Configuración guardada.")


def run_app():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
