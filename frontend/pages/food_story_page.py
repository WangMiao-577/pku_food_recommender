"""
food_story_page.py - 美食故事集（探访 + 用户收集）
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QTextEdit, QMessageBox, QTabWidget,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, get_outline_button_style
from frontend.widgets.food_story_card import FoodStoryCard
from frontend.dialogs.story_image_dialog import StoryImageDialog
from backend.paths import resolve_story_image


class FoodStoryPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self, story_manager, parent=None):
        super().__init__(parent)
        self.stories = story_manager
        self._pending_image = ""
        self._editing_id = ""
        self.setup_ui()
        self.refresh_lists()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 8)
        back = QPushButton("← 返回")
        back.setFont(get_font(11))
        back.setStyleSheet(get_outline_button_style("secondary", radius=8))
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

        img_row = QHBoxLayout()
        self.image_preview = QLabel("未选择配图")
        self.image_preview.setFixedSize(72, 54)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setScaledContents(True)
        self.image_preview.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['bg_warm'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 8px;
                color: {COLORS['text_light'].name()};
                font-size: 9px;
            }}
        """)
        img_row.addWidget(self.image_preview)

        self.image_status = QLabel("可选：为故事添加配图")
        self.image_status.setFont(get_font(9))
        self.image_status.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        img_row.addWidget(self.image_status, 1)

        upload_btn = QPushButton("上传配图")
        upload_btn.setFont(get_font(10, bold=True))
        upload_btn.setStyleSheet(get_button_style("secondary", radius=10))
        upload_btn.clicked.connect(self._open_image_dialog)
        img_row.addWidget(upload_btn)
        col_layout.addLayout(img_row)

        form_btn_row = QHBoxLayout()
        self.cancel_edit_btn = QPushButton("取消编辑")
        self.cancel_edit_btn.setFont(get_font(10))
        self.cancel_edit_btn.setStyleSheet(get_outline_button_style("secondary", radius=8))
        self.cancel_edit_btn.setVisible(False)
        self.cancel_edit_btn.clicked.connect(self._cancel_edit)
        form_btn_row.addWidget(self.cancel_edit_btn)
        form_btn_row.addStretch()
        self.save_btn = QPushButton("保存我的故事")
        self.save_btn.setFont(get_font(11, bold=True))
        self.save_btn.setStyleSheet(get_button_style("primary", radius=10))
        self.save_btn.clicked.connect(self._save_story)
        form_btn_row.addWidget(self.save_btn)
        col_layout.addLayout(form_btn_row)

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
                edit_btn = QPushButton("编辑")
                edit_btn.setFont(get_font(9))
                edit_btn.setStyleSheet(get_outline_button_style("secondary", radius=6))
                edit_btn.clicked.connect(lambda checked, s=story: self._start_edit(s))
                row.addWidget(edit_btn)
                del_btn = QPushButton("删除")
                del_btn.setFont(get_font(9))
                del_btn.setStyleSheet(get_outline_button_style("primary", radius=6))
                del_btn.clicked.connect(lambda checked, sid=story["story_id"]: self._delete(sid))
                row.addWidget(del_btn)
                self.user_layout.addWidget(row_w)

        self.explore_layout.addStretch()

    def _open_image_dialog(self):
        dlg = StoryImageDialog(self, self._pending_image)
        if dlg.exec_():
            self._pending_image = dlg.selected_image()
            self._update_image_preview()

    def _update_image_preview(self):
        if not self._pending_image:
            self.image_preview.clear()
            self.image_preview.setText("未选择")
            self.image_status.setText("可选：为故事添加配图")
            return
        path = resolve_story_image(self._pending_image)
        if path:
            pix = QPixmap(str(path))
            if not pix.isNull():
                self.image_preview.setPixmap(
                    pix.scaled(72, 54, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                )
                self.image_preview.setText("")
        self.image_status.setText(f"已选配图：{self._pending_image}")

    def _clear_form(self):
        self.title_input.clear()
        self.body_input.clear()
        self.link_input.clear()
        self._pending_image = ""
        self._editing_id = ""
        self.save_btn.setText("保存我的故事")
        self.cancel_edit_btn.setVisible(False)
        self._update_image_preview()

    def _start_edit(self, story: dict):
        self._editing_id = story.get("story_id", "")
        self.title_input.setText(story.get("title", ""))
        self.body_input.setPlainText(story.get("summary", ""))
        self.link_input.setText(story.get("link", ""))
        self._pending_image = story.get("image", "")
        self._update_image_preview()
        self.save_btn.setText("保存修改")
        self.cancel_edit_btn.setVisible(True)
        self.title_input.setFocus()

    def _cancel_edit(self):
        self._clear_form()

    def _save_story(self):
        title = self.title_input.text().strip()
        body = self.body_input.toPlainText().strip()
        if not title or not body:
            QMessageBox.warning(self, "提示", "请填写标题和故事内容")
            return
        if self._editing_id:
            updated = self.stories.update_user_story(
                self._editing_id,
                title, body,
                image=self._pending_image,
                link=self.link_input.text().strip(),
            )
            if not updated:
                QMessageBox.warning(self, "提示", "故事不存在或已被删除")
                self._clear_form()
                self.refresh_lists()
                return
            msg = "你的美食故事已更新！"
        else:
            self.stories.add_user_story(
                title, body,
                image=self._pending_image,
                link=self.link_input.text().strip(),
            )
            msg = "你的美食故事已加入故事集！"
        self._clear_form()
        QMessageBox.information(self, "已保存", msg)
        self.refresh_lists()

    def _delete(self, story_id: str):
        if self._editing_id == story_id:
            self._clear_form()
        self.stories.delete_user_story(story_id)
        self.refresh_lists()

    def refresh(self):
        self.refresh_lists()
