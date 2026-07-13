"""N008 — Patrones de perforado (rectangular) con D8 ciego, target_depth=10.

Casos elegidos para aislar geometría y orden:
  - 2x1 y 1x2: dirección de columnas (X) y filas (Y) + ubicación del center.
  - 3x1 y 1x3: confirmar paso uniforme y sentido.
  - 3x2: orden completo (row-major vs column-major vs serpentina).
center en (100,80), spacing=40 (cols, X), row_spacing=30 (filas, Y).

Uso:  py -m iso.machining_lab.n008_drill_patterns.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N008_drill_patterns\\
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_drill_pattern_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N008_drill_patterns"

CENTER_X, CENTER_Y = 100.0, 80.0
SPACING, ROW_SPACING = 40.0, 30.0

# (etiqueta, columnas, filas)
CASES = [
    ("2x1", 2, 1),
    ("1x2", 1, 2),
    ("3x1", 3, 1),
    ("1x3", 1, 3),
    ("3x2", 3, 2),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patrones de perforado D8 (N008).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, cols, rows in CASES:
        name = f"N_DP_{tag}_d8"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drill_patterns=[build_drill_pattern_spec(
                CENTER_X, CENTER_Y, 8.0,
                columns=cols, rows=rows,
                spacing=SPACING, row_spacing=ROW_SPACING,
                plane_name="Top", is_through=False, target_depth=10.0,
                tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({cols} cols x {rows} filas)")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
