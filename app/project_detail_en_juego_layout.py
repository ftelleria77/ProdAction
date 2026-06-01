"""Pure layout helpers for the En-Juego configuration dialog."""

from app.settings import _parse_piece_quantity_value
from core.model import normalize_piece_grain_direction
from pgmx.processing import resolve_piece_grain_hatch_axis


def safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def en_juego_quantity(piece_row: dict) -> int:
    return _parse_piece_quantity_value(piece_row.get("quantity"), default=1)


def en_juego_instance_key(piece_id: str, copy_index: int) -> str:
    return f"{piece_id}#{copy_index}"


def saved_layout_for_instance(saved_layout: dict, piece_id: str, copy_index: int):
    instance_key = en_juego_instance_key(piece_id, copy_index)
    stored = saved_layout.get(instance_key)
    if isinstance(stored, dict):
        return stored, instance_key

    legacy_stored = saved_layout.get(piece_id) if copy_index == 1 else None
    if isinstance(legacy_stored, dict):
        return legacy_stored, instance_key

    return None, instance_key


def saved_scene_placement(saved_layout: dict, piece_id: str, copy_index: int):
    stored, _ = saved_layout_for_instance(saved_layout, piece_id, copy_index)
    if not isinstance(stored, dict):
        return None, None, None

    scene_x = safe_float(stored.get("scene_x"))
    if scene_x is None:
        scene_x = safe_float(stored.get("x"))

    scene_y = safe_float(stored.get("scene_y"))
    if scene_y is None:
        scene_y = safe_float(stored.get("y"))

    rotation_deg = safe_float(stored.get("rotation_deg"))
    if rotation_deg is None:
        rotation_deg = safe_float(stored.get("rotation"))

    return scene_x, scene_y, rotation_deg


def collect_en_juego_instances(en_juego_rows: list[dict]) -> list[dict]:
    en_juego_instances = []
    for piece_row in en_juego_rows:
        piece_id = str(piece_row.get("id") or "").strip()
        if not piece_id:
            continue
        base_title = str(piece_row.get("name") or piece_id).strip() or piece_id
        piece_copy_count = en_juego_quantity(piece_row)
        for copy_index in range(1, piece_copy_count + 1):
            en_juego_instances.append(
                {
                    "piece_id": piece_id,
                    "piece_row": piece_row,
                    "copy_index": copy_index,
                    "instance_key": en_juego_instance_key(piece_id, copy_index),
                    "title_text": f"{base_title} #{copy_index}" if piece_copy_count > 1 else base_title,
                }
            )
    return en_juego_instances


def initial_unsaved_layout_cursor(
    en_juego_instances: list[dict],
    saved_layout: dict,
    width_resolver,
    gap_mm: float,
) -> tuple[float, float, float]:
    current_unsaved_x_mm = 0.0
    for instance in en_juego_instances:
        piece_row = instance["piece_row"]
        piece_id = instance["piece_id"]
        copy_index = instance["copy_index"]
        stored_x, stored_y, _ = saved_scene_placement(saved_layout, piece_id, copy_index)
        if stored_x is None or stored_y is None:
            continue
        width_mm = float(width_resolver(piece_row))
        current_unsaved_x_mm = max(current_unsaved_x_mm, stored_x + width_mm + gap_mm)
    return current_unsaved_x_mm, 0.0, 0.0


def next_unsaved_piece_position(
    current_x_mm: float,
    current_y_mm: float,
    current_row_max_h_mm: float,
    width_mm: float,
    height_mm: float,
    *,
    gap_mm: float,
    wrap_mm: float,
) -> tuple[float, float, float, float, float]:
    if current_x_mm > 0 and current_x_mm + width_mm > wrap_mm:
        current_x_mm = 0.0
        current_y_mm += current_row_max_h_mm + gap_mm
        current_row_max_h_mm = 0.0

    pos_x_mm = current_x_mm
    pos_y_mm = current_y_mm
    next_x_mm = current_x_mm + width_mm + gap_mm
    next_row_max_h_mm = max(current_row_max_h_mm, height_mm)
    return pos_x_mm, pos_y_mm, next_x_mm, current_y_mm, next_row_max_h_mm


def preview_dimensions_mm(piece_row: dict, drawing_data=None) -> tuple[float, float]:
    if drawing_data is not None:
        top_dimensions = drawing_data.face_dimensions.get("Top")
        if top_dimensions and top_dimensions[0] > 0 and top_dimensions[1] > 0:
            return float(top_dimensions[0]), float(top_dimensions[1])
    program_width = safe_float(piece_row.get("program_width")) or 0.0
    program_height = safe_float(piece_row.get("program_height")) or 0.0
    if program_width > 0 and program_height > 0:
        return program_width, program_height
    return safe_float(piece_row.get("width")) or 0.0, safe_float(piece_row.get("height")) or 0.0


