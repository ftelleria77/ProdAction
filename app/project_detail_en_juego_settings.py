"""Settings normalization helpers for the En-Juego configuration dialog."""

from app.settings import (
    _coerce_setting_bool,
    _coerce_setting_number,
    _compact_number,
    _is_forty_five_degree_milling_tool,
    _is_helical_tool_type,
    _resolve_en_juego_cutting_tool,
    _resolve_en_juego_nesting_spacing_mm,
)


def normalize_en_juego_dialog_settings(
    settings: dict,
    *,
    cut_mode: str,
    origin_x,
    origin_y,
    origin_z,
    division_squaring_order: str,
) -> dict:
    normalized = dict(settings)
    normalized["cut_mode"] = "nesting" if str(cut_mode).strip().lower() == "nesting" else "manual"
    normalized["origin_x"] = _compact_number(
        _coerce_setting_number(origin_x, normalized.get("origin_x", 0.0))
    )
    normalized["origin_y"] = _compact_number(
        _coerce_setting_number(origin_y, normalized.get("origin_y", 0.0))
    )
    normalized["origin_z"] = _compact_number(
        _coerce_setting_number(origin_z, normalized.get("origin_z", 0.0))
    )
    normalized["division_squaring_order"] = (
        "squaring_then_division"
        if str(division_squaring_order).strip() == "squaring_then_division"
        else "division_then_squaring"
    )

    normalized["cutting_is_through"] = _coerce_setting_bool(
        normalized.get("cutting_is_through"),
        True,
    )
    normalized["cutting_depth_value"] = _compact_number(
        _coerce_setting_number(
            normalized.get("cutting_depth_value"),
            1.0,
            minimum=0.0,
        )
    )
    normalized["approach_enabled"] = _coerce_setting_bool(
        normalized.get("approach_enabled"),
        False,
    )
    normalized["approach_type"] = (
        "Arc" if str(normalized.get("approach_type") or "Arc").strip().lower() == "arc" else "Line"
    )
    normalized["approach_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            normalized.get("approach_radius_multiplier"),
            2.0,
            minimum=0.0,
        )
    )
    normalized["approach_mode"] = (
        "Quote"
        if str(normalized.get("approach_mode") or "Quote").strip().lower() == "quote"
        else "Down"
    )
    normalized["retract_enabled"] = _coerce_setting_bool(
        normalized.get("retract_enabled"),
        False,
    )
    normalized["retract_type"] = (
        "Arc" if str(normalized.get("retract_type") or "Arc").strip().lower() == "arc" else "Line"
    )
    normalized["retract_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            normalized.get("retract_radius_multiplier"),
            2.0,
            minimum=0.0,
        )
    )
    normalized["retract_mode"] = (
        "Quote"
        if str(normalized.get("retract_mode") or "Quote").strip().lower() == "quote"
        else "Up"
    )

    normalized["squaring_is_through"] = _coerce_setting_bool(
        normalized.get("squaring_is_through"),
        True,
    )
    normalized["squaring_depth_value"] = _compact_number(
        _coerce_setting_number(
            normalized.get("squaring_depth_value"),
            1.0,
            minimum=0.0,
        )
    )
    normalized["squaring_approach_enabled"] = _coerce_setting_bool(
        normalized.get("squaring_approach_enabled"),
        False,
    )
    normalized["squaring_approach_type"] = (
        "Arc"
        if str(normalized.get("squaring_approach_type") or "Arc").strip().lower() == "arc"
        else "Line"
    )
    normalized["squaring_approach_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            normalized.get("squaring_approach_radius_multiplier"),
            2.0,
            minimum=0.0,
        )
    )
    normalized["squaring_approach_mode"] = (
        "Quote"
        if str(normalized.get("squaring_approach_mode") or "Quote").strip().lower() == "quote"
        else "Down"
    )
    normalized["squaring_retract_enabled"] = _coerce_setting_bool(
        normalized.get("squaring_retract_enabled"),
        False,
    )
    normalized["squaring_retract_type"] = (
        "Arc"
        if str(normalized.get("squaring_retract_type") or "Arc").strip().lower() == "arc"
        else "Line"
    )
    normalized["squaring_retract_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            normalized.get("squaring_retract_radius_multiplier"),
            2.0,
            minimum=0.0,
        )
    )
    normalized["squaring_retract_mode"] = (
        "Quote"
        if str(normalized.get("squaring_retract_mode") or "Quote").strip().lower() == "quote"
        else "Up"
    )

    squaring_tool = _resolve_en_juego_cutting_tool(normalized.get("squaring_tool_id"))
    normalized["squaring_tool_id"] = str(
        normalized.get("squaring_tool_id")
        or squaring_tool.get("tool_id")
        or ""
    ).strip()
    normalized["squaring_tool_code"] = str(
        normalized.get("squaring_tool_code")
        or squaring_tool.get("tool_code")
        or ""
    ).strip()
    normalized["squaring_tool_name"] = str(
        normalized.get("squaring_tool_name")
        or squaring_tool.get("tool_name")
        or ""
    ).strip()
    normalized["squaring_tool_diameter"] = _compact_number(
        _coerce_setting_number(
            normalized.get("squaring_tool_diameter"),
            _coerce_setting_number(squaring_tool.get("diameter"), 0.0, minimum=0.0),
            minimum=0.0,
        )
    )

    cutting_tool = _resolve_en_juego_cutting_tool(normalized.get("cutting_tool_id"))
    normalized["cutting_tool_id"] = str(
        normalized.get("cutting_tool_id")
        or cutting_tool.get("tool_id")
        or ""
    ).strip()
    normalized["cutting_tool_code"] = str(
        normalized.get("cutting_tool_code")
        or cutting_tool.get("tool_code")
        or ""
    ).strip()
    normalized["cutting_tool_name"] = str(
        normalized.get("cutting_tool_name")
        or cutting_tool.get("tool_name")
        or ""
    ).strip()
    normalized["cutting_tool_diameter"] = _compact_number(
        _coerce_setting_number(
            normalized.get("cutting_tool_diameter"),
            _coerce_setting_number(cutting_tool.get("diameter"), 0.0, minimum=0.0),
            minimum=0.0,
        )
    )

    return normalized


