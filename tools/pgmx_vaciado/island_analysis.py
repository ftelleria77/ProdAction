"""Compatibility facade for `pgmx.machining_lab.pocket_milling.island_analysis`."""

from __future__ import annotations

from pgmx.machining_lab.pocket_milling.island_analysis import *  # noqa: F401,F403
from pgmx.machining_lab.pocket_milling.island_analysis import main


if __name__ == "__main__":
    raise SystemExit(main())
