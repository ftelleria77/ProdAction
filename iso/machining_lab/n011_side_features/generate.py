"""N011 — Side drill Ø8 en cara Front: pasante, peck y feed/spindle.

Pieza 300x200x18, origen 5/5/25 (DZ=43). Cara Front, Ø8, posición along=150, altura=9.
Casos:
  blind28 : ciego depth=28        (control: debe matchear el render actual)
  blind15 : ciego depth=15        (variación de profundidad)
  through : pasante               (¿cómo codifica el lateral el pasante?)
  peck_n3 : depth=28 step_number=3
  peck_d10: depth=28 step_depth=10
  fs      : depth=28 feedrate=1.5 spindle=4500

Uso:  py -m iso.machining_lab.n011_side_features.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N011_side_features\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N011_side_features"

ALONG, HEIGHT = 150.0, 9.0  # Front: center_x=along (X), center_y=altura en el canto (Z)

# (etiqueta, kwargs de build_drill_spec)
CASES = [
    ("blind28",  dict(target_depth=28.0)),
    ("blind15",  dict(target_depth=15.0)),
    ("through",  dict(is_through=True)),
    ("peck_n3",  dict(target_depth=28.0, step_number=3)),
    ("peck_d10", dict(target_depth=28.0, step_depth=10.0)),
    ("fs",       dict(target_depth=28.0, feedrate=1.5, spindle=4500.0)),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Side drill features Front Ø8 (N011).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, kw in CASES:
        name = f"N_SD_{tag}_front"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[build_drill_spec(
                center_x=ALONG, center_y=HEIGHT, diameter=8.0,
                plane_name="Front", tool_resolution="Auto", **kw,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({kw})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
