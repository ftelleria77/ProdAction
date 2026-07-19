"""Public package for PGMX synthesis."""

from __future__ import annotations

from . import core as _core
from .cli import main
from .core import *  # noqa: F401,F403
from .core import __all__ as _core_all
from .pocket_support import (
    PocketSynthesisSupport,
    adapt_pocket_to_contract,
    pocket_support_status,
)

__all__ = tuple(_core_all) + (
    "PocketSynthesisSupport",
    "adapt_pocket_to_contract",
    "main",
    "pocket_support_status",
)


def __getattr__(name: str):
    return getattr(_core, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_core)))
