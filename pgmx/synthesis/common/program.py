"""Program-level contracts for PGMX synthesis."""

from __future__ import annotations

import hashlib
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union

from ..drilling.pattern import (
    DrillingPatternSpec,
    _HydratedDrillingPatternSpec,
    _append_drilling_pattern,
    _hydrate_drilling_pattern_spec,
)
from ..drilling.single import (
    DrillingSpec,
    _HydratedDrillingSpec,
    _append_drilling,
    _hydrate_drilling_spec,
    _validate_tool_sinking_length_for_drilling_spec,
)
from ..milling._common import (
    _validate_tool_sinking_length_for_spec,
    _validate_tool_type_for_milling_spec,
)
from ..milling.circle import (
    CircleMillingSpec,
    _HydratedCircleMillingSpec,
    _append_circle_milling,
    _hydrate_circle_milling_spec,
)
from ..milling.line import (
    LineMillingSpec,
    _HydratedLineMillingSpec,
    _append_line_milling,
    _hydrate_line_milling_spec,
)
from ..milling.pocket import (
    PocketMillingSpec,
    _HydratedPocketMillingSpec,
    _append_pocket_milling,
    _hydrate_pocket_milling_spec,
)
from ..milling.profile import (
    PolylineMillingSpec,
    _HydratedPolylineMillingSpec,
    _append_polyline_milling,
    _hydrate_polyline_milling_spec,
)
from ..milling.slot import (
    SlotMillingSpec,
    _HydratedSlotMillingSpec,
    _append_slot_milling,
    _hydrate_slot_milling_spec,
)
from ..milling.squaring import (
    SquaringMillingSpec,
    _HydratedSquaringMillingSpec,
    _append_squaring_milling,
    _hydrate_squaring_milling_spec,
)
from .hydration import _load_pgmx_container
from .multi_piece import _active_workpiece_ctx, _add_piece_to_xml
from .output import (
    _finalize_pgmx_xml_bytes,
    _finalize_synthesized_pgmx_xml_bytes,
    _write_pgmx_zip,
)
from .tools import (
    _load_tool_catalog,
    _validate_tool_type_for_drilling_spec,
)
from .xml import (
    BASE_MODEL_NS,
    PARAMETRIC_NS,
    UTILITY_NS,
    XSD_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _compact_number,
    _qname,
    _reserve_ids,
    _safe_float,
    _set_text,
    _set_xmlns,
    _text,
    _xsi_type,
    register_pgmx_namespaces,
)

__all__ = [
    "DEFAULT_BASELINE_DIR",
    "DEFAULT_BASELINE_XML_PATH",
    "DEFAULT_MACHINING_ORDER",
    "HydratedMachiningSpec",
    "MachiningSpec",
    "MODULE_DIR",
    "ParametricVariableSpec",
    "PgmxState",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "PieceSpec",
    "SYNTHESIZER_VERSION",
    "MachineOperationSpec",
    "WorkplanSpec",
    "XnSpec",
    "XmsgSpec",
    "ParkSpec",
    "IsoSpec",
    "_apply_circle_millings",
    "_apply_drilling_patterns",
    "_apply_drillings",
    "_append_hydrated_machining",
    "_append_machine_operation",
    "_apply_line_millings",
    "_apply_parametric_variables",
    "_apply_piece_state",
    "_apply_pocket_millings",
    "_apply_polyline_millings",
    "_apply_slot_millings",
    "_apply_squaring_millings",
    "_build_xmsg_step",
    "_build_xn_step",
    "_drilling_plane_priority",
    "_ensure_xn_step",
    "_append_hydrated_machining_to_workplan",
    "_append_workplan_machinings",
    "_finalize_pgmx_xml_bytes",
    "_finalize_synthesized_pgmx_xml_bytes",
    "_ensure_workplans",
    "_hydrate_machining_spec",
    "_normalize_machining_order",
    "_normalize_execution_fields",
    "_normalize_machine_operations",
    "_normalize_workplan_spec",
    "_normalize_workplan_specs",
    "_normalize_xn_reference",
    "_normalize_xn_spec",
    "_normalize_xmsg_spec",
    "_normalize_xmsg_spec",
    "_merge_state",
    "_module_data_dir",
    "_split_hydrated_machinings",
    "_validate_tool_sinking_lengths",
    "_write_pgmx_zip",
    "_build_variable_node",
    "_normalize_physical_unit",
    "_normalize_variable_type",
    "build_parametric_variable_spec",
    "build_piece_spec",
    "build_synthesis_request",
    "build_workplan_spec",
    "build_xn_spec",
    "build_xmsg_spec",
    "build_park_spec",
    "_normalize_park_spec",
    "_build_park_step",
    "build_iso_spec",
    "_normalize_iso_spec",
    "_build_iso_step",

    "read_pgmx_state",
    "synthesize_pgmx",
    "synthesize_request",
]


DEFAULT_MACHINING_ORDER = ("line", "slot", "polyline", "circle", "squaring", "pocket", "drilling", "drilling_pattern")


register_pgmx_namespaces()


def _module_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        for bundled_data_dir in (
            executable_dir / "pgmx" / "data",
            executable_dir / "_internal" / "pgmx" / "data",
        ):
            if bundled_data_dir.exists():
                return bundled_data_dir
    return Path(__file__).resolve().parents[2] / "data"


MODULE_DIR = _module_data_dir()
DEFAULT_BASELINE_DIR = MODULE_DIR / "maestro_baselines"
DEFAULT_BASELINE_XML_PATH = DEFAULT_BASELINE_DIR / "Pieza.xml"
SYNTHESIZER_VERSION = "1.6"


@dataclass(frozen=True)
class PgmxState:
    """Descripcion de la pieza final a sintetizar."""

    piece_name: str
    length: float
    width: float
    depth: float
    origin_x: float
    origin_y: float
    origin_z: float
    execution_fields: str = "HG"


MachiningSpec = Union[
    LineMillingSpec,
    SlotMillingSpec,
    PolylineMillingSpec,
    CircleMillingSpec,
    SquaringMillingSpec,
    PocketMillingSpec,
    DrillingSpec,
    DrillingPatternSpec,
]


HydratedMachiningSpec = Union[
    _HydratedLineMillingSpec,
    _HydratedSlotMillingSpec,
    _HydratedPolylineMillingSpec,
    _HydratedCircleMillingSpec,
    _HydratedSquaringMillingSpec,
    _HydratedPocketMillingSpec,
    _HydratedDrillingSpec,
    _HydratedDrillingPatternSpec,
]


@dataclass(frozen=True)
class XnSpec:
    """Configuracion publica de `Xn`, la operacion nula de Maestro."""

    reference: str = "Absolute"
    x: float = -3700.0
    y: Optional[float] = None
    name: str = "Xn"
    speed: float = 0.0
    spindle_enable: str = "Off"
    tool_id: Optional[str] = None
    tool_object_type: str = "System.Object"
    tool_name: Optional[str] = None


@dataclass(frozen=True)
class XmsgSpec:
    """Mensaje al operario con modo de parada Maestro."""

    text: str
    stop: str = "Nothing"
    name: str = "Xmsg"
    input_enabled: bool = False
    variable_id: Optional[str] = None
    variable_object_type: str = ""
    variable_name: Optional[str] = None


@dataclass(frozen=True)
class ParkSpec:
    """Aparcamiento del cabezal a la posicion limite."""

    name: str = "Park"
    stop: str = "Nothing"
    limit: str = "Minimum"


@dataclass(frozen=True)
class IsoSpec:
    """Instruccion ISO/PGM embebida en un programa Maestro."""

    text: str
    name: str = "ISO"
    option_parameters: str = ""
    is_xiso: bool = False


MachineOperationSpec = Union[XnSpec, XmsgSpec, ParkSpec, IsoSpec]


@dataclass(frozen=True)
class PieceSpec:
    """Especificacion de una pieza individual para sintesis multipieza."""

    name: str
    length: float
    width: float
    depth: float
    origin_x: float = 0.0
    origin_y: float = 0.0
    origin_z: float = 0.0
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machine_operations: tuple[MachineOperationSpec, ...] = ()
    parametric_variables: tuple[ParametricVariableSpec, ...] = ()


@dataclass(frozen=True)
class ParametricVariableSpec:
    """Variable parametrica de usuario para calculos en tiempo de ejecucion Maestro."""

    name: str
    value: Union[float, int, bool]
    description: str = ""
    variable_type: str = "Double"
    physical_unit: str = "UnitLess"


@dataclass(frozen=True)
class WorkplanSpec:
    """Fase Maestro con origen propio y operaciones de maquina ordenadas."""

    name: str = "Setup"
    origin_x: Optional[float] = None
    origin_y: Optional[float] = None
    origin_z: Optional[float] = None
    machinings: tuple[MachiningSpec, ...] = ()
    machine_operations: tuple[MachineOperationSpec, ...] = ()


