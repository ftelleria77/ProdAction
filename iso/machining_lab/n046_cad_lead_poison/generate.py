r"""N046 - dos preguntas que N045 dejo abiertas.

1. ENVENENADOS (poison_arc, poison_line). N045 derivo el lead CAD, pero sus .pgmx se
   postprocesaron TAL CUAL: la curva Approach ALMACENADA coincidia con el ISO, asi que el lote no
   distingue si Maestro RECALCULA el lead del spec o COPIA nuestra curva. Estos dos archivos
   rompen el empate: se sintetizan normal y despues se les ENVENENA la curva almacenada del
   lead-in (radio/largo deliberadamente equivocado), dejando el RM del spec correcto y el
   lead-out INTACTO. El lead-out es el control interno: en el mismo ISO se comparan los dos.
     - ISO con entrada == salida  -> Maestro RECALCULA del spec  -> N045 queda confirmado.
     - ISO con la entrada envenenada -> Maestro COPIA lo almacenado -> el converter tiene que
       LEER la curva, no recalcularla (y N045 habria estado derivando de si mismo).
   El veneno es una curva VALIDA (tangente y conectada al arranque de la traza): solo cambia el
   radio. Es el patron que hizo prueba por accidente en N029 (rm3).
   -> NO ABRIR NI ACEPTAR en Maestro: si se abre la operacion y se acepta, Maestro REGENERA la
      curva y se pierde el veneno. Postprocesar directo.

2. ZIGZAG CAD (zz_d9/d13/d18). Los de N045 se postprocesaron sin que nadie les agregara la
   estrategia, asi que salieron como contorno CN y no cubren el zigzag. Van de nuevo.
   -> En Maestro: AGREGAR ZigZag con los parametros indicados (la estrategia fuerza ACC=false
      sola), ACEPTAR y GUARDAR. Postprocesar.

Uso: py -m iso.machining_lab.n046_cad_lead_poison.generate
"""
from __future__ import annotations
import argparse, re, shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_polyline_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N046_cad_lead_poison"

# Mismo contexto que N043/N044/N045: pieza 300x300x18, ciego -9, security 30, origen 0/0/0.
PIECE = dict(length=300.0, width=300.0, depth=18.0, origin_x=0.0, origin_y=0.0, origin_z=0.0)
RECT_CCW = dict(start=(0.0, 0.0),
                segments=[((300.0, 0.0),), ((300.0, 300.0),), ((0.0, 300.0),), ((0.0, 0.0),)])
E003 = ("1902", 9.52)   # (tool_id, ancho) — la fresa de control de N044/N045

# Radios/largos VERDADEROS con E003 y RM=2 (los que el spec implica):
#   arco  = (w/2)x(RM-1) = 4.76      linea = (w/2)xRM = 9.52
# Venenos: valores claramente distintos, para que el ISO los delate a simple vista.
POISON_ARC = 12.0
POISON_LINE = 25.0


def _spec(cad: bool = True, **kw):
    tid, w = E003
    common = dict(**RECT_CCW, tool_id=tid, tool_name="E003", tool_width=w,
                  security_plane=30.0, side_of_feature="Right")
    if cad:
        common.update(target_depth=9.0, activate_cnc_correction=False)
    return build_polyline_spec(**common, **kw)


def _approach_block(xml: str) -> tuple[int, int, list[str]]:
    """(inicio, fin, miembros) del composite del ACERCAMIENTO. La traza va en composites
    SEPARADOS (nominal del feature / approach / cuerpo offseteado / retract); el del approach es
    el que ARRANCA con el descenso vertical (recta de direccion 0 0 -1). Envenenar el del cuerpo
    romperia la pieza, y el del retract es el control interno: por eso se identifica, no se
    adivina por tamano."""
    for m in re.finditer(r"<(\w+):_serializingMembers>(.*?)</\1:_serializingMembers>", xml, re.S):
        items = re.findall(r"<\w+:string>(.*?)</\w+:string>", m.group(2), re.S)
        if len(items) != 2:
            continue
        first = items[0].strip().split("\n")[-1].split()
        if first[0] == "1" and first[-3:] == ["0", "0", "-1"]:
            return m.start(2), m.end(2), items
    raise SystemExit("no se encontro el composite del acercamiento (descenso vertical)")


