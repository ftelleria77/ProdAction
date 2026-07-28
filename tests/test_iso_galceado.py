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

import re
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis.common.geometry import GeometryPrimitiveSpec
from pgmx.synthesis.common.leads import build_approach_spec, build_retract_spec
from pgmx.synthesis.common.strategy import ZigZagMillingStrategySpec
from pgmx.synthesis.milling.contour import ContourSpec
from pgmx.synthesis.milling.polyline import (
    PolylineSegment,
    PolylineSpec,
    _build_polyline_toolpath_profile,
)

from iso.synthesis import convert
from iso.synthesis._reader import PieceCtx
from iso.synthesis._router import _poly_cad_body, _poly_cad_zigzag_body, _poly_entry_xy
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

    def test_cad_con_leads_no_fixtureados_guardados(self):
        # N045 derivó el lead CAD En cota/Automatic/Right (Arco y Línea). Lo que queda sin
        # fixture sigue rechazado: velocidad propia, modos En bajada/subida, lado explícito
        # del arco, y el offset del otro lado (Left) con lead.
        self._assert_rejects(
            _rect_cad(approach=build_approach_spec(True, approach_type="Arc", speed=2.0)),
            "velocidad")
        self._assert_rejects(
            _rect_cad(approach=build_approach_spec(True, approach_type="Line", mode="Down")),
            "En cota")
        self._assert_rejects(
            _rect_cad(approach=build_approach_spec(True, approach_type="Arc", arc_side="Left")),
            "Automatic")
        self._assert_rejects(
            _rect_cad(side_of_feature="Left",
                      approach=build_approach_spec(True, approach_type="Arc")),
            "Right")


def _zz_strategy(**kw) -> ZigZagMillingStrategySpec:
    base = dict(allow_multiple_passes=True, feed_cutting_depth=3.0, return_cutting_depth=3.0,
                axial_finish_cutting_depth=2.0, overlap=0.0, cutmode="Climb")
    base.update(kw)
    return ZigZagMillingStrategySpec(**base)


def _line_member(sx, sy, sz, ex, ey, ez) -> GeometryPrimitiveSpec:
    return GeometryPrimitiveSpec("Line", (sx, sy, sz), (ex, ey, ez))


def _arc_member(sx, sy, sz, ex, ey, ez, up=True) -> GeometryPrimitiveSpec:
    return GeometryPrimitiveSpec("Arc", (sx, sy, sz), (ex, ey, ez),
                                 normal_vector=(0.0, 0.0, 1.0 if up else -1.0))


def _fake_stored_rect(z_laps, start_z_iso=0.0) -> tuple[GeometryPrimitiveSpec, ...]:
    """Trayectoria almacenada FABRICADA para el rectángulo de `_rect_cad` (esto prueba NUESTRA
    mecánica de walk/emisión — la Z real de Maestro la validan los e2e de N046/Galceado).
    `z_laps` = lista de vueltas, cada una con 8 z_iso finales (ida/vuelta alternadas);
    `start_z_iso` = z del arranque (superficie=0 con rampa; la profundidad en la vuelta única
    plana estilo Galceado)."""
    pts = [(-4.76, 0.0), (0.0, -4.76), (300.0, -4.76), (304.76, 0.0), (304.76, 300.0),
           (300.0, 304.76), (0.0, 304.76), (-4.76, 300.0), (-4.76, 0.0)]
    fwd_kinds = ["arc", "line", "arc", "line", "arc", "line", "arc", "line"]
    members: list[GeometryPrimitiveSpec] = []
    prev_xy, prev_z = pts[0], 18.0 + start_z_iso
    for lap, zs in enumerate(z_laps):
        forward = lap % 2 == 0
        idx = range(1, 9) if forward else range(7, -1, -1)
        kinds = fwd_kinds if forward else [fwd_kinds[7 - k] for k in range(8)]
        for k, pi in enumerate(idx):
            end, z = pts[pi], 18.0 + zs[k]
            maker = _arc_member if kinds[k] == "arc" else _line_member
            args = (*prev_xy, prev_z, *end, z)
            members.append(maker(*args, up=forward) if kinds[k] == "arc" else maker(*args))
            prev_xy, prev_z = end, z
    return tuple(members)


