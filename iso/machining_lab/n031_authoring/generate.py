r"""N031 - Validacion de la AUTORIA pgmx ampliada (rebaba/longitud/invertir/CAD/Avanz-Rotacion).

Piezas espejo de referencias conocidas (N023/N024): si Maestro postprocesa nuestra autoria
igual que la suya (mismo cuerpo ISO), el ciclo autoria->Maestro queda probado y ya no dependemos
de toggles manuales. Postprocesar TAL CUAL (sin tocar opciones).

  aut_reb2   : rebaba 2          (~ N024 c_x_reb2)
  aut_long   : correccion en longitud (~ N023 c_x_long)
  aut_invert : invertir trabajo  (~ N023 c_x_invert)
  aut_cad_l  : Izquierda + CAD   (~ N023 l_x_CAD)
  aut_f3s12  : Avanz. 3 + Rotacion 12000 (una linea)

Uso:  py -m iso.machining_lab.n031_authoring.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_line_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N031_authoring"
CASES = [
    ("aut_reb2",   dict(side_offset=2.0)),
    ("aut_long",   dict(is_precise=True)),
    ("aut_invert", dict(invert_work=True)),
    ("aut_cad_l",  dict(side_of_feature="Left", activate_cnc_correction=False)),
    ("aut_f3s12",  dict(feedrate=3.0, spindle=12000.0)),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, extra in CASES:
        path = out / f"N_A_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_A_{tag}", length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            lines=[build_line_spec(
                start_x=20.0, start_y=100.0, end_x=280.0, end_y=100.0,
                feature_name="Fresado", tool_id="1903", tool_name="E004",
                tool_width=4.0, security_plane=20.0,
                is_through=False, target_depth=5.0, **extra)]))
        print(f"  {path.name}")
    print("Postprocesar tal cual; comparar contra las referencias N023/N024 equivalentes.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
