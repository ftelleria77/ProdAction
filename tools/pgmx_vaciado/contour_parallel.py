"""Contour-parallel path experiments for rectangular Vaciado pockets."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from tools import synthesize_pgmx as sp
from tools.pgmx_adapters import adapt_pgmx_path

from . import EXTERNAL_ROOT


DEFAULT_OUTPUT_DIR = EXTERNAL_ROOT / "_analysis"


@dataclass(frozen=True)
class ContourParallelComparisonRow:
    relative_path: str
    status: str
    actual_points: int = 0
    generated_points: int = 0
    exact_points: bool = False
    max_xy_delta: float = 0.0
    actual_x_range: str = ""
    generated_x_range: str = ""
    actual_y_range: str = ""
    generated_y_range: str = ""
    first_actual: str = ""
    first_generated: str = ""
    last_actual: str = ""
    last_generated: str = ""
    tool_width: float = 0.0
    allowance_side: float = 0.0
    overlap: float = 0.0
    rotation_direction: str = ""
    inside_to_outside: bool = True
    notes: str = ""


FIELDNAMES = tuple(ContourParallelComparisonRow.__dataclass_fields__)


def generate_rectangular_contour_parallel_path(
    *,
    length: float,
    width: float,
    contour_points: Sequence[tuple[float, float]],
    tool_width: float,
    allowance_side: float = 0.0,
    overlap: float = 0.5,
    radial_cutting_depth: float = 0.0,
    rotation_direction: str = "CounterClockwise",
    inside_to_outside: bool = True,
) -> tuple[tuple[float, float], ...]:
    """Generate Maestro-like XY points for a rectangular contour-parallel pocket."""

    if length <= 0.0 or width <= 0.0:
        raise ValueError("length and width must be positive.")
    if tool_width <= 0.0:
        raise ValueError("tool_width must be positive.")
    if overlap < 0.0 or overlap >= 1.0:
        raise ValueError("overlap must be in the [0, 1) range.")

    outer_offset = (tool_width / 2.0) + allowance_side
    if outer_offset < -1e-9:
        raise ValueError("tool radius + allowance_side must not be negative.")
    radial_step = tool_width * (1.0 - overlap)
    radial_depth = radial_cutting_depth if radial_cutting_depth > 0.0 else radial_step
    offsets_outer_to_inner = _rectangular_offsets(
        outer_offset=outer_offset,
        half_minor=min(length, width) / 2.0,
        radial_step=radial_step,
        radial_depth=radial_depth,
    )
    offsets = (
        tuple(reversed(offsets_outer_to_inner))
        if inside_to_outside
        else offsets_outer_to_inner
    )
    if not offsets:
        return ()

    edge = _effective_start_edge(
        _start_edge(contour_points, length=length, width=width),
        allowance_side=allowance_side,
        rotation_direction=rotation_direction,
    )
    anchor = _start_anchor(
        contour_points[0],
        edge=edge,
        first_offset=offsets[0],
        length=length,
        width=width,
        allowance_side=allowance_side,
        rotation_direction=rotation_direction,
    )

    points: list[tuple[float, float]] = []
    if not inside_to_outside:
        return _generate_outside_to_inside(
            offsets=offsets,
            anchor=anchor,
            edge=edge,
            length=length,
            width=width,
            rotation_direction=rotation_direction,
        )

    for index, offset in enumerate(offsets):
        points.extend(
            _ring_points(
                offset=offset,
                anchor=anchor,
                edge=edge,
                length=length,
                width=width,
                rotation_direction=rotation_direction,
            )
        )
    return tuple(points)


def generate_rectangular_contour_parallel_xyz_path(
    *,
    length: float,
    width: float,
    depth: float,
    contour_points: Sequence[tuple[float, float]],
    tool_width: float,
    target_depth: float,
    security_plane: float,
    allowance_side: float = 0.0,
    overlap: float = 0.5,
    radial_cutting_depth: float = 0.0,
    rotation_direction: str = "CounterClockwise",
    inside_to_outside: bool = True,
    stroke_connection_strategy: str = "LiftShiftPlunge",
    allow_multiple_passes: bool = False,
    axial_cutting_depth: float = 0.0,
    axial_finish_cutting_depth: float = 0.0,
) -> tuple[tuple[float, float, float], ...]:
    """Generate Maestro-like XYZ points for a rectangular Vaciado trajectory."""

    xy_path = generate_rectangular_contour_parallel_path(
        length=length,
        width=width,
        contour_points=contour_points,
        tool_width=tool_width,
        allowance_side=allowance_side,
        overlap=overlap,
        radial_cutting_depth=radial_cutting_depth,
        rotation_direction=rotation_direction,
        inside_to_outside=inside_to_outside,
    )
    if not xy_path:
        return ()

    levels = _cut_depth_levels(
        target_depth=target_depth,
        allow_multiple_passes=allow_multiple_passes,
        axial_cutting_depth=axial_cutting_depth,
        axial_finish_cutting_depth=axial_finish_cutting_depth,
    )
    security_z = depth + security_plane
    strategy = stroke_connection_strategy.strip()
    points: list[tuple[float, float, float]] = []
    first_xy = xy_path[0]
    last_xy = xy_path[-1]

    for index, cut_depth in enumerate(levels):
        cut_z = depth - cut_depth
        if index > 0:
            if strategy == "Straghtline":
                previous_z = depth - levels[index - 1]
                points.append((first_xy[0], first_xy[1], previous_z))
            else:
                points.append((last_xy[0], last_xy[1], security_z))
                points.append((first_xy[0], first_xy[1], security_z))
        points.extend((x, y, cut_z) for x, y in xy_path)
    return tuple(points)


def compare_manual_samples(
    root: Path,
    output_dir: Path,
    *,
    max_index: int = 17,
) -> tuple[list[ContourParallelComparisonRow], Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[ContourParallelComparisonRow] = []
    for path in sorted((root / "manual").glob("Vaciado_*.pgmx")):
        try:
            index = int(path.stem.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        if index > max_index:
            continue
        rows.append(_compare_one(path, root))

    csv_path = output_dir / "vaciado_contour_parallel_comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    summary_path = output_dir / "vaciado_contour_parallel_comparison.md"
    summary_path.write_text(_build_summary(rows, root, csv_path), encoding="utf-8")
    return rows, csv_path, summary_path


def _compare_one(path: Path, root: Path) -> ContourParallelComparisonRow:
    relative_path = _relative_path(path, root)
    try:
        result = adapt_pgmx_path(path)
        if not result.pocket_millings:
            return ContourParallelComparisonRow(relative_path, "no_pocket")
        spec = result.pocket_millings[0]
        actual_xyz = _actual_trajectory_xyz(result.snapshot.operations[0])
        actual = tuple((x, y) for x, y, _z in actual_xyz)
        strategy = spec.milling_strategy
        generated_xyz = generate_rectangular_contour_parallel_xyz_path(
            length=result.snapshot.state.length,
            width=result.snapshot.state.width,
            depth=result.snapshot.state.depth,
            contour_points=spec.contour_points,
            tool_width=spec.tool_width,
            target_depth=float(spec.depth_spec.target_depth or 0.0),
            security_plane=spec.security_plane,
            allowance_side=spec.allowance_side,
            overlap=strategy.overlap,
            radial_cutting_depth=strategy.radial_cutting_depth,
            rotation_direction=strategy.rotation_direction,
            inside_to_outside=strategy.inside_to_outside,
            stroke_connection_strategy=strategy.stroke_connection_strategy,
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
        generated = tuple((x, y) for x, y, _z in generated_xyz)
        max_delta = _max_xy_delta(actual, generated)
        return ContourParallelComparisonRow(
            relative_path=relative_path,
            status="ok",
            actual_points=len(actual),
            generated_points=len(generated),
            exact_points=_same_xyz_points(actual_xyz, generated_xyz),
            max_xy_delta=max_delta,
            actual_x_range=_range_text(point[0] for point in actual),
            generated_x_range=_range_text(point[0] for point in generated),
            actual_y_range=_range_text(point[1] for point in actual),
            generated_y_range=_range_text(point[1] for point in generated),
            first_actual=_point_text(actual[0]) if actual else "",
            first_generated=_point_text(generated[0]) if generated else "",
            last_actual=_point_text(actual[-1]) if actual else "",
            last_generated=_point_text(generated[-1]) if generated else "",
            tool_width=spec.tool_width,
            allowance_side=spec.allowance_side,
            overlap=strategy.overlap,
            rotation_direction=strategy.rotation_direction,
            inside_to_outside=strategy.inside_to_outside,
        )
    except Exception as exc:  # pragma: no cover - evidence script
        return ContourParallelComparisonRow(relative_path, "error", notes=str(exc))


def _rectangular_offsets(
    *,
    outer_offset: float,
    half_minor: float,
    radial_step: float,
    radial_depth: float,
) -> tuple[float, ...]:
    offsets: list[float] = []
    current = outer_offset
    while current <= half_minor + 1e-6:
        offsets.append(round(current, 10))
        current += radial_step
    if offsets and offsets[-1] + radial_depth <= half_minor + 1e-6:
        offsets.append(round(offsets[-1] + radial_depth, 10))
    return tuple(offsets)


def _cut_depth_levels(
    *,
    target_depth: float,
    allow_multiple_passes: bool,
    axial_cutting_depth: float,
    axial_finish_cutting_depth: float,
) -> tuple[float, ...]:
    target = float(target_depth)
    if target <= 0.0:
        raise ValueError("target_depth must be positive for Vaciado.")
    step = float(axial_cutting_depth)
    finish = float(axial_finish_cutting_depth)
    if not allow_multiple_passes or step <= 0.0 or target <= max(finish, step):
        return (target,)

    rough_limit = target - max(finish, 0.0)
    levels: list[float] = []
    current = step
    while current <= rough_limit + 1e-6:
        levels.append(round(current, 10))
        current += step
    if not levels:
        levels.append(round(min(step, target), 10))
    if not math.isclose(levels[-1], target, abs_tol=1e-6):
        levels.append(round(target, 10))
    return tuple(levels)


def _start_edge(
    contour_points: Sequence[tuple[float, float]],
    *,
    length: float,
    width: float,
) -> str:
    x, y = contour_points[0]
    if math.isclose(y, 0.0, abs_tol=1e-6):
        return "bottom"
    if math.isclose(y, width, abs_tol=1e-6):
        return "top"
    if math.isclose(x, 0.0, abs_tol=1e-6):
        return "left"
    if math.isclose(x, length, abs_tol=1e-6):
        return "right"
    return "bottom"


def _start_anchor(
    start: tuple[float, float],
    *,
    edge: str,
    first_offset: float,
    length: float,
    width: float,
    allowance_side: float,
    rotation_direction: str,
) -> float:
    clockwise = rotation_direction == "Clockwise"
    if edge in {"bottom", "top"}:
        if allowance_side < 0.0 and not clockwise:
            return length - first_offset
        return _clamp(start[0], first_offset, length - first_offset)
    if allowance_side < 0.0 and not clockwise:
        return first_offset
    return _clamp(start[1], first_offset, width - first_offset)


def _generate_outside_to_inside(
    *,
    offsets: Sequence[float],
    anchor: float,
    edge: str,
    length: float,
    width: float,
    rotation_direction: str,
) -> tuple[tuple[float, float], ...]:
    points: list[tuple[float, float]] = []
    for index, offset in enumerate(offsets):
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else offset
        ring_anchor = _outside_to_inside_anchor(anchor, edge, next_offset)
        start = _corner_point(edge, offset, length, width)
        next_anchor = _anchor_point(ring_anchor, edge, next_offset, length, width)
        if index == 0:
            points.append(start)
        if index + 1 < len(offsets):
            points.append(_project_anchor_to_edge(next_anchor, edge, offset, length, width))
        points.extend(
            _ring_points(
                offset=offset,
                anchor=ring_anchor,
                edge=edge,
                length=length,
                width=width,
                rotation_direction=rotation_direction,
                include_start=False,
            )
        )
        if index + 1 < len(offsets):
            points.append(next_anchor)
    return tuple(points)


def _outside_to_inside_anchor(anchor: float, edge: str, next_offset: float) -> float:
    if edge in {"bottom", "left"}:
        return max(anchor, next_offset)
    return anchor


def _effective_start_edge(
    edge: str,
    *,
    allowance_side: float,
    rotation_direction: str,
) -> str:
    if edge == "bottom" and rotation_direction == "Clockwise":
        return "left"
    if edge == "bottom" and allowance_side < 0.0:
        return "right"
    if edge == "top":
        return "right" if rotation_direction == "Clockwise" else "left"
    return edge


def _ring_points(
    *,
    offset: float,
    anchor: float,
    edge: str,
    length: float,
    width: float,
    rotation_direction: str,
    include_start: bool = True,
) -> list[tuple[float, float]]:
    left, right = offset, length - offset
    bottom, top = offset, width - offset
    anchor_point = _anchor_point(anchor, edge, offset, length, width)

    if math.isclose(bottom, top, abs_tol=1e-6):
        line = [anchor_point, (right, bottom), anchor_point]
        line = _dedupe_consecutive(line)
        return line if include_start else line[1:]

    ccw_sequences = {
        "bottom": [anchor_point, (right, bottom), (right, top), (left, top), (left, bottom), anchor_point],
        "top": [anchor_point, (left, bottom), (right, bottom), (right, top), (left, top), anchor_point],
        "left": [anchor_point, (left, bottom), (right, bottom), (right, top), (left, top), anchor_point],
        "right": [anchor_point, (right, top), (left, top), (left, bottom), (right, bottom), anchor_point],
    }
    cw_sequences = {
        "bottom": [anchor_point, (left, top), (right, top), (right, bottom), (left, bottom), anchor_point],
        "top": [anchor_point, (right, bottom), (left, bottom), (left, top), (right, top), anchor_point],
        "left": [anchor_point, (left, top), (right, top), (right, bottom), (left, bottom), anchor_point],
        "right": [anchor_point, (right, bottom), (left, bottom), (left, top), (right, top), anchor_point],
    }
    sequence = (cw_sequences if rotation_direction == "Clockwise" else ccw_sequences)[edge]
    sequence = _dedupe_consecutive(sequence)
    return sequence if include_start else sequence[1:]


def _dedupe_consecutive(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for point in points:
        if result and math.isclose(result[-1][0], point[0], abs_tol=1e-9) and math.isclose(
            result[-1][1],
            point[1],
            abs_tol=1e-9,
        ):
            continue
        result.append(point)
    return result


def _anchor_point(
    anchor: float,
    edge: str,
    offset: float,
    length: float,
    width: float,
) -> tuple[float, float]:
    if edge == "bottom":
        return (_clamp(anchor, offset, length - offset), offset)
    if edge == "top":
        return (_clamp(anchor, offset, length - offset), width - offset)
    if edge == "left":
        return (offset, _clamp(anchor, offset, width - offset))
    return (length - offset, _clamp(anchor, offset, width - offset))


def _corner_point(edge: str, offset: float, length: float, width: float) -> tuple[float, float]:
    if edge == "bottom":
        return (offset, offset)
    if edge == "top":
        return (length - offset, width - offset)
    if edge == "left":
        return (offset, width - offset)
    return (length - offset, offset)


def _project_anchor_to_edge(
    anchor_point: tuple[float, float],
    edge: str,
    offset: float,
    length: float,
    width: float,
) -> tuple[float, float]:
    x, y = anchor_point
    if edge == "bottom":
        return (x, offset)
    if edge == "top":
        return (x, width - offset)
    if edge == "left":
        return (offset, y)
    return (length - offset, y)


def _actual_trajectory_xy(operation) -> tuple[tuple[float, float], ...]:
    return tuple((x, y) for x, y, _z in _actual_trajectory_xyz(operation))


def _actual_trajectory_xyz(operation) -> tuple[tuple[float, float, float], ...]:
    for toolpath in operation.toolpaths:
        if toolpath.path_type == "TrajectoryPath" and toolpath.curve is not None:
            return tuple((point[0], point[1], point[2]) for point in toolpath.curve.sampled_points)
    return ()


def _same_points(
    actual: Sequence[tuple[float, float]],
    generated: Sequence[tuple[float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    if len(actual) != len(generated):
        return False
    return all(
        math.isclose(a[0], g[0], abs_tol=tolerance)
        and math.isclose(a[1], g[1], abs_tol=tolerance)
        for a, g in zip(actual, generated)
    )


def _same_xyz_points(
    actual: Sequence[tuple[float, float, float]],
    generated: Sequence[tuple[float, float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    if len(actual) != len(generated):
        return False
    return all(
        math.isclose(a[0], g[0], abs_tol=tolerance)
        and math.isclose(a[1], g[1], abs_tol=tolerance)
        and math.isclose(a[2], g[2], abs_tol=tolerance)
        for a, g in zip(actual, generated)
    )


def _max_xy_delta(
    actual: Sequence[tuple[float, float]],
    generated: Sequence[tuple[float, float]],
) -> float:
    if not actual or not generated or len(actual) != len(generated):
        return float("inf")
    return max(math.hypot(a[0] - g[0], a[1] - g[1]) for a, g in zip(actual, generated))


def _range_text(values: Iterable[float]) -> str:
    values = list(values)
    if not values:
        return ""
    return f"{_num(min(values))}..{_num(max(values))}"


def _point_text(point: tuple[float, float]) -> str:
    return f"{_num(point[0])},{_num(point[1])}"


def _num(value: float) -> str:
    return f"{float(value):.6f}".rstrip("0").rstrip(".")


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(float(value), float(lower)), float(upper))


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _build_summary(
    rows: Sequence[ContourParallelComparisonRow],
    root: Path,
    csv_path: Path,
) -> str:
    exact = sum(1 for row in rows if row.exact_points)
    lines = [
        "# Vaciado Contour Parallel Comparison",
        "",
        f"- Root: `{root}`",
        f"- CSV: `{csv_path}`",
        f"- Rows: `{len(rows)}`",
        f"- Exact point sequences: `{exact}/{len(rows)}`",
        "",
        "## Rows",
        "",
        "| sample | status | actual | generated | exact | max_xy_delta | first | last |",
        "| --- | --- | ---: | ---: | --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{row.relative_path}` | {row.status} | {row.actual_points} | "
            f"{row.generated_points} | {str(row.exact_points).lower()} | "
            f"{_num(row.max_xy_delta) if math.isfinite(row.max_xy_delta) else 'inf'} | "
            f"{row.first_generated} | {row.last_generated} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare experimental rectangular ContourParallel generation against manual Vaciado samples."
    )
    parser.add_argument("--root", type=Path, default=EXTERNAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-index", type=int, default=19)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, csv_path, summary_path = compare_manual_samples(
        args.root,
        args.output_dir,
        max_index=args.max_index,
    )
    exact = sum(1 for row in rows if row.exact_points)
    print(f"Compared {len(rows)} rows. Exact: {exact}/{len(rows)}")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
