"""Piece-row helpers for project detail inspection."""

from pathlib import Path
from typing import Callable, Iterable

from app.settings import _parse_piece_quantity_value
from core.model import (
    PIECE_GRAIN_CODE_NONE,
    Piece,
    normalize_piece_grain_direction,
    normalize_piece_observations,
)
from pgmx.processing import get_pgmx_program_dimensions


def coerce_saved_flag(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    raw = str(value or "").strip().lower()
    return raw in {"1", "true", "yes", "si", "s\u00ed", "x"}


def normalize_piece_row_flags(piece_row: dict) -> dict:
    normalized_row = dict(piece_row)
    en_juego_value = coerce_saved_flag(normalized_row.get("en_juego", False))
    excel_value = coerce_saved_flag(
        normalized_row.get("include_in_sheet", normalized_row.get("excel", False))
    )
    normalized_row["en_juego"] = en_juego_value
    normalized_row["include_in_sheet"] = excel_value
    normalized_row["quantity"] = _parse_piece_quantity_value(
        normalized_row.get("quantity"),
        default=1,
    )
    normalized_row["grain_direction"] = normalize_piece_grain_direction(normalized_row.get("grain_direction"))
    normalized_row["observations"] = normalize_piece_observations(normalized_row.get("observations"))
    normalized_row.pop("excel", None)
    normalized_row.pop("quantity_step", None)
    return normalized_row


def parse_piece_dimension(raw_value) -> float:
    raw_text = "" if raw_value is None else str(raw_value).strip().replace(",", ".")
    if not raw_text:
        return 0.0
    try:
        return float(raw_text)
    except (ValueError, TypeError):
        return 0.0


def parse_module_setting_dimension(raw_value):
    raw_text = "" if raw_value is None else str(raw_value).strip().replace(",", ".")
    if not raw_text:
        return ""
    try:
        number = float(raw_text)
    except ValueError:
        return raw_value
    return int(number) if number.is_integer() else round(number, 2)


def parse_optional_piece_float(raw_value) -> float | None:
    raw_text = "" if raw_value is None else str(raw_value).strip().replace(",", ".")
    if not raw_text:
        return None
    try:
        return float(raw_text)
    except (ValueError, TypeError):
        return None


def parse_positive_optional_piece_float(raw_value) -> float | None:
    parsed = parse_optional_piece_float(raw_value)
    if parsed is None:
        return None
    return parsed if parsed > 0 else None


def build_piece_from_row(piece_row: dict, module_name: str) -> Piece:
    thickness_val = piece_row.get("thickness")
    if thickness_val == "" or thickness_val is None:
        thickness = None
    else:
        try:
            thickness = float(thickness_val)
        except (ValueError, TypeError):
            thickness = None

    quantity = _parse_piece_quantity_value(piece_row.get("quantity"), default=1)

    return Piece(
        id=str(piece_row.get("id") or "").strip() or str(piece_row.get("name") or "pieza").strip(),
        name=str(piece_row.get("name") or piece_row.get("id") or "pieza").strip(),
        quantity=quantity,
        height=parse_piece_dimension(piece_row.get("height")),
        width=parse_piece_dimension(piece_row.get("width")),
        thickness=thickness,
        color=piece_row.get("color"),
        grain_direction=normalize_piece_grain_direction(piece_row.get("grain_direction")),
        module_name=module_name,
        cnc_source=str(piece_row.get("source") or "").strip() or None,
        f6_source=str(piece_row.get("f6_source") or "").strip() or None,
        piece_type=piece_row.get("piece_type"),
        program_width=parse_positive_optional_piece_float(piece_row.get("program_width")),
        program_height=parse_positive_optional_piece_float(piece_row.get("program_height")),
        program_thickness=parse_positive_optional_piece_float(piece_row.get("program_thickness")),
    )


def normalize_source_path(file_path: str, module_path: Path) -> str:
    if not file_path:
        return ""
    try:
        relative = Path(file_path).resolve().relative_to(module_path.resolve())
        return str(relative).replace("\\", "/")
    except Exception:
        return file_path


def serialize_piece_rows_for_config(piece_rows: Iterable[dict]) -> list[dict]:
    serialized_rows: list[dict] = []
    for row in piece_rows:
        serialized_row = dict(row)
        serialized_row["quantity"] = _parse_piece_quantity_value(
            serialized_row.get("quantity"),
            default=1,
        )
        serialized_row["en_juego"] = bool(serialized_row.get("en_juego", False))
        include_in_sheet = bool(serialized_row.get("include_in_sheet", serialized_row.get("excel", False)))
        serialized_row["include_in_sheet"] = include_in_sheet
        serialized_row["grain_direction"] = normalize_piece_grain_direction(serialized_row.get("grain_direction"))
        serialized_row["observations"] = normalize_piece_observations(serialized_row.get("observations"))
        serialized_row.pop("excel", None)
        serialized_row.pop("quantity_step", None)
        serialized_rows.append(serialized_row)
    return serialized_rows


def build_module_pieces_from_rows(piece_rows: Iterable[dict], module_name: str) -> list[Piece]:
    pieces: list[Piece] = []
    for row in piece_rows:
        piece_dict = dict(row)
        if "source" in piece_dict:
            piece_dict["cnc_source"] = piece_dict.pop("source")
        if "module_name" not in piece_dict:
            piece_dict["module_name"] = module_name
        piece_dict.pop("pgmx", None)
        piece_dict.pop("en_juego", None)
        piece_dict.pop("include_in_sheet", None)
        piece_dict.pop("excel", None)
        piece_dict.pop("observations", None)
        piece_dict.pop("quantity_step", None)

        piece_dict["quantity"] = _parse_piece_quantity_value(piece_dict.get("quantity"), default=1)
        piece_dict["grain_direction"] = normalize_piece_grain_direction(piece_dict.get("grain_direction"))
        piece_dict["thickness"] = parse_optional_piece_float(piece_dict.get("thickness"))
        piece_dict["height"] = parse_piece_dimension(piece_dict.get("height"))
        piece_dict["width"] = parse_piece_dimension(piece_dict.get("width"))
        piece_dict["program_width"] = parse_optional_piece_float(piece_dict.get("program_width"))
        piece_dict["program_height"] = parse_optional_piece_float(piece_dict.get("program_height"))
        piece_dict["program_thickness"] = parse_optional_piece_float(piece_dict.get("program_thickness"))

        try:
            pieces.append(Piece(**piece_dict))
        except Exception:
            continue
    return pieces


def normalized_program_reference_keys(source_value: str, module_path: Path) -> set[str]:
    raw_source = str(source_value or "").strip()
    if not raw_source:
        return set()

    keys = {raw_source.replace("\\", "/").lower(), Path(raw_source).name.lower()}
    source_path = Path(raw_source)
    candidate_path = source_path if source_path.is_absolute() else module_path / source_path
    if candidate_path.is_file():
        try:
            keys.add(str(candidate_path.resolve()).lower())
        except OSError:
            keys.add(str(candidate_path).lower())
    return keys


def associated_program_reference_keys(piece_rows: Iterable[dict], module_path: Path) -> set[str]:
    keys: set[str] = set()
    for piece_row in piece_rows:
        keys.update(normalized_program_reference_keys(str(piece_row.get("source") or ""), module_path))
        keys.update(normalized_program_reference_keys(str(piece_row.get("f6_source") or ""), module_path))
    return keys


def find_orphan_pgmx_files(module_path: Path, piece_rows: Iterable[dict]) -> list[Path]:
    associated_keys = associated_program_reference_keys(piece_rows, module_path)
    orphans: list[Path] = []
    for pgmx_file in sorted(module_path.rglob("*.pgmx"), key=lambda item: str(item.relative_to(module_path)).lower()):
        if not pgmx_file.is_file():
            continue
        relative_key = str(pgmx_file.relative_to(module_path)).replace("\\", "/").lower()
        try:
            resolved_key = str(pgmx_file.resolve()).lower()
        except OSError:
            resolved_key = str(pgmx_file).lower()
        if (
            relative_key in associated_keys
            or pgmx_file.name.lower() in associated_keys
            or resolved_key in associated_keys
        ):
            continue
        orphans.append(pgmx_file)
    return orphans


def unique_orphan_piece_id(program_path: Path, piece_rows: Iterable[dict]) -> str:
    existing_ids = {str(row.get("id") or "").strip().lower() for row in piece_rows}
    base_id = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in program_path.stem.strip()
    ).strip("_") or "PGMX"
    candidate = base_id
    suffix = 2
    while candidate.lower() in existing_ids:
        candidate = f"{base_id}_{suffix}"
        suffix += 1
    return candidate


