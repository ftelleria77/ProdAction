"""N026 — Fresado lineal con APPROACH/RETRACT configurables (entrada/salida, lead-in/out).

Distinto del lead fijo de 1 mm de la corrección de herramienta (N023): acá son los leads
programables de la operación (ApproachSpec/RetractSpec): tipo Line/Arc, radio (multiplicador),
velocidad, lado del arco, y solapamiento (overlap) en el retract.

Preguntas: ¿cómo entra/sale la fresa (G2/G3 para el arco)? ¿radio = multiplicador × radio de
fresa? ¿el overlap re-corta el final? ¿la velocidad del lead es propia o la de plunge?

Casos (E004, línea (20,100)->(280,100), ciega prof. 5):
  app_line     : approach Line (defaults: mode Down)
  app_arc      : approach Arc (radius_mult 1.2, arc_side Automatic)
  app_arc_rm2  : approach Arc con radius_multiplier 2.0 (aísla la fórmula del radio)
  app_arc_sp   : approach Arc con speed 10 (¿F propio del lead?)
  ret_arc      : retract Arc
  ret_arc_ov   : retract Arc con overlap 0.25 (¿re-corta 0.25 mm del final?)
  app_ret_arc  : approach Arc + retract Arc (ambos)

Uso:  py -m iso.machining_lab.n026_router_leads.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N026_router_leads\\
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_line_milling_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N026_router_leads"

# (tag, kwargs de build_line_milling_spec para leads)
CASES = [
    ("app_line",    dict(line_approach_enabled=True, line_approach_type="Line")),
    ("app_arc",     dict(line_approach_enabled=True, line_approach_type="Arc")),
    ("app_arc_rm2", dict(line_approach_enabled=True, line_approach_type="Arc",
                         line_approach_radius_multiplier=2.0)),
    ("app_arc_sp",  dict(line_approach_enabled=True, line_approach_type="Arc",
                         line_approach_speed=10.0)),
    ("ret_arc",     dict(line_retract_enabled=True, line_retract_type="Arc")),
    ("ret_arc_ov",  dict(line_retract_enabled=True, line_retract_type="Arc",
                         line_retract_overlap=0.25)),
    ("app_ret_arc", dict(line_approach_enabled=True, line_approach_type="Arc",
                         line_retract_enabled=True, line_retract_type="Arc")),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Approach/retract en fresado lineal (N026).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, lead_kwargs in CASES:
        name = f"N_LD_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=[build_line_milling_spec(
                line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
                line_feature_name="Fresado",
                line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
                line_security_plane=20.0, line_is_through=False, line_target_depth=5.0,
                **lead_kwargs,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
