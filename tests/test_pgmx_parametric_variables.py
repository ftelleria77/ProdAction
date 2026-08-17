"""Un parámetro del programa tiene que salir como lo escribe Maestro.

Hasta el 2026-08-16 la traducción UI → `.pgmx` de los parámetros estaba **predefinida
en el código sin evidencia**: `Integer`, `b:int` y `Speed` venían de la época anterior y
nadie los había derivado contra un archivo real. Los cuatro fixtures manuales de esa
fecha los derivaron —y resultaron correctos—, pero eso no vale de nada si no queda fijado:
sin este test, cambiar `_normalize_variable_type` no pone nada en rojo.

El riesgo no es teórico. En el mismo bloque, SCM escribe el tag `FisicalUnitType` con el
valor `Lenght` (typo) mientras el `Description` de `dx1` dice `Length` bien escrito. Una
"corrección" de ortografía bien intencionada rompe el archivo.

Los nodos de referencia son **literales copiados de los `.pgmx` que hizo Fermín en
Maestro**, así que la suite sigue 100% offline: no hace falta S: ni P:. La procedencia de
cada uno está en `iso/docs/experiments/parametros.md`, sección 7.
"""
import unittest
import xml.etree.ElementTree as ET

import pgmx.synthesis as sp
from pgmx.synthesis.common import program as P

PARAMETRICS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Parametrics"
UTILITY = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Utility"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
XSD = "http://www.w3.org/2001/XMLSchema"


def _referencia(cuerpo: str) -> str:
    """Envuelve un nodo de Maestro con las declaraciones que trae el `.pgmx` completo."""
    return f'<a:Variable xmlns:a="{PARAMETRICS}" xmlns:i="{XSI}">{cuerpo}</a:Variable>'


#: `R_PV_manual_base_Entero_Velocidad_1500.pgmx` — deriva Integer / b:int / Speed.
MAESTRO_ENTERO = _referencia(
    f'<Key xmlns="{UTILITY}"><ID>1930</ID>'
    "<ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Variable</ObjectType></Key>"
    f'<Name xmlns="{UTILITY}">Nombre_Parametro</Name>'
    "<a:Description>Una descripción (opcional).</a:Description>"
    "<a:FisicalUnitType>Speed</a:FisicalUnitType>"
    "<a:IsReadOnly>false</a:IsReadOnly><a:Scope>Local</a:Scope>"
    "<a:Type>Integer</a:Type>"
    f'<a:Value i:type="b:int" xmlns:b="{XSD}">1500</a:Value>'
)

#: `R_PV_manual_base_Decimal_Longitud_-12_5.pgmx` — deriva el punto decimal y el signo.
MAESTRO_DECIMAL = _referencia(
    f'<Key xmlns="{UTILITY}"><ID>1932</ID>'
    "<ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Variable</ObjectType></Key>"
    f'<Name xmlns="{UTILITY}">Parametro_Decimal</Name>'
    "<a:Description>Breve descripción (opcional).</a:Description>"
    "<a:FisicalUnitType>Lenght</a:FisicalUnitType>"
    "<a:IsReadOnly>false</a:IsReadOnly><a:Scope>Local</a:Scope>"
    "<a:Type>Double</a:Type>"
    f'<a:Value i:type="b:double" xmlns:b="{XSD}">-12.5</a:Value>'
)

#: `R_PV_manual_base_Booleano_Usuario_True.pgmx` — deriva Boolean / b:boolean / UnitLess,
#: y que el `True` de la UI se guarda en MINÚSCULA.
MAESTRO_BOOLEANO = _referencia(
    f'<Key xmlns="{UTILITY}"><ID>1928</ID>'
    "<ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Variable</ObjectType></Key>"
    f'<Name xmlns="{UTILITY}">Booleano_Usuario</Name>'
    "<a:Description>Parámetro booleano de usuario.</a:Description>"
    "<a:FisicalUnitType>UnitLess</a:FisicalUnitType>"
    "<a:IsReadOnly>false</a:IsReadOnly><a:Scope>Local</a:Scope>"
    "<a:Type>Boolean</a:Type>"
    f'<a:Value i:type="b:boolean" xmlns:b="{XSD}">true</a:Value>'
)

#: `R_PV_manual_base_Variable_Usuario_10.pgmx` — deriva que la descripción vacía NO se
#: omite: queda como tag vacío.
MAESTRO_SIN_DESCRIPCION = _referencia(
    f'<Key xmlns="{UTILITY}"><ID>1927</ID>'
    "<ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Variable</ObjectType></Key>"
    f'<Name xmlns="{UTILITY}">Variable_Usuario</Name>'
    "<a:Description/>"
    "<a:FisicalUnitType>Lenght</a:FisicalUnitType>"
    "<a:IsReadOnly>false</a:IsReadOnly><a:Scope>Local</a:Scope>"
    "<a:Type>Double</a:Type>"
    f'<a:Value i:type="b:double" xmlns:b="{XSD}">10</a:Value>'
)


