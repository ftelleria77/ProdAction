"""Shared data preparation for production sheet exports."""

from __future__ import annotations

import json
import re
from pathlib import Path

from core.model import (
    PIECE_TYPE_ORDER,
    Piece,
    Project,
    normalize_piece_grain_direction,
    normalize_piece_observations,
)


def is_valid_thickness(value) -> bool:
    parsed = safe_float(value)
    return parsed is not None and parsed > 0


def safe_int(value, default=1) -> int:
    raw_value = str(value).strip().replace(",", ".")
    if not raw_value:
        return default
    try:
        parsed = int(float(raw_value))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def effective_piece_quantity(piece_quantity, module_quantity) -> int:
    return safe_int(piece_quantity, default=1) * safe_int(module_quantity, default=1)


def safe_float(value):
    if value is None:
        return None
    raw_value = str(value).strip().replace(",", ".")
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def confirmed_dimension(value):
    parsed = safe_float(value)
    if parsed is None:
        return None
    return int(parsed) if parsed.is_integer() else round(parsed, 2)


def is_positive_dimension(value) -> bool:
    parsed = safe_float(value)
    return parsed is not None and parsed > 0


def piece_from_sheet_row(module_name: str, piece_row: dict) -> Piece:
    thickness = safe_float(piece_row.get("thickness"))
    quantity = safe_int(piece_row.get("quantity"), default=1)
    return Piece(
        id=str(piece_row.get("id") or piece_row.get("name") or "pieza").strip(),
        name=str(piece_row.get("name") or piece_row.get("id") or "pieza").strip(),
        quantity=quantity,
        width=safe_float(piece_row.get("width")) or 0.0,
        height=safe_float(piece_row.get("height")) or 0.0,
        thickness=thickness,
        color=piece_row.get("color"),
        grain_direction=normalize_piece_grain_direction(piece_row.get("grain_direction")),
        module_name=module_name,
        cnc_source=str(piece_row.get("source") or "").strip() or None,
        f6_source=str(piece_row.get("f6_source") or "").strip() or None,
        piece_type=piece_row.get("piece_type"),
        program_width=safe_float(piece_row.get("program_width")),
        program_height=safe_float(piece_row.get("program_height")),
        program_thickness=safe_float(piece_row.get("program_thickness")),
    )


def extract_named_dimensions(module_name: str):
    raw = module_name or ""
    cleaned = re.sub(r"^\s*mod\.?\s*\d+\s*-\s*", "", raw, flags=re.IGNORECASE)
    parts = [part.strip() for part in cleaned.split("-")]

    numeric_parts = []
    for part in parts:
        if re.fullmatch(r"\d+(?:[\.,]\d+)?", part):
            try:
                numeric_parts.append(float(part.replace(",", ".")))
            except ValueError:
                continue

    if len(numeric_parts) >= 2:
        return numeric_parts[-2], numeric_parts[-1]
    if len(numeric_parts) == 1:
        return numeric_parts[0], None
    return None, None


def derive_module_dimensions(module_name: str, pieces: list[dict]):
    x_named, z_named = extract_named_dimensions(module_name)

    widths = []
    heights = []
    thicknesses = []
    lateral_heights = []
    span_heights = []

    for piece in pieces:
        piece_name = str(piece.get("name") or piece.get("id") or "").lower()
        width = safe_float(piece.get("width"))
        height = safe_float(piece.get("height"))
        thickness = safe_float(piece.get("thickness"))

        if width is not None and width > 0:
            widths.append(width)
        if height is not None and height > 0:
            heights.append(height)
        if thickness is not None and thickness > 0:
            thicknesses.append(thickness)

        if "lateral" in piece_name and height is not None and height > 0:
            lateral_heights.append(height)

        if any(key in piece_name for key in ["fondo", "estante", "tapa", "puerta", "frente", "faja"]):
            if height is not None and height > 0:
                span_heights.append(height)

    max_thickness = max(thicknesses) if thicknesses else 0.0

    if z_named is not None:
        z_val = round(z_named, 2)
    elif widths:
        z_val = round(max(widths), 2)
    else:
        z_val = None

    if x_named is not None:
        x_val = round(x_named, 2)
    else:
        x_base = max(span_heights) if span_heights else (max(heights) if heights else None)
        x_val = round(x_base, 2) if x_base is not None else None

    if lateral_heights:
        y_base = max(lateral_heights)
    elif heights:
        y_base = max(heights)
    else:
        y_base = None

    y_val = round(y_base + max_thickness, 2) if y_base is not None else None

    def compact_number(number):
        if number is None:
            return None
        return int(number) if abs(number - int(number)) < 1e-9 else number

    return compact_number(x_val), compact_number(y_val), compact_number(z_val)


def load_module_sheet_data(
    project: Project,
    module,
    program_dimensions_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]],
) -> dict:
    from pgmx.processing import get_pgmx_program_dimension_notes

    config_path = Path(module.path) / "module_config.json"
    config_data = {}
    module_settings = {
        "herrajes_y_accesorios": "",
        "guias_y_bisagras": "",
        "detalles_de_obra": "",
    }

    if config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config_data = {}
        module_settings.update(config_data.get("settings", {}))
        raw_pieces = config_data.get("pieces", [])
        pieces = [piece for piece in raw_pieces if is_valid_thickness(piece.get("thickness"))]
        type_rank = {piece_type: index for index, piece_type in enumerate(PIECE_TYPE_ORDER)}
        pieces.sort(key=lambda piece: type_rank.get(piece.get("piece_type") or "", len(PIECE_TYPE_ORDER)))
    else:
        pieces = [
            {
                "id": piece.id,
                "name": piece.name or piece.id,
                "quantity": piece.quantity,
                "width": piece.width,
                "height": piece.height,
                "thickness": piece.thickness,
                "color": piece.color,
                "grain_direction": normalize_piece_grain_direction(piece.grain_direction),
                "source": piece.cnc_source,
                "f6_source": piece.f6_source,
                "program_width": piece.program_width,
                "program_height": piece.program_height,
                "program_thickness": piece.program_thickness,
                "include_in_sheet": False,
                "observations": "",
            }
            for piece in module.pieces
            if is_valid_thickness(piece.thickness)
        ]

    piece_objects = [piece_from_sheet_row(module.name, piece) for piece in pieces]
    program_notes = get_pgmx_program_dimension_notes(
        project,
        piece_objects,
        Path(module.path),
        cache=program_dimensions_cache,
    )
    for piece, program_note in zip(pieces, program_notes):
        piece["program_dimension_note"] = program_note
        piece["observations"] = normalize_piece_observations(piece.get("observations"))

    x_inferred, y_inferred, z_inferred = derive_module_dimensions(module.name, pieces)
    x_val = confirmed_dimension(module_settings.get("x")) or x_inferred
    y_val = confirmed_dimension(module_settings.get("y")) or y_inferred
    z_val = confirmed_dimension(module_settings.get("z")) or z_inferred
    return {
        "config_data": config_data,
        "module_settings": module_settings,
        "pieces": pieces,
        "dimensions": (x_val, y_val, z_val),
    }
