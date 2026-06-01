"""Production sheet Excel export and compatibility facade."""

import tempfile
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Border, Font, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU

from core.model import (
    Project,
    build_piece_observations_display,
)
from core.production_sheet_pdf import export_production_sheet_pdf
from core.production_sheet_data import (
    effective_piece_quantity as _effective_piece_quantity,
    is_positive_dimension as _is_positive_dimension,
    load_module_sheet_data as _load_module_sheet_data,
    safe_float as _safe_float,
    safe_int as _safe_int,
)
from core.production_sheet_images import (
    prepare_module_sheet_images as _prepare_module_sheet_images,
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


def export_production_sheet(project: Project, output_xlsx: Path):
    """Generar planilla Excel de producción sin plantilla, desde datos del sistema."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Planilla"
    program_dimensions_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
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
            module_data = _load_module_sheet_data(project, module, program_dimensions_cache)
            module_quantity = _safe_int(getattr(module, "quantity", None), default=1)
            config_data = module_data["config_data"]
            module_settings = module_data["module_settings"]
            pieces = module_data["pieces"]
            x_val, y_val, z_val = module_data["dimensions"]

            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
            module_title_cell = ws.cell(row=current_row, column=1, value=module.name)
            module_title_cell.font = Font(name="Calibri", size=14, bold=True)
            ws.row_dimensions[current_row].height = 18.75
            module_observation = ""
            if module_quantity > 1:
                module_observation = f"{module_quantity} módulos."
                module_observation_cell = ws.cell(row=current_row, column=7, value=module_observation)
                module_observation_cell.font = observations_font
                observations_values.append(module_observation)
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
            prepared_images = _prepare_module_sheet_images(
                project,
                module,
                config_data,
                pieces,
                temp_dir,
                max_width_px=150,
            )

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
                ws.cell(
                    row=row,
                    column=2,
                    value=_effective_piece_quantity(piece.get("quantity"), module_quantity),
                )
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
                ws.cell(
                    row=row,
                    column=2,
                    value=_effective_piece_quantity(piece.get("quantity"), module_quantity),
                )
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
