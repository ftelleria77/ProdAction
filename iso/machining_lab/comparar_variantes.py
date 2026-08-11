r"""Compara un juego de ISOs contra una referencia y muestra SOLO lo que cambia.

Pensado para los barridos de un parámetro por archivo: si cada fixture varía una sola
cosa, las líneas que se mueven son la respuesta. Sirve para cualquier serie R —
parámetros de máquina, áreas, o lo que venga con los mecanizados.

Uso:
    py -m iso.machining_lab.comparar_variantes <carpeta_iso> [referencia.iso]

Si no se indica referencia, usa el ISO más chico de la carpeta (suele ser el base).
Clasifica cada variante en tres cajones:

    IDÉNTICO   el parámetro NO viaja al postprocesado — es un resultado, no un fracaso
    SÓLO NOMBRE  cambia únicamente la línea 1 (el nombre del archivo)
    DIFIERE    hay diferencias reales, y se listan línea por línea
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

# La línea 1 del ISO es el nombre del archivo: cambia siempre y no es un hallazgo.
_LINEA_DEL_NOMBRE = 1


def _lineas(path: Path) -> list[str]:
    return path.read_text(encoding="cp1252").replace("\r\n", "\n").split("\n")


def comparar(referencia: Path, variante: Path) -> tuple[str, list[str]]:
    """Devuelve (veredicto, líneas del diff sin contar el nombre del archivo)."""
    ref, var = _lineas(referencia), _lineas(variante)
    if ref == var:
        return "IDENTICO", []

    diff = []
    for linea in difflib.unified_diff(ref, var, "ref", "var", lineterm="", n=1):
        if linea.startswith(("---", "+++", "@@")):
            continue
        diff.append(linea)

    # ¿todo lo que cambió es la línea del nombre? Sólo cuentan las líneas AGREGADAS o
    # QUITADAS: las de contexto empiezan con espacio y no son diferencias (si se las
    # contara, ningún archivo daría nunca "SOLO NOMBRE").
    cambios = [d for d in diff if d[:1] in "-+"]
    reales = [d for d in cambios if not d[1:].lstrip().startswith("%")]
    if not reales:
        return "SOLO NOMBRE", []
    return "DIFIERE", diff


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("carpeta", type=Path)
    parser.add_argument("referencia", nargs="?", default=None)
    args = parser.parse_args(argv)

    isos = sorted(args.carpeta.glob("*.iso"))
    if not isos:
        print(f"No hay .iso en {args.carpeta}")
        return 1

    if args.referencia:
        referencia = args.carpeta / args.referencia
        if not referencia.exists():
            print(f"No existe la referencia {referencia}")
            return 1
    else:
        referencia = min(isos, key=lambda p: p.stat().st_size)

    print(f"referencia: {referencia.name}  ({len(_lineas(referencia))} líneas)")
    print()

    resumen: dict[str, list[str]] = {"IDENTICO": [], "SOLO NOMBRE": [], "DIFIERE": []}
    for iso in isos:
        if iso == referencia:
            continue
        veredicto, diff = comparar(referencia, iso)
        resumen[veredicto].append(iso.stem)
        if veredicto == "DIFIERE":
            print("=" * 72)
            print(f"{iso.stem}   [{veredicto}]")
            print("=" * 72)
            print("\n".join(diff))
            print()

    print("=" * 72)
    print("RESUMEN")
    print("=" * 72)
    for veredicto in ("DIFIERE", "SOLO NOMBRE", "IDENTICO"):
        nombres = resumen[veredicto]
        if not nombres:
            continue
        print(f"\n{veredicto} ({len(nombres)}):")
        for n in nombres:
            print(f"  {n}")
    if resumen["IDENTICO"] or resumen["SOLO NOMBRE"]:
        print("\nNota: 'IDENTICO' y 'SOLO NOMBRE' significan que ese parámetro NO llegó")
        print("al ISO. Es un resultado con valor: dice que no viaja al postprocesado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
