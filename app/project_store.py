"""Carga y persistencia de proyectos ProdAction."""

import json
from pathlib import Path

from app.project_registry import _find_registry_entry, _read_registry, _write_registry
from app.settings import _parse_piece_quantity_value
from core.model import (
    LocaleData,
    ModuleData,
    Piece,
    Project,
    normalize_piece_grain_direction,
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
