"""Módulo de parseo de archivos CNC y escaneo de proyecto."""

import csv
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.model import LocaleData, ModuleData, Piece

logger = logging.getLogger(__name__)

SUMMARY_FILE_SUFFIXES = {".csv"}
MODULE_SOURCE_EXTENSIONS = {".pgmx", ".csv"}


@dataclass
class ProjectFolderLayout:
    locale_dirs: list[Path] = field(default_factory=list)
    loose_module_dirs: list[Path] = field(default_factory=list)


def parse_cnc_file(file_path: Path, metadata: Optional[Dict[str, dict]] = None) -> List[Piece]:
    """Parse a CNC/PGMX file y extrae piezas.

    - Intenta leer líneas de pieza con formato "PIEZA <id> <w> <h> [thickness]".
    - Si no encuentra piezas, no falla; el módulo usará CSV para crear las piezas.
    """
    pieces = []
    piece_ids = set()
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Formato explícito con etiqueta "PIEZA"
            m = re.match(
                r"PIEZA\s+(\S+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)(?:\s+(\d+(?:\.\d+)?))?",
                line,
            )
            if m:
                piece_id = m.group(1)
                width = float(m.group(2))
                height = float(m.group(3))
                thickness = float(m.group(4)) if m.group(4) else None

                piece = Piece(
                    id=piece_id,
                    width=width,
                    height=height,
                    thickness=thickness,
                    quantity=1,
                    module_name="",
                    cnc_source=str(file_path),
                )

                if metadata and piece_id in metadata:
                    data = metadata[piece_id]
                    piece.name = data.get("name") or piece.id
                    piece.color = data.get("color")
                    piece.grain_direction = data.get("grain_direction") or data.get("sentido_veta") or data.get("veta")
                    piece.piece_type = data.get("piece_type")
                    if (not piece.width or piece.width == 0) and data.get("width"):
                        piece.width = float(data.get("width"))
                    if (not piece.height or piece.height == 0) and data.get("height"):
                        piece.height = float(data.get("height"))
                    if (not piece.thickness or piece.thickness == 0) and data.get("thickness"):
                        piece.thickness = float(data.get("thickness"))

                pieces.append(piece)
                piece_ids.add(piece_id)
                continue

            # Heurística alternativa: detectar líneas con id + ancho + alto (e.g. "A123 1200 800").
            m2 = re.match(r"^(?!PIEZA\b)(?P<id>[0-9A-Za-z_-]+)\s+(?P<width>\d+(?:\.\d+)?)\s+(?P<height>\d+(?:\.\d+)?)(?:\s+(?P<thickness>\d+(?:\.\d+)?))?", line, re.IGNORECASE)
            if m2:
                piece_id = m2.group("id")
                if piece_id not in piece_ids:
                    width = float(m2.group("width"))
                    height = float(m2.group("height"))
                    thickness = float(m2.group("thickness")) if m2.group("thickness") else None

                    piece = Piece(
                        id=piece_id,
                        width=width,
                        height=height,
                        thickness=thickness,
                        quantity=1,
                        module_name="",
                        cnc_source=str(file_path),
                    )
                    if metadata and piece_id in metadata:
                        data = metadata[piece_id]
                        piece.name = data.get("name") or piece.id
                        piece.color = data.get("color")
                        piece.grain_direction = data.get("grain_direction") or data.get("sentido_veta") or data.get("veta")
                        piece.piece_type = data.get("piece_type")
                        if (not piece.width or piece.width == 0) and data.get("width"):
                            piece.width = float(data.get("width"))
                        if (not piece.height or piece.height == 0) and data.get("height"):
                            piece.height = float(data.get("height"))
                        if (not piece.thickness or piece.thickness == 0) and data.get("thickness"):
                            piece.thickness = float(data.get("thickness"))

                    pieces.append(piece)
                    piece_ids.add(piece_id)

    # Si no se extrajeron piezas directamente, intentamos mapear nombres de archivo a CSV.
    if not pieces and metadata:
        for piece_id, data in metadata.items():
            new_piece = Piece(
                id=piece_id,
                width=float(data.get("width")) if data.get("width") else 0.0,
                height=float(data.get("height")) if data.get("height") else 0.0,
                thickness=float(data.get("thickness")) if data.get("thickness") else None,
                quantity=1,
                color=data.get("color"),
                grain_direction=data.get("grain_direction") or data.get("sentido_veta") or data.get("veta"),
                name=data.get("name") or piece_id,
                module_name="",
                cnc_source=data.get("source"),
                piece_type=data.get("piece_type"),
            )
            pieces.append(new_piece)

    return pieces


