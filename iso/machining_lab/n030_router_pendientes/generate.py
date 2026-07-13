"""N030 — Tanda A de pendientes del fresado lineal (sintetizables).

Destraba guardas y completa definiciones:
  Modos de lead (UI: "En bajada"/"En subida"; solo "En cota" validado):
    ld_app_line_baja : Acercamiento Lineal, modo En bajada (Down)
    ld_app_arc_baja  : Acercamiento Arco,   modo En bajada
    ld_ret_line_sube : Alejamiento Lineal,  modo En subida (Up)
    ld_ret_arc_sube  : Alejamiento Arco,    modo En subida
  Velocidad del Alejamiento (guarda):
    ld_ret_arc_sp    : Alejamiento Arco con Velocidad 10
  Último hueco en Unidireccional (validado solo en Bidireccional):
    mp_uni_cd4_f2    : Uni (salida a cota de seguridad), multipaso, prof. hueco 4, último hueco 2
  Combos con DIAGONAL (guardas; la diagonal base (20,20)->(280,180) ya está validada plana):
    dg_side_l        : corrección de herramienta Izquierda sobre diagonal
    dg_long          : corrección de longitud sobre diagonal
    dg_mp_bi_cd4     : multipaso bidireccional (prof. hueco 4) sobre diagonal (prof. 12)
    dg_app_ret_arc   : acercamiento+alejamiento Arco sobre diagonal

Uso:  py -m iso.machining_lab.n030_router_pendientes.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N030_router_pendientes\\
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
from pgmx.synthesis.common.strategy import (  # noqa: E402
    build_bidirectional_milling_strategy_spec,
    build_unidirectional_milling_strategy_spec,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N030_router_pendientes"

LINE_X = dict(line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0)
DIAG = dict(line_x1=20.0, line_y1=20.0, line_x2=280.0, line_y2=180.0)

CASES = [
    ("ld_app_line_baja", LINE_X, dict(line_target_depth=5.0, line_approach_enabled=True,
                                      line_approach_type="Line", line_approach_mode="Down")),
    ("ld_app_arc_baja",  LINE_X, dict(line_target_depth=5.0, line_approach_enabled=True,
                                      line_approach_type="Arc", line_approach_mode="Down")),
    ("ld_ret_line_sube", LINE_X, dict(line_target_depth=5.0, line_retract_enabled=True,
                                      line_retract_type="Line", line_retract_mode="Up")),
    ("ld_ret_arc_sube",  LINE_X, dict(line_target_depth=5.0, line_retract_enabled=True,
                                      line_retract_type="Arc", line_retract_mode="Up")),
    ("ld_ret_arc_sp",    LINE_X, dict(line_target_depth=5.0, line_retract_enabled=True,
                                      line_retract_type="Arc", line_retract_speed=10.0)),
    ("mp_uni_cd4_f2",    LINE_X, dict(line_target_depth=12.0,
                                      line_milling_strategy=build_unidirectional_milling_strategy_spec(
                                          connection_mode="SafetyHeight", allow_multiple_passes=True,
                                          axial_cutting_depth=4.0, axial_finish_cutting_depth=2.0))),
    ("dg_side_l",        DIAG,   dict(line_target_depth=5.0, line_side_of_feature="Left")),
    ("dg_long",          DIAG,   dict(line_target_depth=5.0)),   # + IsPrecise: NO autorable → ver nota
    ("dg_mp_bi_cd4",     DIAG,   dict(line_target_depth=12.0,
                                      line_milling_strategy=build_bidirectional_milling_strategy_spec(
                                          allow_multiple_passes=True, axial_cutting_depth=4.0))),
    ("dg_app_ret_arc",   DIAG,   dict(line_target_depth=5.0,
                                      line_approach_enabled=True, line_approach_type="Arc",
                                      line_retract_enabled=True, line_retract_type="Arc")),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pendientes sintetizables del fresado (N030).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, geom, extra in CASES:
        name = f"N_P_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=[build_line_spec(
                line_feature_name="Fresado",
                line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
                line_security_plane=20.0, line_is_through=False,
                **geom, **extra,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}")

    print("\nNOTA: dg_long salió SIN IsPrecise (la autoría no lo escribe): activale 'Corrección de")
    print("longitud' en Maestro antes de postprocesar, o descartalo si preferís hacerlo aparte.")
    print("Listo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
