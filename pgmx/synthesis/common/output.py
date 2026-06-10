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
    PGMX_NS,
    STRATEGY_NS,
    UTILITY_NS,
    XSD_NS,
)

__all__ = [
    "_finalize_pgmx_xml_bytes",
    "_finalize_synthesized_pgmx_xml_bytes",
    "_write_pgmx_zip",
]


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
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="(?P<dtype>Xn|Xmsg)">',
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
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?BasicCurve i:type="c:GeomCompositeCurve">',
        lambda match: (
            f'<{match.group("prefix") or ""}BasicCurve i:type="c:GeomCompositeCurve" '
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