def _normalize_variable_type(value: Optional[str]) -> str:
    raw = (value or "Double").strip().lower()
    mapping = {
        "double": "Double",
        "float": "Double",
        "real": "Double",
        "decimal": "Double",
        "integer": "Integer",
        "int": "Integer",
        "entero": "Integer",
        "boolean": "Boolean",
        "bool": "Boolean",
        "booleano": "Boolean",
        "logico": "Boolean",
    }
    result = mapping.get(raw)
    if result is None:
        raise ValueError("variable_type invalido. Valores admitidos: Double, Integer o Boolean.")
    return result


def _normalize_physical_unit(value: Optional[str]) -> str:
    raw = (value or "UnitLess").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "unitless": "UnitLess",
        "sinunidades": "UnitLess",
        "adimensional": "UnitLess",
        "length": "Lenght",
        "lenght": "Lenght",
        "longitud": "Lenght",
        "speed": "Speed",
        "velocidad": "Speed",
    }
    result = mapping.get(raw)
    if result is None:
        raise ValueError("physical_unit invalido. Valores admitidos: UnitLess, Length o Speed.")
    return result


def _build_variable_node(var: ParametricVariableSpec, var_id: str) -> ET.Element:
    variable = ET.Element(_qname(PARAMETRIC_NS, "Variable"))
    _append_key(variable, var_id, "ScmGroup.XCam.MachiningDataModel.Parametrics.Variable")
    _append_node(variable, PARAMETRIC_NS, "Name", var.name)
    _append_node(variable, PARAMETRIC_NS, "Description", var.description)
    _append_node(variable, PARAMETRIC_NS, "FisicalUnitType", var.physical_unit)
    _append_node(variable, PARAMETRIC_NS, "IsReadOnly", "false")
    _append_node(variable, PARAMETRIC_NS, "Scope", "Local")
    _append_node(variable, PARAMETRIC_NS, "Type", var.variable_type)
    xsd_type_map = {"Double": "b:double", "Integer": "b:int", "Boolean": "b:boolean"}
    value_node = _append_node(
        variable,
        PARAMETRIC_NS,
        "Value",
        attrib={f"{{{XSI_NS}}}type": xsd_type_map[var.variable_type]},
    )
    _set_xmlns(value_node, "b", XSD_NS)
    if var.variable_type == "Double":
        value_node.text = _compact_number(float(var.value))
    elif var.variable_type == "Integer":
        value_node.text = str(int(var.value))
    else:
        value_node.text = "true" if var.value else "false"
    return variable


def _apply_parametric_variables(
    root: ET.Element,
    variables: Sequence[ParametricVariableSpec],
) -> None:
    if not variables:
        return
    variables_node = root.find("./{*}Variables")
    if variables_node is None:
        raise ValueError("La plantilla no contiene Variables para insertar variables parametricas.")
    existing: dict[str, ET.Element] = {
        _text(var, "./{*}Name").lower(): var
        for var in list(variables_node)
    }
    for var in variables:
        normalized = build_parametric_variable_spec(
            name=var.name,
            value=var.value,
            description=var.description,
            variable_type=var.variable_type,
            physical_unit=var.physical_unit,
        )
        existing_node = existing.get(normalized.name.lower())
        if existing_node is not None:
            value_node = existing_node.find("./{*}Value")
            if value_node is not None:
                _set_xmlns(value_node, "b", XSD_NS)
                if normalized.variable_type == "Double":
                    value_node.text = _compact_number(float(normalized.value))
                elif normalized.variable_type == "Integer":
                    value_node.text = str(int(normalized.value))
                else:
                    value_node.text = "true" if normalized.value else "false"
        else:
            [var_id] = _reserve_ids(root, 1)
            new_node = _build_variable_node(normalized, var_id)
            variables_node.append(new_node)
            existing[normalized.name.lower()] = new_node


def build_parametric_variable_spec(
    *,
    name: str,
    value: Union[float, int, bool],
    description: str = "",
    variable_type: Optional[str] = None,
    physical_unit: Optional[str] = None,
) -> ParametricVariableSpec:
    """Construye una variable parametrica de usuario para el bloque Variables del PGMX."""

    normalized_name = str(name).strip()
    if not normalized_name:
        raise ValueError("`name` es obligatorio para ParametricVariableSpec.")
    if normalized_name.lower() in {"dx1", "dy1", "dz1"}:
        raise ValueError(
            f"El nombre '{normalized_name}' esta reservado para las dimensiones de la pieza."
        )
    normalized_type = _normalize_variable_type(variable_type)
    normalized_unit = _normalize_physical_unit(physical_unit)
    if normalized_type == "Double":
        normalized_value: Union[float, int, bool] = float(value)
    elif normalized_type == "Integer":
        normalized_value = int(value)
    else:
        normalized_value = bool(value)
    return ParametricVariableSpec(
        name=normalized_name,
        value=normalized_value,
        description=str(description),
        variable_type=normalized_type,
        physical_unit=normalized_unit,
    )


def build_piece_spec(
    *,
    name: str,
    length: float,
    width: float,
    depth: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    origin_z: float = 0.0,
    line_millings: Optional[Sequence[LineMillingSpec]] = None,
    slot_millings: Optional[Sequence[SlotMillingSpec]] = None,
    polyline_millings: Optional[Sequence[PolylineMillingSpec]] = None,
    circle_millings: Optional[Sequence[CircleMillingSpec]] = None,
    squaring_millings: Optional[Sequence[SquaringMillingSpec]] = None,
    pocket_millings: Optional[Sequence[PocketMillingSpec]] = None,
    drillings: Optional[Sequence[DrillingSpec]] = None,
    drilling_patterns: Optional[Sequence[DrillingPatternSpec]] = None,
    ordered_machinings: Optional[Sequence[MachiningSpec]] = None,
    machine_operations: Optional[Sequence[MachineOperationSpec]] = None,
    parametric_variables: Optional[Sequence[ParametricVariableSpec]] = None,
) -> PieceSpec:
    """Construye la especificacion de una pieza para sintesis multipieza."""

    normalized_name = str(name).strip()
    if not normalized_name:
        raise ValueError("`name` es obligatorio para PieceSpec.")
    return PieceSpec(
        name=normalized_name,
        length=float(length),
        width=float(width),
        depth=float(depth),
        origin_x=float(origin_x),
        origin_y=float(origin_y),
        origin_z=float(origin_z),
        line_millings=tuple(line_millings or ()),
        slot_millings=tuple(slot_millings or ()),
        polyline_millings=tuple(polyline_millings or ()),
        circle_millings=tuple(circle_millings or ()),
        squaring_millings=tuple(squaring_millings or ()),
        pocket_millings=tuple(pocket_millings or ()),
        drillings=tuple(drillings or ()),
        drilling_patterns=tuple(drilling_patterns or ()),
        ordered_machinings=tuple(ordered_machinings or ()),
        machine_operations=_normalize_machine_operations(machine_operations or ()),
        parametric_variables=tuple(parametric_variables or ()),
    )


def _normalize_xn_reference(value: Optional[str]) -> str:
    raw = (value or "Absolute").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "absolute": "Absolute",
        "absoluto": "Absolute",
        "relative": "Relative",
        "relativo": "Relative",
    }
    normalized = mapping.get(raw)
    if normalized is None:
        raise ValueError("Reference invalido para Xn. Valores admitidos: Absolute/Absoluto o Relative/Relativo.")
    return normalized


def _normalize_spindle_enable(value: Optional[str]) -> str:
    raw = (value or "Off").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "off": "Off",
        "apagado": "Off",
        "emoff": "Off",
        "false": "Off",
        "0": "Off",
        "on": "On",
        "encendido": "On",
        "emon": "On",
        "true": "On",
        "1": "On",
    }
    normalized = mapping.get(raw)
    if normalized is None:
        raise ValueError("SpindleEnable invalido para Xn. Valores admitidos: On/Off.")
    return normalized


def _normalize_park_limit(value: Optional[str]) -> str:
    raw = (value or "Minimum").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "minimum": "Minimum",
        "minimo": "Minimum",
        "min": "Minimum",
        "izquierdo": "Minimum",
        "izquierda": "Minimum",
        "left": "Minimum",
        "maximum": "Maximum",
        "maximo": "Maximum",
        "max": "Maximum",
        "derecho": "Maximum",
        "derecha": "Maximum",
        "right": "Maximum",
    }
    normalized = mapping.get(raw)
    if normalized is None:
        raise ValueError("Limit invalido para Park. Valores admitidos: Minimum/Minimo/Izquierdo o Maximum/Maximo/Derecho.")
    return normalized


def _normalize_stop_mode(value: Optional[str]) -> str:
    raw = (value or "Nothing").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "nothing": "Nothing",
        "ningunparo": "Nothing",
        "sinparo": "Nothing",
        "np": "Nothing",
        "nounlock": "NoUnlock",
        "paroconesperadeinicio": "NoUnlock",
        "esperadeinicio": "NoUnlock",
        "pei": "NoUnlock",
        "unlock": "Unlock",
        "parocondesbloqueoyesperadeinicio": "Unlock",
        "desbloqueoyesperadeinicio": "Unlock",
        "pdei": "Unlock",
    }
    normalized = mapping.get(raw)
    if normalized is None:
        raise ValueError("Stop invalido. Valores admitidos: Nothing, NoUnlock o Unlock.")
    return normalized


