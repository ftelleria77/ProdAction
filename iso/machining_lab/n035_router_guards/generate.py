r"""N035 - Cierre de guardas del fresado lineal (todas las formas nunca fixtureadas).

Cubre: Uni+lado, ZigZag+lado, ZigZag+leads, triple multipaso+lado+leads, y las variantes de
lead con lado C.N. o multipasada (Lineal / En bajada / En subida / velocidad propia / lado
explicito del arco / RM<1). Los leads se RECALCULAN del spec al postprocesar (probado en N034
rm3) -> referencias genuinas; los casos estrategia+lado usan la convencion de desplazamiento
cross-validada (N023 CAD de UI + th_side_l). Postprocesar TAL CUAL.
Uso: py -m iso.machining_lab.n035_router_guards.generate
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
    ZigZagMillingStrategySpec,
    build_bidirectional_milling_strategy_spec,
    build_unidirectional_milling_strategy_spec,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N035_router_guards"

BI = build_bidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=4.0)
UNI = build_unidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=4.0)
ZZ = ZigZagMillingStrategySpec(allow_multiple_passes=True, feed_cutting_depth=2.0,
                               return_cutting_depth=3.0, axial_finish_cutting_depth=1.0)

def _line(depth=12.0, strategy=None, side="Center", **kw):
    base = build_line_spec(
        start_x=20.0, start_y=100.0, end_x=280.0, end_y=100.0,
        feature_name="Fresado", tool_id="1903", tool_name="E004",
        tool_width=4.0, security_plane=20.0,
        is_through=False, target_depth=depth,
        milling_strategy=strategy, side_of_feature=side)
    return replace(base, **kw) if kw else base

def _app(**kw): return build_approach_spec(True, approach_type=kw.pop("type", "Arc"), **kw)
def _ret(**kw): return build_retract_spec(True, retract_type=kw.pop("type", "Arc"), **kw)

CASES = [
    # A. estrategia no-Bi + lado (ACC=false lo fuerza la estrategia)
    ("uni_side_l", _line(strategy=UNI, side="Left")),
    ("zz_side_l",  _line(strategy=ZZ, side="Left")),
    # B. ZigZag + leads (Center)
    ("zz_leads",   _line(strategy=ZZ, approach=_app(), retract=_ret())),
    # C. triple: multipaso + lado + leads
    ("mp_side_leads", _line(strategy=BI, side="Left", approach=_app(), retract=_ret())),
    # D. lado C.N. + variantes de lead (single-pass, prof 5)
    ("side_app_line",    _line(depth=5.0, side="Left", approach=_app(type="Line"))),
    ("side_app_down",    _line(depth=5.0, side="Left", approach=_app(mode="Down"))),
    ("side_ret_up",      _line(depth=5.0, side="Left", retract=_ret(mode="Up"))),
    ("side_app_sp",      _line(depth=5.0, side="Left", approach=_app(speed=2.0))),
    ("side_app_arcleft", _line(depth=5.0, side="Left", approach=_app(arc_side="Left"))),
    # E. multipasada + variantes de lead (Center)
    ("mp_app_line", _line(strategy=BI, approach=_app(type="Line"))),
    ("mp_app_down", _line(strategy=BI, approach=_app(mode="Down"))),
    ("mp_ret_up",   _line(strategy=BI, retract=_ret(mode="Up"))),
    ("mp_app_sp",   _line(strategy=BI, approach=_app(speed=2.0))),
    ("mp_rm05",     _line(strategy=BI, approach=_app(radius_multiplier=0.5))),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_G_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_G_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, lines=[spec]))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
