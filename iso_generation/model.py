"""Small public model for the experimental ISO subsystem."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any


class IsoGenerationError(RuntimeError):
    """Base error raised by the ISO generation subsystem."""


@dataclass(frozen=True)
class IsoGenerationWarning:
    """Non-blocking issue found while preparing a translation."""

    code: str
    message: str
    source: str = ""


@dataclass(frozen=True)
class IsoProgram:
    """ISO text plus warnings produced while emitting it."""

    program_name: str
    lines: tuple[str, ...]
    warnings: tuple[IsoGenerationWarning, ...] = ()

    def text(self) -> str:
        """Return the program text with a final newline."""

        return "\n".join(self.lines) + "\n"

    def write_text(self, output_path: Path) -> Path:
        """Write the ISO text as UTF-8 and return the output path."""

        output_path = Path(output_path)
        output_path.write_text(self.text(), encoding="utf-8")
        return output_path


def to_jsonable(value: Any) -> Any:
    """Convert nested dataclasses, tuples and paths to JSON-friendly objects."""

    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value
