"""Catalog PGMX samples for the Vaciado investigation.

The scanner is intentionally descriptive.  It does not classify a final
``Vaciado`` model; it records the XML-level evidence needed to decide one.
"""

from __future__ import annotations

import argparse
import csv
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from tools.pgmx_snapshot import (
    PgmxOperationSnapshot,
    PgmxResolvedWorkingStepSnapshot,
    read_pgmx_snapshot,
)

from . import EXTERNAL_ROOT

DEFAULT_OUTPUT_DIR = EXTERNAL_ROOT / "_analysis"


@dataclass(frozen=True)
class VaciadoSampleRow:
    relative_path: str
    status: str
    step_index: str = ""
    step_enabled: str = ""
    step_name: str = ""
    feature_name: str = ""
    feature_type: str = ""
    operation_name: str = ""
    operation_type: str = ""
    geometry_name: str = ""
    geometry_type: str = ""
    plane_name: str = ""
    tool_key: str = ""
    tool_diameter: str = ""
    tool_radius: str = ""
    cutting_depth: str = ""
    allowance_bottom: str = ""
    allowance_side: str = ""
    feature_depth_start: str = ""
    feature_depth_end: str = ""
    side_of_feature: str = ""
    material_position: str = ""
    strategy: str = ""
    strategy_overlap_percent: str = ""
    toolpaths: str = ""
    trajectory_points: str = ""
    trajectory_x_range: str = ""
    trajectory_y_range: str = ""
    trajectory_z_values: str = ""
    candidate_kind: str = ""
    notes: str = ""


FIELDNAMES = tuple(VaciadoSampleRow.__dataclass_fields__)


