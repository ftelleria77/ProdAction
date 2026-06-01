"""Configuracion de la app, catalogo de herramientas y defaults de En-Juego."""

import csv
import datetime
import json

from app.runtime import APP_SETTINGS_FILE, BASE_DIR
from core.model import normalize_piece_grain_direction

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
