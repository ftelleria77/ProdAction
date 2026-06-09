"""Scan PGMX program-flow samples for workplans and machine operations."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Iterable, Optional
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from . import ANALYSIS_ROOT, EXTERNAL_ROOT


@dataclass(frozen=True)
class ProgramFlowRow:
    path: Path
    current_workplan_index: str
    workplan_count: int
    workplan_index: int
    workplan_id: str
    workplan_name: str
    setup_id: str
    setup_x: str
    setup_y: str
    setup_z: str
    step_index: int
    runtime_type: str
    name: str
    geometry_id: str
    geometry_object_type: str
    workpiece_id: str
    workpiece_object_type: str
    feature_id: str
    operation_id: str
    reference: str
    speed: str
    spindle_enable: str
    x: str
    y: str
    y_nil: str
    tool_id: str
    tool_object_type: str
    tool_name: str
    stop: str
    text: str
    input_enabled: str
    variable_id: str
    variable_object_type: str
    variable_name: str


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


def _id_ref(node: Optional[ET.Element], local_name: str) -> str:
    ref = _child(node, local_name)
    return _text(ref, "ID")


def _object_type_ref(node: Optional[ET.Element], local_name: str) -> str:
    ref = _child(node, local_name)
    return _text(ref, "ObjectType")


def _name_ref(node: Optional[ET.Element], local_name: str) -> str:
    ref = _child(node, local_name)
    return _text(ref, "Name")


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


def scan_pgmx(path: Path) -> tuple[ProgramFlowRow, ...]:
    root = _xml_root(path)
    rows: list[ProgramFlowRow] = []
    current_workplan_index = _text(root, "CurrentWorkplanIndex")
    workplans = [
        node
        for node in root.findall("./{*}Workplans/{*}MainWorkplan")
    ]
    workplan_count = len(workplans)
    for workplan_index, workplan in enumerate(workplans, start=1):
        setup = _child(workplan, "Setup")
        setup_x, setup_y, setup_z = _setup_origin(workplan)
        elements = _child(workplan, "Elements")
        executables = list(elements) if elements is not None else []
        if not executables:
            rows.append(
                ProgramFlowRow(
                    path=path,
                    current_workplan_index=current_workplan_index,
                    workplan_count=workplan_count,
                    workplan_index=workplan_index,
                    workplan_id=_key_id(workplan),
                    workplan_name=_text(workplan, "Name"),
                    setup_id=_key_id(setup),
                    setup_x=setup_x,
                    setup_y=setup_y,
                    setup_z=setup_z,
                    step_index=0,
                    runtime_type="",
                    name="",
                    geometry_id="",
                    geometry_object_type="",
                    workpiece_id="",
                    workpiece_object_type="",
                    feature_id="",
                    operation_id="",
                    reference="",
                    speed="",
                    spindle_enable="",
                    x="",
                    y="",
                    y_nil="",
                    tool_id="",
                    tool_object_type="",
                    tool_name="",
                    stop="",
                    text="",
                    input_enabled="",
                    variable_id="",
                    variable_object_type="",
                    variable_name="",
                )
            )
            continue
        for step_index, executable in enumerate(executables, start=1):
            y_node = _child(executable, "Y")
            rows.append(
                ProgramFlowRow(
                    path=path,
                    current_workplan_index=current_workplan_index,
                    workplan_count=workplan_count,
                    workplan_index=workplan_index,
                    workplan_id=_key_id(workplan),
                    workplan_name=_text(workplan, "Name"),
                    setup_id=_key_id(setup),
                    setup_x=setup_x,
                    setup_y=setup_y,
                    setup_z=setup_z,
                    step_index=step_index,
                    runtime_type=_xsi_type(executable),
                    name=_text(executable, "Name"),
                    geometry_id=_id_ref(executable, "GeometryID"),
                    geometry_object_type=_object_type_ref(executable, "GeometryID"),
                    workpiece_id=_id_ref(executable, "WorkpieceID"),
                    workpiece_object_type=_object_type_ref(executable, "WorkpieceID"),
                    feature_id=_id_ref(executable, "ManufacturingFeatureID"),
                    operation_id=_id_ref(executable, "OperationID"),
                    reference=_text(executable, "Reference"),
                    speed=_text(executable, "Speed"),
                    spindle_enable=_text(executable, "SpindleEnable"),
                    x=_text(executable, "X"),
                    y=_text(executable, "Y"),
                    y_nil=_nil_attr(y_node),
                    tool_id=_id_ref(executable, "Tool"),
                    tool_object_type=_object_type_ref(executable, "Tool"),
                    tool_name=_name_ref(executable, "Tool"),
                    stop=_text(executable, "Stop"),
                    text=_text(executable, "Text"),
                    input_enabled=_text(executable, "IsInputEnable"),
                    variable_id=_id_ref(executable, "Variable"),
                    variable_object_type=_object_type_ref(executable, "Variable"),
                    variable_name=_name_ref(executable, "Variable"),
                )
            )
    return tuple(rows)


def iter_pgmx_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*.pgmx")):
        yield path


def write_rows(rows: Iterable[ProgramFlowRow], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [field.name for field in fields(ProgramFlowRow)]
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = row.__dict__.copy()
            data["path"] = str(row.path)
            writer.writerow(data)
    return output_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=EXTERNAL_ROOT)
    parser.add_argument("--output", type=Path, default=ANALYSIS_ROOT / "program_flow.csv")
    args = parser.parse_args(argv)

    rows: list[ProgramFlowRow] = []
    for path in iter_pgmx_files(args.root):
        rows.extend(scan_pgmx(path))
    write_rows(rows, args.output)
    print(f"Scanned {len(rows)} executable steps into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