_ZZ_Z_LAPS = [
    [-0.4, -1.0, -1.5, -2.0, -2.4, -2.7, -2.9, -3.0],           # ida en rampa
    [-3.7, -4.3, -5.1, -5.6, -5.9, -5.97, -6.0, -5.99995],      # vuelta (último arco redondea igual)
    [-6.2, -7.0, -7.5, -8.0, -8.4, -8.7, -8.9, -9.0],           # ida en rampa
    [-9.0] * 8,                                                  # vuelta final PLANA
]


class CadZigZagRenderTest(unittest.TestCase):
    """Mecánica del render ZigZag CAD, offline: vueltas alternadas sobre la traza offseteada,
    Z leída de la curva almacenada, Z en arcos solo cuando el REDONDEO cambia, F en todos los
    movimientos. Los bytes REALES de Maestro los validan los e2e (N046 + Galceado.pgmx)."""

    def _spec(self, z_laps=None, start_z_iso=0.0):
        return replace(_rect_cad(), milling_strategy=_zz_strategy(),
                       stored_trajectory=_fake_stored_rect(z_laps or _ZZ_Z_LAPS, start_z_iso))

    def test_cuerpo_zigzag(self):
        ctx = PieceCtx("t", 300.0, 300.0, 18.0, 0.0, 0.0, 0.0)
        body, ret_suppresses_g0, out = _poly_cad_zigzag_body(
            self._spec(), ctx, 9.0, 30.0, 3000.0, 18000.0)
        self.assertEqual(body[:4], [
            "G1 Z30.000 F3000.000",
            "?%ETK[7]=4",
            "G1 Z0.000 F18000.000",                                # plunge a SUPERFICIE
            "G3 X0.000 Y-4.760 Z-0.400 I0.000 J0.000 F18000.000",  # ida: arco con Z de rampa
        ])
        self.assertEqual(body[11], "G1 Y300.000 Z-3.700 F18000.000")   # vuelta: sube el borde izq
        self.assertEqual(body[12], "G2 X0.000 Y304.760 Z-4.300 I0.000 J300.000 F18000.000")
        # Último arco de la vuelta 2: z=-5.99995 redondea a -6.000 = el previo → SIN palabra Z.
        self.assertEqual(body[18], "G2 X-4.760 Y0.000 I0.000 J0.000 F18000.000")
        # Vuelta final plana: G1 repite Z (un solo eje), el arco la omite.
        self.assertEqual(body[27], "G1 Y300.000 Z-9.000 F18000.000")
        self.assertEqual(body[28], "G2 X0.000 Y304.760 I0.000 J300.000 F18000.000")
        self.assertEqual(body[-1], "G1 Z30.000 F18000.000")
        self.assertEqual(len(body), 3 + 32 + 1)
        self.assertFalse(ret_suppresses_g0)
        self.assertEqual(out, (-4.76, 0.0))

    def test_vuelta_unica_plana(self):
        # Galceado.pgmx op1 (pa=pr=uh=0): UNA vuelta plana a profundidad → plunge DIRECTO a -prof.
        ctx = PieceCtx("t", 300.0, 300.0, 18.0, 0.0, 0.0, 0.0)
        body, _ret, _out = _poly_cad_zigzag_body(
            self._spec(z_laps=[[-19.0] * 8], start_z_iso=-19.0), ctx, 19.0, 30.0, 3000.0, 18000.0)
        self.assertEqual(body[2], "G1 Z-19.000 F18000.000")
        self.assertEqual(body[3], "G3 X0.000 Y-4.760 I0.000 J0.000 F18000.000")
        self.assertEqual(len(body), 3 + 8 + 1)

    def test_curva_almacenada_que_no_calza_rechaza(self):
        # Miembros de menos (vuelta incompleta) → fail-loud, no aproximar.
        ctx = PieceCtx("t", 300.0, 300.0, 18.0, 0.0, 0.0, 0.0)
        spec = self._spec()
        spec = replace(spec, stored_trajectory=spec.stored_trajectory[:-3])
        with self.assertRaises(UnsupportedOperationError) as caught:
            _poly_cad_zigzag_body(spec, ctx, 9.0, 30.0, 3000.0, 18000.0)
        self.assertIn("no calza", str(caught.exception))


