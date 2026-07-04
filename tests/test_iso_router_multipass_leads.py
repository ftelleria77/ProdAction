"""Multipasada Z (N025/N027) y approach/retract programables (N026/N027) del fresado lineal.

Multipasada: pasos de axial_cutting_depth, la última del desbaste lleva el resto; con terminación,
desbaste hasta (total−finish) + UNA pasada final. Bidireccional alterna sentido; unidireccional
vuelve al start (Automatic≡SafetyHeight → security; InPiece → z+MillingRetractDistance, sourced de
Programaciones.settingsx).

Leads: lead = (width/2) × radius_multiplier (¡default HABILITADO = 2.0!). Arco tangente:
Automatic≡Right → centro rot90ccw(û), G3; Left → rot90cw(û), G2. La velocidad del approach
(speed>0, ×1000) aplica al plunge y al lead; overlap INERTE en líneas (ov 0/0.25/5 idénticos).
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec
from pgmx.synthesis.milling.line import LineMillingSpec, build_line_milling_spec

from iso.synthesis import convert
from iso.synthesis._router import _lead_geometry, _multipass_cuts
from iso.synthesis._validation import UnsupportedOperationError, _validate_line_milling


def _line(**kw) -> LineMillingSpec:
    strategy = kw.pop("strategy", None)
    base = build_line_milling_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado",
        line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
        line_security_plane=20.0, line_is_through=False,
        line_target_depth=kw.pop("depth", 12.0),
        line_milling_strategy=strategy,
    )
    return replace(base, **kw) if kw else base


def _strategy(cd: float, finish: float = 0.0):
    return build_bidirectional_milling_strategy_spec(
        allow_multiple_passes=True, axial_cutting_depth=cd, axial_finish_cutting_depth=finish)


class MultipassTest(unittest.TestCase):
    def _depths(self, cd, finish=0.0, depth=12.0):
        spec = _line(strategy=_strategy(cd, finish), depth=depth)
        lines = _multipass_cuts(spec, depth, 20.0, 5000.0)
        return [float(l.split("Z")[1].split(" ")[0]) for l in lines if l.startswith("G1 Z")]

    def test_reparto_con_resto(self):
        # N025 bi_cd5: pasos de cd, la última lleva el resto.
        self.assertEqual(self._depths(5.0), [-5.0, -10.0, -12.0])

    def test_reparto_exacto(self):
        self.assertEqual(self._depths(4.0), [-4.0, -8.0, -12.0])

    def test_terminacion(self):
        # N027 bi_cd4_f2: desbaste hasta 10 (−4/−8/−10) + pasada final a −12.
        self.assertEqual(self._depths(4.0, finish=2.0), [-4.0, -8.0, -10.0, -12.0])


class LeadGeometryTest(unittest.TestCase):
    def test_arc_automatic_en_x(self):
        # N026 app_arc: centro a rot90ccw (+Y para +X), punto exterior a −lead·û, G3.
        p, c, g = _lead_geometry(_line(depth=5.0), 4.0, "Automatic", True)
        self.assertEqual((p, c, g), ((16.0, 104.0), (20.0, 104.0), "G3"))

    def test_arc_left_es_g2(self):
        # N027 app_arc_left: centro al otro lado, G2.
        p, c, g = _lead_geometry(_line(depth=5.0), 4.0, "Left", True)
        self.assertEqual((p, c, g), ((16.0, 96.0), (20.0, 96.0), "G2"))

    def test_arc_retract_sale_por_delante(self):
        # N026 ret_arc: exterior = centro + lead·û → (284, 104).
        p, c, g = _lead_geometry(_line(depth=5.0), 4.0, "Automatic", False)
        self.assertEqual((p, c, g), ((284.0, 104.0), (280.0, 104.0), "G3"))


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(**kw))

    def test_casos_validados_pasan(self):
        _validate_line_milling(_line(strategy=_strategy(4.0)))
        _validate_line_milling(_line(strategy=_strategy(4.0, 2.0)))

    def test_terminacion_mayor_que_total(self):
        self._assert_rejects(strategy=_strategy(4.0, 15.0))

    def test_multipasada_diagonal_pasa(self):
        # Validado en N030 dg_mp_bi_cd4 (los tramos planos de la diagonal omiten Z).
        _validate_line_milling(_line(strategy=_strategy(4.0), start_y=20.0, end_y=180.0))

    def test_multipasada_con_correccion(self):
        self._assert_rejects(strategy=_strategy(4.0), side_of_feature="Left")


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    CASES = [
        (r"N025_router_multipass", "N_MP_bi_cd5"),
        (r"N025_router_multipass", "N_MP_uni_piece_cd4"),
        (r"N027_router_leads_b", "N_mp_bi_cd4_f2"),
        (r"N026_router_leads", "N_LD_app_arc"),
        (r"N026_router_leads", "N_LD_app_arc_sp"),
        (r"N027_router_leads_b", "N_ld_app_arc_rm3"),
        (r"N027_router_leads_b", "N_ld_app_arc_left"),
        (r"N027_router_leads_b", "N_ld_ret_line"),
    ]

    def test_byte_identico(self):
        for lot, stem in self.CASES:
            with self.subTest(stem):
                pgmx = Path(rf"S:\Maestro\Projects\ProdAction\{lot}\{stem}.pgmx")
                ref = Path(rf"P:\USBMIX\ProdAction\{lot}\{stem.lower()}.iso")
                if not pgmx.exists() or not ref.exists():
                    self.skipTest("fixtures S:/P: no disponibles")
                gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
                exp = [ln.rstrip() for ln in ref.read_text(
                    encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
                self.assertEqual(gen, exp)


class MultiToolEndToEndTest(unittest.TestCase):
    """Cambio de herramienta entre fresados (N028): shutdown con doble park Z + header ATC nuevo
    (sin ?%ETK[6]) + ?%ETK[13]=1 sin re-setup de SHF/Or. Byte-idéntico contra Maestro."""

    def test_byte_identico(self):
        for stem in ("N_MF_mf_e4_e1", "N_MF_mf_e1_e4", "N_MF_mf_e4_e4_e1"):
            with self.subTest(stem):
                pgmx = Path(rf"S:\Maestro\Projects\ProdAction\N028_router_multitool\{stem}.pgmx")
                ref = Path(rf"P:\USBMIX\ProdAction\N028_router_multitool\{stem.lower()}.iso")
                if not pgmx.exists() or not ref.exists():
                    self.skipTest("fixtures S:/P: no disponibles")
                gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
                exp = [ln.rstrip() for ln in ref.read_text(
                    encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
                self.assertEqual(gen, exp)


if __name__ == "__main__":
    unittest.main()
