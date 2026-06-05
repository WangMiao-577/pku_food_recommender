"""
footprint_dialog.py - 美食足迹周报弹窗（渐显/切换动效）
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QWidget, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha


class FadeSlidePage(QWidget):
    """单页统计内容，支持淡入"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)

    def fade_in(self, duration=450):
        anim = QPropertyAnimation(self.effect, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._anim = anim


class FootprintWeeklyDialog(QDialog):
    """上一周美食足迹摘要（分步动效展示）"""

    view_footprint = pyqtSignal()

    def __init__(self, stats: dict, parent=None):
        super().__init__(parent)
        self.stats = stats
        self._step = 0
        self.setWindowTitle("美食足迹 · 这一周")
        self.setMinimumSize(480, 380)
        self.setModal(True)
        self.setup_ui()
        QTimer.singleShot(200, lambda: self._show_page(0))
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._auto_advance)
        self._auto_timer.start(3800)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QLabel("🍽 美食足迹")
        header.setFont(get_font(20, bold=True))
        header.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        hint = QLabel("这一周，你和燕园食堂的故事")
        hint.setFont(get_font(11))
        hint.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        self.stack = QStackedWidget()
        self.stack.setMinimumHeight(200)
        layout.addWidget(self.stack, 1)

        self._build_pages()
        self._build_dots(layout)

        btn_row = QHBoxLayout()
        self.prev_btn = QPushButton("上一条")
        self.prev_btn.setFont(get_font(10))
        self.prev_btn.clicked.connect(self._show_prev)
        btn_row.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一条")
        self.next_btn.setFont(get_font(10, bold=True))
        self.next_btn.setStyleSheet(get_button_style("secondary", radius=10))
        self.next_btn.clicked.connect(self._show_next)
        btn_row.addWidget(self.next_btn)

        btn_row.addStretch()

        self.week_btn = QPushButton("查看一周足迹")
        self.week_btn.setFont(get_font(11, bold=True))
        self.week_btn.setMinimumHeight(40)
        self.week_btn.setCursor(Qt.PointingHandCursor)
        self.week_btn.setStyleSheet(get_button_style("primary", radius=12))
        self.week_btn.clicked.connect(self._on_view_week)
        btn_row.addWidget(self.week_btn)

        close_btn = QPushButton("知道了")
        close_btn.setFont(get_font(10))
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {COLORS['bg_warm'].name()},
                    stop:1 {COLORS['bg_card'].name()});
            }}
        """)

    def _card(self, text: str, accent: str = "primary") -> FadeSlidePage:
        page = FadeSlidePage()
        box = QFrame(page)
        vl = QVBoxLayout(page)
        vl.setContentsMargins(8, 8, 8, 8)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(20, 24, 20, 24)
        lbl = QLabel(text)
        lbl.setFont(get_font(13))
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet(f"color: {COLORS['text_dark'].name()}; line-height: 1.6;")
        inner.addWidget(lbl)
        box.setStyleSheet(f"""
            QFrame {{
                background: {color_with_alpha(COLORS[accent], 35)};
                border-radius: 16px;
                border: 1px solid {COLORS['border_light'].name()};
            }}
        """)
        vl.addWidget(box)
        return page

    def _build_pages(self):
        s = self.stats
        m, n = s.get("canteen_count", 0), s.get("meal_count", 0)
        c = s.get("cuisine_count", 0)
        alone, friends = s.get("alone_count", 0), s.get("friends_count", 0)

        self.pages_data = [
            self._card(
                f"上一周，你在 <b>{m}</b> 个食堂用餐了 <b>{n}</b> 次，\n"
                f"品尝了 <b>{c}</b> 种不同类型的菜肴。",
                "accent_sky",
            ),
            self._card(
                f"其中 <b>{friends}</b> 次是和朋友一起吃的，\n"
                f"<b>{alone}</b> 次是一个人吃的。",
                "accent_sage",
            ),
        ]

        good = s.get("good_meal")
        bad = s.get("bad_meal")
        if good:
            gtxt = (
                f"心情很好的一餐：\n"
                f"<b>{good['dish_name']}</b> @ {good['canteen']}\n"
                f"{good['time'][:10]}"
            )
            self.pages_data.append(self._card(gtxt, "accent_gold"))
        if bad:
            btxt = (
                f"心情低落时的一餐：\n"
                f"<b>{bad['dish_name']}</b> @ {bad['canteen']}\n"
                f"{bad['time'][:10]}"
            )
            enc = s.get("encouragement", "")
            if enc:
                btxt += f"\n\n<i>{enc}</i>"
            self.pages_data.append(self._card(btxt, "accent_rose"))

        if not good and not bad:
            self.pages_data.append(self._card(
                "这一周还没有记录特别的心情，\n下次吃饭时记得告诉我你的感受哦~",
                "accent_lavender",
            ))

        for p in self.pages_data:
            self.stack.addWidget(p)

        self._dots = []
        self.dot_row = None

    def _build_dots(self, layout):
        self.dot_row = QHBoxLayout()
        self.dot_row.setAlignment(Qt.AlignCenter)
        for i in range(len(self.pages_data)):
            dot = QLabel("●")
            dot.setFont(get_font(8))
            dot.setStyleSheet(f"color: {COLORS['border'].name()}; padding: 0 4px;")
            self._dots.append(dot)
            self.dot_row.addWidget(dot)
        layout.addLayout(self.dot_row)

    def _update_dots(self):
        for i, dot in enumerate(self._dots):
            active = i == self._step
            color = COLORS["primary"].name() if active else COLORS["border"].name()
            dot.setStyleSheet(f"color: {color}; padding: 0 4px;")

    def _show_page(self, index: int):
        index = max(0, min(index, len(self.pages_data) - 1))
        self._step = index
        self.stack.setCurrentIndex(index)
        page = self.pages_data[index]
        if isinstance(page, FadeSlidePage):
            page.fade_in()
        self._update_dots()
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.pages_data) - 1)

    def _auto_advance(self):
        if self._step < len(self.pages_data) - 1:
            self._show_page(self._step + 1)
        else:
            self._auto_timer.stop()

    def _show_next(self):
        if self._step < len(self.pages_data) - 1:
            self._show_page(self._step + 1)
        else:
            self._show_page(0)

    def _show_prev(self):
        if self._step > 0:
            self._show_page(self._step - 1)

    def _on_view_week(self):
        self.view_footprint.emit()
        self.accept()