class CadZigZagGuardsTest(unittest.TestCase):
    """Guardas del ZigZag CAD (regla 4): solo la forma fixtureada por N046/Galceado pasa."""

    def _zz_spec(self, **kw):
        spec = replace(_rect_cad(), milling_strategy=_zz_strategy(),
                       stored_trajectory=_fake_stored_rect(_ZZ_Z_LAPS))
        return replace(spec, **kw) if kw else spec

    def _assert_rejects(self, spec, fragment):
        with self.assertRaises(UnsupportedOperationError) as caught:
            _validate_polyline(spec)
        self.assertIn(fragment, str(caught.exception))

    def test_forma_fixtureada_pasa(self):
        _validate_polyline(self._zz_spec())

    def test_zigzag_con_acc_true_guardado(self):
        self._assert_rejects(self._zz_spec(activate_cnc_correction=True), "ZigZag con corrección CAD")

    def test_uni_bi_en_polilinea_siguen_guardadas(self):
        from pgmx.synthesis.common.strategy import BidirectionalMillingStrategySpec
        self._assert_rejects(
            replace(_rect_cad(), milling_strategy=BidirectionalMillingStrategySpec(
                allow_multiple_passes=True, axial_cutting_depth=4.0)),
            "estrategia multipasada")

    def test_sin_curva_almacenada_guardado(self):
        self._assert_rejects(self._zz_spec(stored_trajectory=()), "TrajectoryPath")

    def test_con_leads_guardado(self):
        self._assert_rejects(
            self._zz_spec(approach=build_approach_spec(True, approach_type="Arc")),
            "acercamiento/alejamiento")

    def test_lado_left_guardado(self):
        self._assert_rejects(self._zz_spec(side_of_feature="Left"), "Right")

    def test_cutmode_no_climb_guardado(self):
        self._assert_rejects(
            self._zz_spec(milling_strategy=_zz_strategy(cutmode="Conventional")), "Climb")

    def test_borde_diagonal_guardado(self):
        self._assert_rejects(self._zz_spec(segments=(
            PolylineSegment(250.0, 0.0), PolylineSegment(300.0, 50.0),
            PolylineSegment(300.0, 300.0), PolylineSegment(0.0, 300.0),
            PolylineSegment(0.0, 0.0))), "DIAGONAL")

    def test_esquina_viva_guardada(self):
        # Muesca entrante (cóncava = viva en el CAD single-pass): en zigzag sigue sin fixture.
        self._assert_rejects(self._zz_spec(segments=(
            PolylineSegment(150.0, 0.0), PolylineSegment(150.0, 50.0),
            PolylineSegment(200.0, 50.0), PolylineSegment(200.0, 0.0),
            PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(0.0, 300.0), PolylineSegment(0.0, 0.0))), "VIVA")

    def test_arranque_a_mitad_de_borde_pasa_en_zigzag(self):
        # Galceado.pgmx op1: vértice colineal pass-through — admitido SOLO en la ruta zigzag.
        spec = self._zz_spec(start_x=150.0, start_y=0.0, segments=(
            PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(0.0, 300.0), PolylineSegment(0.0, 0.0),
            PolylineSegment(150.0, 0.0)))
        # (la curva fabricada del rectángulo ya no calza acá — la validación geométrica es lo
        # que se prueba; el walk contra la almacenada es del render y tiene su propio test)
        _validate_polyline(spec)

    def test_colineal_sigue_guardado_en_cad_single_pass(self):
        spec = _rect_cad(start_x=150.0, start_y=0.0, segments=(
            PolylineSegment(300.0, 0.0), PolylineSegment(300.0, 300.0),
            PolylineSegment(0.0, 300.0), PolylineSegment(0.0, 0.0),
            PolylineSegment(150.0, 0.0)))
        self._assert_rejects(spec, "colineal")

    def test_autoria_zigzag_en_polilinea_fail_loud(self):
        # La AUTORÍA no puede fabricar la rampa Z (la genera Maestro): rechazo con mensaje.
        spec = replace(_rect_cad(), milling_strategy=_zz_strategy())
        with self.assertRaises(ValueError) as caught:
            _build_polyline_toolpath_profile(18.0, -9.0, spec)
        self.assertIn("autoría", str(caught.exception))


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

    def test_galceado_completo_byte_identico(self):
        # Galceado.pgmx COMPLETO (cierre de la etapa 4): op1 ZigZag+CAD (pa=pr=uh=0 → UNA
        # vuelta plana a −19, pasante 18+1, arranque a MITAD de borde) + cambio de herramienta
        # E001→E003 + op2 compensada con leads Line En bajada/En subida. De acá salieron tres
        # reglas: la vuelta única plana del zigzag, el colineal pass-through, y que el reset
        # del preamble lo decide la PRIMERA op del router (no cualquiera).
        _e2e_check(self, _FIXTURE_DIR / "Galceado.pgmx", _REF_DIR / "galceado.iso")


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


