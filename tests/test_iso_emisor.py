"""El cuarto origen tiene que reproducir el ISO real, byte por byte.

`emisor_iso.cfg` guarda el esqueleto que pone el generador de Xilog. Si ese archivo
sirve para algo, tiene que poder rearmar el ISO de referencia sin una sola diferencia
—incluidos los espacios finales, que son parte del byte—.

Todo offline: el ISO de referencia está versionado en `evidencia/paso0_cnc/` y el
`NCI.CFG`, en el snapshot.
"""
import unittest
from pathlib import Path

from iso.emisor import CRLF, bloques_nci, componer, leer_bloques

RAIZ = Path(__file__).resolve().parents[1]
ISO_REFERENCIA = (RAIZ / "iso" / "docs" / "experiments" / "evidencia" / "paso0_cnc"
                  / "r_pv_manual_base_cnc.iso")

#: Los valores del programa base: pieza 400×400×18, origen 0/0/0, área HG.
#: Salen del `.pgmx` y de la fórmula del origen (B1c), no de este archivo.
BASE = {
    "nombre_del_archivo": "r_pv_manual_base_cnc",
    "dx": "400.000", "dy": "400.000", "dz": "18.000",
    "bx": "0.000", "by": "0.000", "bz": "0.000",
    "area": "HG", "v": "0", "c": "0", "t": "0",
    "of_x": "-400000.000", "of_y": "-1515599.976", "of_z": "18000.000",
    "shf_x": "-400.000", "shf_y": "-1515.600", "shf_z": "18.000",
    "edk_mitad_mesa": "13",
    "cuerpo": [],
}


def _valores(**extra):
    nci = bloques_nci()
    return {**BASE, "nci_gen_init": nci["GEN_INIT"], "nci_gen_end": nci["GEN_END"],
            **extra}


class EsqueletoTests(unittest.TestCase):
    def test_reproduce_el_iso_de_referencia_byte_a_byte(self) -> None:
        esperado = ISO_REFERENCIA.read_bytes()
        obtenido = componer(_valores()).encode("cp1252")
        self.assertEqual(obtenido, esperado)

    def test_son_43_lineas_y_termina_con_crlf(self) -> None:
        iso = componer(_valores())
        self.assertTrue(iso.endswith(CRLF))
        self.assertEqual(len(iso.split(CRLF)) - 1, 43)

    def test_los_espacios_finales_sobreviven(self) -> None:
        """Lo que el `;` del archivo protege: sin eso no hay byte-idéntico."""
        lineas = componer(_valores()).split(CRLF)
        self.assertEqual(lineas[8], "G71 ")     # un espacio
        self.assertEqual(lineas[21], "SYN")     # ninguno
        self.assertEqual(lineas[42], "M2  ")    # dos

    def test_el_cuerpo_vacio_no_deja_linea_en_blanco(self) -> None:
        lineas = componer(_valores()).split(CRLF)
        self.assertEqual(lineas[20], "G40 ")
        self.assertEqual(lineas[21], "SYN")

    def test_el_cuerpo_entra_entre_el_g40_y_el_syn(self) -> None:
        park = leer_bloques()["EMI_PARK_FINAL"]
        lineas = componer(_valores(cuerpo=park)).split(CRLF)
        self.assertEqual(lineas[20], "G40 ")
        self.assertEqual(lineas[21], "G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000  ")
        self.assertEqual(lineas[22],
                         "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )  ")
        self.assertEqual(lineas[23], "SYN")

    def test_falta_un_valor_y_falla_ruidosamente(self) -> None:
        """Regla 4: nunca completar un hueco en silencio."""
        incompletos = {k: v for k, v in _valores().items() if k != "shf_x"}
        with self.assertRaises(KeyError):
            componer(incompletos)


class ParkFinalTests(unittest.TestCase):
    def test_la_segunda_linea_del_park_lleva_dos_espacios(self) -> None:
        """La misma instrucción del `$GEN_INIT`, pero escrita distinto."""
        park = leer_bloques()["EMI_PARK_FINAL"]
        preambulo = bloques_nci()["GEN_INIT"]
        self.assertEqual(park[1].rstrip(), preambulo[2].rstrip())
        self.assertTrue(park[1].endswith("  "))
        self.assertFalse(preambulo[2].endswith(" "))


if __name__ == "__main__":
    unittest.main()
