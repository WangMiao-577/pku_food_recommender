"""
footprint_page.py - 一周美食足迹详情与收藏
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha

MOOD_LABELS = {"good": "开心", "bad": "低落", "neutral": "一般"}
COMP_LABELS = {"alone": "独自", "friends": "和朋友"}


class FootprintRecordCard(QFrame):
    favorite_changed = pyqtSignal(str, object)

    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.record = record
        self.setup_ui()

    def setup_ui(self):
        r = self.record
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        info = QVBoxLayout()
        title = QLabel(r["dish_name"])
        title.setFont(get_font(13, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        info.addWidget(title)

        meta = QLabel(
            f"{r['canteen']} · {r.get('cuisine', '')} · "
            f"{MOOD_LABELS.get(r.get('mood'), '一般')} · "
            f"{COMP_LABELS.get(r.get('companions'), '独自')}"
        )
        meta.setFont(get_font(10))
        meta.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        info.addWidget(meta)

        try:
            t = datetime.fromisoformat(r["time"]).strftime("%m月%d日 %H:%M")
        except Exception:
            t = r.get("time", "")[:16]
        time_lbl = QLabel(t)
        time_lbl.setFont(get_font(9))
        time_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        info.addWidget(time_lbl)
        layout.addLayout(info, 1)

        fav = r.get("favorite")
        temp_btn = QPushButton("☆ 暂藏" if fav != "temp" else "★ 已暂藏")
        temp_btn.setFont(get_font(9))
        temp_btn.setCursor(Qt.PointingHandCursor)
        temp_btn.clicked.connect(lambda: self._toggle("temp"))
        layout.addWidget(temp_btn)

        perm_btn = QPushButton("♥ 珍藏" if fav != "perm" else "♥ 已珍藏")
        perm_btn.setFont(get_font(9))
        perm_btn.setCursor(Qt.PointingHandCursor)
        perm_btn.setStyleSheet(get_button_style("secondary", radius=8))
        perm_btn.clicked.connect(lambda: self._toggle("perm"))
        layout.addWidget(perm_btn)

        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
            }}
        """)

    def _toggle(self, level: str):
        cur = self.record.get("favorite")
        new = None if cur == level else level
        self.favorite_changed.emit(self.record["id"], new)


class FootprintPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self, footprint_mgr, parent=None):
        super().__init__(parent)
        self.fp = footprint_mgr
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 8)
        back = QPushButton("← 返回")
        back.setFont(get_font(11))
        back.clicked.connect(self.go_back.emit)
        header.addWidget(back)

        title = QLabel("美食足迹 · 近一周")
        title.setFont(get_font(18, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header.addWidget(title)
        header.addStretch()
        main.addLayout(header)

        self.summary = QLabel()
        self.summary.setFont(get_font(11))
        self.summary.setStyleSheet(f"""
            color: {COLORS['text_medium'].name()};
            background: {color_with_alpha(COLORS['accent_sky'], 40)};
            border-radius: 10px;
            padding: 12px 16px;
            margin: 0 20px;
        """)
        self.summary.setWordWrap(True)
        main.addWidget(self.summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(20, 8, 20, 20)
        scroll.setWidget(self.container)
        main.addWidget(scroll, 1)

        fav_title = QLabel("永久珍藏")
        fav_title.setFont(get_font(12, bold=True))
        fav_title.setStyleSheet(f"color: {COLORS['secondary_dark'].name()}; padding: 8px 20px 0;")
        main.addWidget(fav_title)

        self.fav_lbl = QLabel()
        self.fav_lbl.setFont(get_font(10))
        self.fav_lbl.setWordWrap(True)
        self.fav_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 4px 20px 16px;")
        main.addWidget(self.fav_lbl)

    def refresh(self):
        stats = self.fp.get_week_stats()
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not stats.get("has_data"):
            self.summary.setText("这一周还没有足迹记录。下次点击「去吃」时会自动记下~")
            self.fav_lbl.setText("暂无珍藏")
            return

        self.summary.setText(
            f"你在 {stats['canteen_count']} 个食堂用餐 {stats['meal_count']} 次，"
            f"尝过 {stats['cuisine_count']} 种菜系；"
            f"独自 {stats['alone_count']} 次，和朋友 {stats['friends_count']} 次。"
        )

        for rec in stats["records"]:
            card = FootprintRecordCard(rec)
            card.favorite_changed.connect(self._on_favorite)
            self.list_layout.addWidget(card)
        self.list_layout.addStretch()

        favs = self.fp.get_favorites()
        if favs:
            lines = [f"♥ {f['dish_name']}（{f['canteen']}）" for f in favs[:8]]
            self.fav_lbl.setText(" · ".join(lines))
        else:
            self.fav_lbl.setText("点击「暂藏」保留一周，点击「珍藏」永久保存")

    def _on_favorite(self, record_id: str, level):
        self.fp.set_favorite(record_id, level)
        self.refresh()
