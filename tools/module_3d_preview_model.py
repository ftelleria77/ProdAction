"""Shared module preview model used by standalone 3D renderer prototypes."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_LIBRARY_ROOT = Path(r"S:\Maestro\Projects\01 - Mobile STD\01 - BM - Bajomesada")
DEFAULT_SAMPLE_CODE = "BM-2P-PC-800"
DEFAULT_HEIGHT_MM = 742.0
DEFAULT_DEPTH_MM = 580.0
DEFAULT_THICKNESS_MM = 18.0


@dataclass
class CsvPiece:
    row_code: str
    piece_type: str
    name: str
    quantity: int
    dim_a: float
    dim_b: float
    thickness: float
    material: str
    grain: str
    source: str


@dataclass
class PreviewBox:
    name: str
    piece_type: str
    size_x: float
    size_y: float
    size_z: float
    center_x: float
    center_y: float
    center_z: float
    color: str
    opacity: float = 1.0
    is_internal: bool = False


@dataclass
class ModulePreviewModel:
    name: str
    width: float
    height: float
    depth: float
    pieces_count: int = 0
    boxes: list[PreviewBox] = field(default_factory=list)
    represented_piece_keys: set[str] = field(default_factory=set)
    omitted_pieces: list[str] = field(default_factory=list)
    source_path: Path | None = None


@dataclass
class LibraryModuleSummary:
    csv_path: Path
    pieces_count: int
    boxes_count: int
    represented_count: int
    omitted_pieces: list[str]
    missing_sources: list[str]


def safe_float(value, default: float = 0.0) -> float:
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def safe_int(value, default: int = 1) -> int:
    try:
        return max(int(round(safe_float(value, default))), 1)
    except (TypeError, ValueError):
        return default


def piece_key(piece: CsvPiece) -> str:
    return "\0".join(
        [
            str(piece.row_code).casefold(),
            str(piece.piece_type).casefold(),
            str(piece.name).casefold(),
            str(piece.source).casefold(),
        ]
    )


def compact_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def format_mm(value: float) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.1f}"


def extract_nominal_numbers(module_name: str) -> list[float]:
    return [safe_float(match) for match in re.findall(r"(?<![A-Za-z])(\d+(?:[.,]\d+)?)(?![A-Za-z])", module_name)]


def read_maestro_csv(csv_path: Path) -> list[CsvPiece]:
    pieces: list[CsvPiece] = []
    with csv_path.open("r", encoding="latin-1", newline="") as file:
        for row in csv.reader(file, delimiter=";"):
            if len(row) < 11:
                continue
            pieces.append(
                CsvPiece(
                    row_code=str(row[0]).strip(),
                    piece_type=str(row[1]).strip(),
                    name=str(row[2]).strip(),
                    quantity=safe_int(row[3]),
                    dim_a=safe_float(row[5]),
                    dim_b=safe_float(row[6]),
                    thickness=safe_float(row[7]),
                    material=str(row[8]).strip(),
                    grain=str(row[9]).strip(),
                    source=str(row[10]).strip(),
                )
            )
    return pieces


def builtin_sample_pieces() -> list[CsvPiece]:
    raw_rows = [
        ("1FSX", "F1", "Lateral_Izq", 1, 742, 580, 18, "BCO18", "0", "Lateral_Izq.pgmx"),
        ("2FDX", "F2", "Lateral_Der", 1, 742, 580, 18, "BCO18", "0", "Lateral_Der.pgmx"),
        ("3CP", "T", "Tapa", 1, 764, 580, 0, "BCO00", "0", "Tapa.pgmx"),
        ("4BS", "B", "Fondo", 1, 799.1, 580, 18, "BCO18", "0", "Fondo.pgmx"),
        ("5RP", "R", "Estante", 1, 764, 547, 18, "BCO18", "0", "Estante.pgmx"),
        ("6ANSX", "A1", "Puerta_Izq", 1, 723.1, 396.1, 18, "GAUDI18", "1", "Puerta_Izq.pgmx"),
        ("7ANDX", "A2", "Puerta_Der", 1, 723.1, 396.1, 18, "GAUDI18", "1", "Puerta_Der.pgmx"),
        ("8SCH", "S", "Trasera", 1, 717, 784, 3, "BCO3", "0", "Trasera.pgmx"),
        ("9PBF", "D2", "Faja frontal", 2, 70, 764, 18, "BCO18", "0", "Faja frontal.pgmx"),
    ]
    return [
        CsvPiece(
            row_code=row_code,
            piece_type=piece_type,
            name=name,
            quantity=int(quantity),
            dim_a=float(dim_a),
            dim_b=float(dim_b),
            thickness=float(thickness),
            material=material,
            grain=grain,
            source=source,
        )
        for row_code, piece_type, name, quantity, dim_a, dim_b, thickness, material, grain, source in raw_rows
    ]


def scan_library_csvs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*.csv")
        if path.parent.name.casefold() == path.stem.casefold()
    )


def iter_pgmx_files(module_dir: Path) -> list[Path]:
    if not module_dir.is_dir():
        return []
    return sorted(module_dir.rglob("*.pgmx"), key=lambda path: str(path).casefold())


def resolve_piece_source(module_dir: Path, piece: CsvPiece, pgmx_files: list[Path]) -> Path | None:
    raw_source = str(piece.source or "").strip().strip('"')
    if not raw_source:
        return None

    source_path = Path(raw_source)
    exact_candidate = module_dir / source_path
    if exact_candidate.is_file():
        return exact_candidate

    wanted_rel = str(source_path).replace("\\", "/").casefold()
    for pgmx_file in pgmx_files:
        try:
            rel_path = str(pgmx_file.relative_to(module_dir)).replace("\\", "/").casefold()
        except ValueError:
            rel_path = pgmx_file.name.casefold()
        if rel_path == wanted_rel:
            return pgmx_file

    source_key = compact_name(source_path.stem)
    piece_name_key = compact_name(piece.name)
    for pgmx_file in pgmx_files:
        pgmx_key = compact_name(pgmx_file.stem)
        if pgmx_key and pgmx_key in {source_key, piece_name_key}:
            return pgmx_file

    normalized_name = piece.name.casefold()
    if piece.piece_type in {"D1", "D2"} and "faja" in normalized_name:
        for pgmx_file in pgmx_files:
            if compact_name(pgmx_file.stem).startswith("faja"):
                return pgmx_file

    return None


def missing_piece_sources(csv_path: Path, pieces: list[CsvPiece]) -> list[str]:
    pgmx_files = iter_pgmx_files(csv_path.parent)
    missing_sources: list[str] = []
    for piece in pieces:
        raw_source = str(piece.source or "").strip()
        if not raw_source or Path(raw_source).suffix.casefold() != ".pgmx":
            continue
        if resolve_piece_source(csv_path.parent, piece, pgmx_files) is None:
            missing_sources.append(f"{piece.piece_type} {piece.name} -> {raw_source}")
    return missing_sources


def summarize_library_module(csv_path: Path) -> LibraryModuleSummary:
    pieces = read_maestro_csv(csv_path)
    model = build_preview_model(csv_path.parent.name, pieces, csv_path)
    return LibraryModuleSummary(
        csv_path=csv_path,
        pieces_count=len(pieces),
        boxes_count=len([box for box in model.boxes if box.name != "Floor"]),
        represented_count=len(model.represented_piece_keys),
        omitted_pieces=list(model.omitted_pieces),
        missing_sources=missing_piece_sources(csv_path, pieces),
    )


def print_scan_summary(module_paths: list[Path], *, limit: int = 0) -> None:
    selected_paths = module_paths[:limit] if limit > 0 else module_paths
    print(f"modules_found={len(module_paths)}")
    print(f"modules_listed={len(selected_paths)}")
    for index, csv_path in enumerate(selected_paths, start=1):
        summary = summarize_library_module(csv_path)
        print(
            f"[{index}] {csv_path.parent.name} | "
            f"pieces={summary.pieces_count} | "
            f"represented={summary.represented_count} | "
            f"boxes={summary.boxes_count} | "
            f"omitted={len(summary.omitted_pieces)} | "
            f"missing_pgmx={len(summary.missing_sources)}"
        )
        print(f"    path={csv_path.parent}")
        for missing_source in summary.missing_sources[:5]:
            print(f"    missing: {missing_source}")
        if len(summary.missing_sources) > 5:
            print(f"    missing: ... {len(summary.missing_sources) - 5} more")


def infer_dimensions(module_name: str, pieces: list[CsvPiece]) -> tuple[float, float, float]:
    nominal_numbers = extract_nominal_numbers(module_name)
    width = nominal_numbers[-1] if nominal_numbers else 0.0
    depth = DEFAULT_DEPTH_MM

    if len(nominal_numbers) >= 2 and nominal_numbers[-2] < 300 <= nominal_numbers[-1]:
        width = nominal_numbers[-2]
        depth = nominal_numbers[-1]

    laterals = [piece for piece in pieces if piece.piece_type in {"F1", "F2"}]
    height_candidates = [piece.dim_a for piece in laterals if piece.dim_a > 0]
    depth_candidates = [piece.dim_b for piece in laterals if piece.dim_b > 0]

    height = max(height_candidates) if height_candidates else DEFAULT_HEIGHT_MM
    if depth_candidates:
        depth = max(depth_candidates)

    if width <= 0:
        width_candidates = []
        for piece in pieces:
            if piece.piece_type in {"B", "S", "T", "R"}:
                width_candidates.extend([piece.dim_a, piece.dim_b])
        width = max(width_candidates) if width_candidates else 800.0

    return float(width), float(height), float(depth)


def panel_thickness(piece: CsvPiece) -> float:
    return piece.thickness if piece.thickness > 0 else DEFAULT_THICKNESS_MM


def material_color(material: str, piece_type: str) -> str:
    normalized = str(material or "").casefold()
    if "gaudi" in normalized:
        return "#b47d48"
    if "bc" in normalized or "bco" in normalized:
        if piece_type in {"S", "E"}:
            return "#d9dde3"
        return "#f3f1e9"
    if piece_type in {"A1", "A2", "H"}:
        return "#aa7a4b"
    return "#ccd4dd"


def append_box(
    model: ModulePreviewModel,
    piece: CsvPiece,
    *,
    size_x: float,
    size_y: float,
    size_z: float,
    center_x: float,
    center_y: float,
    center_z: float,
    opacity: float = 1.0,
    is_internal: bool = False,
    suffix: str = "",
) -> None:
    model.represented_piece_keys.add(piece_key(piece))
    model.boxes.append(
        PreviewBox(
            name=f"{piece.name}{suffix}",
            piece_type=piece.piece_type,
            size_x=max(float(size_x), 1.0),
            size_y=max(float(size_y), 1.0),
            size_z=max(float(size_z), 1.0),
            center_x=float(center_x),
            center_y=float(center_y),
            center_z=float(center_z),
            color=material_color(piece.material, piece.piece_type),
            opacity=float(opacity),
            is_internal=is_internal,
        )
    )


def front_panel_entries(pieces: list[CsvPiece]) -> list[tuple[CsvPiece, float, float]]:
    fronts: list[tuple[CsvPiece, float, float]] = []
    for piece in pieces:
        is_door = piece.piece_type in {"A1", "A2"} and "puerta" in piece.name.casefold()
        if not is_door:
            continue
        for _ in range(piece.quantity):
            fronts.append((piece, piece.dim_b, piece.dim_a))
    return fronts


def drawer_front_entries(pieces: list[CsvPiece]) -> list[tuple[CsvPiece, float, float]]:
    fronts: list[tuple[CsvPiece, float, float]] = []
    for piece in pieces:
        normalized_name = piece.name.casefold()
        if piece.piece_type != "H" or "cajon" not in normalized_name:
            continue
        for _ in range(piece.quantity):
            fronts.append((piece, piece.dim_b, piece.dim_a))
    return fronts


def build_preview_model(
    module_name: str,
    pieces: list[CsvPiece],
    source_path: Path | None = None,
    *,
    show_internal: bool = True,
) -> ModulePreviewModel:
    width, height, depth = infer_dimensions(module_name, pieces)
    model = ModulePreviewModel(module_name, width, height, depth, pieces_count=len(pieces), source_path=source_path)

    for piece in pieces:
        t = panel_thickness(piece)
        piece_type = piece.piece_type
        normalized_name = piece.name.casefold()

        if piece_type == "F1":
            append_box(
                model,
                piece,
                size_x=t,
                size_y=piece.dim_a or height,
                size_z=piece.dim_b or depth,
                center_x=-width / 2 + t / 2,
                center_y=(piece.dim_a or height) / 2,
                center_z=0,
            )
            continue

        if piece_type == "F2":
            append_box(
                model,
                piece,
                size_x=t,
                size_y=piece.dim_a or height,
                size_z=piece.dim_b or depth,
                center_x=width / 2 - t / 2,
                center_y=(piece.dim_a or height) / 2,
                center_z=0,
            )
            continue

        if piece_type == "T":
            append_box(
                model,
                piece,
                size_x=piece.dim_a or max(width - 2 * t, 1),
                size_y=t,
                size_z=piece.dim_b or depth,
                center_x=0,
                center_y=height - t / 2,
                center_z=0,
                is_internal=True,
            )
            continue

        if piece_type == "B":
            append_box(
                model,
                piece,
                size_x=piece.dim_a or width,
                size_y=t,
                size_z=piece.dim_b or depth,
                center_x=0,
                center_y=t / 2,
                center_z=0,
                is_internal=True,
            )
            continue

        if piece_type == "R":
            for index in range(piece.quantity):
                step = height / (piece.quantity + 1)
                y = step * (index + 1)
                append_box(
                    model,
                    piece,
                    size_x=piece.dim_a or max(width - 2 * t, 1),
                    size_y=t,
                    size_z=piece.dim_b or max(depth - 30, 1),
                    center_x=0,
                    center_y=y,
                    center_z=0,
                    opacity=0.82,
                    is_internal=True,
                    suffix=f" {index + 1}" if piece.quantity > 1 else "",
                )
            continue

        if piece_type == "S":
            append_box(
                model,
                piece,
                size_x=piece.dim_b or max(width - 16, 1),
                size_y=piece.dim_a or max(height - 25, 1),
                size_z=max(t, 3),
                center_x=0,
                center_y=(piece.dim_a or height) / 2,
                center_z=depth / 2 - max(t, 3) / 2,
                opacity=0.45,
                is_internal=True,
            )
            continue

        if piece_type in {"D1", "D2"} and "faja" in normalized_name:
            faja_height = piece.dim_a if piece.dim_a < piece.dim_b else piece.dim_b
            faja_width = piece.dim_b if piece.dim_b >= piece.dim_a else piece.dim_a
            positions = [height - faja_height / 2]
            if piece.quantity > 1:
                positions = [faja_height / 2, height - faja_height / 2]
            for index, y in enumerate(positions[: piece.quantity]):
                append_box(
                    model,
                    piece,
                    size_x=faja_width,
                    size_y=faja_height,
                    size_z=t,
                    center_x=0,
                    center_y=y,
                    center_z=-depth / 2 - t / 2,
                    opacity=0.72,
                    is_internal=True,
                    suffix=f" {index + 1}" if len(positions) > 1 else "",
                )
            continue

    door_entries = front_panel_entries(pieces)
    if door_entries:
        total_width = sum(entry[1] for entry in door_entries)
        x = -total_width / 2
        for piece, door_width, door_height in door_entries:
            t = panel_thickness(piece)
            x += door_width / 2
            append_box(
                model,
                piece,
                size_x=door_width,
                size_y=door_height,
                size_z=t,
                center_x=x,
                center_y=door_height / 2,
                center_z=-depth / 2 - t / 2,
                opacity=0.86,
            )
            x += door_width / 2

    drawer_entries = drawer_front_entries(pieces)
    if drawer_entries:
        gap = 4.0
        total_height = sum(entry[2] for entry in drawer_entries) + gap * (len(drawer_entries) - 1)
        y = max((height - total_height) / 2, gap)
        for piece, front_width, front_height in drawer_entries:
            t = panel_thickness(piece)
            y += front_height / 2
            append_box(
                model,
                piece,
                size_x=front_width,
                size_y=front_height,
                size_z=t,
                center_x=0,
                center_y=y,
                center_z=-depth / 2 - t / 2,
                opacity=0.88,
            )
            y += front_height / 2 + gap

    for piece in pieces:
        if piece_key(piece) not in model.represented_piece_keys:
            model.omitted_pieces.append(f"{piece.piece_type} {piece.name}")

    if not show_internal:
        model.boxes = [box for box in model.boxes if not box.is_internal]

    return model


def choose_initial_csv(module_paths: list[Path], requested_csv: Path | None) -> Path | None:
    if requested_csv is not None and requested_csv.is_file():
        return requested_csv
    for path in module_paths:
        if path.stem.casefold() == DEFAULT_SAMPLE_CODE.casefold():
            return path
    return module_paths[0] if module_paths else None


def build_model_from_source(
    *,
    csv_path: Path | None,
    show_internal: bool = True,
) -> ModulePreviewModel:
    if csv_path is not None and csv_path.is_file():
        pieces = read_maestro_csv(csv_path)
        return build_preview_model(csv_path.parent.name, pieces, csv_path, show_internal=show_internal)

    pieces = builtin_sample_pieces()
    return build_preview_model(DEFAULT_SAMPLE_CODE, pieces, None, show_internal=show_internal)


def print_model_self_test(model: ModulePreviewModel) -> int:
    display_box_count = len([box for box in model.boxes if box.name != "Floor"])
    print(f"module={model.name}")
    print(f"dimensions={format_mm(model.width)}x{format_mm(model.height)}x{format_mm(model.depth)}")
    print(f"source={model.source_path or 'builtin'}")
    print(f"pieces={model.pieces_count}")
    print(f"represented={len(model.represented_piece_keys)}")
    print(f"boxes={display_box_count}")
    print(f"omitted={len(model.omitted_pieces)}")
    return 0 if display_box_count else 1
