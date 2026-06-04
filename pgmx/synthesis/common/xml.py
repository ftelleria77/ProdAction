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
    "_compact_number",
    "_qname",
    "_raw_text",
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
