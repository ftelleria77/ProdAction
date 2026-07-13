r"""N040 - Eje B etapa 2: ARCOS SUELTOS — baseline + validacion de la autoria nueva.

Primer lote de ArcSpec (autoria estrenada 2026-07-08: composite de UN miembro-arco,
forma de las piezas de produccion FrenteCurvo/Modulo Curvo). Doble proposito, patron N031:
(1) si Maestro ACEPTA y postprocesa nuestra autoria, la extension queda validada;
(2) los ISO ensenan el modelo de render del arco suelto (entrada, G2/G3, leads futuros).
Geometria base: arcos sobre centro (150,100) r60, E004, prof 5.
POSTPROCESAR TAL CUAL. Si Maestro rechaza alguno o pide regenerar, foto: es dato.
Uso: py -m iso.machining_lab.n040_arc.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_arc_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N040_arc"

def _arc(x1=210.0, y1=100.0, x2=90.0, y2=100.0, cx=150.0, cy=100.0, **kw):
    return build_arc_spec(
        start_x=x1, start_y=y1, end_x=x2, end_y=y2, center_x=cx, center_y=cy,
        tool_id=kw.pop("tool_id", "1903"), tool_name=kw.pop("tool_name", "E004"),
        tool_width=kw.pop("tool_width", 4.0),
        target_depth=kw.pop("target_depth", 5.0), **kw)

CASES = [
    ("a180",    _arc()),                                              # semicirculo CCW este->oeste
    ("a90",     _arc(x2=150.0, y2=160.0)),                            # cuarto CCW este->norte
    ("a270",    _arc(x2=150.0, y2=40.0)),                             # 3/4 CCW este->sur
    ("a180_cw", _arc(winding="Clockwise")),                           # semicirculo CW (por el sur)
    ("a90_cw",  _arc(x1=150.0, y1=160.0, x2=210.0, y2=100.0, winding="Clockwise")),
    ("prof10",  _arc(target_depth=10.0)),
    ("th",      _arc(target_depth=None, is_through=True, extra_depth=2.0)),
    ("e001",    _arc(tool_id="1900", tool_name="E001", tool_width=18.36)),
    ("pos",     _arc(x1=120.0, y1=60.0, x2=40.0, y2=60.0, cx=80.0, cy=60.0)),   # r40 en (80,60)
    ("two",     None),  # se arma abajo: dos arcos en un programa
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        arcs = ([_arc(cy=60.0, y1=60.0, y2=60.0), _arc(cy=140.0, y1=140.0, y2=140.0)]
                if tag == "two" else [spec])
        path = out / f"N_Q_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_Q_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, arcs=arcs))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