#: `R_PV_manual_base_Presicion.pgmx` — deriva que Maestro NO redondea: guarda los siete
#: decimales que se le escribieron. Nuestro `_compact_number` habria emitido `12.345679`.
MAESTRO_PRECISION = _referencia(
    f'<Key xmlns="{UTILITY}"><ID>1927</ID>'
    "<ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Variable</ObjectType></Key>"
    f'<Name xmlns="{UTILITY}">Presicion</Name>'
    "<a:Description/>"
    "<a:FisicalUnitType>Lenght</a:FisicalUnitType>"
    "<a:IsReadOnly>false</a:IsReadOnly><a:Scope>Local</a:Scope>"
    "<a:Type>Double</a:Type>"
    f'<a:Value i:type="b:double" xmlns:b="{XSD}">12.3456789</a:Value>'
)


def _local(nombre: str) -> str:
    return nombre.rsplit("}", 1)[-1]


def _canonico(nodo: ET.Element) -> list[tuple[str, str, tuple[tuple[str, str], ...]]]:
    """(tag, texto, atributos) por elemento, sin prefijos y en orden de aparición.

    Maestro serializa con prefijo `a:` y nosotros con `ns0:`; eso es estilo, no
    contenido, y comparar el texto crudo lo confundiría. Las declaraciones `xmlns:*`
    se descartan acá porque ElementTree las consume al parsear el literal de Maestro
    pero las conserva como atributo en el nodo que construimos nosotros: compararlas
    daría una diferencia falsa. Que el `xmlns` del XSD esté tiene su propio test.
    """
    salida = []
    for elemento in nodo.iter():
        atributos = tuple(sorted(
            (_local(k), v) for k, v in elemento.attrib.items()
            if not k.startswith("xmlns")
        ))
        salida.append((_local(elemento.tag), (elemento.text or "").strip(), atributos))
    return salida


def _nuestro(var_id: str, **kwargs) -> ET.Element:
    return P._build_variable_node(sp.build_parametric_variable_spec(**kwargs), var_id)


class NodosDeMaestroTests(unittest.TestCase):
    """Lo derivado el 2026-08-16: reproducir los cuatro nodos reales."""

    def _comparar(self, referencia: str, var_id: str, **kwargs) -> None:
        esperado = _canonico(ET.fromstring(referencia))
        obtenido = _canonico(_nuestro(var_id, **kwargs))
        self.assertEqual(obtenido, esperado)

    def test_entero_con_velocidad(self) -> None:
        self._comparar(
            MAESTRO_ENTERO, "1930",
            name="Nombre_Parametro", value=1500,
            description="Una descripción (opcional).",
            variable_type="Entero", physical_unit="Velocidad",
        )

    def test_decimal_negativo_con_longitud(self) -> None:
        self._comparar(
            MAESTRO_DECIMAL, "1932",
            name="Parametro_Decimal", value=-12.5,
            description="Breve descripción (opcional).",
            variable_type="Decimal", physical_unit="Longitud",
        )

    def test_booleano_con_adimensional(self) -> None:
        self._comparar(
            MAESTRO_BOOLEANO, "1928",
            name="Booleano_Usuario", value=True,
            description="Parámetro booleano de usuario.",
            variable_type="Booleano", physical_unit="Adimensional",
        )

    def test_decimal_de_siete_decimales_no_se_redondea(self) -> None:
        """El caso que `_compact_number` rompia: emitia `12.345679`."""
        self._comparar(
            MAESTRO_PRECISION, "1927",
            name="Presicion", value=12.3456789,
            variable_type="Decimal", physical_unit="Longitud",
        )

    def test_descripcion_vacia_queda_como_tag_vacio(self) -> None:
        self._comparar(
            MAESTRO_SIN_DESCRIPCION, "1927",
            name="Variable_Usuario", value=10,
            variable_type="Decimal", physical_unit="Longitud",
        )


