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
from iso.synthesis.compare import classify_iso_diff
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


class IsoCompareTest(unittest.TestCase):
    """El clasificador byte/funcional/diferente (dato de dominio de Fermín 2026-07-31:
    Maestro mete ruido de MILÉSIMAS por coma flotante; la máquina tiene precisión de
    0.1 mm — la clasificación identifica ese ruido en vez de esconderlo)."""

    REF = "G1 X100.000 Y50.000 F5000.000\nG2 X10.000 Y20.000 I150.000 J150.001 F5000.000"

    def test_byte_identico(self):
        self.assertEqual(classify_iso_diff(self.REF, self.REF).verdict, "byte_identico")
        # espacios finales no cuentan (la convención de todos los e2e)
        con_espacios = self.REF.replace("\n", " \n") + " "
        self.assertEqual(classify_iso_diff(con_espacios, self.REF).verdict, "byte_identico")

    def test_funcionalmente_identico_por_milesimas(self):
        gen = self.REF.replace("J150.001", "J150.000").replace("Y50.000", "Y50.002")
        c = classify_iso_diff(gen, self.REF)
        self.assertEqual(c.verdict, "funcionalmente_identico", c.report())
        self.assertEqual(len(c.numeric_diffs), 2)
        self.assertAlmostEqual(c.max_delta, 0.002, places=6)

    def test_delta_grande_es_diferente(self):
        gen = self.REF.replace("X100.000", "X100.100")   # una décima: ya no es ruido
        self.assertEqual(classify_iso_diff(gen, self.REF).verdict, "diferente")

    def test_estructura_distinta_es_diferente(self):
        gen = self.REF.replace("G2", "G3")               # mismo largo, otro esqueleto
        c = classify_iso_diff(gen, self.REF)
        self.assertEqual(c.verdict, "diferente")
        self.assertTrue(c.structural_issues)
        gen2 = self.REF + "\nG0 Z30.000"                 # línea de más
        self.assertEqual(classify_iso_diff(gen2, self.REF).verdict, "diferente")

    def test_omision_deliberada_no_cuenta_como_diferencia(self):
        # `%DONTCARESPEEDV=1`: Maestro la emite mal formada y el CNC aborta con Alarma 67;
        # el converter la omite a propósito. El comparador la DESCUENTA y la reporta.
        ref = self.REF.replace("\n", "\n%DONTCARESPEEDV=1\n", 1)
        c = classify_iso_diff(self.REF, ref)
        self.assertEqual(c.verdict, "funcionalmente_identico", c.report())
        self.assertEqual(c.deliberate_omissions, ("%DONTCARESPEEDV=1",))
        self.assertEqual(c.numeric_diffs, ())
        self.assertIn("omitida: %DONTCARESPEEDV=1", c.report())

    def test_omision_deliberada_no_tapa_otras_diferencias(self):
        # Si además hay una diferencia REAL, sigue siendo "diferente": la omisión se
        # descuenta, no perdona nada más.
        ref = (self.REF.replace("\n", "\n%DONTCARESPEEDV=1\n", 1)
               .replace("X100.000", "X100.100"))
        c = classify_iso_diff(self.REF, ref)
        self.assertEqual(c.verdict, "diferente")
        self.assertEqual(c.deliberate_omissions, ("%DONTCARESPEEDV=1",))

    def test_cero_negativo_no_es_delta(self):
        gen = self.REF.replace("Y50.000", "Y-0.000")
        ref = self.REF.replace("Y50.000", "Y0.000")
        c = classify_iso_diff(gen, ref)
        self.assertEqual(c.verdict, "funcionalmente_identico")
        self.assertEqual(c.max_delta, 0.0)


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

    def test_experimento01_esquinas_redondas_byte_identico(self):
        # Vaciado de contorno con ESQUINAS REDONDEADAS + leads lineales En bajada/En
        # subida (rampa XY+Z que reemplaza plunge y retracción verticales).
        base_s = self._FIXTURES / "Experimento-01"
        base_p = self._REFS / "Experimento-01"
        _e2e_check(self, base_s / "vaciado_interior_esquinas_redondas.pgmx",
                   base_p / "vaciado_interior_esquinas_redondas.iso")

    def test_circular_funcionalmente_identico(self):
        # ANILLO circular (contorno círculo + isla círculo concéntrica): el adapter lo
        # representa como contour_circle/boss_circles y el render copia sus trayectorias.
        # Cierra FUNCIONALMENTE idéntico: 143/144 líneas byte + UN delta de 0.001 en un J
        # cuyo centro emitido NO es equidistante de los endpoints redondeados — ruido de
        # coma flotante del emisor de Maestro (Fermín 2026-07-31: Maestro suma/resta
        # milésimas sin razón aparente; precisión de máquina 0.1 mm). El comparador
        # IDENTIFICA la diferencia en vez de esconderla (regla 4).
        pgmx = self._FIXTURES / "N_V_e001_d9_Vaciado_Circular_Isla_Circular_manual.pgmx"
        ref = self._REFS / "n_v_e001_d9_vaciado_circular_isla_circular_manual.iso"
        if not pgmx.exists() or not ref.exists():
            self.skipTest("fixtures S:/P: no disponibles")
        from pgmx.adapters import adapt_pgmx_path
        result = adapt_pgmx_path(pgmx)
        self.assertFalse(result.unsupported_entries)
        (entry,) = result.adapted_entries
        self.assertEqual(entry.spec.contour_circle, (150.0, 150.0, 150.0))
        self.assertEqual(entry.spec.boss_circles, ((150.0, 150.0, 75.0),))
        self.assertEqual(entry.spec.contour_points, ())
        self.assertEqual(len(entry.spec.stored_trajectories), 2)

        comparison = classify_iso_diff(convert(pgmx), ref.read_text(encoding="cp1252"))
        self.assertEqual(comparison.verdict, "funcionalmente_identico",
                         comparison.report())
        self.assertEqual(len(comparison.numeric_diffs), 1)     # SOLO la milésima conocida
        self.assertAlmostEqual(comparison.max_delta, 0.001, places=6)
        self.assertIn("J150.001", comparison.numeric_diffs[0].line_reference)

    def test_experimento01_esquinas_redondas_representacion(self):
        # Experimento-01 (2026-08-03): DOBLE frente en un fixture — contorno de rectángulo
        # con esquinas REDONDEADAS (5 rectas + 4 arcos r=25, arranque a mitad de borde) +
        # LEADS Line En bajada/En subida. Acá se fija la REPRESENTACIÓN (contorno con
        # arcos sin aplanar a puntos); el byte-idéntico lo cubre
        # `test_experimento01_esquinas_redondas_byte_identico`.
        pgmx = (Path(r"S:\Maestro\Projects\ProdAction\Programas Manuales\Experimento-01")
                / "vaciado_interior_esquinas_redondas.pgmx")
        if not pgmx.exists():
            self.skipTest("fixtures S: no disponibles")
        from pgmx.adapters import adapt_pgmx_path
        result = adapt_pgmx_path(pgmx)
        self.assertFalse(result.unsupported_entries)
        (entry,) = result.adapted_entries
        kinds = [p.primitive_type for p in entry.spec.contour_primitives]
        self.assertEqual(kinds.count("Line"), 5)
        self.assertEqual(kinds.count("Arc"), 4)
        self.assertEqual(entry.spec.contour_points, ())
        self.assertTrue(entry.spec.approach.is_enabled)
        self.assertTrue(entry.spec.retract.is_enabled)
        self.assertEqual(entry.spec.approach.approach_type, "Line")
        self.assertEqual(entry.spec.approach.mode, "Down")
        self.assertEqual(entry.spec.retract.mode, "Up")

    def test_autoria_circular_fail_loud(self):
        # La síntesis productiva de un pocket circular no existe: solo lectura (regla 5).
        import pgmx.synthesis as sp
        spec = sp.build_pocket_spec(
            contour_points=(), contour_circle=(150.0, 150.0, 150.0),
            boss_circles=((150.0, 150.0, 75.0),),
            tool_id="1900", tool_name="E001", tool_width=18.36, target_depth=9.0)
        with self.assertRaises(NotImplementedError):
            sp.synthesize_request(sp.build_synthesis_request(
                output_path=Path(r"C:\Users\fermi\AppData\Local\Temp\claude"
                                 r"\_n050_circular_no_debe_escribirse.pgmx"),
                piece_name="no", length=300.0, width=300.0, depth=18.0,
                origin_x=0.0, origin_y=0.0, origin_z=0.0, pockets=[spec]))


if __name__ == "__main__":
    unittest.main()
