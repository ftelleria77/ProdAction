"""N006 — Top drill multi-step / peck con D8 ciego (target_depth=14).

step_number (cantidad de pasos) y step_depth (profundidad por paso) son mutuamente
excluyentes. Se postprocesa en Maestro para ver cómo expresa el escalonado en ISO
(varios G1 G9 Z… vs. parámetro de ciclo).

Control: el ciego D8 simple (N004, sin peck) sirve de referencia para aislar qué
líneas agrega el escalonado.

Uso:  py -m iso.machining_lab.n006_top_peck.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N006_top_peck\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N006_top_peck"

# (etiqueta, step_number, step_depth) — uno u otro, nunca ambos. target_depth=14.
CASES = [
    ("n2", 2, 0.0),   # 2 pasos por cantidad
    ("n3", 3, 0.0),   # 3 pasos por cantidad
    ("n4", 4, 0.0),   # 4 pasos por cantidad
    ("d3", 0, 3.0),   # paso de 3 mm
    ("d5", 0, 5.0),   # paso de 5 mm
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Top drill peck D8 (N006).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, step_number, step_depth in CASES:
        name = f"N_PK_{tag}_peck_d8"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=8.0,
                plane_name="Top", target_depth=14.0,
                step_number=step_number or None,
                step_depth=step_depth or None,
                tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        kind = f"step_number={step_number}" if step_number else f"step_depth={step_depth:g}"
        print(f"  {path.name}  ({kind})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
