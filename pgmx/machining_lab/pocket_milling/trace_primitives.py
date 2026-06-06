"""Analyze Maestro pocket milling trajectory primitives.

This is a lab-only evidence tool. It does not synthesize PGMX files; it
decomposes Maestro `TrajectoryPath` curves into lines/arcs and relates them to
the pocket contour, physical islands, and route seeds.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from pgmx import synthesis as sp
from pgmx.adapters import adapt_pgmx_path

from . import EXTERNAL_ROOT


DEFAULT_OUTPUT_DIR = EXTERNAL_ROOT / "_analysis" / "vaciado_trace_primitives"


@dataclass(frozen=True)
class TracePrimitiveRow:
    sample: str
    sequence_index: int
    primitive_index: int
    primitive_type: str
    relation: str
    start: str
    end: str
    center: str = ""
    radius: str = ""
    sweep: str = ""
    length: str = ""


@dataclass(frozen=True)
class TraceCaseRow:
    sample: str
    status: str
    geometry_type: str = ""
    contour: str = ""
    contour_start: str = ""
    boss_bboxes: str = ""
    route_seed_bboxes: str = ""
    tool: str = ""
    tool_width: str = ""
    target_depth: str = ""
    allowance_side: str = ""
    overlap: str = ""
    radial_step: str = ""
    rotation: str = ""
    stroke_connection: str = ""
    inside_to_outside: str = ""
    helic: str = ""
    multipass: str = ""
    axial_cutting_depth: str = ""
    axial_finish_cutting_depth: str = ""
    trajectory_counts: str = ""
    primitive_counts: str = ""
    arc_families: str = ""
    line_families: str = ""
    notes: str = ""


PRIMITIVE_FIELDNAMES = tuple(TracePrimitiveRow.__dataclass_fields__)
CASE_FIELDNAMES = tuple(TraceCaseRow.__dataclass_fields__)


def analyze_trace_primitives(
    root: Path,
    output_dir: Path,
    *,
    include_variants: bool = True,
) -> tuple[list[TraceCaseRow], list[TracePrimitiveRow], Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted((root / "manual").glob("Vaciado_*.pgmx"), key=lambda path: path.name)
    if not include_variants:
        paths = [path for path in paths if "_E" not in path.stem]

    case_rows: list[TraceCaseRow] = []
    primitive_rows: list[TracePrimitiveRow] = []
    for path in paths:
        case_row, rows = _analyze_one(path, root)
        case_rows.append(case_row)
        primitive_rows.extend(rows)

    case_csv_path = output_dir / "vaciado_trace_case_summary.csv"
    with case_csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CASE_FIELDNAMES)
        writer.writeheader()
        for row in case_rows:
            writer.writerow(asdict(row))

    primitive_csv_path = output_dir / "vaciado_trace_primitives.csv"
    with primitive_csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=PRIMITIVE_FIELDNAMES)
        writer.writeheader()
        for row in primitive_rows:
            writer.writerow(asdict(row))

    summary_path = output_dir / "vaciado_trace_primitives_study.md"
    summary_path.write_text(
        _build_summary(root, output_dir, case_csv_path, primitive_csv_path, case_rows, primitive_rows),
        encoding="utf-8",
    )
    return case_rows, primitive_rows, case_csv_path, primitive_csv_path, summary_path


def _analyze_one(path: Path, root: Path) -> tuple[TraceCaseRow, list[TracePrimitiveRow]]:
    relative_path = _relative_path(path, root)
    adaptation = adapt_pgmx_path(path)
    snapshot = adaptation.snapshot
    feature = snapshot.features[0] if snapshot.features else None
    operation = snapshot.operations[0] if snapshot.operations else None
    geometry = snapshot.geometry_by_id.get(feature.geometry_ref.id) if feature and feature.geometry_ref else None
    if feature is None or operation is None:
        return TraceCaseRow(relative_path, "missing_feature_or_operation"), []

    spec = adaptation.pocket_millings[0] if adaptation.pocket_millings else None
    strategy = operation.milling_strategy
    if not isinstance(strategy, sp.ContourParallelMillingStrategySpec):
        return TraceCaseRow(relative_path, "unsupported_strategy", geometry_type=geometry.geometry_type if geometry else ""), []

    contour_points = spec.contour_points if spec is not None else _geometry_xy_points(geometry)
    boss_contours = spec.boss_contours if spec is not None else ()
    route_seed_contours = (
        spec.resolved_boss_route_seed_contours
        if spec is not None
        else _resolved_boss_ref_contours(snapshot, feature)
    )
    tool_width = _effective_tool_width(snapshot, feature, operation, spec)
    target_depth = (
        float(spec.depth_spec.target_depth or 0.0)
        if spec is not None
        else float(feature.depth_spec.target_depth or 0.0 if feature.depth_spec else 0.0)
    )
    allowance_side = float(operation.allowance_side or 0.0)
    radial_step = tool_width * (1.0 - strategy.overlap)
    relation_context = _RelationContext(
        geometry_type=geometry.geometry_type if geometry else "",
        contour_points=contour_points,
        circle_center=geometry.profile.center_point if geometry and geometry.profile else None,
        circle_radius=geometry.profile.radius if geometry and geometry.profile else None,
        boss_bboxes=tuple(_bbox_tuple(contour) for contour in boss_contours),
        seed_bboxes=tuple(_bbox_tuple(contour) for contour in route_seed_contours),
        radial_step=radial_step,
    )

    primitive_rows: list[TracePrimitiveRow] = []
    relation_counts: Counter[str] = Counter()
    primitive_type_counts: Counter[str] = Counter()
    line_relation_counts: Counter[str] = Counter()
    arc_family_counts: Counter[str] = Counter()
    trajectory_counts: list[int] = []

    sequence_index = 0
    for toolpath in operation.toolpaths:
        if toolpath.path_type != "TrajectoryPath" or toolpath.curve is None:
            continue
        sequence_index += 1
        trajectory_counts.append(len(toolpath.curve.sampled_points))
        for primitive_index, serialization in enumerate(toolpath.curve.member_serializations, 1):
            primitive = sp._parse_geometry_primitive(serialization)
            if primitive is None:
                relation = "unparsed"
                primitive_type = "Unknown"
                start = end = center = radius = sweep = length = ""
            else:
                primitive_type = primitive.primitive_type
                relation = _classify_primitive(primitive, relation_context)
                start = _point3_text(primitive.start_point)
                end = _point3_text(primitive.end_point)
                center = _point3_text(primitive.center_point) if primitive.center_point else ""
                radius = _num(primitive.radius) if primitive.radius is not None else ""
                sweep = _num(primitive.parameter_end - primitive.parameter_start)
                length = _primitive_length(primitive)

            primitive_type_counts[primitive_type] += 1
            relation_counts[relation] += 1
            if primitive_type == "Arc":
                arc_family_counts[_arc_family_key(primitive, relation)] += 1
            elif primitive_type == "Line":
                line_relation_counts[relation] += 1
            primitive_rows.append(
                TracePrimitiveRow(
                    sample=relative_path,
                    sequence_index=sequence_index,
                    primitive_index=primitive_index,
                    primitive_type=primitive_type,
                    relation=relation,
                    start=start,
                    end=end,
                    center=center,
                    radius=radius,
                    sweep=sweep,
                    length=length,
                )
            )

    notes = _case_notes(
        geometry_type=geometry.geometry_type if geometry else "",
        circle_radius=geometry.profile.radius if geometry and geometry.profile else None,
        tool_width=tool_width,
        allowance_side=allowance_side,
        radial_step=radial_step,
        strategy=strategy,
        primitive_rows=primitive_rows,
        relation_context=relation_context,
    )
    status = "adapted_pocket" if spec is not None else "snapshot_only"
    return (
        TraceCaseRow(
            sample=relative_path,
            status=status,
            geometry_type=geometry.geometry_type if geometry else "",
            contour=_bbox_text(contour_points),
            contour_start=_point2_text(contour_points[0]) if contour_points else "",
            boss_bboxes="; ".join(_bbox_text(contour) for contour in boss_contours),
            route_seed_bboxes="; ".join(_bbox_text(contour) for contour in route_seed_contours),
            tool=spec.tool_name if spec is not None else (operation.tool_key.name if operation.tool_key else ""),
            tool_width=_num(tool_width),
            target_depth=_num(target_depth),
            allowance_side=_num(allowance_side),
            overlap=_num(strategy.overlap),
            radial_step=_num(radial_step),
            rotation=strategy.rotation_direction,
            stroke_connection=strategy.stroke_connection_strategy,
            inside_to_outside=str(strategy.inside_to_outside),
            helic=str(strategy.is_helic_strategy),
            multipass=str(strategy.allow_multiple_passes),
            axial_cutting_depth=_num(strategy.axial_cutting_depth),
            axial_finish_cutting_depth=_num(strategy.axial_finish_cutting_depth),
            trajectory_counts="+".join(str(count) for count in trajectory_counts),
            primitive_counts=_counter_text(primitive_type_counts),
            arc_families=_counter_text(arc_family_counts),
            line_families=_counter_text(line_relation_counts),
            notes=notes,
        ),
        primitive_rows,
    )


@dataclass(frozen=True)
class _RelationContext:
    geometry_type: str
    contour_points: tuple[tuple[float, float], ...]
    circle_center: tuple[float, float, float] | None
    circle_radius: float | None
    boss_bboxes: tuple[tuple[float, float, float, float], ...]
    seed_bboxes: tuple[tuple[float, float, float, float], ...]
    radial_step: float


def _classify_primitive(primitive: sp.GeometryPrimitiveSpec, context: _RelationContext) -> str:
    if primitive.primitive_type == "Arc":
        assert primitive.center_point is not None
        center_xy = (primitive.center_point[0], primitive.center_point[1])
        radius = float(primitive.radius or 0.0)
        if context.circle_center and _same_xy(center_xy, (context.circle_center[0], context.circle_center[1])):
            if context.circle_radius is not None:
                offset = context.circle_radius - radius
                return f"outer_circle_offset:{_num(offset)}"
            return "outer_circle_center"
        for bbox in context.seed_bboxes:
            if _point_on_bbox_corner(center_xy, bbox):
                return "route_seed_corner_arc"
        for bbox in context.boss_bboxes:
            if _point_on_bbox_corner(center_xy, bbox):
                return "boss_corner_arc"
        for bbox in context.seed_bboxes:
            if _point_on_bbox_edge(center_xy, bbox):
                return "route_seed_edge_arc"
        return "unclassified_arc"

    if primitive.primitive_type == "Line":
        start = primitive.start_point
        end = primitive.end_point
        if context.circle_center and _line_is_radial_to_center(start, end, context.circle_center):
            return "outer_circle_radial_link"
        if math.isclose(start[0], end[0], abs_tol=1e-6):
            return "vertical_link"
        if math.isclose(start[1], end[1], abs_tol=1e-6):
            return "horizontal_link"
        return "diagonal_link"
    return "unclassified"


def _case_notes(
    *,
    geometry_type: str,
    circle_radius: float | None,
    tool_width: float,
    allowance_side: float,
    radial_step: float,
    strategy: sp.ContourParallelMillingStrategySpec,
    primitive_rows: Sequence[TracePrimitiveRow],
    relation_context: _RelationContext,
) -> str:
    notes: list[str] = []
    if "GeomCircle" in geometry_type and circle_radius is not None:
        expected = _circle_offset_radii(circle_radius, (tool_width / 2.0) + allowance_side, radial_step)
        actual = sorted(
            {
                float(row.radius)
                for row in primitive_rows
                if row.primitive_type == "Arc" and row.relation.startswith("outer_circle_offset")
            },
            reverse=True,
        )
        if _same_float_sequence(expected, actual):
            notes.append(f"circle offsets match expected radii {','.join(_num(value) for value in expected)}")
        else:
            notes.append(
                "circle offsets differ from expected "
                f"{','.join(_num(value) for value in expected)} vs {','.join(_num(value) for value in actual)}"
            )
        if strategy.is_helic_strategy:
            z_values = {
                _z_from_point(row.start)
                for row in primitive_rows
                if row.primitive_type in {"Arc", "Line"} and row.start
            } | {
                _z_from_point(row.end)
                for row in primitive_rows
                if row.primitive_type in {"Arc", "Line"} and row.end
            }
            if len(z_values) <= 1:
                notes.append("helic flag active but trajectory primitives stay at constant Z")

    if relation_context.seed_bboxes:
        arc_rows = [row for row in primitive_rows if row.primitive_type == "Arc"]
        seed_arc_count = sum(1 for row in arc_rows if row.relation.startswith("route_seed"))
        if seed_arc_count:
            notes.append(f"{seed_arc_count}/{len(arc_rows)} arcs tied to route seed geometry")
    return "; ".join(notes)


def _circle_offset_radii(circle_radius: float, first_offset: float, radial_step: float) -> tuple[float, ...]:
    if radial_step <= 1e-9:
        return ()
    radii: list[float] = []
    current = circle_radius - first_offset
    while current > 1e-6:
        radii.append(round(current, 10))
        current -= radial_step
    return tuple(radii)


def _effective_tool_width(snapshot, feature, operation, spec) -> float:
    if spec is not None:
        return float(spec.tool_width)
    if feature.tool_width is not None and not math.isclose(float(feature.tool_width), 0.0, abs_tol=1e-6):
        return float(feature.tool_width)
    tool_diameter = _tool_diameter_from_snapshot(snapshot, operation)
    if tool_diameter is not None and not math.isclose(float(tool_diameter), 0.0, abs_tol=1e-6):
        return float(tool_diameter)
    return 0.0


def _tool_diameter_from_snapshot(snapshot, operation) -> float | None:
    if operation.tool_key is None:
        return None
    for tool in snapshot.embedded_tools:
        if tool.id == operation.tool_key.id:
            return tool.diameter
    return None


def _arc_family_key(primitive: sp.GeometryPrimitiveSpec | None, relation: str) -> str:
    if primitive is None or primitive.primitive_type != "Arc" or primitive.center_point is None:
        return relation
    return (
        f"{relation}@{_num(primitive.center_point[0])},"
        f"{_num(primitive.center_point[1])}:r{_num(float(primitive.radius or 0.0))}"
    )


def _primitive_length(primitive: sp.GeometryPrimitiveSpec) -> str:
    if primitive.primitive_type == "Arc" and primitive.radius is not None:
        return _num(abs(primitive.parameter_end - primitive.parameter_start) * primitive.radius)
    start = primitive.start_point
    end = primitive.end_point
    return _num(math.dist(start, end))


def _geometry_xy_points(geometry) -> tuple[tuple[float, float], ...]:
    if geometry is None:
        return ()
    if geometry.curve is not None and geometry.curve.sampled_points:
        return tuple((point[0], point[1]) for point in geometry.curve.sampled_points)
    if geometry.profile is None:
        return ()
    if geometry.profile.primitives:
        points = [(primitive.start_point[0], primitive.start_point[1]) for primitive in geometry.profile.primitives]
        points.append((geometry.profile.primitives[-1].end_point[0], geometry.profile.primitives[-1].end_point[1]))
        return tuple(points)
    return ()


def _resolved_boss_ref_contours(snapshot, feature) -> tuple[tuple[tuple[float, float], ...], ...]:
    contours: list[tuple[tuple[float, float], ...]] = []
    for ref in feature.boss_refs:
        geometry = snapshot.geometry_by_id.get(ref.id)
        points = _geometry_xy_points(geometry)
        if points:
            contours.append(points)
    return tuple(contours)


def _line_is_radial_to_center(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    center: tuple[float, float, float],
) -> bool:
    start_vector = (start[0] - center[0], start[1] - center[1])
    end_vector = (end[0] - center[0], end[1] - center[1])
    cross = (start_vector[0] * end_vector[1]) - (start_vector[1] * end_vector[0])
    return math.isclose(cross, 0.0, abs_tol=1e-6)


def _point_on_bbox_corner(point: tuple[float, float], bbox: tuple[float, float, float, float]) -> bool:
    min_x, max_x, min_y, max_y = bbox
    return any(
        _same_xy(point, corner)
        for corner in (
            (min_x, min_y),
            (min_x, max_y),
            (max_x, min_y),
            (max_x, max_y),
        )
    )


def _point_on_bbox_edge(point: tuple[float, float], bbox: tuple[float, float, float, float]) -> bool:
    x, y = point
    min_x, max_x, min_y, max_y = bbox
    on_vertical = (math.isclose(x, min_x, abs_tol=1e-6) or math.isclose(x, max_x, abs_tol=1e-6)) and (
        min_y - 1e-6 <= y <= max_y + 1e-6
    )
    on_horizontal = (math.isclose(y, min_y, abs_tol=1e-6) or math.isclose(y, max_y, abs_tol=1e-6)) and (
        min_x - 1e-6 <= x <= max_x + 1e-6
    )
    return on_vertical or on_horizontal


def _bbox_tuple(points: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    if not points:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), max(xs), min(ys), max(ys))


def _bbox_text(points: Sequence[tuple[float, float]]) -> str:
    if not points:
        return ""
    min_x, max_x, min_y, max_y = _bbox_tuple(points)
    return f"X {_num(min_x)}..{_num(max_x)}, Y {_num(min_y)}..{_num(max_y)}"


def _same_xy(first: tuple[float, float], second: tuple[float, float], *, tolerance: float = 1e-6) -> bool:
    return math.isclose(first[0], second[0], abs_tol=tolerance) and math.isclose(
        first[1],
        second[1],
        abs_tol=tolerance,
    )


def _same_float_sequence(first: Sequence[float], second: Sequence[float], *, tolerance: float = 1e-6) -> bool:
    return len(first) == len(second) and all(math.isclose(a, b, abs_tol=tolerance) for a, b in zip(first, second))


def _z_from_point(point_text: str) -> float:
    try:
        return float(point_text.split(",")[2])
    except (IndexError, ValueError):
        return 0.0


def _counter_text(counter: Counter[str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common())


def _point2_text(point: tuple[float, float]) -> str:
    return f"{_num(point[0])},{_num(point[1])}"


def _point3_text(point: tuple[float, float, float]) -> str:
    return f"{_num(point[0])},{_num(point[1])},{_num(point[2])}"


def _num(value: float | None) -> str:
    if value is None:
        return ""
    return f"{float(value):.6f}".rstrip("0").rstrip(".")


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _build_summary(
    root: Path,
    output_dir: Path,
    case_csv_path: Path,
    primitive_csv_path: Path,
    case_rows: Sequence[TraceCaseRow],
    primitive_rows: Sequence[TracePrimitiveRow],
) -> str:
    adapted = sum(1 for row in case_rows if row.status == "adapted_pocket")
    snapshot_only = sum(1 for row in case_rows if row.status == "snapshot_only")
    relation_counts = Counter(row.relation for row in primitive_rows)
    primitive_counts = Counter(row.primitive_type for row in primitive_rows)
    lines = [
        "# Maestro Vaciado Trace Primitive Study",
        "",
        f"- Root: `{root}`",
        f"- Output dir: `{output_dir}`",
        f"- Case CSV: `{case_csv_path}`",
        f"- Primitive CSV: `{primitive_csv_path}`",
        f"- Cases: `{len(case_rows)}` (`{adapted}` adapted, `{snapshot_only}` snapshot-only)",
        f"- Primitives: `{len(primitive_rows)}`",
        "",
        "## Primitive Mix",
        "",
        *_counter_lines(primitive_counts),
        "",
        "## Relation Mix",
        "",
        *_counter_lines(relation_counts),
        "",
        "## Candidate Trace Grammar",
        "",
        "1. Normalize the input contour and keep its start point. For the rectangular subset, Maestro's observed anchor follows the start edge and the effective first offset.",
        "2. Compute `effective_offset = tool_radius + AllowanceSide`.",
        "3. Compute `radial_step = tool_width * (1 - overlap)`; do not treat the radius match at 50% overlap as the primary rule.",
        "4. Without islands, generate offset loops of the exterior contour. Rectangles and the circular `Vaciado_035` both follow this offset-family idea.",
        "5. With islands, use `BossList.GeometryID` as route-seed evidence separately from physical `BossGeometryList`; seed corners explain many arc centers.",
        "6. Apply `InsideToOutSide` to loop ordering and bridge direction, then `RotationDirection` to loop orientation.",
        "7. Apply `StrokeConnectionStrategy` at transitions between levels or separated holes; it may not alter a single-level contiguous path.",
        "8. Apply multipass as Z-level sequencing inside one or more `TrajectoryPath` entries.",
        "",
        "## Focus Cases",
        "",
        *(_focus_case_lines(case_rows, primitive_rows)),
    ]
    return "\n".join(lines)


def _focus_case_lines(
    case_rows: Sequence[TraceCaseRow],
    primitive_rows: Sequence[TracePrimitiveRow],
) -> list[str]:
    by_sample = {row.sample: row for row in case_rows}
    primitives_by_sample: dict[str, list[TracePrimitiveRow]] = defaultdict(list)
    for row in primitive_rows:
        primitives_by_sample[row.sample].append(row)

    lines: list[str] = []
    for sample in (
        "manual\\Vaciado_035.pgmx",
        "manual\\Vaciado_027_E006.pgmx",
        "manual\\Vaciado_027_E002.pgmx",
        "manual\\Vaciado_027_E005.pgmx",
        "manual\\Vaciado_027_E004.pgmx",
        "manual\\Vaciado_029_E006.pgmx",
        "manual\\Vaciado_031_E004.pgmx",
    ):
        case = by_sample.get(sample)
        if case is None:
            continue
        lines.extend(
            [
                f"### `{sample}`",
                "",
                f"- Geometry: `{case.geometry_type}` / contour `{case.contour}`.",
                f"- Tool/step: `{case.tool}` width `{case.tool_width}`, radial step `{case.radial_step}`.",
                f"- Strategy: inside_to_outside `{case.inside_to_outside}`, stroke `{case.stroke_connection}`, rotation `{case.rotation}`, helic `{case.helic}`.",
                f"- Trajectory counts: `{case.trajectory_counts}`.",
                f"- Primitive counts: `{case.primitive_counts}`.",
                f"- Arc families: `{_summarized_counter_text(case.arc_families)}`.",
                f"- Notes: {case.notes or 'none'}.",
                "",
            ]
        )
        if sample.endswith("Vaciado_035.pgmx"):
            lines.extend(
                [
                    "| seq | idx | type | relation | start | end | center | radius |",
                    "| ---: | ---: | --- | --- | --- | --- | --- | --- |",
                ]
            )
            for primitive in primitives_by_sample[sample]:
                lines.append(
                    f"| {primitive.sequence_index} | {primitive.primitive_index} | {primitive.primitive_type} | "
                    f"{primitive.relation} | `{primitive.start}` | `{primitive.end}` | "
                    f"`{primitive.center}` | `{primitive.radius}` |"
                )
            lines.append("")
    return lines


def _counter_lines(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- none"]
    return [f"- `{key}`: `{value}`" for key, value in counter.most_common()]


def _summarized_counter_text(counter_text: str, *, max_items: int = 12) -> str:
    if not counter_text:
        return "none"
    items = counter_text.split("; ")
    if len(items) <= max_items:
        return counter_text
    visible = "; ".join(items[:max_items])
    return f"{visible}; ... (+{len(items) - max_items} more in CSV)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Maestro pocket milling trajectory primitives.")
    parser.add_argument("--root", type=Path, default=EXTERNAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-only", action="store_true", help="Skip E00x tool-variant files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    case_rows, primitive_rows, case_csv, primitive_csv, summary = analyze_trace_primitives(
        args.root,
        args.output_dir,
        include_variants=not args.base_only,
    )
    print(f"Cases: {len(case_rows)}")
    print(f"Primitives: {len(primitive_rows)}")
    print(f"Case CSV: {case_csv}")
    print(f"Primitive CSV: {primitive_csv}")
    print(f"Summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
