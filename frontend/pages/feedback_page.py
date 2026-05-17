"""
feedback_page.py - 评价反馈页面
用户可以查看和提交菜品评价
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QTextEdit, QSpinBox,
    QCheckBox, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style


class FeedbackPage(QWidget):
    """评价反馈页面"""

    view_dish = pyqtSignal(str)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.current_dish_id = None
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 顶部
        header = QWidget()
        header.setMaximumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("我的评价")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(title)

        subtitle = QLabel("「食不厌精，脍不厌细」")
        subtitle.setFont(get_font(11, italic=True))
        subtitle.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()
        main.addWidget(header)

        # 内容区
        content = QHBoxLayout()
        content.setSpacing(20)
        content.setContentsMargins(20, 10, 20, 20)

        # 左侧 - 评价列表
        left = QVBoxLayout()
        left_title = QLabel("最近评价")
        left_title.setFont(get_font(13, bold=True))
        left_title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        left.addWidget(left_title)

        self.reviews_list = QFrame()
        self.reviews_list_layout = QVBoxLayout(self.reviews_list)
        self.reviews_list_layout.setSpacing(8)
        self.reviews_list_layout.setContentsMargins(0, 0, 0, 0)
        self.reviews_list_layout.setAlignment(Qt.AlignTop)

        left.addWidget(self.reviews_list)
        content.addLayout(left, 1)

        # 右侧 - 评价表单
        right = QVBoxLayout()

        form_title = QLabel("写评价")
        form_title.setFont(get_font(13, bold=True))
        form_title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        right.addWidget(form_title)

        # 菜品选择
        dish_row = QHBoxLayout()
        dish_row.addWidget(QLabel("菜品:"))
        self.dish_combo = QComboBox()
        self.dish_combo.setFont(get_font(11))
        self.load_dish_options()
        dish_row.addWidget(self.dish_combo)
        right.addLayout(dish_row)

        # 评分
        rating_row = QHBoxLayout()
        rating_row.addWidget(QLabel("评分 (1-5):"))
        self.rating = QSpinBox()
        self.rating.setRange(1, 5)
        self.rating.setValue(4)
        rating_row.addWidget(self.rating)
        rating_row.addStretch()
        right.addLayout(rating_row)

        # 标签
        tags_row = QHBoxLayout()
        tags_row.addWidget(QLabel("标签:"))
        self.tag_tasty = QCheckBox("好吃推荐")
        self.tag_tasty.setFont(get_font(10))
        self.tag_too_oily = QCheckBox("太油")
        self.tag_too_oily.setFont(get_font(10))
        self.tag_too_salty = QCheckBox("太咸")
        self.tag_too_salty.setFont(get_font(10))
        self.tag_too_spicy = QCheckBox("太辣")
        self.tag_too_spicy.setFont(get_font(10))
        self.tag_small = QCheckBox("量少")
        self.tag_small.setFont(get_font(10))
        tags_row.addWidget(self.tag_tasty)
        tags_row.addWidget(self.tag_too_oily)
        tags_row.addWidget(self.tag_too_salty)
        tags_row.addWidget(self.tag_too_spicy)
        tags_row.addWidget(self.tag_small)
        tags_row.addStretch()
        right.addLayout(tags_row)

        # 评论
        comment_label = QLabel("详细评价:")
        comment_label.setFont(get_font(11))
        right.addWidget(comment_label)

        self.comment = QTextEdit()
        self.comment.setFont(get_font(11))
        self.comment.setPlaceholderText("写下你的用餐体验...（可选）")
        self.comment.setMaximumHeight(100)
        self.comment.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border'].name()};
                border-radius: 8px;
                padding: 8px;
                color: {COLORS['text_dark'].name()};
            }}
        """)
        right.addWidget(self.comment)

        # 提交按钮
        submit_btn = QPushButton("提交评价 ⭐")
        submit_btn.setFont(get_font(12, bold=True))
        submit_btn.setMinimumHeight(40)
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setStyleSheet(get_button_style("primary"))
        submit_btn.clicked.connect(self.on_submit)
        right.addWidget(submit_btn)

        right.addStretch()
        content.addLayout(right, 1)

        main.addLayout(content)

        # 加载已有评价
        self.load_reviews()

    def load_dish_options(self):
        """加载菜品选项"""
        self.dish_combo.clear()
        for dish in self.dm.get_all_dishes():
            self.dish_combo.addItem(f"{dish['name']} ({dish['canteen']})", dish["id"])

    def load_reviews(self):
        """加载评价列表"""
        # 清除
        while self.reviews_list_layout.count():
            item = self.reviews_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        reviews = self.dm.get_recent_reviews(20)

        if not reviews:
            empty = QLabel("还没有评价，写下第一条吧！「唯爱与美食不可辜负」")
            empty.setFont(get_font(11, italic=True))
            empty.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 20px;")
            self.reviews_list_layout.addWidget(empty)
            return

        for review in reviews:
            dish = self.dm.get_dish_by_id(review["dish_id"])
            dish_name = dish["name"] if dish else "未知菜品"

            card = QFrame()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(4)

            # 标题行
            title_row = QHBoxLayout()
            name_lbl = QLabel(f"{dish_name}")
            name_lbl.setFont(get_font(11, bold=True))
            name_lbl.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
            title_row.addWidget(name_lbl)
            title_row.addStretch()

            stars = "⭐" * review["rating"] + "☆" * (5 - review["rating"])
            stars_lbl = QLabel(stars)
            stars_lbl.setFont(get_font(11))
            title_row.addWidget(stars_lbl)
            card_layout.addLayout(title_row)

            # 标签
            if review.get("tags"):
                tags_lbl = QLabel(" · ".join(review["tags"]))
                tags_lbl.setFont(get_font(9))
                tags_lbl.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
                card_layout.addWidget(tags_lbl)

            # 评论
            if review.get("comment"):
                comment_lbl = QLabel(review["comment"])
                comment_lbl.setFont(get_font(10))
                comment_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
                comment_lbl.setWordWrap(True)
                card_layout.addWidget(comment_lbl)

            # 时间
            time_lbl = QLabel(review.get("time", "")[:16])
            time_lbl.setFont(get_font(9))
            time_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            card_layout.addWidget(time_lbl)

            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card'].name()};
                    border: 1px solid {COLORS['border_light'].name()};
                    border-radius: 10px;
                }}
            """)

            self.reviews_list_layout.addWidget(card)

    def on_submit(self):
        """提交评价"""
        dish_id = self.dish_combo.currentData()
        rating = self.rating.value()

        tags = []
        if self.tag_tasty.isChecked():
            tags.append("好吃推荐")
        if self.tag_too_oily.isChecked():
            tags.append("太油")
        if self.tag_too_salty.isChecked():
            tags.append("太咸")
        if self.tag_too_spicy.isChecked():
            tags.append("太辣")
        if self.tag_small.isChecked():
            tags.append("量少")

        comment = self.comment.toPlainText().strip()

        self.dm.add_review(dish_id, rating, tags if tags else None, comment)

        QMessageBox.information(self, "评价提交", "感谢你的评价！你的反馈将帮助我们做得更好。")

        # 重置表单
        self.rating.setValue(4)
        self.tag_tasty.setChecked(False)
        self.tag_too_oily.setChecked(False)
        self.tag_too_salty.setChecked(False)
        self.tag_too_spicy.setChecked(False)
        self.tag_small.setChecked(False)
        self.comment.clear()

        # 刷新列表
        self.load_reviews()

    def refresh(self):
        self.load_dish_options()
        self.load_reviews()


from PyQt5.QtWidgets import QComboBox
