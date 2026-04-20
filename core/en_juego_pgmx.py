import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from core.model import Piece, Project, normalize_piece_grain_direction
from core.pgmx_processing import PieceDrawingData, parse_pgmx_for_piece
from tools.synthesize_pgmx import (
    build_polyline_milling_spec,
    build_synthesis_request,
    synthesize_request,
)


@dataclass(frozen=True)
class EnJuegoPgmxResult:
    output_path: Path
    piece_name: str
    board_width: float
    board_height: float
    board_thickness: float
    instance_count: int
    contour_count: int
    fallback_contour_count: int


@dataclass(frozen=True)
class _EnJuegoInstance:
    piece_id: str
    title_text: str
    piece_row: dict
    width_mm: float
    height_mm: float
    pos_x_mm: float
    pos_y_mm: float
    rotation_deg: float
    contour_points: tuple[tuple[float, float], ...]
    used_fallback_contour: bool


def _safe_float(value) -> Optional[float]:
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _parse_dimension(raw_value) -> float:
    parsed = _safe_float(raw_value)
    return float(parsed) if parsed is not None else 0.0


def _parse_optional_dimension(raw_value) -> Optional[float]:
    parsed = _safe_float(raw_value)
    if parsed is None or parsed <= 0:
        return None
    return float(parsed)


def _build_piece_from_row(module_name: str, piece_row: dict) -> Piece:
    thickness = _safe_float(piece_row.get("thickness"))
    quantity_raw = str(piece_row.get("quantity") or "").strip()
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        quantity = 1
    if quantity <= 0:
        quantity = 1

    return Piece(
        id=str(piece_row.get("id") or "").strip() or str(piece_row.get("name") or "pieza").strip(),
        name=str(piece_row.get("name") or piece_row.get("id") or "pieza").strip(),
        quantity=quantity,
        height=_parse_dimension(piece_row.get("height")),
        width=_parse_dimension(piece_row.get("width")),
        thickness=thickness,
        color=piece_row.get("color"),
        grain_direction=normalize_piece_grain_direction(piece_row.get("grain_direction")),
        module_name=module_name,
        cnc_source=str(piece_row.get("source") or "").strip() or None,
        f6_source=str(piece_row.get("f6_source") or "").strip() or None,
        piece_type=piece_row.get("piece_type"),
        program_width=_parse_optional_dimension(piece_row.get("program_width")),
        program_height=_parse_optional_dimension(piece_row.get("program_height")),
        program_thickness=_parse_optional_dimension(piece_row.get("program_thickness")),
    )


def _en_juego_quantity(piece_row: dict) -> int:
    quantity_raw = str(piece_row.get("quantity") or "").strip()
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        return 1
    return quantity if quantity > 0 else 1


def _preview_dimensions_mm(piece_row: dict, drawing_data: Optional[PieceDrawingData]) -> tuple[float, float]:
    if drawing_data is not None:
        top_dimensions = drawing_data.face_dimensions.get("Top")
        if top_dimensions and top_dimensions[0] > 0 and top_dimensions[1] > 0:
            return float(top_dimensions[0]), float(top_dimensions[1])
    program_width = _safe_float(piece_row.get("program_width")) or 0.0
    program_height = _safe_float(piece_row.get("program_height")) or 0.0
    if program_width > 0 and program_height > 0:
        return program_width, program_height
    return _parse_dimension(piece_row.get("width")), _parse_dimension(piece_row.get("height"))


def _instance_key(piece_id: str, copy_index: int) -> str:
    return f"{piece_id}#{copy_index}"


def _saved_layout_for_instance(saved_layout: dict, piece_id: str, copy_index: int):
    instance_key = _instance_key(piece_id, copy_index)
    stored = saved_layout.get(instance_key)
    if isinstance(stored, dict):
        return stored
    legacy_stored = saved_layout.get(piece_id) if copy_index == 1 else None
    if isinstance(legacy_stored, dict):
        return legacy_stored
    return None


def _is_closed_points(points: Sequence[tuple[float, float]], tolerance: float = 1e-6) -> bool:
    if len(points) < 3:
        return False
    first_x, first_y = points[0]
    last_x, last_y = points[-1]
    return abs(first_x - last_x) <= tolerance and abs(first_y - last_y) <= tolerance


def _path_bbox_area(points: Sequence[tuple[float, float]]) -> float:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def _largest_top_closed_contour(drawing_data: Optional[PieceDrawingData]) -> Optional[tuple[tuple[float, float], ...]]:
    if drawing_data is None:
        return None
    top_closed_paths = [
        tuple(path.points)
        for path in drawing_data.milling_paths
        if (path.face or "Top").strip().lower() == "top" and _is_closed_points(path.points)
    ]
    if not top_closed_paths:
        return None
    return max(top_closed_paths, key=_path_bbox_area)


def _fallback_rect_contour(width_mm: float, height_mm: float) -> tuple[tuple[float, float], ...]:
    return (
        (0.0, 0.0),
        (width_mm, 0.0),
        (width_mm, height_mm),
        (0.0, height_mm),
        (0.0, 0.0),
    )


