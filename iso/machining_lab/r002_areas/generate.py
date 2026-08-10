r"""R002 - Reinvestigacion: barrido de AREAS de trabajo (campo de ejecucion).

R001 dejo tres cosas sin resolver sobre el area (el «Área» de Parametros de maquina,
`ExecutionFields` en el `.pgmx`):

1. **La formula de `%Or[0].ofX` / `SHF[X]`.** Con area HG el emisor puso `-(DX+ox)`
   (-400 con pieza 400, -500 con pieza 500 y tambien -500 con pieza 400 + origen 100).
   Con area EF puso `-3688.000`, que es el X del campo E de `fields.cfg` TAL CUAL: si
   restara DX daria -4088. Una sola regla no explica las dos areas.
2. **La tabla de `?%EDK[n]`.** El indice cambio con el area: 13 con HG, 10 con EF.
3. **La correspondencia area -> bloque de `fields.cfg`.** El archivo trae 16 bloques de
   29 valores con una letra al final de cada uno; leyendolos como «la letra nombra al
   bloque que la precede», el `ofY` de HG sale de H (-1515.60) y el de EF sale de E
   (-1515.25) — o sea, el area de dos letras usaria la PRIMERA. Coincide en los dos
   casos conocidos, pero dos casos no son una tabla.

`fields.cfg` de esta maquina, con esa lectura (los campos I..P estan en cero):

    fila Y=0.00      A: X=-3685.85   B: X=-1843.00   C: X=-1843.00   D: X=0.00
    fila Y=-1515.xx  E: X=-3688.00   F: X=-1843.00   G: X=-1843.00   H: X=0.00
                        (-1515.25)      (-1515.75)      (-1515.75)      (-1515.60)

Este lote varia el AREA y, para tres de ellas, tambien DX y el origen X. Cada archivo
mata una hipotesis:

- **Grupo 1 (7 archivos)**: misma pieza, siete areas distintas. Da la tabla de `ofY` y
  de `EDK` de una pasada, y dice si el ORDEN de las letras importa (`CD` contra `DC`) y
  si una letra sola es un area valida (`A`).
- **Grupo 2 (3 archivos)**: la misma area con DX mas grande. Si `ofX` se mueve, el area
  resta la dimension; si no se mueve, no la resta. Es la pregunta 1, respondida por area.
- **Grupo 3 (1 archivo)**: `EF` con origen X. Separa «depende de DX» de «depende del
  origen», que en HG viajan juntos.

Uso: py -m iso.machining_lab.r002_areas.generate
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "R002_areas"

# Pieza de referencia: la misma de R001, para que los ISO sean comparables con el
# esqueleto ya derivado. Sin operaciones y sin Xn.
BASE = dict(length=400.0, width=400.0, depth=18.0,
            origin_x=0.0, origin_y=0.0, origin_z=0.0)

# Grupo 1: un area por archivo, todo lo demas igual.
AREAS = (
    ("ab", "AB", "fila Y=0, par A+B"),
    ("cd", "CD", "fila Y=0, par C+D"),
    ("ef", "EF", "fila Y=-1515, par E+F — CONTROL: R001 dio ofX=-3688.000, ofY=-1515.250"),
    ("gh", "GH", "fila Y=-1515, par G+H — el par de HG en orden directo"),
    ("hg", "HG", "CONTROL: R001 dio ofX=-400.000, ofY=-1515.600, EDK[13]"),
    ("dc", "DC", "CD al reves: ¿el ORDEN de las letras cambia algo?"),
    ("a", "A", "una letra sola: ¿es un area valida? ¿la normaliza Maestro a otra cosa?"),
)

# Grupo 2: misma area, DX mas grande. Si ofX cambia, el area resta la dimension.
DX_GRANDE = 600.0
AREAS_CON_DX = (("ab", "AB"), ("ef", "EF"), ("hg", "HG"))

# Grupo 3: EF con el origen corrido en X (en HG ya se sabe que suma; falta en EF).
ORIGEN_X = 100.0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    notas = [
        "# R002 - barrido de areas de trabajo", "",
        "Postprocesar TODO tal cual a `P:\\USBMIX\\ProdAction\\R002_areas\\`.", "",
        "Todos son programas SIN operaciones: solo cambia el **Área** de",
        "`Maquinas > Parametros > Parametros de maquina` (y, en el grupo 2, la medida).",
        "", "Si Maestro RECHAZA algun area, anotar el mensaje exacto: ese rechazo",
        "tambien es un dato (dice que combinaciones existen de verdad).", "",
        "## Grupo 1 - un area por archivo (pieza 400x400x18, origen 0/0/0)", "",
        "Responde: la tabla de `ofY` y de `?%EDK[n]` por area, si el ORDEN de las",
        "letras importa, y si una letra sola vale como area.", "",
    ]

    for sufijo, area, nota in AREAS:
        name = f"R_AR_{sufijo}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name,
            execution_fields=area, xn=None, **BASE))
        print(f"  {name}.pgmx: area {area} — {nota}")
        notas.append(f"- `{name}.pgmx` — area **{area}**. {nota}")

    notas += [
        "", f"## Grupo 2 - la misma area con DX={DX_GRANDE:.0f} (origen 0/0/0)", "",
        "Responde la pregunta principal: **¿el area resta la dimension al calcular",
        "`ofX`?** Comparar cada uno contra su gemelo del grupo 1.", "",
        "- Si `ofX` se mueve con DX -> el area resta la dimension.",
        "- Si `ofX` NO se mueve -> el area apoya la pieza en su propio tope y la",
        "  dimension no entra.", "",
    ]
    for sufijo, area in AREAS_CON_DX:
        name = f"R_AR_{sufijo}_dx{DX_GRANDE:.0f}"
        synthesize_request(build_synthesis_request(
            output_path=out / f"{name}.pgmx", piece_name=name,
            execution_fields=area, xn=None, **dict(BASE, length=DX_GRANDE)))
        print(f"  {name}.pgmx: area {area}, DX={DX_GRANDE:.0f}")
        notas.append(f"- `{name}.pgmx` — area **{area}**, pieza {DX_GRANDE:.0f}x400x18.")

    name = f"R_AR_ef_ox{ORIGEN_X:.0f}"
    synthesize_request(build_synthesis_request(
        output_path=out / f"{name}.pgmx", piece_name=name,
        execution_fields="EF", xn=None, **dict(BASE, origin_x=ORIGEN_X)))
    print(f"  {name}.pgmx: area EF, origen X={ORIGEN_X:.0f}")
    notas += [
        "", f"## Grupo 3 - area EF con origen X={ORIGEN_X:.0f}", "",
        "En HG ya se sabe que el origen se SUMA (R001: origen 100 movio `ofX` de -400",
        "a -500, y el header de 400 a 500). Falta saber si en EF pasa lo mismo, porque",
        "ahi `ofX` no siguio a la dimension.", "",
        f"- `{name}.pgmx` — area **EF**, pieza 400x400x18, origen X={ORIGEN_X:.0f}.", "",
        "## Que mirar al volver", "",
        "En cada ISO, estas cinco lineas:", "",
        "```",
        ";H DX=... DY=... DZ=...            <- envolvente (dimension + origen)",
        "%Or[0].ofX=...   %Or[0].ofY=...    <- origen en micras",
        "SHF[X]=...       SHF[Y]=...        <- lo mismo en mm",
        "?%EDK[n].0=1                       <- el indice n identifica el area",
        "```",
    ]
    (out / "INSTRUCCIONES.md").write_text("\n".join(notas) + "\n", encoding="utf-8")
    print("  INSTRUCCIONES.md escrito.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