def build_xn_spec(
    *,
    name: Optional[str] = None,
    reference: Optional[str] = None,
    speed: Optional[float] = None,
    spindle_enable: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
    tool_id: Optional[str] = None,
    tool_object_type: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> XnSpec:
    """Construye la spec publica `Xn` con defaults observados en Maestro."""

    return XnSpec(
        reference=_normalize_xn_reference(reference),
        x=-3700.0 if x is None else float(x),
        y=None if y is None else float(y),
        name=(name or "Xn").strip() or "Xn",
        speed=0.0 if speed is None else float(speed),
        spindle_enable=_normalize_spindle_enable(spindle_enable),
        tool_id=None if tool_id is None or str(tool_id).strip() == "" else str(tool_id).strip(),
        tool_object_type=(tool_object_type or "System.Object").strip() or "System.Object",
        tool_name=None if tool_name is None else str(tool_name),
    )


def build_xmsg_spec(
    *,
    text: str,
    name: Optional[str] = None,
    stop: Optional[str] = None,
    input_enabled: bool = False,
    variable_id: Optional[str] = None,
    variable_object_type: Optional[str] = None,
    variable_name: Optional[str] = None,
) -> XmsgSpec:
    """Construye la spec publica `Xmsg` con los modos de paro observados."""

    normalized_text = str(text)
    if not normalized_text:
        raise ValueError("`text` es obligatorio para Xmsg.")
    return XmsgSpec(
        text=normalized_text,
        stop=_normalize_stop_mode(stop),
        name=(name or "Xmsg").strip() or "Xmsg",
        input_enabled=bool(input_enabled),
        variable_id=None if variable_id is None or str(variable_id).strip() == "" else str(variable_id).strip(),
        variable_object_type=(variable_object_type or "").strip(),
        variable_name=None if variable_name is None else str(variable_name),
    )


def build_park_spec(
    *,
    name: Optional[str] = None,
    stop: Optional[str] = None,
    limit: Optional[str] = None,
) -> ParkSpec:
    """Construye la spec publica `Park` (aparcamiento de cabezal)."""

    return ParkSpec(
        name=(name or "Park").strip() or "Park",
        stop=_normalize_stop_mode(stop),
        limit=_normalize_park_limit(limit),
    )


def build_iso_spec(
    *,
    text: str,
    name: Optional[str] = None,
    option_parameters: Optional[str] = None,
    is_xiso: bool = False,
) -> IsoSpec:
    """Construye la spec publica `Iso` (instruccion G-code embebida en Maestro)."""

    normalized_text = str(text)
    if not normalized_text:
        raise ValueError("`text` es obligatorio para Iso.")
    return IsoSpec(
        text=normalized_text,
        name=(name or "ISO").strip() or "ISO",
        option_parameters=(option_parameters or "").strip(),
        is_xiso=bool(is_xiso),
    )


def build_workplan_spec(
    *,
    name: Optional[str] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    machinings: Optional[Sequence[MachiningSpec]] = None,
    machine_operations: Optional[Sequence[MachineOperationSpec]] = None,
) -> WorkplanSpec:
    """Construye una fase Maestro para sintesis multifase."""

    return WorkplanSpec(
        name=(name or "Setup").strip() or "Setup",
        origin_x=None if origin_x is None else float(origin_x),
        origin_y=None if origin_y is None else float(origin_y),
        origin_z=None if origin_z is None else float(origin_z),
        machinings=tuple(machinings or ()),
        machine_operations=_normalize_machine_operations(machine_operations or ()),
    )


def _normalize_xn_spec(xn: Optional[XnSpec]) -> XnSpec:
    if xn is None:
        return build_xn_spec()
    return build_xn_spec(
        name=xn.name,
        reference=xn.reference,
        speed=xn.speed,
        spindle_enable=xn.spindle_enable,
        x=xn.x,
        y=xn.y,
        tool_id=xn.tool_id,
        tool_object_type=xn.tool_object_type,
        tool_name=xn.tool_name,
    )


def _normalize_xmsg_spec(xmsg: XmsgSpec) -> XmsgSpec:
    return build_xmsg_spec(
        text=xmsg.text,
        name=xmsg.name,
        stop=xmsg.stop,
        input_enabled=xmsg.input_enabled,
        variable_id=xmsg.variable_id,
        variable_object_type=xmsg.variable_object_type,
        variable_name=xmsg.variable_name,
    )


def _normalize_park_spec(park: ParkSpec) -> ParkSpec:
    return build_park_spec(name=park.name, stop=park.stop, limit=park.limit)


def _normalize_iso_spec(iso: IsoSpec) -> IsoSpec:
    return build_iso_spec(
        text=iso.text,
        name=iso.name,
        option_parameters=iso.option_parameters,
        is_xiso=iso.is_xiso,
    )


def _normalize_machine_operations(
    machine_operations: Sequence[MachineOperationSpec],
) -> tuple[MachineOperationSpec, ...]:
    normalized: list[MachineOperationSpec] = []
    for operation in machine_operations:
        if isinstance(operation, XnSpec):
            normalized.append(_normalize_xn_spec(operation))
        elif isinstance(operation, XmsgSpec):
            normalized.append(_normalize_xmsg_spec(operation))
        elif isinstance(operation, ParkSpec):
            normalized.append(_normalize_park_spec(operation))
        elif isinstance(operation, IsoSpec):
            normalized.append(_normalize_iso_spec(operation))
        else:
            raise TypeError(f"Operacion de maquina no soportada: {type(operation).__name__}")
    return tuple(normalized)


def _normalize_workplan_spec(spec: WorkplanSpec, state: PgmxState, index: int) -> WorkplanSpec:
    default_x = state.origin_x if index == 0 else 0.0
    default_y = state.origin_y if index == 0 else 0.0
    default_z = state.origin_z
    return build_workplan_spec(
        name=spec.name,
        origin_x=default_x if spec.origin_x is None else spec.origin_x,
        origin_y=default_y if spec.origin_y is None else spec.origin_y,
        origin_z=default_z if spec.origin_z is None else spec.origin_z,
        machinings=spec.machinings,
        machine_operations=spec.machine_operations,
    )


def _normalize_workplan_specs(
    workplans: Sequence[WorkplanSpec],
    state: PgmxState,
) -> tuple[WorkplanSpec, ...]:
    return tuple(
        _normalize_workplan_spec(workplan, state, index)
        for index, workplan in enumerate(workplans)
    )


def _build_xn_step(
    step_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: XnSpec,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "Xn"},
    )
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.Xn")
    _append_blank_name(step).text = spec.name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    if spec.y is None:
        geometry_ref = _append_node(step, BASE_MODEL_NS, "GeometryID")
        _append_node(geometry_ref, UTILITY_NS, "ID", "0")
        _append_node(geometry_ref, UTILITY_NS, "ObjectType", attrib={f"{{{XSI_NS}}}nil": "true"})
        _set_xmlns(geometry_ref, "a", UTILITY_NS)
    else:
        geometry_ref = _append_object_ref(
            step,
            BASE_MODEL_NS,
            "GeometryID",
            "0",
            "System.Object",
        )
        _set_xmlns(geometry_ref, "a", UTILITY_NS)

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "Reference", spec.reference)
    _append_node(step, BASE_MODEL_NS, "Speed", _compact_number(spec.speed))
    _append_node(step, BASE_MODEL_NS, "SpindleEnable", spec.spindle_enable)

    tool_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "Tool",
        spec.tool_id or "0",
        spec.tool_object_type,
        include_name=True,
        name_text=spec.tool_name or "",
    )
    _set_xmlns(tool_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "X", _compact_number(spec.x))
    if spec.y is None:
        _append_node(step, BASE_MODEL_NS, "Y", attrib={f"{{{XSI_NS}}}nil": "true"})
    else:
        _append_node(step, BASE_MODEL_NS, "Y", _compact_number(spec.y))
    return step


def _build_xmsg_step(
    step_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: XmsgSpec,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "Xmsg"},
    )
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.Xmsg")
    _append_blank_name(step).text = spec.name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    geometry_ref = _append_node(step, BASE_MODEL_NS, "GeometryID")
    _append_node(geometry_ref, UTILITY_NS, "ID", "0")
    _append_node(geometry_ref, UTILITY_NS, "ObjectType", attrib={f"{{{XSI_NS}}}nil": "true"})
    _set_xmlns(geometry_ref, "a", UTILITY_NS)

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "IsInputEnable", "true" if spec.input_enabled else "false")
    _append_node(step, BASE_MODEL_NS, "Stop", spec.stop)
    _append_node(step, BASE_MODEL_NS, "Text", spec.text)
    if spec.variable_id:
        variable_ref = _append_object_ref(
            step,
            BASE_MODEL_NS,
            "Variable",
            spec.variable_id,
            spec.variable_object_type,
            include_name=spec.variable_name is not None,
            name_text=spec.variable_name or "",
        )
        _set_xmlns(variable_ref, "a", UTILITY_NS)
    else:
        _append_node(step, BASE_MODEL_NS, "Variable")
    return step


