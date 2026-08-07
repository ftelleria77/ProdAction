"""N017 — Transición Top→Side en Right y Back (D8 vertical + side Ø8).

Pieza 300x200x18, origen 5/5/25. Un taladro vertical D8 + uno lateral (Right o Back) Ø8
target 20, security_plane sp. Confirma: (a) el bloque SHF previo al G40 (Right NO / Back SÍ),
(b) el piso del approach (5) y del g53 (10.5) y el shf_z por cara.

Uso:  py -m iso.machining_lab.n017_top_side_faces.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N017_top_side_faces\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N017_top_side_faces"

# (etiqueta, cara, along, sp)
CASES = [
    ("right_sp02", "Right", 100.0, 2.0),
    ("right_sp20", "Right", 100.0, 20.0),
    ("back_sp02",  "Back",  150.0, 2.0),
    ("back_sp20",  "Back",  150.0, 20.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Top→Side Right/Back (N017).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, face, along, sp in CASES:
        name = f"N_TS_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[
                build_drill_spec(center_x=150.0, center_y=100.0, diameter=8.0,
                                    plane_name="Top", target_depth=10.0, tool_resolution="Auto"),
                build_drill_spec(center_x=along, center_y=9.0, diameter=8.0,
                                    plane_name=face, target_depth=20.0, security_plane=sp,
                                    tool_resolution="Auto"),
            ],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({face}, sp={sp:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
