"""La geometría que emite el sintetizador tiene que salir como la escribe Maestro.

Hasta el 2026-08-19 **sólo la línea** estaba respaldada por fixtures de la época nueva. El
arco, el círculo y la polilínea se validaban por *roundtrip contra nosotros mismos*
(`test_pgmx_arc_authoring.py`), y su única ancla externa era N040 — serie N, época
congelada, declarada no-fuente. Es el punto ciego de la regla 5 del CLAUDE.md: el corpus no
puede contener lo que su propia autoría no produjo.

El lote «Rama G» (88 `.pgmx` manuales de Fermín) cerró ese hueco y destapó un defecto real:
**el espacio final antes del salto de línea es por CÓDIGO DE CURVA** —la recta `1` lo lleva,
las cónicas `2` y `3` no— y el sintetizador se lo ponía también al arco. Este test fija la
regla contra archivos de Maestro para que nadie la vuelva a mover sin evidencia.

Los once fixtures están versionados en `evidencia/dibujos_rama_g/`, así que la suite sigue
**100% offline**: no hace falta S: ni P:. Derivación completa en
`iso/docs/experiments/dibujos.md`, sección 12.
"""
from __future__ import annotations

import re
import unittest
import zipfile
from pathlib import Path

from pgmx.synthesis.common import geometry as G

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIA = RAIZ / "iso" / "docs" / "experiments" / "evidencia" / "dibujos_rama_g"

_SERIALIZACION = re.compile(
    r"<a:_serializationGeometryDescription>(.*?)</a:_serializationGeometryDescription>", re.S
)
_MIEMBRO = re.compile(r"<b:string>(.*?)</b:string>", re.S)

TODOS = (
    "linea_01", "arco_01", "arco_04", "circulo_01", "elipse_01",
    "polilinea_01", "polilinea_11", "poligono_01", "rectangulo_01",
    "rectangulo_07", "punto_01",
)


def _geometrias(nombre: str) -> str:
    """Bloque `<Geometries>` de un `.pgmx` del lote (el `.pgmx` es un ZIP)."""
    ruta = EVIDENCIA / f"R_PV_manual_base_{nombre}.pgmx"
    with zipfile.ZipFile(ruta) as zf:
        interno = next(i.filename for i in zf.infolist() if i.filename.lower().endswith(".xml"))
        xml = zf.read(interno).decode("utf-8")
    return re.search(r"<Geometries\b.*?</Geometries>", xml, re.S).group(0)


def _curvas(nombre: str) -> list:
    """Todas las serializaciones de curva: la propia y las de los miembros del compuesto."""
    bloque = _geometrias(nombre)
    return _SERIALIZACION.findall(bloque) + _MIEMBRO.findall(bloque)


def _codigo_base(serializacion: str) -> str:
    """Código de la curva base: última fila, primer número."""
    return serializacion.strip("\n").split("\n")[-1].split()[0]


class EspacioFinalPorCodigoDeCurvaTest(unittest.TestCase):
    """La regla derivada sobre las 183 curvas del lote (dibujos.md, sección 12.1)."""

    CON_ESPACIO = {"1"}          # recta
    SIN_ESPACIO = {"2", "3"}     # círculo/arco y elipse

    def test_la_regla_se_cumple_en_todos_los_fixtures(self):
        vistos = set()
        for nombre in TODOS:
            for curva in _curvas(nombre):
                codigo = _codigo_base(curva)
                vistos.add(codigo)
                lleva_espacio = curva.rstrip("\n").endswith(" ")
                with self.subTest(fixture=nombre, codigo=codigo):
                    if codigo in self.CON_ESPACIO:
                        self.assertTrue(
                            lleva_espacio, "la recta debe llevar espacio final: %r" % curva)
                    else:
                        self.assertIn(codigo, self.SIN_ESPACIO)
                        self.assertFalse(
                            lleva_espacio, "la cónica NO debe llevar espacio final: %r" % curva)
        self.assertEqual(vistos, {"1", "2", "3"}, "el lote debe ejercitar los tres códigos")


class SintetizadorReproduceAMaestroTest(unittest.TestCase):
    """Byte a byte contra el archivo que hizo Maestro. Es lo que faltaba."""

    def test_linea(self):
        # linea_01: (50,50) -> (350,50)
        self.assertEqual(
            G._build_maestro_line_serialization((50.0, 50.0, 0.0), (350.0, 50.0, 0.0)),
            _curvas("linea_01")[0],
        )

    def test_arco_antihorario(self):
        # arco_01: centro (50,50), R=300, ANTIHORARIO, de 0 a 90 grados
        self.assertEqual(
            G._build_maestro_arc_serialization(
                (350.0, 50.0), (50.0, 350.0), (50.0, 50.0), 1.0, 0.0, radius=300.0),
            _curvas("arco_01")[0],
        )

    def test_circulo(self):
        # circulo_01: centro (150,150), R=100
        self.assertEqual(
            G._build_circle_geometry_serialization(
                center_point=(150.0, 150.0, 0.0), radius=100.0, normal_z=1.0),
            _curvas("circulo_01")[0],
        )