class EndToEndManualLeadsTest(unittest.TestCase):
    """`Galceado_Ar3Cota` (2026-07-27): galceado de AUTORÍA 100% MANUAL en Maestro — contorno de
    pieza, E003, sin estrategia, acercamiento y alejamiento Arco RM=3 En cota, C.N. (ACC=true).

    Es la primera referencia GENUINA del contorno compensado con leads: la traza y el lead los
    calculó Maestro, no nuestro sintetizador. Byte-idéntico ⇒ valida el modelo de N042/N044 (lead
    = arco tangente de radio (w/2)×RM anclado al vértice nominal, G42, 1 mm de activación) sin la
    circularidad que arrastraban los lotes autorados.
    """

    STEMS = ("Galceado_Ar3Cota", "Galceado_Ar3Cota_Geom",
             "Fresado_perimetral_Ar3Cota_CAD", "Fresado_perimetral_Ar3Cota_CN")

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, _FIXTURE_DIR / f"{stem}.pgmx", _REF_DIR / f"{stem.lower()}.iso")

    def test_lead_cad_confirmado_contra_autoria_manual(self):
        # El par Fresado_perimetral (mismo contorno, mismos leads Arco RM=3 En cota, solo cambia
        # C.N./CAD) CIERRA la pregunta de N045/N046: en el CAD, Maestro CALCULÓ y almacenó el lead
        # con radio (w/2)×(RM−1)=9.52 anclado a la traza OFFSETEADA, y lo copió al ISO — la regla
        # de N045, ahora sin circularidad. En el C.N., el MISMO pgmx almacena la misma curva pero
        # el ISO emite (w/2)×RM=14.28 sobre el vértice nominal (recalculado).
        refs = {t: _REF_DIR / f"fresado_perimetral_ar3cota_{t}.iso" for t in ("cad", "cn")}
        if not all(r.exists() for r in refs.values()):
            self.skipTest("fixtures P: no disponibles")
        cad = refs["cad"].read_text(encoding="cp1252")
        cn = refs["cn"].read_text(encoding="cp1252")
        self.assertIn("G2 X-4.760 Y0.000 I-14.280 J0.000", cad)   # r=9.52 sobre la offseteada
        self.assertIn("G2 X0.000 Y0.000 I0.000 J-14.280", cn)     # r=14.28 sobre el vértice
        self.assertNotIn("G42", cad)                              # CAD: sin corrección de control
        self.assertIn("G42", cn)

    def test_contour_type_es_invisible_en_el_iso(self):
        # Los dos fixtures son el MISMO galceado con Perfil: Pieza (Workpiece) y Perfil: Geometría
        # (Geometry). N043 ya lo había derivado con archivos autorados; acá queda confirmado con
        # dos programas MANUALES: los ISO son idénticos salvo el comentario con el nombre del .pgm.
        refs = [_REF_DIR / f"{s.lower()}.iso" for s in self.STEMS]
        if not all(r.exists() for r in refs):
            self.skipTest("fixtures P: no disponibles")
        cuerpos = [[ln.rstrip() for ln in r.read_text(encoding="cp1252")
                    .replace("\r\n", "\n").splitlines()][1:] for r in refs]
        self.assertEqual(cuerpos[0], cuerpos[1])

    def test_maestro_ignora_la_curva_almacenada_con_acc_true(self):
        # El .pgmx GUARDA el lead con radio (w/2)×(RM−1)=9.52 y en una posición que ni siquiera
        # toca el arranque del contorno; el ISO emite (w/2)×RM=14.28 anclado al vértice (0,0).
        # Con ACC=true Maestro recalcula el lead del spec — lo contrario de lo que hace en CAD
        # (N046). Este test fija esa asimetría, que es la que decide si el converter puede
        # recalcular o tiene que leer la curva.
        pgmx = _FIXTURE_DIR / "Galceado_Ar3Cota.pgmx"
        ref = _REF_DIR / "galceado_ar3cota.iso"
        if not pgmx.exists() or not ref.exists():
            self.skipTest("fixtures S:/P: no disponibles")
        iso = ref.read_text(encoding="cp1252")
        self.assertIn("G2 X0.000 Y0.000 I0.000 J-14.280", iso)   # emitido: r = (w/2)×RM
        with zipfile.ZipFile(pgmx) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".xml"))
            xml = z.read(name).decode("utf-8", "replace")
        radios = [float(ln.split()[-1]) for block in re.findall(
                      r"<\w+:_serializingMembers[^>]*>(.*?)</\w+:_serializingMembers>", xml, re.S)
                  for item in re.findall(r"<\w+:string>(.*?)</\w+:string>", block, re.S)
                  for ln in [item.strip().split("\n")[-1]] if ln.startswith("2 ")]
        w2 = 9.52 / 2.0
        # Los arcos del CUERPO son las esquinas (r = w/2); los dos leads son los de r = (w/2)×(RM−1).
        leads = [r for r in radios if abs(r - w2) > 1e-6]
        self.assertTrue(leads, "no se encontraron los arcos de lead en la curva almacenada")
        for r in leads:
            self.assertAlmostEqual(r, w2 * (3 - 1), places=6)      # almacenado: (w/2)×(RM−1)=9.52
        self.assertNotAlmostEqual(leads[0], w2 * 3, places=6)      # emitido: (w/2)×RM=14.28


