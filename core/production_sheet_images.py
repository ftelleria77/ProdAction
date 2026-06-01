"""Image preparation helpers for production sheet exports."""

from __future__ import annotations

import io
import re
from pathlib import Path

from core.model import Piece, Project
from core.production_sheet_data import piece_from_sheet_row

try:
    import cairosvg
except Exception:  # pragma: no cover - optional dependency
    cairosvg = None

try:
    from PIL import Image as PILImage
except Exception:  # pragma: no cover - optional dependency
    PILImage = None

try:
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover - optional dependency
    QImage = None
    QPainter = None
    QSvgRenderer = None
    QApplication = None


_QT_APP_REF = None


def pil_image_available() -> bool:
    return PILImage is not None


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return cleaned.strip("._") or "pieza"


def add_text_to_png(png_path: Path, text: str, font_size: int = 10) -> None:
    if PILImage is None:
        return

    try:
        from PIL import ImageDraw, ImageFont

        img = PILImage.open(png_path).convert("RGBA")
        img_w, img_h = img.size

        txt_layer = PILImage.new("RGBA", (img_w, img_h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        try:
            font = ImageFont.truetype("calibri.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = max(0, (img_w - text_width) // 2)
        text_y = max(0, (img_h - text_height) // 2)

        padding = 5
        bg_left = max(0, text_x - padding)
        bg_top = max(0, text_y - padding)
        bg_right = min(img_w, text_x + text_width + padding)
        bg_bottom = min(img_h, text_y + text_height + padding)
        draw.rectangle(
            [(bg_left, bg_top), (bg_right, bg_bottom)],
            fill=(255, 255, 255, 200),
        )

        draw.text((text_x, text_y), text, fill=(50, 50, 50, 255), font=font)

        img_with_text = PILImage.alpha_composite(img, txt_layer)
        img_rgb = PILImage.new("RGB", img_with_text.size, (255, 255, 255))
        img_rgb.paste(img_with_text, mask=img_with_text.split()[3])
        img_rgb.save(png_path, format="PNG")
    except Exception:
        pass


def svg_to_png_for_excel(svg_path: Path, png_path: Path, max_width_px: int = 200) -> tuple[int, int] | None:
    if cairosvg is not None and PILImage is not None:
        try:
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
        except Exception:
            pass

    if QSvgRenderer is None or QImage is None or QPainter is None:
        return None

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


def normalize_en_juego_sheet_cut_mode(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"nesting", "corte nesting", "cut nesting"}:
        return "nesting"
    if raw in {"manual", "corte manual", "cut manual"}:
        return "manual"
    return "manual"


def en_juego_sheet_replacement_enabled(config_data: dict, pieces: list[dict]) -> bool:
    settings = config_data.get("en_juego_settings")
    if not isinstance(settings, dict):
        return False
    if normalize_en_juego_sheet_cut_mode(settings.get("cut_mode")) != "nesting":
        return False
    return any(bool(piece.get("en_juego", False)) and bool(piece.get("include_in_sheet", False)) for piece in pieces)


def resolve_en_juego_output_path(
    project: Project,
    module_path: Path,
    module_name: str,
    config_data: dict,
) -> Path | None:
    raw_paths: list[str] = []
    for key in ("en_juego_output_path", "en_juego_pgmx_path"):
        raw_value = str(config_data.get(key) or "").strip()
        if raw_value:
            raw_paths.append(raw_value)

    synthesis_data = config_data.get("en_juego_synthesis")
    if isinstance(synthesis_data, dict):
        raw_value = str(synthesis_data.get("output_path") or "").strip()
        if raw_value:
            raw_paths.append(raw_value)

    bases = [module_path]
    project_root_value = str(getattr(project, "root_directory", "") or "").strip()
    if project_root_value:
        bases.append(Path(project_root_value))

    for raw_value in raw_paths:
        candidate = Path(raw_value)
        if candidate.is_file():
            return candidate
        if not candidate.is_absolute():
            for base in bases:
                based_candidate = base / candidate
                if based_candidate.is_file():
                    return based_candidate

    exact_candidates = [
        module_path / f"{module_name}_EnJuego.pgmx",
        module_path / f"{sanitize_filename(module_name)}_EnJuego.pgmx",
    ]
    for candidate in exact_candidates:
        if candidate.is_file():
            return candidate

    discovered = sorted(
        (candidate for candidate in module_path.glob("*EnJuego.pgmx") if candidate.is_file()),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    return discovered[0] if discovered else None


def build_en_juego_sheet_svg(
    project: Project,
    module,
    module_path: Path,
    config_data: dict,
    temp_dir: Path,
) -> Path | None:
    en_juego_pgmx_path = resolve_en_juego_output_path(project, module_path, module.name, config_data)
    if en_juego_pgmx_path is None:
        return None

    from pgmx.processing import build_piece_svg, parse_pgmx_for_piece

    en_juego_piece = Piece(
        id="EN_JUEGO",
        name="En-Juego",
        width=0.0,
        height=0.0,
        thickness=None,
        quantity=1,
        module_name=module.name,
        cnc_source=str(en_juego_pgmx_path),
    )
    drawing = parse_pgmx_for_piece(project, en_juego_piece, module_path)
    if drawing is None:
        return None

    svg_path = temp_dir / f"{sanitize_filename(module.name)}_EnJuego.svg"
    try:
        build_piece_svg(en_juego_piece, drawing, svg_path)
    except Exception:
        return None
    return svg_path if svg_path.is_file() else None


def prepare_module_sheet_images(
    project: Project,
    module,
    config_data: dict,
    pieces: list[dict],
    temp_dir: Path,
    *,
    max_width_px: int = 150,
) -> list[tuple[Path, int, int, str]]:
    prepared_images: list[tuple[Path, int, int, str]] = []
    if not pil_image_available():
        return prepared_images

    en_juego_replaced_piece_ids: set[str] = set()
    if en_juego_sheet_replacement_enabled(config_data, pieces):
        en_juego_svg_path = build_en_juego_sheet_svg(
            project,
            module,
            Path(module.path),
            config_data,
            temp_dir,
        )
        if en_juego_svg_path is not None:
            en_juego_png_path = temp_dir / f"{sanitize_filename(module.name)}_EnJuego.png"
            prepared_en_juego = prepare_excel_drawing_image(
                en_juego_svg_path,
                en_juego_png_path,
                "En-Juego",
                max_width_px=max_width_px,
            )
            if prepared_en_juego is not None:
                prepared_images.append(prepared_en_juego)
                en_juego_replaced_piece_ids = {
                    str(piece.get("id") or "").strip()
                    for piece in pieces
                    if bool(piece.get("en_juego", False))
                }

    for idx, piece in enumerate(pieces):
        if not bool(piece.get("include_in_sheet", False)):
            continue
        if (
            bool(piece.get("en_juego", False))
            and str(piece.get("id") or "").strip() in en_juego_replaced_piece_ids
        ):
            continue

        piece_display_name = str(piece.get("name") or piece.get("id") or "pieza").strip()
        piece_slug = sanitize_filename(piece_display_name)
        svg_path = Path(module.path) / f"{piece_slug}.svg"
        if not svg_path.is_file():
            continue

        png_path = temp_dir / f"{sanitize_filename(module.name)}_{idx}_{piece_slug}.png"
        prepared_piece = prepare_excel_drawing_image(
            svg_path,
            png_path,
            piece_display_name,
            max_width_px=max_width_px,
        )
        if prepared_piece is not None:
            prepared_images.append(prepared_piece)

    return prepared_images


def prepare_excel_drawing_image(
    svg_path: Path,
    png_path: Path,
    display_name: str,
    *,
    max_width_px: int = 150,
) -> tuple[Path, int, int, str] | None:
    size = svg_to_png_for_excel(svg_path, png_path, max_width_px=max_width_px)
    if not size:
        return None

    src_w, src_h = size
    if src_w <= 0 or src_h <= 0:
        return None

    if src_h > 150:
        ratio = 150.0 / float(src_h)
        target_w = int(round(src_w * ratio))
        target_h = 150
    else:
        target_w = src_w
        target_h = src_h

    add_text_to_png(png_path, display_name, font_size=10)
    return png_path, target_w, target_h, display_name


def image_to_rgb_on_white(image):
    if PILImage is None:
        return image
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = PILImage.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return image.convert("RGB")


def prepare_pdf_popup_drawing_image(
    svg_path: Path,
    png_path: Path,
    *,
    max_width_px: int = 1260,
    max_height_px: int = 900,
    width_scale: float = 3.0,
) -> tuple[Path, int, int] | None:
    size = svg_to_png_for_excel(svg_path, png_path, max_width_px=max_width_px)
    if not size or PILImage is None:
        return None

    try:
        with PILImage.open(png_path) as image:
            rgb_image = image_to_rgb_on_white(image)
            source_w, source_h = rgb_image.size
            if source_w <= 0 or source_h <= 0:
                return None

            target_w = max(1, int(round(source_w * width_scale)))
            target_w = min(target_w, max_width_px)
            target_h = max(1, int(round(source_h * (target_w / float(source_w)))))
            if target_h > max_height_px:
                ratio = max_height_px / float(target_h)
                target_w = max(1, int(round(target_w * ratio)))
                target_h = max_height_px

            if (target_w, target_h) != rgb_image.size:
                resampling = getattr(getattr(PILImage, "Resampling", PILImage), "LANCZOS", 1)
                rgb_image = rgb_image.resize((target_w, target_h), resampling)
            rgb_image.save(png_path, format="PNG")
            width_px, height_px = rgb_image.size
    except Exception:
        return None

    return png_path, width_px, height_px


def prepare_pdf_piece_popups(
    project: Project,
    module,
    pieces: list[dict],
    temp_dir: Path,
    drawing_index_start: int,
) -> tuple[int, dict[str, dict]]:
    drawing_index = drawing_index_start
    popup_images: dict[str, dict] = {}
    module_path = Path(module.path)

    for piece in pieces:
        piece_display_name = str(piece.get("name") or piece.get("id") or "pieza").strip()
        piece_slug = sanitize_filename(piece_display_name)
        svg_path = module_path / f"{piece_slug}.svg"
        if not svg_path.is_file():
            svg_path = temp_dir / f"{sanitize_filename(module.name)}_{piece_slug}.svg"
            try:
                from pgmx.processing import build_piece_svg, parse_pgmx_for_piece

                piece_obj = piece_from_sheet_row(module.name, piece)
                drawing_data = parse_pgmx_for_piece(project, piece_obj, module_path)
                if drawing_data is None:
                    continue
                build_piece_svg(piece_obj, drawing_data, svg_path)
            except Exception:
                continue
            if not svg_path.is_file():
                continue

        drawing_index += 1
        popup_key = f"img_{drawing_index:05d}"
        png_path = temp_dir / f"{popup_key}_{piece_slug}.png"
        prepared_popup = prepare_pdf_popup_drawing_image(svg_path, png_path)
        if prepared_popup is None:
            continue

        prepared_path, width_px, height_px = prepared_popup
        piece["_pdf_popup_key"] = popup_key
        piece["_pdf_popup_width"] = width_px
        piece["_pdf_popup_height"] = height_px
        popup_images[popup_key] = {
            "path": prepared_path,
            "width": width_px,
            "height": height_px,
            "title": piece_display_name,
        }

    return drawing_index, popup_images


def popup_image_jpeg_data(popup_path: Path) -> tuple[bytes, int, int]:
    if PILImage is None:
        return b"", 1, 1

    try:
        with PILImage.open(popup_path) as popup_image:
            popup_rgb = image_to_rgb_on_white(popup_image)
            popup_buffer = io.BytesIO()
            popup_rgb.save(popup_buffer, format="JPEG", quality=95)
            return popup_buffer.getvalue(), popup_rgb.width, popup_rgb.height
    except Exception:
        popup_rgb = PILImage.new("RGB", (1, 1), "white")
        popup_buffer = io.BytesIO()
        popup_rgb.save(popup_buffer, format="JPEG", quality=95)
        return popup_buffer.getvalue(), 1, 1
