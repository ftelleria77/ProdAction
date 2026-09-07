"""El `ChannelSpec`, con lo que la HERRAMIENTA decide.

Los valores esperados de este archivo salieron de comparar el `.pgmx` que genera
Maestro contra el nuestro, sobre los fixtures del lote D2
(`iso/docs/experiments/canal.md` §10, §19 y §23). El test es **offline**: no lee
los fixtures, lleva los números medidos.
"""

from __future__ import annotations

import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from pgmx.synthesis import (
    build_channel_spec,
    build_synthesis_request,
    synthesize_request,
)
from pgmx.tlgx import load_tlgx


def _sintetizar(**kwargs) -> str:
    """Un canal mínimo con la herramienta pedida; devuelve el XML del `.pgmx`."""

    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / "canal.pgmx"
        synthesize_request(
            build_synthesis_request(
                output_path=destino,
                piece_name="canal",
                length=400.0,
                width=400.0,
                depth=18.0,
                channels=[
                    build_channel_spec(
                        start_x=50.0, start_y=200.0, end_x=350.0, end_y=200.0,
                        target_depth=10.0, **kwargs,
                    )
                ],
            )
        )
        with zipfile.ZipFile(destino) as archivo:
            nombre = [n for n in archivo.namelist() if n.endswith(".xml")][0]
            return archivo.read(nombre).decode("utf-8", errors="replace")


def _sintetizar_en(*, start_x=50.0, start_y=200.0, end_x=350.0, end_y=200.0,
                   target_depth=10.0, **kwargs) -> str:
    """Igual que `_sintetizar` pero con la geometría abierta."""

    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / "canal.pgmx"
        synthesize_request(
            build_synthesis_request(
                output_path=destino, piece_name="canal",
                length=400.0, width=400.0, depth=18.0,
                channels=[build_channel_spec(
                    start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y,
                    target_depth=target_depth, **kwargs,
                )],
            )
        )
        with zipfile.ZipFile(destino) as archivo:
            nombre = [n for n in archivo.namelist() if n.endswith(".xml")][0]
            return archivo.read(nombre).decode("utf-8", errors="replace")


def _valores(xml: str, tag: str) -> list[str]:
    return re.findall(rf"<[a-z0-9]*:?{tag}>([^<]*)</", xml)


def _tipos_de_extremo(xml: str) -> set[str]:
    return set(re.findall(r"SlotEndType[^>]*type=\"[a-z0-9]*:(\w+)\"", xml))


class TestLaHerramientaDecide(unittest.TestCase):
    """Lo que la ventana de Canal muestra en gris no es un parámetro nuestro."""

    def test_el_ancho_sale_del_catalogo(self) -> None:
        """`Anchura`: 3,8 con la sierra y 4 con la `E004` (canal.md §10)."""

        self.assertEqual(_valores(_sintetizar(tool_name="082"), "Width")[:1], ["3.8"])
        self.assertEqual(_valores(_sintetizar(tool_name="E004"), "Width")[:1], ["4"])

    def test_el_tipo_de_extremo_lo_elige_la_herramienta(self) -> None:
        """Un disco deja el corte curvo (`Woodruff`); una fresa, el redondo."""

        self.assertEqual(_tipos_de_extremo(_sintetizar(tool_name="082")), {"WoodruffSlotEndType"})
        self.assertEqual(_tipos_de_extremo(_sintetizar(tool_name="E004")), {"RadiusedSlotEndType"})

    def test_el_radio_de_extremo_es_el_del_disco_y_solo_lo_lleva_el_disco(self) -> None:
        self.assertEqual(_valores(_sintetizar(tool_name="082"), "Radius")[:1], ["60"])
        self.assertEqual(_valores(_sintetizar(tool_name="E004"), "Radius"), [])

    def test_el_modo_de_correccion_lo_decide_la_herramienta(self) -> None:
        """`ActivateCNCCorrection`: la sierra trabaja siempre en modo CAD (§10)."""

        self.assertEqual(
            _valores(_sintetizar(tool_name="082"), "ActivateCNCCorrection")[:1], ["false"]
        )
        self.assertEqual(
            _valores(_sintetizar(tool_name="E004"), "ActivateCNCCorrection")[:1], ["true"]
        )

    def test_el_tool_id_se_resuelve_del_catalogo_vigente(self) -> None:
        """Nunca un literal: Maestro reasigna los IDs al regenerar el catálogo."""

        catalogo = load_tlgx()
        spec = build_channel_spec(
            start_x=50.0, start_y=200.0, end_x=350.0, end_y=200.0, target_depth=10.0
        )
        self.assertEqual(spec.tool_name, "082")
        self.assertEqual(spec.tool_id, catalogo["082"].tool_id)

    def test_el_ancho_y_el_radio_ya_no_son_parametros_de_entrada(self) -> None:
        """La ventana no los deja poner; el spec tampoco (decisión 2026-09-07)."""

        for parametro in ("tool_width", "end_radius", "tool_id"):
            with self.subTest(parametro=parametro):
                with self.assertRaises(TypeError):
                    build_channel_spec(
                        start_x=50.0, start_y=200.0, end_x=350.0, end_y=200.0,
                        **{parametro: 1.0},
                    )

    def test_una_herramienta_que_no_existe_se_rechaza_nombrando_las_que_hay(self) -> None:
        with self.assertRaisesRegex(ValueError, "no existe en el catálogo"):
            build_channel_spec(
                start_x=50.0, start_y=200.0, end_x=350.0, end_y=200.0, tool_name="E099"
            )


class TestLimitesDelDisco(unittest.TestCase):
    """Los límites son del DISCO, no del `Canal` — el lote D2 lo midió."""

    def test_el_disco_solo_corta_paralelo_al_eje_x(self) -> None:
        """Winxiso: «Ángulo no válido del perfil con herramienta de tipo fresa de disco»."""

        with self.assertRaisesRegex(ValueError, "líneas horizontales"):
            _sintetizar_en(start_x=200.0, start_y=50.0, end_x=200.0, end_y=350.0)

    def test_el_disco_no_puede_pasar_de_su_SinkingLength(self) -> None:
        """10 mm: por eso el canal pasante de 18 se rechaza (canal.md §12)."""

        with self.assertRaisesRegex(ValueError, "sinking_length"):
            _sintetizar_en(target_depth=18.0)

    def test_pero_con_fresa_el_canal_en_Y_se_puede(self) -> None:
        """Medido en el Grupo 11: la `E004` postprocesa en Y y en diagonal (§19)."""

        xml = _sintetizar_en(
            start_x=200.0, start_y=50.0, end_x=200.0, end_y=350.0, tool_name="E004"
        )
        self.assertIn("SlotSide", xml)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
