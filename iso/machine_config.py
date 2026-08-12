r"""Refresco y verificación del snapshot de configuración de máquina.

El snapshot (`iso/data/machine_config/snapshot/`) es la **fuente única** de la
configuración de la máquina, y el requisito del 2026-08-04 es explícito: sale SIEMPRE de
los archivos extraídos de la PC del CNC, y refrescar significa sobreescribir la carpeta.

Este módulo existe porque ese requisito no se podía verificar. El 2026-08-12, con una copia
completa del CNC a mano, apareció que dos archivos del snapshot venían de la PC de oficina
técnica —entre ellos `Maestro.rel`, **justamente el que declara la versión**, que decía
`1.00.006.1010` cuando el CNC tiene `1.00.006.1009`—. No fue un descuido de nadie: el
snapshot se armó desde los shares `S:\Xilog Plus` y `S:\Maestro`, que para Xilog reflejan
al CNC (81 de 82 archivos byte-idénticos) y para Maestro no.

Modo de uso:

    py -m iso.machine_config verificar --fuente "S:\Copia CNC"
    py -m iso.machine_config refrescar --fuente "S:\Copia CNC"

`verificar` no escribe nada: dice qué archivos del snapshot ya no coinciden con la máquina
y cuáles no existen allá. `refrescar` copia y regenera el manifest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SNAPSHOT = RAIZ / "data" / "machine_config" / "snapshot"
MANIFEST = SNAPSHOT / "manifest.csv"

#: Qué entra al snapshot. `destino` es la carpeta bajo `snapshot/`; `origen` es la ruta
#: relativa dentro de la copia del CNC; `patron` selecciona los archivos.
#:
#: El snapshot es un RECORTE deliberado de la instalación (~2.900 archivos), no una copia.
#: Agregar acá lo que se necesite, con el motivo escrito.
SELECCION = (
    # destino,             origen,                        patrón
    ("xilog_plus",         r"Xilog Plus\Bin",              "axis.ini"),
    ("xilog_plus/Cfg",     r"Xilog Plus\Cfg",              "*"),
    ("xilog_plus/Job",     r"Xilog Plus\Job",              "def.tlg"),
    ("maestro/Cfgx",       r"Maestro\Cfgx",                "Head.cfg"),
    ("maestro/Cfgx",       r"Maestro\Cfgx",                "Maestro.rel"),
    ("maestro/Cfgx",       r"Maestro\Cfgx",                "Programaciones.settingsx"),
    ("maestro/Tlgx",       r"Maestro\Tlgx",                "def.tlgx"),
    ("maestro/Tlgx",       r"Maestro\Tlgx",                "def.old"),
    # El tercer origen: la ventana Opciones (configuración global de la aplicación).
    ("maestro_ui",         r"Maestro",                     "UI00.exe.Config"),
    # Plantilla de fábrica de esa ventana y ajustes de la instalación (E1).
    ("maestro/Settings",   r"Maestro\Settings",            "*"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _pares(fuente: Path):
    """(archivo en la fuente, ruta relativa dentro del snapshot, carpeta destino)."""
    for destino, origen, patron in SELECCION:
        carpeta = fuente / origen
        if not carpeta.is_dir():
            continue
        for archivo in sorted(carpeta.glob(patron)):
            if archivo.is_file():
                yield archivo, Path(destino) / archivo.name, destino, origen


def verificar(fuente: Path) -> int:
    iguales, distintos, ausentes, nuevos = [], [], [], []
    esperados = set()
    for archivo, rel, _destino, _origen in _pares(fuente):
        esperados.add(rel)
        copia = SNAPSHOT / rel
        if not copia.exists():
            nuevos.append(rel)
        elif sha256(copia) == sha256(archivo):
            iguales.append(rel)
        else:
            distintos.append(rel)

    for copia in sorted(SNAPSHOT.rglob("*")):
        if copia.is_file() and copia != MANIFEST:
            rel = copia.relative_to(SNAPSHOT)
            if rel not in esperados:
                ausentes.append(rel)

    print(f"fuente: {fuente}")
    print(f"  {len(iguales)} iguales")
    print(f"  {len(distintos)} DISTINTOS — el snapshot quedó viejo o es de otra máquina")
    for rel in distintos:
        print(f"      {rel}")
    print(f"  {len(nuevos)} en la máquina y NO en el snapshot")
    for rel in nuevos:
        print(f"      {rel}")
    print(f"  {len(ausentes)} en el snapshot y NO en la máquina")
    for rel in ausentes:
        print(f"      {rel}")
    return 1 if (distintos or nuevos or ausentes) else 0


def refrescar(fuente: Path, etiqueta_fuente: str) -> int:
    filas = []
    escritos = 0
    for archivo, rel, destino, origen in _pares(fuente):
        copia = SNAPSHOT / rel
        copia.parent.mkdir(parents=True, exist_ok=True)
        if not copia.exists() or sha256(copia) != sha256(archivo):
            shutil.copy2(archivo, copia)
            escritos += 1
        filas.append({
            "source_root": f"{etiqueta_fuente}\\{origen}",
            "snapshot_root": destino,
            "relative_path": archivo.name,
            "bytes": str(archivo.stat().st_size),
            "sha256": sha256(archivo),
        })

    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as fh:
        escritor = csv.DictWriter(
            fh, fieldnames=["source_root", "snapshot_root", "relative_path",
                            "bytes", "sha256"], quoting=csv.QUOTE_ALL)
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"{len(filas)} archivos en el manifest · {escritos} copiados o actualizados")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="modo", required=True)
    for nombre in ("verificar", "refrescar"):
        p = sub.add_parser(nombre)
        p.add_argument("--fuente", type=Path, required=True,
                       help=r'copia de la PC del CNC, ej. "S:\Copia CNC"')
        if nombre == "refrescar":
            p.add_argument("--etiqueta", default=r"PC del CNC (C:\Archivos de programa\Scm Group)",
                           help="qué se escribe como source_root en el manifest")
    args = ap.parse_args(argv)
    if args.modo == "verificar":
        return verificar(args.fuente)
    return refrescar(args.fuente, args.etiqueta)


if __name__ == "__main__":
    raise SystemExit(main())
