"""Generación de resúmenes y exportación de datos a CSV/Excel."""

import pandas as pd
import re
from datetime import datetime
import json
import tempfile
from math import ceil
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Border, Font, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU

try:
    import cairosvg
except Exception:  # pragma: no cover - entorno sin dependencia opcional
    cairosvg = None

try:
    from PIL import Image as PILImage
except Exception:  # pragma: no cover - entorno sin dependencia opcional
    PILImage = None

try:
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover - entorno sin dependencia opcional
    QImage = None
    QPainter = None
    QSvgRenderer = None
    QApplication = None


_QT_APP_REF = None

from core.model import (
    Piece,
    Project,
    build_piece_observations_display,
    normalize_piece_grain_direction,
    normalize_piece_observations,
)


def _excel_image_embedding_available() -> bool:
    """openpyxl requiere Pillow incluso para insertar PNG ya existentes."""

    return PILImage is not None


def export_summary(project: Project, output_csv: Path):
    """Exporta un resumen de piezas por módulo a un archivo CSV.
    
    Excluye piezas con espesor = 0.
    Módulos automáticos (escaneados) se muestran primero, luego los manuales.
    Columnas en orden: module; piece_id; piece_name; quantity; height; width; thickness; color; grain_direction; source
    """
    # Ordenar módulos: primero automáticos (is_manual=False), luego manuales (is_manual=True)
    modules_sorted = sorted(project.modules, key=lambda m: m.is_manual)
    
    rows = []
    for module in modules_sorted:
        for piece in module.pieces:
            # Filtrar piezas con espesor 0
            if piece.thickness == 0 or piece.thickness is None:
                continue
            rows.append({
                "module": module.name,
                "piece_id": piece.id,
                "piece_name": piece.name or piece.id,
                "quantity": piece.quantity,
                "height": piece.height,
                "width": piece.width,
                "thickness": piece.thickness,
                "color": piece.color,
                "grain_direction": normalize_piece_grain_direction(piece.grain_direction),
                "source": piece.cnc_source,
            })
    df = pd.DataFrame(rows, columns=["module", "piece_id", "piece_name", "quantity", "height", "width", "thickness", "color", "grain_direction", "source"])
    df.to_csv(output_csv, index=False, encoding="utf-8", sep=";")
    return df


def _is_valid_thickness(value) -> bool:
    if value is None:
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _safe_int(value, default=1) -> int:
    try:
        parsed = int(float(value))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _confirmed_dimension(value):
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return int(parsed) if parsed.is_integer() else round(parsed, 2)


def _is_positive_dimension(value) -> bool:
    parsed = _safe_float(value)
    return parsed is not None and parsed > 0


def _piece_from_sheet_row(module_name: str, piece_row: dict) -> Piece:
    thickness = _safe_float(piece_row.get("thickness"))
    quantity = _safe_int(piece_row.get("quantity"), default=1)
    return Piece(
        id=str(piece_row.get("id") or piece_row.get("name") or "pieza").strip(),
        name=str(piece_row.get("name") or piece_row.get("id") or "pieza").strip(),
        quantity=quantity,
        width=_safe_float(piece_row.get("width")) or 0.0,
        height=_safe_float(piece_row.get("height")) or 0.0,
        thickness=thickness,
        color=piece_row.get("color"),
        grain_direction=normalize_piece_grain_direction(piece_row.get("grain_direction")),
        module_name=module_name,
        cnc_source=str(piece_row.get("source") or "").strip() or None,
        f6_source=str(piece_row.get("f6_source") or "").strip() or None,
        piece_type=piece_row.get("piece_type"),
        program_width=_safe_float(piece_row.get("program_width")),
        program_height=_safe_float(piece_row.get("program_height")),
        program_thickness=_safe_float(piece_row.get("program_thickness")),
    )


def _px_to_excel_width(px: int) -> float:
    """Convertir px a unidad de ancho de columna de Excel (aprox. Calibri 11)."""
    if px <= 12:
        return 1.0
    return round((px - 5) / 7, 2)


