"""Initial ISO emitter surface.

Only the validated header rule is emitted for now.  Operational blocks are the
next MVP step and must not be implied by this scaffold.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from tools import synthesize_pgmx as sp

from .model import IsoGenerationError, IsoGenerationWarning, IsoProgram
from .pgmx_source import PgmxIsoSource, load_pgmx_iso_source


class IsoEmissionNotImplemented(IsoGenerationError, NotImplementedError):
    """Raised when callers request operational ISO blocks before the MVP exists."""


def build_iso_header_lines(
    state: sp.PgmxState,
    *,
    program_name: str,
) -> tuple[str, str]:
    """Build the two validated ISO header lines for a PGMX state."""

    area = _normalize_execution_area(state.execution_fields)
    return (
        f"% {program_name}.pgm",
        (
            f";H DX={_format_mm(state.length + state.origin_x)} "
            f"DY={_format_mm(state.width + state.origin_y)} "
            f"DZ={_format_mm(state.depth + state.origin_z)} "
            "BX=0.000 BY=0.000 BZ=0.000 "
            f"-{area} V=0 *MM C=0 T=0"
        ),
    )


def emit_header_only(
    source: PgmxIsoSource | Path,
    *,
    program_name: Optional[str] = None,
) -> IsoProgram:
    """Emit only the validated ISO header.

    This is useful for comparing the first contract rules while the operational
    emitter is still under construction.
    """

    if not isinstance(source, PgmxIsoSource):
        source = load_pgmx_iso_source(Path(source))
    resolved_program_name = _program_name(program_name, source.path)
    warnings = (
        IsoGenerationWarning(
            code="header_only",
            message=(
                "Only the validated ISO header is emitted. Operational blocks "
                "are intentionally not generated yet."
            ),
            source=str(source.path),
        ),
        *source.warnings,
    )
    return IsoProgram(
        program_name=resolved_program_name,
        lines=build_iso_header_lines(source.state, program_name=resolved_program_name),
        warnings=warnings,
    )


def emit_iso_program(
    source: PgmxIsoSource | Path,
    *,
    program_name: Optional[str] = None,
) -> IsoProgram:
    """Future full emitter entry point.

    It raises until the MVP operational families are implemented.
    """

    if not isinstance(source, PgmxIsoSource):
        source = load_pgmx_iso_source(Path(source))
    resolved_program_name = _program_name(program_name, source.path)
    raise IsoEmissionNotImplemented(
        "Full ISO emission is not implemented yet. "
        f"Use emit_header_only(..., program_name={resolved_program_name!r}) "
        "for the validated header contract."
    )


def _program_name(program_name: Optional[str], source_path: Path) -> str:
    raw = (program_name or source_path.stem).strip()
    return raw or "program"


def _normalize_execution_area(value: str) -> str:
    normalized = (value or "HG").strip().upper().replace(" ", "")
    return normalized or "HG"


def _format_mm(value: float) -> str:
    return f"{float(value):.3f}"
