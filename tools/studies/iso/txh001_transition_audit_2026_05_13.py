"""Audit Cazaux candidates that exercise the T-XH-001 transition.

The report is intended to be run before and after a focused T-XH-001 change.
It lists exact candidates, T-XH-001 residuals, and optional movement against a
baseline CSV.
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

from iso_state_synthesis.differential import evaluate_pgmx_state_plan  # noqa: E402
from iso_state_synthesis.emitter import (  # noqa: E402
    ExplainedIsoLine,
    IsoCandidateEmissionError,
    compare_candidate_to_iso,
    emit_candidate_from_evaluation,
    _normalize_iso_lines,
    _work_stage_groups,
)
from iso_state_synthesis.model import StageDifferential  # noqa: E402


DEFAULT_PGMX_ROOT = Path(r"S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux")
DEFAULT_ISO_ROOT = Path(r"P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux")
DEFAULT_OUTPUT_DIR = DEFAULT_PGMX_ROOT / "_analysis"
TARGET_TRANSITION = "T-XH-001"


@dataclass(frozen=True)
class NormalizedLineMeta:
    line: str
    explained: ExplainedIsoLine


def audit_corpus(
    pgmx_root: Path,
    iso_root: Path,
    output_dir: Path,
    *,
    label: str,
    baseline_csv: Path | None = None,
) -> tuple[list[dict[str, str]], Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = _read_baseline(baseline_csv) if baseline_csv else {}
    rows: list[dict[str, str]] = []

    for pgmx_path in sorted(pgmx_root.rglob("*.pgmx"), key=lambda path: str(path).lower()):
        if "_analysis" in pgmx_path.parts:
            continue
        rel_path = pgmx_path.relative_to(pgmx_root)
        iso_path = iso_root / rel_path.with_suffix(".iso")
        row = _audit_pair(pgmx_path, iso_path, rel_path)
        if row["has_txh001"] == "yes":
            _add_baseline_comparison(row, baseline.get(row["relative_path"]))
            rows.append(row)

    csv_path = output_dir / f"txh001_transition_audit_{label}.csv"
    fieldnames = [
        "relative_path",
        "has_txh001",
        "txh001_result",
        "status",
        "candidate_front",
        "first_diff_line",
        "expected_line",
        "actual_line",
        "first_diff_kind",
        "txh001_top_count",
        "txh001_side_count",
        "txh001_slot_count",
        "txh001_targets",
        "previous_router_families",
        "work_sequence",
        "transition_sequence",
        "expected_line_count",
        "actual_line_count",
        "difference_count",
        "significant_difference_count",
        "before_status",
        "before_candidate_front",
        "before_txh001_result",
        "change_vs_baseline",
        "pgmx_path",
        "iso_path",
        "notes",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_path = output_dir / f"txh001_transition_audit_{label}.md"
    summary_path.write_text(
        _build_summary(rows, pgmx_root, iso_root, csv_path, label, baseline_csv),
        encoding="utf-8",
    )
    return rows, csv_path, summary_path


def _audit_pair(pgmx_path: Path, iso_path: Path, rel_path: Path) -> dict[str, str]:
    base = {
        "relative_path": str(rel_path),
        "pgmx_path": str(pgmx_path),
        "iso_path": str(iso_path),
        "has_txh001": "no",
    }
    if not iso_path.exists():
        return _row(base, status="missing_iso", notes="ISO pair not found")

    try:
        evaluation = evaluate_pgmx_state_plan(pgmx_path)
        program = emit_candidate_from_evaluation(evaluation)
    except IsoCandidateEmissionError as exc:
        return _row(base, status="unsupported_candidate", notes=str(exc))
    except Exception as exc:  # pragma: no cover - evidence script
        return _row(base, status="error", notes=str(exc))

    groups = _safe_work_groups(tuple(sorted(evaluation.differentials, key=lambda item: item.order_index)))
    txh001_groups = tuple(group for group in groups if group.incoming_transition_id == TARGET_TRANSITION)
    if not txh001_groups:
        return _row(base)

    comparison = compare_candidate_to_iso(iso_path, program)
    line_meta = _normalized_line_meta(program.lines)
    significant_differences = tuple(
        difference
        for difference in comparison.differences
        if not _is_minor_header_difference(difference.expected, difference.actual)
    )
    first = significant_differences[0] if significant_differences else None
    candidate_meta = _meta_at(line_meta, first.line_number - 1) if first else None
    candidate_front = _candidate_front(candidate_meta)
    if comparison.equal:
        status = "exact"
    elif not significant_differences:
        status = "header_only"
    else:
        status = "operational_diff"

    expected_line = first.expected if first else ""
    actual_line = first.actual if first else ""
    txh001_result = _txh001_result(status, candidate_front)

    return _row(
        base,
        has_txh001="yes",
        txh001_result=txh001_result,
        status=status,
        candidate_front=candidate_front,
        first_diff_line=str(first.line_number if first else ""),
        expected_line=expected_line or "",
        actual_line=actual_line or "",
        first_diff_kind=_join_nonempty((_line_kind(expected_line), _line_kind(actual_line)), " / "),
        txh001_top_count=str(sum(1 for group in txh001_groups if group.family == "top_drill")),
        txh001_side_count=str(sum(1 for group in txh001_groups if group.family == "side_drill")),
        txh001_slot_count=str(sum(1 for group in txh001_groups if group.family == "slot_milling")),
        txh001_targets=" -> ".join(group.family for group in txh001_groups),
        previous_router_families=_previous_router_families(groups),
        work_sequence=_work_sequence(groups),
        transition_sequence=_transition_sequence(groups),
        expected_line_count=str(comparison.expected_line_count),
        actual_line_count=str(comparison.actual_line_count),
        difference_count=str(comparison.difference_count),
        significant_difference_count=str(len(significant_differences)),
    )


def _safe_work_groups(differentials: tuple[StageDifferential, ...]):
    try:
        return _work_stage_groups(list(differentials))
    except Exception:
        return ()


def _normalized_line_meta(lines: Iterable[ExplainedIsoLine]) -> list[NormalizedLineMeta]:
    result: list[NormalizedLineMeta] = []
    for explained in lines:
        for line in _normalize_iso_lines(explained.line):
            result.append(NormalizedLineMeta(line=line, explained=explained))
    return result


def _meta_at(lines: Sequence[NormalizedLineMeta], index: int) -> NormalizedLineMeta | None:
    if 0 <= index < len(lines):
        return lines[index]
    return None


def _candidate_front(meta: NormalizedLineMeta | None) -> str:
    if meta is None:
        return "missing_candidate_line"
    if meta.explained.transition_id:
        return f"transition:{meta.explained.transition_id}"
    if meta.explained.block_id:
        return f"block:{meta.explained.block_id}"
    return f"stage:{meta.explained.stage_key}"


def _txh001_result(status: str, candidate_front: str) -> str:
    if status == "exact":
        return "exact"
    if status == "header_only":
        return "header_only"
    if candidate_front == f"transition:{TARGET_TRANSITION}":
        return "txh001_diff"
    return "other_diff"


def _previous_router_families(groups) -> str:
    families: list[str] = []
    previous_family = ""
    for group in groups:
        if group.incoming_transition_id == TARGET_TRANSITION:
            families.append(previous_family)
        previous_family = group.family
    return " -> ".join(families)


def _work_sequence(groups) -> str:
    return " -> ".join(group.family for group in groups)


def _transition_sequence(groups) -> str:
    parts: list[str] = []
    for group in groups:
        if group.incoming_transition_id:
            parts.append(f"{group.incoming_transition_id}->{group.family}")
        else:
            parts.append(group.family)
    return " -> ".join(parts)


def _is_minor_header_difference(expected: str | None, actual: str | None) -> bool:
    if not expected or not actual:
        return False
    expected_match = re.fullmatch(r"(%Or\[0\]\.of[XYZ]=)([-+]?[0-9]+(?:\.[0-9]+)?)", expected)
    actual_match = re.fullmatch(r"(%Or\[0\]\.of[XYZ]=)([-+]?[0-9]+(?:\.[0-9]+)?)", actual)
    if expected_match is None or actual_match is None:
        return False
    if expected_match.group(1) != actual_match.group(1):
        return False
    return abs(float(expected_match.group(2)) - float(actual_match.group(2))) <= 0.05


def _line_kind(line: str | None) -> str:
    if not line:
        return "blank"
    if line.startswith("?%ETK["):
        end = line.find("]")
        return f"ETK[{line[6:end]}]" if end > 0 else "ETK"
    if line.startswith("?%EDK["):
        return "EDK"
    if line.startswith("%Or["):
        return "Or"
    if line.startswith("SHF["):
        return "SHF"
    if line.startswith("VL"):
        return "VL"
    return line.split(maxsplit=1)[0].split("=", 1)[0]


def _join_nonempty(values: Iterable[str], separator: str) -> str:
    return separator.join(value for value in values if value)


def _row(base: dict[str, str], **updates: str) -> dict[str, str]:
    row = {
        "relative_path": "",
        "txh001_result": "",
        "status": "",
        "candidate_front": "",
        "first_diff_line": "",
        "expected_line": "",
        "actual_line": "",
        "first_diff_kind": "",
        "txh001_top_count": "",
        "txh001_side_count": "",
        "txh001_slot_count": "",
        "txh001_targets": "",
        "previous_router_families": "",
        "work_sequence": "",
        "transition_sequence": "",
        "expected_line_count": "",
        "actual_line_count": "",
        "difference_count": "",
        "significant_difference_count": "",
        "before_status": "",
        "before_candidate_front": "",
        "before_txh001_result": "",
        "change_vs_baseline": "",
        "pgmx_path": "",
        "iso_path": "",
        "notes": "",
        "has_txh001": "",
    }
    row.update(base)
    row.update(updates)
    return row


def _read_baseline(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8") as baseline_file:
        return {
            row["relative_path"]: row
            for row in csv.DictReader(baseline_file)
        }


def _add_baseline_comparison(row: dict[str, str], baseline: dict[str, str] | None) -> None:
    if baseline is None:
        row["change_vs_baseline"] = "no_baseline"
        return
    row["before_status"] = baseline.get("status", "")
    row["before_candidate_front"] = baseline.get("candidate_front", "")
    row["before_txh001_result"] = baseline.get("txh001_result", "")
    before_result = row["before_txh001_result"]
    after_result = row["txh001_result"]
    if before_result == "exact" and after_result == "exact":
        row["change_vs_baseline"] = "still_exact"
    elif before_result == "header_only" and after_result == "header_only":
        row["change_vs_baseline"] = "still_header_only"
    elif before_result == after_result and row["before_candidate_front"] == row["candidate_front"]:
        row["change_vs_baseline"] = "unchanged_same_front"
    elif before_result in {"txh001_diff", "other_diff"} and after_result in {"exact", "header_only"}:
        row["change_vs_baseline"] = "improved_to_clean"
    elif before_result == "txh001_diff" and after_result == "other_diff":
        row["change_vs_baseline"] = "txh001_cleared_next_front"
    elif before_result in {"exact", "header_only"} and after_result in {"txh001_diff", "other_diff"}:
        row["change_vs_baseline"] = "worsened"
    elif before_result == "other_diff" and after_result == "txh001_diff":
        row["change_vs_baseline"] = "worsened_to_txh001"
    else:
        row["change_vs_baseline"] = "changed"


def _build_summary(
    rows: list[dict[str, str]],
    pgmx_root: Path,
    iso_root: Path,
    csv_path: Path,
    label: str,
    baseline_csv: Path | None,
) -> str:
    status_counts = Counter(row["status"] for row in rows)
    result_counts = Counter(row["txh001_result"] for row in rows)
    target_counts = Counter(row["txh001_targets"] for row in rows)
    change_counts = Counter(row["change_vs_baseline"] for row in rows)
    txh001_diffs = [row for row in rows if row["txh001_result"] == "txh001_diff"]
    exacts = [row for row in rows if row["txh001_result"] == "exact"]

    lines = [
        f"# T-XH-001 Transition Audit - {label}",
        "",
        f"- PGMX root: `{pgmx_root}`",
        f"- ISO root: `{iso_root}`",
        f"- CSV: `{csv_path}`",
        f"- Baseline CSV: `{baseline_csv}`" if baseline_csv else "- Baseline CSV: none",
        f"- Rows with `{TARGET_TRANSITION}`: `{len(rows)}`",
        "",
        "## Result Counts",
        "",
    ]
    for key, count in sorted(result_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Status Counts", ""])
    for key, count in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Target Sequences", ""])
    for key, count in target_counts.most_common():
        lines.append(f"- `{key}`: `{count}`")
    if baseline_csv:
        lines.extend(["", "## Change Vs Baseline", ""])
        for key, count in sorted(change_counts.items()):
            lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Exact Candidates", ""])
    for row in exacts:
        lines.append(f"- `{row['relative_path']}`")
    lines.extend(["", "## T-XH-001 Differences", ""])
    if not txh001_diffs:
        lines.append("- none")
    for row in txh001_diffs:
        lines.append(
            "- "
            f"`{row['relative_path']}` line `{row['first_diff_line']}`: "
            f"Maestro `{row['expected_line']}` / candidato `{row['actual_line']}`; "
            f"targets `{row['txh001_targets']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pgmx-root", type=Path, default=DEFAULT_PGMX_ROOT)
    parser.add_argument("--iso-root", type=Path, default=DEFAULT_ISO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--label", default="before")
    parser.add_argument("--baseline-csv", type=Path)
    args = parser.parse_args()

    rows, csv_path, summary_path = audit_corpus(
        args.pgmx_root,
        args.iso_root,
        args.output_dir,
        label=args.label,
        baseline_csv=args.baseline_csv,
    )
    counts = Counter(row["txh001_result"] for row in rows)
    print(f"Audited {len(rows)} rows with {TARGET_TRANSITION}.")
    for key, count in sorted(counts.items()):
        print(f"{key}: {count}")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
