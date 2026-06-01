"""Printable PDF renderer for cut diagrams."""

from __future__ import annotations

import math
import re
from pathlib import Path

from core.nesting_model import (
    A4_EXPORT_DPI,
    A4_LANDSCAPE_MM,
    A4_PORTRAIT_MM,
    PRINT_FONT_SCALE,
    CutBoard,
    CutPiece,
    CutPlacement,
)


def _format_dimension(value: float) -> str:
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _page_size_for_board(board: CutBoard) -> tuple[float, float]:
    if float(board.board_width) >= float(board.board_height):
        return A4_LANDSCAPE_MM
    return A4_PORTRAIT_MM


def _mm_to_pixels(value_mm: float, dpi: int = A4_EXPORT_DPI) -> int:
    return int(round(float(value_mm) / 25.4 * float(dpi)))


def _load_print_font(image_font_module, size_px: int, bold: bool = False):
    font_candidates = [
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        'arialbd.ttf' if bold else 'arial.ttf',
        'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
    ]
    for candidate in font_candidates:
        try:
            return image_font_module.truetype(candidate, size_px)
        except OSError:
            continue
    return image_font_module.load_default()


def _scaled_print_font_size(size_px: float) -> int:
    return max(1, int(math.ceil(float(size_px) * PRINT_FONT_SCALE)))


def _piece_display_name(cut_piece: CutPiece) -> str:
    display_name = str(cut_piece.label or cut_piece.piece.name or cut_piece.piece.id or "pieza").strip()
    display_name = re.sub(r'\s+#\d+(?=\s*(?:\(|$))', '', display_name).strip()
    return display_name or "pieza"


def _piece_cut_dimension_label(placement: CutPlacement) -> str:
    return f'{_format_dimension(placement.width)} x {_format_dimension(placement.height)}'


def _piece_needs_external_label(width_px: int, height_px: int) -> bool:
    return width_px < 130 or height_px < 58 or min(width_px, height_px) < 42


def _placement_should_use_external_label(placement: CutPlacement, width_px: int, height_px: int) -> bool:
    if _piece_needs_external_label(width_px, height_px):
        return True
    piece_name = _piece_display_name(placement.cut_piece)
    return len(piece_name) > 26 and (width_px < 220 or height_px < 82)


def _build_piece_identifier_overlay(image_module, image_draw_module, image_font_module, piece_number: int, width_px: int, height_px: int):
    if width_px <= 8 or height_px <= 8:
        return None

    label = str(piece_number)
    measure_image = image_module.new('RGBA', (1, 1), (255, 255, 255, 0))
    measure_draw = image_draw_module.Draw(measure_image)
    font_size = max(
        _scaled_print_font_size(10),
        min(_scaled_print_font_size(19), _scaled_print_font_size(min(width_px, height_px) * 0.68)),
    )
    font = _load_print_font(image_font_module, font_size, bold=True)
    bbox = measure_draw.textbbox((0, 0), label, font=font)
    text_width = int(round(bbox[2] - bbox[0]))
    text_height = int(round(bbox[3] - bbox[1]))
    padding_x = max(3, font_size // 3)
    padding_y = max(2, font_size // 5)
    overlay = image_module.new(
        'RGBA',
        (max(1, text_width + padding_x * 2), max(1, text_height + padding_y * 2)),
        (255, 255, 255, 0),
    )
    overlay_draw = image_draw_module.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(0, 0), (overlay.width - 1, overlay.height - 1)],
        radius=max(2, padding_y),
        fill=(255, 255, 255, 235),
        outline=(28, 53, 92, 210),
        width=1,
    )
    overlay_draw.text(
        (padding_x - bbox[0], padding_y - bbox[1]),
        label,
        fill=(17, 17, 17, 255),
        font=font,
    )
    return overlay