def _excel_width_for_text_values(
    values,
    *,
    minimum_width: float,
    maximum_width: float,
    padding_chars: float = 2.0,
) -> float:
    longest_line_length = 0
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        longest_line_length = max(
            longest_line_length,
            max(len(line.strip()) for line in text.splitlines() if line.strip()) if text.splitlines() else len(text),
        )

    if longest_line_length <= 0:
        return minimum_width

    estimated_width = round((longest_line_length * 0.92) + padding_chars, 2)
    return max(minimum_width, min(maximum_width, estimated_width))


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return cleaned.strip("._") or "pieza"


def _add_text_to_png(png_path: Path, text: str, font_size: int = 10) -> None:
    """Agrega texto centrado en la imagen PNG (sobre la imagen original)."""
    if PILImage is None:
        return
    
    try:
        from PIL import ImageDraw, ImageFont
        
        # Abrir imagen existente
        img = PILImage.open(png_path).convert("RGBA")
        img_w, img_h = img.size
        
        # Crear capa de texto semi-transparente
        txt_layer = PILImage.new("RGBA", (img_w, img_h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Intentar usar una fuente específica, si no está disponible usar la default
        try:
            font = ImageFont.truetype("calibri.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
        
        # Calcular dimensiones del texto
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Posición centrada en la imagen
        text_x = max(0, (img_w - text_width) // 2)
        text_y = max(0, (img_h - text_height) // 2)
        
        # Dibujar rectángulo de fondo semi-transparente
        padding = 5
        bg_left = max(0, text_x - padding)
        bg_top = max(0, text_y - padding)
        bg_right = min(img_w, text_x + text_width + padding)
        bg_bottom = min(img_h, text_y + text_height + padding)
        draw.rectangle(
            [(bg_left, bg_top), (bg_right, bg_bottom)],
            fill=(255, 255, 255, 200)  # Fondo blanco semi-transparente
        )
        
        # Dibujar texto en gris oscuro
        draw.text((text_x, text_y), text, fill=(50, 50, 50, 255), font=font)
        
        # Combinar capas
        img_with_text = PILImage.alpha_composite(img, txt_layer)
        
        # Guardar imagen modificada (convertir de vuelta a RGB para PNG)
        img_rgb = PILImage.new("RGB", img_with_text.size, (255, 255, 255))
        img_rgb.paste(img_with_text, mask=img_with_text.split()[3])
        img_rgb.save(png_path, format="PNG")
    except Exception:
        pass  # Si hay error, dejar la imagen como está


def _svg_to_png_for_excel(svg_path: Path, png_path: Path, max_width_px: int = 200) -> tuple[int, int] | None:
    """Convierte SVG a PNG para Excel y limita ancho sin perder aspecto."""

    if cairosvg is not None and PILImage is not None:
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
        with PILImage.open(png_path) as image:
            width_px, height_px = image.size
            if width_px <= 0 or height_px <= 0:
                return None

            if width_px > max_width_px:
                ratio = max_width_px / float(width_px)
                resized = image.resize((max_width_px, max(1, int(round(height_px * ratio)))))
                resized.save(png_path, format="PNG")
                width_px, height_px = resized.size

        return width_px, height_px

    # Fallback para entornos Windows donde CairoSVG puede no cargar librerías nativas.
    if QSvgRenderer is None or QImage is None or QPainter is None:
        return None

    # QSvgRenderer renderiza de forma estable cuando existe una app Qt activa.
    global _QT_APP_REF
    if QApplication is not None and QApplication.instance() is None:
        _QT_APP_REF = QApplication([])

    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        return None

    default_size = renderer.defaultSize()
    width_px = int(default_size.width()) if default_size.width() > 0 else max_width_px
    height_px = int(default_size.height()) if default_size.height() > 0 else max_width_px
    if width_px <= 0 or height_px <= 0:
        return None

    if width_px > max_width_px:
        ratio = max_width_px / float(width_px)
        width_px = max_width_px
        height_px = max(1, int(round(height_px * ratio)))

    image = QImage(width_px, height_px, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    if not image.save(str(png_path), "PNG"):
        return None

    return width_px, height_px


def _apply_outer_frame(ws, start_row: int, end_row: int, start_col: int = 1, end_col: int = 7):
    """Dibuja un marco exterior alrededor de un bloque rectangular."""

    if end_row < start_row:
        return

    side = Side(style="medium", color="FF808080")
    for row in range(start_row, end_row + 1):
        for col in range(start_col, end_col + 1):
            cell = ws.cell(row=row, column=col)
            left = side if col == start_col else cell.border.left
            right = side if col == end_col else cell.border.right
            top = side if row == start_row else cell.border.top
            bottom = side if row == end_row else cell.border.bottom
            cell.border = Border(left=left, right=right, top=top, bottom=bottom)


def _extract_named_dimensions(module_name: str):
    """Extraer dimensiones desde nombre de módulo respetando convención ...-X-Z."""
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


def _derive_module_dimensions(module_name: str, pieces: list[dict]):
    """Inferir X, Y, Z según: ancho total, altura total y profundidad sin frente."""
    x_named, z_named = _extract_named_dimensions(module_name)

    widths = []
    heights = []
    thicknesses = []
    lateral_heights = []
    span_heights = []

    for piece in pieces:
        piece_name = str(piece.get("name") or piece.get("id") or "").lower()
        width = _safe_float(piece.get("width"))
        height = _safe_float(piece.get("height"))
        thickness = _safe_float(piece.get("thickness"))

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

    # Z: profundidad sin frente/tapas. En la mayoría de casos coincide con el mayor ancho de pieza.
    if z_named is not None:
        z_val = round(z_named, 2)
    elif widths:
        z_val = round(max(widths), 2)
    else:
        z_val = None

    # X: ancho total. Se prioriza nomenclatura del módulo (convención ...-X-Z).
    if x_named is not None:
        x_val = round(x_named, 2)
    else:
        # Fallback geométrico: usar piezas de "travesía" (fondo/estante/puerta/faja/tapa/frente).
        x_base = max(span_heights) if span_heights else (max(heights) if heights else None)
        x_val = round(x_base, 2) if x_base is not None else None

    # Y: altura total. Lateral + espesor superior/inferior cuando se puede inferir.
    if lateral_heights:
        y_base = max(lateral_heights)
    elif heights:
        y_base = max(heights)
    else:
        y_base = None

    y_val = round(y_base + max_thickness, 2) if y_base is not None else None

    # Normalizar enteros visuales (150.0 -> 150)
    def _compact_number(n):
        if n is None:
            return None
        return int(n) if abs(n - int(n)) < 1e-9 else n

    return _compact_number(x_val), _compact_number(y_val), _compact_number(z_val)


def export_production_sheet(project: Project, output_xlsx: Path):
    """Generar planilla Excel de producción sin plantilla, desde datos del sistema."""
    from core.pgmx_processing import get_pgmx_program_dimension_notes

    wb = Workbook()
    ws = wb.active
    ws.title = "Planilla"
    program_dimensions_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
    excel_images_supported = _excel_image_embedding_available()
    observations_min_width = _px_to_excel_width(120)
    observations_max_width = _px_to_excel_width(280)
    observations_font = Font(name="Calibri", size=9, bold=True, color="FFFF0000")
    observations_values: list[str] = []

    # Configurar formato de impresión
    # Tamaño A4 (paperSize=9)
    ws.page_setup.paperSize = 9
    ws.page_setup.orientation = "portrait"
    
    # Escala: Ajustar al ancho de todas las columnas (ancho = 1)
    ws.page_setup.fitToHeight = 0  # Sin límite de altura
    ws.page_setup.fitToWidth = 1   # Ajustar a 1 página de ancho
    ws.print_options.horizontalCentered = True
    
    # Márgenes (en pulgadas): 1.5cm superior, 0.5cm otros
    ws.page_margins.left = 0.19685    # 0.5 cm en pulgadas
    ws.page_margins.right = 0.19685   # 0.5 cm en pulgadas
    ws.page_margins.top = 0.59055     # 1.5 cm en pulgadas
    ws.page_margins.bottom = 0.19685  # 0.5 cm en pulgadas
    ws.page_margins.header = 0.0
    ws.page_margins.footer = 0.0

    # Anchos de columnas solicitados (en px), convertidos a unidad Excel.
    ws.column_dimensions["A"].width = _px_to_excel_width(200)
    ws.column_dimensions["B"].width = _px_to_excel_width(50)
    ws.column_dimensions["C"].width = _px_to_excel_width(70)
    ws.column_dimensions["D"].width = _px_to_excel_width(70)
    ws.column_dimensions["E"].width = _px_to_excel_width(70)
    ws.column_dimensions["F"].width = _px_to_excel_width(70)
    ws.column_dimensions["G"].width = _px_to_excel_width(120)

    col_widths_px = [200, 50, 70, 70, 70, 70, 120]
    block_width_px = sum(col_widths_px)

    def marker_for_x(row_1_based: int, x_offset_px: float) -> AnchorMarker:
        """Convierte un offset X (px) dentro de A:G a (columna, offset local)."""

        x = max(0.0, min(float(x_offset_px), float(block_width_px - 1)))
        remaining = x
        col_idx = 0
        for idx, width in enumerate(col_widths_px):
            if remaining < width or idx == len(col_widths_px) - 1:
                col_idx = idx
                break
            remaining -= width

        return AnchorMarker(
            col=col_idx,
            row=row_1_based - 1,
            colOff=pixels_to_EMU(int(round(remaining))),
            rowOff=0,
        )

    # Encabezado principal
    ws["A1"] = project.name or "Proyecto"
    ws["A1"].font = Font(name="Calibri", size=50, bold=False)

    ws["A2"] = f"Cliente: {project.client or '-'}"
    ws["A2"].font = Font(name="Calibri", size=14, bold=True)

    # Local es opcional
    ws["A4"] = project.local or ""
    ws["A4"].font = Font(name="Calibri", size=24, bold=True)

    # Alturas base de encabezado.
    ws.row_dimensions[1].height = 64.5
    ws.row_dimensions[2].height = 18.75
    ws.row_dimensions[4].height = 31.5

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)

        current_row = 6
        for module in project.modules:
            config_path = Path(module.path) / "module_config.json"
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
                pieces = [piece for piece in raw_pieces if _is_valid_thickness(piece.get("thickness"))]
                from core.model import PIECE_TYPE_ORDER as _PTO
                _type_rank = {t: i for i, t in enumerate(_PTO)}
                pieces.sort(key=lambda p: _type_rank.get(p.get("piece_type") or "", len(_PTO)))
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
                    if _is_valid_thickness(piece.thickness)
                ]

            piece_objects = [_piece_from_sheet_row(module.name, piece) for piece in pieces]
            program_notes = get_pgmx_program_dimension_notes(
                project,
                piece_objects,
                Path(module.path),
                cache=program_dimensions_cache,
            )
            for piece, program_note in zip(pieces, program_notes):
                piece["program_dimension_note"] = program_note
                piece["observations"] = normalize_piece_observations(piece.get("observations"))

            x_inferred, y_inferred, z_inferred = _derive_module_dimensions(module.name, pieces)
            x_val = _confirmed_dimension(module_settings.get("x")) or x_inferred
            y_val = _confirmed_dimension(module_settings.get("y")) or y_inferred
            z_val = _confirmed_dimension(module_settings.get("z")) or z_inferred

            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
            module_title_cell = ws.cell(row=current_row, column=1, value=module.name)
            module_title_cell.font = Font(name="Calibri", size=14, bold=True)
            ws.row_dimensions[current_row].height = 18.75
            has_dimensions = all([
                _is_positive_dimension(x_val),
                _is_positive_dimension(y_val),
                _is_positive_dimension(z_val),
            ])

            dim_font = Font(name="Calibri", size=12, bold=True)
            if has_dimensions:
                dim_x_cell = ws.cell(row=current_row, column=4, value=f"X: {x_val}")
                dim_y_cell = ws.cell(row=current_row, column=5, value=f"Y: {y_val}")
                dim_z_cell = ws.cell(row=current_row, column=6, value=f"Z: {z_val}")
                dim_x_cell.font = dim_font
                dim_y_cell.font = dim_font
                dim_z_cell.font = dim_font
            else:
                ws.cell(row=current_row, column=4, value=None)
                ws.cell(row=current_row, column=5, value=None)
                ws.cell(row=current_row, column=6, value=None)

            detail_row = current_row + 1
            herrajes_value = str(module_settings.get("herrajes_y_accesorios") or "").strip()
            if herrajes_value:
                herrajes_cell = ws.cell(row=detail_row, column=1, value=herrajes_value)
                herrajes_cell.font = Font(name="Calibri", size=11, bold=True, color="FF7030A0")
                detail_row += 1

            guias_value = str(module_settings.get("guias_y_bisagras") or "").strip()
            if guias_value:
                guias_cell = ws.cell(row=detail_row, column=1, value=guias_value)
                guias_cell.font = Font(name="Calibri", size=11, bold=True, color="FF0070C0")
                detail_row += 1

            detalles_value = str(module_settings.get("detalles_de_obra") or "").strip()
            if detalles_value:
                detalles_cell = ws.cell(row=detail_row, column=1, value=detalles_value)
                detalles_cell.font = Font(name="Calibri", size=11, bold=True, color="FF548235")
                detail_row += 1

            # Leave exactly one blank row after the last detail/settings row.
            images_start_row = detail_row + 1
            images_end_row = images_start_row - 1  # No images initially

            # Insert drawings immediately after details: up to 3 per row, max height 4cm (150px).
            prepared_images: list[tuple[Path, int, int, str]] = []
            if excel_images_supported:
                for idx, piece in enumerate(pieces):
                    if not bool(piece.get("include_in_sheet", False)):
                        continue

                    piece_display_name = str(piece.get("name") or piece.get("id") or "pieza").strip()
                    piece_slug = _sanitize_filename(piece_display_name)
                    svg_path = Path(module.path) / f"{piece_slug}.svg"
                    if not svg_path.is_file():
                        continue

                    # Max 4cm height (150px at 96 DPI)
                    png_path = temp_dir / f"{_sanitize_filename(module.name)}_{idx}_{piece_slug}.png"
                    size = _svg_to_png_for_excel(svg_path, png_path, max_width_px=150)
                    if not size:
                        continue

                    src_w, src_h = size
                    if src_w <= 0 or src_h <= 0:
                        continue

                    # Calcular altura manteniendo aspectratio con máximo de 150px
                    if src_h > 150:
                        ratio = 150.0 / float(src_h)
                        target_w = int(round(src_w * ratio))
                        target_h = 150
                    else:
                        target_w = src_w
                        target_h = src_h

                    # Agregar nombre de la pieza a la imagen (texto centrado, no cambia dimensiones)
                    _add_text_to_png(png_path, piece_display_name, font_size=10)

                    prepared_images.append((png_path, target_w, target_h, piece_display_name))

            # Insertar imágenes: 3 por fila
            if prepared_images:
                drawing_anchor_row = images_start_row
                for chunk_start in range(0, len(prepared_images), 3):
                    chunk = prepared_images[chunk_start:chunk_start + 3]
                    count = len(chunk)
                    if count == 0:
                        continue

                    # Espaciado para 3 imágenes distribuidas en las 7 columnas:
                    # Imagen 1: columnas A:B (ancho 250px)
                    # Imagen 2: columnas C:D (ancho 140px)
                    # Imagen 3: columnas E:F:G (ancho 260px)
                    block_configs = [
                        {"start_col": 0, "end_col": 2, "width": sum(col_widths_px[:2])},
                        {"start_col": 2, "end_col": 4, "width": sum(col_widths_px[2:4])},
                        {"start_col": 4, "end_col": 7, "width": sum(col_widths_px[4:])},
                    ]
                    
                    max_h = 0
                    for idx_in_row, (png_path, img_w, img_h, piece_name) in enumerate(chunk):
                        if idx_in_row >= len(block_configs):
                            break
                            
                        config = block_configs[idx_in_row]
                        block_w = config["width"]
                        col_offset_start = sum(col_widths_px[:config["start_col"]])
                        
                        # Centrar imagen en su bloque asignado
                        centered_x = col_offset_start + max(0.0, (block_w - img_w) / 2.0)
                        
                        try:
                            image = XLImage(str(png_path))
                        except Exception:
                            continue
                        image.width = int(img_w)
                        image.height = int(img_h)

                        x_offset_px = int(round(centered_x))
                        image.anchor = OneCellAnchor(
                            _from=marker_for_x(drawing_anchor_row, x_offset_px),
                            ext=XDRPositiveSize2D(
                                pixels_to_EMU(int(image.width)),
                                pixels_to_EMU(int(image.height)),
                            ),
                        )
                        ws.add_image(image)
                        max_h = max(max_h, img_h)

                    ws.row_dimensions[drawing_anchor_row].height = max(
                        ws.row_dimensions[drawing_anchor_row].height or 15.0,
                        round(max_h * 0.75, 2),
                    )
                    images_end_row = drawing_anchor_row
                    drawing_anchor_row += 1

            # Piezas empiezan después de las imágenes
            pieces_start = images_end_row + 2 if prepared_images else images_start_row

            # Separar piezas en dos grupos: con piece_type y sin piece_type
            pieces_with_type = [p for p in pieces if p.get("piece_type")]
            pieces_without_type = [p for p in pieces if not p.get("piece_type")]

            # Encontrar índice de la última pieza tipo "H"
            last_h_index = None
            for i, piece in enumerate(pieces_with_type):
                if (piece.get("piece_type") or "").strip().upper() == "H":
                    last_h_index = i

            extra_rows = 0  # blank rows inserted so far (shifts subsequent offsets)
            
            # Procesar piezas con piece_type
            for offset, piece in enumerate(pieces_with_type):
                row = pieces_start + offset + extra_rows
                ws.cell(row=row, column=1, value=piece.get("name") or piece.get("id") or "")
                ws.cell(row=row, column=2, value=_safe_int(piece.get("quantity"), default=1))
                ws.cell(row=row, column=3, value=_safe_float(piece.get("width")))
                ws.cell(row=row, column=4, value=_safe_float(piece.get("height")))
                ws.cell(row=row, column=5, value=_safe_float(piece.get("thickness")))
                ws.cell(row=row, column=6, value=piece.get("color") or "")
                note_value = build_piece_observations_display(
                    piece.get("observations"),
                    piece.get("program_dimension_note"),
                )
                col_g_cell = ws.cell(row=row, column=7, value=note_value)
                col_g_cell.font = observations_font
                observations_values.append(str(note_value))

                # Insertar fila vacía después de la última pieza tipo "H" si hay más piezas
                if offset == last_h_index and (pieces_without_type or offset < len(pieces_with_type) - 1):
                    extra_rows += 1

            # Agregar fila vacía si hay piezas sin piece_type
            if pieces_without_type and pieces_with_type:
                extra_rows += 1
            
            # Procesar piezas sin piece_type (agregadas manualmente)
            for offset, piece in enumerate(pieces_without_type):
                row = pieces_start + len(pieces_with_type) + offset + extra_rows
                ws.cell(row=row, column=1, value=piece.get("name") or piece.get("id") or "")
                ws.cell(row=row, column=2, value=_safe_int(piece.get("quantity"), default=1))
                ws.cell(row=row, column=3, value=_safe_float(piece.get("width")))
                ws.cell(row=row, column=4, value=_safe_float(piece.get("height")))
                ws.cell(row=row, column=5, value=_safe_float(piece.get("thickness")))
                ws.cell(row=row, column=6, value=piece.get("color") or "")
                note_value = build_piece_observations_display(
                    piece.get("observations"),
                    piece.get("program_dimension_note"),
                )
                col_g_cell = ws.cell(row=row, column=7, value=note_value)
                col_g_cell.font = observations_font
                observations_values.append(str(note_value))

            module_last_piece_row = pieces_start + len(pieces_with_type) + len(pieces_without_type) + extra_rows - 1
            content_end_row = max(module_last_piece_row, images_end_row)
            _apply_outer_frame(ws, current_row, content_end_row, start_col=1, end_col=7)

            # Leave two blank rows between framed module blocks.
            current_row = content_end_row + 3

        ws.column_dimensions["G"].width = _excel_width_for_text_values(
            observations_values,
            minimum_width=observations_min_width,
            maximum_width=observations_max_width,
        )

        output_xlsx.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_xlsx)
    return output_xlsx
