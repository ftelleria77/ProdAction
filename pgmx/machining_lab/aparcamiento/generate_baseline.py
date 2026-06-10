"""Generate a minimal baseline PGMX for the Aparcamiento lab.

Produces a 400 x 400 x 18 piece with origin (5, 5, 25), one empty workplan,
and no machinings or machine operations (Xn suppressed).
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Optional

from pgmx import synthesis as sp

from . import GENERATED_ROOT


def generate(output_path: Path) -> Path:
    request = sp.build_synthesis_request(
        output_path=output_path,
        piece_name="Aparcamiento_Baseline",
        length=400.0,
        width=400.0,
        depth=18.0,
        origin_x=5.0,
        origin_y=5.0,
        origin_z=25.0,
        workplans=[sp.build_workplan_spec()],
    )
    sp.synthesize_request(request)
    sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
    print(f"Generado: {output_path}")
    print(f"SHA256:   {sha256}")
    return output_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=GENERATED_ROOT / "Aparcamiento_Baseline.pgmx",
    )
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generate(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
