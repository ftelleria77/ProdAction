r"""N038 - Eje B etapa 2: CIRCULOS (fresado circular completo) — lote baseline.

Primer lote de CircleMillingSpec. Disciplina N001: una dimension por fixture, todo Center
(la correccion Interna/Externa, leads y multipaso van en el lote siguiente, con el modelo
base derivado). El ISO nos ensena el modelo de emision de arcos G2/G3 (I/J, arranque,
cierre del circulo, sentido horario/antihorario) — la primitiva de la etapa 3 (polilineas).
POSTPROCESAR TAL CUAL. Si Maestro rechaza alguno (p.ej. el pasante), es dato.
Uso: py -m iso.machining_lab.n038_circle.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_circle_milling_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N038_circle"

def _circ(cx=150.0, cy=100.0, r=30.0, depth=5.0, **kw):
    return build_circle_milling_spec(
        center_x=cx, center_y=cy, radius=r,
        tool_id=kw.pop("tool_id", "1903"), tool_name=kw.pop("tool_name", "E004"),
        tool_width=kw.pop("tool_width", 4.0),
        target_depth=kw.pop("target_depth", depth), **kw)

CASES = [
    ("base",   [_circ()]),                                    # r30 (150,100) prof5 CCW E004
    ("cw",     [_circ(winding="Clockwise")]),                 # sentido horario
    ("r10",    [_circ(r=10.0)]),
    ("r60",    [_circ(r=60.0)]),
    ("prof10", [_circ(depth=10.0)]),
    ("th",     [_circ(target_depth=None, is_through=True, extra_depth=2.0)]),   # pasante (corta un disco)
    ("e001",   [_circ(tool_id="1900", tool_name="E001", tool_width=18.36)]),
    ("pos",    [_circ(cx=70.0, cy=60.0)]),
    ("sec10",  [_circ(security_plane=10.0)]),
    ("two",    [_circ(cx=80.0, cy=100.0, r=25.0), _circ(cx=220.0, cy=100.0, r=25.0)]),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, circles in CASES:
        path = out / f"N_O_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_O_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, circle_millings=list(circles)))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
