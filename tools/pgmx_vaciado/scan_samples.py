"""Compatibility facade for `pgmx.vaciado_lab.scan_samples`."""

from __future__ import annotations

from pgmx.vaciado_lab.scan_samples import *  # noqa: F401,F403
from pgmx.vaciado_lab.scan_samples import main


if __name__ == "__main__":
    raise SystemExit(main())
