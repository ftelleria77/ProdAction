"""Compatibility facade for `pgmx.processing`."""

from __future__ import annotations

from pgmx.processing import *  # noqa: F401,F403
from pgmx import processing as _processing


def __getattr__(name: str):
    return getattr(_processing, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_processing)))