def _build_park_step(
    step_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: ParkSpec,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "Park"},
    )
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.Park")
    _append_blank_name(step).text = spec.name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    geometry_ref = _append_node(
        step, BASE_MODEL_NS, "GeometryID",
        attrib={f"{{{XSI_NS}}}nil": "true"},
    )
    _set_xmlns(geometry_ref, "a", UTILITY_NS)

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "Limit", spec.limit)
    _append_node(step, BASE_MODEL_NS, "Stop", spec.stop)
    return step


def _build_iso_step(
    step_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: IsoSpec,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "Iso"},
    )
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.Iso")
    _append_blank_name(step).text = spec.name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    geometry_ref = _append_node(
        step, BASE_MODEL_NS, "GeometryID",
        attrib={f"{{{XSI_NS}}}nil": "true"},
    )
    _set_xmlns(geometry_ref, "a", UTILITY_NS)

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "IsXiso", "true" if spec.is_xiso else "false")
    _append_node(step, BASE_MODEL_NS, "OptionParameters", spec.option_parameters)
    _append_node(step, BASE_MODEL_NS, "Text", spec.text)
    return step


def _append_machine_operation(
    root: ET.Element,
    elements: ET.Element,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: MachineOperationSpec,
) -> None:
    [step_id] = _reserve_ids(root, 1)
    if isinstance(spec, XnSpec):
        elements.append(_build_xn_step(step_id, workpiece_id, workpiece_object_type, spec))
        return
    if isinstance(spec, XmsgSpec):
        elements.append(_build_xmsg_step(step_id, workpiece_id, workpiece_object_type, spec))
        return
    if isinstance(spec, ParkSpec):
        elements.append(_build_park_step(step_id, workpiece_id, workpiece_object_type, spec))
        return
    if isinstance(spec, IsoSpec):
        elements.append(_build_iso_step(step_id, workpiece_id, workpiece_object_type, spec))
        return
    raise TypeError(f"Operacion de maquina no soportada: {type(spec).__name__}")


def _workpiece_ref(root: ET.Element) -> tuple[str, str]:
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    return (
        _text(workpiece, "./{*}Key/{*}ID"),
        _text(workpiece, "./{*}Key/{*}ObjectType"),
    )


def _ensure_xn_step(root: ET.Element, xn: XnSpec) -> None:
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    if elements is None:
        raise ValueError("La plantilla no contiene MainWorkplan/Elements o WorkPiece para sintetizar Xn.")

    for executable in list(elements):
        if _xsi_type(executable) == "Xn":
            elements.remove(executable)

    workpiece_id, workpiece_object_type = _workpiece_ref(root)
    _append_machine_operation(root, elements, workpiece_id, workpiece_object_type, _normalize_xn_spec(xn))


def _workplan_setup_origin_node(workplan: ET.Element) -> Optional[ET.Element]:
    return workplan.find(
        "./{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )


def _set_workplan_setup_origin(workplan: ET.Element, spec: WorkplanSpec) -> None:
    placement = _workplan_setup_origin_node(workplan)
    if placement is None:
        raise ValueError("La plantilla no contiene Setup/WorkpieceSetup/Placement.")
    _set_text(placement.find("./{*}_xP"), _compact_number(float(spec.origin_x or 0.0)))
    _set_text(placement.find("./{*}_yP"), _compact_number(float(spec.origin_y or 0.0)))
    _set_text(placement.find("./{*}_zP"), _compact_number(float(spec.origin_z or 0.0)))


def _set_workplan_name(workplan: ET.Element, name: str) -> None:
    name_node = workplan.find("./{*}Name")
    if name_node is None:
        _append_blank_name(workplan).text = name
    else:
        _set_text(name_node, name)


def _clear_workplan_elements(workplan: ET.Element) -> ET.Element:
    elements = workplan.find("./{*}Elements")
    if elements is None:
        elements = _append_node(workplan, BASE_MODEL_NS, "Elements")
    for child in list(elements):
        elements.remove(child)
    return elements


def _set_workplan_ids(workplan: ET.Element, workplan_id: str, setup_id: str) -> None:
    _set_text(workplan.find("./{*}Key/{*}ID"), workplan_id)
    setup = workplan.find("./{*}Setup")
    if setup is None:
        raise ValueError("La plantilla no contiene Setup para crear fases.")
    _set_text(setup.find("./{*}Key/{*}ID"), setup_id)


def _ensure_workplans(
    root: ET.Element,
    state: PgmxState,
    workplans: Sequence[WorkplanSpec],
    *,
    current_workplan_index: int = 0,
) -> tuple[ET.Element, ...]:
    """Configura las fases Maestro solicitadas y devuelve sus nodos XML."""

    workplans_node = root.find("./{*}Workplans")
    if workplans_node is None:
        raise ValueError("La plantilla no contiene Workplans.")
    existing_workplans = list(workplans_node.findall("./{*}MainWorkplan"))
    if not existing_workplans:
        raise ValueError("La plantilla no contiene MainWorkplan.")
    if not workplans:
        return tuple(existing_workplans)

    normalized = _normalize_workplan_specs(workplans, state)
    template = deepcopy(existing_workplans[0])
    configured: list[ET.Element] = []

    for child in list(workplans_node):
        workplans_node.remove(child)

    for index, spec in enumerate(normalized):
        workplan = existing_workplans[0] if index == 0 else deepcopy(template)
        if index == 0:
            workplan_id = _text(workplan, "./{*}Key/{*}ID")
            setup_id = _text(workplan, "./{*}Setup/{*}Key/{*}ID")
        else:
            workplan_id, setup_id = _reserve_ids(root, 2)
            _set_workplan_ids(workplan, workplan_id, setup_id)
        _set_workplan_name(workplan, spec.name)
        _set_workplan_setup_origin(workplan, spec)
        _clear_workplan_elements(workplan)
        workplans_node.append(workplan)
        configured.append(workplan)

    current_index = max(0, min(int(current_workplan_index), len(configured) - 1))
    _set_text(root.find("./{*}CurrentWorkplanIndex"), str(current_index))
    return tuple(configured)


def _append_workplan_machine_operations(
    root: ET.Element,
    workplan_nodes: Sequence[ET.Element],
    workplans: Sequence[WorkplanSpec],
) -> None:
    workpiece_id, workpiece_object_type = _workpiece_ref(root)
    for workplan, spec in zip(workplan_nodes, workplans):
        elements = workplan.find("./{*}Elements")
        if elements is None:
            elements = _append_node(workplan, BASE_MODEL_NS, "Elements")
        for operation in spec.machine_operations:
            _append_machine_operation(
                root,
                elements,
                workpiece_id,
                workpiece_object_type,
                operation,
            )


def _append_workplan_machinings(
    root: ET.Element,
    state: PgmxState,
    workplan_nodes: Sequence[ET.Element],
    hydrated_workplan_machinings: Sequence[Sequence[HydratedMachiningSpec]],
) -> None:
    for workplan, machinings in zip(workplan_nodes, hydrated_workplan_machinings):
        for machining in machinings:
            _append_hydrated_machining_to_workplan(root, state, machining, workplan)


@dataclass(frozen=True)
class PgmxSynthesisRequest:
    """Solicitud completa para sintetizar un `.pgmx` reutilizable desde la app."""

    baseline_path: Path
    output_path: Path
    piece: PgmxState
    source_pgmx_path: Optional[Path] = None
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = DEFAULT_MACHINING_ORDER
    xn: XnSpec = field(default_factory=XnSpec)
    workplans: tuple[WorkplanSpec, ...] = ()
    current_workplan_index: int = 0
    parametric_variables: tuple[ParametricVariableSpec, ...] = ()
    pieces: tuple[PieceSpec, ...] = ()


@dataclass(frozen=True)
class PgmxSynthesisResult:
    """Resultado de una sintesis ya escrita a disco."""

    output_path: Path
    piece: PgmxState
    sha256: str
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    pocket_millings: tuple[PocketMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = DEFAULT_MACHINING_ORDER
    xn: Optional[XnSpec] = None
    workplans: tuple[WorkplanSpec, ...] = ()
    current_workplan_index: int = 0
    pieces: tuple[PieceSpec, ...] = ()


def _hydrate_machining_spec(
    spec: MachiningSpec,
    source_pgmx_path: Optional[Path],
) -> HydratedMachiningSpec:
    if isinstance(spec, SlotMillingSpec):
        return _hydrate_slot_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, LineMillingSpec):
        return _hydrate_line_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, PolylineMillingSpec):
        return _hydrate_polyline_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, CircleMillingSpec):
        return _hydrate_circle_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, SquaringMillingSpec):
        return _hydrate_squaring_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, PocketMillingSpec):
        return _hydrate_pocket_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, DrillingSpec):
        return _hydrate_drilling_spec(spec, source_pgmx_path)
    if isinstance(spec, DrillingPatternSpec):
        return _hydrate_drilling_pattern_spec(spec, source_pgmx_path)
    raise TypeError(f"Spec de mecanizado no soportado: {type(spec).__name__}")


