"""Regresión del fail-loud del converter PGMX→ISO (Eje 0) + fidelidad del adapter.

Verifica que:
  - operaciones/parámetros fuera del subconjunto soportado abortan con
    UnsupportedOperationError (en vez de crashear o emitir ISO incompleto);
  - el adapter de lectura recupera los campos que antes perdía
    (feedrate, spindle, step_number/step_depth), condición necesaria para que
    el fail-loud pueda verlos.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.adapters import adapt_pgmx_path
from pgmx.synthesis import (
    build_drilling_spec,
    build_slot_milling_spec,
    build_synthesis_request,
    synthesize_request,
)
from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError


def _make(tmp: Path, name: str, **kwargs) -> Path:
    path = tmp / f"{name}.pgmx"
    req = build_synthesis_request(
        output_path=path, piece_name=name,
        length=300, width=200, depth=18, origin_x=5, origin_y=5, origin_z=25,
        **kwargs,
    )
    synthesize_request(req)
    return path


def _drill(**kw):
    base = dict(center_x=150.0, center_y=100.0, diameter=8.0, plane_name="Top")
    base.update(kw)
    return build_drilling_spec(**base)


class FailLoudTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _assert_rejected(self, name, **kwargs):
        path = _make(self.tmp, name, **kwargs)
        with self.assertRaises(UnsupportedOperationError):
            convert(path)

    def test_unsupported_spec_type(self):
        self._assert_rejected("slot", slot_millings=[build_slot_milling_spec(
            start_x=20, start_y=100, end_x=280, end_y=100,
            feature_name="Canal", target_depth=8.0)])

    def test_unsupported_top_diameter(self):
        # El toolset solo auto-resuelve las montadas (= TOP_TOOL), así que un Ø
        # fuera de tabla no se puede sintetizar; ejercemos la rama del validador
        # directamente con un spec de Ø10 (no montado).
        import dataclasses
        from iso.synthesis._validation import validate_entries
        spec = dataclasses.replace(_drill(diameter=8.0, target_depth=10.0), diameter=10.0)
        with self.assertRaises(UnsupportedOperationError):
            validate_entries([spec])

    def test_side_through_drill_rejected(self):
        self._assert_rejected("side_through", drillings=[_drill(
            plane_name="Front", center_y=0.0, is_through=True)])

    def test_top_through_drill_passes(self):
        # Top-pasante soportado desde N005: z_cut = cara inferior (tlc).
        path = _make(self.tmp, "top_through", drillings=[_drill(is_through=True)])
        iso = convert(path)
        self.assertIn("G1 G9 Z77.000", iso)

    def test_conical_d5_through_passes(self):
        # D5 + pasante → tool 007 (cónica) auto-seleccionada (N007).
        path = _make(self.tmp, "conic", drillings=[_drill(
            diameter=5.0, is_through=True)])
        iso = convert(path)
        self.assertIn("?%ETK[6]=7", iso)   # tool 007
        self.assertIn("?%ETK[0]=64", iso)

    def test_flat_d5_through_passes(self):
        # D5 pasante forzado a punta plana → tool 005 (no la cónica).
        path = _make(self.tmp, "flatd5", drillings=[_drill(
            diameter=5.0, is_through=True, drill_family="Flat")])
        iso = convert(path)
        self.assertIn("?%ETK[6]=5", iso)   # tool 005

    def test_side_multistep_ignored_single_cut(self):
        # El husillo lateral no hace peck → un solo corte (N011), no se rechaza.
        path = _make(self.tmp, "side_peck", drillings=[_drill(
            plane_name="Front", center_y=9.0, target_depth=28.0, step_number=3)])
        iso = convert(path)
        self.assertEqual(iso.count("G1 G9 Y"), 1)

    def test_top_multistep_by_number_passes(self):
        path = _make(self.tmp, "peck_n", drillings=[_drill(target_depth=14.0, step_number=3)])
        iso = convert(path)
        self.assertEqual(iso.count("G1 G9 Z"), 3)  # 3 pasadas

    def test_top_multistep_by_depth_passes(self):
        path = _make(self.tmp, "peck_d", drillings=[_drill(target_depth=14.0, step_depth=5.0)])
        iso = convert(path)
        self.assertEqual(iso.count("G1 G9 Z"), 3)  # ceil(14/5)=3 pasadas

    def test_side_feed_applied_spindle_ignored(self):
        # Lateral (N011): feed = feedrate×1000 clampado; husillo lateral fijo 6000
        # (override de spindle ignorado).
        path = _make(self.tmp, "side_fs", drillings=[_drill(
            plane_name="Front", center_y=9.0, target_depth=28.0,
            feedrate=1.5, spindle=4500.0)])
        iso = convert(path)
        self.assertIn("G1 G9 Y-37.000 F1500.000", iso)
        self.assertIn("S6000M3", iso)
        self.assertNotIn("S4500M3", iso)

    def test_supported_drill_passes(self):
        path = _make(self.tmp, "ok", drillings=[_drill(target_depth=10.0)])
        iso = convert(path)  # no debe levantar
        self.assertIn("G1 G9 Z", iso)


class AdapterFidelityTest(unittest.TestCase):
    """El adapter de lectura debe recuperar los campos que antes perdía."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _read_drill(self, **kw):
        path = _make(self.tmp, "rt", drillings=[_drill(**kw)])
        specs = [e.spec for e in adapt_pgmx_path(path).adapted_entries]
        return specs[0]

    def test_feedrate_spindle_roundtrip(self):
        d = self._read_drill(target_depth=10.0, feedrate=1234.0, spindle=5678.0)
        self.assertEqual(d.feedrate, 1234.0)
        self.assertEqual(d.spindle, 5678.0)

    def test_step_number_roundtrip(self):
        d = self._read_drill(target_depth=14.0, step_number=3)
        self.assertEqual(d.step_number, 3)

    def test_step_depth_roundtrip(self):
        d = self._read_drill(target_depth=14.0, step_depth=4.0)
        self.assertEqual(d.step_depth, 4.0)

    def test_normal_drill_has_no_overrides(self):
        d = self._read_drill(target_depth=10.0)
        self.assertEqual((d.feedrate, d.spindle, d.step_number, d.step_depth), (0.0, 0.0, 0, 0.0))


if __name__ == "__main__":
    unittest.main()
