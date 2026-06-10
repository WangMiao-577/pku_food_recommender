"""
dish_detail_page.py - 菜品详情页面
展示菜品的详细信息，包括照片、营养、评分等
提供评价和就餐记录功能
"""

import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QSpacerItem, QProgressBar, QMessageBox, QTextEdit,
    QSpinBox, QCheckBox
)
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, POEMS
from frontend.ui_scale import dish_dim


class NutritionBar(QFrame):
    """营养成分条"""

    def __init__(self, name, value, max_val, unit, color_key, parent=None):
        super().__init__(parent)
        self.setup_ui(name, value, max_val, unit, color_key)

    def setup_ui(self, name, value, max_val, unit, color_key):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        # 标签行
        label_row = QHBoxLayout()
        name_lbl = QLabel(f"{name}")
        name_lbl.setFont(get_font(10))
        name_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        label_row.addWidget(name_lbl)
        label_row.addStretch()

        val_lbl = QLabel(f"{value:.0f}{unit}")
        val_lbl.setFont(get_font(10, bold=True))
        val_lbl.setStyleSheet(f"color: {COLORS[color_key].name()};")
        label_row.addWidget(val_lbl)
        layout.addLayout(label_row)

        # 进度条
        bar = QProgressBar()
        bar.setMaximumHeight(8)
        pct = min(int(value / max_val * 100), 100)
        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: {COLORS['border_light'].name()};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {COLORS[color_key].name()};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(bar)

        self.setStyleSheet("border: none; background: transparent;")


