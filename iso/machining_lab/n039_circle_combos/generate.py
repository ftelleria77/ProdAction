r"""N039 - Eje B etapa 2: combos del CIRCULO (correccion, estrategias, leads).

Sobre el base de N038 (E004, r30 en (150,100), prof 5), una dimension por fixture:
- Correccion Interna/Externa (side Left/Right — el ISO dira cual es cual), con sentido
  horario, con pasante y con leads.
- Estrategias sobre contorno cerrado: Bi, Uni (conexiones en cerrado!), ZigZag y HELICOIDAL
  (fallo en lineas: el circulo es su caso natural — si Maestro la rechaza, es dato).
- Leads: arco, ambos, lineal, y sobre multipasada.
POSTPROCESAR TAL CUAL. Si Maestro rechaza alguno, es dato (foto del error).
Uso: py -m iso.machining_lab.n039_circle_combos.generate
"""
from __future__ import annotations
import argparse, sys
from dataclasses import replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_circle_spec, build_synthesis_request, synthesize_request  # noqa: E402
from pgmx.synthesis.common.leads import build_approach_spec, build_retract_spec  # noqa: E402
from pgmx.synthesis.common.strategy import (  # noqa: E402
    build_bidirectional_milling_strategy_spec,
    build_helical_milling_strategy_spec,
    build_unidirectional_milling_strategy_spec,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N039_circle_combos"

BI = build_bidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=4.0)
UNI = build_unidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=4.0)
HELI = build_helical_milling_strategy_spec(axial_cutting_depth=4.0)

def _circ(depth=5.0, **kw):
    strategy = kw.pop("strategy", None)
    base = build_circle_spec(
        center_x=150.0, center_y=100.0, radius=30.0,
        tool_id="1903", tool_name="E004", tool_width=4.0,
        target_depth=kw.pop("target_depth", depth),
        is_through=kw.pop("is_through", None), extra_depth=kw.pop("extra_depth", None),
        milling_strategy=strategy)
    return replace(base, **kw) if kw else base

def _app(**kw): return build_approach_spec(True, approach_type=kw.pop("type", "Arc"), **kw)
def _ret(**kw): return build_retract_spec(True, retract_type=kw.pop("type", "Arc"), **kw)

CASES = [
    # correccion Interna/Externa
    ("side_l",       _circ(side_of_feature="Left")),
    ("side_r",       _circ(side_of_feature="Right")),
    ("side_l_cw",    _circ(side_of_feature="Left", winding="Clockwise")),
    ("side_l_th",    _circ(side_of_feature="Left", target_depth=None, is_through=True, extra_depth=2.0)),
    # estrategias sobre contorno cerrado
    ("mp_bi",        _circ(depth=12.0, strategy=BI)),
    ("mp_uni",       _circ(depth=12.0, strategy=UNI)),
    # zz: la lista blanca del sintetizador no admite ZigZag en circulos (allowlist del lab);
    # si la UI lo ofrece para circulos, extender la autoria y fixturear despues.
    ("heli",         _circ(depth=12.0, strategy=HELI)),
    # leads
    ("app_arc",      _circ(approach=_app())),
    ("app_ret_arc",  _circ(approach=_app(), retract=_ret())),
    ("app_line",     _circ(approach=_app(type="Line"))),
    ("mp_leads",     _circ(depth=12.0, strategy=BI, approach=_app(), retract=_ret())),
    ("side_l_leads", _circ(side_of_feature="Left", approach=_app(), retract=_ret())),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_P_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_P_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, circle_millings=[spec]))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