def _to_scene_y(y_mm: float, piece_height_mm: float) -> float:
    return piece_height_mm - y_mm


def _rotate_scene_point(
    x_value: float,
    y_value: float,
    *,
    center_x: float,
    center_y: float,
    angle_deg: float,
) -> tuple[float, float]:
    radians = math.radians(angle_deg)
    delta_x = x_value - center_x
    delta_y = y_value - center_y
    rotated_x = center_x + delta_x * math.cos(radians) - delta_y * math.sin(radians)
    rotated_y = center_y + delta_x * math.sin(radians) + delta_y * math.cos(radians)
    return rotated_x, rotated_y


def _local_maestro_to_global_scene(
    x_value: float,
    y_value: float,
    *,
    piece_width_mm: float,
    piece_height_mm: float,
    pos_x_mm: float,
    pos_y_mm: float,
    rotation_deg: float,
) -> tuple[float, float]:
    local_scene_x = x_value
    local_scene_y = _to_scene_y(y_value, piece_height_mm)
    rotated_x, rotated_y = _rotate_scene_point(
        local_scene_x,
        local_scene_y,
        center_x=piece_width_mm / 2.0,
        center_y=piece_height_mm / 2.0,
        angle_deg=rotation_deg,
    )
    return pos_x_mm + rotated_x, pos_y_mm + rotated_y


def _scene_to_board_maestro(
    x_value: float,
    y_value: float,
    *,
    min_x: float,
    min_y: float,
    board_height: float,
) -> tuple[float, float]:
    shifted_x = x_value - min_x
    shifted_y = y_value - min_y
    return shifted_x, board_height - shifted_y


def _dedup_points(points: Sequence[tuple[float, float]], tolerance: float = 1e-6) -> tuple[tuple[float, float], ...]:
    deduped: list[tuple[float, float]] = []
    for point_x, point_y in points:
        if deduped:
            last_x, last_y = deduped[-1]
            if abs(last_x - point_x) <= tolerance and abs(last_y - point_y) <= tolerance:
                continue
        deduped.append((round(point_x, 4), round(point_y, 4)))
    if len(deduped) >= 2:
        first_x, first_y = deduped[0]
        last_x, last_y = deduped[-1]
        if abs(first_x - last_x) <= tolerance and abs(first_y - last_y) <= tolerance:
            deduped[-1] = deduped[0]
    return tuple(deduped)


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return cleaned.strip("._") or "En_Juego"


