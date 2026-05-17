"""
recommendation_page.py - 推荐结果展示页面
以美观的排版展示推荐菜品，有水彩风格卡片和照片
"""

import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame, QScrollArea, QSizePolicy,
    QSpacerItem, QMessageBox
)
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha, POEMS, CANTEEN_TAGS


class DishResultCard(QFrame):
    """推荐结果菜品卡片"""

    view_clicked = pyqtSignal(str)
    eat_clicked = pyqtSignal(str)

    def __init__(self, dish, rank, parent=None):
        super().__init__(parent)
        self.dish = dish
        self.rank = rank
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(15, 12, 15, 12)
        main.setSpacing(15)

        # 排名标签
        rank_lbl = QLabel(f"#{self.rank}")
        rank_lbl.setFont(get_font(28, bold=True))
        rank_lbl.setFixedWidth(50)
        rank_lbl.setAlignment(Qt.AlignCenter)

        if self.rank == 1:
            rank_lbl.setStyleSheet("color: #D4A574;")
        elif self.rank == 2:
            rank_lbl.setStyleSheet("color: #A8B8B0;")
        elif self.rank == 3:
            rank_lbl.setStyleSheet("color: #C4A88C;")
        else:
            rank_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")

        main.addWidget(rank_lbl)

        # 菜品图片
        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(160, 120)
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setStyleSheet(f"""
            background-color: {COLORS['bg_warm'].name()};
            border-radius: 10px;
        """)

        # 加载图片
        img_path = os.path.join(os.path.dirname(__file__), "..", "..", "images",
                                self.dish.get("image", ""))
        if os.path.exists(img_path):
            self.img_lbl.setPixmap(QPixmap(img_path))
        else:
            self.img_lbl.setText("(图片)")
            self.img_lbl.setAlignment(Qt.AlignCenter)

        main.addWidget(self.img_lbl)

        # 菜品信息
        info = QVBoxLayout()
        info.setSpacing(6)

        # 名称和评分行
        title_row = QHBoxLayout()

        name = QLabel(self.dish["name"])
        name.setFont(get_font(16, bold=True))
        name.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        title_row.addWidget(name)

        # 探索标记
        if self.dish.get("_is_explore"):
            explore = QLabel("探索发现")
            explore.setFont(get_font(9))
            explore.setStyleSheet(f"""
                color: {COLORS['accent_lavender'].name()};
                background-color: {color_with_alpha(COLORS['accent_lavender'], 32)};
                border-radius: 8px;
                padding: 2px 8px;
            """)
            title_row.addWidget(explore)

        title_row.addStretch()

        # 评分
        rating = QLabel(f"⭐ {self.dish['rating']}")
        rating.setFont(get_font(12, bold=True))
        rating.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        title_row.addWidget(rating)

        info.addLayout(title_row)

        # 食堂和价格
        meta_row = QHBoxLayout()
        canteen = self.dish["canteen"]
        tag = CANTEEN_TAGS.get(canteen, canteen)
        meta = QLabel(f"{canteen} · {self.dish.get('window', '')} · ¥{self.dish['price']}")
        meta.setFont(get_font(10))
        meta.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        meta_row.addWidget(meta)
        meta_row.addStretch()

        # 出餐时间
        time_lbl = QLabel(f"⏱ {self.dish.get('prep_time', '?')}分钟")
        time_lbl.setFont(get_font(10))
        time_lbl.setStyleSheet(f"color: {COLORS['secondary'].name()};")
        meta_row.addWidget(time_lbl)

        info.addLayout(meta_row)

        # 标签
        tags = " · ".join(self.dish.get("tags", []))
        tags_lbl = QLabel(tags)
        tags_lbl.setFont(get_font(9))
        tags_lbl.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        info.addWidget(tags_lbl)

        # 推荐理由
        details = self.dish.get("_score_details", {})
        reasons = []
        if "freshness" in details:
            reasons.append(details["freshness"])
        if "nutrition" in details:
            reasons.append(details["nutrition"])
        if "distance" in details:
            reasons.append(details["distance"])

        if reasons:
            reason_text = " | ".join(reasons)
            reason_lbl = QLabel(f"推荐理由：{reason_text}")
            reason_lbl.setFont(get_font(9))
            reason_lbl.setStyleSheet(f"color: {COLORS['secondary_dark'].name()};")
            reason_lbl.setWordWrap(True)
            info.addWidget(reason_lbl)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        view_btn = QPushButton("查看详情")
        view_btn.setFont(get_font(10))
        view_btn.setMinimumHeight(32)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['secondary'].name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary_dark'].name()};
            }}
        """)
        view_btn.clicked.connect(lambda: self.view_clicked.emit(self.dish["id"]))
        btn_row.addWidget(view_btn)

        eat_btn = QPushButton("去吃这个！")
        eat_btn.setFont(get_font(10))
        eat_btn.setMinimumHeight(32)
        eat_btn.setCursor(Qt.PointingHandCursor)
        eat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary'].name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark'].name()};
            }}
        """)
        eat_btn.clicked.connect(lambda: self.eat_clicked.emit(self.dish["id"]))
        btn_row.addWidget(eat_btn)

        info.addLayout(btn_row)

        main.addLayout(info, 1)

        # 卡片样式
        is_top3 = self.rank <= 3
        border_color = COLORS["accent_gold"].name() if self.rank == 1 else COLORS["border_light"].name()
        bg_alpha = 255 if is_top3 else 248

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color_with_alpha(COLORS['bg_card'], bg_alpha)};
                border: {'2' if is_top3 else '1'}px solid {border_color};
                border-radius: 14px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15 if is_top3 else 10)
        shadow.setColor(QColor(0, 0, 0, 30 if is_top3 else 20))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        self.setMinimumHeight(160)


