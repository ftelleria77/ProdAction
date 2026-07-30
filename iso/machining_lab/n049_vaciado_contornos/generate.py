r"""N049 - Vaciado: CONTORNOS parciales, arranques y excedidos (Eje B etapa 5, F3c).

N047/N048 usaron siempre el rectangulo PLENO de la pieza arrancado en la esquina (0,0).
Este lote varia el CONTORNO — un aspecto por fixture — para confirmar que las convenciones
del ISO (entrada, anillos, feeds, teardown) no cambian cuando el contorno es parcial,
arranca en otro punto, se recorre al reves o EXCEDE la pieza. Como el render COPIA la
trayectoria almacenada y las guardas ya aceptan rectangulos parciales (con colineales
tolerados), lo esperable es byte-identico directo, sin levantar nada: el lote es la RED
que confirma esa expectativa con evidencia.

Base de evidencia PGMX (lab pocket_milling): la sintesis productiva acepta rectangulos
parciales sin islas (corpus Vaciado_020/021, 023..026, 032..035, trazas exactas contra
Maestro) y Maestro aplica el offset contra el BBOX del contorno, no contra el tablero
(incluye contornos que exceden la pieza). El punto inicial del contorno influye en el
punto de entrada de la trayectoria (Vaciado_002/003).

Todos sintetizados: postprocesar TAL CUAL, sin abrir en Maestro.

Uso: py -m iso.machining_lab.n049_vaciado_contornos.generate
"""
from __future__ import annotations

import argparse
import sys
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N049_vaciado_contornos"

# Convencion del workstream (= N047/N048): pieza 300x300x18, origen 0/0/0, security 30.
PIECE = dict(length=300.0, width=300.0, depth=18.0, origin_x=0.0, origin_y=0.0, origin_z=0.0)
E003 = ("1902", "E003", 9.52)
E006 = ("1905", "E006", 80.0)


def _rect(x0, y0, x1, y1, start=None, clockwise=False):
    """Contorno rectangular cerrado. `start` (opcional) parte un borde en dos tramos
    colineales (arranque a mitad de borde, como Vaciado_002)."""
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if clockwise:
        corners = [corners[0]] + corners[1:][::-1]
    if start is None:
        return corners + [corners[0]]
    # insertar el punto de arranque sobre el borde que lo contiene y rotar la secuencia
    pts = []
    n = len(corners)
    for i in range(n):
        a, b = corners[i], corners[(i + 1) % n]
        pts.append(a)
        on_edge = (
            (a[0] == b[0] == start[0] and min(a[1], b[1]) < start[1] < max(a[1], b[1]))
            or (a[1] == b[1] == start[1] and min(a[0], b[0]) < start[0] < max(a[0], b[0]))
        )
        if on_edge:
            pts.append(start)
    k = pts.index(start)
    return pts[k:] + pts[:k] + [start]


def _spec(contour, tool=E003):
    tid, name, w = tool
    return build_pocket_spec(
        contour_points=contour, tool_id=tid, tool_name=name, tool_width=w,
        security_plane=30.0, target_depth=9.0,
        milling_strategy=build_contour_parallel_milling_strategy_spec(),
    )


# (tag, spec, aspecto aislado)
FIXTURES = (
    ("parcial_centro", _spec(_rect(75.0, 75.0, 225.0, 225.0)),
     "rectangulo parcial 150x150 CENTRADO (el offset ancla al bbox del contorno)"),
    ("parcial_esquina", _spec(_rect(0.0, 0.0, 150.0, 150.0)),
     "rectangulo parcial pegado a la ESQUINA de la pieza (bordes del contorno = bordes de pieza)"),
    ("parcial_banda", _spec(_rect(50.0, 100.0, 250.0, 180.0)),
     "banda rectangular 200x80 (proporcion distinta; menos anillos en Y)"),
    ("arranque_mitad", _spec(_rect(75.0, 75.0, 225.0, 225.0, start=(150.0, 75.0))),
     "mismo parcial centrado, contorno arrancando a MITAD del borde inferior "
     "(punto colineal extra, como Vaciado_002)"),
    ("contorno_horario", _spec(_rect(75.0, 75.0, 225.0, 225.0, clockwise=True)),
     "contorno nominal HORARIO con trayectoria almacenada IDENTICA al parcial_centro "
     "(nuestro sintetizador normaliza el winding al generar): prueba que el winding del "
     "contorno es INVISIBLE para el postprocesador dada la misma trayectoria. OJO: NO "
     "reproduce Vaciado_003 (contorno invertido dibujado EN Maestro, donde el generador "
     "de Maestro si cambia la trayectoria) — ese caso seria un manual futuro"),
    ("excede_pieza", _spec(_rect(-30.0, -30.0, 330.0, 330.0)),
     "contorno que EXCEDE la pieza 30mm por lado (offset contra el bbox del contorno, "
     "anillos parcialmente FUERA del tablero)"),
    ("parcial_chico_e006", _spec(_rect(90.0, 90.0, 210.0, 210.0), tool=E006),
     "parcial 120x120 con E006 (radio 40): caso borde de POCOS anillos (span interior 40)"),
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    notes = [
        "# N049 - accion por archivo", "",
        "Postprocesar TODO tal cual a `P:\\USBMIX\\ProdAction\\N049_vaciado_contornos\\`.",
        "No hace falta abrir nada en Maestro (autoria validada por el lab: rectangulos",
        "parciales con trazas exactas, corpus Vaciado_020..035).", "",
        "## Sintetizados (un aspecto del contorno por archivo)", "",
    ]
    for tag, spec, note in FIXTURES:
        name = f"N_V9_{tag}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name, pockets=[spec], **PIECE))
        print(f"  {name}.pgmx: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")
    notes += [
        "", "## Recordatorio (para la misma sesion, si hay tiempo)", "",
        "- Los dos manuales de ARCOS ya dibujados (anillo circular `N_V_e001_d9_Isla_manual`",
        "  y `N_V_e001_d9_Vaciado_Rebaba_negativa_manual`): guardarlos/postprocesarlos en una",
        "  carpeta nueva `N050_vaciado_arcos_islas\\` — arrancan ese lote.",
        "- Manuales chicos pendientes: PASANTE (tildar en una copia + Aceptar + guardar) y",
        "  Avanz./Rotacion con un valor cargado.",
    ]
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