def en_juego_depth_role_text(is_through: bool, *, operation_label: str) -> str:
    return "Profundidad extra" if is_through else f"Profundidad de {operation_label}"


def en_juego_effective_piece_spacing_mm(
    *,
    cut_mode: str,
    app_cut_settings: dict,
    en_juego_settings: dict,
    material_thickness_mm: float,
) -> float:
    if str(cut_mode or "").strip().lower() != "nesting":
        return max(
            0.0,
            _coerce_setting_number(
                app_cut_settings.get("cut_squaring_allowance"),
                10.0,
                minimum=0.0,
            )
            + _coerce_setting_number(
                app_cut_settings.get("cut_saw_kerf"),
                4.0,
                minimum=0.0,
            ),
        )

    return _resolve_en_juego_nesting_spacing_mm(
        en_juego_settings,
        material_thickness_mm=material_thickness_mm,
    )


def division_tool_hint_text(
    current_tool: dict,
    current_settings: dict,
    *,
    material_thickness_mm: float,
) -> str:
    spacing_value = _resolve_en_juego_nesting_spacing_mm(
        current_settings,
        material_thickness_mm=material_thickness_mm,
    )
    if spacing_value <= 0:
        return "No hay una herramienta de corte disponible para definir la separacion."

    if _is_forty_five_degree_milling_tool(current_tool.get("tool_type")):
        if _coerce_setting_bool(current_settings.get("cutting_is_through"), True):
            return (
                "Con Fresa 45º, la separacion minima entre piezas contiguas sera de "
                f"{_compact_number(spacing_value)} mm, a razon de 2 mm por cada 1 mm "
                "de profundidad extra."
            )
        return (
            "Con Fresa 45º, la separacion minima entre piezas contiguas sera de "
            f"{_compact_number(spacing_value)} mm, calculada respecto del espesor "
            f"de {_compact_number(material_thickness_mm)} mm."
        )

    if _is_helical_tool_type(current_tool.get("tool_type")):
        return (
            "Herramienta preferente para dividir En-Juego. "
            "La separacion minima entre piezas contiguas sera de "
            f"{_compact_number(spacing_value)} mm."
        )

    return (
        "La separacion minima entre piezas contiguas sera de "
        f"{_compact_number(spacing_value)} mm."
    )


def squaring_tool_hint_text(current_tool: dict) -> str:
    diameter_value = _coerce_setting_number(current_tool.get("diameter"), 0.0, minimum=0.0)
    if diameter_value > 0:
        return f"Herramienta de escuadrado seleccionada: Ø {_compact_number(diameter_value)} mm."
    return "No hay una herramienta disponible para el escuadrado."


