"""N028 — MULTI-FRESA: varias líneas con herramientas DISTINTAS en un programa.

El multi-pasada con la MISMA fresa ya está validado (N001 D002: G17/MLV=2/triple G0 entre
pasadas). Falta el CAMBIO DE HERRAMIENTA entre pasadas: ¿repite el header ATC completo
(T/SYN/M06/ETK/S)? ¿retrae a park antes? ¿re-emite el setup MLV1/Or?

Casos (líneas en X a distintas Y, prof. 5 (E004) / 3 (E001)):
  mf_e4_e1    : E004 → E001 (cambio chica→grande)
  mf_e1_e4    : E001 → E004 (cambio grande→chica)
  mf_e4_e4_e1 : E004 → E004 → E001 (mezcla: misma fresa + cambio)

Uso:  py -m iso.machining_lab.n028_router_multitool.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N028_router_multitool\\
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N028_router_multitool"


def _e004(y: float):
    return build_line_milling_spec(
        line_x1=20.0, line_y1=y, line_x2=280.0, line_y2=y,
        line_feature_name="Fresado",
        line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
        line_security_plane=20.0, line_is_through=False, line_target_depth=5.0,
    )


def _e001(y: float):
    return build_line_milling_spec(
        line_x1=20.0, line_y1=y, line_x2=280.0, line_y2=y,
        line_feature_name="Fresado",
        line_tool_id="1900", line_tool_name="E001", line_tool_width=18.36,
        line_security_plane=20.0, line_is_through=False, line_target_depth=3.0,
    )


CASES = [
    ("mf_e4_e1",    [_e004(60.0), _e001(140.0)]),
    ("mf_e1_e4",    [_e001(60.0), _e004(140.0)]),
    ("mf_e4_e4_e1", [_e004(60.0), _e004(100.0), _e001(140.0)]),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-fresa en un programa (N028).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, millings in CASES:
        name = f"N_MF_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=millings,
        )
        synthesize_request(req)
        print(f"  {path.name}  ({' -> '.join(m.tool_name for m in millings)})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