def _append_hydrated_machining(
    root: ET.Element,
    state: PgmxState,
    spec: HydratedMachiningSpec,
) -> None:
    if isinstance(spec, _HydratedLineMillingSpec):
        _append_line_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedSlotMillingSpec):
        _append_slot_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedPolylineMillingSpec):
        _append_polyline_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedCircleMillingSpec):
        _append_circle_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedSquaringMillingSpec):
        _append_squaring_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedPocketMillingSpec):
        _append_pocket_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedDrillingSpec):
        _append_drilling(root, state, spec)
        return
    if isinstance(spec, _HydratedDrillingPatternSpec):
        _append_drilling_pattern(root, state, spec)
        return
    raise TypeError(f"Spec hidratado no soportado: {type(spec).__name__}")


def _append_hydrated_machining_to_workplan(
    root: ET.Element,
    state: PgmxState,
    spec: HydratedMachiningSpec,
    workplan: ET.Element,
) -> None:
    default_elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    if default_elements is None:
        raise ValueError("La plantilla no contiene MainWorkplan/Elements.")

    target_elements = workplan.find("./{*}Elements")
    if target_elements is None:
        target_elements = _append_node(workplan, BASE_MODEL_NS, "Elements")

    previous_count = len(default_elements)
    _append_hydrated_machining(root, state, spec)
    appended_steps = list(default_elements)[previous_count:]
    if not appended_steps:
        raise ValueError("El mecanizado no agrego ningun working step al workplan.")

    if target_elements is default_elements:
        return
    for step in appended_steps:
        default_elements.remove(step)
        target_elements.append(step)


def _split_hydrated_machinings(
    specs: Sequence[HydratedMachiningSpec],
) -> tuple[
    list[_HydratedLineMillingSpec],
    list[_HydratedSlotMillingSpec],
    list[_HydratedPolylineMillingSpec],
    list[_HydratedCircleMillingSpec],
    list[_HydratedSquaringMillingSpec],
    list[_HydratedPocketMillingSpec],
    list[_HydratedDrillingSpec],
    list[_HydratedDrillingPatternSpec],
]:
    line_millings: list[_HydratedLineMillingSpec] = []
    slot_millings: list[_HydratedSlotMillingSpec] = []
    polyline_millings: list[_HydratedPolylineMillingSpec] = []
    circle_millings: list[_HydratedCircleMillingSpec] = []
    squaring_millings: list[_HydratedSquaringMillingSpec] = []
    pocket_millings: list[_HydratedPocketMillingSpec] = []
    drillings: list[_HydratedDrillingSpec] = []
    drilling_patterns: list[_HydratedDrillingPatternSpec] = []
    for spec in specs:
        if isinstance(spec, _HydratedLineMillingSpec):
            line_millings.append(spec)
        elif isinstance(spec, _HydratedSlotMillingSpec):
            slot_millings.append(spec)
        elif isinstance(spec, _HydratedPolylineMillingSpec):
            polyline_millings.append(spec)
        elif isinstance(spec, _HydratedCircleMillingSpec):
            circle_millings.append(spec)
        elif isinstance(spec, _HydratedSquaringMillingSpec):
            squaring_millings.append(spec)
        elif isinstance(spec, _HydratedPocketMillingSpec):
            pocket_millings.append(spec)
        elif isinstance(spec, _HydratedDrillingSpec):
            drillings.append(spec)
        elif isinstance(spec, _HydratedDrillingPatternSpec):
            drilling_patterns.append(spec)
    return (
        line_millings,
        slot_millings,
        polyline_millings,
        circle_millings,
        squaring_millings,
        pocket_millings,
        drillings,
        drilling_patterns,
    )


def _normalize_machining_order(value: Optional[Sequence[str]]) -> tuple[str, ...]:
    default_order = DEFAULT_MACHINING_ORDER
    aliases = {
        "lines": "line",
        "line_milling": "line",
        "line_millings": "line",
        "slots": "slot",
        "slot_milling": "slot",
        "slot_millings": "slot",
        "canal": "slot",
        "canales": "slot",
        "ranura": "slot",
        "ranuras": "slot",
        "polyline_milling": "polyline",
        "polyline_millings": "polyline",
        "division": "polyline",
        "divisions": "polyline",
        "cutting": "polyline",
        "circle_milling": "circle",
        "circle_millings": "circle",
        "squaring_milling": "squaring",
        "squaring_millings": "squaring",
        "square": "squaring",
        "pocket": "pocket",
        "pockets": "pocket",
        "pocket_milling": "pocket",
        "pocket_millings": "pocket",
        "vaciado": "pocket",
        "vaciados": "pocket",
        "drilling": "drilling",
        "drilling_millings": "drilling",
        "drilling_pattern": "drilling_pattern",
        "drilling_patterns": "drilling_pattern",
        "hole_pattern": "drilling_pattern",
        "hole_patterns": "drilling_pattern",
        "pattern": "drilling_pattern",
        "patterns": "drilling_pattern",
        "patron": "drilling_pattern",
        "patrones": "drilling_pattern",
        "repeticion": "drilling_pattern",
        "repeticiones": "drilling_pattern",
    }
    ordered: list[str] = []
    for raw_item in value or default_order:
        normalized = aliases.get(str(raw_item or "").strip().lower(), str(raw_item or "").strip().lower())
        if normalized not in default_order or normalized in ordered:
            continue
        ordered.append(normalized)
    for item in default_order:
        if item not in ordered:
            ordered.append(item)
    return tuple(ordered)


def _normalize_execution_fields(value: Optional[str]) -> str:
    raw = (value or "HG").strip().upper().replace(" ", "")
    if not raw:
        return "HG"
    if any(letter not in "ABCDEFGH" for letter in raw):
        raise ValueError(
            "ExecutionFields invalido. Use letras entre A y H, por ejemplo: A, EF o HG."
        )
    if len(set(raw)) != len(raw):
        raise ValueError("ExecutionFields invalido. No debe repetir letras.")
    return raw


def _validate_tool_sinking_lengths(
    state: PgmxState,
    line_millings: Sequence[_HydratedLineMillingSpec],
    slot_millings: Sequence[_HydratedSlotMillingSpec],
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
    circle_millings: Sequence[_HydratedCircleMillingSpec],
    squaring_millings: Sequence[_HydratedSquaringMillingSpec],
    pocket_millings: Sequence[_HydratedPocketMillingSpec],
    drillings: Sequence[_HydratedDrillingSpec],
    drilling_patterns: Sequence[_HydratedDrillingPatternSpec] = (),
) -> None:
    """Aplica la validacion de `sinking_length` a todos los mecanizados del request."""

    tool_catalog = _load_tool_catalog()
    for spec in line_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in slot_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in polyline_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in circle_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in squaring_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in pocket_millings:
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in drillings:
        _validate_tool_type_for_drilling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_drilling_spec(state, spec, tool_catalog)
    for spec in drilling_patterns:
        _validate_tool_type_for_drilling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_drilling_spec(state, spec, tool_catalog)


# ============================================================================
# Public read/build API
# ============================================================================

def read_pgmx_state(path: Path) -> PgmxState:
    """Lee un baseline Maestro y devuelve el estado basico de pieza, origen y area.

    No interpreta mecanizados. Sirve para reutilizar dimensiones reales y para
    tomar un baseline o un `source_pgmx_path` como punto de partida.
    """

    root, _, _ = _load_pgmx_container(path)

    variables = root.find("./{*}Variables")
    variable_values: dict[str, float] = {}
    if variables is not None:
        for variable in list(variables):
            name = _text(variable, "./{*}Name").lower()
            if not name:
                continue
            variable_values[name] = _safe_float(_text(variable, "./{*}Value"), 0.0)

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError(f"El archivo '{path}' no contiene WorkPiece.")

    piece_name = _text(workpiece, "./{*}Name", path.stem) or path.stem
    length = variable_values.get("dx1", _safe_float(_text(workpiece, "./{*}Length"), 0.0))
    width = variable_values.get("dy1", _safe_float(_text(workpiece, "./{*}Width"), 0.0))
    depth = variable_values.get("dz1", _safe_float(_text(workpiece, "./{*}Depth"), 0.0))

    setup_placement = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )
    if setup_placement is None:
        raise ValueError(f"El archivo '{path}' no contiene WorkpieceSetup/Placement.")

    origin_x = _safe_float(_text(setup_placement, "./{*}_xP"), 0.0)
    origin_y = _safe_float(_text(setup_placement, "./{*}_yP"), 0.0)
    origin_z = _safe_float(_text(setup_placement, "./{*}_zP"), 0.0)
    execution_fields = _normalize_execution_fields(
        _text(root, "./{*}MachiningParameters/{*}ExecutionFields", "HG")
    )

    return PgmxState(
        piece_name=piece_name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        execution_fields=execution_fields,
    )


