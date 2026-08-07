r"""N045 - Eje B etapa 4: desambiguar cad_leads y cad_zigzag (los 2 fail-loud de N044).

Dos preguntas abiertas, cada una con UN solo fixture en N044 (subdeterminadas):

1. LEAD CAD (cad_leads). En N044 el lead-in fue un CUARTO DE ARCO de radio w/2 (=4.76 con E003
   w=9.52), centro a w del vertice nominal, con RM=2. ¿El radio/centro escala con RM, o el radio
   es w/2 fijo y RM no entra? ¿Y escala con la fresa? Este lote varia RM (1/2/3) con la MISMA
   fresa y la fresa (E001/E003/E004) con la MISMA RM, para separar las dos dependencias. Ademas
   un lead LINEAL en CAD (¿existe? ¿mismo largo que la linea, w/2xRM?).
   -> Son CAD (ACC=false): la traza almacenada trae el offset. ABRIR la op en Maestro, ACEPTAR
      (regenerar) y GUARDAR antes de postprocesar (regla 5: autorarla seria circular).

2. ZIGZAG en contorno CERRADO CAD (cad_zigzag = op1 de Galceado.pgmx). Un solo fixture no fija
   como se generan las pasadas del zigzag sobre el perfil offseteado. Este lote da rectangulos de
   distinta PROFUNDIDAD (mas pasadas) para derivar el patron.
   -> El .pgmx base va SIN estrategia (CN). En Maestro: AGREGAR ZigZag con los parametros que
      indica cada archivo (la estrategia fuerza ACC=false sola), ACEPTAR y GUARDAR. Postprocesar.

El generador deja un INSTRUCCIONES.md con la accion y los parametros por archivo.
Uso: py -m iso.machining_lab.n045_galceado_cad_combos.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_polyline_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N045_galceado_cad_combos"

# Contexto de N043/N044: pieza 300x300x18, ciego -9, security 30, origen 0/0/0.
PIECE = dict(length=300.0, width=300.0, depth=18.0, origin_x=0.0, origin_y=0.0, origin_z=0.0)

# Rectangulo del perimetro 300x300, arranque en la esquina (0,0), CCW (offset exterior con Right).
RECT_CCW = dict(start=(0.0, 0.0),
                segments=[((300.0, 0.0),), ((300.0, 300.0),), ((0.0, 300.0),), ((0.0, 0.0),)])

# (nombre_de_fresa, id, ancho) — E003 control, E001 grande, E004 chica.
TOOLS = {"E003": ("1902", 9.52), "E001": ("1900", 18.36), "E004": ("1903", 4.0)}


def _cad(tool="E003", **kw):
    tid, w = TOOLS[tool]
    return build_polyline_spec(
        **RECT_CCW, tool_id=tid, tool_name=tool, tool_width=w,
        security_plane=30.0, target_depth=9.0,
        side_of_feature="Right", activate_cnc_correction=False, **kw)


def _cn(tool="E003", **kw):
    """Rectangulo CN (sin estrategia) para que Fermin le agregue ZigZag en Maestro."""
    tid, w = TOOLS[tool]
    return build_polyline_spec(
        **RECT_CCW, tool_id=tid, tool_name=tool, tool_width=w,
        security_plane=30.0, side_of_feature="Right", **kw)


ARC = dict(approach_enabled=True, approach_type="Arc",
           retract_enabled=True, retract_type="Arc")

# --- 1. LEAD CAD: barrido de RM (misma fresa) y de fresa (misma RM); + lead lineal ---
CAD_LEADS = [
    ("cad_leads_rm1",  "E003 RM=1", _cad(**ARC, approach_radius_multiplier=1.0, retract_radius_multiplier=1.0)),
    ("cad_leads_rm2",  "E003 RM=2 (control, = cad_leads de N044)", _cad(**ARC, approach_radius_multiplier=2.0, retract_radius_multiplier=2.0)),
    ("cad_leads_rm3",  "E003 RM=3", _cad(**ARC, approach_radius_multiplier=3.0, retract_radius_multiplier=3.0)),
    ("cad_leads_e001", "E001 RM=2 (fresa grande w=18.36)", _cad(tool="E001", **ARC, approach_radius_multiplier=2.0, retract_radius_multiplier=2.0)),
    ("cad_leads_e004", "E004 RM=2 (fresa chica w=4)", _cad(tool="E004", **ARC, approach_radius_multiplier=2.0, retract_radius_multiplier=2.0)),
    ("cad_leads_line", "E003 lead LINEAL En cota (RM=2): ¿existe en CAD? ¿largo w/2xRM?",
     _cad(approach_enabled=True, approach_type="Line", approach_radius_multiplier=2.0,
          retract_enabled=True, retract_type="Line", retract_radius_multiplier=2.0)),
]

# --- 2. ZIGZAG CAD: rectangulos de distinta profundidad (Fermin agrega la estrategia) ---
# Parametros pedidos (los de la op1 de Galceado): avance 3 / retorno 3 / ultimo hueco 2, Climb.
ZZ_PARAMS = "ZigZag: pasada avance=3, retorno=3, ultimo hueco=2, Climb"
CAD_ZIGZAG = [
    ("cad_zz_d9",  f"ciego -9 (~pocas pasadas). {ZZ_PARAMS}", _cn(target_depth=9.0)),
    ("cad_zz_d13", f"ciego -13 (mas pasadas). {ZZ_PARAMS}", _cn(target_depth=13.0)),
    ("cad_zz_d18", f"PASANTE (espesor 18). {ZZ_PARAMS}", _cn(is_through=True)),
]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    notes = ["# N045 - cerrar cad_leads y cad_zigzag: accion por archivo", "",
             "## 1. LEAD CAD (ABRIR la op + ACEPTAR/regenerar + GUARDAR antes de postprocesar)", ""]
    for tag, note, spec in CAD_LEADS:
        name = f"N_G5_{tag}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name, polylines=[spec], **PIECE))
        print(f"  {name}.pgmx: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")
    notes += ["", "## 2. ZIGZAG CAD (AGREGAR la estrategia en Maestro + ACEPTAR + GUARDAR)", ""]
    for tag, note, spec in CAD_ZIGZAG:
        name = f"N_G5_{tag}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name, polylines=[spec], **PIECE))
        print(f"  {name}.pgmx: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
