"""
welcome_page.py - 欢迎主页
展示应用介绍、今日推荐、快捷入口
水彩印象派风格，融入北大未名湖元素
"""

import os
import random
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem, QFrame, QGridLayout
)
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from frontend.watercolor_style import (
    COLORS, get_font, get_button_style, get_card_style, POEMS, CANTEEN_TAGS
)


class FeatureCard(QFrame):
    """功能卡片"""

    def __init__(self, title, desc, btn_text, color_key, parent=None):
        super().__init__(parent)
        self.setup_ui(title, desc, btn_text, color_key)

    def setup_ui(self, title, desc, btn_text, color_key):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title_lbl = QLabel(title)
        title_lbl.setFont(get_font(13, bold=True))
        title_lbl.setStyleSheet(f"color: {COLORS[color_key].name()};")
        layout.addWidget(title_lbl)

        # 描述
        desc_lbl = QLabel(desc)
        desc_lbl.setFont(get_font(10))
        desc_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumHeight(50)
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # 按钮
        self.btn = QPushButton(btn_text)
        self.btn.setFont(get_font(20, bold=True))
        self.btn.setMinimumHeight(70)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS[color_key].name()};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS[color_key].lighter(120).name()};
            }}
        """)
        layout.addWidget(self.btn)

        # 卡片样式
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 16px;
            }}
        """)

        # 阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.setMinimumHeight(200)
        self.setMaximumWidth(320)


class TodayCard(QFrame):
    """今日推荐卡片"""

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        # 标题行
        title_row = QHBoxLayout()
        title = QLabel("今日推荐")
        title.setFont(get_font(18, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        title_row.addWidget(title)

        # 时间标签
        self.time_lbl = QLabel()
        self.time_lbl.setFont(get_font(10))
        self.time_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        title_row.addWidget(self.time_lbl)

        title_row.addStretch()
        layout.addLayout(title_row)

        # 推荐内容
        self.content = QHBoxLayout()
        self.content.setSpacing(20)

        # 菜品图片
        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(500, 375)
        self.img_lbl.setStyleSheet(f"""
            background-color: {COLORS['bg_warm'].name()};
            border-radius: 12px;
        """)
        self.img_lbl.setScaledContents(True)
        self.content.addWidget(self.img_lbl)

        # 菜品信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.dish_name = QLabel()
        self.dish_name.setFont(get_font(20, bold=True))
        self.dish_name.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        info_layout.addWidget(self.dish_name)

        self.dish_info = QLabel()
        self.dish_info.setFont(get_font(11))
        self.dish_info.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        self.dish_info.setWordWrap(True)
        info_layout.addWidget(self.dish_info)

        self.dish_tags = QLabel()
        self.dish_tags.setFont(get_font(10))
        self.dish_tags.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        info_layout.addWidget(self.dish_tags)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.eat_btn = QPushButton("这就去吃！")
        self.eat_btn.setFont(get_font(35, bold=True))
        self.eat_btn.setMinimumHeight(100)
        self.eat_btn.setCursor(Qt.PointingHandCursor)
        self.eat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["secondary"].name()};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 30px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["secondary"].lighter(120).name()};
            }}
        """)
        self.eat_btn.setFixedWidth(250)
        btn_row.addWidget(self.eat_btn)

        self.alt_btn = QPushButton("换一道")
        self.alt_btn.setFont(get_font(35,bold=True))
        self.alt_btn.setMinimumHeight(100)
        self.alt_btn.setCursor(Qt.PointingHandCursor)
        self.alt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["secondary"].name()};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 30px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["secondary"].lighter(120).name()};
            }}
        """)
        self.alt_btn.setFixedWidth(250)
        btn_row.addWidget(self.alt_btn)

        btn_row.addStretch()
        info_layout.addLayout(btn_row)
        info_layout.addStretch()

        self.content.addLayout(info_layout, 1)
        layout.addLayout(self.content)

        # 样式
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 16px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        self.setMinimumWidth(1300)  

        # 加载今日推荐
        self.load_today_recommendation()

    def load_today_recommendation(self):
        """加载今日推荐"""
        now = datetime.now()
        self.time_lbl.setText(now.strftime("%Y年%m月%d日 %H:%M"))

        dish = self.recommender.get_quick_pick()
        if dish:
            self.dish_name.setText(dish["name"])
            canteen_tag = CANTEEN_TAGS.get(dish["canteen"], dish["canteen"])
            self.dish_info.setText(
                f"来自：{dish['canteen']} · {dish.get('window', '')}\n"
                f"{canteen_tag}\n"
                f"价格：¥{dish['price']}  评分：{dish['rating']}分"
            )
            self.dish_tags.setText(" · ".join(dish.get("tags", [])))

            # 加载菜品图片
            img_path = os.path.join(os.path.dirname(__file__), "..", "..", "images",
                                     dish.get("image", ""))
            if os.path.exists(img_path):
                self.img_lbl.setPixmap(QPixmap(img_path))
            else:
                self.img_lbl.setText("(菜品图片)")
                self.img_lbl.setAlignment(Qt.AlignCenter)
                self.img_lbl.setStyleSheet(f"""
                    background-color: {COLORS['bg_warm'].name()};
                    border-radius: 12px;
                    color: {COLORS['text_light'].name()};
                """)


