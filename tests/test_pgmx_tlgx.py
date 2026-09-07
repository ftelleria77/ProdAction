"""El lector de `def.tlgx`, atado a los valores medidos en ISO reales.

Cada numero de este archivo salio de un ISO postprocesado por Maestro y esta
documentado en `iso/docs/experiments/`. El test no verifica que el lector "haga
algo": verifica que el catalogo explique lo que la maquina emitio.
"""

from __future__ import annotations

import unittest

from pgmx.tlgx import TlgxTool, load_tlgx


class TestCatalogoTlgx(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalogo = load_tlgx()

    def test_lee_las_diecinueve_herramientas(self) -> None:
        self.assertEqual(len(self.catalogo), 19)
        self.assertIn("082", self.catalogo)
        self.assertIn("E002", self.catalogo)

    def test_la_sierra_vertical_vive_en_el_cabezal_perforador(self) -> None:
        """`canal.md`: por eso su bloque no tiene `T`, `SYN` ni `M06`."""

        sierra = self.catalogo["082"]
        self.assertTrue(sierra.is_boring_unit)
        self.assertTrue(sierra.is_blade)
        self.assertFalse(self.catalogo["E002"].is_boring_unit)

    def test_svl_y_svr_reproducen_el_iso(self) -> None:
        """`SVL` = `ToolOffsetLength` y `SVR` = radio del CUERPO (canal.md 19)."""

        medidos = {
            # herramienta: (SVL, SVR) leidos del ISO
            "082": (60.0, 1.900),
            "E001": (125.4, 9.180),
            "E002": (107.0, 50.000),
            "E004": (107.2, 2.000),
        }
        for nombre, (svl, svr) in medidos.items():
            with self.subTest(herramienta=nombre):
                tool = self.catalogo[nombre]
                self.assertAlmostEqual(tool.tool_offset_length, svl, places=3)
                self.assertAlmostEqual(tool.cutting_radius, svr, places=3)

    def test_la_anchura_sale_de_la_herramienta(self) -> None:
        """La ventana de Canal la muestra en gris: 3,8 - 4 - 18,36 - 100."""

        anchos = {"082": 3.8, "E004": 4.0, "E001": 18.36, "E002": 100.0}
        for nombre, ancho in anchos.items():
            with self.subTest(herramienta=nombre):
                self.assertAlmostEqual(self.catalogo[nombre].cutting_width, ancho, places=3)

    def test_el_modo_de_correccion_lo_decide_la_herramienta(self) -> None:
        """`ActivateCNCCorrection`: la sierra trabaja siempre en modo CAD."""

        self.assertFalse(self.catalogo["082"].uses_cnc_correction)
        for fresa in ("E001", "E002", "E004"):
            with self.subTest(herramienta=fresa):
                self.assertTrue(self.catalogo[fresa].uses_cnc_correction)

    def test_la_sierra_solo_trabaja_la_cara_superior(self) -> None:
        """`st_OFace`, y la UI lo aplica: con `Lado delantero` la 082 desaparece."""

        sierra = self.catalogo["082"]
        self.assertTrue(sierra.works_face(1))
        for cara in (2, 3, 4, 5):
            with self.subTest(cara=cara):
                self.assertFalse(sierra.works_face(cara))

    def test_el_plc_out_explica_la_mascara_del_iso(self) -> None:
        """`?%ETK[0] = 2^(plc-1)` para los bits 1-32; el 33-64 va en `ETK[1]`."""

        casos = {"001": 1, "005": 5, "058": 31, "060": 32, "082": 37}
        for nombre, plc in casos.items():
            with self.subTest(herramienta=nombre):
                self.assertEqual(self.catalogo[nombre].plc_out, plc)

        # La sierra: 2^(37-33) = 16, que es el ?%ETK[1]=16 del ISO.
        self.assertEqual(2 ** (self.catalogo["082"].plc_out - 33), 16)
        # La broca 001: 2^(1-1) = 1, el ?%ETK[0]=1.
        self.assertEqual(2 ** (self.catalogo["001"].plc_out - 1), 1)

    def test_la_posicion_de_almacen_explica_la_T_del_cambio(self) -> None:
        """`E002` -> `T2` y `E004` -> `T4` en los ISO del Grupo 11."""

        self.assertEqual(self.catalogo["E002"].store_pos, 2)
        self.assertEqual(self.catalogo["E004"].store_pos, 4)
        self.assertEqual(self.catalogo["E001"].store_pos, 1)

    def test_la_velocidad_estandar_es_la_del_iso(self) -> None:
        """`S4000M3` con la sierra, `S18000M3` con la `E004`."""

        self.assertAlmostEqual(self.catalogo["082"].spindle_speed[1], 4000.0)
        self.assertAlmostEqual(self.catalogo["E004"].spindle_speed[1], 18000.0)
        self.assertAlmostEqual(self.catalogo["E002"].spindle_speed[1], 6000.0)

    def test_el_avance_estandar_explica_la_F_del_corte(self) -> None:
        """`F5000` con la sierra y la `E004`; `F3000` con la `E002`."""

        self.assertAlmostEqual(self.catalogo["082"].feed_rate[1] * 1000, 5000.0)
        self.assertAlmostEqual(self.catalogo["E004"].feed_rate[1] * 1000, 5000.0)
        self.assertAlmostEqual(self.catalogo["E002"].feed_rate[1] * 1000, 3000.0)

    def test_la_profundidad_maxima_de_la_sierra_son_diez(self) -> None:
        """`SinkingLength`: por eso el canal pasante de 18 se rechaza."""

        self.assertAlmostEqual(self.catalogo["082"].sinking_length, 10.0)

    def test_el_offset_lateral_del_perforado_sale_del_catalogo(self) -> None:
        """77 en las verticales y 65 en las laterales (perforado.md Grupo 6)."""

        self.assertAlmostEqual(self.catalogo["001"].tool_offset_length, 77.0)
        for lateral in ("058", "059", "060", "061"):
            with self.subTest(herramienta=lateral):
                self.assertAlmostEqual(self.catalogo[lateral].tool_offset_length, 65.0)

    def test_la_aproximacion_es_el_offset_mas_el_plano_de_seguridad(self) -> None:
        """`G0 Z80.000` con la sierra, `Z127.200` con la `E004` (canal.md 19)."""

        seguridad = 20.0
        esperado = {"082": 80.0, "E002": 127.0, "E004": 127.2}
        for nombre, z in esperado.items():
            with self.subTest(herramienta=nombre):
                tool = self.catalogo[nombre]
                self.assertAlmostEqual(tool.tool_offset_length + seguridad, z, places=3)


class TestTlgxEmbebido(unittest.TestCase):
    def test_el_catalogo_viaja_dentro_del_pgmx(self) -> None:
        """Es la razon por la que `def.tlgx` es la fuente y no un CSV nuestro."""

        from pgmx.synthesis import (
            build_channel_spec,
            build_synthesis_request,
            synthesize_request,
        )
        import tempfile
        from pathlib import Path

        from pgmx.tlgx import load_tlgx_from_pgmx

        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "canal.pgmx"
            solicitud = build_synthesis_request(
                output_path=destino,
                piece_name="canal",
                length=400.0,
                width=400.0,
                depth=18.0,
                channels=[
                    build_channel_spec(
                        start_x=50.0, start_y=200.0, end_x=350.0, end_y=200.0,
                        target_depth=10.0,
                    )
                ],
            )
            synthesize_request(solicitud)
            catalogo = load_tlgx_from_pgmx(destino)

        self.assertIn("082", catalogo)
        self.assertAlmostEqual(catalogo["082"].cutting_radius, 1.9, places=3)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
