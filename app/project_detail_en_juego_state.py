"""State helpers for En-Juego data stored in module configs."""

from app.project_detail_en_juego_layout import collect_en_juego_composition_data
from app.settings import (
    _coerce_setting_number,
    _default_en_juego_settings,
    _normalize_en_juego_settings,
)
from core.model import set_piece_en_juego_observation


def has_configurable_en_juego_pieces(piece_rows) -> bool:
    return any(bool(row.get("en_juego", False)) for row in piece_rows)


def configurable_en_juego_rows(piece_rows, is_valid_thickness_value) -> list[dict]:
    return [
        row
        for row in piece_rows
        if bool(row.get("en_juego", False)) and is_valid_thickness_value(row.get("thickness"))
    ]


def en_juego_material_thickness_mm(piece_rows) -> float:
    return max(
        (
            _coerce_setting_number(row.get("thickness"), 0.0, minimum=0.0)
            for row in piece_rows
        ),
        default=0.0,
    )


def normalized_en_juego_layout(config_data: dict) -> dict:
    saved_layout = config_data.get("en_juego_layout", {})
    return saved_layout if isinstance(saved_layout, dict) else {}


def store_en_juego_composition_layout(config_data: dict, layout_data: dict) -> None:
    config_data["en_juego_layout"] = layout_data
    config_data["en_juego_composition"] = collect_en_juego_composition_data(layout_data)


def config_section_has_data(value) -> bool:
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return value not in (None, "", False)


def has_persistent_en_juego_info(config_data: dict) -> bool:
    if config_section_has_data(config_data.get("en_juego_layout")):
        return True
    if config_section_has_data(config_data.get("en_juego_composition")):
        return True
    if config_section_has_data(config_data.get("en_juego_output_path")):
        return True
    settings_value = config_data.get("en_juego_settings")
    if isinstance(settings_value, dict):
        return _normalize_en_juego_settings(settings_value) != _default_en_juego_settings()
    return False


def clear_persistent_en_juego_info(config_data: dict) -> None:
    config_data["en_juego_layout"] = {}
    config_data["en_juego_composition"] = {}
    config_data.pop("en_juego_output_path", None)
    config_data["en_juego_settings"] = _default_en_juego_settings()


def sync_en_juego_observations(piece_rows) -> None:
    for piece_row in piece_rows:
        piece_row["observations"] = set_piece_en_juego_observation(
            piece_row.get("observations"),
            bool(piece_row.get("en_juego", False)),
        )
