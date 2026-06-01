"""Data helpers for the project detail piece editor."""

from dataclasses import dataclass
from typing import Callable

from app.project_detail_piece_rows import parse_optional_piece_float
from app.settings import _parse_piece_quantity_value
from core.model import PIECE_GRAIN_CODE_NONE


@dataclass(frozen=True)
class PieceEditorValues:
    piece_id: str
    name: str
    quantity: str
    height: str
    width: str
    thickness: str
    color: str
    grain_direction: str | None
    source: str


def manual_piece_template_label(template_entry: dict) -> str:
    template_label = str(template_entry.get("name") or template_entry.get("id") or "pieza").strip()
    template_id = str(template_entry.get("id") or "").strip()
    if template_id and template_id != template_label:
        return f"{template_id} - {template_label}"
    return template_label


def optional_field_text(value) -> str:
    return "" if value is None else str(value)


def build_piece_editor_row(
    *,
    base_piece_row: dict,
    values: PieceEditorValues,
    normalize_source: Callable[[str], str],
    infer_companion_f6_source: Callable[[str], str | None],
    pgmx_status: Callable[[str], str],
    color_has_no_grain: Callable[[str, float | None], bool],
) -> dict:
    piece_id = values.piece_id.strip()
    source_value = values.source.strip()
    normalized_source = normalize_source(source_value) if source_value else ""
    updated_quantity = _parse_piece_quantity_value(values.quantity.strip(), default=1)
    selected_color = values.color.strip()
    selected_thickness = parse_optional_piece_float(values.thickness)
    selected_grain = values.grain_direction
    if color_has_no_grain(selected_color, selected_thickness):
        selected_grain = PIECE_GRAIN_CODE_NONE

    updated_piece = dict(base_piece_row)
    updated_piece.update(
        {
            "id": piece_id,
            "name": values.name.strip() or piece_id,
            "quantity": updated_quantity,
            "height": parse_optional_piece_float(values.height),
            "width": parse_optional_piece_float(values.width),
            "thickness": selected_thickness,
            "color": selected_color or None,
            "grain_direction": selected_grain,
            "source": normalized_source,
            "f6_source": infer_companion_f6_source(normalized_source),
            "pgmx": pgmx_status(normalized_source),
            "program_width": base_piece_row.get("program_width") if normalized_source else None,
            "program_height": base_piece_row.get("program_height") if normalized_source else None,
            "program_thickness": base_piece_row.get("program_thickness") if normalized_source else None,
            "en_juego": bool(base_piece_row.get("en_juego", False)),
            "include_in_sheet": bool(base_piece_row.get("include_in_sheet", base_piece_row.get("excel", False))),
        }
    )
    return updated_piece
