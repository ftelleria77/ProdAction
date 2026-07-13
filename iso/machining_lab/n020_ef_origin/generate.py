"""N020 — Fórmula del origen/SHF en el campo EF (espejado en X) + remapeo de caras.

N019 mostró que en EF: SHF[X]=field_x (=-3688), SHF[Y]=field_y (=-1515.25), el eje X se espeja, y
EDK[13]→EDK[10]. Pero con UNA sola geometría no se separa field_x del término de pieza ni se ve el
signo del espejo. Este lote VARÍA la geometría EN EF para derivar las fórmulas, como N018 hizo en HG.

⚠️ EF descalibrado: los valores serán los viejos (-3688 / -1515.25). Lo que se deriva es la ESTRUCTURA
(¿el SHF[X] de EF lleva término de pieza?, ¿con qué signo?). Los valores caen solos al recalibrar +
re-snapshotear fields.cfg.

Top (hueco off-center 60,40 fijo, para aislar el efecto de la geometría en el origen):
  top_base    300×200 ox5  oy5
  top_len400  400×200 ox5  oy5   → efecto de length en ofX/SHF[X] EF
  top_ox20    300×200 ox20 oy5   → efecto de origin_x (separa el término de pieza)
  top_oy20    300×200 ox5  oy20  → efecto de origin_y en ofY/SHF[Y] EF
Caras alcanzables en EF (Left choca el límite X → se omite):
  right  cara Right (lado +X, hacia el centro) → remapeo de cara
  back   cara Back                              → remapeo de cara

Uso:  py -m iso.machining_lab.n020_ef_origin.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N020_ef_origin\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N020_ef_origin"

# (etiqueta, plane, center_x, center_y, length, width, origin_x, origin_y, depth)
CASES = [
    ("top_base",   "Top",   60.0, 40.0, 300.0, 200.0,  5.0,  5.0, 10.0),
    ("top_len400", "Top",   60.0, 40.0, 400.0, 200.0,  5.0,  5.0, 10.0),
    ("top_ox20",   "Top",   60.0, 40.0, 300.0, 200.0, 20.0,  5.0, 10.0),
    ("top_oy20",   "Top",   60.0, 40.0, 300.0, 200.0,  5.0, 20.0, 10.0),
    ("right",      "Right", 60.0,  9.0, 300.0, 200.0,  5.0,  5.0, 15.0),
    ("back",       "Back",  60.0,  9.0, 300.0, 200.0,  5.0,  5.0, 15.0),
    # Left en EF con origin_x=105 (pieza corrida +X, lejos del límite X): probar si así NO choca
    # el tope del eje X y la cara Left se vuelve alcanzable (Fermín).
    ("left_ox105", "Left",  60.0,  9.0, 300.0, 200.0, 105.0,  5.0, 15.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Origen/SHF en EF, geometría variada (N020).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, plane, cx, cy, length, width, ox, oy, depth in CASES:
        name = f"N_EO_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=length, width=width, depth=18.0,
            origin_x=ox, origin_y=oy, origin_z=25.0,
            execution_fields="EF",
            drills=[build_drill_spec(
                center_x=cx, center_y=cy, diameter=8.0,
                plane_name=plane, target_depth=depth, tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  (EF, {plane}, {length:g}×{width:g}, ox={ox:g}, oy={oy:g})")

    print("\nListo. Postprocesá los .pgmx en Maestro (campo EF) y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