def apply_en_juego_division_dialog_settings(
    settings: dict,
    *,
    selected_tool: dict,
    origin_x,
    origin_y,
    origin_z,
    cutting_is_through: bool,
    cutting_depth_value,
    cutting_multipass_enabled: bool,
    cutting_path_mode,
    cutting_pocket_depth,
    cutting_last_pocket,
    approach_enabled: bool,
    approach_type,
    approach_radius_multiplier,
    approach_mode,
    retract_enabled: bool,
    retract_type,
    retract_radius_multiplier,
    retract_mode,
) -> dict:
    updated = dict(settings)
    updated["origin_x"] = _compact_number(
        _coerce_setting_number(origin_x, updated.get("origin_x", 0.0))
    )
    updated["origin_y"] = _compact_number(
        _coerce_setting_number(origin_y, updated.get("origin_y", 0.0))
    )
    updated["origin_z"] = _compact_number(
        _coerce_setting_number(origin_z, updated.get("origin_z", 0.0))
    )
    updated["cutting_tool_id"] = str(selected_tool.get("tool_id") or "").strip()
    updated["cutting_tool_code"] = str(selected_tool.get("tool_code") or "").strip()
    updated["cutting_tool_name"] = str(selected_tool.get("tool_name") or "").strip()
    updated["cutting_tool_diameter"] = _compact_number(
        _coerce_setting_number(selected_tool.get("diameter"), 0.0, minimum=0.0)
    )
    updated["cutting_is_through"] = bool(cutting_is_through)
    updated["cutting_depth_value"] = _compact_number(
        _coerce_setting_number(
            cutting_depth_value,
            updated.get("cutting_depth_value", 1.0),
            minimum=0.0,
        )
    )
    updated["cutting_multipass_enabled"] = bool(cutting_multipass_enabled)
    updated["cutting_path_mode"] = str(cutting_path_mode or "Unidirectional")
    updated["cutting_pocket_depth"] = _compact_number(
        _coerce_setting_number(
            cutting_pocket_depth,
            updated.get("cutting_pocket_depth", 0.0),
            minimum=0.0,
        )
    )
    updated["cutting_last_pocket"] = _compact_number(
        _coerce_setting_number(
            cutting_last_pocket,
            updated.get("cutting_last_pocket", 0.0),
            minimum=0.0,
        )
    )
    updated["approach_enabled"] = bool(approach_enabled)
    updated["approach_type"] = str(approach_type or "Arc")
    updated["approach_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            approach_radius_multiplier,
            updated.get("approach_radius_multiplier", 2.0),
            minimum=0.0,
        )
    )
    updated["approach_mode"] = str(approach_mode or "Quote")
    updated["retract_enabled"] = bool(retract_enabled)
    updated["retract_type"] = str(retract_type or "Arc")
    updated["retract_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            retract_radius_multiplier,
            updated.get("retract_radius_multiplier", 2.0),
            minimum=0.0,
        )
    )
    updated["retract_mode"] = str(retract_mode or "Quote")
    return updated


def apply_en_juego_squaring_dialog_settings(
    settings: dict,
    *,
    selected_tool: dict,
    squaring_is_through: bool,
    squaring_depth_value,
    squaring_approach_enabled: bool,
    squaring_approach_type,
    squaring_approach_radius_multiplier,
    squaring_approach_mode,
    squaring_retract_enabled: bool,
    squaring_retract_type,
    squaring_retract_radius_multiplier,
    squaring_retract_mode,
    squaring_direction,
    squaring_unidirectional_multipass: bool,
    squaring_pocket_depth,
    squaring_last_pocket,
) -> dict:
    updated = dict(settings)
    updated["squaring_tool_id"] = str(selected_tool.get("tool_id") or "").strip()
    updated["squaring_tool_code"] = str(selected_tool.get("tool_code") or "").strip()
    updated["squaring_tool_name"] = str(selected_tool.get("tool_name") or "").strip()
    updated["squaring_tool_diameter"] = _compact_number(
        _coerce_setting_number(selected_tool.get("diameter"), 0.0, minimum=0.0)
    )
    updated["squaring_is_through"] = bool(squaring_is_through)
    updated["squaring_depth_value"] = _compact_number(
        _coerce_setting_number(
            squaring_depth_value,
            updated.get("squaring_depth_value", 1.0),
            minimum=0.0,
        )
    )
    updated["squaring_approach_enabled"] = bool(squaring_approach_enabled)
    updated["squaring_approach_type"] = str(squaring_approach_type or "Arc")
    updated["squaring_approach_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            squaring_approach_radius_multiplier,
            updated.get("squaring_approach_radius_multiplier", 2.0),
            minimum=0.0,
        )
    )
    updated["squaring_approach_mode"] = str(squaring_approach_mode or "Quote")
    updated["squaring_retract_enabled"] = bool(squaring_retract_enabled)
    updated["squaring_retract_type"] = str(squaring_retract_type or "Arc")
    updated["squaring_retract_radius_multiplier"] = _compact_number(
        _coerce_setting_number(
            squaring_retract_radius_multiplier,
            updated.get("squaring_retract_radius_multiplier", 2.0),
            minimum=0.0,
        )
    )
    updated["squaring_retract_mode"] = str(squaring_retract_mode or "Quote")
    updated["squaring_direction"] = str(squaring_direction or "CW")
    updated["squaring_unidirectional_multipass"] = bool(squaring_unidirectional_multipass)
    updated["squaring_pocket_depth"] = _compact_number(
        _coerce_setting_number(
            squaring_pocket_depth,
            updated.get("squaring_pocket_depth", 0.0),
            minimum=0.0,
        )
    )
    updated["squaring_last_pocket"] = _compact_number(
        _coerce_setting_number(
            squaring_last_pocket,
            updated.get("squaring_last_pocket", 0.0),
            minimum=0.0,
        )
    )
    return updated
