r"""Procesa la serie R_OPC: barrido de la ventana Opciones sobre el mismo programa base.

Para cada fixture responde las dos preguntas de la serie, que son distintas:

  1. ¿el `.pgmx` cambió?  -> si el XML difiere del base, la opción SE ESCRIBE en el
     archivo (viaja con el programa). Si es byte-idéntico, es de la aplicación.
  2. ¿el `.iso` cambió?   -> si difiere en algo más que la línea 1 (el nombre del
     archivo), la opción LLEGA al postprocesado.

Las dos son independientes: una opción puede no estar en el archivo y aun así decidir el
ISO — de hecho es lo que se está buscando.

Uso:
    py -m iso.machining_lab.procesar_opciones
"""
from __future__ import annotations

import argparse
import difflib
import zipfile
from pathlib import Path

RAIZ = Path(r"S:\Maestro\Projects\ProdAction\Programas Manuales\Reinvestigación")
BASE_PGMX = RAIZ / "R_PV_manual_base.pgmx"
BASE_ISO = Path(r"P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación"
                r"\r_pv_manual_base.iso")
VARIANTES_PGMX = RAIZ / "Opciones de Maestro"
VARIANTES_ISO = Path(r"P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación"
                     r"\Opciones de Maestro")


def _xml(path: Path) -> tuple[str, str]:
    """(contenido del XML, crc en hexa) del .pgmx."""
    zf = zipfile.ZipFile(path)
    info = next(i for i in zf.infolist() if i.filename.lower().endswith(".xml"))
    return zf.read(info.filename).decode("utf-8"), f"{info.CRC:08x}"


def _iso(path: Path) -> list[str]:
    return path.read_text(encoding="cp1252").replace("\r\n", "\n").split("\n")


def _diff_iso(base: list[str], var: list[str]) -> list[str]:
    """Diferencias SIN contar la línea 1, que es el nombre del archivo."""
    crudo = [d for d in difflib.unified_diff(base, var, lineterm="", n=0)
             if d[:1] in "-+" and not d.startswith(("---", "+++"))]
    return [d for d in crudo if not d[1:].lstrip().startswith("%")]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pgmx-dir", type=Path, default=VARIANTES_PGMX)
    parser.add_argument("--iso-dir", type=Path, default=VARIANTES_ISO)
    args = parser.parse_args(argv)

    xml_base, crc_base = _xml(BASE_PGMX)
    iso_base = _iso(BASE_ISO)
    print(f"base: XML {len(xml_base):,} bytes crc={crc_base} · "
          f"ISO {len(iso_base)} líneas")
    print()

    encabezado = f"{'fixture':30s} {'XML vs base':13s} {'ISO vs base':13s}"
    print(encabezado)
    print("-" * len(encabezado))

    pendientes = []
    for pgmx in sorted(args.pgmx_dir.glob("*.pgmx")):
        xml_var, crc_var = _xml(pgmx)
        igual_xml = "IDÉNTICO" if xml_var == xml_base else "DIFIERE"

        iso_path = args.iso_dir / f"{pgmx.stem.lower()}.iso"
        if not iso_path.exists():
            estado_iso = "(sin ISO)"
            diff = []
        else:
            diff = _diff_iso(iso_base, _iso(iso_path))
            estado_iso = "DIFIERE" if diff else "sólo el nombre"

        print(f"{pgmx.stem:30s} {igual_xml:13s} {estado_iso:13s}")
        if diff:
            pendientes.append((pgmx.stem, diff))

    if pendientes:
        print()
        print("=" * 72)
        print("DIFERENCIAS REALES EN EL ISO (más allá del nombre del archivo)")
        print("=" * 72)
        for nombre, diff in pendientes:
            print(f"\n[{nombre}]")
            print("\n".join(diff))
    else:
        print()
        print("Ningún fixture cambió el ISO más allá del nombre del archivo.")
        print("Para estas opciones eso es un RESULTADO: no llegan al postprocesado de un")
        print("programa sin operaciones. Las que gobiernan trazas necesitan un mecanizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
