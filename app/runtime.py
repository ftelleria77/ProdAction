"""Rutas runtime para la app desktop de ProdAction."""

import sys
from pathlib import Path

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
