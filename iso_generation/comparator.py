"""Comparison helpers for Maestro ISO references and generated ISO text."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class IsoComparisonOptions:
    """Line normalization knobs for ISO comparison."""

    normalize_program_name: bool = True
    strip_blank_lines: bool = True
    normalize_whitespace: bool = True
    ignore_case: bool = False


@dataclass(frozen=True)
class IsoDifference:
    """One differing normalized line."""

    line_number: int
    expected: Optional[str]
    actual: Optional[str]


@dataclass(frozen=True)
class IsoComparisonResult:
    """Result of comparing two normalized ISO texts."""

    equal: bool
    expected_line_count: int
    actual_line_count: int
    differences: tuple[IsoDifference, ...]

    @property
    def difference_count(self) -> int:
        return len(self.differences)


def normalize_iso_lines(
    text: str,
    options: IsoComparisonOptions = IsoComparisonOptions(),
) -> tuple[str, ...]:
    """Normalize ISO text into comparable lines."""

    lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if options.strip_blank_lines and not line:
            continue
        if options.normalize_whitespace:
            line = " ".join(line.split())
        if options.normalize_program_name and line.startswith("%"):
            line = "%"
        if options.ignore_case:
            line = line.upper()
        lines.append(line)
    return tuple(lines)


def compare_iso_texts(
    expected_text: str,
    actual_text: str,
    options: IsoComparisonOptions = IsoComparisonOptions(),
) -> IsoComparisonResult:
    """Compare two ISO texts after normalization."""

    expected = normalize_iso_lines(expected_text, options)
    actual = normalize_iso_lines(actual_text, options)
    differences: list[IsoDifference] = []
    max_len = max(len(expected), len(actual))
    for index in range(max_len):
        expected_line = expected[index] if index < len(expected) else None
        actual_line = actual[index] if index < len(actual) else None
        if expected_line != actual_line:
            differences.append(
                IsoDifference(
                    line_number=index + 1,
                    expected=expected_line,
                    actual=actual_line,
                )
            )
    return IsoComparisonResult(
        equal=not differences,
        expected_line_count=len(expected),
        actual_line_count=len(actual),
        differences=tuple(differences),
    )


def compare_iso_files(
    expected_path: Path,
    actual_path: Path,
    options: IsoComparisonOptions = IsoComparisonOptions(),
) -> IsoComparisonResult:
    """Read and compare two ISO files."""

    expected_text = Path(expected_path).read_text(encoding="utf-8", errors="replace")
    actual_text = Path(actual_path).read_text(encoding="utf-8", errors="replace")
    return compare_iso_texts(expected_text, actual_text, options)


def unified_diff(
    expected_text: str,
    actual_text: str,
    options: IsoComparisonOptions = IsoComparisonOptions(),
    *,
    expected_label: str = "expected",
    actual_label: str = "actual",
) -> str:
    """Return a unified diff of normalized ISO lines."""

    expected = list(normalize_iso_lines(expected_text, options))
    actual = list(normalize_iso_lines(actual_text, options))
    return "\n".join(
        difflib.unified_diff(
            expected,
            actual,
            fromfile=expected_label,
            tofile=actual_label,
            lineterm="",
        )
    )