class NormalZCodificaElSentidoTest(unittest.TestCase):
    """Nz = +1 antihorario, -1 horario. Derivado 8/8 con la descripción de Fermín."""

    def _normal_z(self, nombre: str) -> float:
        return float(_curvas(nombre)[0].strip("\n").split("\n")[-1].split()[6])

    def test_antihorario_es_positivo(self):
        self.assertEqual(self._normal_z("arco_01"), 1.0)   # CCW, de 0 a 90 grados

    def test_horario_es_negativo(self):
        self.assertEqual(self._normal_z("arco_04"), -1.0)  # CW, de 360 a 90 grados


class CompuestosTest(unittest.TestCase):
    """Polígono, polilínea y rectángulo son el MISMO nodo (dibujos.md, sección 12.4)."""

    COMPUESTOS = ("polilinea_01", "polilinea_11", "poligono_01",
                  "rectangulo_01", "rectangulo_07")

    def test_todos_son_geom_composite_curve(self):
        for nombre in self.COMPUESTOS:
            with self.subTest(fixture=nombre):
                self.assertIn("GeomCompositeCurve", _geometrias(nombre))

    def test_un_id_por_miembro(self):
        for nombre in self.COMPUESTOS:
            bloque = _geometrias(nombre)
            claves = re.findall(r"<b:unsignedInt>(\d+)</b:unsignedInt>", bloque)
            with self.subTest(fixture=nombre):
                self.assertEqual(len(claves), len(_MIEMBRO.findall(bloque)))
                self.assertEqual(len(set(claves)), len(claves), "los ID no se repiten")

    def test_un_compuesto_puede_mezclar_rectas_y_arcos(self):
        codigos = [_codigo_base(m) for m in _MIEMBRO.findall(_geometrias("polilinea_11"))]
        self.assertEqual(codigos, ["1", "2", "1"])

    def test_el_lado_partido_comparte_la_recta_base(self):
        """rectangulo_07 arrancó en medio de un lado: va en dos miembros colineales."""
        miembros = _MIEMBRO.findall(_geometrias("rectangulo_07"))
        self.assertEqual(len(miembros), 5)
        base = [tuple(m.strip("\n").split("\n")[-1].split()[1:]) for m in miembros]
        self.assertEqual(base[0], base[-1],
                         "el primer y el último miembro son el mismo lado partido")


class PuntoTest(unittest.TestCase):
    def test_guarda_coordenadas_y_no_serializacion(self):
        bloque = _geometrias("punto_01")
        self.assertIn("GeomCartesianPoint", bloque)
        self.assertEqual(_SERIALIZACION.findall(bloque), [])
        self.assertEqual(re.findall(r"<a:_x>(.*?)</a:_x>", bloque), ["50"])
        self.assertEqual(re.findall(r"<a:_y>(.*?)</a:_y>", bloque), ["50"])


class ElipseTest(unittest.TestCase):
    """`GeomEllipse` existe en Maestro y el sintetizador NO la tiene todavía."""

    def test_la_elipse_es_curva_base_3_con_dos_radios(self):
        base = _curvas("elipse_01")[0].strip("\n").split("\n")[-1].split()
        self.assertEqual(base[0], "3")
        self.assertEqual(len(base), 15, "centro(3) + N(3) + U(3) + V(3) + dos radios")
        self.assertEqual(base[-2:], ["150", "50"])

    def test_el_sintetizador_la_rechaza_ruidosamente(self):
        """Regla 4: mientras no esté soportada tiene que explotar, no aproximar."""
        with self.assertRaises(ValueError) as caso:
            G._primitive_to_serialization(
                G.GeometryPrimitiveSpec(
                    primitive_type="Ellipse",
                    start_point=(0.0, 0.0, 0.0),
                    end_point=(1.0, 0.0, 0.0)))
        self.assertIn("no soportado", str(caso.exception))


