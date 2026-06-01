"""Production sheet exports for Excel and interactive PDF."""

import io
import tempfile
from math import ceil
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Border, Font, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU

from core.production_pdf import (
    PDF_CHECKBOX_GAP,
    PDF_CHECKBOX_MARGIN_X,
    PDF_CHECKBOX_MARGIN_Y,
    PDF_CHECKBOX_SIZE,
    PDF_EXPORT_DPI,
    PDF_HEADER_HEIGHT,
    PDF_MARGIN_BOTTOM,
    PDF_MARGIN_TOP,
    PDF_MARGIN_X,
    PDF_PAGE_HEIGHT,
    PDF_PAGE_WIDTH,
    pdf_checkbox_appearance,
    pdf_checkbox_changed_javascript,
    pdf_checkbox_rect,
    pdf_hide_popup_javascript,
    pdf_literal_string,
    pdf_number,
    pdf_popup_appearance,
    pdf_popup_rect_from_link,
    pdf_rect_from_pixels,
    pdf_show_popup_javascript,
    pdf_stream_object,
)

from core.model import (
    Project,
    build_piece_observations_display,
)
from core.production_sheet_data import (
    effective_piece_quantity as _effective_piece_quantity,
    is_positive_dimension as _is_positive_dimension,
    load_module_sheet_data as _load_module_sheet_data,
    safe_float as _safe_float,
    safe_int as _safe_int,
)
from core.production_sheet_images import (
    pil_image_available as _pil_image_available,
    popup_image_jpeg_data as _popup_image_jpeg_data,
    prepare_module_sheet_images as _prepare_module_sheet_images,
    prepare_pdf_piece_popups as _prepare_pdf_piece_popups,
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



def _load_pdf_font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    font_names = (
        ("arialbd.ttf", "arial.ttf")
        if bold
        else ("arial.ttf", "calibri.ttf", "DejaVuSans.ttf")
    )
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_width(draw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), str(text or ""), font=font)
    return int(bbox[2] - bbox[0])


def _fit_text(draw, text, font, max_width: int) -> str:
    value = str(text or "")
    if _text_width(draw, value, font) <= max_width:
        return value
    ellipsis = "..."
    while value and _text_width(draw, f"{value}{ellipsis}", font) > max_width:
        value = value[:-1]
    return f"{value}{ellipsis}" if value else ellipsis


def _draw_fit_text(draw, xy: tuple[int, int], text, font, fill, max_width: int) -> None:
    draw.text(xy, _fit_text(draw, text, font, max_width), font=font, fill=fill)


def _pdf_column_metrics(content_width: int) -> tuple[list[int], list[int]]:
    base_widths = [110, 175, 45, 65, 65, 65, 95, 130]
    base_total = sum(base_widths)
    widths = [max(1, int(round(width * content_width / base_total))) for width in base_widths]
    widths[-1] += content_width - sum(widths)
    starts = [0]
    for width in widths[:-1]:
        starts.append(starts[-1] + width)
    return widths, starts


def _pdf_piece_rows(pieces: list[dict]) -> list[dict | None]:
    pieces_with_type = [piece for piece in pieces if piece.get("piece_type")]
    pieces_without_type = [piece for piece in pieces if not piece.get("piece_type")]
    rows: list[dict | None] = []
    last_h_index = None
    for index, piece in enumerate(pieces_with_type):
        if (piece.get("piece_type") or "").strip().upper() == "H":
            last_h_index = index

    for index, piece in enumerate(pieces_with_type):
        rows.append(piece)
        if index == last_h_index and (pieces_without_type or index < len(pieces_with_type) - 1):
            rows.append(None)

    if pieces_without_type and pieces_with_type:
        rows.append(None)
    rows.extend(pieces_without_type)
    return rows


