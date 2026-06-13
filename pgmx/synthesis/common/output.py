"""Output finalization helpers for PGMX synthesis."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from .xml import (
    BASE_MODEL_NS,
    DRILLING_NS,
    GEOMETRY_NS,
    MILLING_NS,
    PARAMETRIC_NS,
    PATTERNS_NS,
    PGMX_NS,
    STRATEGY_NS,
    UTILITY_NS,
    XSD_NS,
)

__all__ = [
    "_finalize_pgmx_xml_bytes",
    "_finalize_synthesized_pgmx_xml_bytes",
    "_build_itype_ns_map",
    "_fix_itype_namespaces",
    "_write_pgmx_zip",
]


def _build_itype_ns_map(xml_text: str) -> dict[tuple[str, str], str]:
    """Scans raw XML text and returns {(element_local_name, type_name): namespace_uri}.

    Collects all i:type='prefix:TypeName' + xmlns:prefix='NS' pairs that appear
    together on the same opening tag, regardless of attribute order.
    """
    result: dict[tuple[str, str], str] = {}
    # i:type appears before xmlns
    for m in re.finditer(
        r'<([\w:]+)[^>]*i:type="(\w+):(\w+)"[^>]*xmlns:\2="([^"]+)"[^>]*>',
        xml_text,
    ):
        elem_local = m.group(1).split(":")[-1]
        result[(elem_local, m.group(3))] = m.group(4)
    # xmlns appears before i:type
    for m in re.finditer(
        r'<([\w:]+)[^>]*xmlns:(\w+)="([^"]+)"[^>]*i:type="\2:(\w+)"[^>]*>',
        xml_text,
    ):
        elem_local = m.group(1).split(":")[-1]
        result[(elem_local, m.group(4))] = m.group(3)
    return result


def _fix_itype_namespaces(
    xml_text: str,
    ns_map: dict[tuple[str, str], str],
) -> str:
    """Ensures every i:type='prefix:TypeName' opening tag has the correct xmlns:prefix.

    Uses *ns_map* (built from the original source file) to look up the authoritative
    namespace URI for each (element_local_name, type_name) pair.  Only tags where the
    namespace declaration is absent or wrong are modified.
    """
    if not ns_map:
        return xml_text

    def fix_tag(match: re.Match) -> str:
        full_tag = match.group(0)
        elem_local = match.group("elem").split(":")[-1]
        ns_prefix = match.group("ns_prefix")
        dtype = match.group("dtype")
        correct_ns = ns_map.get((elem_local, dtype))
        if correct_ns is None:
            return full_tag
        wanted = f'xmlns:{ns_prefix}="{correct_ns}"'
        if wanted in full_tag:
            return full_tag
        # Remove any wrong xmlns:prefix binding already on this tag
        cleaned = re.sub(rf'\s+xmlns:{re.escape(ns_prefix)}="[^"]*"', "", full_tag)
        # Inject correct binding right after the i:type attribute
        return re.sub(
            rf'(i:type="{re.escape(ns_prefix)}:{re.escape(dtype)}")',
            rf"\1 {wanted}",
            cleaned,
            count=1,
        )

    return re.sub(
        r'<(?P<elem>[\w:]+)(?P<before>[^>]*?) i:type="(?P<ns_prefix>\w+):(?P<dtype>\w+)"(?P<after>[^>]*)>',
        fix_tag,
        xml_text,
    )


def _write_pgmx_zip(
    output_path: Path,
    xml_bytes: bytes,
    template_entries: dict[str, bytes],
    xml_entry_name: str,
) -> None:
    """Write a `.pgmx` preserving non-XML entries from the template ZIP."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epl_written = False
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(xml_entry_name, xml_bytes)
        for entry_name, data in template_entries.items():
            if entry_name.lower().endswith(".xml"):
                continue
            if entry_name.lower().endswith(".epl"):
                zip_file.writestr(f"{output_path.stem}.epl", data)
                epl_written = True
                continue
            zip_file.writestr(entry_name, data)
        if not epl_written:
            zip_file.writestr(f"{output_path.stem}.epl", b"")


