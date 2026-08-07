"""N018 — De dónde salen los %Or[0].ofX/ofY (origen de trabajo del ISO).

Todos los fixtures previos usan la MISMA pieza (300×200, origen 5,5), así que ofX[blk]=-310000 y
ofY=-1515599.976 no se pueden distinguir entre constante de máquina o fórmula que depende de la
pieza (riesgo de sobreajuste). Este lote VARÍA la geometría para desambiguar.

Hipótesis a confirmar (de la única geometría conocida 300×200/5,5):
  - ofZ = DZ×1000                              (ya confirmado en N013)
  - ofX[preamble] = -DX×1000  (DX=length+origin_x)
  - ofX[bloque]   = -(DX+origin_x)×1000 ?  (porque -310 = -(305+5));  ó constante -310000 ?
  - ofY           = cero-Y de máquina, independiente de la pieza ?  (-1515.599976 ≈ HG.y)

Casos (hueco simple D8 pasante, centrado; origin_z=25, depth=18 → DZ=43 fijo para aislar X/Y):
  base        300×200 ox5  oy5   → reproduce -305000 / -310000 / -1515599.976
  len400      400×200 ox5  oy5   → ofX vs length
  ox20        300×200 ox20 oy5   → separa origin_x: ¿-(DX+ox) o -(DX+5) fijo?
  wid300oy20  300×300 ox5  oy20  → ¿ofY depende de Y o es constante?

Uso:  py -m iso.machining_lab.n018_work_origin.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N018_work_origin\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N018_work_origin"

# (etiqueta, length, width, origin_x, origin_y)
CASES = [
    ("base",       300.0, 200.0,  5.0,  5.0),
    ("len400",     400.0, 200.0,  5.0,  5.0),
    ("ox20",       300.0, 200.0, 20.0,  5.0),
    ("wid300oy20", 300.0, 300.0,  5.0, 20.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Origen de trabajo Or[0] vs geometría (N018).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, length, width, ox, oy in CASES:
        name = f"N_WO_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=length, width=width, depth=18.0,
            origin_x=ox, origin_y=oy, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=length / 2, center_y=width / 2, diameter=8.0,
                plane_name="Top", is_through=True, drill_family="Flat",
                tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({length:g}×{width:g}, ox={ox:g}, oy={oy:g}, DX={length+ox:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
