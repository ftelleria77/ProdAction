"""Pocket milling integration status for PGMX synthesis."""

from __future__ import annotations

from dataclasses import dataclass

from .core import PocketSpec


@dataclass(frozen=True)
class PocketSynthesisSupport:
    """Current production boundary for Vaciado synthesis."""

    enabled: bool
    model_package: str
    legacy_engine_allowed: bool
    notes: tuple[str, ...] = ()


def pocket_support_status() -> PocketSynthesisSupport:
    """Return the current Vaciado integration status for the PGMX subsystem."""

    return PocketSynthesisSupport(
        enabled=True,
        model_package="pgmx.synthesis.milling.pocket",
        legacy_engine_allowed=False,
        notes=(
            "PocketSpec remains the public PGMX spec for ClosedPocket Vaciado.",
            "The former V2 contract now lives in pgmx.synthesis.milling.pocket_contract.",
            "The pocket trace engine lives in pgmx.synthesis.milling.pocket_trace.",
        ),
    )


def adapt_pocket_to_contract(spec: PocketSpec):
    """Adapt a public `PocketSpec` to the Vaciado V2 contract.

    The import is intentionally lazy to avoid making the public synthesizer
    package depend on laboratory modules at import time.
    """

    from pgmx.synthesis.milling.pocket_contract import from_pocket_spec

    return from_pocket_spec(spec)
