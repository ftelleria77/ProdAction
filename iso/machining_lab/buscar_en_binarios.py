r"""Busca las plantillas de una línea del ISO en los binarios de Xilog Plus y Maestro.

Cuando una línea del ISO no sale del `.pgmx` ni de un `.cfg`, la escribe algún módulo del
emisor. Sus plantillas `printf` están en la tabla de cadenas del binario, y **las cadenas
vecinas suelen ser las del mismo bloque de emisión**: por eso este módulo muestra contexto
en vez de la coincidencia sola. Así apareció que el teardown del esqueleto es del módulo de
mesa (ver `docs/experiments/anatomia_iso.md`, B1g).

Dos modos:

  `barrer`   — qué binario contiene cada patrón, en las dos instalaciones enteras.
  `contexto` — las cadenas vecinas de cada coincidencia dentro de un binario.

Ojo con dos cosas al leer los resultados:

- **Contigüidad no es prueba.** Que dos cadenas estén juntas en la tabla sugiere que el
  código las emite junto; no lo demuestra. Vale como HIPÓTESIS.
- **Esto dice quién ESCRIBE la línea, no de dónde sale su VALOR.** Son preguntas distintas
  (`NCI.CFG` mostró que parte del preámbulo, que parecía fijo, es configuración).

Uso:
    py -m iso.machining_lab.buscar_en_binarios barrer "VL[67]=" "SHF\[Z\]"
    py -m iso.machining_lab.buscar_en_binarios contexto <binario> "^VL[67]=" --ctx 20
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

RAICES = (
    Path(r"C:\Program Files (x86)\Scm Group\Xilog Plus"),
    Path(r"C:\Program Files (x86)\Scm Group\Maestro"),
)
LIMITE_BYTES = 60 * 1024 * 1024

_ASCII = rb"[\x20-\x7e]{%d,}"
_WIDE = rb"(?:[\x20-\x7e]\x00){%d,}"


def cadenas(data: bytes, minimo: int = 3, wide: bool = False) -> list[tuple[int, str]]:
    """Cadenas imprimibles con su offset. `wide` agrega las UTF-16LE (binarios .NET)."""
    salida = [(m.start(), m.group().decode("ascii"))
              for m in re.finditer(_ASCII % minimo, data)]
    if wide:
        salida += [(m.start(), m.group().decode("utf-16-le"))
                   for m in re.finditer(_WIDE % minimo, data)]
    return salida


def _archivos(raices=RAICES):
    for raiz in raices:
        if not raiz.exists():
            continue
        for path in sorted(raiz.rglob("*")):
            if path.is_file():
                yield path


def barrer(patrones: list[str], solo_ejecutables: bool = True) -> int:
    compilados = {p: re.compile(p) for p in patrones}
    hallazgos: dict[str, list[tuple[Path, str]]] = {p: [] for p in patrones}
    revisados = 0
    for path in _archivos():
        if solo_ejecutables and path.suffix.lower() not in {".dll", ".exe"}:
            continue
        try:
            if path.stat().st_size > LIMITE_BYTES:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        revisados += 1
        texto = [s for _, s in cadenas(data, wide=True)]
        for patron, rx in compilados.items():
            for s in texto:
                if rx.search(s):
                    hallazgos[patron].append((path, s))
                    break

    print(f"{revisados} binarios revisados\n")
    for patron, lista in hallazgos.items():
        print(f"### /{patron}/")
        if not lista:
            print("   (ninguno) — la cadena no existe como literal; se compone en runtime")
        for path, ejemplo in lista[:10]:
            print(f"   {path.name:28s} {ejemplo[:70]!r}")
        print()
    return 0


def contexto(binario: Path, patron: str, ctx: int, maximo: int) -> int:
    todas = cadenas(binario.read_bytes())
    rx = re.compile(patron)
    hits = [i for i, (_, s) in enumerate(todas) if rx.search(s)]
    print(f"{binario.name}: {len(todas):,} cadenas · {len(hits)} coinciden")
    vistos: set[int] = set()
    mostrados = 0
    for i in hits:
        if i in vistos or mostrados >= maximo:
            continue
        lo, hi = max(0, i - ctx), min(len(todas), i + ctx + 1)
        vistos.update(range(lo, hi))
        mostrados += 1
        print(f"\n--- offset 0x{todas[i][0]:X} ---")
        for j in range(lo, hi):
            marca = ">>" if rx.search(todas[j][1]) else "  "
            print(f"{marca} {todas[j][1]}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="modo", required=True)

    b = sub.add_parser("barrer", help="qué binario contiene cada patrón")
    b.add_argument("patrones", nargs="+")
    b.add_argument("--todos-los-archivos", action="store_true",
                   help="no limitarse a .dll/.exe (más lento)")

    c = sub.add_parser("contexto", help="cadenas vecinas de cada coincidencia")
    c.add_argument("binario", type=Path)
    c.add_argument("patron")
    c.add_argument("--ctx", type=int, default=12)
    c.add_argument("--max", type=int, default=6)

    args = ap.parse_args(argv)
    if args.modo == "barrer":
        return barrer(args.patrones, solo_ejecutables=not args.todos_los_archivos)
    return contexto(args.binario, args.patron, args.ctx, args.max)


if __name__ == "__main__":
    raise SystemExit(main())