class DishDetailPage(QWidget):
    """菜品详情页面"""

    back_clicked = pyqtSignal()
    rate_dish = pyqtSignal(str, int, list, str)  # dish_id, rating, tags, comment
    eat_dish = pyqtSignal(str)

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

        # 顶部栏
        header = QWidget()
        header.setMaximumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        back_btn = QPushButton("← 返回")
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
        back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(back_btn)

        self.title_lbl = QLabel("菜品详情")
        self.title_lbl.setFont(get_font(18, bold=True))
        self.title_lbl.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(self.title_lbl)

        header_layout.addStretch()
        main.addWidget(header)

        # 内容滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        content = QVBoxLayout(container)
        content.setSpacing(15)
        content.setContentsMargins(20, 10, 20, 20)

        # 图片区
        self.img_lbl = QLabel()
        self.img_lbl.setFixedHeight(dish_dim(280))
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setStyleSheet(f"""
            background-color: {COLORS['bg_warm'].name()};
            border-radius: 16px;
        """)
        self.img_lbl.setAlignment(Qt.AlignCenter)
        content.addWidget(self.img_lbl)

        # 名称和评分
        title_row = QHBoxLayout()

        self.name_lbl = QLabel()
        self.name_lbl.setFont(get_font(24, bold=True))
        self.name_lbl.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        title_row.addWidget(self.name_lbl)

        title_row.addStretch()

        self.rating_lbl = QLabel()
        self.rating_lbl.setFont(get_font(18, bold=True))
        self.rating_lbl.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        title_row.addWidget(self.rating_lbl)

        content.addLayout(title_row)

        # 元信息
        self.meta_lbl = QLabel()
        self.meta_lbl.setFont(get_font(11))
        self.meta_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        content.addWidget(self.meta_lbl)

        # 标签
        self.tags_lbl = QLabel()
        self.tags_lbl.setFont(get_font(10))
        self.tags_lbl.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        content.addWidget(self.tags_lbl)

        # 简介/诗句
        self.poem_lbl = QLabel()
        self.poem_lbl.setFont(get_font(11, italic=True))
        self.poem_lbl.setStyleSheet(f"color: {COLORS['accent_rose'].name()}; padding: 5px;")
        self.poem_lbl.setAlignment(Qt.AlignCenter)
        self.poem_lbl.setWordWrap(True)
        content.addWidget(self.poem_lbl)

        # 营养信息卡片
        nutrition_card = QFrame()
        nutrition_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 14px;
                padding: 5px;
            }}
        """)
        nutrition_layout = QVBoxLayout(nutrition_card)
        nutrition_layout.setContentsMargins(15, 12, 15, 12)
        nutrition_layout.setSpacing(8)

        nut_title = QLabel("营养成分")
        nut_title.setFont(get_font(14, bold=True))
        nut_title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        nutrition_layout.addWidget(nut_title)

        self.nutrition_container = QVBoxLayout()
        self.nutrition_container.setSpacing(4)
        nutrition_layout.addLayout(self.nutrition_container)

        shadow = QGraphicsDropShadowEffect(nutrition_card)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 3)
        nutrition_card.setGraphicsEffect(shadow)

        content.addWidget(nutrition_card)

        # 详情卡片
        detail_card = QFrame()
        detail_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 14px;
                padding: 5px;
            }}
        """)
        detail_layout = QGridLayout(detail_card)
        detail_layout.setContentsMargins(15, 12, 15, 12)
        detail_layout.setSpacing(10)

        detail_title = QLabel("详细信息")
        detail_title.setFont(get_font(14, bold=True))
        detail_title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        detail_layout.addWidget(detail_title, 0, 0, 1, 2)

        # 详细信息
        self.detail_labels = []
        detail_items = [
            ("食堂", "canteen"), ("档口", "window"),
            ("菜系", "cuisine"), ("烹饪方式", "cooking"),
            ("口味", "flavor"), ("出餐时间", "prep_time"),
            ("价格", "price"),
        ]

        for i, (label, key) in enumerate(detail_items):
            row = (i // 2) + 1
            col = i % 2

            lbl = QLabel(f"{label}:")
            lbl.setFont(get_font(10))
            lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            detail_layout.addWidget(lbl, row, col * 2)

            val = QLabel()
            val.setFont(get_font(11))
            val.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
            self.detail_labels.append((key, val))
            detail_layout.addWidget(val, row, col * 2 + 1)

        shadow2 = QGraphicsDropShadowEffect(detail_card)
        shadow2.setBlurRadius(15)
        shadow2.setColor(QColor(0, 0, 0, 20))
        shadow2.setOffset(0, 3)
        detail_card.setGraphicsEffect(shadow2)

        content.addWidget(detail_card)

        # 操作按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        self.eat_btn = QPushButton("记录就餐 🍽️")
        self.eat_btn.setFont(get_font(12, bold=True))
        self.eat_btn.setMinimumHeight(44)
        self.eat_btn.setCursor(Qt.PointingHandCursor)
        self.eat_btn.setStyleSheet(get_button_style("primary"))
        self.eat_btn.clicked.connect(self.on_eat)
        btn_row.addWidget(self.eat_btn)

        self.alt_btn = QPushButton("查看替代品 🔍")
        self.alt_btn.setFont(get_font(11))
        self.alt_btn.setMinimumHeight(44)
        self.alt_btn.setCursor(Qt.PointingHandCursor)
        self.alt_btn.setStyleSheet(get_button_style("secondary"))
        self.alt_btn.clicked.connect(self.on_alternatives)
        btn_row.addWidget(self.alt_btn)

        btn_row.addStretch()
        content.addLayout(btn_row)

        content.addStretch()

        scroll.setWidget(container)
        main.addWidget(scroll)

    def set_dish(self, dish_id):
        """设置显示的菜品"""
        self.current_dish_id = dish_id
        dish = self.dm.get_dish_by_id(dish_id)
        if not dish:
            return

        # 图片
        img_path = os.path.join(os.path.dirname(__file__), "..", "..", "images",
                                dish.get("image", ""))
        if os.path.exists(img_path):
            self.img_lbl.setPixmap(QPixmap(img_path))
        else:
            self.img_lbl.setText("菜品图片")
            self.img_lbl.setStyleSheet(f"""
                background-color: {COLORS['bg_warm'].name()};
                border-radius: 16px;
                color: {COLORS['text_light'].name()};
                font-size: 16px;
            """)

        # 名称
        self.name_lbl.setText(dish["name"])
        self.title_lbl.setText(dish["name"])

        # 评分
        stars = "⭐" * int(dish["rating"]) + "☆" * (5 - int(dish["rating"]))
        self.rating_lbl.setText(f"{stars} {dish['rating']}")

        # 元信息
        self.meta_lbl.setText(
            f"{dish['canteen']} · {dish.get('window', '')}  |  ¥{dish['price']}  |  出餐约{dish.get('prep_time', '?')}分钟"
        )

        # 标签
        self.tags_lbl.setText(" · ".join(dish.get("tags", [])))

        # 诗句
        import random
        from frontend.watercolor_style import CANTEEN_TAGS
        canteen_tag = CANTEEN_TAGS.get(dish["canteen"], "")
        poem = random.choice(POEMS)
        self.poem_lbl.setText(f"「{canteen_tag}」\n{poem}" if canteen_tag else f"「{poem}」")

        # 营养
        # 清除旧营养条
        while self.nutrition_container.count():
            item = self.nutrition_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        nutrition_data = [
            ("热量", dish.get("calories", 0), 800, " kcal", "accent_gold"),
            ("蛋白质", dish.get("protein", 0), 50, " g", "accent_rose"),
            ("碳水化合物", dish.get("carbs", 0), 100, " g", "secondary"),
            ("脂肪", dish.get("fat", 0), 50, " g", "accent_sage"),
            ("膳食纤维", dish.get("fiber", 0), 20, " g", "accent_sky"),
        ]

        for name, val, max_v, unit, color in nutrition_data:
            bar = NutritionBar(name, val, max_v, unit, color)
            self.nutrition_container.addWidget(bar)

        # 详细信息
        for key, lbl in self.detail_labels:
            value = dish.get(key, "")
            if key == "price":
                lbl.setText(f"¥{value}")
            elif key == "prep_time":
                lbl.setText(f"{value} 分钟")
            elif key == "flavor" and isinstance(value, list):
                lbl.setText(", ".join(value))
            else:
                lbl.setText(str(value))

    def on_eat(self):
        """记录就餐"""
        if self.current_dish_id:
            dish = self.dm.get_dish_by_id(self.current_dish_id)
            if dish:
                self.dm.add_history(self.current_dish_id, dish["name"], dish["canteen"])
                self.eat_dish.emit(self.current_dish_id)

    def on_alternatives(self):
        """查看替代品"""
        if self.current_dish_id:
            alts = self.recommender.get_alternatives(self.current_dish_id, 3)
            if alts:
                msg = "也许你也想试试这些：\n\n"
                for i, a in enumerate(alts, 1):
                    msg += f"{i}. {a['name']} ({a['canteen']}) - ¥{a['price']}  ⭐{a['rating']}\n"
                QMessageBox.information(self, "替代推荐", msg)
            else:
                QMessageBox.information(self, "提示", "暂无替代推荐")

    def refresh(self):
        if self.current_dish_id:
            self.set_dish(self.current_dish_id)


import random
