"""N022 — Ampliar/consolidar el fresado en línea (router): TODAS las fresas + dirección/sentido.

Hoy el router está atado a E004 (ROUTER_ETK6/ATC_SLOT/TLC/SPINDLE/SHF constantes) y la línea solo
corta en X (`G1 X{end_x}`, Y fijo). Este lote deriva las dos generalizaciones:

Parte A — barrido de FRESAS (misma línea en X, depth 3): E001-E007. Revela por fresa el slot de
  cambio (T), ETK[6/9/18], TLC, spindle, SHF y feeds (plunge/cut). tool_id: E001=1900 … E007=1906.
Parte B — DIRECCIÓN y SENTIDO de la línea (con E004, depth 5): X (control), Y, diagonal, X-invertida.
  Revela cómo generaliza la trayectoria (G1 X..Y.. al end) y el sentido (start→end vs reverso).

⚠️ Fresas grandes (E002=100, E005=76, E006=80): puede que Maestro rechace algunas para line milling
   (son de perfil/canto). Si alguna falla, es dato (soportamos las line-millables).

Uso:  py -m iso.machining_lab.n022_router_expand.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N022_router_expand\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N022_router_expand"

# Parte A — (tag, tool_id, tool_name, width)  línea en X (20,100)->(280,100), depth 3.
# TODAS las herramientas del cabezal: el converter no distingue tipo (decisión de Fermín). E002 es
# Sierra Horizontal pero se programa igual que una fresa en una línea (uso = responsabilidad del
# programador). Se relajó la validación del sintetizador para line milling (milling/_common.py).
CUTTERS = [
    ("E001", "1900", "E001", 18.36),   # Fresa 90° Widea 18
    ("E002", "1901", "E002", 100.0),   # Sierra Horizontal (se usa como fresa en línea)
    ("E003", "1902", "E003", 9.52),    # Freza Compresión (Violeta)
    ("E005", "1904", "E005", 76.0),    # Fresa 45°
    ("E006", "1905", "E006", 80.0),    # Fresa 0° Rectificado
    ("E007", "1906", "E007", 17.72),   # Fresa 90° Recta 50
]
# Parte B — (tag, x1,y1,x2,y2)  fresa E004, depth 5
DIRECTIONS = [
    ("dir_x",    20.0, 100.0, 280.0, 100.0),   # control (= N001 D001)
    ("dir_y",   150.0,  20.0, 150.0, 180.0),   # línea en Y
    ("dir_diag", 20.0,  20.0, 280.0, 180.0),   # diagonal
    ("dir_xrev",280.0, 100.0,  20.0, 100.0),   # X invertida (sentido opuesto)
]


def _line(out: Path, name: str, tool_id: str, tool_name: str, width: float,
          x1: float, y1: float, x2: float, y2: float, depth: float) -> None:
    path = out / f"{name}.pgmx"
    spec = build_line_spec(
        line_x1=x1, line_y1=y1, line_x2=x2, line_y2=y2,
        line_feature_name="Fresado",
        line_tool_id=tool_id, line_tool_name=tool_name, line_tool_width=width,
        line_security_plane=20.0, line_side_of_feature="Center",
        line_is_through=False, line_target_depth=depth,
    )
    req = build_synthesis_request(
        output_path=path, piece_name=name,
        length=300.0, width=200.0, depth=18.0,
        origin_x=5.0, origin_y=5.0, origin_z=25.0,
        line_millings=[spec],
    )
    synthesize_request(req)
    print(f"  {path.name}  ({tool_name}, ({x1:g},{y1:g})->({x2:g},{y2:g}), d={depth:g})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Router: todas las fresas + dirección (N022).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, tid, tname, w in CUTTERS:
        _line(out, f"N_RT_{tag}", tid, tname, w, 20.0, 100.0, 280.0, 100.0, 3.0)
    for tag, x1, y1, x2, y2 in DIRECTIONS:
        _line(out, f"N_RT_{tag}", "1903", "E004", 4.0, x1, y1, x2, y2, 5.0)

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
