"""Compatibility facade for `pgmx.snapshot`."""

from __future__ import annotations

from pgmx import snapshot as _snapshot
from pgmx.snapshot import *  # noqa: F401,F403
from pgmx.snapshot import main

__all__ = tuple(getattr(_snapshot, "__all__", ())) + ("main",)


def __getattr__(name: str):
    return getattr(_snapshot, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_snapshot)))


if __name__ == "__main__":
    raise SystemExit(main())