def _merge_state(
    base_state: PgmxState,
    piece_name: Optional[str],
    length: Optional[float],
    width: Optional[float],
    depth: Optional[float],
    origin_x: Optional[float],
    origin_y: Optional[float],
    origin_z: Optional[float],
    execution_fields: Optional[str],
) -> PgmxState:
    return PgmxState(
        piece_name=base_state.piece_name if piece_name is None else piece_name,
        length=base_state.length if length is None else length,
        width=base_state.width if width is None else width,
        depth=base_state.depth if depth is None else depth,
        origin_x=base_state.origin_x if origin_x is None else origin_x,
        origin_y=base_state.origin_y if origin_y is None else origin_y,
        origin_z=base_state.origin_z if origin_z is None else origin_z,
        execution_fields=(
            base_state.execution_fields
            if execution_fields is None
            else _normalize_execution_fields(execution_fields)
        ),
    )


def _apply_piece_state(root: ET.Element, state: PgmxState) -> None:
    variables = root.find("./{*}Variables")
    if variables is not None:
        for variable in list(variables):
            value_node = variable.find("./{*}Value")
            _set_xmlns(value_node, "b", XSD_NS)
            name = _text(variable, "./{*}Name").lower()
            if name == "dx1":
                _set_text(value_node, _compact_number(state.length))
            elif name == "dy1":
                _set_text(value_node, _compact_number(state.width))
            elif name == "dz1":
                _set_text(value_node, _compact_number(state.depth))

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    _set_text(workpiece.find("./{*}Name"), state.piece_name)
    _set_text(workpiece.find("./{*}Length"), _compact_number(state.length))
    _set_text(workpiece.find("./{*}Width"), _compact_number(state.width))
    _set_text(workpiece.find("./{*}Depth"), _compact_number(state.depth))
    geometry = workpiece.find("./{*}Geometry")
    if geometry is not None:
        _set_text(geometry.find("./{*}Length"), _compact_number(state.length))
        _set_text(geometry.find("./{*}Width"), _compact_number(state.width))
        _set_text(geometry.find("./{*}Depth"), _compact_number(state.depth))

    plane_specs = {
        "Top": (state.length, state.width, 0.0, 0.0, state.depth),
        "Bottom": (state.length, state.width, 0.0, state.width, 0.0),
        "Right": (state.width, state.depth, state.length, 0.0, 0.0),
        "Left": (state.width, state.depth, 0.0, state.width, 0.0),
        "Front": (state.length, state.depth, 0.0, 0.0, 0.0),
        "Back": (state.length, state.depth, state.length, state.width, 0.0),
    }
    planes = root.find("./{*}Planes")
    if planes is not None:
        for plane in list(planes):
            plane_type = _text(plane, "./{*}Type") or _text(plane, "./{*}Name")
            spec = plane_specs.get(plane_type)
            if spec is None:
                continue
            x_dimension, y_dimension, x_origin, y_origin, z_origin = spec
            _set_text(plane.find("./{*}XDimension"), _compact_number(x_dimension))
            _set_text(plane.find("./{*}YDimension"), _compact_number(y_dimension))
            placement = plane.find("./{*}Placement")
            if placement is None:
                continue
            _set_text(placement.find("./{*}_xP"), _compact_number(x_origin))
            _set_text(placement.find("./{*}_yP"), _compact_number(y_origin))
            _set_text(placement.find("./{*}_zP"), _compact_number(z_origin))

    setup_placement = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )
    if setup_placement is None:
        raise ValueError("La plantilla no contiene WorkpieceSetup/Placement.")
    _set_text(setup_placement.find("./{*}_xP"), _compact_number(state.origin_x))
    _set_text(setup_placement.find("./{*}_yP"), _compact_number(state.origin_y))
    _set_text(setup_placement.find("./{*}_zP"), _compact_number(state.origin_z))

    execution_fields_node = root.find("./{*}MachiningParameters/{*}ExecutionFields")
    if execution_fields_node is None:
        raise ValueError("La plantilla no contiene MachiningParameters/ExecutionFields.")
    _set_text(execution_fields_node, state.execution_fields)


def _apply_line_millings(
    root: ET.Element,
    state: PgmxState,
    line_millings: Sequence[_HydratedLineMillingSpec],
) -> None:
    for line_milling in line_millings:
        _append_line_milling(root, state, line_milling)


def _apply_slot_millings(
    root: ET.Element,
    state: PgmxState,
    slot_millings: Sequence[_HydratedSlotMillingSpec],
) -> None:
    for slot_milling in slot_millings:
        _append_slot_milling(root, state, slot_milling)


def _apply_polyline_millings(
    root: ET.Element,
    state: PgmxState,
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
) -> None:
    for polyline_milling in polyline_millings:
        _append_polyline_milling(root, state, polyline_milling)


def _apply_circle_millings(
    root: ET.Element,
    state: PgmxState,
    circle_millings: Sequence[_HydratedCircleMillingSpec],
) -> None:
    for circle_milling in circle_millings:
        _append_circle_milling(root, state, circle_milling)


def _apply_squaring_millings(
    root: ET.Element,
    state: PgmxState,
    squaring_millings: Sequence[_HydratedSquaringMillingSpec],
) -> None:
    for squaring_milling in squaring_millings:
        _append_squaring_milling(root, state, squaring_milling)


def _apply_drillings(
    root: ET.Element,
    state: PgmxState,
    drillings: Sequence[_HydratedDrillingSpec],
) -> None:
    # Maestro guarda consistentemente los taladros multicara agrupados por
    # plano. Mantener ese orden reduce diferencias contra los ejemplos manuales
    # y evita mezclar caras arbitrariamente segun el orden de entrada.
    plane_priority = {
        "Top": 0,
        "Front": 1,
        "Back": 2,
        "Left": 3,
        "Right": 4,
    }
    ordered_drillings = sorted(
        enumerate(drillings),
        key=lambda item: (plane_priority.get(item[1].plane_name, 99), item[0]),
    )
    for _, drilling in ordered_drillings:
        _append_drilling(root, state, drilling)


def _drilling_plane_priority(plane_name: str) -> int:
    plane_priority = {
        "Top": 0,
        "Front": 1,
        "Back": 2,
        "Left": 3,
        "Right": 4,
    }
    return plane_priority.get(plane_name, 99)


def _apply_drilling_patterns(
    root: ET.Element,
    state: PgmxState,
    drilling_patterns: Sequence[_HydratedDrillingPatternSpec],
) -> None:
    ordered_drilling_patterns = sorted(
        enumerate(drilling_patterns),
        key=lambda item: (_drilling_plane_priority(item[1].plane_name), item[0]),
    )
    for _, drilling_pattern in ordered_drilling_patterns:
        _append_drilling_pattern(root, state, drilling_pattern)


def _apply_pocket_millings(
    root: ET.Element,
    state: PgmxState,
    pocket_millings: Sequence[_HydratedPocketMillingSpec],
) -> None:
    for pocket_milling in pocket_millings:
        _append_pocket_milling(root, state, pocket_milling)


# ============================================================================
# Multi-piece synthesis helpers
# ============================================================================

def _piece_to_state(piece: PieceSpec, execution_fields: str) -> PgmxState:
    return PgmxState(
        piece_name=piece.name,
        length=piece.length,
        width=piece.width,
        depth=piece.depth,
        origin_x=piece.origin_x,
        origin_y=piece.origin_y,
        origin_z=piece.origin_z,
        execution_fields=execution_fields,
    )


