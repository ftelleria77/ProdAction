r"""N032 - Validacion de autoria B: ZigZag y atributos de recorrido (sin curvas partidas).

Hipotesis (apoyada por N031): Maestro REGENERA los toolpaths al postprocesar -> basta autorar el
nodo de estrategia / los OperationAttribute, sin partir las curvas almacenadas. Espejos de refs:
  aut_zz    : ZigZag pa2/pr3/uh1, prof 12   (~ N025 zigzag)
  aut_vel   : cambio velocidad 0.3->1, E001 prof 3   (~ N022 Vel)
  aut_prof  : cambio profundidad 0.25->5, E001 prof 3 (~ N022 Prof)
  aut_multi : 2 rampas + 2 velocidades, E001 prof 3   (~ op de N028 _coment)
Postprocesar TAL CUAL.  Uso: py -m iso.machining_lab.n032_authoring_b.generate
"""
from __future__ import annotations
import argparse, sys
from dataclasses import replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_line_spec, build_synthesis_request, synthesize_request  # noqa: E402
from pgmx.synthesis.common.strategy import ZigZagMillingStrategySpec  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N032_authoring_b"

def _line(tool, width, depth, **kw):
    tid = {"E004": "1903", "E001": "1900"}[tool]
    return build_line_spec(
        start_x=20.0, start_y=100.0, end_x=280.0, end_y=100.0,
        feature_name="Fresado", tool_id=tid, tool_name=tool,
        tool_width=width, security_plane=20.0,
        is_through=False, target_depth=depth, **kw)

ZZ = ZigZagMillingStrategySpec(allow_multiple_passes=True, feed_cutting_depth=2.0,
                               return_cutting_depth=3.0, axial_finish_cutting_depth=1.0)
CASES = [
    ("aut_zz",    _line("E004", 4.0, 12.0, milling_strategy=ZZ)),
    ("aut_vel",   replace(_line("E001", 18.36, 3.0), speed_changes=((0.3, 1.0),))),
    ("aut_prof",  replace(_line("E001", 18.36, 3.0), depth_changes=((0.25, 5.0),))),
    ("aut_multi", replace(_line("E001", 18.36, 3.0),
                          speed_changes=((0.25, 1.0), (0.75, 5.0)),
                          depth_changes=((0.2, 13.0), (0.8, 3.0)))),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_B_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_B_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, lines=[spec]))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
