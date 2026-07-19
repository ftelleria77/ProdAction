"""N013 — Pasante vertical vs. SinkingLength de la broca.

D20 SinkingLength=20. Casos (todos pasante, centrado, Ø según etiqueta):
  d20_t40 : espesor 40, D20 pasante  → 40 > 20  → se espera ERROR de Maestro
  d20_t20 : espesor 20, D20 pasante  → 20 = 20  → borde (¿entra?)
  d20_t18 : espesor 18, D20 pasante  → 18 < 20  → OK
  d8_t40  : espesor 40, D8  pasante  → 40 = 40 (D8 sink=40) → borde OK

Uso:  py -m iso.machining_lab.n013_top_depth_limit.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N013_top_depth_limit\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N013_top_depth_limit"

# (etiqueta, espesor, diámetro)
CASES = [
    ("d20_t40", 40.0, 20.0),
    ("d20_t20", 20.0, 20.0),
    ("d20_t18", 18.0, 20.0),
    ("d8_t40",  40.0, 8.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pasante vertical vs SinkingLength (N013).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, thickness, dia in CASES:
        name = f"N_DL_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=thickness,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drills=[build_drill_spec(
                center_x=150.0, center_y=100.0, diameter=dia,
                plane_name="Top", is_through=True, drill_family="Flat",
                tool_resolution="Auto",
            )],
        )
        try:
            synthesize_request(req)
            print(f"  {path.name}  (espesor={thickness:g}, Ø{dia:g} pasante)")
        except ValueError as exc:
            print(f"  {path.name}  BLOQUEADO por el sintetizador: {exc}")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
