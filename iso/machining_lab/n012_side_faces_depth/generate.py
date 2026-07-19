"""N012 — Cut lateral en Left/Right/Back a depth=15 (y depth=28 de control).

Confirma la fórmula nueva (cut = borde ∓ TLC_CUT ± depth, approach fijo) en las caras
que N001 solo prueba a depth=28. Pieza 300x200x18, origen 5/5/25.

Uso:  py -m iso.machining_lab.n012_side_faces_depth.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N012_side_faces_depth\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N012_side_faces_depth"

# (etiqueta, cara, along, depth). along = posición sobre el canto; altura fija 9.
CASES = [
    ("left_d15",  "Left",  100.0, 15.0),
    ("right_d15", "Right", 100.0, 15.0),
    ("back_d15",  "Back",  150.0, 15.0),
    ("left_d28",  "Left",  100.0, 28.0),   # control: debe matchear N001/código viejo
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cut lateral por cara a depth≠28 (N012).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, face, along, depth in CASES:
        name = f"N_SF_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=along, center_y=9.0, diameter=8.0,
                plane_name=face, target_depth=depth, tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({face}, depth={depth:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