def _finalize_pgmx_xml_bytes(xml_bytes: bytes) -> bytes:
    """Normalize namespaces and runtime XML types for Maestro compatibility."""

    xml_text = xml_bytes.decode("utf-8")
    geometry_decl = f'<Geometries xmlns:a="{GEOMETRY_NS}">'
    global_setup_decl = f'<GlobalSetup xmlns:a="{BASE_MODEL_NS}">'
    machining_params_decl = (
        f'<MachiningParameters i:type="a:XilogHeaderParameters" xmlns:a="{BASE_MODEL_NS}">'
    )
    workpiece_geometry_decl = f'<Geometry i:type="a:WorkpieceBoxGeometry" xmlns:a="{BASE_MODEL_NS}">'
    variable_value_decl = f'<Value i:type="b:double" xmlns:b="{XSD_NS}">'
    approach_decl = f'<Approach i:type="b:BaseApproachStrategy" xmlns:b="{STRATEGY_NS}">'
    retract_decl = f'<Retract i:type="b:BaseRetractStrategy" xmlns:b="{STRATEGY_NS}">'

    def ensure_prefixed_namespace_attr(
        text: str,
        element_name: str,
        prefix: str,
        namespace: str,
    ) -> str:
        pattern = re.compile(
            rf'<(?P<tagprefix>[A-Za-z_][\w.-]*:)?{element_name}(?P<attrs>[^<>]*?)(?P<selfclose>\s*/?)>',
        )

        def replacer(match: re.Match[str]) -> str:
            attrs = (match.group("attrs") or "").rstrip()
            selfclose = match.group("selfclose") or ""
            if f'xmlns:{prefix}="' in attrs:
                return match.group(0)
            if attrs:
                return (
                    f'<{match.group("tagprefix") or ""}{element_name}'
                    f'{attrs} xmlns:{prefix}="{namespace}"{selfclose}>'
                )
            return (
                f'<{match.group("tagprefix") or ""}{element_name}'
                f' xmlns:{prefix}="{namespace}"{selfclose}>'
            )

        return pattern.sub(replacer, text)

    if "<Geometries>" in xml_text and geometry_decl not in xml_text:
        xml_text = xml_text.replace("<Geometries>", geometry_decl, 1)
    if "<GlobalSetup>" in xml_text and global_setup_decl not in xml_text:
        xml_text = xml_text.replace("<GlobalSetup>", global_setup_decl, 1)
    xml_text = xml_text.replace(
        '<MachiningParameters i:type="a:XilogHeaderParameters">',
        machining_params_decl,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Geometry i:type="a:WorkpieceBoxGeometry">',
        lambda match: (
            f'<{match.group("prefix") or ""}Geometry i:type="a:WorkpieceBoxGeometry" '
            f'xmlns:a="{BASE_MODEL_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Value i:type="b:double">',
        lambda match: (
            f'<{match.group("prefix") or ""}Value i:type="b:double" '
            f'xmlns:b="{XSD_NS}">'
        ),
        xml_text,
    )
    xml_text = ensure_prefixed_namespace_attr(xml_text, "ToolpathList", "b", BASE_MODEL_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "Head", "b", BASE_MODEL_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "MachineFunctions", "b", BASE_MODEL_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "StartPoint", "b", GEOMETRY_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "ToolKey", "b", UTILITY_NS)
    xml_text = xml_text.replace(
        '<Approach i:type="b:BaseApproachStrategy">',
        approach_decl,
    )
    xml_text = xml_text.replace(
        '<Retract i:type="b:BaseRetractStrategy">',
        retract_decl,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="a:MachiningWorkingStep">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="a:MachiningWorkingStep" '
            f'xmlns:a="{PGMX_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="(?P<dtype>Xn|Xmsg|Park|Iso)">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="{match.group("dtype")}" '
            f'xmlns="{BASE_MODEL_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?ManufacturingFeatureID>',
        lambda match: (
            f'<{match.group("prefix") or ""}ManufacturingFeatureID '
            f'xmlns:b="{UTILITY_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?OperationID>',
        lambda match: (
            f'<{match.group("prefix") or ""}OperationID '
            f'xmlns:b="{UTILITY_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?PlaneID>',
        lambda match: f'<{match.group("prefix") or ""}PlaneID xmlns:c="{UTILITY_NS}">',
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?BasicCurve i:type="(?:c:)?(?P<dtype>Geom\w+)">',
        lambda match: (
            f'<{match.group("prefix") or ""}BasicCurve i:type="c:{match.group("dtype")}" '
            f'xmlns:c="{GEOMETRY_NS}">'
        ),
        xml_text,
    )
    xml_text = xml_text.replace(
        '<Geometry i:type="a:WorkpieceBoxGeometry">',
        workpiece_geometry_decl,
    )
    xml_text = xml_text.replace(
        '<Value i:type="b:double">',
        variable_value_decl,
    )
    return xml_text.encode("utf-8")


def _finalize_synthesized_pgmx_xml_bytes(xml_bytes: bytes) -> bytes:
    finalized = _finalize_pgmx_xml_bytes(xml_bytes)
    xml_text = finalized.decode("utf-8")
    expressions_decl = f'<Expressions xmlns:a="{PARAMETRIC_NS}">'
    if "<Expressions>" in xml_text and expressions_decl not in xml_text:
        xml_text = xml_text.replace("<Expressions>", expressions_decl, 1)
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Property i:type="a:CompositeField">',
        lambda match: (
            f'<{match.group("prefix") or ""}Property i:type="a:CompositeField" '
            f'xmlns:a="{PARAMETRIC_NS}">'
        ),
        xml_text,
    )

    def runtime_type_namespace(element_name: str, dtype: str) -> str:
        if element_name == "ManufacturingFeature":
            return {
                "GeneralProfileFeature": MILLING_NS,
                "RoundHole": DRILLING_NS,
                "ReplicateFeature": PATTERNS_NS,
            }.get(dtype, MILLING_NS)
        if element_name == "Operation":
            return {
                "BottomAndSideFinishMilling": MILLING_NS,
                "DrillingOperation": DRILLING_NS,
            }.get(dtype, MILLING_NS)
        if element_name == "GeomGeometry":
            return GEOMETRY_NS
        return MILLING_NS

    for element_name in ("ManufacturingFeature", "Operation", "GeomGeometry"):
        xml_text = re.sub(
            rf'<(?P<prefix>[A-Za-z_][\w.-]*:)?{element_name}(?P<attrs>[^>]*) i:type="a:(?P<dtype>[^"]+)"(?P<tail>[^>]*)>',
            lambda match: (
                match.group(0)
                if 'xmlns:a="' in match.group(0)
                else (
                    f'<{match.group("prefix") or ""}{element_name}'
                    f'{match.group("attrs")} i:type="a:{match.group("dtype")}"'
                    f' xmlns:a="{runtime_type_namespace(element_name, match.group("dtype"))}"{match.group("tail")}>'
                )
            ),
            xml_text,
        )
    xml_text = xml_text.replace(
        '<MachiningStrategy i:type="b:SingleStepDrilling">',
        f'<MachiningStrategy i:type="b:SingleStepDrilling" xmlns:b="{BASE_MODEL_NS}">',
    )
    return xml_text.encode("utf-8")
