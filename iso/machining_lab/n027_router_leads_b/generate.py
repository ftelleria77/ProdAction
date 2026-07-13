"""N027 — Tanda B: desambiguar leads (N026) y pasada de terminación (N025).

Ambigüedades a resolver:
- ¿El lead (largo de entrada recta / radio del arco = 4 con E004) es `tool_width` o constante?
  → repetir con E001 (width 18.36): si el ISO da 18.36, es width; si da 4, es constante.
- ¿"Automatic" del arc_side siempre cae a la IZQUIERDA del avance? → variar dirección (Y, X
  invertida) y probar arc_side explícito Left/Right.
- ¿retract tipo Line? (N026 solo probó retract Arc.)
- Finish de multipasada: cd4 finish2 sobre prof. 12 separa las semánticas: "resto" daría
  -4/-8/-12 (3 pasadas); "desbaste hasta total-finish y pasada final" daría -4/-8/-10/-12 (4).

Casos:
  ld_app_line_e001 : approach Line con E001    → ¿largo 18.36 o 4?
  ld_app_arc_e001  : approach Arc con E001     → ¿radio 18.36 o 4?
  ld_app_arc_y     : approach Arc en línea +Y  → dirección del arco
  ld_app_arc_xrev  : approach Arc en línea -X  → sentido
  ld_app_arc_left  : approach Arc arc_side=Left
  ld_app_arc_right : approach Arc arc_side=Right
  ld_ret_line      : retract Line
  mp_bi_cd4_f2     : bidireccional cd 4, terminación 2, prof. 12

Uso:  py -m iso.machining_lab.n027_router_leads_b.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N027_router_leads_b\\
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
from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N027_router_leads_b"

E004 = dict(line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0)
E001 = dict(line_tool_id="1900", line_tool_name="E001", line_tool_width=18.36)
LINE_X = dict(line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0)
LINE_Y = dict(line_x1=150.0, line_y1=20.0, line_x2=150.0, line_y2=180.0)
LINE_XREV = dict(line_x1=280.0, line_y1=100.0, line_x2=20.0, line_y2=100.0)

# (tag, geom, tool, extra kwargs)
CASES = [
    ("ld_app_line_e001", LINE_X, E001, dict(line_approach_enabled=True, line_approach_type="Line",
                                            line_target_depth=3.0)),
    ("ld_app_arc_e001",  LINE_X, E001, dict(line_approach_enabled=True, line_approach_type="Arc",
                                            line_target_depth=3.0)),
    ("ld_app_arc_y",     LINE_Y, E004, dict(line_approach_enabled=True, line_approach_type="Arc",
                                            line_target_depth=5.0)),
    ("ld_app_arc_xrev",  LINE_XREV, E004, dict(line_approach_enabled=True, line_approach_type="Arc",
                                               line_target_depth=5.0)),
    ("ld_app_arc_left",  LINE_X, E004, dict(line_approach_enabled=True, line_approach_type="Arc",
                                            line_approach_arc_side="Left", line_target_depth=5.0)),
    ("ld_app_arc_right", LINE_X, E004, dict(line_approach_enabled=True, line_approach_type="Arc",
                                            line_approach_arc_side="Right", line_target_depth=5.0)),
    ("ld_ret_line",      LINE_X, E004, dict(line_retract_enabled=True, line_retract_type="Line",
                                            line_target_depth=5.0)),
    # OJO: el default de radius_multiplier con lead HABILITADO es 2.0 (no 1.2) — el "rm2" de N026
    # no varió nada. Hipótesis: lead = (width/2)×RM → rm3 con E004 daría 6.
    ("ld_app_arc_rm3",   LINE_X, E004, dict(line_approach_enabled=True, line_approach_type="Arc",
                                            line_approach_radius_multiplier=3.0,
                                            line_target_depth=5.0)),
    # Overlap 0.25 dio ISO idéntico: ¿solo aplica a contornos cerrados, o 0.25 era muy chico?
    ("ld_ret_arc_ov5",   LINE_X, E004, dict(line_retract_enabled=True, line_retract_type="Arc",
                                            line_retract_overlap=5.0, line_target_depth=5.0)),
    ("mp_bi_cd4_f2",     LINE_X, E004, dict(line_target_depth=12.0,
                                            line_milling_strategy=build_bidirectional_milling_strategy_spec(
                                                allow_multiple_passes=True, axial_cutting_depth=4.0,
                                                axial_finish_cutting_depth=2.0))),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tanda B leads + finish (N027).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for tag, geom, tool, extra in CASES:
        name = f"N_{tag}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path, piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=[build_line_spec(
                line_feature_name="Fresado", line_security_plane=20.0, line_is_through=False,
                **geom, **tool, **extra,
            )],
        )
        synthesize_request(req)
        print(f"  {path.name}")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