def create_en_juego_pgmx(
    project: Project,
    module_name: str,
    module_path: Path,
    piece_rows: Sequence[dict],
    saved_layout: dict,
    output_path: Path,
) -> EnJuegoPgmxResult:
    en_juego_rows = [
        row
        for row in piece_rows
        if bool(row.get("en_juego", False)) and _safe_float(row.get("thickness")) is not None
    ]
    if not en_juego_rows:
        raise ValueError("No hay piezas marcadas como 'En juego' con espesor válido.")

    thickness_values = sorted(
        {
            round(float(thickness_value), 6)
            for thickness_value in (_safe_float(row.get("thickness")) for row in en_juego_rows)
            if thickness_value is not None and thickness_value > 0
        }
    )
    if not thickness_values:
        raise ValueError("Las piezas de 'En juego' no tienen un espesor válido.")
    if len(thickness_values) > 1:
        thickness_text = ", ".join(
            str(int(value)) if float(value).is_integer() else str(value)
            for value in thickness_values
        )
        raise ValueError(
            "El archivo 'En-Juego' requiere que todas las piezas tengan el mismo espesor. "
            f"Se encontraron: {thickness_text}."
        )

    preview_gap_mm = 120.0
    layout_wrap_mm = 2400.0
    drawing_data_cache: dict[str, Optional[PieceDrawingData]] = {}

    def piece_drawing_data(piece_row: dict) -> Optional[PieceDrawingData]:
        piece_id = str(piece_row.get("id") or "").strip()
        if piece_id in drawing_data_cache:
            return drawing_data_cache[piece_id]

        piece_obj = _build_piece_from_row(module_name, piece_row)
        if not piece_obj.cnc_source:
            drawing_data_cache[piece_id] = None
            return None

        try:
            drawing_data = parse_pgmx_for_piece(project, piece_obj, module_path)
        except Exception:
            drawing_data = None
        drawing_data_cache[piece_id] = drawing_data
        return drawing_data

    instances: list[_EnJuegoInstance] = []
    current_unsaved_x_mm = 0.0
    current_unsaved_y_mm = 0.0
    current_row_max_h_mm = 0.0

    for piece_row in en_juego_rows:
        piece_id = str(piece_row.get("id") or "").strip()
        if not piece_id:
            continue
        base_title = str(piece_row.get("name") or piece_id).strip() or piece_id
        drawing_data = piece_drawing_data(piece_row)
        width_mm, height_mm = _preview_dimensions_mm(piece_row, drawing_data)
        width_mm = max(width_mm, 1.0)
        height_mm = max(height_mm, 1.0)
        contour_points = _largest_top_closed_contour(drawing_data)
        used_fallback_contour = contour_points is None
        if contour_points is None:
            contour_points = _fallback_rect_contour(width_mm, height_mm)

        for copy_index in range(1, _en_juego_quantity(piece_row) + 1):
            stored = _saved_layout_for_instance(saved_layout, piece_id, copy_index)
            stored_x_mm = _safe_float(stored.get("x")) if isinstance(stored, dict) else None
            stored_y_mm = _safe_float(stored.get("y")) if isinstance(stored, dict) else None
            stored_rotation = _safe_float(stored.get("rotation")) if isinstance(stored, dict) else None

            if stored_x_mm is not None and stored_y_mm is not None:
                pos_x_mm = stored_x_mm
                pos_y_mm = stored_y_mm
            else:
                if current_unsaved_x_mm > 0 and current_unsaved_x_mm + width_mm > layout_wrap_mm:
                    current_unsaved_x_mm = 0.0
                    current_unsaved_y_mm += current_row_max_h_mm + preview_gap_mm
                    current_row_max_h_mm = 0.0

                pos_x_mm = current_unsaved_x_mm
                pos_y_mm = current_unsaved_y_mm
                current_unsaved_x_mm += width_mm + preview_gap_mm
                current_row_max_h_mm = max(current_row_max_h_mm, height_mm)

            instances.append(
                _EnJuegoInstance(
                    piece_id=piece_id,
                    title_text=f"{base_title} #{copy_index}",
                    piece_row=piece_row,
                    width_mm=width_mm,
                    height_mm=height_mm,
                    pos_x_mm=pos_x_mm,
                    pos_y_mm=pos_y_mm,
                    rotation_deg=float(stored_rotation or 0.0),
                    contour_points=tuple(contour_points),
                    used_fallback_contour=used_fallback_contour,
                )
            )

    if not instances:
        raise ValueError("No hay instancias válidas para generar el archivo 'En-Juego'.")

    scene_bound_points: list[tuple[float, float]] = []
    for instance in instances:
        rect_corners = (
            (0.0, 0.0),
            (instance.width_mm, 0.0),
            (instance.width_mm, instance.height_mm),
            (0.0, instance.height_mm),
        )
        for local_x, local_y in rect_corners:
            scene_bound_points.append(
                _local_maestro_to_global_scene(
                    local_x,
                    local_y,
                    piece_width_mm=instance.width_mm,
                    piece_height_mm=instance.height_mm,
                    pos_x_mm=instance.pos_x_mm,
                    pos_y_mm=instance.pos_y_mm,
                    rotation_deg=instance.rotation_deg,
                )
            )

    min_x = min(point[0] for point in scene_bound_points)
    max_x = max(point[0] for point in scene_bound_points)
    min_y = min(point[1] for point in scene_bound_points)
    max_y = max(point[1] for point in scene_bound_points)
    board_width = round(max_x - min_x, 4)
    board_height = round(max_y - min_y, 4)
    board_thickness = float(thickness_values[0])

    polyline_millings = []
    fallback_contour_count = 0
    for instance in instances:
        transformed_points = [
            _scene_to_board_maestro(
                *_local_maestro_to_global_scene(
                    point_x,
                    point_y,
                    piece_width_mm=instance.width_mm,
                    piece_height_mm=instance.height_mm,
                    pos_x_mm=instance.pos_x_mm,
                    pos_y_mm=instance.pos_y_mm,
                    rotation_deg=instance.rotation_deg,
                ),
                min_x=min_x,
                min_y=min_y,
                board_height=board_height,
            )
            for point_x, point_y in instance.contour_points
        ]
        normalized_points = _dedup_points(transformed_points)
        if len(normalized_points) < 3:
            continue
        if not _is_closed_points(normalized_points):
            normalized_points = normalized_points + (normalized_points[0],)

        double_area = 0.0
        for current_point, next_point in zip(normalized_points, normalized_points[1:]):
            double_area += (current_point[0] * next_point[1]) - (next_point[0] * current_point[1])
        side_of_feature = "Right" if double_area > 0 else "Left"

        polyline_millings.append(
            build_polyline_milling_spec(
                points=normalized_points,
                feature_name=f"{instance.title_text} - Contorno",
                tool_id="1902",
                tool_name="E003",
                tool_width=9.52,
                side_of_feature=side_of_feature,
                is_through=True,
                extra_depth=1.0,
            )
        )
        if instance.used_fallback_contour:
            fallback_contour_count += 1

    if not polyline_millings:
        raise ValueError("No se pudieron construir contornos válidos para el archivo 'En-Juego'.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    piece_name = _sanitize_filename(f"{module_name}_EnJuego")
    request = build_synthesis_request(
        output_path=output_path,
        piece_name=piece_name,
        length=board_width,
        width=board_height,
        depth=board_thickness,
        polyline_millings=tuple(polyline_millings),
    )
    synthesize_request(request)
    return EnJuegoPgmxResult(
        output_path=output_path,
        piece_name=piece_name,
        board_width=board_width,
        board_height=board_height,
        board_thickness=board_thickness,
        instance_count=len(instances),
        contour_count=len(polyline_millings),
        fallback_contour_count=fallback_contour_count,
    )
