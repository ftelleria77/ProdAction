r"""N029 - Combos de guardas restantes + Invertir trabajo x arcos de Acercamiento/Alejamiento.

Sintetizables directo (postprocesar tal cual):
  cmb_side_l_leads : correccion Izquierda (C.N.) + acercamiento y alejamiento en Arco
  cmb_mp_side_l    : multipaso bidireccional (hueco 4) + correccion Izquierda, prof. 12
  cmb_mp_leads     : multipaso bidireccional + acercamiento/alejamiento Arco
  cmb_th_side_l    : pasante + extra 2 + correccion Izquierda

Requieren TILDAR UNA OPCION en Maestro antes de postprocesar (esta en el nombre):
  inv_app_ret_arc  : leads Arco -> tildar "Invertir trabajo"  (el arco: G3->G2?)
  inv_side_l_app   : Izquierda + acercamiento Arco -> tildar "Invertir trabajo"
  reb2_long        : linea limpia -> tildar "Correccion en longitud" + Rebaba 2 (acorte w/2 o SVR?)
  cad_diag         : diagonal -> elegir Izquierda + "Correccion CAD"
  f9_tope          : linea limpia -> Avanz. 9 (tope E004=5: clampa o error?)

Uso:  py -m iso.machining_lab.n029_router_combos.generate
Salida: S:/Maestro/Projects/ProdAction/N029_router_combos/
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_line_milling_spec, build_synthesis_request, synthesize_request  # noqa: E402
from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N029_router_combos"
X = dict(line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0)
DIAG = dict(line_x1=20.0, line_y1=20.0, line_x2=280.0, line_y2=180.0)
ARC = dict(line_approach_enabled=True, line_approach_type="Arc",
           line_retract_enabled=True, line_retract_type="Arc")
MP = build_bidirectional_milling_strategy_spec(allow_multiple_passes=True, axial_cutting_depth=4.0)
CASES = [
    ("cmb_side_l_leads", X, dict(line_target_depth=5.0, line_side_of_feature="Left", **ARC)),
    ("cmb_mp_side_l",    X, dict(line_target_depth=12.0, line_side_of_feature="Left",
                                 line_milling_strategy=MP)),
    ("cmb_mp_leads",     X, dict(line_target_depth=12.0, line_milling_strategy=MP, **ARC)),
    ("cmb_th_side_l",    X, dict(line_is_through=True, line_extra_depth=2.0,
                                 line_side_of_feature="Left")),
    ("inv_app_ret_arc",  X, dict(line_target_depth=5.0, **ARC)),
    ("inv_side_l_app",   X, dict(line_target_depth=5.0, line_side_of_feature="Left",
                                 line_approach_enabled=True, line_approach_type="Arc")),
    ("reb2_long",        X, dict(line_target_depth=5.0)),
    ("cad_diag",         DIAG, dict(line_target_depth=5.0)),
    ("f9_tope",          X, dict(line_target_depth=5.0)),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, geom, extra in CASES:
        kw = dict(line_feature_name="Fresado", line_tool_id="1903", line_tool_name="E004",
                  line_tool_width=4.0, line_security_plane=20.0)
        if "line_is_through" not in extra: kw["line_is_through"] = False
        path = out / f"N_C_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_C_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            line_millings=[build_line_milling_spec(**geom, **kw, **extra)]))
        print(f"  {path.name}")
    print("OJO: inv_*/reb2_long/cad_diag/f9_tope requieren tocar la opcion en Maestro (docstring).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
