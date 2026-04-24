"""Sintesis En-Juego basada en snapshots reales de `.pgmx`.

La visualizacion solo aporta composicion, los programas originales se leen con
`tools.pgmx_snapshot`/`tools.pgmx_adapters` y la escritura final pasa por
`tools.synthesize_pgmx`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from core.en_juego_transform import EnJuegoTransform, transform_supported_spec
from core.model import Project
from tools import synthesize_pgmx as sp
from tools.pgmx_adapters import PgmxAdaptationResult, adapt_pgmx_path
from tools.pgmx_snapshot import PgmxSnapshot, read_pgmx_snapshot


DIVISION_TOLERANCE_MM = 0.1
GEOMETRY_EPSILON_MM = 1e-6


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
class _ResolvedInstance:
    instance_key: str
    piece_id: str
    copy_index: int
    title_text: str
    piece_row: dict
    source_path: Path
    snapshot: PgmxSnapshot
    transform: EnJuegoTransform
    footprint_x: float
    footprint_y: float
    footprint_width: float
    footprint_height: float

    @property
    def left(self) -> float:
        return self.footprint_x

    @property
    def right(self) -> float:
        return self.footprint_x + self.footprint_width

    @property
    def bottom(self) -> float:
        return self.footprint_y

    @property
    def top(self) -> float:
        return self.footprint_y + self.footprint_height


@dataclass(frozen=True)
class _DivisionSegment:
    orientation: str
    rank: int
    center: float
    band_start: float
    band_end: float
    gap_width: float
    before_title: str
    after_title: str


@dataclass(frozen=True)
class _DivisionPath:
    orientation: str
    segments: tuple[_DivisionSegment, ...]
    points: tuple[tuple[float, float], ...]
    is_full: bool


def _safe_float(value) -> Optional[float]:
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _safe_bool(value, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "si", "sí", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "off"}:
        return False
    return bool(default)


def _setting_float(settings: dict, key: str, default: float = 0.0) -> float:
    parsed = _safe_float(settings.get(key))
    return float(default) if parsed is None else float(parsed)


def _nonnegative_setting(value, default: float = 0.0) -> float:
    parsed = _safe_float(value)
    if parsed is None:
        return max(0.0, float(default))
    return max(0.0, float(parsed))


def _parse_quantity(piece_row: dict) -> int:
    raw = "" if piece_row.get("quantity") is None else str(piece_row.get("quantity")).strip()
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        return 1
    return quantity if quantity > 0 else 1


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


def _iter_pgmx_search_roots(project: Project, module_path: Path) -> tuple[Path, ...]:
    roots = (
        module_path,
        Path(project.root_directory),
        Path(project.root_directory) / "archive",
        Path(project.root_directory).parent / "archive",
        module_path.parent / "archive",
    )
    seen: set[str] = set()
    unique_roots: list[Path] = []
    for root in roots:
        root_key = str(root)
        if root_key in seen or not root.exists():
            continue
        seen.add(root_key)
        unique_roots.append(root)
    return tuple(unique_roots)


def _resolve_source_path(project: Project, module_path: Path, source_value: str) -> Optional[Path]:
    source_text = str(source_value or "").strip()
    if not source_text:
        return None

    direct_path = Path(source_text)
    if direct_path.is_file():
        return direct_path

    candidates = (
        module_path / source_text,
        Path(project.root_directory) / source_text,
        Path(project.root_directory) / "archive" / Path(source_text).name,
        Path(project.root_directory).parent / "archive" / Path(source_text).name,
        module_path.parent / "archive" / Path(source_text).name,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    source_name = Path(source_text).name
    matched_by_name = next(module_path.rglob(source_name), None) if module_path.exists() else None
    if matched_by_name and matched_by_name.is_file():
        return matched_by_name

    source_name_lower = source_name.lower()
    for root in _iter_pgmx_search_roots(project, module_path):
        for candidate in root.rglob("*.pgmx"):
            if candidate.name.lower() == source_name_lower:
                return candidate
    return None


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return cleaned.strip("._") or "pieza"


def _resolved_tool_name(settings: dict, key_prefix: str) -> str:
    return str(
        settings.get(f"{key_prefix}_tool_code")
        or settings.get(f"{key_prefix}_tool_name")
        or ""
    ).strip()


def _build_division_strategy(settings: dict):
    if not _safe_bool(settings.get("cutting_multipass_enabled"), False):
        return None
    axial_cutting_depth = _nonnegative_setting(settings.get("cutting_pocket_depth"), 0.0)
    axial_finish_cutting_depth = _nonnegative_setting(settings.get("cutting_last_pocket"), 0.0)
    path_mode = str(settings.get("cutting_path_mode") or "Unidirectional").strip().lower()
    if path_mode == "bidirectional":
        return sp.build_bidirectional_milling_strategy_spec(
            is_multi_level=True,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    return sp.build_unidirectional_milling_strategy_spec(
        is_multi_level=True,
        axial_cutting_depth=axial_cutting_depth,
        axial_finish_cutting_depth=axial_finish_cutting_depth,
    )


def _build_squaring_strategy(settings: dict):
    if not _safe_bool(settings.get("squaring_unidirectional_multipass"), False):
        return None
    return sp.build_unidirectional_milling_strategy_spec(
        is_multi_level=True,
        axial_cutting_depth=_nonnegative_setting(settings.get("squaring_pocket_depth"), 0.0),
        axial_finish_cutting_depth=_nonnegative_setting(settings.get("squaring_last_pocket"), 0.0),
    )


def _division_depth_kwargs(settings: dict) -> dict:
    if _safe_bool(settings.get("cutting_is_through"), True):
        return {
            "line_is_through": True,
            "line_extra_depth": _nonnegative_setting(settings.get("cutting_depth_value"), 1.0),
        }
    return {
        "line_is_through": False,
        "line_target_depth": _nonnegative_setting(settings.get("cutting_depth_value"), 0.0),
    }


def _division_polyline_depth_kwargs(settings: dict) -> dict:
    if _safe_bool(settings.get("cutting_is_through"), True):
        return {
            "is_through": True,
            "extra_depth": _nonnegative_setting(settings.get("cutting_depth_value"), 1.0),
        }
    return {
        "is_through": False,
        "target_depth": _nonnegative_setting(settings.get("cutting_depth_value"), 0.0),
    }


def _squaring_depth_kwargs(settings: dict) -> dict:
    if _safe_bool(settings.get("squaring_is_through"), True):
        return {
            "is_through": True,
            "extra_depth": _nonnegative_setting(settings.get("squaring_depth_value"), 1.0),
        }
    return {
        "is_through": False,
        "target_depth": _nonnegative_setting(settings.get("squaring_depth_value"), 0.0),
    }


def _transform_corners(
    transform: EnJuegoTransform,
    length: float,
    width: float,
) -> tuple[tuple[float, float], ...]:
    return tuple(
        transform.point(point_x, point_y)
        for point_x, point_y in (
            (0.0, 0.0),
            (length, 0.0),
            (length, width),
            (0.0, width),
        )
    )


def _resolve_footprint(
    stored_layout: dict,
    transform: EnJuegoTransform,
    snapshot: PgmxSnapshot,
) -> tuple[float, float, float, float]:
    footprint_x = _safe_float(stored_layout.get("footprint_x_mm"))
    footprint_y = _safe_float(stored_layout.get("footprint_y_mm"))
    footprint_width = _safe_float(stored_layout.get("footprint_width_mm"))
    footprint_height = _safe_float(stored_layout.get("footprint_height_mm"))
    if (
        footprint_x is not None
        and footprint_y is not None
        and footprint_width is not None
        and footprint_height is not None
        and footprint_width > 0
        and footprint_height > 0
    ):
        return footprint_x, footprint_y, footprint_width, footprint_height

    corners = _transform_corners(transform, snapshot.state.length, snapshot.state.width)
    xs = [point[0] for point in corners]
    ys = [point[1] for point in corners]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def _layout_transform(stored_layout: dict) -> Optional[EnJuegoTransform]:
    x_mm = _safe_float(stored_layout.get("x_mm"))
    y_mm = _safe_float(stored_layout.get("y_mm"))
    rotation_deg = _safe_float(stored_layout.get("rotation_deg"))
    if rotation_deg is None:
        rotation_deg = _safe_float(stored_layout.get("rotation"))
    if x_mm is None or y_mm is None:
        return None
    return EnJuegoTransform(x_mm, y_mm, float(rotation_deg or 0.0))


def _resolve_instances(
    project: Project,
    module_name: str,
    module_path: Path,
    piece_rows: Sequence[dict],
    saved_layout: dict,
) -> tuple[_ResolvedInstance, ...]:
    snapshot_cache: dict[Path, PgmxSnapshot] = {}
    instances: list[_ResolvedInstance] = []
    for piece_row in piece_rows:
        piece_id = str(piece_row.get("id") or "").strip()
        if not piece_id:
            continue
        source_path = _resolve_source_path(
            project,
            module_path,
            str(piece_row.get("source") or piece_row.get("cnc_source") or "").strip(),
        )
        if source_path is None:
            raise ValueError(
                f"No se encontro el .pgmx original de la pieza '{piece_row.get('name') or piece_id}'."
            )
        if source_path not in snapshot_cache:
            snapshot_cache[source_path] = read_pgmx_snapshot(source_path)
        snapshot = snapshot_cache[source_path]
        base_title = str(piece_row.get("name") or piece_id).strip() or piece_id
        copy_count = _parse_quantity(piece_row)
        for copy_index in range(1, copy_count + 1):
            instance_key = _instance_key(piece_id, copy_index)
            stored = _saved_layout_for_instance(saved_layout, piece_id, copy_index)
            if not isinstance(stored, dict):
                raise ValueError(
                    f"Falta guardar la disposicion de la instancia '{instance_key}'. "
                    "Abra Configurar En-Juego y guarde la disposicion."
                )
            transform = _layout_transform(stored)
            if transform is None:
                raise ValueError(
                    f"La instancia '{instance_key}' no tiene layout version 2 utilizable. "
                    "Abra Configurar En-Juego y guarde la disposicion nuevamente."
                )
            footprint_x, footprint_y, footprint_width, footprint_height = _resolve_footprint(
                stored,
                transform,
                snapshot,
            )
            instances.append(
                _ResolvedInstance(
                    instance_key=instance_key,
                    piece_id=piece_id,
                    copy_index=copy_index,
                    title_text=f"{base_title} #{copy_index}" if copy_count > 1 else base_title,
                    piece_row=piece_row,
                    source_path=source_path,
                    snapshot=snapshot,
                    transform=transform,
                    footprint_x=footprint_x,
                    footprint_y=footprint_y,
                    footprint_width=footprint_width,
                    footprint_height=footprint_height,
                )
            )
    return tuple(instances)


def _instances_in_layout_order(instances: Sequence[_ResolvedInstance]) -> tuple[_ResolvedInstance, ...]:
    return tuple(
        sorted(
            instances,
            key=lambda instance: (
                round(instance.footprint_y, 4),
                round(instance.footprint_x, 4),
                instance.instance_key,
            ),
        )
    )


def _is_non_top_unsupported(entry) -> bool:
    return str(entry.plane_name or "").strip().lower() not in {"", "top"}


def _transferred_machinings(
    instances: Sequence[_ResolvedInstance],
) -> tuple[sp.MachiningSpec, ...]:
    adaptation_cache: dict[Path, PgmxAdaptationResult] = {}
    ordered_specs: list[sp.MachiningSpec] = []
    unsupported_messages: list[str] = []
    for instance in _instances_in_layout_order(instances):
        if instance.source_path not in adaptation_cache:
            adaptation_cache[instance.source_path] = adapt_pgmx_path(instance.source_path)
        adaptation = adaptation_cache[instance.source_path]
        for entry in adaptation.entries:
            if entry.status == "ignored":
                continue
            if entry.status == "unsupported":
                if _is_non_top_unsupported(entry):
                    continue
                unsupported_messages.append(
                    f"{instance.title_text} / {entry.feature_name or entry.feature_id}: "
                    f"{'; '.join(entry.reasons or ('sin detalle',))}"
                )
                continue
            spec = entry.spec
            if spec is None:
                continue
            if isinstance(spec, sp.SquaringMillingSpec):
                continue
            if getattr(spec, "plane_name", "Top") != "Top":
                continue
            transformed = transform_supported_spec(
                spec,
                instance.transform,
                feature_name_prefix=instance.title_text,
            )
            ordered_specs.append(transformed)
    if unsupported_messages:
        raise ValueError(
            "No se pueden transferir todos los mecanizados superiores del En-Juego:\n- "
            + "\n- ".join(unsupported_messages)
        )
    return tuple(ordered_specs)


def _format_mm(value: float) -> str:
    rounded = round(float(value), 3)
    if rounded.is_integer():
        return str(int(rounded))
    return str(rounded).rstrip("0").rstrip(".")


def _almost_equal(first: float, second: float, tolerance: float = DIVISION_TOLERANCE_MM) -> bool:
    return abs(first - second) <= tolerance


def _unique_axis_values(values: Sequence[float]) -> tuple[float, ...]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return ()
    clusters: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if abs(value - clusters[-1][-1]) <= DIVISION_TOLERANCE_MM:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return tuple(sum(cluster) / len(cluster) for cluster in clusters)


def _validate_no_piece_overlaps(instances: Sequence[_ResolvedInstance]) -> None:
    errors: list[str] = []
    ordered_instances = _instances_in_layout_order(instances)
    for first_index, first in enumerate(ordered_instances):
        for second in ordered_instances[first_index + 1 :]:
            overlap_x = min(first.right, second.right) - max(first.left, second.left)
            overlap_y = min(first.top, second.top) - max(first.bottom, second.bottom)
            if overlap_x > DIVISION_TOLERANCE_MM and overlap_y > DIVISION_TOLERANCE_MM:
                errors.append(
                    f"{first.title_text} / {second.title_text}: "
                    f"solape {_format_mm(overlap_x)} x {_format_mm(overlap_y)} mm"
                )
    if errors:
        raise ValueError(
            "No se puede sintetizar el En-Juego porque hay solapes entre piezas:\n- "
            + "\n- ".join(errors)
        )


def _validate_division_gap(
    gap_width: float,
    cutting_tool_width: float,
    context: str,
) -> None:
    if gap_width < cutting_tool_width - GEOMETRY_EPSILON_MM:
        raise ValueError(
            "No se puede sintetizar el En-Juego porque una separacion es menor "
            "que el diametro de la herramienta de division: "
            f"{context}; separacion {_format_mm(gap_width)} mm, "
            f"herramienta {_format_mm(cutting_tool_width)} mm."
        )


def _validate_uniform_division_gap(
    segments: Sequence[_DivisionSegment],
    extra_gaps: Sequence[float],
) -> None:
    gap_values = [segment.gap_width for segment in segments] + [float(value) for value in extra_gaps]
    if not gap_values:
        return
    min_gap = min(gap_values)
    max_gap = max(gap_values)
    if max_gap - min_gap > DIVISION_TOLERANCE_MM:
        segment_names = " / ".join(
            f"{segment.before_title}-{segment.after_title}"
            for segment in segments
        )
        raise ValueError(
            "No se puede sintetizar el En-Juego porque la separacion no es "
            "uniforme en una division: "
            f"{segment_names}; minimo {_format_mm(min_gap)} mm, "
            f"maximo {_format_mm(max_gap)} mm, tolerancia "
            f"{_format_mm(DIVISION_TOLERANCE_MM)} mm."
        )


def _vertical_division_bands(
    instances: Sequence[_ResolvedInstance],
    cutting_tool_width: float,
) -> tuple[tuple[_DivisionSegment, ...], ...]:
    edges = _unique_axis_values([value for instance in instances for value in (instance.bottom, instance.top)])
    bands: list[tuple[_DivisionSegment, ...]] = []
    for start, end in zip(edges, edges[1:]):
        if end - start <= DIVISION_TOLERANCE_MM:
            continue
        mid_y = (start + end) / 2.0
        active_instances = [
            instance
            for instance in instances
            if instance.bottom <= mid_y <= instance.top
        ]
        if len(active_instances) < 2:
            continue
        active_instances.sort(key=lambda instance: (instance.left, instance.instance_key))
        segments: list[_DivisionSegment] = []
        for rank, (left_instance, right_instance) in enumerate(
            zip(active_instances, active_instances[1:])
        ):
            gap_width = right_instance.left - left_instance.right
            context = (
                f"division vertical entre '{left_instance.title_text}' y "
                f"'{right_instance.title_text}'"
            )
            _validate_division_gap(gap_width, cutting_tool_width, context)
            segments.append(
                _DivisionSegment(
                    orientation="vertical",
                    rank=rank,
                    center=left_instance.right + (gap_width / 2.0),
                    band_start=start,
                    band_end=end,
                    gap_width=gap_width,
                    before_title=left_instance.title_text,
                    after_title=right_instance.title_text,
                )
            )
        if segments:
            bands.append(tuple(segments))
    return tuple(bands)


def _horizontal_division_bands(
    instances: Sequence[_ResolvedInstance],
    cutting_tool_width: float,
) -> tuple[tuple[_DivisionSegment, ...], ...]:
    edges = _unique_axis_values([value for instance in instances for value in (instance.left, instance.right)])
    bands: list[tuple[_DivisionSegment, ...]] = []
    for start, end in zip(edges, edges[1:]):
        if end - start <= DIVISION_TOLERANCE_MM:
            continue
        mid_x = (start + end) / 2.0
        active_instances = [
            instance
            for instance in instances
            if instance.left <= mid_x <= instance.right
        ]
        if len(active_instances) < 2:
            continue
        active_instances.sort(key=lambda instance: (instance.bottom, instance.instance_key))
        segments: list[_DivisionSegment] = []
        for rank, (bottom_instance, top_instance) in enumerate(
            zip(active_instances, active_instances[1:])
        ):
            gap_width = top_instance.bottom - bottom_instance.top
            context = (
                f"division horizontal entre '{bottom_instance.title_text}' y "
                f"'{top_instance.title_text}'"
            )
            _validate_division_gap(gap_width, cutting_tool_width, context)
            segments.append(
                _DivisionSegment(
                    orientation="horizontal",
                    rank=rank,
                    center=bottom_instance.top + (gap_width / 2.0),
                    band_start=start,
                    band_end=end,
                    gap_width=gap_width,
                    before_title=bottom_instance.title_text,
                    after_title=top_instance.title_text,
                )
            )
        if segments:
            bands.append(tuple(segments))
    return tuple(bands)


def _chain_division_segments(
    orientation: str,
    bands: Sequence[tuple[_DivisionSegment, ...]],
    board_start: float,
    board_end: float,
    cutting_tool_width: float,
) -> tuple[_DivisionPath, ...]:
    active_paths: dict[int, list[_DivisionSegment]] = {}
    paths: list[_DivisionPath] = []
    previous_band_size: Optional[int] = None

    def finish_path(rank: int) -> None:
        segments = active_paths.pop(rank, None)
        if segments:
            paths.append(
                _build_division_path(
                    orientation,
                    tuple(segments),
                    board_start,
                    board_end,
                    cutting_tool_width,
                )
            )

    for band in bands:
        if previous_band_size is not None and len(band) != previous_band_size:
            for rank in tuple(active_paths):
                finish_path(rank)
        previous_band_size = len(band)
        present_ranks: set[int] = set()
        for segment in band:
            present_ranks.add(segment.rank)
            active_paths.setdefault(segment.rank, []).append(segment)
        for rank in tuple(active_paths):
            if rank not in present_ranks:
                finish_path(rank)
    for rank in tuple(active_paths):
        finish_path(rank)
    return tuple(path for path in paths if len(path.points) >= 2)


def _build_division_path(
    orientation: str,
    segments: tuple[_DivisionSegment, ...],
    board_start: float,
    board_end: float,
    cutting_tool_width: float,
) -> _DivisionPath:
    ordered_segments = tuple(sorted(segments, key=lambda segment: (segment.band_start, segment.band_end)))
    extra_gaps: list[float] = []
    centers = [segment.center for segment in ordered_segments]
    center_is_straight = max(centers) - min(centers) <= DIVISION_TOLERANCE_MM
    points: list[tuple[float, float]]

    if center_is_straight:
        center = sum(centers) / len(centers)
        first = ordered_segments[0]
        last = ordered_segments[-1]
        points = (
            [(center, first.band_start), (center, last.band_end)]
            if orientation == "vertical"
            else [(first.band_start, center), (last.band_end, center)]
        )
    else:
        first = ordered_segments[0]
        points = (
            [(first.center, first.band_start)]
            if orientation == "vertical"
            else [(first.band_start, first.center)]
        )
        for previous, current in zip(ordered_segments, ordered_segments[1:]):
            transition_gap = current.band_start - previous.band_end
            context = f"escalon de division {orientation}"
            _validate_division_gap(transition_gap, cutting_tool_width, context)
            extra_gaps.append(transition_gap)
            transition_center = previous.band_end + (transition_gap / 2.0)
            if orientation == "vertical":
                points.append((previous.center, transition_center))
                points.append((current.center, transition_center))
            else:
                points.append((transition_center, previous.center))
                points.append((transition_center, current.center))
        last = ordered_segments[-1]
        points.append(
            (last.center, last.band_end)
            if orientation == "vertical"
            else (last.band_end, last.center)
        )

    _validate_uniform_division_gap(ordered_segments, extra_gaps)
    normalized_points = _dedupe_path_points(points)
    is_full = (
        ordered_segments[0].band_start <= board_start + DIVISION_TOLERANCE_MM
        and ordered_segments[-1].band_end >= board_end - DIVISION_TOLERANCE_MM
    )
    return _DivisionPath(
        orientation=orientation,
        segments=ordered_segments,
        points=normalized_points,
        is_full=is_full,
    )


def _dedupe_path_points(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    deduped: list[tuple[float, float]] = []
    for point in points:
        rounded_point = (round(float(point[0]), 4), round(float(point[1]), 4))
        if deduped and _almost_equal(deduped[-1][0], rounded_point[0]) and _almost_equal(
            deduped[-1][1],
            rounded_point[1],
        ):
            continue
        deduped.append(rounded_point)
    return tuple(deduped)


def _division_sort_key(path: _DivisionPath) -> tuple[int, int, float, float]:
    orientation_order = 0 if path.orientation == "vertical" else 1
    if path.orientation == "vertical":
        primary = min(point[0] for point in path.points)
        secondary = min(point[1] for point in path.points)
    else:
        primary = min(point[1] for point in path.points)
        secondary = min(point[0] for point in path.points)
    return (0 if path.is_full else 1, orientation_order, primary, secondary)


def _division_feature_name(path: _DivisionPath, index: int) -> str:
    orientation_text = "vertical" if path.orientation == "vertical" else "horizontal"
    scope_text = "completa" if path.is_full else "interrumpida"
    return f"Division {orientation_text} {scope_text} {index}"


def _build_division_spec(
    path: _DivisionPath,
    index: int,
    settings: dict,
    cutting_tool_id: str,
    cutting_tool_name: str,
    cutting_tool_width: float,
):
    feature_name = _division_feature_name(path, index)
    common_kwargs = {
        "approach_enabled": _safe_bool(settings.get("approach_enabled"), False),
        "approach_type": str(settings.get("approach_type") or "Arc"),
        "approach_mode": str(settings.get("approach_mode") or "Quote"),
        "approach_radius_multiplier": _nonnegative_setting(
            settings.get("approach_radius_multiplier"),
            2.0,
        ),
        "retract_enabled": _safe_bool(settings.get("retract_enabled"), False),
        "retract_type": str(settings.get("retract_type") or "Arc"),
        "retract_mode": str(settings.get("retract_mode") or "Quote"),
        "retract_radius_multiplier": _nonnegative_setting(
            settings.get("retract_radius_multiplier"),
            2.0,
        ),
        "milling_strategy": _build_division_strategy(settings),
    }
    if len(path.points) == 2:
        return sp.build_line_milling_spec(
            path.points[0][0],
            path.points[0][1],
            path.points[1][0],
            path.points[1][1],
            feature_name,
            cutting_tool_id,
            cutting_tool_name,
            cutting_tool_width,
            None,
            line_side_of_feature="Center",
            line_approach_enabled=common_kwargs["approach_enabled"],
            line_approach_type=common_kwargs["approach_type"],
            line_approach_mode=common_kwargs["approach_mode"],
            line_approach_radius_multiplier=common_kwargs["approach_radius_multiplier"],
            line_retract_enabled=common_kwargs["retract_enabled"],
            line_retract_type=common_kwargs["retract_type"],
            line_retract_mode=common_kwargs["retract_mode"],
            line_retract_radius_multiplier=common_kwargs["retract_radius_multiplier"],
            line_milling_strategy=common_kwargs["milling_strategy"],
            **_division_depth_kwargs(settings),
        )
    return sp.build_polyline_milling_spec(
        path.points,
        feature_name=feature_name,
        tool_id=cutting_tool_id,
        tool_name=cutting_tool_name,
        tool_width=cutting_tool_width,
        security_plane=None,
        side_of_feature="Center",
        **common_kwargs,
        **_division_polyline_depth_kwargs(settings),
    )


def _division_specs(
    instances: Sequence[_ResolvedInstance],
    settings: dict,
) -> tuple[sp.MachiningSpec, ...]:
    cutting_tool_id = str(settings.get("cutting_tool_id") or "").strip()
    cutting_tool_name = _resolved_tool_name(settings, "cutting")
    cutting_tool_width = _nonnegative_setting(settings.get("cutting_tool_diameter"), 0.0)
    if not cutting_tool_id or not cutting_tool_name or cutting_tool_width <= 0.0:
        raise ValueError("Debe configurar una herramienta de division valida antes de crear el En-Juego.")

    _validate_no_piece_overlaps(instances)
    min_x = min(instance.left for instance in instances)
    max_x = max(instance.right for instance in instances)
    min_y = min(instance.bottom for instance in instances)
    max_y = max(instance.top for instance in instances)

    vertical_paths = _chain_division_segments(
        "vertical",
        _vertical_division_bands(instances, cutting_tool_width),
        min_y,
        max_y,
        cutting_tool_width,
    )
    horizontal_paths = _chain_division_segments(
        "horizontal",
        _horizontal_division_bands(instances, cutting_tool_width),
        min_x,
        max_x,
        cutting_tool_width,
    )
    paths = tuple(sorted(vertical_paths + horizontal_paths, key=_division_sort_key))
    specs: list[sp.MachiningSpec] = []
    for index, path in enumerate(paths, start=1):
        spec = _build_division_spec(
            path,
            index,
            settings,
            cutting_tool_id,
            cutting_tool_name,
            cutting_tool_width,
        )
        if spec is not None:
            specs.append(spec)
    if not specs and len(instances) > 1:
        raise ValueError("No se pudieron detectar divisiones interiores validas para el En-Juego.")
    return tuple(specs)


def _squaring_spec(module_name: str, settings: dict) -> sp.SquaringMillingSpec:
    squaring_tool_id = str(settings.get("squaring_tool_id") or "").strip()
    squaring_tool_name = _resolved_tool_name(settings, "squaring")
    squaring_tool_width = _nonnegative_setting(settings.get("squaring_tool_diameter"), 0.0)
    if not squaring_tool_id or not squaring_tool_name or squaring_tool_width <= 0.0:
        raise ValueError("Debe configurar una herramienta de escuadrado valida antes de crear el En-Juego.")
    return sp.build_squaring_milling_spec(
        feature_name=f"{module_name} - Escuadrado",
        tool_id=squaring_tool_id,
        tool_name=squaring_tool_name,
        tool_width=squaring_tool_width,
        winding=str(settings.get("squaring_direction") or "CW"),
        approach_enabled=_safe_bool(settings.get("squaring_approach_enabled"), False),
        approach_type=str(settings.get("squaring_approach_type") or "Arc"),
        approach_mode=str(settings.get("squaring_approach_mode") or "Quote"),
        approach_radius_multiplier=_nonnegative_setting(
            settings.get("squaring_approach_radius_multiplier"),
            2.0,
        ),
        retract_enabled=_safe_bool(settings.get("squaring_retract_enabled"), False),
        retract_type=str(settings.get("squaring_retract_type") or "Arc"),
        retract_mode=str(settings.get("squaring_retract_mode") or "Quote"),
        retract_radius_multiplier=_nonnegative_setting(
            settings.get("squaring_retract_radius_multiplier"),
            2.0,
        ),
        milling_strategy=_build_squaring_strategy(settings),
        **_squaring_depth_kwargs(settings),
    )


def _ordered_machinings(
    transferred_specs: Sequence[sp.MachiningSpec],
    division_specs: Sequence[sp.MachiningSpec],
    squaring_spec: sp.SquaringMillingSpec,
    settings: dict,
) -> tuple[sp.MachiningSpec, ...]:
    raw_order = str(settings.get("division_squaring_order") or "").strip().lower()
    if raw_order == "squaring_then_division":
        return tuple(transferred_specs) + (squaring_spec,) + tuple(division_specs)
    return tuple(transferred_specs) + tuple(division_specs) + (squaring_spec,)


def create_en_juego_pgmx(
    project: Project,
    module_name: str,
    module_path: Path,
    piece_rows: Sequence[dict],
    saved_layout: dict,
    settings: Optional[dict],
    output_path: Path,
) -> EnJuegoPgmxResult:
    en_juego_rows = [
        row
        for row in piece_rows
        if bool(row.get("en_juego", False)) and _safe_float(row.get("thickness")) is not None
    ]
    if not en_juego_rows:
        raise ValueError("No hay piezas marcadas como 'En juego' con espesor valido.")

    thickness_values = sorted(
        {
            round(float(thickness_value), 6)
            for thickness_value in (_safe_float(row.get("thickness")) for row in en_juego_rows)
            if thickness_value is not None and thickness_value > 0
        }
    )
    if not thickness_values:
        raise ValueError("Las piezas de 'En juego' no tienen un espesor valido.")
    if len(thickness_values) > 1:
        thickness_text = ", ".join(
            str(int(value)) if float(value).is_integer() else str(value)
            for value in thickness_values
        )
        raise ValueError(
            "El archivo 'En-Juego' requiere que todas las piezas tengan el mismo espesor. "
            f"Se encontraron: {thickness_text}."
        )

    normalized_settings = dict(settings or {})
    instances = _resolve_instances(
        project,
        module_name,
        module_path,
        en_juego_rows,
        saved_layout if isinstance(saved_layout, dict) else {},
    )
    if not instances:
        raise ValueError("No hay instancias validas para generar el archivo 'En-Juego'.")

    min_x = min(instance.left for instance in instances)
    min_y = min(instance.bottom for instance in instances)
    max_x = max(instance.right for instance in instances)
    max_y = max(instance.top for instance in instances)
    board_width = round(max_x - min_x, 4)
    board_height = round(max_y - min_y, 4)
    board_thickness = float(thickness_values[0])

    transferred_specs = _transferred_machinings(instances)
    division_specs = _division_specs(instances, normalized_settings)
    squaring_milling = _squaring_spec(module_name, normalized_settings)
    ordered_specs = _ordered_machinings(
        transferred_specs,
        division_specs,
        squaring_milling,
        normalized_settings,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    piece_name = _sanitize_filename(f"{module_name}_EnJuego")
    request = sp.build_synthesis_request(
        output_path=output_path,
        piece_name=piece_name,
        length=board_width,
        width=board_height,
        depth=board_thickness,
        origin_x=_setting_float(normalized_settings, "origin_x", 0.0),
        origin_y=_setting_float(normalized_settings, "origin_y", 0.0),
        origin_z=_setting_float(normalized_settings, "origin_z", 0.0),
        ordered_machinings=ordered_specs,
    )
    sp.synthesize_request(request)
    return EnJuegoPgmxResult(
        output_path=output_path,
        piece_name=piece_name,
        board_width=board_width,
        board_height=board_height,
        board_thickness=board_thickness,
        instance_count=len(instances),
        contour_count=len(division_specs),
        fallback_contour_count=0,
    )
