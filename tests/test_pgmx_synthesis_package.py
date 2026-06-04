from __future__ import annotations

import unittest

from pgmx import synthesis as pgmx_synthesis
from pgmx.synthesis import common as synthesis_common
from pgmx.synthesis import core as core_sp
from pgmx.synthesis import drilling as synthesis_drilling
from pgmx.synthesis import milling as synthesis_milling
from pgmx.synthesis.common import depth as common_depth
from pgmx.synthesis.common import hydration as common_hydration
from pgmx.synthesis.common import leads as common_leads
from pgmx.synthesis.common import piece as common_piece
from pgmx.synthesis.common import strategy as common_strategy
from pgmx.synthesis.common import tools as common_tools
from pgmx.synthesis.common import xml as common_xml
from pgmx.synthesis.milling import line as milling_line
from pgmx.synthesis.milling import profile as milling_profile
from pgmx.synthesis.milling import slot as milling_slot
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
        self.assertIs(core_sp.TOOL_CATALOG_PATH, common_tools.TOOL_CATALOG_PATH)
        self.assertIs(core_sp._load_tool_catalog, common_tools._load_tool_catalog)
        self.assertEqual(common_tools._normalize_tool_resolution("manual"), "Explicit")
        self.assertEqual(common_tools._normalize_tool_usage_group("Broca D5"), "drilling")
        self.assertEqual(common_tools._normalize_tool_usage_group("Fresa Helicoidal"), "milling")
        self.assertTrue(common_tools._is_vertical_x_saw("Sierra Vertical X"))
        self.assertIn("1900", common_tools._load_tool_catalog())
        self.assertIs(core_sp.UnidirectionalMillingStrategySpec, common_strategy.UnidirectionalMillingStrategySpec)
        self.assertIs(core_sp.BidirectionalMillingStrategySpec, common_strategy.BidirectionalMillingStrategySpec)
        self.assertIs(core_sp.HelicalMillingStrategySpec, common_strategy.HelicalMillingStrategySpec)
        self.assertIs(core_sp.ContourParallelMillingStrategySpec, common_strategy.ContourParallelMillingStrategySpec)
        self.assertIs(
            core_sp.build_contour_parallel_milling_strategy_spec,
            common_strategy.build_contour_parallel_milling_strategy_spec,
        )
        self.assertEqual(common_strategy._normalize_strategy_connection_mode("en-la-pieza"), "InPiece")
        strategy = common_strategy.build_bidirectional_milling_strategy_spec(axial_cutting_depth=2.5)
        self.assertTrue(strategy.allow_multiple_passes)
        self.assertEqual(strategy.axial_cutting_depth, 2.5)
        self.assertIs(core_sp._load_pgmx_container, common_hydration._load_pgmx_container)
        self.assertIs(core_sp.load_pgmx_template_document, common_hydration.load_pgmx_template_document)
        template = common_hydration.load_pgmx_template_document(core_sp.DEFAULT_BASELINE_XML_PATH)
        self.assertIsInstance(template, common_hydration.PgmxTemplateDocument)
        self.assertEqual(template.xml_entry_name, "Pieza.xml")
        self.assertIn("Pieza.xml", template.archive_entries)
        root, entries, xml_entry_name = core_sp._load_pgmx_container(core_sp.DEFAULT_BASELINE_XML_PATH)
        self.assertEqual(root.tag, template.root.tag)
        self.assertEqual(xml_entry_name, template.xml_entry_name)
        self.assertEqual(entries.keys(), template.archive_entries.keys())
        self.assertIs(core_sp.ApproachSpec, common_leads.ApproachSpec)
        self.assertIs(core_sp.RetractSpec, common_leads.RetractSpec)
        self.assertIs(core_sp.build_approach_spec, common_leads.build_approach_spec)
        self.assertIs(core_sp.build_retract_spec, common_leads.build_retract_spec)
        self.assertIs(core_sp._normalize_retract_mode, common_leads._normalize_retract_mode)
        self.assertEqual(common_leads._normalize_approach_arc_side("izquierda"), "Left")
        self.assertEqual(common_leads._normalize_retract_mode("en-cota"), "Quote")
        self.assertFalse(common_leads.build_approach_spec().is_enabled)
        approach = common_leads.build_approach_spec(approach_type="arc")
        self.assertTrue(approach.is_enabled)
        self.assertEqual(approach.approach_type, "Arc")
        self.assertEqual(approach.mode, "Quote")
        retract = common_leads.build_retract_spec(retract_type="arco", overlap=0.25)
        self.assertTrue(retract.is_enabled)
        self.assertEqual(retract.retract_type, "Arc")
        self.assertEqual(retract.overlap, 0.25)
        self.assertIs(core_sp.LineMillingSpec, milling_line.LineMillingSpec)
        self.assertIs(core_sp.build_line_milling_spec, milling_line.build_line_milling_spec)
        self.assertIs(core_sp._normalize_line_milling_spec, milling_line._normalize_line_milling_spec)
        line = milling_line.build_line_milling_spec(
            0,
            0,
            100,
            0,
            None,
            None,
            None,
            None,
            None,
            line_side_of_feature="derecha",
            line_milling_strategy=common_strategy.build_unidirectional_milling_strategy_spec(),
        )
        self.assertIsInstance(line, milling_line.LineMillingSpec)
        self.assertEqual(line.side_of_feature, "Right")
        self.assertEqual(line.tool_width, 9.52)
        normalized_line = milling_line._normalize_line_milling_spec(
            milling_line.LineMillingSpec(0, 0, 100, 0, side_of_feature="izquierda")
        )
        self.assertEqual(normalized_line.side_of_feature, "Left")
        self.assertIs(core_sp.SlotMillingSpec, milling_slot.SlotMillingSpec)
        self.assertIs(core_sp.build_slot_milling_spec, milling_slot.build_slot_milling_spec)
        self.assertIs(core_sp._normalize_slot_milling_spec, milling_slot._normalize_slot_milling_spec)
        slot = milling_slot.build_slot_milling_spec(
            start_x=0,
            start_y=0,
            end_x=120,
            end_y=0,
            side_of_feature="derecha",
        )
        self.assertIsInstance(slot, milling_slot.SlotMillingSpec)
        self.assertEqual(slot.feature_name, "Canal")
        self.assertEqual(slot.side_of_feature, "Right")
        self.assertEqual(slot.tool_id, "1899")
        self.assertEqual(slot.depth_spec.target_depth, 10.0)
        self.assertIsNone(slot.milling_strategy)
        with self.assertRaisesRegex(ValueError, "longitud cero"):
            milling_slot.build_slot_milling_spec(start_x=0, start_y=0, end_x=0, end_y=0)
        self.assertIs(core_sp.PolylineMillingSpec, milling_profile.PolylineMillingSpec)
        self.assertIs(core_sp.build_polyline_milling_spec, milling_profile.build_polyline_milling_spec)
        self.assertIs(core_sp._normalize_polyline_milling_spec, milling_profile._normalize_polyline_milling_spec)
        polyline = milling_profile.build_polyline_milling_spec(
            ((0, 0), (100, 0), (100, 50), (0, 0)),
            side_of_feature="izquierda",
        )
        self.assertIsInstance(polyline, milling_profile.PolylineMillingSpec)
        self.assertEqual(polyline.side_of_feature, "Left")
        self.assertTrue(milling_profile._is_closed_polyline_points(polyline.points))
        with self.assertRaisesRegex(ValueError, "Maestro no postprocesa"):
            milling_profile.build_polyline_milling_spec(
                ((0, 0), (100, 0), (100, 50)),
                milling_strategy=common_strategy.build_unidirectional_milling_strategy_spec(
                    allow_multiple_passes=True,
                    axial_cutting_depth=5.0,
                ),
                retract_enabled=True,
                retract_type="Arc",
                retract_mode="Up",
            )


if __name__ == "__main__":
    unittest.main()
