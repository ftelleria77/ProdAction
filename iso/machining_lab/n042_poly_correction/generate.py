r"""N042 - Eje B etapa 3: POLILINEAS con correccion + acercamiento/alejamiento (exploracion).

Barre lo que Fermin senalo como el corazon de la operacion: correccion (SIEMPRE izq/der segun
avance) y forma de INGRESO, POR SEPARADO en abiertas y cerradas. En la cerrada el PUNTO INICIAL
importa (esquina vs medio de segmento) y el sentido puede invertirse.

CAMINO 1 (Fermin 2026-07-09): la autoria guarda la traza NOMINAL; Maestro regenera la compensada
(con arcos de empalme en las esquinas vivas). Este lote lo CONFIRMA: si el ISO sale compensado,
la creencia queda probada. POSTPROCESAR TAL CUAL. Si Maestro rechaza o pide regenerar, foto.

Perfil ABIERTO: linea-arco-linea (todo tangente). Perfil CERRADO: rectangulo con esquinas
superiores redondeadas (base con esquinas VIVAS -> prueba el offset con inglete de Maestro).
Uso: py -m iso.machining_lab.n042_poly_correction.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_polyline_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N042_poly_correction"

# perfil ABIERTO tangente (start (40,60)): sube, cuarto de arco, va a la derecha
OPEN = dict(start=(40.0, 60.0),
            segments=[((40.0, 140.0),),
                      ((100.0, 200.0), (100.0, 140.0), "CounterClockwise"),
                      ((240.0, 200.0),)])
# perfil CERRADO (start esquina (60,40)), esquinas superiores redondeadas, base con esquinas vivas
CLOSED = dict(start=(60.0, 40.0),
              segments=[((240.0, 40.0),), ((240.0, 140.0),),
                        ((200.0, 180.0), (200.0, 140.0), "CounterClockwise"),
                        ((100.0, 180.0),),
                        ((60.0, 140.0), (100.0, 140.0), "CounterClockwise"),
                        ((60.0, 40.0),)])
# CERRADO invertido (mismo contorno, sentido opuesto): sube por la izquierda primero, arcos CW
CLOSED_REV = dict(start=(60.0, 40.0),
                  segments=[((60.0, 140.0),),
                            ((100.0, 180.0), (100.0, 140.0), "Clockwise"),
                            ((200.0, 180.0),),
                            ((240.0, 140.0), (200.0, 140.0), "Clockwise"),
                            ((240.0, 40.0),), ((60.0, 40.0),)])
# CERRADO con punto inicial en el MEDIO de la base (150,40): la base se parte en dos mitades
CLOSED_MID = dict(start=(150.0, 40.0),
                  segments=[((240.0, 40.0),), ((240.0, 140.0),),
                            ((200.0, 180.0), (200.0, 140.0), "CounterClockwise"),
                            ((100.0, 180.0),),
                            ((60.0, 140.0), (100.0, 140.0), "CounterClockwise"),
                            ((60.0, 40.0),), ((150.0, 40.0),)])

def _poly(geom, **kw):
    return build_polyline_spec(
        **geom, tool_id="1903", tool_name="E004", tool_width=4.0,
        target_depth=5.0, **kw)

CASES = [
    # --- ABIERTAS: correccion izq/der, acercamiento ---
    ("open_l",       _poly(OPEN, side_of_feature="Left")),
    ("open_r",       _poly(OPEN, side_of_feature="Right")),
    ("open_app",     _poly(OPEN, approach_enabled=True, approach_type="Arc")),
    ("open_l_app",   _poly(OPEN, side_of_feature="Left", approach_enabled=True, approach_type="Arc")),
    # --- CERRADAS: correccion izq/der (offset con arcos de empalme en esquinas vivas) ---
    ("closed_l",     _poly(CLOSED, side_of_feature="Left")),
    ("closed_r",     _poly(CLOSED, side_of_feature="Right")),
    ("closed_l_rev", _poly(CLOSED_REV, side_of_feature="Left")),   # sentido invertido x lado
    # --- CERRADAS: acercamiento (como ingresa un lazo cerrado) ---
    ("closed_app",   _poly(CLOSED, approach_enabled=True, approach_type="Arc")),
    ("closed_l_app", _poly(CLOSED, side_of_feature="Left", approach_enabled=True, approach_type="Arc")),
    # --- CERRADAS: punto inicial en el MEDIO de un segmento (Fermin: importa!) ---
    ("closed_mid",   _poly(CLOSED_MID)),
    ("closed_l_mid", _poly(CLOSED_MID, side_of_feature="Left")),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        path = out / f"N_T_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_T_{tag}", length=300.0, width=250.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, polyline_millings=[spec]))
        print(f"  {path.name}  (cerrada={spec.is_closed})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
