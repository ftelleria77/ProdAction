"""Lo derivado de las operaciones de máquina, fijado contra los ISO de Maestro.

Hasta el 2026-08-25 la rama C tenía 544 líneas de derivaciones en
`iso/docs/experiments/operaciones_maquina.md` y **ningún test las sostenía**. Es el mismo
agujero que la auditoría del 08-18 encontró en la geometría: derivado en un doc, no fijado
en código — y un doc no pone nada en rojo cuando alguien cambia una fórmula.

Estos tests NO ejercitan el converter (todavía no existe): comparan los `.pgmx` que hizo
Fermín en Maestro contra los `.iso` que produjo el CNC, y fijan las reglas que el converter
va a tener que reproducir. Si un fixture nuevo las contradice, esto cae.

Los 25 archivos están versionados en `evidencia/operaciones_c/`, así que la suite sigue
**100% offline**. Derivación completa en `operaciones_maquina.md`.
"""
from __future__ import annotations

import re
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIA = RAIZ / "iso" / "docs" / "experiments" / "evidencia" / "operaciones_c"


def _pgmx(nombre: str) -> str:
    ruta = EVIDENCIA / f"{nombre}.pgmx"
    with zipfile.ZipFile(ruta) as zf:
        interno = next(i.filename for i in zf.infolist() if i.filename.lower().endswith(".xml"))
        return zf.read(interno).decode("utf-8", "replace")


def _iso(nombre: str) -> list:
    ruta = EVIDENCIA / f"{nombre.lower()}.iso"
    return ruta.read_text(encoding="cp1252").replace("\r\n", "\n").split("\n")


def _nodos(xml: str, tipo: str) -> list:
    return re.findall(rf'<Executable i:type="{tipo}".*?</Executable>', xml, re.S)


def _campo(nodo: str, tag: str):
    m = re.search(rf"<{tag}\s*/>|<{tag}\s+i:nil=\"true\"\s*/>|<{tag}>(.*?)</{tag}>", nodo, re.S)
    if m is None:
        return None
    return "nil" if m.group(1) is None else m.group(1)


def _shf(lineas: list) -> dict:
    """Primer bloque `SHF` del ISO: el origen de la pieza."""
    out = {}
    for l in lineas:
        m = re.match(r"SHF\[([XYZ])\]=(-?[\d.]+)", l)
        if m and m.group(1) not in out:
            out[m.group(1)] = float(m.group(2))
    return out


def _g53(lineas: list) -> list:
    return [l.strip() for l in lineas if re.match(r"G[01] G53 X", l)]


def _cuerpo(nombre: str, base: str) -> list:
    """Líneas que el fixture agrega sobre su programa base."""
    import difflib
    b, o = _iso(base), _iso(nombre)
    return [l for t, l in ((x[0], x[2:]) for x in difflib.ndiff(b, o))
            if t == "+" and not l.startswith("% ")]


def _enes(nombre: str) -> list:
    """Los conteos `$0?N` que lleva el ISO, en orden."""
    return [int(m) for m in re.findall(r"\$0\?(\d+)S", "\n".join(_iso(nombre)))]


BASE_HG = "R_PV_HG_manual_op"


class XnCoordenadasTest(unittest.TestCase):
    """`X` va directo; la `Y` invierte el signo; `Relative` corre por el `SHF`."""

    def test_x_absoluta_va_sin_transformar(self):
        self.assertIn("G0 G53 X-3700.000", _g53(_iso("R_PV_HG_manual_op_XN_x-3700_Ab_NT"))[0])

    def test_la_y_invierte_el_signo(self):
        nodo = _nodos(_pgmx("R_PV_HG_manual_op_XN_x-3700_y-1000_Ab_NT"), "Xn")[0]
        self.assertEqual(_campo(nodo, "Y"), "-1000")
        self.assertIn("Y1000.000", _g53(_iso("R_PV_HG_manual_op_XN_x-3700_y-1000_Ab_NT"))[0])

    def test_sin_y_el_iso_no_emite_y(self):
        """«Sin Y» y «Y=0» son casos distintos, y el `.pgmx` los separa."""
        nodo = _nodos(_pgmx("R_PV_HG_manual_op_XN_x-3700_Ab_NT"), "Xn")[0]
        self.assertEqual(_campo(nodo, "Y"), "nil")
        self.assertNotIn("Y", _g53(_iso("R_PV_HG_manual_op_XN_x-3700_Ab_NT"))[0].split("X")[1])

    def test_relative_suma_el_shf_en_x_y_lo_resta_en_y(self):
        nombre = "R_PV_HG_manual_op_XN_x-3700_y-1000_Re_NT"
        nodo = _nodos(_pgmx(nombre), "Xn")[0]
        self.assertEqual(_campo(nodo, "Reference"), "Relative")
        x, y = float(_campo(nodo, "X")), float(_campo(nodo, "Y"))
        shf = _shf(_iso(nombre))
        linea = _g53(_iso(nombre))[0]
        self.assertIn(f"X{x + shf['X']:.3f}", linea)
        self.assertIn(f"Y{y - shf['Y']:.3f}", linea)


