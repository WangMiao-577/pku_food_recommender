"""
frameless_titlebar.py - 自定义边框标题栏（左侧四季标签 + 右侧窗口控制）
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject
from frontend.watercolor_style import COLORS, get_font, color_with_alpha


class FramelessTitleBar(QWidget):
    """自定义标题栏：左侧四季标签，右侧全屏/最小化/关闭，整条可拖动"""

    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    fullscreen_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start: QPoint = None
        self._window = None
        self.setFixedHeight(36)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 10, 4)
        layout.setSpacing(8)

        self.season_lbl = QLabel()
        self.season_lbl.setFont(get_font(10, bold=True))
        layout.addWidget(self.season_lbl)

        self.title_lbl = QLabel("今天吃什么？")
        self.title_lbl.setFont(get_font(10))
        layout.addWidget(self.title_lbl)

        layout.addStretch()

        self.full_btn = QPushButton("⛶")
        self.min_btn = QPushButton("—")
        self.close_btn = QPushButton("✕")
        for btn in (self.full_btn, self.min_btn, self.close_btn):
            btn.setFixedSize(32, 26)
            btn.setFont(QFont("Segoe UI", 11))
            btn.setCursor(Qt.PointingHandCursor)

        self.full_btn.setToolTip("全屏")
        self.min_btn.setToolTip("最小化")
        self.close_btn.setToolTip("关闭")

        self.full_btn.clicked.connect(self.fullscreen_clicked.emit)
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        self.close_btn.clicked.connect(self.close_clicked.emit)

        layout.addWidget(self.full_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)

        self._apply_style()

    def bind_window(self, window):
        self._window = window

    def set_season_label(self, text: str):
        self.season_lbl.setText(text)

    def update_fullscreen_button(self, is_fullscreen: bool):
        self.full_btn.setText("❐" if is_fullscreen else "⛶")
        self.full_btn.setToolTip("退出全屏" if is_fullscreen else "全屏")

    def _apply_style(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS.get('header_overlay', color_with_alpha(COLORS['bg_card'], 220))};
                border-bottom: 1px solid {COLORS['border_light'].name()};
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }}
        """)
        self.season_lbl.setStyleSheet(f"color: {COLORS['primary'].name()}; font-weight: bold;")
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        self.full_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color_with_alpha(COLORS['accent_sky'], 80)};
                color: {COLORS['text_dark'].name()};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: {COLORS['accent_sky'].lighter(120).name()}; }}
        """)
        self.min_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color_with_alpha(COLORS['accent_sky'], 80)};
                color: {COLORS['text_dark'].name()};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: {COLORS['accent_sky'].lighter(120).name()}; }}
        """)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color_with_alpha(COLORS['primary_light'], 90)};
                color: {COLORS['primary_dark'].name()};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_light'].lighter(115).name()};
                color: {COLORS['primary_dark'].name()};
            }}
        """)

    def refresh_theme(self):
        self._apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._window and not self._window.isFullScreen():
            self._drag_start = event.globalPos() - self._window.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start is not None and event.buttons() & Qt.LeftButton and self._window:
            if not self._window.isFullScreen():
                self._window.move(event.globalPos() - self._drag_start)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        super().mouseReleaseEvent(event)


class WindowDragFilter(QObject):
    """为空白区域（页眉等）启用拖动"""

    def __init__(self, window):
        super().__init__()
        self._window = window
        self._origin = None

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if self._window.isFullScreen():
            return False
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            if self._is_draggable(obj, event.pos()):
                self._origin = event.globalPos() - self._window.frameGeometry().topLeft()
                return False
        if event.type() == QEvent.MouseMove and self._origin and event.buttons() & Qt.LeftButton:
            if self._is_draggable(obj, event.pos()):
                self._window.move(event.globalPos() - self._origin)
                return True
        if event.type() == QEvent.MouseButtonRelease:
            self._origin = None
        return False

    @staticmethod
    def _is_draggable(widget, pos):
        child = widget.childAt(pos)
        if child is None:
            return True
        from PyQt5.QtWidgets import QPushButton, QLineEdit, QComboBox, QSpinBox
        if isinstance(child, (QPushButton, QLineEdit, QComboBox, QSpinBox)):
            return False
        return child.__class__.__name__ in ("QLabel", "QWidget", "QFrame", "PoemLabel")