class SintetizarDibujosTest(unittest.TestCase):
    """`drawings=` agrega geometría a la pieza SIN crear mecanizado.

    Es la contraparte de la sección 1 de `dibujos.md`: dibujar deja `<Features/>` vacío.
    """

    def _sintetizar(self, dibujos):
        import tempfile
        import pgmx.synthesis as sp
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "dibujos.pgmx"
            sp.synthesize_request(sp.build_synthesis_request(
                output_path=salida, piece_name="dibujos",
                length=400.0, width=400.0, depth=18.0, drawings=dibujos))
            with zipfile.ZipFile(salida) as zf:
                interno = next(i.filename for i in zf.infolist()
                               if i.filename.lower().endswith(".xml"))
                return zf.read(interno).decode("utf-8")

    def _bloque(self, xml: str, tag: str) -> str:
        encontrado = re.search(r"<%s\b[^>]*/>|<%s\b.*?</%s>" % (tag, tag, tag), xml, re.S)
        return encontrado.group(0) if encontrado else ""

    def test_un_dibujo_no_crea_mecanizado(self):
        import pgmx.synthesis as sp
        xml = self._sintetizar([
            sp.build_drawing_spec(profile=sp.build_line_geometry_profile(50.0, 50.0, 350.0, 50.0)),
        ])
        self.assertEqual(self._bloque(xml, "Features").replace(" ", ""), "<Features/>")
        self.assertIn("GeomTrimmedCurve", self._bloque(xml, "Geometries"))

    def test_la_linea_dibujada_sale_como_la_de_maestro(self):
        """La serialización tiene que ser la del fixture `linea_01`, byte a byte."""
        import pgmx.synthesis as sp
        xml = self._sintetizar([
            sp.build_drawing_spec(profile=sp.build_line_geometry_profile(50.0, 50.0, 350.0, 50.0)),
        ])
        nuestra = re.search(
            r"<[\w:]*_serializationGeometryDescription>(.*?)</[\w:]*_serializationGeometryDescription>",
            self._bloque(xml, "Geometries"), re.S).group(1)
        self.assertEqual(nuestra, _curvas("linea_01")[0])

    def test_el_punto_guarda_coordenadas(self):
        import pgmx.synthesis as sp
        bloque = self._bloque(self._sintetizar([
            sp.build_drawing_spec(profile=sp.build_point_geometry_profile(50.0, 50.0)),
        ]), "Geometries")
        self.assertIn("GeomCartesianPoint", bloque)
        self.assertEqual(re.findall(r"<[\w:]*_x>(.*?)</[\w:]*_x>", bloque), ["50"])

    def test_el_compuesto_reserva_un_id_por_miembro(self):
        """Derivado del lote: `_serializingKeys` lleva un ID por miembro (sección 12.2)."""
        import pgmx.synthesis as sp
        bloque = self._bloque(self._sintetizar([
            sp.build_drawing_spec(profile=sp.build_composite_geometry_profile([
                sp.build_line_geometry_primitive(0.0, 0.0, 100.0, 0.0),
                sp.build_line_geometry_primitive(100.0, 0.0, 100.0, 80.0),
            ])),
        ]), "Geometries")
        claves = re.findall(r"<[\w:]*unsignedInt>(\d+)</[\w:]*unsignedInt>", bloque)
        miembros = re.findall(r"<[\w:]*string>(.*?)</[\w:]*string>", bloque, re.S)
        self.assertEqual(len(claves), 2)
        self.assertEqual(len(miembros), 2)
        self.assertEqual(len(set(claves)), 2, "los ID de los miembros no se repiten")

    def test_el_nombre_queda_vacio_como_en_maestro(self):
        """`ref` es una etiqueta NUESTRA y no debe viajar al `.pgmx`.

        En los 88 fixtures Maestro deja `<Name/>` vacío; escribir un nombre sería
        apartarse de lo que hace él.
        """
        import pgmx.synthesis as sp
        bloque = self._bloque(self._sintetizar([
            sp.build_drawing_spec(
                profile=sp.build_line_geometry_profile(50.0, 50.0, 350.0, 50.0),
                ref="la_base"),
        ]), "Geometries")
        self.assertNotIn("la_base", bloque)

    def test_dos_dibujos_con_el_mismo_ref_explotan(self):
        import pgmx.synthesis as sp
        perfil = sp.build_line_geometry_profile(0.0, 0.0, 10.0, 0.0)
        with self.assertRaises(ValueError) as caso:
            self._sintetizar([
                sp.build_drawing_spec(profile=perfil, ref="repetido"),
                sp.build_drawing_spec(profile=perfil, ref="repetido"),
            ])
        self.assertIn("mismo `ref`", str(caso.exception))

    def test_ref_vacio_se_rechaza(self):
        import pgmx.synthesis as sp
        with self.assertRaises(ValueError):
            sp.build_drawing_spec(
                profile=sp.build_line_geometry_profile(0.0, 0.0, 10.0, 0.0), ref="   ")


if __name__ == "__main__":
    unittest.main()
