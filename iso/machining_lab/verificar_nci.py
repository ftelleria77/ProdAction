r"""Cruza el preámbulo y el cierre de un ISO contra `NCI.CFG` de la máquina.

El generador ISO copia dos bloques del archivo de configuración **literalmente**:

  `$GEN_INIT` -> el preámbulo, después de la cabecera
  `$GEN_END`  -> el bloque de reset de registros, dentro del cierre

La copia no es cruda: aplica una regla de emisión, que este módulo implementa en
`emitir()` y verifica contra el ISO real.

  1. se corta la línea en el primer `;` (el comentario no se emite, pero **lo que
     quedó antes sí, con sus espacios**);
  2. `%%` se desdobla a `%`.

Una línea que es toda comentario queda entonces como **línea vacía** — no
desaparece — y una con comentario al final conserva el espacio que lo separaba.

Uso:
    py -m iso.machining_lab.verificar_nci
    py -m iso.machining_lab.verificar_nci --iso <ruta.iso>
"""
from __future__ import annotations

import argparse
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parents[1] / "data" / "machine_config" / "snapshot"
NCI = SNAPSHOT / "xilog_plus" / "Cfg" / "NCI.CFG"
ISO_BASE = Path(r"P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación"
                r"\r_pv_manual_base.iso")


def leer_secciones(nci: Path) -> dict[str, list[str]]:
    """Las secciones de un .CFG de Xilog: `$CLAVE`, valores, y un `$` que cierra."""
    lineas = nci.read_text(encoding="cp1252").replace("\r\n", "\n").split("\n")
    secciones: dict[str, list[str]] = {}
    clave: str | None = None
    for linea in lineas:
        if linea.startswith("$") and len(linea) > 1:
            clave = linea[1:]
            secciones[clave] = []
        elif linea == "$":
            clave = None
        elif clave is not None:
            secciones[clave].append(linea)
    return secciones


def emitir(linea: str) -> str:
    """La regla de emisión: cortar en el primer `;`, desdoblar `%%`."""
    return linea.split(";", 1)[0].replace("%%", "%")


def buscar_bloque(iso: list[str], bloque: list[str]) -> int | None:
    """Índice (0-based) donde `bloque` aparece contiguo en `iso`, o None."""
    if not bloque:
        return None
    for i in range(len(iso) - len(bloque) + 1):
        if iso[i:i + len(bloque)] == bloque:
            return i
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--iso", type=Path, default=ISO_BASE)
    parser.add_argument("--nci", type=Path, default=NCI)
    args = parser.parse_args(argv)

    secciones = leer_secciones(args.nci)
    iso = args.iso.read_text(encoding="cp1252").replace("\r\n", "\n").split("\n")

    print(f"NCI: {args.nci}")
    print(f"ISO: {args.iso}  ({len(iso)} líneas)")
    print()

    cubiertas: set[int] = set()
    for clave in ("GEN_INIT", "GEN_END"):
        crudo = secciones.get(clave, [])
        bloque = [emitir(l) for l in crudo]
        inicio = buscar_bloque(iso, bloque)
        estado = f"línea {inicio + 1}" if inicio is not None else "NO APARECE"
        print(f"${clave}: {len(bloque)} líneas -> {estado}")
        for n, (origen, salida) in enumerate(zip(crudo, bloque)):
            marca = f"{inicio + n + 1:3d}" if inicio is not None else "  ?"
            print(f"  {marca} | {origen!r}")
            if origen != salida:
                print(f"      -> {salida!r}")
        if inicio is not None:
            cubiertas.update(range(inicio, inicio + len(bloque)))
        print()

    print("Líneas del ISO que NO salen de NCI.CFG (las pone el emisor):")
    for i, linea in enumerate(iso):
        if i not in cubiertas and linea:
            print(f"  {i + 1:3d} | {linea}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
