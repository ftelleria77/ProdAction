r"""N048 - Vaciado: parametros de la estrategia, UNO por fixture (Eje B etapa 5, F3b).

N047 fijo el baseline (defaults: Antihorario, LiftShiftPlunge, dentro->afuera, 50%, Climb,
sin helicoidal) y la arquitectura (el ISO COPIA la trayectoria ALMACENADA). Este lote aisla
cada parametro de la ventana Vaciado contra ese baseline, para LEVANTAR las guardas de
`_validate_pocket` una por una. Como el render copia lo almacenado, lo que se deriva aca son
las CONVENCIONES (feeds, orden, transiciones) — y si algun parametro cambia algo mas que la
trayectoria, el byte lo delata.

Todos los parametros de este lote estan validados en la AUTORIA (lab pocket_milling,
corpus Vaciado_010..019: el motor reproduce la trayectoria de Maestro exacta para cada
variante) => fixtures sintetizados legitimos, se postprocesan TAL CUAL, sin tocar Maestro.

Decisiones de diseno:
- Herramienta de control E003 (feeds 3000/18000 discriminan plunge vs corte). EXCEPTO la
  rebaba +-20, que va con E006 (radio 40, como Vaciado_015/016 del corpus): con E003
  (radio 4.76) la rebaba -20 daria offset efectivo NEGATIVO. CORRECCION 2026-07-29: el
  offset efectivo negativo (rebaba mas alla del radio) SI existe en la UI — capturado con
  Rebaba -75 sobre E006: el recorrido SOBREPASA el contorno y las esquinas se redondean =
  ARCOS en la trayectoria almacenada. Ese caso va con el lote de arcos (N050), no aca.
- `Conexion entre huecos = En la pieza` (Straghtline) solo difiere de LiftShiftPlunge en
  MULTIPASO (lab, Vaciado_011 vs 019): va en par con su comparador `mp_e003` (identico
  salvo la conexion).
- PASANTE y AllowanceBottom NO se sintetizan: no sabemos si la ventana Vaciado los expone
  (pregunta abierta del checklist de capturas). Autorarlos seria fabricar un .pgmx que
  quiza ninguna UI produce. Van como MANUALES OPCIONALES en las instrucciones.

Uso: py -m iso.machining_lab.n048_vaciado_estrategia.generate
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

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "Investigacion iso_converter" / "N048_vaciado_estrategia"

# Convencion del workstream (= N047): pieza 300x300x18, origen 0/0/0, security 30.
PIECE = dict(length=300.0, width=300.0, depth=18.0, origin_x=0.0, origin_y=0.0, origin_z=0.0)
RECT = [(0.0, 0.0), (300.0, 0.0), (300.0, 300.0), (0.0, 300.0), (0.0, 0.0)]
E003 = ("1902", "E003", 9.52)
E006 = ("1905", "E006", 80.0)


def _spec(tool=E003, target_depth=9.0, allowance_side=0.0, **strategy_kw):
    tid, name, w = tool
    return build_pocket_spec(
        contour_points=RECT, tool_id=tid, tool_name=name, tool_width=w,
        security_plane=30.0, target_depth=target_depth,
        allowance_side=allowance_side,
        milling_strategy=build_contour_parallel_milling_strategy_spec(**strategy_kw),
    )


# (tag, spec, parametro UI aislado)
FIXTURES = (
    ("horario", _spec(rotation_direction="Clockwise"),
     "Direccion del recorrido = Horario (RotationDirection=Clockwise)"),
    ("afuera_adentro", _spec(inside_to_outside=False),
     "Direccion de vaciado = Desde afuera hacia adentro (InsideToOutSide=false)"),
    ("overlap25", _spec(overlap=0.25),
     "Sobreposicion % = 25 (Overlap=0.25; paso radial 9.52x0.75=7.14)"),
    ("helicoidal", _spec(is_helic_strategy=True),
     "Habilitar helicoidal = true (el corpus del lab lo vio SIN cambiar la trayectoria "
     "almacenada — si el ISO tampoco cambia, la guarda se levanta como flag invisible)"),
    ("mp_e003", _spec(target_depth=12.0, allow_multiple_passes=True,
                      axial_cutting_depth=5.0, axial_finish_cutting_depth=2.0),
     "multipaso cd=5 uh=2 con E003 — COMPARADOR de straghtline_mp (conexion default "
     "LiftShiftPlunge)"),
    ("straghtline_mp", _spec(target_depth=12.0, allow_multiple_passes=True,
                             axial_cutting_depth=5.0, axial_finish_cutting_depth=2.0,
                             stroke_connection_strategy="Straghtline"),
     "Conexion entre huecos = En la pieza (Straghtline) + multipaso — las transiciones "
     "de nivel bajan DENTRO de la pieza en vez de subir a seguridad"),
    ("reb_p20", _spec(tool=E006, allowance_side=20.0),
     "Rebaba / despeje al contorno = +20 (AllowanceSide; E006 como Vaciado_015)"),
    ("reb_m20", _spec(tool=E006, allowance_side=-20.0),
     "Rebaba / despeje al contorno = -20 (AllowanceSide negativa; E006 como Vaciado_016)"),
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    notes = [
        "# N048 - accion por archivo", "",
        "Postprocesar TODO tal cual a `P:\\USBMIX\\ProdAction\\N048_vaciado_estrategia\\`.",
        "No hace falta abrir nada en Maestro (autoria validada por el lab, Vaciado_010..019).",
        "", "## 1. SINTETIZADOS (un parametro de la estrategia por archivo)", "",
    ]
    for tag, spec, note in FIXTURES:
        name = f"N_V8_{tag}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name, pockets=[spec], **PIECE))
        print(f"  {name}.pgmx: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")
    notes += [
        "", "## 2. MANUALES OPCIONALES (solo si la ventana Vaciado los expone)", "",
        "Estos dos NO se sintetizaron porque no sabemos si la UI los ofrece (pregunta del",
        "checklist de capturas). Si existen, dibujarlos en Maestro desde cero (pieza",
        "300x300x18, rectangulo completo, E003, defaults) y postprocesarlos:", "",
        "- `N_V8_manual_pasante.pgmx` — vaciado PASANTE (si la profundidad lo permite).",
        "- `N_V8_manual_acabado.pgmx` — cualquier opcion de acabado/despeje al FONDO",
        "  (AllowanceBottom u otra que aparezca en la ventana).", "",
        "## 3. RECORDATORIO: capturas de la UI", "",
        "El checklist completo sigue pendiente en `iso/docs/experiments/vaciado.md` (F1).",
        "Para este lote importa especialmente: el dropdown de ESTRATEGIAS del vaciado y",
        "los campos del panel `Paralela al perfil` que el lab no mapeo a UI",
        "(RadialFinishCuttingDepth, AllowsBidirectional, AllowsFinishCutting, Cutmode).",
    ]
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
