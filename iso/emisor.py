r"""El cuarto origen: las líneas que pone el generador ISO y no salen de ningún archivo.

Lee `data/machine_config/emisor_iso.cfg`, donde vive el esqueleto del ISO con sus
`<marcadores>`, y lo arma con los valores de un programa concreto.

Por qué existe: sin este archivo, las 22 líneas que el emisor aporta al programa vacío
—`G71`, los `MLV`, `SYN`, el teardown de mesa, `M2`— tendrían que estar escritas dentro
del converter, y la regla 4 lo prohíbe. Acá son dato.

La regla de lectura es la del `NCI.CFG`, prestada a propósito: la línea se corta en el
primer `;` y lo anterior se emite tal cual, **con sus espacios finales**. Así los espacios
—que son parte del byte— quedan protegidos de cualquier editor que los recorte. Un `;`
literal se escribe `;;`.

Uso:
    py -m iso.emisor            # arma el esqueleto del programa vacío de referencia
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
EMISOR_CFG = RAIZ / "data" / "machine_config" / "emisor_iso.cfg"
NCI_CFG = (RAIZ / "data" / "machine_config" / "snapshot"
           / "xilog_plus" / "Cfg" / "NCI.CFG")

MARCADOR = re.compile(r"<([a-z_]+)>")
#: Fin de línea del ISO. No es negociable: el archivo de referencia es CRLF y termina
#: con CRLF.
CRLF = "\r\n"


def _sin_comentario(linea: str) -> str:
    """Corta en el primer `;` no escapado; `;;` es un `;` literal."""
    salida = []
    i = 0
    while i < len(linea):
        if linea[i] == ";":
            if linea[i:i + 2] == ";;":
                salida.append(";")
                i += 2
                continue
            break
        salida.append(linea[i])
        i += 1
    return "".join(salida)


def leer_bloques(path: Path = EMISOR_CFG) -> dict[str, list[str]]:
    """`$CLAVE` … `$`. Fuera de los bloques todo es comentario."""
    bloques: dict[str, list[str]] = {}
    clave: str | None = None
    # El archivo es NUESTRO y va en UTF-8 (tiene acentos). Los `.cfg` de la máquina son
    # cp1252 y se leen con su propio encoding; el ISO de salida también es cp1252, pero
    # las líneas del esqueleto son ASCII puro, así que no hay pérdida.
    for cruda in path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        if cruda.startswith("$") and len(cruda) > 1:
            clave = cruda[1:]
            bloques[clave] = []
        elif cruda == "$":
            clave = None
        elif clave is not None:
            bloques[clave].append(_sin_comentario(cruda))
    return bloques


def expandir(plantilla: list[str], valores: dict[str, object]) -> list[str]:
    """Rellena los `<marcadores>`.

    Un marcador que ocupa la línea entera se reemplaza por una lista de líneas: si la
    lista viene vacía, **la línea desaparece** (no queda una línea en blanco). El resto
    se sustituye dentro del texto.
    """
    salida: list[str] = []
    for linea in plantilla:
        solo = MARCADOR.fullmatch(linea.strip())
        if solo and linea.strip() == linea:
            valor = valores.get(solo.group(1))
            if valor is None:
                raise KeyError(f"falta el valor de <{solo.group(1)}>")
            salida.extend(valor if isinstance(valor, list) else [str(valor)])
            continue

        def _sustituir(m: re.Match) -> str:
            if m.group(1) not in valores:
                raise KeyError(f"falta el valor de <{m.group(1)}>")
            return str(valores[m.group(1)])

        salida.append(MARCADOR.sub(_sustituir, linea))
    return salida


def bloques_nci(path: Path = NCI_CFG) -> dict[str, list[str]]:
    """`$GEN_INIT` y `$GEN_END` del archivo de la máquina, ya emitidos.

    Misma regla de corte, más el desdoblado de `%%` que sí aplica allá: esas líneas
    pasan por un printf del emisor.
    """
    from iso.machining_lab.verificar_nci import emitir, leer_secciones

    secciones = leer_secciones(path)
    return {clave: [emitir(l) for l in secciones.get(clave, [])]
            for clave in ("GEN_INIT", "GEN_END")}


def componer(valores: dict[str, object], path: Path = EMISOR_CFG) -> str:
    """El ISO completo, con su CRLF final."""
    bloques = leer_bloques(path)
    lineas = expandir(bloques["EMI_ESQUELETO"], valores)
    return CRLF.join(lineas) + CRLF


def main(argv=None) -> int:
    nci = bloques_nci()
    iso = componer({
        "nombre_del_archivo": "r_pv_manual_base_cnc",
        "dx": "400.000", "dy": "400.000", "dz": "18.000",
        "bx": "0.000", "by": "0.000", "bz": "0.000",
        "area": "HG", "v": "0", "c": "0", "t": "0",
        "nci_gen_init": nci["GEN_INIT"],
        "nci_gen_end": nci["GEN_END"],
        "of_x": "-400000.000", "of_y": "-1515599.976", "of_z": "18000.000",
        "shf_x": "-400.000", "shf_y": "-1515.600", "shf_z": "18.000",
        "edk_mitad_mesa": "13",
        "cuerpo": [],
    })
    for numero, linea in enumerate(iso.split(CRLF), 1):
        print(f"{numero:3d}|{linea}|")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
