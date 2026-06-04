from __future__ import annotations

import unittest

from pgmx import synthesis as pgmx_synthesis
from pgmx.synthesis import common as synthesis_common
from pgmx.synthesis import core as core_sp
from pgmx.synthesis import drilling as synthesis_drilling
from pgmx.synthesis import milling as synthesis_milling
from pgmx.synthesis.common import depth as common_depth
from pgmx.synthesis.common import piece as common_piece
from pgmx.synthesis.common import xml as common_xml
from tools import synthesize_pgmx as legacy_sp
from tools import pgmx_synthesis as legacy_pgmx_synthesis


class PgmxSynthesisPackageTests(unittest.TestCase):
    def test_public_facade_reexports_core_api_and_keeps_data_paths(self) -> None:
        self.assertIs(pgmx_synthesis.PocketMillingSpec, core_sp.PocketMillingSpec)
        self.assertIs(pgmx_synthesis.build_pocket_milling_spec, core_sp.build_pocket_milling_spec)
        self.assertIs(legacy_sp.PocketMillingSpec, core_sp.PocketMillingSpec)
        self.assertIs(legacy_pgmx_synthesis.PocketMillingSpec, core_sp.PocketMillingSpec)
        self.assertTrue(pgmx_synthesis.DEFAULT_BASELINE_XML_PATH.name.endswith("Pieza.xml"))
        self.assertEqual(pgmx_synthesis.DEFAULT_BASELINE_DIR.name, "maestro_baselines")
        self.assertEqual(pgmx_synthesis.DEFAULT_BASELINE_DIR.parent.name, "data")
        self.assertEqual(pgmx_synthesis.TOOL_CATALOG_PATH.name, "tool_catalog.csv")
        self.assertEqual(pgmx_synthesis.TOOL_CATALOG_PATH.parent.name, "data")

    def test_vaciado_boundary_adapts_public_pocket_spec_to_v2_contract(self) -> None:
        status = pgmx_synthesis.vaciado_support_status()
        self.assertTrue(status.enabled)
        self.assertEqual(status.model_package, "pgmx.vaciado")
        self.assertFalse(status.legacy_engine_allowed)

        pocket = pgmx_synthesis.build_pocket_milling_spec(
            contour_points=((0, 0), (400, 0), (400, 300), (0, 300), (0, 0)),
            tool_width=80.0,
            target_depth=10.0,
        )

        geometry, strategy, depth = pgmx_synthesis.adapt_pocket_milling_to_vaciado_contract(pocket)

        self.assertEqual(geometry.outer.bbox.width, 400.0)
        self.assertEqual(geometry.outer.bbox.height, 300.0)
        self.assertEqual(strategy.tool_width, 80.0)
        self.assertEqual(depth.target_depth, 10.0)

    def test_modular_synthesis_packages_import_and_core_uses_common_xml(self) -> None:
        self.assertIsNotNone(synthesis_common)
        self.assertIsNotNone(synthesis_milling)
        self.assertIsNotNone(synthesis_drilling)
        self.assertEqual(common_xml.PGMX_NS, core_sp.PGMX_NS)
        self.assertIs(core_sp._append_node, common_xml._append_node)
        self.assertEqual(common_xml._compact_number(1.25), "1.25")
        self.assertIs(core_sp.MillingDepthSpec, common_depth.MillingDepthSpec)
        self.assertIs(common_depth.DepthSpec, common_depth.MillingDepthSpec)
        self.assertIs(core_sp.build_milling_depth_spec, common_depth.build_milling_depth_spec)
        self.assertIs(core_sp._normalize_plane_name, common_piece._normalize_plane_name)
        self.assertEqual(common_piece._normalize_plane_name("cara-derecha"), "Right")
        piece = common_piece.PieceGeometry(length=500.0, width=300.0, depth=18.0)
        drill = core_sp.build_drilling_spec(
            center_x=40.0,
            center_y=9.0,
            diameter=5.0,
            plane_name="Left",
        )
        self.assertEqual(common_piece._plane_local_dimensions(piece, "Left"), (300.0, 18.0))
        self.assertEqual(common_piece._drilling_axis_span(piece, "Left"), 500.0)
        self.assertEqual(
            common_piece._drilling_entry_point_and_direction(piece, drill),
            ((0.0, 260.0, 9.0), (1.0, 0.0, 0.0)),
        )


if __name__ == "__main__":
    unittest.main()