def scene_piece_items_in_layout_order(
    item_by_instance_id: dict,
    nominal_scene_rect,
) -> list:
    return sorted(
        item_by_instance_id.values(),
        key=lambda scene_item: (
            round(nominal_scene_rect(scene_item).top(), 3),
            round(nominal_scene_rect(scene_item).left(), 3),
            str(scene_item.data(0) or ""),
        ),
    )


def enforce_scene_piece_spacing(
    item_by_instance_id: dict,
    nominal_scene_rect,
    spacing_mm: float,
    *,
    max_passes: int | None = None,
) -> bool:
    if spacing_mm <= 0:
        return False

    moved_any = False
    pass_count = max_passes if max_passes is not None else len(item_by_instance_id) * 2
    for _ in range(max(1, pass_count)):
        pass_moved = False
        ordered_items = scene_piece_items_in_layout_order(
            item_by_instance_id,
            nominal_scene_rect,
        )
        for current_index, current_item in enumerate(ordered_items):
            current_rect = nominal_scene_rect(current_item)
            for previous_item in ordered_items[:current_index]:
                previous_rect = nominal_scene_rect(previous_item)
                overlap_height = min(previous_rect.bottom(), current_rect.bottom()) - max(
                    previous_rect.top(),
                    current_rect.top(),
                )
                overlap_width = min(previous_rect.right(), current_rect.right()) - max(
                    previous_rect.left(),
                    current_rect.left(),
                )

                push_right_mm = (
                    (previous_rect.right() + spacing_mm) - current_rect.left()
                    if overlap_height > 0
                    else 0.0
                )
                push_down_mm = (
                    (previous_rect.bottom() + spacing_mm) - current_rect.top()
                    if overlap_width > 0
                    else 0.0
                )

                candidate_pushes = [
                    (axis_name, delta_value)
                    for axis_name, delta_value in (("x", push_right_mm), ("y", push_down_mm))
                    if delta_value > 0.001
                ]
                if not candidate_pushes:
                    continue

                axis_name, delta_value = min(candidate_pushes, key=lambda item: item[1])
                current_pos = current_item.pos()
                if axis_name == "x":
                    current_item.setPos(current_pos.x() + delta_value, current_pos.y())
                else:
                    current_item.setPos(current_pos.x(), current_pos.y() + delta_value)
                current_rect = nominal_scene_rect(current_item)
                moved_any = True
                pass_moved = True

        if not pass_moved:
            break

    return moved_any


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def to_scene_y(y_mm: float, piece_height_mm: float) -> float:
    return piece_height_mm - y_mm


def vertical_overlap(rect_a, rect_b) -> float:
    return min(rect_a.bottom(), rect_b.bottom()) - max(rect_a.top(), rect_b.top())


def horizontal_overlap(rect_a, rect_b) -> float:
    return min(rect_a.right(), rect_b.right()) - max(rect_a.left(), rect_b.left())


def has_horizontal_blocker(
    rect_entries,
    left_key,
    right_key,
    left_rect,
    right_rect,
    tolerance_mm: float = 0.1,
) -> bool:
    overlap_top = max(left_rect.top(), right_rect.top())
    overlap_bottom = min(left_rect.bottom(), right_rect.bottom())
    for candidate_key, _, candidate_rect in rect_entries:
        if candidate_key in {left_key, right_key}:
            continue
        if min(candidate_rect.bottom(), overlap_bottom) - max(candidate_rect.top(), overlap_top) <= tolerance_mm:
            continue
        if (
            candidate_rect.left() >= left_rect.right() - tolerance_mm
            and candidate_rect.right() <= right_rect.left() + tolerance_mm
        ):
            return True
    return False


def has_vertical_blocker(
    rect_entries,
    upper_key,
    lower_key,
    upper_rect,
    lower_rect,
    tolerance_mm: float = 0.1,
) -> bool:
    overlap_left = max(upper_rect.left(), lower_rect.left())
    overlap_right = min(upper_rect.right(), lower_rect.right())
    for candidate_key, _, candidate_rect in rect_entries:
        if candidate_key in {upper_key, lower_key}:
            continue
        if min(candidate_rect.right(), overlap_right) - max(candidate_rect.left(), overlap_left) <= tolerance_mm:
            continue
        if (
            candidate_rect.top() >= upper_rect.bottom() - tolerance_mm
            and candidate_rect.bottom() <= lower_rect.top() + tolerance_mm
        ):
            return True
    return False


def dimension_x_near_inner_edge(rect, *, left_side_piece: bool) -> float:
    margin = 12.0
    if rect.width() <= margin * 2.0:
        return (rect.left() + rect.right()) / 2.0
    desired_x = rect.right() - 28.0 if left_side_piece else rect.left() + 28.0
    return max(rect.left() + margin, min(rect.right() - margin, desired_x))


