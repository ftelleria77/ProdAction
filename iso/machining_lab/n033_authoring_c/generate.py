r"""N033 - Validacion de autoria C: ZigZag y atributos on-route con la FORMA MAESTRO completa.

Correccion de N032 (que fallo 0/4): Maestro postprocesa el toolpath ALMACENADO, no regenera
desde la estrategia/atributos; y los OperationAttribute en namespace equivocado se ignoran en
silencio. Ahora se autora identico a los archivos reales (diff estructural 0 vs N025/N022):
  - ZigZag: strokes en rampa en la curva compuesta del TrajectoryPath (entrada en superficie).
  - Cambios on-route: op-attrs en namespace del modelo base con Key real; curva partida en cada
    evento con Z interpolada entre eventos de profundidad; SpeedAttribute a nivel toolpath
    anclado por ElementKey al segmento que arranca en su UPar.
Mismos 4 casos espejo que N032. Postprocesar TAL CUAL.
Uso: py -m iso.machining_lab.n033_authoring_c.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_synthesis_request, synthesize_request  # noqa: E402
from iso.machining_lab.n032_authoring_b.generate import CASES  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N033_authoring_c"

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_C_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_C_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, lines=[spec]))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
