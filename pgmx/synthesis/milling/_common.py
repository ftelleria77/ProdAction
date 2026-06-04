"""Shared helpers for PGMX milling family modules."""

from __future__ import annotations

import math

from ..common.depth import _normalize_milling_depth_spec
from ..common.geometry import (
    _normalize_geometry_winding,
    _normalize_side_of_feature,
)
from ..common.piece import _normalize_plane_name
from ..common.tools import (
    TOOL_CATALOG_PATH,
    _is_vertical_x_saw,
    _normalize_tool_usage_group,
    _tool_catalog_label,
    _validate_tool_sinking_length_for_total_depth,
)

__all__ = [
    "_normalize_geometry_winding",
    "_normalize_side_of_feature",
    "_feature_bottom_condition_type",
    "_feature_depth_value",
    "_operation_overcut_length",
    "_tool_total_milling_depth",
    "_toolpath_cut_z",
    "_uses_feature_depth_expressions",
    "_validate_tool_sinking_length_for_spec",
    "_validate_tool_type_for_milling_spec",
    "_validate_vertical_x_saw_for_milling_spec",
]


def _feature_depth_value(state, spec) -> float:
    # En Maestro, un pasante deja `Depth.StartDepth/EndDepth` igual al espesor
    # actual de la pieza y luego agrega expresiones parametricas hacia `DepthName`.
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    if depth_spec.target_depth > state.depth + 1e-9:
        raise ValueError("La profundidad del fresado no pasante no puede superar el espesor de la pieza.")
    return depth_spec.target_depth


def _tool_total_milling_depth(state, spec) -> float:
    """Calcula la profundidad total efectiva que debe alcanzar la herramienta."""

    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth + depth_spec.extra_depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    return depth_spec.target_depth


def _toolpath_cut_z(state, spec) -> float:
    # Regla validada en Maestro:
    # - no pasante: `cut_z = espesor - target_depth`
    # - pasante: `cut_z = -extra_depth`
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return -depth_spec.extra_depth
    return state.depth - _feature_depth_value(state, spec)


def _feature_bottom_condition_type(spec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return "a:ThroughMillingBottom" if depth_spec.is_through else "a:GeneralMillingBottom"


def _operation_overcut_length(spec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return depth_spec.extra_depth if depth_spec.is_through else 0.0


def _uses_feature_depth_expressions(spec) -> bool:
    return _normalize_milling_depth_spec(spec.depth_spec).is_through


def _is_hydrated_line_or_slot_milling_spec(spec) -> bool:
    return type(spec).__name__ in {"_HydratedLineMillingSpec", "_HydratedSlotMillingSpec"}


def _is_hydrated_slot_milling_spec(spec) -> bool:
    return type(spec).__name__ == "_HydratedSlotMillingSpec"


def _validate_tool_sinking_length_for_spec(
    state,
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    """Valida que la profundidad total no supere el `sinking_length` de la herramienta."""

    catalog_entry = tool_catalog.get(spec.tool_id)
    _validate_tool_sinking_length_for_total_depth(
        spec,
        catalog_entry,
        total_depth=_tool_total_milling_depth(state, spec),
        operation_name="fresado",
    )


def _validate_vertical_x_saw_for_milling_spec(spec, tool_type: str) -> None:
    if not _is_hydrated_line_or_slot_milling_spec(spec):
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite ranurados lineales rectos."
        )

    if _normalize_plane_name(spec.plane_name) != "Top":
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite ranurados sobre el plano Top."
        )

    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite ranurados no pasantes."
        )

    if not math.isclose(float(spec.start_y), float(spec.end_y), abs_tol=1e-9):
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite líneas horizontales."
        )


def _validate_tool_type_for_milling_spec(spec, tool_catalog: dict[str, dict[str, str]]) -> None:
    catalog_entry = tool_catalog.get(spec.tool_id)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar el tipo de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    tool_type = (catalog_entry.get("type") or "").strip()
    usage_group = _normalize_tool_usage_group(tool_type)
    if _is_hydrated_slot_milling_spec(spec):
        if not _is_vertical_x_saw(tool_type):
            raise ValueError(
                "La ranura `SlotSide` requiere una Sierra Vertical X compatible: "
                f"{_tool_catalog_label(spec)} figura como '{tool_type or 'sin tipo'}'."
            )
        _validate_vertical_x_saw_for_milling_spec(spec, tool_type)
        return
    if usage_group == "milling":
        return
    if _is_vertical_x_saw(tool_type):
        _validate_vertical_x_saw_for_milling_spec(spec, tool_type)
        return
    if usage_group != "milling":
        raise ValueError(
            "El fresado requiere una herramienta de tipo Fresa/Freza, "
            "o bien una Sierra Vertical X en modo ranurado horizontal no pasante: "
            f"{_tool_catalog_label(spec)} figura como '{tool_type or 'sin tipo'}'."
        )