def load_module_summary(module_dir: Path) -> Dict[str, dict]:
    """Cargar CSV de resumen de piezas por módulo.

    Soporta:
    1. CSV con encabezados (detecta columnas por nombre)
    2. CSV sin encabezados con estructura fija: ID;...;ancho;alto;...;color;...
       (posiciones: 0=id, 5=ancho, 6=alto, 3=cantidad, 8=color)
    """
    lookup = {}

    def normalize(col_name: str) -> str:
        if not col_name:
            return ""
        return re.sub(r"[^a-z0-9]+", "", col_name.strip().lower())

    def parse_dimension(val: str) -> Optional[float]:
        """Convierte dimensión con coma o punto a float."""
        if not val:
            return None
        val = val.strip().replace(",", ".")
        try:
            return float(val)
        except ValueError:
            return None

    def parse_quantity(val: str) -> int:
        if val is None:
            return 1
        raw = str(val).strip().replace(",", ".")
        if not raw:
            return 1
        try:
            qty = int(float(raw))
            return qty if qty > 0 else 1
        except ValueError:
            return 1

    possible_ids = {normalize(x) for x in ["id", "pieza_id", "piece_id", "nombre", "pieza", "codigo"]}
    possible_widths = {normalize(x) for x in ["width", "ancho", "ancho_mm", "largo", "ancho_cm", "width_mm"]}
    possible_heights = {normalize(x) for x in ["height", "alto", "alto_mm", "alto_cm", "height_mm", "largo"]}
    possible_color = {normalize(x) for x in ["color", "colores", "tono", "color_id"]}
    possible_grain = {normalize(x) for x in ["grain_direction", "sentido_veta", "veta", "veta_sentido", "sentido"]}
    possible_quantity = {normalize(x) for x in ["quantity", "cantidad", "qty", "cant"]}

    summary_files = [
        summary_file
        for summary_file in module_dir.rglob("*")
        if summary_file.is_file() and summary_file.suffix.lower() in SUMMARY_FILE_SUFFIXES
    ]

    for summary_file in summary_files:
        logger.debug("Evaluando CSV %s para módulo %s", summary_file, module_dir.name)
        text = summary_file.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            logger.debug("CSV vacío en %s", summary_file)
            continue

        lines = text.strip().split("\n")
        if not lines:
            continue

        # Detectar delimitador (intentar ; primero, luego ,)
        delimiter = ";"
        if ";" not in lines[0]:
            delimiter = ","
        logger.debug("Delimitador detectado en línea 1: %r", delimiter)

        # Heurística: si primer valor parece ID de pieza (contiene letras y números), probablemente no hay encabezados
        first_row_values = lines[0].split(delimiter)
        has_headers = False
        
        if len(first_row_values) > 0:
            first_val = first_row_values[0].strip()
            # Si empieza con número+letra (tipo "1FSX", "2FDX") es probablemente una pieza, no encabezado
            if re.match(r"^[0-9]+[A-Za-z]", first_val):
                has_headers = False
                logger.debug("CSV detectado SIN encabezados (formato posicional, primer valor: %s)", first_val)
            else:
                has_headers = True
                logger.debug("CSV detectado CON encabezados (primer valor: %s)", first_val)

        # Intentar procesar como CSV sin encabezados primero (formato posicional).
        rows_count = 0
        no_header_lookup = {}
        for line in lines:
            if not line.strip():
                continue
            cols = line.split(delimiter)
            rows_count += 1

            if len(cols) < 10:
                logger.debug("Fila %d: columnas insuficientes (%d < 10), saltando", rows_count, len(cols))
                continue

            piece_id = cols[0].strip()
            if not piece_id:
                logger.debug("Fila %d: ID vacío, saltando", rows_count)
                continue

            piece_type = cols[1].strip() if len(cols) > 1 else None
            quantity_str = cols[3].strip() if len(cols) > 3 else "1"
            largo = parse_dimension(cols[5].strip()) if len(cols) > 5 else None
            ancho = parse_dimension(cols[6].strip()) if len(cols) > 6 else None
            espesor = parse_dimension(cols[7].strip()) if len(cols) > 7 else None
            color = cols[8].strip() if len(cols) > 8 else None
            veta_str = cols[9].strip() if len(cols) > 9 else "0"
            veta_map = {"0": "sin veta", "1": "a lo largo", "2": "a lo ancho"}
            grain_direction = veta_map.get(veta_str, veta_str)
            piece_name = cols[2].strip() if len(cols) > 2 else piece_id
            source_file = cols[10].strip() if len(cols) > 10 else None

            if not largo and not ancho:
                logger.debug("Fila %d: no dimension valida, saltando", rows_count)
                continue

            qty_num = parse_quantity(quantity_str)
            if piece_id in no_header_lookup:
                prev_qty = parse_quantity(no_header_lookup[piece_id].get("quantity"))
                no_header_lookup[piece_id]["quantity"] = str(prev_qty + qty_num)
                if not no_header_lookup[piece_id].get("source") and source_file:
                    no_header_lookup[piece_id]["source"] = source_file
                continue

            no_header_lookup[piece_id] = {
                "width": str(ancho) if ancho else None,
                "height": str(largo) if largo else None,
                "thickness": str(espesor) if espesor else None,
                "color": color if color else None,
                "grain_direction": grain_direction,
                "quantity": str(qty_num),
                "name": piece_name,
                "source": source_file,
                "piece_type": piece_type or None,
            }
            logger.debug("Fila %d: parseada sin encabezados %s", rows_count, piece_id)

        if no_header_lookup:
            lookup = no_header_lookup
            logger.debug("CSV sin encabezados detectado: %d piezas capturadas", len(lookup))
        else:
            # Procesamiento con encabezados (DictReader)
            with summary_file.open("r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                if not reader.fieldnames:
                    logger.warning("CSV sin encabezados detectados en %s", summary_file)
                    continue

                logger.debug("Encabezados detectados: %s", reader.fieldnames[:10])
                rows_count = 0
                normalized_keys = {normalize(k): k for k in reader.fieldnames if k}

                for row in reader:
                    rows_count += 1
                    row_norm = {normalize(k): (v.strip() if v is not None else "") for k, v in row.items() if k}

                    piece_id = ""
                    for candidate in possible_ids:
                        if candidate in row_norm and row_norm.get(candidate):
                            piece_id = row_norm[candidate]
                            break

                    if not piece_id:
                        for normalized_key, original_key in normalized_keys.items():
                            if normalized_key in possible_ids and row.get(original_key) and row.get(original_key).strip():
                                piece_id = row.get(original_key).strip()
                                break

                    if not piece_id:
                        continue

                    def find_value(candidates):
                        for candidate in candidates:
                            if candidate in row_norm and row_norm[candidate] != "":
                                return row_norm[candidate]
                        return None

                    width = find_value(possible_widths)
                    height = find_value(possible_heights)
                    color = find_value(possible_color)
                    grain_direction = find_value(possible_grain)
                    quantity = find_value(possible_quantity) or "1"

                    qty_num = parse_quantity(quantity)
                    if piece_id in lookup:
                        prev_qty = parse_quantity(lookup[piece_id].get("quantity"))
                        lookup[piece_id]["quantity"] = str(prev_qty + qty_num)
                        continue

                    lookup[piece_id] = {
                        "width": width,
                        "height": height,
                        "color": color,
                        "grain_direction": grain_direction,
                        "quantity": str(qty_num),
                        "source": row_norm.get("source") if "source" in row_norm else None,
                        "name": row_norm.get("name") if "name" in row_norm else piece_id,
                    }
                    logger.debug("Fila %d: pieza '%s' (w=%s, h=%s, qty=%s)", rows_count, piece_id, width, height, quantity)

                logger.debug("Total filas: %d, piezas capturadas: %d", rows_count, len(lookup))

        if lookup:
            logger.debug("✓ Cargado CSV de módulo %s -> %d piezas", module_dir.name, len(lookup))
            break

    if not lookup:
        logger.debug("✗ No se encontró resumen CSV válido para módulo %s", module_dir.name)
    return lookup


def scan_project(root_path: Path) -> List[ModuleData]:
    """Escanea la carpeta raíz del proyecto y procesa módulos y piezas.

    Cada subcarpeta es un módulo, y contiene archivos PGMX con piezas.
    También usa el CSV de resumen para asociar color, sentido de veta y dimensiones.
    """
    modules = []

    def parse_quantity(val) -> int:
        if val is None:
            return 1
        raw = str(val).strip().replace(",", ".")
        if not raw:
            return 1
        try:
            qty = int(float(raw))
            return qty if qty > 0 else 1
        except ValueError:
            return 1

    for module_dir in root_path.iterdir():
        if not module_dir.is_dir():
            continue

        metadata = load_module_summary(module_dir)
        module = ModuleData(name=module_dir.name, path=str(module_dir))

        piece_map = {}
        pgmx_files = [p for p in module_dir.rglob("*.pgmx") if p.is_file()]
        associated_map: Dict[str, str] = {}

        # Parsear únicamente archivos PGMX como programas de pieza.
        valid_extensions = {".pgmx"}
        for file_path in module_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in valid_extensions:
                continue
            logger.debug("Parseando archivo %s del módulo %s", file_path, module_dir.name)
            for piece in parse_cnc_file(file_path, metadata=metadata):
                if not piece.name and piece.id in metadata:
                    piece.name = metadata[piece.id].get("name") or piece.id
                
                # Preferir source del metadata (columna 10 del CSV) sobre la ruta descubierta
                original_source = piece.cnc_source
                if piece.id in metadata and metadata[piece.id].get("source"):
                    piece.cnc_source = metadata[piece.id].get("source")
                    logger.debug("Pieza %s: usando source del CSV '%s' (en lugar de '%s')", piece.id, piece.cnc_source, original_source)
                
                piece.module_name = module.name
                piece_map[piece.id] = piece

        # Si no se encontró cnc_source por pieza, intentar asociar por nombre de archivo
        for file_path in pgmx_files:
            file_name = file_path.stem.lower()
            for piece_id, data in metadata.items():
                if piece_id.lower() in file_name:
                    associated_map[piece_id] = str(file_path)

        # Agregar piezas del CSV que no estaban en los archivos de CNC para asegurar cobertura completa
        for piece_id, data in metadata.items():
            if piece_id not in piece_map:
                # Usar source del CSV, o intentar asociar por nombre de archivo, o dejar vacío
                cnc_source = data.get("source") or associated_map.get(piece_id)

                piece = Piece(
                    id=piece_id,
                    width=float(data.get("width")) if data.get("width") else 0.0,
                    height=float(data.get("height")) if data.get("height") else 0.0,
                    thickness=float(data.get("thickness")) if data.get("thickness") else None,
                    quantity=int(data.get("quantity", 1)) if data.get("quantity") else 1,
                    color=data.get("color"),
                    grain_direction=data.get("grain_direction") or data.get("sentido_veta") or data.get("veta"),
                    name=data.get("name") or piece_id,
                    module_name=module.name,
                    cnc_source=cnc_source,
                    piece_type=data.get("piece_type"),
                )
                piece_map[piece.id] = piece

        # Normalizar cantidad final con el CSV de módulo para evitar desajustes de conteo.
        for piece_id, piece in piece_map.items():
            if piece_id in metadata and metadata[piece_id].get("quantity") is not None:
                piece.quantity = parse_quantity(metadata[piece_id].get("quantity"))

        module.pieces = list(piece_map.values())
        modules.append(module)
        logger.debug("Módulo %s procesado: %d piezas", module.name, len(module.pieces))

    return modules


def _has_module_source_files(path: Path) -> bool:
    if not path.is_dir():
        return False
    if (path / "module_config.json").exists():
        return True
    for file_path in path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in MODULE_SOURCE_EXTENSIONS:
            return True
    return False


def _find_direct_module_dirs(parent_dir: Path) -> list[Path]:
    module_dirs: list[Path] = []
    for child in parent_dir.iterdir():
        if not child.is_dir():
            continue
        if _has_module_source_files(child):
            module_dirs.append(child)
    return module_dirs


def inspect_project_layout(root_path: Path) -> ProjectFolderLayout:
    """Clasifica carpetas de primer nivel en locales y módulos sueltos."""
    layout = ProjectFolderLayout()

    for child in root_path.iterdir():
        if not child.is_dir():
            continue

        direct_module_dirs = _find_direct_module_dirs(child)
        if direct_module_dirs:
            layout.locale_dirs.append(child)
            continue

        if _has_module_source_files(child):
            layout.loose_module_dirs.append(child)

    layout.locale_dirs.sort(key=lambda path: path.name.lower())
    layout.loose_module_dirs.sort(key=lambda path: path.name.lower())
    return layout


def _scan_module_from_locale(root_path: Path, locale_dir: Path, module_dir: Path) -> ModuleData:
    """Escanea un único módulo ubicado dentro de una carpeta de local."""
    modules = scan_project(module_dir.parent)
    for module in modules:
        if Path(module.path).resolve() != module_dir.resolve():
            continue
        module.locale_name = locale_dir.name
        module.relative_path = str(module_dir.relative_to(root_path)).replace("\\", "/")
        return module

    return ModuleData(
        name=module_dir.name,
        path=str(module_dir),
        locale_name=locale_dir.name,
        relative_path=str(module_dir.relative_to(root_path)).replace("\\", "/"),
        pieces=[],
    )


def scan_project_structure(root_path: Path) -> tuple[list[LocaleData], list[ModuleData]]:
    """Escanea una estructura proyecto/local/módulo ya normalizada."""
    layout = inspect_project_layout(root_path)
    locales: list[LocaleData] = []
    modules: list[ModuleData] = []

    for locale_dir in layout.locale_dirs:
        locale_modules: list[ModuleData] = []
        for module_dir in sorted(_find_direct_module_dirs(locale_dir), key=lambda path: path.name.lower()):
            locale_modules.append(_scan_module_from_locale(root_path, locale_dir, module_dir))

        locales.append(
            LocaleData(
                name=locale_dir.name,
                path=str(locale_dir.relative_to(root_path)).replace("\\", "/"),
                modules_count=len(locale_modules),
            )
        )
        modules.extend(locale_modules)

    return locales, modules
