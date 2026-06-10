"""
food_story_card.py - 可复用美食故事消息卡片
"""

import os
import webbrowser

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QTextEdit,QWidget
)
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha

from backend.paths import resolve_story_image

DEFAULT_STORY_LINK = "https://cyzx.pku.edu.cn/"
DEFAULT_STORY_LINK_LABEL = "逛逛餐饮中心"


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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(16)

        img_lbl = QLabel()
        img_size = (160, 120) if self.compact else (240, 180)
        img_lbl.setFixedSize(*img_size)
        img_lbl.setScaledContents(True)

        img_name = story.get("image", "")
        img_path = resolve_story_image(img_name) if img_name else None
        if img_path:
            pix = QPixmap(str(img_path)).scaled(*img_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else:
            emoji = "🍜" if "面" in story.get("title", "") else "📖"
            pix = _placeholder_pixmap(*img_size, emoji)
        img_lbl.setPixmap(pix)
        img_lbl.setStyleSheet("border-radius: 10px;")
        layout.addWidget(img_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.setContentsMargins(0, 0, 0, 0)

        tag_row = QHBoxLayout()
        tag_row.setSpacing(6)
        tag_row.setAlignment(Qt.AlignVCenter)

        tag_text = story.get("tag") or ("我的故事" if story.get("source") == "user" else "燕园食事")
        tag = QLabel(tag_text)
        tag.setFont(get_font(8, bold=True))
        tag.setFixedHeight(20)
        tag.setAlignment(Qt.AlignCenter)
        tag.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        tag.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['secondary_dark'].name()};
                background: {color_with_alpha(COLORS['accent_sage'], 60)};
                border-radius: 6px;
                padding: 0px 7px;
            }}
        """)
        tag_row.addWidget(tag)
        if story.get("author"):
            author = QLabel(story["author"])
            author.setFont(get_font(8))
            author.setFixedHeight(20)
            author.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            author.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 0;")
            tag_row.addWidget(author)
        tag_row.addStretch()
        text_col.addLayout(tag_row)

        title = QLabel(story.get("title", "美食故事"))
        title.setFont(get_font(13 if self.compact else 15, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        title.setWordWrap(True)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_col.addWidget(title)

        summary = story.get("summary", "")
        if self.compact:
            sum_view = QLabel(summary)
            sum_view.setFont(get_font(10))
            sum_view.setWordWrap(True)
            sum_view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            sum_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            sum_view.setMaximumHeight(110)
            sum_view.setStyleSheet(f"""
                color: {COLORS['text_medium'].name()};
                background: transparent;
                padding: 0;
            """)
        else:
            sum_view = QTextEdit()
            sum_view.setReadOnly(True)
            sum_view.setPlainText(summary)
            sum_view.setFont(get_font(11))
            sum_view.setFrameShape(QFrame.NoFrame)
            sum_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            sum_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sum_view.setLineWrapMode(QTextEdit.WidgetWidth)
            sum_view.setMaximumHeight(200)
            sum_view.setStyleSheet(f"""
                QTextEdit {{
                    color: {COLORS['text_medium'].name()};
                    background: transparent;
                    border: none;
                    padding: 0;
                }}
            """)
        text_col.addWidget(sum_view, 1)

        btn_row = QHBoxLayout()
        link = (story.get("link") or "").strip()
        if link:
            link_label = "阅读原文 →"
        else:
            link = DEFAULT_STORY_LINK
            link_label = DEFAULT_STORY_LINK_LABEL
        link_btn = QPushButton(link_label)
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
            QPushButton:hover {{ color: {COLORS['primary_light'].name()}; text-decoration: underline; }}
        """)
        link_btn.clicked.connect(lambda: self._open_link(link))
        btn_row.addWidget(link_btn)
        btn_row.addStretch()
        text_col.addLayout(btn_row)

        text_widget = QWidget()
        text_widget.setLayout(text_col)
        text_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(text_widget, 1)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 16px;
            }}
        """)
        self.setMaximumHeight(280 if self.compact else 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

    def _open_link(self, url: str):
        self.open_link.emit(url)
        if url:
            webbrowser.open(url)
