"""Compatibility facade for `pgmx.adapters`."""

from __future__ import annotations

from pgmx import adapters as _adapters
from pgmx.adapters import *  # noqa: F401,F403
from pgmx.adapters import main

__all__ = tuple(getattr(_adapters, "__all__", ())) + ("main",)


def __getattr__(name: str):
    return getattr(_adapters, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_adapters)))


if __name__ == "__main__":
    raise SystemExit(main())