def _poison(pgmx: Path, radius: float) -> str:
    """Reescribe el .pgmx cambiando SOLO el lead-in almacenado (descenso + primer movimiento) por
    uno de radio/largo `radius`. Devuelve una descripcion de lo que cambio."""
    with zipfile.ZipFile(pgmx) as z:
        names = z.namelist()
        xml_name = next(n for n in names if n.lower().endswith(".xml"))
        blobs = {n: z.read(n) for n in names}
    xml = blobs[xml_name].decode("utf-8")
    start, end, items = _approach_block(xml)

    down = items[0].strip().split("\n")      # "8 0 39" / "1 x y z dx dy dz" (descenso vertical)
    lead = items[1].strip().split("\n")      # arco "2 cx cy cz n u v r" o recta "1 x y z dx dy dz"
    lead_tok = lead[1].split()
    if lead_tok[0] == "2":                   # ARCO: centro a `radius` del arranque, sobre -x
        # El arco tiene que seguir CERRANDO en el arranque de la traza offseteada (-w/2, 0) y
        # llegando tangente: centro = arranque - radius*x̂, punto exterior = centro + radius*ŷ.
        cx = -E003[1] / 2.0 - radius
        lead_tok[1], lead_tok[-1] = repr(cx), repr(radius)
        entry = (cx, radius)                 # punto exterior = centro + radius*(0,+1)
        lead[1] = " ".join(lead_tok) + " "
        what = f"arco r={radius} (centro x={cx})"
    else:                                    # RECTA: largo `radius` sobre la tangente (0,-1)
        head = lead[0].split()
        head[2] = repr(radius)
        lead[0] = " ".join(head)
        lead_tok[1], lead_tok[2] = repr(-E003[1] / 2.0), repr(radius)
        entry = (-E003[1] / 2.0, radius)
        lead[1] = " ".join(lead_tok) + " "
        what = f"recta largo={radius}"
    down_tok = down[1].split()               # el descenso arranca en el punto exterior nuevo
    down_tok[1], down_tok[2] = repr(entry[0]), repr(entry[1])
    down[1] = " ".join(down_tok) + " "

    items[0], items[1] = "\n".join(down) + "\n", "\n".join(lead) + "\n"
    body = "".join(f"<b:string>{it}</b:string>" for it in items)
    ns = re.match(r"<(\w+):string>", re.search(r"<\w+:string>", xml[start:end]).group(0)).group(1)
    xml = xml[:start] + body.replace("<b:string>", f"<{ns}:string>").replace(
        "</b:string>", f"</{ns}:string>") + xml[end:]
    blobs[xml_name] = xml.encode("utf-8")
    with zipfile.ZipFile(pgmx, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in blobs.items():
            z.writestr(n, data)
    return what


ARC = dict(approach_enabled=True, approach_type="Arc", approach_radius_multiplier=2.0,
           retract_enabled=True, retract_type="Arc", retract_radius_multiplier=2.0)
LINE = dict(approach_enabled=True, approach_type="Line", approach_radius_multiplier=2.0,
            retract_enabled=True, retract_type="Line", retract_radius_multiplier=2.0)
ZZ = "ZigZag: pasada avance=3, retorno=3, ultimo hueco=2, Climb"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    notes = ["# N046 - accion por archivo", "",
             "## 1. ENVENENADOS - **NO ABRIR NI ACEPTAR EN MAESTRO**, postprocesar directo", "",
             "Si se abre la operacion y se acepta, Maestro regenera la curva y se pierde el veneno.",
             "El lead-OUT quedo intacto a proposito: es el control interno del mismo ISO.", ""]
    for tag, poison, leads, note in (
        ("poison_arc", POISON_ARC, ARC, f"lead-in ARCO envenenado a r={POISON_ARC} (el spec RM=2 implica 4.76)"),
        ("poison_line", POISON_LINE, LINE, f"lead-in LINEAL envenenado a largo={POISON_LINE} (el spec RM=2 implica 9.52)"),
    ):
        name = f"N_G6_{tag}"
        path = out / f"{name}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=name, polylines=[_spec(**leads)], **PIECE))
        what = _poison(path, poison)
        print(f"  {name}.pgmx: envenenado {what}")
        notes.append(f"- `{name}.pgmx` — {note}")
    notes += ["", "## 2. ZIGZAG CAD (AGREGAR la estrategia en Maestro + ACEPTAR + GUARDAR)", ""]
    for tag, kw, note in (
        ("zz_d9", dict(target_depth=9.0), "ciego -9 (~pocas pasadas)"),
        ("zz_d13", dict(target_depth=13.0), "ciego -13 (mas pasadas)"),
        ("zz_d18", dict(is_through=True), "PASANTE (espesor 18)"),
    ):
        name = f"N_G6_{tag}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name,
            polylines=[_spec(cad=False, **kw)], **PIECE))
        print(f"  {name}.pgmx: {note}. {ZZ}")
        notes.append(f"- `{name}.pgmx` — {note}. {ZZ}")
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