class RecommendationPage(QWidget):
    """推荐结果页面"""

    view_dish = pyqtSignal(str)
    go_back = pyqtSignal()
    eat_dish = pyqtSignal(str)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.recommendations = []
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 顶部栏
        header = QWidget()
        header.setMaximumHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # 返回按钮
        back_btn = QPushButton("← 返回问卷")
        back_btn.setFont(get_font(11))
        back_btn.setMinimumHeight(36)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_warm'].name()};
                color: {COLORS['text_medium'].name()};
                border: 1px solid {COLORS['border'].name()};
                border-radius: 8px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light'].name()};
            }}
        """)
        back_btn.clicked.connect(self.go_back.emit)
        header_layout.addWidget(back_btn)

        # 标题
        self.title = QLabel("为你推荐")
        self.title.setFont(get_font(20, bold=True))
        self.title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(self.title)

        header_layout.addStretch()

        # 推荐时间
        self.time_lbl = QLabel()
        self.time_lbl.setFont(get_font(10))
        self.time_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header_layout.addWidget(self.time_lbl)

        main.addWidget(header)

        # 诗句
        poem = QLabel("「食在燕园，味在其中。今日推荐，为你而选。」")
        poem.setFont(get_font(11, italic=True))
        poem.setStyleSheet(f"color: {COLORS['accent_gold'].name()}; padding: 5px 20px;")
        poem.setAlignment(Qt.AlignCenter)
        main.addWidget(poem)

        # 滚动内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        self.content = QVBoxLayout(container)
        self.content.setSpacing(15)
        self.content.setContentsMargins(20, 10, 20, 20)

        # 说明文字
        self.desc = QLabel("根据你的回答，我们从多个维度为你精选了以下菜品。")
        self.desc.setFont(get_font(11))
        self.desc.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        self.desc.setWordWrap(True)
        self.content.addWidget(self.desc)

        self.content.addStretch()

        scroll.setWidget(container)
        main.addWidget(scroll)

    def set_recommendations(self, recommendations):
        """设置推荐结果"""
        self.recommendations = recommendations

        # 清除旧内容（保留说明文字）
        while self.content.count() > 1:
            item = self.content.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        from datetime import datetime
        self.time_lbl.setText(datetime.now().strftime("推荐时间：%H:%M"))

        # 显示推荐菜品
        for i, dish in enumerate(recommendations, 1):
            card = DishResultCard(dish, i)
            card.view_clicked.connect(self.view_dish.emit)
            card.eat_clicked.connect(self.on_eat)
            self.content.insertWidget(self.content.count() - 1, card)

        # 底部提示
        tip = QLabel("💡 小贴士：点击「去吃这个！」记录就餐，点击「查看详情」了解更多信息")
        tip.setFont(get_font(10))
        tip.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 10px;")
        tip.setAlignment(Qt.AlignCenter)
        self.content.insertWidget(self.content.count() - 1, tip)

    def on_eat(self, dish_id):
        """处理就餐"""
        self.eat_dish.emit(dish_id)

    def refresh(self):
        """刷新"""
        pass
