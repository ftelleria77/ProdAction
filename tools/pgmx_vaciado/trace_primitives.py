"""Compatibility facade for `pgmx.vaciado_lab.trace_primitives`."""

from __future__ import annotations

from pgmx.vaciado_lab.trace_primitives import *  # noqa: F401,F403
from pgmx.vaciado_lab.trace_primitives import main


if __name__ == "__main__":
    raise SystemExit(main())
