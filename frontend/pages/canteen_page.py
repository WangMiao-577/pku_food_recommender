"""
canteen_page.py - 食堂浏览页面
展示各食堂信息，可以按食堂筛选菜品
"""

import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QSpacerItem, QComboBox, QLineEdit, QTabWidget
)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal

from backend.data_manager import CANTEENS
from backend.paths import dish_image_path
from frontend.watercolor_style import COLORS, get_font, get_button_style, CANTEEN_TAGS
from frontend.ui_scale import grid_columns, scale_value, viewport_width, dish_dim


class CanteenCard(QFrame):
    """食堂卡片"""

    clicked = pyqtSignal(str)

    def __init__(self, canteen, is_selected=False, parent=None):
        super().__init__(parent)
        self.canteen = canteen
        self.is_selected = is_selected
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # 食堂名称
        name = QLabel(self.canteen["name"])
        name.setFont(get_font(13, bold=True))
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        # 标签诗句
        tag = CANTEEN_TAGS.get(self.canteen["name"], "食在燕园")
        tag_lbl = QLabel(tag)
        tag_lbl.setFont(get_font(9, italic=True))
        tag_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        tag_lbl.setAlignment(Qt.AlignCenter)
        tag_lbl.setWordWrap(True)
        layout.addWidget(tag_lbl)

        # 档口数量
        windows = self.canteen.get("windows", [])
        count = QLabel(f"{len(windows)}个档口")
        count.setFont(get_font(9))
        count.setAlignment(Qt.AlignCenter)
        layout.addWidget(count)

        self.setCursor(Qt.PointingHandCursor)
        self.mousePressEvent = lambda e: self.clicked.emit(self.canteen["name"])

        self.update_style()

    def update_style(self):
        if self.is_selected:
            bg = COLORS["primary_light"].name()
            border = COLORS["primary"].name()
        else:
            bg = COLORS["bg_card"].name()
            border = COLORS["border_light"].name()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 12px;
            }}
        """)

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()


class DishSmallCard(QFrame):
    """小菜品卡片"""

    clicked = pyqtSignal(str)

    def __init__(self, dish, parent=None):
        super().__init__(parent)
        self.dish = dish
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 图片
        self.img = QLabel()
        iw, ih = scale_value(dish_dim(130)), scale_value(dish_dim(100), lo=dish_dim(72))
        self.img.setMinimumSize(iw, ih)
        self.img.setMaximumSize(iw + 20, ih + 16)
        self.img.setScaledContents(True)
        self.img.setStyleSheet(f"""
            background-color: {COLORS['bg_warm'].name()};
            border-radius: 8px;
        """)

        img_path = dish_image_path(self.dish.get("image", ""))
        if img_path.exists():
            self.img.setPixmap(QPixmap(str(img_path)))
        else:
            self.img.setText("(图片)")
            self.img.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.img, alignment=Qt.AlignCenter)

        # 名称
        name = QLabel(self.dish["name"])
        name.setFont(get_font(11, bold=True))
        name.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        # 价格
        price = QLabel(f"¥{self.dish['price']}")
        price.setFont(get_font(11, bold=True))
        price.setStyleSheet(f"color: {COLORS['primary'].name()};")
        price.setAlignment(Qt.AlignCenter)
        layout.addWidget(price)

        # 评分
        rating = QLabel(f"⭐ {self.dish['rating']}")
        rating.setFont(get_font(10))
        rating.setAlignment(Qt.AlignCenter)
        layout.addWidget(rating)

        self.setCursor(Qt.PointingHandCursor)
        self.mousePressEvent = lambda e: self.clicked.emit(self.dish["id"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary_light'].name()};
                background-color: {COLORS['bg_warm'].name()};
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        self.setMinimumWidth(150)


class CanteenPage(QWidget):
    """食堂浏览页面"""

    view_dish = pyqtSignal(str)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.current_canteen = None
        self.canteen_cards = {}
        self._grid_cols = 4
        self._filter_state = {}
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 顶部
        header = QWidget()
        header.setMaximumHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("燕园食堂")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(title)

        subtitle = QLabel("「未名湖畔，食色生香」")
        subtitle.setFont(get_font(11, italic=True))
        subtitle.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        # 搜索
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索菜品...")
        self.search.setFont(get_font(11))
        self.search.setMinimumWidth(200)
        self.search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border'].name()};
                border-radius: 8px;
                padding: 6px 12px;
                color: {COLORS['text_dark'].name()};
            }}
        """)
        self.search.textChanged.connect(self.on_search)
        header_layout.addWidget(self.search)

        # 筛选
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部菜系", "川", "鲁", "粤", "西北", "日韩", "西式", "融合"])
        self.filter_combo.setFont(get_font(10))
        self.filter_combo.currentTextChanged.connect(self.on_filter)
        header_layout.addWidget(self.filter_combo)

        main.addWidget(header)

        # 食堂选择栏
        canteen_bar = QScrollArea()
        canteen_bar.setWidgetResizable(True)
        canteen_bar.setMaximumHeight(110)
        canteen_bar.setStyleSheet("border: none; background: transparent;")

        canteen_container = QWidget()
        canteen_layout = QHBoxLayout(canteen_container)
        canteen_layout.setSpacing(10)
        canteen_layout.setContentsMargins(20, 5, 20, 5)

        for c in CANTEENS:
            card = CanteenCard(c)
            card.clicked.connect(self.on_canteen_select)
            self.canteen_cards[c["name"]] = card
            canteen_layout.addWidget(card)

        canteen_layout.addStretch()
        canteen_bar.setWidget(canteen_container)
        main.addWidget(canteen_bar)

        # 菜品展示区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        self.dishes_layout = QGridLayout(container)
        self.dishes_layout.setSpacing(15)
        self.dishes_layout.setContentsMargins(20, 10, 20, 20)
        self.dishes_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(container)
        main.addWidget(scroll)

        # 加载所有菜品
        self.load_dishes()

    def _compute_grid_cols(self, width: int = None) -> int:
        width = width or self.width() or viewport_width()
        content_w = max(320, width - scale_value(360))
        return grid_columns(content_w, card_min_width=scale_value(220), max_cols=5)

    def on_viewport_resize(self, width: int, height: int):
        cols = self._compute_grid_cols(width)
        if cols != self._grid_cols:
            self._grid_cols = cols
            fs = self._filter_state
            self.load_dishes(
                canteen_filter=fs.get("canteen"),
                search_text=fs.get("search"),
                cuisine_filter=fs.get("cuisine"),
            )

    def load_dishes(self, canteen_filter=None, search_text=None, cuisine_filter=None):
        """加载菜品"""
        self._filter_state = {
            "canteen": canteen_filter,
            "search": search_text,
            "cuisine": cuisine_filter,
        }
        cols = self._compute_grid_cols()
        self._grid_cols = cols

        while self.dishes_layout.count():
            item = self.dishes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dishes = self.dm.get_all_dishes()

        # 食堂筛选
        if canteen_filter:
            dishes = [d for d in dishes if d["canteen"] == canteen_filter]

        # 搜索筛选
        if search_text:
            text = search_text.lower()
            dishes = [d for d in dishes if text in d["name"].lower()
                      or text in d.get("canteen", "").lower()]

        # 菜系筛选
        if cuisine_filter and cuisine_filter != "全部菜系":
            dishes = [d for d in dishes if d.get("cuisine") == cuisine_filter]

        # 显示
        for i, dish in enumerate(dishes):
            card = DishSmallCard(dish)
            card.clicked.connect(self.view_dish.emit)
            row = i // cols
            col = i % cols
            self.dishes_layout.addWidget(card, row, col)

        if not dishes:
            empty = QLabel("没有找到匹配的菜品")
            empty.setFont(get_font(14))
            empty.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self.dishes_layout.addWidget(empty, 0, 0, 1, cols)

    def on_canteen_select(self, canteen_name):
        """选择食堂"""
        self.current_canteen = canteen_name if self.current_canteen != canteen_name else None

        # 更新卡片状态
        for name, card in self.canteen_cards.items():
            card.set_selected(name == self.current_canteen)

        # 加载菜品
        self.load_dishes(canteen_filter=self.current_canteen,
                         search_text=self.search.text(),
                         cuisine_filter=self.filter_combo.currentText())

    def on_search(self, text):
        """搜索"""
        self.load_dishes(canteen_filter=self.current_canteen,
                         search_text=text,
                         cuisine_filter=self.filter_combo.currentText())

    def on_filter(self, cuisine):
        """菜系筛选"""
        self.load_dishes(canteen_filter=self.current_canteen,
                         search_text=self.search.text(),
                         cuisine_filter=cuisine)

    def refresh(self):
        self.load_dishes()


# 兼容导入
from PyQt5.QtWidgets import QLineEdit
