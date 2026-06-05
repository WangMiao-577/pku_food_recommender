"""
food_story_panel.py - 主页美食故事面板（随机展示 + 入口）
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import (
    COLORS, get_font, get_button_style, get_card_style, POEMS, CANTEEN_TAGS
)
from frontend.widgets.food_story_card import FoodStoryCard


class FoodStoryPanel(QFrame):
    """主页故事卡：与今日推荐上下并列"""

    open_stories = pyqtSignal()
    story_link = pyqtSignal(str)

    def __init__(self, story_manager, parent=None):
        super().__init__(parent)
        self.stories = story_manager
        self._current = None
        self.setup_ui()
        self.show_random()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("美食故事")
        title.setFont(get_font(16, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header.addWidget(title)

        sub = QLabel("燕园食事 · 人间烟火")
        sub.setFont(get_font(9))
        sub.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header.addWidget(sub)
        header.addStretch()

        self.shuffle_btn = QPushButton("换一个")
        self.shuffle_btn.setFixedSize(200, 50)
        self.shuffle_btn.setFont(get_font(20, bold=True))
        self.shuffle_btn.setCursor(Qt.PointingHandCursor)
        self.shuffle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["secondary"].name()};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["secondary"].lighter(120).name()};
            }}
        """)
        self.shuffle_btn.clicked.connect(self.show_random)
        header.addWidget(self.shuffle_btn)

        self.more_btn = QPushButton("故事集")
        self.more_btn.setFixedSize(200, 50)
        self.more_btn.setFont(get_font(20, bold=True))
        self.more_btn.setCursor(Qt.PointingHandCursor)
        self.more_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["primary"].name()};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["primary"].lighter(120).name()};
            }}
        """)
        self.more_btn.clicked.connect(self.open_stories.emit)
        header.addWidget(self.more_btn)
        layout.addLayout(header)

        self.card_host = QVBoxLayout()
        layout.addLayout(self.card_host)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 14px;
            }}
        """)
        self.setMaximumHeight(400)

    def _clear_card(self):
        while self.card_host.count():
            item = self.card_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_random(self):
        self._clear_card()
        story = self.stories.random_story()
        if not story:
            empty = QLabel("暂无故事，去「故事集」写下你的第一条美食记忆吧~")
            empty.setFont(get_font(10))
            empty.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            empty.setWordWrap(True)
            self.card_host.addWidget(empty)
            return
        self._current = story
        card = FoodStoryCard(story, compact=True)
        card.open_link.connect(self.story_link.emit)
        self.card_host.addWidget(card)

    def refresh(self):
        self.show_random()