class TablaDeTraduccionTests(unittest.TestCase):
    """Los dos desplegables de la ventana «Parámetro» tienen dominio cerrado de tres."""

    #: (término de la UI, <a:Type>, atributo del valor)
    TIPOS = [
        ("Decimal", "Double", "b:double"),
        ("Entero", "Integer", "b:int"),
        ("Booleano", "Boolean", "b:boolean"),
    ]

    #: (término de la UI, <a:FisicalUnitType>)
    UNIDADES = [
        ("Longitud", "Lenght"),      # el typo es de SCM y es parte del contrato
        ("Velocidad", "Speed"),
        ("Adimensional", "UnitLess"),
    ]

    def _campo(self, nodo: ET.Element, nombre: str) -> ET.Element:
        return next(e for e in nodo.iter() if _local(e.tag) == nombre)

    def test_cada_tipo_de_la_ui_da_su_type_y_su_atributo(self) -> None:
        for ui, tipo, xsd in self.TIPOS:
            with self.subTest(tipo=ui):
                nodo = _nuestro("1", name="p", value=1, variable_type=ui)
                self.assertEqual(self._campo(nodo, "Type").text, tipo)
                valor = self._campo(nodo, "Value")
                self.assertEqual(valor.attrib[f"{{{XSI}}}type"], xsd)

    def test_cada_unidad_de_la_ui_da_su_fisicalunittype(self) -> None:
        for ui, unidad in self.UNIDADES:
            with self.subTest(unidad=ui):
                nodo = _nuestro("1", name="p", value=1, physical_unit=ui)
                self.assertEqual(self._campo(nodo, "FisicalUnitType").text, unidad)

    def test_los_defaults_de_la_api_no_son_los_del_dialogo(self) -> None:
        """OJO: nuestros defaults y los de Maestro coinciden en el tipo y NO en la unidad.

        El diálogo de Maestro abre en `Decimal` + `Longitud` (2026-08-16). Nuestra API
        arranca en `Double` + `UnitLess`: el tipo es el mismo, la unidad no. No es un
        defecto —en Maestro no se puede aplicar sin escribir nombre y valor, así que ese
        default nunca viaja solo— pero está fijado acá para que la divergencia sea
        explícita y no una sorpresa. Si algún día se decide alinearlos, este test es el
        que hay que cambiar a propósito.
        """
        spec = sp.build_parametric_variable_spec(name="p", value=1)
        self.assertEqual(spec.variable_type, "Double")     # = «Decimal», igual que Maestro
        self.assertEqual(spec.physical_unit, "UnitLess")   # Maestro abre en «Longitud»

    def test_el_booleano_va_en_minuscula(self) -> None:
        """La UI acepta `True`; el `.pgmx` guarda `true`."""
        for valor, texto in [(True, "true"), (False, "false")]:
            with self.subTest(valor=valor):
                nodo = _nuestro("1", name="p", value=valor, variable_type="Booleano")
                self.assertEqual(self._campo(nodo, "Value").text, texto)

    def test_el_decimal_va_con_punto(self) -> None:
        """La grilla de Maestro muestra `10,000` con coma: eso es presentación."""
        nodo = _nuestro("1", name="p", value=-12.5, variable_type="Decimal")
        self.assertEqual(self._campo(nodo, "Value").text, "-12.5")

    def test_el_xmlns_del_xsd_va_en_el_propio_value(self) -> None:
        """Maestro lo repite en cada nodo `Value`; sin él, `i:type` no resuelve."""
        nodo = _nuestro("1", name="p", value=1)
        serializado = ET.tostring(self._campo(nodo, "Value"), encoding="unicode")
        self.assertIn(f'xmlns:b="{XSD}"', serializado)


class FailLoudTests(unittest.TestCase):
    """Regla 4: lo que no está derivado se rechaza, no se aproxima."""

    def test_un_tipo_fuera_del_dominio_explota(self) -> None:
        with self.assertRaises(ValueError):
            sp.build_parametric_variable_spec(name="p", value=1, variable_type="Texto")

    def test_una_unidad_fuera_del_dominio_explota(self) -> None:
        """La ventana ofrece tres unidades. Una cuarta no tiene traducción derivada."""
        with self.assertRaises(ValueError):
            sp.build_parametric_variable_spec(name="p", value=1, physical_unit="Angulo")

    def test_las_dimensiones_de_la_pieza_estan_reservadas(self) -> None:
        """`dx1`/`dy1`/`dz1` los referencia la pieza por nombre vía Expression."""
        for reservado in ["dx1", "dy1", "dz1", "DX1"]:
            with self.subTest(nombre=reservado):
                with self.assertRaises(ValueError):
                    sp.build_parametric_variable_spec(name=reservado, value=1)

    def test_el_nombre_es_obligatorio(self) -> None:
        with self.assertRaises(ValueError):
            sp.build_parametric_variable_spec(name="   ", value=1)


class NamespacesTests(unittest.TestCase):
    def test_key_y_name_van_en_utility_y_el_resto_en_parametrics(self) -> None:
        """El bug de R001 (2026-08-10): con `Name` en Parametrics, Maestro lo
        deserializa nulo y no puede abrir el archivo — `VariableList` indexa por
        nombre. El test viejo usaba un comodín de namespace y por eso daba verde
        con el XML roto; éste compara el namespace resuelto.
        """
        nodo = _nuestro("1", name="p", value=1)
        esperado = {
            "Key": UTILITY, "ID": UTILITY, "ObjectType": UTILITY, "Name": UTILITY,
            "Description": PARAMETRICS, "FisicalUnitType": PARAMETRICS,
            "IsReadOnly": PARAMETRICS, "Scope": PARAMETRICS,
            "Type": PARAMETRICS, "Value": PARAMETRICS,
        }
        for elemento in nodo.iter():
            nombre = _local(elemento.tag)
            if nombre == "Variable":
                continue
            with self.subTest(campo=nombre):
                self.assertTrue(elemento.tag.startswith(f"{{{esperado[nombre]}}}"))

    def test_el_orden_de_los_campos_es_el_de_maestro(self) -> None:
        nodo = _nuestro("1", name="p", value=1)
        orden = [_local(e.tag) for e in nodo]
        self.assertEqual(
            orden,
            ["Key", "Name", "Description", "FisicalUnitType",
             "IsReadOnly", "Scope", "Type", "Value"],
        )


if __name__ == "__main__":
    unittest.main()
