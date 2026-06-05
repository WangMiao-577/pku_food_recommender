"""
recommend_cards.py - 推荐结果卡片组件 v2.0
菜品信息卡片、套餐推荐卡片、找店指引浮层
"""

import os

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QScrollArea, QWidget, QDialog,
    QGridLayout, QSizePolicy,
)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha

PORTION_LABELS = {"S": "小份", "M": "标准", "L": "大份"}
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "images")


def load_dish_image(image_name: str, size=(120, 120)) -> QPixmap:
    path = os.path.join(IMAGES_DIR, image_name or "")
    if os.path.exists(path):
        return QPixmap(path).scaled(*size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    return QPixmap()


class NutritionMiniBar(QWidget):
    """微型营养条"""

    def __init__(self, label, value, unit, max_val, bar_color, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        ratio = min(value / max_val, 1.0) if max_val else 0
        filled = int(ratio * 10)
        bar = "█" * filled + "░" * (10 - filled)

        bar_lbl = QLabel(bar)
        bar_lbl.setFont(get_font(8))
        bar_lbl.setStyleSheet(f"color: {bar_color};")
        bar_lbl.setFixedWidth(80)

        text = QLabel(f"{label} {value:.0f}{unit}" if isinstance(value, float) else f"{label} {value}{unit}")
        text.setFont(get_font(9))
        text.setStyleSheet(f"color: {COLORS['text_medium'].name()};")

        layout.addWidget(bar_lbl)
        layout.addWidget(text)
        layout.addStretch()


class StoreGuideDialog(QDialog):
    """找店指引浮层（简化版）"""

    def __init__(self, canteen_name, location_hint="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("找店指引")
        self.setMinimumWidth(420)
        self.setMaximumHeight(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(canteen_name)
        title.setFont(get_font(18, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        layout.addWidget(title)

        map_hint = QLabel("校园示意图（简化）\n未名湖 · 图书馆 · 百讲 · 各校门")
        map_hint.setFont(get_font(11))
        map_hint.setAlignment(Qt.AlignCenter)
        map_hint.setMinimumHeight(120)
        map_hint.setStyleSheet(f"""
            background-color: {COLORS['accent_sky'].name()}22;
            border: 1px dashed {COLORS['border'].name()};
            border-radius: 12px;
            color: {COLORS['text_light'].name()};
            padding: 16px;
        """)
        layout.addWidget(map_hint)

        route = location_hint or f"前往 {canteen_name}，沿校园主路步行约 5-10 分钟可达。"
        route_lbl = QLabel(f"路线指引：{route}")
        route_lbl.setFont(get_font(11))
        route_lbl.setWordWrap(True)
        route_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        layout.addWidget(route_lbl)

        tip = QLabel("AI 模式下可开启外部地图导航（需在设置中配置 API）")
        tip.setFont(get_font(9))
        tip.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        close_btn = QPushButton("知道了")
        close_btn.setStyleSheet(get_button_style("primary"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class ComboResultCard(QFrame):
    """套餐推荐卡片"""

    select_combo = pyqtSignal(dict)
    view_dish = pyqtSignal(str)

    def __init__(self, combo, parent=None):
        super().__init__(parent)
        self.combo = combo
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        tag_text = "聚餐套餐" if self.combo.get("is_preset") else "套餐推荐"
        tag = QLabel(tag_text)
        tag.setFont(get_font(10, bold=True))
        tag.setStyleSheet(f"""
            background-color: {COLORS['accent_sage'].name()};
            color: white;
            border-radius: 10px;
            padding: 4px 12px;
        """)
        header.addWidget(tag)

        if self.combo.get("name"):
            title = QLabel(self.combo["name"])
            title.setFont(get_font(12, bold=True))
            title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
            header.addWidget(title)

        loc = self.combo.get("window", "")
        if self.combo.get("description"):
            loc = loc or self.combo.get("description", "")[:20]
        canteen = QLabel(f"{self.combo.get('canteen', '')} · {loc}")
        canteen.setFont(get_font(10))
        canteen.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header.addWidget(canteen)
        header.addStretch()
        layout.addLayout(header)

        dishes_row = QHBoxLayout()
        dishes_row.setSpacing(8)
        details = self.combo.get("dish_details", [])
        for i, dish in enumerate(details):
            if i > 0:
                plus = QLabel("+")
                plus.setFont(get_font(14, bold=True))
                plus.setStyleSheet(f"color: {COLORS['text_light'].name()};")
                dishes_row.addWidget(plus)

            cell = QVBoxLayout()
            img = QLabel()
            img.setFixedSize(80, 80)
            img.setScaledContents(True)
            pix = load_dish_image(dish.get("image", ""), (80, 80))
            if not pix.isNull():
                img.setPixmap(pix)
            else:
                img.setText("图")
                img.setAlignment(Qt.AlignCenter)
            img.setStyleSheet(f"border-radius: 10px; background: {COLORS['bg_warm'].name()};")
            img.setCursor(Qt.PointingHandCursor)
            img.mousePressEvent = lambda e, did=dish["id"]: self.view_dish.emit(did)

            name = QLabel(dish["name"])
            name.setFont(get_font(11, bold=True))
            name.setWordWrap(True)
            name.setMaximumWidth(90)
            price = QLabel(f"¥{dish['price']}")
            price.setFont(get_font(9))
            price.setStyleSheet(f"color: {COLORS['primary'].name()};")

            cell.addWidget(img)
            cell.addWidget(name)
            cell.addWidget(price)
            dishes_row.addLayout(cell)

        dishes_row.addStretch()
        layout.addLayout(dishes_row)

        footer = QHBoxLayout()
        reason = self.combo.get("reason") or "同窗口取餐，不用奔波"
        hint = QLabel(reason)
        hint.setFont(get_font(10))
        hint.setStyleSheet(f"color: {COLORS['secondary_dark'].name()};")
        hint.setWordWrap(True)
        footer.addWidget(hint)

        footer.addStretch()

        price_box = QVBoxLayout()
        combo_price = QLabel(f"套餐价 ¥{self.combo.get('total_price', 0)}")
        combo_price.setFont(get_font(14, bold=True))
        combo_price.setStyleSheet(f"color: {COLORS['primary'].name()};")
        orig = QLabel(f"单点 ¥{self.combo.get('original_price', 0)}")
        orig.setFont(get_font(9))
        orig.setStyleSheet(f"color: {COLORS['text_light'].name()}; text-decoration: line-through;")
        price_box.addWidget(combo_price)
        price_box.addWidget(orig)
        footer.addLayout(price_box)

        nutrition = QLabel(
            f"约{self.combo.get('total_calories', 0)}kcal · "
            f"蛋白质{self.combo.get('total_protein', 0)}g"
        )
        nutrition.setFont(get_font(9))
        nutrition.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        footer.addWidget(nutrition)

        layout.addLayout(footer)

        select_btn = QPushButton("选此套餐")
        select_btn.setFont(get_font(11, bold=True))
        select_btn.setMinimumHeight(38)
        select_btn.setCursor(Qt.PointingHandCursor)
        select_btn.setStyleSheet(get_button_style("secondary", radius=12))
        select_btn.clicked.connect(lambda: self.select_combo.emit(self.combo))
        layout.addWidget(select_btn)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #F5F8F4;
                border: 2px dashed {COLORS['accent_sage'].name()};
                border-radius: 16px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        self.setMinimumHeight(200)


class DishResultCard(QFrame):
    """升级版菜品信息卡片"""

    view_clicked = pyqtSignal(str)
    eat_clicked = pyqtSignal(str)
    guide_clicked = pyqtSignal(str)

    def __init__(self, dish, rank, related_dishes=None, parent=None):
        super().__init__(parent)
        self.dish = dish
        self.rank = rank
        self.related_dishes = related_dishes or []
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(16, 14, 16, 14)
        main.setSpacing(14)

        rank_lbl = QLabel(f"#{self.rank}")
        rank_lbl.setFont(get_font(24, bold=True))
        rank_lbl.setFixedWidth(44)
        rank_lbl.setAlignment(Qt.AlignCenter)
        colors = ["#D4A574", "#A8B8B0", "#C4A88C"]
        rank_lbl.setStyleSheet(
            f"color: {colors[self.rank - 1] if self.rank <= 3 else COLORS['text_light'].name()};"
        )
        main.addWidget(rank_lbl)

        img_lbl = QLabel()
        img_lbl.setFixedSize(120, 120)
        img_lbl.setScaledContents(True)
        pix = load_dish_image(self.dish.get("image", ""), (120, 120))
        if not pix.isNull():
            img_lbl.setPixmap(pix)
        else:
            img_lbl.setText("(图片)")
            img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet(f"background: {COLORS['bg_warm'].name()}; border-radius: 12px;")
        main.addWidget(img_lbl)

        info = QVBoxLayout()
        info.setSpacing(5)

        title_row = QHBoxLayout()
        name = QLabel(self.dish["name"])
        name.setFont(get_font(16, bold=True))
        name.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        title_row.addWidget(name)

        label = self.dish.get("_mode_label", "")
        if self.dish.get("_is_explore") or label == "新发现":
            pill = QLabel(label or "新发现")
            pill.setStyleSheet(f"""
                color: {COLORS['accent_lavender'].name()};
                background: {color_with_alpha(COLORS['accent_lavender'], 40)};
                border-radius: 8px; padding: 2px 8px;
            """)
            pill.setFont(get_font(9))
            title_row.addWidget(pill)
        elif label == "常点":
            pill = QLabel("常点")
            pill.setStyleSheet(f"""
                color: {COLORS['secondary_dark'].name()};
                background: {color_with_alpha(COLORS['secondary'], 50)};
                border-radius: 8px; padding: 2px 8px;
            """)
            pill.setFont(get_font(9))
            title_row.addWidget(pill)

        title_row.addStretch()
        price = QLabel(f"¥{self.dish['price']}")
        price.setFont(get_font(14, bold=True))
        price.setStyleSheet(f"color: {COLORS['primary'].name()};")
        title_row.addWidget(price)
        info.addLayout(title_row)

        loc_parts = [self.dish["canteen"]]
        if self.dish.get("location_hint"):
            loc_parts.append(self.dish["location_hint"])
        elif self.dish.get("window"):
            loc_parts.append(self.dish["window"])
        meta = QLabel(" · ".join(loc_parts))
        meta.setFont(get_font(10))
        meta.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        meta.setWordWrap(True)
        info.addWidget(meta)

        flavor_row = QHBoxLayout()
        flavor_row.setSpacing(4)
        for f in self.dish.get("flavor", [])[:4]:
            tag = QLabel(f)
            tag.setFont(get_font(9))
            tag.setStyleSheet(f"""
                background: {COLORS['border_light'].name()};
                color: {COLORS['text_medium'].name()};
                border-radius: 8px; padding: 2px 8px;
            """)
            flavor_row.addWidget(tag)
        flavor_row.addStretch()
        info.addLayout(flavor_row)

        nutrition_row = QHBoxLayout()
        nutrition_row.setSpacing(12)
        nutrition_row.addWidget(NutritionMiniBar(
            "热量", self.dish.get("calories", 0), "kcal", 700, COLORS["accent_gold"].name()
        ))
        nutrition_row.addWidget(NutritionMiniBar(
            "蛋白质", self.dish.get("protein", 0), "g", 40, COLORS["accent_rose"].name()
        ))
        nutrition_row.addWidget(NutritionMiniBar(
            "脂肪", self.dish.get("fat", 0), "g", 35, COLORS["accent_sage"].name()
        ))
        info.addLayout(nutrition_row)

        portion = PORTION_LABELS.get(self.dish.get("portion_size", "M"), "标准")
        portion_lbl = QLabel(f"🍽 {portion}")
        portion_lbl.setFont(get_font(10))
        portion_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        info.addWidget(portion_lbl)

        if self.related_dishes:
            rel_title = QLabel("搭配推荐")
            rel_title.setFont(get_font(9))
            rel_title.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            info.addWidget(rel_title)

            rel_scroll = QScrollArea()
            rel_scroll.setWidgetResizable(True)
            rel_scroll.setFixedHeight(52)
            rel_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            rel_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            rel_scroll.setStyleSheet("border: none; background: transparent;")

            rel_w = QWidget()
            rel_layout = QHBoxLayout(rel_w)
            rel_layout.setContentsMargins(0, 0, 0, 0)
            rel_layout.setSpacing(8)
            for rd in self.related_dishes[:6]:
                rb = QPushButton(f"{rd['name']}\n¥{rd['price']}")
                rb.setFont(get_font(8))
                rb.setFixedSize(72, 44)
                rb.setCursor(Qt.PointingHandCursor)
                rb.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['bg_warm'].name()};
                        border: 1px solid {COLORS['border_light'].name()};
                        border-radius: 8px;
                        color: {COLORS['text_medium'].name()};
                    }}
                    QPushButton:hover {{ background: {COLORS['primary_light'].name()}; }}
                """)
                rb.clicked.connect(lambda checked, did=rd["id"]: self.view_clicked.emit(did))
                rel_layout.addWidget(rb)
            rel_layout.addStretch()
            rel_scroll.setWidget(rel_w)
            info.addWidget(rel_scroll)

        details = self.dish.get("_score_details", {})
        reasons = [details[k] for k in ("preference", "freshness", "location") if k in details and details[k]]
        if reasons:
            reason_lbl = QLabel("推荐理由：" + " | ".join(reasons))
            reason_lbl.setFont(get_font(9))
            reason_lbl.setStyleSheet(f"color: {COLORS['secondary_dark'].name()};")
            reason_lbl.setWordWrap(True)
            info.addWidget(reason_lbl)

        btn_row = QHBoxLayout()
        guide_btn = QPushButton(f"📍 怎么去 · {self.dish['canteen']}")
        guide_btn.setFont(get_font(9))
        guide_btn.setCursor(Qt.PointingHandCursor)
        guide_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['primary'].name()};
                border: 1px solid {COLORS['primary_light'].name()};
                border-radius: 8px; padding: 4px 10px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary'].name()};
                color: white;
            }}
        """)
        guide_btn.clicked.connect(lambda: self.guide_clicked.emit(self.dish["canteen"]))
        btn_row.addWidget(guide_btn)
        btn_row.addStretch()

        view_btn = QPushButton("查看详情")
        view_btn.setFont(get_font(10))
        view_btn.setStyleSheet(get_button_style("secondary", radius=6))
        view_btn.clicked.connect(lambda: self.view_clicked.emit(self.dish["id"]))
        btn_row.addWidget(view_btn)

        eat_btn = QPushButton("去吃这个！")
        eat_btn.setFont(get_font(10))
        eat_btn.setStyleSheet(get_button_style("primary", radius=6))
        eat_btn.clicked.connect(lambda: self.eat_clicked.emit(self.dish["id"]))
        btn_row.addWidget(eat_btn)
        info.addLayout(btn_row)

        main.addLayout(info, 1)

        border = COLORS["accent_gold"].name() if self.rank == 1 else COLORS["border_light"].name()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color_with_alpha(COLORS['bg_card'], 230)};
                border: {'2' if self.rank == 1 else '1'}px solid {border};
                border-radius: 16px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16 if self.rank <= 3 else 10)
        shadow.setColor(QColor(0, 0, 0, 28 if self.rank <= 3 else 18))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        self.setMinimumHeight(180)


class ChatInlineRecommendBlock(QFrame):
    """AI 对话内嵌推荐块（套餐 + 菜品卡片）"""

    view_dish = pyqtSignal(str)
    select_combo = pyqtSignal(dict)
    open_full_result = pyqtSignal(dict)

    def __init__(self, dishes=None, combos=None, parent=None):
        super().__init__(parent)
        self.payload = {"dishes": dishes or [], "combos": combos or []}
        self.setup_ui(dishes or [], combos or [])

    def setup_ui(self, dishes, combos):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(12)

        if combos:
            sec = QLabel("推荐套餐")
            sec.setFont(get_font(11, bold=True))
            sec.setStyleSheet(f"color: {COLORS['secondary_dark'].name()};")
            layout.addWidget(sec)
            for combo in combos[:3]:
                card = ComboResultCard(combo)
                card.view_dish.connect(self.view_dish.emit)
                card.select_combo.connect(self.select_combo.emit)
                layout.addWidget(card)

        if dishes:
            sec = QLabel("推荐菜品")
            sec.setFont(get_font(11, bold=True))
            sec.setStyleSheet(f"color: {COLORS['secondary_dark'].name()};")
            layout.addWidget(sec)
            for i, dish in enumerate(dishes[:5], 1):
                card = DishResultCard(dish, i)
                card.view_clicked.connect(self.view_dish.emit)
                layout.addWidget(card)

        full_btn = QPushButton("在结果页查看完整推荐")
        full_btn.setFont(get_font(10))
        full_btn.setCursor(Qt.PointingHandCursor)
        full_btn.setStyleSheet(get_button_style("secondary", radius=10))
        full_btn.clicked.connect(lambda: self.open_full_result.emit(self.payload))
        layout.addWidget(full_btn)

        self.setStyleSheet("QFrame { background: transparent; border: none; }")
