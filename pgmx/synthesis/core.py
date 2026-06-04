"""Utilidades para sintetizar archivos `.pgmx` a partir de un baseline Maestro.

La API publica del modulo esta pensada para poder reutilizarla desde el flujo
principal de la aplicacion, sin depender de la CLI:

Referencia operativa recomendada:
- `docs/synthesize_pgmx_help.md`

- `read_pgmx_state(...)` lee dimensiones, nombre, origen y area desde un
    baseline Maestro (`.pgmx`, `Pieza.xml` o carpeta contenedora).
- `read_pgmx_geometries(...)` clasifica las geometrías base guardadas en `Geometries`.
- `build_synthesis_request(...)` arma una solicitud clara y reusable.
- `synthesize_request(...)` aplica la solicitud sobre un baseline Maestro y
    escribe el `.pgmx` de salida.
- `synthesize_pgmx(...)` se mantiene como wrapper de compatibilidad para los
    scripts y experimentos ya existentes.

Soporte actual de mecanizados sinteticos:
- `LineMillingSpec`: linea sobre un plano con su fresado asociado.
- `PolylineMillingSpec`: polilinea lineal abierta o cerrada con su fresado asociado.
- `CircleMillingSpec`: circulo sobre `Top` con su fresado asociado.
- `SquaringMillingSpec`: escuadrado exterior del contorno de la pieza sobre `Top`.
- `PocketMillingSpec`: `Vaciado` rectangular sobre `Top` (`ClosedPocket` +
  `BottomAndSideRoughMilling` + `ContourParallel`).
- `DrillingSpec`: taladro puntual sobre `Top`, `Front`, `Back`, `Right` o `Left`.
- `DrillingPatternSpec`: repeticion rectangular de taladros sobre `Top`, `Front`, `Back`,
  `Right` o `Left`.
- `XnSpec`: operacion nula final para mover la herramienta sin mecanizar.

Estado de hito:
- la API publica del sintetizador queda establecida como `v1.6`

Soporte actual de geometria base reusable:
- `build_point_geometry_profile(...)`
- `build_line_geometry_profile(...)`
- `build_circle_geometry_profile(...)`
- `build_composite_geometry_profile(...)`
- `build_compensated_toolpath_profile(...)`

Hallazgos ya volcados en la sintesis:
- `Area` de `Parametros de Maquina` usa `HG` por defecto si no se indica otro valor.
- La profundidad total del fresado se valida contra `pgmx/data/tool_catalog.csv`:
    `target_depth` en no pasante y `espesor + Extra` en pasante no pueden
    superar `sinking_length` de la herramienta elegida.
- `Approach` y `Retract` soportan `Line` y `Arc`.
- Para `Approach Line + Down` ya se sintetizo la regla observada en Maestro:
    una sola bajada oblicua desde un punto previo desplazado sobre la direccion
    opuesta al avance, sin alterar `TrajectoryPath`. La regla ya se aplica
    sobre la tangente de entrada del toolpath efectivo, sin depender de la
    familia geometrica nominal.
- Para `Retract Line + Up` ya se sintetizo la regla observada en Maestro:
    una sola subida oblicua hacia un punto final desplazado sobre la direccion
    de salida, sin alterar `TrajectoryPath`. La regla ya se aplica sobre la
    tangente de salida del toolpath efectivo, sin depender de la familia
    geometrica nominal.
- Para `Arc + Quote` ya se sintetizo la regla observada en Maestro para entrada/salida
    sobre perfiles rectos: toolpath vertical cuando la estrategia esta deshabilitada y
    `linea vertical + arco` / `arco + linea vertical` cuando esta habilitada.
    La construccion ya cuelga del toolpath efectivo y su tangente de entrada/salida.
- Para `Retract Arc + Up` ya se sintetizo la salida observada en Maestro:
    `arco en un plano vertical + linea vertical`, sin alterar `TrajectoryPath`.
    La construccion ya cuelga del toolpath efectivo y su tangente de salida.
- Por limitacion observada en Maestro, se bloquea `Retract Arc + Up` en
    polilineas abiertas de varios segmentos con estrategia multipasada `PH`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

from .common.depth import (
    MillingDepthSpec,
    _extract_depth_spec_from_template,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from .common.geometry import (
    GeometryPrimitiveSpec,
    GeometryProfileSpec,
    _CurveSpec,
    _build_boundary_curve_holder,
    _build_geometry_from_curve_spec,
    _build_curve_holder,
    _build_identity_profile_placement,
    _build_maestro_arc_serialization,
    _build_maestro_line_serialization,
    _build_oriented_maestro_arc_serialization,
    _build_profile_geometry_spec,
    _build_start_point,
    _build_toolpath,
    _build_toolpath_description,
    _build_vector_holder,
    _build_closed_polyline_geometry_profile,
    _build_line_description,
    _build_open_polyline_descriptions,
    _build_open_polyline_geometry_profile,
    _circle_curve_spec,
    _composite_curve_spec,
    _curve_spec_from_composite_curve_node,
    _curve_spec_from_profile_geometry,
    _curve_spec_from_toolpath_node,
    _curve_spec_points,
    _extract_geometry_profile,
    _geometry_object_type,
    _is_closed_polyline_points,
    _normalize_polyline_points,
    _build_compensated_profile_geometry,
    _line_primitive_at_plane,
    _line_primitive_3d,
    _line_unit_direction,
    _primitive_at_z,
    _profile_at_z,
    _profile_endpoint_directions,
    _profile_endpoint_points,
    _profile_endpoint_points_3d,
    _profile_entry_exit_context,
    _resolve_toolpath_direction,
    _reverse_geometry_primitive,
    _reverse_profile_geometry,
    _vertical_transition_primitive,
    _normalize_side_of_feature,
    _primitive_winding,
    _normalize_curve_serialization_text,
    _normalize_geometry_winding,
    _parse_circle_geometry_profile,
    _parse_geometry_primitive,
    _parse_line_serialization,
    _points_close_2d,
    _points_close_3d,
    _primitive_end_tangent_2d,
    _primitive_start_tangent_2d,
    _sample_arc_point,
    _trimmed_curve_spec,
    build_arc_geometry_primitive,
    build_compensated_toolpath_profile,
    build_circle_geometry_profile,
    build_composite_geometry_profile,
    build_line_geometry_primitive,
    build_line_geometry_profile,
    build_point_geometry_profile,
    read_pgmx_geometries,
)
from .common.hydration import (
    PgmxTemplateDocument,
    _load_exploded_pgmx_container,
    _load_pgmx_container,
    _resolve_exploded_pgmx_xml_path,
    load_pgmx_template_document,
)
from .common.leads import (
    ApproachSpec,
    RetractSpec,
    _extract_approach_spec_from_operation,
    _extract_retract_spec_from_operation,
    _normalize_approach_arc_side,
    _normalize_approach_mode,
    _normalize_approach_spec,
    _normalize_approach_type,
    _normalize_retract_arc_side,
    _normalize_retract_mode,
    _normalize_retract_spec,
    _normalize_retract_type,
    build_approach_spec,
    build_retract_spec,
)
from .common.piece import (
    PieceGeometry,
    _drilling_axis_span,
    _drilling_axis_variable_name,
    _drilling_entry_point_and_direction,
    _normalize_plane_name,
    _plane_local_dimensions,
    _workpiece_depth_name,
    _workpiece_length_name,
    _workpiece_width_name,
)
from .common.program import (
    DEFAULT_MACHINING_ORDER,
    MachiningSpec,
    PgmxState,
    PgmxSynthesisRequest,
    PgmxSynthesisResult,
    XnSpec,
)
from .common.strategy import (
    BidirectionalMillingStrategySpec,
    ContourParallelMillingStrategySpec,
    HelicalMillingStrategySpec,
    MillingStrategySpec,
    UnidirectionalMillingStrategySpec,
    _ensure_milling_strategy_allowed,
    _extract_milling_strategy_spec_from_operation,
    _build_bidirectional_line_strategy_profile,
    _build_bidirectional_open_profile_strategy_toolpath,
    _build_closed_profile_strategy_toolpath,
    _build_helical_arc_primitive,
    _build_helical_circle_strategy_toolpath,
    _build_milling_strategy_node,
    _build_unidirectional_line_strategy_profile,
    _build_unidirectional_open_profile_strategy_toolpath,
    _helical_rough_end_levels,
    _normalize_milling_strategy_spec,
    _normalize_strategy_connection_mode,
    _resolve_unidirectional_connection_mode,
    _serialize_unidirectional_connection_mode,
    _should_activate_cnc_correction,
    _spec_uses_closed_profile,
    _strategy_comparison_key,
    _strategy_is_multilevel,
    _strategy_pass_levels,
    build_bidirectional_milling_strategy_spec,
    build_contour_parallel_milling_strategy_spec,
    build_helical_milling_strategy_spec,
    build_unidirectional_milling_strategy_spec,
)
from .common.tools import (
    TOOL_CATALOG_PATH,
    _is_vertical_x_saw,
    _load_tool_catalog,
    _normalize_tool_usage_group,
    _resolve_drilling_tool,
    _tool_catalog_label,
    _validate_tool_sinking_length_for_total_depth,
    _validate_tool_type_for_drilling_spec,
)
from .common.xml import (
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
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _build_depth_expression,
    _build_point_geometry,
    _build_working_step,
    _compact_number,
    _find_plane_ref,
    _id_counter,
    _qname,
    _raw_text,
    _reserve_ids,
    _safe_bool,
    _safe_float,
    _set_text,
    _set_xmlns,
    _strip_namespace,
    _text,
    _xsi_type,
    register_pgmx_namespaces,
)
from .drilling.pattern import (
    DrillingPatternSpec,
    _HydratedDrillingPatternSpec,
    _append_drilling_pattern,
    _build_drilling_pattern_depth_expression,
    _build_drilling_pattern_feature,
    _drilling_pattern_bottom_condition_type,
    _hydrate_drilling_pattern_spec,
    _normalize_drilling_pattern_spec,
    _validate_drilling_pattern_center,
    build_drilling_pattern_spec,
)
from .drilling.single import (
    DrillingSpec,
    _HydratedDrillingSpec,
    _append_drilling,
    _append_drilling_feature_payload,
    _build_drilling_feature,
    _build_drilling_operation,
    _drilling_bottom_condition_type,
    _drilling_feature_depth_value,
    _drilling_total_depth,
    _hydrate_drilling_spec,
    _normalize_drilling_spec,
    _uses_drilling_depth_expressions,
    _validate_drilling_center,
    _validate_tool_sinking_length_for_drilling_spec,
    build_drilling_spec,
)
from .milling._common import (
    _feature_bottom_condition_type,
    _feature_depth_value,
    _operation_overcut_length,
    _tool_total_milling_depth,
    _toolpath_cut_z,
    _uses_feature_depth_expressions,
    _validate_tool_sinking_length_for_spec,
    _validate_tool_type_for_milling_spec,
    _validate_vertical_x_saw_for_milling_spec,
)
from .milling.line import (
    LineMillingSpec,
    _HydratedLineMillingSpec,
    _build_line_geometry,
    _build_line_operation,
    _build_line_toolpath_profile,
    _can_hydrate_exact_serialization,
    _extract_line_milling_template,
    _hydrate_line_milling_spec,
    _matches_line_geometry,
    _normalize_line_milling_spec,
    _offset_line_for_toolpath,
    build_line_milling_spec,
)
from .milling.circle import (
    CircleMillingSpec,
    _HydratedCircleMillingSpec,
    _build_circle_toolpath_profile,
    _can_hydrate_exact_circle_serialization,
    _extract_circle_milling_template,
    _hydrate_circle_milling_spec,
    _matches_circle_geometry,
    _normalize_circle_milling_spec,
    build_circle_milling_spec,
)
from .milling.profile import (
    PolylineMillingSpec,
    _HydratedPolylineMillingSpec,
    _build_polyline_toolpath_profile,
    _can_hydrate_exact_polyline_serialization,
    _extract_polyline_milling_template,
    _hydrate_polyline_milling_spec,
    _matches_polyline_geometry,
    _normalize_polyline_milling_spec,
    _validate_polyline_postprocessable_by_maestro,
    build_polyline_milling_spec,
)
from .milling.pocket import (
    PocketBossRouteSeedSpec,
    PocketMillingSpec,
    _HydratedPocketMillingSpec,
    _can_hydrate_pocket_template_trace,
    _extract_pocket_milling_template,
    _hydrate_pocket_milling_spec,
    _same_xy_contours,
    _same_xy_points,
    build_pocket_boss_route_seed_spec,
    build_pocket_milling_spec,
)
from .milling.slot import (
    SlotMillingSpec,
    _HydratedSlotMillingSpec,
    _build_slot_side_feature,
    _hydrate_slot_milling_spec,
    _normalize_slot_milling_spec,
    build_slot_milling_spec,
)
from .milling.squaring import (
    SquaringMillingSpec,
    _HydratedSquaringMillingSpec,
    _normalize_squaring_milling_spec,
    _normalize_squaring_start_edge,
    _build_squaring_geometry_profile,
    _build_squaring_outline_points,
    _build_squaring_toolpath_profile,
    _hydrate_squaring_milling_spec,
    _reparameterize_line_primitive_from_end,
    _reparameterize_squaring_toolpath_profile,
    _with_line_direction_hint,
    build_squaring_milling_spec,
)


register_pgmx_namespaces()


def _module_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        for bundled_data_dir in (
            executable_dir / "pgmx" / "data",
            executable_dir / "_internal" / "pgmx" / "data",
            executable_dir / "tools",
            executable_dir / "_internal" / "tools",
        ):
            if bundled_data_dir.exists():
                return bundled_data_dir
    return Path(__file__).resolve().parents[1] / "data"


MODULE_DIR = _module_data_dir()
DEFAULT_BASELINE_DIR = MODULE_DIR / "maestro_baselines"
DEFAULT_BASELINE_XML_PATH = DEFAULT_BASELINE_DIR / "Pieza.xml"
SYNTHESIZER_VERSION = "1.6"

__all__ = [
    "DEFAULT_BASELINE_DIR",
    "DEFAULT_BASELINE_XML_PATH",
    "SYNTHESIZER_VERSION",
    "PgmxState",
    "ApproachSpec",
    "RetractSpec",
    "MillingDepthSpec",
    "UnidirectionalMillingStrategySpec",
    "BidirectionalMillingStrategySpec",
    "HelicalMillingStrategySpec",
    "ContourParallelMillingStrategySpec",
    "GeometryPrimitiveSpec",
    "GeometryProfileSpec",
    "PocketBossRouteSeedSpec",
    "LineMillingSpec",
    "SlotMillingSpec",
    "PolylineMillingSpec",
    "CircleMillingSpec",
    "SquaringMillingSpec",
    "PocketMillingSpec",
    "DrillingSpec",
    "DrillingPatternSpec",
    "MachiningSpec",
    "XnSpec",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "build_approach_spec",
    "build_retract_spec",
    "build_milling_depth_spec",
    "build_unidirectional_milling_strategy_spec",
    "build_bidirectional_milling_strategy_spec",
    "build_helical_milling_strategy_spec",
    "build_contour_parallel_milling_strategy_spec",
    "build_line_geometry_primitive",
    "build_arc_geometry_primitive",
    "build_point_geometry_profile",
    "build_line_geometry_profile",
    "build_circle_geometry_profile",
    "build_composite_geometry_profile",
    "build_compensated_toolpath_profile",
    "build_pocket_boss_route_seed_spec",
    "build_line_milling_spec",
    "build_slot_milling_spec",
    "build_polyline_milling_spec",
    "build_circle_milling_spec",
    "build_squaring_milling_spec",
    "build_pocket_milling_spec",
    "build_drilling_spec",
    "build_drilling_pattern_spec",
    "build_xn_spec",
    "read_pgmx_state",
    "read_pgmx_geometries",
    "build_synthesis_request",
    "synthesize_request",
    "synthesize_pgmx",
]


# ============================================================================
# Public data model
# ============================================================================

# ============================================================================
# Public spec builders
# ============================================================================

def _toolpath_line_string(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    """Serializa un segmento recto de `ToolpathList` en el formato raw de Maestro."""

    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    dz = end_point[2] - start_point[2]
    length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if length <= 1e-6:
        raise ValueError("No se puede crear un segmento de toolpath con longitud cero.")

    return "\n".join(
        [
            f"8 0 {_compact_number(length)}",
            " ".join(
                [
                    "1",
                    _compact_number(start_point[0]),
                    _compact_number(start_point[1]),
                    _compact_number(start_point[2]),
                    _compact_number(dx / length),
                    _compact_number(dy / length),
                    _compact_number(dz / length),
                ]
            ),
        ]
    )


def _write_pgmx_zip(output_path: Path, xml_bytes: bytes, template_entries: dict[str, bytes], xml_entry_name: str) -> None:
    """Escribe un `.pgmx` preservando el resto de entradas del template ZIP."""

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
    """Normaliza namespaces y tipos XML para que Maestro acepte el `.pgmx`."""

    xml_text = xml_bytes.decode("utf-8")
    geometry_decl = f'<Geometries xmlns:a="{GEOMETRY_NS}">'
    global_setup_decl = f'<GlobalSetup xmlns:a="{BASE_MODEL_NS}">'
    machining_params_decl = (
        f'<MachiningParameters i:type="a:XilogHeaderParameters" xmlns:a="{BASE_MODEL_NS}">'
    )
    workpiece_geometry_decl = f'<Geometry i:type="a:WorkpieceBoxGeometry" xmlns:a="{BASE_MODEL_NS}">'
    variable_value_decl = f'<Value i:type="b:double" xmlns:b="{XSD_NS}">'
    toolpath_list_decl = f'<ToolpathList xmlns:b="{BASE_MODEL_NS}">'
    head_decl = f'<Head xmlns:b="{BASE_MODEL_NS}">'
    machine_functions_decl = f'<MachineFunctions xmlns:b="{BASE_MODEL_NS}">'
    start_point_decl = f'<StartPoint xmlns:b="{GEOMETRY_NS}">'
    tool_key_decl = f'<ToolKey xmlns:b="{UTILITY_NS}">'
    approach_decl = f'<Approach i:type="b:BaseApproachStrategy" xmlns:b="{STRATEGY_NS}">'
    retract_decl = f'<Retract i:type="b:BaseRetractStrategy" xmlns:b="{STRATEGY_NS}">'

    def ensure_prefixed_namespace_attr(text: str, element_name: str, prefix: str, namespace: str) -> str:
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
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="Xn">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="Xn" '
            f'xmlns="{BASE_MODEL_NS}">'
        ),
        xml_text,
        count=1,
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


def build_xn_spec(
    *,
    reference: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
) -> XnSpec:
    """Construye la spec publica `Xn` con defaults observados en Maestro."""

    return XnSpec(
        reference=_normalize_xn_reference(reference),
        x=-3700.0 if x is None else float(x),
        y=None if y is None else float(y),
    )


def _normalize_xn_spec(xn: Optional[XnSpec]) -> XnSpec:
    if xn is None:
        return build_xn_spec()
    return build_xn_spec(
        reference=xn.reference,
        x=xn.x,
        y=xn.y,
    )


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


def _preferred_side_for_arc(side_of_feature: str, arc_side: str) -> str:
    normalized_side = _normalize_side_of_feature(side_of_feature)
    if normalized_side != "Center":
        return normalized_side
    normalized_arc_side = _normalize_approach_arc_side(arc_side)
    if normalized_arc_side in {"Left", "Right"}:
        return normalized_arc_side
    return "Right"


def _side_normal_for_direction(
    direction_x: float,
    direction_y: float,
    side_of_feature: str,
    arc_side: str,
) -> tuple[tuple[float, float], float]:
    right_normal = (direction_y, -direction_x)
    left_normal = (-right_normal[0], -right_normal[1])
    preferred_side = _preferred_side_for_arc(side_of_feature, arc_side)
    if preferred_side == "Left":
        return left_normal, 1.0
    return right_normal, -1.0


def _build_vertical_toolpath_curve(
    x_value: float,
    y_value: float,
    start_z: float,
    end_z: float,
) -> _CurveSpec:
    # Maestro mantiene un toolpath vertical en Approach/Lift aunque la estrategia este deshabilitada.
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (x_value, y_value, start_z),
            (x_value, y_value, end_z),
        )
    )


def _quote_arc_radius(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * max(radius_multiplier - 1.0, 0.0)


def _linear_lead_distance(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * radius_multiplier


def _dominant_component_sign_2d(vector: tuple[float, float]) -> float:
    x_value, y_value = vector
    if abs(x_value) >= abs(y_value):
        if not math.isclose(x_value, 0.0, abs_tol=1e-15):
            return 1.0 if x_value > 0.0 else -1.0
    if not math.isclose(y_value, 0.0, abs_tol=1e-15):
        return 1.0 if y_value > 0.0 else -1.0
    return 1.0


def _build_oriented_maestro_arc_basis(
    direction: tuple[float, float],
    side_normal: tuple[float, float],
    normal_z: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    # Maestro serializa estos arcos con una base 3D orientada y pequeños epsilon
    # en algunos componentes. Mantener esta estructura ayuda a que el XML sintetizado
    # se parezca mas al guardado manualmente desde Maestro.
    epsilon = math.ulp(0.5)
    direction_x, direction_y = direction
    side_x, side_y = side_normal
    u_vector = (
        0.0 if math.isclose(side_x, 0.0, abs_tol=1e-15) else (normal_z * side_x),
        normal_z * side_y,
        epsilon * normal_z,
    )
    v_vector = (
        -normal_z * direction_x,
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-normal_z * direction_y),
        0.0,
    )
    normal_vector = (
        (-0.0 if normal_z > 0.0 else 0.0)
        if math.isclose(direction_y, 0.0, abs_tol=1e-15)
        else (epsilon * direction_y),
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-epsilon * direction_x),
        normal_z,
    )
    return normal_vector, u_vector, v_vector


def _build_quote_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. bajada vertical en el punto inicial del acercamiento
    # 2. cuarto de arco en la cota de corte hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = entry_point[0] + (side_normal[0] * arc_radius)
    center_y = entry_point[1] + (side_normal[1] * arc_radius)
    plunge_x = center_x - (direction_x * arc_radius)
    plunge_y = center_y - (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = (1.5 * math.pi) if normal_z < 0.0 else (0.5 * math.pi)
    end_angle = (2.0 * math.pi) if normal_z < 0.0 else math.pi

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, cut_z),
            ),
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
        ]
    )


def _build_down_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Down:
    # 1. bajada vertical hasta `cut_z + radio`
    # 2. cuarto de arco en un plano vertical hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    right_normal_x = direction_y
    right_normal_y = -direction_x
    pre_entry_z = cut_z + arc_radius
    plunge_x = entry_point[0] - (direction_x * arc_radius)
    plunge_y = entry_point[1] - (direction_y * arc_radius)

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, pre_entry_z),
            ),
            _build_oriented_maestro_arc_serialization(
                1.5 * math.pi,
                2.0 * math.pi,
                (entry_point[0], entry_point[1], pre_entry_z),
                (right_normal_x, right_normal_y, 0.0),
                (0.0, 0.0, -1.0),
                (direction_x, direction_y, 0.0),
                arc_radius,
                z_value=pre_entry_z,
            ),
        ]
    )


def _build_down_line_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Down:
    # una sola bajada oblicua desde un punto previo desplazado
    # en la direccion opuesta al avance del toolpath.
    pre_entry_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    pre_entry_x = entry_point[0] - (direction_x * pre_entry_distance)
    pre_entry_y = entry_point[1] - (direction_y * pre_entry_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (pre_entry_x, pre_entry_y, clearance_z),
            (entry_point[0], entry_point[1], cut_z),
        )
    )


def _build_up_line_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Up:
    # una sola subida oblicua hacia un punto final desplazado
    # sobre la direccion de salida del toolpath.
    post_exit_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    post_exit_x = exit_point[0] + (direction_x * post_exit_distance)
    post_exit_y = exit_point[1] + (direction_y * post_exit_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (exit_point[0], exit_point[1], cut_z),
            (post_exit_x, post_exit_y, clearance_z),
        )
    )


def _build_quote_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. cuarto de arco en la cota de corte desde el punto de salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = exit_point[0] + (side_normal[0] * arc_radius)
    center_y = exit_point[1] + (side_normal[1] * arc_radius)
    lift_x = center_x + (direction_x * arc_radius)
    lift_y = center_y + (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = 0.0 if normal_z < 0.0 else math.pi
    end_angle = (0.5 * math.pi) if normal_z < 0.0 else (1.5 * math.pi)

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, cut_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _build_up_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Up:
    # 1. cuarto de arco en un plano vertical desde la salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    plane_normal = (
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else direction_y,
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-direction_x),
    )
    basis_sign = _dominant_component_sign_2d(plane_normal)
    center_z = cut_z + arc_radius
    lift_x = exit_point[0] + (direction_x * arc_radius)
    lift_y = exit_point[1] + (direction_y * arc_radius)
    lift_z = center_z
    tangent_vector = (
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-basis_sign * direction_x),
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-basis_sign * direction_y),
        0.0,
    )

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                math.pi if basis_sign > 0.0 else 0.0,
                (1.5 * math.pi) if basis_sign > 0.0 else (0.5 * math.pi),
                exit_point,
                (plane_normal[0], plane_normal[1], 0.0),
                (0.0, 0.0, basis_sign),
                tangent_vector,
                arc_radius,
                z_value=center_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, lift_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _build_polyline_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    curve_spec: _CurveSpec,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    return _build_geometry_from_curve_spec(
        geometry_id,
        plane_id,
        plane_object_type,
        curve_spec,
        generated_member_keys=generated_member_keys,
    )


def _build_profile_feature(
    state: PgmxState,
    spec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    geometry_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:GeneralProfileFeature"},
    )
    _set_xmlns(feature, "a", MILLING_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        geometry_object_type,
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _feature_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", MILLING_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    end_conditions = _append_node(feature, PGMX_NS, "EndConditions")
    slot_end_a = _append_node(
        end_conditions,
        MILLING_NS,
        "SlotEndType",
        attrib={f"{{{XSI_NS}}}type": "a:RadiusedSlotEndType"},
    )
    slot_end_b = _append_node(
        end_conditions,
        MILLING_NS,
        "SlotEndType",
        attrib={f"{{{XSI_NS}}}type": "a:RadiusedSlotEndType"},
    )
    _set_xmlns(slot_end_a, "a", MILLING_NS)
    _set_xmlns(slot_end_b, "a", MILLING_NS)
    _append_node(feature, PGMX_NS, "IsGeomSameDirection", "true")
    _append_node(feature, PGMX_NS, "IsPrecise", "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", "Left")
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", "0")
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", "0")
    _append_node(feature, PGMX_NS, "SideOfFeature", spec.side_of_feature)
    _append_node(feature, PGMX_NS, "SideOffset", "0")
    swept_shape = _append_node(
        feature,
        PGMX_NS,
        "SweptShape",
        attrib={f"{{{XSI_NS}}}type": "a:SquareUProfile"},
    )
    _set_xmlns(swept_shape, "a", MILLING_NS)
    swept_shape.append(_build_identity_profile_placement())
    _append_node(swept_shape, MILLING_NS, "FirstAngle", "0")
    _append_node(swept_shape, MILLING_NS, "FirstRadius", "0")
    _append_node(swept_shape, MILLING_NS, "SecondAngle", "0")
    _append_node(swept_shape, MILLING_NS, "SecondRadius", "0")
    _append_node(swept_shape, MILLING_NS, "Width", _compact_number(spec.tool_width))
    return feature


def _build_closed_pocket_feature(
    state: PgmxState,
    spec: _HydratedPocketMillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    geometry_object_type: str,
    boundary_curve: _CurveSpec,
    boundary_member_keys: Sequence[str],
    boss_geometry_curves: Sequence[tuple[_CurveSpec, Sequence[str]]] = (),
    boss_route_seed_refs: Sequence[tuple[PocketBossRouteSeedSpec, str, str]] = (),
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:ClosedPocket"},
    )
    _set_xmlns(feature, "a", BASE_MODEL_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.ClosedPocket")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(feature, PGMX_NS, "GeometryID", geometry_id, geometry_object_type)
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideRoughMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": "a:PlanarPocketBottomCondition"},
    )
    _set_xmlns(bottom_condition, "a", BASE_MODEL_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    boss_geometry_list = _append_node(feature, BASE_MODEL_NS, "BossGeometryList")
    for boss_curve, boss_member_keys in boss_geometry_curves:
        boss_geometry_list.append(_build_boundary_curve_holder(boss_curve, boss_member_keys))
    boss_list = _append_node(feature, BASE_MODEL_NS, "BossList")
    for route_seed, route_seed_geometry_id, route_seed_object_type in boss_route_seed_refs:
        boss_list.append(
            _build_closed_pocket_boss(
                route_seed,
                route_seed_geometry_id,
                route_seed_object_type,
                workpiece_id,
                workpiece_object_type,
            )
        )
    boundary_list = _append_node(feature, BASE_MODEL_NS, "BoundaryGeometryList")
    boundary_list.append(_build_boundary_curve_holder(boundary_curve, boundary_member_keys))
    _append_node(feature, BASE_MODEL_NS, "OrthogonalRadius", "0")
    _append_node(feature, BASE_MODEL_NS, "PlanarRadius", "0")
    _append_node(feature, BASE_MODEL_NS, "Slope", "0")
    return feature


def _build_closed_pocket_boss(
    route_seed: PocketBossRouteSeedSpec,
    geometry_id: str,
    geometry_object_type: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    boss = ET.Element(_qname(BASE_MODEL_NS, "Boss"))
    _append_key(boss, "0", "System.Object")
    _append_blank_name(boss).text = route_seed.name or "Boss"
    _append_object_ref(boss, PGMX_NS, "GeometryID", geometry_id, geometry_object_type)
    _append_node(boss, PGMX_NS, "OperationIDs")
    _append_object_ref(boss, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    _append_node(boss, PGMX_NS, "BottomCondition", attrib={f"{{{XSI_NS}}}nil": "true"})
    depth = _append_node(boss, PGMX_NS, "Depth")
    _append_node(depth, PGMX_NS, "EndDepth", "0")
    _append_node(depth, PGMX_NS, "StartDepth", "0")
    _append_node(boss, BASE_MODEL_NS, "Slope", "0")
    return boss


def _build_generated_approach_curve(
    state: PgmxState,
    spec,
    toolpath_start: tuple[float, float, float],
    toolpath_end: tuple[float, float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    approach = _normalize_approach_spec(spec.approach)
    clearance_z = state.depth + spec.security_plane
    cut_z = toolpath_start[2]
    direction_x, direction_y = _resolve_toolpath_direction(
        (toolpath_start[0], toolpath_start[1]),
        (toolpath_end[0], toolpath_end[1]),
        direction=direction,
    )
    if not approach.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_start[0], toolpath_start[1], clearance_z, cut_z)

    if approach.approach_type == "Line" and approach.mode == "Quote":
        pre_entry_distance = _linear_lead_distance(spec.tool_width, approach.radius_multiplier)
        pre_entry_x = toolpath_start[0] - (direction_x * pre_entry_distance)
        pre_entry_y = toolpath_start[1] - (direction_y * pre_entry_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, clearance_z),
                    (pre_entry_x, pre_entry_y, cut_z),
                ),
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, cut_z),
                    (toolpath_start[0], toolpath_start[1], cut_z),
                ),
            ]
        )

    if approach.approach_type == "Line" and approach.mode == "Down":
        return _build_down_line_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Quote":
        return _build_quote_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=approach.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Down":
        return _build_down_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un approach habilitado con "
        f"type={approach.approach_type} y mode={approach.mode}."
    )


def _build_generated_approach_curve_for_profile(
    state: PgmxState,
    spec,
    toolpath_profile: GeometryProfileSpec,
) -> _CurveSpec:
    """Construye el approach a partir de una trayectoria efectiva y su tangente de entrada."""

    toolpath_start, toolpath_end = _profile_endpoint_points_3d(toolpath_profile)
    _, _, start_direction, _ = _profile_entry_exit_context(toolpath_profile)
    return _build_generated_approach_curve(
        state,
        spec,
        toolpath_start,
        toolpath_end,
        direction=start_direction,
    )


def _build_generated_lift_curve(
    state: PgmxState,
    spec,
    toolpath_start: tuple[float, float, float],
    toolpath_end: tuple[float, float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    retract = _normalize_retract_spec(spec.retract)
    clearance_z = state.depth + spec.security_plane
    cut_z = toolpath_end[2]
    direction_x, direction_y = _resolve_toolpath_direction(
        (toolpath_start[0], toolpath_start[1]),
        (toolpath_end[0], toolpath_end[1]),
        direction=direction,
    )
    if not retract.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_end[0], toolpath_end[1], cut_z, clearance_z)

    if retract.retract_type == "Line" and retract.mode == "Quote":
        post_exit_distance = (spec.tool_width / 2.0) * retract.radius_multiplier
        post_exit_x = toolpath_end[0] + (direction_x * post_exit_distance)
        post_exit_y = toolpath_end[1] + (direction_y * post_exit_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (toolpath_end[0], toolpath_end[1], cut_z),
                    (post_exit_x, post_exit_y, cut_z),
                ),
                _build_toolpath_description(
                    (post_exit_x, post_exit_y, cut_z),
                    (post_exit_x, post_exit_y, clearance_z),
                ),
            ]
        )

    if retract.retract_type == "Line" and retract.mode == "Up":
        return _build_up_line_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Quote":
        return _build_quote_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=retract.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Up":
        return _build_up_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un retract habilitado con "
        f"type={retract.retract_type} y mode={retract.mode}."
    )


def _build_generated_lift_curve_for_profile(
    state: PgmxState,
    spec,
    toolpath_profile: GeometryProfileSpec,
) -> _CurveSpec:
    """Construye el lift a partir de una trayectoria efectiva y su tangente de salida."""

    toolpath_start, toolpath_end = _profile_endpoint_points_3d(toolpath_profile)
    _, _, _, end_direction = _profile_entry_exit_context(toolpath_profile)
    return _build_generated_lift_curve(
        state,
        spec,
        toolpath_start,
        toolpath_end,
        direction=end_direction,
    )


def _build_contour_parallel_xyz_path(
    state: PgmxState,
    spec: _HydratedPocketMillingSpec,
) -> tuple[tuple[float, float, float], ...]:
    from pgmx.vaciado_lab.contour_parallel import generate_rectangular_contour_parallel_xyz_path

    strategy = spec.milling_strategy
    return generate_rectangular_contour_parallel_xyz_path(
        length=state.length,
        width=state.width,
        depth=state.depth,
        contour_points=spec.contour_points,
        tool_width=spec.tool_width,
        target_depth=float(_feature_depth_value(state, spec)),
        security_plane=spec.security_plane,
        allowance_side=spec.allowance_side,
        overlap=strategy.overlap,
        radial_cutting_depth=strategy.radial_cutting_depth,
        rotation_direction=strategy.rotation_direction,
        inside_to_outside=strategy.inside_to_outside,
        stroke_connection_strategy=strategy.stroke_connection_strategy,
        allow_multiple_passes=strategy.allow_multiple_passes,
        axial_cutting_depth=strategy.axial_cutting_depth,
        axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
    )


def _build_pocket_trajectory_xyz_sequences(
    state: PgmxState,
    spec: _HydratedPocketMillingSpec,
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    if spec.trajectory_sequences:
        return spec.trajectory_sequences

    if not spec.boss_contours and not spec.boss_route_seeds:
        return (_build_contour_parallel_xyz_path(state, spec),)

    trace_engine_sequences = _build_trace_engine_pocket_xyz_sequences(state, spec)
    if trace_engine_sequences is not None:
        return trace_engine_sequences

    controlled_sequences = _build_single_seed_base_loop_xyz_sequences(state, spec)
    if controlled_sequences is not None:
        return controlled_sequences

    cut_z = state.depth - float(_feature_depth_value(state, spec))
    controlled_multiloop = _build_single_seed_multiloop_curve_and_sequence(spec, cut_z)
    if controlled_multiloop is not None:
        _curve_spec, sequence = controlled_multiloop
        return (sequence,)

    raise NotImplementedError(
        "PocketMillingSpec con islas/BossGeometryList o semillas BossList.GeometryID "
        "se adapta para lectura, pero la serializacion productiva de Vaciado con islas "
        "todavia no esta implementada para esta configuracion."
    )


def _build_single_seed_base_loop_xyz_sequences(
    state: PgmxState,
    spec: _HydratedPocketMillingSpec,
) -> Optional[tuple[tuple[tuple[float, float, float], ...], ...]]:
    seed = _supported_single_seed_base_loop_route_seed(spec)
    if seed is None:
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    radii = _single_seed_base_loop_radii(spec, seed)
    cut_z = state.depth - float(_feature_depth_value(state, spec))

    exterior = _single_seed_exterior_rectangle_loops_xyz(
        (contour_min_x, contour_max_x, contour_min_y, contour_max_y),
        radii,
        cut_z,
    )
    island = tuple(
        (x, y, cut_z)
        for radius in radii
        for x, y in _rounded_kernel_loop_xy(
            (seed_min_x, seed_max_x, seed_min_y, seed_max_y),
            radius,
        )
    )
    return (exterior, island)


def _build_pocket_trajectory_curve_specs(
    spec: _HydratedPocketMillingSpec,
    trajectory_sequences: Sequence[Sequence[tuple[float, float, float]]],
) -> tuple[_CurveSpec, ...]:
    if spec.trajectory_curves and len(spec.trajectory_curves) == len(trajectory_sequences):
        return spec.trajectory_curves

    if not spec.boss_contours and not spec.boss_route_seeds:
        return tuple(_curve_spec_from_xyz_path(sequence) for sequence in trajectory_sequences)

    trace_engine_curves = _build_trace_engine_pocket_curve_specs(spec, trajectory_sequences)
    if trace_engine_curves is not None:
        return trace_engine_curves

    seed = _supported_single_seed_base_loop_route_seed(spec)
    if seed is not None and len(trajectory_sequences) == 2:
        cut_z = trajectory_sequences[1][0][2]
        seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
        radii = _single_seed_base_loop_radii(spec, seed)
        return (
            _curve_spec_from_xyz_path(trajectory_sequences[0]),
            _rounded_kernel_multi_loop_curve_spec(
                (seed_min_x, seed_max_x, seed_min_y, seed_max_y),
                radii,
                cut_z,
            ),
        )

    if len(trajectory_sequences) == 1 and trajectory_sequences[0]:
        cut_z = trajectory_sequences[0][0][2]
        controlled_multiloop = _build_single_seed_multiloop_curve_and_sequence(spec, cut_z)
        if controlled_multiloop is not None:
            curve_spec, _sequence = controlled_multiloop
            return (curve_spec,)

    return tuple(_curve_spec_from_xyz_path(sequence) for sequence in trajectory_sequences)


def _build_trace_engine_pocket_xyz_sequences(
    state: PgmxState,
    spec: _HydratedPocketMillingSpec,
) -> Optional[tuple[tuple[tuple[float, float, float], ...], ...]]:
    plan = _build_trace_engine_pocket_plan(spec, surface_z=state.depth)
    if plan is None or not plan.trajectory_sequences:
        return None
    return plan.trajectory_sequences


def _build_trace_engine_pocket_curve_specs(
    spec: _HydratedPocketMillingSpec,
    trajectory_sequences: Sequence[Sequence[tuple[float, float, float]]],
) -> Optional[tuple[_CurveSpec, ...]]:
    if not trajectory_sequences:
        return None
    plan = _build_trace_engine_pocket_plan(spec, surface_z=0.0)
    if plan is None:
        return None
    if len(plan.resolved_sequences) != len(trajectory_sequences):
        return None

    curve_specs: list[_CurveSpec] = []
    for resolved_sequence, trajectory_sequence in zip(plan.resolved_sequences, trajectory_sequences):
        if not trajectory_sequence:
            return None
        z_value = float(trajectory_sequence[0][2])
        curve_specs.append(_curve_spec_from_trace_resolved_sequence(resolved_sequence, z_value))
    return tuple(curve_specs)


def _build_trace_engine_pocket_plan(
    spec: _HydratedPocketMillingSpec,
    *,
    surface_z: float,
):
    from pgmx.vaciado_lab.trace_engine import generate_contour_parallel_pocket_trace

    plan = generate_contour_parallel_pocket_trace(spec, surface_z=surface_z)
    if plan.pending_stages:
        return None
    if not plan.resolved_sequences:
        return None
    return plan


def _curve_spec_from_trace_resolved_sequence(resolved_sequence, z_value: float) -> _CurveSpec:
    descriptions: list[str] = []
    for primitive in resolved_sequence.primitives:
        start = (primitive.start[0], primitive.start[1], z_value)
        end = (primitive.end[0], primitive.end[1], z_value)
        if primitive.primitive_type == "Line":
            descriptions.append(_build_toolpath_description(start, end))
            continue
        if primitive.primitive_type == "Arc":
            if primitive.center is None:
                raise ValueError("La primitiva Arc de Vaciado requiere centro.")
            normal_z = -1.0 if primitive.orientation == "Clockwise" else 1.0
            descriptions.append(
                _build_maestro_arc_serialization(
                    start,
                    end,
                    primitive.center,
                    normal_z,
                    z_value,
                    radius=primitive.radius,
                )
            )
            continue
        raise ValueError(f"Tipo de primitiva de Vaciado no soportado: {primitive.primitive_type}")
    if not descriptions:
        raise ValueError("La secuencia resuelta de Vaciado no contiene primitivas serializables.")
    return _composite_curve_spec(descriptions)


def _rounded_kernel_loop_curve_spec(
    kernel_bbox: tuple[float, float, float, float],
    radius: float,
    z_value: float,
) -> _CurveSpec:
    min_x, max_x, min_y, max_y = kernel_bbox
    diagonal = radius / math.sqrt(2.0)
    p0 = (min_x - radius, min_y, z_value)
    p1 = (min_x - radius, max_y, z_value)
    p2 = (min_x, max_y + radius, z_value)
    p3 = (max_x, max_y + radius, z_value)
    p4 = (max_x + diagonal, max_y + diagonal, z_value)
    p5 = (max_x + radius, max_y, z_value)
    p6 = (max_x + radius, min_y, z_value)
    p7 = (max_x, min_y - radius, z_value)
    p8 = (min_x, min_y - radius, z_value)

    return _composite_curve_spec(
        [
            _build_toolpath_description(p0, p1),
            _build_maestro_arc_serialization(p1, p2, (min_x, max_y), -1.0, z_value),
            _build_toolpath_description(p2, p3),
            _build_maestro_arc_serialization(p3, p4, (max_x, max_y), -1.0, z_value),
            _build_maestro_arc_serialization(p4, p5, (max_x, max_y), -1.0, z_value),
            _build_toolpath_description(p5, p6),
            _build_maestro_arc_serialization(p6, p7, (max_x, min_y), -1.0, z_value),
            _build_toolpath_description(p7, p8),
            _build_maestro_arc_serialization(p8, p0, (min_x, min_y), -1.0, z_value),
        ]
    )


def _rounded_kernel_multi_loop_curve_spec(
    kernel_bbox: tuple[float, float, float, float],
    radii: Sequence[float],
    z_value: float,
) -> _CurveSpec:
    descriptions: list[str] = []
    previous_start: Optional[tuple[float, float, float]] = None
    min_x, _max_x, min_y, _max_y = kernel_bbox
    for radius in radii:
        loop_start = (min_x - radius, min_y, z_value)
        if previous_start is not None:
            descriptions.append(_build_toolpath_description(previous_start, loop_start))
        loop_curve = _rounded_kernel_loop_curve_spec(kernel_bbox, radius, z_value)
        descriptions.extend(loop_curve.member_serializations)
        previous_start = loop_start
    return _composite_curve_spec(descriptions)


def _single_seed_exterior_rectangle_loops_xyz(
    contour_bbox: tuple[float, float, float, float],
    radii: Sequence[float],
    cut_z: float,
) -> tuple[tuple[float, float, float], ...]:
    contour_min_x, contour_max_x, contour_min_y, contour_max_y = contour_bbox
    points: list[tuple[float, float, float]] = []
    for index, radius in enumerate(radii):
        left = contour_min_x + radius
        right = contour_max_x - radius
        bottom = contour_min_y + radius
        top = contour_max_y - radius
        next_radius = radii[index + 1] if index + 1 < len(radii) else None

        if not points:
            points.append((left, top, cut_z))
        if next_radius is not None:
            points.append((left, contour_max_y - next_radius, cut_z))
        points.extend(
            (
                (left, bottom, cut_z),
                (right, bottom, cut_z),
                (right, top, cut_z),
                (left, top, cut_z),
            )
        )
        if next_radius is not None:
            next_left = contour_min_x + next_radius
            next_top = contour_max_y - next_radius
            points.extend(
                (
                    (left, next_top, cut_z),
                    (next_left, next_top, cut_z),
                )
            )
    return tuple(points)


@dataclass(frozen=True)
class _SingleSeedMultiloopRoute:
    seed: PocketBossRouteSeedSpec
    complete_radii: tuple[float, ...]
    partial_radii: tuple[float, ...]
    beta_angle: float
    bridge_radius: Optional[float] = None
    edge_boundary: bool = False


def _build_single_seed_multiloop_curve_and_sequence(
    spec: _HydratedPocketMillingSpec,
    cut_z: float,
) -> Optional[tuple[_CurveSpec, tuple[tuple[float, float, float], ...]]]:
    route = _supported_single_seed_multiloop_route(spec)
    if route is None:
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(route.seed.contour_points)
    max_complete = route.complete_radii[-1]
    min_partial = route.partial_radii[0] if route.partial_radii else None
    max_partial = route.partial_radii[-1] if route.partial_radii else None
    bridge_radius = route.bridge_radius
    if bridge_radius is not None and not route.partial_radii and not route.edge_boundary:
        return _build_single_seed_bridge_only_curve_and_sequence(route, cut_z, spec.contour_points)
    anchor_radius = bridge_radius if bridge_radius is not None else (max_partial or max_complete)
    anchor_x = contour_min_x + anchor_radius

    descriptions: list[str] = []
    points: list[tuple[float, float, float]] = [
        (anchor_x, contour_min_y + anchor_radius, cut_z)
    ]

    def point(x_value: float, y_value: float) -> tuple[float, float, float]:
        return (float(x_value), float(y_value), cut_z)

    def add_line(end_point: tuple[float, float, float]) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_toolpath_description(start_point, end_point))
        points.append(end_point)

    def add_arc(
        end_point: tuple[float, float, float],
        center_point: tuple[float, float],
    ) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_maestro_arc_serialization(start_point, end_point, center_point, -1.0, cut_z))
        points.append(end_point)

    def left_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def right_intersection_x(radius: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius * radius) - (delta_y * delta_y)))

    def beta_point(radius: float) -> tuple[float, float, float]:
        return point(
            seed_min_x + (radius * math.cos(route.beta_angle)),
            seed_min_y - (radius * math.sin(route.beta_angle)),
        )

    def add_complete_loop_from_right_bottom(radius: float) -> None:
        diagonal = radius / math.sqrt(2.0)

        add_line(point(seed_min_x, seed_min_y - radius))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y))
        add_line(point(seed_max_x, seed_max_y + radius))
        add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y))
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
        add_line(point(seed_max_x + radius, seed_min_y))
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y))

    if bridge_radius is not None:
        bridge_bottom_y = contour_min_y + bridge_radius
        bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - anchor_x) ** 2)))
        add_line(point(left_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y))
        add_arc(point(anchor_x, seed_min_y - bridge_y_delta), (seed_min_x, seed_min_y))
        add_line(point(anchor_x, bridge_bottom_y))
        add_line(point(anchor_x, contour_min_y + max_partial))

    for index, radius in enumerate(reversed(route.partial_radii)):
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        left_boundary_x = contour_min_x + radius
        next_radii = tuple(reversed(route.partial_radii))[index + 1 :]

        add_line(point(left_intersection_x(radius, seed_min_y, bottom_y), bottom_y))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(left_intersection_x(radius, seed_max_y, top_y), top_y), (seed_min_x, seed_max_y))
        add_line(point(left_boundary_x, top_y))
        if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
            add_line(point(left_boundary_x, contour_max_y - bridge_radius))
        add_line(point(left_boundary_x, bottom_y))
        add_line(point(anchor_x, bottom_y))
        if next_radii:
            add_line(point(anchor_x, contour_min_y + next_radii[0]))

    add_line(point(anchor_x, contour_min_y + max_complete))
    if route.edge_boundary:
        add_line(point(seed_max_x, contour_min_y + max_complete))
        add_complete_loop_from_right_bottom(max_complete)
    for index, radius in enumerate(reversed(route.complete_radii)):
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        right_x = contour_max_x - radius
        left_x = contour_min_x + radius
        remaining = tuple(reversed(route.complete_radii))[index + 1 :]

        add_line(point(right_x, bottom_y))
        add_line(point(right_x, top_y))
        if min_partial is not None and math.isclose(radius, max_complete, abs_tol=1e-6):
            add_line(point(contour_max_x - min_partial, top_y))
        add_line(point(left_x, top_y))
        add_line(point(left_x, bottom_y))
        add_line(point(anchor_x, bottom_y))
        if remaining:
            add_line(point(anchor_x, contour_min_y + remaining[0]))

    for radius in route.complete_radii[1:]:
        add_line(point(anchor_x, contour_min_y + radius))

    if route.edge_boundary:
        if min_partial is None or max_partial is None:
            return (_composite_curve_spec(descriptions), tuple(points))

        add_line(point(seed_max_x, contour_min_y + max_complete))
        add_complete_loop_from_right_bottom(max_complete)
        for radius in reversed(route.complete_radii[:-1]):
            add_line(point(seed_max_x, seed_min_y - radius))
            add_complete_loop_from_right_bottom(radius)
        for radius in route.complete_radii[1:]:
            add_line(point(seed_max_x, seed_min_y - radius))

        add_line(point(contour_max_x - max_complete, contour_min_y + max_complete))
        add_line(point(contour_max_x - max_complete, contour_max_y - max_complete))
        add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
        add_line(point(contour_max_x - min_partial, contour_max_y - min_partial))

        for index, radius in enumerate(route.partial_radii):
            top_y = contour_max_y - radius
            bottom_y = contour_min_y + radius
            right_boundary_x = contour_max_x - radius
            next_radii = route.partial_radii[index + 1 :]

            if next_radii:
                add_line(point(contour_max_x - next_radii[0], top_y))
            if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
                add_line(point(contour_max_x - bridge_radius, top_y))
            add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
            diagonal = radius / math.sqrt(2.0)
            diagonal_point = point(seed_max_x + diagonal, seed_max_y + diagonal)
            if top_y >= seed_max_y + diagonal - 1e-6:
                if math.hypot(diagonal_point[0] - points[-1][0], diagonal_point[1] - points[-1][1]) > 2.0:
                    add_arc(diagonal_point, (seed_max_x, seed_max_y))
                else:
                    add_line(diagonal_point)
            add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
            add_line(point(seed_max_x + radius, seed_min_y))
            add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
            add_line(point(right_boundary_x, bottom_y))
            if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
                bridge_anchor_x = contour_max_x - bridge_radius
                bridge_top_y = contour_max_y - bridge_radius
                bridge_bottom_y = contour_min_y + bridge_radius
                bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((bridge_anchor_x - seed_max_x) ** 2)))
                add_line(point(right_boundary_x, bridge_bottom_y))
                add_line(point(right_boundary_x, top_y))
                add_line(point(bridge_anchor_x, top_y))
                add_line(point(bridge_anchor_x, bridge_top_y))
                add_line(point(right_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y))
                add_arc(point(bridge_anchor_x, seed_max_y + bridge_y_delta), (seed_max_x, seed_max_y))
                add_line(point(bridge_anchor_x, bridge_top_y))
                add_line(point(bridge_anchor_x, top_y))
                add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
                add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
                add_line(point(seed_max_x + radius, seed_min_y))
                add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
                add_line(point(right_boundary_x, bottom_y))
                add_line(point(right_boundary_x, bridge_bottom_y))
                add_line(point(bridge_anchor_x, bridge_bottom_y))
                add_line(point(bridge_anchor_x, seed_min_y - bridge_y_delta))
                add_arc(
                    point(right_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y),
                    (seed_max_x, seed_min_y),
                )
                add_line(point(bridge_anchor_x, bridge_bottom_y))
                add_line(point(right_boundary_x, bridge_bottom_y))
            add_line(point(right_boundary_x, top_y))
            if next_radii:
                add_line(point(contour_max_x - next_radii[0], top_y))
                add_line(point(contour_max_x - next_radii[0], contour_max_y - next_radii[0]))

        for high_radius, low_radius in zip(reversed(route.partial_radii[1:]), reversed(route.partial_radii[:-1])):
            add_line(point(contour_max_x - high_radius, contour_max_y - low_radius))
            add_line(point(contour_max_x - low_radius, contour_max_y - low_radius))

        add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
        add_line(point(contour_min_x + max_complete, contour_max_y - max_complete))
        add_line(point(contour_min_x + max_complete, contour_min_y + max_complete))
        add_line(point(anchor_x, contour_min_y + max_complete))
        add_line(point(anchor_x, contour_min_y + min_partial))
        for radius in route.partial_radii[1:]:
            add_line(point(anchor_x, contour_min_y + radius))

        radius = max_partial
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        left_boundary_x = contour_min_x + radius
        add_line(point(left_intersection_x(radius, seed_min_y, bottom_y), bottom_y))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(left_intersection_x(radius, seed_max_y, top_y), top_y), (seed_min_x, seed_max_y))
        add_line(point(left_boundary_x, top_y))

        if bridge_radius is not None:
            bridge_top_y = contour_max_y - bridge_radius
            bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - anchor_x) ** 2)))
            add_line(point(left_boundary_x, bridge_top_y))
            add_line(point(anchor_x, bridge_top_y))
            add_line(point(anchor_x, seed_max_y + bridge_y_delta))
            add_arc(
                point(left_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y),
                (seed_min_x, seed_max_y),
            )
            add_line(point(anchor_x, bridge_top_y))

        return (_composite_curve_spec(descriptions), tuple(points))

    add_line(point(contour_max_x - max_complete, contour_min_y + max_complete))
    add_line(point(contour_max_x - max_complete, contour_max_y - max_complete))
    add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
    add_line(point(contour_max_x - min_partial, contour_max_y - min_partial))

    for index, radius in enumerate(route.partial_radii):
        top_y = contour_max_y - radius
        bottom_y = contour_min_y + radius
        right_boundary_x = contour_max_x - radius
        next_radii = route.partial_radii[index + 1 :]

        if next_radii:
            add_line(point(contour_max_x - next_radii[0], top_y))
        if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
            add_line(point(contour_max_x - bridge_radius, top_y))
        add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
        diagonal = radius / math.sqrt(2.0)
        diagonal_point = point(seed_max_x + diagonal, seed_max_y + diagonal)
        if top_y >= seed_max_y + diagonal - 1e-6:
            if math.hypot(diagonal_point[0] - points[-1][0], diagonal_point[1] - points[-1][1]) > 2.0:
                add_arc(diagonal_point, (seed_max_x, seed_max_y))
            else:
                add_line(diagonal_point)
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
        add_line(point(seed_max_x + radius, seed_min_y))
        add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
        add_line(point(right_boundary_x, bottom_y))
        if bridge_radius is not None and math.isclose(radius, max_partial, abs_tol=1e-6):
            bridge_anchor_x = contour_max_x - bridge_radius
            bridge_top_y = contour_max_y - bridge_radius
            bridge_bottom_y = contour_min_y + bridge_radius
            bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((bridge_anchor_x - seed_max_x) ** 2)))
            add_line(point(right_boundary_x, bridge_bottom_y))
            add_line(point(right_boundary_x, top_y))
            add_line(point(bridge_anchor_x, top_y))
            add_line(point(bridge_anchor_x, bridge_top_y))
            add_line(point(right_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y))
            add_arc(point(bridge_anchor_x, seed_max_y + bridge_y_delta), (seed_max_x, seed_max_y))
            add_line(point(bridge_anchor_x, bridge_top_y))
            add_line(point(bridge_anchor_x, top_y))
            add_line(point(right_intersection_x(radius, seed_max_y, top_y), top_y))
            add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
            add_line(point(seed_max_x + radius, seed_min_y))
            add_arc(point(right_intersection_x(radius, seed_min_y, bottom_y), bottom_y), (seed_max_x, seed_min_y))
            add_line(point(right_boundary_x, bottom_y))
            add_line(point(right_boundary_x, bridge_bottom_y))
            add_line(point(bridge_anchor_x, bridge_bottom_y))
            add_line(point(bridge_anchor_x, seed_min_y - bridge_y_delta))
            add_arc(point(right_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y), (seed_max_x, seed_min_y))
            add_line(point(bridge_anchor_x, bridge_bottom_y))
            add_line(point(right_boundary_x, bridge_bottom_y))
        add_line(point(right_boundary_x, top_y))
        if next_radii:
            add_line(point(contour_max_x - next_radii[0], top_y))
            add_line(point(contour_max_x - next_radii[0], contour_max_y - next_radii[0]))

    for high_radius, low_radius in zip(reversed(route.partial_radii[1:]), reversed(route.partial_radii[:-1])):
        add_line(point(contour_max_x - high_radius, contour_max_y - low_radius))
        add_line(point(contour_max_x - low_radius, contour_max_y - low_radius))

    add_line(point(contour_max_x - min_partial, contour_max_y - max_complete))
    add_line(point(contour_max_x - max_complete, contour_max_y - max_complete))
    add_line(point(contour_max_x - max_complete, contour_min_y + max_complete))
    add_line(point(anchor_x, contour_min_y + max_complete))
    add_line(point(anchor_x, contour_min_y + min_partial))
    add_line(point(left_intersection_x(min_partial, seed_min_y, contour_min_y + min_partial), contour_min_y + min_partial))
    add_line(beta_point(max_complete))

    for index, radius in enumerate(reversed(route.complete_radii)):
        next_radii = tuple(reversed(route.complete_radii))[index + 1 :]
        diagonal = radius / math.sqrt(2.0)

        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y))
        add_line(point(seed_max_x, seed_max_y + radius))
        add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y))
        add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
        add_line(point(seed_max_x + radius, seed_min_y))
        add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y))
        add_line(point(seed_min_x, seed_min_y - radius))
        add_arc(beta_point(radius), (seed_min_x, seed_min_y))
        if next_radii:
            add_line(beta_point(next_radii[0]))

    if bridge_radius is not None:
        for radius in route.complete_radii[1:]:
            add_line(beta_point(radius))

        add_line(point(left_intersection_x(min_partial, seed_min_y, contour_min_y + min_partial), contour_min_y + min_partial))
        add_line(point(anchor_x, contour_min_y + min_partial))
        for radius in route.partial_radii[1:]:
            add_line(point(anchor_x, contour_min_y + radius))

        radius = max_partial
        bottom_y = contour_min_y + radius
        top_y = contour_max_y - radius
        left_boundary_x = contour_min_x + radius
        add_line(point(left_intersection_x(radius, seed_min_y, bottom_y), bottom_y))
        add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
        add_line(point(seed_min_x - radius, seed_max_y))
        add_arc(point(left_intersection_x(radius, seed_max_y, top_y), top_y), (seed_min_x, seed_max_y))
        add_line(point(left_boundary_x, top_y))

        bridge_top_y = contour_max_y - bridge_radius
        bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - anchor_x) ** 2)))
        add_line(point(left_boundary_x, bridge_top_y))
        add_line(point(anchor_x, bridge_top_y))
        add_line(point(anchor_x, seed_max_y + bridge_y_delta))
        add_arc(point(left_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y), (seed_min_x, seed_max_y))
        add_line(point(anchor_x, bridge_top_y))

    return (_composite_curve_spec(descriptions), tuple(points))


def _build_single_seed_bridge_only_curve_and_sequence(
    route: _SingleSeedMultiloopRoute,
    cut_z: float,
    contour_points: Sequence[tuple[float, float]],
) -> tuple[_CurveSpec, tuple[tuple[float, float, float], ...]]:
    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(route.seed.contour_points)
    radius = route.complete_radii[-1]
    bridge_radius = route.bridge_radius
    if bridge_radius is None:
        raise ValueError("La ruta bridge-only requiere bridge_radius.")

    left_anchor_x = contour_min_x + bridge_radius
    right_anchor_x = contour_max_x - bridge_radius
    left_boundary_x = contour_min_x + radius
    right_boundary_x = contour_max_x - radius
    bottom_y = contour_min_y + radius
    top_y = contour_max_y - radius
    bridge_bottom_y = contour_min_y + bridge_radius
    bridge_top_y = contour_max_y - bridge_radius
    bridge_y_delta = math.sqrt(max(0.0, (bridge_radius * bridge_radius) - ((seed_min_x - left_anchor_x) ** 2)))
    diagonal = radius / math.sqrt(2.0)
    radius_angle_x = seed_min_x + (radius * ((left_anchor_x - seed_min_x) / bridge_radius))
    radius_angle_top_y = seed_max_y + (radius * (bridge_y_delta / bridge_radius))

    descriptions: list[str] = []
    points: list[tuple[float, float, float]] = [
        (left_anchor_x, bridge_top_y, cut_z)
    ]

    def point(x_value: float, y_value: float) -> tuple[float, float, float]:
        return (float(x_value), float(y_value), cut_z)

    def add_line(end_point: tuple[float, float, float]) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_toolpath_description(start_point, end_point))
        points.append(end_point)

    def add_arc(
        end_point: tuple[float, float, float],
        center_point: tuple[float, float],
    ) -> None:
        start_point = points[-1]
        if _points_are_close_3d(start_point, end_point):
            return
        descriptions.append(_build_maestro_arc_serialization(start_point, end_point, center_point, -1.0, cut_z))
        points.append(end_point)

    def left_intersection_x(radius_value: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_min_x - math.sqrt(max(0.0, (radius_value * radius_value) - (delta_y * delta_y)))

    def right_intersection_x(radius_value: float, center_y: float, y_value: float) -> float:
        delta_y = center_y - y_value
        return seed_max_x + math.sqrt(max(0.0, (radius_value * radius_value) - (delta_y * delta_y)))

    add_line(point(left_anchor_x, seed_max_y + bridge_y_delta))
    add_arc(
        point(left_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y),
        (seed_min_x, seed_max_y),
    )
    add_line(point(left_anchor_x, bridge_top_y))
    add_line(point(left_boundary_x, bridge_top_y))
    add_line(point(left_boundary_x, bottom_y))
    add_line(point(left_anchor_x, bottom_y))
    add_line(point(right_boundary_x, bottom_y))
    add_line(point(right_boundary_x, bridge_bottom_y))
    add_line(point(right_boundary_x, top_y))
    add_line(point(right_anchor_x, top_y))
    add_line(point(left_boundary_x, top_y))
    add_line(point(left_boundary_x, bridge_top_y))
    add_line(point(left_boundary_x, bottom_y))
    add_line(point(left_anchor_x, bottom_y))

    add_line(point(left_anchor_x, bridge_bottom_y))
    add_line(point(left_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y))
    add_arc(point(left_anchor_x, seed_min_y - bridge_y_delta), (seed_min_x, seed_min_y))
    add_line(point(left_anchor_x, bridge_bottom_y))
    add_line(point(left_anchor_x, bottom_y))

    add_line(point(right_boundary_x, bottom_y))
    add_line(point(right_boundary_x, bridge_bottom_y))
    add_line(point(right_anchor_x, bridge_bottom_y))
    add_line(point(right_anchor_x, seed_min_y - bridge_y_delta))
    add_arc(
        point(right_intersection_x(bridge_radius, seed_min_y, bridge_bottom_y), bridge_bottom_y),
        (seed_max_x, seed_min_y),
    )
    add_line(point(right_anchor_x, bridge_bottom_y))
    add_line(point(right_boundary_x, bridge_bottom_y))

    add_line(point(right_boundary_x, top_y))
    add_line(point(right_anchor_x, top_y))
    add_line(point(right_anchor_x, bridge_top_y))
    add_line(point(right_intersection_x(bridge_radius, seed_max_y, bridge_top_y), bridge_top_y))
    add_arc(point(right_anchor_x, seed_max_y + bridge_y_delta), (seed_max_x, seed_max_y))
    add_line(point(right_anchor_x, bridge_top_y))
    add_line(point(right_anchor_x, top_y))

    add_line(point(left_boundary_x, top_y))
    add_line(point(left_boundary_x, bridge_top_y))
    add_line(point(left_anchor_x, bridge_top_y))
    add_line(point(left_anchor_x, seed_max_y + bridge_y_delta))
    add_line(point(radius_angle_x, radius_angle_top_y))

    add_arc(point(seed_min_x, seed_max_y + radius), (seed_min_x, seed_max_y))
    add_line(point(seed_max_x, seed_max_y + radius))
    add_arc(point(seed_max_x + diagonal, seed_max_y + diagonal), (seed_max_x, seed_max_y))
    add_arc(point(seed_max_x + radius, seed_max_y), (seed_max_x, seed_max_y))
    add_line(point(seed_max_x + radius, seed_min_y))
    add_arc(point(seed_max_x, seed_min_y - radius), (seed_max_x, seed_min_y))
    add_line(point(seed_min_x, seed_min_y - radius))
    add_arc(point(seed_min_x - radius, seed_min_y), (seed_min_x, seed_min_y))
    add_line(point(seed_min_x - radius, seed_max_y))
    add_arc(point(radius_angle_x, radius_angle_top_y), (seed_min_x, seed_max_y))

    return (_composite_curve_spec(descriptions), tuple(points))


def _supported_single_seed_base_loop_route_seed(
    spec: _HydratedPocketMillingSpec,
) -> Optional[PocketBossRouteSeedSpec]:
    seed = _supported_single_seed_base_loop_seed(spec)
    if seed is None:
        return None
    if not _single_seed_base_loop_radii(spec, seed):
        return None
    return seed


def _supported_single_seed_base_loop_seed(
    spec: _HydratedPocketMillingSpec,
) -> Optional[PocketBossRouteSeedSpec]:
    if len(spec.boss_contours) != 1 or len(spec.boss_route_seeds) != 1:
        return None
    seed = spec.boss_route_seeds[0]
    if not seed.is_resolved:
        return None
    if not _same_xy_bbox(spec.boss_contours[0], seed.contour_points):
        return None
    if spec.plane_name != "Top" or spec.milling_strategy.allow_multiple_passes:
        return None
    if spec.milling_strategy.inside_to_outside:
        if spec.milling_strategy.stroke_connection_strategy != "LiftShiftPlunge":
            return None
    elif spec.milling_strategy.stroke_connection_strategy != "Straghtline":
        return None
    return seed


def _single_seed_base_loop_radii(
    spec: _HydratedPocketMillingSpec,
    seed: PocketBossRouteSeedSpec,
) -> tuple[float, ...]:
    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    if not math.isclose(seed_max_x - seed_min_x, 50.0, abs_tol=1e-6):
        return ()
    if not math.isclose(seed_max_y - seed_min_y, 50.0, abs_tol=1e-6):
        return ()
    clearances = (
        seed_min_x - contour_min_x,
        contour_max_x - seed_max_x,
        seed_min_y - contour_min_y,
        contour_max_y - seed_max_y,
    )
    if min(clearances) <= 0.0:
        return ()
    if not math.isclose(clearances[0], clearances[1], abs_tol=1e-6):
        return ()
    if not math.isclose(clearances[2], clearances[3], abs_tol=1e-6):
        return ()

    half_min_clearance = min(clearances) / 2.0
    radial_step = spec.radial_step
    if radial_step <= 0.0:
        return ()
    if not math.isclose(radial_step, 40.0, abs_tol=1e-6):
        return ()
    if radial_step > half_min_clearance + 1e-6:
        return ()
    count = int(math.floor((half_min_clearance + 1e-6) / radial_step))
    if count < 1:
        return ()
    return tuple(radial_step * multiplier for multiplier in range(1, count + 1))


def _supported_single_seed_multiloop_route(
    spec: _HydratedPocketMillingSpec,
) -> Optional[_SingleSeedMultiloopRoute]:
    seed = _supported_single_seed_route_seed(spec)
    if seed is None:
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    left_clearance = seed_min_x - contour_min_x
    right_clearance = contour_max_x - seed_max_x
    bottom_clearance = seed_min_y - contour_min_y
    top_clearance = contour_max_y - seed_max_y
    horizontal_half_clearance = min(left_clearance, right_clearance) / 2.0
    vertical_half_clearance = min(bottom_clearance, top_clearance) / 2.0
    radial_step = spec.radial_step
    if radial_step <= 0.0:
        return None

    radius_count = int(math.floor((horizontal_half_clearance + 1e-6) / radial_step))
    radii = tuple(radial_step * multiplier for multiplier in range(1, radius_count + 1))
    complete_radii = tuple(radius for radius in radii if radius <= vertical_half_clearance + 1e-6)
    partial_radii = tuple(radius for radius in radii if radius > vertical_half_clearance + 1e-6)
    if not complete_radii:
        return None
    edge_boundary = math.isclose(complete_radii[-1], vertical_half_clearance, abs_tol=1e-6)

    next_radius = radial_step * (radius_count + 1)
    bridge_radius = None
    if 0.0 < (next_radius - horizontal_half_clearance) <= 2.0:
        bridge_radius = next_radius
    if not partial_radii and not edge_boundary and bridge_radius is None:
        return None

    beta_angle = 0.0
    if partial_radii:
        min_partial = partial_radii[0]
        partial_bottom_y = contour_min_y + min_partial
        sin_beta = (seed_min_y - partial_bottom_y) / min_partial
        if sin_beta <= -1.0 or sin_beta >= 1.0:
            return None
        beta_angle = math.pi - math.asin(sin_beta)
    return _SingleSeedMultiloopRoute(
        seed=seed,
        complete_radii=complete_radii,
        partial_radii=partial_radii,
        beta_angle=beta_angle,
        bridge_radius=bridge_radius,
        edge_boundary=edge_boundary,
    )


def _supported_single_seed_route_seed(
    spec: _HydratedPocketMillingSpec,
) -> Optional[PocketBossRouteSeedSpec]:
    if len(spec.boss_contours) != 1 or len(spec.boss_route_seeds) != 1:
        return None
    seed = spec.boss_route_seeds[0]
    if not seed.is_resolved:
        return None
    if not _same_xy_bbox(spec.boss_contours[0], seed.contour_points):
        return None
    if spec.plane_name != "Top" or spec.milling_strategy.allow_multiple_passes:
        return None
    if not spec.milling_strategy.inside_to_outside:
        return None
    if spec.milling_strategy.stroke_connection_strategy != "LiftShiftPlunge":
        return None

    contour_min_x, contour_max_x, contour_min_y, contour_max_y = _xy_bbox_minmax(spec.contour_points)
    seed_min_x, seed_max_x, seed_min_y, seed_max_y = _xy_bbox_minmax(seed.contour_points)
    clearances = (
        seed_min_x - contour_min_x,
        contour_max_x - seed_max_x,
        seed_min_y - contour_min_y,
        contour_max_y - seed_max_y,
    )
    if min(clearances) <= 0.0:
        return None
    if not math.isclose(clearances[0], clearances[1], abs_tol=1e-6):
        return None
    if not math.isclose(clearances[2], clearances[3], abs_tol=1e-6):
        return None
    return seed


def _rounded_kernel_loop_xy(
    kernel_bbox: tuple[float, float, float, float],
    radius: float,
) -> tuple[tuple[float, float], ...]:
    min_x, max_x, min_y, max_y = kernel_bbox
    diagonal = radius / math.sqrt(2.0)
    return (
        (min_x - radius, min_y),
        (min_x - radius, max_y),
        (min_x, max_y + radius),
        (max_x, max_y + radius),
        (max_x + diagonal, max_y + diagonal),
        (max_x + radius, max_y),
        (max_x + radius, min_y),
        (max_x, min_y - radius),
        (min_x, min_y - radius),
        (min_x - radius, min_y),
    )


def _xy_bbox_minmax(points: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    if not xs or not ys:
        raise ValueError("No se puede calcular bbox de una geometria vacia.")
    return (min(xs), max(xs), min(ys), max(ys))


def _same_xy_bbox(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    return all(
        math.isclose(left, right, abs_tol=tolerance)
        for left, right in zip(_xy_bbox_minmax(first), _xy_bbox_minmax(second))
    )


def _points_are_close_3d(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    *,
    tolerance: float = 1e-9,
) -> bool:
    return (
        math.isclose(first[0], second[0], abs_tol=tolerance)
        and math.isclose(first[1], second[1], abs_tol=tolerance)
        and math.isclose(first[2], second[2], abs_tol=tolerance)
    )


def _curve_spec_from_xyz_path(points: Sequence[tuple[float, float, float]]) -> _CurveSpec:
    descriptions: list[str] = []
    for start_point, end_point in zip(points, points[1:]):
        if _points_are_close_3d(start_point, end_point):
            continue
        descriptions.append(_build_toolpath_description(start_point, end_point))
    if not descriptions:
        raise ValueError("La trayectoria de Vaciado no contiene segmentos serializables.")
    return _composite_curve_spec(descriptions)


def _build_pocket_operation(
    state: PgmxState,
    spec: _HydratedPocketMillingSpec,
    operation_id: str,
    trajectory_curves: Sequence[_CurveSpec],
    trajectory_curve_member_keys: Sequence[Sequence[str]],
    trajectory_sequences: Sequence[Sequence[tuple[float, float, float]]],
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:BottomAndSideRoughMilling"},
    )
    _set_xmlns(operation, "a", MILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideRoughMilling")
    _append_blank_name(operation)
    _append_node(operation, PGMX_NS, "ActivateCNCCorrection", "false")
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)

    if not trajectory_sequences:
        raise ValueError("La estrategia ContourParallel no genero trayectoria para el Vaciado.")
    first_sequence = trajectory_sequences[0]
    last_sequence = trajectory_sequences[-1]
    if not first_sequence or not last_sequence:
        raise ValueError("La estrategia ContourParallel genero una trayectoria vacia para el Vaciado.")
    first_point = first_sequence[0]
    last_point = last_sequence[-1]
    clearance_z = state.depth + spec.security_plane
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            _trimmed_curve_spec(
                _build_toolpath_description(
                    (first_point[0], first_point[1], clearance_z),
                    first_point,
                )
            ),
        )
    )
    if len(trajectory_curves) != len(trajectory_curve_member_keys):
        raise ValueError("Cantidad inconsistente de curvas y claves de trayectoria para Vaciado.")
    for trajectory_curve, member_keys in zip(trajectory_curves, trajectory_curve_member_keys):
        toolpath_list.append(
            _build_toolpath(
                "TrajectoryPath",
                trajectory_curve,
                generated_member_keys=member_keys,
            )
        )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            _trimmed_curve_spec(
                _build_toolpath_description(
                    last_point,
                    (last_point[0], last_point[1], clearance_z),
                )
            ),
        )
    )
    _append_node(operation, PGMX_NS, "ToolpathPriority", "true")
    _append_node(operation, PGMX_NS, "AdditionalToolKeys", "")
    _append_node(operation, PGMX_NS, "ApproachSecurityPlane", _compact_number(spec.security_plane))
    _append_node(operation, PGMX_NS, "Head", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(operation, PGMX_NS, "HeadRotation", "0")
    _append_node(operation, PGMX_NS, "MachineFunctions", "")
    _append_node(operation, PGMX_NS, "RetractSecurityPlane", _compact_number(spec.security_plane))
    operation.append(_build_start_point(0.0, 0.0, 0.0))
    technology = _append_node(
        operation,
        PGMX_NS,
        "Technology",
        attrib={f"{{{XSI_NS}}}type": "MillingTechnology"},
    )
    _append_node(technology, PGMX_NS, "Feedrate", "0")
    _append_node(technology, PGMX_NS, "CutSpeed", "0")
    _append_node(technology, PGMX_NS, "Spindle", "0")
    _append_object_ref(
        operation,
        PGMX_NS,
        "ToolKey",
        spec.tool_id,
        "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
        include_name=True,
        name_text=spec.tool_name,
    )
    _append_node(operation, PGMX_NS, "OvercutLength", _compact_number(_operation_overcut_length(spec)))
    approach = _append_node(
        operation,
        PGMX_NS,
        "Approach",
        attrib={f"{{{XSI_NS}}}type": "b:BaseApproachStrategy"},
    )
    _set_xmlns(approach, "b", STRATEGY_NS)
    _append_node(approach, STRATEGY_NS, "ApproachArcSide", spec.approach.arc_side)
    _append_node(approach, STRATEGY_NS, "ApproachMode", spec.approach.mode)
    _append_node(approach, STRATEGY_NS, "ApproachType", spec.approach.approach_type)
    _append_node(approach, STRATEGY_NS, "IsEnabled", "true" if spec.approach.is_enabled else "false")
    _append_node(approach, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.approach.radius_multiplier))
    _append_node(approach, STRATEGY_NS, "Speed", _compact_number(spec.approach.speed))
    retract = _append_node(
        operation,
        PGMX_NS,
        "Retract",
        attrib={f"{{{XSI_NS}}}type": "b:BaseRetractStrategy"},
    )
    _set_xmlns(retract, "b", STRATEGY_NS)
    _append_node(retract, STRATEGY_NS, "IsEnabled", "true" if spec.retract.is_enabled else "false")
    _append_node(retract, STRATEGY_NS, "OverLap", _compact_number(spec.retract.overlap))
    _append_node(retract, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.retract.radius_multiplier))
    _append_node(retract, STRATEGY_NS, "RetractArcSide", spec.retract.arc_side)
    _append_node(retract, STRATEGY_NS, "RetractMode", spec.retract.mode)
    _append_node(retract, STRATEGY_NS, "RetractType", spec.retract.retract_type)
    _append_node(retract, STRATEGY_NS, "Speed", _compact_number(spec.retract.speed))
    operation.append(_build_milling_strategy_node(spec))
    _append_node(operation, PGMX_NS, "AllowanceBottom", _compact_number(spec.allowance_bottom))
    _append_node(operation, PGMX_NS, "AllowanceSide", _compact_number(spec.allowance_side))
    return operation


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
    _append_blank_name(step).text = "Xn"
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    if spec.y is None:
        geometry_ref = _append_node(step, BASE_MODEL_NS, "GeometryID")
        _append_node(geometry_ref, UTILITY_NS, "ID", "0")
        _append_node(geometry_ref, UTILITY_NS, "ObjectType", attrib={f"{{{XSI_NS}}}nil": "true"})
        _set_xmlns(geometry_ref, "a", UTILITY_NS)
    else:
        _append_node(step, BASE_MODEL_NS, "GeometryID", attrib={f"{{{XSI_NS}}}nil": "true"})

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "Reference", spec.reference)
    _append_node(step, BASE_MODEL_NS, "Speed", "0")
    _append_node(step, BASE_MODEL_NS, "SpindleEnable", "Off")

    tool_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "Tool",
        "0",
        "System.Object",
        include_name=True,
        name_text="",
    )
    _set_xmlns(tool_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "X", _compact_number(spec.x))
    if spec.y is None:
        _append_node(step, BASE_MODEL_NS, "Y", attrib={f"{{{XSI_NS}}}nil": "true"})
    else:
        _append_node(step, BASE_MODEL_NS, "Y", _compact_number(spec.y))
    return step


def _append_line_milling(root: ET.Element, state: PgmxState, spec: _HydratedLineMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None
    generated_toolpath_profile = _build_line_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    trajectory_curve_member_keys: tuple[str, ...] = ()
    next_generated_aux_id = int(end_expression_id or step_id) + 1
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
        member_count = len(trajectory_curve.member_serializations)
        trajectory_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys or trajectory_curve_member_keys,
            toolpath_start=toolpath_start,
            toolpath_end=toolpath_end,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _append_slot_milling(root: ET.Element, state: PgmxState, spec: _HydratedSlotMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar la ranura.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None
    generated_toolpath_profile = _build_line_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_slot_side_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            lift_curve=lift_curve,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys,
            toolpath_start=toolpath_start,
            toolpath_end=toolpath_end,
        )
    )
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.Milling.SlotSide",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _append_curve_profile_milling(
    root: ET.Element,
    state: PgmxState,
    spec,
    generated_geometry_curve: _CurveSpec,
    generated_toolpath_profile: GeometryProfileSpec,
) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)

    geometry_member_count = len(generated_geometry_curve.member_serializations)
    reserved_ids = _reserve_ids(
        root,
        geometry_member_count + (6 if uses_depth_expressions else 4),
        spec.preferred_id_start,
    )
    geometry_id = reserved_ids[0]
    generated_geometry_member_keys: tuple[str, ...] = ()
    if generated_geometry_curve.geometry_type == "GeomCompositeCurve" and not generated_geometry_curve.member_keys:
        generated_geometry_member_keys = tuple(reserved_ids[1 : 1 + geometry_member_count])

    operation_index = 1 + geometry_member_count
    operation_id = reserved_ids[operation_index]
    feature_id = reserved_ids[operation_index + 1]
    step_id = reserved_ids[operation_index + 2]
    start_expression_id = reserved_ids[operation_index + 3] if uses_depth_expressions else None
    end_expression_id = reserved_ids[operation_index + 4] if uses_depth_expressions else None

    generated_trajectory_curve = _curve_spec_from_profile_geometry(generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or generated_trajectory_curve
    start_point, end_point, _, _ = _profile_entry_exit_context(generated_toolpath_profile)

    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)

    next_generated_aux_id = int(end_expression_id or step_id) + 1
    trajectory_curve_member_keys: tuple[str, ...] = ()
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
        if trajectory_curve.member_serializations == generated_geometry_curve.member_serializations:
            trajectory_curve_member_keys = generated_geometry_curve.member_keys or generated_geometry_member_keys
        else:
            member_count = len(trajectory_curve.member_serializations)
            trajectory_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
            next_generated_aux_id += member_count

    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(
        _build_polyline_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            generated_geometry_curve,
            generated_member_keys=generated_geometry_member_keys,
        )
    )
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            _geometry_object_type(generated_geometry_curve.geometry_type),
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys or trajectory_curve_member_keys,
            toolpath_start=start_point,
            toolpath_end=end_point,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _append_polyline_milling(root: ET.Element, state: PgmxState, spec: _HydratedPolylineMillingSpec) -> None:
    if spec.geometry_curve is not None:
        generated_geometry_curve = spec.geometry_curve
    elif _is_closed_polyline_points(spec.points):
        generated_geometry_curve = _curve_spec_from_profile_geometry(
            _build_closed_polyline_geometry_profile(spec.points, z_value=0.0)
        )
    else:
        generated_geometry_curve = _composite_curve_spec(_build_open_polyline_descriptions(spec.points))
    generated_toolpath_profile = _build_polyline_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        generated_geometry_curve,
        generated_toolpath_profile,
    )


def _append_circle_milling(root: ET.Element, state: PgmxState, spec: _HydratedCircleMillingSpec) -> None:
    generated_geometry_curve = spec.geometry_curve or _curve_spec_from_profile_geometry(
        build_circle_geometry_profile(
            spec.center_x,
            spec.center_y,
            spec.radius,
            z_value=0.0,
            winding=spec.winding,
        )
    )
    generated_toolpath_profile = _build_circle_toolpath_profile(float(state.depth), _toolpath_cut_z(state, spec), spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        generated_geometry_curve,
        generated_toolpath_profile,
    )


def _append_squaring_milling(root: ET.Element, state: PgmxState, spec: _HydratedSquaringMillingSpec) -> None:
    generated_geometry_profile = _build_squaring_geometry_profile(state, spec, z_value=0.0)
    generated_toolpath_profile = _build_squaring_toolpath_profile(state, _toolpath_cut_z(state, spec), spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        spec.geometry_curve or _curve_spec_from_profile_geometry(generated_geometry_profile),
        generated_toolpath_profile,
    )


def _append_pocket_milling(root: ET.Element, state: PgmxState, spec: _HydratedPocketMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el Vaciado.")

    if not _is_closed_polyline_points(spec.contour_points):
        raise ValueError("PocketMillingSpec requiere un contorno cerrado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)

    trajectory_sequences = _build_pocket_trajectory_xyz_sequences(state, spec)
    boundary_curve = spec.geometry_curve or _curve_spec_from_profile_geometry(
        _build_closed_polyline_geometry_profile(spec.contour_points, z_value=0.0)
    )
    boundary_member_count = len(boundary_curve.member_serializations)
    boss_geometry_curves = tuple(
        _curve_spec_from_profile_geometry(_build_closed_polyline_geometry_profile(boss_contour, z_value=0.0))
        for boss_contour in spec.boss_contours
    )
    boss_geometry_member_count = sum(len(curve.member_serializations) for curve in boss_geometry_curves)
    route_seed_curves = tuple(
        _curve_spec_from_profile_geometry(_build_closed_polyline_geometry_profile(seed.contour_points, z_value=0.0))
        for seed in spec.boss_route_seeds
        if seed.is_resolved
    )
    route_seed_member_count = sum(1 + len(curve.member_serializations) for curve in route_seed_curves)
    trajectory_curves = _build_pocket_trajectory_curve_specs(spec, trajectory_sequences)
    trajectory_member_counts = tuple(len(curve.member_serializations) for curve in trajectory_curves)
    trajectory_member_count = sum(trajectory_member_counts)
    reserve_count = (
        1
        + boundary_member_count
        + boss_geometry_member_count
        + route_seed_member_count
        + (6 if uses_depth_expressions else 4)
        + trajectory_member_count
    )
    reserved_ids = _reserve_ids(root, reserve_count, spec.preferred_id_start)
    geometry_id = reserved_ids[0]
    boundary_member_keys = tuple(reserved_ids[1 : 1 + boundary_member_count])
    cursor = 1 + boundary_member_count
    boss_geometry_specs: list[tuple[_CurveSpec, tuple[str, ...]]] = []
    for boss_curve in boss_geometry_curves:
        boss_member_keys = tuple(reserved_ids[cursor : cursor + len(boss_curve.member_serializations)])
        cursor += len(boss_curve.member_serializations)
        boss_geometry_specs.append((boss_curve, boss_member_keys))
    route_seed_geometry_specs: list[tuple[PocketBossRouteSeedSpec, str, _CurveSpec, tuple[str, ...]]] = []
    for seed, curve in zip((seed for seed in spec.boss_route_seeds if seed.is_resolved), route_seed_curves):
        seed_geometry_id = reserved_ids[cursor]
        cursor += 1
        seed_member_keys = tuple(reserved_ids[cursor : cursor + len(curve.member_serializations)])
        cursor += len(curve.member_serializations)
        route_seed_geometry_specs.append((seed, seed_geometry_id, curve, seed_member_keys))
    operation_index = cursor
    operation_id = reserved_ids[operation_index]
    feature_id = reserved_ids[operation_index + 1]
    step_id = reserved_ids[operation_index + 2]
    start_expression_id = reserved_ids[operation_index + 3] if uses_depth_expressions else None
    end_expression_id = reserved_ids[operation_index + 4] if uses_depth_expressions else None
    trajectory_index = operation_index + (5 if uses_depth_expressions else 3)
    trajectory_member_keys: list[tuple[str, ...]] = []
    cursor = trajectory_index
    for member_count in trajectory_member_counts:
        trajectory_member_keys.append(tuple(reserved_ids[cursor : cursor + member_count]))
        cursor += member_count

    geometries.append(
        _build_polyline_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            boundary_curve,
            generated_member_keys=boundary_curve.member_keys or boundary_member_keys,
        )
    )
    for _seed, seed_geometry_id, seed_curve, seed_member_keys in route_seed_geometry_specs:
        geometries.append(
            _build_polyline_geometry(
                seed_geometry_id,
                plane_id,
                plane_object_type,
                seed_curve,
                generated_member_keys=seed_curve.member_keys or seed_member_keys,
            )
        )
    features.append(
        _build_closed_pocket_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            _geometry_object_type(boundary_curve.geometry_type),
            boundary_curve,
            boundary_curve.member_keys or boundary_member_keys,
            boss_geometry_curves=tuple(
                (boss_curve, boss_curve.member_keys or boss_member_keys)
                for boss_curve, boss_member_keys in boss_geometry_specs
            ),
            boss_route_seed_refs=tuple(
                (
                    seed,
                    seed_geometry_id,
                    _geometry_object_type(seed_curve.geometry_type),
                )
                for seed, seed_geometry_id, seed_curve, _seed_member_keys in route_seed_geometry_specs
            ),
        )
    )
    operations.append(
        _build_pocket_operation(
            state,
            spec,
            operation_id,
            trajectory_curves,
            tuple(
                trajectory_curve.member_keys or member_keys
                for trajectory_curve, member_keys in zip(trajectory_curves, trajectory_member_keys)
            ),
            trajectory_sequences,
        )
    )
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.ClosedPocket",
            operation_object_type="ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideRoughMilling",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


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


def _ensure_xn_step(root: ET.Element, xn: XnSpec) -> None:
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if elements is None or workpiece is None:
        raise ValueError("La plantilla no contiene MainWorkplan/Elements o WorkPiece para sintetizar Xn.")

    for executable in list(elements):
        if _xsi_type(executable) == "Xn":
            elements.remove(executable)

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    [step_id] = _reserve_ids(root, 1)
    elements.append(_build_xn_step(step_id, workpiece_id, workpiece_object_type, _normalize_xn_spec(xn)))


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
    )


def synthesize_request(request: PgmxSynthesisRequest) -> PgmxSynthesisResult:
    """Ejecuta una solicitud de sintesis y escribe el `.pgmx` resultante.

    Esta es la funcion principal para el flujo programatico.
    """

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
    _validate_tool_sinking_lengths(
        request.piece,
        hydrated_line_millings + ordered_line_millings,
        hydrated_slot_millings + ordered_slot_millings,
        hydrated_polyline_millings + ordered_polyline_millings,
        hydrated_circle_millings + ordered_circle_millings,
        hydrated_squaring_millings + ordered_squaring_millings,
        hydrated_pocket_millings + ordered_pocket_millings,
        hydrated_drillings + ordered_drillings,
        hydrated_drilling_patterns + ordered_drilling_patterns,
    )

    _apply_piece_state(baseline_root, request.piece)
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
        xn=normalized_xn,
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
    )
    return synthesize_request(request).piece


# ============================================================================
# CLI
# ============================================================================

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sintetiza un PGMX base a partir de un baseline Maestro (.pgmx, Pieza.xml o carpeta)."
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE_DIR),
        help=(
            "Ruta al baseline Maestro: `.pgmx`, `Pieza.xml` o carpeta contenedora. "
            "Si no se indica, usa `pgmx/data/maestro_baselines`."
        ),
    )
    parser.add_argument("--output", required=True, help="Ruta del .pgmx sintetizado de salida.")
    parser.add_argument(
        "--source-pgmx",
        "--source-template",
        dest="source_pgmx",
        help=(
            "Ruta a una plantilla manual de Maestro (`.pgmx`, `Pieza.xml` o carpeta) "
            "desde la cual copiar serializacion ya validada."
        ),
    )
    parser.add_argument("--piece-name", help="Nombre interno de la pieza dentro del .pgmx.")
    parser.add_argument("--length", type=float, help="Largo final de la pieza (dx1).")
    parser.add_argument("--width", type=float, help="Ancho final de la pieza (dy1).")
    parser.add_argument("--depth", type=float, help="Espesor final de la pieza (dz1).")
    parser.add_argument("--origin-x", type=float, help="Origen de mecanizado X.")
    parser.add_argument("--origin-y", type=float, help="Origen de mecanizado Y.")
    parser.add_argument("--origin-z", type=float, help="Origen de mecanizado Z.")
    parser.add_argument(
        "--execution-fields",
        "--area",
        dest="execution_fields",
        help="Area de Parametros de Maquina. Valores observados: A, EF, HG. Si no se indica, la sintesis usa HG.",
    )
    parser.add_argument("--line-x1", type=float, help="Coordenada X inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y1", type=float, help="Coordenada Y inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-x2", type=float, help="Coordenada X final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y2", type=float, help="Coordenada Y final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-feature-name", help="Nombre del feature/working step del fresado lineal.")
    parser.add_argument("--line-side-of-feature", help="Correccion de herramienta del fresado lineal: Center, Right o Left.")
    parser.add_argument("--line-tool-id", help="ID de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-name", help="Nombre de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-width", type=float, help="Ancho del perfil barrido para el fresado lineal.")
    parser.add_argument("--line-security-plane", type=float, help="Plano de seguridad usado en approach/retract.")
    parser.add_argument(
        "--line-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado lineal. Por defecto queda activado.",
    )
    parser.add_argument(
        "--line-target-depth",
        type=float,
        help="Profundidad fija del fresado lineal cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--line-extra-depth",
        type=float,
        help="Extra del fresado lineal cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--line-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1."
        ),
    )
    parser.add_argument("--line-approach-type", help="Tipo de approach. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-approach-mode",
        help="Modo de approach. Valores utiles: Down o Quote (UI Maestro: En Cota). Para Arc se valido Quote.",
    )
    parser.add_argument(
        "--line-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach lineal.",
    )
    parser.add_argument(
        "--line-approach-speed",
        type=float,
        help="Velocidad del approach. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-approach-arc-side",
        help="Lado del arco del approach. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1/overlap 0."
        ),
    )
    parser.add_argument("--line-retract-type", help="Tipo de retract. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-retract-mode",
        help="Modo de retract. Valores utiles: Up o Quote (UI Maestro: En Cota). Para Arc se validaron Quote y Up.",
    )
    parser.add_argument(
        "--line-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract lineal.",
    )
    parser.add_argument(
        "--line-retract-speed",
        type=float,
        help="Velocidad del retract. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-retract-arc-side",
        help="Lado del arco del retract. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-overlap",
        type=float,
        help="Sobreposicion del retract lineal.",
    )
    parser.add_argument("--circle-center-x", type=float, help="Coordenada X del centro del circulo sobre Top.")
    parser.add_argument("--circle-center-y", type=float, help="Coordenada Y del centro del circulo sobre Top.")
    parser.add_argument("--circle-radius", type=float, help="Radio del circulo a fresar sobre Top.")
    parser.add_argument("--circle-winding", help="Sentido del circulo: CounterClockwise/Antihorario o Clockwise/Horario.")
    parser.add_argument("--circle-feature-name", help="Nombre del feature/working step del fresado circular.")
    parser.add_argument("--circle-side-of-feature", help="Correccion de herramienta del fresado circular: Center, Right o Left.")
    parser.add_argument("--circle-tool-id", help="ID de herramienta para el fresado circular.")
    parser.add_argument("--circle-tool-name", help="Nombre de herramienta para el fresado circular.")
    parser.add_argument("--circle-tool-width", type=float, help="Ancho del perfil barrido para el fresado circular.")
    parser.add_argument("--circle-security-plane", type=float, help="Plano de seguridad usado en approach/retract del circulo.")
    parser.add_argument(
        "--circle-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado circular. Por defecto queda activado.",
    )
    parser.add_argument(
        "--circle-target-depth",
        type=float,
        help="Profundidad fija del fresado circular cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--circle-extra-depth",
        type=float,
        help="Extra del fresado circular cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--circle-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado circular. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro."
        ),
    )
    parser.add_argument("--circle-approach-type", help="Tipo de approach del circulo. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--circle-approach-mode",
        help="Modo de approach del circulo. Valores utiles: Down o Quote (UI Maestro: En Cota).",
    )
    parser.add_argument(
        "--circle-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach circular.",
    )
    parser.add_argument(
        "--circle-approach-speed",
        type=float,
        help="Velocidad del approach del circulo. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--circle-approach-arc-side",
        help="Lado del arco del approach circular. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--circle-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado circular. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro."
        ),
    )
    parser.add_argument("--circle-retract-type", help="Tipo de retract del circulo. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--circle-retract-mode",
        help="Modo de retract del circulo. Valores utiles: Up o Quote (UI Maestro: En Cota).",
    )
    parser.add_argument(
        "--circle-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract circular.",
    )
    parser.add_argument(
        "--circle-retract-speed",
        type=float,
        help="Velocidad del retract del circulo. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--circle-retract-arc-side",
        help="Lado del arco del retract circular. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--circle-retract-overlap",
        type=float,
        help="Sobreposicion del retract circular.",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output)
    line_milling = build_line_milling_spec(
        line_x1=args.line_x1,
        line_y1=args.line_y1,
        line_x2=args.line_x2,
        line_y2=args.line_y2,
        line_feature_name=args.line_feature_name,
        line_side_of_feature=args.line_side_of_feature,
        line_tool_id=args.line_tool_id,
        line_tool_name=args.line_tool_name,
        line_tool_width=args.line_tool_width,
        line_security_plane=args.line_security_plane,
        line_is_through=args.line_through,
        line_target_depth=args.line_target_depth,
        line_extra_depth=args.line_extra_depth,
        line_approach_enabled=args.line_approach_enabled,
        line_approach_type=args.line_approach_type,
        line_approach_mode=args.line_approach_mode,
        line_approach_radius_multiplier=args.line_approach_radius_multiplier,
        line_approach_speed=args.line_approach_speed,
        line_approach_arc_side=args.line_approach_arc_side,
        line_retract_enabled=args.line_retract_enabled,
        line_retract_type=args.line_retract_type,
        line_retract_mode=args.line_retract_mode,
        line_retract_radius_multiplier=args.line_retract_radius_multiplier,
        line_retract_speed=args.line_retract_speed,
        line_retract_arc_side=args.line_retract_arc_side,
        line_retract_overlap=args.line_retract_overlap,
    )
    circle_args = (args.circle_center_x, args.circle_center_y, args.circle_radius)
    if all(value is None for value in circle_args):
        circle_milling = None
    elif any(value is None for value in circle_args):
        raise ValueError(
            "Para sintetizar el fresado circular hay que indicar center_x, center_y y radius."
        )
    else:
        circle_milling = build_circle_milling_spec(
            center_x=float(args.circle_center_x),
            center_y=float(args.circle_center_y),
            radius=float(args.circle_radius),
            winding=args.circle_winding,
            feature_name=args.circle_feature_name,
            tool_id=args.circle_tool_id,
            tool_name=args.circle_tool_name,
            tool_width=args.circle_tool_width,
            security_plane=args.circle_security_plane,
            side_of_feature=args.circle_side_of_feature,
            is_through=args.circle_through,
            target_depth=args.circle_target_depth,
            extra_depth=args.circle_extra_depth,
            approach_enabled=args.circle_approach_enabled,
            approach_type=args.circle_approach_type,
            approach_mode=args.circle_approach_mode,
            approach_radius_multiplier=args.circle_approach_radius_multiplier,
            approach_speed=args.circle_approach_speed,
            approach_arc_side=args.circle_approach_arc_side,
            retract_enabled=args.circle_retract_enabled,
            retract_type=args.circle_retract_type,
            retract_mode=args.circle_retract_mode,
            retract_radius_multiplier=args.circle_retract_radius_multiplier,
            retract_speed=args.circle_retract_speed,
            retract_arc_side=args.circle_retract_arc_side,
            retract_overlap=args.circle_retract_overlap,
        )
    request = build_synthesis_request(
        baseline_path=Path(args.baseline),
        output_path=output_path,
        source_pgmx_path=Path(args.source_pgmx) if args.source_pgmx else None,
        piece_name=args.piece_name,
        length=args.length,
        width=args.width,
        depth=args.depth,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        origin_z=args.origin_z,
        execution_fields=args.execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
        circle_millings=[circle_milling] if circle_milling is not None else (),
    )
    result = synthesize_request(request)

    summary = {
        "output": str(output_path),
        "piece_name": result.piece.piece_name,
        "length": _compact_number(result.piece.length),
        "width": _compact_number(result.piece.width),
        "depth": _compact_number(result.piece.depth),
        "origin_x": _compact_number(result.piece.origin_x),
        "origin_y": _compact_number(result.piece.origin_y),
        "origin_z": _compact_number(result.piece.origin_z),
        "execution_fields": result.piece.execution_fields,
        "sha256": result.sha256,
    }
    if line_milling is not None:
        summary["line_milling"] = {
            "feature_name": line_milling.feature_name,
            "start": [_compact_number(line_milling.start_x), _compact_number(line_milling.start_y)],
            "end": [_compact_number(line_milling.end_x), _compact_number(line_milling.end_y)],
            "side_of_feature": line_milling.side_of_feature,
            "tool_id": line_milling.tool_id,
            "tool_name": line_milling.tool_name,
            "tool_width": _compact_number(line_milling.tool_width),
            "security_plane": _compact_number(line_milling.security_plane),
            "approach": {
                "is_enabled": line_milling.approach.is_enabled,
                "approach_type": line_milling.approach.approach_type,
                "mode": line_milling.approach.mode,
                "radius_multiplier": _compact_number(line_milling.approach.radius_multiplier),
                "speed": _compact_number(line_milling.approach.speed),
                "arc_side": line_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": line_milling.retract.is_enabled,
                "retract_type": line_milling.retract.retract_type,
                "mode": line_milling.retract.mode,
                "radius_multiplier": _compact_number(line_milling.retract.radius_multiplier),
                "speed": _compact_number(line_milling.retract.speed),
                "arc_side": line_milling.retract.arc_side,
                "overlap": _compact_number(line_milling.retract.overlap),
            },
        }
    if circle_milling is not None:
        summary["circle_milling"] = {
            "feature_name": circle_milling.feature_name,
            "center": [_compact_number(circle_milling.center_x), _compact_number(circle_milling.center_y)],
            "radius": _compact_number(circle_milling.radius),
            "winding": circle_milling.winding,
            "side_of_feature": circle_milling.side_of_feature,
            "tool_id": circle_milling.tool_id,
            "tool_name": circle_milling.tool_name,
            "tool_width": _compact_number(circle_milling.tool_width),
            "security_plane": _compact_number(circle_milling.security_plane),
            "approach": {
                "is_enabled": circle_milling.approach.is_enabled,
                "approach_type": circle_milling.approach.approach_type,
                "mode": circle_milling.approach.mode,
                "radius_multiplier": _compact_number(circle_milling.approach.radius_multiplier),
                "speed": _compact_number(circle_milling.approach.speed),
                "arc_side": circle_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": circle_milling.retract.is_enabled,
                "retract_type": circle_milling.retract.retract_type,
                "mode": circle_milling.retract.mode,
                "radius_multiplier": _compact_number(circle_milling.retract.radius_multiplier),
                "speed": _compact_number(circle_milling.retract.speed),
                "arc_side": circle_milling.retract.arc_side,
                "overlap": _compact_number(circle_milling.retract.overlap),
            },
        }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
