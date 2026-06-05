"""Compatibility facade for `pgmx.machining_lab.pocket_milling.scan_samples`."""

from __future__ import annotations

from pgmx.machining_lab.pocket_milling.scan_samples import *  # noqa: F401,F403
from pgmx.machining_lab.pocket_milling.scan_samples import main


if __name__ == "__main__":
    raise SystemExit(main())
