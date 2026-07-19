"""N015 — Xn (operación nula) y el park del footer. D8 ciego + Xn variable.

Pieza 300x200x18, origen 5/5/25, un taladro D8 ciego (target 10). Casos:
  no_xn        : sin Xn                       (control: footer actual = X-3700/Z201)
  xn_default   : Xn x=-3700                   (¿igual al control?)
  xn_x2000     : Xn x=-2000                   (¿el footer X sigue al Xn?)
  xn_x1500_y800: Xn x=-1500, y=800            (¿aparece Y? ¿cambia algo más?)
  xn_x0        : Xn x=0

Uso:  py -m iso.machining_lab.n015_xn_park.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N015_xn_park\\
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import (  # noqa: E402
    build_drill_spec, build_synthesis_request, build_xn_spec, synthesize_request,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N015_xn_park"

# (etiqueta, xn_kwargs o None). Y de la cama: rango 0 a ~-1500 (Fermín).
CASES = [
    ("no_xn",          None),
    ("xn_default",     dict(x=-3700.0)),
    ("xn_x2000",       dict(x=-2000.0)),
    ("xn_x1500_ym700", dict(x=-1500.0, y=-700.0)),
    ("xn_x0",          dict(x=0.0)),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Xn y park del footer (N015).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, xn in CASES:
        name = f"N_XN_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=8.0,
                plane_name="Top", target_depth=10.0, tool_resolution="Auto",
            )],
            xn=None if xn is None else build_xn_spec(**xn),
        )
        synthesize_request(req)
        print(f"  {path.name}  ({'sin Xn' if xn is None else xn})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
