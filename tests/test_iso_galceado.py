"""Galceado / Perfilado / Escuadrado — Eje B etapa 4 (N043, 2026-07-23).

El Galceado NO es una feature nueva del ISO: es una RUTA DE AUTORÍA hacia el mismo fresado de
contorno cerrado (N043: ContourFeature y GeneralProfileFeature con la misma geometría y el mismo
ACC dan el mismo byte; el ContourType Pieza/Geometría es invisible). Lo único que cambia el ISO
es ActivateCNCCorrection:

- ACC=true (C.N., estilo A): la polilínea cerrada de N042 — nominal + G42 + lead de 1 mm.
- ACC=false (CAD, estilo B): polígono OFFSETEADO r=w/2 + CUARTO DE ARCO en cada esquina
  (centro = vértice nominal), sin G41/G42 ni leads; plunge a feed de CORTE; el preamble
  CAD omite el ?%ETK[7]=0.

Ver iso/docs/experiments/galceado_perfilado.md.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis.common.leads import build_approach_spec, build_retract_spec
from pgmx.synthesis.milling.contour import ContourSpec
from pgmx.synthesis.milling.polyline import PolylineSegment, PolylineSpec

from iso.synthesis import convert
from iso.synthesis._router import _poly_cad_body, _poly_entry_xy
from iso.synthesis._validation import UnsupportedOperationError, _validate_polyline

_FIXTURE_DIR = Path(r"S:\Maestro\Projects\ProdAction\Programas Manuales")
_REF_DIR = Path(r"P:\USBMIX\ProdAction\Programas Manuales")

_N043_STEMS = (
    "Lote N043_contour - Galceado-Perfilado - Pieza",
    "Lote N043_contour - Galceado-Perfilado - Geometría",
    "Lote N043_contour - Fresado-Escuadrado - CN",
    "Lote N043_contour - Fresado-Escuadrado - CAD",
)


def _rect_cad(**kw) -> PolylineSpec:
    """El contorno del fixture CAD de N043: perímetro 300×300 CCW, E003, Right, ciego −9."""
    base = PolylineSpec(
        start_x=0.0, start_y=0.0,
        segments=(PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0),
                  PolylineSegment(0.0, 300.0), PolylineSegment(0.0, 0.0)),
        feature_name="Escuadrado",
        side_of_feature="Right",
        tool_id="1902", tool_name="E003", tool_width=9.52,
        security_plane=30.0,
        activate_cnc_correction=False,
    )
    return replace(base, **kw) if kw else base


class CadRenderTest(unittest.TestCase):
    """Estilo B derivado del ISO real (fresado-escuadrado - cad.iso), offline."""

    EXPECTED_BODY = [
        "G1 Z30.000 F3000.000",
        "?%ETK[7]=4",
        "G1 Z-9.000 F18000.000",
        "G3 X0.000 Y-4.760 I0.000 J0.000 F18000.000",
        "G1 X300.000 Z-9.000 F18000.000",
        "G3 X304.760 Y0.000 I300.000 J0.000 F18000.000",
        "G1 Y300.000 Z-9.000 F18000.000",
        "G3 X300.000 Y304.760 I300.000 J300.000 F18000.000",
        "G1 X0.000 Z-9.000 F18000.000",
        "G3 X-4.760 Y300.000 I0.000 J300.000 F18000.000",
        "G1 Y0.000 Z-9.000 F18000.000",
        "G1 Z30.000 F18000.000",
    ]

    def test_cuerpo_cad_byte_igual_a_la_referencia(self):
        body, ret_suppresses_g0, out = _poly_cad_body(
            _rect_cad(), 9.0, 30.0, 3000.0, 18000.0)
        self.assertEqual(body, self.EXPECTED_BODY)
        self.assertFalse(ret_suppresses_g0)
        self.assertEqual(out, (-4.76, 0.0))

    def test_entrada_cad_es_el_fin_del_ultimo_borde_offseteado(self):
        # El arranque nominal (0,0) es un VÉRTICE: su offset es un arco. El path arranca donde
        # termina el borde izquierdo offseteado (dir −y, Right ⇒ −x): (−4.76, 0).
        entry = _poly_entry_xy(_rect_cad(), False, False, 0.0, True)
        self.assertEqual(entry, (-4.76, 0.0))


class CadValidatedFormsTest(unittest.TestCase):
    """Formas CAD byte-validadas por N044 (antes eran guardas; ahora el render las cubre)."""

    def test_rectangulo_ccw_right_pasa(self):
        _validate_polyline(_rect_cad())

    def test_cw_right_interno_pasa(self):
        # CW+Right = offset interior = todas esquinas vivas (N044 cad_interno).
        _validate_polyline(_rect_cad(segments=(
            PolylineSegment(0.0, 300.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(300.0, 0.0), PolylineSegment(0.0, 0.0))))

    def test_cw_left_pasa(self):
        # CW+Left = offset exterior = arcos G2 (N044 cad_cw_left).
        _validate_polyline(_rect_cad(side_of_feature="Left", segments=(
            PolylineSegment(0.0, 300.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(300.0, 0.0), PolylineSegment(0.0, 0.0))))

    def test_chaflan_no_ortogonal_pasa(self):
        # Esquina convexa a 45° = arco de ángulo cualquiera (N044 cad_chaflan).
        _validate_polyline(_rect_cad(segments=(
            PolylineSegment(250.0, 0.0), PolylineSegment(300.0, 50.0),
            PolylineSegment(300.0, 300.0), PolylineSegment(0.0, 300.0),
            PolylineSegment(0.0, 0.0))))

    def test_concava_pasa(self):
        # Muesca entrante: esquinas cóncavas = ESQUINA VIVA (N044 cad_concava, pregunta estrella).
        _validate_polyline(_rect_cad(segments=(
            PolylineSegment(150.0, 0.0), PolylineSegment(150.0, 50.0),
            PolylineSegment(200.0, 50.0), PolylineSegment(200.0, 0.0),
            PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(0.0, 300.0), PolylineSegment(0.0, 0.0))))


class CadGuardsTest(unittest.TestCase):
    """Lo que sigue SIN fixture → fail-loud (regla 4: byte-idéntico o rechazo)."""

    def _assert_rejects(self, spec: PolylineSpec, fragment: str) -> None:
        with self.assertRaises(UnsupportedOperationError) as caught:
            _validate_polyline(spec)
        self.assertIn(fragment, str(caught.exception))

    def test_cad_abierta_guardada(self):
        spec = _rect_cad(segments=(PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0)))
        self._assert_rejects(spec, "ABIERTA")

    def test_cad_con_arco_guardado(self):
        spec = _rect_cad(segments=(
            PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(0.0, 300.0, center_x=150.0, center_y=300.0,
                            winding="CounterClockwise"),
            PolylineSegment(0.0, 0.0)))
        self._assert_rejects(spec, "ARCO")

    def test_cad_lado_center_guardado(self):
        # Center no define lado de offset (Right/Left sí tienen fixture).
        self._assert_rejects(_rect_cad(side_of_feature="Center"), "Center")

    def test_cad_con_leads_guardado(self):
        # cad_leads sigue subdeterminado (lead CAD de radio w/2, ≠ el de la línea).
        self._assert_rejects(
            _rect_cad(approach=build_approach_spec(True, approach_type="Arc")),
            "acercamiento")
        self._assert_rejects(
            _rect_cad(retract=build_retract_spec(True, retract_type="Arc")),
            "alejamiento")


class AdapterContourTest(unittest.TestCase):
    """El adapter con los archivos reales de Programas Manuales (requiere S: montado)."""

    def _adapted_specs(self, stem: str):
        pgmx = _FIXTURE_DIR / f"{stem}.pgmx"
        if not pgmx.exists():
            self.skipTest("fixtures S: no disponibles")
        result = adapt_pgmx_path(pgmx)
        return result

    def test_contour_feature_adapta_a_polilinea(self):
        # ContourFeature (Galceado-Perfilado) y GeneralProfileFeature (Fresado-Escuadrado)
        # arrancan en una ESQUINA → rama polilínea (la forma de En-Juego arranca a MITAD de
        # borde y esa sí intercepta a ContourSpec). El tipo de feature es invisible.
        for stem in _N043_STEMS[:3]:
            with self.subTest(stem):
                result = self._adapted_specs(stem)
                self.assertFalse(result.unsupported_entries)
                (entry,) = result.adapted_entries
                self.assertIsInstance(entry.spec, PolylineSpec)
                self.assertNotIsInstance(entry.spec, ContourSpec)
                self.assertTrue(entry.spec.activate_cnc_correction)

    def test_escuadrado_cad_conserva_el_acc(self):
        # Antes el intercept lo mandaba a ContourSpec, que NO tiene campo de corrección: el
        # ActivateCNCCorrection=false se perdía EN SILENCIO (evidencia falsa — regla 1).
        result = self._adapted_specs("Lote N043_contour - Fresado-Escuadrado - CAD")
        self.assertFalse(result.unsupported_entries)
        (entry,) = result.adapted_entries
        self.assertIsInstance(entry.spec, PolylineSpec)
        self.assertFalse(entry.spec.activate_cnc_correction)

    def test_galceado_multiop_sigue_pendiente_fail_loud(self):
        # Galceado.pgmx: op1 ZigZag+CAD y op2 con leads Line/Down+Up — combos sin fixture
        # aislado (lote pendiente). Debe rechazar con mensaje, no aproximar.
        pgmx = _FIXTURE_DIR / "Galceado.pgmx"
        if not pgmx.exists():
            self.skipTest("fixtures S: no disponibles")
        with self.assertRaises(UnsupportedOperationError):
            convert(pgmx)


def _e2e_check(test, pgmx: Path, ref: Path) -> None:
    if not pgmx.exists() or not ref.exists():
        test.skipTest("fixtures S:/P: no disponibles")
    gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
    # Maestro escribe el ISO en ANSI (cp1252), no UTF-8 — con nombres acentuados ("Geometría")
    # la decodificación importa. Los lotes previos eran ASCII puro.
    exp = [ln.rstrip() for ln in ref.read_text(encoding="cp1252").replace("\r\n", "\n").splitlines()]
    test.assertEqual(gen, exp)


class EndToEndN043Test(unittest.TestCase):
    """Byte-idéntico contra Maestro (requiere S:/P: montados)."""

    def test_byte_identico(self):
        for stem in _N043_STEMS:
            with self.subTest(stem):
                _e2e_check(self, _FIXTURE_DIR / f"{stem}.pgmx", _REF_DIR / f"{stem.lower()}.iso")


class EndToEndN044Test(unittest.TestCase):
    """N044: pendientes de la etapa 4, byte-idéntico contra Maestro (requiere S:/P: montados).

    - CN leads Línea (compensado): En cota / En bajada (acercamiento) / En subida (alejamiento).
    - Forma En-Juego (ContourSpec → polilínea del perímetro): con y sin leads Arco.
    - CAD estilo B general: cóncava = ESQUINA VIVA (respuesta a la pregunta estrella), contorno
      interno (CW+Right, todo vivo), Left (arcos G2), chaflán (arco de ángulo cualquiera).
    """

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N044_galceado_combos")
    _REFS = Path(r"P:\USBMIX\ProdAction\N044_galceado_combos")

    STEMS = (
        "N_G_app_line", "N_G_app_line_down", "N_G_ret_line", "N_G_ret_line_up",
        "N_G_leads_line_down_up", "N_G_enjuego", "N_G_enjuego_noleads",
        "N_G_cad_concava", "N_G_cad_interno", "N_G_cad_cw_left", "N_G_cad_chaflan",
    )

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, self._FIXTURES / f"{stem}.pgmx", self._REFS / f"{stem.lower()}.iso")


class PendingN044Test(unittest.TestCase):
    """Combos CAD que quedan fail-loud (regla 4: rechazo con mensaje, no aproximar). Cada uno
    depende de UN fixture y está subdeterminado: cad_leads usa un lead CAD de radio w/2 (≠ el
    lead de la línea, w/2×RM); cad_zigzag es ZigZag en contorno cerrado CAD (la spec de polilínea
    ni siquiera admite ZigZag hoy, y el render sin derivar). Necesitan más fixtures para cerrarlos."""

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N044_galceado_combos")

    def _assert_fail_loud(self, name: str) -> None:
        pgmx = self._FIXTURES / f"{name}.pgmx"
        if not pgmx.exists():
            self.skipTest("fixtures S: no disponibles")
        with self.assertRaises(UnsupportedOperationError):
            convert(pgmx)

    def test_cad_leads_fail_loud(self):
        self._assert_fail_loud("N_G_cad_leads")

    def test_cad_zigzag_fail_loud(self):
        self._assert_fail_loud("N_G_cad_zigzag")


if __name__ == "__main__":
    unittest.main()
