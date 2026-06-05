"""
food_story_page.py - 美食故事集（探访 + 用户收集）
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QTextEdit, QMessageBox, QTabWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style
from frontend.widgets.food_story_card import FoodStoryCard


class FoodStoryPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self, story_manager, parent=None):
        super().__init__(parent)
        self.stories = story_manager
        self.setup_ui()
        self.refresh_lists()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 8)
        back = QPushButton("← 返回")
        back.setFont(get_font(11))
        back.clicked.connect(self.go_back.emit)
        header.addWidget(back)

        title = QLabel("美食故事")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header.addWidget(title)
        header.addStretch()
        main.addLayout(header)

        tabs = QTabWidget()
        tabs.setFont(get_font(11))

        explore = QWidget()
        ex_layout = QVBoxLayout(explore)
        ex_hint = QLabel("燕园食事与你的美食记忆，同等珍藏")
        ex_hint.setFont(get_font(10))
        ex_hint.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 4px 0;")
        ex_layout.addWidget(ex_hint)

        ex_scroll = QScrollArea()
        ex_scroll.setWidgetResizable(True)
        ex_scroll.setStyleSheet("border: none;")
        self.explore_host = QWidget()
        self.explore_layout = QVBoxLayout(self.explore_host)
        self.explore_layout.setSpacing(14)
        self.explore_layout.setContentsMargins(8, 8, 8, 16)
        ex_scroll.setWidget(self.explore_host)
        ex_layout.addWidget(ex_scroll)
        tabs.addTab(explore, "故事探访")

        collect = QWidget()
        col_layout = QVBoxLayout(collect)
        col_layout.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("故事标题，如：期末周的那碗面")
        self.title_input.setFont(get_font(11))
        col_layout.addWidget(self.title_input)

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("写下你的美食故事（200字左右为佳）…")
        self.body_input.setFont(get_font(11))
        self.body_input.setMaximumHeight(140)
        col_layout.addWidget(self.body_input)

        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("可选：相关链接")
        self.link_input.setFont(get_font(10))
        col_layout.addWidget(self.link_input)

        save_btn = QPushButton("保存我的故事")
        save_btn.setFont(get_font(11, bold=True))
        save_btn.setStyleSheet(get_button_style("primary", radius=10))
        save_btn.clicked.connect(self._save_story)
        col_layout.addWidget(save_btn)

        col_scroll = QScrollArea()
        col_scroll.setWidgetResizable(True)
        col_scroll.setStyleSheet("border: none;")
        self.user_host = QWidget()
        self.user_layout = QVBoxLayout(self.user_host)
        self.user_layout.setSpacing(12)
        col_scroll.setWidget(self.user_host)
        col_layout.addWidget(col_scroll, 1)
        tabs.addTab(collect, "我的收集")

        main.addWidget(tabs)

    def refresh_lists(self):
        while self.explore_layout.count():
            item = self.explore_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while self.user_layout.count():
            item = self.user_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_stories = self.stories.all_stories()
        if not all_stories:
            self.explore_layout.addWidget(QLabel("暂无故事"))
            return

        for story in all_stories:
            card = FoodStoryCard(story, compact=False)
            self.explore_layout.addWidget(card)

        user_only = [s for s in all_stories if s.get("source") == "user"]
        if not user_only:
            hint = QLabel("你还没有写下自己的故事~")
            hint.setFont(get_font(10))
            hint.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            self.user_layout.addWidget(hint)
        else:
            for story in user_only:
                row = QHBoxLayout()
                card = FoodStoryCard(story, compact=True)
                row_w = QWidget()
                row_w.setLayout(row)
                row.addWidget(card, 1)
                del_btn = QPushButton("删除")
                del_btn.setFont(get_font(9))
                del_btn.clicked.connect(lambda checked, sid=story["story_id"]: self._delete(sid))
                row.addWidget(del_btn)
                self.user_layout.addWidget(row_w)

        self.explore_layout.addStretch()

    def _save_story(self):
        title = self.title_input.text().strip()
        body = self.body_input.toPlainText().strip()
        if not title or not body:
            QMessageBox.warning(self, "提示", "请填写标题和故事内容")
            return
        self.stories.add_user_story(title, body, link=self.link_input.text().strip())
        self.title_input.clear()
        self.body_input.clear()
        self.link_input.clear()
        QMessageBox.information(self, "已保存", "你的美食故事已加入故事集！")
        self.refresh_lists()

    def _delete(self, story_id: str):
        self.stories.delete_user_story(story_id)
        self.refresh_lists()

    def refresh(self):
        self.refresh_lists()
