"""Scan PGMX files for Aparcamiento executables and dump all their XML children."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Iterable, Optional
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from . import ANALYSIS_ROOT, EXTERNAL_ROOT


@dataclass
class AparcamientoRow:
    path: Path
    current_workplan_index: str
    workplan_count: int
    workplan_index: int
    workplan_id: str
    workplan_name: str
    setup_x: str
    setup_y: str
    setup_z: str
    step_index: int
    runtime_type: str
    discovered_fields: dict = field(default_factory=dict)


_CONTEXT_FIELDS = [f.name for f in fields(AparcamientoRow) if f.name != "discovered_fields"]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(node: Optional[ET.Element], local_name: str) -> Optional[ET.Element]:
    if node is None:
        return None
    for child in list(node):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _text(node: Optional[ET.Element], local_name: str, default: str = "") -> str:
    child = _child(node, local_name)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _key_id(node: Optional[ET.Element]) -> str:
    return _text(_child(node, "Key"), "ID")


def _xsi_type(node: ET.Element) -> str:
    for key, value in node.attrib.items():
        if key.endswith("}type") or key == "type":
            return value.split(":")[-1]
    return ""


def _nil_attr(node: Optional[ET.Element]) -> str:
    if node is None:
        return ""
    for key, value in node.attrib.items():
        if key.endswith("}nil"):
            return value
    return ""


def _xml_root(path: Path) -> ET.Element:
    if path.suffix.lower() == ".pgmx":
        with ZipFile(path) as archive:
            xml_name = next(name for name in archive.namelist() if name.lower().endswith(".xml"))
            return ET.fromstring(archive.read(xml_name))
    return ET.parse(path).getroot()


def _setup_origin(workplan: ET.Element) -> tuple[str, str, str]:
    setup = _child(workplan, "Setup")
    placement = None
    if setup is not None:
        for node in setup.iter():
            if _local_name(node.tag) == "Placement":
                placement = node
                break
    return (
        _text(placement, "_xP"),
        _text(placement, "_yP"),
        _text(placement, "_zP"),
    )


def _discover_fields(executable: ET.Element) -> dict[str, str]:
    """Dump every direct child of the executable as child_<tag> and child_<tag>_nil."""
    result: dict[str, str] = {}
    for child in executable:
        tag = _local_name(child.tag)
        key = f"child_{tag}"
        result[key] = (child.text or "").strip()
        nil = _nil_attr(child)
        if nil:
            result[f"{key}_nil"] = nil
    return result


def scan_pgmx(path: Path) -> tuple[AparcamientoRow, ...]:
    root = _xml_root(path)
    rows: list[AparcamientoRow] = []
    current_workplan_index = _text(root, "CurrentWorkplanIndex")
    workplans = list(root.findall("./{*}Workplans/{*}MainWorkplan"))
    workplan_count = len(workplans)

    for workplan_index, workplan in enumerate(workplans, start=1):
        setup_x, setup_y, setup_z = _setup_origin(workplan)
        elements = _child(workplan, "Elements")
        executables = list(elements) if elements is not None else []

        for step_index, executable in enumerate(executables, start=1):
            runtime_type = _xsi_type(executable)
            rows.append(
                AparcamientoRow(
                    path=path,
                    current_workplan_index=current_workplan_index,
                    workplan_count=workplan_count,
                    workplan_index=workplan_index,
                    workplan_id=_key_id(workplan),
                    workplan_name=_text(workplan, "Name"),
                    setup_x=setup_x,
                    setup_y=setup_y,
                    setup_z=setup_z,
                    step_index=step_index,
                    runtime_type=runtime_type,
                    discovered_fields=_discover_fields(executable),
                )
            )

    return tuple(rows)


def iter_pgmx_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*.pgmx")):
        yield path


def write_rows(rows: Iterable[AparcamientoRow], output_path: Path) -> Path:
    all_rows = list(rows)
    discovered_keys: list[str] = []
    seen: set[str] = set()
    for row in all_rows:
        for key in row.discovered_fields:
            if key not in seen:
                discovered_keys.append(key)
                seen.add(key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _CONTEXT_FIELDS + discovered_keys
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            data: dict = {f: getattr(row, f) for f in _CONTEXT_FIELDS}
            data["path"] = str(row.path)
            data.update(row.discovered_fields)
            writer.writerow(data)
    return output_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=EXTERNAL_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ANALYSIS_ROOT / "aparcamiento_fields.csv",
    )
    args = parser.parse_args(argv)

    all_rows: list[AparcamientoRow] = []
    for path in iter_pgmx_files(args.root):
        all_rows.extend(scan_pgmx(path))

    if not all_rows:
        print(f"No se encontraron archivos .pgmx en {args.root}")
        return 0

    park_rows = [r for r in all_rows if r.runtime_type == "Park"]
    write_rows(park_rows, args.output)
    print(
        f"Escaneados {len(all_rows)} executable steps "
        f"({len(park_rows)} Park) en {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