class EndToEndN045Test(unittest.TestCase):
    """N045: el lead del contorno CAD, byte-idéntico contra Maestro (requiere S:/P: montados).

    Barrido que separa las dos dependencias que N044 dejaba confundidas en un solo fixture:
    RM (1/2/3 con la misma fresa) y fresa (E001/E003/E004 con la misma RM). Resultado: el lead
    CAD usa las MISMAS fórmulas que en estrategia — Arco (w/2)×(RM−1), con RM=1 omitiendo el
    arco; Línea (w/2)×RM — ancladas a la tangente de la traza OFFSETEADA, no a la nominal.
    Los tres `cad_zz` son el contorno CN sin estrategia (el ZigZag no llegó a agregarse en
    Maestro): valen como regresión de profundidad/pasante, no cubren el zigzag CAD.
    """

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N045_galceado_cad_combos")
    _REFS = Path(r"P:\USBMIX\ProdAction\N045_galceado_cad_combos")

    STEMS = (
        "N_G5_cad_leads_rm1", "N_G5_cad_leads_rm2", "N_G5_cad_leads_rm3",
        "N_G5_cad_leads_e001", "N_G5_cad_leads_e004", "N_G5_cad_leads_line",
        "N_G5_cad_zz_d9", "N_G5_cad_zz_d13", "N_G5_cad_zz_d18",
    )

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, self._FIXTURES / f"{stem}.pgmx", self._REFS / f"{stem.lower()}.iso")


