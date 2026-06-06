"""Board definition preparation for cut nesting."""

from __future__ import annotations

from core.nesting_model import CutBoard


def _safe_float(value):
    raw_value = str(value).strip().replace(",", ".")
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def normalize_board_definition(board_definition: dict) -> dict | None:
    if not isinstance(board_definition, dict):
        return None

    color = str(board_definition.get("color") or "").strip()
    grain = str(board_definition.get("grain") or board_definition.get("veta") or "").strip()
    length = _safe_float(board_definition.get("length"))
    width = _safe_float(board_definition.get("width"))
    thickness = _safe_float(board_definition.get("thickness"))
    margin = _safe_float(board_definition.get("margin"))

    if margin is None:
        margin = 0.0

    if not color or length is None or width is None or thickness is None:
        return None
    if length <= 0 or width <= 0 or thickness <= 0 or margin < 0:
        return None
    if margin * 2 >= min(length, width):
        return None

    return {
        "color": color,
        "length": length,
        "width": width,
        "thickness": thickness,
        "grain": grain,
        "margin": margin,
    }


def apply_board_margin(boards: list[CutBoard], board_width: float, board_height: float, board_margin: float) -> list[CutBoard]:
    resolved_board_width = _safe_float(board_width) or 0.0
    resolved_board_height = _safe_float(board_height) or 0.0
    normalized_margin = max(0.0, _safe_float(board_margin) or 0.0)
    board_area = float(resolved_board_width * resolved_board_height)

    for board in boards:
        if normalized_margin > 0:
            for placement in board.placements:
                placement.x += normalized_margin
                placement.y += normalized_margin
            board.main_cut_positions = [position + normalized_margin for position in board.main_cut_positions]

        board.board_width = float(resolved_board_width)
        board.board_height = float(resolved_board_height)
        board.board_margin = normalized_margin

        used_area = sum(placement.width * placement.height for placement in board.placements)
        board.utilization = used_area / board_area if board_area > 0 else 0.0

    return boards


def resolve_board_definition(material: str, thickness: float, board_definitions: list[dict]) -> dict | None:
    matches: list[dict] = []
    material_key = str(material or "").strip().lower()
    for raw_definition in board_definitions:
        definition = normalize_board_definition(raw_definition)
        if definition is None:
            continue
        if str(definition["color"]).strip().lower() != material_key:
            continue
        if abs(float(definition["thickness"]) - float(thickness)) > 0.01:
            continue
        matches.append(definition)

    if not matches:
        return None

    return max(matches, key=lambda item: (float(item["length"]) * float(item["width"]), float(item["length"]), float(item["width"])))


__all__ = [
    "apply_board_margin",
    "normalize_board_definition",
    "resolve_board_definition",
]
