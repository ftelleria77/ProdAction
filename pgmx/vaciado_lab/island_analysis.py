"""Analyze Vaciado samples with BossGeometryList islands.

This is an evidence tool for the Vaciado laboratory. It records how Maestro
materializes islands before any productive serialization rule is enabled.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from pgmx.adapters import adapt_pgmx_path
from pgmx.vaciado_lab.contour_parallel import (
    _actual_trajectory_xyz_sequences,
    generate_rectangular_contour_parallel_xyz_path,
)

from . import EXTERNAL_ROOT


DEFAULT_CASES = (22, 27, 28, 29, 30, 31)
DEFAULT_OUTPUT_DIR = EXTERNAL_ROOT / "_analysis" / "vaciado_islands_analysis"


@dataclass(frozen=True)
class IslandSequenceRow:
    sample: str
    sequence_index: int
    point_count: int
    x_range: str
    y_range: str
    z_values: str
    first_point: str
    last_point: str
    notes: str = ""


@dataclass(frozen=True)
class RoundedKernelLoopRule:
    kernel_bbox: tuple[float, float, float, float]
    radius: float
    max_delta: float


FIELDNAMES = tuple(IslandSequenceRow.__dataclass_fields__)


def analyze_island_samples(
    root: Path,
    output_dir: Path,
    *,
    cases: Sequence[int] = DEFAULT_CASES,
) -> tuple[list[IslandSequenceRow], Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[IslandSequenceRow] = []
    markdown_sections: list[str] = []

    for index in cases:
        path = root / "manual" / f"Vaciado_{index:03d}.pgmx"
        section, case_rows = _analyze_one(path, root)
        markdown_sections.append(section)
        rows.extend(case_rows)
    markdown_sections.append(_build_cross_case_notes(root))

    csv_path = output_dir / "vaciado_islands_sequences.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    summary_path = output_dir / "vaciado_islands_analysis.md"
    summary_path.write_text(
        _build_summary(root, output_dir, csv_path, markdown_sections),
        encoding="utf-8",
    )
    return rows, csv_path, summary_path


def _analyze_one(path: Path, root: Path) -> tuple[str, list[IslandSequenceRow]]:
    relative_path = _relative_path(path, root)
    if not path.exists():
        return (
            "\n".join(
                [
                    f"## `{relative_path}`",
                    "",
                    "- Status: missing.",
                    "",
                ]
            ),
            [],
        )

    adaptation = adapt_pgmx_path(path)
    if not adaptation.pocket_millings:
        return (
            "\n".join(
                [
                    f"## `{relative_path}`",
                    "",
                    "- Status: no pocket milling adaptation.",
                    f"- Unsupported entries: `{len(adaptation.unsupported_entries)}`",
                    "",
                ]
            ),
            [],
        )

    spec = adaptation.pocket_millings[0]
    operation = adaptation.snapshot.operations[0]
    feature = adaptation.snapshot.features[0]
    sequences = _actual_trajectory_xyz_sequences(operation)
    rows = [
        IslandSequenceRow(
            sample=relative_path,
            sequence_index=index,
            point_count=len(sequence),
            x_range=_range_text(point[0] for point in sequence),
            y_range=_range_text(point[1] for point in sequence),
            z_values=",".join(_num(value) for value in _z_values(sequence)),
            first_point=_point3_text(sequence[0]),
            last_point=_point3_text(sequence[-1]),
            notes=_sequence_note(relative_path, index, sequence, sequences, spec, adaptation),
        )
        for index, sequence in enumerate(sequences, 1)
    ]

    boss_bboxes = [_bbox_text(boss) for boss in spec.boss_contours]
    boss_refs = [
        f"{ref.id}:{ref.object_type.rsplit('.', 1)[-1]}"
        for ref in feature.boss_refs
    ]
    resolved_boss_ref_contours = resolved_boss_ref_xy_contours(adaptation)
    resolved_boss_ref_bboxes = [
        f"{ref_id}:{_bbox_text(contour)}" if contour else f"{ref_id}:unresolved"
        for ref_id, contour in resolved_boss_ref_contours
    ]
    boss_ref_note = _boss_reference_note(spec.boss_contours, resolved_boss_ref_contours)
    toolpath_summary = " | ".join(
        f"{toolpath.path_type}:{len(toolpath.curve.sampled_points) if toolpath.curve else 0}"
        for toolpath in operation.toolpaths
    )
    strategy = spec.milling_strategy

    lines = [
        f"## `{relative_path}`",
        "",
        f"- Pocket contour bbox: `{_bbox_text(spec.contour_points)}`",
        f"- Boss count: `{len(spec.boss_contours)}`",
        f"- BossGeometryList bboxes: `{'; '.join(boss_bboxes) if boss_bboxes else 'none'}`",
        f"- Boss refs: `{'; '.join(boss_refs) if boss_refs else 'none'}`",
        f"- BossList ref bboxes: `{'; '.join(resolved_boss_ref_bboxes) if resolved_boss_ref_bboxes else 'none'}`",
        f"- Boss ref note: {boss_ref_note}",
        f"- Tool: `{spec.tool_name}` / `{spec.tool_id}` / width `{_num(spec.tool_width)}`",
        f"- Depth: `{_num(float(spec.depth_spec.target_depth or 0.0))}`",
        f"- Strategy: rotation `{strategy.rotation_direction}`, inside_to_outside "
        f"`{str(strategy.inside_to_outside).lower()}`, stroke `{strategy.stroke_connection_strategy}`, "
        f"overlap `{_num(strategy.overlap)}`, radial `{_num(strategy.radial_cutting_depth)}`",
        f"- Toolpaths: `{toolpath_summary}`",
        "",
        "| seq | points | X range | Y range | Z | first | last | note |",
        "| ---: | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.sequence_index} | {row.point_count} | `{row.x_range}` | "
            f"`{row.y_range}` | `{row.z_values}` | `{row.first_point}` | "
            f"`{row.last_point}` | {row.notes} |"
        )
    if path.name == "Vaciado_027.pgmx":
        lines.extend(_vaciado_027_notes(adaptation, sequences))
    for index, sequence in enumerate(sequences, 1):
        offset_note = _offset_repeat_note(sequence, spec.milling_strategy.radial_cutting_depth or spec.radial_step)
        if offset_note:
            lines.extend(["", f"### Sequence {index} Offset Structure", "", f"- {offset_note}"])
    lines.append("")
    return "\n".join(lines), rows


def _sequence_note(
    relative_path: str,
    sequence_index: int,
    sequence: Sequence[tuple[float, float, float]],
    sequences: Sequence[Sequence[tuple[float, float, float]]],
    spec,
    adaptation,
) -> str:
    if relative_path.endswith("Vaciado_027.pgmx") and sequence_index == 1:
        generated = _bossless_rectangular_path(adaptation, spec)
        prefix = _common_prefix_length(sequence, generated)
        return f"shares `{prefix}` starting points with bossless rectangular path"
    offset_note = _offset_repeat_note(sequence, spec.milling_strategy.radial_cutting_depth or spec.radial_step)
    if offset_note:
        return offset_note
    if len(sequences) > 1:
        return "separate island/exterior trajectory"
    if spec.boss_contours:
        return "single trajectory mixes exterior and island logic"
    return ""


def _vaciado_027_notes(adaptation, sequences: Sequence[Sequence[tuple[float, float, float]]]) -> list[str]:
    spec = adaptation.pocket_millings[0]
    generated = _bossless_rectangular_path(adaptation, spec)
    first_sequence = sequences[0] if sequences else ()
    prefix = _common_prefix_length(first_sequence, generated)
    lines = [
        "",
        "### `Vaciado_027` Isolation",
        "",
        f"- Bossless rectangular generator points: `{len(generated)}`.",
        f"- First Maestro trajectory points: `{len(first_sequence)}`.",
        f"- Shared prefix: `{prefix}` points.",
    ]
    if prefix < len(first_sequence):
        lines.append(
            "- First divergence: Maestro keeps the outer ring but changes the bridge "
            "toward the next ring before stopping the exterior trajectory."
        )
    if len(sequences) > 1:
        island_sequence = sequences[1]
        lines.extend(
            [
                f"- Island trajectory points: `{len(island_sequence)}`.",
                f"- Island trajectory bbox: `{_bbox_text(tuple((x, y) for x, y, _ in island_sequence))}`.",
                "- The island trajectory is not a simple rectangle around the boss bbox; "
                "it has diagonal/corner transition points, so productive generation "
                "needs a dedicated island offset rule before lifting the guardrail.",
            ]
        )
        offset_note = _offset_repeat_note(island_sequence, spec.milling_strategy.radial_cutting_depth or spec.radial_step)
        if offset_note:
            lines.append(f"- Internal offset structure: {offset_note}.")
    return lines


def _build_cross_case_notes(root: Path) -> str:
    try:
        v027 = adapt_pgmx_path(root / "manual" / "Vaciado_027.pgmx")
        v031 = adapt_pgmx_path(root / "manual" / "Vaciado_031.pgmx")
    except Exception as exc:  # pragma: no cover - evidence script
        return "\n".join(["## Cross-Case Notes", "", f"- Could not compare cases: `{exc}`", ""])

    v027_sequences = _actual_trajectory_xyz_sequences(v027.snapshot.operations[0])
    v031_sequences = _actual_trajectory_xyz_sequences(v031.snapshot.operations[0])
    lines = ["## Cross-Case Notes", ""]
    if len(v027_sequences) >= 2 and len(v031_sequences) >= 2:
        v027_base = v027_sequences[1][: len(v027_sequences[1]) // 2]
        v031_island = v031_sequences[1]
        if _same_xy_sequence(v027_base, v031_island):
            lines.append(
                "- `Vaciado_027` sequence 2 first loop matches `Vaciado_031` sequence 2 "
                "exactly in XY. This suggests a reusable base island/corridor loop before "
                "additional radial offsets are applied."
            )
            rule = infer_rounded_kernel_loop_xy(v027_base)
            if rule:
                lines.extend(
                    [
                        "- Base-loop rule candidate: the shared `10` points are exactly a "
                        "rounded-kernel contour with kernel "
                        f"`{_bbox_tuple_text(rule.kernel_bbox)}` and radius `{_num(rule.radius)}` "
                        f"(max delta `{_num(rule.max_delta)}`).",
                        "- `Vaciado_027`: "
                        f"{_kernel_relation_to_bosses(rule.kernel_bbox, v027.pocket_millings[0].boss_contours)}",
                        "- `Vaciado_031`: "
                        f"{_kernel_relation_to_bosses(rule.kernel_bbox, v031.pocket_millings[0].boss_contours)}",
                        "- BossList evidence: the same kernel matches a resolved "
                        "`BossList.GeometryID` bbox in both `Vaciado_027` and `Vaciado_031`; "
                        "`BossGeometryList` keeps the physical island geometry separately.",
                        "- This remains a lab rule: it explains the shared base loop, but "
                        "does not yet explain every bridge/order decision in `022`, `028`, "
                        "`029` or `030`.",
                    ]
                )
        else:
            lines.append(
                "- `Vaciado_027` sequence 2 first loop does not match `Vaciado_031` sequence 2."
            )
    else:
        lines.append("- `Vaciado_027` or `Vaciado_031` does not expose the expected second trajectory.")
    lines.append("")
    return "\n".join(lines)


def resolved_boss_ref_xy_contours(adaptation) -> tuple[tuple[str, tuple[tuple[float, float], ...]], ...]:
    if adaptation.pocket_millings:
        return tuple(
            (seed.geometry_id, seed.contour_points)
            for seed in adaptation.pocket_millings[0].boss_route_seeds
        )

    snapshot = adaptation.snapshot
    if not snapshot.features:
        return ()
    feature = snapshot.features[0]
    contours: list[tuple[str, tuple[tuple[float, float], ...]]] = []
    for ref in feature.boss_refs:
        geometry = snapshot.geometry_by_id.get(ref.id)
        contour = _xy_points_from_geometry_profile(geometry.profile) if geometry and geometry.profile else ()
        contours.append((ref.id, contour))
    return tuple(contours)


def generate_rounded_kernel_loop_xy(
    kernel_bbox: tuple[float, float, float, float],
    radius: float,
) -> tuple[tuple[float, float], ...]:
    """Generate the observed 10-point rounded-kernel base loop.

    The kernel bbox order is `(min_x, max_x, min_y, max_y)`. This is lab-only
    evidence for the island/corridor base loop; productive synthesis remains
    blocked until the surrounding bridge rules are known.
    """

    min_x, max_x, min_y, max_y = kernel_bbox
    if max_x <= min_x or max_y <= min_y:
        raise ValueError("kernel bbox must have positive width and height.")
    if radius <= 0.0:
        raise ValueError("radius must be positive.")
    diagonal = radius / math.sqrt(2.0)
    return (
        (min_x - radius, min_y),
        (min_x - radius, max_y),
        (min_x, max_y + radius),
        (max_x, max_y + radius),
        (max_x + diagonal, max_y + diagonal),
        (max_x + radius, max_y),
        (max_x + radius, min_y),
        (max_x, min_y - radius),
        (min_x, min_y - radius),
        (min_x - radius, min_y),
    )


def infer_rounded_kernel_loop_xy(
    loop: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-6,
) -> RoundedKernelLoopRule | None:
    if len(loop) != 10:
        return None
    xy = tuple((float(point[0]), float(point[1])) for point in loop)
    if not _same_xy(xy[0], xy[-1], tolerance=tolerance):
        return None

    min_x = xy[2][0]
    max_x = xy[3][0]
    min_y = xy[0][1]
    max_y = xy[1][1]
    radius_candidates = (
        min_x - xy[0][0],
        min_x - xy[1][0],
        xy[2][1] - max_y,
        xy[3][1] - max_y,
        xy[5][0] - max_x,
        xy[6][0] - max_x,
        min_y - xy[7][1],
        min_y - xy[8][1],
    )
    radius = sum(radius_candidates) / len(radius_candidates)
    if radius <= 0.0 or any(
        not math.isclose(value, radius, abs_tol=tolerance) for value in radius_candidates
    ):
        return None
    if max_x <= min_x or max_y <= min_y:
        return None

    structural_pairs = (
        (xy[0][0], xy[1][0]),
        (xy[2][1], xy[3][1]),
        (xy[5][0], xy[6][0]),
        (xy[7][1], xy[8][1]),
        (xy[2][0], xy[8][0]),
        (xy[3][0], xy[7][0]),
        (xy[0][1], xy[6][1]),
        (xy[1][1], xy[5][1]),
    )
    if any(not math.isclose(left, right, abs_tol=tolerance) for left, right in structural_pairs):
        return None

    generated = generate_rounded_kernel_loop_xy((min_x, max_x, min_y, max_y), radius)
    deltas = [
        math.hypot(actual[0] - expected[0], actual[1] - expected[1])
        for actual, expected in zip(xy, generated)
    ]
    max_delta = max(deltas)
    if max_delta > tolerance:
        return None
    return RoundedKernelLoopRule(
        kernel_bbox=(min_x, max_x, min_y, max_y),
        radius=radius,
        max_delta=max_delta,
    )


def _bossless_rectangular_path(adaptation, spec) -> tuple[tuple[float, float, float], ...]:
    strategy = spec.milling_strategy
    state = adaptation.snapshot.state
    return generate_rectangular_contour_parallel_xyz_path(
        length=state.length,
        width=state.width,
        depth=state.depth,
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


def _common_prefix_length(
    first: Sequence[tuple[float, float, float]],
    second: Sequence[tuple[float, float, float]],
) -> int:
    count = 0
    for left, right in zip(first, second):
        if not _same_point3(left, right):
            break
        count += 1
    return count


def _offset_repeat_note(
    sequence: Sequence[tuple[float, float, float]],
    radial_step: float,
) -> str:
    if len(sequence) < 4 or len(sequence) % 2 != 0 or radial_step <= 0.0:
        return ""
    half = len(sequence) // 2
    first_loop = sequence[:half]
    second_loop = sequence[half:]
    if not first_loop or not second_loop:
        return ""
    center_x = (min(point[0] for point in first_loop) + max(point[0] for point in first_loop)) / 2.0
    center_y = (min(point[1] for point in first_loop) + max(point[1] for point in first_loop)) / 2.0
    distances: list[float] = []
    for base, offset in zip(first_loop, second_loop):
        dx = offset[0] - base[0]
        dy = offset[1] - base[1]
        distance = math.hypot(dx, dy)
        if not math.isclose(distance, radial_step, abs_tol=1e-5):
            return ""
        if ((base[0] - center_x) * dx) + ((base[1] - center_y) * dy) < -1e-6:
            return ""
        distances.append(distance)
    max_delta = max(abs(distance - radial_step) for distance in distances)
    return (
        f"splits into `{half}+{half}` points; the second loop is an outward "
        f"radial offset of `{_num(radial_step)}` mm from the first loop "
        f"(max delta `{_num(max_delta)}`)"
    )


def _boss_reference_note(
    boss_contours: Sequence[Sequence[tuple[float, float]]],
    boss_ref_contours: Sequence[tuple[str, Sequence[tuple[float, float]]]],
) -> str:
    physical_bboxes = tuple(_bbox_tuple(contour) for contour in boss_contours)
    ref_bboxes = tuple(_bbox_tuple(contour) for _ref_id, contour in boss_ref_contours if contour)
    unresolved = tuple(ref_id for ref_id, contour in boss_ref_contours if not contour)
    details: list[str] = []
    if physical_bboxes and ref_bboxes:
        if len(physical_bboxes) == len(ref_bboxes) and all(
            _same_bbox(left, right) for left, right in zip(physical_bboxes, ref_bboxes)
        ):
            details.append("resolved BossList geometry matches BossGeometryList.")
        else:
            details.append(
                "resolved BossList geometry differs from BossGeometryList; treat it as route-seed evidence."
            )
    elif boss_ref_contours:
        details.append("BossList has refs but no resolved geometry profile.")
    else:
        details.append("no BossList refs.")
    if unresolved:
        details.append(f"unresolved refs: `{', '.join(unresolved)}`.")
    return " ".join(details)


def _kernel_relation_to_bosses(
    kernel_bbox: tuple[float, float, float, float],
    boss_contours: Sequence[Sequence[tuple[float, float]]],
) -> str:
    if not boss_contours:
        return "no boss geometry available for relation check."
    boss_bboxes = tuple(_bbox_tuple(boss) for boss in boss_contours)
    kernel_min_x, kernel_max_x, kernel_min_y, kernel_max_y = kernel_bbox
    if len(boss_bboxes) == 1:
        boss_min_x, boss_max_x, boss_min_y, boss_max_y = boss_bboxes[0]
        insets = (
            kernel_min_x - boss_min_x,
            boss_max_x - kernel_max_x,
            kernel_min_y - boss_min_y,
            boss_max_y - kernel_max_y,
        )
        if all(value >= -1e-6 for value in insets):
            return (
                "kernel is inside the single boss bbox with insets "
                f"`{', '.join(_num(value) for value in insets)}` "
                "(left, right, bottom, top)."
            )
        return "kernel is not a simple inset of the single boss bbox."

    if len(boss_bboxes) == 2:
        ordered = tuple(sorted(boss_bboxes, key=lambda bbox: bbox[0]))
        left, right = ordered
        shared_y = math.isclose(left[2], right[2], abs_tol=1e-6) and math.isclose(
            left[3],
            right[3],
            abs_tol=1e-6,
        )
        margins = (kernel_min_x - left[1], right[0] - kernel_max_x)
        if (
            shared_y
            and math.isclose(kernel_min_y, left[2], abs_tol=1e-6)
            and math.isclose(kernel_max_y, left[3], abs_tol=1e-6)
            and all(value >= -1e-6 for value in margins)
        ):
            return (
                "kernel sits in the corridor between the two boss bboxes; "
                f"side margins are `{', '.join(_num(value) for value in margins)}` "
                "and Y span matches the bosses."
            )
        return "kernel is not a simple horizontal corridor between the two boss bboxes."
    return "kernel relation for more than two bosses is not classified yet."


def _same_xy_sequence(
    first: Sequence[tuple[float, float, float]],
    second: Sequence[tuple[float, float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    if len(first) != len(second):
        return False
    return all(
        _same_xy((left[0], left[1]), (right[0], right[1]), tolerance=tolerance)
        for left, right in zip(first, second)
    )


def _same_xy(
    first: tuple[float, float],
    second: tuple[float, float],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return math.isclose(first[0], second[0], abs_tol=tolerance) and math.isclose(
        first[1],
        second[1],
        abs_tol=tolerance,
    )


def _same_point3(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return all(math.isclose(a, b, abs_tol=tolerance) for a, b in zip(first, second))


def _bbox_text(points: Sequence[tuple[float, float]]) -> str:
    return _bbox_tuple_text(_bbox_tuple(points))


def _xy_points_from_geometry_profile(profile) -> tuple[tuple[float, float], ...]:
    if profile.geometry_type != "GeomCompositeCurve" or not profile.primitives:
        return ()
    points = [(primitive.start_point[0], primitive.start_point[1]) for primitive in profile.primitives]
    points.append((profile.primitives[-1].end_point[0], profile.primitives[-1].end_point[1]))
    return tuple(points)


def _bbox_tuple(points: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    if not xs or not ys:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), max(xs), min(ys), max(ys))


def _bbox_tuple_text(bbox: tuple[float, float, float, float]) -> str:
    min_x, max_x, min_y, max_y = bbox
    if math.isclose(min_x, max_x, abs_tol=1e-9) and math.isclose(min_y, max_y, abs_tol=1e-9):
        return "none"
    return f"X {_num(min_x)}..{_num(max_x)}, Y {_num(min_y)}..{_num(max_y)}"


def _same_bbox(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return all(math.isclose(left, right, abs_tol=tolerance) for left, right in zip(first, second))


def _range_text(values: Iterable[float]) -> str:
    values = list(values)
    if not values:
        return ""
    return f"{_num(min(values))}..{_num(max(values))}"


def _z_values(points: Sequence[tuple[float, float, float]]) -> tuple[float, ...]:
    return tuple(sorted({round(point[2], 6) for point in points}))


def _point3_text(point: tuple[float, float, float]) -> str:
    return f"{_num(point[0])},{_num(point[1])},{_num(point[2])}"


def _num(value: float) -> str:
    return f"{float(value):.6f}".rstrip("0").rstrip(".")


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _build_summary(
    root: Path,
    output_dir: Path,
    csv_path: Path,
    sections: Sequence[str],
) -> str:
    return "\n".join(
        [
            "# Vaciado Islands Analysis",
            "",
            f"- Root: `{root}`",
            f"- Output dir: `{output_dir}`",
            f"- CSV: `{csv_path}`",
            "",
            "This report is descriptive. Productive synthesis remains blocked for "
            "`BossGeometryList` until the island offset and bridge rules are derived.",
            "",
            *sections,
        ]
    )


def _parse_cases(value: str) -> tuple[int, ...]:
    cases: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        cases.append(int(item))
    return tuple(cases)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Vaciado samples with islands.")
    parser.add_argument("--root", type=Path, default=EXTERNAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--cases",
        default=",".join(str(case) for case in DEFAULT_CASES),
        help="Comma-separated Vaciado indexes to inspect.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, csv_path, summary_path = analyze_island_samples(
        args.root,
        args.output_dir,
        cases=_parse_cases(args.cases),
    )
    print(f"Analyzed {len(rows)} trajectory rows.")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