def _build_piece_text_overlay(
    image_module,
    image_draw_module,
    image_font_module,
    placement: CutPlacement,
    width_px: int,
    height_px: int,
    piece_number: int,
):
    piece_name = _piece_display_name(placement.cut_piece)
    if not piece_name or width_px <= 8 or height_px <= 8:
        return None

    rotate_text = height_px > width_px
    dimension_label = _piece_cut_dimension_label(placement)
    base_lines = [f'{piece_number}. {piece_name}', dimension_label]

    measure_image = image_module.new('RGBA', (1, 1), (255, 255, 255, 0))
    measure_draw = image_draw_module.Draw(measure_image)
    available_width = max(1, width_px - 12)
    available_height = max(1, height_px - 12)
    font_size = _scaled_print_font_size(16 if min(width_px, height_px) >= 76 else 14)
    font = _load_print_font(image_font_module, font_size, bold=True)
    spacing = max(2, font_size // 4)
    text = '\n'.join(base_lines)
    bbox = measure_draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align='center')
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    oriented_width = text_height if rotate_text else text_width
    oriented_height = text_width if rotate_text else text_height
    if oriented_width > available_width or oriented_height > available_height:
        return None

    text_width = int(round(text_width))
    text_height = int(round(text_height))
    padding = max(2, font_size // 4)
    overlay = image_module.new('RGBA', (text_width + padding * 2, text_height + padding * 2), (255, 255, 255, 0))
    overlay_draw = image_draw_module.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(0, 0), (overlay.width - 1, overlay.height - 1)],
        radius=max(2, padding),
        fill=(255, 255, 255, 220),
    )
    overlay_draw.multiline_text(
        (padding - bbox[0], padding - bbox[1]),
        text,
        fill=(17, 17, 17, 255),
        font=font,
        spacing=spacing,
        align='center',
    )
    if rotate_text:
        overlay = overlay.rotate(270, expand=True)
    return overlay


def _placement_requires_external_label(
    image_module,
    image_draw_module,
    image_font_module,
    placement: CutPlacement,
    piece_number: int,
    width_px: int,
    height_px: int,
) -> bool:
    if _placement_should_use_external_label(placement, width_px, height_px):
        return True
    return _build_piece_text_overlay(
        image_module,
        image_draw_module,
        image_font_module,
        placement,
        width_px,
        height_px,
        piece_number,
    ) is None


def _draw_dashed_guide(draw, start: tuple[int, int], end: tuple[int, int], color: str, width: int = 3, dash: int = 18, gap: int = 10):
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        current = min(y1, y2)
        limit = max(y1, y2)
        while current < limit:
            segment_end = min(current + dash, limit)
            draw.line([(x1, current), (x2, segment_end)], fill=color, width=width)
            current = segment_end + gap
        return

    if y1 == y2:
        current = min(x1, x2)
        limit = max(x1, x2)
        while current < limit:
            segment_end = min(current + dash, limit)
            draw.line([(current, y1), (segment_end, y2)], fill=color, width=width)
            current = segment_end + gap


def _draw_dimension_label(
    image,
    image_module,
    image_draw_module,
    text: str,
    center_x: float,
    center_y: float,
    font,
    *,
    rotate: bool = False,
):
    if not text:
        return

    measure_image = image_module.new('RGBA', (1, 1), (255, 255, 255, 0))
    measure_draw = image_draw_module.Draw(measure_image)
    bbox = measure_draw.textbbox((0, 0), text, font=font)
    text_width = int(round(bbox[2] - bbox[0]))
    text_height = int(round(bbox[3] - bbox[1]))
    padding_x = 5
    padding_y = 3
    overlay = image_module.new(
        'RGBA',
        (max(1, text_width + padding_x * 2), max(1, text_height + padding_y * 2)),
        (255, 255, 255, 0),
    )
    overlay_draw = image_draw_module.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(0, 0), (overlay.width - 1, overlay.height - 1)],
        radius=4,
        fill=(255, 253, 248, 220),
        outline=(42, 54, 82, 190),
        width=1,
    )
    overlay_draw.text(
        (padding_x - bbox[0], padding_y - bbox[1]),
        text,
        fill=(28, 53, 92, 255),
        font=font,
    )
    if rotate:
        overlay = overlay.rotate(270, expand=True)

    paste_x = int(round(center_x - overlay.width / 2.0))
    paste_y = int(round(center_y - overlay.height / 2.0))
    paste_x = max(0, min(image.width - overlay.width, paste_x))
    paste_y = max(0, min(image.height - overlay.height, paste_y))
    image.paste(overlay, (paste_x, paste_y), overlay)


