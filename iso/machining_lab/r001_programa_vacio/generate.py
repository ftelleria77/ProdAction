r"""R001 - Reinvestigacion, etapa 1: programa SIN mecanizados (configuracion de programa).

Reinicio metodico de la investigacion del converter (decision 2026-08-06): antes de
cualquier operacion, aislar que emite el postprocesador cuando el programa NO tiene
mecanizados. El ISO de un programa vacio es puro esqueleto: cada linea tiene que poder
atribuirse a (a) la configuracion del PROGRAMA (este .pgmx) o (b) la configuracion de la
MAQUINA (snapshot de la PC del CNC). Nada puede venir "de una operacion" porque no hay
ninguna.

Variaciones controladas, UNA opcion por archivo, siempre contra `R_PV_base`:

- base:      400x400x18, origen 0/0/0, campo HG, SIN Xn (la forma nativa de Maestro:
             un .pgmx recien creado no trae ninguna operacion de maquina).
- dim:       500x350x25 — las tres dimensiones (DX/DY/DZ aparecen por separado en el ISO,
             el archivo unico alcanza para atribuir cada una).
- origen_xy: origen 100/50/0 — aisla el origen XY de la fase (Setup/Placement _xP/_yP).
- origen_z:  origen 0/0/5 — aisla el origen Z (interactua con _zP del plano Top?).
- campo_EF:  campo de ejecucion EF (vs HG del base).
- con_xn:    UN Xn con los defaults de Maestro (aisla el bloque que el Xn agrega al ISO).
- variable:  una variable de usuario (Double, sin uso) — ¿deja rastro en el ISO?

Lo que la config del programa tiene y este synth NO puede variar (candidatos a gemelos
manuales tras el repaso de la UI con capturas): WorkpieceOffsetX/Y/Z, Repetitions,
ContinuousCycle, IsTechnologicalMirror, TableOptions, MechanicalOptions,
IsRelatedToOppositeSideStop (bloque XilogHeaderParameters del .pgmx).

Uso: py -m iso.machining_lab.r001_programa_vacio.generate
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
    build_parametric_variable_spec,
    build_synthesis_request,
    synthesize_request,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "R001_programa_vacio"

# Base = la pieza que propone la plantilla nativa de Maestro (Pieza.xml): 400x400x18.
BASE = dict(length=400.0, width=400.0, depth=18.0,
            origin_x=0.0, origin_y=0.0, origin_z=0.0, execution_fields="HG")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    cases = (
        ("R_PV_base", dict(BASE), dict(xn=None),
         "400x400x18, origen 0/0/0, HG, sin operaciones, SIN Xn (forma nativa)"),
        ("R_PV_dim_500x350x25", dict(BASE, length=500.0, width=350.0, depth=25.0),
         dict(xn=None), "solo cambian las dimensiones"),
        ("R_PV_origen_x100_y50", dict(BASE, origin_x=100.0, origin_y=50.0),
         dict(xn=None), "solo cambia el origen XY"),
        ("R_PV_origen_z5", dict(BASE, origin_z=5.0),
         dict(xn=None), "solo cambia el origen Z"),
        ("R_PV_campo_EF", dict(BASE, execution_fields="EF"),
         dict(xn=None), "solo cambia el campo de ejecucion (EF)"),
        ("R_PV_con_xn", dict(BASE), dict(),
         "identico al base MAS un Xn con defaults de Maestro"),
        ("R_PV_variable_usuario", dict(BASE),
         dict(xn=None, parametric_variables=[build_parametric_variable_spec(
             name="p1", value=100.0, description="variable de usuario sin uso")]),
         "identico al base MAS una variable de usuario Double p1=100 (sin uso)"),
    )
    notes = [
        "# R001 - programa sin mecanizados (reinicio de la investigacion)", "",
        "Postprocesar TODO tal cual a `P:\\USBMIX\\ProdAction\\R001_programa_vacio\\`.", "",
        "Si Maestro se NIEGA a postprocesar un programa sin operaciones, anotar el",
        "mensaje EXACTO (ventana/texto): ese rechazo tambien es un dato del experimento.", "",
        "## Archivos sintetizados (una opcion variada por archivo, contra el base)", "",
    ]
    for name, piece_kw, extra_kw, note in cases:
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name, **piece_kw, **extra_kw))
        print(f"  {name}.pgmx: {note}")
        notes.append(f"- `{name}.pgmx` — {note}")

    notes += [
        "", "## Gemelo manual (control de circularidad)", "",
        "- `R_PV_manual_base.pgmx` — crear EN MAESTRO una pieza nueva 400x400x18, origen",
        "  0/0/0, campo HG, SIN agregar ninguna operacion. Guardar en esta carpeta y",
        "  postprocesar. Dirime si un vacio hecho a mano difiere en algo del sintetizado",
        "  (regla 5 del CLAUDE.md: nuestro corpus tiene puntos ciegos por construccion).", "",
        "## Pendiente de la sesion de repaso de la UI", "",
        "Las opciones del programa que nuestro synth no puede variar (offset de pieza,",
        "repeticiones, ciclo continuo, espejo tecnologico, opciones de mesa/mecanica)",
        "se relevaran con capturas de la UI de Maestro y, si alguna interesa, con un",
        "gemelo manual variando SOLO esa opcion.",
    ]
    (out / "INSTRUCCIONES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