def local_grain_axis(hatch_axis: str) -> str:
    if hatch_axis == "horizontal":
        return "x"
    if hatch_axis == "vertical":
        return "y"
    return "none"


def composition_grain_axis(axis: str, rotation_deg: float) -> str:
    if axis not in {"x", "y"}:
        return "none"
    normalized_rotation = round(rotation_deg) % 180
    if normalized_rotation == 90:
        return "y" if axis == "x" else "x"
    return axis


def collect_en_juego_layout_data(
    item_by_instance_id: dict,
    piece_rows: list[dict],
    nominal_scene_rect,
) -> dict:
    piece_rows_by_id = {
        str(piece_row.get("id") or "").strip(): piece_row
        for piece_row in piece_rows
    }

    def instance_grain_fields(piece_id: str, item_rect, rotation_deg: float) -> dict:
        piece_row = piece_rows_by_id.get(piece_id) or {}
        grain_direction = normalize_piece_grain_direction(piece_row.get("grain_direction"))
        hatch_axis = resolve_piece_grain_hatch_axis(
            grain_direction,
            safe_float(piece_row.get("width")),
            safe_float(piece_row.get("height")),
            float(item_rect.width()),
            float(item_rect.height()),
        )
        local_axis = local_grain_axis(hatch_axis)
        return {
            "grain_direction": grain_direction,
            "grain_axis_local": local_axis,
            "grain_axis_composition": composition_grain_axis(local_axis, rotation_deg),
        }

    def instance_piece_color(piece_id: str) -> str:
        piece_row = piece_rows_by_id.get(piece_id) or {}
        return str(piece_row.get("color") or "").strip()

    layout_data = {}
    nominal_rects = {
        instance_key: nominal_scene_rect(scene_item)
        for instance_key, scene_item in item_by_instance_id.items()
    }
    if nominal_rects:
        min_scene_x = min(rect.left() for rect in nominal_rects.values())
        max_scene_y = max(rect.bottom() for rect in nominal_rects.values())
    else:
        min_scene_x = 0.0
        max_scene_y = 0.0
    for instance_key, scene_item in item_by_instance_id.items():
        scene_pos = scene_item.pos()
        rotation_deg = scene_item.rotation()
        item_rect = scene_item.rect()
        nominal_rect = nominal_rects.get(instance_key)
        origin_scene_point = scene_item.mapToScene(item_rect.left(), item_rect.bottom())
        piece_id = str(scene_item.data(1) or "").strip()
        footprint_x_mm = nominal_rect.left() - min_scene_x if nominal_rect is not None else 0.0
        footprint_y_mm = max_scene_y - nominal_rect.bottom() if nominal_rect is not None else 0.0
        layout_data[instance_key] = {
            "layout_version": 2,
            "instance_key": instance_key,
            "piece_id": piece_id,
            "x": round(scene_pos.x(), 2),
            "y": round(scene_pos.y(), 2),
            "rotation": round(rotation_deg, 2),
            "scene_x": round(scene_pos.x(), 2),
            "scene_y": round(scene_pos.y(), 2),
            "rotation_deg": round(rotation_deg, 2),
            "x_mm": round(origin_scene_point.x() - min_scene_x, 2),
            "y_mm": round(max_scene_y - origin_scene_point.y(), 2),
            "footprint_x_mm": round(footprint_x_mm, 2),
            "footprint_y_mm": round(footprint_y_mm, 2),
            "footprint_width_mm": (
                round(nominal_rect.width(), 2) if nominal_rect is not None else 0.0
            ),
            "footprint_height_mm": (
                round(nominal_rect.height(), 2) if nominal_rect is not None else 0.0
            ),
            "width_mm": round(item_rect.width(), 2),
            "height_mm": round(item_rect.height(), 2),
            "color": instance_piece_color(piece_id),
            **instance_grain_fields(piece_id, item_rect, rotation_deg),
        }
    return layout_data


def collect_en_juego_composition_data(layout_data: dict) -> dict:
    grain_axes = {
        str(stored.get("grain_axis_composition") or "").strip().lower()
        for stored in layout_data.values()
        if isinstance(stored, dict)
        and str(stored.get("grain_axis_composition") or "").strip().lower() in {"x", "y"}
    }
    if not grain_axes:
        grain_axis = "none"
        grain_direction = "0"
        grain_status = "ok"
    elif len(grain_axes) == 1:
        grain_axis = next(iter(grain_axes))
        grain_direction = "2" if grain_axis == "x" else "1"
        grain_status = "ok"
    else:
        grain_axis = "mixed"
        grain_direction = "mixed"
        grain_status = "mixed"
    return {
        "layout_version": 2,
        "composition_grain_direction": grain_direction,
        "composition_grain_axis": grain_axis,
        "composition_grain_status": grain_status,
    }
