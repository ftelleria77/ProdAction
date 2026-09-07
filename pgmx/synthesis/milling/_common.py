"""Shared helpers for PGMX milling family modules."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from ..common.depth import _normalize_milling_depth_spec
from ..common.geometry import (
    _build_identity_profile_placement,
    _normalize_geometry_winding,
    _normalize_side_of_feature,
)
from ..common.piece import _normalize_plane_name
from ..common.tools import (
    TOOL_CATALOG_PATH,
    _is_vertical_x_saw,
    _normalize_tool_usage_group,
    _catalog_row_for_spec,
    _tool_catalog_label,
    _validate_tool_sinking_length_for_total_depth,
)
from ..common.xml import (
    MILLING_NS,
    PGMX_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _compact_number,
    _qname,
    _set_xmlns,
)

__all__ = [
    "_normalize_geometry_winding",
    "_normalize_side_of_feature",
    "_build_profile_feature",
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


def _build_profile_feature(
    state,
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
    # Autoría de los flags del feature (directiva Fermín 2026-07-04): salen del spec; los
    # defaults reproducen los bytes históricos. getattr: specs sin estos campos (slot) → default.
    _append_node(feature, PGMX_NS, "IsGeomSameDirection",
                 "false" if getattr(spec, "invert_work", False) else "true")
    _append_node(feature, PGMX_NS, "IsPrecise",
                 "true" if getattr(spec, "is_precise", False) else "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", "Left")
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", "0")
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", "0")
    _append_node(feature, PGMX_NS, "SideOfFeature", spec.side_of_feature)
    _append_node(feature, PGMX_NS, "SideOffset", _compact_number(getattr(spec, "side_offset", 0.0)))
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


def _is_hydrated_line_or_slot_milling_spec(spec) -> bool:
    return type(spec).__name__ in {"_HydratedLineSpec", "_HydratedChannelSpec"}


def _is_hydrated_slot_milling_spec(spec) -> bool:
    return type(spec).__name__ == "_HydratedChannelSpec"


def _is_hydrated_line_milling_spec(spec) -> bool:
    return type(spec).__name__ == "_HydratedLineSpec"


def _validate_tool_sinking_length_for_spec(
    state,
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    """Valida que la profundidad total no supere el `sinking_length` de la herramienta."""

    catalog_entry = _catalog_row_for_spec(spec, tool_catalog)
    _validate_tool_sinking_length_for_total_depth(
        spec,
        catalog_entry,
        total_depth=_tool_total_milling_depth(state, spec),
        operation_name="fresado",
    )


def _validate_vertical_x_saw_for_milling_spec(spec, tool_type: str) -> None:
    """Los limites del DISCO, medidos sobre fixtures (`iso/docs/experiments/canal.md`).

    ⚠️ Valen para una herramienta de tipo disco, **no para el `Canal` en general**:
    el lote D2 probo las ocho herramientas del desplegable y con una fresa el canal
    admite Y y diagonal (§19, §23).
    """

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
        # Winxiso: «Angulo no valido del perfil con herramienta de tipo fresa de
        # disco». Medido con el perpendicular y el diagonal del Grupo 3.
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite líneas horizontales."
        )


def _validate_tool_type_for_milling_spec(spec, tool_catalog: dict[str, dict[str, str]]) -> None:
    catalog_entry = _catalog_row_for_spec(spec, tool_catalog)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar el tipo de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    tool_type = (catalog_entry.get("type") or "").strip()
    # Fresado LINEAL: no se distingue el tipo de herramienta. Una sierra (p.ej. E002 Sierra
    # Horizontal) se programa igual que una fresa en una línea; el uso/recorrido es responsabilidad
    # del programador de Maestro.
    if _is_hydrated_line_milling_spec(spec):
        return
    usage_group = _normalize_tool_usage_group(tool_type)
    if _is_hydrated_slot_milling_spec(spec):
        # ⚠️ CORREGIDO 2026-09-07 con el lote D2. Acá se exigía una Sierra Vertical X,
        # y es FALSO: el desplegable de la ventana de Canal ofrece **las ocho**
        # herramientas del catálogo, y las siete `E00x` postprocesan (`canal.md` §23).
        # Lo que sí es del disco son sus límites —ángulo 0, cara superior y
        # profundidad ≤ `SinkingLength`—, que se validan sólo para él.
        if _is_vertical_x_saw(tool_type):
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
