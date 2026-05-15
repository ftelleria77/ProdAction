"""Readers over the Maestro/Xilog machine configuration snapshot."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


class MachineConfigError(RuntimeError):
    """Raised when the machine configuration snapshot is missing required data."""


@dataclass(frozen=True)
class TopDrillToolConfig:
    spindle: int
    mask: int
    shf_x: float
    shf_y: float
    shf_z: float
    tool_offset_length: float
    spindle_speed: float
    descent_feed: float


@dataclass(frozen=True)
class SideDrillToolConfig:
    plane_name: str
    etk8: int
    spindle: int
    mask: int
    shf_x: float
    shf_y: float
    shf_z: float
    tool_offset_length: float
    spindle_speed: float
    descent_feed: float
    axis: str
    direction: int
    coordinate_sign: int


@dataclass(frozen=True)
class LineMillingToolConfig:
    tool_name: str
    tool_number: int
    spindle: int
    tool_code: int
    etk18: int
    tool_width: float
    shf_x: float
    shf_y: float
    shf_z: float
    tool_offset_length: float
    spindle_speed: float
    plunge_feed: float
    milling_feed: float


@dataclass(frozen=True)
class SlotMillingToolConfig:
    tool_name: str
    spindle: int
    mask: int
    shf_x: float
    shf_y: float
    shf_z: float
    tool_offset_length: float
    spindle_speed: float
    plunge_feed: float
    milling_feed: float


@dataclass(frozen=True)
class MachineFrameConfig:
    work_origin_y: float
    base_shf_y: float
    safe_z: float
    park_x: float
    side_g53_clearance: float


@dataclass(frozen=True)
class MachineConfig:
    frame: MachineFrameConfig
    top_drill_tools: dict[str, TopDrillToolConfig]
    side_drill_tools: dict[str, SideDrillToolConfig]
    line_milling_tools: dict[str, LineMillingToolConfig]
    slot_milling_tools: dict[str, SlotMillingToolConfig]
    tool_names_by_id: dict[str, str]


@dataclass(frozen=True)
class _CoreToolData:
    tool_id: str
    name: str
    tool_offset_length: float
    pilot_length: float
    diameter: float
    spindle_speed: float
    feed_rate: float
    descent_speed: float


@dataclass(frozen=True)
class _SpindleComponentData:
    spindle: int
    ref_tool_id: str
    translation_x: float
    translation_y: float
    translation_z: float
    pilot_length: float
    radius: float
    spindle_speed: float
    feed_rate: float
    descent_speed: float


@dataclass(frozen=True)
class _ToolLibraryData:
    core_tools: dict[str, _CoreToolData]
    spindle_components: dict[int, _SpindleComponentData]


@dataclass(frozen=True)
class _SideDrillPolicy:
    plane_name: str
    etk8: int
    spindle: int
    mask: int
    axis: str
    direction: int
    coordinate_sign: int


@dataclass(frozen=True)
class _WorkFieldData:
    name: str
    origin_x: float
    origin_y: float
    origin_z: float
    size_x: float
    size_y: float


_DEFAULT_SNAPSHOT_ROOT = Path(__file__).resolve().parent / "snapshot"

# Face selectors and ETK masks are ISO control policy observed in Maestro output;
# dimensional values for these tools are still loaded from def.tlgx below.
_SIDE_DRILL_POLICIES = {
    "Left": _SideDrillPolicy("Left", 3, 61, 2147483648, "X", -1, -1),
    "Right": _SideDrillPolicy("Right", 2, 60, 2147483648, "X", 1, 1),
    "Front": _SideDrillPolicy("Front", 5, 58, 1073741824, "Y", -1, 1),
    "Back": _SideDrillPolicy("Back", 4, 59, 1073741824, "Y", 1, -1),
}

_ROUTER_TOOL_NAMES = ("E001", "E003", "E004", "E005", "E006", "E007")


def load_machine_config(snapshot_root: Path | None = None) -> MachineConfig:
    """Load ISO-relevant machine configuration from the local snapshot."""

    root = Path(snapshot_root) if snapshot_root is not None else _DEFAULT_SNAPSHOT_ROOT
    return _load_machine_config_cached(root.resolve())


@lru_cache(maxsize=None)
def _load_machine_config_cached(snapshot_root: Path) -> MachineConfig:
    library = _load_tool_library(snapshot_root / "maestro" / "Tlgx" / "def.tlgx")
    frame = _load_frame_config(snapshot_root)
    return MachineConfig(
        frame=frame,
        top_drill_tools=_build_top_drill_tools(library),
        side_drill_tools=_build_side_drill_tools(library),
        line_milling_tools=_build_line_milling_tools(snapshot_root, library),
        slot_milling_tools=_build_slot_milling_tools(library),
        tool_names_by_id={
            tool.tool_id: tool.name.upper() for tool in library.core_tools.values()
        },
    )


def _load_tool_library(path: Path) -> _ToolLibraryData:
    if not path.exists():
        raise MachineConfigError(f"Missing Maestro tool library: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise MachineConfigError(f"Cannot parse Maestro tool library {path}: {exc}") from exc

    core_tools: dict[str, _CoreToolData] = {}
    spindle_components: dict[int, _SpindleComponentData] = {}
    for element in root.iter():
        if _local_name(element.tag) == "CoreTool":
            core_tool = _parse_core_tool(element)
            if core_tool is not None:
                core_tools[core_tool.name.upper()] = core_tool
        elif _local_name(element.tag) == "SpindleComponent":
            component = _parse_spindle_component(element)
            spindle_components[component.spindle] = component
    return _ToolLibraryData(core_tools=core_tools, spindle_components=spindle_components)


def _parse_core_tool(element: ET.Element) -> _CoreToolData | None:
    name = _child_text(element, "Name")
    key = _child(element, "Key")
    tool_id = _child_text(key, "ID") if key is not None else None
    technology = _first_descendant(element, "ToolTechnology")
    offset_length = _first_descendant_float(element, "ToolOffsetLength")
    if not name or not tool_id or technology is None or offset_length is None:
        return None
    return _CoreToolData(
        tool_id=tool_id,
        name=name,
        tool_offset_length=offset_length,
        pilot_length=_required_float(_first_descendant_float(element, "PilotLength"), name),
        diameter=_required_float(_first_descendant_float(element, "Diameter"), name),
        spindle_speed=_technology_standard(technology, "SpindleSpeed"),
        feed_rate=_technology_standard(technology, "FeedRate"),
        descent_speed=_technology_standard(technology, "DescentSpeed"),
    )


def _parse_spindle_component(element: ET.Element) -> _SpindleComponentData:
    spindle_text = _child_text(element, "Id")
    if spindle_text is None:
        raise MachineConfigError("SpindleComponent without Id in Maestro tool library.")
    ref_key = _first_descendant(element, "RefToolKey")
    ref_tool_id = _child_text(ref_key, "ID") if ref_key is not None else None
    translation = _first_descendant(element, "Translation")
    technology = _first_descendant(element, "SpindleTechnology")
    if ref_tool_id is None or translation is None or technology is None:
        raise MachineConfigError(f"SpindleComponent {spindle_text} is incomplete.")
    return _SpindleComponentData(
        spindle=int(spindle_text),
        ref_tool_id=ref_tool_id,
        translation_x=_required_float(_child_float(translation, "OX"), spindle_text),
        translation_y=_required_float(_child_float(translation, "OY"), spindle_text),
        translation_z=_required_float(_child_float(translation, "OZ"), spindle_text),
        pilot_length=_required_float(_child_float(element, "PilotLength"), spindle_text),
        radius=_first_descendant_float(element, "Radius") or 0.0,
        spindle_speed=_technology_standard(technology, "SpindleSpeed"),
        feed_rate=_technology_standard(technology, "FeedRate"),
        descent_speed=_technology_standard(technology, "DescentSpeed"),
    )


def _build_top_drill_tools(library: _ToolLibraryData) -> dict[str, TopDrillToolConfig]:
    tools: dict[str, TopDrillToolConfig] = {}
    for spindle in range(1, 8):
        tool_name = f"{spindle:03d}"
        component = _required_component(library, spindle)
        _required_core_tool(library, tool_name)
        tools[tool_name] = TopDrillToolConfig(
            spindle=spindle,
            mask=1 << (spindle - 1),
            shf_x=_invert_offset(component.translation_x),
            shf_y=_invert_offset(component.translation_y),
            shf_z=_invert_offset(component.translation_z),
            tool_offset_length=component.pilot_length,
            spindle_speed=component.spindle_speed,
            descent_feed=_drilling_descent_feed(component),
        )
    return tools


def _build_side_drill_tools(library: _ToolLibraryData) -> dict[str, SideDrillToolConfig]:
    tools: dict[str, SideDrillToolConfig] = {}
    for policy in _SIDE_DRILL_POLICIES.values():
        component = _required_component(library, policy.spindle)
        tools[policy.plane_name] = SideDrillToolConfig(
            plane_name=policy.plane_name,
            etk8=policy.etk8,
            spindle=policy.spindle,
            mask=policy.mask,
            shf_x=_invert_offset(component.translation_x),
            shf_y=_invert_offset(component.translation_y),
            shf_z=_invert_offset(component.translation_z),
            tool_offset_length=component.pilot_length,
            spindle_speed=component.spindle_speed,
            descent_feed=_drilling_descent_feed(component),
            axis=policy.axis,
            direction=policy.direction,
            coordinate_sign=policy.coordinate_sign,
        )
    return tools


def _build_line_milling_tools(
    snapshot_root: Path,
    library: _ToolLibraryData,
) -> dict[str, LineMillingToolConfig]:
    head_x, head_y, head_z = _read_line_spindle_offsets(
        snapshot_root / "xilog_plus" / "Cfg" / "pheads.cfg"
    )
    tools: dict[str, LineMillingToolConfig] = {}
    for tool_name in _ROUTER_TOOL_NAMES:
        tool = _required_core_tool(library, tool_name)
        tool_number = int(tool.name.removeprefix("E"))
        tools[tool.name.upper()] = LineMillingToolConfig(
            tool_name=tool.name.upper(),
            tool_number=tool_number,
            # Spindle/ETK routing is ISO policy; tool geometry comes from snapshot.
            spindle=1,
            tool_code=tool_number,
            etk18=1,
            tool_width=tool.diameter,
            shf_x=_invert_offset(head_x),
            shf_y=_invert_offset(head_y),
            shf_z=_invert_offset(head_z),
            tool_offset_length=tool.tool_offset_length,
            spindle_speed=tool.spindle_speed,
            plunge_feed=tool.descent_speed * 1000.0,
            milling_feed=tool.feed_rate * 1000.0,
        )
    return tools


def _build_slot_milling_tools(library: _ToolLibraryData) -> dict[str, SlotMillingToolConfig]:
    tool = _required_core_tool(library, "082")
    component = _required_component(library, 82)
    return {
        tool.name.upper(): SlotMillingToolConfig(
            tool_name=tool.name.upper(),
            spindle=component.spindle,
            # Slot activation mask is ISO policy; offsets and rates come from def.tlgx.
            mask=16,
            shf_x=_invert_offset(component.translation_x),
            shf_y=_clean_zero(_invert_offset(component.translation_y) - component.radius),
            shf_z=_invert_offset(component.translation_z),
            tool_offset_length=component.pilot_length,
            spindle_speed=component.spindle_speed,
            plunge_feed=component.descent_speed * 1000.0,
            milling_feed=component.feed_rate * 1000.0,
        )
    }


def _load_frame_config(snapshot_root: Path) -> MachineFrameConfig:
    maestro_security_distance = _read_maestro_app_setting(
        snapshot_root / "maestro" / "Cfgx" / "Programaciones.settingsx",
        ("UI00.exe.Config", "XConverter.exe.config"),
        "SecurityDistance",
    )
    params = _read_ini_sections(snapshot_root / "xilog_plus" / "Cfg" / "Params.cfg")
    hg_reference = _read_work_field(
        snapshot_root / "xilog_plus" / "Cfg" / "fields.cfg",
        "H",
    )
    z_park = _axis_param(params, "ax2", "AP_PARKQTA")
    if z_park == 0.0:
        z_park = _axis_param(params, "ax2", "AP_MAXQUOTA")
    x_min = _axis_param(params, "ax0", "AP_MINQUOTA")
    return MachineFrameConfig(
        # HG programs observed from Maestro use field H as the Y reference.
        # %Or is emitted in controller units after single-precision storage.
        work_origin_y=_controller_units_from_mm(hg_reference.origin_y),
        base_shf_y=hg_reference.origin_y,
        safe_z=z_park / 1000.0,
        park_x=(x_min / 1000.0) + 2.0,
        # Lateral aggregate changes clear both safety offsets around the panel.
        side_g53_clearance=2.0 * maestro_security_distance,
    )


def _read_line_spindle_offsets(path: Path) -> tuple[float, float, float]:
    values = list(_read_numeric_lines(path))
    start_index = 308
    try:
        return values[start_index], values[start_index + 1], values[start_index + 2]
    except IndexError as exc:
        raise MachineConfigError(f"Cannot read E004 spindle offsets from {path}.") from exc


def _read_numeric_lines(path: Path) -> Iterable[float]:
    if not path.exists():
        raise MachineConfigError(f"Missing Xilog head configuration: {path}")
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            yield float(raw_line.strip())
        except ValueError:
            continue


def _read_maestro_app_setting(
    path: Path,
    config_entry_names: tuple[str, ...],
    key: str,
) -> float:
    if not path.exists():
        raise MachineConfigError(f"Missing Maestro settings archive: {path}")
    wanted_entries = tuple(name.lower() for name in config_entry_names)
    try:
        with ZipFile(path) as archive:
            entries = {
                name.lower(): name
                for name in archive.namelist()
                if name.lower() in wanted_entries
            }
            for wanted in wanted_entries:
                entry_name = entries.get(wanted)
                if entry_name is None:
                    continue
                root = ET.fromstring(archive.read(entry_name))
                for add in root.iter("add"):
                    if add.attrib.get("key") != key:
                        continue
                    value = add.attrib.get("value")
                    if value is None:
                        break
                    try:
                        return float(value)
                    except ValueError as exc:
                        raise MachineConfigError(
                            f"Invalid Maestro setting {key!r} in {path}:{entry_name}."
                        ) from exc
    except (BadZipFile, ET.ParseError) as exc:
        raise MachineConfigError(f"Cannot parse Maestro settings archive {path}.") from exc
    raise MachineConfigError(
        f"Missing Maestro setting {key!r} in {path} "
        f"entries {', '.join(config_entry_names)}."
    )


def _read_work_field(path: Path, field_name: str) -> _WorkFieldData:
    if not path.exists():
        raise MachineConfigError(f"Missing Xilog fields configuration: {path}")
    field_name = field_name.strip().upper()
    for label, values in _read_labeled_numeric_blocks(path):
        if label.upper() != field_name:
            continue
        if len(values) < 19:
            raise MachineConfigError(
                f"Cannot read field {field_name!r} origin from {path}: "
                f"expected at least 19 numeric values, got {len(values)}."
            )
        return _WorkFieldData(
            name=label.upper(),
            origin_x=values[14],
            origin_y=values[15],
            origin_z=values[16],
            size_x=values[17],
            size_y=values[18],
        )
    raise MachineConfigError(f"Missing work field {field_name!r} in {path}.")


def _read_labeled_numeric_blocks(path: Path) -> Iterable[tuple[str, list[float]]]:
    values: list[float] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        try:
            values.append(float(line))
            continue
        except ValueError:
            pass
        label = "".join(
            char for char in line if ord(char) >= 32 and char != "\x7f"
        ).strip()
        yield label, values
        values = []
    if values:
        yield "", values


def _controller_units_from_mm(value: float) -> float:
    return _to_float32(value) * 1000.0


def _to_float32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _read_ini_sections(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        raise MachineConfigError(f"Missing Xilog axis parameters: {path}")
    sections: dict[str, dict[str, float]] = {}
    current = ""
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip().lower()
            sections.setdefault(current, {})
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        try:
            sections.setdefault(current, {})[key.strip()] = float(value.strip())
        except ValueError:
            continue
    return sections


def _axis_param(sections: dict[str, dict[str, float]], section: str, key: str) -> float:
    try:
        return sections[section][key]
    except KeyError as exc:
        raise MachineConfigError(f"Missing {section}.{key} in Xilog axis parameters.") from exc


def _required_core_tool(library: _ToolLibraryData, name: str) -> _CoreToolData:
    try:
        return library.core_tools[name.upper()]
    except KeyError as exc:
        raise MachineConfigError(f"Missing Maestro tool {name!r} in tool library.") from exc


def _required_component(library: _ToolLibraryData, spindle: int) -> _SpindleComponentData:
    try:
        return library.spindle_components[spindle]
    except KeyError as exc:
        raise MachineConfigError(f"Missing spindle component {spindle} in tool library.") from exc


def _drilling_descent_feed(component: _SpindleComponentData) -> float:
    return min(component.feed_rate, component.descent_speed) * 1000.0


def _invert_offset(value: float) -> float:
    return _clean_zero(-value)


def _clean_zero(value: float) -> float:
    if abs(value) < 1e-9:
        return 0.0
    return value


def _technology_standard(technology: ET.Element, name: str) -> float:
    group = _child(technology, name)
    if group is None:
        raise MachineConfigError(f"Missing technology group {name!r}.")
    value = _child_float(group, "Standard")
    if value is None:
        raise MachineConfigError(f"Missing Standard value for technology group {name!r}.")
    return value


def _required_float(value: float | None, label: str) -> float:
    if value is None:
        raise MachineConfigError(f"Missing numeric value while parsing {label!r}.")
    return value


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _child(element: ET.Element | None, name: str) -> ET.Element | None:
    if element is None:
        return None
    for child in element:
        if _local_name(child.tag) == name:
            return child
    return None


def _child_text(element: ET.Element | None, name: str) -> str | None:
    child = _child(element, name)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _child_float(element: ET.Element | None, name: str) -> float | None:
    text = _child_text(element, name)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise MachineConfigError(f"Invalid float for {name!r}: {text!r}.") from exc


def _first_descendant(element: ET.Element, name: str) -> ET.Element | None:
    for candidate in element.iter():
        if candidate is element:
            continue
        if _local_name(candidate.tag) == name:
            return candidate
    return None


def _first_descendant_float(element: ET.Element, name: str) -> float | None:
    candidate = _first_descendant(element, name)
    if candidate is None or candidate.text is None:
        return None
    try:
        return float(candidate.text.strip())
    except ValueError as exc:
        raise MachineConfigError(f"Invalid float for {name!r}: {candidate.text!r}.") from exc