def _synthesize_piece_machinings(
    root: ET.Element,
    piece: PieceSpec,
    workpiece_id: str,
    workpiece_object_type: str,
    source_pgmx_path: Optional[Path],
    machining_order: tuple[str, ...],
    execution_fields: str,
) -> None:
    """Hidratan, validan y aplican todos los mecanizados de una PieceSpec."""
    state = _piece_to_state(piece, execution_fields)

    hydrated_line_millings = [
        _hydrate_line_milling_spec(s, source_pgmx_path) for s in piece.line_millings
    ]
    hydrated_slot_millings = [
        _hydrate_slot_milling_spec(s, source_pgmx_path) for s in piece.slot_millings
    ]
    hydrated_polyline_millings = [
        _hydrate_polyline_milling_spec(s, source_pgmx_path) for s in piece.polyline_millings
    ]
    hydrated_circle_millings = [
        _hydrate_circle_milling_spec(s, source_pgmx_path) for s in piece.circle_millings
    ]
    hydrated_squaring_millings = [
        _hydrate_squaring_milling_spec(s, source_pgmx_path) for s in piece.squaring_millings
    ]
    hydrated_pocket_millings = [
        _hydrate_pocket_milling_spec(s, source_pgmx_path) for s in piece.pocket_millings
    ]
    hydrated_drillings = [
        _hydrate_drilling_spec(s, source_pgmx_path) for s in piece.drillings
    ]
    hydrated_drilling_patterns = [
        _hydrate_drilling_pattern_spec(s, source_pgmx_path) for s in piece.drilling_patterns
    ]
    hydrated_ordered = [
        _hydrate_machining_spec(s, source_pgmx_path) for s in piece.ordered_machinings
    ]
    (
        ordered_line, ordered_slot, ordered_polyline, ordered_circle,
        ordered_squaring, ordered_pocket, ordered_drilling, ordered_pattern,
    ) = _split_hydrated_machinings(hydrated_ordered)

    _validate_tool_sinking_lengths(
        state,
        hydrated_line_millings + ordered_line,
        hydrated_slot_millings + ordered_slot,
        hydrated_polyline_millings + ordered_polyline,
        hydrated_circle_millings + ordered_circle,
        hydrated_squaring_millings + ordered_squaring,
        hydrated_pocket_millings + ordered_pocket,
        hydrated_drillings + ordered_drilling,
        hydrated_drilling_patterns + ordered_pattern,
    )

    apply_group = {
        "line":             lambda: _apply_line_millings(root, state, hydrated_line_millings),
        "slot":             lambda: _apply_slot_millings(root, state, hydrated_slot_millings),
        "polyline":         lambda: _apply_polyline_millings(root, state, hydrated_polyline_millings),
        "circle":           lambda: _apply_circle_millings(root, state, hydrated_circle_millings),
        "squaring":         lambda: _apply_squaring_millings(root, state, hydrated_squaring_millings),
        "pocket":           lambda: _apply_pocket_millings(root, state, hydrated_pocket_millings),
        "drilling":         lambda: _apply_drillings(root, state, hydrated_drillings),
        "drilling_pattern": lambda: _apply_drilling_patterns(root, state, hydrated_drilling_patterns),
    }

    with _active_workpiece_ctx(root, workpiece_id):
        for spec in hydrated_ordered:
            _append_hydrated_machining(root, state, spec)
        for group_name in machining_order:
            apply_group[group_name]()

    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    if elements is None:
        raise ValueError("La plantilla no contiene MainWorkplan/Elements.")
    for op in piece.machine_operations:
        _append_machine_operation(root, elements, workpiece_id, workpiece_object_type, op)

    _apply_parametric_variables(root, piece.parametric_variables)


# ============================================================================
# Public execution API
# ============================================================================

def build_synthesis_request(
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    *,
    source_pgmx_path: Optional[Path] = None,
    piece: Optional[PgmxState] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    execution_fields: Optional[str] = None,
    line_millings: Optional[Sequence[LineMillingSpec]] = None,
    slot_millings: Optional[Sequence[SlotMillingSpec]] = None,
    polyline_millings: Optional[Sequence[PolylineMillingSpec]] = None,
    circle_millings: Optional[Sequence[CircleMillingSpec]] = None,
    squaring_millings: Optional[Sequence[SquaringMillingSpec]] = None,
    pocket_millings: Optional[Sequence[PocketMillingSpec]] = None,
    drillings: Optional[Sequence[DrillingSpec]] = None,
    drilling_patterns: Optional[Sequence[DrillingPatternSpec]] = None,
    ordered_machinings: Optional[Sequence[MachiningSpec]] = None,
    machining_order: Optional[Sequence[str]] = None,
    xn: Optional[XnSpec] = None,
    workplans: Optional[Sequence[WorkplanSpec]] = None,
    current_workplan_index: int = 0,
    parametric_variables: Optional[Sequence[ParametricVariableSpec]] = None,
    pieces: Optional[Sequence[PieceSpec]] = None,
) -> PgmxSynthesisRequest:
    """Arma una solicitud reusable de sintesis para el flujo principal.

    Orden recomendado de uso:
    1. leer o definir la pieza
    2. construir `LineMillingSpec`, `SlotMillingSpec`, `PolylineMillingSpec`,
       `CircleMillingSpec`, `SquaringMillingSpec`, `DrillingSpec` y
       `DrillingPatternSpec`, y
       opcionalmente `XnSpec`
    3. construir el request
    4. ejecutar `synthesize_request(...)`

    Soporte de contenedores baseline:
    - `baseline_path`: `.pgmx`, `Pieza.xml` o carpeta que contenga `Pieza.xml`
      Si no se indica, usa `DEFAULT_BASELINE_DIR`.
    - `source_pgmx_path`: `.pgmx`, `Pieza.xml` o carpeta usada como plantilla de serializacion
    """

    if output_path is None:
        raise ValueError("`output_path` es obligatorio para construir un `PgmxSynthesisRequest`.")

    effective_baseline_path = Path(baseline_path) if baseline_path is not None else DEFAULT_BASELINE_DIR
    effective_output_path = Path(output_path)

    base_piece = piece or (
        read_pgmx_state(source_pgmx_path) if source_pgmx_path else read_pgmx_state(effective_baseline_path)
    )
    effective_execution_fields = execution_fields
    if effective_execution_fields is None and piece is None:
        effective_execution_fields = "HG"
    target_piece = _merge_state(
        base_piece,
        piece_name,
        length,
        width,
        depth,
        origin_x,
        origin_y,
        origin_z,
        effective_execution_fields,
    )
    return PgmxSynthesisRequest(
        baseline_path=effective_baseline_path,
        output_path=effective_output_path,
        piece=target_piece,
        source_pgmx_path=source_pgmx_path,
        line_millings=tuple(line_millings or ()),
        slot_millings=tuple(slot_millings or ()),
        polyline_millings=tuple(polyline_millings or ()),
        circle_millings=tuple(circle_millings or ()),
        squaring_millings=tuple(squaring_millings or ()),
        pocket_millings=tuple(pocket_millings or ()),
        drillings=tuple(drillings or ()),
        drilling_patterns=tuple(drilling_patterns or ()),
        ordered_machinings=tuple(ordered_machinings or ()),
        machining_order=_normalize_machining_order(machining_order),
        xn=_normalize_xn_spec(xn),
        workplans=_normalize_workplan_specs(tuple(workplans or ()), target_piece),
        current_workplan_index=max(0, int(current_workplan_index)),
        parametric_variables=tuple(parametric_variables or ()),
        pieces=tuple(pieces or ()),
    )


def _synthesize_multi_piece(request: PgmxSynthesisRequest) -> PgmxSynthesisResult:
    """Ejecuta la rama multi-pieza de synthesize_request."""
    if request.workplans:
        raise ValueError(
            "Los campos `workplans` y `pieces` son mutuamente excluyentes."
        )
    pieces = request.pieces
    if not pieces:
        raise ValueError("_synthesize_multi_piece requiere al menos una pieza.")

    baseline_root, baseline_entries, _ = _load_pgmx_container(request.baseline_path)
    execution_fields = request.piece.execution_fields
    machining_order = _normalize_machining_order(request.machining_order)

    # Piece 1: update the existing WorkPiece, variables, planes and Setup origin.
    piece1 = pieces[0]
    state1 = _piece_to_state(piece1, execution_fields)
    _apply_piece_state(baseline_root, state1)

    # Piece 1 workpiece reference (already in the baseline).
    wp1 = baseline_root.find("./{*}Workpieces/{*}WorkPiece")
    if wp1 is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    piece_refs: list[tuple[str, str]] = [
        (_text(wp1, "./{*}Key/{*}ID"), _text(wp1, "./{*}Key/{*}ObjectType"))
    ]

    # Pieces 2..N: add WorkPiece, variables, expressions, planes, WorkpieceSetup.
    for piece_index, piece in enumerate(pieces[1:], start=2):
        wp_id, wp_ot = _add_piece_to_xml(
            baseline_root,
            piece_index,
            piece.name,
            piece.length,
            piece.width,
            piece.depth,
            piece.origin_x,
            piece.origin_y,
            piece.origin_z,
        )
        piece_refs.append((wp_id, wp_ot))

    # Apply machinings for each piece in order.
    for piece, (wp_id, wp_ot) in zip(pieces, piece_refs):
        _synthesize_piece_machinings(
            baseline_root,
            piece,
            wp_id,
            wp_ot,
            request.source_pgmx_path,
            machining_order,
            execution_fields,
        )

    xml_bytes = _finalize_synthesized_pgmx_xml_bytes(
        ET.tostring(
            baseline_root,
            encoding="utf-8",
            xml_declaration=request.source_pgmx_path is None,
        )
    )
    _write_pgmx_zip(
        output_path=request.output_path,
        xml_bytes=xml_bytes,
        template_entries=baseline_entries,
        xml_entry_name=f"{request.output_path.stem}.xml",
    )
    return PgmxSynthesisResult(
        output_path=request.output_path,
        piece=state1,
        sha256=hashlib.sha256(request.output_path.read_bytes()).hexdigest(),
        pieces=pieces,
    )