def _draw_piece_cut_dimensions(
    image,
    draw,
    image_module,
    image_draw_module,
    image_font_module,
    placement: CutPlacement,
    x_px: int,
    y_px: int,
    width_px: int,
    height_px: int,
):
    if width_px <= 36 or height_px <= 28:
        return

    inset = max(7, min(18, int(round(min(width_px, height_px) * 0.12))))
    font_size = max(
        _scaled_print_font_size(10),
        min(_scaled_print_font_size(17), _scaled_print_font_size(min(width_px, height_px) * 0.18)),
    )
    font = _load_print_font(image_font_module, font_size, bold=True)

    horizontal_label = _format_dimension(placement.width)
    vertical_label = _format_dimension(placement.height)

    if width_px >= 72 and height_px >= 42:
        _draw_dimension_label(
            image,
            image_module,
            image_draw_module,
            horizontal_label,
            x_px + width_px / 2.0,
            y_px + inset,
            font,
        )

    if height_px >= 72 and width_px >= 42:
        _draw_dimension_label(
            image,
            image_module,
            image_draw_module,
            vertical_label,
            x_px + width_px - inset,
            y_px + height_px / 2.0,
            font,
            rotate=True,
        )


def _main_cut_dimension_points(cut_positions: list[float], total_size: float) -> list[float]:
    total = max(0.0, float(total_size))
    points = [0.0]
    for position in sorted(_safe_float(position) for position in cut_positions):
        if position is None:
            continue
        if position <= 0.5 or position >= total - 0.5:
            continue
        if abs(position - points[-1]) > 0.5:
            points.append(float(position))
    if not points or abs(total - points[-1]) > 0.5:
        points.append(total)
    return points


