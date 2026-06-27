"""N007 — Top drill cónico (tool 007, D5 punta cónica) + control plano.

El sintetizador elige tool 007 automáticamente en D5 + pasante. Variamos espesor
para ver si z_cut del cónico escala con la geometría (¿para en mesa como el plano,
o baja por la punta?). El caso de control fuerza punta plana (drill_family="Flat")
en D5 pasante (tool 005) para contraste.

Uso:  py -m iso.machining_lab.n007_top_conical.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N007_top_conical\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N007_top_conical"

# (etiqueta, espesor, drill_family) — None = auto (D5+pasante -> Conical tool 007).
CASES = [
    ("conic_t18", 18.0, None),     # cónico auto, espesor 18
    ("conic_t25", 25.0, None),     # cónico auto, espesor 25 (¿z_cut escala?)
    ("conic_t12", 12.0, None),     # cónico auto, espesor 12
    ("flat_t18",  18.0, "Flat"),   # control: D5 pasante PLANO (tool 005)
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Top drill cónico D5 (N007).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, thickness, family in CASES:
        name = f"N_CN_{tag}_d5"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=thickness,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[build_drilling_spec(
                center_x=150.0, center_y=100.0, diameter=5.0,
                plane_name="Top", is_through=True, drill_family=family,
                tool_resolution="Auto",
            )],
        )
        synthesize_request(req)
        fam = family or "auto(Conical)"
        print(f"  {path.name}  (espesor={thickness:g}, family={fam})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
