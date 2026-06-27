"""N010 — Topes de feed/spindle por herramienta (override enorme → clamp).

Un agujero por herramienta con feedrate=9.999 (m/min) y spindle=99999 (rpm). El ISO
clampa al máximo de cada tool: el F revela max_feed×1000 y el S revela si el husillo
clampa (y a qué). Flats ciegas D4/5/8/15/20/35 + cónica D5 (tool 007, pasante).

Uso:  py -m iso.machining_lab.n010_tool_limits.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N010_tool_limits\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N010_tool_limits"

BIG_FEED = 9.999      # m/min, muy por encima de cualquier máximo
# Sin override de spindle: 99999 rpm es 'S no válida' en ChkPgm (Maestro NO clampa el
# husillo, lo rechaza). El spindle se usa directo dentro del rango válido. Aislamos max_feed.

# (etiqueta, diámetro, pasante, family) — cónica D5 requiere pasante.
CASES = [
    ("d4",   4.0,  False, None),
    ("d5",   5.0,  False, None),
    ("d8",   8.0,  False, None),
    ("d15", 15.0,  False, None),
    ("d20", 20.0,  False, None),
    ("d35", 35.0,  False, None),
    ("conic5", 5.0, True, None),   # D5 + pasante → cónica (tool 007)
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Topes feed/spindle por tool (N010).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, dia, through, family in CASES:
        name = f"N_TL_{tag}"
        path = out / f"{name}.pgmx"
        kw = dict(is_through=True) if through else dict(target_depth=10.0)
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[build_drilling_spec(
                center_x=150.0, center_y=100.0, diameter=dia,
                plane_name="Top", drill_family=family, tool_resolution="Auto",
                feedrate=BIG_FEED, **kw,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}  (Ø{dia:g}{', pasante' if through else ''})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
