"""Analyze top-drill ordering across a paired PGMX/ISO corpus.

The tool compares three orders for each paired file:

* raw ``WorkingStep`` order from the PGMX;
* current candidate order from ``iso_state_synthesis.pgmx_source``;
* Maestro order observed in the ISO.

It is intentionally read-only.  The output is a CSV report plus a Markdown
summary that can be used as evidence before changing the top-drill ordering
rule.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso_state_synthesis.pgmx_source import (  # noqa: E402
    _embedded_top_drill_tool_for_feature,
    _ordered_resolved_working_steps,
    _resolved_step_family,
)
from tools.pgmx_snapshot import (  # noqa: E402
    PgmxSnapshot,
    PgmxResolvedWorkingStepSnapshot,
    read_pgmx_snapshot,
)


DEFAULT_PGMX_ROOT = Path(r"S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux")
DEFAULT_ISO_ROOT = Path(r"P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux")
DEFAULT_OUTPUT_DIR = DEFAULT_PGMX_ROOT / "_analysis"
TOP_TOOLS = {f"{number:03d}" for number in range(1, 8)}


@dataclass(frozen=True)
class TopEvent:
    tool: str
    x: float
    y: float
    label: str = ""

    @property
    def key(self) -> str:
        return f"{self.tool}@{_format_coord(self.x)},{_format_coord(self.y)}"

    @property
    def encoded(self) -> str:
        if self.label:
            return f"{self.label}:{self.key}"
        return self.key


def analyze_corpus(pgmx_root: Path, iso_root: Path, output_dir: Path) -> tuple[list[dict[str, str]], Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for pgmx_path in sorted(pgmx_root.rglob("*.pgmx"), key=lambda path: str(path).lower()):
        rel_path = pgmx_path.relative_to(pgmx_root)
        iso_path = iso_root / rel_path.with_suffix(".iso")
        rows.append(_analyze_pair(pgmx_path, iso_path, rel_path))

    csv_path = output_dir / "top_drill_order_corpus_analysis.csv"
    fieldnames = [
        "relative_path",
        "status",
        "top_count_pgmx",
        "top_count_iso",
        "top_tool_key_mode",
        "top_explicit_tool_keys",
        "top_auto_tool_keys",
        "top_blocks_raw",
        "top_blocks_candidate",
        "families_raw",
        "raw_matches_iso",
        "candidate_matches_iso",
        "raw_matches_candidate",
        "multiset_matches_iso",
        "first_raw_iso_diff",
        "first_candidate_iso_diff",
        "raw_order",
        "candidate_order",
        "maestro_order",
        "pgmx_path",
        "iso_path",
        "notes",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_path = output_dir / "top_drill_order_corpus_summary.md"
    summary_path.write_text(_build_summary(rows, pgmx_root, iso_root, csv_path), encoding="utf-8")
    return rows, csv_path, summary_path


def _analyze_pair(pgmx_path: Path, iso_path: Path, rel_path: Path) -> dict[str, str]:
    base = {
        "relative_path": str(rel_path),
        "pgmx_path": str(pgmx_path),
        "iso_path": str(iso_path),
    }
    if not iso_path.exists():
        return _row(base, status="missing_iso", notes="ISO pair not found")

    try:
        snapshot = read_pgmx_snapshot(pgmx_path)
    except Exception as exc:  # pragma: no cover - evidence script
        return _row(base, status="pgmx_error", notes=str(exc))

    raw_steps = tuple(snapshot.resolved_working_steps)
    candidate_steps = _ordered_resolved_working_steps(snapshot)
    raw_families = [_resolved_step_family(step) for step in raw_steps]
    candidate_families = [_resolved_step_family(step) for step in candidate_steps]

    raw_order = _top_events_from_steps(snapshot, raw_steps)
    candidate_order = _top_events_from_steps(snapshot, candidate_steps)
    maestro_order = _top_events_from_iso(iso_path)
    explicit_tool_keys, auto_tool_keys = _top_tool_key_counts(raw_steps)
    raw_keys = [event.key for event in raw_order]
    candidate_keys = [event.key for event in candidate_order]
    maestro_keys = [event.key for event in maestro_order]

    if not raw_order and not maestro_order:
        status = "no_top_drill"
    elif len(raw_order) != len(maestro_order):
        status = "count_mismatch"
    elif Counter(raw_keys) != Counter(maestro_keys):
        status = "multiset_mismatch"
    elif raw_keys == maestro_keys and candidate_keys == maestro_keys:
        status = "raw_and_candidate_match"
    elif raw_keys == maestro_keys:
        status = "raw_matches"
    elif candidate_keys == maestro_keys:
        status = "candidate_matches"
    else:
        status = "neither_matches"

    return _row(
        base,
        status=status,
        top_count_pgmx=str(len(raw_order)),
        top_count_iso=str(len(maestro_order)),
        top_tool_key_mode=_top_tool_key_mode(explicit_tool_keys, auto_tool_keys),
        top_explicit_tool_keys=str(explicit_tool_keys),
        top_auto_tool_keys=str(auto_tool_keys),
        top_blocks_raw=str(_top_block_count(raw_families)),
        top_blocks_candidate=str(_top_block_count(candidate_families)),
        families_raw=_compress_families(raw_families),
        raw_matches_iso=_bool_text(raw_keys == maestro_keys and bool(raw_order or maestro_order)),
        candidate_matches_iso=_bool_text(candidate_keys == maestro_keys and bool(candidate_order or maestro_order)),
        raw_matches_candidate=_bool_text(raw_keys == candidate_keys and bool(raw_order or candidate_order)),
        multiset_matches_iso=_bool_text(Counter(raw_keys) == Counter(maestro_keys) and bool(raw_order or maestro_order)),
        first_raw_iso_diff=_first_difference(raw_keys, maestro_keys),
        first_candidate_iso_diff=_first_difference(candidate_keys, maestro_keys),
        raw_order=_format_order(raw_order),
        candidate_order=_format_order(candidate_order),
        maestro_order=_format_order(maestro_order),
    )


def _row(base: dict[str, str], **values: str) -> dict[str, str]:
    row = {
        "relative_path": base.get("relative_path", ""),
        "status": "",
        "top_count_pgmx": "0",
        "top_count_iso": "0",
        "top_tool_key_mode": "",
        "top_explicit_tool_keys": "0",
        "top_auto_tool_keys": "0",
        "top_blocks_raw": "0",
        "top_blocks_candidate": "0",
        "families_raw": "",
        "raw_matches_iso": "",
        "candidate_matches_iso": "",
        "raw_matches_candidate": "",
        "multiset_matches_iso": "",
        "first_raw_iso_diff": "",
        "first_candidate_iso_diff": "",
        "raw_order": "",
        "candidate_order": "",
        "maestro_order": "",
        "pgmx_path": base.get("pgmx_path", ""),
        "iso_path": base.get("iso_path", ""),
        "notes": "",
    }
    row.update(values)
    return row


def _top_events_from_steps(
    snapshot: PgmxSnapshot,
    steps: Iterable[PgmxResolvedWorkingStepSnapshot],
) -> list[TopEvent]:
    events: list[TopEvent] = []
    for index, step in enumerate(steps, start=1):
        if _resolved_step_family(step) != "top_drill":
            continue
        if step.geometry is None or step.geometry.point is None:
            continue
        tool = _top_tool_for_step(snapshot, step)
        x, y, _ = step.geometry.point
        feature_name = step.feature.name if step.feature is not None else ""
        label = f"{index}:{feature_name or step.step.id}"
        events.append(TopEvent(tool=tool, x=round(float(x), 6), y=round(float(y), 6), label=label))
    return events


def _top_tool_for_step(snapshot: PgmxSnapshot, step: PgmxResolvedWorkingStepSnapshot) -> str:
    operation = step.operation
    if operation is not None and operation.tool_key is not None:
        tool_name = _normalize_tool(operation.tool_key.name)
        if tool_name:
            return tool_name
    if step.feature is not None:
        embedded_tool = _embedded_top_drill_tool_for_feature(snapshot, step.feature)
        if embedded_tool is not None:
            return _normalize_tool(embedded_tool.name or embedded_tool.tool_key)
    return ""


def _top_tool_key_counts(steps: Iterable[PgmxResolvedWorkingStepSnapshot]) -> tuple[int, int]:
    explicit = 0
    auto = 0
    for step in steps:
        if _resolved_step_family(step) != "top_drill":
            continue
        operation = step.operation
        tool_name = ""
        if operation is not None and operation.tool_key is not None:
            tool_name = _normalize_tool(operation.tool_key.name)
        if tool_name:
            explicit += 1
        else:
            auto += 1
    return explicit, auto


def _top_tool_key_mode(explicit: int, auto: int) -> str:
    if explicit and auto:
        return "mixed"
    if explicit:
        return "explicit"
    if auto:
        return "auto"
    return "none"


def _top_events_from_iso(path: Path) -> list[TopEvent]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    order: list[TopEvent] = []
    current_tool = ""
    last_g0_xy: tuple[float, float] | None = None

    for raw_line in lines:
        line = raw_line.strip()
        tool_match = re.fullmatch(r"\?%ETK\[6\]=(\d+)", line)
        if tool_match:
            current_tool = _normalize_tool(tool_match.group(1))
            continue

        if line.startswith("G0 "):
            xy = _extract_xy(line)
            if xy is not None:
                last_g0_xy = xy
            continue

        if line == "?%ETK[7]=3" and last_g0_xy is not None and current_tool in TOP_TOOLS:
            x, y = last_g0_xy
            order.append(TopEvent(tool=current_tool, x=x, y=y, label=str(len(order) + 1)))

    return order


def _extract_xy(line: str) -> tuple[float, float] | None:
    x_match = re.search(r"\bX(-?\d+(?:\.\d+)?)", line)
    y_match = re.search(r"\bY(-?\d+(?:\.\d+)?)", line)
    if not x_match or not y_match:
        return None
    return (round(float(x_match.group(1)), 6), round(float(y_match.group(1)), 6))


def _normalize_tool(tool: str) -> str:
    tool = str(tool).strip()
    if tool.isdigit():
        return f"{int(tool):03d}"
    return tool


def _format_coord(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_order(events: Iterable[TopEvent]) -> str:
    return " -> ".join(event.encoded for event in events)


def _first_difference(left: Sequence[str], right: Sequence[str]) -> str:
    max_len = max(len(left), len(right))
    for index in range(max_len):
        left_value = left[index] if index < len(left) else "<missing>"
        right_value = right[index] if index < len(right) else "<missing>"
        if left_value != right_value:
            return f"{index + 1}: {left_value} != {right_value}"
    return ""


def _top_block_count(families: Sequence[str]) -> int:
    count = 0
    previous = ""
    for family in families:
        if family == "top_drill" and previous != "top_drill":
            count += 1
        previous = family
    return count


def _compress_families(families: Sequence[str]) -> str:
    compressed: list[str] = []
    for family in families:
        if not compressed or compressed[-1] != family:
            compressed.append(family)
    return " -> ".join(compressed)


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def _build_summary(rows: Sequence[dict[str, str]], pgmx_root: Path, iso_root: Path, csv_path: Path) -> str:
    status_counts = Counter(row["status"] for row in rows)
    top_rows = [row for row in rows if int(row["top_count_pgmx"] or "0") > 0 or int(row["top_count_iso"] or "0") > 0]
    complete_rows = [
        row
        for row in top_rows
        if row["status"] not in {"count_mismatch", "multiset_mismatch"}
    ]
    raw_matches = [row for row in complete_rows if row["raw_matches_iso"] == "yes"]
    candidate_matches = [row for row in complete_rows if row["candidate_matches_iso"] == "yes"]
    neither = [row for row in complete_rows if row["status"] == "neither_matches"]
    count_or_multiset = [
        row
        for row in top_rows
        if row["status"] in {"count_mismatch", "multiset_mismatch"}
    ]
    tool_key_modes = Counter(row["top_tool_key_mode"] for row in top_rows)

    lines = [
        "# Top Drill Order Corpus Analysis",
        "",
        f"- PGMX root: `{pgmx_root}`",
        f"- ISO root: `{iso_root}`",
        f"- CSV: `{csv_path}`",
        f"- Paired rows: `{len(rows)}`",
        f"- Rows with top drill evidence: `{len(top_rows)}`",
        f"- Rows with complete top-order comparison: `{len(complete_rows)}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")

    lines.extend(["", "## Tool Key Modes", ""])
    for mode, count in sorted(tool_key_modes.items()):
        lines.append(f"- `{mode}`: `{count}`")

    lines.extend(
        [
            "",
            "## Match Counts",
            "",
            f"- Raw PGMX order matches Maestro ISO: `{len(raw_matches)}/{len(complete_rows)}`",
            f"- Current candidate order matches Maestro ISO: `{len(candidate_matches)}/{len(complete_rows)}`",
            f"- Neither raw nor candidate matches: `{len(neither)}`",
            f"- Count/multiset extraction mismatches: `{len(count_or_multiset)}`",
            "",
            "## Neither Matches",
            "",
        ]
    )
    if neither:
        for row in neither[:30]:
            lines.append(f"- `{row['relative_path']}`: {row['first_candidate_iso_diff'] or row['first_raw_iso_diff']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Count Or Multiset Mismatches", ""])
    if count_or_multiset:
        for row in count_or_multiset[:30]:
            lines.append(
                f"- `{row['relative_path']}`: status `{row['status']}`, "
                f"PGMX `{row['top_count_pgmx']}`, ISO `{row['top_count_iso']}`"
            )
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze top-drill ordering in a paired PGMX/ISO corpus.")
    parser.add_argument("--pgmx-root", type=Path, default=DEFAULT_PGMX_ROOT)
    parser.add_argument("--iso-root", type=Path, default=DEFAULT_ISO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, csv_path, summary_path = analyze_corpus(args.pgmx_root, args.iso_root, args.output_dir)
    status_counts = Counter(row["status"] for row in rows)
    print(f"Analyzed {len(rows)} PGMX/ISO rows.")
    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
