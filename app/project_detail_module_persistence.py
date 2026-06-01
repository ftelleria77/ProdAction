"""Persistence helpers for inspected project-detail modules."""

from datetime import datetime
import json
from pathlib import Path
from typing import Callable, Iterable, MutableSequence

from app.project_detail_piece_rows import (
    build_module_pieces_from_rows,
    parse_module_setting_dimension,
    serialize_piece_rows_for_config,
)
from app.settings import _parse_piece_quantity_value


def build_module_settings_payload(
    *,
    x,
    y,
    z,
    herrajes_y_accesorios,
    guias_y_bisagras,
    detalles_de_obra,
) -> dict:
    return {
        "x": parse_module_setting_dimension(x),
        "y": parse_module_setting_dimension(y),
        "z": parse_module_setting_dimension(z),
        "herrajes_y_accesorios": str(herrajes_y_accesorios or "").strip(),
        "guias_y_bisagras": str(guias_y_bisagras or "").strip(),
        "detalles_de_obra": str(detalles_de_obra or "").strip(),
    }


def sync_piece_program_dimensions_from_rows(
    *,
    project,
    module_path: Path,
    piece_rows: Iterable[dict],
    build_piece_from_row: Callable[[dict], object],
    cache: dict | None = None,
    persist_program_dimensions: Callable | None = None,
) -> None:
    if persist_program_dimensions is None:
        from core.pgmx_processing import persist_piece_program_dimensions

        persist_program_dimensions = persist_piece_program_dimensions

    for piece_row in piece_rows:
        piece_obj = build_piece_from_row(piece_row)
        persist_program_dimensions(project, piece_obj, module_path, cache=cache)
        piece_row["program_width"] = piece_obj.program_width
        piece_row["program_height"] = piece_obj.program_height
        piece_row["program_thickness"] = piece_obj.program_thickness


def persist_inspected_module_config(
    *,
    project,
    selected_module,
    config_path: Path,
    config_data: dict,
    piece_rows: MutableSequence[dict],
    module_settings: dict,
    module_quantity,
    module_path: Path,
    build_piece_from_row: Callable[[dict], object],
    program_dimensions_cache: dict | None,
    write_locale_config_files: Callable[[], None],
    save_project: Callable[[object], None],
    on_module_updated: Callable[[], None] | None = None,
    generated_at: str | None = None,
    persist_program_dimensions: Callable | None = None,
) -> list[dict]:
    config_data["settings"] = dict(module_settings)
    selected_module.quantity = _parse_piece_quantity_value(module_quantity, default=1)
    sync_piece_program_dimensions_from_rows(
        project=project,
        module_path=module_path,
        piece_rows=piece_rows,
        build_piece_from_row=build_piece_from_row,
        cache=program_dimensions_cache,
        persist_program_dimensions=persist_program_dimensions,
    )
    serialized_rows = serialize_piece_rows_for_config(piece_rows)
    piece_rows[:] = serialized_rows
    config_data["pieces"] = serialized_rows
    config_data["generated_at"] = generated_at or datetime.now().isoformat(sep=" ", timespec="seconds")
    config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")
    selected_module.pieces = build_module_pieces_from_rows(piece_rows, selected_module.name)
    write_locale_config_files()
    save_project(project)
    if on_module_updated:
        on_module_updated()
    return serialized_rows
