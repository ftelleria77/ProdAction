"""State helpers for En-Juego data stored in module configs."""

from app.settings import _default_en_juego_settings, _normalize_en_juego_settings
from core.model import set_piece_en_juego_observation


def has_configurable_en_juego_pieces(piece_rows) -> bool:
    return any(bool(row.get("en_juego", False)) for row in piece_rows)


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
