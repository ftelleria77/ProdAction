"""Low-level helpers for the interactive production-sheet PDF."""

from __future__ import annotations

PDF_EXPORT_DPI = 150
PDF_PAGE_WIDTH = int(round(8.27 * PDF_EXPORT_DPI))
PDF_PAGE_HEIGHT = int(round(11.69 * PDF_EXPORT_DPI))
PDF_MARGIN_X = int(round(0.35 * PDF_EXPORT_DPI))
PDF_MARGIN_TOP = int(round(0.35 * PDF_EXPORT_DPI))
PDF_MARGIN_BOTTOM = int(round(0.3 * PDF_EXPORT_DPI))
PDF_HEADER_HEIGHT = int(round(1.05 * PDF_EXPORT_DPI))

PDF_CHECKBOX_SIZE = 16
PDF_CHECKBOX_GAP = 6
PDF_CHECKBOX_MARGIN_X = 6
PDF_CHECKBOX_MARGIN_Y = 7


def pdf_number(value: float) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".") or "0"


def pdf_checkbox_appearance(size_pt: float, *, checked: bool) -> bytes:
    size = pdf_number(size_pt)
    inset = pdf_number(max(0.5, size_pt * 0.08))
    box_size = pdf_number(max(1.0, size_pt - (2 * float(inset))))
    commands = [
        "q",
        "1 1 1 rg",
        f"0 0 {size} {size} re f",
        "0 0 0 RG",
        "1 w",
        f"{inset} {inset} {box_size} {box_size} re S",
    ]
    if checked:
        commands.extend([
            "2 w",
            f"{pdf_number(size_pt * 0.22)} {pdf_number(size_pt * 0.52)} m",
            f"{pdf_number(size_pt * 0.42)} {pdf_number(size_pt * 0.28)} l",
            f"{pdf_number(size_pt * 0.78)} {pdf_number(size_pt * 0.76)} l",
            "S",
        ])
    commands.append("Q")
    return "\n".join(commands).encode("ascii")


def pdf_stream_object(dictionary: str, stream_data: bytes) -> bytes:
    return (
        f"<< {dictionary} /Length {len(stream_data)} >>\nstream\n".encode("ascii")
        + stream_data
        + b"\nendstream"
    )


def pdf_literal_string(value: str) -> str:
    encoded = str(value or "").encode("cp1252", errors="replace").decode("cp1252")
    escaped = (
        encoded
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )
    return f"({escaped})"


def pdf_rect_from_pixels(
    x_px: float,
    y_px: float,
    width_px: float,
    height_px: float,
    page_height_px: int,
    scale: float,
) -> str:
    llx = x_px * scale
    lly = (page_height_px - (y_px + height_px)) * scale
    urx = (x_px + width_px) * scale
    ury = (page_height_px - y_px) * scale
    return " ".join(pdf_number(value) for value in (llx, lly, urx, ury))


def pdf_checkbox_rect(x_px: int, y_px: int, page_height_px: int, scale: float) -> str:
    return pdf_rect_from_pixels(x_px, y_px, PDF_CHECKBOX_SIZE, PDF_CHECKBOX_SIZE, page_height_px, scale)


def pdf_popup_rect_from_link(
    link_rect: tuple[float, float, float, float],
    popup_data: dict,
    page_width_px: int,
    page_height_px: int,
) -> tuple[int, int, int, int]:
    _link_x, link_y, _link_w, _link_h = link_rect
    image_width = int(popup_data.get("width") or 1)
    image_height = int(popup_data.get("height") or 1)
    popup_width = min(max(image_width + 36, 260), max(260, page_width_px - (PDF_MARGIN_X * 2) - 24))
    popup_height = min(max(image_height + 36, 200), max(200, page_height_px - (PDF_MARGIN_TOP + PDF_MARGIN_BOTTOM)))
    popup_x = max(PDF_MARGIN_X, page_width_px - PDF_MARGIN_X - popup_width - 12)
    popup_y = int(min(max(PDF_MARGIN_TOP, link_y - 16), max(PDF_MARGIN_TOP, page_height_px - PDF_MARGIN_BOTTOM - popup_height)))
    return popup_x, popup_y, popup_width, popup_height


def pdf_popup_appearance(
    image_name: str,
    popup_width_pt: float,
    popup_height_pt: float,
    image_width_px: int,
    image_height_px: int,
    scale: float,
) -> bytes:
    margin = 8.0
    image_width_pt = max(1.0, image_width_px * scale)
    image_height_pt = max(1.0, image_height_px * scale)
    fit_ratio = min(
        (popup_width_pt - (margin * 2)) / image_width_pt,
        (popup_height_pt - (margin * 2)) / image_height_pt,
    )
    fitted_width = image_width_pt * fit_ratio
    fitted_height = image_height_pt * fit_ratio
    image_x = (popup_width_pt - fitted_width) / 2.0
    image_y = (popup_height_pt - fitted_height) / 2.0
    commands = [
        "q",
        "1 1 1 rg",
        f"0 0 {pdf_number(popup_width_pt)} {pdf_number(popup_height_pt)} re f",
        "0 0 0 RG",
        "1.2 w",
        f"0.6 0.6 {pdf_number(popup_width_pt - 1.2)} {pdf_number(popup_height_pt - 1.2)} re S",
        "q",
        f"{pdf_number(fitted_width)} 0 0 {pdf_number(fitted_height)} {pdf_number(image_x)} {pdf_number(image_y)} cm",
        f"/{image_name} Do",
        "Q",
        "Q",
    ]
    return "\n".join(commands).encode("ascii")


def pdf_show_popup_javascript(active_key: str, popup_keys: list[str]) -> str:
    lines = ["try {"]
    for key in popup_keys:
        lines.append(f'var f_{key}=this.getField("{key}"); if (f_{key}) f_{key}.display = display.hidden;')
    lines.append(f'var active=this.getField("{active_key}"); if (active) active.display = display.visible;')
    lines.append("} catch (e) {}")
    return "\n".join(lines)


def pdf_hide_popup_javascript(active_key: str) -> str:
    return f'try {{ var f=this.getField("{active_key}"); if (f) f.display = display.hidden; }} catch (e) {{}}'


def pdf_checkbox_changed_javascript() -> str:
    return f'try {{ this.dirty = true; }} catch (e) {{}}'
