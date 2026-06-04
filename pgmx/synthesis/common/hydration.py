"""Template loading helpers for PGMX synthesis hydration."""

from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "PgmxTemplateDocument",
    "load_pgmx_template_document",
    "_load_exploded_pgmx_container",
    "_load_pgmx_container",
    "_resolve_exploded_pgmx_xml_path",
]


@dataclass(frozen=True)
class PgmxTemplateDocument:
    """Loaded Maestro template document used as hydration source."""

    root: ET.Element
    archive_entries: dict[str, bytes]
    xml_entry_name: str
    source_path: Path

    def as_container_tuple(self) -> tuple[ET.Element, dict[str, bytes], str]:
        return self.root, self.archive_entries, self.xml_entry_name


def _resolve_exploded_pgmx_xml_path(source_path: Path) -> Path:
    """Resuelve el XML base cuando el baseline esta desempaquetado en disco."""

    if source_path.is_file() and source_path.suffix.lower() == ".xml":
        return source_path
    if not source_path.is_dir():
        raise ValueError(
            "El baseline Maestro desempaquetado debe pasarse como carpeta o como archivo `.xml`."
        )

    xml_candidates = sorted(
        (
            child
            for child in source_path.iterdir()
            if child.is_file() and child.suffix.lower() == ".xml"
        ),
        key=lambda path: (path.name.lower() != "pieza.xml", path.name.lower()),
    )
    if not xml_candidates:
        raise ValueError(f"La carpeta '{source_path}' no contiene ningun archivo `.xml`.")
    return xml_candidates[0]


def _load_exploded_pgmx_container(source_path: Path) -> tuple[ET.Element, dict[str, bytes], str]:
    """Carga un baseline Maestro desempaquetado (`Pieza.xml` + extras asociados)."""

    xml_path = _resolve_exploded_pgmx_xml_path(source_path)
    container_dir = xml_path.parent
    archive_entries: dict[str, bytes] = {xml_path.name: xml_path.read_bytes()}
    for child in sorted(container_dir.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_file() or child == xml_path:
            continue
        if child.suffix.lower() not in {".epl", ".tlgx"}:
            continue
        archive_entries[child.name] = child.read_bytes()

    xml_root = ET.fromstring(archive_entries[xml_path.name].decode("utf-8", errors="ignore"))
    return xml_root, archive_entries, xml_path.name


def load_pgmx_template_document(source_path: Path) -> PgmxTemplateDocument:
    """Carga un PGMX fuente desde `.pgmx`, `Pieza.xml` o carpeta contenedora."""

    if not source_path.exists():
        raise FileNotFoundError(f"No existe el baseline Maestro '{source_path}'.")
    if source_path.is_file() and source_path.suffix.lower() == ".pgmx":
        with zipfile.ZipFile(source_path) as zip_file:
            archive_entries = {name: zip_file.read(name) for name in zip_file.namelist()}
        xml_entry_name = next((name for name in archive_entries if name.lower().endswith(".xml")), "")
        if not xml_entry_name:
            raise ValueError(f"El archivo '{source_path}' no contiene una entrada XML.")
        xml_root = ET.fromstring(archive_entries[xml_entry_name].decode("utf-8", errors="ignore"))
        return PgmxTemplateDocument(
            root=xml_root,
            archive_entries=archive_entries,
            xml_entry_name=xml_entry_name,
            source_path=source_path,
        )
    if source_path.is_dir() or (source_path.is_file() and source_path.suffix.lower() == ".xml"):
        xml_root, archive_entries, xml_entry_name = _load_exploded_pgmx_container(source_path)
        return PgmxTemplateDocument(
            root=xml_root,
            archive_entries=archive_entries,
            xml_entry_name=xml_entry_name,
            source_path=source_path,
        )
    raise ValueError(
        f"El baseline Maestro '{source_path}' debe ser un `.pgmx`, un `.xml` o una carpeta."
    )


def _load_pgmx_container(source_path: Path) -> tuple[ET.Element, dict[str, bytes], str]:
    """Carga un baseline Maestro desde `.pgmx`, `Pieza.xml` o carpeta contenedora."""

    return load_pgmx_template_document(source_path).as_container_tuple()
