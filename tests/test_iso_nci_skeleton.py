"""El preámbulo y el cierre del ISO salen de `NCI.CFG`, no del emisor.

Los dos bloques `$GEN_INIT` y `$GEN_END` del archivo de configuración de la
máquina aparecen **literales** en el ISO, en el orden en que están escritos.
Este test lo fija como regresión: si alguien tratara el preámbulo como una
plantilla fija en el converter, acá se rompe.

Todo offline: el `NCI.CFG` viene del snapshot versionado y el ISO, de la
evidencia versionada en `iso/docs/experiments/evidencia/`.
"""
import unittest
from pathlib import Path

from iso.machining_lab.verificar_nci import buscar_bloque, emitir, leer_secciones

RAIZ = Path(__file__).resolve().parents[1]
NCI = (RAIZ / "iso" / "data" / "machine_config" / "snapshot"
       / "xilog_plus" / "Cfg" / "NCI.CFG")
ISO = (RAIZ / "iso" / "docs" / "experiments" / "evidencia" / "fases_2fases"
       / "r_pv_manual_base_2fases.iso")


def _lineas_iso(path: Path) -> list[str]:
    return path.read_text(encoding="cp1252").replace("\r\n", "\n").split("\n")


class ReglaDeEmisionTests(unittest.TestCase):
    """Cortar en el primer `;`, desdoblar `%%`. Los seis casos del $GEN_INIT."""

    def test_linea_sin_comentario_solo_desdobla_el_porcentaje(self) -> None:
        self.assertEqual(emitir("?%%ETK[500]=100"), "?%ETK[500]=100")

    def test_linea_toda_comentario_queda_vacia_pero_no_desaparece(self) -> None:
        self.assertEqual(emitir(";?%%ETK[500]=%%ax[0].pa[22]/1000 ;solo per zone"), "")
        self.assertEqual(emitir(";"), "")

    def test_comentario_al_final_conserva_el_espacio_que_lo_separaba(self) -> None:
        # El espacio final de `M58 ` en el ISO no es adorno: es el del .CFG.
        self.assertEqual(emitir("M58 ;abilita controllo vuoto"), "M58 ")


class EsqueletoDesdeNciTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secciones = leer_secciones(NCI)
        self.iso = _lineas_iso(ISO)

    def test_gen_init_aparece_literal_en_el_preambulo(self) -> None:
        bloque = [emitir(l) for l in self.secciones["GEN_INIT"]]
        self.assertEqual(len(bloque), 6)
        # 0-based: la línea 3 del ISO.
        self.assertEqual(buscar_bloque(self.iso, bloque), 2)

    def test_gen_end_aparece_literal_dentro_del_cierre(self) -> None:
        bloque = [emitir(l) for l in self.secciones["GEN_END"]]
        self.assertEqual(len(bloque), 7)
        self.assertEqual(buscar_bloque(self.iso, bloque), 22)

    def test_gen_end_no_es_el_final_del_archivo(self) -> None:
        """Quedan catorce líneas después: el bloque se inserta en el medio."""
        bloque = [emitir(l) for l in self.secciones["GEN_END"]]
        inicio = buscar_bloque(self.iso, bloque)
        self.assertIsNotNone(inicio)
        restantes = [l for l in self.iso[inicio + len(bloque):] if l]
        self.assertEqual(len(restantes), 14)
        self.assertEqual(restantes[-1], "M2  ")

    def test_los_siete_registros_del_reset_salen_del_archivo_de_maquina(self) -> None:
        """Por qué justo esos siete: porque están escritos en el .CFG."""
        self.assertEqual(
            self.secciones["GEN_END"],
            [f"?%%ETK[{n}]=0" for n in (0, 1, 2, 13, 17, 18, 19)],
        )

    def test_el_generador_iso_esta_habilitado_para_aplicacion_externa(self) -> None:
        self.assertEqual(self.secciones["GEN_ISO_FOR_EXTERNAL_APP"], ["1"])


if __name__ == "__main__":
    unittest.main()