def infer_companion_f6_source(source_value: str, module_path: Path) -> str | None:
    normalized_source = str(source_value or "").strip()
    if not normalized_source:
        return None

    source_path = Path(normalized_source)
    if not source_path.is_absolute():
        source_path = module_path / source_path

    if source_path.stem.lower().endswith("f6"):
        return None

    f6_candidate = source_path.with_name(f"{source_path.stem}F6{source_path.suffix}")
    if f6_candidate.is_file():
        return normalize_source_path(str(f6_candidate), module_path)
    return None


def build_orphan_program_row(
    *,
    project,
    module_path: Path,
    module_name: str,
    program_path: Path,
    existing_rows: Iterable[dict],
    pgmx_status: Callable[[str], str],
) -> dict:
    source_value = normalize_source_path(str(program_path), module_path)
    piece_id = unique_orphan_piece_id(program_path, existing_rows)
    temp_piece = Piece(
        id=piece_id,
        name=program_path.stem,
        width=0.0,
        height=0.0,
        thickness=None,
        module_name=module_name,
        cnc_source=source_value,
    )
    program_width, program_height, program_thickness = get_pgmx_program_dimensions(
        project,
        temp_piece,
        module_path,
    )
    return {
        "id": piece_id,
        "name": program_path.stem,
        "quantity": 1,
        "height": program_width or "",
        "width": program_height or "",
        "thickness": program_thickness,
        "color": None,
        "grain_direction": PIECE_GRAIN_CODE_NONE,
        "source": source_value,
        "f6_source": None,
        "pgmx": pgmx_status(source_value),
        "piece_type": None,
        "program_width": program_width,
        "program_height": program_height,
        "program_thickness": program_thickness,
        "en_juego": False,
        "include_in_sheet": False,
        "observations": "",
    }