class XnVelocidadYHerramientaTest(unittest.TestCase):
    def test_speed_cero_emite_g0_sin_avance(self):
        linea = _g53(_iso("R_PV_HG_manual_op_XN_x-3700_Ab_NT"))[0]
        self.assertTrue(linea.startswith("G0 G53"))
        self.assertNotIn("F", linea)

    def test_speed_no_nulo_emite_g1_y_avance_por_mil(self):
        nombre = "R_PV_manual_op_XN_x-3700_Ab_V10_E001"
        speed = float(_campo(_nodos(_pgmx(nombre), "Xn")[0], "Speed"))
        linea = _g53(_iso(nombre))[0]
        self.assertTrue(linea.startswith("G1 G53"))
        self.assertIn(f"F{speed * 1000:.3f}", linea)

    def test_la_herramienta_agrega_el_cambio(self):
        cuerpo = _cuerpo("R_PV_HG_manual_op_XN_x-3700_Ab_E001", BASE_HG)
        planas = [l.strip() for l in cuerpo]
        self.assertIn("T1", planas)
        self.assertIn("M06", planas)


class BloqueDeOperacionesTest(unittest.TestCase):
    """El `?%ETK[8]=1` + `G40` son preámbulo del BLOQUE, no del `Xn`."""

    def test_un_xn_son_dos_de_preambulo_mas_seis(self):
        cuerpo = [l.strip() for l in _cuerpo("R_PV_HG_manual_op_XN_x-3700_Ab_NT", BASE_HG)]
        self.assertEqual(len(cuerpo), 8)
        self.assertEqual(cuerpo[:2], ["?%ETK[8]=1", "G40"])

    def test_el_segundo_xn_no_repite_el_mlv(self):
        cuerpo = [l.strip() for l in _cuerpo("R_PV_HG_manual_op_XN_x-3700_Ab_NT_XN_dos", BASE_HG)]
        self.assertEqual(len(cuerpo), 13, "2 de preámbulo + 6 del primero + 5 del segundo")
        self.assertEqual(cuerpo.count("MLV=0"), 1)
        self.assertEqual(len(_g53(_iso("R_PV_HG_manual_op_XN_x-3700_Ab_NT_XN_dos"))), 2)

    def test_el_orden_de_la_lista_se_respeta(self):
        """`OPS_tres` es `Xn` -> `Xmsg` -> `Park`, y así salen."""
        cuerpo = [l.strip() for l in _cuerpo("R_PV_HG_manual_op_OPS_tres", BASE_HG)]
        i_xn = cuerpo.index("G0 G53 X-3700.000")
        i_msg = next(k for k, l in enumerate(cuerpo) if l.startswith("$0?"))
        i_park = next(k for k, l in enumerate(cuerpo) if l.startswith("G0G53 X%ax"))
        self.assertLess(i_xn, i_msg)
        self.assertLess(i_msg, i_park)


