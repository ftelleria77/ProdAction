"""Experimental ISO generation subsystem for ProdAction.

The package is intentionally separate from the main PySide application and from
`cnc_traceability`.  It starts as a small translation workbench around existing
PGMX snapshots, Maestro ISO references, and comparison tooling.
"""

from .comparator import (
    IsoComparisonOptions,
    IsoComparisonResult,
    compare_iso_files,
    compare_iso_texts,
    normalize_iso_lines,
)
from .emitter import (
    IsoEmissionNotImplemented,
    build_iso_header_lines,
    emit_header_only,
    emit_iso_program,
)
from .model import IsoGenerationWarning, IsoProgram
from .pgmx_source import PgmxIsoSource, load_pgmx_iso_source

__all__ = [
    "IsoComparisonOptions",
    "IsoComparisonResult",
    "IsoEmissionNotImplemented",
    "IsoGenerationWarning",
    "IsoProgram",
    "PgmxIsoSource",
    "build_iso_header_lines",
    "compare_iso_files",
    "compare_iso_texts",
    "emit_iso_program",
    "emit_header_only",
    "load_pgmx_iso_source",
    "normalize_iso_lines",
]
