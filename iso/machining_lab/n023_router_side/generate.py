"""N023 — Corrección de herramienta en el fresado lineal (side_of_feature Left/Right).

La fresa corre desplazada medio ancho respecto de la línea programada. El lado es RELATIVO al
sentido de avance (start→end), por eso se varía también la dirección. Preguntas a responder con
los ISOs: ¿el ISO emite coordenadas ya desplazadas, o corrección del control (G41/G42)?, ¿cómo
juega el SVR (radio) que ya se emite?, ¿signo del offset por lado/dirección?

Casos (E004 ancho 4 → offset esperado 2; línea base (20,100)->(280,100), prof. 5):
  side_c_x     : Center (control, = N022 dir_x)
  side_l_x     : Left  en +X
  side_r_x     : Right en +X
  side_l_xrev  : Left  en -X (línea invertida → ¿el offset se invierte?)
  side_l_y     : Left  en +Y
  side_l_wide  : Left en +X con E001 (ancho 18.36 → offset 9.18; separa offset=width/2 de constante)

Uso:  py -m iso.machining_lab.n023_router_side.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N023_router_side\\
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_line_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N023_router_side"

# (tag, side, x1,y1,x2,y2, tool_id, tool_name, width)
CASES = [
    ("side_c_x",    "Center", 20.0, 100.0, 280.0, 100.0, "1903", "E004", 4.0),
    ("side_l_x",    "Left",   20.0, 100.0, 280.0, 100.0, "1903", "E004", 4.0),
    ("side_r_x",    "Right",  20.0, 100.0, 280.0, 100.0, "1903", "E004", 4.0),
    ("side_l_xrev", "Left",  280.0, 100.0,  20.0, 100.0, "1903", "E004", 4.0),
    ("side_l_y",    "Left",  150.0,  20.0, 150.0, 180.0, "1903", "E004", 4.0),
    ("side_l_wide", "Left",   20.0, 100.0, 280.0, 100.0, "1900", "E001", 18.36),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corrección de herramienta (side) en línea (N023).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, side, x1, y1, x2, y2, tid, tname, w in CASES:
        name = f"N_RS_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=[build_line_spec(
                line_x1=x1, line_y1=y1, line_x2=x2, line_y2=y2,
                line_feature_name="Fresado",
                line_tool_id=tid, line_tool_name=tname, line_tool_width=w,
                line_security_plane=20.0, line_side_of_feature=side,
                line_is_through=False, line_target_depth=5.0,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  ({side}, ({x1:g},{y1:g})->({x2:g},{y2:g}), {tname})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
