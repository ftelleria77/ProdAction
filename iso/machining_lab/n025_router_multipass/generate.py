"""N025 — Fresado lineal con estrategia MULTIPASADA en Z (desbaste por capas).

Preguntas a responder con los ISOs:
- ¿Cómo reparte Maestro las pasadas? (12/cd4 → ¿3 iguales? 12/cd5 → ¿5/5/2 o ceil iguales?)
- ¿Qué hace la pasada de terminación (finish_cutting_depth)?
- Bidireccional: ¿alterna el sentido por pasada? ¿cómo re-posiciona?
- Unidireccional: los 3 modos de conexión (Automatic / SafetyHeight / InPiece).

Casos (E004, línea (20,100)->(280,100), ciega prof. 12):
  bi_cd4        : bidireccional, pasada 4       → ¿3 pasadas?
  bi_cd5        : bidireccional, pasada 5       → ¿reparto de 12/5?
  bi_cd5_f2     : bidireccional, pasada 5, terminación 2
  uni_auto_cd4  : unidireccional Automatic, pasada 4
  uni_safe_cd4  : unidireccional SafetyHeight (salida a cota de seguridad), pasada 4
  uni_piece_cd4 : unidireccional InPiece (en la pieza), pasada 4

Uso:  py -m iso.machining_lab.n025_router_multipass.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N025_router_multipass\\
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
from pgmx.synthesis.common.strategy import (  # noqa: E402
    build_bidirectional_milling_strategy_spec,
    build_unidirectional_milling_strategy_spec,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N025_router_multipass"


def _bi(cd: float, finish: float = 0.0):
    return build_bidirectional_milling_strategy_spec(
        allow_multiple_passes=True, axial_cutting_depth=cd, axial_finish_cutting_depth=finish)


def _uni(mode: str, cd: float):
    return build_unidirectional_milling_strategy_spec(
        connection_mode=mode, allow_multiple_passes=True,
        axial_cutting_depth=cd, axial_finish_cutting_depth=0.0)


CASES = [
    ("bi_cd4",        _bi(4.0)),
    ("bi_cd5",        _bi(5.0)),
    ("bi_cd5_f2",     _bi(5.0, 2.0)),
    ("uni_auto_cd4",  _uni("Automatic", 4.0)),
    ("uni_safe_cd4",  _uni("SafetyHeight", 4.0)),
    ("uni_piece_cd4", _uni("InPiece", 4.0)),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multipasada Z en fresado lineal (N025).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, strategy in CASES:
        name = f"N_MP_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=[build_line_milling_spec(
                line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
                line_feature_name="Fresado",
                line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
                line_security_plane=20.0, line_is_through=False, line_target_depth=12.0,
                line_milling_strategy=strategy,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
