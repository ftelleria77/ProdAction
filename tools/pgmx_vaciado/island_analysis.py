"""Compatibility facade for `pgmx.vaciado_lab.island_analysis`."""

from __future__ import annotations

from pgmx.vaciado_lab.island_analysis import *  # noqa: F401,F403
from pgmx.vaciado_lab.island_analysis import main


if __name__ == "__main__":
    raise SystemExit(main())
