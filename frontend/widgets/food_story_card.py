"""
food_story_card.py - 可复用美食故事消息卡片
"""

import os
import webbrowser

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QTextEdit,
)
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "images")


def _placeholder_pixmap(w: int, h: int, title: str = "🍜") -> QPixmap:
    pix = QPixmap(w, h)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0, QColor("#E8D5B5"))
    grad.setColorAt(0.5, QColor("#C9A87C"))
    grad.setColorAt(1, QColor("#8B6F47"))
    painter.fillRect(0, 0, w, h, grad)
    painter.setPen(QColor("#FFF8F0"))
    painter.setFont(get_font(28, bold=True))
    painter.drawText(pix.rect(), Qt.AlignCenter, title[:4])
    painter.end()
    return pix


class FoodStoryCard(QFrame):
    """美食故事展示卡（预设与用户故事通用）"""

    open_link = pyqtSignal(str)

    def __init__(self, story: dict, compact: bool = False, parent=None):
        super().__init__(parent)
        self.story = story
        self.compact = compact
        self.setup_ui()

    def setup_ui(self):
        story = self.story
        bg = story.get("card_bg", "#F7F2EA")
        if story.get("source") == "user":
            bg = "#F0F5F2"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(20)

        img_lbl = QLabel()
        img_size = (240, 180) if self.compact else (240, 180)
        img_lbl.setFixedSize(*img_size)
        img_lbl.setScaledContents(True)

        img_name = story.get("image", "")
        img_path = os.path.join(IMAGES_DIR, img_name) if img_name else ""
        if img_path and os.path.exists(img_path):
            pix = QPixmap(img_path).scaled(*img_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else:
            emoji = "🍜" if "面" in story.get("title", "") else "📖"
            pix = _placeholder_pixmap(*img_size, emoji)
        img_lbl.setPixmap(pix)
        img_lbl.setStyleSheet("border-radius: 10px;")
        layout.addWidget(img_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)

        tag_row = QHBoxLayout()
        tag = QLabel(story.get("tag") or ("我的故事" if story.get("source") == "user" else "燕园食事"))
        tag.setFont(get_font(9, bold=True))
        tag.setStyleSheet(f"""
            color: {COLORS['secondary_dark'].name()};
            background: {color_with_alpha(COLORS['accent_sage'], 60)};
            border-radius: 8px;
            padding: 2px 8px;
        """)
        tag_row.addWidget(tag)
        if story.get("author"):
            author = QLabel(story["author"])
            author.setFont(get_font(9))
            author.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            tag_row.addWidget(author)
        tag_row.addStretch()
        text_col.addLayout(tag_row)

        title = QLabel(story.get("title", "美食故事"))
        title.setFont(get_font(13 if self.compact else 15, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        title.setWordWrap(True)
        text_col.addWidget(title)

        summary = story.get("summary", "")
        sum_view = QTextEdit()
        sum_view.setReadOnly(True)
        sum_view.setPlainText(summary)
        sum_view.setFont(get_font(10 if self.compact else 11))
        sum_view.setFrameShape(QFrame.NoFrame)
        sum_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sum_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sum_view.setLineWrapMode(QTextEdit.WidgetWidth)
        sum_view.setMaximumHeight(250 if self.compact else 200)
        sum_view.setStyleSheet(f"""
            QTextEdit {{
                color: {COLORS['text_medium'].name()};
                background: transparent;
                border: none;
                padding: 0;
            }}
        """)
        text_col.addWidget(sum_view)

        btn_row = QHBoxLayout()
        link = story.get("link", "")
        if link:
            link_btn = QPushButton("阅读原文 →")
            link_btn.setFont(get_font(10, bold=True))
            link_btn.setCursor(Qt.PointingHandCursor)
            link_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['primary'].name()};
                    border: none;
                    text-align: left;
                    padding: 0;
                }}
                QPushButton:hover {{ color: {COLORS['primary_dark'].name()}; text-decoration: underline; }}
            """)
            link_btn.clicked.connect(lambda: self._open_link(link))
            btn_row.addWidget(link_btn)
        btn_row.addStretch()
        text_col.addLayout(btn_row)

        layout.addLayout(text_col, 1)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 16px;
            }}
        """)
        self.setMaximumHeight(320)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def _open_link(self, url: str):
        self.open_link.emit(url)
        if url:
            webbrowser.open(url)
