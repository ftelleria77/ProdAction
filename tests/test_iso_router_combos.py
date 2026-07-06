"""Combos finos de N029 derivados con cuerpos completos (2026-07-05).

- MULTIPASADA + LADO (mp_side_l): la estrategia fuerza ACC=false → las pasadas corren en las
  coordenadas DESPLAZADAS radio×normal(lado), estilo CAD, sin G41/G42.
- LADO C.N. + LEADS (side_l_leads / inv_side_l_app): el arco del lead se emite en coordenadas de
  CONTORNO con G41/G42 activo; el 1 mm de la corrección se ancla al punto exterior del arco sobre
  su TANGENTE (entrada: 1 mm antes; salida: 1 mm después, tras el G40). Con compensación,
  `Automatic` elige el arco del lado LIBRE (G41→G3, G42→G2). Cada lead es independiente
  (approach solo → salida plana de 1 mm sobre û).
- MULTIPASADA + LEADS sigue guardado: mp_leads mostró OTRA regla (radio w/2 y lado espejado con
  RM=2/Automatic) — subdeterminada con un solo fixture; se deriva con N034.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.common.leads import build_approach_spec, build_retract_spec
from pgmx.synthesis.common.strategy import build_bidirectional_milling_strategy_spec
from pgmx.synthesis.milling.line import LineMillingSpec, build_line_milling_spec

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError, _validate_line_milling

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\N029_router_combos")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\N029_router_combos")


def _line(**kw) -> LineMillingSpec:
    strategy = kw.pop("strategy", None)
    base = build_line_milling_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado",
        line_tool_id="1903", line_tool_name="E004", line_tool_width=4.0,
        line_security_plane=20.0, line_is_through=False,
        line_target_depth=kw.pop("depth", 5.0),
        line_milling_strategy=strategy,
    )
    return replace(base, **kw) if kw else base


def _bi(cd: float = 4.0):
    return build_bidirectional_milling_strategy_spec(
        allow_multiple_passes=True, axial_cutting_depth=cd)


class FailLoudTest(unittest.TestCase):
    def _assert_rejects(self, **kw):
        with self.assertRaises(UnsupportedOperationError):
            _validate_line_milling(_line(**kw))

    def test_formas_fixtured_pasan(self):
        _validate_line_milling(_line(strategy=_bi(), depth=12.0, side_of_feature="Left",
                                     activate_cnc_correction=False))
        _validate_line_milling(_line(side_of_feature="Left",
                                     approach=build_approach_spec(True, approach_type="Arc"),
                                     retract=build_retract_spec(True, retract_type="Arc")))
        _validate_line_milling(_line(side_of_feature="Left", invert_work=True,
                                     approach=build_approach_spec(True, approach_type="Arc")))

    def test_lado_con_estrategia_no_bi_pasa(self):
        # N035 uni_side_l / zz_side_l: coordenadas desplazadas con cualquier estrategia.
        from pgmx.synthesis.common.strategy import build_unidirectional_milling_strategy_spec
        uni = build_unidirectional_milling_strategy_spec(
            allow_multiple_passes=True, axial_cutting_depth=4.0)
        _validate_line_milling(_line(strategy=uni, depth=12.0, side_of_feature="Left",
                                     activate_cnc_correction=False))

    def test_lado_con_lead_variantes_pasan(self):
        # N035: Lineal, En bajada (helicoidal), velocidad, arco explícito (IGNORADO → lado libre).
        for kw in (dict(approach=build_approach_spec(True, approach_type="Line")),
                   dict(approach=build_approach_spec(True, approach_type="Arc", mode="Down")),
                   dict(approach=build_approach_spec(True, approach_type="Arc", speed=2.0)),
                   dict(approach=build_approach_spec(True, approach_type="Arc", arc_side="Left")),
                   dict(retract=build_retract_spec(True, retract_type="Arc", mode="Up"))):
            _validate_line_milling(_line(side_of_feature="Left", **kw))

    def test_lado_con_lead_no_fixtured(self):
        # Alejamiento Lineal con G41 sigue sin fixture.
        self._assert_rejects(side_of_feature="Left",
                             retract=build_retract_spec(True, retract_type="Line"))


class EndToEndTest(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    def _check(self, stem: str) -> None:
        pgmx = _FIXTURE_DIR / f"{stem}.pgmx"
        ref = _REF_DIR / f"{stem.lower()}.iso"
        if not pgmx.exists() or not ref.exists():
            self.skipTest("fixtures S:/P: no disponibles")
        gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
        exp = [ln.rstrip() for ln in
               ref.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").splitlines()]
        self.assertEqual(gen, exp)

    def test_multipasada_con_lado(self):
        self._check("N_C_cmb_mp_side_l")

    def test_lado_con_leads(self):
        self._check("N_C_cmb_side_l_leads")

    def test_invertir_lado_approach(self):
        self._check("N_C_inv_side_l_app")

    def test_pasante_con_lado(self):
        self._check("N_C_cmb_th_side_l")


if __name__ == "__main__":
    unittest.main()
