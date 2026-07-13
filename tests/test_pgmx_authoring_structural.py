"""Autoría pgmx forma-Maestro: la operación AUTORADA debe ser estructuralmente idéntica a la
que escribe Maestro (N032 falló 0/4 por diferencias invisibles al roundtrip propio: namespaces
de OperationAttribute que el deserializador ignora EN SILENCIO, y el toolpath almacenado —
que Maestro postprocesa TAL CUAL — sin los strokes zigzag / curvas partidas).

Compara el subárbol <Operation> sintetizado contra el de los fixtures REALES hechos en Maestro
(N025 zigzag / N022 Vel / N022 Prof), normalizando IDs y redondeando floats. No requiere
postprocesar: es la red de regresión offline del modelo derivado en N032→N033 (commit eb1d7fa).
"""

from __future__ import annotations

import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from pgmx.synthesis import build_line_spec, build_synthesis_request, synthesize_request
from pgmx.synthesis.common.strategy import ZigZagMillingStrategySpec

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"

_REAL_FIXTURES = {
    "zigzag": Path(r"S:\Maestro\Projects\ProdAction\N025_router_multipass\N_MP_zigzag_pa2_pr3_uh1.pgmx"),
    "vel": Path(r"S:\Maestro\Projects\ProdAction\N022_router_expand\N_RT_E001_Vel.pgmx"),
    "prof": Path(r"S:\Maestro\Projects\ProdAction\N022_router_expand\N_RT_E001_Prof.pgmx"),
}


def _line_spec(tool: str, width: float, depth: float, **kwargs):
    tool_id = {"E004": "1903", "E001": "1900"}[tool]
    return build_line_spec(
        line_x1=20.0, line_y1=100.0, line_x2=280.0, line_y2=100.0,
        line_feature_name="Fresado", line_tool_id=tool_id, line_tool_name=tool,
        line_tool_width=width, line_security_plane=20.0,
        line_is_through=False, line_target_depth=depth, **kwargs)


def _inner_xml(path: Path) -> bytes:
    with zipfile.ZipFile(path) as container:
        name = [n for n in container.namelist() if n.endswith(".xml")][0]
        return container.read(name)


def _operation_lines(xml_bytes: bytes) -> list[str]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_bytes)
    operation = next(
        e for e in root.iter() if e.attrib.get(_XSI_TYPE, "").endswith("BottomAndSideFinishMilling")
    )

    lines: list[str] = []

    def walk(element, depth=0):
        match = re.match(r"\{(.*)\}(.*)", element.tag)
        if match:
            namespace, local = match.groups()
            short = namespace.rsplit(".", 1)[-1] if "ScmGroup" in namespace else namespace.rsplit("/", 1)[-1]
            tag = f"{short}:{local}"
        else:
            tag = element.tag
        text = (element.text or "").strip()
        if re.fullmatch(r"\d{3,5}", text):
            text = "#ID"  # claves asignadas (difieren por archivo, no por estructura)
        else:
            text = re.sub(r"-?\d+\.\d{6,}", lambda m: f"{float(m.group(0)):.4f}", text)
        xsi = element.attrib.get(_XSI_TYPE, "")
        lines.append(f"{'  ' * depth}{tag}{'[' + xsi + ']' if xsi else ''}={text}")
        for child in element:
            walk(child, depth + 1)

    walk(operation)
    return lines


class AuthoringStructuralTest(unittest.TestCase):
    """La forma autorada == la forma Maestro (mod IDs), sin necesidad de postprocesar."""

    def _check(self, fixture_name: str, spec) -> None:
        real_path = _REAL_FIXTURES[fixture_name]
        if not real_path.exists():
            self.skipTest("fixtures S: no disponibles")
        with tempfile.TemporaryDirectory() as tmp:
            authored_path = Path(tmp) / f"aut_{fixture_name}.pgmx"
            synthesize_request(build_synthesis_request(
                output_path=authored_path, piece_name=f"aut_{fixture_name}",
                length=300.0, width=200.0, depth=18.0,
                origin_x=5.0, origin_y=5.0, origin_z=25.0, line_millings=[spec]))
            authored = _operation_lines(_inner_xml(authored_path))
        real = _operation_lines(_inner_xml(real_path))
        self.assertEqual(authored, real)

    def test_zigzag_strokes_en_toolpath(self):
        # Maestro postprocesa el toolpath ALMACENADO: los strokes en rampa van en la curva.
        self._check("zigzag", _line_spec("E004", 4.0, 12.0, line_milling_strategy=ZigZagMillingStrategySpec(
            allow_multiple_passes=True, feed_cutting_depth=2.0,
            return_cutting_depth=3.0, axial_finish_cutting_depth=1.0)))

    def test_cambio_velocidad_curva_partida(self):
        # Curva partida en el UPar + SpeedAttribute a nivel toolpath anclado al segmento 2.
        from dataclasses import replace
        self._check("vel", replace(_line_spec("E001", 18.36, 3.0), speed_changes=((0.3, 1.0),)))

    def test_cambio_profundidad_rampa(self):
        # Rampa lineal hasta el UPar + plano; sin atributo de toolpath (la prof. es geometría).
        from dataclasses import replace
        self._check("prof", replace(_line_spec("E001", 18.36, 3.0), depth_changes=((0.25, 5.0),)))


if __name__ == "__main__":
    unittest.main()
