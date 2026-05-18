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

from tools.pgmx_adapters import adapt_pgmx_path
from tools.pgmx_vaciado.contour_parallel import (
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
        f"- Boss bboxes: `{'; '.join(boss_bboxes) if boss_bboxes else 'none'}`",
        f"- Boss refs: `{'; '.join(boss_refs) if boss_refs else 'none'}`",
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
        else:
            lines.append(
                "- `Vaciado_027` sequence 2 first loop does not match `Vaciado_031` sequence 2."
            )
    else:
        lines.append("- `Vaciado_027` or `Vaciado_031` does not expose the expected second trajectory.")
    lines.append("")
    return "\n".join(lines)


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


def _same_xy_sequence(
    first: Sequence[tuple[float, float, float]],
    second: Sequence[tuple[float, float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    if len(first) != len(second):
        return False
    return all(
        math.isclose(left[0], right[0], abs_tol=tolerance)
        and math.isclose(left[1], right[1], abs_tol=tolerance)
        for left, right in zip(first, second)
    )


def _same_point3(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return all(math.isclose(a, b, abs_tol=tolerance) for a, b in zip(first, second))


def _bbox_text(points: Sequence[tuple[float, float]]) -> str:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    if not xs or not ys:
        return "none"
    return f"X {_num(min(xs))}..{_num(max(xs))}, Y {_num(min(ys))}..{_num(max(ys))}"


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
