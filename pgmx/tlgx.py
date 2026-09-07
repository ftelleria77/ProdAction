"""Lector del catalogo de herramientas de Maestro (`def.tlgx`).

`def.tlgx` es el catalogo que arma el taller en Maestro y **viaja dentro de cada
`.pgmx`**, asi que es la fuente de datos de herramienta que siempre esta a mano.

Este modulo existe porque `pgmx/data/tool_catalog.csv` **no es origen de datos**:
lo derivo Fermin a mano con ayuda de IA como resumen, y tiene errores conocidos
--las descripciones de las brocas `058` y `059` quedaron cruzadas--. La decision
del 2026-08-30 fue re-anclar todo en `def.tlgx`; esto es esa decision, aplicada.

Ver `iso/docs/experiments/perforado.md` (Grupo 6) y `experiments/canal.md`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

__all__ = [
    "TlgxTool",
    "load_tlgx",
    "load_tlgx_from_pgmx",
    "default_tlgx_path",
]

# Tipos de cuerpo que el catalogo declara para un disco de sierra.
_BLADE_BODIES = {"UniversalBlade"}


def default_tlgx_path() -> Path:
    """El `def.tlgx` del snapshot de la maquina."""

    return (
        Path(__file__).resolve().parents[1]
        / "iso"
        / "data"
        / "machine_config"
        / "snapshot"
        / "maestro"
        / "Tlgx"
        / "def.tlgx"
    )


def _local(element: ET.Element) -> str:
    return element.tag.split("}")[-1]


def _walk(element: ET.Element) -> Iterator[ET.Element]:
    for child in element:
        yield child
        yield from _walk(child)


def _text(element: ET.Element, name: str, default: str = "") -> str:
    for node in _walk(element):
        if _local(node) == name and node.text is not None:
            return node.text.strip()
    return default


def _number(element: ET.Element, name: str, default: float = 0.0) -> float:
    raw = _text(element, name)
    try:
        return float(raw)
    except ValueError:
        return default


def _integer(element: ET.Element, name: str, default: int = 0) -> int:
    raw = _text(element, name)
    try:
        return int(raw)
    except ValueError:
        return default


def _speed_triplet(element: ET.Element, name: str) -> tuple[float, float, float]:
    """`<name><Minimum/><Standard/><Maximum/></name>` en cualquier profundidad."""

    for node in _walk(element):
        if _local(node) == name:
            return (
                _number(node, "Minimum"),
                _number(node, "Standard"),
                _number(node, "Maximum"),
            )
    return (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class TlgxTool:
    """Una herramienta del catalogo, con lo que el ISO necesita saber de ella."""

    tool_id: str
    name: str
    description: str
    kind_of_tool: str
    body_type: str
    diameter: float
    blade_thickness: Optional[float]
    tool_offset_length: float
    sinking_length: float
    pilot_length: float
    hand_of_cut: str
    plc_out: int
    store_pos: int
    head_num: int
    faces: tuple[bool, bool, bool, bool, bool]
    spindle_speed: tuple[float, float, float]
    feed_rate: tuple[float, float, float]
    descent_speed: tuple[float, float, float]

    # --- lecturas derivadas, todas con evidencia en experiments/ ---

    @property
    def is_blade(self) -> bool:
        """Disco de sierra: el manual de Xilog lo llama herramienta de tipo `D`."""

        return self.body_type in _BLADE_BODIES

    @property
    def is_boring_unit(self) -> bool:
        """Vive en el cabezal perforador (no hay cambio de herramienta)."""

        return self.kind_of_tool == "XilogBoringUnitTool"

    @property
    def cutting_radius(self) -> float:
        """El `SVR` del ISO: el radio del CUERPO de la herramienta.

        Manual de Xilog: *"si la fresa es de vela (tipo F), la correccion es igual
        al radio declarado; si es de disco (tipo D), a la mitad del espesor de la
        hoja"*. Verificado contra el ISO: `082` -> 1.9 - `E004` -> 2.0 -
        `E001` -> 9.18 - `E002` -> 50.0.
        """

        if self.is_blade and self.blade_thickness:
            return self.blade_thickness / 2.0
        return self.diameter / 2.0

    @property
    def cutting_width(self) -> float:
        """La `Anchura` de la ventana de Canal, que la UI no deja editar."""

        if self.is_blade and self.blade_thickness:
            return self.blade_thickness
        return self.diameter

    @property
    def uses_cnc_correction(self) -> bool:
        """`ActivateCNCCorrection` del `.pgmx`, que lo decide la HERRAMIENTA.

        `false` con la sierra --que trabaja siempre en modo CAD-- y `true` con una
        fresa del electromandril. Ver `experiments/canal.md` seccion 10.
        """

        return not self.is_blade

    def works_face(self, face: int) -> bool:
        """`st_OFace`: en que caras puede trabajar (1 = superior)."""

        if not 1 <= face <= 5:
            raise ValueError("El catalogo declara las caras 1 a 5.")
        return self.faces[face - 1]


def _parse_tool(element: ET.Element) -> Optional[TlgxTool]:
    key = None
    for node in element:
        if _local(node) == "Key":
            key = node
            break
    tool_id = _text(key, "ID") if key is not None else ""

    holder = None
    body = None
    for node in _walk(element):
        local = _local(node)
        if local == "HolderDataTool" and holder is None:
            holder = node
        elif local == "ToolBody" and body is None:
            body = node
    if holder is None or body is None:
        return None

    name = ""
    for node in element:
        if _local(node) == "Name" and node.text:
            name = node.text.strip()
            break

    faces = tuple(
        _text(holder, f"Face{i}", "false").lower() == "true" for i in range(1, 6)
    )

    body_type = ""
    for attr, value in body.attrib.items():
        if attr.endswith("type"):
            body_type = value.split(":")[-1]
            break

    blade_thickness = None
    raw_thickness = _text(body, "BladeThickness")
    if raw_thickness:
        try:
            blade_thickness = float(raw_thickness)
        except ValueError:
            blade_thickness = None

    return TlgxTool(
        tool_id=tool_id,
        name=name,
        description=_text(element, "Description"),
        kind_of_tool=_text(holder, "KindOfTool"),
        body_type=body_type,
        diameter=_number(body, "Diameter"),
        blade_thickness=blade_thickness,
        tool_offset_length=_number(body, "ToolOffsetLength"),
        sinking_length=_number(body, "SinkingLength"),
        pilot_length=_number(body, "PilotLength"),
        hand_of_cut=_text(body, "HandOfCut"),
        plc_out=_integer(holder, "shPlcOut"),
        store_pos=_integer(holder, "shStorePos"),
        head_num=_integer(holder, "shHeadNum"),
        faces=faces,  # type: ignore[arg-type]
        spindle_speed=_speed_triplet(body, "SpindleSpeed"),
        feed_rate=_speed_triplet(body, "FeedRate"),
        descent_speed=_speed_triplet(body, "DescentSpeed"),
    )


def _parse_catalog(raw: bytes) -> dict[str, TlgxTool]:
    root = ET.fromstring(raw)
    catalogo: dict[str, TlgxTool] = {}
    for element in root:
        if _local(element) != "CoreTool":
            continue
        tool = _parse_tool(element)
        if tool is not None and tool.name:
            catalogo[tool.name] = tool
    return catalogo


def load_tlgx(path: Optional[Path] = None) -> dict[str, TlgxTool]:
    """Lee un `def.tlgx` y devuelve las herramientas indexadas por nombre."""

    target = Path(path) if path is not None else default_tlgx_path()
    if not target.exists():
        raise FileNotFoundError(f"No existe el catalogo de herramientas '{target}'.")
    return _parse_catalog(target.read_bytes())


def load_tlgx_from_pgmx(path: Path) -> dict[str, TlgxTool]:
    """Lee el `def.tlgx` que viaja adentro de un `.pgmx`."""

    with zipfile.ZipFile(Path(path)) as archive:
        nombres = [n for n in archive.namelist() if n.lower().endswith("def.tlgx")]
        if not nombres:
            raise KeyError(f"El .pgmx '{path}' no trae 'def.tlgx' adentro.")
        return _parse_catalog(archive.read(nombres[0]))
