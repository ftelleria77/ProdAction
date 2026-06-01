"""Compatibility facade for the PGMX synthesizer CLI and legacy imports."""

from __future__ import annotations

from pgmx.synthesis import core as _core
from pgmx.synthesis import *  # noqa: F401,F403
from pgmx.synthesis import main

__all__ = tuple(getattr(_core, "__all__", ())) + ("main",)


def __getattr__(name: str):
    return getattr(_core, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_core)))


if __name__ == "__main__":
    raise SystemExit(main())