def _draw_horizontal_main_cut_dimensions(
    image,
    draw,
    image_module,
    image_draw_module,
    image_font_module,
    *,
    board_left_px: int,
    board_top_px: int,
    board_width_px: int,
    scale: float,
    cut_positions: list[float],
    board_width_mm: float,
    top_band_px: int,
):
    points = _main_cut_dimension_points(cut_positions, board_width_mm)
    if len(points) < 2 or top_band_px <= 0:
        return

    dimension_color = '#1c355c'
    line_width = 2
    tick = max(6, min(11, top_band_px // 5))
    line_y = board_top_px - max(18, int(round(top_band_px * 0.52)))
    font = _load_print_font(
        image_font_module,
        max(
            _scaled_print_font_size(10),
            min(_scaled_print_font_size(16), _scaled_print_font_size(top_band_px / 4.0)),
        ),
        bold=True,
    )
    board_right_px = board_left_px + board_width_px

    for point in points:
        point_x = int(round(board_left_px + point * scale))
        point_x = max(board_left_px, min(board_right_px, point_x))
        draw.line(
            [(point_x, board_top_px), (point_x, line_y + tick)],
            fill=dimension_color,
            width=1,
        )

    for start, end in zip(points, points[1:]):
        if end - start <= 0.5:
            continue
        x1 = int(round(board_left_px + start * scale))
        x2 = int(round(board_left_px + end * scale))
        x1 = max(board_left_px, min(board_right_px, x1))
        x2 = max(board_left_px, min(board_right_px, x2))
        if x2 - x1 < 8:
            continue
        draw.line([(x1, line_y), (x2, line_y)], fill=dimension_color, width=line_width)
        draw.line([(x1, line_y - tick), (x1, line_y + tick)], fill=dimension_color, width=line_width)
        draw.line([(x2, line_y - tick), (x2, line_y + tick)], fill=dimension_color, width=line_width)
        _draw_dimension_label(
            image,
            image_module,
            image_draw_module,
            _format_dimension(end - start),
            (x1 + x2) / 2.0,
            line_y,
            font,
        )


def _draw_vertical_main_cut_dimensions(
    image,
    draw,
    image_module,
    image_draw_module,
    image_font_module,
    *,
    board_left_px: int,
    board_top_px: int,
    board_width_px: int,
    board_height_px: int,
    scale: float,
    cut_positions: list[float],
    board_height_mm: float,
    right_band_px: int,
):
    points = _main_cut_dimension_points(cut_positions, board_height_mm)
    if len(points) < 2 or right_band_px <= 0:
        return

    dimension_color = '#1c355c'
    line_width = 2
    tick = max(6, min(11, right_band_px // 5))
    board_right_px = board_left_px + board_width_px
    x_line = board_right_px + max(18, int(round(right_band_px * 0.45)))
    font = _load_print_font(
        image_font_module,
        max(
            _scaled_print_font_size(10),
            min(_scaled_print_font_size(16), _scaled_print_font_size(right_band_px / 4.0)),
        ),
        bold=True,
    )
    board_bottom_px = board_top_px + board_height_px

    for point in points:
        point_y = int(round(board_top_px + point * scale))
        point_y = max(board_top_px, min(board_bottom_px, point_y))
        draw.line(
            [(board_right_px, point_y), (x_line - tick, point_y)],
            fill=dimension_color,
            width=1,
        )

    for start, end in zip(points, points[1:]):
        if end - start <= 0.5:
            continue
        y1 = int(round(board_top_px + start * scale))
        y2 = int(round(board_top_px + end * scale))
        y1 = max(board_top_px, min(board_bottom_px, y1))
        y2 = max(board_top_px, min(board_bottom_px, y2))
        if y2 - y1 < 8:
            continue
        draw.line([(x_line, y1), (x_line, y2)], fill=dimension_color, width=line_width)
        draw.line([(x_line - tick, y1), (x_line + tick, y1)], fill=dimension_color, width=line_width)
        draw.line([(x_line - tick, y2), (x_line + tick, y2)], fill=dimension_color, width=line_width)
        _draw_dimension_label(
            image,
            image_module,
            image_draw_module,
            _format_dimension(end - start),
            x_line,
            (y1 + y2) / 2.0,
            font,
            rotate=True,
        )


def _wrap_text_to_width(draw, text: str, font, max_width_px: int) -> list[str]:
    words = str(text or "").split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f'{current} {word}'
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width_px:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)
    return lines


def _draw_external_piece_list(
    draw,
    image_font_module,
    entries: list[tuple[int, CutPlacement]],
    *,
    left_px: int,
    top_px: int,
    width_px: int,
    height_px: int,
):
    if not entries or width_px <= 40 or height_px <= 40:
        return

    title_font = _load_print_font(image_font_module, _scaled_print_font_size(17), bold=True)
    entry_font = _load_print_font(image_font_module, _scaled_print_font_size(13))
    entry_bold_font = _load_print_font(image_font_module, _scaled_print_font_size(13), bold=True)
    padding = _scaled_print_font_size(8)
    line_gap = _scaled_print_font_size(3)
    row_gap = _scaled_print_font_size(7)
    usable_width = max(1, width_px - padding * 2)
    bottom_px = top_px + height_px

    draw.rounded_rectangle(
        [(left_px, top_px), (left_px + width_px, bottom_px)],
        radius=8,
        fill='#ffffff',
        outline='#9a9a9a',
        width=1,
    )
    cursor_y = top_px + padding
    draw.text((left_px + padding, cursor_y), 'Piezas pequenas', fill='#111111', font=title_font)
    title_bbox = draw.textbbox((left_px + padding, cursor_y), 'Piezas pequenas', font=title_font)
    cursor_y = title_bbox[3] + row_gap

    for entry_index, (piece_number, placement) in enumerate(entries):
        if cursor_y + _scaled_print_font_size(22) > bottom_px - padding:
            remaining = len(entries) - entry_index
            draw.text(
                (left_px + padding, cursor_y),
                f'+ {remaining} piezas mas',
                fill='#111111',
                font=entry_bold_font,
            )
            break

        number_text = f'{piece_number}.'
        draw.text((left_px + padding, cursor_y), number_text, fill='#111111', font=entry_bold_font)
        number_bbox = draw.textbbox((left_px + padding, cursor_y), number_text, font=entry_bold_font)
        text_left = number_bbox[2] + 5
        text_width = max(1, left_px + width_px - padding - text_left)

        name_lines = _wrap_text_to_width(
            draw,
            _piece_display_name(placement.cut_piece),
            entry_font,
            text_width,
        )
        dimension_line = f'C {_piece_cut_dimension_label(placement)}'
        for line in name_lines[:2]:
            if cursor_y + _scaled_print_font_size(14) > bottom_px - padding:
                return
            draw.text((text_left, cursor_y), line, fill='#222222', font=entry_font)
            line_bbox = draw.textbbox((text_left, cursor_y), line, font=entry_font)
            cursor_y = line_bbox[3] + line_gap

        if cursor_y + _scaled_print_font_size(12) > bottom_px - padding:
            return
        draw.text((text_left, cursor_y), dimension_line, fill='#555555', font=entry_font)
        dimension_bbox = draw.textbbox((text_left, cursor_y), dimension_line, font=entry_font)
        cursor_y = dimension_bbox[3] + row_gap


def _board_group_key(board: CutBoard) -> tuple[str, float]:
    return (str(board.material or "").strip().lower(), round(float(board.thickness or 0.0), 2))


def _build_board_print_image(
    board: CutBoard,
    *,
    production_name: str = "",
    client_name: str = "",
    board_group_total: int = 1,
):
    from PIL import Image, ImageDraw, ImageFont

    page_width_mm, page_height_mm = _page_size_for_board(board)
    page_width_px = _mm_to_pixels(page_width_mm)
    page_height_px = _mm_to_pixels(page_height_mm)
    margin_px = _mm_to_pixels(10.0)
    header_h_px = _mm_to_pixels(28.0)
    has_horizontal_main_cut_dimensions = (
        board.main_cut_orientation == 'vertical' and bool(board.main_cut_positions)
    )
    has_vertical_main_cut_dimensions = (
        board.main_cut_orientation == 'horizontal' and bool(board.main_cut_positions)
    )
    top_dimension_band_px = _mm_to_pixels(12.0) if has_horizontal_main_cut_dimensions else 0
    right_dimension_band_px = _mm_to_pixels(18.0) if has_vertical_main_cut_dimensions else 0
    legend_gap_px = _mm_to_pixels(3.0)
    legend_band_px = 0

    def compute_layout(current_legend_band_px: int):
        board_top = margin_px + header_h_px + top_dimension_band_px
        legend_gap = legend_gap_px if current_legend_band_px > 0 else 0
        available_width = page_width_px - margin_px * 2 - right_dimension_band_px - current_legend_band_px - legend_gap
        available_height = page_height_px - board_top - margin_px
        current_scale = min(available_width / board.board_width, available_height / board.board_height)
        current_scale = max(0.01, current_scale)
        current_board_width = int(round(board.board_width * current_scale))
        current_board_height = int(round(board.board_height * current_scale))
        current_board_left = margin_px + max(0, (available_width - current_board_width) // 2)
        return board_top, available_width, available_height, current_scale, current_board_width, current_board_height, current_board_left

    for _ in range(2):
        board_top_px, available_width_px, available_height_px, scale, board_width_px, board_height_px, board_left_px = compute_layout(legend_band_px)
        needs_legend = False
        for piece_number, placement in enumerate(board.placements, start=1):
            width_px = int(round(placement.width * scale))
            height_px = int(round(placement.height * scale))
            if _placement_requires_external_label(
                Image,
                ImageDraw,
                ImageFont,
                placement,
                piece_number,
                width_px,
                height_px,
            ):
                needs_legend = True
                break
        if needs_legend and legend_band_px == 0:
            legend_band_px = _mm_to_pixels(40.0)
            continue
        break

    image = Image.new('RGB', (page_width_px, page_height_px), 'white')
    draw = ImageDraw.Draw(image)

    title_font = _load_print_font(ImageFont, _scaled_print_font_size(24), bold=True)
    material_font = _load_print_font(ImageFont, _scaled_print_font_size(22), bold=True)
    subtitle_font = _load_print_font(ImageFont, _scaled_print_font_size(15))
    header_parts = []
    if str(production_name or "").strip():
        header_parts.append(f'Produccion: {str(production_name).strip()}')
    if str(client_name or "").strip():
        header_parts.append(f'Cliente: {str(client_name).strip()}')
    if not header_parts:
        header_parts.append('Diagrama de corte')
    draw.text(
        (margin_px, _mm_to_pixels(4.0)),
        ' | '.join(header_parts),
        fill='#111111',
        font=title_font,
    )
    draw.text(
        (margin_px, _mm_to_pixels(12.5)),
        f'{board.material} - {_format_dimension(board.thickness)} mm - Placa {board.index} de {max(1, int(board_group_total or 1))}',
        fill='#222222',
        font=material_font,
    )
    draw.text(
        (margin_px, _mm_to_pixels(21.0)),
        f'Base: {_format_dimension(board.board_width)} x {_format_dimension(board.board_height)} mm | Margen: {_format_dimension(board.board_margin)} mm | Veta: {board.grain or "-"}',
        fill='#4f4f4f',
        font=subtitle_font,
    )
    draw.rounded_rectangle(
        [
            (board_left_px, board_top_px),
            (board_left_px + board_width_px, board_top_px + board_height_px),
        ],
        radius=max(8, _mm_to_pixels(1.8)),
        fill='#ffffff',
        outline='#2f2f2f',
        width=2,
    )

    if has_horizontal_main_cut_dimensions:
        _draw_horizontal_main_cut_dimensions(
            image,
            draw,
            Image,
            ImageDraw,
            ImageFont,
            board_left_px=board_left_px,
            board_top_px=board_top_px,
            board_width_px=board_width_px,
            scale=scale,
            cut_positions=board.main_cut_positions,
            board_width_mm=board.board_width,
            top_band_px=top_dimension_band_px,
        )
    if has_vertical_main_cut_dimensions:
        _draw_vertical_main_cut_dimensions(
            image,
            draw,
            Image,
            ImageDraw,
            ImageFont,
            board_left_px=board_left_px,
            board_top_px=board_top_px,
            board_width_px=board_width_px,
            board_height_px=board_height_px,
            scale=scale,
            cut_positions=board.main_cut_positions,
            board_height_mm=board.board_height,
            right_band_px=right_dimension_band_px,
        )

    external_label_entries: list[tuple[int, CutPlacement]] = []

    for piece_number, placement in enumerate(board.placements, start=1):
        x_px = int(round(board_left_px + placement.x * scale))
        y_px = int(round(board_top_px + placement.y * scale))
        width_px = int(round(placement.width * scale))
        height_px = int(round(placement.height * scale))
        use_external_label = _placement_should_use_external_label(placement, width_px, height_px)
        if use_external_label:
            external_label_entries.append((piece_number, placement))

        draw.rectangle(
            [
                (x_px, y_px),
                (x_px + width_px, y_px + height_px),
            ],
            fill='#ffffff',
            outline='#222222',
            width=2,
        )

        if not use_external_label:
            _draw_piece_cut_dimensions(
                image,
                draw,
                Image,
                ImageDraw,
                ImageFont,
                placement,
                x_px,
                y_px,
                width_px,
                height_px,
            )

        if use_external_label:
            text_overlay = _build_piece_identifier_overlay(Image, ImageDraw, ImageFont, piece_number, width_px, height_px)
        else:
            text_overlay = _build_piece_text_overlay(Image, ImageDraw, ImageFont, placement, width_px, height_px, piece_number)
            if text_overlay is None:
                external_label_entries.append((piece_number, placement))
                text_overlay = _build_piece_identifier_overlay(Image, ImageDraw, ImageFont, piece_number, width_px, height_px)
        if text_overlay is not None:
            paste_x = x_px + max(0, (width_px - text_overlay.width) // 2)
            paste_y = y_px + max(0, (height_px - text_overlay.height) // 2)
            image.paste(text_overlay, (paste_x, paste_y), text_overlay)

    guide_color = '#d14b38'
    for cut_position in board.main_cut_positions:
        if board.main_cut_orientation == 'vertical':
            x_px = int(round(board_left_px + cut_position * scale))
            _draw_dashed_guide(
                draw,
                (x_px, board_top_px),
                (x_px, board_top_px + board_height_px),
                guide_color,
            )
        elif board.main_cut_orientation == 'horizontal':
            y_px = int(round(board_top_px + cut_position * scale))
            _draw_dashed_guide(
                draw,
                (board_left_px, y_px),
                (board_left_px + board_width_px, y_px),
                guide_color,
            )

    if legend_band_px > 0 and external_label_entries:
        legend_left_px = board_left_px + board_width_px + right_dimension_band_px + legend_gap_px
        legend_width_px = min(legend_band_px, max(0, page_width_px - margin_px - legend_left_px))
        _draw_external_piece_list(
            draw,
            ImageFont,
            external_label_entries,
            left_px=legend_left_px,
            top_px=board_top_px,
            width_px=legend_width_px,
            height_px=board_height_px,
        )

    return image


def build_cut_diagram_pdf(
    pdf_path: Path,
    boards: list[CutBoard],
    *,
    production_name: str = "",
    client_name: str = "",
) -> Path | None:
    if not boards:
        return None

    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(f'No se pudo generar el PDF A4: {exc}') from exc

    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page_images: list[Image.Image] = []
    board_group_totals: dict[tuple[str, float], int] = {}
    for board in boards:
        group_key = _board_group_key(board)
        board_group_totals[group_key] = board_group_totals.get(group_key, 0) + 1

    try:
        for board in boards:
            page_images.append(
                _build_board_print_image(
                    board,
                    production_name=production_name,
                    client_name=client_name,
                    board_group_total=board_group_totals.get(_board_group_key(board), 1),
                )
            )

        first_page, *other_pages = page_images
        first_page.save(
            pdf_path,
            'PDF',
            resolution=float(A4_EXPORT_DPI),
            save_all=True,
            append_images=other_pages,
        )
    finally:
        for image in page_images:
            image.close()

    return pdf_path