def scan_samples(root: Path, output_dir: Path) -> tuple[list[VaciadoSampleRow], Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[VaciadoSampleRow] = []
    for pgmx_path in sorted(root.rglob("*.pgmx"), key=lambda path: str(path).lower()):
        if "_analysis" in pgmx_path.parts:
            continue
        rows.extend(_scan_pgmx(pgmx_path, root))

    csv_path = output_dir / "vaciado_pgmx_catalog.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    summary_path = output_dir / "vaciado_pgmx_catalog_summary.md"
    summary_path.write_text(_build_summary(rows, root, csv_path), encoding="utf-8")
    return rows, csv_path, summary_path


def _scan_pgmx(pgmx_path: Path, root: Path) -> list[VaciadoSampleRow]:
    relative_path = _relative_path(pgmx_path, root)
    try:
        snapshot = read_pgmx_snapshot(pgmx_path)
    except Exception as exc:  # pragma: no cover - evidence script
        return [
            VaciadoSampleRow(
                relative_path=relative_path,
                status="pgmx_error",
                notes=str(exc),
            )
        ]

    raw_strategies = _raw_strategy_by_operation_id(pgmx_path)
    tools_by_id = {tool.id: tool for tool in snapshot.embedded_tools}
    rows = [
        _row_from_step(relative_path, resolved, raw_strategies, tools_by_id)
        for resolved in snapshot.resolved_working_steps
    ]
    if rows:
        return rows
    return [
        VaciadoSampleRow(
            relative_path=relative_path,
            status="empty_workplan",
            notes="PGMX has no resolved working steps.",
        )
    ]


def _row_from_step(
    relative_path: str,
    resolved: PgmxResolvedWorkingStepSnapshot,
    raw_strategies: dict[str, str],
    tools_by_id: dict[str, object],
) -> VaciadoSampleRow:
    feature = resolved.feature
    operation = resolved.operation
    geometry = resolved.geometry
    plane = resolved.plane
    tool_key = operation.tool_key.name if operation and operation.tool_key else ""
    tool = tools_by_id.get(operation.tool_key.id) if operation and operation.tool_key else None
    tool_diameter = getattr(tool, "diameter", None)
    tool_radius = tool_diameter / 2 if tool_diameter is not None else None
    strategy = _strategy_summary(operation, raw_strategies) if operation else ""
    toolpaths = _toolpath_summary(operation) if operation else ""
    trajectory = _trajectory_summary(operation) if operation else {}
    feature_name = feature.name if feature else ""
    feature_type = feature.feature_type if feature else ""
    operation_name = operation.name if operation else ""
    operation_type = operation.operation_type if operation else ""
    geometry_name = geometry.name if geometry else ""
    geometry_type = geometry.geometry_type if geometry else ""
    candidate_kind = _candidate_kind(
        feature_name=feature_name,
        feature_type=feature_type,
        operation_name=operation_name,
        operation_type=operation_type,
        geometry_name=geometry_name,
        geometry_type=geometry_type,
        strategy=strategy,
        toolpaths=toolpaths,
    )
    return VaciadoSampleRow(
        relative_path=relative_path,
        status="ok",
        step_index=str(resolved.index),
        step_enabled=str(resolved.step.is_enabled).lower(),
        step_name=resolved.step.name,
        feature_name=feature_name,
        feature_type=feature_type,
        operation_name=operation_name,
        operation_type=operation_type,
        geometry_name=geometry_name,
        geometry_type=geometry_type,
        plane_name=plane.name if plane else "",
        tool_key=tool_key,
        tool_diameter=_format_optional(tool_diameter),
        tool_radius=_format_optional(tool_radius),
        cutting_depth=_format_optional(operation.cutting_depth if operation else None),
        allowance_bottom=_format_optional(operation.allowance_bottom if operation else None),
        allowance_side=_format_optional(operation.allowance_side if operation else None),
        feature_depth_start=_format_optional(feature.depth_start if feature else None),
        feature_depth_end=_format_optional(feature.depth_end if feature else None),
        side_of_feature=feature.side_of_feature if feature else "",
        material_position=feature.material_position if feature else "",
        strategy=strategy,
        strategy_overlap_percent=_strategy_overlap_percent(operation) if operation else "",
        toolpaths=toolpaths,
        trajectory_points=trajectory.get("points", ""),
        trajectory_x_range=trajectory.get("x_range", ""),
        trajectory_y_range=trajectory.get("y_range", ""),
        trajectory_z_values=trajectory.get("z_values", ""),
        candidate_kind=candidate_kind,
        notes="",
    )


def _strategy_summary(operation: PgmxOperationSnapshot, raw_strategies: dict[str, str]) -> str:
    strategy = operation.milling_strategy
    if strategy is None:
        return raw_strategies.get(operation.id, "")
    name = type(strategy).__name__.replace("MillingStrategySpec", "")
    if not is_dataclass(strategy):
        return name
    values = [
        f"{key}={_format_value(value)}"
        for key, value in asdict(strategy).items()
    ]
    return f"{name}({', '.join(values)})"


def _strategy_overlap_percent(operation: PgmxOperationSnapshot) -> str:
    strategy = operation.milling_strategy
    overlap = getattr(strategy, "overlap", None)
    if overlap is None:
        return ""
    return f"{float(overlap) * 100:.6g}%"


def _raw_strategy_by_operation_id(pgmx_path: Path) -> dict[str, str]:
    try:
        with zipfile.ZipFile(pgmx_path) as pgmx_zip:
            xml_name = next(name for name in pgmx_zip.namelist() if name.lower().endswith(".xml"))
            root = ET.fromstring(pgmx_zip.read(xml_name))
    except Exception:
        return {}

    result: dict[str, str] = {}
    for operation in root.findall("./{*}Operations/{*}Operation"):
        operation_id = _child_text(_first_child(operation, "Key"), "ID")
        strategy = _first_child(operation, "MachiningStrategy")
        if not operation_id or strategy is None:
            continue
        strategy_type = _xsi_type(strategy).removeprefix("b:")
        values = [
            f"{_local_name(child.tag)}={_format_value((child.text or '').strip())}"
            for child in list(strategy)
        ]
        result[operation_id] = f"{strategy_type}({', '.join(values)})"
    return result


def _toolpath_summary(operation: PgmxOperationSnapshot) -> str:
    parts: list[str] = []
    for toolpath in operation.toolpaths:
        curve = toolpath.curve
        curve_type = curve.geometry_type if curve else ""
        point_count = len(curve.sampled_points) if curve else 0
        parts.append(f"{toolpath.path_type}:{curve_type}:points={point_count}")
    return " | ".join(parts)


def _trajectory_summary(operation: PgmxOperationSnapshot) -> dict[str, str]:
    for toolpath in operation.toolpaths:
        if toolpath.path_type != "TrajectoryPath" or toolpath.curve is None:
            continue
        points = toolpath.curve.sampled_points
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        zs = sorted({round(point[2], 6) for point in points})
        return {
            "points": str(len(points)),
            "x_range": f"{_format_value(min(xs))}..{_format_value(max(xs))}",
            "y_range": f"{_format_value(min(ys))}..{_format_value(max(ys))}",
            "z_values": ",".join(_format_value(value) for value in zs),
        }
    return {}


def _candidate_kind(**values: str) -> str:
    text = " ".join(values.values()).lower()
    if "vaciado" in text:
        return "named_vaciado"
    if "pocket" in text:
        return "pocket_named"
    if "milling" in values["operation_type"].lower() and _looks_like_closed_area(values["geometry_type"]):
        return "closed_area_milling_review"
    if "fresado" in text or "milling" in text:
        return "milling_review"
    return "non_milling"


def _looks_like_closed_area(geometry_type: str) -> bool:
    lowered = geometry_type.lower()
    return any(token in lowered for token in ("closed", "circle", "rectangle", "polygon"))


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _format_optional(value: object | None) -> str:
    if value is None:
        return ""
    return _format_value(value)


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _first_child(parent: ET.Element | None, local_name: str) -> ET.Element | None:
    if parent is None:
        return None
    for child in list(parent):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _child_text(parent: ET.Element | None, local_name: str) -> str:
    child = _first_child(parent, local_name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xsi_type(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return node.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")


def _build_summary(rows: Iterable[VaciadoSampleRow], root: Path, csv_path: Path) -> str:
    rows = list(rows)
    status_counts = Counter(row.status for row in rows)
    candidate_counts = Counter(row.candidate_kind for row in rows)
    operation_counts = Counter(row.operation_type for row in rows if row.operation_type)
    feature_counts = Counter(row.feature_type for row in rows if row.feature_type)
    allowance_side_counts = Counter(row.allowance_side for row in rows if row.allowance_side)
    overlap_counts = Counter(row.strategy_overlap_percent for row in rows if row.strategy_overlap_percent)
    lines = [
        "# Vaciado PGMX Catalog",
        "",
        f"- Root: `{root}`",
        f"- CSV: `{csv_path}`",
        f"- Rows: `{len(rows)}`",
        "",
        "## Status",
        "",
        *_counter_lines(status_counts),
        "",
        "## Candidate Kinds",
        "",
        *_counter_lines(candidate_counts),
        "",
        "## Operation Types",
        "",
        *_counter_lines(operation_counts),
        "",
        "## Feature Types",
        "",
        *_counter_lines(feature_counts),
        "",
        "## AllowanceSide Values",
        "",
        *_counter_lines(allowance_side_counts),
        "",
        "## Overlap Values",
        "",
        *_counter_lines(overlap_counts),
        "",
    ]
    return "\n".join(lines)


def _counter_lines(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- none"]
    return [f"- `{key}`: `{value}`" for key, value in counter.most_common()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Catalog PGMX samples for the Vaciado investigation.")
    parser.add_argument("--root", type=Path, default=EXTERNAL_ROOT, help="Root folder with manual/generated PGMX samples.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder for CSV and Markdown reports.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, csv_path, summary_path = scan_samples(args.root, args.output_dir)
    print(f"Scanned {len(rows)} rows.")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
