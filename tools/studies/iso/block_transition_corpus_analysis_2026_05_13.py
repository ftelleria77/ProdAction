"""Classify candidate ISO residuals by block and transition sequence.

The report is read-only evidence for deciding the next state-synthesis change.
It pairs PGMX files with Maestro ISO files, emits the current candidate, and
uses the candidate line explanations to locate the first difference in a
documented block or transition.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso_state_synthesis.differential import evaluate_pgmx_state_plan  # noqa: E402
from iso_state_synthesis.emitter import (  # noqa: E402
    IsoCandidateEmissionError,
    ExplainedIsoLine,
    compare_candidate_to_iso,
    emit_candidate_from_evaluation,
    _normalize_iso_lines,
    _work_stage_groups,
)
from iso_state_synthesis.model import StageDifferential  # noqa: E402


DEFAULT_PGMX_ROOT = Path(r"S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux")
DEFAULT_ISO_ROOT = Path(r"P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux")
DEFAULT_OUTPUT_DIR = DEFAULT_PGMX_ROOT / "_analysis"
COMMON_STAGE_KEYS = {"program_header", "machine_preamble", "program_close"}


@dataclass(frozen=True)
class NormalizedLineMeta:
    line: str
    explained: ExplainedIsoLine


def analyze_corpus(pgmx_root: Path, iso_root: Path, output_dir: Path) -> tuple[list[dict[str, str]], Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for pgmx_path in sorted(pgmx_root.rglob("*.pgmx"), key=lambda path: str(path).lower()):
        if "_analysis" in pgmx_path.parts:
            continue
        rel_path = pgmx_path.relative_to(pgmx_root)
        iso_path = iso_root / rel_path.with_suffix(".iso")
        rows.append(_analyze_pair(pgmx_path, iso_path, rel_path))

    csv_path = output_dir / "block_transition_corpus_analysis.csv"
    fieldnames = [
        "relative_path",
        "status",
        "expected_line_count",
        "actual_line_count",
        "difference_count",
        "significant_difference_count",
        "first_diff_line",
        "expected_line",
        "actual_line",
        "expected_kind",
        "actual_kind",
        "first_diff_kind",
        "candidate_stage_key",
        "candidate_family",
        "candidate_block_id",
        "candidate_transition_id",
        "candidate_rule_status",
        "candidate_front",
        "previous_stage_key",
        "previous_block_id",
        "previous_transition_id",
        "next_stage_key",
        "next_block_id",
        "next_transition_id",
        "work_sequence",
        "transition_sequence",
        "block_sequence",
        "work_count",
        "transition_count",
        "pgmx_path",
        "iso_path",
        "notes",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_path = output_dir / "block_transition_corpus_summary.md"
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
        evaluation = evaluate_pgmx_state_plan(pgmx_path)
        program = emit_candidate_from_evaluation(evaluation)
    except IsoCandidateEmissionError as exc:
        return _row(base, status="unsupported_candidate", notes=str(exc))
    except Exception as exc:  # pragma: no cover - evidence script
        return _row(base, status="error", notes=str(exc))

    comparison = compare_candidate_to_iso(iso_path, program)
    groups = _safe_work_groups(tuple(sorted(evaluation.differentials, key=lambda item: item.order_index)))
    line_meta = _normalized_line_meta(program.lines)
    significant_differences = tuple(
        difference
        for difference in comparison.differences
        if not _is_minor_header_difference(difference.expected, difference.actual)
    )
    first = significant_differences[0] if significant_differences else None
    candidate_meta = _meta_at(line_meta, first.line_number - 1) if first else None
    previous_meta = _meta_at(line_meta, first.line_number - 2) if first else None
    next_meta = _meta_at(line_meta, first.line_number) if first else None
    expected_line = first.expected if first else ""
    actual_line = first.actual if first else ""
    expected_kind = _line_kind(expected_line)
    actual_kind = _line_kind(actual_line)
    if comparison.equal:
        status = "exact"
    elif not significant_differences:
        status = "header_only"
    else:
        status = "operational_diff"

    return _row(
        base,
        status=status,
        expected_line_count=str(comparison.expected_line_count),
        actual_line_count=str(comparison.actual_line_count),
        difference_count=str(comparison.difference_count),
        significant_difference_count=str(len(significant_differences)),
        first_diff_line=str(first.line_number if first else ""),
        expected_line=expected_line or "",
        actual_line=actual_line or "",
        expected_kind=expected_kind,
        actual_kind=actual_kind,
        first_diff_kind=_join_nonempty((expected_kind, actual_kind), " / "),
        candidate_stage_key=_explained_attr(candidate_meta, "stage_key"),
        candidate_family=_family_for_stage(evaluation.differentials, _explained_attr(candidate_meta, "stage_key")),
        candidate_block_id=_explained_attr(candidate_meta, "block_id"),
        candidate_transition_id=_explained_attr(candidate_meta, "transition_id"),
        candidate_rule_status=_explained_attr(candidate_meta, "rule_status"),
        candidate_front=_candidate_front(candidate_meta),
        previous_stage_key=_explained_attr(previous_meta, "stage_key"),
        previous_block_id=_explained_attr(previous_meta, "block_id"),
        previous_transition_id=_explained_attr(previous_meta, "transition_id"),
        next_stage_key=_explained_attr(next_meta, "stage_key"),
        next_block_id=_explained_attr(next_meta, "block_id"),
        next_transition_id=_explained_attr(next_meta, "transition_id"),
        work_sequence=_work_sequence(groups),
        transition_sequence=_transition_sequence(groups),
        block_sequence=_block_sequence(program.lines),
        work_count=str(len(groups)),
        transition_count=str(len([group for group in groups if group.incoming_transition_id])),
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


def _explained_attr(meta: NormalizedLineMeta | None, attr: str) -> str:
    if meta is None:
        return ""
    value = getattr(meta.explained, attr)
    return "" if value is None else str(value)


def _candidate_front(meta: NormalizedLineMeta | None) -> str:
    if meta is None:
        return "missing_candidate_line"
    transition_id = meta.explained.transition_id
    if transition_id:
        return f"transition:{transition_id}"
    block_id = meta.explained.block_id
    if block_id:
        return f"block:{block_id}"
    return f"stage:{meta.explained.stage_key}"


def _family_for_stage(differentials: Sequence[StageDifferential], stage_key: str) -> str:
    if not stage_key:
        return ""
    for differential in differentials:
        if differential.stage_key == stage_key:
            return differential.family
    return ""


def _work_sequence(groups: Sequence[object]) -> str:
    return " -> ".join(group.family for group in groups)


def _transition_sequence(groups: Sequence[object]) -> str:
    values: list[str] = []
    for group in groups:
        transition_id = group.incoming_transition_id
        if transition_id:
            values.append(f"{transition_id}->{group.family}")
        else:
            values.append(group.family)
    return " -> ".join(values)


def _block_sequence(lines: Iterable[ExplainedIsoLine]) -> str:
    values: list[str] = []
    for line in lines:
        marker = line.transition_id or line.block_id or line.stage_key
        if not marker:
            continue
        if not values or values[-1] != marker:
            values.append(marker)
    return " -> ".join(values)


def _line_kind(line: str | None) -> str:
    if line is None:
        return "missing"
    text = line.strip()
    if not text:
        return "blank"
    etk_match = re.fullmatch(r"\?%ETK\[(\d+)\]=.*", text)
    if etk_match:
        return f"ETK[{etk_match.group(1)}]"
    edk_match = re.fullmatch(r"\?%EDK\[(\d+)\]=.*", text)
    if edk_match:
        return f"EDK[{edk_match.group(1)}]"
    if text.startswith("SHF["):
        return "SHF"
    or_match = re.fullmatch(r"%Or\[(\d+)\]\.(\w+)=.*", text)
    if or_match:
        return f"%Or[{or_match.group(1)}].{or_match.group(2)}"
    if text.startswith("G0 G53"):
        return "G0_G53"
    if text.startswith("G0 "):
        return "G0"
    if text.startswith("G1 "):
        return "G1"
    if text in {"G17", "G40", "G41", "G42", "G61", "G64"}:
        return text
    if text.startswith("MLV="):
        return "MLV"
    if text in {"D0", "M5", "M06", "SYN"}:
        return text
    if re.fullmatch(r"S\d+(?:\.\d+)?M3", text):
        return "S_M3"
    if re.fullmatch(r"T\d+", text):
        return "T"
    if text.startswith(("SVL", "SVR", "VL6", "VL7")):
        return "router_offset"
    if text == "%":
        return "program_marker"
    return text.split()[0]


def _is_minor_header_difference(expected: str | None, actual: str | None) -> bool:
    if expected is None or actual is None:
        return False
    expected_match = re.fullmatch(r"(%Or\[\d+\]\.\w+)=(-?\d+(?:\.\d+)?)", expected.strip())
    actual_match = re.fullmatch(r"(%Or\[\d+\]\.\w+)=(-?\d+(?:\.\d+)?)", actual.strip())
    if not expected_match or not actual_match:
        return False
    if expected_match.group(1) != actual_match.group(1):
        return False
    return abs(float(expected_match.group(2)) - float(actual_match.group(2))) <= 0.05


def _join_nonempty(values: Iterable[str], separator: str) -> str:
    return separator.join(value for value in values if value)


def _row(base: dict[str, str], **values: str) -> dict[str, str]:
    row = {
        "relative_path": base.get("relative_path", ""),
        "status": "",
        "expected_line_count": "0",
        "actual_line_count": "0",
        "difference_count": "0",
        "significant_difference_count": "0",
        "first_diff_line": "",
        "expected_line": "",
        "actual_line": "",
        "expected_kind": "",
        "actual_kind": "",
        "first_diff_kind": "",
        "candidate_stage_key": "",
        "candidate_family": "",
        "candidate_block_id": "",
        "candidate_transition_id": "",
        "candidate_rule_status": "",
        "candidate_front": "",
        "previous_stage_key": "",
        "previous_block_id": "",
        "previous_transition_id": "",
        "next_stage_key": "",
        "next_block_id": "",
        "next_transition_id": "",
        "work_sequence": "",
        "transition_sequence": "",
        "block_sequence": "",
        "work_count": "0",
        "transition_count": "0",
        "pgmx_path": base.get("pgmx_path", ""),
        "iso_path": base.get("iso_path", ""),
        "notes": "",
    }
    row.update(values)
    return row


def _build_summary(rows: Sequence[dict[str, str]], pgmx_root: Path, iso_root: Path, csv_path: Path) -> str:
    status_counts = Counter(row["status"] for row in rows)
    operational = [row for row in rows if row["status"] == "operational_diff"]
    header_only = [row for row in rows if row["status"] == "header_only"]
    front_counts = Counter(row["candidate_front"] for row in operational)
    kind_counts = Counter(row["first_diff_kind"] for row in operational)
    transition_sequence_counts = Counter(row["transition_sequence"] for row in operational)
    work_sequence_counts = Counter(row["work_sequence"] for row in operational)
    block_usage_counts, block_example_counts = _block_usage_counts(rows)

    lines = [
        "# Block And Transition Corpus Analysis",
        "",
        f"- PGMX root: `{pgmx_root}`",
        f"- ISO root: `{iso_root}`",
        f"- CSV: `{csv_path}`",
        f"- Paired rows: `{len(rows)}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")

    lines.extend(["", "## Header Only", ""])
    if header_only:
        lines.append(f"- Rows with only minor `%Or` header deltas: `{len(header_only)}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Block Usage Counts", ""])
    if block_usage_counts:
        lines.append("| block | occurrences | rows |")
        lines.append("| --- | ---: | ---: |")
        for block in sorted(block_usage_counts):
            lines.append(
                f"| `{block}` | `{block_usage_counts[block]}` | `{block_example_counts[block]}` |"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## First Difference Fronts", ""])
    for front, count in front_counts.most_common():
        lines.append(f"- `{front}`: `{count}`")

    lines.extend(["", "## First Difference Line Kinds", ""])
    for kind, count in kind_counts.most_common(20):
        lines.append(f"- `{kind}`: `{count}`")

    lines.extend(["", "## Residual Work Sequences", ""])
    for sequence, count in work_sequence_counts.most_common(20):
        lines.append(f"- `{sequence}`: `{count}`")

    lines.extend(["", "## Residual Transition Sequences", ""])
    for sequence, count in transition_sequence_counts.most_common(20):
        lines.append(f"- `{sequence}`: `{count}`")

    lines.extend(["", "## Examples By Front", ""])
    by_front: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in operational:
        by_front[row["candidate_front"]].append(row)
    for front, front_rows in sorted(by_front.items()):
        lines.extend(["", f"### `{front}`", ""])
        for row in front_rows[:8]:
            lines.append(
                f"- `{row['relative_path']}` line `{row['first_diff_line']}`: "
                f"Maestro `{row['expected_line']}` / candidato `{row['actual_line']}`"
            )

    lines.extend(["", "## Strategy", ""])
    lines.extend(_strategy_lines(operational, front_counts, kind_counts, header_only))
    return "\n".join(lines) + "\n"


def _block_usage_counts(rows: Sequence[dict[str, str]]) -> tuple[Counter[str], dict[str, int]]:
    occurrence_counts: Counter[str] = Counter()
    row_indexes: dict[str, set[int]] = defaultdict(set)
    for row_index, row in enumerate(rows):
        for token in (part.strip() for part in row["block_sequence"].split("->")):
            if not token.startswith("B-"):
                continue
            occurrence_counts[token] += 1
            row_indexes[token].add(row_index)
    return occurrence_counts, {block: len(indexes) for block, indexes in row_indexes.items()}


def _strategy_lines(
    operational: Sequence[dict[str, str]],
    front_counts: Counter[str],
    kind_counts: Counter[str],
    header_only: Sequence[dict[str, str]],
) -> list[str]:
    lines: list[str] = []
    if front_counts:
        front, count = front_counts.most_common(1)[0]
        lines.append(
            f"- Priorizar `{front}`: concentra `{count}/{len(operational)}` residuales operativos por primera diferencia."
        )
    if header_only:
        lines.append(
            f"- Tratar `{len(header_only)}` casos `header_only` como frente de formato/precision de cabecera, separado de la estrategia de bloques."
        )
    if "G1 / G1" in kind_counts or "G0 / G0" in kind_counts:
        lines.append(
            "- Separar diferencias geometricas de secuencia: `G0/G1` como primera diferencia suele indicar orden, coordenada o modalidad de traza."
        )
    if any(front.startswith("transition:") for front in front_counts):
        lines.append(
            "- Para frentes `transition:*`, crear mini tandas dirigidas por transicion antes de tocar bloques reutilizables."
        )
    if any(front.startswith("block:") for front in front_counts):
        lines.append(
            "- Para frentes `block:*`, comparar la traza interna del bloque y registrar una regla de bloque antes de mover transiciones."
        )
    if not lines:
        lines.append("- No hay residuales clasificados para priorizar.")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze residual ISO differences by block and transition.")
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
