"""Pure helpers for options dialogs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NonNegativeMeasureParseResult:
    value: float | None
    error: str | None = None


def parse_non_negative_measure(raw_value: str) -> NonNegativeMeasureParseResult:
    raw_text = str(raw_value or "").strip().replace(",", ".")
    try:
        value = float(raw_text)
    except ValueError:
        return NonNegativeMeasureParseResult(None, "invalid")
    if value < 0:
        return NonNegativeMeasureParseResult(None, "negative")
    return NonNegativeMeasureParseResult(value)
