"""N005 — Top drill pasante (is_through) plano con D8.

Un taladro vertical pasante centrado por pieza. Se varía espesor y extra_depth
para derivar del ISO la profundidad de corte del pasante (y ver si cambia ETK[7]
respecto del ciego). D8 se mantiene Flat; el pasante en D5 se vuelve Conical y se
trata aparte.

Control: comparar contra el ciego D8 de N004 (mismo Ø, setup idéntico) para aislar
qué líneas cambian al volverse pasante.

Uso:  py -m iso.machining_lab.n005_top_through.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N005_top_through\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N005_top_through"

# (etiqueta, espesor, extra_depth) — 1 variable por pieza respecto del par base.
CASES = [
    ("t18_e0", 18.0, 0.0),   # base: espesor 18, sin sobre-recorrido
    ("t18_e2", 18.0, 2.0),   # +extra_depth
    ("t18_e5", 18.0, 5.0),   # +extra_depth mayor
    ("t25_e0", 25.0, 0.0),   # +espesor (con e0)
    ("t12_e3", 12.0, 3.0),   # espesor menor + extra_depth
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Top drill pasante D8 (N005).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, thickness, extra in CASES:
        name = f"N_P_{tag}_through_d8"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=thickness,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=8.0,
                plane_name="Top", is_through=True, extra_depth=extra,
                tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  (espesor={thickness:g}, extra_depth={extra:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
