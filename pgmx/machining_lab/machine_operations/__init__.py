"""Machine-operation research laboratory for PGMX program-flow evidence."""

from __future__ import annotations

from pathlib import Path

EXTERNAL_ROOT = Path(r"S:\Maestro\Projects\ProdAction\PGMX\machine_operations")
MANUAL_ROOT = EXTERNAL_ROOT / "manual"
GENERATED_ROOT = EXTERNAL_ROOT / "generated"
ANALYSIS_ROOT = EXTERNAL_ROOT / "_analysis"

__all__ = [
    "ANALYSIS_ROOT",
    "EXTERNAL_ROOT",
    "GENERATED_ROOT",
    "MANUAL_ROOT",
]
