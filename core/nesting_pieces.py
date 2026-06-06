"""Piece preparation for cut nesting."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

from core.model import (
    PIECE_TYPE_ORDER,
    ModuleData,
    Piece,
    Project,
    normalize_piece_grain_direction,
)
from core.nesting_model import (
    PIECE_GRAIN_HEIGHT_AXIS,
    PIECE_GRAIN_LOCKED,
    PIECE_GRAIN_NONE,
    PIECE_GRAIN_WIDTH_AXIS,
    CutPiece,
)


def _safe_quantity(value) -> int:
    raw_value = str(value).strip().replace(",", ".")
    if not raw_value:
        return 1
    try:
        parsed = int(float(raw_value))
    except (TypeError, ValueError):
        return 1
    return parsed if parsed > 0 else 1


def _safe_float(value):
    raw_value = str(value).strip().replace(",", ".")
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _has_valid_cut_dimensions(width: float, height: float, thickness: float) -> bool:
    resolved_width = _safe_float(width)
    resolved_height = _safe_float(height)
    resolved_thickness = _safe_float(thickness)
    return (
        resolved_width is not None
        and resolved_width > 0
        and resolved_height is not None
        and resolved_height > 0
        and resolved_thickness is not None
        and resolved_thickness > 0
    )


def _normalize_piece_grain_mode(value) -> str:
    raw = str(value or '').strip().lower()
    if not raw:
        return PIECE_GRAIN_NONE
    normalized = normalize_piece_grain_direction(raw)
    if normalized == '1':
        return PIECE_GRAIN_HEIGHT_AXIS
    if normalized == '2':
        return PIECE_GRAIN_WIDTH_AXIS
    if 'veta' in raw and raw not in {'0', '0 - sin veta', 'sin veta', 'no veta'}:
        return PIECE_GRAIN_LOCKED
    return PIECE_GRAIN_NONE


def _is_valid_piece(piece: Piece) -> bool:
    return _has_valid_cut_dimensions(piece.width, piece.height, piece.thickness or 0)


def _piece_can_rotate(piece: Piece) -> bool:
    return _normalize_piece_grain_mode(piece.grain_direction) != PIECE_GRAIN_LOCKED


def _resolve_piece_source_value(
    piece: Piece,
    module_path: Path,
    module_metadata_cache: dict[str, dict[str, dict]],
) -> str:
    source_value = str(piece.cnc_source or '').strip()
    if source_value:
        return source_value

    module_key = str(module_path)
    if module_key not in module_metadata_cache:
        from core.parser import load_module_summary

        module_metadata_cache[module_key] = load_module_summary(module_path)

    metadata_entry = module_metadata_cache.get(module_key, {}).get(str(piece.id or '').strip())
    if not isinstance(metadata_entry, dict):
        return ''
    return str(metadata_entry.get('source') or '').strip()


def _resolve_cut_piece_dimensions(
    project: Project,
    piece: Piece,
    module_path: Path,
    squaring_allowance: float,
    dimension_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]],
    module_metadata_cache: dict[str, dict[str, dict]],
) -> tuple[float, float, float, int]:
    resolved_width = _safe_float(piece.width) or 0.0
    resolved_height = _safe_float(piece.height) or 0.0
    resolved_thickness = _safe_float(piece.thickness) or 0.0
    program_piece_yield = 1
    source_value = _resolve_piece_source_value(piece, module_path, module_metadata_cache)

    if source_value:
        from pgmx.processing import get_program_piece_yield_count, resolve_piece_program_dimensions

        source_piece = piece if source_value == str(piece.cnc_source or '').strip() else replace(piece, cnc_source=source_value)
        program_width, program_height, program_thickness = resolve_piece_program_dimensions(
            project,
            source_piece,
            module_path,
            cache=dimension_cache,
            prefer_stored=True,
        )
        if program_width is not None and program_width > 0 and program_height is not None and program_height > 0:
            resolved_width = float(program_width)
            resolved_height = float(program_height)
            program_piece_yield = get_program_piece_yield_count(
                _safe_float(piece.width),
                _safe_float(piece.height),
                program_width,
                program_height,
            )
        if program_thickness is not None and program_thickness > 0:
            resolved_thickness = float(program_thickness)

    if resolved_width > 0 and resolved_height > 0 and squaring_allowance > 0:
        resolved_width += squaring_allowance
        resolved_height += squaring_allowance

    return resolved_width, resolved_height, resolved_thickness, program_piece_yield


def _module_short_name(module_name: str) -> str:
    raw = str(module_name or "").strip()
    if not raw:
        return ""
    return raw.split("-", 1)[0].strip() or raw


def _read_module_config(module_path: Path) -> dict:
    config_path = module_path / "module_config.json"
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _row_by_piece_id(config_data: dict) -> dict[str, dict]:
    rows = config_data.get("pieces", [])
    if not isinstance(rows, list):
        return {}
    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        piece_id = str(row.get("id") or "").strip()
        if piece_id:
            result[piece_id] = row
    return result


def _layout_piece_id(instance_key: str, stored: dict) -> str:
    piece_id = str(stored.get("piece_id") or "").strip()
    if piece_id:
        return piece_id
    key = str(instance_key or "").strip()
    if "#" in key:
        return key.rsplit("#", 1)[0].strip()
    return key


def _layout_rotation_degrees(stored: dict) -> float:
    rotation = _safe_float(stored.get("rotation_deg"))
    if rotation is None:
        rotation = _safe_float(stored.get("rotation"))
    return float(rotation or 0.0)


def _stored_layout_dimensions(
    stored: dict,
    piece_row: dict,
    drawing_dimensions: tuple[float, float] | None = None,
) -> tuple[float, float] | None:
    width = _safe_float(stored.get("width_mm"))
    height = _safe_float(stored.get("height_mm"))
    if width is not None and height is not None and width > 0 and height > 0:
        return float(width), float(height)

    if drawing_dimensions is not None:
        width, height = drawing_dimensions
        if width > 0 and height > 0:
            return float(width), float(height)

    width = _safe_float(piece_row.get("program_width"))
    height = _safe_float(piece_row.get("program_height"))
    if width is not None and height is not None and width > 0 and height > 0:
        return float(width), float(height)

    width = _safe_float(piece_row.get("width"))
    height = _safe_float(piece_row.get("height"))
    if width is not None and height is not None and width > 0 and height > 0:
        return float(width), float(height)

    return None


def _layout_has_footprint(stored: dict) -> bool:
    x = _safe_float(stored.get("footprint_x_mm"))
    y = _safe_float(stored.get("footprint_y_mm"))
    width = _safe_float(stored.get("footprint_width_mm"))
    height = _safe_float(stored.get("footprint_height_mm"))
    return (
        x is not None
        and y is not None
        and width is not None
        and height is not None
        and width > 0
        and height > 0
    )


def _legacy_layout_scene_rect(
    stored: dict,
    piece_row: dict,
    drawing_dimensions: tuple[float, float] | None = None,
) -> tuple[float, float, float, float] | None:
    scene_x = _safe_float(stored.get("scene_x"))
    if scene_x is None:
        scene_x = _safe_float(stored.get("x"))
    scene_y = _safe_float(stored.get("scene_y"))
    if scene_y is None:
        scene_y = _safe_float(stored.get("y"))
    dimensions = _stored_layout_dimensions(stored, piece_row, drawing_dimensions)
    if scene_x is None or scene_y is None or dimensions is None:
        return None

    width, height = dimensions
    angle = math.radians(_layout_rotation_degrees(stored))
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    center_x = width / 2.0
    center_y = height / 2.0
    points: list[tuple[float, float]] = []
    for local_x, local_y in ((0.0, 0.0), (width, 0.0), (width, height), (0.0, height)):
        offset_x = local_x - center_x
        offset_y = local_y - center_y
        points.append(
            (
                float(scene_x) + center_x + (offset_x * cos_a) + (offset_y * sin_a),
                float(scene_y) + center_y - (offset_x * sin_a) + (offset_y * cos_a),
            )
        )
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x = min(xs)
    min_y = min(ys)
    return min_x, min_y, max(xs) - min_x, max(ys) - min_y


def _composition_layout_rect_from_footprints(layout_data: dict) -> tuple[float, float] | None:
    min_x: float | None = None
    min_y: float | None = None
    max_x: float | None = None
    max_y: float | None = None

    for stored in layout_data.values():
        if not isinstance(stored, dict):
            continue
        x = _safe_float(stored.get("footprint_x_mm"))
        y = _safe_float(stored.get("footprint_y_mm"))
        width = _safe_float(stored.get("footprint_width_mm"))
        height = _safe_float(stored.get("footprint_height_mm"))
        if x is None or y is None or width is None or height is None or width <= 0 or height <= 0:
            continue
        min_x = x if min_x is None else min(min_x, x)
        min_y = y if min_y is None else min(min_y, y)
        max_x = x + width if max_x is None else max(max_x, x + width)
        max_y = y + height if max_y is None else max(max_y, y + height)

    if min_x is None or min_y is None or max_x is None or max_y is None:
        return None
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return None
    return width, height


def _composition_layout_rect_from_scene(
    layout_data: dict,
    row_by_id: dict[str, dict],
    drawing_dimensions_by_piece_id: dict[str, tuple[float, float]] | None = None,
) -> tuple[float, float] | None:
    rects: list[tuple[float, float, float, float]] = []
    for instance_key, stored in layout_data.items():
        if not isinstance(stored, dict):
            continue
        piece_id = _layout_piece_id(str(instance_key), stored)
        piece_row = row_by_id.get(piece_id)
        if not isinstance(piece_row, dict):
            return None
        rect = _legacy_layout_scene_rect(
            stored,
            piece_row,
            (drawing_dimensions_by_piece_id or {}).get(piece_id),
        )
        if rect is None:
            return None
        rects.append(rect)

    if not rects:
        return None

    min_x = min(rect[0] for rect in rects)
    min_y = min(rect[1] for rect in rects)
    max_x = max(rect[0] + rect[2] for rect in rects)
    max_y = max(rect[1] + rect[3] for rect in rects)
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return None
    return width, height


def _composition_layout_rect(
    layout_data: dict,
    row_by_id: dict[str, dict],
    drawing_dimensions_by_piece_id: dict[str, tuple[float, float]] | None = None,
) -> tuple[float, float] | None:
    if layout_data and all(
        isinstance(stored, dict) and _layout_has_footprint(stored)
        for stored in layout_data.values()
    ):
        return _composition_layout_rect_from_footprints(layout_data)

    scene_rect = _composition_layout_rect_from_scene(
        layout_data,
        row_by_id,
        drawing_dimensions_by_piece_id,
    )
    if scene_rect is not None:
        return scene_rect

    return _composition_layout_rect_from_footprints(layout_data)


def _unique_nonempty_values(values) -> set[str]:
    return {str(value or "").strip() for value in values if str(value or "").strip()}


def _derived_grain_axis_for_layout(
    stored: dict,
    piece_row: dict,
    drawing_dimensions: tuple[float, float] | None = None,
) -> str:
    grain_direction = normalize_piece_grain_direction(piece_row.get("grain_direction"))
    if grain_direction not in {"1", "2"}:
        return ""

    dimensions = _stored_layout_dimensions(stored, piece_row, drawing_dimensions)
    if dimensions is None:
        return ""
    drawn_width, drawn_height = dimensions
    piece_width = _safe_float(piece_row.get("width"))
    piece_height = _safe_float(piece_row.get("height"))

    try:
        from pgmx.processing import resolve_piece_grain_hatch_axis

        hatch_axis = resolve_piece_grain_hatch_axis(
            grain_direction,
            piece_width,
            piece_height,
            drawn_width,
            drawn_height,
        )
    except Exception:
        hatch_axis = "vertical" if grain_direction == "1" else "horizontal"

    if hatch_axis == "horizontal":
        local_axis = "x"
    elif hatch_axis == "vertical":
        local_axis = "y"
    else:
        return ""

    if round(_layout_rotation_degrees(stored)) % 180 == 90:
        return "y" if local_axis == "x" else "x"
    return local_axis


def _composition_grain_axes(
    layout_data: dict,
    row_by_id: dict[str, dict],
    drawing_dimensions_by_piece_id: dict[str, tuple[float, float]] | None = None,
) -> set[str]:
    axes: set[str] = set()
    for instance_key, stored in layout_data.items():
        if not isinstance(stored, dict):
            continue
        axis = str(stored.get("grain_axis_composition") or "").strip().lower()
        if axis not in {"x", "y"}:
            piece_id = _layout_piece_id(str(instance_key), stored)
            piece_row = row_by_id.get(piece_id)
            if isinstance(piece_row, dict):
                axis = _derived_grain_axis_for_layout(
                    stored,
                    piece_row,
                    (drawing_dimensions_by_piece_id or {}).get(piece_id),
                )
        if axis in {"x", "y"}:
            axes.add(axis)
    return axes


def _resolve_layout_drawing_dimensions(
    project: Project | None,
    module: ModuleData,
    module_path: Path,
    involved_piece_ids: set[str],
) -> dict[str, tuple[float, float]]:
    if project is None:
        return {}

    resolved: dict[str, tuple[float, float]] = {}
    piece_by_id = {
        str(piece.id or "").strip(): piece
        for piece in module.pieces
        if str(piece.id or "").strip() in involved_piece_ids
    }
    if not piece_by_id:
        return resolved

    try:
        from pgmx.processing import parse_pgmx_for_piece
    except Exception:
        return resolved

    for piece_id, piece in piece_by_id.items():
        try:
            drawing_data = parse_pgmx_for_piece(project, piece, module_path)
        except Exception:
            continue
        if drawing_data is None:
            continue
        top_dimensions = getattr(drawing_data, "face_dimensions", {}).get("Top")
        if not top_dimensions or len(top_dimensions) < 2:
            continue
        width = _safe_float(top_dimensions[0])
        height = _safe_float(top_dimensions[1])
        if width is not None and height is not None and width > 0 and height > 0:
            resolved[piece_id] = (float(width), float(height))

    return resolved


def _build_en_juego_cut_piece(
    project: Project | None,
    module: ModuleData,
    module_path: Path,
    config_data: dict,
    squaring_allowance: float,
) -> tuple[CutPiece | None, set[str]]:
    layout_data = config_data.get("en_juego_layout", {})
    if not isinstance(layout_data, dict) or not layout_data:
        return None, set()

    row_by_id = _row_by_piece_id(config_data)
    enabled_en_juego_ids = {
        piece_id
        for piece_id, row in row_by_id.items()
        if bool(row.get("en_juego", False))
    }
    if not enabled_en_juego_ids:
        return None, set()

    layout_piece_ids = {
        _layout_piece_id(str(instance_key), stored)
        for instance_key, stored in layout_data.items()
        if isinstance(stored, dict) and _layout_piece_id(str(instance_key), stored)
    }
    if not enabled_en_juego_ids.issubset(layout_piece_ids):
        return None, set()

    involved_piece_ids = layout_piece_ids & enabled_en_juego_ids
    if not involved_piece_ids:
        return None, set()

    active_layout_data = {
        instance_key: stored
        for instance_key, stored in layout_data.items()
        if isinstance(stored, dict)
        and _layout_piece_id(str(instance_key), stored) in involved_piece_ids
    }
    active_counts: dict[str, int] = {}
    for instance_key, stored in active_layout_data.items():
        piece_id = _layout_piece_id(str(instance_key), stored)
        active_counts[piece_id] = active_counts.get(piece_id, 0) + 1
    for piece_id in involved_piece_ids:
        expected_quantity = _safe_quantity(row_by_id.get(piece_id, {}).get("quantity"))
        if active_counts.get(piece_id, 0) != expected_quantity:
            return None, set()

    drawing_dimensions_by_piece_id = _resolve_layout_drawing_dimensions(
        project,
        module,
        module_path,
        involved_piece_ids,
    )

    dimensions = _composition_layout_rect(
        active_layout_data,
        row_by_id,
        drawing_dimensions_by_piece_id,
    )
    if dimensions is None:
        return None, set()

    colors = _unique_nonempty_values(
        stored.get("color")
        for stored in active_layout_data.values()
        if isinstance(stored, dict)
    )
    if not colors:
        colors = _unique_nonempty_values(
            row_by_id.get(piece_id, {}).get("color")
            for piece_id in involved_piece_ids
        )
    if len(colors) > 1:
        raise ValueError(
            f"El En-Juego del modulo '{module.name}' tiene piezas de distintos colores y no puede reemplazarlas en diagramas de corte."
        )
    material = next(iter(colors), "SIN_COLOR") or "SIN_COLOR"

    thicknesses = {
        round(float(thickness), 2)
        for thickness in (
            _safe_float(row_by_id.get(piece_id, {}).get("thickness"))
            for piece_id in involved_piece_ids
        )
        if thickness is not None and thickness > 0
    }
    if len(thicknesses) != 1:
        raise ValueError(
            f"El En-Juego del modulo '{module.name}' debe tener un unico espesor valido para diagramas de corte."
        )
    thickness = next(iter(thicknesses))

    grain_axes = _composition_grain_axes(
        active_layout_data,
        row_by_id,
        drawing_dimensions_by_piece_id,
    )

    composition_data = config_data.get("en_juego_composition", {})
    composition_grain = "0"
    if isinstance(composition_data, dict):
        if str(composition_data.get("composition_grain_status") or "").strip().lower() == "mixed":
            raise ValueError(
                f"El En-Juego del modulo '{module.name}' tiene veta mixta y no puede reemplazarlas en diagramas de corte."
            )
        composition_grain = normalize_piece_grain_direction(
            composition_data.get("composition_grain_direction")
        )
    if composition_grain == "0" and grain_axes:
        if len(grain_axes) > 1:
            raise ValueError(
                f"El En-Juego del modulo '{module.name}' tiene veta mixta y no puede reemplazarlas en diagramas de corte."
            )
        composition_grain = "2" if next(iter(grain_axes)) == "x" else "1"

    final_width, final_height = dimensions
    width, height = final_width, final_height
    resolved_squaring_allowance = max(0.0, _safe_float(squaring_allowance) or 0.0)
    if resolved_squaring_allowance > 0:
        width += resolved_squaring_allowance
        height += resolved_squaring_allowance

    composite_piece = Piece(
        id="EN_JUEGO",
        width=width,
        height=height,
        thickness=thickness,
        quantity=1,
        color=material,
        grain_direction=composition_grain,
        name="En-Juego",
        module_name=module.name,
    )
    return (
        CutPiece(
            piece=composite_piece,
            label="En-Juego",
            width=width,
            height=height,
            thickness=thickness,
            color=material,
            allow_rotate=_piece_can_rotate(composite_piece),
            grain_mode=_normalize_piece_grain_mode(composition_grain),
            final_width=final_width,
            final_height=final_height,
        ),
        involved_piece_ids,
    )


def _expand_project_pieces(project: Project, squaring_allowance: float = 0.0) -> dict[tuple[str, float], list[CutPiece]]:
    grouped: dict[tuple[str, float], list[CutPiece]] = {}
    dimension_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
    module_metadata_cache: dict[str, dict[str, dict]] = {}
    resolved_squaring_allowance = max(0.0, _safe_float(squaring_allowance) or 0.0)
    piece_type_rank = {piece_type: index for index, piece_type in enumerate(PIECE_TYPE_ORDER)}

    for module in project.modules:
        from pgmx.processing import get_pgmx_program_dimension_annotations

        module_tag = _module_short_name(module.name)
        module_path = Path(module.path)
        module_quantity = _safe_quantity(getattr(module, 'quantity', None))
        config_data = _read_module_config(module_path)
        en_juego_cut_piece, en_juego_involved_piece_ids = _build_en_juego_cut_piece(
            project,
            module,
            module_path,
            config_data,
            resolved_squaring_allowance,
        )
        ordered_module_pieces = sorted(
            [
                piece
                for piece in module.pieces
                if (_safe_float(piece.thickness) or 0.0) > 0
                and str(piece.id or "").strip() not in en_juego_involved_piece_ids
            ],
            key=lambda piece: piece_type_rank.get(str(piece.piece_type or "").strip(), len(PIECE_TYPE_ORDER)),
        )
        program_annotations = get_pgmx_program_dimension_annotations(
            project,
            ordered_module_pieces,
            module_path,
            cache=dimension_cache,
        )

        for piece, program_annotation in zip(ordered_module_pieces, program_annotations):
            if bool(program_annotation.get("exclude_from_cut_diagrams")):
                continue

            resolved_width, resolved_height, resolved_thickness, program_piece_yield = _resolve_cut_piece_dimensions(
                project,
                piece,
                module_path,
                resolved_squaring_allowance,
                dimension_cache,
                module_metadata_cache,
            )
            if not _has_valid_cut_dimensions(resolved_width, resolved_height, resolved_thickness):
                continue
            material = str(piece.color or "SIN_COLOR").strip() or "SIN_COLOR"
            thickness = float(resolved_thickness)
            base_label = str(piece.name or piece.id or "pieza").strip()
            quantity = _safe_quantity(piece.quantity) * module_quantity
            if program_piece_yield > 1:
                quantity = max(1, (quantity + program_piece_yield - 1) // program_piece_yield)
            grain_mode = _normalize_piece_grain_mode(piece.grain_direction)
            allow_rotate = _piece_can_rotate(piece)
            group_key = (material, round(thickness, 2))
            final_width = _safe_float(piece.width) or resolved_width
            final_height = _safe_float(piece.height) or resolved_height

            for copy_index in range(quantity):
                label = base_label
                if quantity > 1:
                    label = f"{label} #{copy_index + 1}"
                if module_tag:
                    label = f"{label} ({module_tag})"

                grouped.setdefault(group_key, []).append(
                    CutPiece(
                        piece=piece,
                        label=label,
                        width=resolved_width,
                        height=resolved_height,
                        thickness=thickness,
                        color=material,
                        allow_rotate=allow_rotate,
                        grain_mode=grain_mode,
                        final_width=final_width,
                        final_height=final_height,
                    )
                )

        if en_juego_cut_piece is not None:
            material = en_juego_cut_piece.color
            thickness = float(en_juego_cut_piece.thickness)
            group_key = (material, round(thickness, 2))
            for copy_index in range(module_quantity):
                label = en_juego_cut_piece.label
                if module_quantity > 1:
                    label = f"{label} #{copy_index + 1}"
                if module_tag:
                    label = f"{label} ({module_tag})"
                grouped.setdefault(group_key, []).append(
                    replace(en_juego_cut_piece, label=label)
                )

    return grouped


safe_quantity = _safe_quantity
safe_float = _safe_float
has_valid_cut_dimensions = _has_valid_cut_dimensions
normalize_piece_grain_mode = _normalize_piece_grain_mode
is_valid_piece = _is_valid_piece
piece_can_rotate = _piece_can_rotate
resolve_piece_source_value = _resolve_piece_source_value
resolve_cut_piece_dimensions = _resolve_cut_piece_dimensions
module_short_name = _module_short_name
read_module_config = _read_module_config
row_by_piece_id = _row_by_piece_id
layout_piece_id = _layout_piece_id
layout_rotation_degrees = _layout_rotation_degrees
stored_layout_dimensions = _stored_layout_dimensions
layout_has_footprint = _layout_has_footprint
legacy_layout_scene_rect = _legacy_layout_scene_rect
composition_layout_rect_from_footprints = _composition_layout_rect_from_footprints
composition_layout_rect_from_scene = _composition_layout_rect_from_scene
composition_layout_rect = _composition_layout_rect
unique_nonempty_values = _unique_nonempty_values
derived_grain_axis_for_layout = _derived_grain_axis_for_layout
composition_grain_axes = _composition_grain_axes
resolve_layout_drawing_dimensions = _resolve_layout_drawing_dimensions
build_en_juego_cut_piece = _build_en_juego_cut_piece
expand_project_pieces = _expand_project_pieces


__all__ = [
    "build_en_juego_cut_piece",
    "composition_grain_axes",
    "composition_layout_rect",
    "composition_layout_rect_from_footprints",
    "composition_layout_rect_from_scene",
    "derived_grain_axis_for_layout",
    "expand_project_pieces",
    "has_valid_cut_dimensions",
    "is_valid_piece",
    "layout_has_footprint",
    "layout_piece_id",
    "layout_rotation_degrees",
    "legacy_layout_scene_rect",
    "module_short_name",
    "normalize_piece_grain_mode",
    "piece_can_rotate",
    "read_module_config",
    "resolve_cut_piece_dimensions",
    "resolve_layout_drawing_dimensions",
    "resolve_piece_source_value",
    "row_by_piece_id",
    "safe_float",
    "safe_quantity",
    "stored_layout_dimensions",
    "unique_nonempty_values",
]