class StatWidget(QFrame):
    """统计小部件"""

    def __init__(self, icon, number, label, color, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setAlignment(Qt.AlignCenter)

        self.num = QLabel(str(number))
        self.num.setFont(get_font(24, bold=True))
        self.num.setStyleSheet(f"color: {COLORS[color].name()};")
        self.num.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.num)

        self.lbl = QLabel(label)
        self.lbl.setFont(get_font(10))
        self.lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        self.lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
            }}
        """)


class WelcomePage(QWidget):
    """欢迎主页"""

    go_survey = pyqtSignal()
    go_recommend = pyqtSignal()
    go_canteens = pyqtSignal()

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(20)

        # 顶部区域 - 未名湖背景
        top_area = QWidget()
        top_area.setMinimumHeight(300)
        top_area.setMaximumHeight(400)
        top_layout = QVBoxLayout(top_area)
        top_layout.setAlignment(Qt.AlignCenter)

        # 欢迎标题
        welcome = QLabel("欢迎来到北大食堂智能推荐")
        welcome.setFont(get_font(28, bold=True))
        welcome.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        welcome.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(welcome)

        # 副标题
        sub = QLabel("「四方食事，不过一碗人间烟火」")
        sub.setFont(get_font(14, italic=True))
        sub.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        sub.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(sub)

        # 统计行
        stats = QHBoxLayout()
        stats.setSpacing(15)

        dishes_count = len(self.dm.get_all_dishes())
        canteens_count = 15  # 食堂数量
        history_count = len(self.dm.get_history(30))

        stats.addWidget(StatWidget("🍜", dishes_count, "收录菜品", "primary"))
        stats.addWidget(StatWidget("🏪", canteens_count, "合作食堂", "secondary"))
        stats.addWidget(StatWidget("🍽️", history_count, "本月就餐", "accent_gold"))
        stats.addWidget(StatWidget("⭐",
                        f"{self.dm.get_all_dishes()[0]['rating'] if self.dm.get_all_dishes() else 4.5:.1f}",
                        "最高评分", "accent_rose"))

        top_layout.addLayout(stats)
        main.addWidget(top_area)

        # 中间内容区
        mid = QHBoxLayout()
        mid.setSpacing(20)

        # 今日推荐
        self.today = TodayCard(self.dm, self.recommender)
        self.today.eat_btn.clicked.connect(self.on_eat_today)
        self.today.alt_btn.clicked.connect(self.on_change_today)
        mid.addWidget(self.today, 2)

        # 快捷功能卡片
        right_cards = QVBoxLayout()
        right_cards.setSpacing(15)

        # 智能推荐卡片
        card1 = FeatureCard(
            "不知道吃什么？",
            "回答几个小问题，让我们为你推荐最合适的菜品。考虑营养、距离、口味等多个维度。",
            "开始智能推荐",
            "primary"
        )
        card1.btn.clicked.connect(self.go_survey.emit)
        right_cards.addWidget(card1)

        # 浏览食堂卡片
        card2 = FeatureCard(
            "逛逛食堂",
            "浏览燕园各处食堂的招牌菜品，发现新的美味。",
            "浏览食堂",
            "secondary"
        )
        card2.btn.clicked.connect(self.go_canteens.emit)
        right_cards.addWidget(card2)

        right_container = QWidget()
        right_container.setLayout(right_cards)
        mid.addWidget(right_container, 1)

        main.addLayout(mid, 1)

        # 底部诗句
        bottom_poem = QLabel()
        bottom_poem.setFont(get_font(11, italic=True))
        bottom_poem.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 10px;")
        bottom_poem.setAlignment(Qt.AlignCenter)
        bottom_poem.setText(f"「{random.choice(POEMS)}」")
        main.addWidget(bottom_poem)

    def on_eat_today(self):
        """记录今日推荐的就餐"""
        dish = self.recommender.get_quick_pick()
        if dish:
            self.dm.add_history(dish["id"], dish["name"], dish["canteen"])
            self.refresh()

    def on_change_today(self):
        """换一道今日推荐"""
        self.today.load_today_recommendation()

    def refresh(self):
        """刷新页面"""
        self.today.load_today_recommendation()
