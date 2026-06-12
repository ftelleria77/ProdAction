"""XML primitives shared by PGMX synthesis modules."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

PGMX_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.ProjectModule"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
BASE_MODEL_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"
MILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Milling"
DRILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Drilling"
PATTERNS_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Patterns"
GEOMETRY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Geometry"
STRATEGY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Strategy"
UTILITY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Utility"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
ARRAYS_NS = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
PARAMETRIC_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Parametrics"

__all__ = [
    "ARRAYS_NS",
    "BASE_MODEL_NS",
    "DRILLING_NS",
    "GEOMETRY_NS",
    "MILLING_NS",
    "PARAMETRIC_NS",
    "PATTERNS_NS",
    "PGMX_NS",
    "STRATEGY_NS",
    "UTILITY_NS",
    "XSD_NS",
    "XSI_NS",
    "register_pgmx_namespaces",
    "_append_blank_name",
    "_append_key",
    "_append_node",
    "_append_object_ref",
    "_append_reference_key",
    "_build_depth_expression",
    "_build_point_geometry",
    "_build_property_expression",
    "_build_working_step",
    "_compact_number",
    "_find_plane_ref",
    "_id_counter",
    "_qname",
    "_raw_text",
    "_reserve_ids",
    "_safe_bool",
    "_safe_float",
    "_set_text",
    "_set_xmlns",
    "_strip_namespace",
    "_text",
    "_xsi_type",
]


def register_pgmx_namespaces() -> None:
    """Register the namespace prefixes used by Maestro PGMX XML."""

    ET.register_namespace("", PGMX_NS)
    ET.register_namespace("i", XSI_NS)


def _strip_namespace(tag: str) -> str:
    """Devuelve el nombre local de un tag XML, sin su namespace."""

    return tag.split("}", 1)[-1] if "}" in tag else tag


def _compact_number(value: float) -> str:
    """Serializa un numero con el formato compacto que usamos en PGMX."""

    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.6f}".rstrip("0").rstrip(".")


def _xsi_type(element: ET.Element) -> str:
    """Lee el `xsi:type` de un nodo XML sin depender del prefijo exacto."""

    for key, value in element.attrib.items():
        if _strip_namespace(key).lower() == "type":
            return value or ""
    return ""


def _set_text(element: Optional[ET.Element], value) -> None:
    """Asigna texto a un nodo XML, tolerando `None`."""

    if element is not None:
        element.text = "" if value is None else str(value)


def _set_xmlns(element: Optional[ET.Element], prefix: str, uri: str) -> None:
    """Inyecta una declaracion `xmlns:prefix` en un nodo si existe."""

    if element is not None:
        element.set(f"xmlns:{prefix}", uri)


def _qname(namespace: str, local_name: str) -> str:
    return f"{{{namespace}}}{local_name}"


def _append_node(
    parent: ET.Element,
    namespace: str,
    local_name: str,
    text: Optional[str] = None,
    attrib: Optional[dict[str, str]] = None,
) -> ET.Element:
    node = ET.SubElement(parent, _qname(namespace, local_name), attrib or {})
    if text is not None:
        node.text = text
    return node


def _append_key(parent: ET.Element, key_id: str, object_type: str) -> ET.Element:
    key = _append_node(parent, UTILITY_NS, "Key")
    _append_node(key, UTILITY_NS, "ID", key_id)
    _append_node(key, UTILITY_NS, "ObjectType", object_type)
    return key


def _append_reference_key(parent: ET.Element, key_id: str, object_type: str) -> ET.Element:
    key = _append_node(parent, UTILITY_NS, "ReferenceKey")
    _append_node(key, UTILITY_NS, "ID", key_id)
    _append_node(key, UTILITY_NS, "ObjectType", object_type)
    return key


def _append_object_ref(
    parent: ET.Element,
    namespace: str,
    local_name: str,
    ref_id: str,
    object_type: str,
    *,
    include_name: bool = False,
    name_text: str = "",
) -> ET.Element:
    ref = _append_node(parent, namespace, local_name)
    _append_node(ref, UTILITY_NS, "ID", ref_id)
    _append_node(ref, UTILITY_NS, "ObjectType", object_type)
    if include_name:
        _append_node(ref, UTILITY_NS, "Name", name_text)
    return ref


def _append_blank_name(parent: ET.Element) -> ET.Element:
    return _append_node(parent, UTILITY_NS, "Name", "")


def _id_counter(root: ET.Element):
    """Genera IDs nuevos por encima del mayor ID/unsignedInt ya presente en el XML."""

    max_value = 0
    for element in root.iter():
        tag = _strip_namespace(element.tag)
        text = str(element.text or "").strip()
        if tag not in {"ID", "unsignedInt"} or not text.isdigit():
            continue
        max_value = max(max_value, int(text))

    current = max_value + 1
    while True:
        yield str(current)
        current += 1


def _reserve_ids(root: ET.Element, count: int, preferred_start: Optional[int] = None) -> list[str]:
    first_default_id = int(next(_id_counter(root)))
    start_id = first_default_id if preferred_start is None else max(first_default_id, preferred_start)
    return [str(start_id + offset) for offset in range(count)]


def _find_plane_ref(root: ET.Element, plane_name: str) -> tuple[str, str]:
    planes = root.find("./{*}Planes")
    if planes is None:
        raise ValueError("La plantilla no contiene Planes.")
    for plane in list(planes):
        plane_type = _text(plane, "./{*}Type") or _text(plane, "./{*}Name")
        if plane_type == plane_name:
            return (
                _text(plane, "./{*}Key/{*}ID"),
                _text(plane, "./{*}Key/{*}ObjectType"),
            )
    raise ValueError(f"La plantilla no contiene el plano '{plane_name}'.")


def _build_point_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    point_x: float,
    point_y: float,
    point_z: float = 0.0,
) -> ET.Element:
    geometry = ET.Element(
        _qname(GEOMETRY_NS, "GeomGeometry"),
        {f"{{{XSI_NS}}}type": "a:GeomCartesianPoint"},
    )
    _set_xmlns(geometry, "a", GEOMETRY_NS)
    _append_key(geometry, geometry_id, "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint")
    _append_blank_name(geometry)
    _append_node(geometry, GEOMETRY_NS, "IsAbsolute", "false")
    _append_object_ref(
        geometry,
        GEOMETRY_NS,
        "PlaneID",
        plane_id,
        plane_object_type,
    )
    _append_node(geometry, GEOMETRY_NS, "_x", _compact_number(point_x))
    _append_node(geometry, GEOMETRY_NS, "_y", _compact_number(point_y))
    _append_node(geometry, GEOMETRY_NS, "_z", _compact_number(point_z))
    return geometry


def _build_working_step(
    feature_name: str,
    step_id: str,
    feature_id: str,
    operation_id: str,
    feature_object_type: str = "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature",
    operation_object_type: str = "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "a:MachiningWorkingStep"},
    )
    _set_xmlns(step, "a", PGMX_NS)
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep")
    _append_blank_name(step).text = feature_name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")
    feature_ref = _append_object_ref(
        step,
        PGMX_NS,
        "ManufacturingFeatureID",
        feature_id,
        feature_object_type,
    )
    operation_ref = _append_object_ref(
        step,
        PGMX_NS,
        "OperationID",
        operation_id,
        operation_object_type,
    )
    _set_xmlns(feature_ref, "b", UTILITY_NS)
    _set_xmlns(operation_ref, "b", UTILITY_NS)
    return step


def _build_depth_expression(
    expression_id: str,
    feature_id: str,
    inner_field_name: str,
    depth_variable_name: str,
    referenced_object_type: str = "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature",
) -> ET.Element:
    expression = ET.Element(_qname(PARAMETRIC_NS, "Expression"))
    _append_key(expression, expression_id, "ScmGroup.XCam.MachiningDataModel.Parametrics.Expression")
    _append_blank_name(expression)
    property_node = _append_node(
        expression,
        PARAMETRIC_NS,
        "Property",
        attrib={f"{{{XSI_NS}}}type": "a:CompositeField"},
    )
    _set_xmlns(property_node, "a", PARAMETRIC_NS)
    _append_node(property_node, PARAMETRIC_NS, "Index", "-1")
    _append_node(property_node, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(property_node, PARAMETRIC_NS, "Name", "Depth")
    inner_field = _append_node(property_node, PARAMETRIC_NS, "InnerField")
    _append_node(inner_field, PARAMETRIC_NS, "Index", "-1")
    _append_node(inner_field, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(inner_field, PARAMETRIC_NS, "Name", inner_field_name)
    _append_object_ref(
        expression,
        PARAMETRIC_NS,
        "ReferencedObject",
        feature_id,
        referenced_object_type,
    )
    _append_node(expression, PARAMETRIC_NS, "Value", depth_variable_name)
    return expression


def _build_property_expression(
    expression_id: str,
    obj_id: str,
    obj_type: str,
    property_name: str,
    value: str,
) -> ET.Element:
    """Builds an Expression binding obj.property_name to a formula string.

    Covers simple (non-CompositeField) properties: X, Y on GeomCartesianPoint
    and IsEnabled on MachiningWorkingStep.
    """
    expression = ET.Element(_qname(PARAMETRIC_NS, "Expression"))
    _append_key(expression, expression_id, "ScmGroup.XCam.MachiningDataModel.Parametrics.Expression")
    _append_blank_name(expression)
    property_node = _append_node(expression, PARAMETRIC_NS, "Property")
    _append_node(property_node, PARAMETRIC_NS, "Index", "-1")
    _append_node(property_node, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(property_node, PARAMETRIC_NS, "Name", property_name)
    _append_object_ref(expression, PARAMETRIC_NS, "ReferencedObject", obj_id, obj_type)
    _append_node(expression, PARAMETRIC_NS, "Value", value)
    return expression


def _text(node: Optional[ET.Element], path: str, default: str = "") -> str:
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return str(found.text).strip()


def _raw_text(node: Optional[ET.Element], path: str, default: str = "") -> str:
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return str(found.text)


def _safe_float(value, default: float) -> float:
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _safe_bool(value, default: bool) -> bool:
    raw = "" if value is None else str(value).strip().lower()
    if not raw:
        return default
    if raw in {"true", "1", "yes", "si", "s\u00ed"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    return default
