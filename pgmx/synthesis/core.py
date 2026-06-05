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

import math

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
    _normalize_side_of_feature,
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
    _build_down_arc_entry_curve,
    _build_down_line_entry_curve,
    _build_generated_approach_curve,
    _build_generated_approach_curve_for_profile,
    _build_generated_lift_curve,
    _build_generated_lift_curve_for_profile,
    _build_oriented_maestro_arc_basis,
    _build_quote_arc_entry_curve,
    _build_quote_arc_exit_curve,
    _build_up_arc_exit_curve,
    _build_up_line_exit_curve,
    _build_vertical_toolpath_curve,
    _dominant_component_sign_2d,
    _extract_approach_spec_from_operation,
    _extract_retract_spec_from_operation,
    _linear_lead_distance,
    _normalize_approach_arc_side,
    _normalize_approach_mode,
    _normalize_approach_spec,
    _normalize_approach_type,
    _normalize_retract_arc_side,
    _normalize_retract_mode,
    _normalize_retract_spec,
    _normalize_retract_type,
    _preferred_side_for_arc,
    _quote_arc_radius,
    _side_normal_for_direction,
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
    DEFAULT_BASELINE_DIR,
    DEFAULT_BASELINE_XML_PATH,
    DEFAULT_MACHINING_ORDER,
    HydratedMachiningSpec,
    MachiningSpec,
    MODULE_DIR,
    PgmxState,
    PgmxSynthesisRequest,
    PgmxSynthesisResult,
    SYNTHESIZER_VERSION,
    XnSpec,
    _apply_circle_millings,
    _apply_drilling_patterns,
    _apply_drillings,
    _append_hydrated_machining,
    _apply_line_millings,
    _apply_piece_state,
    _apply_pocket_millings,
    _apply_polyline_millings,
    _apply_slot_millings,
    _apply_squaring_millings,
    _build_xn_step,
    _drilling_plane_priority,
    _ensure_xn_step,
    _finalize_pgmx_xml_bytes,
    _finalize_synthesized_pgmx_xml_bytes,
    _hydrate_machining_spec,
    _merge_state,
    _module_data_dir,
    _normalize_execution_fields,
    _normalize_machining_order,
    _normalize_xn_reference,
    _normalize_xn_spec,
    _split_hydrated_machinings,
    _validate_tool_sinking_lengths,
    _write_pgmx_zip,
    build_synthesis_request,
    build_xn_spec,
    read_pgmx_state,
    synthesize_pgmx,
    synthesize_request,
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
    _build_profile_feature,
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
    _append_line_milling,
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
    _append_circle_milling,
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
    _append_curve_profile_milling,
    _append_polyline_milling,
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
    _SingleSeedMultiloopRoute,
    _append_pocket_milling,
    _build_closed_pocket_boss,
    _build_closed_pocket_feature,
    _build_contour_parallel_xyz_path,
    _build_pocket_operation,
    _build_pocket_trajectory_curve_specs,
    _build_pocket_trajectory_xyz_sequences,
    _build_single_seed_base_loop_xyz_sequences,
    _build_single_seed_bridge_only_curve_and_sequence,
    _build_single_seed_multiloop_curve_and_sequence,
    _build_trace_engine_pocket_curve_specs,
    _build_trace_engine_pocket_plan,
    _build_trace_engine_pocket_xyz_sequences,
    _can_hydrate_pocket_template_trace,
    _curve_spec_from_trace_resolved_sequence,
    _curve_spec_from_xyz_path,
    _extract_pocket_milling_template,
    _hydrate_pocket_milling_spec,
    _points_are_close_3d,
    _rounded_kernel_loop_curve_spec,
    _rounded_kernel_loop_xy,
    _rounded_kernel_multi_loop_curve_spec,
    _same_xy_bbox,
    _same_xy_contours,
    _same_xy_points,
    _single_seed_base_loop_radii,
    _single_seed_exterior_rectangle_loops_xyz,
    _supported_single_seed_base_loop_route_seed,
    _supported_single_seed_base_loop_seed,
    _supported_single_seed_multiloop_route,
    _supported_single_seed_route_seed,
    _xy_bbox_minmax,
    build_pocket_boss_route_seed_spec,
    build_pocket_milling_spec,
)
from .milling.slot import (
    SlotMillingSpec,
    _HydratedSlotMillingSpec,
    _append_slot_milling,
    _build_slot_side_feature,
    _hydrate_slot_milling_spec,
    _normalize_slot_milling_spec,
    build_slot_milling_spec,
)
from .milling.squaring import (
    SquaringMillingSpec,
    _HydratedSquaringMillingSpec,
    _append_squaring_milling,
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


# ============================================================================
# Compatibility helpers
# ============================================================================

# Alias de compatibilidad: la implementacion CLI vive en `pgmx.synthesis.cli`.
from .cli import main  # noqa: E402