def _pdf_checkboxes_per_line(column_width: int) -> int:
    available_width = max(1, column_width - (PDF_CHECKBOX_MARGIN_X * 2))
    return max(1, (available_width + PDF_CHECKBOX_GAP) // (PDF_CHECKBOX_SIZE + PDF_CHECKBOX_GAP))


def _pdf_piece_row_height(quantity: int, checkbox_column_width: int, base_row_height: int) -> int:
    boxes_per_line = _pdf_checkboxes_per_line(checkbox_column_width)
    lines = max(1, ceil(max(1, quantity) / boxes_per_line))
    checkbox_height = (
        PDF_CHECKBOX_MARGIN_Y * 2
        + (lines * PDF_CHECKBOX_SIZE)
        + ((lines - 1) * PDF_CHECKBOX_GAP)
    )
    return max(base_row_height, checkbox_height)


def _draw_pdf_checkboxes(
    draw,
    x: int,
    y: int,
    column_width: int,
    row_height: int,
    quantity: int,
) -> list[tuple[int, int]]:
    boxes_per_line = _pdf_checkboxes_per_line(column_width)
    quantity = max(1, int(quantity))
    positions: list[tuple[int, int]] = []
    for index in range(quantity):
        line_index = index // boxes_per_line
        col_index = index % boxes_per_line
        box_x = x + PDF_CHECKBOX_MARGIN_X + col_index * (PDF_CHECKBOX_SIZE + PDF_CHECKBOX_GAP)
        box_y = y + PDF_CHECKBOX_MARGIN_Y + line_index * (PDF_CHECKBOX_SIZE + PDF_CHECKBOX_GAP)
        if box_y + PDF_CHECKBOX_SIZE > y + row_height - 2:
            break
        positions.append((box_x, box_y))
        draw.rectangle(
            (box_x, box_y, box_x + PDF_CHECKBOX_SIZE, box_y + PDF_CHECKBOX_SIZE),
            outline="black",
            width=2,
        )
    return positions


def _render_module_pdf_block(
    project: Project,
    module,
    module_data: dict,
) -> tuple[object, list[tuple[int, int]], list[dict]]:
    from PIL import Image, ImageDraw

    content_width = PDF_PAGE_WIDTH - (PDF_MARGIN_X * 2)
    col_widths, col_starts = _pdf_column_metrics(content_width)
    title_h = 38
    detail_h = 28
    row_h = 30
    gap_h = 18
    module_quantity = _safe_int(getattr(module, "quantity", None), default=1)
    module_settings = module_data["module_settings"]
    pieces = module_data["pieces"]
    x_val, y_val, z_val = module_data["dimensions"]

    detail_values = [
        ("herrajes_y_accesorios", (112, 48, 160)),
        ("guias_y_bisagras", (0, 112, 192)),
        ("detalles_de_obra", (84, 130, 53)),
    ]
    visible_details = [
        (str(module_settings.get(key) or "").strip(), color)
        for key, color in detail_values
        if str(module_settings.get(key) or "").strip()
    ]
    piece_rows = _pdf_piece_rows(pieces)
    piece_row_heights = [
        row_h if piece is None else _pdf_piece_row_height(
            _effective_piece_quantity(piece.get("quantity"), module_quantity),
            col_widths[0],
            row_h,
        )
        for piece in piece_rows
    ]
    block_height = (
        title_h
        + (len(visible_details) * detail_h)
        + gap_h
        + sum(piece_row_heights)
        + 10
    )
    block_height = max(block_height, title_h + 10)

    image = Image.new("RGB", (content_width, block_height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _load_pdf_font(24, bold=True)
    dim_font = _load_pdf_font(20, bold=True)
    detail_font = _load_pdf_font(18, bold=True)
    row_font = _load_pdf_font(17)
    note_font = _load_pdf_font(15, bold=True)
    checkbox_positions: list[tuple[int, int]] = []
    piece_links: list[dict] = []

    y = 4
    _draw_fit_text(draw, (6, y + 5), module.name, title_font, "black", sum(col_widths[:3]) - 12)
    if all(_is_positive_dimension(value) for value in (x_val, y_val, z_val)):
        for label, value, col_index in (("X", x_val, 3), ("Y", y_val, 4), ("Z", z_val, 5)):
            _draw_fit_text(
                draw,
                (col_starts[col_index] + 4, y + 7),
                f"{label}: {value}",
                dim_font,
                "black",
                col_widths[col_index] - 8,
            )
    if module_quantity > 1:
        _draw_fit_text(
            draw,
            (col_starts[7] + 4, y + 9),
            f"{module_quantity} modulos.",
            note_font,
            (255, 0, 0),
            col_widths[7] - 8,
        )
    y += title_h

    for text, color in visible_details:
        _draw_fit_text(draw, (6, y + 4), text, detail_font, color, content_width - 12)
        y += detail_h

    y += gap_h

    for piece, current_row_h in zip(piece_rows, piece_row_heights):
        if piece is None:
            y += current_row_h
            continue
        effective_quantity = _effective_piece_quantity(piece.get("quantity"), module_quantity)
        checkbox_positions.extend(
            _draw_pdf_checkboxes(draw, col_starts[0], y, col_widths[0], current_row_h, effective_quantity)
        )
        popup_key = str(piece.get("_pdf_popup_key") or "").strip()
        note_value = build_piece_observations_display(
            piece.get("observations"),
            piece.get("program_dimension_note"),
        )
        values = [
            piece.get("name") or piece.get("id") or "",
            effective_quantity,
            _safe_float(piece.get("width")),
            _safe_float(piece.get("height")),
            _safe_float(piece.get("thickness")),
            piece.get("color") or "",
            note_value,
        ]
        for col_index, value in enumerate(values):
            target_col = col_index + 1
            font = note_font if target_col == 7 else row_font
            fill = (0, 82, 160) if target_col == 1 and popup_key else ((255, 0, 0) if target_col == 7 else "black")
            text_x = col_starts[target_col] + 4
            text_y = y + 6
            _draw_fit_text(
                draw,
                (text_x, text_y),
                "" if value is None else value,
                font,
                fill,
                col_widths[target_col] - 8,
            )
            if target_col == 1 and popup_key:
                fitted_name = _fit_text(draw, value, font, col_widths[target_col] - 8)
                underline_y = text_y + 20
                underline_w = min(_text_width(draw, fitted_name, font), col_widths[target_col] - 8)
                draw.line((text_x, underline_y, text_x + underline_w, underline_y), fill=(0, 82, 160), width=1)
                piece_links.append({
                    "key": popup_key,
                    "rect": (
                        col_starts[target_col] + 2,
                        y + 2,
                        col_widths[target_col] - 4,
                        min(current_row_h - 4, row_h),
                    ),
                })
        y += current_row_h

    draw.rectangle((0, 0, content_width - 1, min(block_height - 1, y + 4)), outline=(128, 128, 128), width=3)
    return image, checkbox_positions, piece_links


def _draw_production_pdf_header(draw, project: Project) -> int:
    title_font = _load_pdf_font(56)
    client_font = _load_pdf_font(24, bold=True)
    local_font = _load_pdf_font(36, bold=True)
    content_width = PDF_PAGE_WIDTH - (PDF_MARGIN_X * 2)
    x = PDF_MARGIN_X
    y = PDF_MARGIN_TOP
    _draw_fit_text(draw, (x, y), project.name or "Proyecto", title_font, "black", content_width)
    y += 70
    _draw_fit_text(draw, (x, y), f"Cliente: {project.client or '-'}", client_font, "black", content_width)
    y += 42
    _draw_fit_text(draw, (x, y), project.local or "", local_font, "black", content_width)
    return PDF_MARGIN_TOP + PDF_HEADER_HEIGHT


def _write_interactive_pdf_page(
    page,
    output_pdf: Path,
    checkbox_positions: list[tuple[int, int]],
    popup_images: dict[str, dict],
    piece_links: list[dict],
) -> None:
    page_rgb = page.convert("RGB")
    image_buffer = io.BytesIO()
    page_rgb.save(image_buffer, format="JPEG", quality=95)
    image_data = image_buffer.getvalue()

    scale = 72.0 / float(PDF_EXPORT_DPI)
    page_width_pt = page_rgb.width * scale
    page_height_pt = page_rgb.height * scale
    content_stream = (
        f"q\n{pdf_number(page_width_pt)} 0 0 {pdf_number(page_height_pt)} 0 0 cm\n/Im0 Do\nQ\n"
    ).encode("ascii")

    objects: list[tuple[int, bytes]] = []
    field_refs: list[str] = []
    annot_refs: list[str] = []
    next_object_id = 6

    checkbox_object_ids: list[int] = []
    off_appearance_id = None
    yes_appearance_id = None
    if checkbox_positions:
        off_appearance_id = next_object_id
        yes_appearance_id = next_object_id + 1
        next_object_id += 2
        for _ in checkbox_positions:
            checkbox_object_ids.append(next_object_id)
            field_refs.append(f"{next_object_id} 0 R")
            annot_refs.append(f"{next_object_id} 0 R")
            next_object_id += 1

    popup_records: dict[str, dict] = {}
    visible_popup_keys = sorted({
        str(link.get("key") or "").strip()
        for link in piece_links
        if str(link.get("key") or "").strip() in popup_images
    })
    first_link_by_key: dict[str, tuple[float, float, float, float]] = {}
    for link in piece_links:
        key = str(link.get("key") or "").strip()
        if key and key not in first_link_by_key and isinstance(link.get("rect"), tuple):
            first_link_by_key[key] = link["rect"]

    for key in visible_popup_keys:
        popup_data = popup_images[key]
        popup_rect = pdf_popup_rect_from_link(
            first_link_by_key[key],
            popup_data,
            page_rgb.width,
            page_rgb.height,
        )
        image_object_id = next_object_id
        appearance_object_id = next_object_id + 1
        widget_object_id = next_object_id + 2
        next_object_id += 3
        popup_records[key] = {
            "image_object_id": image_object_id,
            "appearance_object_id": appearance_object_id,
            "widget_object_id": widget_object_id,
            "rect": popup_rect,
            "data": popup_data,
        }
        field_refs.append(f"{widget_object_id} 0 R")
        annot_refs.append(f"{widget_object_id} 0 R")

    link_button_records: list[dict] = []
    for link in piece_links:
        key = str(link.get("key") or "").strip()
        rect = link.get("rect")
        if key not in popup_records or not isinstance(rect, tuple):
            continue
        object_id = next_object_id
        next_object_id += 1
        link_button_records.append({"object_id": object_id, "key": key, "rect": rect})
        field_refs.append(f"{object_id} 0 R")
        annot_refs.append(f"{object_id} 0 R")
    link_button_appearance_id = None
    if link_button_records:
        link_button_appearance_id = next_object_id
        next_object_id += 1

    acroform = ""
    if field_refs:
        acroform = f" /AcroForm << /Fields [{' '.join(field_refs)}] /NeedAppearances false >>"
    objects.append((1, f"<< /Type /Catalog /Pages 2 0 R{acroform} >>".encode("ascii")))
    objects.append((2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"))

    annots = f" /Annots [{' '.join(annot_refs)}]" if annot_refs else ""
    page_body = (
        "<< /Type /Page /Parent 2 0 R "
        f"/MediaBox [0 0 {pdf_number(page_width_pt)} {pdf_number(page_height_pt)}] "
        "/Resources << /ProcSet [/PDF /ImageC] /XObject << /Im0 5 0 R >> >> "
        f"/Contents 4 0 R{annots} >>"
    )
    objects.append((3, page_body.encode("ascii")))
    objects.append((4, pdf_stream_object("", content_stream)))
    image_dictionary = (
        f"/Type /XObject /Subtype /Image /Width {page_rgb.width} /Height {page_rgb.height} "
        "/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode"
    )
    objects.append((5, pdf_stream_object(image_dictionary, image_data)))

    if checkbox_positions and off_appearance_id is not None and yes_appearance_id is not None:
        checkbox_size_pt = PDF_CHECKBOX_SIZE * scale
        appearance_dictionary = (
            f"/Type /XObject /Subtype /Form /FormType 1 /BBox [0 0 "
            f"{pdf_number(checkbox_size_pt)} {pdf_number(checkbox_size_pt)}] /Resources << >>"
        )
        objects.append((
            off_appearance_id,
            pdf_stream_object(appearance_dictionary, pdf_checkbox_appearance(checkbox_size_pt, checked=False)),
        ))
        objects.append((
            yes_appearance_id,
            pdf_stream_object(appearance_dictionary, pdf_checkbox_appearance(checkbox_size_pt, checked=True)),
        ))
        for index, ((x_px, y_px), object_id) in enumerate(zip(checkbox_positions, checkbox_object_ids), start=1):
            rect = pdf_checkbox_rect(x_px, y_px, page_rgb.height, scale)
            changed_js = pdf_literal_string(pdf_checkbox_changed_javascript())
            widget = (
                "<< /Type /Annot /Subtype /Widget /FT /Btn "
                f"/T (cb_{index:05d}) /F 4 /Ff 0 /Rect [{rect}] "
                "/V /Off /DV /Off /AS /Off "
                f"/AP << /N << /Off {off_appearance_id} 0 R /Yes {yes_appearance_id} 0 R >> >> "
                f"/AA << /U << /S /JavaScript /JS {changed_js} >> >> "
                "/MK << /BC [0 0 0] /BG [1 1 1] >> "
                "/BS << /W 1 /S /S >> /H /P /P 3 0 R >>"
            )
            objects.append((object_id, widget.encode("ascii")))

    for key, record in popup_records.items():
        popup_data = record["data"]
        popup_path = Path(popup_data["path"])
        popup_image_data, image_width, image_height = _popup_image_jpeg_data(popup_path)

        image_dictionary = (
            f"/Type /XObject /Subtype /Image /Width {image_width} /Height {image_height} "
            "/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode"
        )
        image_object_id = int(record["image_object_id"])
        appearance_object_id = int(record["appearance_object_id"])
        widget_object_id = int(record["widget_object_id"])
        objects.append((image_object_id, pdf_stream_object(image_dictionary, popup_image_data)))

        popup_x, popup_y, popup_w, popup_h = record["rect"]
        popup_w_pt = popup_w * scale
        popup_h_pt = popup_h * scale
        appearance_dictionary = (
            f"/Type /XObject /Subtype /Form /FormType 1 /BBox [0 0 {pdf_number(popup_w_pt)} {pdf_number(popup_h_pt)}] "
            f"/Resources << /XObject << /PopupImage {image_object_id} 0 R >> >>"
        )
        objects.append((
            appearance_object_id,
            pdf_stream_object(
                appearance_dictionary,
                pdf_popup_appearance("PopupImage", popup_w_pt, popup_h_pt, image_width, image_height, scale),
            ),
        ))

        popup_rect = pdf_rect_from_pixels(popup_x, popup_y, popup_w, popup_h, page_rgb.height, scale)
        hide_js = pdf_literal_string(pdf_hide_popup_javascript(key))
        popup_widget = (
            "<< /Type /Annot /Subtype /Widget /FT /Btn "
            f"/T {pdf_literal_string(key)} /F 6 /Ff 65536 /Rect [{popup_rect}] "
            f"/AP << /N {appearance_object_id} 0 R >> "
            f"/A << /S /JavaScript /JS {hide_js} >> "
            f"/AA << /U << /S /JavaScript /JS {hide_js} >> >> "
            "/MK << /BC [0 0 0] /BG [1 1 1] >> /BS << /W 1 /S /S >> /P 3 0 R >>"
        )
        objects.append((widget_object_id, popup_widget.encode("ascii")))

    if link_button_appearance_id is not None:
        objects.append((
            link_button_appearance_id,
            pdf_stream_object(
                "/Type /XObject /Subtype /Form /FormType 1 /BBox [0 0 1 1] /Resources << >>",
                b"",
            ),
        ))

    for index, record in enumerate(link_button_records, start=1):
        key = record["key"]
        x_px, y_px, width_px, height_px = record["rect"]
        rect = pdf_rect_from_pixels(x_px, y_px, width_px, height_px, page_rgb.height, scale)
        js = pdf_literal_string(pdf_show_popup_javascript(key, visible_popup_keys))
        link_button = (
            "<< /Type /Annot /Subtype /Widget /FT /Btn "
            f"/T {pdf_literal_string(f'open_{index:05d}_{key}')} /F 4 /Ff 65536 /Rect [{rect}] "
            f"/AP << /N {link_button_appearance_id} 0 R >> "
            f"/A << /S /JavaScript /JS {js} >> "
            f"/AA << /U << /S /JavaScript /JS {js} >> >> "
            "/MK << >> /BS << /W 0 /S /S >> /H /P /P 3 0 R >>"
        )
        objects.append((int(record["object_id"]), link_button.encode("ascii")))

    max_object_id = max(object_id for object_id, _ in objects)
    objects.sort(key=lambda item: item[0])
    pdf_data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0] * (max_object_id + 1)
    for object_id, body in objects:
        offsets[object_id] = len(pdf_data)
        pdf_data.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf_data.extend(body)
        pdf_data.extend(b"\nendobj\n")

    xref_offset = len(pdf_data)
    pdf_data.extend(f"xref\n0 {max_object_id + 1}\n".encode("ascii"))
    pdf_data.extend(b"0000000000 65535 f \n")
    for object_id in range(1, max_object_id + 1):
        pdf_data.extend(f"{offsets[object_id]:010d} 00000 n \n".encode("ascii"))
    pdf_data.extend(
        f"trailer\n<< /Size {max_object_id + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    output_pdf.write_bytes(pdf_data)


def export_production_sheet_pdf(project: Project, output_pdf: Path) -> Path:
    """Genera un PDF plano continuo de la planilla de produccion."""

    if not _pil_image_available():
        raise RuntimeError("Pillow es necesario para generar el PDF de planilla.")

    from PIL import Image, ImageDraw

    output_pdf = Path(output_pdf)
    program_dimensions_cache: dict[tuple[str, str], tuple[float | None, float | None, float | None]] = {}
    module_gap = 24
    blocks = []
    popup_images: dict[str, dict] = {}
    drawing_index = 0

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        for module in project.modules:
            module_data = _load_module_sheet_data(project, module, program_dimensions_cache)
            drawing_index, module_popups = _prepare_pdf_piece_popups(
                project,
                module,
                module_data["pieces"],
                temp_dir,
                drawing_index,
            )
            popup_images.update(module_popups)
            blocks.append(_render_module_pdf_block(project, module, module_data))

        content_height = (
            PDF_MARGIN_TOP
            + PDF_HEADER_HEIGHT
            + sum(block.height for block, _checkboxes, _links in blocks)
            + (module_gap * max(0, len(blocks) - 1))
            + PDF_MARGIN_BOTTOM
        )
        page_height = max(PDF_PAGE_HEIGHT, content_height)
        page = Image.new("RGB", (PDF_PAGE_WIDTH, page_height), "white")
        draw = ImageDraw.Draw(page)
        current_y = _draw_production_pdf_header(draw, project)
        checkbox_positions: list[tuple[int, int]] = []
        piece_links: list[dict] = []

        for index, (block, block_checkboxes, block_links) in enumerate(blocks):
            page.paste(block, (PDF_MARGIN_X, current_y))
            checkbox_positions.extend(
                (PDF_MARGIN_X + x, current_y + y)
                for x, y in block_checkboxes
            )
            for link in block_links:
                x, y, width, height = link["rect"]
                piece_links.append({
                    "key": link["key"],
                    "rect": (PDF_MARGIN_X + x, current_y + y, width, height),
                })
            current_y += block.height
            if index < len(blocks) - 1:
                current_y += module_gap

        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        _write_interactive_pdf_page(page, output_pdf, checkbox_positions, popup_images, piece_links)
    return output_pdf


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
