"""Persistencia del registro de proyectos."""

import json

from app.runtime import PROJECT_REGISTRY

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
