from __future__ import annotations

import re
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from pgmx.adapters import adapt_pgmx_path
from pgmx import synthesis as sp
from pgmx.snapshot import read_pgmx_snapshot


class PgmxMachineOperationsTests(unittest.TestCase):
    def test_synthesizes_multiphase_xn_and_xmsg_program_flow(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "MachineOps_Multiphase.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                piece_name="MachineOps",
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        name="Fase Inicial",
                        machine_operations=(
                            sp.build_xn_spec(
                                name="Despeje de pieza",
                                x=-2000,
                                y=None,
                            ),
                            sp.build_xmsg_spec(
                                text="Girar la Pieza",
                                name="Mensaje a operador",
                                stop="PEI",
                            ),
                        ),
                    ),
                    sp.build_workplan_spec(
                        name="Fase Final",
                        origin_x=0,
                        origin_y=0,
                        origin_z=25,
                        machine_operations=(
                            sp.build_xn_spec(
                                name="Despeje y Fin",
                                x=-2500,
                                y=None,
                            ),
                        ),
                    ),
                ),
            )

            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertEqual(snapshot.current_workplan_index, 0)
        self.assertEqual([workplan.name for workplan in snapshot.workplans], ["Fase Inicial", "Fase Final"])
        self.assertEqual(
            [
                (workplan.origin_x, workplan.origin_y, workplan.origin_z)
                for workplan in snapshot.workplans
            ],
            [(5.0, 5.0, 25.0), (0.0, 0.0, 25.0)],
        )
        self.assertEqual([step.runtime_type for step in snapshot.working_steps], ["Xn", "Xmsg", "Xn"])
        self.assertEqual([step.workplan_index for step in snapshot.working_steps], [1, 1, 2])

        first_xn, xmsg, final_xn = snapshot.working_steps
        self.assertEqual(first_xn.name, "Despeje de pieza")
        self.assertEqual(first_xn.reference, "Absolute")
        self.assertEqual(first_xn.speed, 0.0)
        self.assertEqual(first_xn.spindle_enable, "Off")
        self.assertEqual(first_xn.x, -2000.0)
        self.assertIsNone(first_xn.y)
        self.assertIsNotNone(first_xn.tool_ref)
        self.assertEqual(first_xn.tool_ref.id, "0")

        self.assertEqual(xmsg.name, "Mensaje a operador")
        self.assertEqual(xmsg.text, "Girar la Pieza")
        self.assertEqual(xmsg.stop, "NoUnlock")
        self.assertFalse(xmsg.input_enabled)
        self.assertIsNotNone(xmsg.geometry_ref)
        self.assertEqual(xmsg.geometry_ref.id, "0")
        self.assertIsNotNone(xmsg.workpiece_ref)

        self.assertEqual(final_xn.name, "Despeje y Fin")
        self.assertEqual(final_xn.x, -2500.0)
        self.assertEqual(len(snapshot.machine_operations), 3)
        self.assertEqual(len(re.findall(r'i:type="Xn" xmlns="http://schemas\.datacontract\.org/2004/07/ScmGroup\.XCam\.MachiningDataModel"', xml_text)), 2)
        self.assertEqual(len(re.findall(r'i:type="Xmsg" xmlns="http://schemas\.datacontract\.org/2004/07/ScmGroup\.XCam\.MachiningDataModel"', xml_text)), 1)

    def test_legacy_xn_request_keeps_single_workplan_behavior(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "MachineOps_Legacy_XN.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                xn=sp.build_xn_spec(x=-2500, y=None),
            )

            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        self.assertEqual(len(snapshot.workplans), 1)
        self.assertEqual(len(snapshot.working_steps), 1)
        self.assertEqual(snapshot.working_steps[0].runtime_type, "Xn")
        self.assertEqual(snapshot.working_steps[0].x, -2500.0)
        self.assertEqual(snapshot.working_steps[0].workplan_index, 1)
        self.assertEqual(result.workplans, ())

    def test_synthesizes_machinings_in_requested_workplans(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "MachineOps_Multiphase_Machinings.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                piece_name="MachineOps",
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        name="Cara_Superior",
                        machinings=(
                            sp.build_line_milling_spec(
                                20,
                                30,
                                380,
                                30,
                                "Linea Superior",
                                "1900",
                                "E001",
                                18.36,
                                20,
                                line_target_depth=8,
                            ),
                        ),
                        machine_operations=(
                            sp.build_xn_spec(name="XN Superior", x=-2300, y=0),
                        ),
                    ),
                    sp.build_workplan_spec(
                        name="Cara_Inferior",
                        origin_x=0,
                        origin_y=0,
                        origin_z=25,
                        machinings=(
                            sp.build_drilling_spec(
                                center_x=100,
                                center_y=100,
                                diameter=5,
                                feature_name="Taladro Inferior",
                                target_depth=2,
                                tool_resolution="None",
                            ),
                        ),
                        machine_operations=(
                            sp.build_xn_spec(name="XN Inferior", x=-2300, y=0),
                        ),
                    ),
                ),
            )

            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        self.assertEqual([workplan.name for workplan in snapshot.workplans], ["Cara_Superior", "Cara_Inferior"])
        self.assertEqual([step.name for step in snapshot.working_steps], [
            "Linea Superior",
            "XN Superior",
            "Taladro Inferior",
            "XN Inferior",
        ])
        self.assertEqual([step.workplan_index for step in snapshot.working_steps], [1, 1, 2, 2])
        self.assertEqual([len(workplan.working_steps) for workplan in snapshot.workplans], [2, 2])
        self.assertEqual(snapshot.workplans[1].origin_x, 0.0)
        self.assertEqual(snapshot.workplans[1].origin_y, 0.0)
        self.assertEqual(snapshot.workplans[1].origin_z, 25.0)

    def test_xn_y_can_be_null_or_explicit_numeric_coordinate(self) -> None:
        with TemporaryDirectory() as tmpdir:
            null_y_output = Path(tmpdir) / "MachineOps_XN_Y_Null.pgmx"
            explicit_y_output = Path(tmpdir) / "MachineOps_XN_Y_Zero.pgmx"

            sp.synthesize_request(
                sp.build_synthesis_request(
                    output_path=null_y_output,
                    xn=sp.build_xn_spec(x=-2500, y=None),
                )
            )
            sp.synthesize_request(
                sp.build_synthesis_request(
                    output_path=explicit_y_output,
                    xn=sp.build_xn_spec(
                        name="XN",
                        x=-2300,
                        y=0,
                        tool_id="1900",
                        tool_object_type="ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
                        tool_name="E001",
                    ),
                )
            )

            null_y_snapshot = read_pgmx_snapshot(null_y_output)
            explicit_y_snapshot = read_pgmx_snapshot(explicit_y_output)

        null_y_xn = null_y_snapshot.working_steps[0]
        explicit_y_xn = explicit_y_snapshot.working_steps[0]

        self.assertIsNone(null_y_xn.y)
        self.assertIsNotNone(null_y_xn.geometry_ref)
        self.assertEqual(null_y_xn.geometry_ref.id, "0")
        self.assertEqual(null_y_xn.geometry_ref.object_type, "")

        self.assertEqual(explicit_y_xn.y, 0.0)
        self.assertIsNotNone(explicit_y_xn.geometry_ref)
        self.assertEqual(explicit_y_xn.geometry_ref.id, "0")
        self.assertEqual(explicit_y_xn.geometry_ref.object_type, "System.Object")
        self.assertIsNotNone(explicit_y_xn.tool_ref)
        self.assertEqual(explicit_y_xn.tool_ref.id, "1900")
        self.assertEqual(explicit_y_xn.tool_ref.name, "E001")

    def test_adapter_preserves_final_xn_numeric_y_coordinate(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "MachineOps_Source_XN_Y_Zero.pgmx"
            output_path = Path(tmpdir) / "MachineOps_Adapted_XN_Y_Zero.pgmx"
            sp.synthesize_request(
                sp.build_synthesis_request(
                    output_path=source_path,
                    xn=sp.build_xn_spec(
                        name="XN",
                        reference="Absolute",
                        x=-2300,
                        y=0,
                        tool_id="1900",
                        tool_object_type="ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
                        tool_name="E001",
                    ),
                )
            )

            adaptation = adapt_pgmx_path(source_path)
            request = adaptation.build_synthesis_request(output_path)
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        self.assertIsNotNone(adaptation.xn)
        self.assertEqual(adaptation.xn.x, -2300.0)
        self.assertEqual(adaptation.xn.y, 0.0)
        self.assertEqual(adaptation.xn.tool_id, "1900")
        self.assertEqual(request.xn.y, 0.0)

        adapted_xn = snapshot.working_steps[-1]
        self.assertEqual(adapted_xn.runtime_type, "Xn")
        self.assertEqual(adapted_xn.x, -2300.0)
        self.assertEqual(adapted_xn.y, 0.0)
        self.assertIsNotNone(adapted_xn.tool_ref)
        self.assertEqual(adapted_xn.tool_ref.id, "1900")


    def test_synthesizes_park_operation_stop_modes(self) -> None:
        stop_cases = [
            ("Nothing", "NP"),
            ("NoUnlock", "PEI"),
            ("Unlock", "PDEI"),
        ]
        for stop_value, label in stop_cases:
            with self.subTest(stop=stop_value):
                with TemporaryDirectory() as tmpdir:
                    output_path = Path(tmpdir) / f"Park_{label}.pgmx"
                    request = sp.build_synthesis_request(
                        output_path=output_path,
                        piece_name="Park_Test",
                        length=400,
                        width=400,
                        depth=18,
                        origin_x=5,
                        origin_y=5,
                        origin_z=25,
                        workplans=(
                            sp.build_workplan_spec(
                                name="Setup",
                                machine_operations=(
                                    sp.build_park_spec(stop=stop_value),
                                ),
                            ),
                        ),
                    )
                    result = sp.synthesize_request(request)
                    snapshot = read_pgmx_snapshot(result.output_path)
                    xml_text = _pgmx_xml_text(result.output_path)

                self.assertEqual(len(snapshot.machine_operations), 1)
                park = snapshot.machine_operations[0]
                self.assertEqual(park.runtime_type, "Park")
                self.assertEqual(park.name, "Park")
                self.assertEqual(park.limit, "Minimum")
                self.assertEqual(park.stop, stop_value)
                self.assertIsNotNone(park.workpiece_ref)
                self.assertIn(
                    f'i:type="Park" xmlns="http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"',
                    xml_text,
                )

    def test_park_name_is_configurable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Park_Custom.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        machine_operations=(
                            sp.build_park_spec(
                                name="Aparcar Cabezal",
                                stop="np",
                            ),
                        ),
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        park = snapshot.machine_operations[0]
        self.assertEqual(park.runtime_type, "Park")
        self.assertEqual(park.name, "Aparcar Cabezal")
        self.assertEqual(park.limit, "Minimum")
        self.assertEqual(park.stop, "Nothing")

    def test_park_limit_maximum(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Park_Maximum.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        machine_operations=(
                            sp.build_park_spec(limit="Maximum"),
                        ),
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        park = snapshot.machine_operations[0]
        self.assertEqual(park.runtime_type, "Park")
        self.assertEqual(park.limit, "Maximum")

    def test_park_limit_default_is_minimum(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Park_DefaultLimit.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        machine_operations=(
                            sp.build_park_spec(),
                        ),
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        park = snapshot.machine_operations[0]
        self.assertEqual(park.runtime_type, "Park")
        self.assertEqual(park.limit, "Minimum")

    def test_synthesizes_iso_operation(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Iso_G0Z100.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                piece_name="Iso_Test",
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        name="Setup",
                        machine_operations=(
                            sp.build_iso_spec(text="G0Z100"),
                        ),
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertEqual(len(snapshot.machine_operations), 1)
        iso = snapshot.machine_operations[0]
        self.assertEqual(iso.runtime_type, "Iso")
        self.assertEqual(iso.name, "ISO")
        self.assertEqual(iso.text, "G0Z100")
        self.assertEqual(iso.is_xiso, False)
        self.assertEqual(iso.option_parameters, "")
        self.assertIsNotNone(iso.workpiece_ref)
        self.assertIn(
            'i:type="Iso" xmlns="http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"',
            xml_text,
        )

    def test_iso_is_xiso_flag(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Iso_Xiso.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        machine_operations=(
                            sp.build_iso_spec(
                                text="G1X100Y50F3000",
                                name="Mi ISO",
                                is_xiso=True,
                            ),
                        ),
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        iso = snapshot.machine_operations[0]
        self.assertEqual(iso.runtime_type, "Iso")
        self.assertEqual(iso.name, "Mi ISO")
        self.assertEqual(iso.text, "G1X100Y50F3000")
        self.assertEqual(iso.is_xiso, True)

    def test_iso_option_parameters(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Iso_Opts.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                workplans=(
                    sp.build_workplan_spec(
                        machine_operations=(
                            sp.build_iso_spec(
                                text="G0Z100",
                                option_parameters="OPT1",
                            ),
                        ),
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            snapshot = read_pgmx_snapshot(result.output_path)

        iso = snapshot.machine_operations[0]
        self.assertEqual(iso.option_parameters, "OPT1")


    def test_drill_step_number(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Drill_StepNumber.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drillings=(
                    sp.build_drilling_spec(
                        center_x=100,
                        center_y=100,
                        diameter=5,
                        target_depth=10,
                        tool_resolution="None",
                        step_number=2,
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn('i:type="b:MultiStepDrilling"', xml_text)
        self.assertRegex(xml_text, r'<\w+:IsStepDepth>false</\w+:IsStepDepth>')
        self.assertRegex(xml_text, r'<\w+:StepNumber>2</\w+:StepNumber>')
        self.assertRegex(xml_text, r'<\w+:StepDepth>0</\w+:StepDepth>')

    def test_drill_step_depth(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Drill_StepDepth.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drillings=(
                    sp.build_drilling_spec(
                        center_x=100,
                        center_y=100,
                        diameter=5,
                        target_depth=10,
                        tool_resolution="None",
                        step_depth=3.0,
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn('i:type="b:MultiStepDrilling"', xml_text)
        self.assertRegex(xml_text, r'<\w+:IsStepDepth>true</\w+:IsStepDepth>')
        self.assertRegex(xml_text, r'<\w+:StepDepth>3</\w+:StepDepth>')

    def test_drill_feedrate_and_spindle(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Drill_Technology.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drillings=(
                    sp.build_drilling_spec(
                        center_x=100,
                        center_y=100,
                        diameter=5,
                        target_depth=10,
                        tool_resolution="None",
                        feedrate=3.0,
                        spindle=15000.0,
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn('<Feedrate>3</Feedrate>', xml_text)
        self.assertIn('<Spindle>15000</Spindle>', xml_text)

    def test_drill_taper_height(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Drill_TaperHeight.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drillings=(
                    sp.build_drilling_spec(
                        center_x=100,
                        center_y=100,
                        diameter=5,
                        target_depth=10,
                        tool_resolution="None",
                        taper_height=10.0,
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:TaperHeight>10</\w+:TaperHeight>')

    def test_parametric_variable_double_written_to_xml(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ParamVar_Double.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                parametric_variables=(
                    sp.build_parametric_variable_spec(
                        name="GrusorPanel",
                        value=18.0,
                        description="Grosor en mm",
                        variable_type="double",
                        physical_unit="length",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>GrusorPanel</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Type>Double</\w+:Type>')
        self.assertRegex(xml_text, r'<\w+:FisicalUnitType>Lenght</\w+:FisicalUnitType>')
        self.assertRegex(xml_text, r'i:type="b:double"')
        self.assertIn('>18<', xml_text)

    def test_parametric_variable_boolean_written_to_xml(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ParamVar_Bool.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                parametric_variables=(
                    sp.build_parametric_variable_spec(
                        name="EsActivo",
                        value=True,
                        variable_type="bool",
                        physical_unit="unitless",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>EsActivo</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Type>Boolean</\w+:Type>')
        self.assertRegex(xml_text, r'i:type="b:boolean"')
        self.assertIn('>true<', xml_text)

    def test_drill_is_enabled_expr_writes_expression_node(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Drill_IsEnabled.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drillings=(
                    sp.build_drilling_spec(
                        center_x=100,
                        center_y=100,
                        diameter=5,
                        target_depth=10,
                        tool_resolution="None",
                        is_enabled_expr="HabilitarTaladro",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>IsEnabled</\w+:Name>')
        self.assertIn('>HabilitarTaladro<', xml_text)

    def test_drill_center_xy_expr_writes_expression_nodes(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Drill_CenterXY.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drillings=(
                    sp.build_drilling_spec(
                        center_x=100,
                        center_y=100,
                        diameter=5,
                        target_depth=10,
                        tool_resolution="None",
                        center_x_expr="PosX",
                        center_y_expr="PosY",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn('>PosX<', xml_text)
        self.assertIn('>PosY<', xml_text)
        self.assertRegex(xml_text, r'<\w+:Name>X</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Name>Y</\w+:Name>')

    def test_slot_is_enabled_expr_writes_expression_node(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Slot_IsEnabled.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                slot_millings=(
                    sp.build_slot_milling_spec(
                        start_x=10,
                        start_y=100,
                        end_x=390,
                        end_y=100,
                        target_depth=8,
                        is_enabled_expr="HabilitarRanura",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>IsEnabled</\w+:Name>')
        self.assertIn('>HabilitarRanura<', xml_text)

    def test_pocket_is_enabled_expr_writes_expression_node(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Pocket_IsEnabled.pgmx"
            contour = [(50.0, 50.0), (350.0, 50.0), (350.0, 350.0), (50.0, 350.0), (50.0, 50.0)]
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                pocket_millings=(
                    sp.build_pocket_milling_spec(
                        contour_points=contour,
                        target_depth=10,
                        is_enabled_expr="HabilitarVaciado",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>IsEnabled</\w+:Name>')
        self.assertIn('>HabilitarVaciado<', xml_text)

    def test_drilling_pattern_is_enabled_expr_writes_expression_node(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Pattern_IsEnabled.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                length=400,
                width=400,
                depth=18,
                origin_x=5,
                origin_y=5,
                origin_z=25,
                drilling_patterns=(
                    sp.build_drilling_pattern_spec(
                        center_x=50,
                        center_y=50,
                        diameter=5,
                        columns=3,
                        rows=2,
                        spacing=100,
                        target_depth=10,
                        tool_resolution="None",
                        is_enabled_expr="HabilitarPatron",
                    ),
                ),
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>IsEnabled</\w+:Name>')
        self.assertIn('>HabilitarPatron<', xml_text)


def _pgmx_xml_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        entry_name = next(name for name in archive.namelist() if name.lower().endswith(".xml"))
        return archive.read(entry_name).decode("utf-8")


if __name__ == "__main__":
    unittest.main()
