"""N016 — g53 de transición Top→Side con security_plane lateral variable.

Pieza 300x200x18, origen 5/5/25 (DZ=43). Un taladro vertical D8 (target 10) + un taladro
lateral Front Ø8 (target 20) con security_plane = sp. Se lee del ISO el `G0 G53 Z<g53>` de
la transición Top→Side para re-derivar el +20 y el piso 5.

Uso:  py -m iso.machining_lab.n016_g53_transition.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N016_g53_transition\\
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_drilling_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N016_g53_transition"

SP_VALUES = [2.0, 5.0, 10.0, 20.0, 30.0]  # 20 = control (valor ya validado: g53=149.5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="g53 transición Top→Side (N016).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for sp in SP_VALUES:
        name = f"N_G53_top_front_sp{int(sp):02d}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[
                build_drilling_spec(center_x=150.0, center_y=100.0, diameter=8.0,
                                    plane_name="Top", target_depth=10.0, tool_resolution="Auto"),
                build_drilling_spec(center_x=150.0, center_y=9.0, diameter=8.0,
                                    plane_name="Front", target_depth=20.0, security_plane=sp,
                                    tool_resolution="Auto"),
            ],
        )
        synthesize_request(req)
        print(f"  {path.name}  (side security_plane={sp:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
