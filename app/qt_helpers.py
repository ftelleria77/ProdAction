"""Helpers compartidos para ventanas y dialogos Qt."""

from PySide6.QtWidgets import QApplication, QDialog, QWidget

def _window_available_geometry(widget: QWidget):
    screen = None
    try:
        screen = widget.screen()
    except Exception:
        screen = None

    if screen is None:
        try:
            parent_widget = widget.parentWidget()
        except Exception:
            parent_widget = None
        if parent_widget is not None:
            try:
                screen = parent_widget.screen()
            except Exception:
                screen = None

    if screen is None:
        try:
            handle = widget.windowHandle()
        except Exception:
            handle = None
        if handle is not None:
            screen = handle.screen()

    if screen is None:
        app = QApplication.instance()
        if app is not None:
            screen = app.primaryScreen()

    return None if screen is None else screen.availableGeometry()

def _scaled_int(value: int | float, scale: float, minimum: int | None = None) -> int:
    scaled_value = int(round(float(value) * float(scale)))
    if minimum is not None:
        return max(int(minimum), scaled_value)
    return scaled_value

def _apply_responsive_window_size(
    widget: QWidget,
    desired_width: int,
    desired_height: int,
    *,
    width_ratio: float = 0.94,
    height_ratio: float = 0.90,
    min_font_size: float = 8.0,
) -> tuple[float, int, int]:
    available = _window_available_geometry(widget)
    target_width = int(desired_width)
    target_height = int(desired_height)
    if available is not None:
        target_width = min(target_width, max(360, int(available.width() * width_ratio)))
        target_height = min(target_height, max(280, int(available.height() * height_ratio)))

    scale = min(
        target_width / max(1, int(desired_width)),
        target_height / max(1, int(desired_height)),
        1.0,
    )

    current_font = widget.font()
    current_size = current_font.pointSizeF()
    if current_size <= 0:
        current_size = float(current_font.pointSize() if current_font.pointSize() > 0 else 9.0)

    font_scale = max(scale, 0.82)
    scaled_font_size = max(float(min_font_size), round(current_size * font_scale, 1))
    if scaled_font_size < current_size:
        current_font.setPointSizeF(scaled_font_size)
        widget.setFont(current_font)

    widget.resize(target_width, target_height)
    return scale, target_width, target_height

def _center_window_on_screen(widget: QWidget) -> None:
    available = _window_available_geometry(widget)
    if available is None:
        return

    frame_rect = widget.frameGeometry()
    target_width = frame_rect.width() if frame_rect.width() > 0 else widget.width()
    target_height = frame_rect.height() if frame_rect.height() > 0 else widget.height()
    if target_width <= 0 or target_height <= 0:
        return

    target_x = available.x() + max(0, int((available.width() - target_width) / 2))
    target_y = available.y() + max(0, int((available.height() - target_height) / 2))
    widget.move(target_x, target_y)

def _center_window_on_origin(widget: QWidget, origin: QWidget | None = None) -> None:
    origin_widget = origin
    if origin_widget is None:
        try:
            origin_widget = widget.parentWidget()
        except Exception:
            origin_widget = None

    if origin_widget is not None:
        try:
            origin_widget = origin_widget.window()
        except Exception:
            pass

    origin_rect = None
    if origin_widget is not None:
        try:
            candidate_rect = origin_widget.frameGeometry()
        except Exception:
            candidate_rect = None
        if candidate_rect is not None and candidate_rect.width() > 0 and candidate_rect.height() > 0:
            origin_rect = candidate_rect

    if origin_rect is None:
        _center_window_on_screen(widget)
        return

    available = _window_available_geometry(origin_widget) or _window_available_geometry(widget)
    frame_rect = widget.frameGeometry()
    target_width = frame_rect.width() if frame_rect.width() > 0 else max(widget.width(), widget.sizeHint().width())
    target_height = frame_rect.height() if frame_rect.height() > 0 else max(widget.height(), widget.sizeHint().height())
    if target_width <= 0 or target_height <= 0:
        return

    target_x = origin_rect.x() + int((origin_rect.width() - target_width) / 2)
    target_y = origin_rect.y() + int((origin_rect.height() - target_height) / 2)

    if available is not None:
        min_x = available.x()
        min_y = available.y()
        max_x = available.x() + max(0, available.width() - target_width)
        max_y = available.y() + max(0, available.height() - target_height)
        target_x = min(max(target_x, min_x), max_x)
        target_y = min(max(target_y, min_y), max_y)

    widget.move(target_x, target_y)

def _show_centered(widget: QWidget, origin: QWidget | None = None) -> None:
    widget.show()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    _center_window_on_origin(widget, origin)

def _exec_centered(dialog: QDialog, origin: QWidget | None = None) -> int:
    _center_window_on_origin(dialog, origin)
    return dialog.exec()
