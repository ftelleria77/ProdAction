"""Aparcamiento machine-operation research laboratory for PGMX evidence."""

from __future__ import annotations

from pathlib import Path

# Corpus movido a "Investigación previa" al arrancar la era del converter (lotes N0xx).
EXTERNAL_ROOT = Path(r"S:\Maestro\Projects\ProdAction\Investigación previa\PGMX\aparcamiento")
MANUAL_ROOT = EXTERNAL_ROOT / "manual"
GENERATED_ROOT = EXTERNAL_ROOT / "generated"
ANALYSIS_ROOT = EXTERNAL_ROOT / "_analysis"

__all__ = [
    "ANALYSIS_ROOT",
    "EXTERNAL_ROOT",
    "GENERATED_ROOT",
    "MANUAL_ROOT",
]
