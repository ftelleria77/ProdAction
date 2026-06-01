"""Internal package for PGMX synthesis.

`tools.synthesize_pgmx` remains the public compatibility facade. New production
PGMX synthesis modules should live here instead of growing that facade.
"""

from __future__ import annotations

from . import core as _core
from .core import *  # noqa: F401,F403
from .core import __all__ as _core_all
from .core import main
from .vaciado import (
    VaciadoSynthesisSupport,
    adapt_pocket_milling_to_vaciado_contract,
    vaciado_support_status,
)

__all__ = tuple(_core_all) + (
    "VaciadoSynthesisSupport",
    "adapt_pocket_milling_to_vaciado_contract",
    "main",
    "vaciado_support_status",
)


def __getattr__(name: str):
    return getattr(_core, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_core)))
