"""Tests para split_pgmx_pieces — extracción de piezas individuales desde un PGMX multipiezas."""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pgmx import synthesis as sp


def _xml_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        entry = next(n for n in zf.namelist() if n.lower().endswith(".xml"))
        return zf.read(entry).decode("utf-8")


def _xml_root(path: Path) -> ET.Element:
    return ET.fromstring(_xml_text(path))


def _build_two_piece_pgmx(output_path: Path) -> sp.PgmxSynthesisResult:
    return sp.synthesize_request(
        sp.build_synthesis_request(
            output_path=output_path,
            pieces=[
                sp.build_piece_spec(
                    name="Pieza A",
                    length=600,
                    width=300,
                    depth=18,
                    drillings=[
                        sp.build_drilling_spec(diameter=5, center_x=50, center_y=50, target_depth=15),
                        sp.build_drilling_spec(diameter=5, center_x=100, center_y=50, target_depth=15),
                    ],
                ),
                sp.build_piece_spec(
                    name="Pieza B",
                    length=400,
                    width=250,
                    depth=12,
                    drillings=[
                        sp.build_drilling_spec(diameter=8, center_x=80, center_y=80, target_depth=10),
                    ],
                ),
            ],
        )
    )


# ------------------------------------------------------------------
# Conteo de archivos extraídos
# ------------------------------------------------------------------

def test_split_two_piece_returns_two_files() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)

        paths = sp.split_pgmx_pieces(src, out)

    assert len(paths) == 2


def test_split_three_piece_returns_three_files() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        sp.synthesize_request(
            sp.build_synthesis_request(
                output_path=src,
                pieces=[
                    sp.build_piece_spec(name="P1", length=400, width=300, depth=18),
                    sp.build_piece_spec(name="P2", length=500, width=280, depth=15),
                    sp.build_piece_spec(name="P3", length=300, width=200, depth=12),
                ],
            )
        )
        paths = sp.split_pgmx_pieces(src, out)

    assert len(paths) == 3


# ------------------------------------------------------------------
# Cada archivo extraído tiene exactamente 1 WorkPiece
# ------------------------------------------------------------------

def test_each_extracted_file_has_one_workpiece() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        for p in paths:
            root = _xml_root(p)
            wps = root.findall("./{*}Workpieces/{*}WorkPiece")
            assert len(wps) == 1, f"{p.name}: expected 1 WorkPiece, got {len(wps)}"


# ------------------------------------------------------------------
# Nombres de los archivos y WorkPiece
# ------------------------------------------------------------------

def test_extracted_files_are_named_after_workpieces() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        names = {p.stem for p in paths}
    assert names == {"Pieza A", "Pieza B"}


def test_extracted_workpiece_names_match_originals() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        found_names = set()
        for p in paths:
            root = _xml_root(p)
            wp = root.find("./{*}Workpieces/{*}WorkPiece")
            if wp is not None:
                found_names.add((wp.findtext(".//{*}Name") or "").strip())

    assert found_names == {"Pieza A", "Pieza B"}


# ------------------------------------------------------------------
# Variables dimensionales → renombradas a dx1/dy1/dz1
# ------------------------------------------------------------------

def test_each_piece_uses_dx1_dy1_dz1() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        for p in paths:
            root = _xml_root(p)
            wp = root.find("./{*}Workpieces/{*}WorkPiece")
            assert wp is not None
            lname = (wp.findtext(".//{*}LengthName") or "").strip()
            wname = (wp.findtext(".//{*}WidthName") or "").strip()
            dname = (wp.findtext(".//{*}DepthName") or "").strip()
            assert lname == "dx1", f"{p.name}: LengthName={lname!r}"
            assert wname == "dy1", f"{p.name}: WidthName={wname!r}"
            assert dname == "dz1", f"{p.name}: DepthName={dname!r}"


def test_no_indexed_dim_vars_above_1_in_extracted_file() -> None:
    """No deben quedar dx2/dy3/dz4... sin prefijo en archivos extraídos."""
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        for p in paths:
            xml = _xml_text(p)
            # Variables with index >= 2 that are NOT snapshot-prefixed
            bad = re.findall(r'\bd[xyz][2-9]\b', xml)
            assert not bad, f"{p.name}: found unrenamed dim vars: {set(bad)}"


def test_extracted_piece_has_correct_dimensions() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        piece_a = next(p for p in paths if p.stem == "Pieza A")
        root = _xml_root(piece_a)
        vars_node = root.find("./{*}Variables")
        values = {}
        for var in (list(vars_node) if vars_node is not None else []):
            name = (var.findtext(".//{*}Name") or "").strip()
            val = (var.findtext(".//{*}Value") or "").strip()
            if name in ("dx1", "dy1", "dz1"):
                values[name] = val

    assert values.get("dx1") == "600"
    assert values.get("dy1") == "300"
    assert values.get("dz1") == "18"


# ------------------------------------------------------------------
# Planos — nombres canónicos sin sufijo
# ------------------------------------------------------------------

def test_extracted_file_has_six_canonical_planes() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        expected = {"Top", "Right", "Left", "Front", "Back", "Bottom"}
        for p in paths:
            root = _xml_root(p)
            planes = root.findall("./{*}Planes/{*}Plane")
            names = {(pl.findtext(".//{*}Name") or "").strip() for pl in planes}
            assert names == expected, f"{p.name}: planes={names}"


# ------------------------------------------------------------------
# Mecanizados — asignados a la pieza correcta
# ------------------------------------------------------------------

def test_step_counts_match_source_drillings() -> None:
    """Pieza A tiene 2 taladros → 2 steps; Pieza B tiene 1 → 1 step."""
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        counts = {}
        for p in paths:
            root = _xml_root(p)
            elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
            counts[p.stem] = len(list(elements)) if elements is not None else 0

    assert counts["Pieza A"] == 2
    assert counts["Pieza B"] == 1


# ------------------------------------------------------------------
# Expresiones — solo las de la pieza extraída
# ------------------------------------------------------------------

def test_expressions_only_reference_own_workpiece() -> None:
    with TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "multi.pgmx"
        out = Path(tmpdir) / "out"
        _build_two_piece_pgmx(src)
        paths = sp.split_pgmx_pieces(src, out)

        for p in paths:
            root = _xml_root(p)
            wp = root.find("./{*}Workpieces/{*}WorkPiece")
            assert wp is not None
            own_id = (wp.findtext(".//{*}Key/{*}ID") or "").strip()
            exprs = root.findall("./{*}Expressions/{*}Expression")
            for expr in exprs:
                ref_id = (expr.findtext(".//{*}ReferencedObject/{*}ID") or "").strip()
                assert ref_id == own_id, f"{p.name}: expr refs foreign id {ref_id!r}"
