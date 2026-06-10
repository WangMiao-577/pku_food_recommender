"""
ui_scale.py - 跨屏幕尺寸的 UI 缩放辅助
"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication


DESIGN_WIDTH = 1600
DESIGN_HEIGHT = 900
SIDEBAR_MIN = 220
SIDEBAR_MAX = 380

_viewport_width = DESIGN_WIDTH
_viewport_height = DESIGN_HEIGHT


def set_viewport_size(width: int, height: int):
    global _viewport_width, _viewport_height
    _viewport_width = max(800, width)
    _viewport_height = max(600, height)


def viewport_width() -> int:
    return _viewport_width


def viewport_height() -> int:
    return _viewport_height


def sidebar_width_for(window_width: int) -> int:
    ratio = window_width / DESIGN_WIDTH
    w = int(300 * ratio)
    return max(SIDEBAR_MIN, min(SIDEBAR_MAX, w))


def scale_value(base: int, window_width: int = None, lo: int = None, hi: int = None) -> int:
    width = window_width or _viewport_width
    ratio = width / DESIGN_WIDTH
    v = int(base * ratio)
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


DISH_IMAGE_SCALE = 1.3


def dish_dim(value: int) -> int:
    """菜品配图基准尺寸 × 1.2"""
    return int(round(value * DISH_IMAGE_SCALE))


def scale_pair(w: int, h: int, window_width: int = None, min_w: int = None, min_h: int = None):
    width = window_width or _viewport_width
    sw = scale_value(w, width)
    sh = scale_value(h, width)
    if min_w is not None:
        sw = max(min_w, sw)
    if min_h is not None:
        sh = max(min_h, sh)
    return sw, sh


def grid_columns(content_width: int, card_min_width: int = 240, max_cols: int = 5) -> int:
    if content_width <= 0:
        return 2
    cols = content_width // card_min_width
    return max(1, min(max_cols, cols))


def setup_high_dpi():
    """在创建 QApplication 之前调用"""
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def initial_window_geometry(app: QApplication = None, ratio: float = 0.86):
    """
    根据主屏幕可用区域计算初始窗口大小与居中位置。
    返回 (width, height, x, y)
    """
    app = app or QApplication.instance()
    if app is None:
        return 1280, 800, 100, 80

    screen = app.primaryScreen()
    if screen is None:
        return 1280, 800, 100, 80

    avail = screen.availableGeometry()
    min_w, min_h = 960, 640
    max_w, max_h = 1680, 1050

    w = int(avail.width() * ratio)
    h = int(avail.height() * ratio)
    w = max(min_w, min(w, max_w, avail.width() - 40))
    h = max(min_h, min(h, max_h, avail.height() - 40))

    x = avail.x() + max(0, (avail.width() - w) // 2)
    y = avail.y() + max(0, (avail.height() - h) // 2)
    return w, h, x, y


def fit_pixmap_size(pix_w: int, pix_h: int, max_w: int, max_h: int) -> QSize:
    if pix_w <= 0 or pix_h <= 0:
        return QSize(max_w, max_h)
    scale = min(max_w / pix_w, max_h / pix_h, 1.0)
    return QSize(max(1, int(pix_w * scale)), max(1, int(pix_h * scale)))