def synthesize_request(request: PgmxSynthesisRequest) -> PgmxSynthesisResult:
    """Ejecuta una solicitud de sintesis y escribe el `.pgmx` resultante.

    Esta es la funcion principal para el flujo programatico.
    """

    if request.pieces:
        return _synthesize_multi_piece(request)

    baseline_root, baseline_entries, _ = _load_pgmx_container(request.baseline_path)
    hydrated_line_millings = [
        _hydrate_line_milling_spec(line_milling, request.source_pgmx_path)
        for line_milling in request.line_millings
    ]
    hydrated_slot_millings = [
        _hydrate_slot_milling_spec(slot_milling, request.source_pgmx_path)
        for slot_milling in request.slot_millings
    ]
    hydrated_polyline_millings = [
        _hydrate_polyline_milling_spec(polyline_milling, request.source_pgmx_path)
        for polyline_milling in request.polyline_millings
    ]
    hydrated_circle_millings = [
        _hydrate_circle_milling_spec(circle_milling, request.source_pgmx_path)
        for circle_milling in request.circle_millings
    ]
    hydrated_squaring_millings = [
        _hydrate_squaring_milling_spec(squaring_milling, request.source_pgmx_path)
        for squaring_milling in request.squaring_millings
    ]
    hydrated_pocket_millings = [
        _hydrate_pocket_milling_spec(pocket_milling, request.source_pgmx_path)
        for pocket_milling in request.pocket_millings
    ]
    hydrated_drillings = [
        _hydrate_drilling_spec(drilling, request.source_pgmx_path)
        for drilling in request.drillings
    ]
    hydrated_drilling_patterns = [
        _hydrate_drilling_pattern_spec(drilling_pattern, request.source_pgmx_path)
        for drilling_pattern in request.drilling_patterns
    ]
    hydrated_ordered_machinings = [
        _hydrate_machining_spec(spec, request.source_pgmx_path)
        for spec in request.ordered_machinings
    ]
    (
        ordered_line_millings,
        ordered_slot_millings,
        ordered_polyline_millings,
        ordered_circle_millings,
        ordered_squaring_millings,
        ordered_pocket_millings,
        ordered_drillings,
        ordered_drilling_patterns,
    ) = _split_hydrated_machinings(hydrated_ordered_machinings)
    normalized_xn = _normalize_xn_spec(request.xn)
    normalized_workplans = _normalize_workplan_specs(request.workplans, request.piece)
    hydrated_workplan_machinings = tuple(
        tuple(_hydrate_machining_spec(spec, request.source_pgmx_path) for spec in workplan.machinings)
        for workplan in normalized_workplans
    )
    flattened_workplan_machinings = [
        spec
        for workplan_machinings in hydrated_workplan_machinings
        for spec in workplan_machinings
    ]
    (
        workplan_line_millings,
        workplan_slot_millings,
        workplan_polyline_millings,
        workplan_circle_millings,
        workplan_squaring_millings,
        workplan_pocket_millings,
        workplan_drillings,
        workplan_drilling_patterns,
    ) = _split_hydrated_machinings(flattened_workplan_machinings)
    _validate_tool_sinking_lengths(
        request.piece,
        hydrated_line_millings + ordered_line_millings + workplan_line_millings,
        hydrated_slot_millings + ordered_slot_millings + workplan_slot_millings,
        hydrated_polyline_millings + ordered_polyline_millings + workplan_polyline_millings,
        hydrated_circle_millings + ordered_circle_millings + workplan_circle_millings,
        hydrated_squaring_millings + ordered_squaring_millings + workplan_squaring_millings,
        hydrated_pocket_millings + ordered_pocket_millings + workplan_pocket_millings,
        hydrated_drillings + ordered_drillings + workplan_drillings,
        hydrated_drilling_patterns + ordered_drilling_patterns + workplan_drilling_patterns,
    )

    _apply_piece_state(baseline_root, request.piece)
    _apply_parametric_variables(baseline_root, request.parametric_variables)
    workplan_nodes: tuple[ET.Element, ...] = ()
    if normalized_workplans:
        workplan_nodes = _ensure_workplans(
            baseline_root,
            request.piece,
            normalized_workplans,
            current_workplan_index=request.current_workplan_index,
        )
    for spec in hydrated_ordered_machinings:
        _append_hydrated_machining(baseline_root, request.piece, spec)
    apply_group = {
        "line": lambda: _apply_line_millings(
            baseline_root,
            request.piece,
            hydrated_line_millings,
        ),
        "slot": lambda: _apply_slot_millings(
            baseline_root,
            request.piece,
            hydrated_slot_millings,
        ),
        "polyline": lambda: _apply_polyline_millings(
            baseline_root,
            request.piece,
            hydrated_polyline_millings,
        ),
        "circle": lambda: _apply_circle_millings(
            baseline_root,
            request.piece,
            hydrated_circle_millings,
        ),
        "squaring": lambda: _apply_squaring_millings(
            baseline_root,
            request.piece,
            hydrated_squaring_millings,
        ),
        "pocket": lambda: _apply_pocket_millings(
            baseline_root,
            request.piece,
            hydrated_pocket_millings,
        ),
        "drilling": lambda: _apply_drillings(
            baseline_root,
            request.piece,
            hydrated_drillings,
        ),
        "drilling_pattern": lambda: _apply_drilling_patterns(
            baseline_root,
            request.piece,
            hydrated_drilling_patterns,
        ),
    }
    for group_name in _normalize_machining_order(request.machining_order):
        apply_group[group_name]()
    if normalized_workplans:
        _append_workplan_machinings(
            baseline_root,
            request.piece,
            workplan_nodes,
            hydrated_workplan_machinings,
        )
        _append_workplan_machine_operations(baseline_root, workplan_nodes, normalized_workplans)
    else:
        _ensure_xn_step(baseline_root, normalized_xn)

    xml_bytes = _finalize_synthesized_pgmx_xml_bytes(
        ET.tostring(
            baseline_root,
            encoding="utf-8",
            xml_declaration=request.source_pgmx_path is None,
        )
    )
    _write_pgmx_zip(
        output_path=request.output_path,
        xml_bytes=xml_bytes,
        template_entries=baseline_entries,
        xml_entry_name=f"{request.output_path.stem}.xml",
    )
    return PgmxSynthesisResult(
        output_path=request.output_path,
        piece=request.piece,
        sha256=hashlib.sha256(request.output_path.read_bytes()).hexdigest(),
        line_millings=request.line_millings,
        slot_millings=request.slot_millings,
        polyline_millings=request.polyline_millings,
        circle_millings=request.circle_millings,
        squaring_millings=request.squaring_millings,
        pocket_millings=request.pocket_millings,
        drillings=request.drillings,
        drilling_patterns=request.drilling_patterns,
        ordered_machinings=request.ordered_machinings,
        machining_order=_normalize_machining_order(request.machining_order),
        xn=normalized_xn if not normalized_workplans else None,
        workplans=normalized_workplans,
        current_workplan_index=(
            max(0, min(int(request.current_workplan_index), len(normalized_workplans) - 1))
            if normalized_workplans
            else 0
        ),
    )


def synthesize_pgmx(
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    source_pgmx_path: Optional[Path] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    line_milling: Optional[LineMillingSpec] = None,
    slot_milling: Optional[SlotMillingSpec] = None,
    polyline_milling: Optional[PolylineMillingSpec] = None,
    circle_milling: Optional[CircleMillingSpec] = None,
    squaring_milling: Optional[SquaringMillingSpec] = None,
    drilling: Optional[DrillingSpec] = None,
    drilling_pattern: Optional[DrillingPatternSpec] = None,
    xn: Optional[XnSpec] = None,
    workplans: Optional[Sequence[WorkplanSpec]] = None,
    current_workplan_index: int = 0,
    execution_fields: Optional[str] = None,
) -> PgmxState:
    """Wrapper de compatibilidad para el flujo historico basado en argumentos sueltos.

    Para codigo nuevo conviene preferir `build_synthesis_request(...)` y
    `synthesize_request(...)`.
    """

    request = build_synthesis_request(
        baseline_path=baseline_path,
        output_path=output_path,
        source_pgmx_path=source_pgmx_path,
        piece_name=piece_name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        execution_fields=execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
        slot_millings=[slot_milling] if slot_milling is not None else (),
        polyline_millings=[polyline_milling] if polyline_milling is not None else (),
        circle_millings=[circle_milling] if circle_milling is not None else (),
        squaring_millings=[squaring_milling] if squaring_milling is not None else (),
        drillings=[drilling] if drilling is not None else (),
        drilling_patterns=[drilling_pattern] if drilling_pattern is not None else (),
        xn=xn,
        workplans=workplans,
        current_workplan_index=current_workplan_index,
    )
    return synthesize_request(request).piece