class XmsgTest(unittest.TestCase):
    def test_el_texto_no_viaja_al_iso(self):
        texto = _campo(_nodos(_pgmx("R_PV_HG_manual_op_XMSG_prueba"), "Xmsg")[0], "Text")
        self.assertEqual(texto, "PRUEBA")
        iso = "\n".join(_iso("R_PV_HG_manual_op_XMSG_prueba"))
        self.assertNotIn("PRUEBA", iso)

    def test_el_xmsg_son_dos_lineas(self):
        cuerpo = [l.strip() for l in _cuerpo("R_PV_HG_manual_op_XMSG_prueba", BASE_HG)]
        self.assertEqual(len(cuerpo), 4, "2 de preámbulo + 2 propias")
        self.assertTrue(cuerpo[2].startswith("$0?"))
        self.assertEqual(cuerpo[3], "G4 F0")

    def test_el_conteo_lo_incrementa_cada_elemento_anterior(self):
        """`N = conteo inicial + Σ incrementos`. Base 212 en AB, 213 en HG."""
        self.assertEqual(_enes("R_PV_HG_manual_op_XMSG_prueba"), [213])
        self.assertEqual(_enes("R_PV_HG_manual_op_XMSG_dos"), [213, 226])
        self.assertEqual(_enes("R_PV_HG_manual_op_OPS_tres"), [213 + 45], "un `Xn` antes")

    def test_el_incremento_de_un_xmsg_es_el_largo_del_texto_mas_siete(self):
        """El incremento NO es fijo: depende del contenido (derivado 2026-08-25).

        `xmsg_dos` y `xmsg_dos_largo` sólo difieren en el largo del PRIMER mensaje, y el
        conteo del segundo se corre exactamente lo mismo que crece el texto: de 6 a 25
        caracteres mueve el incremento de 13 a 32. La pendiente queda en 1 por el delta,
        y la ordenada en 7 por los dos puntos.
        """
        for nombre in ("R_PV_manual_op_XMSG_dos", "R_PV_manual_op_XMSG_dos_largo"):
            primero, segundo = _enes(nombre)
            texto = _campo(_nodos(_pgmx(nombre), "Xmsg")[0], "Text")
            with self.subTest(fixture=nombre):
                self.assertEqual(primero, 212, "el largo del propio mensaje no mueve su N")
                self.assertEqual(segundo - primero, len(texto) + 7)


class ParkTest(unittest.TestCase):
    def test_el_park_depende_del_campo(self):
        """HG usa `%ax0.pa21`; el campo AB usa `%ax0.pa31` y agrega un `_paras`."""
        hg = [l.strip() for l in _cuerpo("R_PV_HG_manual_op_PARK", BASE_HG)][2:]
        ab = [l.strip() for l in _cuerpo("R_PV_manual_op_PARK", "R_PV_manual_op")][2:]
        self.assertEqual(len(hg), 2)
        self.assertEqual(len(ab), 3)
        self.assertIn("X%ax0.pa21/1000", hg[0])
        self.assertIn("X%ax0.pa31/1000", ab[1])

    def test_es_el_mismo_bloque_que_el_estacionamiento_automatico(self):
        """El `Park` de la UI emite lo mismo que `$EMI_PARK_FINAL` (derivado de `eafe_*`)."""
        from iso.emisor import leer_bloques
        automatico = [l for l in leer_bloques()["EMI_PARK_FINAL"]]
        manual = [l.rstrip() for l in _cuerpo("R_PV_HG_manual_op_PARK", BASE_HG)][2:]
        self.assertEqual([l.rstrip() for l in automatico], manual)


class NoLleganAlIsoTest(unittest.TestCase):
    """Campos que existen en el `.pgmx` y no tienen efecto en el ISO."""

    def test_el_stop_del_park_no_llega(self):
        a, b = "R_PV_HG_manual_op_PARK", "R_PV_HG_manual_op_PARK_pes"
        self.assertEqual(_campo(_nodos(_pgmx(a), "Park")[0], "Stop"), "Nothing")
        self.assertEqual(_campo(_nodos(_pgmx(b), "Park")[0], "Stop"), "NoUnlock")
        # la linea 1 lleva el nombre del archivo; el resto tiene que salir igual
        self.assertEqual(_iso(a)[1:], _iso(b)[1:])

    def test_el_electromandril_no_llega(self):
        a, b = "R_PV_HG_manual_op_XN_x-3700_Ab_E001", "R_PV_HG_manual_op_XN_x-3700_Ab_E001_SpEncendido"
        self.assertEqual(_campo(_nodos(_pgmx(a), "Xn")[0], "SpindleEnable"), "Off")
        self.assertNotEqual(_campo(_nodos(_pgmx(b), "Xn")[0], "SpindleEnable"), "Off")
        self.assertEqual(_iso(a)[1:], _iso(b)[1:])


if __name__ == "__main__":
    unittest.main()
