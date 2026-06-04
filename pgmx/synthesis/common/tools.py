"""Tool catalog helpers for PGMX synthesis."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Optional, Protocol

from .xml import _compact_number

__all__ = [
    "TOOL_CATALOG_PATH",
    "_diameter_key",
    "_is_vertical_x_saw",
    "_load_tool_catalog",
    "_lookup_tool_catalog_entry",
    "_normalize_tool_resolution",
    "_normalize_tool_usage_group",
    "_resolve_drilling_tool",
    "_tool_catalog_label",
    "_validate_tool_sinking_length_for_total_depth",
    "_validate_tool_type_for_drilling_spec",
]


class _ToolSpec(Protocol):
    tool_id: str
    tool_name: str


class _DrillingToolRequest(_ToolSpec, Protocol):
    diameter: float
    drill_family: str
    plane_name: str
    tool_resolution: str


class _ResolvedToolSpec(_ToolSpec, Protocol):
    tool_object_type: str


def _module_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        for bundled_data_dir in (
            executable_dir / "pgmx" / "data",
            executable_dir / "_internal" / "pgmx" / "data",
            executable_dir / "tools",
            executable_dir / "_internal" / "tools",
        ):
            if bundled_data_dir.exists():
                return bundled_data_dir
    return Path(__file__).resolve().parents[2] / "data"


TOOL_CATALOG_PATH = _module_data_dir() / "tool_catalog.csv"


def _normalize_tool_resolution(value: Optional[str]) -> str:
    raw = (value or "Auto").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "auto": "Auto",
        "automatic": "Auto",
        "automatico": "Auto",
        "none": "None",
        "sin": "None",
        "ninguna": "None",
        "empty": "None",
        "explicit": "Explicit",
        "explicita": "Explicit",
        "manual": "Explicit",
    }
    if raw not in mapping:
        raise ValueError("ToolResolution invalido. Valores admitidos: Auto, None o Explicit.")
    return mapping[raw]


def _load_tool_catalog() -> dict[str, dict[str, str]]:
    """Carga el catalogo plano de herramientas indexado por `tool_id`."""

    if not TOOL_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"No existe el catalogo de herramientas '{TOOL_CATALOG_PATH}'."
        )
    with TOOL_CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    return {
        str((row.get("tool_id") or "").strip()): row
        for row in rows
        if (row.get("tool_id") or "").strip()
    }


_AUTO_VERTICAL_DRILL_TOOLS: dict[tuple[str, str], tuple[str, str]] = {
    ("Flat", "8"): ("1888", "001"),
    ("Flat", "15"): ("1889", "002"),
    ("Flat", "20"): ("1890", "003"),
    ("Flat", "35"): ("1891", "004"),
    ("Flat", "5"): ("1892", "005"),
    ("Flat", "4"): ("1893", "006"),
    ("Conical", "5"): ("1894", "007"),
}


def _lookup_tool_catalog_entry(
    tool_catalog: dict[str, dict[str, str]],
    *,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> dict[str, str]:
    normalized_tool_id = (tool_id or "").strip()
    normalized_tool_name = (tool_name or "").strip()
    if normalized_tool_id == "0" and normalized_tool_name:
        normalized_tool_id = ""

    if normalized_tool_id:
        row = tool_catalog.get(normalized_tool_id)
        if row is None:
            raise ValueError(
                f"No existe la herramienta '{normalized_tool_id}' en '{TOOL_CATALOG_PATH.name}'."
            )
        if normalized_tool_name and (row.get("name") or "").strip() != normalized_tool_name:
            raise ValueError(
                "La herramienta explicita no coincide con el catalogo: "
                f"id={normalized_tool_id} corresponde a '{(row.get('name') or '').strip()}'."
            )
        return row

    if normalized_tool_name:
        for row in tool_catalog.values():
            if (row.get("name") or "").strip() == normalized_tool_name:
                return row
        raise ValueError(
            f"No existe la herramienta '{normalized_tool_name}' en '{TOOL_CATALOG_PATH.name}'."
        )

    raise ValueError("La resolucion explicita de herramienta requiere tool_id, tool_name o ambos.")


def _tool_catalog_label(spec: _ToolSpec) -> str:
    return f"{spec.tool_name} ({spec.tool_id})"


def _diameter_key(value: float) -> str:
    return _compact_number(float(value))


def _resolve_drilling_tool(
    drilling: _DrillingToolRequest,
    tool_catalog: dict[str, dict[str, str]],
) -> tuple[str, str, str]:
    if drilling.tool_resolution == "None":
        return "0", "", "System.Object"

    if drilling.tool_resolution == "Explicit":
        row = _lookup_tool_catalog_entry(
            tool_catalog,
            tool_id=drilling.tool_id,
            tool_name=drilling.tool_name,
        )
        return (
            str((row.get("tool_id") or "").strip()),
            str((row.get("name") or "").strip()),
            "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
        )

    if drilling.plane_name in {"Front", "Back", "Right", "Left"}:
        # En los taladros laterales Maestro deja la operacion sin ToolKey hasta
        # el postprocesado. Forzar 058/059/060/061 desde el PGMX puede asignar
        # una broca incorrecta segun el sentido real de la cara.
        return "0", "", "System.Object"

    diameter_key = _diameter_key(drilling.diameter)
    tool_key = _AUTO_VERTICAL_DRILL_TOOLS.get((drilling.drill_family, diameter_key))
    if tool_key is None:
        raise ValueError(
            "No hay una herramienta vertical auto-resoluble para ese diametro/familia en el toolset relevado."
        )

    row = _lookup_tool_catalog_entry(
        tool_catalog,
        tool_id=tool_key[0],
        tool_name=tool_key[1],
    )
    return (
        str((row.get("tool_id") or "").strip()),
        str((row.get("name") or "").strip()),
        "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
    )


def _normalize_tool_usage_group(tool_type: str) -> str:
    normalized = (tool_type or "").strip().lower()
    if normalized.startswith("broca"):
        return "drilling"
    if normalized.startswith("fresa") or normalized.startswith("freza"):
        return "milling"
    if normalized.startswith("sierra"):
        return "saw"
    return "other"


def _is_vertical_x_saw(tool_type: str) -> bool:
    return (tool_type or "").strip().lower() == "sierra vertical x"


def _validate_tool_type_for_drilling_spec(
    spec: _ResolvedToolSpec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    if spec.tool_object_type == "System.Object":
        return

    catalog_entry = tool_catalog.get(spec.tool_id)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar el tipo de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    tool_type = (catalog_entry.get("type") or "").strip()
    if _normalize_tool_usage_group(tool_type) != "drilling":
        raise ValueError(
            "El taladrado requiere una herramienta de tipo Broca: "
            f"{_tool_catalog_label(spec)} figura como '{tool_type or 'sin tipo'}'."
        )


def _validate_tool_sinking_length_for_total_depth(
    spec: _ToolSpec,
    catalog_entry: Optional[dict[str, str]],
    *,
    total_depth: float,
    operation_name: str,
) -> None:
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar la seguridad de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    sinking_length_text = (catalog_entry.get("sinking_length") or "").strip()
    sinking_length = float(sinking_length_text or "0")
    if sinking_length <= 0.0:
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} no tiene un `sinking_length` valido en '{TOOL_CATALOG_PATH.name}'."
        )

    if total_depth > sinking_length + 1e-9:
        raise ValueError(
            f"La profundidad total del {operation_name} excede el `sinking_length` de la herramienta: "
            f"{_tool_catalog_label(spec)} permite { _compact_number(sinking_length) } mm, "
            f"pero la solicitud requiere { _compact_number(total_depth) } mm."
        )
