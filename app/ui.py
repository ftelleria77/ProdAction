"""Interfaz gráfica principal para gestión de proyectos CNC.

Contiene ventana principal con creación, apertura, limpieza,
archivado y selección de carpeta raíz de proyecto.
Incluye ventana de detalle de proyecto con edición.
"""

import csv
import datetime
import json
import os
import shutil
import sys
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
    QGridLayout,
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
    QGroupBox,
    QSizePolicy,
    QProgressDialog,
)
from PySide6.QtSvgWidgets import QSvgWidget

from core.model import (
    LocaleData,
    Project,
    ModuleData,
    Piece,
    PIECE_GRAIN_CODE_NONE,
    build_piece_observations_display,
    normalize_piece_grain_direction,
    normalize_piece_observations,
    piece_grain_direction_label,
    set_piece_en_juego_observation,
)

def _application_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        internal_dir = executable_dir / "_internal"
        if (internal_dir / "tools" / "tool_catalog.csv").exists():
            return internal_dir
        return executable_dir
    return Path(__file__).resolve().parents[1]


BASE_DIR = _application_base_dir()
PROJECT_REGISTRY = BASE_DIR / "projects_list.json"
APP_SETTINGS_FILE = BASE_DIR / "app_settings.json"
ARCHIVE_DIR = BASE_DIR / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)

MAIN_ACTION_BUTTON_WIDTH = 96
MAIN_ACTION_BUTTON_HEIGHT = 40
_TOOL_CATALOG_ROWS_CACHE: list[dict] | None = None
_EN_JUEGO_CUTTING_TOOLS_CACHE: list[dict] | None = None

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


