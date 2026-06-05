"""Historical Vaciado integration boundary for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass

from .core import PocketMillingSpec


@dataclass(frozen=True)
class VaciadoSynthesisSupport:
    """Current production boundary for Vaciado synthesis."""

    enabled: bool
    model_package: str
    legacy_engine_allowed: bool
    notes: tuple[str, ...] = ()


def vaciado_support_status() -> VaciadoSynthesisSupport:
    """Return the current Vaciado integration status for the PGMX subsystem."""

    return VaciadoSynthesisSupport(
        enabled=True,
        model_package="pgmx.synthesis.milling.pocket",
        legacy_engine_allowed=False,
        notes=(
            "PocketMillingSpec remains the public PGMX spec for ClosedPocket Vaciado.",
            "The former V2 contract now lives in pgmx.synthesis.milling.pocket_contract.",
            "The pocket trace engine lives in pgmx.synthesis.milling.pocket_trace; pgmx.vaciado_lab reexports it for compatibility.",
        ),
    )


def adapt_pocket_milling_to_vaciado_contract(spec: PocketMillingSpec):
    """Adapt a public `PocketMillingSpec` to the Vaciado V2 contract.

    The import is intentionally lazy to avoid making the public synthesizer
    package depend on laboratory modules at import time.
    """

    from pgmx.synthesis.milling.pocket_contract import from_pocket_milling_spec

    return from_pocket_milling_spec(spec)
