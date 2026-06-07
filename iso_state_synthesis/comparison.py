"""Comparison helpers for explained ISO candidates."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol


class IsoTextCandidate(Protocol):
    """Object that can render normalized ISO text for comparison."""

    def text(self) -> str:
        """Return the candidate ISO text."""


@dataclass(frozen=True)
class IsoLineDifference:
    """One differing normalized line."""

    line_number: int
    expected: Optional[str]
    actual: Optional[str]


@dataclass(frozen=True)
class IsoCandidateComparison:
    """Comparison between Maestro ISO and an explained candidate."""

    equal: bool
    expected_line_count: int
    actual_line_count: int
    differences: tuple[IsoLineDifference, ...]
    diff: str = ""

    @property
    def difference_count(self) -> int:
        return len(self.differences)


def compare_candidate_to_iso(
    expected_iso_path: Path,
    candidate: IsoTextCandidate,
    *,
    include_diff: bool = False,
) -> IsoCandidateComparison:
    """Compare an explained candidate against a Maestro ISO file."""

    expected_text = Path(expected_iso_path).read_text(encoding="utf-8", errors="replace")
    expected = _normalize_iso_lines(expected_text)
    actual = _normalize_iso_lines(candidate.text())
    differences: list[IsoLineDifference] = []
    for index in range(max(len(expected), len(actual))):
        expected_line = expected[index] if index < len(expected) else None
        actual_line = actual[index] if index < len(actual) else None
        if expected_line != actual_line:
            differences.append(
                IsoLineDifference(
                    line_number=index + 1,
                    expected=expected_line,
                    actual=actual_line,
                )
            )
    diff = ""
    if include_diff and differences:
        diff = "\n".join(
            difflib.unified_diff(
                expected,
                actual,
                fromfile=str(expected_iso_path),
                tofile="candidate",
                lineterm="",
            )
        )
    return IsoCandidateComparison(
        equal=not differences,
        expected_line_count=len(expected),
        actual_line_count=len(actual),
        differences=tuple(differences),
        diff=diff,
    )


def _normalize_iso_lines(text: str) -> tuple[str, ...]:
    lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        line = " ".join(line.split())
        if line == "%" or line.startswith("% "):
            line = "%"
        lines.append(line)
    return tuple(lines)