class EndToEndN046Test(unittest.TestCase):
    """N046: el ZigZag CAD byte-idéntico + los envenenados como doc de la semántica de copia.

    Los 3 `zz` volvieron de Maestro con la estrategia agregada (`ZigZagMilling`, ACC=false
    forzado): la curva almacenada trae las vueltas alternadas con la rampa Z que GENERÓ Maestro
    (no es función de la longitud de arco — no hay fórmula), y el ISO la COPIA. El converter
    LEE esa Z y recomputa el XY (I/J al vértice nominal). Requiere S:/P: montados."""

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N046_cad_lead_poison")
    _REFS = Path(r"P:\USBMIX\ProdAction\N046_cad_lead_poison")

    STEMS = ("N_G6_zz_d9", "N_G6_zz_d13", "N_G6_zz_d18")

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, self._FIXTURES / f"{stem}.pgmx", self._REFS / f"{stem.lower()}.iso")

    def test_envenenados_documentan_la_semantica_de_copia(self):
        # Los 2 envenenados (lead-in almacenado corrupto a propósito) CONVIERTEN pero NO
        # byte-idéntico: el converter recalcula el lead CAD (validado contra autoría manual en
        # Fresado_perimetral_Ar3Cota) y Maestro copió el veneno. Son la regresión que documenta
        # que con ACC=false manda lo ALMACENADO; un archivo así no lo produce ninguna autoría
        # real. Si algún día este test falla porque salieron byte-idénticos, el converter pasó
        # a leer la curva del lead — revisar qué más cambió.
        for stem, poison_frag in (("N_G6_poison_arc", "I-16.760"), ("N_G6_poison_line", "Y25.000")):
            pgmx = self._FIXTURES / f"{stem}.pgmx"
            ref = self._REFS / f"{stem.lower()}.iso"
            if not pgmx.exists() or not ref.exists():
                self.skipTest("fixtures S:/P: no disponibles")
            with self.subTest(stem):
                gen = convert(pgmx)
                iso = ref.read_text(encoding="cp1252")
                self.assertIn(poison_frag, iso)      # Maestro emitió el VENENO almacenado
                self.assertNotIn(poison_frag, gen)   # nosotros, el recálculo del spec


class ClosedN044Test(unittest.TestCase):
    """Los 2 fail-loud que N044 dejó subdeterminados, hoy CERRADOS por lotes posteriores.

    `cad_leads`: N045 derivó el lead CAD ((w/2)×(RM−1) sobre la traza offseteada) y el fixture
    que planteó la pregunta cierra byte-idéntico con esa regla, sin tocarlo. `cad_zigzag`: N046
    derivó el ZigZag CAD (la Z se LEE de la curva almacenada — con ACC=false Maestro la copia)
    y este fixture, cuya estrategia agregó Fermín en Maestro, cierra byte-idéntico solo."""

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N044_galceado_combos")
    _REFS = Path(r"P:\USBMIX\ProdAction\N044_galceado_combos")

    def test_cad_zigzag_cierra_con_la_regla_de_n046(self):
        # Validación CRUZADA (como cad_leads con N045): el fixture que planteó la pregunta
        # cae solo con la regla derivada de N046, sin tocarlo.
        _e2e_check(self, self._FIXTURES / "N_G_cad_zigzag.pgmx",
                   self._REFS / "n_g_cad_zigzag.iso")

    def test_cad_leads_de_n044_cierra_con_la_regla_de_n045(self):
        # Validación CRUZADA: el fixture que planteó la pregunta (RM=2, donde (w/2)×(RM−1) y
        # w/2 coinciden) tiene que caer solo con la regla derivada del barrido de N045.
        _e2e_check(self, self._FIXTURES / "N_G_cad_leads.pgmx",
                   self._REFS / "n_g_cad_leads.iso")


if __name__ == "__main__":
    unittest.main()
