"""
edge_resize.py - 无边框窗口边缘拖拽缩放
"""

from PyQt5.QtCore import QObject, Qt, QRect, QPoint
from PyQt5.QtWidgets import QWidget


class _ResizeGrip(QWidget):
    """窗口边缘/角落的透明拖拽热区"""

    _CURSORS = {
        "top": Qt.SizeVerCursor,
        "bottom": Qt.SizeVerCursor,
        "left": Qt.SizeHorCursor,
        "right": Qt.SizeHorCursor,
        "top_left": Qt.SizeFDiagCursor,
        "top_right": Qt.SizeBDiagCursor,
        "bottom_left": Qt.SizeBDiagCursor,
        "bottom_right": Qt.SizeFDiagCursor,
    }

    def __init__(self, window, edge_key: str, controller: "FramelessResizeController"):
        super().__init__(window)
        self._window = window
        self._edge_key = edge_key
        self._controller = controller
        self.setCursor(self._CURSORS[edge_key])
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._window.isFullScreen():
            self._controller.begin_resize(self._edge_key, event.globalPos())
            self.grabMouse()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._controller.is_resizing():
            self._controller.update_resize(event.globalPos())
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._controller.is_resizing():
            self._controller.end_resize()
            self.releaseMouse()
            event.accept()
        super().mouseReleaseEvent(event)


class FramelessResizeController(QObject):
    """管理无边框窗口八向边缘缩放"""

    MARGIN = 10

    def __init__(self, window: QWidget, host: QWidget = None):
        super().__init__(window)
        self._window = window
        self._host = host or window
        self._edge_key = None
        self._origin = None
        self._geom = None
        self._grips = []
        self._create_grips()

    def _create_grips(self):
        for key in (
            "top", "bottom", "left", "right",
            "top_left", "top_right", "bottom_left", "bottom_right",
        ):
            grip = _ResizeGrip(self._host, key, self)
            grip.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            grip.setAttribute(Qt.WA_NoSystemBackground, True)
            grip.setStyleSheet("background: transparent;")
            self._grips.append(grip)

    def relayout(self):
        if self._window.isFullScreen():
            for grip in self._grips:
                grip.hide()
            return

        for grip in self._grips:
            grip.show()

        m = self.MARGIN
        r = self._host.rect()
        w, h = r.width(), r.height()
        inner_w = max(0, w - 2 * m)
        inner_h = max(0, h - 2 * m)

        placements = {
            "top": (m, 0, inner_w, m),
            "bottom": (m, h - m, inner_w, m),
            "left": (0, m, m, inner_h),
            "right": (w - m, m, m, inner_h),
            "top_left": (0, 0, m, m),
            "top_right": (w - m, 0, m, m),
            "bottom_left": (0, h - m, m, m),
            "bottom_right": (w - m, h - m, m, m),
        }
        for grip in self._grips:
            x, y, gw, gh = placements[grip._edge_key]
            grip.setGeometry(x, y, gw, gh)
            grip.raise_()

    def set_enabled(self, enabled: bool):
        for grip in self._grips:
            grip.setVisible(enabled)
            grip.setEnabled(enabled)
        if enabled:
            self.relayout()

    def is_resizing(self):
        return self._edge_key is not None

    def begin_resize(self, edge_key: str, global_pos: QPoint):
        if self._window.isFullScreen():
            return
        self._edge_key = edge_key
        self._origin = global_pos
        self._geom = QRect(self._window.geometry())

    def update_resize(self, global_pos: QPoint):
        if not self._edge_key or not self._origin or not self._geom:
            return

        delta = global_pos - self._origin
        geo = QRect(self._geom)
        min_w = self._window.minimumWidth()
        min_h = self._window.minimumHeight()

        key = self._edge_key
        if "left" in key:
            new_left = geo.left() + delta.x()
            new_width = geo.right() - new_left + 1
            if new_width >= min_w:
                geo.setLeft(new_left)
        if "right" in key:
            new_width = geo.width() + delta.x()
            if new_width >= min_w:
                geo.setWidth(new_width)
        if "top" in key:
            new_top = geo.top() + delta.y()
            new_height = geo.bottom() - new_top + 1
            if new_height >= min_h:
                geo.setTop(new_top)
        if "bottom" in key:
            new_height = geo.height() + delta.y()
            if new_height >= min_h:
                geo.setHeight(new_height)

        self._window.setGeometry(geo)

    def end_resize(self):
        self._edge_key = None
        self._origin = None
        self._geom = None