DEFAULT_PATH_FIELDS = [
    ("projects", "Proyectos"),
    ("excel_sheets", "Planillas Excel"),
    ("cut_diagrams", "Diagramas de corte"),
    ("cnc_files", "Archivos CNC"),
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
        "manual_piece_templates": [],
        "default_paths": {},
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


def _normalize_default_paths(raw_paths) -> dict:
    if not isinstance(raw_paths, dict):
        raw_paths = {}
    return {
        key: str(raw_paths.get(key) or "").strip()
        for key, _label in DEFAULT_PATH_FIELDS
    }


def _board_matches_piece_thickness(board: dict, piece_thickness: float | None) -> bool:
    if piece_thickness is None:
        return True
    try:
        board_thickness = float(board.get("thickness"))
    except (TypeError, ValueError):
        return False
    return abs(board_thickness - piece_thickness) <= 0.001


def _board_color_has_no_grain(color: str | None, piece_thickness: float | None = None) -> bool:
    color_key = str(color or "").strip().lower()
    if not color_key:
        return False

    matching_boards = [
        board
        for board in _read_app_settings().get("available_boards", [])
        if str(board.get("color") or "").strip().lower() == color_key
        and _board_matches_piece_thickness(board, piece_thickness)
    ]
    return bool(matching_boards) and all(
        _normalize_board_grain(board.get("grain") or board.get("veta")) == BOARD_GRAIN_OPTIONS[0]
        for board in matching_boards
    )


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
    settings["manual_piece_templates"] = _normalize_manual_piece_templates(settings.get("manual_piece_templates"))
    settings["default_paths"] = _normalize_default_paths(settings.get("default_paths"))
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
    merged_settings["manual_piece_templates"] = _normalize_manual_piece_templates(
        merged_settings.get("manual_piece_templates")
    )
    merged_settings["default_paths"] = _normalize_default_paths(merged_settings.get("default_paths"))
    merged_settings["cut_optimization_mode"] = _normalize_cut_optimization_option(merged_settings.get("cut_optimization_mode"))
    merged_settings["cut_piece_gap"] = _compact_number(_coerce_setting_number(merged_settings.get("cut_piece_gap"), 0.0, minimum=0.0))
    merged_settings["cut_squaring_allowance"] = _compact_number(_coerce_setting_number(merged_settings.get("cut_squaring_allowance"), 10.0, minimum=0.0))
    merged_settings["cut_saw_kerf"] = _compact_number(_coerce_setting_number(merged_settings.get("cut_saw_kerf"), 4.0, minimum=0.0))
    APP_SETTINGS_FILE.write_text(
        json.dumps(merged_settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _normalize_manual_piece_template_dimension(value):
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return _compact_number(float(raw))
    except ValueError:
        return None


def _normalize_manual_piece_template_entry(template_data: dict) -> dict | None:
    if not isinstance(template_data, dict):
        return None

    template_id = str(template_data.get("id") or "").strip()
    template_name = str(template_data.get("name") or template_id).strip()
    if not template_id and not template_name:
        return None
    if not template_id:
        template_id = template_name

    normalized_entry = {
        "id": template_id,
        "name": template_name or template_id,
        "quantity": _parse_piece_quantity_value(template_data.get("quantity"), default=1),
        "height": _normalize_manual_piece_template_dimension(template_data.get("height")),
        "width": _normalize_manual_piece_template_dimension(template_data.get("width")),
        "thickness": _normalize_manual_piece_template_dimension(template_data.get("thickness")),
        "color": str(template_data.get("color") or "").strip() or None,
        "grain_direction": normalize_piece_grain_direction(template_data.get("grain_direction")),
        "source": str(template_data.get("source") or "").strip(),
        "f6_source": str(template_data.get("f6_source") or "").strip() or None,
        "piece_type": str(template_data.get("piece_type") or "").strip() or None,
    }
    saved_at = str(template_data.get("saved_at") or "").strip()
    if saved_at:
        normalized_entry["saved_at"] = saved_at
    return normalized_entry


def _normalize_manual_piece_templates(raw_templates) -> list[dict]:
    templates: list[dict] = []
    for template_data in raw_templates or []:
        normalized_entry = _normalize_manual_piece_template_entry(template_data)
        if normalized_entry is not None:
            templates.append(normalized_entry)
    return templates


def _manual_piece_template_signature(template_entry: dict) -> tuple:
    return (
        str(template_entry.get("id") or "").strip().lower(),
        str(template_entry.get("name") or "").strip().lower(),
        int(_parse_piece_quantity_value(template_entry.get("quantity"), default=1)),
        template_entry.get("height"),
        template_entry.get("width"),
        template_entry.get("thickness"),
        str(template_entry.get("color") or "").strip().lower(),
        normalize_piece_grain_direction(template_entry.get("grain_direction")),
        str(template_entry.get("source") or "").strip().lower(),
        str(template_entry.get("piece_type") or "").strip().lower(),
    )


def _build_manual_piece_template_entry(piece_row: dict) -> dict:
    normalized_entry = _normalize_manual_piece_template_entry(piece_row) or {
        "id": "pieza",
        "name": "pieza",
        "quantity": 1,
        "height": None,
        "width": None,
        "thickness": None,
        "color": None,
        "grain_direction": normalize_piece_grain_direction(None),
        "source": "",
        "f6_source": None,
        "piece_type": None,
    }
    normalized_entry["saved_at"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    return normalized_entry


def _save_manual_piece_template(piece_row: dict) -> dict:
    settings = _read_app_settings()
    template_entry = _build_manual_piece_template_entry(piece_row)
    template_signature = _manual_piece_template_signature(template_entry)
    existing_templates = _normalize_manual_piece_templates(settings.get("manual_piece_templates"))
    filtered_templates = [
        entry
        for entry in existing_templates
        if _manual_piece_template_signature(entry) != template_signature
    ]
    settings["manual_piece_templates"] = [template_entry] + filtered_templates
    _write_app_settings(settings)
    return template_entry


def _persist_manual_piece_templates(template_entries) -> list[dict]:
    normalized_templates = _normalize_manual_piece_templates(template_entries)
    settings = _read_app_settings()
    settings["manual_piece_templates"] = normalized_templates
    _write_app_settings(settings)
    return normalized_templates


def _normalize_en_juego_cut_mode(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"nesting", "corte nesting", "cut nesting"}:
        return "nesting"
    if raw in {"manual", "corte manual", "cut manual"}:
        return "manual"
    return "manual"


def _normalize_en_juego_operation_order(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {
        "squaring_then_division",
        "squaring_then_cutting",
        "escuadrar_dividir",
        "escuadrar -> dividir",
        "escuadrar-dividir",
    }:
        return "squaring_then_division"
    return "division_then_squaring"


def _load_tool_catalog_rows() -> list[dict]:
    global _TOOL_CATALOG_ROWS_CACHE

    if _TOOL_CATALOG_ROWS_CACHE is not None:
        return [dict(tool_data) for tool_data in _TOOL_CATALOG_ROWS_CACHE]

    catalog_path = BASE_DIR / "tools" / "tool_catalog.csv"
    if not catalog_path.exists():
        return []

    rows: list[dict] = []
    try:
        with catalog_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                tool_id = str(row.get("tool_id") or "").strip()
                if not tool_id:
                    continue
                rows.append(
                    {
                        "tool_id": tool_id,
                        "name": str(row.get("name") or "").strip(),
                        "description": str(row.get("description") or "").strip(),
                        "type": str(row.get("type") or "").strip(),
                        "holder_key": str(row.get("holder_key") or "").strip(),
                        "diameter": _compact_number(
                            _coerce_setting_number(row.get("diameter"), 0.0, minimum=0.0)
                        ),
                        "sinking_length": _compact_number(
                            _coerce_setting_number(row.get("sinking_length"), 0.0, minimum=0.0)
                        ),
                        "tool_offset_length": _compact_number(
                            _coerce_setting_number(row.get("tool_offset_length"), 0.0, minimum=0.0)
                        ),
                    }
                )
    except Exception:
        return []

    _TOOL_CATALOG_ROWS_CACHE = [dict(tool_data) for tool_data in rows]
    return [dict(tool_data) for tool_data in rows]


def _normalize_tool_usage_group(tool_type) -> str:
    normalized = str(tool_type or "").strip().lower()
    if normalized.startswith("broca"):
        return "drilling"
    if normalized.startswith("fresa") or normalized.startswith("freza"):
        return "milling"
    if normalized.startswith("sierra"):
        return "saw"
    return "other"


def _tool_usage_family_label(tool_type) -> str:
    usage_group = _normalize_tool_usage_group(tool_type)
    if usage_group == "drilling":
        return "Broca"
    if usage_group == "milling":
        return "Fresa"
    if usage_group == "saw":
        return "Sierra"
    return "Otro"


def _is_helical_tool_type(tool_type) -> bool:
    normalized = str(tool_type or "").strip().lower()
    return "compres" in normalized or "helic" in normalized


def _is_zero_degree_milling_tool(tool_type) -> bool:
    normalized = str(tool_type or "").strip().lower()
    return normalized.startswith("fresa 0") or normalized.startswith("freza 0")


def _is_forty_five_degree_milling_tool(tool_type) -> bool:
    normalized = str(tool_type or "").strip().lower()
    return normalized.startswith("fresa 45") or normalized.startswith("freza 45")


def _is_horizontal_saw_tool(tool_type) -> bool:
    normalized = str(tool_type or "").strip().lower()
    return normalized == "sierra horizontal"


def _coerce_setting_bool(value, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "si", "sí", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "off"}:
        return False
    return bool(default)


def _tool_usage_label(tool_type) -> str:
    normalized_type = str(tool_type or "").strip().lower()
    if normalized_type == "sierra vertical x":
        return "Ranurado recto horizontal no pasante"
    if _is_horizontal_saw_tool(tool_type):
        return "No apta para dividir En-Juego"
    if _is_forty_five_degree_milling_tool(tool_type):
        return "Divide En-Juego segun profundidad; 2 mm por cada 1 mm extra"
    if _is_zero_degree_milling_tool(tool_type):
        return "No apta para dividir En-Juego"
    if _is_helical_tool_type(tool_type):
        return "Preferente para dividir En-Juego; su diametro define la separacion"
    usage_group = _normalize_tool_usage_group(tool_type)
    if usage_group == "drilling":
        return "Taladrado"
    if usage_group == "milling":
        return "Fresado, escuadrado y corte Nesting"
    if usage_group == "saw":
        return "Corte con sierra"
    return "Sin regla definida"


def _tool_allows_en_juego_cutting(tool_row: dict) -> bool:
    tool_type = tool_row.get("type")
    if _is_horizontal_saw_tool(tool_type):
        return False
    if _is_zero_degree_milling_tool(tool_type):
        return False
    return _normalize_tool_usage_group(tool_type) == "milling"


def _en_juego_cutting_tool_priority(tool_row: dict) -> tuple[int, float, str]:
    diameter = _coerce_setting_number(tool_row.get("diameter"), 0.0, minimum=0.0)
    tool_code = str(tool_row.get("name") or tool_row.get("tool_code") or "").strip()
    return (
        0 if _is_helical_tool_type(tool_row.get("type")) else 1,
        -float(diameter),
        tool_code,
    )


def _load_en_juego_cutting_tools() -> list[dict]:
    global _EN_JUEGO_CUTTING_TOOLS_CACHE

    if _EN_JUEGO_CUTTING_TOOLS_CACHE is not None:
        return [dict(tool_data) for tool_data in _EN_JUEGO_CUTTING_TOOLS_CACHE]

    tools: list[dict] = []
    for row in _load_tool_catalog_rows():
        if not _tool_allows_en_juego_cutting(row):
            continue
        tool_id = str(row.get("tool_id") or "").strip()
        tool_code = str(row.get("name") or "").strip()
        tool_name = str(row.get("description") or "").strip()
        tool_type = str(row.get("type") or "").strip()
        diameter = _coerce_setting_number(row.get("diameter"), 0.0, minimum=0.0)
        if not tool_id or diameter <= 0:
            continue
        label_parts = [part for part in (tool_code, tool_name) if part]
        label = " - ".join(label_parts) if label_parts else tool_id
        tools.append(
            {
                "tool_id": tool_id,
                "tool_code": tool_code,
                "tool_name": tool_name,
                "tool_type": tool_type,
                "diameter": _compact_number(diameter),
                "label": f"{label} (Ø{_compact_number(diameter)} mm)",
            }
        )

    tools.sort(key=_en_juego_cutting_tool_priority)
    _EN_JUEGO_CUTTING_TOOLS_CACHE = [dict(tool_data) for tool_data in tools]
    return [dict(tool_data) for tool_data in tools]


def _default_en_juego_cutting_tool() -> dict:
    tools = _load_en_juego_cutting_tools()
    for tool in tools:
        if _is_helical_tool_type(tool.get("tool_type")):
            return dict(tool)
    for tool in tools:
        if str(tool.get("tool_id") or "").strip() == "1902":
            return dict(tool)
    if tools:
        return dict(tools[0])
    return {
        "tool_id": "",
        "tool_code": "",
        "tool_name": "",
        "tool_type": "",
        "diameter": 0,
        "label": "",
    }


def _resolve_en_juego_cutting_tool(tool_id) -> dict:
    normalized_id = str(tool_id or "").strip()
    for tool in _load_en_juego_cutting_tools():
        if str(tool.get("tool_id") or "").strip() == normalized_id:
            return dict(tool)
    return _default_en_juego_cutting_tool()


def _resolve_en_juego_nesting_spacing_mm(
    settings: dict,
    *,
    material_thickness_mm: float = 0.0,
) -> float:
    tool_data = _resolve_en_juego_cutting_tool(settings.get("cutting_tool_id"))
    tool_type = tool_data.get("tool_type")
    if _is_forty_five_degree_milling_tool(tool_type):
        depth_value = _coerce_setting_number(
            settings.get("cutting_depth_value"),
            1.0,
            minimum=0.0,
        )
        if _coerce_setting_bool(settings.get("cutting_is_through"), True):
            extra_depth = depth_value
        else:
            extra_depth = max(0.0, depth_value - max(0.0, float(material_thickness_mm)))
        return max(0.0, extra_depth * 2.0)

    return max(
        0.0,
        _coerce_setting_number(
            settings.get("cutting_tool_diameter"),
            _coerce_setting_number(tool_data.get("diameter"), 0.0, minimum=0.0),
            minimum=0.0,
        ),
    )


def _default_en_juego_settings() -> dict:
    default_tool = _default_en_juego_cutting_tool()
    return {
        "cut_mode": "manual",
        "origin_x": 5,
        "origin_y": 5,
        "origin_z": 9,
        "division_squaring_order": "division_then_squaring",
        "cutting_is_through": True,
        "cutting_depth_value": 1.0,
        "cutting_multipass_enabled": False,
        "cutting_path_mode": "Unidirectional",
        "cutting_pocket_depth": 0.0,
        "cutting_last_pocket": 0.0,
        "approach_enabled": False,
        "approach_type": "Arc",
        "approach_radius_multiplier": 2.0,
        "approach_mode": "Quote",
        "retract_enabled": False,
        "retract_type": "Arc",
        "retract_radius_multiplier": 2.0,
        "retract_mode": "Quote",
        "squaring_is_through": True,
        "squaring_depth_value": 1.0,
        "squaring_approach_enabled": False,
        "squaring_approach_type": "Arc",
        "squaring_approach_radius_multiplier": 2.0,
        "squaring_approach_mode": "Quote",
        "squaring_retract_enabled": False,
        "squaring_retract_type": "Arc",
        "squaring_retract_radius_multiplier": 2.0,
        "squaring_retract_mode": "Quote",
        "squaring_direction": "CW",
        "squaring_unidirectional_multipass": False,
        "squaring_pocket_depth": 0.0,
        "squaring_last_pocket": 0.0,
        "squaring_tool_id": str(default_tool.get("tool_id") or "").strip(),
        "squaring_tool_code": str(default_tool.get("tool_code") or "").strip(),
        "squaring_tool_name": str(default_tool.get("tool_name") or "").strip(),
        "squaring_tool_diameter": _compact_number(
            _coerce_setting_number(default_tool.get("diameter"), 0.0, minimum=0.0)
        ),
        "cutting_tool_id": str(default_tool.get("tool_id") or "").strip(),
        "cutting_tool_code": str(default_tool.get("tool_code") or "").strip(),
        "cutting_tool_name": str(default_tool.get("tool_name") or "").strip(),
        "cutting_tool_diameter": _compact_number(
            _coerce_setting_number(default_tool.get("diameter"), 0.0, minimum=0.0)
        ),
    }


def _normalize_en_juego_settings(value) -> dict:
    defaults = _default_en_juego_settings()
    if not isinstance(value, dict):
        return defaults

    resolved_tool = _resolve_en_juego_cutting_tool(value.get("cutting_tool_id") or defaults.get("cutting_tool_id"))
    fallback_diameter = _coerce_setting_number(
        resolved_tool.get("diameter"),
        float(defaults["cutting_tool_diameter"]),
        minimum=0.0,
    )
    squaring_tool = _resolve_en_juego_cutting_tool(
        value.get("squaring_tool_id") or defaults.get("squaring_tool_id")
    )
    squaring_fallback_diameter = _coerce_setting_number(
        squaring_tool.get("diameter"),
        float(defaults["squaring_tool_diameter"]),
        minimum=0.0,
    )

    return {
        "cut_mode": _normalize_en_juego_cut_mode(value.get("cut_mode")),
        "origin_x": _compact_number(
            _coerce_setting_number(value.get("origin_x"), float(defaults["origin_x"]))
        ),
        "origin_y": _compact_number(
            _coerce_setting_number(value.get("origin_y"), float(defaults["origin_y"]))
        ),
        "origin_z": _compact_number(
            _coerce_setting_number(value.get("origin_z"), float(defaults["origin_z"]))
        ),
        "division_squaring_order": _normalize_en_juego_operation_order(
            value.get("division_squaring_order")
            or value.get("operation_order")
            or defaults["division_squaring_order"]
        ),
        "cutting_is_through": _coerce_setting_bool(
            value.get("cutting_is_through"),
            bool(defaults["cutting_is_through"]),
        ),
        "cutting_depth_value": _compact_number(
            _coerce_setting_number(
                value.get("cutting_depth_value"),
                float(defaults["cutting_depth_value"]),
                minimum=0.0,
            )
        ),
        "cutting_multipass_enabled": _coerce_setting_bool(
            value.get("cutting_multipass_enabled"),
            bool(defaults["cutting_multipass_enabled"]),
        ),
        "cutting_path_mode": "Bidirectional"
        if str(value.get("cutting_path_mode") or defaults["cutting_path_mode"]).strip().lower() in {
            "bidirectional",
            "bidireccional",
        }
        else "Unidirectional",
        "cutting_pocket_depth": _compact_number(
            _coerce_setting_number(
                value.get("cutting_pocket_depth"),
                float(defaults["cutting_pocket_depth"]),
                minimum=0.0,
            )
        ),
        "cutting_last_pocket": _compact_number(
            _coerce_setting_number(
                value.get("cutting_last_pocket"),
                float(defaults["cutting_last_pocket"]),
                minimum=0.0,
            )
        ),
        "approach_enabled": _coerce_setting_bool(
            value.get("approach_enabled"),
            bool(defaults["approach_enabled"]),
        ),
        "approach_type": "Arc"
        if str(value.get("approach_type") or defaults["approach_type"]).strip().lower() == "arc"
        else "Line",
        "approach_radius_multiplier": _compact_number(
            _coerce_setting_number(
                value.get("approach_radius_multiplier"),
                float(defaults["approach_radius_multiplier"]),
                minimum=0.0,
            )
        ),
        "approach_mode": "Quote"
        if str(value.get("approach_mode") or defaults["approach_mode"]).strip().lower() == "quote"
        else "Down",
        "retract_enabled": _coerce_setting_bool(
            value.get("retract_enabled"),
            bool(defaults["retract_enabled"]),
        ),
        "retract_type": "Arc"
        if str(value.get("retract_type") or defaults["retract_type"]).strip().lower() == "arc"
        else "Line",
        "retract_radius_multiplier": _compact_number(
            _coerce_setting_number(
                value.get("retract_radius_multiplier"),
                float(defaults["retract_radius_multiplier"]),
                minimum=0.0,
            )
        ),
        "retract_mode": "Quote"
        if str(value.get("retract_mode") or defaults["retract_mode"]).strip().lower() == "quote"
        else "Up",
        "squaring_is_through": _coerce_setting_bool(
            value.get("squaring_is_through"),
            bool(defaults["squaring_is_through"]),
        ),
        "squaring_depth_value": _compact_number(
            _coerce_setting_number(
                value.get("squaring_depth_value"),
                float(defaults["squaring_depth_value"]),
                minimum=0.0,
            )
        ),
        "squaring_approach_enabled": _coerce_setting_bool(
            value.get("squaring_approach_enabled"),
            bool(defaults["squaring_approach_enabled"]),
        ),
        "squaring_approach_type": "Arc"
        if str(value.get("squaring_approach_type") or defaults["squaring_approach_type"]).strip().lower() == "arc"
        else "Line",
        "squaring_approach_radius_multiplier": _compact_number(
            _coerce_setting_number(
                value.get("squaring_approach_radius_multiplier"),
                float(defaults["squaring_approach_radius_multiplier"]),
                minimum=0.0,
            )
        ),
        "squaring_approach_mode": "Quote"
        if str(value.get("squaring_approach_mode") or defaults["squaring_approach_mode"]).strip().lower() == "quote"
        else "Down",
        "squaring_retract_enabled": _coerce_setting_bool(
            value.get("squaring_retract_enabled"),
            bool(defaults["squaring_retract_enabled"]),
        ),
        "squaring_retract_type": "Arc"
        if str(value.get("squaring_retract_type") or defaults["squaring_retract_type"]).strip().lower() == "arc"
        else "Line",
        "squaring_retract_radius_multiplier": _compact_number(
            _coerce_setting_number(
                value.get("squaring_retract_radius_multiplier"),
                float(defaults["squaring_retract_radius_multiplier"]),
                minimum=0.0,
            )
        ),
        "squaring_retract_mode": "Quote"
        if str(value.get("squaring_retract_mode") or defaults["squaring_retract_mode"]).strip().lower() == "quote"
        else "Up",
        "squaring_direction": "CCW"
        if str(value.get("squaring_direction") or defaults["squaring_direction"]).strip().lower() in {
            "ccw",
            "antihorario",
            "anti horario",
            "anti-horario",
        }
        else "CW",
        "squaring_unidirectional_multipass": _coerce_setting_bool(
            value.get("squaring_unidirectional_multipass"),
            bool(defaults["squaring_unidirectional_multipass"]),
        ),
        "squaring_pocket_depth": _compact_number(
            _coerce_setting_number(
                value.get("squaring_pocket_depth"),
                float(defaults["squaring_pocket_depth"]),
                minimum=0.0,
            )
        ),
        "squaring_last_pocket": _compact_number(
            _coerce_setting_number(
                value.get("squaring_last_pocket"),
                float(defaults["squaring_last_pocket"]),
                minimum=0.0,
            )
        ),
        "squaring_tool_id": str(
            value.get("squaring_tool_id")
            or squaring_tool.get("tool_id")
            or defaults.get("squaring_tool_id")
            or ""
        ).strip(),
        "squaring_tool_code": str(
            value.get("squaring_tool_code")
            or squaring_tool.get("tool_code")
            or defaults.get("squaring_tool_code")
            or ""
        ).strip(),
        "squaring_tool_name": str(
            value.get("squaring_tool_name")
            or squaring_tool.get("tool_name")
            or defaults.get("squaring_tool_name")
            or ""
        ).strip(),
        "squaring_tool_diameter": _compact_number(
            _coerce_setting_number(
                value.get("squaring_tool_diameter"),
                squaring_fallback_diameter,
                minimum=0.0,
            )
        ),
        "cutting_tool_id": str(
            value.get("cutting_tool_id")
            or resolved_tool.get("tool_id")
            or defaults.get("cutting_tool_id")
            or ""
        ).strip(),
        "cutting_tool_code": str(
            value.get("cutting_tool_code")
            or resolved_tool.get("tool_code")
            or defaults.get("cutting_tool_code")
            or ""
        ).strip(),
        "cutting_tool_name": str(
            value.get("cutting_tool_name")
            or resolved_tool.get("tool_name")
            or defaults.get("cutting_tool_name")
            or ""
        ).strip(),
        "cutting_tool_diameter": _compact_number(
            _coerce_setting_number(
                value.get("cutting_tool_diameter"),
                fallback_diameter,
                minimum=0.0,
            )
        ),
    }


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


def _center_window_on_screen(widget: QWidget) -> None:
    available = _window_available_geometry(widget)
    if available is None:
        return

    frame_rect = widget.frameGeometry()
    target_width = frame_rect.width() if frame_rect.width() > 0 else widget.width()
    target_height = frame_rect.height() if frame_rect.height() > 0 else widget.height()
    if target_width <= 0 or target_height <= 0:
        return

    target_x = available.x() + max(0, int((available.width() - target_width) / 2))
    target_y = available.y() + max(0, int((available.height() - target_height) / 2))
    widget.move(target_x, target_y)


def _center_window_on_origin(widget: QWidget, origin: QWidget | None = None) -> None:
    origin_widget = origin
    if origin_widget is None:
        try:
            origin_widget = widget.parentWidget()
        except Exception:
            origin_widget = None

    if origin_widget is not None:
        try:
            origin_widget = origin_widget.window()
        except Exception:
            pass

    origin_rect = None
    if origin_widget is not None:
        try:
            candidate_rect = origin_widget.frameGeometry()
        except Exception:
            candidate_rect = None
        if candidate_rect is not None and candidate_rect.width() > 0 and candidate_rect.height() > 0:
            origin_rect = candidate_rect

    if origin_rect is None:
        _center_window_on_screen(widget)
        return

    available = _window_available_geometry(origin_widget) or _window_available_geometry(widget)
    frame_rect = widget.frameGeometry()
    target_width = frame_rect.width() if frame_rect.width() > 0 else max(widget.width(), widget.sizeHint().width())
    target_height = frame_rect.height() if frame_rect.height() > 0 else max(widget.height(), widget.sizeHint().height())
    if target_width <= 0 or target_height <= 0:
        return

    target_x = origin_rect.x() + int((origin_rect.width() - target_width) / 2)
    target_y = origin_rect.y() + int((origin_rect.height() - target_height) / 2)

    if available is not None:
        min_x = available.x()
        min_y = available.y()
        max_x = available.x() + max(0, available.width() - target_width)
        max_y = available.y() + max(0, available.height() - target_height)
        target_x = min(max(target_x, min_x), max_x)
        target_y = min(max(target_y, min_y), max_y)

    widget.move(target_x, target_y)


def _show_centered(widget: QWidget, origin: QWidget | None = None) -> None:
    widget.show()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    _center_window_on_origin(widget, origin)


def _exec_centered(dialog: QDialog, origin: QWidget | None = None) -> int:
    _center_window_on_origin(dialog, origin)
    return dialog.exec()


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


def _parse_piece_quantity_value(raw_value, default: int = 1, minimum: int = 1) -> int:
    try:
        fallback_value = max(minimum, int(float(default)))
    except (TypeError, ValueError):
        fallback_value = minimum
    if raw_value == "" or raw_value is None:
        return fallback_value
    try:
        quantity = int(float(raw_value))
    except (ValueError, TypeError):
        return fallback_value
    return quantity if quantity >= minimum else minimum


def _total_module_quantity(modules) -> int:
    total_quantity = 0
    for module in modules or []:
        total_quantity += _parse_piece_quantity_value(getattr(module, "quantity", None), default=1)
    return total_quantity


def _coerce_piece_quantity_field(
    piece_data: dict,
    field_name: str = "quantity",
    *,
    default: int = 1,
    minimum: int = 1,
) -> None:
    piece_data[field_name] = _parse_piece_quantity_value(
        piece_data.get(field_name),
        default=default,
        minimum=minimum,
    )


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
        filtered_row["grain_direction"] = normalize_piece_grain_direction(filtered_row.get("grain_direction"))
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
    module_quantity_hint=1,
) -> ModuleData:
    config_path = module_path / "module_config.json"
    config_data = _read_json_file(config_path)
    if not isinstance(config_data, dict):
        config_data = {}

    module_name = str(config_data.get("module") or module_name_hint or module_path.name).strip() or module_path.name
    relative_path = _module_relative_path(project_root, module_path, relative_path_hint) or relative_path_hint
    pieces = _load_pieces_from_config_rows(config_data.get("pieces", []), module_name)
    module_quantity = _parse_piece_quantity_value(module_quantity_hint, default=1)

    return ModuleData(
        name=module_name,
        path=str(module_path),
        locale_name=locale_name,
        relative_path=relative_path,
        quantity=module_quantity,
        pieces=pieces,
    )


def _load_saved_modules_for_locale(project_root: Path, locale: LocaleData) -> list[ModuleData]:
    locale_path = project_root / locale.path
    modules_by_key: dict[str, ModuleData] = {}
    ordered_module_keys: list[str] = []

    def remember_module(module: ModuleData) -> None:
        module_key = (module.relative_path or str(module.path)).lower()
        modules_by_key[module_key] = module
        if module_key not in ordered_module_keys:
            ordered_module_keys.append(module_key)

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
                module_quantity = _parse_piece_quantity_value(module_row.get("quantity"), default=1)

                module_path = locale_path / module_relative_from_locale
                relative_path_hint = str((Path(locale.path) / module_relative_from_locale)).replace("\\", "/")
                module = _load_module_from_saved_config(
                    project_root=project_root,
                    module_path=module_path,
                    locale_name=locale.name,
                    module_name_hint=module_name,
                    relative_path_hint=relative_path_hint,
                    module_quantity_hint=module_quantity,
                )
                remember_module(module)

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
            if module_key not in modules_by_key:
                remember_module(module)

    return [modules_by_key[module_key] for module_key in ordered_module_keys]


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
        locale.modules_count = _total_module_quantity(locale_modules)
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
                locale_modules = [
                    module
                    for module in self.project.modules
                    if str(module.locale_name or "").strip().lower() == locale.name.strip().lower()
                ]
                modules_count = _total_module_quantity(locale_modules)
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

        self.update_modules_button()
        self.update_output_action_buttons()

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
                filtered_dict["grain_direction"] = normalize_piece_grain_direction(filtered_dict.get("grain_direction"))
                
                _coerce_optional_piece_float_fields(
                    filtered_dict,
                    ("thickness", "program_width", "program_height", "program_thickness"),
                )
                _coerce_piece_quantity_field(filtered_dict)
                
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
                piece_quantity = _parse_piece_quantity_value(piece.quantity, default=1)
                rows.append(
                    {
                        "id": piece.id,
                        "name": piece.name or piece.id,
                        "quantity": piece_quantity,
                        "height": piece.height,
                        "width": piece.width,
                        "thickness": piece.thickness,
                        "color": piece.color,
                        "grain_direction": normalize_piece_grain_direction(piece.grain_direction),
                        "source": source_value,
                        "f6_source": piece.f6_source or previous_row.get("f6_source"),
                        "pgmx": pgmx_status,
                        "piece_type": piece.piece_type,
                        "program_width": piece.program_width,
                        "program_height": piece.program_height,
                        "program_thickness": piece.program_thickness,
                        "en_juego": bool(previous_row.get("en_juego", False)),
                        "include_in_sheet": bool(previous_row.get("include_in_sheet", previous_row.get("excel", False))),
                        "observations": normalize_piece_observations(previous_row.get("observations")),
                    }
                )

            config_data = {
                "module": module.name,
                "path": str(module_path),
                "generated_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                "en_juego_layout": previous_config.get("en_juego_layout", {}),
                "en_juego_output_path": previous_config.get("en_juego_output_path", ""),
                "en_juego_settings": _normalize_en_juego_settings(previous_config.get("en_juego_settings")),
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

    def _configured_board_colors(self, piece_thickness: float | None = None) -> list[str]:
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

    def _prompt_processing_color_replacement(
        self,
        original_color: str,
        available_colors: list[str],
        affected_piece_count: int,
        affected_units_count: int,
    ) -> str | None:
        color_dialog = QDialog(self)
        color_dialog.setWindowTitle("Procesar proyecto")
        color_layout = QVBoxLayout()
        color_layout.addWidget(
            QLabel(
                "Se encontraron piezas con un color no configurado en los tableros.\n"
                f"Color detectado: {original_color or '(sin color)'}\n"
                f"Piezas afectadas: {affected_piece_count} | Unidades: {affected_units_count}\n"
                "Seleccione el color de tablero que se aplicará a todas ellas."
            )
        )

        colors_list = QListWidget()
        for color in available_colors:
            colors_list.addItem(color)
        color_layout.addWidget(colors_list)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        accept_button = QPushButton("Aceptar")
        cancel_button = QPushButton("Cancelar")
        accept_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        buttons_layout.addWidget(accept_button)
        buttons_layout.addWidget(cancel_button)
        color_layout.addLayout(buttons_layout)

        if colors_list.count() > 0:
            colors_list.setCurrentRow(0)

        def accept_color_selection():
            if colors_list.currentItem() is None:
                QMessageBox.warning(color_dialog, "Procesar proyecto", "Seleccione un color.")
                return
            color_dialog.accept()

        accept_button.clicked.connect(accept_color_selection)
        cancel_button.clicked.connect(color_dialog.reject)
        colors_list.itemDoubleClicked.connect(lambda _item: accept_color_selection())
        color_dialog.setLayout(color_layout)

        if _exec_centered(color_dialog, self) != QDialog.Accepted or colors_list.currentItem() is None:
            return None
        return colors_list.currentItem().text().strip() or None

    def _resolve_processed_piece_colors(self, processed_modules: list[ModuleData]) -> bool:
        available_colors = self._configured_board_colors()
        available_color_map = {color.strip().lower(): color for color in available_colors if str(color).strip()}

        unresolved_groups: dict[str, dict] = {}
        for module in processed_modules:
            for piece in getattr(module, "pieces", []):
                if not self._is_valid_piece_for_count(piece):
                    continue

                raw_color = str(piece.color or "").strip()
                color_key = raw_color.lower()
                if color_key in available_color_map:
                    piece.color = available_color_map[color_key]
                    continue

                group = unresolved_groups.setdefault(
                    color_key,
                    {
                        "display": raw_color,
                        "pieces": [],
                        "piece_count": 0,
                        "units_count": 0,
                    },
                )
                group["pieces"].append(piece)
                group["piece_count"] += 1
                group["units_count"] += _parse_piece_quantity_value(
                    getattr(piece, "quantity", None),
                    default=1,
                )

        if not unresolved_groups:
            return True

        if not available_colors:
            missing_labels = ", ".join(
                sorted(group["display"] or "(sin color)" for group in unresolved_groups.values())
            )
            QMessageBox.warning(
                self,
                "Procesar",
                "Hay piezas con colores que no coinciden con ningún tablero configurado,\n"
                "pero no hay colores disponibles para reasignar.\n\n"
                f"Colores detectados: {missing_labels}",
            )
            return False

        for group in sorted(
            unresolved_groups.values(),
            key=lambda item: (str(item["display"] or "").strip().lower(), item["piece_count"]),
        ):
            selected_color = self._prompt_processing_color_replacement(
                str(group["display"] or "").strip(),
                available_colors,
                int(group["piece_count"] or 0),
                int(group["units_count"] or 0),
            )
            if not selected_color:
                return False
            for piece in group["pieces"]:
                piece.color = selected_color

        return True

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

    def _module_path_processing_key(self, module: ModuleData) -> str:
        try:
            return str(Path(module.path).resolve()).lower()
        except Exception:
            return str(module.path or "").strip().lower()

    def _preserve_locale_module_order(
        self,
        locale_name: str,
        modules: list[ModuleData],
    ) -> list[ModuleData]:
        locale_key = str(locale_name or "").strip().lower()
        modules_by_path: dict[str, ModuleData] = {}
        scanned_order: list[str] = []
        for module in modules:
            module_key = self._module_path_processing_key(module)
            if module_key not in modules_by_path:
                scanned_order.append(module_key)
            modules_by_path[module_key] = module

        ordered_modules: list[ModuleData] = []
        used_keys: set[str] = set()
        for module in self.project.modules:
            if str(module.locale_name or "").strip().lower() != locale_key:
                continue
            module_key = self._module_path_processing_key(module)
            ordered_module = modules_by_path.get(module_key)
            if ordered_module is None or module_key in used_keys:
                continue
            ordered_modules.append(ordered_module)
            used_keys.add(module_key)

        for module_key in scanned_order:
            if module_key not in used_keys:
                ordered_modules.append(modules_by_path[module_key])

        return ordered_modules

    def _resolve_modules_for_processing(
        self,
        scanned_modules: list[ModuleData],
    ) -> tuple[list[ModuleData], list[ModuleData]] | None:
        existing_modules_by_path = {
            self._module_path_processing_key(module): module
            for module in getattr(self.project, "modules", [])
        }

        resolved_modules: list[ModuleData] = []
        modules_to_reprocess: list[ModuleData] = []

        for scanned_module in scanned_modules:
            existing_module = existing_modules_by_path.get(self._module_path_processing_key(scanned_module))
            if existing_module is not None:
                scanned_module.quantity = _parse_piece_quantity_value(
                    getattr(existing_module, "quantity", None),
                    default=1,
                )

            config_path = self._module_config_path(scanned_module)
            if not config_path.exists():
                resolved_modules.append(scanned_module)
                modules_to_reprocess.append(scanned_module)
                continue

            module_label = (
                f"{scanned_module.locale_name} / {scanned_module.name}"
                if str(scanned_module.locale_name or "").strip()
                else scanned_module.name
            )
            answer = QMessageBox.question(
                self,
                "Procesar",
                (
                    f"El módulo '{module_label}' ya tiene una configuración previa.\n\n"
                    "¿Desea reprocesarlo?"
                ),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No,
            )
            if answer == QMessageBox.Cancel:
                return None
            if answer == QMessageBox.Yes:
                resolved_modules.append(scanned_module)
                modules_to_reprocess.append(scanned_module)
                continue

            if existing_module is None:
                existing_module = ModuleData(
                    name=scanned_module.name,
                    path=scanned_module.path,
                    locale_name=scanned_module.locale_name,
                    relative_path=scanned_module.relative_path,
                    quantity=_parse_piece_quantity_value(getattr(scanned_module, "quantity", None), default=1),
                    is_manual=scanned_module.is_manual,
                    pieces=[],
                )
            else:
                existing_module.name = scanned_module.name
                existing_module.path = scanned_module.path
                existing_module.locale_name = scanned_module.locale_name
                existing_module.relative_path = scanned_module.relative_path
                existing_module.is_manual = scanned_module.is_manual

            self._reload_module_pieces_from_config(existing_module)
            self._normalize_module_piece_thickness(existing_module)
            resolved_modules.append(existing_module)

        return resolved_modules, modules_to_reprocess

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
            locale.modules_count = _total_module_quantity(locale_modules)

            rows = []
            for module in locale_modules:
                module_path = Path(module.path)
                try:
                    relative_module_path = str(module_path.relative_to(locale_path)).replace("\\", "/")
                except ValueError:
                    relative_module_path = module.relative_path or module.name

                rows.append(
                    {
                        "name": module.name,
                        "path": relative_module_path,
                        "quantity": _parse_piece_quantity_value(getattr(module, "quantity", None), default=1),
                        "dimensions": self._resolve_module_nominal_dimensions(module),
                    }
                )

            config_data = {
                "locale_name": locale.name,
                "path": locale.path,
                "modules_count": locale.modules_count,
                "modules": rows,
            }
            self._locale_config_path(locale).write_text(
                json.dumps(config_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _valid_pieces_in_module(self, module):
        return [piece for piece in module.pieces if self._is_valid_piece_for_count(piece)]

    def _piece_quantity(self, piece) -> int:
        """Cantidad numérica de la pieza."""
        return _parse_piece_quantity_value(getattr(piece, "quantity", None), default=1)

    def _valid_piece_count_in_module(self, module) -> int:
        """Total de piezas (unidades) válidas en el módulo."""
        return sum(self._piece_quantity(piece) for piece in module.pieces if self._is_valid_piece_for_count(piece))

    def edit_project(self):
        """Abrir ventana de edición del proyecto."""
        edit_window = EditProjectWindow(self.project)
        _show_centered(edit_window, self)
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

            if (
                locale_name in {".", ".."}
                or locale_name.rstrip(" .") != locale_name
                or any(char in locale_name for char in '<>:"/\\|?*')
            ):
                QMessageBox.warning(
                    self,
                    title,
                    "El nombre del local contiene caracteres no validos para una carpeta.",
                )
                continue

            existing_locale_keys = {
                value
                for locale in _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
                for value in {
                    str(locale.name or "").strip().lower(),
                    str(locale.path or "").strip().lower(),
                }
                if value
            }
            if locale_name.lower() in existing_locale_keys:
                QMessageBox.warning(self, title, "Ya existe un local con ese nombre.")
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

    def add_locale(self):
        root_path = Path(self.project.root_directory)
        if not root_path.exists():
            QMessageBox.warning(self, "Agregar Local", "La carpeta raiz del proyecto no existe.")
            return

        locale_name = self._prompt_new_locale_name(
            root_path,
            "Agregar Local",
            "Nombre del nuevo local:",
        )
        if not locale_name:
            return

        new_locale = LocaleData(name=locale_name, path=locale_name, modules_count=0)
        current_locales = _normalize_project_locales(
            getattr(self.project, "locales", []),
            getattr(self.project, "local", ""),
        )
        updated_locales = sorted(
            current_locales + [new_locale],
            key=lambda locale: locale.name.lower(),
        )
        try:
            self._write_locale_config_files([new_locale])
            self.project.locales = updated_locales
            _save_project(self.project)
        except Exception as exc:
            QMessageBox.warning(self, "Agregar Local", f"No se pudo crear el local:\n{exc}")
            return

        self.refresh_project_header_info()
        QMessageBox.information(
            self,
            "Agregar Local",
            f"Local creado correctamente:\n{root_path / locale_name}",
        )

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

        progress_dialog: QProgressDialog | None = None
        progress_step = 0
        total_steps = 8

        def close_progress() -> None:
            nonlocal progress_dialog
            if progress_dialog is None:
                return
            progress_dialog.close()
            progress_dialog = None
            QApplication.processEvents()

        def start_progress(message: str = "Preparando procesamiento del proyecto...") -> None:
            nonlocal progress_dialog
            if progress_dialog is not None:
                progress_dialog.setLabelText(message)
                progress_dialog.show()
                QApplication.processEvents()
                return
            progress_dialog = QProgressDialog(message, "", 0, total_steps, self)
            progress_dialog.setWindowTitle("Procesar Seleccion")
            progress_dialog.setWindowModality(Qt.ApplicationModal)
            progress_dialog.setCancelButton(None)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            progress_dialog.setValue(progress_step)
            progress_dialog.show()
            QApplication.processEvents()

        def update_progress(message: str, *, advance: bool = True) -> None:
            nonlocal progress_step
            if progress_dialog is None:
                return
            if advance:
                progress_step = min(total_steps, progress_step + 1)
            progress_dialog.setLabelText(message)
            progress_dialog.setValue(progress_step)
            QApplication.processEvents()

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
            reprocessed_modules: list[ModuleData] = []

            if listed_locale_names:
                if not selected_locale_names:
                    QMessageBox.warning(
                        self,
                        "Procesar",
                        "Seleccione al menos un local en la lista para procesar.",
                    )
                    return

                start_progress()
                update_progress("Buscando locales seleccionados...", advance=False)
                layout = inspect_project_layout(root_path)
                selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names}
                locale_dirs = [
                    locale_dir
                    for locale_dir in layout.locale_dirs
                    if locale_dir.name.strip().lower() in selected_locale_keys
                ]
                if not locale_dirs:
                    close_progress()
                    QMessageBox.warning(
                        self,
                        "Procesar",
                        "No se encontraron carpetas disponibles para los locales seleccionados.",
                    )
                    return

                rescanned_locale_keys = {locale_dir.name.strip().lower() for locale_dir in locale_dirs}
                processed_locales = []
                processed_modules = []
                update_progress("Escaneando locales seleccionados.")
                for locale_dir in locale_dirs:
                    update_progress(f"Escaneando local {locale_dir.name}...", advance=False)
                    locale_modules = scan_project(locale_dir)
                    for module in locale_modules:
                        module.locale_name = locale_dir.name
                        module.relative_path = str(Path(module.path).relative_to(root_path)).replace("\\", "/")
                    close_progress()
                    resolved_modules = self._resolve_modules_for_processing(locale_modules)
                    if resolved_modules is None:
                        return
                    start_progress(f"Local {locale_dir.name} escaneado.")
                    locale_modules, locale_reprocessed_modules = resolved_modules
                    locale_modules = self._preserve_locale_module_order(locale_dir.name, locale_modules)
                    processed_locales.append(
                        LocaleData(
                            name=locale_dir.name,
                            path=str(locale_dir.relative_to(root_path)).replace("\\", "/"),
                            modules_count=_total_module_quantity(locale_modules),
                        )
                    )
                    processed_modules.extend(locale_modules)
                    reprocessed_modules.extend(locale_reprocessed_modules)

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
                self.project.modules = preserved_modules + processed_modules
            else:
                start_progress()
                update_progress("Escaneando estructura del proyecto...", advance=False)
                scanned_locales, scanned_modules = scan_project_structure(root_path)
                update_progress("Estructura del proyecto escaneada.")
                scanned_modules_by_locale: dict[str, list[ModuleData]] = {}
                for module in scanned_modules:
                    locale_key = str(module.locale_name or "").strip().lower()
                    scanned_modules_by_locale.setdefault(locale_key, []).append(module)

                processed_locales = []
                processed_modules = []
                for locale in scanned_locales:
                    locale_key = locale.name.strip().lower()
                    locale_modules = scanned_modules_by_locale.get(locale_key, [])
                    update_progress(f"Resolviendo local {locale.name}...", advance=False)
                    close_progress()
                    resolved_modules = self._resolve_modules_for_processing(locale_modules)
                    if resolved_modules is None:
                        return
                    start_progress(f"Local {locale.name} resuelto.")
                    locale_modules, locale_reprocessed_modules = resolved_modules
                    locale_modules = self._preserve_locale_module_order(locale.name, locale_modules)
                    locale.modules_count = _total_module_quantity(locale_modules)
                    processed_locales.append(locale)
                    processed_modules.extend(locale_modules)
                    reprocessed_modules.extend(locale_reprocessed_modules)

                self.project.locales = processed_locales
                self.project.modules = processed_modules

            # Normalizar thickness de todas las piezas procesadas
            update_progress("Normalizando piezas procesadas.")
            for module in reprocessed_modules:
                self._normalize_module_piece_thickness(module)

            update_progress("Revisando colores de piezas.")
            close_progress()
            if not self._resolve_processed_piece_colors(reprocessed_modules):
                return
            start_progress("Colores de piezas resueltos.")
            
            update_progress("Guardando configuracion de modulos.")
            self._write_module_config_files(reprocessed_modules)
            self._write_locale_config_files(processed_locales)
            
            # Recargar piezas desde los module_config.json recién generados
            for module in reprocessed_modules:
                self._reload_module_pieces_from_config(module)
            
            self._write_locale_config_files(processed_locales)
            _save_project(self.project)

            from core.summary import export_summary
            summary_csv_path = root_path / "resumen_piezas.csv"
            update_progress("Exportando resumen de piezas.")
            export_summary(self.project, summary_csv_path)

            processed_project = Project(
                name=self.project.name,
                root_directory=self.project.root_directory,
                project_data_file=self.project.project_data_file,
                client=self.project.client,
                created_at=self.project.created_at,
                locales=processed_locales,
                modules=reprocessed_modules,
                output_directory=self.project.output_directory,
            )
            update_progress("Generando dibujos SVG de piezas.")
            generated_drawings, skipped_drawings, pieces_with_machining = generate_project_piece_drawings(
                processed_project,
            )

            total_pieces = sum(self._valid_piece_count_in_module(module) for module in reprocessed_modules)
            module_breakdown = "\n".join([
                f"{module.name}: {self._valid_piece_count_in_module(module)}"
                for module in reprocessed_modules
            ])
            if not module_breakdown:
                module_breakdown = "(sin módulos reprocesados)"
            warning_parts = []
            for module in reprocessed_modules:
                if self._valid_piece_count_in_module(module) == 0:
                    warning_parts.append(module.name)

            self.refresh_project_header_info()
            self.update_modules_button()
            update_progress("Actualizando interfaz.")

            detail_text = (
                f"Locales procesados: {len(processed_locales)}\n"
                f"Módulos reprocesados: {len(reprocessed_modules)}\n"
                f"Módulos conservados desde configuración previa: {len(processed_modules) - len(reprocessed_modules)}\n"
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

            update_progress("Procesamiento completado.")
            close_progress()
            QMessageBox.information(self, "Procesamiento completado", detail_text)
        except Exception as exc:
            close_progress()
            QMessageBox.warning(self, "Error", f"Error durante el procesamiento: {exc}")

    def _project_has_locales_and_modules(self) -> bool:
        locales = _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
        return bool(locales) and bool(getattr(self.project, "modules", []))

    def _project_has_module_window_context(self) -> bool:
        locales = _normalize_project_locales(getattr(self.project, "locales", []), getattr(self.project, "local", ""))
        return bool(locales) or bool(getattr(self.project, "modules", []))

    def update_modules_button(self):
        """Habilitar boton Modulos si hay un local o modulos cargados."""
        enabled = self._project_has_module_window_context()
        self.btn_modules.setEnabled(enabled)
        self.btn_modules.setToolTip("" if enabled else "Agregue un local o procese el proyecto.")

    def update_output_action_buttons(self):
        enabled = self._project_has_locales_and_modules()
        tooltip = "" if enabled else "Procese el proyecto y asegure que tenga locales y modulos."
        for button in (self.btn_sheets, self.btn_cuts):
            button.setEnabled(enabled)
            button.setToolTip(tooltip)

    def show_modules(self):
        """Mostrar lista de módulos en una ventana modal"""
        selected_locale_names: list[str] = []
        seen_locale_keys: set[str] = set()
        for item in self.locales_list.selectedItems():
            locale_name = str(item.data(Qt.UserRole) or "").strip()
            locale_key = locale_name.lower()
            if not locale_name or locale_key in seen_locale_keys:
                continue
            seen_locale_keys.add(locale_key)
            selected_locale_names.append(locale_name)

        if not selected_locale_names:
            current_locale_item = self.locales_list.currentItem()
            current_locale_name = str(current_locale_item.data(Qt.UserRole) or "").strip() if current_locale_item else ""
            if current_locale_name:
                selected_locale_names.append(current_locale_name)

        available_locale_names = self._listed_locale_names()
        if available_locale_names and not selected_locale_names:
            if len(available_locale_names) == 1:
                selected_locale_names = list(available_locale_names)
            else:
                QMessageBox.warning(
                    self,
                    "Módulos",
                    "Seleccione un local en la lista para ver sus módulos.",
                )
                return
        if not selected_locale_names and not self.project.modules:
            QMessageBox.warning(
                self,
                "Módulos",
                "Agregue un local o procese el proyecto para continuar.",
            )
            return

        selected_locale_keys = {locale_name.strip().lower() for locale_name in selected_locale_names if locale_name.strip()}
        def filtered_modules_for_dialog() -> list[ModuleData]:
            return [
                module
                for module in self.project.modules
                if not selected_locale_keys or str(module.locale_name or "").strip().lower() in selected_locale_keys
            ]

        dialog = QDialog(self)
        if len(selected_locale_names) == 1:
            dialog.setWindowTitle(f"Local: {selected_locale_names[0]}")
        else:
            dialog.setWindowTitle("Locales")
        dialog.resize(760, 400)

        dlg_layout = QVBoxLayout()
        self.modules_list = QTableWidget()
        self.modules_list.setColumnCount(3)
        self.modules_list.setHorizontalHeaderLabels(["Cantidad", "Módulo", "Piezas"])
        self.modules_list.verticalHeader().setVisible(False)
        self.modules_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.modules_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.modules_list.setSelectionMode(QTableWidget.SingleSelection)
        self.modules_list.setAlternatingRowColors(True)
        modules_header = self.modules_list.horizontalHeader()
        modules_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        modules_header.setSectionResizeMode(1, QHeaderView.Stretch)
        modules_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        def refresh_modules_list_view(
            selected_module_key: str | None = None,
            *,
            focus_selected_row: bool = False,
        ):
            current_visible_modules = filtered_modules_for_dialog()
            current_selected_key = str(selected_module_key or "").strip()
            if not current_selected_key and self.modules_list.currentRow() >= 0:
                selected_item = self.modules_list.item(self.modules_list.currentRow(), 1)
                if selected_item is not None:
                    current_selected_key = str(selected_item.data(Qt.UserRole) or "").strip()
            # Recargar piezas desde module_config.json y normalizar thickness
            for module in current_visible_modules:
                self._reload_module_pieces_from_config(module)
                self._normalize_module_piece_thickness(module)
            
            self.modules_list.setRowCount(len(current_visible_modules))
            selected_row = -1
            for row_idx, module in enumerate(current_visible_modules):
                valid_count = self._valid_piece_count_in_module(module)
                module_label = f"{module.locale_name} / {module.name}" if module.locale_name else module.name
                module_key = module.relative_path or module.path
                module_item = QTableWidgetItem(module_label)
                module_item.setData(Qt.UserRole, module_key)
                quantity_item = QTableWidgetItem(
                    str(_parse_piece_quantity_value(getattr(module, "quantity", None), default=1))
                )
                quantity_item.setTextAlignment(Qt.AlignCenter)
                pieces_item = QTableWidgetItem(str(valid_count))
                pieces_item.setTextAlignment(Qt.AlignCenter)
                self.modules_list.setItem(row_idx, 0, quantity_item)
                self.modules_list.setItem(row_idx, 1, module_item)
                self.modules_list.setItem(row_idx, 2, pieces_item)
                if current_selected_key and str(module_key).strip() == current_selected_key:
                    selected_row = row_idx

            if self.modules_list.rowCount() > 0:
                if selected_row < 0:
                    selected_row = 0
                self.modules_list.clearSelection()
                self.modules_list.setCurrentCell(selected_row, 1)
                self.modules_list.selectRow(selected_row)
                selected_item = self.modules_list.item(selected_row, 1)
                if selected_item is not None:
                    self.modules_list.scrollToItem(selected_item)
                if focus_selected_row:
                    self.modules_list.setFocus(Qt.OtherFocusReason)
            refresh_inspect_button_state()
            refresh_module_order_button_state()

        dlg_layout.addWidget(QLabel("Módulos encontrados:"))
        modules_and_actions_row = QHBoxLayout()
        modules_and_actions_row.addWidget(self.modules_list, 1)

        new_btn = QPushButton("Nuevo\nMódulo")
        inspect_btn = QPushButton("Abrir\nMódulo")
        move_up_btn = QPushButton("Subir")
        move_down_btn = QPushButton("Bajar")
        close_btn = QPushButton("Cerrar")
        for button in (new_btn, inspect_btn, move_up_btn, move_down_btn, close_btn):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

        def refresh_inspect_button_state():
            current_row = self.modules_list.currentRow()
            enabled = 0 <= current_row < self.modules_list.rowCount()
            inspect_btn.setEnabled(enabled)
            inspect_btn.setToolTip("" if enabled else "Seleccione un módulo para abrirlo.")

        def module_at_table_row(row: int) -> ModuleData | None:
            if row < 0 or row >= self.modules_list.rowCount():
                return None
            module_item = self.modules_list.item(row, 1)
            module_key = str(module_item.data(Qt.UserRole) or "").strip() if module_item is not None else ""
            if not module_key:
                return None
            for module in self.project.modules:
                if str(module.relative_path or module.path).strip() == module_key:
                    return module
            return None

        def module_locale_key(module: ModuleData | None) -> str:
            return str(getattr(module, "locale_name", "") or "").strip().lower()

        def can_move_selected_module(delta: int) -> bool:
            current_row = self.modules_list.currentRow()
            target_row = current_row + delta
            current_module = module_at_table_row(current_row)
            target_module = module_at_table_row(target_row)
            return (
                current_module is not None
                and target_module is not None
                and module_locale_key(current_module) == module_locale_key(target_module)
            )

        def refresh_module_order_button_state():
            move_up_btn.setEnabled(can_move_selected_module(-1))
            move_down_btn.setEnabled(can_move_selected_module(1))
            move_up_btn.setToolTip("" if move_up_btn.isEnabled() else "Seleccione un modulo que pueda subir.")
            move_down_btn.setToolTip("" if move_down_btn.isEnabled() else "Seleccione un modulo que pueda bajar.")

        def module_project_index(module: ModuleData) -> int | None:
            module_key = str(module.relative_path or module.path).strip()
            for index, current_module in enumerate(self.project.modules):
                if str(current_module.relative_path or current_module.path).strip() == module_key:
                    return index
            return None

        def persist_module_order(module: ModuleData) -> None:
            locale_key = module_locale_key(module)
            target_locale = next(
                (
                    locale
                    for locale in self.project.locales
                    if str(locale.name or "").strip().lower() == locale_key
                ),
                None,
            )
            if target_locale is not None:
                self._write_locale_config_files([target_locale])
            _save_project(self.project)

        def move_selected_module(delta: int) -> None:
            current_row = self.modules_list.currentRow()
            target_row = current_row + delta
            current_module = module_at_table_row(current_row)
            target_module = module_at_table_row(target_row)
            if (
                current_module is None
                or target_module is None
                or module_locale_key(current_module) != module_locale_key(target_module)
            ):
                return

            current_index = module_project_index(current_module)
            target_index = module_project_index(target_module)
            if current_index is None or target_index is None:
                return

            self.project.modules[current_index], self.project.modules[target_index] = (
                self.project.modules[target_index],
                self.project.modules[current_index],
            )
            persist_module_order(current_module)
            moved_module_key = str(current_module.relative_path or current_module.path).strip()
            refresh_modules_list_view(moved_module_key, focus_selected_row=True)

        self.modules_list.itemSelectionChanged.connect(refresh_inspect_button_state)
        self.modules_list.itemSelectionChanged.connect(refresh_module_order_button_state)
        refresh_modules_list_view()

        actions_column = QVBoxLayout()
        actions_column.setContentsMargins(0, 0, 0, 0)
        actions_column.addWidget(new_btn)
        actions_column.addWidget(inspect_btn)
        actions_column.addWidget(move_up_btn)
        actions_column.addWidget(move_down_btn)
        actions_column.addStretch(1)
        actions_column.addWidget(close_btn)

        modules_and_actions_row.addLayout(actions_column)
        dlg_layout.addLayout(modules_and_actions_row, 1)

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

            if selected_locale_keys:
                locale_options = [
                    locale.name
                    for locale in self.project.locales
                    if locale.name.strip().lower() in selected_locale_keys
                ]
            else:
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
                quantity=1,
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
                "en_juego_output_path": "",
                "en_juego_settings": _default_en_juego_settings(),
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
            self._write_locale_config_files([selected_locale])

            _save_project(self.project)
            self.refresh_project_header_info()
            refresh_modules_list_view()
            QMessageBox.information(dialog, "Nuevo módulo", f"Módulo '{module_name}' creado correctamente.")

        new_btn.clicked.connect(create_manual_module)
        inspect_btn.clicked.connect(lambda: self.inspect_module(dialog, refresh_modules_list_view))
        move_up_btn.clicked.connect(lambda: move_selected_module(-1))
        move_down_btn.clicked.connect(lambda: move_selected_module(1))
        self.modules_list.cellDoubleClicked.connect(lambda *_: self.inspect_module(dialog, refresh_modules_list_view))
        close_btn.clicked.connect(dialog.accept)

        _exec_centered(dialog, self)

    def inspect_module(self, parent_dialog, on_module_updated=None):
        """Mostrar piezas del módulo seleccionado"""
        selected_item = None
        if isinstance(self.modules_list, QTableWidget):
            current_row = self.modules_list.currentRow()
            if current_row >= 0:
                selected_item = self.modules_list.item(current_row, 1)
        else:
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
        config_data["en_juego_settings"] = _normalize_en_juego_settings(config_data.get("en_juego_settings"))
        settings = config_data.get("settings", {})
        raw_rows = config_data.get("pieces", [])
        if not isinstance(raw_rows, list):
            raw_rows = []

        def _coerce_saved_flag(value) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            raw = str(value or "").strip().lower()
            return raw in {"1", "true", "yes", "si", "sí", "x"}

        def _normalize_piece_row_flags(piece_row: dict) -> dict:
            normalized_row = dict(piece_row)
            en_juego_value = _coerce_saved_flag(normalized_row.get("en_juego", False))
            excel_value = _coerce_saved_flag(
                normalized_row.get("include_in_sheet", normalized_row.get("excel", False))
            )
            normalized_row["en_juego"] = en_juego_value
            normalized_row["include_in_sheet"] = excel_value
            normalized_row["quantity"] = _parse_piece_quantity_value(
                normalized_row.get("quantity"),
                default=1,
            )
            normalized_row["grain_direction"] = normalize_piece_grain_direction(normalized_row.get("grain_direction"))
            normalized_row["observations"] = normalize_piece_observations(normalized_row.get("observations"))
            normalized_row.pop("excel", None)
            normalized_row.pop("quantity_step", None)
            return normalized_row

        all_rows = [
            _normalize_piece_row_flags(piece_row)
            for piece_row in raw_rows
            if isinstance(piece_row, dict)
        ]
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

        def normalized_program_reference_keys(source_value: str) -> set[str]:
            raw_source = str(source_value or "").strip()
            if not raw_source:
                return set()

            keys = {raw_source.replace("\\", "/").lower(), Path(raw_source).name.lower()}
            source_path = Path(raw_source)
            candidate_path = source_path if source_path.is_absolute() else module_path / source_path
            if candidate_path.is_file():
                try:
                    keys.add(str(candidate_path.resolve()).lower())
                except OSError:
                    keys.add(str(candidate_path).lower())
            return keys

        def associated_program_reference_keys() -> set[str]:
            keys: set[str] = set()
            for piece_row in all_rows:
                keys.update(normalized_program_reference_keys(str(piece_row.get("source") or "")))
                keys.update(normalized_program_reference_keys(str(piece_row.get("f6_source") or "")))
            return keys

        def orphan_pgmx_files() -> list[Path]:
            associated_keys = associated_program_reference_keys()
            orphans: list[Path] = []
            for pgmx_file in sorted(module_path.rglob("*.pgmx"), key=lambda item: str(item.relative_to(module_path)).lower()):
                if not pgmx_file.is_file():
                    continue
                relative_key = str(pgmx_file.relative_to(module_path)).replace("\\", "/").lower()
                try:
                    resolved_key = str(pgmx_file.resolve()).lower()
                except OSError:
                    resolved_key = str(pgmx_file).lower()
                if (
                    relative_key in associated_keys
                    or pgmx_file.name.lower() in associated_keys
                    or resolved_key in associated_keys
                ):
                    continue
                orphans.append(pgmx_file)
            return orphans

        def unique_orphan_piece_id(program_path: Path) -> str:
            existing_ids = {str(row.get("id") or "").strip().lower() for row in all_rows}
            base_id = "".join(
                char if char.isalnum() or char in {"-", "_"} else "_"
                for char in program_path.stem.strip()
            ).strip("_") or "PGMX"
            candidate = base_id
            suffix = 2
            while candidate.lower() in existing_ids:
                candidate = f"{base_id}_{suffix}"
                suffix += 1
            existing_ids.add(candidate.lower())
            return candidate

        def row_for_orphan_program(program_path: Path) -> dict:
            from core.pgmx_processing import get_pgmx_program_dimensions

            source_value = normalize_source_path(str(program_path))
            piece_id = unique_orphan_piece_id(program_path)
            temp_piece = Piece(
                id=piece_id,
                name=program_path.stem,
                width=0.0,
                height=0.0,
                thickness=None,
                module_name=selected_module.name,
                cnc_source=source_value,
            )
            program_width, program_height, program_thickness = get_pgmx_program_dimensions(
                self.project,
                temp_piece,
                module_path,
            )
            return {
                "id": piece_id,
                "name": program_path.stem,
                "quantity": 1,
                "height": program_width or "",
                "width": program_height or "",
                "thickness": program_thickness,
                "color": None,
                "grain_direction": PIECE_GRAIN_CODE_NONE,
                "source": source_value,
                "f6_source": None,
                "pgmx": self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths),
                "piece_type": None,
                "program_width": program_width,
                "program_height": program_height,
                "program_thickness": program_thickness,
                "en_juego": False,
                "include_in_sheet": False,
                "observations": "",
            }

        def prompt_add_orphan_programs() -> bool:
            orphan_files = orphan_pgmx_files()
            if not orphan_files:
                return False

            relative_names = [
                str(program_path.relative_to(module_path)).replace("\\", "/")
                for program_path in orphan_files
            ]
            preview_names = "\n".join(f"- {name}" for name in relative_names[:12])
            if len(relative_names) > 12:
                preview_names += f"\n- ... y {len(relative_names) - 12} mas"

            answer = QMessageBox.question(
                inspect_dialog,
                "Programas no asociados",
                (
                    "Se encontraron programas PGMX en la carpeta del modulo "
                    "que no estan asociados a ninguna pieza.\n\n"
                    f"{preview_names}\n\n"
                    "Desea agregarlos a la lista de piezas?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                return False

            for program_path in orphan_files:
                all_rows.append(row_for_orphan_program(program_path))
            return True

        added_orphan_program_rows = prompt_add_orphan_programs()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración del módulo:"))

        dim_x_field = QLineEdit(str(settings.get("x", "") or ""))
        dim_y_field = QLineEdit(str(settings.get("y", "") or ""))
        dim_z_field = QLineEdit(str(settings.get("z", "") or ""))
        module_quantity_field = QLineEdit(
            str(_parse_piece_quantity_value(getattr(selected_module, "quantity", None), default=1))
        )
        field_width = _scaled_int(100, compact_scale, 72)
        quantity_field_width = _scaled_int(80, compact_scale, 60)
        quantity_button_width = _scaled_int(14, compact_scale, 11)
        quantity_button_height = _scaled_int(12, compact_scale, 10)
        quantity_button_font_size = _scaled_int(7, compact_scale, 6)
        dim_x_field.setFixedWidth(field_width)
        dim_y_field.setFixedWidth(field_width)
        dim_z_field.setFixedWidth(field_width)
        module_quantity_field.setFixedWidth(quantity_field_width)

        def style_quantity_micro_button(button: QPushButton) -> None:
            button.setContentsMargins(0, 0, 0, 0)
            button.setStyleSheet(
                "QPushButton {"
                f"font-size: {quantity_button_font_size}px;"
                "padding: 0px;"
                "margin: 0px;"
                "text-align: center;"
                "}"
            )

        def adjust_module_quantity(delta: int) -> None:
            current_value = _parse_piece_quantity_value(module_quantity_field.text().strip(), default=1)
            target_value = max(1, current_value + int(delta))
            if target_value != current_value:
                module_quantity_field.setText(str(target_value))

        module_quantity_buttons = QWidget()
        module_quantity_buttons_layout = QVBoxLayout(module_quantity_buttons)
        module_quantity_buttons_layout.setContentsMargins(0, 0, 0, 0)
        module_quantity_buttons_layout.setSpacing(0)

        module_quantity_plus_btn = QPushButton("+", module_quantity_buttons)
        module_quantity_plus_btn.setToolTip("Incrementar cantidad del módulo")
        module_quantity_plus_btn.setFixedSize(quantity_button_width, quantity_button_height)
        style_quantity_micro_button(module_quantity_plus_btn)
        module_quantity_plus_btn.clicked.connect(lambda: adjust_module_quantity(+1))

        module_quantity_minus_btn = QPushButton("-", module_quantity_buttons)
        module_quantity_minus_btn.setToolTip("Disminuir cantidad del módulo")
        module_quantity_minus_btn.setFixedSize(quantity_button_width, quantity_button_height)
        style_quantity_micro_button(module_quantity_minus_btn)
        module_quantity_minus_btn.clicked.connect(lambda: adjust_module_quantity(-1))

        module_quantity_buttons_layout.addWidget(module_quantity_plus_btn)
        module_quantity_buttons_layout.addWidget(module_quantity_minus_btn)
        module_quantity_buttons.setFixedSize(quantity_button_width, quantity_button_height * 2)

        module_quantity_widget = QWidget()
        module_quantity_layout = QHBoxLayout(module_quantity_widget)
        module_quantity_layout.setContentsMargins(0, 0, 0, 0)
        module_quantity_layout.setSpacing(2)
        module_quantity_layout.addWidget(module_quantity_field)
        module_quantity_layout.addWidget(module_quantity_buttons)

        xyz_layout = QHBoxLayout()
        xyz_layout.addWidget(QLabel("X: "))
        xyz_layout.addWidget(dim_x_field)
        xyz_layout.addWidget(QLabel("Y: "))
        xyz_layout.addWidget(dim_y_field)
        xyz_layout.addWidget(QLabel("Z: "))
        xyz_layout.addWidget(dim_z_field)
        xyz_layout.addStretch(1)
        xyz_layout.addWidget(QLabel("Cantidad: "))
        xyz_layout.addWidget(module_quantity_widget)

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
        module_quantity_field.textChanged.connect(mark_unsaved_changes)
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
            
            _exec_centered(dialog, inspect_dialog)
        
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
            
            _exec_centered(dialog, inspect_dialog)
        
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
            
            _exec_centered(dialog, inspect_dialog)
        
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
        pgmx_repair_warning_label = QLabel("")
        pgmx_repair_warning_label.setWordWrap(True)
        pgmx_repair_warning_label.setStyleSheet("color: #B71C1C; font-weight: 600;")
        pgmx_repair_warning_label.hide()
        layout.addWidget(pgmx_repair_warning_label)

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

        pieces_table = QTableWidget()
        pieces_table.setColumnCount(13)
        pieces_table.setHorizontalHeaderLabels([
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
        ])
        visible_row_indexes = []
        refreshing_pieces_table = False
        program_dimensions_cache = {}
        configure_en_juego_btn = None
        repair_pgmx_btn = None
        move_piece_up_btn = None
        move_piece_down_btn = None
        invalid_slot_cache = {}

        def build_piece_from_row(piece_row):
            thickness_val = piece_row.get("thickness")
            if thickness_val == "" or thickness_val is None:
                thickness = None
            else:
                try:
                    thickness = float(thickness_val)
                except (ValueError, TypeError):
                    thickness = None

            quantity = _parse_piece_quantity_value(piece_row.get("quantity"), default=1)

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
                grain_direction=normalize_piece_grain_direction(piece_row.get("grain_direction")),
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

        def select_piece_table_row(row_idx: int, *, focus_selected_row: bool = False) -> None:
            if row_idx < 0 or row_idx >= pieces_table.rowCount():
                return
            pieces_table.clearSelection()
            pieces_table.setCurrentCell(row_idx, PIECES_COL_ID)
            pieces_table.selectRow(row_idx)
            selected_item = pieces_table.item(row_idx, PIECES_COL_ID)
            if selected_item is not None:
                pieces_table.scrollToItem(selected_item)
            if focus_selected_row:
                pieces_table.setFocus(Qt.OtherFocusReason)

        def select_visible_piece_by_all_index(all_idx: int, *, focus_selected_row: bool = False) -> bool:
            if all_idx not in visible_row_indexes:
                return False
            select_piece_table_row(visible_row_indexes.index(all_idx), focus_selected_row=focus_selected_row)
            return True

        def select_visible_piece_by_id(piece_id: str, fallback_row: int | None = None):
            normalized_id = str(piece_id or "").strip()
            if normalized_id:
                for row_idx, all_idx in enumerate(visible_row_indexes):
                    if str(all_rows[all_idx].get("id") or "").strip() == normalized_id:
                        select_piece_table_row(row_idx)
                        return

            if fallback_row is not None and pieces_table.rowCount() > 0:
                select_piece_table_row(max(0, min(fallback_row, pieces_table.rowCount() - 1)))

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

        def clear_invalid_slot_cache(source_value: str | None = None):
            if source_value is None:
                invalid_slot_cache.clear()
                return
            normalized_source = str(source_value or "").strip()
            keys_to_remove = [
                key for key in invalid_slot_cache
                if key[1] == normalized_source
            ]
            for key in keys_to_remove:
                invalid_slot_cache.pop(key, None)

        def get_invalid_slot_issues_for_row(piece_row: dict):
            source_value = str(piece_row.get("source") or "").strip()
            if not source_value:
                return ()
            cache_key = (str(module_path), source_value)
            if cache_key not in invalid_slot_cache:
                from core.pgmx_processing import get_invalid_slot_machining_issues

                try:
                    invalid_slot_cache[cache_key] = get_invalid_slot_machining_issues(
                        self.project,
                        build_piece_from_row(piece_row),
                        module_path,
                    )
                except Exception:
                    invalid_slot_cache[cache_key] = ()
            return invalid_slot_cache.get(cache_key, ())

        def invalid_slot_message(issues) -> str:
            if not issues:
                return ""
            first_issue = issues[0]
            feature_name = str(first_issue.feature_name or first_issue.feature_id or "ranura")
            return (
                f"Ranura no ejecutable: {feature_name}. "
                "Puede corregirse girando el PGMX 90 grados antihorario."
            )

        def refresh_repair_pgmx_button_state():
            if repair_pgmx_btn is None:
                return
            all_idx = selected_piece_all_index()
            if all_idx is None:
                repair_pgmx_btn.setEnabled(False)
                repair_pgmx_btn.setToolTip("Seleccione una pieza con ranura no ejecutable.")
                return
            issues = get_invalid_slot_issues_for_row(all_rows[all_idx])
            repair_pgmx_btn.setEnabled(bool(issues))
            repair_pgmx_btn.setToolTip(
                "Corregir PGMX girandolo 90 grados antihorario"
                if issues
                else "La pieza seleccionada no tiene ranuras no ejecutables detectadas."
            )

        def can_move_selected_piece(delta: int) -> bool:
            current_row = pieces_table.currentRow()
            target_row = current_row + delta
            return (
                0 <= current_row < pieces_table.rowCount()
                and 0 <= target_row < pieces_table.rowCount()
                and current_row < len(visible_row_indexes)
                and target_row < len(visible_row_indexes)
            )

        def refresh_piece_order_button_state():
            if move_piece_up_btn is None or move_piece_down_btn is None:
                return
            move_piece_up_btn.setEnabled(can_move_selected_piece(-1))
            move_piece_down_btn.setEnabled(can_move_selected_piece(1))
            move_piece_up_btn.setToolTip(
                "" if move_piece_up_btn.isEnabled() else "Seleccione una pieza que pueda subir."
            )
            move_piece_down_btn.setToolTip(
                "" if move_piece_down_btn.isEnabled() else "Seleccione una pieza que pueda bajar."
            )

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

        swap_button_width = _scaled_int(14, compact_scale, 11)
        swap_button_height = _scaled_int(20, compact_scale, 16)
        swap_button_font_size = _scaled_int(8, compact_scale, 6)

        def create_centered_swap_button(on_clicked, tooltip: str):
            container = QWidget()
            button_layout = QHBoxLayout(container)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(0)
            swap_button = QPushButton("↔", container)
            swap_button.setToolTip(tooltip)
            swap_button.setFixedSize(swap_button_width, swap_button_height)
            swap_button.setContentsMargins(0, 0, 0, 0)
            swap_button.setStyleSheet(
                "QPushButton {"
                f"font-size: {swap_button_font_size}px;"
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

        def swap_piece_dimensions(all_idx: int, visible_row: int | None = None):
            if all_idx < 0 or all_idx >= len(all_rows):
                return
            piece_row = all_rows[all_idx]
            piece_row["height"], piece_row["width"] = piece_row.get("width"), piece_row.get("height")
            mark_unsaved_changes()
            refresh_pieces_table()
            if visible_row is not None and pieces_table.rowCount() > 0:
                pieces_table.selectRow(max(0, min(visible_row, pieces_table.rowCount() - 1)))

        def swap_all_piece_dimensions():
            if not all_rows:
                return
            current_row = pieces_table.currentRow()
            for piece_row in all_rows:
                piece_row["height"], piece_row["width"] = piece_row.get("width"), piece_row.get("height")
            mark_unsaved_changes()
            refresh_pieces_table()
            if current_row >= 0 and pieces_table.rowCount() > 0:
                pieces_table.selectRow(max(0, min(current_row, pieces_table.rowCount() - 1)))

        def update_piece_flag(all_idx: int, field_name: str, state: int):
            if refreshing_pieces_table:
                return
            normalized_state = Qt.CheckState(state) == Qt.CheckState.Checked
            all_rows[all_idx][field_name] = normalized_state
            mark_unsaved_changes()
            if field_name == "en_juego":
                all_rows[all_idx]["observations"] = set_piece_en_juego_observation(
                    all_rows[all_idx].get("observations"),
                    normalized_state,
                )
                refresh_visible_piece_observations(all_idx)
                refresh_configure_en_juego_button_state()
                if not normalized_state:
                    prompt_clear_persistent_en_juego_info_if_needed()

        def has_configurable_en_juego_pieces() -> bool:
            return any(bool(row.get("en_juego", False)) for row in all_rows)

        def _config_section_has_data(value) -> bool:
            if isinstance(value, dict):
                return bool(value)
            if isinstance(value, (list, tuple, set)):
                return bool(value)
            return value not in (None, "", False)

        def has_persistent_en_juego_info() -> bool:
            if _config_section_has_data(config_data.get("en_juego_layout")):
                return True
            if _config_section_has_data(config_data.get("en_juego_composition")):
                return True
            if _config_section_has_data(config_data.get("en_juego_output_path")):
                return True
            settings_value = config_data.get("en_juego_settings")
            if isinstance(settings_value, dict):
                return _normalize_en_juego_settings(settings_value) != _default_en_juego_settings()
            return False

        def clear_persistent_en_juego_info():
            config_data["en_juego_layout"] = {}
            config_data["en_juego_composition"] = {}
            config_data.pop("en_juego_output_path", None)
            config_data["en_juego_settings"] = _default_en_juego_settings()
            mark_unsaved_changes()

        def prompt_clear_persistent_en_juego_info_if_needed():
            if has_configurable_en_juego_pieces() or not has_persistent_en_juego_info():
                return
            answer = QMessageBox.question(
                inspect_dialog,
                "Eliminar En-Juego",
                (
                    "Ya no hay piezas marcadas como En-Juego en este modulo.\n\n"
                    "Existe informacion guardada de En-Juego para este modulo. "
                    "Desea eliminar toda esa informacion?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer == QMessageBox.Yes:
                clear_persistent_en_juego_info()

        def refresh_configure_en_juego_button_state():
            if configure_en_juego_btn is None:
                return
            enabled = has_configurable_en_juego_pieces()
            configure_en_juego_btn.setEnabled(enabled)
            configure_en_juego_btn.setToolTip(
                "Configurar En Juego"
                if enabled
                else "Marque al menos una pieza en la columna En-Juego."
            )

        def refresh_visible_piece_observations(all_idx: int):
            if all_idx not in visible_row_indexes:
                return
            row_idx = visible_row_indexes.index(all_idx)
            if row_idx < 0 or row_idx >= pieces_table.rowCount():
                return

            from core.pgmx_processing import get_pgmx_program_dimension_notes

            piece_row = all_rows[all_idx]
            notes = get_pgmx_program_dimension_notes(
                self.project,
                [build_piece_from_row(piece_row)],
                module_path,
                cache=program_dimensions_cache,
            )
            program_dimension_note = notes[0] if notes else ""
            observations_text = build_piece_observations_display(
                piece_row.get("observations"),
                program_dimension_note,
            )
            invalid_slot_note = invalid_slot_message(get_invalid_slot_issues_for_row(piece_row))
            if invalid_slot_note:
                observations_text = "\n".join(
                    item for item in (observations_text, invalid_slot_note) if item
                )
            dimension_item = QTableWidgetItem(observations_text)
            dimension_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            dimension_item.setToolTip(observations_text)
            if observations_text:
                dimension_item.setForeground(QColor("#B71C1C"))
            pieces_table.setItem(row_idx, PIECES_COL_NOTES, dimension_item)

        def sync_en_juego_observations():
            for piece_row in all_rows:
                piece_row["observations"] = set_piece_en_juego_observation(
                    piece_row.get("observations"),
                    bool(piece_row.get("en_juego", False)),
                )

        def refresh_pieces_table():
            nonlocal refreshing_pieces_table
            from core.pgmx_processing import get_pgmx_program_dimension_notes

            for old_row in range(pieces_table.rowCount()):
                for old_column in range(pieces_table.columnCount()):
                    old_widget = pieces_table.cellWidget(old_row, old_column)
                    if old_widget is None:
                        continue
                    pieces_table.removeCellWidget(old_row, old_column)
                    old_widget.deleteLater()

            sync_program_dimensions_from_rows()

            visible_row_indexes.clear()
            filtered = []
            for idx, row_data in enumerate(all_rows):
                if self._is_valid_thickness_value(row_data.get("thickness")):
                    filtered.append((idx, row_data))

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
            invalid_slot_row_count = 0

            for row_idx, (all_idx, piece_row) in enumerate(filtered):
                source_value = str(piece_row.get("source", "")).strip()
                pgmx_status = self._get_pgmx_status(source_value, pgmx_names, pgmx_relpaths)
                program_dimension_note = filtered_program_notes[row_idx]
                invalid_slot_issues = get_invalid_slot_issues_for_row(piece_row)
                invalid_slot_note = invalid_slot_message(invalid_slot_issues)
                if invalid_slot_issues:
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
                program_filename = Path(source_value).name if source_value else "(ninguno)"
                program_prefix = "!" if invalid_slot_issues else pgmx_status
                program_item = QTableWidgetItem(f"{program_prefix} {program_filename}")
                if invalid_slot_issues:
                    program_item.setForeground(QColor("#E65100"))
                elif pgmx_status == "✓":
                    program_item.setForeground(QColor("#4CAF50"))
                else:
                    program_item.setForeground(QColor("#B71C1C"))
                program_tooltip = source_value or "(ninguno)"
                if invalid_slot_note:
                    program_tooltip = f"{program_tooltip}\n{invalid_slot_note}"
                program_item.setToolTip(program_tooltip)
                pieces_table.setItem(row_idx, PIECES_COL_PROGRAM, program_item)

                observations_text = build_piece_observations_display(
                    piece_row.get("observations"),
                    program_dimension_note,
                )
                if invalid_slot_note:
                    observations_text = "\n".join(
                        item for item in (observations_text, invalid_slot_note) if item
                    )
                dimension_item = QTableWidgetItem(observations_text)
                dimension_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                dimension_item.setToolTip(observations_text)
                if observations_text:
                    dimension_item.setForeground(QColor("#B71C1C"))
                pieces_table.setItem(row_idx, PIECES_COL_NOTES, dimension_item)

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

            if invalid_slot_row_count:
                pgmx_repair_warning_label.setText(
                    f"Se detectaron {invalid_slot_row_count} pieza(s) con ranuras no ejecutables. "
                    "Seleccione una fila y use 'Corregir PGMX' para sintetizar el archivo rotado."
                )
                pgmx_repair_warning_label.show()
            else:
                pgmx_repair_warning_label.clear()
                pgmx_repair_warning_label.hide()
            refreshing_pieces_table = False
            refresh_configure_en_juego_button_state()
            refresh_repair_pgmx_button_state()
            refresh_piece_order_button_state()

        refresh_pieces_table()

        header = pieces_table.horizontalHeader()
        auto_columns = {
            PIECES_COL_QUANTITY,
            PIECES_COL_HEIGHT,
            PIECES_COL_WIDTH,
            PIECES_COL_THICKNESS,
        }
        fixed_column_widths = {
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
        for column_idx in range(pieces_table.columnCount()):
            if column_idx in auto_columns:
                header.setSectionResizeMode(column_idx, QHeaderView.ResizeToContents)
            else:
                header.setSectionResizeMode(column_idx, QHeaderView.Fixed)
                pieces_table.setColumnWidth(column_idx, fixed_column_widths[column_idx])

        swap_all_dimensions_btn = QPushButton("↔", header)
        swap_all_dimensions_btn.setToolTip("Intercambiar alto y ancho de todas las piezas")
        swap_all_dimensions_btn.setFixedHeight(swap_button_height)
        swap_all_dimensions_btn.setContentsMargins(0, 0, 0, 0)
        swap_all_dimensions_btn.setStyleSheet(
            "QPushButton {"
            f"font-size: {swap_button_font_size}px;"
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
            button_width = max(9, min(swap_button_width, section_width - 2))
            button_height = max(16, min(swap_button_height, header.height() - 2))
            x_position = header.sectionViewportPosition(PIECES_COL_SWAP) + max(0, (section_width - button_width) // 2)
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
            max(320, min(sum(fixed_column_widths.values()) + 520, inspect_width - actions_column_reserved_width))
        )
        pieces_table.verticalHeader().setDefaultSectionSize(_scaled_int(30, compact_scale, 22))

        pieces_table.setAlternatingRowColors(True)
        pieces_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pieces_table.setSelectionBehavior(QTableWidget.SelectRows)
        pieces_table.setSelectionMode(QTableWidget.SingleSelection)

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
            selected_module.quantity = _parse_piece_quantity_value(module_quantity_field.text().strip(), default=1)
            sync_program_dimensions_from_rows()
            serialized_rows = []
            for row in all_rows:
                serialized_row = dict(row)
                serialized_row["quantity"] = _parse_piece_quantity_value(
                    serialized_row.get("quantity"),
                    default=1,
                )
                serialized_row["en_juego"] = bool(serialized_row.get("en_juego", False))
                include_in_sheet = bool(serialized_row.get("include_in_sheet", serialized_row.get("excel", False)))
                serialized_row["include_in_sheet"] = include_in_sheet
                serialized_row["grain_direction"] = normalize_piece_grain_direction(serialized_row.get("grain_direction"))
                serialized_row["observations"] = normalize_piece_observations(serialized_row.get("observations"))
                serialized_row.pop("excel", None)
                serialized_row.pop("quantity_step", None)
                serialized_rows.append(serialized_row)
            all_rows[:] = serialized_rows
            config_data["pieces"] = serialized_rows
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
                piece_dict.pop("excel", None)
                piece_dict.pop("observations", None)
                piece_dict.pop("quantity_step", None)
                
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

        if added_orphan_program_rows:
            persist_module_config()

        def move_selected_piece(delta: int) -> None:
            current_row = pieces_table.currentRow()
            target_row = current_row + delta
            if not can_move_selected_piece(delta):
                return
            current_all_idx = visible_row_indexes[current_row]
            target_all_idx = visible_row_indexes[target_row]
            if current_all_idx < 0 or target_all_idx < 0:
                return
            if current_all_idx >= len(all_rows) or target_all_idx >= len(all_rows):
                return

            all_rows[current_all_idx], all_rows[target_all_idx] = all_rows[target_all_idx], all_rows[current_all_idx]
            persist_module_config()
            refresh_pieces_table()
            select_visible_piece_by_all_index(target_all_idx, focus_selected_row=True)
            refresh_piece_order_button_state()

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
            _exec_centered(drawing_dialog, inspect_dialog)

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

        def remove_piece_drawing_file(piece_row, ignore_row_index: int | None = None):
            drawing_path = drawing_path_for_piece_row(piece_row)
            if not drawing_path.is_file():
                return
            for other_idx, other_row in enumerate(all_rows):
                if ignore_row_index is not None and other_idx == ignore_row_index:
                    continue
                if not str(other_row.get("source") or "").strip():
                    continue
                if drawing_path_for_piece_row(other_row) == drawing_path:
                    return
            try:
                drawing_path.unlink()
            except OSError:
                pass

        def refresh_piece_drawing_file(piece_row, row_index: int | None = None):
            if not str(piece_row.get("source") or "").strip():
                remove_piece_drawing_file(piece_row, ignore_row_index=row_index)
                return None

            drawing_path = ensure_piece_drawing(piece_row, force_regenerate=True, show_warning=False)
            if drawing_path is None or not drawing_path.is_file():
                remove_piece_drawing_file(piece_row, ignore_row_index=row_index)
                return None
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
            return

        def repair_selected_invalid_pgmx():
            current_row = pieces_table.currentRow()
            all_idx = selected_piece_all_index("Corregir PGMX")
            if all_idx is None:
                return

            piece_row = all_rows[all_idx]
            issues = get_invalid_slot_issues_for_row(piece_row)
            if not issues:
                QMessageBox.information(
                    inspect_dialog,
                    "Corregir PGMX",
                    "La pieza seleccionada no tiene ranuras no ejecutables detectadas.",
                )
                refresh_repair_pgmx_button_state()
                return

            from core.pgmx_processing import (
                repair_invalid_slot_machining_by_rotating_ccw,
                resolve_piece_program_path,
            )

            piece_obj = build_piece_from_row(piece_row)
            source_path = resolve_piece_program_path(self.project, piece_obj, module_path)
            if source_path is None:
                QMessageBox.warning(
                    inspect_dialog,
                    "Corregir PGMX",
                    "No se encontro el archivo PGMX asociado a la pieza seleccionada.",
                )
                return

            issue_names = ", ".join(
                str(issue.feature_name or issue.feature_id or "ranura")
                for issue in issues
            )
            answer = QMessageBox.question(
                inspect_dialog,
                "Corregir PGMX",
                (
                    "Se detecto una ranura no ejecutable por la herramienta seleccionada.\n\n"
                    f"Archivo: {source_path}\n"
                    f"Ranura(s): {issue_names}\n\n"
                    "El programa va a sintetizar el PGMX girandolo 90 grados antihorario "
                    "y va a sobreescribir el archivo original. Continuar?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

            try:
                result = repair_invalid_slot_machining_by_rotating_ccw(
                    self.project,
                    piece_obj,
                    module_path,
                )
            except Exception as exc:
                QMessageBox.critical(
                    inspect_dialog,
                    "Corregir PGMX",
                    f"No se pudo corregir el PGMX.\n\n{exc}",
                )
                clear_invalid_slot_cache()
                refresh_pieces_table()
                if current_row >= 0 and pieces_table.rowCount() > 0:
                    pieces_table.selectRow(max(0, min(current_row, pieces_table.rowCount() - 1)))
                return

            program_dimensions_cache.clear()
            clear_invalid_slot_cache()
            refresh_piece_drawing_file(piece_row, row_index=all_idx)
            persist_module_config()
            refresh_pieces_table()
            if current_row >= 0 and pieces_table.rowCount() > 0:
                pieces_table.selectRow(max(0, min(current_row, pieces_table.rowCount() - 1)))

            QMessageBox.information(
                inspect_dialog,
                "Corregir PGMX",
                (
                    "PGMX corregido correctamente.\n\n"
                    f"Archivo: {result.source_path}\n"
                    f"Dimensiones: {result.original_length:g} x {result.original_width:g} mm -> "
                    f"{result.rotated_length:g} x {result.rotated_width:g} mm"
                ),
            )

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
            editor_inline_button_width = MAIN_ACTION_BUTTON_WIDTH

            editor_layout = QVBoxLayout()
            content_layout = QHBoxLayout()
            content_layout.setSpacing(8)
            content_layout.setContentsMargins(0, 0, 0, 0)

            form_layout = QVBoxLayout()
            form_layout.setSpacing(6)
            form_layout.setContentsMargins(0, 0, 0, 0)

            id_field = QLineEdit(str(base_piece_row.get("id") or ""))
            name_field = QLineEdit(str(base_piece_row.get("name") or ""))
            base_piece_quantity = _parse_piece_quantity_value(base_piece_row.get("quantity"), default=1)
            qty_field = QLineEdit(str(base_piece_quantity))
            height_field = QLineEdit(str(base_piece_row.get("height") or ""))
            width_field = QLineEdit(str(base_piece_row.get("width") or ""))
            thickness_field = QLineEdit(str(base_piece_row.get("thickness") or ""))
            color_field = QLineEdit(str(base_piece_row.get("color") or ""))
            grain_field = QComboBox()
            source_field = QLineEdit(str(base_piece_row.get("source") or ""))
            id_field.setFixedWidth(_scaled_int(120, max(editor_scale, 0.82), 90))
            qty_field.setFixedWidth(_scaled_int(80, max(editor_scale, 0.82), 60))
            dimension_field_width = _scaled_int(90, max(editor_scale, 0.82), 68)
            color_grain_field_width = _scaled_int(104, max(editor_scale, 0.82), 82)
            top_fields_spacing = 8
            editor_inline_button_height = MAIN_ACTION_BUTTON_HEIGHT
            editor_field_block_spacing = 2
            editor_label_height = QLabel("X").sizeHint().height()
            editor_grid_row_height = editor_label_height + editor_field_block_spacing + editor_inline_button_height
            name_field.setFixedWidth((dimension_field_width * 3) + (top_fields_spacing * 2))
            height_field.setFixedWidth(dimension_field_width)
            width_field.setFixedWidth(dimension_field_width)
            thickness_field.setFixedWidth(dimension_field_width)
            color_field.setMinimumWidth(color_grain_field_width)
            grain_field.setMinimumWidth(color_grain_field_width)
            color_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grain_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            source_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            grain_field.addItem("Sin veta", "0")
            grain_field.addItem("Alto", "1")
            grain_field.addItem("Ancho", "2")
            current_grain_code = normalize_piece_grain_direction(base_piece_row.get("grain_direction"))
            if current_grain_code == "1":
                grain_field.setCurrentIndex(1)
            elif current_grain_code == "2":
                grain_field.setCurrentIndex(2)
            else:
                grain_field.setCurrentIndex(0)
            manual_piece_templates = _normalize_manual_piece_templates(
                _read_app_settings().get("manual_piece_templates")
            )
            template_combo = None
            if is_new_piece:
                template_combo = QComboBox()
                template_combo.addItem("(sin plantilla)", None)
                for template_entry in manual_piece_templates:
                    template_label = str(template_entry.get("name") or template_entry.get("id") or "pieza").strip()
                    template_id = str(template_entry.get("id") or "").strip()
                    if template_id and template_id != template_label:
                        template_label = f"{template_id} - {template_label}"
                    template_combo.addItem(template_label, template_entry)

            def build_labeled_field_widget(label_text: str, field: QWidget) -> QWidget:
                label = QLabel(label_text)
                label.setFixedHeight(editor_label_height)
                column_layout = QVBoxLayout()
                column_layout.setSpacing(editor_field_block_spacing)
                column_layout.setContentsMargins(0, 0, 0, 0)
                column_layout.addStretch(1)
                column_layout.addWidget(label)
                column_layout.addWidget(field)
                column_widget = QWidget()
                column_widget.setFixedHeight(editor_grid_row_height)
                column_widget.setLayout(column_layout)
                return column_widget

            top_fields_grid = QGridLayout()
            top_fields_grid.setHorizontalSpacing(top_fields_spacing)
            top_fields_grid.setVerticalSpacing(4)
            top_fields_grid.setContentsMargins(0, 0, 0, 0)

            if template_combo is not None:
                template_column = build_labeled_field_widget("Plantilla:", template_combo)
                top_fields_grid.addWidget(template_column, 0, 0, 1, 4)

            id_column = build_labeled_field_widget("ID:", id_field)
            name_column = build_labeled_field_widget("Nombre:", name_field)
            height_column = build_labeled_field_widget("Alto:", height_field)
            width_column = build_labeled_field_widget("Ancho:", width_field)
            thickness_column = build_labeled_field_widget("Espesor:", thickness_field)
            qty_column = build_labeled_field_widget("Cantidad:", qty_field)

            top_row_offset = 1 if template_combo is not None else 0
            top_fields_grid.addWidget(id_column, 0 + top_row_offset, 0)
            top_fields_grid.addWidget(name_column, 0 + top_row_offset, 1, 1, 3)
            top_fields_grid.addWidget(qty_column, 1 + top_row_offset, 0)
            top_fields_grid.addWidget(height_column, 1 + top_row_offset, 1)
            top_fields_grid.addWidget(width_column, 1 + top_row_offset, 2)
            top_fields_grid.addWidget(thickness_column, 1 + top_row_offset, 3)
            top_fields_grid.setColumnStretch(4, 1)
            for top_fields_row in range(5 if template_combo is not None else 4):
                top_fields_grid.setRowMinimumHeight(top_fields_row, editor_grid_row_height)

            form_layout.insertLayout(0, top_fields_grid)

            apply_color_btn = None
            if not is_new_piece:
                apply_color_btn = QPushButton("Cambiar")
                apply_color_btn.setFixedSize(editor_inline_button_width, editor_inline_button_height)
            select_color_btn = None
            if is_new_piece:
                select_color_btn = QPushButton("Seleccionar")
                select_color_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)

            color_column = build_labeled_field_widget("Color:", color_field)
            grain_column = build_labeled_field_widget("Veta:", grain_field)
            color_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grain_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            color_grain_row = QHBoxLayout()
            color_grain_row.setSpacing(top_fields_spacing)
            color_grain_row.setContentsMargins(0, 0, 0, 0)
            color_grain_row.addWidget(color_column, 1, Qt.AlignTop)
            color_grain_row.addWidget(grain_column, 1, Qt.AlignTop)
            if select_color_btn is not None:
                select_button_label = QLabel("")
                select_button_label.setFixedHeight(editor_label_height)
                select_button_column = QVBoxLayout()
                select_button_column.setSpacing(editor_field_block_spacing)
                select_button_column.setContentsMargins(0, 0, 0, 0)
                select_button_column.addWidget(select_button_label)
                select_button_column.addWidget(select_color_btn, 0, Qt.AlignRight)
                select_button_widget = QWidget()
                select_button_widget.setFixedWidth(editor_inline_button_width)
                select_button_widget.setFixedHeight(editor_grid_row_height)
                select_button_widget.setLayout(select_button_column)
                color_grain_row.addWidget(select_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
            if apply_color_btn is not None:
                change_button_label = QLabel("")
                change_button_label.setFixedHeight(editor_label_height)
                change_button_column = QVBoxLayout()
                change_button_column.setSpacing(editor_field_block_spacing)
                change_button_column.setContentsMargins(0, 0, 0, 0)
                change_button_column.addWidget(change_button_label)
                change_button_column.addWidget(apply_color_btn, 0, Qt.AlignRight)
                change_button_widget = QWidget()
                change_button_widget.setFixedWidth(editor_inline_button_width)
                change_button_widget.setFixedHeight(editor_grid_row_height)
                change_button_widget.setLayout(change_button_column)
                color_grain_row.addWidget(change_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
            color_grain_widget = QWidget()
            color_grain_widget.setFixedHeight(editor_grid_row_height)
            color_grain_widget.setLayout(color_grain_row)
            top_fields_grid.addWidget(color_grain_widget, 2 + top_row_offset, 0, 1, 4)

            source_field_widget = build_labeled_field_widget("Programa asociado (opcional):", source_field)
            source_field_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            select_source_btn = QPushButton("Seleccionar")
            select_source_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            edit_source_editor_btn = QPushButton("Editar\nPrograma")
            edit_source_editor_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            remove_source_editor_btn = QPushButton("Quitar\nPrograma")
            remove_source_editor_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            source_row = QHBoxLayout()
            source_row.setSpacing(top_fields_spacing)
            source_row.setContentsMargins(0, 0, 0, 0)
            source_row.addWidget(source_field_widget, 1, Qt.AlignTop)
            source_button_label = QLabel("")
            source_button_label.setFixedHeight(editor_label_height)
            source_buttons_column = QVBoxLayout()
            source_buttons_column.setSpacing(top_fields_spacing)
            source_buttons_column.setContentsMargins(0, 0, 0, 0)
            source_buttons_column.addWidget(select_source_btn)
            source_buttons_column.addWidget(edit_source_editor_btn)
            source_buttons_column.addWidget(remove_source_editor_btn)
            source_buttons_widget = QWidget()
            source_buttons_widget.setFixedWidth(editor_inline_button_width)
            source_buttons_widget.setLayout(source_buttons_column)
            source_button_column = QVBoxLayout()
            source_button_column.setSpacing(editor_field_block_spacing)
            source_button_column.setContentsMargins(0, 0, 0, 0)
            source_button_column.addWidget(source_button_label)
            source_button_column.addWidget(source_buttons_widget, 0, Qt.AlignRight)
            source_buttons_stack_height = (
                editor_label_height
                + editor_field_block_spacing
                + (MAIN_ACTION_BUTTON_HEIGHT * 3)
                + (top_fields_spacing * 2)
            )
            source_button_widget = QWidget()
            source_button_widget.setFixedWidth(editor_inline_button_width)
            source_button_widget.setFixedHeight(source_buttons_stack_height)
            source_button_widget.setLayout(source_button_column)
            source_row.addWidget(source_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
            source_widget = QWidget()
            source_widget.setFixedHeight(source_buttons_stack_height)
            source_widget.setLayout(source_row)
            top_fields_grid.addWidget(source_widget, 3 + top_row_offset, 0, 1, 4)

            form_panel = QWidget()
            form_panel_layout = QVBoxLayout()
            form_panel_layout.setContentsMargins(4, 0, 4, 0)
            form_panel_layout.setSpacing(0)
            form_panel_layout.addLayout(form_layout)
            form_panel.setLayout(form_panel_layout)
            form_panel_width_hint = form_panel.sizeHint().width()
            form_panel_height_hint = form_panel.minimumSizeHint().height()
            form_panel.setFixedWidth(form_panel_width_hint)
            form_panel.setFixedHeight(form_panel_height_hint)
            form_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            preview_panel_width = form_panel_width_hint
            preview_canvas_min_height = preview_panel_width

            preview_layout = QVBoxLayout()
            preview_layout.setSpacing(6)
            preview_layout.setContentsMargins(0, 0, 0, 0)
            preview_title_label = QLabel("Vista previa: (ninguno)")
            preview_title_label.setWordWrap(True)
            preview_layout.addWidget(preview_title_label)

            preview_svg = QSvgWidget()
            preview_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
            preview_svg.setFixedSize(preview_panel_width, preview_canvas_min_height)
            preview_svg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            preview_layout.addWidget(preview_svg, 1)

            preview_placeholder = QLabel("Sin dibujo disponible para esta pieza.")
            preview_placeholder.setAlignment(Qt.AlignCenter)
            preview_placeholder.setWordWrap(True)
            preview_placeholder.setStyleSheet("color: #666; border: 1px dashed #999; padding: 12px;")
            preview_placeholder.setFixedSize(preview_panel_width, preview_canvas_min_height)
            preview_layout.addWidget(preview_placeholder, 1)

            preview_panel = QWidget()
            preview_panel.setFixedWidth(preview_panel_width)
            preview_panel.setMinimumHeight(
                preview_title_label.sizeHint().height()
                + preview_layout.spacing()
                + preview_canvas_min_height
            )
            preview_panel.setLayout(preview_layout)

            def refresh_source_button_state():
                has_source = bool(source_field.text().strip())
                edit_source_editor_btn.setEnabled(has_source)
                remove_source_editor_btn.setEnabled(has_source)

            def build_editor_piece_row():
                piece_id = id_field.text().strip()
                source_value = source_field.text().strip()
                normalized_source = normalize_source_path(source_value) if source_value else ""
                updated_quantity = _parse_piece_quantity_value(qty_field.text().strip(), default=1)
                selected_color = color_field.text().strip()
                selected_thickness = parse_optional_piece_float(thickness_field.text())
                selected_grain = grain_field.currentData()
                if _board_color_has_no_grain(selected_color, selected_thickness):
                    selected_grain = PIECE_GRAIN_CODE_NONE

                updated_piece = dict(base_piece_row)
                updated_piece.update(
                    {
                        "id": piece_id,
                        "name": name_field.text().strip() or piece_id,
                        "quantity": updated_quantity,
                        "height": parse_optional_piece_float(height_field.text()),
                        "width": parse_optional_piece_float(width_field.text()),
                        "thickness": selected_thickness,
                        "color": selected_color or None,
                        "grain_direction": selected_grain,
                        "source": normalized_source,
                        "f6_source": infer_companion_f6_source(normalized_source),
                        "pgmx": self._get_pgmx_status(normalized_source, pgmx_names, pgmx_relpaths),
                        "program_width": base_piece_row.get("program_width") if normalized_source else None,
                        "program_height": base_piece_row.get("program_height") if normalized_source else None,
                        "program_thickness": base_piece_row.get("program_thickness") if normalized_source else None,
                        "en_juego": bool(base_piece_row.get("en_juego", False)),
                        "include_in_sheet": bool(base_piece_row.get("include_in_sheet", base_piece_row.get("excel", False))),
                    }
                )
                return updated_piece

            def set_editor_grain_to_no_grain_if_color_requires(color_value: str | None = None) -> bool:
                selected_color = color_field.text().strip() if color_value is None else str(color_value or "").strip()
                selected_thickness = parse_optional_piece_float(thickness_field.text())
                if not _board_color_has_no_grain(selected_color, selected_thickness):
                    return False
                if grain_field.currentData() != PIECE_GRAIN_CODE_NONE:
                    grain_field.setCurrentIndex(0)
                base_piece_row["grain_direction"] = PIECE_GRAIN_CODE_NONE
                return True

            def set_preview_canvas_height(canvas_height: int) -> None:
                normalized_height = max(int(round(canvas_height)), 1)
                preview_svg.setFixedSize(preview_panel_width, normalized_height)
                preview_placeholder.setFixedSize(preview_panel_width, normalized_height)
                preview_panel.setMinimumHeight(
                    preview_title_label.sizeHint().height()
                    + preview_layout.spacing()
                    + normalized_height
                )

            def refresh_piece_preview():
                refresh_source_button_state()
                preview_piece_row = build_editor_piece_row()
                preview_source = str(preview_piece_row.get("source") or "").strip()
                preview_title_label.setText(
                    f"Vista previa: {Path(preview_source).name if preview_source else '(ninguno)'}"
                )

                set_preview_canvas_height(preview_canvas_min_height)
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
                svg_default_size = preview_svg.renderer().defaultSize()
                if svg_default_size.width() > 0 and svg_default_size.height() > 0:
                    aspect_height = round(preview_panel_width * (svg_default_size.height() / svg_default_size.width()))
                    set_preview_canvas_height(aspect_height)
                preview_placeholder.hide()
                preview_svg.show()

            def refresh_piece_preview_and_layout(*_args):
                refresh_piece_preview()
                sync_editor_panel_heights()
                sync_editor_dialog_height()

            def sync_editor_panel_heights():
                editor_dialog.layout().activate()
                preview_height = max(preview_panel.sizeHint().height(), preview_panel.minimumSizeHint().height())
                right_panel_height = max(preview_height, right_panel.minimumSizeHint().height())
                right_panel.setFixedHeight(right_panel_height)
                right_panel.updateGeometry()
                content_panel.updateGeometry()

            def sync_editor_dialog_height():
                editor_dialog.layout().activate()
                target_height = max(editor_dialog.minimumHeight(), editor_dialog.sizeHint().height())
                available_editor_geometry = _window_available_geometry(editor_dialog)
                if available_editor_geometry is not None:
                    target_height = min(
                        target_height,
                        max(editor_dialog.minimumHeight(), int(available_editor_geometry.height() * 0.92)),
                    )
                if target_height > 0 and editor_dialog.height() != target_height:
                    editor_dialog.resize(editor_dialog.width(), target_height)

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
                refresh_piece_preview_and_layout()

            def edit_source_from_editor():
                from core.pgmx_processing import resolve_piece_program_path

                if not source_field.text().strip():
                    QMessageBox.warning(
                        editor_dialog,
                        "Editar programa",
                        "La pieza no tiene un programa asociado.",
                    )
                    return

                piece_obj = build_piece_from_row(build_editor_piece_row())
                source_path = resolve_piece_program_path(self.project, piece_obj, module_path)
                if source_path is None:
                    QMessageBox.warning(
                        editor_dialog,
                        "Editar programa",
                        "No se encontro el archivo PGMX asociado a la pieza seleccionada.",
                    )
                    return

                try:
                    os.startfile(str(source_path))
                except OSError as exc:
                    QMessageBox.critical(
                        editor_dialog,
                        "Editar programa",
                        (
                            "No se pudo abrir el programa asociado.\n\n"
                            "Verifique que Maestro este instalado o que los archivos PGMX "
                            "tengan una aplicacion predeterminada.\n\n"
                            f"{exc}"
                        ),
                    )

            def remove_source_from_editor():
                source_field.clear()
                base_piece_row["f6_source"] = None
                base_piece_row["program_width"] = None
                base_piece_row["program_height"] = None
                base_piece_row["program_thickness"] = None
                refresh_piece_preview_and_layout()

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
                if set_editor_grain_to_no_grain_if_color_requires(new_color_val):
                    base_piece_row["grain_direction"] = PIECE_GRAIN_CODE_NONE

            def select_color_from_boards_for_editor():
                piece_thickness = parse_optional_piece_float(thickness_field.text())
                available_colors = _configured_board_colors(piece_thickness=piece_thickness)
                if not available_colors:
                    thickness_label = (
                        f" para espesor {int(piece_thickness) if float(piece_thickness).is_integer() else piece_thickness} mm"
                        if piece_thickness is not None
                        else ""
                    )
                    QMessageBox.warning(
                        editor_dialog,
                        "Seleccionar color",
                        f"No hay colores disponibles en los tableros configurados{thickness_label}.",
                    )
                    return

                current_color = color_field.text().strip()
                selected_index = 0
                if current_color:
                    for color_index, color_value in enumerate(available_colors):
                        if color_value.strip().lower() == current_color.lower():
                            selected_index = color_index
                            break

                selected_color, ok = QInputDialog.getItem(
                    editor_dialog,
                    "Seleccionar color",
                    "Color:",
                    available_colors,
                    selected_index,
                    False,
                )
                if not ok:
                    return
                color_field.setText(str(selected_color or "").strip())
                set_editor_grain_to_no_grain_if_color_requires(selected_color)

            def apply_template_to_editor(template_entry: dict) -> None:
                normalized_template = _normalize_manual_piece_template_entry(template_entry)
                if normalized_template is None:
                    return

                base_piece_row["piece_type"] = normalized_template.get("piece_type")
                base_piece_row["f6_source"] = normalized_template.get("f6_source")
                base_piece_row["program_width"] = None
                base_piece_row["program_height"] = None
                base_piece_row["program_thickness"] = None

                id_field.setText(str(normalized_template.get("id") or ""))
                name_field.setText(str(normalized_template.get("name") or ""))
                qty_field.setText(str(_parse_piece_quantity_value(normalized_template.get("quantity"), default=1)))
                height_field.setText("" if normalized_template.get("height") is None else str(normalized_template.get("height")))
                width_field.setText("" if normalized_template.get("width") is None else str(normalized_template.get("width")))
                thickness_field.setText(
                    "" if normalized_template.get("thickness") is None else str(normalized_template.get("thickness"))
                )
                color_field.setText(str(normalized_template.get("color") or ""))
                previous_grain_block = grain_field.blockSignals(True)
                normalized_grain = normalize_piece_grain_direction(normalized_template.get("grain_direction"))
                if normalized_grain == "1":
                    grain_field.setCurrentIndex(1)
                elif normalized_grain == "2":
                    grain_field.setCurrentIndex(2)
                else:
                    grain_field.setCurrentIndex(0)
                grain_field.blockSignals(previous_grain_block)
                source_field.setText(str(normalized_template.get("source") or ""))
                refresh_piece_preview_and_layout()

            def on_template_changed(_index: int) -> None:
                if template_combo is None:
                    return
                selected_template = template_combo.currentData()
                if selected_template is None:
                    return
                apply_template_to_editor(selected_template)

            def save_piece_changes():
                piece_id = id_field.text().strip()
                if not piece_id:
                    QMessageBox.warning(editor_dialog, "Editar pieza", "El campo ID es obligatorio.")
                    return

                set_editor_grain_to_no_grain_if_color_requires()
                updated_piece = build_editor_piece_row()
                save_as_template = False
                template_selected = bool(template_combo is not None and template_combo.currentData() is not None)
                if is_new_piece and not template_selected:
                    piece_display_name = str(updated_piece.get("name") or updated_piece.get("id") or "pieza").strip()
                    template_answer = QMessageBox.question(
                        editor_dialog,
                        "Guardar plantilla",
                        f'¿Desea guardar la pieza "{piece_display_name}" como plantilla?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    save_as_template = template_answer == QMessageBox.Yes
                fallback_row = pieces_table.currentRow()
                previous_piece = None if is_new_piece or row_index is None else dict(all_rows[row_index])
                if is_new_piece:
                    all_rows.append(updated_piece)
                    target_row_index = len(all_rows) - 1
                else:
                    all_rows[row_index] = updated_piece
                    target_row_index = row_index

                persist_module_config()
                if previous_piece is not None and drawing_path_for_piece_row(previous_piece) != drawing_path_for_piece_row(updated_piece):
                    remove_piece_drawing_file(previous_piece, ignore_row_index=target_row_index)
                refresh_piece_drawing_file(updated_piece, row_index=target_row_index)
                if save_as_template:
                    try:
                        _save_manual_piece_template(updated_piece)
                    except Exception as exc:
                        QMessageBox.warning(
                            editor_dialog,
                            "Guardar plantilla",
                            f"No se pudo guardar la pieza como plantilla:\n{exc}",
                        )
                refresh_pieces_table()
                select_visible_piece_by_id(updated_piece["id"], fallback_row=fallback_row)
                editor_dialog.accept()

            editor_buttons = QHBoxLayout()
            editor_buttons.setContentsMargins(0, 0, 0, 0)
            editor_buttons.setSpacing(8)
            editor_buttons.addStretch(1)
            btn_save_piece = QPushButton("Aceptar")
            btn_cancel_piece = QPushButton("Cancelar")
            btn_save_piece.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            btn_cancel_piece.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            btn_save_piece.setDefault(True)
            btn_save_piece.setAutoDefault(True)
            btn_cancel_piece.setAutoDefault(False)
            for auxiliary_button in (
                apply_color_btn,
                select_color_btn,
                select_source_btn,
                edit_source_editor_btn,
                remove_source_editor_btn,
                btn_cancel_piece,
            ):
                if auxiliary_button is not None:
                    auxiliary_button.setDefault(False)
                    auxiliary_button.setAutoDefault(False)
                    auxiliary_button.setFocusPolicy(Qt.NoFocus)
            btn_save_piece.clicked.connect(save_piece_changes)
            btn_cancel_piece.clicked.connect(editor_dialog.reject)
            editor_buttons.addWidget(btn_save_piece)
            editor_buttons.addWidget(btn_cancel_piece)

            buttons_widget = QWidget()
            buttons_widget.setFixedWidth(form_panel_width_hint)
            buttons_widget.setContentsMargins(0, 0, 0, 0)
            buttons_widget.setLayout(editor_buttons)
            buttons_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            def sync_editor_grainless_color_rule():
                if set_editor_grain_to_no_grain_if_color_requires():
                    refresh_piece_preview_and_layout()

            editor_buttons_top_gap = _scaled_int(155, max(editor_scale, 0.82), 96)
            right_panel = QWidget()
            right_panel.setFixedWidth(form_panel_width_hint)
            right_panel_layout = QVBoxLayout()
            right_panel_layout.setContentsMargins(0, 0, 0, 0)
            right_panel_layout.setSpacing(8)
            right_panel_layout.addWidget(form_panel, 0, Qt.AlignTop | Qt.AlignLeft)
            right_panel_layout.addSpacing(editor_buttons_top_gap)
            right_panel_layout.addWidget(buttons_widget, 0, Qt.AlignTop | Qt.AlignRight)
            right_panel_layout.addStretch(1)
            right_panel.setLayout(right_panel_layout)

            content_layout.addWidget(preview_panel, 0, Qt.AlignTop | Qt.AlignLeft)
            content_layout.addWidget(right_panel, 0, Qt.AlignTop | Qt.AlignLeft)
            content_panel = QWidget()
            content_panel.setLayout(content_layout)
            editor_layout.addWidget(content_panel, 0)

            select_source_btn.clicked.connect(select_source_from_editor)
            edit_source_editor_btn.clicked.connect(edit_source_from_editor)
            remove_source_editor_btn.clicked.connect(remove_source_from_editor)
            color_field.editingFinished.connect(sync_editor_grainless_color_rule)
            thickness_field.editingFinished.connect(sync_editor_grainless_color_rule)
            source_field.textChanged.connect(lambda *_: refresh_source_button_state())
            source_field.editingFinished.connect(refresh_piece_preview_and_layout)
            grain_field.currentIndexChanged.connect(refresh_piece_preview_and_layout)
            if template_combo is not None:
                template_combo.currentIndexChanged.connect(on_template_changed)
            if select_color_btn is not None:
                select_color_btn.clicked.connect(select_color_from_boards_for_editor)
            if apply_color_btn is not None:
                apply_color_btn.clicked.connect(apply_color_from_editor)
            editor_dialog.setLayout(editor_layout)
            refresh_piece_preview_and_layout()
            editor_dialog.layout().activate()
            compact_editor_width = editor_dialog.sizeHint().width()
            compact_editor_height = editor_dialog.minimumSizeHint().height()
            available_editor_geometry = _window_available_geometry(editor_dialog)
            if available_editor_geometry is not None:
                compact_editor_width = min(
                    compact_editor_width,
                    max(420, int(available_editor_geometry.width() * 0.94)),
                )
            editor_dialog.setMinimumHeight(compact_editor_height)
            editor_dialog.resize(compact_editor_width, compact_editor_height)
            _exec_centered(editor_dialog, inspect_dialog)

        def add_manual_piece():
            open_piece_editor()

        def edit_selected_piece():
            all_idx = selected_piece_all_index("Editar pieza")
            if all_idx is None:
                return
            open_piece_editor(all_rows[all_idx], row_index=all_idx)

        def edit_piece_from_table_double_click(row: int, _column: int):
            if row < 0 or row >= pieces_table.rowCount():
                return
            pieces_table.selectRow(row)
            edit_selected_piece()

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
            remove_piece_drawing_file(piece_row)
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
            _exec_centered(scope_box, inspect_dialog)
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
            if _exec_centered(color_dialog, inspect_dialog) != QDialog.Accepted or colors_list.currentItem() is None:
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
            new_color_has_no_grain = _board_color_has_no_grain(new_color_val, piece_thickness)

            def apply_selected_color_to_row(row: dict) -> None:
                row["color"] = new_color_val
                if new_color_has_no_grain:
                    row["grain_direction"] = PIECE_GRAIN_CODE_NONE

            selected_piece_id = ""
            fallback_row = pieces_table.currentRow()
            if target_row_index is not None and 0 <= target_row_index < len(all_rows):
                selected_piece_id = str(all_rows[target_row_index].get("id") or "").strip()

            if scope == "piece":
                if target_row_index is None or target_row_index >= len(all_rows):
                    return None
                apply_selected_color_to_row(all_rows[target_row_index])
                persist_module_config()

            elif scope == "module":
                for row in all_rows:
                    if str(row.get("color") or "") == current_color:
                        apply_selected_color_to_row(row)
                persist_module_config()

            else:
                for row in all_rows:
                    if str(row.get("color") or "") == current_color:
                        apply_selected_color_to_row(row)
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
                            if new_color_has_no_grain:
                                piece.grain_direction = PIECE_GRAIN_CODE_NONE

                    other_config_path = self._module_config_path(mod)
                    if not other_config_path.exists():
                        continue
                    try:
                        other_config = json.loads(other_config_path.read_text(encoding="utf-8"))
                        changed = False
                        for row in other_config.get("pieces", []):
                            if str(row.get("color") or "") == current_color:
                                apply_selected_color_to_row(row)
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

            app_cut_settings = _read_app_settings()
            scene_padding_mm = 400.0
            snap_distance_mm = 18.0
            en_juego_settings = dict(_normalize_en_juego_settings(config_data.get("en_juego_settings")))
            en_juego_saw_kerf_mm = 0.0
            available_cutting_tools = _load_en_juego_cutting_tools()
            en_juego_material_thickness_mm = max(
                (
                    _coerce_setting_number(row.get("thickness"), 0.0, minimum=0.0)
                    for row in en_juego_rows
                ),
                default=0.0,
            )

            def effective_piece_spacing_mm() -> float:
                try:
                    cut_mode = "nesting" if nesting_cut_radio.isChecked() else "manual"
                except NameError:
                    cut_mode = _normalize_en_juego_cut_mode(en_juego_settings.get("cut_mode"))
                if cut_mode == "manual":
                    return max(
                        0.0,
                        _coerce_setting_number(app_cut_settings.get("cut_squaring_allowance"), 10.0, minimum=0.0)
                        + _coerce_setting_number(app_cut_settings.get("cut_saw_kerf"), 4.0, minimum=0.0),
                    )

                return _resolve_en_juego_nesting_spacing_mm(
                    en_juego_settings,
                    material_thickness_mm=en_juego_material_thickness_mm,
                )

            preview_gap_mm = effective_piece_spacing_mm()
            saved_layout = config_data.get("en_juego_layout", {})
            if not isinstance(saved_layout, dict):
                saved_layout = {}
            auto_spacing_adjustment_state = {"active": False}

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
                1320,
                760,
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
            left_panel = QWidget()
            left_panel_layout = QVBoxLayout()
            left_panel_layout.setContentsMargins(0, 0, 0, 0)
            left_panel_layout.setSpacing(8)
            pieces_list = QListWidget()
            left_panel_width = _scaled_int(250, max(config_scale, 0.82), 180)
            pieces_list.setFixedWidth(left_panel_width)
            pieces_list.setFixedHeight(_scaled_int(220, max(config_scale, 0.82), 170))
            left_panel_layout.addWidget(pieces_list, 0)

            origin_group = QGroupBox("Origen")
            origin_layout = QGridLayout()
            origin_layout.setContentsMargins(8, 8, 8, 8)
            origin_layout.setHorizontalSpacing(8)
            origin_layout.setVerticalSpacing(6)
            origin_x_field = QLineEdit(str(en_juego_settings.get("origin_x", 0)))
            origin_y_field = QLineEdit(str(en_juego_settings.get("origin_y", 0)))
            origin_z_field = QLineEdit(str(en_juego_settings.get("origin_z", 0)))
            origin_layout.addWidget(QLabel("Origen X"), 0, 0)
            origin_layout.addWidget(origin_x_field, 0, 1)
            origin_layout.addWidget(QLabel("Origen Y"), 1, 0)
            origin_layout.addWidget(origin_y_field, 1, 1)
            origin_layout.addWidget(QLabel("Origen Z"), 2, 0)
            origin_layout.addWidget(origin_z_field, 2, 1)
            origin_group.setLayout(origin_layout)

            operation_order_group = QGroupBox("Orden")
            operation_order_layout = QVBoxLayout()
            operation_order_layout.setContentsMargins(8, 8, 8, 8)
            operation_order_layout.setSpacing(6)
            divide_then_square_radio = QRadioButton("Dividir -> Escuadrar")
            square_then_divide_radio = QRadioButton("Escuadrar -> Dividir")
            current_operation_order = _normalize_en_juego_operation_order(
                en_juego_settings.get("division_squaring_order")
            )
            divide_then_square_radio.setChecked(current_operation_order == "division_then_squaring")
            square_then_divide_radio.setChecked(current_operation_order == "squaring_then_division")
            operation_order_layout.addWidget(divide_then_square_radio)
            operation_order_layout.addWidget(square_then_divide_radio)
            operation_order_group.setLayout(operation_order_layout)

            options_group = QGroupBox("Opciones")
            options_group.setFixedWidth(left_panel_width)
            options_layout = QVBoxLayout()
            options_layout.setContentsMargins(8, 8, 8, 8)
            options_layout.setSpacing(8)
            manual_cut_radio = QRadioButton("Corte Manual")
            nesting_cut_radio = QRadioButton("Corte Nesting")
            manual_cut_radio.setChecked(_normalize_en_juego_cut_mode(en_juego_settings.get("cut_mode")) == "manual")
            nesting_cut_radio.setChecked(not manual_cut_radio.isChecked())
            spacing_hint_label = QLabel()
            spacing_hint_label.setWordWrap(True)
            configure_division_btn = QPushButton("Configurar\nDivisiones")
            configure_squaring_btn = QPushButton("Configurar\nEscuadrado")
            configure_division_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            configure_squaring_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            configure_buttons_row = QHBoxLayout()
            configure_buttons_row.setContentsMargins(0, 0, 0, 0)
            configure_buttons_row.setSpacing(8)
            configure_buttons_row.addStretch(1)
            configure_buttons_row.addWidget(configure_squaring_btn)
            configure_buttons_row.addWidget(configure_division_btn)
            configure_buttons_row.addStretch(1)
            options_layout.addWidget(manual_cut_radio)
            options_layout.addWidget(nesting_cut_radio)
            options_layout.addWidget(spacing_hint_label)
            options_layout.addWidget(origin_group)
            options_layout.addWidget(operation_order_group)
            options_layout.addLayout(configure_buttons_row)
            options_group.setLayout(options_layout)
            left_panel_layout.addWidget(options_group, 0)
            left_panel_layout.addStretch(1)
            left_panel.setFixedWidth(left_panel_width)
            left_panel.setLayout(left_panel_layout)
            content_layout.addWidget(left_panel, 0, Qt.AlignTop)

            scene = QGraphicsScene(config_dialog)
            view = EnJuegoGraphicsView(scene)
            view_panel = QWidget()
            view_panel_layout = QVBoxLayout()
            view_panel_layout.setContentsMargins(0, 0, 0, 0)
            view_panel_layout.setSpacing(8)
            view_panel_layout.addWidget(view, 1)
            view_panel.setLayout(view_panel_layout)
            content_layout.addWidget(view_panel, 1)
            main_layout.addLayout(content_layout)

            def safe_float(value):
                if value is None:
                    return None
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

            def en_juego_quantity(piece_row: dict) -> int:
                return _parse_piece_quantity_value(piece_row.get("quantity"), default=1)

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

            def draw_chevron_marker(rect_item, marker, piece_height_mm: float, color: str, offset_mm: float = 0.0):
                if marker is None:
                    return
                dx = float(getattr(marker, "dx", 0.0) or 0.0)
                dy = float(getattr(marker, "dy", 0.0) or 0.0)
                length = (dx * dx + dy * dy) ** 0.5
                if length <= 1e-9:
                    return
                unit_x = dx / length
                unit_y = -dy / length

                anchor_x = float(getattr(marker, "x", 0.0) or 0.0)
                anchor_y = to_scene_y(float(getattr(marker, "y", 0.0) or 0.0), piece_height_mm)
                if abs(offset_mm) > 1e-9:
                    anchor_x += (-unit_y) * offset_mm
                    anchor_y += unit_x * offset_mm

                chevron_length = 4.0
                chevron_half_width = 2.25
                back_x = anchor_x - (unit_x * chevron_length)
                back_y = anchor_y - (unit_y * chevron_length)
                left_x = back_x + ((-unit_y) * chevron_half_width)
                left_y = back_y + (unit_x * chevron_half_width)
                right_x = back_x - ((-unit_y) * chevron_half_width)
                right_y = back_y - (unit_x * chevron_half_width)

                left_segment = QGraphicsLineItem(left_x, left_y, anchor_x, anchor_y, rect_item)
                left_segment.setPen(make_pen(color, 1.3))
                left_segment.setAcceptedMouseButtons(QtCoreQt.NoButton)

                right_segment = QGraphicsLineItem(right_x, right_y, anchor_x, anchor_y, rect_item)
                right_segment.setPen(make_pen(color, 1.3))
                right_segment.setAcceptedMouseButtons(QtCoreQt.NoButton)

            def draw_entry_marker(rect_item, entry_marker, piece_height_mm: float, color: str):
                draw_chevron_marker(rect_item, entry_marker, piece_height_mm, color)

            def draw_grain_hatching(rect_item, piece_row: dict, width_mm: float, height_mm: float):
                from core.pgmx_processing import resolve_piece_grain_hatch_axis

                hatch_axis = resolve_piece_grain_hatch_axis(
                    piece_row.get("grain_direction"),
                    safe_float(piece_row.get("width")),
                    safe_float(piece_row.get("height")),
                    width_mm,
                    height_mm,
                )
                if hatch_axis not in {"vertical", "horizontal"}:
                    return

                hatch_color = "#D8D2C7"
                hatch_spacing = 10.0
                hatch_margin = 0.0
                hatch_pen = make_pen(hatch_color, 0.7)

                if hatch_axis == "vertical":
                    current_x = hatch_margin
                    while current_x <= (width_mm - hatch_margin):
                        hatch_line = QGraphicsLineItem(current_x, hatch_margin, current_x, height_mm - hatch_margin, rect_item)
                        hatch_line.setPen(hatch_pen)
                        hatch_line.setZValue(-1.0)
                        hatch_line.setAcceptedMouseButtons(QtCoreQt.NoButton)
                        current_x += hatch_spacing
                    return

                current_y = hatch_margin
                while current_y <= (height_mm - hatch_margin):
                    hatch_line = QGraphicsLineItem(hatch_margin, current_y, width_mm - hatch_margin, current_y, rect_item)
                    hatch_line.setPen(hatch_pen)
                    hatch_line.setZValue(-1.0)
                    hatch_line.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    current_y += hatch_spacing

            item_by_instance_id: dict[str, object] = {}
            dimension_annotation_items = []
            dimension_annotation_state = {"ready": False}
            dimension_tolerance_mm = 0.1

            def nominal_scene_rect(scene_item):
                return scene_item.mapRectToScene(scene_item.rect())

            def clear_dimension_annotations():
                for annotation_item in dimension_annotation_items:
                    scene.removeItem(annotation_item)
                dimension_annotation_items.clear()

            def add_dimension_annotation_item(annotation_item, *, interactive: bool = False, z_value: float = 20.0):
                annotation_item.setAcceptedMouseButtons(
                    QtCoreQt.LeftButton if interactive else QtCoreQt.NoButton
                )
                annotation_item.setZValue(z_value)
                scene.addItem(annotation_item)
                dimension_annotation_items.append(annotation_item)
                return annotation_item

            class DimensionLabelTextItem(QGraphicsSimpleTextItem):
                def __init__(self, text: str, on_click):
                    super().__init__(text)
                    self._on_click = on_click

                def mousePressEvent(self, event):
                    if self._on_click is not None:
                        self._on_click()
                        event.accept()
                        return
                    super().mousePressEvent(event)

            class DimensionLabelBackgroundItem(QGraphicsRectItem):
                def __init__(self, x: float, y: float, width: float, height: float, on_click):
                    super().__init__(x, y, width, height)
                    self._on_click = on_click

                def mousePressEvent(self, event):
                    if self._on_click is not None:
                        self._on_click()
                        event.accept()
                        return
                    super().mousePressEvent(event)

            def add_dimension_line_item(x1: float, y1: float, x2: float, y2: float, *, dashed: bool = False):
                line_item = QGraphicsLineItem(float(x1), float(y1), float(x2), float(y2))
                line_item.setPen(make_pen("#7A4E00", 1.0, dashed=dashed))
                return add_dimension_annotation_item(line_item)

            def move_dimension_target(target_key: str, axis: str, delta_mm: float):
                if abs(delta_mm) <= dimension_tolerance_mm:
                    return
                target_item = item_by_instance_id.get(target_key)
                if target_item is None:
                    return
                current_pos = target_item.pos()
                auto_spacing_adjustment_state["active"] = True
                try:
                    if axis == "x":
                        target_item.setPos(current_pos.x() + delta_mm, current_pos.y())
                    else:
                        target_item.setPos(current_pos.x(), current_pos.y() + delta_mm)
                finally:
                    auto_spacing_adjustment_state["active"] = False
                update_dimension_annotations()
                update_scene_bounds()
                scene.clearSelection()
                target_item.setSelected(True)

            def edit_dimension_value(
                current_value_mm: float,
                *,
                target_key: str,
                axis: str,
                minimum_value_mm: float = 0.0,
            ):
                current_abs_value = round(abs(float(current_value_mm)), 1)
                new_value, ok = QInputDialog.getDouble(
                    config_dialog,
                    "Editar cota",
                    "Medida en mm:",
                    current_abs_value,
                    float(minimum_value_mm),
                    100000.0,
                    1,
                )
                if not ok:
                    return
                direction = -1.0 if current_value_mm < 0 else 1.0
                desired_value = direction * float(new_value)
                move_dimension_target(target_key, axis, desired_value - float(current_value_mm))

            def add_dimension_text(text: str, x: float, y: float, on_edit=None):
                text_item = DimensionLabelTextItem(text, on_edit)
                text_item.setBrush(QBrush(QColorGui("#2A2418")))
                text_item.setScale(1.35)
                bounds = text_item.boundingRect()
                text_width = bounds.width() * text_item.scale()
                text_height = bounds.height() * text_item.scale()
                background_item = DimensionLabelBackgroundItem(
                    x - (text_width / 2.0) - 3.0,
                    y - (text_height / 2.0) - 2.0,
                    text_width + 6.0,
                    text_height + 4.0,
                    on_edit,
                )
                background_item.setPen(QPen(QtCoreQt.NoPen))
                background_item.setBrush(QBrush(QColorGui("#FFFDF8")))
                add_dimension_annotation_item(background_item, interactive=on_edit is not None, z_value=19.5)
                text_item.setPos(x - (text_width / 2.0), y - (text_height / 2.0))
                text_item.setToolTip("Editar medida")
                background_item.setToolTip("Editar medida")
                return add_dimension_annotation_item(text_item, interactive=on_edit is not None)

            def dimension_label(value_mm: float) -> str:
                return f"{_compact_number(round(abs(float(value_mm)), 1))} mm"

            def add_horizontal_dimension(
                x1: float,
                x2: float,
                y: float,
                label_value: float,
                *,
                target_key: str | None = None,
                minimum_value_mm: float = 0.0,
            ):
                if abs(x2 - x1) <= dimension_tolerance_mm:
                    return
                tick = 7.0
                add_dimension_line_item(x1, y, x2, y)
                add_dimension_line_item(x1, y - tick, x1, y + tick)
                add_dimension_line_item(x2, y - tick, x2, y + tick)
                on_edit = None
                if target_key:
                    on_edit = lambda value=label_value, key=target_key, minimum=minimum_value_mm: edit_dimension_value(
                        value,
                        target_key=key,
                        axis="x",
                        minimum_value_mm=minimum,
                    )
                add_dimension_text(dimension_label(label_value), (x1 + x2) / 2.0, y - 18.0, on_edit)

            def add_vertical_dimension(
                x: float,
                y1: float,
                y2: float,
                label_value: float,
                *,
                target_key: str | None = None,
                minimum_value_mm: float = 0.0,
            ):
                if abs(y2 - y1) <= dimension_tolerance_mm:
                    return
                tick = 7.0
                add_dimension_line_item(x, y1, x, y2)
                add_dimension_line_item(x - tick, y1, x + tick, y1)
                add_dimension_line_item(x - tick, y2, x + tick, y2)
                on_edit = None
                if target_key:
                    on_edit = lambda value=label_value, key=target_key, minimum=minimum_value_mm: edit_dimension_value(
                        value,
                        target_key=key,
                        axis="y",
                        minimum_value_mm=minimum,
                    )
                add_dimension_text(dimension_label(label_value), x + 22.0, (y1 + y2) / 2.0, on_edit)

            def vertical_overlap(rect_a, rect_b) -> float:
                return min(rect_a.bottom(), rect_b.bottom()) - max(rect_a.top(), rect_b.top())

            def horizontal_overlap(rect_a, rect_b) -> float:
                return min(rect_a.right(), rect_b.right()) - max(rect_a.left(), rect_b.left())

            def has_horizontal_blocker(rect_entries, left_key, right_key, left_rect, right_rect) -> bool:
                overlap_top = max(left_rect.top(), right_rect.top())
                overlap_bottom = min(left_rect.bottom(), right_rect.bottom())
                for candidate_key, _, candidate_rect in rect_entries:
                    if candidate_key in {left_key, right_key}:
                        continue
                    if min(candidate_rect.bottom(), overlap_bottom) - max(candidate_rect.top(), overlap_top) <= dimension_tolerance_mm:
                        continue
                    if (
                        candidate_rect.left() >= left_rect.right() - dimension_tolerance_mm
                        and candidate_rect.right() <= right_rect.left() + dimension_tolerance_mm
                    ):
                        return True
                return False

            def has_vertical_blocker(rect_entries, upper_key, lower_key, upper_rect, lower_rect) -> bool:
                overlap_left = max(upper_rect.left(), lower_rect.left())
                overlap_right = min(upper_rect.right(), lower_rect.right())
                for candidate_key, _, candidate_rect in rect_entries:
                    if candidate_key in {upper_key, lower_key}:
                        continue
                    if min(candidate_rect.right(), overlap_right) - max(candidate_rect.left(), overlap_left) <= dimension_tolerance_mm:
                        continue
                    if (
                        candidate_rect.top() >= upper_rect.bottom() - dimension_tolerance_mm
                        and candidate_rect.bottom() <= lower_rect.top() + dimension_tolerance_mm
                    ):
                        return True
                return False

            def dimension_x_near_inner_edge(rect, *, left_side_piece: bool) -> float:
                margin = 12.0
                if rect.width() <= margin * 2.0:
                    return (rect.left() + rect.right()) / 2.0
                desired_x = rect.right() - 28.0 if left_side_piece else rect.left() + 28.0
                return max(rect.left() + margin, min(rect.right() - margin, desired_x))

            def add_vertical_edge_offsets(left_rect, right_rect, right_key: str):
                gap = right_rect.left() - left_rect.right()
                if gap < -dimension_tolerance_mm:
                    return
                top_offset = right_rect.top() - left_rect.top()
                bottom_offset = right_rect.bottom() - left_rect.bottom()
                if abs(top_offset) > dimension_tolerance_mm:
                    lower_top_rect = left_rect if left_rect.top() > right_rect.top() else right_rect
                    add_vertical_dimension(
                        dimension_x_near_inner_edge(lower_top_rect, left_side_piece=lower_top_rect is left_rect),
                        left_rect.top(),
                        right_rect.top(),
                        top_offset,
                        target_key=right_key,
                    )
                if (
                    abs(bottom_offset) > dimension_tolerance_mm
                    and abs(abs(bottom_offset) - abs(top_offset)) > dimension_tolerance_mm
                ):
                    higher_bottom_rect = left_rect if left_rect.bottom() < right_rect.bottom() else right_rect
                    add_vertical_dimension(
                        dimension_x_near_inner_edge(
                            higher_bottom_rect,
                            left_side_piece=higher_bottom_rect is left_rect,
                        ),
                        left_rect.bottom(),
                        right_rect.bottom(),
                        bottom_offset,
                        target_key=right_key,
                    )

            def add_horizontal_edge_offsets(upper_rect, lower_rect, lower_key: str):
                gap = lower_rect.top() - upper_rect.bottom()
                if gap < -dimension_tolerance_mm:
                    return
                dimension_y = upper_rect.bottom() + (max(gap, 0.0) / 2.0)
                left_offset = lower_rect.left() - upper_rect.left()
                right_offset = lower_rect.right() - upper_rect.right()
                if abs(left_offset) > dimension_tolerance_mm:
                    add_horizontal_dimension(
                        upper_rect.left(),
                        lower_rect.left(),
                        dimension_y,
                        left_offset,
                        target_key=lower_key,
                    )
                if (
                    abs(right_offset) > dimension_tolerance_mm
                    and abs(abs(right_offset) - abs(left_offset)) > dimension_tolerance_mm
                ):
                    add_horizontal_dimension(
                        upper_rect.right(),
                        lower_rect.right(),
                        dimension_y,
                        right_offset,
                        target_key=lower_key,
                    )

            def update_dimension_annotations():
                if not dimension_annotation_state["ready"]:
                    return
                clear_dimension_annotations()
                rect_entries = [
                    (instance_key, scene_item, nominal_scene_rect(scene_item))
                    for instance_key, scene_item in item_by_instance_id.items()
                ]
                if len(rect_entries) < 2:
                    return
                spacing_mm = effective_piece_spacing_mm()
                for current_index, (first_key, _, first_rect) in enumerate(rect_entries):
                    for second_key, _, second_rect in rect_entries[current_index + 1 :]:
                        if vertical_overlap(first_rect, second_rect) > dimension_tolerance_mm:
                            left_key, left_rect, right_key, right_rect = (
                                (first_key, first_rect, second_key, second_rect)
                                if first_rect.right() <= second_rect.left()
                                else (second_key, second_rect, first_key, first_rect)
                            )
                            gap = right_rect.left() - left_rect.right()
                            if gap >= -dimension_tolerance_mm and not has_horizontal_blocker(
                                rect_entries,
                                left_key,
                                right_key,
                                left_rect,
                                right_rect,
                            ):
                                overlap_top = max(left_rect.top(), right_rect.top())
                                overlap_bottom = min(left_rect.bottom(), right_rect.bottom())
                                if gap > spacing_mm + dimension_tolerance_mm:
                                    add_horizontal_dimension(
                                        left_rect.right(),
                                        right_rect.left(),
                                        (overlap_top + overlap_bottom) / 2.0,
                                        gap,
                                        target_key=right_key,
                                        minimum_value_mm=spacing_mm,
                                    )
                                add_vertical_edge_offsets(left_rect, right_rect, right_key)

                        if horizontal_overlap(first_rect, second_rect) > dimension_tolerance_mm:
                            upper_key, upper_rect, lower_key, lower_rect = (
                                (first_key, first_rect, second_key, second_rect)
                                if first_rect.bottom() <= second_rect.top()
                                else (second_key, second_rect, first_key, first_rect)
                            )
                            gap = lower_rect.top() - upper_rect.bottom()
                            if gap >= -dimension_tolerance_mm and not has_vertical_blocker(
                                rect_entries,
                                upper_key,
                                lower_key,
                                upper_rect,
                                lower_rect,
                            ):
                                overlap_left = max(upper_rect.left(), lower_rect.left())
                                overlap_right = min(upper_rect.right(), lower_rect.right())
                                if gap > spacing_mm + dimension_tolerance_mm:
                                    add_vertical_dimension(
                                        (overlap_left + overlap_right) / 2.0,
                                        upper_rect.bottom(),
                                        lower_rect.top(),
                                        gap,
                                        target_key=lower_key,
                                        minimum_value_mm=spacing_mm,
                                    )
                                add_horizontal_edge_offsets(upper_rect, lower_rect, lower_key)

            class EnJuegoPieceItem(QGraphicsRectItem):
                def itemChange(self, change, value):
                    if change == QGraphicsItem.ItemPositionChange and auto_spacing_adjustment_state["active"]:
                        return QPointF(value)

                    if change == QGraphicsItem.ItemPositionChange and self.scene() is not None:
                        proposed_pos = QPointF(value)
                        current_pos = self.pos()
                        current_rect = nominal_scene_rect(self)
                        delta_x = proposed_pos.x() - current_pos.x()
                        delta_y = proposed_pos.y() - current_pos.y()
                        candidate_rect = current_rect.translated(delta_x, delta_y)

                        target_xs = []
                        target_ys = []
                        for other_item in self.scene().items():
                            if other_item is self or not str(other_item.data(0) or "").strip():
                                continue
                            other_rect = nominal_scene_rect(other_item)
                            spacing_mm = effective_piece_spacing_mm()
                            target_xs.extend([
                                other_rect.left() - candidate_rect.left(),
                                other_rect.right() - candidate_rect.right(),
                                other_rect.right() + spacing_mm - candidate_rect.left(),
                                other_rect.left() - spacing_mm - candidate_rect.right(),
                            ])
                            target_ys.extend([
                                other_rect.top() - candidate_rect.top(),
                                other_rect.bottom() - candidate_rect.bottom(),
                                other_rect.bottom() + spacing_mm - candidate_rect.top(),
                                other_rect.top() - spacing_mm - candidate_rect.bottom(),
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
                        update_dimension_annotations()
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

                def center_text_item(text_item, *, vertical_offset_mm: float = 0.0):
                    scale_value = text_item.scale() if text_item.scale() > 0 else 1.0
                    bounds = text_item.boundingRect()
                    text_width = bounds.width() * scale_value
                    text_height = bounds.height() * scale_value
                    pos_x = (width_mm - text_width) / 2.0
                    pos_y = ((height_mm - text_height) / 2.0) + vertical_offset_mm
                    text_item.setPos(pos_x, pos_y)

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
                title_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                title_item.setZValue(2.0)
                center_text_item(title_item)

                if drawing_data is None:
                    empty_item = QGraphicsSimpleTextItem("(sin dibujo)", rect_item)
                    empty_item.setBrush(QBrush(QColorGui("#666666")))
                    empty_item.setScale(4.0)
                    empty_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    empty_item.setZValue(2.0)
                    center_text_item(empty_item, vertical_offset_mm=18.0)
                    draw_grain_hatching(rect_item, piece_row, width_mm, height_mm)
                    return rect_item, width_mm, height_mm

                draw_grain_hatching(rect_item, piece_row, width_mm, height_mm)

                for path in drawing_data.milling_paths:
                    if (path.face or "Top").strip().lower() != "top":
                        continue
                    if len(path.points) < 2:
                        continue
                    is_closed_path = len(path.points) >= 3 and path.points[0] == path.points[-1]
                    painter_path = QPainterPath()
                    first_x, first_y = path.points[0]
                    painter_path.moveTo(first_x, to_scene_y(first_y, height_mm))
                    for point_x, point_y in path.points[1:]:
                        painter_path.lineTo(point_x, to_scene_y(point_y, height_mm))
                    path_item = QGraphicsPathItem(painter_path, rect_item)
                    path_color = "#C0392B" if not is_closed_path else "#0B7A75"
                    path_item.setPen(make_pen(path_color, 1.0))
                    path_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    if not is_closed_path:
                        draw_entry_marker(rect_item, path.entry_arrow, height_mm, path_color)

                for circle in drawing_data.milling_circles:
                    face = (circle.face or "Top").strip().lower()
                    if face not in {"top", "bottom"}:
                        continue
                    radius = max(1.0, float(circle.radius or 0.0))
                    center_x = clamp(float(circle.center_x or 0.0), 0.0, width_mm)
                    center_y = clamp(float(circle.center_y or 0.0), 0.0, height_mm)
                    scene_y = to_scene_y(center_y, height_mm)
                    ellipse_item = QGraphicsEllipseItem(
                        center_x - radius,
                        scene_y - radius,
                        radius * 2.0,
                        radius * 2.0,
                        rect_item,
                    )
                    ellipse_item.setPen(make_pen("#0B7A75" if face == "top" else "#1F78B4", 1.0, dashed=(face == "bottom")))
                    ellipse_item.setBrush(QBrush(QtCoreQt.transparent))
                    ellipse_item.setAcceptedMouseButtons(QtCoreQt.NoButton)
                    if face == "top":
                        draw_entry_marker(rect_item, circle.entry_arrow, height_mm, "#0B7A75")

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
                piece_copy_count = en_juego_quantity(piece_row)
                for copy_index in range(1, piece_copy_count + 1):
                    en_juego_instances.append(
                        {
                            "piece_id": piece_id,
                            "piece_row": piece_row,
                            "copy_index": copy_index,
                            "instance_key": en_juego_instance_key(piece_id, copy_index),
                            "title_text": f"{base_title} #{copy_index}" if piece_copy_count > 1 else base_title,
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
                stored_x = safe_float(stored.get("scene_x"))
                if stored_x is None:
                    stored_x = safe_float(stored.get("x"))
                stored_y = safe_float(stored.get("scene_y"))
                if stored_y is None:
                    stored_y = safe_float(stored.get("y"))
                if stored_x is not None and stored_y is not None:
                    width_mm, _ = preview_dimensions_mm(piece_row, piece_drawing_data(piece_row))
                    current_unsaved_x_mm = max(current_unsaved_x_mm, stored_x + width_mm + preview_gap_mm)

            for instance in en_juego_instances:
                piece_row = instance["piece_row"]
                piece_id = instance["piece_id"]
                copy_index = instance["copy_index"]
                instance_key = instance["instance_key"]
                title_text = instance["title_text"]

                rect_item, width_mm, height_mm = build_piece_scene_item(piece_row, instance_key, title_text)

                stored, _ = saved_layout_for_instance(piece_id, copy_index)
                stored_x_mm = None
                stored_y_mm = None
                stored_rotation = None
                if isinstance(stored, dict):
                    stored_x_mm = safe_float(stored.get("scene_x"))
                    if stored_x_mm is None:
                        stored_x_mm = safe_float(stored.get("x"))
                    stored_y_mm = safe_float(stored.get("scene_y"))
                    if stored_y_mm is None:
                        stored_y_mm = safe_float(stored.get("y"))
                    stored_rotation = safe_float(stored.get("rotation_deg"))
                    if stored_rotation is None:
                        stored_rotation = safe_float(stored.get("rotation"))
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

            def scene_piece_items_in_layout_order():
                return sorted(
                    item_by_instance_id.values(),
                    key=lambda scene_item: (
                        round(nominal_scene_rect(scene_item).top(), 3),
                        round(nominal_scene_rect(scene_item).left(), 3),
                        str(scene_item.data(0) or ""),
                    ),
                )

            def update_scene_bounds():
                items_rect = scene.itemsBoundingRect()
                if items_rect.isNull():
                    return
                padded_rect = items_rect.adjusted(-scene_padding_mm, -scene_padding_mm, scene_padding_mm, scene_padding_mm)
                scene.setSceneRect(padded_rect)

            def enforce_minimum_piece_spacing(*, fit_view_after: bool = True):
                spacing_mm = effective_piece_spacing_mm()
                if spacing_mm <= 0:
                    return

                selected_instance_key = None
                selected_items = [item for item in scene.selectedItems() if str(item.data(0) or "").strip()]
                if selected_items:
                    selected_instance_key = str(selected_items[0].data(0) or "")

                moved_any = False
                auto_spacing_adjustment_state["active"] = True
                try:
                    for _ in range(max(1, len(item_by_instance_id) * 2)):
                        pass_moved = False
                        ordered_items = scene_piece_items_in_layout_order()
                        for current_index, current_item in enumerate(ordered_items):
                            current_rect = nominal_scene_rect(current_item)
                            for previous_item in ordered_items[:current_index]:
                                previous_rect = nominal_scene_rect(previous_item)
                                overlap_height = min(previous_rect.bottom(), current_rect.bottom()) - max(previous_rect.top(), current_rect.top())
                                overlap_width = min(previous_rect.right(), current_rect.right()) - max(previous_rect.left(), current_rect.left())

                                push_right_mm = (
                                    (previous_rect.right() + spacing_mm) - current_rect.left()
                                    if overlap_height > 0
                                    else 0.0
                                )
                                push_down_mm = (
                                    (previous_rect.bottom() + spacing_mm) - current_rect.top()
                                    if overlap_width > 0
                                    else 0.0
                                )

                                candidate_pushes = [
                                    (axis_name, delta_value)
                                    for axis_name, delta_value in (("x", push_right_mm), ("y", push_down_mm))
                                    if delta_value > 0.001
                                ]
                                if not candidate_pushes:
                                    continue

                                axis_name, delta_value = min(candidate_pushes, key=lambda item: item[1])
                                current_pos = current_item.pos()
                                if axis_name == "x":
                                    current_item.setPos(current_pos.x() + delta_value, current_pos.y())
                                else:
                                    current_item.setPos(current_pos.x(), current_pos.y() + delta_value)
                                current_rect = nominal_scene_rect(current_item)
                                moved_any = True
                                pass_moved = True

                        if not pass_moved:
                            break
                finally:
                    auto_spacing_adjustment_state["active"] = False

                if not moved_any:
                    return

                update_dimension_annotations()
                update_scene_bounds()
                if fit_view_after:
                    items_rect = scene.itemsBoundingRect()
                    if not items_rect.isNull():
                        view.fitInView(items_rect.adjusted(-80, -80, 80, 80), Qt.KeepAspectRatio)

                if selected_instance_key:
                    restored_item = item_by_instance_id.get(selected_instance_key)
                    if restored_item is not None:
                        scene.clearSelection()
                        restored_item.setSelected(True)

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

            dimension_annotation_state["ready"] = True
            update_dimension_annotations()
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
                update_dimension_annotations()
                update_scene_bounds()
                view.centerOn(scene_item)

            def sync_en_juego_settings_from_controls():
                en_juego_settings["cut_mode"] = "nesting" if nesting_cut_radio.isChecked() else "manual"
                resolved_tool = _resolve_en_juego_cutting_tool(en_juego_settings.get("cutting_tool_id"))
                en_juego_settings["origin_x"] = _compact_number(
                    _coerce_setting_number(origin_x_field.text().strip(), en_juego_settings.get("origin_x", 0.0))
                )
                en_juego_settings["origin_y"] = _compact_number(
                    _coerce_setting_number(origin_y_field.text().strip(), en_juego_settings.get("origin_y", 0.0))
                )
                en_juego_settings["origin_z"] = _compact_number(
                    _coerce_setting_number(origin_z_field.text().strip(), en_juego_settings.get("origin_z", 0.0))
                )
                en_juego_settings["division_squaring_order"] = (
                    "squaring_then_division"
                    if square_then_divide_radio.isChecked()
                    else "division_then_squaring"
                )
                en_juego_settings["cutting_is_through"] = _coerce_setting_bool(
                    en_juego_settings.get("cutting_is_through"),
                    True,
                )
                en_juego_settings["cutting_depth_value"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("cutting_depth_value"),
                        1.0,
                        minimum=0.0,
                    )
                )
                en_juego_settings["approach_enabled"] = _coerce_setting_bool(
                    en_juego_settings.get("approach_enabled"),
                    False,
                )
                en_juego_settings["approach_type"] = (
                    "Arc"
                    if str(en_juego_settings.get("approach_type") or "Arc").strip().lower() == "arc"
                    else "Line"
                )
                en_juego_settings["approach_radius_multiplier"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("approach_radius_multiplier"),
                        2.0,
                        minimum=0.0,
                    )
                )
                en_juego_settings["approach_mode"] = (
                    "Quote"
                    if str(en_juego_settings.get("approach_mode") or "Quote").strip().lower() == "quote"
                    else "Down"
                )
                en_juego_settings["retract_enabled"] = _coerce_setting_bool(
                    en_juego_settings.get("retract_enabled"),
                    False,
                )
                en_juego_settings["retract_type"] = (
                    "Arc"
                    if str(en_juego_settings.get("retract_type") or "Arc").strip().lower() == "arc"
                    else "Line"
                )
                en_juego_settings["retract_radius_multiplier"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("retract_radius_multiplier"),
                        2.0,
                        minimum=0.0,
                    )
                )
                en_juego_settings["retract_mode"] = (
                    "Quote"
                    if str(en_juego_settings.get("retract_mode") or "Quote").strip().lower() == "quote"
                    else "Up"
                )
                en_juego_settings["squaring_is_through"] = _coerce_setting_bool(
                    en_juego_settings.get("squaring_is_through"),
                    True,
                )
                en_juego_settings["squaring_depth_value"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("squaring_depth_value"),
                        1.0,
                        minimum=0.0,
                    )
                )
                en_juego_settings["squaring_approach_enabled"] = _coerce_setting_bool(
                    en_juego_settings.get("squaring_approach_enabled"),
                    False,
                )
                en_juego_settings["squaring_approach_type"] = (
                    "Arc"
                    if str(en_juego_settings.get("squaring_approach_type") or "Arc").strip().lower() == "arc"
                    else "Line"
                )
                en_juego_settings["squaring_approach_radius_multiplier"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("squaring_approach_radius_multiplier"),
                        2.0,
                        minimum=0.0,
                    )
                )
                en_juego_settings["squaring_approach_mode"] = (
                    "Quote"
                    if str(en_juego_settings.get("squaring_approach_mode") or "Quote").strip().lower() == "quote"
                    else "Down"
                )
                en_juego_settings["squaring_retract_enabled"] = _coerce_setting_bool(
                    en_juego_settings.get("squaring_retract_enabled"),
                    False,
                )
                en_juego_settings["squaring_retract_type"] = (
                    "Arc"
                    if str(en_juego_settings.get("squaring_retract_type") or "Arc").strip().lower() == "arc"
                    else "Line"
                )
                en_juego_settings["squaring_retract_radius_multiplier"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("squaring_retract_radius_multiplier"),
                        2.0,
                        minimum=0.0,
                    )
                )
                en_juego_settings["squaring_retract_mode"] = (
                    "Quote"
                    if str(en_juego_settings.get("squaring_retract_mode") or "Quote").strip().lower() == "quote"
                    else "Up"
                )
                squaring_tool = _resolve_en_juego_cutting_tool(en_juego_settings.get("squaring_tool_id"))
                en_juego_settings["squaring_tool_id"] = str(
                    en_juego_settings.get("squaring_tool_id")
                    or squaring_tool.get("tool_id")
                    or ""
                ).strip()
                en_juego_settings["squaring_tool_code"] = str(
                    en_juego_settings.get("squaring_tool_code")
                    or squaring_tool.get("tool_code")
                    or ""
                ).strip()
                en_juego_settings["squaring_tool_name"] = str(
                    en_juego_settings.get("squaring_tool_name")
                    or squaring_tool.get("tool_name")
                    or ""
                ).strip()
                en_juego_settings["squaring_tool_diameter"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("squaring_tool_diameter"),
                        _coerce_setting_number(squaring_tool.get("diameter"), 0.0, minimum=0.0),
                        minimum=0.0,
                    )
                )
                en_juego_settings["cutting_tool_id"] = str(
                    en_juego_settings.get("cutting_tool_id")
                    or resolved_tool.get("tool_id")
                    or ""
                ).strip()
                en_juego_settings["cutting_tool_code"] = str(
                    en_juego_settings.get("cutting_tool_code")
                    or resolved_tool.get("tool_code")
                    or ""
                ).strip()
                en_juego_settings["cutting_tool_name"] = str(
                    en_juego_settings.get("cutting_tool_name")
                    or resolved_tool.get("tool_name")
                    or ""
                ).strip()
                en_juego_settings["cutting_tool_diameter"] = _compact_number(
                    _coerce_setting_number(
                        en_juego_settings.get("cutting_tool_diameter"),
                        _coerce_setting_number(resolved_tool.get("diameter"), 0.0, minimum=0.0),
                        minimum=0.0,
                    )
                )

            def persist_en_juego_settings():
                sync_en_juego_settings_from_controls()
                config_data["en_juego_settings"] = dict(en_juego_settings)
                persist_module_config()

            def open_en_juego_settings_dialog():
                settings_dialog = QDialog(config_dialog)
                settings_dialog.setWindowTitle("Configurar Divisiones")
                settings_layout = QVBoxLayout()
                settings_layout.setContentsMargins(12, 12, 12, 12)
                settings_layout.setSpacing(10)
                settings_layout.addWidget(
                    QLabel(
                        "Defina las opciones de divisiones del En-Juego para este módulo.\n"
                        "El modo Nesting todavía no genera el programa automáticamente."
                    )
                )

                mode_group = QGroupBox("Modo de Corte")
                mode_group_layout = QVBoxLayout()
                mode_group_layout.setContentsMargins(8, 8, 8, 8)
                mode_group_layout.setSpacing(6)
                manual_mode_radio = QRadioButton("Corte Manual")
                nesting_mode_radio = QRadioButton("Corte Nesting")
                manual_mode_radio.setChecked(manual_cut_radio.isChecked())
                nesting_mode_radio.setChecked(nesting_cut_radio.isChecked())
                mode_group_layout.addWidget(manual_mode_radio)
                mode_group_layout.addWidget(nesting_mode_radio)
                mode_group.setLayout(mode_group_layout)
                settings_layout.addWidget(mode_group)

                saw_kerf_row = QHBoxLayout()
                saw_kerf_row.addWidget(QLabel("Espesor de Sierra"))
                saw_kerf_field = QLineEdit(str(en_juego_settings.get("saw_kerf", 4)))
                saw_kerf_row.addWidget(saw_kerf_field)
                settings_layout.addLayout(saw_kerf_row)

                buttons_row = QHBoxLayout()
                buttons_row.addStretch(1)
                save_settings_btn = QPushButton("Guardar")
                cancel_settings_btn = QPushButton("Cancelar")
                save_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
                cancel_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
                buttons_row.addWidget(save_settings_btn)
                buttons_row.addWidget(cancel_settings_btn)
                settings_layout.addLayout(buttons_row)
                settings_dialog.setLayout(settings_layout)

                def save_en_juego_settings_dialog():
                    saw_kerf_value = _coerce_setting_number(
                        saw_kerf_field.text().strip() or en_juego_settings.get("saw_kerf"),
                        en_juego_settings.get("saw_kerf", 4.0),
                        minimum=0.0,
                    )
                    en_juego_settings["cut_mode"] = "nesting" if nesting_mode_radio.isChecked() else "manual"
                    en_juego_settings["saw_kerf"] = _compact_number(saw_kerf_value)
                    manual_cut_radio.setChecked(en_juego_settings["cut_mode"] == "manual")
                    nesting_cut_radio.setChecked(en_juego_settings["cut_mode"] == "nesting")
                    nonlocal en_juego_saw_kerf_mm
                    en_juego_saw_kerf_mm = float(saw_kerf_value)
                    persist_en_juego_settings()
                    settings_dialog.accept()

                save_settings_btn.clicked.connect(save_en_juego_settings_dialog)
                cancel_settings_btn.clicked.connect(settings_dialog.reject)
                _exec_centered(settings_dialog, config_dialog)

            def open_en_juego_settings_dialog_v2():
                if not nesting_cut_radio.isChecked():
                    return

                settings_dialog = QDialog(config_dialog)
                settings_dialog.setWindowTitle("Configurar Divisiones")
                _apply_responsive_window_size(
                    settings_dialog,
                    780,
                    460,
                    width_ratio=0.66,
                    height_ratio=0.6,
                )
                settings_layout = QVBoxLayout()
                settings_layout.setContentsMargins(12, 12, 12, 12)
                settings_layout.setSpacing(10)
                settings_layout.addWidget(
                    QLabel(
                        "Defina las opciones de divisiones del En-Juego para este módulo.\n"
                        "Por ahora, la herramienta elegida define la separación mínima en el panel."
                    )
                )

                tool_group = QGroupBox("Herramienta de corte")
                tool_layout = QVBoxLayout()
                tool_layout.setContentsMargins(8, 8, 8, 8)
                tool_layout.setSpacing(6)
                tool_combo = QComboBox()
                for tool_data in available_cutting_tools:
                    tool_combo.addItem(tool_data["label"], tool_data["tool_id"])
                selected_tool_id = str(en_juego_settings.get("cutting_tool_id") or "").strip()
                selected_index = next(
                    (
                        index
                        for index, tool_data in enumerate(available_cutting_tools)
                        if str(tool_data.get("tool_id") or "").strip() == selected_tool_id
                    ),
                    0,
                )
                if tool_combo.count() > 0:
                    tool_combo.setCurrentIndex(selected_index)
                else:
                    tool_combo.addItem("(sin herramientas disponibles)", "")
                    tool_combo.setEnabled(False)
                tool_hint_label = QLabel()
                tool_hint_label.setWordWrap(True)
                tool_layout.addWidget(tool_combo)
                tool_layout.addWidget(tool_hint_label)
                tool_group.setLayout(tool_layout)
                settings_layout.addWidget(tool_group)

                depth_group = QGroupBox("Profundidad de división")
                depth_layout = QGridLayout()
                depth_layout.setContentsMargins(8, 6, 8, 6)
                depth_layout.setHorizontalSpacing(8)
                depth_layout.setVerticalSpacing(4)
                through_checkbox = QCheckBox("Pasante")
                through_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("cutting_is_through"), True)
                )
                depth_role_label = QLabel()
                depth_value_field = QLineEdit(str(en_juego_settings.get("cutting_depth_value", 1.0)))
                depth_layout.addWidget(through_checkbox, 0, 0, 1, 2)
                depth_layout.addWidget(depth_role_label, 1, 0)
                depth_layout.addWidget(depth_value_field, 1, 1)
                depth_group.setLayout(depth_layout)
                depth_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

                strategy_group = QGroupBox("Estrategia")
                strategy_layout = QGridLayout()
                strategy_layout.setContentsMargins(8, 8, 8, 8)
                strategy_layout.setHorizontalSpacing(8)
                strategy_layout.setVerticalSpacing(6)
                cutting_multipass_checkbox = QCheckBox("Multipasada")
                cutting_multipass_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("cutting_multipass_enabled"), False)
                )
                cutting_path_mode_combo = QComboBox()
                cutting_path_mode_combo.addItem("Unidireccional", "Unidirectional")
                cutting_path_mode_combo.addItem("Bidireccional", "Bidirectional")
                cutting_path_mode_combo.setCurrentIndex(
                    1
                    if str(en_juego_settings.get("cutting_path_mode") or "Unidirectional") == "Bidirectional"
                    else 0
                )
                cutting_pocket_depth_field = QLineEdit(str(en_juego_settings.get("cutting_pocket_depth", 0.0)))
                cutting_last_pocket_field = QLineEdit(str(en_juego_settings.get("cutting_last_pocket", 0.0)))
                strategy_layout.addWidget(cutting_multipass_checkbox, 0, 0, 1, 2)
                strategy_layout.addWidget(QLabel("Recorrido"), 1, 0)
                strategy_layout.addWidget(cutting_path_mode_combo, 1, 1)
                strategy_layout.addWidget(QLabel("Profundidad de Hueco"), 2, 0)
                strategy_layout.addWidget(cutting_pocket_depth_field, 2, 1)
                strategy_layout.addWidget(QLabel("Último Hueco"), 3, 0)
                strategy_layout.addWidget(cutting_last_pocket_field, 3, 1)
                strategy_group.setLayout(strategy_layout)
                strategy_group.setMinimumHeight(_scaled_int(138, compact_scale, 108))

                lead_group = QGroupBox("Acercamiento y Alejamiento")
                lead_layout = QGridLayout()
                lead_layout.setContentsMargins(8, 8, 8, 8)
                lead_layout.setHorizontalSpacing(8)
                lead_layout.setVerticalSpacing(6)

                approach_checkbox = QCheckBox("Acercamiento")
                approach_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("approach_enabled"), False)
                )
                approach_type_combo = QComboBox()
                approach_type_combo.addItem("Arco", "Arc")
                approach_type_combo.addItem("Lineal", "Line")
                approach_type_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("approach_type") or "Arc") == "Arc" else 1
                )
                approach_radius_field = QLineEdit(str(en_juego_settings.get("approach_radius_multiplier", 2.0)))
                approach_mode_combo = QComboBox()
                approach_mode_combo.addItem("En cota", "Quote")
                approach_mode_combo.addItem("En bajada", "Down")
                approach_mode_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("approach_mode") or "Quote") == "Quote" else 1
                )

                retract_checkbox = QCheckBox("Alejamiento")
                retract_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("retract_enabled"), False)
                )
                retract_type_combo = QComboBox()
                retract_type_combo.addItem("Arco", "Arc")
                retract_type_combo.addItem("Lineal", "Line")
                retract_type_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("retract_type") or "Arc") == "Arc" else 1
                )
                retract_radius_field = QLineEdit(str(en_juego_settings.get("retract_radius_multiplier", 2.0)))
                retract_mode_combo = QComboBox()
                retract_mode_combo.addItem("En cota", "Quote")
                retract_mode_combo.addItem("En subida", "Up")
                retract_mode_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("retract_mode") or "Quote") == "Quote" else 1
                )

                lead_layout.addWidget(approach_checkbox, 0, 0, 1, 2)
                lead_layout.addWidget(QLabel("Entrada"), 1, 0)
                lead_layout.addWidget(approach_type_combo, 1, 1)
                lead_layout.addWidget(QLabel("Multipl radio"), 2, 0)
                lead_layout.addWidget(approach_radius_field, 2, 1)
                lead_layout.addWidget(QLabel("Acercamiento"), 3, 0)
                lead_layout.addWidget(approach_mode_combo, 3, 1)
                lead_layout.addWidget(retract_checkbox, 4, 0, 1, 2)
                lead_layout.addWidget(QLabel("Salida"), 5, 0)
                lead_layout.addWidget(retract_type_combo, 5, 1)
                lead_layout.addWidget(QLabel("Multipl radio"), 6, 0)
                lead_layout.addWidget(retract_radius_field, 6, 1)
                lead_layout.addWidget(QLabel("Alejamiento"), 7, 0)
                lead_layout.addWidget(retract_mode_combo, 7, 1)
                lead_group.setLayout(lead_layout)

                left_column_layout = QVBoxLayout()
                left_column_layout.setContentsMargins(0, 0, 0, 0)
                left_column_layout.setSpacing(8)
                left_column_layout.addWidget(depth_group, 0, Qt.AlignTop)
                left_column_layout.addWidget(strategy_group, 1)
                left_column_widget = QWidget()
                left_column_widget.setLayout(left_column_layout)

                depth_and_lead_row = QHBoxLayout()
                depth_and_lead_row.setContentsMargins(0, 0, 0, 0)
                depth_and_lead_row.setSpacing(8)
                depth_and_lead_row.addWidget(left_column_widget, 1)
                depth_and_lead_row.addWidget(lead_group, 1)
                settings_layout.addLayout(depth_and_lead_row)

                buttons_row = QHBoxLayout()
                buttons_row.addStretch(1)
                save_settings_btn = QPushButton("Guardar")
                cancel_settings_btn = QPushButton("Cancelar")
                save_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
                cancel_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
                buttons_row.addWidget(save_settings_btn)
                buttons_row.addWidget(cancel_settings_btn)
                settings_layout.addLayout(buttons_row)
                settings_dialog.setLayout(settings_layout)

                def refresh_tool_hint():
                    current_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
                    diameter_value = _coerce_setting_number(current_tool.get("diameter"), 0.0, minimum=0.0)
                    if diameter_value > 0:
                        tool_hint_label.setText(
                            "Separación mínima en Nesting: "
                            f"{_compact_number(diameter_value)} mm"
                        )
                    else:
                        tool_hint_label.setText(
                            "No hay una herramienta de corte disponible para definir la separación."
                        )

                refresh_tool_hint()
                tool_combo.currentIndexChanged.connect(lambda *_: refresh_tool_hint())

                def refresh_tool_hint_v2():
                    current_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
                    current_settings = dict(en_juego_settings)
                    current_settings["cutting_tool_id"] = str(current_tool.get("tool_id") or "").strip()
                    current_settings["cutting_tool_diameter"] = _compact_number(
                        _coerce_setting_number(current_tool.get("diameter"), 0.0, minimum=0.0)
                    )
                    current_settings["cutting_is_through"] = through_checkbox.isChecked()
                    current_settings["cutting_depth_value"] = _compact_number(
                        _coerce_setting_number(
                            depth_value_field.text().strip(),
                            en_juego_settings.get("cutting_depth_value", 1.0),
                            minimum=0.0,
                        )
                    )
                    depth_role_label.setText(
                        "Profundidad extra"
                        if current_settings["cutting_is_through"]
                        else "Profundidad de división"
                    )
                    spacing_value = _resolve_en_juego_nesting_spacing_mm(
                        current_settings,
                        material_thickness_mm=en_juego_material_thickness_mm,
                    )
                    if spacing_value > 0:
                        if _is_forty_five_degree_milling_tool(current_tool.get("tool_type")):
                            if current_settings["cutting_is_through"]:
                                tool_hint_label.setText(
                                    "Con Fresa 45º, la separacion minima entre piezas contiguas sera de "
                                    f"{_compact_number(spacing_value)} mm, a razon de 2 mm por cada 1 mm "
                                    "de profundidad extra."
                                )
                            else:
                                tool_hint_label.setText(
                                    "Con Fresa 45º, la separacion minima entre piezas contiguas sera de "
                                    f"{_compact_number(spacing_value)} mm, calculada respecto del espesor "
                                    f"de { _compact_number(en_juego_material_thickness_mm) } mm."
                                )
                        elif _is_helical_tool_type(current_tool.get("tool_type")):
                            tool_hint_label.setText(
                                "Herramienta preferente para dividir En-Juego. "
                                "La separacion minima entre piezas contiguas sera de "
                                f"{_compact_number(spacing_value)} mm."
                            )
                        else:
                            tool_hint_label.setText(
                                "La separacion minima entre piezas contiguas sera de "
                                f"{_compact_number(spacing_value)} mm."
                            )
                    else:
                        tool_hint_label.setText(
                            "No hay una herramienta de corte disponible para definir la separacion."
                        )

                def refresh_lead_controls():
                    approach_enabled = approach_checkbox.isChecked()
                    for widget in (approach_type_combo, approach_radius_field, approach_mode_combo):
                        widget.setEnabled(approach_enabled)

                    retract_enabled = retract_checkbox.isChecked()
                    for widget in (retract_type_combo, retract_radius_field, retract_mode_combo):
                        widget.setEnabled(retract_enabled)

                    multipass_enabled = cutting_multipass_checkbox.isChecked()
                    for widget in (
                        cutting_path_mode_combo,
                        cutting_pocket_depth_field,
                        cutting_last_pocket_field,
                    ):
                        widget.setEnabled(multipass_enabled)

                    depth_role_label.setText(
                        "Profundidad extra" if through_checkbox.isChecked() else "Profundidad de división"
                    )

                refresh_lead_controls()
                refresh_tool_hint_v2()
                tool_combo.currentIndexChanged.connect(lambda *_: refresh_tool_hint_v2())
                through_checkbox.toggled.connect(lambda *_: refresh_tool_hint_v2())
                depth_value_field.textChanged.connect(lambda *_: refresh_tool_hint_v2())
                through_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
                approach_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
                retract_checkbox.toggled.connect(lambda *_: refresh_lead_controls())
                cutting_multipass_checkbox.toggled.connect(lambda *_: refresh_lead_controls())

                def save_en_juego_settings_dialog_v2():
                    selected_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
                    en_juego_settings["origin_x"] = _compact_number(
                        _coerce_setting_number(origin_x_field.text().strip(), en_juego_settings.get("origin_x", 0.0))
                    )
                    en_juego_settings["origin_y"] = _compact_number(
                        _coerce_setting_number(origin_y_field.text().strip(), en_juego_settings.get("origin_y", 0.0))
                    )
                    en_juego_settings["origin_z"] = _compact_number(
                        _coerce_setting_number(origin_z_field.text().strip(), en_juego_settings.get("origin_z", 0.0))
                    )
                    en_juego_settings["cutting_tool_id"] = str(selected_tool.get("tool_id") or "").strip()
                    en_juego_settings["cutting_tool_code"] = str(selected_tool.get("tool_code") or "").strip()
                    en_juego_settings["cutting_tool_name"] = str(selected_tool.get("tool_name") or "").strip()
                    en_juego_settings["cutting_tool_diameter"] = _compact_number(
                        _coerce_setting_number(selected_tool.get("diameter"), 0.0, minimum=0.0)
                    )
                    en_juego_settings["cutting_is_through"] = through_checkbox.isChecked()
                    en_juego_settings["cutting_depth_value"] = _compact_number(
                        _coerce_setting_number(
                            depth_value_field.text().strip(),
                            en_juego_settings.get("cutting_depth_value", 1.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["cutting_multipass_enabled"] = cutting_multipass_checkbox.isChecked()
                    en_juego_settings["cutting_path_mode"] = str(
                        cutting_path_mode_combo.currentData() or "Unidirectional"
                    )
                    en_juego_settings["cutting_pocket_depth"] = _compact_number(
                        _coerce_setting_number(
                            cutting_pocket_depth_field.text().strip(),
                            en_juego_settings.get("cutting_pocket_depth", 0.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["cutting_last_pocket"] = _compact_number(
                        _coerce_setting_number(
                            cutting_last_pocket_field.text().strip(),
                            en_juego_settings.get("cutting_last_pocket", 0.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["approach_enabled"] = approach_checkbox.isChecked()
                    en_juego_settings["approach_type"] = str(approach_type_combo.currentData() or "Arc")
                    en_juego_settings["approach_radius_multiplier"] = _compact_number(
                        _coerce_setting_number(
                            approach_radius_field.text().strip(),
                            en_juego_settings.get("approach_radius_multiplier", 2.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["approach_mode"] = str(approach_mode_combo.currentData() or "Quote")
                    en_juego_settings["retract_enabled"] = retract_checkbox.isChecked()
                    en_juego_settings["retract_type"] = str(retract_type_combo.currentData() or "Arc")
                    en_juego_settings["retract_radius_multiplier"] = _compact_number(
                        _coerce_setting_number(
                            retract_radius_field.text().strip(),
                            en_juego_settings.get("retract_radius_multiplier", 2.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["retract_mode"] = str(retract_mode_combo.currentData() or "Quote")
                    persist_en_juego_settings()
                    refresh_cut_mode_controls()
                    settings_dialog.accept()

                save_settings_btn.clicked.connect(save_en_juego_settings_dialog_v2)
                cancel_settings_btn.clicked.connect(settings_dialog.reject)
                _exec_centered(settings_dialog, config_dialog)

            def open_en_juego_squaring_settings_dialog_v2():
                if not nesting_cut_radio.isChecked():
                    return

                settings_dialog = QDialog(config_dialog)
                settings_dialog.setWindowTitle("Configurar Escuadrado")
                _apply_responsive_window_size(
                    settings_dialog,
                    780,
                    420,
                    width_ratio=0.64,
                    height_ratio=0.58,
                )
                settings_layout = QVBoxLayout()
                settings_layout.setContentsMargins(12, 12, 12, 12)
                settings_layout.setSpacing(10)
                settings_layout.addWidget(
                    QLabel(
                        "Defina las opciones de escuadrado del En-Juego para este módulo.\n"
                        "Estas opciones se guardan junto con la disposición del módulo."
                    )
                )

                tool_group = QGroupBox("Herramienta de escuadrado")
                tool_layout = QVBoxLayout()
                tool_layout.setContentsMargins(8, 8, 8, 8)
                tool_layout.setSpacing(6)
                tool_combo = QComboBox()
                for tool_data in available_cutting_tools:
                    tool_combo.addItem(tool_data["label"], tool_data["tool_id"])
                selected_tool_id = str(en_juego_settings.get("squaring_tool_id") or "").strip()
                selected_index = next(
                    (
                        index
                        for index, tool_data in enumerate(available_cutting_tools)
                        if str(tool_data.get("tool_id") or "").strip() == selected_tool_id
                    ),
                    0,
                )
                if tool_combo.count() > 0:
                    tool_combo.setCurrentIndex(selected_index)
                else:
                    tool_combo.addItem("(sin herramientas disponibles)", "")
                    tool_combo.setEnabled(False)
                tool_hint_label = QLabel()
                tool_hint_label.setWordWrap(True)
                tool_layout.addWidget(tool_combo)
                tool_layout.addWidget(tool_hint_label)
                tool_group.setLayout(tool_layout)
                settings_layout.addWidget(tool_group)

                depth_group = QGroupBox("Profundidad de escuadrado")
                depth_layout = QGridLayout()
                depth_layout.setContentsMargins(8, 6, 8, 6)
                depth_layout.setHorizontalSpacing(8)
                depth_layout.setVerticalSpacing(4)
                through_checkbox = QCheckBox("Pasante")
                through_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("squaring_is_through"), True)
                )
                depth_role_label = QLabel()
                depth_value_field = QLineEdit(str(en_juego_settings.get("squaring_depth_value", 1.0)))
                depth_layout.addWidget(through_checkbox, 0, 0, 1, 2)
                depth_layout.addWidget(depth_role_label, 1, 0)
                depth_layout.addWidget(depth_value_field, 1, 1)
                depth_group.setLayout(depth_layout)
                depth_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

                strategy_group = QGroupBox("Estrategia")
                strategy_layout = QGridLayout()
                strategy_layout.setContentsMargins(8, 8, 8, 8)
                strategy_layout.setSpacing(6)
                strategy_layout.setHorizontalSpacing(8)
                strategy_layout.setVerticalSpacing(6)
                direction_combo = QComboBox()
                direction_combo.addItem("Horario", "CW")
                direction_combo.addItem("Antihorario", "CCW")
                direction_combo.setCurrentIndex(
                    1 if str(en_juego_settings.get("squaring_direction") or "CW") == "CCW" else 0
                )
                unidirectional_multipass_checkbox = QCheckBox("Multipasada Unidireccional")
                unidirectional_multipass_checkbox.setChecked(
                    _coerce_setting_bool(
                        en_juego_settings.get("squaring_unidirectional_multipass"),
                        False,
                    )
                )
                pocket_depth_field = QLineEdit(str(en_juego_settings.get("squaring_pocket_depth", 0.0)))
                last_pocket_field = QLineEdit(str(en_juego_settings.get("squaring_last_pocket", 0.0)))
                strategy_layout.addWidget(QLabel("Sentido"), 0, 0)
                strategy_layout.addWidget(direction_combo, 0, 1)
                strategy_layout.addWidget(unidirectional_multipass_checkbox, 1, 0, 1, 2)
                strategy_layout.addWidget(QLabel("Profundidad de Hueco"), 2, 0)
                strategy_layout.addWidget(pocket_depth_field, 2, 1)
                strategy_layout.addWidget(QLabel("Último Hueco"), 3, 0)
                strategy_layout.addWidget(last_pocket_field, 3, 1)
                strategy_group.setLayout(strategy_layout)
                strategy_group.setMinimumHeight(_scaled_int(138, compact_scale, 108))

                lead_group = QGroupBox("Acercamiento y Alejamiento")
                lead_layout = QGridLayout()
                lead_layout.setContentsMargins(8, 8, 8, 8)
                lead_layout.setHorizontalSpacing(8)
                lead_layout.setVerticalSpacing(6)

                approach_checkbox = QCheckBox("Acercamiento")
                approach_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("squaring_approach_enabled"), False)
                )
                approach_type_combo = QComboBox()
                approach_type_combo.addItem("Arco", "Arc")
                approach_type_combo.addItem("Lineal", "Line")
                approach_type_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("squaring_approach_type") or "Arc") == "Arc" else 1
                )
                approach_radius_field = QLineEdit(
                    str(en_juego_settings.get("squaring_approach_radius_multiplier", 2.0))
                )
                approach_mode_combo = QComboBox()
                approach_mode_combo.addItem("En cota", "Quote")
                approach_mode_combo.addItem("En bajada", "Down")
                approach_mode_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("squaring_approach_mode") or "Quote") == "Quote" else 1
                )

                retract_checkbox = QCheckBox("Alejamiento")
                retract_checkbox.setChecked(
                    _coerce_setting_bool(en_juego_settings.get("squaring_retract_enabled"), False)
                )
                retract_type_combo = QComboBox()
                retract_type_combo.addItem("Arco", "Arc")
                retract_type_combo.addItem("Lineal", "Line")
                retract_type_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("squaring_retract_type") or "Arc") == "Arc" else 1
                )
                retract_radius_field = QLineEdit(
                    str(en_juego_settings.get("squaring_retract_radius_multiplier", 2.0))
                )
                retract_mode_combo = QComboBox()
                retract_mode_combo.addItem("En cota", "Quote")
                retract_mode_combo.addItem("En subida", "Up")
                retract_mode_combo.setCurrentIndex(
                    0 if str(en_juego_settings.get("squaring_retract_mode") or "Quote") == "Quote" else 1
                )

                lead_layout.addWidget(approach_checkbox, 0, 0, 1, 2)
                lead_layout.addWidget(QLabel("Entrada"), 1, 0)
                lead_layout.addWidget(approach_type_combo, 1, 1)
                lead_layout.addWidget(QLabel("Multipl radio"), 2, 0)
                lead_layout.addWidget(approach_radius_field, 2, 1)
                lead_layout.addWidget(QLabel("Acercamiento"), 3, 0)
                lead_layout.addWidget(approach_mode_combo, 3, 1)
                lead_layout.addWidget(retract_checkbox, 4, 0, 1, 2)
                lead_layout.addWidget(QLabel("Salida"), 5, 0)
                lead_layout.addWidget(retract_type_combo, 5, 1)
                lead_layout.addWidget(QLabel("Multipl radio"), 6, 0)
                lead_layout.addWidget(retract_radius_field, 6, 1)
                lead_layout.addWidget(QLabel("Alejamiento"), 7, 0)
                lead_layout.addWidget(retract_mode_combo, 7, 1)
                lead_group.setLayout(lead_layout)

                left_column_layout = QVBoxLayout()
                left_column_layout.setContentsMargins(0, 0, 0, 0)
                left_column_layout.setSpacing(8)
                left_column_layout.addWidget(depth_group, 0, Qt.AlignTop)
                left_column_layout.addWidget(strategy_group, 1)
                left_column_widget = QWidget()
                left_column_widget.setLayout(left_column_layout)

                depth_and_lead_row = QHBoxLayout()
                depth_and_lead_row.setContentsMargins(0, 0, 0, 0)
                depth_and_lead_row.setSpacing(8)
                depth_and_lead_row.addWidget(left_column_widget, 1)
                depth_and_lead_row.addWidget(lead_group, 1)
                settings_layout.addLayout(depth_and_lead_row)

                buttons_row = QHBoxLayout()
                buttons_row.addStretch(1)
                save_settings_btn = QPushButton("Guardar")
                cancel_settings_btn = QPushButton("Cancelar")
                save_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
                cancel_settings_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
                buttons_row.addWidget(save_settings_btn)
                buttons_row.addWidget(cancel_settings_btn)
                settings_layout.addLayout(buttons_row)
                settings_dialog.setLayout(settings_layout)

                def refresh_squaring_tool_hint():
                    current_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
                    diameter_value = _coerce_setting_number(current_tool.get("diameter"), 0.0, minimum=0.0)
                    depth_role_label.setText(
                        "Profundidad extra" if through_checkbox.isChecked() else "Profundidad de escuadrado"
                    )
                    if diameter_value > 0:
                        tool_hint_label.setText(
                            "Herramienta de escuadrado seleccionada: "
                            f"Ø {_compact_number(diameter_value)} mm."
                        )
                    else:
                        tool_hint_label.setText(
                            "No hay una herramienta disponible para el escuadrado."
                        )

                def refresh_squaring_lead_controls():
                    for widget in (approach_type_combo, approach_radius_field, approach_mode_combo):
                        widget.setEnabled(approach_checkbox.isChecked())
                    for widget in (retract_type_combo, retract_radius_field, retract_mode_combo):
                        widget.setEnabled(retract_checkbox.isChecked())
                    multipass_enabled = unidirectional_multipass_checkbox.isChecked()
                    for widget in (pocket_depth_field, last_pocket_field):
                        widget.setEnabled(multipass_enabled)
                    depth_role_label.setText(
                        "Profundidad extra" if through_checkbox.isChecked() else "Profundidad de escuadrado"
                    )

                refresh_squaring_lead_controls()
                refresh_squaring_tool_hint()
                tool_combo.currentIndexChanged.connect(lambda *_: refresh_squaring_tool_hint())
                through_checkbox.toggled.connect(lambda *_: refresh_squaring_tool_hint())
                through_checkbox.toggled.connect(lambda *_: refresh_squaring_lead_controls())
                approach_checkbox.toggled.connect(lambda *_: refresh_squaring_lead_controls())
                retract_checkbox.toggled.connect(lambda *_: refresh_squaring_lead_controls())
                unidirectional_multipass_checkbox.toggled.connect(lambda *_: refresh_squaring_lead_controls())

                def save_en_juego_squaring_settings_dialog_v2():
                    selected_tool = _resolve_en_juego_cutting_tool(tool_combo.currentData())
                    en_juego_settings["squaring_tool_id"] = str(selected_tool.get("tool_id") or "").strip()
                    en_juego_settings["squaring_tool_code"] = str(selected_tool.get("tool_code") or "").strip()
                    en_juego_settings["squaring_tool_name"] = str(selected_tool.get("tool_name") or "").strip()
                    en_juego_settings["squaring_tool_diameter"] = _compact_number(
                        _coerce_setting_number(selected_tool.get("diameter"), 0.0, minimum=0.0)
                    )
                    en_juego_settings["squaring_is_through"] = through_checkbox.isChecked()
                    en_juego_settings["squaring_depth_value"] = _compact_number(
                        _coerce_setting_number(
                            depth_value_field.text().strip(),
                            en_juego_settings.get("squaring_depth_value", 1.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["squaring_approach_enabled"] = approach_checkbox.isChecked()
                    en_juego_settings["squaring_approach_type"] = str(approach_type_combo.currentData() or "Arc")
                    en_juego_settings["squaring_approach_radius_multiplier"] = _compact_number(
                        _coerce_setting_number(
                            approach_radius_field.text().strip(),
                            en_juego_settings.get("squaring_approach_radius_multiplier", 2.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["squaring_approach_mode"] = str(approach_mode_combo.currentData() or "Quote")
                    en_juego_settings["squaring_retract_enabled"] = retract_checkbox.isChecked()
                    en_juego_settings["squaring_retract_type"] = str(retract_type_combo.currentData() or "Arc")
                    en_juego_settings["squaring_retract_radius_multiplier"] = _compact_number(
                        _coerce_setting_number(
                            retract_radius_field.text().strip(),
                            en_juego_settings.get("squaring_retract_radius_multiplier", 2.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["squaring_retract_mode"] = str(retract_mode_combo.currentData() or "Quote")
                    en_juego_settings["squaring_direction"] = str(direction_combo.currentData() or "CW")
                    en_juego_settings["squaring_unidirectional_multipass"] = (
                        unidirectional_multipass_checkbox.isChecked()
                    )
                    en_juego_settings["squaring_pocket_depth"] = _compact_number(
                        _coerce_setting_number(
                            pocket_depth_field.text().strip(),
                            en_juego_settings.get("squaring_pocket_depth", 0.0),
                            minimum=0.0,
                        )
                    )
                    en_juego_settings["squaring_last_pocket"] = _compact_number(
                        _coerce_setting_number(
                            last_pocket_field.text().strip(),
                            en_juego_settings.get("squaring_last_pocket", 0.0),
                            minimum=0.0,
                        )
                    )
                    persist_en_juego_settings()
                    refresh_cut_mode_controls()
                    settings_dialog.accept()

                save_settings_btn.clicked.connect(save_en_juego_squaring_settings_dialog_v2)
                cancel_settings_btn.clicked.connect(settings_dialog.reject)
                _exec_centered(settings_dialog, config_dialog)

            def collect_en_juego_layout_data():
                from core.pgmx_processing import resolve_piece_grain_hatch_axis

                piece_rows_by_id = {
                    str(piece_row.get("id") or "").strip(): piece_row
                    for piece_row in en_juego_rows
                }

                def local_grain_axis(hatch_axis: str) -> str:
                    if hatch_axis == "horizontal":
                        return "x"
                    if hatch_axis == "vertical":
                        return "y"
                    return "none"

                def composition_grain_axis(axis: str, rotation_deg: float) -> str:
                    if axis not in {"x", "y"}:
                        return "none"
                    normalized_rotation = round(rotation_deg) % 180
                    if normalized_rotation == 90:
                        return "y" if axis == "x" else "x"
                    return axis

                def instance_grain_fields(piece_id: str, item_rect, rotation_deg: float) -> dict:
                    piece_row = piece_rows_by_id.get(piece_id) or {}
                    grain_direction = normalize_piece_grain_direction(piece_row.get("grain_direction"))
                    hatch_axis = resolve_piece_grain_hatch_axis(
                        grain_direction,
                        safe_float(piece_row.get("width")),
                        safe_float(piece_row.get("height")),
                        float(item_rect.width()),
                        float(item_rect.height()),
                    )
                    local_axis = local_grain_axis(hatch_axis)
                    return {
                        "grain_direction": grain_direction,
                        "grain_axis_local": local_axis,
                        "grain_axis_composition": composition_grain_axis(local_axis, rotation_deg),
                    }

                def instance_piece_color(piece_id: str) -> str:
                    piece_row = piece_rows_by_id.get(piece_id) or {}
                    return str(piece_row.get("color") or "").strip()

                layout_data = {}
                nominal_rects = {
                    instance_key: nominal_scene_rect(scene_item)
                    for instance_key, scene_item in item_by_instance_id.items()
                }
                if nominal_rects:
                    min_scene_x = min(rect.left() for rect in nominal_rects.values())
                    max_scene_y = max(rect.bottom() for rect in nominal_rects.values())
                else:
                    min_scene_x = 0.0
                    max_scene_y = 0.0
                for instance_key, scene_item in item_by_instance_id.items():
                    scene_pos = scene_item.pos()
                    rotation_deg = scene_item.rotation()
                    item_rect = scene_item.rect()
                    nominal_rect = nominal_rects.get(instance_key)
                    origin_scene_point = scene_item.mapToScene(item_rect.left(), item_rect.bottom())
                    piece_id = str(scene_item.data(1) or "").strip()
                    footprint_x_mm = nominal_rect.left() - min_scene_x if nominal_rect is not None else 0.0
                    footprint_y_mm = max_scene_y - nominal_rect.bottom() if nominal_rect is not None else 0.0
                    layout_data[instance_key] = {
                        "layout_version": 2,
                        "instance_key": instance_key,
                        "piece_id": piece_id,
                        "x": round(scene_pos.x(), 2),
                        "y": round(scene_pos.y(), 2),
                        "rotation": round(rotation_deg, 2),
                        "scene_x": round(scene_pos.x(), 2),
                        "scene_y": round(scene_pos.y(), 2),
                        "rotation_deg": round(rotation_deg, 2),
                        "x_mm": round(origin_scene_point.x() - min_scene_x, 2),
                        "y_mm": round(max_scene_y - origin_scene_point.y(), 2),
                        "footprint_x_mm": round(footprint_x_mm, 2),
                        "footprint_y_mm": round(footprint_y_mm, 2),
                        "footprint_width_mm": (
                            round(nominal_rect.width(), 2) if nominal_rect is not None else 0.0
                        ),
                        "footprint_height_mm": (
                            round(nominal_rect.height(), 2) if nominal_rect is not None else 0.0
                        ),
                        "width_mm": round(item_rect.width(), 2),
                        "height_mm": round(item_rect.height(), 2),
                        "color": instance_piece_color(piece_id),
                        **instance_grain_fields(piece_id, item_rect, rotation_deg),
                    }
                return layout_data

            def collect_en_juego_composition_data(layout_data: dict) -> dict:
                grain_axes = {
                    str(stored.get("grain_axis_composition") or "").strip().lower()
                    for stored in layout_data.values()
                    if isinstance(stored, dict)
                    and str(stored.get("grain_axis_composition") or "").strip().lower() in {"x", "y"}
                }
                if not grain_axes:
                    grain_axis = "none"
                    grain_direction = "0"
                    grain_status = "ok"
                elif len(grain_axes) == 1:
                    grain_axis = next(iter(grain_axes))
                    grain_direction = "2" if grain_axis == "x" else "1"
                    grain_status = "ok"
                else:
                    grain_axis = "mixed"
                    grain_direction = "mixed"
                    grain_status = "mixed"
                return {
                    "layout_version": 2,
                    "composition_grain_direction": grain_direction,
                    "composition_grain_axis": grain_axis,
                    "composition_grain_status": grain_status,
                }

            def save_en_juego_composition_layout():
                layout_data = collect_en_juego_layout_data()
                config_data["en_juego_layout"] = layout_data
                config_data["en_juego_composition"] = collect_en_juego_composition_data(layout_data)

            def save_en_juego_layout():
                sync_en_juego_settings_from_controls()
                save_en_juego_composition_layout()
                config_data["en_juego_settings"] = dict(en_juego_settings)
                persist_module_config()
                config_dialog.accept()

            def create_en_juego_pgmx_from_dialog():
                sync_en_juego_settings_from_controls()
                if en_juego_settings.get("cut_mode") != "nesting":
                    QMessageBox.information(
                        config_dialog,
                        "Crear En-Juego",
                        "La generación del En-Juego automático solo está disponible con 'Corte Nesting'.",
                    )
                    return

                from core.en_juego_synthesis import create_en_juego_pgmx

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

                sync_en_juego_settings_from_controls()
                save_en_juego_composition_layout()
                config_data["en_juego_settings"] = dict(en_juego_settings)
                persist_module_config()

                try:
                    result = create_en_juego_pgmx(
                        project=self.project,
                        module_name=module_name,
                        module_path=module_path,
                        piece_rows=all_rows,
                        saved_layout=config_data.get("en_juego_layout", {}),
                        settings=config_data.get("en_juego_settings", {}),
                        output_path=Path(output_file),
                    )
                except Exception as exc:
                    QMessageBox.critical(
                        config_dialog,
                        "Crear En-Juego",
                        f"No se pudo generar el archivo En-Juego.\n\n{exc}",
                    )
                    return

                generated_output_path = Path(result.output_path)
                try:
                    output_for_config = str(
                        generated_output_path.resolve().relative_to(module_path.resolve())
                    ).replace("\\", "/")
                except Exception:
                    output_for_config = str(generated_output_path)
                config_data["en_juego_output_path"] = output_for_config

                sync_en_juego_observations()
                persist_module_config()
                refresh_pieces_table()

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

            view_buttons_layout = QHBoxLayout()
            view_buttons_layout.setContentsMargins(0, 0, 0, 0)
            view_buttons_layout.setSpacing(8)
            fit_view_btn = QPushButton("Ajustar\nVista")
            rotate_left_btn = QPushButton("Rotar\n-90°")
            rotate_right_btn = QPushButton("Rotar\n+90°")
            for button in (fit_view_btn, rotate_left_btn, rotate_right_btn):
                button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            fit_view_btn.clicked.connect(lambda: view.fitInView(scene.itemsBoundingRect().adjusted(-80, -80, 80, 80), Qt.KeepAspectRatio))
            rotate_left_btn.clicked.connect(lambda: rotate_selected_piece(-90.0))
            rotate_right_btn.clicked.connect(lambda: rotate_selected_piece(90.0))
            view_buttons_layout.addWidget(fit_view_btn)
            view_buttons_layout.addWidget(rotate_left_btn)
            view_buttons_layout.addWidget(rotate_right_btn)
            create_en_juego_btn = QPushButton("Crear\nEn-Juego")
            save_layout_btn = QPushButton("Guardar\nDisposición")
            close_layout_btn = QPushButton("Cerrar")
            for button in (create_en_juego_btn, save_layout_btn, close_layout_btn):
                button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
            create_en_juego_btn.clicked.connect(create_en_juego_pgmx_from_dialog)
            save_layout_btn.clicked.connect(save_en_juego_layout)
            close_layout_btn.clicked.connect(config_dialog.reject)
            configure_division_btn.clicked.connect(open_en_juego_settings_dialog_v2)
            configure_squaring_btn.clicked.connect(open_en_juego_squaring_settings_dialog_v2)
            view_buttons_layout.addStretch()
            view_buttons_layout.addWidget(create_en_juego_btn)
            view_buttons_layout.addWidget(save_layout_btn)
            view_buttons_layout.addWidget(close_layout_btn)
            view_panel_layout.addLayout(view_buttons_layout)

            def refresh_cut_mode_controls(*, enforce_spacing: bool = False):
                sync_en_juego_settings_from_controls()
                is_nesting_mode = en_juego_settings.get("cut_mode") == "nesting"
                origin_group.setEnabled(is_nesting_mode)
                operation_order_group.setEnabled(is_nesting_mode)
                configure_division_btn.setEnabled(is_nesting_mode)
                configure_squaring_btn.setEnabled(is_nesting_mode)
                create_en_juego_btn.setEnabled(is_nesting_mode)
                spacing_hint_label.setText(
                    "Separación mínima actual: "
                    f"{_compact_number(effective_piece_spacing_mm())} mm"
                )
                if enforce_spacing:
                    enforce_minimum_piece_spacing()
                update_dimension_annotations()

            manual_cut_radio.toggled.connect(lambda *_: refresh_cut_mode_controls(enforce_spacing=True))
            nesting_cut_radio.toggled.connect(lambda *_: refresh_cut_mode_controls(enforce_spacing=True))
            refresh_cut_mode_controls()

            config_dialog.setLayout(main_layout)
            _exec_centered(config_dialog, inspect_dialog)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.addWidget(pieces_table, 1)

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
        refresh_configure_en_juego_button_state()

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

        actions_column.addWidget(add_piece_btn)
        actions_column.addWidget(edit_piece_btn)
        actions_column.addWidget(delete_piece_btn)
        actions_column.addWidget(move_piece_up_btn)
        actions_column.addWidget(move_piece_down_btn)
        actions_column.addWidget(repair_pgmx_btn)
        actions_column.addWidget(configure_en_juego_btn)

        content_row.addLayout(actions_column)
        layout.addLayout(content_row, 1)

        add_piece_btn.clicked.connect(add_manual_piece)
        edit_piece_btn.clicked.connect(edit_selected_piece)
        pieces_table.cellDoubleClicked.connect(edit_piece_from_table_double_click)
        delete_piece_btn.clicked.connect(remove_selected_piece)
        move_piece_up_btn.clicked.connect(lambda: move_selected_piece(-1))
        move_piece_down_btn.clicked.connect(lambda: move_selected_piece(1))
        repair_pgmx_btn.clicked.connect(repair_selected_invalid_pgmx)
        configure_en_juego_btn.clicked.connect(open_en_juego_configuration_dialog)
        pieces_table.itemSelectionChanged.connect(refresh_repair_pgmx_button_state)
        pieces_table.itemSelectionChanged.connect(refresh_piece_order_button_state)
        refresh_repair_pgmx_button_state()
        refresh_piece_order_button_state()

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

        actions_column.addStretch(1)

        save_btn = QPushButton("Guardar")
        save_btn.setToolTip("Guardar Configuración")
        save_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_btn.clicked.connect(save_module_settings)
        close_btn = QPushButton("Cerrar")
        close_btn.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_btn.clicked.connect(request_close_dialog)

        actions_column.addWidget(save_btn)
        actions_column.addWidget(close_btn)

        inspect_dialog.setLayout(layout)
        _exec_centered(inspect_dialog, parent_dialog)

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
            if optimization_mode != "Sin optimizar":
                detail_lines.append(f"Metodo de guillotina: {result.get('guillotine_algorithm')}")
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

    def _default_output_start_dir(self, path_key: str) -> str:
        default_paths = _normalize_default_paths(_read_app_settings().get("default_paths"))
        configured_value = str(default_paths.get(path_key, "")).strip()
        configured_path = Path(configured_value) if configured_value else None
        if configured_path is not None and configured_path.is_dir():
            return str(configured_path)
        project_root = Path(getattr(self.project, "root_directory", "") or "")
        if str(project_root) and project_root.is_dir():
            return str(project_root)
        return str(Path.home())

    def _safe_output_filename(self, value: str, fallback: str) -> str:
        raw = str(value or "").strip() or fallback
        invalid_chars = '<>:"/\\|?*'
        cleaned = "".join("_" if char in invalid_chars or ord(char) < 32 else char for char in raw)
        return cleaned.strip(" ._") or fallback

    def _output_relative_path(self, value: str, fallback: str) -> Path:
        raw = str(value or "").strip()
        relative_path = Path(raw) if raw else Path(fallback)
        if relative_path.is_absolute():
            try:
                relative_path = relative_path.resolve().relative_to(Path(self.project.root_directory).resolve())
            except Exception:
                relative_path = Path(relative_path.name)
        parts = [
            self._safe_output_filename(part, "carpeta")
            for part in relative_path.parts
            if part not in {"", ".", ".."}
        ]
        if not parts:
            parts = [self._safe_output_filename(fallback, "carpeta")]
        return Path(*parts)

    def _project_cnc_output_root(self, selected_project: Project, output_root: Path) -> Path:
        project_root_name = Path(str(selected_project.root_directory or "")).name.strip()
        project_folder_name = self._safe_output_filename(
            project_root_name or selected_project.name,
            "Proyecto",
        )
        return output_root / project_folder_name

    def _create_plan_sheet_output_structure(self, selected_project: Project, output_root: Path) -> dict[str, Path]:
        project_output_root = self._project_cnc_output_root(selected_project, output_root)
        project_output_root.mkdir(parents=True, exist_ok=True)
        locale_dirs: dict[str, Path] = {}

        for locale in selected_project.locales:
            locale_dir = project_output_root / self._output_relative_path(locale.path, locale.name)
            locale_dir.mkdir(parents=True, exist_ok=True)
            locale_dirs[locale.name.strip().lower()] = locale_dir

        for module in selected_project.modules:
            module_dir = self._module_cnc_output_dir(selected_project, output_root, module)
            module_dir.mkdir(parents=True, exist_ok=True)

        return locale_dirs

    def _module_cnc_output_dir(self, selected_project: Project, output_root: Path, module: ModuleData) -> Path:
        project_output_root = self._project_cnc_output_root(selected_project, output_root)
        locales_by_key = {
            locale.name.strip().lower(): locale
            for locale in selected_project.locales
        }
        module_relative = str(module.relative_path or "").strip()
        if not module_relative:
            locale_key = str(module.locale_name or "").strip().lower()
            locale = locales_by_key.get(locale_key)
            locale_relative = self._output_relative_path(
                locale.path if locale is not None else module.locale_name,
                module.locale_name or "local",
            )
            module_relative = str(locale_relative / module.name)
        return project_output_root / self._output_relative_path(module_relative, module.name)

    def _unique_iso_output_path(
        self,
        module_output_dir: Path,
        pgmx_path: Path,
        used_stems: set[str],
        piece: Piece,
    ) -> Path:
        base_stem = self._safe_output_filename(pgmx_path.stem, "programa")
        stem = base_stem
        if stem.lower() in used_stems:
            piece_label = self._safe_output_filename(
                str(piece.id or piece.name or "").strip(),
                "",
            )
            if piece_label:
                stem = f"{base_stem}_{piece_label}"

        candidate_stem = stem
        suffix = 2
        while candidate_stem.lower() in used_stems:
            candidate_stem = f"{stem}_{suffix}"
            suffix += 1

        used_stems.add(candidate_stem.lower())
        return module_output_dir / f"{candidate_stem}.iso"

    def _export_project_iso_files(self, selected_project: Project, output_root: Path) -> dict:
        from core.pgmx_processing import resolve_piece_program_path
        from iso_state_synthesis.emitter import emit_candidate_for_pgmx

        generated_paths: list[Path] = []
        skipped_missing: list[dict] = []
        skipped_failed: list[dict] = []
        warnings: list[dict] = []
        duplicate_sources = 0
        used_stems_by_dir: dict[Path, set[str]] = {}
        converted_by_module_source: dict[tuple[str, str], Path] = {}

        for module in selected_project.modules:
            module_path = Path(module.path)
            module_output_dir = self._module_cnc_output_dir(selected_project, output_root, module)
            module_output_dir.mkdir(parents=True, exist_ok=True)
            used_stems = used_stems_by_dir.setdefault(module_output_dir, set())
            module_key = str(module.relative_path or module.path).strip().lower()

            for piece in module.pieces:
                source_value = str(piece.cnc_source or piece.f6_source or "").strip()
                if not source_value:
                    continue

                source_path = resolve_piece_program_path(selected_project, piece, module_path)
                piece_label = str(piece.id or piece.name or "").strip() or "(sin ID)"
                if source_path is None or source_path.suffix.lower() != ".pgmx":
                    skipped_missing.append(
                        {
                            "module": module.name,
                            "piece": piece_label,
                            "source": source_value,
                        }
                    )
                    continue

                try:
                    source_key = str(source_path.resolve()).lower()
                except OSError:
                    source_key = str(source_path).lower()
                conversion_key = (module_key, source_key)
                if conversion_key in converted_by_module_source:
                    duplicate_sources += 1
                    continue

                output_path = self._unique_iso_output_path(module_output_dir, source_path, used_stems, piece)
                try:
                    program = emit_candidate_for_pgmx(source_path, program_name=output_path.stem)
                    program.write_text(output_path)
                except Exception as exc:
                    skipped_failed.append(
                        {
                            "module": module.name,
                            "piece": piece_label,
                            "source": str(source_path),
                            "error": str(exc),
                        }
                    )
                    continue

                converted_by_module_source[conversion_key] = output_path
                generated_paths.append(output_path)
                for warning in program.warnings:
                    warnings.append(
                        {
                            "module": module.name,
                            "piece": piece_label,
                            "source": str(source_path),
                            "code": warning.code,
                            "message": warning.message,
                        }
                    )

        return {
            "generated_paths": generated_paths,
            "missing": skipped_missing,
            "failed": skipped_failed,
            "warnings": warnings,
            "duplicate_sources": duplicate_sources,
        }

    def _production_output_base_name(self, project: Project) -> str:
        name_parts = [str(project.name or "Proyecto").strip()]
        client_name = str(project.client or "").strip()
        if client_name:
            name_parts.append(client_name)
        return self._safe_output_filename(" - ".join(name_parts), "Proyecto")

    def _project_for_single_locale(self, selected_project: Project, locale: LocaleData) -> Project:
        locale_key = locale.name.strip().lower()
        locale_modules = [
            module
            for module in selected_project.modules
            if str(module.locale_name or "").strip().lower() == locale_key
        ]
        return Project(
            name=selected_project.name,
            root_directory=selected_project.root_directory,
            project_data_file=selected_project.project_data_file,
            client=selected_project.client,
            created_at=selected_project.created_at,
            locales=[locale],
            modules=locale_modules,
            output_directory=selected_project.output_directory,
        )

    def generate_sheets(self):
        if not self.project.modules:
            QMessageBox.warning(self, "Generar Planillas", "No hay módulos cargados. Procese el proyecto primero.")
            return

        selected_project = self._project_for_selected_locales("Generar Planillas")
        if selected_project is None:
            return

        output_root_value = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta raiz para estructura de archivos CNC",
            self._default_output_start_dir("cnc_files"),
        )
        if not output_root_value:
            return
        output_root = Path(output_root_value)

        # Loop para permitir reintentos
        while True:
            progress_dialog = None
            try:
                from core.pgmx_processing import generate_project_piece_drawings
                from core.summary import export_production_sheet, export_production_sheet_pdf

                locale_work_items = []
                for locale in selected_project.locales:
                    locale_project = self._project_for_single_locale(selected_project, locale)
                    if locale_project.modules:
                        locale_work_items.append((locale, locale_project))

                total_steps = max(1, 3 + len(locale_work_items))
                progress_step = 0
                progress_dialog = QProgressDialog(
                    "Preparando generación de archivos...",
                    "",
                    0,
                    total_steps,
                    self,
                )
                progress_dialog.setWindowTitle("Generar Planillas")
                progress_dialog.setWindowModality(Qt.ApplicationModal)
                progress_dialog.setCancelButton(None)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setAutoClose(False)
                progress_dialog.setAutoReset(False)
                progress_dialog.setValue(0)
                progress_dialog.show()
                QApplication.processEvents()

                def update_progress(message: str, *, advance: bool = True) -> None:
                    nonlocal progress_step
                    if progress_dialog is None:
                        return
                    if advance:
                        progress_step = min(total_steps, progress_step + 1)
                    progress_dialog.setLabelText(message)
                    progress_dialog.setValue(progress_step)
                    QApplication.processEvents()

                update_progress("Generando dibujos de piezas desde PGMX...", advance=False)
                generate_project_piece_drawings(selected_project)
                update_progress("Dibujos de piezas generados.")

                update_progress("Creando estructura de carpetas...", advance=False)
                project_output_root = self._project_cnc_output_root(selected_project, output_root)
                locale_dirs = self._create_plan_sheet_output_structure(selected_project, output_root)
                update_progress("Estructura de carpetas creada.")

                update_progress("Convirtiendo programas PGMX asociados a ISO...", advance=False)
                iso_result = self._export_project_iso_files(selected_project, output_root)
                update_progress("Conversion ISO finalizada.")

                base_name = self._production_output_base_name(selected_project)
                generated_pdf_paths: list[Path] = []
                for locale, locale_project in locale_work_items:
                    locale_key = locale.name.strip().lower()
                    locale_dir = locale_dirs.get(locale_key)
                    if locale_dir is None:
                        locale_dir = project_output_root / self._output_relative_path(locale.path, locale.name)
                        locale_dir.mkdir(parents=True, exist_ok=True)
                    pdf_base_name = self._safe_output_filename(
                        f"{base_name} - {locale.name}",
                        "Planilla",
                    )
                    update_progress(f"Generando PDF del local {locale.name}...", advance=False)
                    generated_pdf_paths.append(
                        export_production_sheet_pdf(
                            locale_project,
                            locale_dir / f"{pdf_base_name}.pdf",
                        )
                    )
                    update_progress(f"PDF del local {locale.name} generado.")

                if progress_dialog is not None:
                    progress_dialog.setLabelText("Estructura, ISO y PDF generados.")
                    progress_dialog.setValue(total_steps)
                    QApplication.processEvents()
                    progress_dialog.close()
                    progress_dialog = None

                excel_default_path = str(Path(self._default_output_start_dir("excel_sheets")) / f"{base_name}.xlsx")
                excel_output_file, _ = QFileDialog.getSaveFileName(
                    self,
                    "Guardar planilla Excel",
                    excel_default_path,
                    "Excel (*.xlsx)",
                )
                generated_excel_path = None
                if excel_output_file:
                    excel_output_path = Path(excel_output_file)
                    if excel_output_path.suffix.lower() != ".xlsx":
                        excel_output_path = excel_output_path.with_suffix(".xlsx")
                    generated_excel_path = export_production_sheet(
                        selected_project,
                        excel_output_path,
                    )

                detail_lines = [
                    "Planillas generadas correctamente.",
                    "",
                    f"Carpeta raiz seleccionada: {output_root}",
                    f"Carpeta proyecto CNC: {project_output_root}",
                ]
                if generated_excel_path is not None:
                    detail_lines.append(f"Excel: {generated_excel_path}")
                else:
                    detail_lines.append("Excel: no guardado.")
                if generated_pdf_paths:
                    detail_lines.append("PDF por local:")
                    detail_lines.extend(str(path) for path in generated_pdf_paths)
                generated_iso_paths = iso_result.get("generated_paths", [])
                missing_iso_sources = iso_result.get("missing", [])
                failed_iso_sources = iso_result.get("failed", [])
                iso_warnings = iso_result.get("warnings", [])
                duplicate_iso_sources = int(iso_result.get("duplicate_sources") or 0)
                detail_lines.append(f"ISO generados: {len(generated_iso_paths)}")
                if duplicate_iso_sources:
                    detail_lines.append(f"PGMX repetidos reutilizados: {duplicate_iso_sources}")
                if missing_iso_sources:
                    detail_lines.append(f"PGMX asociados no encontrados: {len(missing_iso_sources)}")
                if failed_iso_sources:
                    detail_lines.append(f"PGMX no convertidos a ISO: {len(failed_iso_sources)}")
                    for failed_item in failed_iso_sources[:5]:
                        detail_lines.append(
                            "  - "
                            f"{failed_item.get('module', '')} / {failed_item.get('piece', '')}: "
                            f"{failed_item.get('error', '')}"
                        )
                if iso_warnings:
                    detail_lines.append(f"Advertencias ISO: {len(iso_warnings)}")
                QMessageBox.information(
                    self,
                    "Generar Planillas",
                    "\n".join(detail_lines),
                )
                break  # Éxito, salir del loop
            except Exception as exc:
                if progress_dialog is not None:
                    progress_dialog.close()
                    progress_dialog = None
                # Mostrar error con opciones de reintentar
                error_msg = f"No se pudieron generar las planillas:\n\n{exc}"
                
                # Crear un diálogo personalizado con más opciones
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Generar Planillas - Error")
                dlg.setText(error_msg)
                dlg.setIcon(QMessageBox.Critical)
                
                retry_btn = dlg.addButton("Reintentar", QMessageBox.ActionRole)
                change_location_btn = dlg.addButton("Guardar en otro lugar", QMessageBox.ActionRole)
                cancel_btn = dlg.addButton("Cancelar", QMessageBox.RejectRole)
                
                _exec_centered(dlg, self)
                
                if dlg.clickedButton() == cancel_btn:
                    break  # Usuario cancela, salir del loop
                elif dlg.clickedButton() == change_location_btn:
                    new_output_root = QFileDialog.getExistingDirectory(
                        self,
                        "Seleccionar carpeta raiz para estructura de archivos CNC",
                        str(output_root),
                    )
                    if new_output_root:
                        output_root = Path(new_output_root)
                    else:
                        break

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


class BoardEditDialog(QDialog):
    def __init__(self, board: dict | None = None, parent=None):
        super().__init__(parent)
        self.board_data: dict | None = None
        self.setWindowTitle("Editar tablero" if board else "Nuevo tablero")
        self.setModal(True)
        self.setMinimumWidth(420)

        board = dict(board or {})

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel("Complete los datos del tablero."))
        self.color_field = QLineEdit(str(board.get("color") or ""))
        self.length_field = QLineEdit(str(board.get("length") or "2750"))
        self.width_field = QLineEdit(str(board.get("width") or "1830"))
        self.thickness_field = QLineEdit(str(board.get("thickness") or "18"))
        self.margin_field = QLineEdit(str(board.get("margin") or "0"))
        self.grain_field = QComboBox()
        self.grain_field.addItems(BOARD_GRAIN_OPTIONS)
        current_grain = _normalize_board_grain(board.get("grain") or board.get("veta"))
        self.grain_field.setCurrentText(current_grain)

        label_width = 78
        field_width = 220
        self.color_field.setFixedWidth(field_width)
        self.length_field.setFixedWidth(field_width)
        self.width_field.setFixedWidth(field_width)
        self.thickness_field.setFixedWidth(field_width)
        self.margin_field.setFixedWidth(field_width)
        self.grain_field.setFixedWidth(field_width)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(6)

        def add_form_row(row_index: int, label_text: str, field: QWidget):
            label = QLabel(label_text)
            label.setFixedWidth(label_width)
            form_grid.addWidget(label, row_index, 0)
            form_grid.addWidget(field, row_index, 1, alignment=Qt.AlignLeft)

        add_form_row(0, "Color", self.color_field)
        add_form_row(1, "Longitud", self.length_field)
        add_form_row(2, "Ancho", self.width_field)
        add_form_row(3, "Espesor", self.thickness_field)
        add_form_row(4, "Margen", self.margin_field)
        add_form_row(5, "Veta", self.grain_field)
        layout.addLayout(form_grid)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, 0, 0)
        buttons_row.setSpacing(8)
        buttons_row.addStretch(1)
        save_button = QPushButton("Guardar")
        cancel_button = QPushButton("Cancelar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
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
        self.boards_table.setColumnWidth(1, 84)
        self.boards_table.setColumnWidth(2, 84)
        self.boards_table.setColumnWidth(3, 84)
        self.boards_table.setColumnWidth(4, 72)
        self.boards_table.itemDoubleClicked.connect(lambda _item: self.edit_board())

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(8)
        content_row.addWidget(self.boards_table, 1)

        buttons_column = QVBoxLayout()
        buttons_column.setContentsMargins(0, 0, 0, 0)
        buttons_column.setSpacing(8)
        new_button = QPushButton("Nuevo")
        edit_button = QPushButton("Editar")
        delete_button = QPushButton("Eliminar")
        close_button = QPushButton("Cerrar")
        for button in (new_button, edit_button, delete_button, close_button):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        new_button.clicked.connect(self.add_board)
        edit_button.clicked.connect(self.edit_board)
        delete_button.clicked.connect(self.delete_board)
        close_button.clicked.connect(self.accept)
        buttons_column.addWidget(new_button)
        buttons_column.addWidget(edit_button)
        buttons_column.addWidget(delete_button)
        buttons_column.addStretch(1)
        buttons_column.addWidget(close_button)
        content_row.addLayout(buttons_column)
        layout.addLayout(content_row, 1)

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
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.board_data is None:
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
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.board_data is None:
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


class ToolsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Herramientas")
        self.setModal(True)
        self.resize(1080, 480)
        self.tools = _load_tool_catalog_rows()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Herramientas disponibles en el catálogo y regla de uso por tipo."))

        self.tools_table = QTableWidget()
        self.tools_table.setColumnCount(10)
        self.tools_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Código",
                "Descripción",
                "Tipo",
                "Familia",
                "Uso permitido",
                "Porta",
                "Ø",
                "L. hund.",
                "Offset",
            ]
        )
        self.tools_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tools_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tools_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tools_table.setAlternatingRowColors(True)
        self.tools_table.verticalHeader().setVisible(False)
        header = self.tools_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        layout.addWidget(self.tools_table, 1)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        close_button = QPushButton("Cerrar")
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)
        self.refresh_tools_table()

    def refresh_tools_table(self):
        self.tools = _load_tool_catalog_rows()
        self.tools_table.setRowCount(len(self.tools))
        for row_idx, tool in enumerate(self.tools):
            row_values = [
                str(tool.get("tool_id") or ""),
                str(tool.get("name") or ""),
                str(tool.get("description") or ""),
                str(tool.get("type") or ""),
                _tool_usage_family_label(tool.get("type")),
                _tool_usage_label(tool.get("type")),
                str(tool.get("holder_key") or ""),
                str(tool.get("diameter") or ""),
                str(tool.get("sinking_length") or ""),
                str(tool.get("tool_offset_length") or ""),
            ]
            for column_idx, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if column_idx in {0, 7, 8, 9}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.tools_table.setItem(row_idx, column_idx, item)
        if self.tools:
            self.tools_table.selectRow(0)


class CutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cortes")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.settings = _read_app_settings()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración de cortes y separación."))

        label_width = 170
        field_width = 160

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(8)

        optimization_label = QLabel("Optimización de cortes")
        optimization_label.setFixedWidth(label_width)
        self.cut_optimization_field = QComboBox()
        self.cut_optimization_field.addItems(CUT_OPTIMIZATION_OPTIONS)
        self.cut_optimization_field.setCurrentText(
            _normalize_cut_optimization_option(self.settings.get("cut_optimization_mode"))
        )
        self.cut_optimization_field.setFixedWidth(field_width)
        form_grid.addWidget(optimization_label, 0, 0)
        form_grid.addWidget(self.cut_optimization_field, 0, 1, alignment=Qt.AlignLeft)

        squaring_label = QLabel("Adicional para escuadrado")
        squaring_label.setFixedWidth(label_width)
        self.cut_squaring_field = QLineEdit(
            str(_compact_number(self.settings.get("cut_squaring_allowance", 10)))
        )
        self.cut_squaring_field.setPlaceholderText("10")
        self.cut_squaring_field.setFixedWidth(field_width)
        form_grid.addWidget(squaring_label, 1, 0)
        form_grid.addWidget(self.cut_squaring_field, 1, 1, alignment=Qt.AlignLeft)

        saw_kerf_label = QLabel("Espesor de Sierra")
        saw_kerf_label.setFixedWidth(label_width)
        self.cut_saw_kerf_field = QLineEdit(
            str(_compact_number(self.settings.get("cut_saw_kerf", 4)))
        )
        self.cut_saw_kerf_field.setPlaceholderText("4")
        self.cut_saw_kerf_field.setFixedWidth(field_width)
        form_grid.addWidget(saw_kerf_label, 2, 0)
        form_grid.addWidget(self.cut_saw_kerf_field, 2, 1, alignment=Qt.AlignLeft)

        layout.addLayout(form_grid)

        buttons_row = QHBoxLayout()
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_settings)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def save_settings(self):
        squaring_raw = self.cut_squaring_field.text().strip() or "10"
        saw_kerf_raw = self.cut_saw_kerf_field.text().strip() or "4"

        def parse_non_negative_measure(raw_value: str, field_name: str) -> float | None:
            try:
                value = float(raw_value.replace(",", "."))
            except ValueError:
                QMessageBox.warning(self, "Cortes", f"{field_name} debe ser un número.")
                return None
            if value < 0:
                QMessageBox.warning(self, "Cortes", f"{field_name} debe ser mayor o igual a cero.")
                return None
            return value

        squaring_allowance = parse_non_negative_measure(squaring_raw, "El adicional para escuadrado")
        if squaring_allowance is None:
            return

        saw_kerf = parse_non_negative_measure(saw_kerf_raw, "El espesor de sierra")
        if saw_kerf is None:
            return

        current_settings = _read_app_settings()
        current_settings["cut_squaring_allowance"] = _compact_number(squaring_allowance)
        current_settings["cut_saw_kerf"] = _compact_number(saw_kerf)
        current_settings["cut_optimization_mode"] = _normalize_cut_optimization_option(
            self.cut_optimization_field.currentText()
        )
        _write_app_settings(current_settings)
        self.settings = current_settings
        QMessageBox.information(self, "Cortes", "Configuración guardada.")


class PieceTemplateEditDialog(QDialog):
    def __init__(self, template_entry: dict | None = None, parent=None):
        super().__init__(parent)
        self.template_data: dict | None = None
        self.original_template = dict(template_entry or {})
        self.setWindowTitle("Editar plantilla" if template_entry else "Nueva plantilla")
        self.setModal(True)
        editor_scale, _, _ = _apply_responsive_window_size(
            self,
            720,
            400,
            width_ratio=0.84,
            height_ratio=0.80,
        )

        normalized_template = _normalize_manual_piece_template_entry(template_entry or {}) or {}

        self.id_field = QLineEdit(str(normalized_template.get("id") or ""))
        self.name_field = QLineEdit(str(normalized_template.get("name") or ""))
        self.quantity_field = QLineEdit(
            str(_parse_piece_quantity_value(normalized_template.get("quantity"), default=1))
        )
        self.height_field = QLineEdit(
            "" if normalized_template.get("height") is None else str(normalized_template.get("height"))
        )
        self.width_field = QLineEdit(
            "" if normalized_template.get("width") is None else str(normalized_template.get("width"))
        )
        self.thickness_field = QLineEdit(
            "" if normalized_template.get("thickness") is None else str(normalized_template.get("thickness"))
        )
        self.color_field = QLineEdit(str(normalized_template.get("color") or ""))
        self.grain_field = QComboBox()
        self.source_field = QLineEdit(str(normalized_template.get("source") or ""))

        self.grain_field.addItem("Sin veta", "0")
        self.grain_field.addItem("Alto", "1")
        self.grain_field.addItem("Ancho", "2")
        current_grain = normalize_piece_grain_direction(normalized_template.get("grain_direction"))
        if current_grain == "1":
            self.grain_field.setCurrentIndex(1)
        elif current_grain == "2":
            self.grain_field.setCurrentIndex(2)
        else:
            self.grain_field.setCurrentIndex(0)

        editor_inline_button_width = MAIN_ACTION_BUTTON_WIDTH
        editor_inline_button_height = MAIN_ACTION_BUTTON_HEIGHT
        top_fields_spacing = 8
        editor_field_block_spacing = 1
        editor_label_height = QLabel("X").sizeHint().height()
        editor_field_height = max(
            self.id_field.sizeHint().height(),
            self.grain_field.sizeHint().height(),
            self.source_field.sizeHint().height(),
        )
        editor_field_row_height = editor_label_height + editor_field_block_spacing + editor_field_height
        editor_inline_row_height = editor_label_height + editor_field_block_spacing + editor_inline_button_height
        id_field_width = _scaled_int(120, max(editor_scale, 0.82), 90)
        quantity_field_width = _scaled_int(80, max(editor_scale, 0.82), 60)
        dimension_field_width = _scaled_int(90, max(editor_scale, 0.82), 68)
        color_grain_field_width = _scaled_int(104, max(editor_scale, 0.82), 82)

        self.id_field.setFixedWidth(id_field_width)
        self.quantity_field.setFixedWidth(quantity_field_width)
        self.height_field.setFixedWidth(dimension_field_width)
        self.width_field.setFixedWidth(dimension_field_width)
        self.thickness_field.setFixedWidth(dimension_field_width)
        self.name_field.setFixedWidth((dimension_field_width * 3) + (top_fields_spacing * 2))
        self.color_field.setMinimumWidth(color_grain_field_width)
        self.grain_field.setMinimumWidth(color_grain_field_width)
        self.color_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.grain_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.source_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        def build_labeled_field_widget(
            label_text: str,
            field: QWidget,
            row_height: int = editor_field_row_height,
        ) -> QWidget:
            label = QLabel(label_text)
            label.setFixedHeight(editor_label_height)
            column_layout = QVBoxLayout()
            column_layout.setSpacing(editor_field_block_spacing)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.addStretch(1)
            column_layout.addWidget(label)
            column_layout.addWidget(field)
            column_widget = QWidget()
            column_widget.setFixedHeight(row_height)
            column_widget.setLayout(column_layout)
            return column_widget

        def available_board_colors(piece_thickness: float | None = None) -> list[str]:
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

        def parse_optional_piece_float(raw_value: str):
            raw_text = (raw_value or "").strip().replace(",", ".")
            if not raw_text:
                return None
            try:
                return float(raw_text)
            except ValueError:
                return None

        def select_color_from_boards():
            piece_thickness = parse_optional_piece_float(self.thickness_field.text())
            available_colors = available_board_colors(piece_thickness=piece_thickness)
            if not available_colors:
                thickness_label = (
                    f" para espesor {int(piece_thickness) if float(piece_thickness).is_integer() else piece_thickness} mm"
                    if piece_thickness is not None
                    else ""
                )
                QMessageBox.warning(
                    self,
                    "Piezas",
                    f"No hay colores disponibles en los tableros configurados{thickness_label}.",
                )
                return

            current_color = self.color_field.text().strip()
            selected_index = 0
            if current_color:
                for color_index, color_value in enumerate(available_colors):
                    if color_value.strip().lower() == current_color.lower():
                        selected_index = color_index
                        break

            selected_color, ok = QInputDialog.getItem(
                self,
                "Seleccionar color",
                "Color:",
                available_colors,
                selected_index,
                False,
            )
            if ok:
                self.color_field.setText(str(selected_color or "").strip())

        def select_source():
            source_file, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar programa asociado",
                "",
                "Programas PGMX (*.pgmx);;Todos los archivos (*.*)",
            )
            if source_file:
                self.source_field.setText(source_file)

        top_fields_grid = QGridLayout()
        top_fields_grid.setHorizontalSpacing(top_fields_spacing)
        top_fields_grid.setVerticalSpacing(2)
        top_fields_grid.setContentsMargins(0, 0, 0, 0)

        id_column = build_labeled_field_widget("ID:", self.id_field)
        name_column = build_labeled_field_widget("Nombre:", self.name_field)
        height_column = build_labeled_field_widget("Alto:", self.height_field)
        width_column = build_labeled_field_widget("Ancho:", self.width_field)
        thickness_column = build_labeled_field_widget("Espesor:", self.thickness_field)
        qty_column = build_labeled_field_widget("Cantidad:", self.quantity_field)

        top_fields_grid.addWidget(id_column, 0, 0)
        top_fields_grid.addWidget(name_column, 0, 1, 1, 3)
        top_fields_grid.addWidget(qty_column, 1, 0)
        top_fields_grid.addWidget(height_column, 1, 1)
        top_fields_grid.addWidget(width_column, 1, 2)
        top_fields_grid.addWidget(thickness_column, 1, 3)
        top_fields_grid.setColumnStretch(4, 1)

        select_color_btn = QPushButton("Seleccionar")
        select_color_btn.setFixedSize(editor_inline_button_width, editor_inline_button_height)
        select_color_btn.setDefault(False)
        select_color_btn.setAutoDefault(False)
        select_color_btn.setFocusPolicy(Qt.NoFocus)
        select_color_btn.clicked.connect(select_color_from_boards)

        color_column = build_labeled_field_widget(
            "Color:",
            self.color_field,
            row_height=editor_inline_row_height,
        )
        grain_column = build_labeled_field_widget(
            "Veta:",
            self.grain_field,
            row_height=editor_inline_row_height,
        )
        color_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grain_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        color_grain_row = QHBoxLayout()
        color_grain_row.setSpacing(top_fields_spacing)
        color_grain_row.setContentsMargins(0, 0, 0, 0)
        color_grain_row.addWidget(color_column, 1, Qt.AlignTop)
        color_grain_row.addWidget(grain_column, 1, Qt.AlignTop)
        select_button_label = QLabel("")
        select_button_label.setFixedHeight(editor_label_height)
        select_button_column = QVBoxLayout()
        select_button_column.setSpacing(editor_field_block_spacing)
        select_button_column.setContentsMargins(0, 0, 0, 0)
        select_button_column.addWidget(select_button_label)
        select_button_column.addWidget(select_color_btn, 0, Qt.AlignRight)
        select_button_widget = QWidget()
        select_button_widget.setFixedWidth(editor_inline_button_width)
        select_button_widget.setFixedHeight(editor_inline_row_height)
        select_button_widget.setLayout(select_button_column)
        color_grain_row.addWidget(select_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
        color_grain_widget = QWidget()
        color_grain_widget.setFixedHeight(editor_inline_row_height)
        color_grain_widget.setLayout(color_grain_row)
        top_fields_grid.addWidget(color_grain_widget, 2, 0, 1, 4)

        source_field_widget = build_labeled_field_widget(
            "Programa asociado (opcional):",
            self.source_field,
            row_height=editor_inline_row_height,
        )
        source_field_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        select_source_btn = QPushButton("Seleccionar")
        select_source_btn.setFixedSize(editor_inline_button_width, editor_inline_button_height)
        select_source_btn.clicked.connect(select_source)
        source_row = QHBoxLayout()
        source_row.setSpacing(top_fields_spacing)
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.addWidget(source_field_widget, 1, Qt.AlignTop)
        source_button_label = QLabel("")
        source_button_label.setFixedHeight(editor_label_height)
        source_button_column = QVBoxLayout()
        source_button_column.setSpacing(editor_field_block_spacing)
        source_button_column.setContentsMargins(0, 0, 0, 0)
        source_button_column.addWidget(source_button_label)
        source_button_column.addWidget(select_source_btn, 0, Qt.AlignRight)
        source_button_widget = QWidget()
        source_button_widget.setFixedWidth(editor_inline_button_width)
        source_button_widget.setFixedHeight(editor_inline_row_height)
        source_button_widget.setLayout(source_button_column)
        source_row.addWidget(source_button_widget, 0, Qt.AlignTop | Qt.AlignRight)
        source_widget = QWidget()
        source_widget.setFixedHeight(editor_inline_row_height)
        source_widget.setLayout(source_row)
        top_fields_grid.addWidget(source_widget, 3, 0, 1, 4)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addLayout(top_fields_grid)

        form_panel = QWidget()
        form_panel_horizontal_margin = 4
        form_panel_layout = QVBoxLayout()
        form_panel_layout.setContentsMargins(
            form_panel_horizontal_margin,
            0,
            form_panel_horizontal_margin,
            0,
        )
        form_panel_layout.setSpacing(0)
        form_panel_layout.addLayout(form_layout)
        form_panel.setLayout(form_panel_layout)
        form_panel_width_hint = form_panel.sizeHint().width()
        form_panel.setFixedWidth(form_panel_width_hint)
        form_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, form_panel_horizontal_margin, 0)
        buttons_row.setSpacing(8)
        buttons_row.addStretch(1)
        save_button = QPushButton("Aceptar")
        cancel_button = QPushButton("Cancelar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cancel_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.setDefault(True)
        save_button.setAutoDefault(True)
        cancel_button.setDefault(False)
        cancel_button.setAutoDefault(False)
        select_source_btn.setDefault(False)
        select_source_btn.setAutoDefault(False)
        select_source_btn.setFocusPolicy(Qt.NoFocus)
        save_button.clicked.connect(self.save_template)
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(cancel_button)

        buttons_widget = QWidget()
        buttons_widget.setFixedWidth(form_panel_width_hint)
        buttons_widget.setContentsMargins(0, 0, 0, 0)
        buttons_widget.setLayout(buttons_row)
        buttons_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel("Complete los datos de la plantilla de pieza."))
        layout.addWidget(form_panel, 0, Qt.AlignTop | Qt.AlignLeft)
        layout.addSpacing(_scaled_int(14, max(editor_scale, 0.82), 10))
        layout.addWidget(buttons_widget, 0, Qt.AlignTop | Qt.AlignLeft)
        layout.addStretch(1)
        self.setLayout(layout)
        self.layout().activate()
        compact_dialog_width = self.sizeHint().width()
        compact_dialog_height = self.sizeHint().height()
        available_geometry = _window_available_geometry(self)
        if available_geometry is not None:
            compact_dialog_width = min(
                compact_dialog_width,
                max(420, int(available_geometry.width() * 0.94)),
            )
            compact_dialog_height = min(
                compact_dialog_height,
                max(300, int(available_geometry.height() * 0.90)),
            )
        self.setMinimumSize(compact_dialog_width, compact_dialog_height)
        self.resize(compact_dialog_width, compact_dialog_height)

    def save_template(self):
        template_id = self.id_field.text().strip()
        if not template_id:
            QMessageBox.warning(self, "Piezas", "El campo ID es obligatorio.")
            return

        raw_template = {
            "id": template_id,
            "name": self.name_field.text().strip() or template_id,
            "quantity": self.quantity_field.text().strip() or "1",
            "height": self.height_field.text().strip(),
            "width": self.width_field.text().strip(),
            "thickness": self.thickness_field.text().strip(),
            "color": self.color_field.text().strip(),
            "grain_direction": self.grain_field.currentData(),
            "source": self.source_field.text().strip(),
            "f6_source": self.original_template.get("f6_source"),
            "piece_type": self.original_template.get("piece_type"),
            "saved_at": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
        }
        normalized_template = _normalize_manual_piece_template_entry(raw_template)
        if normalized_template is None:
            QMessageBox.warning(self, "Piezas", "No se pudo guardar la plantilla con los datos ingresados.")
            return

        self.template_data = normalized_template
        self.accept()


class PieceTemplatesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Piezas")
        self.setModal(True)
        self.resize(900, 460)
        self.templates = _normalize_manual_piece_templates(_read_app_settings().get("manual_piece_templates"))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Plantillas de piezas agregadas manualmente."))

        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(6)
        self.templates_table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Cantidad", "Color", "Espesor", "Programa"]
        )
        self.templates_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.templates_table.setSelectionMode(QTableWidget.SingleSelection)
        self.templates_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.templates_table.setAlternatingRowColors(True)
        self.templates_table.verticalHeader().setVisible(False)
        header = self.templates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.templates_table.itemDoubleClicked.connect(lambda _item: self.edit_template())

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(8)
        content_row.addWidget(self.templates_table, 1)

        buttons_column = QVBoxLayout()
        buttons_column.setContentsMargins(0, 0, 0, 0)
        buttons_column.setSpacing(8)
        new_button = QPushButton("Nuevo")
        edit_button = QPushButton("Editar")
        delete_button = QPushButton("Eliminar")
        close_button = QPushButton("Cerrar")
        for button in (new_button, edit_button, delete_button, close_button):
            button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        new_button.clicked.connect(self.add_template)
        edit_button.clicked.connect(self.edit_template)
        delete_button.clicked.connect(self.delete_template)
        close_button.clicked.connect(self.accept)
        buttons_column.addWidget(new_button)
        buttons_column.addWidget(edit_button)
        buttons_column.addWidget(delete_button)
        buttons_column.addStretch(1)
        buttons_column.addWidget(close_button)
        content_row.addLayout(buttons_column)
        layout.addLayout(content_row, 1)

        self.setLayout(layout)
        self.refresh_templates_table()

    def _persist_templates(self):
        self.templates = _persist_manual_piece_templates(self.templates)

    def _selected_template_index(self) -> int:
        return self.templates_table.currentRow()

    def refresh_templates_table(self):
        self.templates = _normalize_manual_piece_templates(self.templates)
        self.templates_table.setRowCount(len(self.templates))
        for row_idx, template_entry in enumerate(self.templates):
            row_values = [
                str(template_entry.get("id") or ""),
                str(template_entry.get("name") or ""),
                str(_parse_piece_quantity_value(template_entry.get("quantity"), default=1)),
                str(template_entry.get("color") or ""),
                "" if template_entry.get("thickness") is None else str(template_entry.get("thickness")),
                Path(str(template_entry.get("source") or "")).name,
            ]
            for column_idx, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if column_idx in {2, 4}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.templates_table.setItem(row_idx, column_idx, item)
        if self.templates:
            self.templates_table.selectRow(0)

    def add_template(self):
        dialog = PieceTemplateEditDialog(parent=self)
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.template_data is None:
            return
        self.templates.append(dialog.template_data)
        self._persist_templates()
        self.refresh_templates_table()
        self.templates_table.selectRow(len(self.templates) - 1)

    def edit_template(self):
        row_idx = self._selected_template_index()
        if row_idx < 0 or row_idx >= len(self.templates):
            QMessageBox.warning(self, "Piezas", "Seleccione una plantilla para editar.")
            return
        dialog = PieceTemplateEditDialog(template_entry=self.templates[row_idx], parent=self)
        if _exec_centered(dialog, self) != QDialog.Accepted or dialog.template_data is None:
            return
        self.templates[row_idx] = dialog.template_data
        self._persist_templates()
        self.refresh_templates_table()
        self.templates_table.selectRow(row_idx)

    def delete_template(self):
        row_idx = self._selected_template_index()
        if row_idx < 0 or row_idx >= len(self.templates):
            QMessageBox.warning(self, "Piezas", "Seleccione una plantilla para eliminar.")
            return
        template_entry = self.templates[row_idx]
        template_label = str(template_entry.get("name") or template_entry.get("id") or "pieza").strip()
        answer = QMessageBox.question(
            self,
            "Piezas",
            f'¿Eliminar la plantilla "{template_label}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        del self.templates[row_idx]
        self._persist_templates()
        self.refresh_templates_table()


class PathsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rutas")
        self.setModal(True)
        self.setMinimumWidth(720)
        self.settings = _read_app_settings()
        self.path_fields: dict[str, QLineEdit] = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Rutas predeterminadas para abrir selectores de carpetas y archivos."))

        paths_grid = QGridLayout()
        paths_grid.setColumnStretch(1, 1)
        default_paths = _normalize_default_paths(self.settings.get("default_paths"))
        for row_index, (path_key, label_text) in enumerate(DEFAULT_PATH_FIELDS):
            label = QLabel(label_text)
            field = QLineEdit(default_paths.get(path_key, ""))
            field.setMinimumWidth(440)
            browse_button = QPushButton("...")
            browse_button.setFixedSize(40, MAIN_ACTION_BUTTON_HEIGHT)
            browse_button.clicked.connect(
                lambda _checked=False, key=path_key: self.select_folder(key)
            )
            self.path_fields[path_key] = field
            paths_grid.addWidget(label, row_index, 0)
            paths_grid.addWidget(field, row_index, 1)
            paths_grid.addWidget(browse_button, row_index, 2)
        layout.addLayout(paths_grid)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_paths)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def _field_label(self, path_key: str) -> str:
        return dict(DEFAULT_PATH_FIELDS).get(path_key, "Ruta")

    def _selector_start_dir(self, path_key: str) -> str:
        raw_path = self.path_fields[path_key].text().strip()
        current_path = Path(raw_path) if raw_path else None
        if current_path is not None and current_path.is_dir():
            return str(current_path)
        return str(Path.home())

    def select_folder(self, path_key: str):
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            f"Seleccionar carpeta - {self._field_label(path_key)}",
            self._selector_start_dir(path_key),
        )
        if selected_folder:
            self.path_fields[path_key].setText(selected_folder)

    def save_paths(self):
        normalized_paths = {}
        for path_key, field in self.path_fields.items():
            path_value = field.text().strip()
            if path_value and not Path(path_value).is_dir():
                QMessageBox.warning(
                    self,
                    "Rutas",
                    f"La ruta de {self._field_label(path_key)} no existe o no es una carpeta.",
                )
                return
            normalized_paths[path_key] = path_value

        current_settings = _read_app_settings()
        current_settings["default_paths"] = normalized_paths
        _write_app_settings(current_settings)
        self.settings = _read_app_settings()
        QMessageBox.information(self, "Rutas", "Rutas guardadas.")


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

        paths_row = QHBoxLayout()
        paths_row.addWidget(QLabel("Rutas predeterminadas"))
        paths_button = QPushButton("Rutas")
        paths_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        paths_button.clicked.connect(self.open_paths_dialog)
        paths_row.addWidget(paths_button)
        layout.addLayout(paths_row)

        cuts_row = QHBoxLayout()
        cuts_row.addWidget(QLabel("Configuración de cortes"))
        cuts_button = QPushButton("Cortes")
        cuts_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        cuts_button.clicked.connect(self.open_cuts_dialog)
        cuts_row.addWidget(cuts_button)
        layout.addLayout(cuts_row)

        boards_row = QHBoxLayout()
        boards_row.addWidget(QLabel("Tableros disponibles"))
        boards_button = QPushButton("Tableros")
        boards_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        boards_button.clicked.connect(self.open_boards_dialog)
        boards_row.addWidget(boards_button)
        layout.addLayout(boards_row)

        tools_row = QHBoxLayout()
        tools_row.addWidget(QLabel("Herramientas de corte"))
        tools_button = QPushButton("Herramientas")
        tools_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        tools_button.clicked.connect(self.open_tools_dialog)
        tools_row.addWidget(tools_button)
        layout.addLayout(tools_row)

        pieces_row = QHBoxLayout()
        pieces_row.addWidget(QLabel("Plantillas de piezas"))
        pieces_button = QPushButton("Piezas")
        pieces_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        pieces_button.clicked.connect(self.open_pieces_dialog)
        pieces_row.addWidget(pieces_button)
        layout.addLayout(pieces_row)

        buttons_row = QHBoxLayout()
        save_button = QPushButton("Guardar")
        close_button = QPushButton("Cerrar")
        save_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        close_button.setFixedSize(MAIN_ACTION_BUTTON_WIDTH, MAIN_ACTION_BUTTON_HEIGHT)
        save_button.clicked.connect(self.save_settings)
        close_button.clicked.connect(self.accept)
        buttons_row.addWidget(save_button)
        buttons_row.addWidget(close_button)
        layout.addLayout(buttons_row)

        self.setLayout(layout)

    def open_boards_dialog(self):
        dialog = BoardsDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def open_paths_dialog(self):
        dialog = PathsDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def open_cuts_dialog(self):
        dialog = CutsDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def open_tools_dialog(self):
        dialog = ToolsDialog(self)
        _exec_centered(dialog, self)

    def open_pieces_dialog(self):
        dialog = PieceTemplatesDialog(self)
        _exec_centered(dialog, self)
        self.settings = _read_app_settings()

    def save_settings(self):
        minimum_dimension_raw = self.minimum_dimension_field.text().strip() or "150"

        try:
            minimum_dimension = int(minimum_dimension_raw)
        except ValueError:
            QMessageBox.warning(self, "Opciones", "La mínima dimensión mecanizable debe ser un número entero.")
            return

        if minimum_dimension <= 0:
            QMessageBox.warning(self, "Opciones", "La mínima dimensión mecanizable debe ser mayor que cero.")
            return

        current_settings = _read_app_settings()
        current_settings["minimum_machinable_dimension"] = minimum_dimension
        _write_app_settings(current_settings)
        self.settings = current_settings
        QMessageBox.information(self, "Opciones", "Configuración guardada.")


def run_app():
    app = QApplication([])
    window = MainWindow()
    _show_centered(window)
    app.exec()
