r"""N047 - Vaciado (pocket milling): baseline ISO + envenenados. Eje B etapa 5, arranque.

El lado PGMX del vaciado ya esta derivado (lab pgmx/machining_lab/pocket_milling: modelo
ClosedPocket + BottomAndSideRoughMilling + ContourParallel, motor de trazas EXACTO contra
Maestro). Lo que NO existe es NINGUNA referencia ISO. Este lote trae las primeras:

1. ENVENENADOS (poison_xy, poison_z) - PRIMERO EN IMPORTANCIA: definen la arquitectura del
   render. Se sintetiza un vaciado normal y se corrompe UN VERTICE de un anillo interior del
   TrajectoryPath almacenado (los dos miembros adyacentes se recomputan para que la cadena
   siga siendo valida). El spec queda correcto: solo miente la curva almacenada.
     - ISO con el veneno   -> Maestro COPIA lo almacenado (como el CAD/ZigZag, N046)
                              -> el converter debera LEER la trayectoria del .pgmx.
     - ISO sin el veneno   -> Maestro REGENERA de los parametros
                              -> el converter debera derivar del motor pocket_trace.
   -> NO ABRIR NI ACEPTAR EN MAESTRO: si se abre la operacion y se acepta, Maestro regenera
      la curva y se pierde el veneno. Postprocesar directo.

2. BASELINE (9 archivos): rectangular pleno 300x300, barrido de herramientas + profundidad
   + un multipaso. Derivan: header/familia, entrada (Approach), cuerpo (anillos), feeds,
   transiciones de nivel, teardown y footer.

PUNTOS CIEGOS DE NUESTRA AUTORIA (por eso las INSTRUCCIONES piden 2 GEMELOS MANUALES):
- nuestro synth escribe RadialCuttingDepth=0 (los .pgmx manuales de Maestro traen el radio);
- nuestro synth no materializa curvas Approach/Lift (los manuales si las tienen).
Si Maestro postprocesa lo ALMACENADO, cualquiera de las dos diferencias puede cambiar el
ISO de un archivo nuestro vs uno dibujado a mano. El diff synth-vs-manual lo dirime.

Uso: py -m iso.machining_lab.n047_vaciado_baseline.generate
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import (  # noqa: E402
    build_contour_parallel_milling_strategy_spec,
    build_pocket_spec,
    build_synthesis_request,
    synthesize_request,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N047_vaciado_baseline"

# Convencion del workstream (N043+): pieza 300x300x18, origen 0/0/0, security 30.
PIECE = dict(length=300.0, width=300.0, depth=18.0, origin_x=0.0, origin_y=0.0, origin_z=0.0)
RECT = [(0.0, 0.0), (300.0, 0.0), (300.0, 300.0), (0.0, 300.0), (0.0, 0.0)]

# (nombre, tool_id, ancho) del catalogo def.tlgx. E002 es la Sierra Horizontal: Maestro la
# acepta para vaciado (lab: Vaciado_004) y el converter no distingue tipo (decision Fermin).
TOOLS = {
    "E001": ("1900", 18.36), "E002": ("1901", 100.0), "E003": ("1902", 9.52),
    "E004": ("1903", 4.0), "E005": ("1904", 76.0), "E006": ("1905", 80.0),
    "E007": ("1906", 17.72),
}

# Venenos: desplazamientos claramente visibles en el ISO a 3 decimales.
POISON_XY = (4.0, 3.0)   # el vertice se corre en diagonal: aparece un quiebre imposible
POISON_Z = 1.5           # el vertice sube: aparecen dos rampas en un nivel plano


def _spec(tool: str, **kw):
    tid, w = TOOLS[tool]
    strategy_kw = {k: kw.pop(k) for k in ("allow_multiple_passes", "axial_cutting_depth",
                                          "axial_finish_cutting_depth") if k in kw}
    return build_pocket_spec(
        contour_points=RECT, tool_id=tid, tool_name=tool, tool_width=w,
        security_plane=30.0,
        milling_strategy=build_contour_parallel_milling_strategy_spec(**strategy_kw),
        **kw)


def _trajectory_block(xml: str) -> tuple[int, int, list[str]]:
    """(inicio, fin, miembros) del composite del TrajectoryPath: el de MAS miembros (los de
    geometria nominal tienen 4; la trayectoria de anillos tiene decenas)."""
    best = None
    for m in re.finditer(r"<(\w+):_serializingMembers[^>]*>(.*?)</\1:_serializingMembers>",
                         xml, re.S):
        items = re.findall(r"<\w+:string>(.*?)</\w+:string>", m.group(2), re.S)
        if best is None or len(items) > len(best[2]):
            best = (m.start(2), m.end(2), items)
    if best is None or len(best[2]) < 20:
        raise SystemExit("no se encontro el composite del TrajectoryPath (anillos)")
    return best


def _parse_line(item: str) -> tuple[list[str], tuple, tuple, float]:
    """(lineas_crudas, start, end, largo) de un miembro RECTA '8 0 L\\n1 ox oy oz dx dy dz'."""
    lines = item.strip().split("\n")
    head, body = lines[0].split(), lines[1].split()
    if body[0] != "1":
        raise SystemExit("el miembro elegido no es una recta")
    length = float(head[2])
    o = tuple(float(v) for v in body[1:4])
    d = tuple(float(v) for v in body[4:7])
    end = (o[0] + d[0] * length, o[1] + d[1] * length, o[2] + d[2] * length)
    return lines, o, end, length


def _line_item(start: tuple, end: tuple) -> str:
    """Serializa una recta Maestro de `start` a `end` (origen + direccion unitaria + largo)."""
    v = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    length = math.dist(start, end)
    d = (v[0] / length, v[1] / length, v[2] / length)
    return (f"8 0 {length!r}\n1 {start[0]!r} {start[1]!r} {start[2]!r} "
            f"{d[0]!r} {d[1]!r} {d[2]!r} ")


def _poison(pgmx: Path, dx: float, dy: float, dz: float) -> str:
    """Corre UN VERTICE interior de la trayectoria almacenada en (dx, dy, dz), recomputando
    los DOS miembros adyacentes (la cadena sigue conectada y valida). El spec no se toca."""
    with zipfile.ZipFile(pgmx) as z:
        names = z.namelist()
        xml_name = next(n for n in names if n.lower().endswith(".xml"))
        blobs = {n: z.read(n) for n in names}
    xml = blobs[xml_name].decode("utf-8")
    start, end, items = _trajectory_block(xml)

    # Un vertice del medio (lejos de la entrada y del cierre), entre dos rectas.
    k = len(items) // 2
    while k + 1 < len(items) - 1:
        if (items[k].strip().split("\n")[1].split()[0] == "1"
                and items[k + 1].strip().split("\n")[1].split()[0] == "1"):
            break
        k += 1
    _, a_start, a_end, _ = _parse_line(items[k])
    _, b_start, b_end, _ = _parse_line(items[k + 1])
    if math.dist(a_end, b_start) > 1e-6:
        raise SystemExit("la cadena no conecta donde se esperaba: revisar el composite")
    vertex = (a_end[0] + dx, a_end[1] + dy, a_end[2] + dz)
    items[k] = _line_item(a_start, vertex)
    items[k + 1] = _line_item(vertex, b_end)

    ns = re.match(r"<(\w+):string>", re.search(r"<\w+:string>", xml[start:end]).group(0)).group(1)
    body = "".join(f"<{ns}:string>{it}</{ns}:string>" for it in items)
    xml = xml[:start] + body + xml[end:]
    blobs[xml_name] = xml.encode("utf-8")
    with zipfile.ZipFile(pgmx, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in blobs.items():
            z.writestr(n, data)
    return (f"vertice {a_end[0]:.3f}/{a_end[1]:.3f}/{a_end[2]:.3f} -> "
            f"{vertex[0]:.3f}/{vertex[1]:.3f}/{vertex[2]:.3f} (miembros {k},{k + 1})")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    notes = [
        "# N047 - accion por archivo", "",
        "Postprocesar TODO tal cual a `P:\\USBMIX\\ProdAction\\N047_vaciado_baseline\\`.", "",
        "## 1. ENVENENADOS - **NO ABRIR NI ACEPTAR EN MAESTRO**, postprocesar directo", "",
        "Si se abre la operacion y se acepta, Maestro regenera la trayectoria y se pierde",
        "el veneno. Responden LA pregunta estructural: copia vs recalculo.", "",
    ]

    for tag, (dx, dy, dz), note in (
        ("poison_xy", (*POISON_XY, 0.0),
         f"vertice de anillo corrido +{POISON_XY[0]}/+{POISON_XY[1]} en XY"),
        ("poison_z", (0.0, 0.0, POISON_Z),
         f"vertice de anillo levantado +{POISON_Z} en Z (nivel plano con rampa imposible)"),
    ):
        name = f"N_V_{tag}"
        path = out / f"{name}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=name,
            pockets=[_spec("E003", target_depth=9.0)], **PIECE))
        what = _poison(path, dx, dy, dz)
        print(f"  {name}.pgmx: {what}")
        notes.append(f"- `{name}.pgmx` — {note}")

    notes += ["", "## 2. BASELINE (postprocesar tal cual)", ""]
    for tag, tool, kw, note in (
        ("e001_d9", "E001", dict(target_depth=9.0), "Widea 18.36, ciego -9"),
        ("e003_d9", "E003", dict(target_depth=9.0), "Violeta 9.52, ciego -9 (pedir GEMELO manual)"),
        ("e004_d9", "E004", dict(target_depth=9.0), "4 mm, ciego -9 (anillos densos)"),
        ("e006_d9", "E006", dict(target_depth=9.0), "Rectificado 80, ciego -9 (pocos anillos)"),
        ("e007_d9", "E007", dict(target_depth=9.0), "Recta 17.72, ciego -9"),
        ("e002_d9", "E002", dict(target_depth=9.0), "Sierra Horizontal 100, ciego -9"),
        ("e005_d9", "E005", dict(target_depth=9.0), "Fresa 45 de 76, ciego -9"),
        ("e003_d4", "E003", dict(target_depth=4.0), "Violeta, ciego -4 (aisla la profundidad)"),
        ("e006_mp_d12", "E006", dict(target_depth=12.0, allow_multiple_passes=True,
                                     axial_cutting_depth=5.0, axial_finish_cutting_depth=2.0),
         "multipaso cd=5 uh=2 (niveles Z en un TrajectoryPath; pedir GEMELO manual)"),
    ):
        name = f"N_V_{tag}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name,
            pockets=[_spec(tool, **kw)], **PIECE))
        print(f"  {name}.pgmx: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")

    notes += [
        "", "## 3. GEMELOS MANUALES (dibujar EN MAESTRO desde cero, sin sintetizador)", "",
        "Dos vaciados dibujados a mano con los MISMOS parametros, guardados en esta carpeta",
        "y postprocesados. Son el control de circularidad (regla 5) y dirimen dos puntos",
        "ciegos de nuestra autoria: RadialCuttingDepth=0 y Approach/Lift no materializados.", "",
        "- `N_V_manual_e003_d9.pgmx` — pieza 300x300x18 origen 0/0/0, vaciado del rectangulo",
        "  completo, E003, ciego -9, cota de seguridad 30, estrategia Paralela al perfil con",
        "  defaults (Antihorario, LiftShiftPlunge, dentro->afuera, sobreposicion 50%, sin",
        "  helicoidal, sin multipaso, sin rebaba).",
        "- `N_V_manual_e006_mp_d12.pgmx` — idem con E006, ciego -12, multipaso: profundidad",
        "  de hueco 5, ultimo hueco 2.", "",
        "## 4. CAPTURAS DE LA UI (mismo dia si se puede)", "",
        "Checklist completo en `iso/docs/experiments/vaciado.md` (seccion F1): ventana",
        "Vaciado completa, dropdown de estrategias, panel Paralela al perfil, C.N./CAD,",
        "como se dibuja una isla, profundidad/pasante, Datos avanzados y Datos maquina.",
    ]
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
