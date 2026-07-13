r"""N036 - Cierre TOTAL de guardas fixtureables del fresado lineal.

POSTPROCESAR TAL CUAL, salvo los 4 marcados [REGEN]: mp_vel, zz_diag, zz_uh0, strat_single —
para esos, ABRIR la operacion en Maestro, REGENERAR el recorrido (tocar la op y aceptar) y
GUARDAR antes de postprocesar (son formas de trayectoria: el toolpath almacenado manda y el
nuestro puede no ser la forma que genera Maestro; los demas son features de postprocesador o
leads, que Maestro recalcula del spec — N034 rm3).

Grupos: CAD+combos, invertir+combos, cambios de recorrido con precise/lado/estrategia,
pasante con estrategia/leads, ZigZag (diagonal, uh=0, leads variantes), leads residuales
(alejamiento Lineal / velocidad, Lineal En bajada, triple Right/velocidad), estrategia sin
multipaso, y programas MULTI-fresado (lado / estrategia / leads).
Uso: py -m iso.machining_lab.n036_router_guards_b.generate
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
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N036_router_guards_b"

BI = build_bidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=4.0)
BI_SINGLE = build_bidirectional_milling_strategy_spec(allow_multiple_passes=False)
ZZ = ZigZagMillingStrategySpec(allow_multiple_passes=True, feed_cutting_depth=2.0,
                               return_cutting_depth=3.0, axial_finish_cutting_depth=1.0)
ZZ_UH0 = ZigZagMillingStrategySpec(allow_multiple_passes=True, feed_cutting_depth=2.0,
                                   return_cutting_depth=3.0, axial_finish_cutting_depth=0.0)

def _line(depth=5.0, strategy=None, side="Center", through=False, y=100.0, x2=280.0, y2=None, **kw):
    base = build_line_spec(
        line_x1=20.0, line_y1=y, line_x2=x2, line_y2=(y if y2 is None else y2),
        line_feature_name="Fresado", line_tool_id="1903", line_tool_name="E004",
        line_tool_width=4.0, line_security_plane=20.0,
        line_is_through=through, line_target_depth=(None if through else depth),
        line_extra_depth=(2.0 if through else 0.0),
        line_milling_strategy=strategy, line_side_of_feature=side)
    return replace(base, **kw) if kw else base

def _app(**kw): return build_approach_spec(True, approach_type=kw.pop("type", "Arc"), **kw)
def _ret(**kw): return build_retract_spec(True, retract_type=kw.pop("type", "Arc"), **kw)

VEL = ((0.3, 1.0),)

CASES = [
    # --- CAD (ACC=false + lado) + combos ---
    ("cad_reb2",  _line(side="Left", activate_cnc_correction=False, side_offset=2.0)),
    ("cad_long",  _line(side="Left", activate_cnc_correction=False, is_precise=True)),
    ("cad_leads", _line(side="Left", activate_cnc_correction=False, approach=_app(), retract=_ret())),
    ("cad_vel",   _line(side="Left", activate_cnc_correction=False, speed_changes=VEL)),
    ("cad_th",    _line(side="Left", activate_cnc_correction=False, through=True)),
    # --- Invertir trabajo + combos ---
    ("inv_vel",   _line(invert_work=True, speed_changes=VEL)),
    ("inv_mp",    _line(depth=12.0, strategy=BI, invert_work=True)),
    ("inv_long",  _line(invert_work=True, is_precise=True)),
    ("inv_reb2",  _line(invert_work=True, side_offset=2.0)),
    ("inv_cad",   _line(side="Left", activate_cnc_correction=False, invert_work=True)),
    # --- Cambios de recorrido con precise / lado / estrategia ---
    ("long_vel",  _line(is_precise=True, speed_changes=VEL)),
    ("side_vel",  _line(side="Left", speed_changes=VEL)),
    # mp_vel ELIMINADO: Maestro prohibe estrategia + atributos asociados (error de UI,
    # 2026-07-07) -> guarda PERMANENTE en _validation, no fixtureable.
    # --- Pasante con estrategia / leads ---
    ("mp_th",     _line(strategy=BI, through=True)),
    ("leads_th",  _line(through=True, approach=_app(), retract=_ret())),
    # --- ZigZag: diagonal, uh=0, leads variantes ---
    ("zz_diag",   _line(depth=12.0, strategy=ZZ, y=20.0, y2=180.0)),           # [REGEN]
    ("zz_uh0",    _line(depth=12.0, strategy=ZZ_UH0)),                         # [REGEN]
    ("zz_app_line", _line(depth=12.0, strategy=ZZ, approach=_app(type="Line"))),
    ("zz_app_down", _line(depth=12.0, strategy=ZZ, approach=_app(mode="Down"))),
    ("zz_ret_up",   _line(depth=12.0, strategy=ZZ, retract=_ret(mode="Up"))),
    ("zz_app_sp",   _line(depth=12.0, strategy=ZZ, approach=_app(speed=3.0))),
    # --- Leads residuales ---
    ("mp_ret_line",       _line(depth=12.0, strategy=BI, retract=_ret(type="Line"))),
    ("mp_ret_sp",         _line(depth=12.0, strategy=BI, retract=_ret(speed=3.0))),
    ("mp_app_line_down",  _line(depth=12.0, strategy=BI, approach=_app(type="Line", mode="Down"))),
    ("side_ret_line",     _line(side="Left", retract=_ret(type="Line"))),
    ("side_app_line_down", _line(side="Left", approach=_app(type="Line", mode="Down"))),
    ("mp_sider_leads",    _line(depth=12.0, strategy=BI, side="Right",
                                activate_cnc_correction=False, approach=_app(), retract=_ret())),
    ("mp_side_leads_sp",  _line(depth=12.0, strategy=BI, side="Left",
                                activate_cnc_correction=False, approach=_app(speed=3.0))),
    # --- Estrategia sin multipaso ---
    ("strat_single", _line(depth=12.0, strategy=BI_SINGLE)),                   # [REGEN]
]

MULTI = [
    # --- Programas con VARIOS fresados (guardas de converter.py) ---
    ("two_side",  [_line(side="Left", y=80.0), _line(side="Left", y=120.0)]),
    ("two_mp",    [_line(depth=12.0, strategy=BI, y=80.0), _line(depth=12.0, strategy=BI, y=120.0)]),
    ("two_leads", [_line(approach=_app(), y=80.0), _line(approach=_app(), y=120.0)]),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_H_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_H_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, line_millings=[spec]))
        print(f"  {path.name}")
    for tag, specs in MULTI:
        path = out / f"N_H_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_H_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, line_millings=list(specs)))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
