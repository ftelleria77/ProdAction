"""N004 — Top drill por diámetro: D4/D20/D35 (nuevos) + D5/D8/D15 (control).

Cada pieza: un taladro vertical ciego centrado, target_depth=10. Se postprocesa en
Maestro y se leen del ISO: ETK[6], ETK[0], spindle (S....M3), feed (F en G1 G9),
y SHF[X/Y/Z] del setup — para completar la tabla TOP_TOOL.

Los controles D5/D8/D15 deben reproducir los valores ya conocidos:
  D5  -> etk6=5 etk0=16 spindle=6000 feed=2000 shf=(-64, 0, -0.95)
  D8  -> etk6=1 etk0=1  spindle=6000 feed=2000 shf=(0, 0, 0)
  D15 -> etk6=2 etk0=2  spindle=4000 feed=1000 shf=(0, 32, -0.20)

Uso:  py -m iso.machining_lab.n004_top_diameters.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N004_top_diameters\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N004_top_diameters"

# Diámetros montados según oheads.cfg / def.tlgx. Control: 5/8/15. Nuevos: 4/20/35.
DIAMETERS = [4.0, 5.0, 8.0, 15.0, 20.0, 35.0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Top drill por diámetro (N004).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for dia in DIAMETERS:
        name = f"N_T{int(dia):02d}_top_d{dia:g}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=dia,
                plane_name="Top", target_depth=10.0, tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  (Ø{dia:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
