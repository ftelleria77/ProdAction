r"""N034 - Multipasada + leads: desambiguar la regla del lead (N029 mp_leads).

Observado con UN solo fixture (Bi cd4, E004 w4, ambos Arc, RM=2, Automatic):
  arco r=2 (=w/2, NO w/2xRM=4) y lado ESPEJADO (-y / G2) vs. single-pass (+y / G3).
La formula esta subdeterminada: r=w/2 constante? f(RM)? y el lado con Uni/lado explicito/
paridad de pasadas? Los leads se RECALCULAN del spec al postprocesar (probado con rm3:
la curva almacenada equivocada NO llego al ISO) -> estos fixtures sintetizados son
referencias genuinas. Postprocesar TAL CUAL.
Uso: py -m iso.machining_lab.n034_router_mp_leads.generate
"""
from __future__ import annotations
import argparse, sys
from dataclasses import replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_line_spec, build_synthesis_request, synthesize_request  # noqa: E402
from pgmx.synthesis.common.leads import build_approach_spec, build_retract_spec  # noqa: E402
from pgmx.synthesis.common.strategy import (  # noqa: E402
    build_bidirectional_milling_strategy_spec,
    build_unidirectional_milling_strategy_spec,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N034_router_mp_leads"

def _bi(cd=4.0):
    return build_bidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=cd)

def _uni(cd=4.0):
    return build_unidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=cd)

def _line(tool="E004", width=4.0, strategy=None, app=None, ret=None):
    tid = {"E004": "1903", "E001": "1900"}[tool]
    base = build_line_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado", line_tool_id=tid, line_tool_name=tool,
        line_tool_width=width, line_security_plane=20.0,
        line_is_through=False, line_target_depth=12.0,
        line_milling_strategy=strategy)
    kw = {}
    if app is not None: kw["approach"] = app
    if ret is not None: kw["retract"] = ret
    return replace(base, **kw) if kw else base

def _arc(rm=2.0, side="Automatic"):
    return build_approach_spec(True, approach_type="Arc", radius_multiplier=rm, arc_side=side)

def _arc_ret(rm=2.0, side="Automatic"):
    return build_retract_spec(True, retract_type="Arc", radius_multiplier=rm, arc_side=side)

CASES = [
    # formula del radio: rm1/rm3 separan r=w/2 constante de r=f(RM); e001 separa la escala en w
    ("mpl_rm1",  _line(strategy=_bi(), app=_arc(rm=1.0), ret=_arc_ret(rm=1.0))),
    ("mpl_rm3",  _line(strategy=_bi(), app=_arc(rm=3.0), ret=_arc_ret(rm=3.0))),
    ("mpl_e001", _line("E001", 18.36, strategy=_bi(), app=_arc(), ret=_arc_ret())),
    # lado del arco: explicito Left/Right (Automatic salio espejado en N029)
    ("mpl_left",  _line(strategy=_bi(), app=_arc(side="Left"), ret=_arc_ret(side="Left"))),
    ("mpl_right", _line(strategy=_bi(), app=_arc(side="Right"), ret=_arc_ret(side="Right"))),
    # conexion Uni y paridad de pasadas (cd6 -> 2 pasadas: la ultima termina en el START)
    ("mpl_uni", _line(strategy=_uni(), app=_arc(), ret=_arc_ret())),
    ("mpl_cd6", _line(strategy=_bi(cd=6.0), app=_arc(), ret=_arc_ret())),
    # un solo extremo
    ("mpl_app_only", _line(strategy=_bi(), app=_arc())),
    ("mpl_ret_only", _line(strategy=_bi(), ret=_arc_ret())),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_ML_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_ML_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, line_millings=[spec]))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
