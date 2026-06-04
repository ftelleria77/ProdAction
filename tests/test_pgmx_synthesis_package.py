from __future__ import annotations

import unittest

from pgmx import synthesis as pgmx_synthesis
from pgmx.synthesis import common as synthesis_common
from pgmx.synthesis import core as core_sp
from pgmx.synthesis import drilling as synthesis_drilling
from pgmx.synthesis import milling as synthesis_milling
from pgmx.synthesis.common import depth as common_depth
from pgmx.synthesis.common import geometry as common_geometry
from pgmx.synthesis.common import hydration as common_hydration
from pgmx.synthesis.common import leads as common_leads
from pgmx.synthesis.common import piece as common_piece
from pgmx.synthesis.common import program as common_program
from pgmx.synthesis.common import strategy as common_strategy
from pgmx.synthesis.common import tools as common_tools
from pgmx.synthesis.common import xml as common_xml
from pgmx.synthesis.drilling import pattern as drilling_pattern
from pgmx.synthesis.drilling import single as drilling_single
from pgmx.synthesis.milling import _common as milling_common
from pgmx.synthesis.milling import circle as milling_circle
from pgmx.synthesis.milling import line as milling_line
from pgmx.synthesis.milling import pocket as milling_pocket
from pgmx.synthesis.milling import profile as milling_profile
from pgmx.synthesis.milling import slot as milling_slot
from pgmx.synthesis.milling import squaring as milling_squaring
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
        self.assertIs(core_sp._safe_float, common_xml._safe_float)
        self.assertIs(core_sp._safe_bool, common_xml._safe_bool)
        self.assertEqual(common_xml._safe_float("1,25", 0.0), 1.25)
        self.assertTrue(common_xml._safe_bool("si", False))
        self.assertIs(core_sp.PgmxState, common_program.PgmxState)
        self.assertIs(core_sp.MachiningSpec, common_program.MachiningSpec)
        self.assertIs(core_sp.XnSpec, common_program.XnSpec)
        self.assertIs(core_sp.PgmxSynthesisRequest, common_program.PgmxSynthesisRequest)
        self.assertIs(core_sp.PgmxSynthesisResult, common_program.PgmxSynthesisResult)
        self.assertEqual(
            common_program.DEFAULT_MACHINING_ORDER,
            ("line", "slot", "polyline", "circle", "squaring", "pocket", "drilling", "drilling_pattern"),
        )
        self.assertIs(core_sp.GeometryPrimitiveSpec, common_geometry.GeometryPrimitiveSpec)
        self.assertIs(core_sp.GeometryProfileSpec, common_geometry.GeometryProfileSpec)
        self.assertIs(core_sp.build_line_geometry_primitive, common_geometry.build_line_geometry_primitive)
        self.assertIs(core_sp.build_arc_geometry_primitive, common_geometry.build_arc_geometry_primitive)
        self.assertIs(core_sp.build_point_geometry_profile, common_geometry.build_point_geometry_profile)
        self.assertIs(core_sp.build_line_geometry_profile, common_geometry.build_line_geometry_profile)
        self.assertIs(core_sp.build_circle_geometry_profile, common_geometry.build_circle_geometry_profile)
        self.assertIs(core_sp.build_composite_geometry_profile, common_geometry.build_composite_geometry_profile)
        self.assertIs(core_sp._CurveSpec, common_geometry._CurveSpec)
        self.assertIs(core_sp._trimmed_curve_spec, common_geometry._trimmed_curve_spec)
        self.assertIs(core_sp._circle_curve_spec, common_geometry._circle_curve_spec)
        self.assertIs(core_sp._composite_curve_spec, common_geometry._composite_curve_spec)
        self.assertIs(core_sp._curve_spec_from_profile_geometry, common_geometry._curve_spec_from_profile_geometry)
        self.assertIs(core_sp._curve_spec_from_composite_curve_node, common_geometry._curve_spec_from_composite_curve_node)
        self.assertIs(core_sp._curve_spec_from_toolpath_node, common_geometry._curve_spec_from_toolpath_node)
        self.assertIs(core_sp._parse_geometry_primitive, common_geometry._parse_geometry_primitive)
        self.assertIs(core_sp._parse_line_serialization, common_geometry._parse_line_serialization)
        self.assertIs(core_sp._curve_spec_points, common_geometry._curve_spec_points)
        self.assertIs(core_sp._parse_circle_geometry_profile, common_geometry._parse_circle_geometry_profile)
        self.assertIs(core_sp._extract_geometry_profile, common_geometry._extract_geometry_profile)
        self.assertIs(core_sp.read_pgmx_geometries, common_geometry.read_pgmx_geometries)
        self.assertIs(core_sp.build_compensated_toolpath_profile, common_geometry.build_compensated_toolpath_profile)
        self.assertIs(core_sp._build_compensated_profile_geometry, common_geometry._build_compensated_profile_geometry)
        self.assertIs(core_sp._normalize_side_of_feature, common_geometry._normalize_side_of_feature)
        self.assertIs(core_sp._line_primitive_at_plane, common_geometry._line_primitive_at_plane)
        self.assertIs(core_sp._primitive_winding, common_geometry._primitive_winding)
        self.assertIs(core_sp._line_unit_direction, common_geometry._line_unit_direction)
        self.assertIs(core_sp._resolve_toolpath_direction, common_geometry._resolve_toolpath_direction)
        self.assertIs(core_sp._profile_endpoint_points, common_geometry._profile_endpoint_points)
        self.assertIs(core_sp._profile_entry_exit_context, common_geometry._profile_entry_exit_context)
        self.assertIs(core_sp._profile_endpoint_points_3d, common_geometry._profile_endpoint_points_3d)
        self.assertIs(core_sp._profile_at_z, common_geometry._profile_at_z)
        self.assertIs(core_sp._reverse_profile_geometry, common_geometry._reverse_profile_geometry)
        self.assertIs(core_sp._vertical_transition_primitive, common_geometry._vertical_transition_primitive)
        self.assertIs(core_sp._normalize_polyline_points, common_geometry._normalize_polyline_points)
        self.assertIs(core_sp._is_closed_polyline_points, common_geometry._is_closed_polyline_points)
        self.assertIs(core_sp._build_line_description, common_geometry._build_line_description)
        self.assertIs(core_sp._build_open_polyline_descriptions, common_geometry._build_open_polyline_descriptions)
        self.assertIs(core_sp._build_open_polyline_geometry_profile, common_geometry._build_open_polyline_geometry_profile)
        self.assertIs(
            core_sp._build_closed_polyline_geometry_profile,
            common_geometry._build_closed_polyline_geometry_profile,
        )
        compensated_line = common_geometry.build_compensated_toolpath_profile(
            common_geometry.build_line_geometry_profile(0.0, 0.0, 100.0, 0.0),
            side_of_feature="derecha",
            tool_width=20.0,
        )
        self.assertEqual(compensated_line.primitives[0].start_point[:2], (0.0, -10.0))
        self.assertEqual(compensated_line.primitives[0].end_point[:2], (100.0, -10.0))
        compensated_corner = common_geometry.build_compensated_toolpath_profile(
            common_geometry.build_composite_geometry_profile(
                (
                    common_geometry.build_line_geometry_primitive(0.0, 0.0, 100.0, 0.0),
                    common_geometry.build_line_geometry_primitive(100.0, 0.0, 100.0, 100.0),
                )
            ),
            side_of_feature="izquierda",
            tool_width=20.0,
        )
        self.assertEqual(compensated_corner.primitives[0].end_point[:2], (90.0, 10.0))
        self.assertEqual(compensated_corner.primitives[1].start_point[:2], (90.0, 10.0))
        lowered_corner = common_geometry._profile_at_z(compensated_corner, -5.0)
        self.assertEqual(lowered_corner.primitives[0].start_point[2], -5.0)
        reversed_corner = common_geometry._reverse_profile_geometry(lowered_corner)
        self.assertEqual(reversed_corner.primitives[0].start_point, lowered_corner.primitives[-1].end_point)
        primitive = common_geometry.GeometryPrimitiveSpec("Point", (1.0, 2.0, 0.0), (1.0, 2.0, 0.0))
        profile = common_geometry.GeometryProfileSpec("GeomCartesianPoint", "Point", primitives=(primitive,))
        self.assertEqual(profile.primitive_count, 1)
        self.assertEqual(profile.classification_key, "Point")
        self.assertIs(core_sp.MillingDepthSpec, common_depth.MillingDepthSpec)
        self.assertIs(common_depth.DepthSpec, common_depth.MillingDepthSpec)
        self.assertIs(core_sp.build_milling_depth_spec, common_depth.build_milling_depth_spec)
        self.assertIs(core_sp._extract_depth_spec_from_template, common_depth._extract_depth_spec_from_template)
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
        self.assertIs(core_sp.DrillingSpec, drilling_single.DrillingSpec)
        self.assertIs(core_sp.build_drilling_spec, drilling_single.build_drilling_spec)
        self.assertIs(core_sp._normalize_drilling_spec, drilling_single._normalize_drilling_spec)
        top_drill = drilling_single.build_drilling_spec(center_x=40, center_y=60, diameter=5.0)
        self.assertIsInstance(top_drill, drilling_single.DrillingSpec)
        self.assertEqual(top_drill.drill_family, "Conical")
        self.assertEqual(top_drill.tool_id, "0")
        side_drill = drilling_single._normalize_drilling_spec(
            drilling_single.DrillingSpec(
                center_x=40,
                center_y=9,
                diameter=8,
                plane_name="cara-derecha",
                drill_family="plana",
                tool_resolution="manual",
                tool_id=" 123 ",
            )
        )
        self.assertEqual(side_drill.plane_name, "Right")
        self.assertEqual(side_drill.drill_family, "Flat")
        self.assertEqual(side_drill.tool_resolution, "Explicit")
        self.assertEqual(side_drill.tool_id, "123")
        with self.assertRaisesRegex(ValueError, "D5"):
            drilling_single._normalize_drilling_spec(
                drilling_single.DrillingSpec(center_x=0, center_y=0, diameter=8, drill_family="lanza")
            )
        self.assertIs(core_sp.DrillingPatternSpec, drilling_pattern.DrillingPatternSpec)
        self.assertIs(core_sp.build_drilling_pattern_spec, drilling_pattern.build_drilling_pattern_spec)
        self.assertIs(core_sp._normalize_drilling_pattern_spec, drilling_pattern._normalize_drilling_pattern_spec)
        drill_pattern = drilling_pattern.build_drilling_pattern_spec(
            20,
            30,
            5.0,
            2,
            3,
            32.0,
            row_spacing=45.0,
        )
        self.assertIsInstance(drill_pattern, drilling_pattern.DrillingPatternSpec)
        self.assertEqual(drill_pattern.drill_family, "Conical")
        self.assertEqual(drill_pattern.columns, 2)
        self.assertEqual(drill_pattern.rows, 3)
        self.assertEqual(drill_pattern.row_spacing, 45.0)
        self.assertEqual(drill_pattern.tool_id, "0")
        with self.assertRaisesRegex(ValueError, "unico taladro"):
            drilling_pattern.build_drilling_pattern_spec(0, 0, 5, 1, 1, 0)
        self.assertIs(core_sp.UnidirectionalMillingStrategySpec, common_strategy.UnidirectionalMillingStrategySpec)
        self.assertIs(core_sp.BidirectionalMillingStrategySpec, common_strategy.BidirectionalMillingStrategySpec)
        self.assertIs(core_sp.HelicalMillingStrategySpec, common_strategy.HelicalMillingStrategySpec)
        self.assertIs(core_sp.ContourParallelMillingStrategySpec, common_strategy.ContourParallelMillingStrategySpec)
        self.assertIs(
            core_sp.build_contour_parallel_milling_strategy_spec,
            common_strategy.build_contour_parallel_milling_strategy_spec,
        )
        self.assertIs(core_sp._strategy_is_multilevel, common_strategy._strategy_is_multilevel)
        self.assertIs(
            core_sp._extract_milling_strategy_spec_from_operation,
            common_strategy._extract_milling_strategy_spec_from_operation,
        )
        self.assertIs(core_sp._strategy_pass_levels, common_strategy._strategy_pass_levels)
        self.assertIs(core_sp._helical_rough_end_levels, common_strategy._helical_rough_end_levels)
        self.assertIs(
            core_sp._build_unidirectional_line_strategy_profile,
            common_strategy._build_unidirectional_line_strategy_profile,
        )
        self.assertIs(
            core_sp._build_bidirectional_line_strategy_profile,
            common_strategy._build_bidirectional_line_strategy_profile,
        )
        self.assertIs(
            core_sp._build_unidirectional_open_profile_strategy_toolpath,
            common_strategy._build_unidirectional_open_profile_strategy_toolpath,
        )
        self.assertIs(
            core_sp._build_bidirectional_open_profile_strategy_toolpath,
            common_strategy._build_bidirectional_open_profile_strategy_toolpath,
        )
        self.assertIs(core_sp._build_closed_profile_strategy_toolpath, common_strategy._build_closed_profile_strategy_toolpath)
        self.assertIs(core_sp._build_helical_arc_primitive, common_strategy._build_helical_arc_primitive)
        self.assertIs(
            core_sp._build_helical_circle_strategy_toolpath,
            common_strategy._build_helical_circle_strategy_toolpath,
        )
        self.assertIs(
            core_sp._resolve_unidirectional_connection_mode,
            common_strategy._resolve_unidirectional_connection_mode,
        )
        self.assertIs(
            core_sp._serialize_unidirectional_connection_mode,
            common_strategy._serialize_unidirectional_connection_mode,
        )
        self.assertIs(core_sp._strategy_comparison_key, common_strategy._strategy_comparison_key)
        self.assertEqual(common_strategy._normalize_strategy_connection_mode("en-la-pieza"), "InPiece")
        self.assertEqual(
            common_strategy._resolve_unidirectional_connection_mode(
                common_strategy.build_unidirectional_milling_strategy_spec(),
                is_closed_profile=True,
            ),
            "InPiece",
        )
        self.assertEqual(
            common_strategy._strategy_pass_levels(
                18.0,
                0.0,
                common_strategy.build_unidirectional_milling_strategy_spec(
                    axial_cutting_depth=5.0,
                    axial_finish_cutting_depth=2.0,
                ),
            ),
            (13.0, 8.0, 3.0, 2.0, 0.0),
        )
        self.assertEqual(
            common_strategy._helical_rough_end_levels(
                18.0,
                0.0,
                common_strategy.build_helical_milling_strategy_spec(
                    axial_cutting_depth=5.0,
                    axial_finish_cutting_depth=2.0,
                ),
            ),
            (13.0, 8.0, 3.0, 2.0),
        )
        strategy = common_strategy.build_bidirectional_milling_strategy_spec(axial_cutting_depth=2.5)
        self.assertTrue(strategy.allow_multiple_passes)
        self.assertEqual(strategy.axial_cutting_depth, 2.5)
        self.assertIs(milling_common._normalize_geometry_winding, common_geometry._normalize_geometry_winding)
        self.assertIs(milling_common._normalize_side_of_feature, common_geometry._normalize_side_of_feature)
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
        self.assertIs(core_sp._extract_approach_spec_from_operation, common_leads._extract_approach_spec_from_operation)
        self.assertIs(core_sp._extract_retract_spec_from_operation, common_leads._extract_retract_spec_from_operation)
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
        self.assertIs(core_sp._build_line_toolpath_profile, milling_line._build_line_toolpath_profile)
        self.assertIs(core_sp._offset_line_for_toolpath, milling_line._offset_line_for_toolpath)
        self.assertIs(core_sp._matches_line_geometry, milling_line._matches_line_geometry)
        self.assertIs(core_sp._can_hydrate_exact_serialization, milling_line._can_hydrate_exact_serialization)
        self.assertIs(core_sp._extract_line_milling_template, milling_line._extract_line_milling_template)
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
        self.assertIs(core_sp._build_polyline_toolpath_profile, milling_profile._build_polyline_toolpath_profile)
        self.assertIs(core_sp._matches_polyline_geometry, milling_profile._matches_polyline_geometry)
        self.assertIs(
            core_sp._can_hydrate_exact_polyline_serialization,
            milling_profile._can_hydrate_exact_polyline_serialization,
        )
        self.assertIs(core_sp._extract_polyline_milling_template, milling_profile._extract_polyline_milling_template)
        self.assertIs(milling_profile._normalize_polyline_points, common_geometry._normalize_polyline_points)
        self.assertIs(milling_profile._is_closed_polyline_points, common_geometry._is_closed_polyline_points)
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
        self.assertIs(core_sp.CircleMillingSpec, milling_circle.CircleMillingSpec)
        self.assertIs(core_sp.build_circle_milling_spec, milling_circle.build_circle_milling_spec)
        self.assertIs(core_sp._normalize_circle_milling_spec, milling_circle._normalize_circle_milling_spec)
        self.assertIs(core_sp._build_circle_toolpath_profile, milling_circle._build_circle_toolpath_profile)
        self.assertIs(core_sp._matches_circle_geometry, milling_circle._matches_circle_geometry)
        self.assertIs(
            core_sp._can_hydrate_exact_circle_serialization,
            milling_circle._can_hydrate_exact_circle_serialization,
        )
        self.assertIs(core_sp._extract_circle_milling_template, milling_circle._extract_circle_milling_template)
        circle = milling_circle.build_circle_milling_spec(
            center_x=50,
            center_y=60,
            radius=20,
            winding="horario",
            side_of_feature="derecha",
            milling_strategy=common_strategy.build_helical_milling_strategy_spec(axial_cutting_depth=2.0),
        )
        self.assertIsInstance(circle, milling_circle.CircleMillingSpec)
        self.assertEqual(circle.winding, "Clockwise")
        self.assertEqual(circle.side_of_feature, "Right")
        self.assertIsInstance(circle.milling_strategy, common_strategy.HelicalMillingStrategySpec)
        with self.assertRaisesRegex(ValueError, "radio"):
            milling_circle.build_circle_milling_spec(center_x=0, center_y=0, radius=0)
        self.assertIs(core_sp.SquaringMillingSpec, milling_squaring.SquaringMillingSpec)
        self.assertIs(core_sp.build_squaring_milling_spec, milling_squaring.build_squaring_milling_spec)
        self.assertIs(core_sp._normalize_squaring_milling_spec, milling_squaring._normalize_squaring_milling_spec)
        self.assertIs(core_sp._build_squaring_outline_points, milling_squaring._build_squaring_outline_points)
        self.assertIs(core_sp._build_squaring_geometry_profile, milling_squaring._build_squaring_geometry_profile)
        self.assertIs(core_sp._build_squaring_toolpath_profile, milling_squaring._build_squaring_toolpath_profile)
        self.assertIs(
            core_sp._reparameterize_squaring_toolpath_profile,
            milling_squaring._reparameterize_squaring_toolpath_profile,
        )
        squaring = milling_squaring.build_squaring_milling_spec(start_edge="borde-derecho", winding="horario")
        self.assertIsInstance(squaring, milling_squaring.SquaringMillingSpec)
        self.assertEqual(squaring.start_edge, "Right")
        self.assertEqual(squaring.winding, "Clockwise")
        self.assertEqual(squaring.side_of_feature, "Left")
        self.assertEqual(squaring.tool_id, "1900")
        self.assertTrue(squaring.depth_spec.is_through)
        self.assertEqual(squaring.depth_spec.extra_depth, 1.0)
        self.assertEqual(squaring.approach.approach_type, "Arc")
        self.assertIs(core_sp.PocketMillingSpec, milling_pocket.PocketMillingSpec)
        self.assertIs(core_sp.PocketBossRouteSeedSpec, milling_pocket.PocketBossRouteSeedSpec)
        self.assertIs(core_sp.build_pocket_milling_spec, milling_pocket.build_pocket_milling_spec)
        self.assertIs(core_sp._extract_pocket_milling_template, milling_pocket._extract_pocket_milling_template)
        self.assertIs(
            core_sp._can_hydrate_pocket_template_trace,
            milling_pocket._can_hydrate_pocket_template_trace,
        )
        self.assertIs(
            core_sp.build_pocket_boss_route_seed_spec,
            milling_pocket.build_pocket_boss_route_seed_spec,
        )
        seed = milling_pocket.build_pocket_boss_route_seed_spec(
            geometry_id="42",
            contour_points=((20, 20), (40, 20), (40, 40), (20, 20)),
        )
        pocket = milling_pocket.build_pocket_milling_spec(
            contour_points=((0, 0), (100, 0), (100, 80), (0, 0)),
            tool_width=20.0,
            allowance_side=2.0,
            boss_route_seeds=(seed,),
        )
        self.assertIsInstance(pocket, milling_pocket.PocketMillingSpec)
        self.assertEqual(pocket.feature_name, "Vaciado")
        self.assertEqual(pocket.effective_contour_offset, 12.0)
        self.assertEqual(pocket.radial_step, 10.0)
        self.assertTrue(pocket.has_boss_route_seeds)
        self.assertEqual(pocket.resolved_boss_route_seed_contours, (seed.contour_points,))
        with self.assertRaisesRegex(ValueError, "primer y ultimo punto"):
            milling_pocket.build_pocket_milling_spec(contour_points=((0, 0), (100, 0), (100, 80), (0, 80)))


if __name__ == "__main__":
    unittest.main()
