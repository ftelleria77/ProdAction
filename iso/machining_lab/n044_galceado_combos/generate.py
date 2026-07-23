r"""N044 - Eje B etapa 4: pendientes del Galceado/Perfilado/Escuadrado (post-N043).

Tres grupos (ver iso/docs/experiments/galceado_perfilado.md, seccion Pendientes):

1. CN + leads LINE sobre contorno cerrado (la op2 de Galceado.pgmx usa Line/Down + Line/Up
   con RM=4): POSTPROCESAR TAL CUAL — la traza nominal la regenera Maestro del spec.
2. Forma EN-JUEGO (ContourSpec: arranque a MITAD de borde, leads Arc RM=2): POSTPROCESAR TAL
   CUAL — le da fixture al contour que autora la App (hoy el converter lo rechaza).
3. CAD (ActivateCNCCorrection=false): ⚠️ con ACC=false Maestro postprocesa la traza ALMACENADA
   — la que autoramos es NUESTRA hipotesis (regla 5 de CLAUDE.md: seria circular). Antes de
   postprocesar cada uno: ABRIR la operacion en Maestro, ACEPTAR (regenerar la trayectoria) y
   GUARDAR. En cad_zigzag ademas hay que AGREGAR la estrategia en la UI (la estrategia fuerza
   ACC=false sola — regla N029/N035).

El generador deja un INSTRUCCIONES.md en la carpeta de salida con la accion por archivo.
Uso: py -m iso.machining_lab.n044_galceado_combos.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import (  # noqa: E402
    build_contour_spec, build_polyline_spec, build_synthesis_request, synthesize_request,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N044_galceado_combos"

# Contexto de N043: pieza 300x300x18, E003 (w=9.52), ciego -9, security 30, origen 0/0/0.
PIECE = dict(length=300.0, width=300.0, depth=18.0, origin_x=0.0, origin_y=0.0, origin_z=0.0)

RECT_CCW = dict(start=(0.0, 0.0),
                segments=[((300.0, 0.0),), ((300.0, 300.0),), ((0.0, 300.0),), ((0.0, 0.0),)])
RECT_CW = dict(start=(0.0, 0.0),
               segments=[((0.0, 300.0),), ((300.0, 300.0),), ((300.0, 0.0),), ((0.0, 0.0),)])
# Muesca rectangular en el borde inferior: DOS esquinas concavas (150,50) y (200,50).
CONCAVA = dict(start=(0.0, 0.0),
               segments=[((150.0, 0.0),), ((150.0, 50.0),), ((200.0, 50.0),), ((200.0, 0.0),),
                         ((300.0, 0.0),), ((300.0, 300.0),), ((0.0, 300.0),), ((0.0, 0.0),)])
# Chaflan a 45 grados en la esquina (300, 0): convexa pero NO ortogonal.
CHAFLAN = dict(start=(0.0, 0.0),
               segments=[((250.0, 0.0),), ((300.0, 50.0),), ((300.0, 300.0),), ((0.0, 300.0),),
                         ((0.0, 0.0),)])


def _poly(geom, **kw):
    return build_polyline_spec(
        **geom, tool_id="1902", tool_name="E003", tool_width=9.52,
        security_plane=30.0, target_depth=9.0,
        side_of_feature=kw.pop("side", "Right"), **kw)


CASES = [
    # --- 1. CN + leads LINE (postprocesar tal cual) ---
    ("app_line",           "Postprocesar tal cual.",
     _poly(RECT_CCW, approach_enabled=True, approach_type="Line",
           approach_radius_multiplier=4.0)),
    ("app_line_down",      "Postprocesar tal cual.",
     _poly(RECT_CCW, approach_enabled=True, approach_type="Line", approach_mode="Down",
           approach_radius_multiplier=4.0)),
    ("ret_line",           "Postprocesar tal cual.",
     _poly(RECT_CCW, retract_enabled=True, retract_type="Line",
           retract_radius_multiplier=4.0)),
    ("ret_line_up",        "Postprocesar tal cual.",
     _poly(RECT_CCW, retract_enabled=True, retract_type="Line", retract_mode="Up",
           retract_radius_multiplier=4.0)),
    ("leads_line_down_up", "Postprocesar tal cual. (= la op2 de Galceado.pgmx)",
     _poly(RECT_CCW, approach_enabled=True, approach_type="Line", approach_mode="Down",
           approach_radius_multiplier=4.0,
           retract_enabled=True, retract_type="Line", retract_mode="Up",
           retract_radius_multiplier=4.0)),
    # --- 2. Forma EN-JUEGO (postprocesar tal cual) ---
    ("enjuego",            "Postprocesar tal cual. (forma canonica de la App: arranque a mitad "
                           "de borde, leads Arc RM=2, E001, pasante+extra 1)",
     build_contour_spec()),
    ("enjuego_noleads",    "Postprocesar tal cual.",
     build_contour_spec(approach_enabled=False, retract_enabled=False)),
    # --- 3. CAD (ABRIR la operacion, ACEPTAR/regenerar y GUARDAR antes de postprocesar) ---
    ("cad_concava",        "ABRIR la op, ACEPTAR (regenerar) y GUARDAR antes de postprocesar. "
                           "Pregunta: la esquina concava, arco o esquina viva?",
     _poly(CONCAVA, activate_cnc_correction=False)),
    ("cad_interno",        "ABRIR la op, ACEPTAR y GUARDAR antes de postprocesar. "
                           "(CW+Right = offset hacia ADENTRO = Interno)",
     _poly(RECT_CW, activate_cnc_correction=False)),
    ("cad_cw_left",        "ABRIR la op, ACEPTAR y GUARDAR antes de postprocesar. "
                           "(CW+Left = exterior espejado, arcos G2?)",
     _poly(RECT_CW, side="Left", activate_cnc_correction=False)),
    ("cad_chaflan",        "ABRIR la op, ACEPTAR y GUARDAR antes de postprocesar. "
                           "(esquina convexa NO ortogonal)",
     _poly(CHAFLAN, activate_cnc_correction=False)),
    ("cad_leads",          "ABRIR la op, ACEPTAR y GUARDAR antes de postprocesar.",
     _poly(RECT_CCW, activate_cnc_correction=False,
           approach_enabled=True, approach_type="Arc",
           retract_enabled=True, retract_type="Arc")),
    ("cad_zigzag",         "En Maestro: AGREGAR estrategia ZigZag a la op (pasada avance 3 / "
                           "retorno 3 / ultimo hueco 2 como Galceado op1, o los valores que "
                           "queden comodos), ACEPTAR y GUARDAR — la estrategia fuerza el CAD "
                           "sola. Despues postprocesar. (= la op1 de Galceado.pgmx)",
     _poly(RECT_CCW)),
]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    notes = ["# N044 - Galceado pendientes: que hacer con cada archivo antes de postprocesar",
             ""]
    for tag, note, spec in CASES:
        name = f"N_G_{tag}"
        path = out / f"{name}.pgmx"
        kwargs = dict(PIECE)
        if type(spec).__name__ == "ContourSpec":
            kwargs["contours"] = [spec]
        else:
            kwargs["polylines"] = [spec]
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=name, **kwargs))
        print(f"  {path.name}: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print(f"  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
