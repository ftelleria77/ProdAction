"""N009 — Override feedrate/spindle por operación, D8 ciego target=10.

Default tool D8: F2000 / S6000. Casos:
  f1500 : feedrate=1500          (¿F1500 directo o F1500000 si m/min?)
  f3    : feedrate=3             (desambigua unidad: F3 vs F3000)
  s4500 : spindle=4500           (solo husillo)
  both  : feedrate=1200, spindle=5000

Uso:  py -m iso.machining_lab.n009_top_feedspindle.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N009_top_feedspindle\\
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_drill_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N009_top_feedspindle"

# (etiqueta, feedrate, spindle) — 0 = sin override (usa default de la tool).
# Sub-máximo (f0p5/f1p5/f2p5) desambigua: si F=valor×1000 → value-faithful con clamp;
# si F=3000 fijo → cualquier override usa el feed de trabajo de la tool (valor ignorado).
CASES = [
    ("f1500", 1500.0, 0.0),
    ("f3",    3.0,    0.0),
    ("s4500", 0.0,    4500.0),
    ("both",  1200.0, 5000.0),
    ("f0p5",  0.5,    0.0),
    ("f1p5",  1.5,    0.0),
    ("f2p5",  2.5,    0.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Override feed/spindle D8 (N009).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, feed, spindle in CASES:
        name = f"N_FS_{tag}_d8"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=8.0,
                plane_name="Top", target_depth=10.0, tool_resolution="Auto",
                feedrate=feed or None, spindle=spindle or None,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  (feed={feed:g}, spindle={spindle:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
