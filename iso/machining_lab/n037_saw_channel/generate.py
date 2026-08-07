r"""N037 - Eje B: CANAL con la Sierra Vertical X (082, cabezal perforador) — lote baseline.

Primer lote de la operacion Canal (SlotSide). Restricciones fisicas (Fermin): cara superior,
direccion X, sentido NEGATIVO (hacia -x), profundidad maxima 10 mm. La 082 va en el mandril 82
del cabezal perforador (shf de spindles.cfg: -96, 128.85, 22.15), Ø120, ancho 3.8/4.
Variaciones de a UNA dimension (disciplina N001): profundidad, posicion Y, largo, sentido
autorado, cota de seguridad, y dos canales en un programa (transiciones del cabezal).
POSTPROCESAR TAL CUAL. Si Maestro rechaza alguno (p.ej. el sentido invertido), es dato.
Uso: py -m iso.machining_lab.n037_saw_channel.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_synthesis_request, synthesize_request  # noqa: E402
from pgmx.synthesis.milling.channel import build_channel_spec  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N037_saw_channel"

def _slot(x1=280.0, y1=100.0, x2=20.0, y2=100.0, **kw):
    # sentido -x por defecto (280 -> 20), la restriccion fisica de la 082
    return build_channel_spec(start_x=x1, start_y=y1, end_x=x2, end_y=y2, **kw)

CASES = [
    ("base",     [_slot(target_depth=5.0)]),
    ("prof2",    [_slot(target_depth=2.0)]),
    ("prof10",   [_slot(target_depth=10.0)]),           # el maximo fisico
    ("y50",      [_slot(y1=50.0, y2=50.0, target_depth=5.0)]),
    ("y150",     [_slot(y1=150.0, y2=150.0, target_depth=5.0)]),
    ("corto",    [_slot(x1=200.0, x2=100.0, target_depth=5.0)]),
    ("xfwd",     [_slot(x1=20.0, x2=280.0, target_depth=5.0)]),   # sentido +x autorado: ver que hace Maestro
    ("sec10",    [_slot(target_depth=5.0, security_plane=10.0)]),
    ("two",      [_slot(y1=60.0, y2=60.0, target_depth=5.0),
                  _slot(y1=140.0, y2=140.0, target_depth=5.0)]),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, slots in CASES:
        path = out / f"N_S_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_S_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, channels=list(slots)))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
