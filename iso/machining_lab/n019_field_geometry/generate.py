"""N019 — Cálculos geométricos por CAMPO: HG (front-der) vs EF (front-izq).

EF es el espejo en X de HG (mismo lado Y, lado X opuesto). Esto sirve para estudiar cómo cambian
los cálculos geométricos al cambiar de campo: no solo el origen, sino la DIRECCIÓN de los movimientos
(signos), el remapeo de caras (¿Left de EF se comporta como Right de HG?), etc.

⚠️ EF tiene calibración inicial INVÁLIDA (ver bitácora): los VALORES de origen que devuelva Maestro
serán los viejos. Pero la ESTRUCTURA (signos/espejado/remapeo) es lo que queremos derivar — eso no
depende de la calibración fina. Los números se ajustan cuando se recalibre EF.

Piezas ASIMÉTRICAS (huecos fuera de centro): un hueco centrado se ve igual espejado y oculta el
efecto. Se generan PARES HG+EF de la misma geometría para diff directo.
  top    : taladro Top en (60, 40) — rompe simetría X e Y → espejado de coordenadas top
  left   : taladro cara Left, along=60 — cara sobre el lado X
  front  : taladro cara Front, along=60 — cara sobre el lado Y

Nota: el converter ISO rechaza EF (fail-loud); estos fixtures son entrada a MAESTRO, no al converter.

Uso:  py -m iso.machining_lab.n019_field_geometry.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N019_field_geometry\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N019_field_geometry"

FIELDS = ["HG", "EF"]

# (etiqueta, plane_name, center_x, center_y, target_depth)  — asimétricos a propósito.
GEOMS = [
    ("top",   "Top",   60.0, 40.0, 10.0),
    ("left",  "Left",  60.0,  9.0, 15.0),
    ("front", "Front", 60.0,  9.0, 15.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Geometría por campo HG vs EF (N019).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for field in FIELDS:
        for tag, plane, cx, cy, depth in GEOMS:
            name = f"N_FG_{tag}_{field}"
            path = out / f"{name}.pgmx"
            req = build_synthesis_request(
                output_path=path, piece_name=name,
                length=300.0, width=200.0, depth=18.0,
                origin_x=5.0, origin_y=5.0, origin_z=25.0,
                execution_fields=field,
                drillings=[build_drill_spec(
                    center_x=cx, center_y=cy, diameter=8.0,
                    plane_name=plane, target_depth=depth, tool_resolution="Auto",
                )],
            )
            synthesize_request(req)
            print(f"  {path.name}  ({field}, {plane} @ ({cx:g},{cy:g}))")

    print("\nListo. Postprocesá los .pgmx en Maestro (HG y EF) y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
