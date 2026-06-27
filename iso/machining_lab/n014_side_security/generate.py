"""N014 — Barrido de security_plane en un taladro lateral Front Ø8, depth=20.

Un solo agujero por pieza (side-only, sin transición g53) para aislar el approach.
Si approach varía con sp → usa la operación (corregir el código a -(TLC_CUT+sp)).
Si approach queda fijo → es una constante de máquina (sourcear, no hornear).

Uso:  py -m iso.machining_lab.n014_side_security.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N014_side_security\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N014_side_security"

SP_VALUES = [5.0, 10.0, 20.0, 30.0]  # 20 = control (igual a lo ya validado)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Barrido security_plane lateral (N014).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for sp in SP_VALUES:
        name = f"N_SS_front_sp{int(sp):02d}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[build_drilling_spec(
                center_x=150.0, center_y=9.0, diameter=8.0,
                plane_name="Front", target_depth=20.0, security_plane=sp,
                tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  (security_plane={sp:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
