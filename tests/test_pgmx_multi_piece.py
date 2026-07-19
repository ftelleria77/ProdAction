"""Tests para sintesis PGMX multi-pieza (Workstream A: composicion N piezas → 1 PGMX)."""

from __future__ import annotations

import re
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from pgmx import synthesis as sp


def _pgmx_xml_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        entry_name = next(name for name in archive.namelist() if name.lower().endswith(".xml"))
        return archive.read(entry_name).decode("utf-8")


def _pgmx_root(path: Path) -> ET.Element:
    return ET.fromstring(_pgmx_xml_text(path))


class MultiPieceSynthesisTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # Estructura basica — pieza unica via pieces=
    # ------------------------------------------------------------------

    def test_single_piece_via_pieces_produces_valid_pgmx(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "SingleViaPieces.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(
                        name="Pieza A",
                        length=600,
                        width=300,
                        depth=18,
                    )
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn("Pieza A", xml_text)
        # La variable dx1 debe valer 600
        self.assertIn(">600<", xml_text)
        self.assertIn(">300<", xml_text)
        # Solo un WorkPiece
        self.assertEqual(xml_text.count("<WorkPiece>"), 1)

    # ------------------------------------------------------------------
    # Dos piezas — variables dimensionales
    # ------------------------------------------------------------------

    def test_two_pieces_write_dx1_dy1_dz1_and_dx2_dy2_dz2(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "TwoPieces.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(name="Pieza 1", length=400, width=400, depth=18),
                    sp.build_piece_spec(name="Pieza 2", length=600, width=250, depth=15),
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        # Dos WorkPiece
        self.assertEqual(xml_text.count("<WorkPiece>"), 2)
        # Variables dimensionales de pieza 1
        self.assertRegex(xml_text, r'<\w+:Name>dx1</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Name>dy1</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Name>dz1</\w+:Name>')
        # Variables dimensionales de pieza 2
        self.assertRegex(xml_text, r'<\w+:Name>dx2</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Name>dy2</\w+:Name>')
        self.assertRegex(xml_text, r'<\w+:Name>dz2</\w+:Name>')

    def test_two_pieces_workpiece_names_are_written(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "TwoPiecesNames.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(name="Panel Largo", length=800, width=400, depth=18),
                    sp.build_piece_spec(name="Panel Corto", length=400, width=400, depth=18),
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn("Panel Largo", xml_text)
        self.assertIn("Panel Corto", xml_text)

    # ------------------------------------------------------------------
    # Planos — naming convention
    # ------------------------------------------------------------------

    def test_two_pieces_planes_use_suffix_convention(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "TwoPiecesPlanes.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(name="P1", length=400, width=300, depth=18),
                    sp.build_piece_spec(name="P2", length=600, width=250, depth=18),
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        # Pieza 1: planos sin sufijo
        self.assertIn(">Top<", xml_text)
        self.assertIn(">Right<", xml_text)
        # Pieza 2: planos con sufijo (1)
        self.assertIn(">Top(1)<", xml_text)
        self.assertIn(">Right(1)<", xml_text)
        # 12 planos en total (6 × 2)
        self.assertEqual(xml_text.count("<Plane>"), 12)

    def test_three_pieces_planes_naming(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ThreePiecesPlanes.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(name="P1", length=400, width=300, depth=18),
                    sp.build_piece_spec(name="P2", length=600, width=250, depth=18),
                    sp.build_piece_spec(name="P3", length=500, width=500, depth=22),
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertIn(">Top<", xml_text)
        self.assertIn(">Top(1)<", xml_text)
        self.assertIn(">Top(2)<", xml_text)
        self.assertEqual(xml_text.count("<Plane>"), 18)

    # ------------------------------------------------------------------
    # WorkpieceSetup — origenes por pieza
    # ------------------------------------------------------------------

    def test_two_pieces_origins_are_written_to_workpiece_setups(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "TwoPiecesOrigin.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(
                        name="P1", length=400, width=300, depth=18,
                        origin_x=5, origin_y=5, origin_z=25,
                    ),
                    sp.build_piece_spec(
                        name="P2", length=600, width=250, depth=18,
                        origin_x=450, origin_y=5, origin_z=25,
                    ),
                ],
            )
            result = sp.synthesize_request(request)
            root = _pgmx_root(result.output_path)

        setups = root.findall(
            "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup"
        )
        self.assertEqual(len(setups), 2)

        def get_xP(setup: ET.Element) -> str:
            return (setup.findtext(".//{*}_xP") or "").strip()

        x_values = {get_xP(s) for s in setups}
        self.assertIn("5", x_values)
        self.assertIn("450", x_values)

    # ------------------------------------------------------------------
    # Mecanizados — se asignan a la pieza correcta
    # ------------------------------------------------------------------

    def test_drilling_on_piece2_uses_piece2_workpiece_id(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DrillPiece2.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(name="P1", length=400, width=300, depth=18),
                    sp.build_piece_spec(
                        name="P2",
                        length=600,
                        width=250,
                        depth=18,
                        drills=[
                            sp.build_drill_spec(
                                diameter=5,
                                center_x=100,
                                center_y=100,
                                target_depth=15,
                            )
                        ],
                    ),
                ],
            )
            result = sp.synthesize_request(request)
            root = _pgmx_root(result.output_path)
            xml_text = _pgmx_xml_text(result.output_path)

        # El WorkPiece de P2 debe existir
        workpieces = root.findall("./{*}Workpieces/{*}WorkPiece")
        self.assertEqual(len(workpieces), 2)

        p2_wp = next(
            wp for wp in workpieces
            if (wp.findtext(".//{*}Name") or "").strip() == "P2"
        )
        p2_id = (p2_wp.findtext(".//{*}Key/{*}ID") or "").strip()

        # El p2_id aparece al menos dos veces: definicion de WorkPiece + referencia del mecanizado
        # (el prefijo de namespace puede variar segun el contexto XML)
        self.assertGreaterEqual(xml_text.count(f">{p2_id}<"), 2)

    # ------------------------------------------------------------------
    # Variables parametricas por pieza
    # ------------------------------------------------------------------

    def test_piece_parametric_variables_are_written(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "PieceVars.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(
                        name="P1",
                        length=400,
                        width=300,
                        depth=18,
                        parametric_variables=[
                            sp.build_parametric_variable_spec(
                                name="Profundidad",
                                value=12.0,
                            )
                        ],
                    ),
                    sp.build_piece_spec(name="P2", length=600, width=250, depth=18),
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        self.assertRegex(xml_text, r'<\w+:Name>Profundidad</\w+:Name>')
        self.assertIn(">12<", xml_text)

    # ------------------------------------------------------------------
    # Expresiones dimensionales de piezas adicionales
    # ------------------------------------------------------------------

    def test_two_pieces_have_dim_expressions_for_both(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "TwoPiecesExpr.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[
                    sp.build_piece_spec(name="P1", length=400, width=300, depth=18),
                    sp.build_piece_spec(name="P2", length=600, width=250, depth=15),
                ],
            )
            result = sp.synthesize_request(request)
            xml_text = _pgmx_xml_text(result.output_path)

        # Las expresiones que vinculan dx1/dy1/dz1 y dx2/dy2/dz2 a los WorkPieces
        self.assertIn(">dx1<", xml_text)
        self.assertIn(">dy1<", xml_text)
        self.assertIn(">dz1<", xml_text)
        self.assertIn(">dx2<", xml_text)
        self.assertIn(">dy2<", xml_text)
        self.assertIn(">dz2<", xml_text)

    # ------------------------------------------------------------------
    # PgmxSynthesisResult refleja las piezas
    # ------------------------------------------------------------------

    def test_result_pieces_field_reflects_input(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ResultPieces.pgmx"
            p1 = sp.build_piece_spec(name="P1", length=400, width=300, depth=18)
            p2 = sp.build_piece_spec(name="P2", length=600, width=250, depth=15)
            request = sp.build_synthesis_request(output_path=output_path, pieces=[p1, p2])
            result = sp.synthesize_request(request)

        self.assertEqual(len(result.pieces), 2)
        self.assertEqual(result.pieces[0].name, "P1")
        self.assertEqual(result.pieces[1].name, "P2")

    # ------------------------------------------------------------------
    # Validacion: pieces y workplans son mutuamente excluyentes
    # ------------------------------------------------------------------

    def test_pieces_and_workplans_raises_value_error(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Conflict.pgmx"
            request = sp.build_synthesis_request(
                output_path=output_path,
                pieces=[sp.build_piece_spec(name="P1", length=400, width=300, depth=18)],
                workplans=[sp.build_workplan_spec(name="Setup")],
            )
            with self.assertRaises(ValueError):
                sp.synthesize_request(request)


if __name__ == "__main__":
    unittest.main()
