"""Vaciado (pocket milling) — Eje B etapa 5, lote N047 (2026-07-28).

El postprocesador COPIA la trayectoria ALMACENADA del vaciado (los 2 envenenados de N047
salieron al ISO con el veneno) — el converter LEE `PocketSpec.stored_trajectories` (cableada
por el adapter desde los TrajectoryPath del .pgmx) y emite UN G1 por miembro a feed de CORTE,
con la bajada a security a feed de plunge y ETK[7]=4 en posición estilo multipasada (sin
reset de preamble). ISO_z = z_almacenada − ESPESOR (coordenadas de PIEZA, z=0 en la base).

Los gemelos manuales del lote (dibujados en Maestro desde cero) validaron sin circularidad:
el cuerpo es byte-idéntico al sintetizado, y trajeron el alias de campo "A" → AB (el área
default de Maestro) y el footer sin Xn para pockets.

Ver iso/docs/experiments/vaciado.md.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from pgmx.synthesis.common.geometry import GeometryPrimitiveSpec
from pgmx.synthesis.common.leads import build_approach_spec
from pgmx.synthesis.milling.pocket import PocketSpec
from pgmx.synthesis import build_contour_parallel_milling_strategy_spec

from iso.synthesis import convert
from iso.synthesis._reader import PieceCtx
from iso.synthesis._router import _pocket_body
from iso.synthesis._validation import UnsupportedOperationError, _validate_pocket

_FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N047_vaciado_baseline")
_REFS = Path(r"P:\USBMIX\ProdAction\N047_vaciado_baseline")

_RECT = ((0.0, 0.0), (300.0, 0.0), (300.0, 300.0), (0.0, 300.0), (0.0, 0.0))


def _line_member(sx, sy, sz, ex, ey, ez) -> GeometryPrimitiveSpec:
    return GeometryPrimitiveSpec("Line", (sx, sy, sz), (ex, ey, ez))


def _chain(points) -> tuple[GeometryPrimitiveSpec, ...]:
    """Miembros recta encadenados por una lista de puntos 3D (trayectoria fabricada — esto
    prueba NUESTRA mecánica de emisión; los bytes reales los validan los e2e de N047)."""
    return tuple(_line_member(*a, *b) for a, b in zip(points, points[1:]))


# Mini-vaciado plausible: un anillo a −9 (pieza 300×300×18 → z almacenada 9).
_RING = _chain([(140.0, 140.0, 9.0), (160.0, 140.0, 9.0), (160.0, 160.0, 9.0),
                (140.0, 160.0, 9.0), (140.0, 140.0, 9.0)])


def _pocket(**kw) -> PocketSpec:
    from pgmx.synthesis import build_pocket_spec
    stored = kw.pop("stored_trajectories", (_RING,))
    strategy_kw = {k: kw.pop(k) for k in ("allow_multiple_passes", "axial_cutting_depth",
                                          "axial_finish_cutting_depth") if k in kw}
    spec = build_pocket_spec(
        contour_points=list(kw.pop("contour_points", _RECT)),
        tool_id="1902", tool_name="E003", tool_width=9.52,
        security_plane=30.0,
        milling_strategy=build_contour_parallel_milling_strategy_spec(**strategy_kw),
        target_depth=kw.pop("target_depth", 9.0),
        **{k: v for k, v in kw.items() if k in (
            "is_through", "approach_enabled", "approach_type",
            "allowance_side", "allowance_bottom", "boss_contours")},
    )
    spec = replace(spec, stored_trajectories=stored)
    extra = {k: v for k, v in kw.items() if k not in (
        "is_through", "approach_enabled", "approach_type",
        "allowance_side", "allowance_bottom", "boss_contours")}
    return replace(spec, **extra) if extra else spec


def _body(spec, depth=9.0):
    ctx = PieceCtx("t", 300.0, 300.0, 18.0, 0.0, 0.0, 0.0)
    # svl/svr/z_approach del E003 (TLC 111.5, w/2 4.76) — solo alimentan los bloques de
    # transición entre trayectorias.
    return _pocket_body(spec, ctx, depth, 30.0, 3000.0, 18000.0, 111.5, 4.76, 141.5)


class PocketRenderTest(unittest.TestCase):
    """Mecánica del cuerpo del vaciado, offline (los bytes reales: e2e N047 + manuales)."""

    def test_cuerpo_copia_la_trayectoria_almacenada(self):
        body, ret_suppresses_g0, out = _body(_pocket())
        self.assertEqual(body, [
            "G1 Z30.000 F3000.000",              # bajada a security a feed de PLUNGE
            "?%ETK[7]=4",
            "G1 Z-9.000 F18000.000",             # plunge al primer nivel a feed de CORTE
            "G1 X160.000 Z-9.000 F18000.000",    # anillo: un G1 por miembro, Z repetida
            "G1 Y160.000 Z-9.000 F18000.000",
            "G1 X140.000 Z-9.000 F18000.000",
            "G1 Y140.000 Z-9.000 F18000.000",
            "G1 Z30.000 F18000.000",             # retracción final a feed de corte
        ])
        self.assertFalse(ret_suppresses_g0)
        self.assertEqual(out, (140.0, 140.0))

    def test_transiciones_de_nivel_multipaso(self):
        # LiftShiftPlunge materializa las transiciones DENTRO de la trayectoria: subida a
        # security (z almacenada 48 = 18+30), traslado y bajada — todos G1 a feed de corte.
        stored = _chain([
            (140.0, 140.0, 13.0), (160.0, 140.0, 13.0), (160.0, 160.0, 13.0),
            (160.0, 160.0, 48.0),                 # sube a security
            (140.0, 140.0, 48.0),                 # traslado en security (diagonal)
            (140.0, 140.0, 9.0),                  # baja al nivel final
            (160.0, 140.0, 9.0), (160.0, 160.0, 9.0),
        ])
        body, _ret, _out = _body(_pocket(stored_trajectories=(stored,)))
        self.assertIn("G1 Z30.000 F18000.000", body[3:])          # subida en G1, no G0
        self.assertIn("G1 X140.000 Y140.000 F18000.000", body)    # traslado diagonal sin Z
        self.assertIn("G1 Z-9.000 F18000.000", body[4:])          # plunge al nivel final

    def test_arcos_g2_g3_con_centro_reajustado(self):
        # Manual 2026-07-30: arco plano → G3 (normal +z) / G2 (−z), I/J del centro
        # REAJUSTADO a los endpoints redondeados (acá exactos → coincide con el almacenado).
        arco_ccw = GeometryPrimitiveSpec(
            "Arc", (160.0, 160.0, 9.0), (150.0, 170.0, 9.0),
            center_point=(150.0, 160.0, 9.0), radius=10.0, normal_vector=(0.0, 0.0, 1.0))
        stored = _RING[:2] + (arco_ccw,) + (
            _line_member(150.0, 170.0, 9.0, 140.0, 140.0, 9.0),)
        body, _ret, _out = _body(_pocket(stored_trajectories=(stored,)))
        self.assertIn("G3 X150.000 Y170.000 I150.000 J160.000 F18000.000", body)

    def test_dos_trayectorias_transicion_de_pasada(self):
        # Isla (manual 2026-07-30): cada trayectoria es una PASADA de misma fresa — teardown
        # no-último (ETK[7]=0 primero) + G17/MLV=2 + triple G0 + setup D1 + plunge de nuevo.
        anillo2 = _chain([(200.0, 200.0, 9.0), (210.0, 200.0, 9.0), (210.0, 210.0, 9.0),
                          (200.0, 200.0, 9.0)])
        body, _ret, out = _body(_pocket(stored_trajectories=(_RING, anillo2)))
        i = body.index("?%ETK[7]=0")
        self.assertEqual(body[i - 1], "G1 Z30.000 F18000.000")    # fin de la trayectoria 1
        self.assertEqual(body[i + 1:i + 8], [
            "G0 Z30.000", "D0", "SVL 0.000", "VL6=0.000", "SVR 0.000", "VL7=0.000", "G17"])
        self.assertIn("G0 X140.000 Y140.000 Z141.500", body)      # ancla: fin de traj 1
        self.assertEqual(body.count("G0 X200.000 Y200.000 Z141.500"), 2)  # entrada ×2
        self.assertEqual(body.count("?%ETK[7]=4"), 2)             # plunge por trayectoria
        self.assertEqual(out, (200.0, 200.0))

    def test_trayectoria_discontinua_rechaza(self):
        rota = _RING[:2] + (_line_member(200.0, 200.0, 9.0, 210.0, 200.0, 9.0),)
        with self.assertRaises(UnsupportedOperationError) as caught:
            _body(_pocket(stored_trajectories=(rota,)))
        self.assertIn("DISCONTINUA", str(caught.exception))

    def test_profundidad_inconsistente_rechaza(self):
        with self.assertRaises(UnsupportedOperationError) as caught:
            _body(_pocket(), depth=12.0)
        self.assertIn("inconsistente", str(caught.exception))

    def test_arco_inclinado_rechaza(self):
        # Solo hay fixture de arcos PLANOS: un arco con normal inclinada → fail-loud.
        arco = _RING + (GeometryPrimitiveSpec(
            "Arc", (140.0, 140.0, 9.0), (150.0, 150.0, 9.0),
            center_point=(145.0, 145.0, 9.0), radius=7.07,
            normal_vector=(0.3, 0.0, 0.954)),)
        with self.assertRaises(UnsupportedOperationError) as caught:
            _body(_pocket(stored_trajectories=(arco,)))
        self.assertIn("inclinado", str(caught.exception))


class PocketGuardsTest(unittest.TestCase):
    """Lo NO fixtureado por N047 → fail-loud (regla 4)."""

    def _assert_rejects(self, spec: PocketSpec, fragment: str) -> None:
        with self.assertRaises(UnsupportedOperationError) as caught:
            _validate_pocket(spec)
        self.assertIn(fragment, str(caught.exception))

    def test_forma_fixtureada_pasa(self):
        _validate_pocket(_pocket())

    def test_multipaso_fixtureado_pasa(self):
        _validate_pocket(_pocket(target_depth=12.0, allow_multiple_passes=True,
                                 axial_cutting_depth=5.0, axial_finish_cutting_depth=2.0))

    def test_pasante_guardado(self):
        self._assert_rejects(_pocket(is_through=True, target_depth=None), "PASANTE")

    def test_leads_guardados(self):
        spec = replace(_pocket(), approach=build_approach_spec(True, approach_type="Arc"))
        self._assert_rejects(spec, "acercamiento")

    def test_rebaba_pasa(self):
        # LEVANTADA por N048 (reb_p20/reb_m20): AllowanceSide solo corre los anillos de la
        # trayectoria almacenada, que el render copia.
        _validate_pocket(_pocket(allowance_side=20.0))
        _validate_pocket(_pocket(allowance_side=-20.0))

    def test_allowance_bottom_guardado(self):
        # Sin fixture: no sabemos si la ventana Vaciado lo expone (checklist de capturas).
        self._assert_rejects(_pocket(allowance_bottom=2.0), "AllowanceBottom")

    def test_avanz_rotacion_guardados(self):
        # La ventana Vaciado expone Avanz./Rotación (captura UI 2026-07-29) pero no hay
        # fixture ISO: sin la guarda, un override real convertía con el feed del catálogo
        # EN SILENCIO.
        self._assert_rejects(replace(_pocket(), feedrate=3.0), "Avanz")
        self._assert_rejects(replace(_pocket(), spindle=12000.0), "Avanz")

    def test_isla_rectangular_pasa(self):
        # LEVANTADA por el manual 2026-07-30 (isla rectangular, dos trayectorias).
        _validate_pocket(_pocket(
            boss_contours=(((100.0, 100.0), (200.0, 100.0), (200.0, 200.0),
                            (100.0, 200.0), (100.0, 100.0)),),
            stored_trajectories=(_RING, _RING)))

    def test_isla_no_rectangular_guardada(self):
        # Isla circular (polilínea muestreada) o forma libre: sin fixture aún.
        import math as _math
        circulo = tuple(
            (150.0 + 30.0 * _math.cos(2 * _math.pi * k / 16),
             150.0 + 30.0 * _math.sin(2 * _math.pi * k / 16)) for k in range(17))
        self._assert_rejects(_pocket(boss_contours=(circulo,)), "ISLA no rectangular")

    def test_parametros_de_estrategia_n048_pasan(self):
        # LEVANTADOS por N048 (uno aislado por fixture, 8/8 byte-idéntico): todos mediados
        # por la trayectoria almacenada que el render copia; el helicoidal es directamente
        # INVISIBLE (ni la trayectoria ni el ISO cambian).
        for kw in (
            dict(rotation_direction="Clockwise"),
            dict(stroke_connection_strategy="Straghtline"),
            dict(inside_to_outside=False),
            dict(overlap=0.25),
            dict(is_helic_strategy=True),
        ):
            with self.subTest(**kw):
                strategy = build_contour_parallel_milling_strategy_spec(**kw)
                _validate_pocket(replace(_pocket(), milling_strategy=strategy))

    def test_cutmode_no_climb_guardado(self):
        # Todo el corpus (lab + N047/N048) trae Climb; sin UI conocida que lo cambie.
        strategy = build_contour_parallel_milling_strategy_spec(cutmode="Conventional")
        self._assert_rejects(replace(_pocket(), milling_strategy=strategy), "Cutmode")

    def test_contorno_no_rectangular_guardado(self):
        forma_l = ((0.0, 0.0), (300.0, 0.0), (300.0, 150.0), (150.0, 150.0),
                   (150.0, 300.0), (0.0, 300.0), (0.0, 0.0))
        self._assert_rejects(_pocket(contour_points=forma_l), "vértice interior")
        diagonal = ((0.0, 0.0), (300.0, 50.0), (300.0, 300.0), (0.0, 300.0), (0.0, 0.0))
        self._assert_rejects(_pocket(contour_points=diagonal), "diagonal")

    def test_arranque_a_mitad_de_borde_pasa(self):
        # Vaciado_002 del corpus: rectángulo con punto colineal extra sobre el perímetro.
        medio = ((150.0, 0.0), (300.0, 0.0), (300.0, 300.0), (0.0, 300.0), (0.0, 0.0),
                 (150.0, 0.0))
        _validate_pocket(_pocket(contour_points=medio))

    def test_sin_trayectoria_almacenada_guardado(self):
        self._assert_rejects(_pocket(stored_trajectories=()), "trayectorias almacenadas")

    def test_dos_trayectorias_pasan_tres_no(self):
        # DOS fixtureadas por la isla rectangular (manual 2026-07-30); más → sin fixture.
        _validate_pocket(_pocket(stored_trajectories=(_RING, _RING)))
        self._assert_rejects(_pocket(stored_trajectories=(_RING, _RING, _RING)),
                             "trayectorias almacenadas")


def _e2e_check(test, pgmx: Path, ref: Path) -> None:
    if not pgmx.exists() or not ref.exists():
        test.skipTest("fixtures S:/P: no disponibles")
    gen = [ln.rstrip() for ln in convert(pgmx).splitlines()]
    exp = [ln.rstrip() for ln in ref.read_text(encoding="cp1252")
           .replace("\r\n", "\n").splitlines()]
    test.assertEqual(gen, exp)


class EndToEndN047Test(unittest.TestCase):
    """N047 byte-idéntico contra Maestro (requiere S:/P: montados).

    Los envenenados también son byte-idénticos ACÁ (a diferencia de los de N046): como el
    render COPIA lo almacenado igual que Maestro, el veneno viaja por los dos lados. Son la
    prueba viva de la semántica de copia — si algún día el render pasara a recalcular, estos
    dos son los primeros que rompen. Los gemelos `_manual` (dibujados en Maestro desde cero,
    campo default A→AB, sin Xn) validan sin circularidad."""

    STEMS = (
        "N_V_e001_d9", "N_V_e002_d9", "N_V_e003_d4", "N_V_e003_d9", "N_V_e004_d9",
        "N_V_e005_d9", "N_V_e006_d9", "N_V_e006_mp_d12", "N_V_e007_d9",
        "N_V_e003_d9_manual", "N_V_e006_mp_d12_manual",
        "N_V_poison_xy", "N_V_poison_z",
    )

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, _FIXTURES / f"{stem}.pgmx", _REFS / f"{stem.lower()}.iso")

    def test_los_envenenados_prueban_la_copia(self):
        # El veneno está en el ISO de Maestro Y en el nuestro: ambos copian lo almacenado.
        ref = _REFS / "n_v_poison_xy.iso"
        pgmx = _FIXTURES / "N_V_poison_xy.pgmx"
        if not ref.exists() or not pgmx.exists():
            self.skipTest("fixtures S:/P: no disponibles")
        self.assertIn("X80.160 Y79.160", ref.read_text(encoding="cp1252"))
        self.assertIn("X80.160 Y79.160", convert(pgmx))


class EndToEndN048Test(unittest.TestCase):
    """N048: los parámetros de la estrategia, uno por fixture, byte-idéntico (requiere
    S:/P:). Todos mediados por la trayectoria ALMACENADA que el render copia — el lote
    valida que ninguno toca las convenciones de emisión (feeds/orden/G-codes). El par
    mp_e003/straghtline_mp aísla la Conexión entre huecos donde de verdad difiere (las
    transiciones de nivel: a security vs dentro de la pieza, ambas DENTRO de la
    trayectoria); el helicoidal quedó confirmado INVISIBLE."""

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N048_vaciado_estrategia")
    _REFS = Path(r"P:\USBMIX\ProdAction\N048_vaciado_estrategia")

    STEMS = ("N_V8_horario", "N_V8_afuera_adentro", "N_V8_overlap25", "N_V8_helicoidal",
             "N_V8_mp_e003", "N_V8_straghtline_mp", "N_V8_reb_p20", "N_V8_reb_m20")

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, self._FIXTURES / f"{stem}.pgmx",
                           self._REFS / f"{stem.lower()}.iso")

    def test_helicoidal_es_invisible_en_el_iso(self):
        # Mismo cuerpo que el baseline de N047 (solo cambia el comentario % del nombre):
        # el flag no toca ni la trayectoria almacenada ni el ISO.
        hel = self._REFS / "n_v8_helicoidal.iso"
        base = _REFS / "n_v_e003_d9.iso"
        if not hel.exists() or not base.exists():
            self.skipTest("fixtures P: no disponibles")
        cuerpo = lambda p: [ln.rstrip() for ln in p.read_text(encoding="cp1252")
                            .replace("\r\n", "\n").splitlines()][1:]
        self.assertEqual(cuerpo(hel), cuerpo(base))


class EndToEndN049Test(unittest.TestCase):
    """N049: contornos parciales/arranques/excedidos, byte-idéntico (requiere S:/P:).
    Salió 7/7 DIRECTO, sin levantar nada: el render copia lo almacenado y el contorno solo
    gatea validación — la red que confirma que no hay convenciones ocultas por contorno."""

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\N049_vaciado_contornos")
    _REFS = Path(r"P:\USBMIX\ProdAction\N049_vaciado_contornos")

    STEMS = ("N_V9_parcial_centro", "N_V9_parcial_esquina", "N_V9_parcial_banda",
             "N_V9_arranque_mitad", "N_V9_contorno_horario", "N_V9_excede_pieza",
             "N_V9_parcial_chico_e006")

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, self._FIXTURES / f"{stem}.pgmx",
                           self._REFS / f"{stem.lower()}.iso")


class EndToEndManualesArcosTest(unittest.TestCase):
    """Manuales de arcos (2026-07-30, dibujados EN Maestro — regla 5): los primeros pockets
    con ARCOS en la trayectoria almacenada, byte-idénticos.

    - Isla rectangular: DOS trayectorias (anillo exterior + corona con esquinas
      redondeadas); derivó la transición entre trayectorias (= pasada de misma fresa,
      N028) y el REAJUSTE del centro del arco a los endpoints redondeados
      (`_pocket_arc_center`, el ruido I225.001 con centro almacenado exacto).
    - Rebaba negativa −75 (offset efectivo −35): anillos FUERA del contorno con esquinas
      redondeadas; trajo además el primer Xn AL INICIO del programa (park en el preamble
      SIN M5 entre el 2º y 3er par ETK[8]/G40; footer sin M5/park) y el cero negativo
      (−0.0 almacenado → `0.000` emitido).
    - El vaciado circular con isla circular sigue SIN adaptar (contorno GeomCircle):
      fail-loud correcto hasta extender el adapter."""

    _FIXTURES = Path(r"S:\Maestro\Projects\ProdAction\Programas Manuales")
    _REFS = Path(r"P:\USBMIX\ProdAction\Programas Manuales")

    STEMS = ("N_V_e001_d9_Isla_manual", "N_V_e001_d9_Vaciado_Rebaba_negativa_manual")

    def test_byte_identico(self):
        for stem in self.STEMS:
            with self.subTest(stem):
                _e2e_check(self, self._FIXTURES / f"{stem}.pgmx",
                           self._REFS / f"{stem.lower()}.iso")

    def test_circular_sigue_fail_loud(self):
        pgmx = self._FIXTURES / "N_V_e001_d9_Vaciado_Circular_Isla_Circular_manual.pgmx"
        if not pgmx.exists():
            self.skipTest("fixtures S: no disponibles")
        with self.assertRaises(UnsupportedOperationError):
            convert(pgmx)


if __name__ == "__main__":
    unittest.main()
