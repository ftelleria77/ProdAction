"""N021 — Extensión del estudio de campos a AB (atrás-izq) y DC (atrás-der).

Grilla 2×2: HG (front-der, referencia calibrada), EF (front-izq, espejo X — N019/N020),
DC (back-der, espejo Y), AB (back-izq, espejo X+Y). Orígenes (fields.cfg):
  AB=(-3685.85, 0)   DC=(0, 0)   EF=(-3688, -1515.25)   HG=(0, -1515.60)

Objetivo: derivar la ESTRUCTURA del espejado de AB/DC (origen/SHF, remapeo de caras, reachability).
  - DC aísla el espejo en Y (X=0 como HG, pero atrás) → cómo se comporta SHF[Y]/ofY al invertir Y.
  - AB combina X+Y → confirma.

⚠️ AB/DC descalibrados (solo HG es válido): los VALORES serán los viejos; lo que se deriva es la
ESTRUCTURA. El converter los rechaza (fail-loud); son entrada a Maestro.

Reachability esperada (a confirmar):
  - AB (X≈-3686, izq): cara Left choca tope X → se prueba con origin_x=105 (corrida +X), como en EF.
  - DC (X=0, der): caras X como HG. Y atrás: ver qué cara (Front/Back) queda hacia el tope Y.

Top off-center (60,40) para ver el espejado; variación de origin en el campo que aísla cada eje.

Uso:  py -m iso.machining_lab.n021_fields_ab_dc.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N021_fields_ab_dc\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N021_fields_ab_dc"

# (campo, etiqueta, plane, center_x, center_y, length, width, origin_x, origin_y, depth)
CASES = [
    # DC (back-der): aísla el espejo en Y
    ("DC", "top_base", "Top",   60.0, 40.0, 300.0, 200.0,  5.0,  5.0, 10.0),
    ("DC", "top_oy20", "Top",   60.0, 40.0, 300.0, 200.0,  5.0, 20.0, 10.0),
    ("DC", "front",    "Front", 60.0,  9.0, 300.0, 200.0,  5.0,  5.0, 15.0),
    ("DC", "back",     "Back",  60.0,  9.0, 300.0, 200.0,  5.0,  5.0, 15.0),
    ("DC", "left",     "Left",  60.0,  9.0, 300.0, 200.0,  5.0,  5.0, 15.0),
    ("DC", "right",    "Right", 60.0,  9.0, 300.0, 200.0,  5.0,  5.0, 15.0),
    # AB (back-izq): espejo X+Y; Left con corrida +X para esquivar el tope
    ("AB", "top_base",  "Top",   60.0, 40.0, 300.0, 200.0,   5.0, 5.0, 10.0),
    ("AB", "top_ox20",  "Top",   60.0, 40.0, 300.0, 200.0,  20.0, 5.0, 10.0),
    ("AB", "front",     "Front", 60.0,  9.0, 300.0, 200.0,   5.0, 5.0, 15.0),
    ("AB", "back",      "Back",  60.0,  9.0, 300.0, 200.0,   5.0, 5.0, 15.0),
    ("AB", "right",     "Right", 60.0,  9.0, 300.0, 200.0,   5.0, 5.0, 15.0),
    ("AB", "left_ox105", "Left", 60.0,  9.0, 300.0, 200.0, 105.0, 5.0, 15.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Campos AB y DC (N021).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for field, tag, plane, cx, cy, length, width, ox, oy, depth in CASES:
        name = f"N_{field}_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=length, width=width, depth=18.0,
            origin_x=ox, origin_y=oy, origin_z=25.0,
            execution_fields=field,
            drills=[build_drill_spec(
                center_x=cx, center_y=cy, diameter=8.0,
                plane_name=plane, target_depth=depth, tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({field}, {plane}, {length:g}×{width:g}, ox={ox:g}, oy={oy:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro (campos AB y DC) y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
