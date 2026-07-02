"""N024 — Fresado lineal PASANTE (is_through) y PROFUNDIDAD EXTRA (extra_depth).

Preguntas a responder con los ISOs:
- Pasante: ¿el corte baja a -espesor (z=-18)? ¿o hasta la mesa como el taladro vertical?
- extra_depth: ¿baja -(espesor+extra)? (el fresado SÍ puede pasar la cara inferior — corta al
  spoilboard — a diferencia del taladro vertical que paraba en la mesa e ignoraba extra).
- ¿Cambia el plano de seguridad / SVL / plunge respecto del ciego?

Límite: E004 SinkingLength=22; pieza 18 → extra 4 da 22 (borde exacto). extra 2 = 20 (holgado).
Casos (E004, línea (20,100)->(280,100)):
  th_e0 : pasante, extra 0
  th_e2 : pasante, extra 2
  th_e4 : pasante, extra 4 (= sinking exacto; ¿pasa o Maestro se queja?)

Uso:  py -m iso.machining_lab.n024_router_through.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N024_router_through\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N024_router_through"

# (tag, extra_depth)
CASES = [
    ("th_e0", 0.0),
    ("th_e2", 2.0),
    ("th_e4", 4.0),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fresado lineal pasante + extra (N024).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, extra in CASES:
        name = f"N_RTH_{tag}"
        path = out / f"{name}.pgmx"
        try:
            req = build_synthesis_request(
                output_path=path, piece_name=name,
                length=300.0, width=200.0, depth=18.0,
                origin_x=5.0, origin_y=5.0, origin_z=25.0,
                line_millings=[build_line_milling_spec(
                    line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
                    line_feature_name="Fresado",
                    line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
                    line_security_plane=20.0,
                    line_is_through=True, line_extra_depth=extra,
                )],
            )
            synthesize_request(req)
            print(f"  {path.name}  (pasante, extra={extra:g})")
        except ValueError as exc:
            print(f"  {name}  BLOQUEADO por el sintetizador: {exc}")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
