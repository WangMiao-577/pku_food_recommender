"""
recommendation_page.py - 推荐结果展示页面 v2.0
展示套餐卡片 + 升级版菜品卡片
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, color_with_alpha
from frontend.widgets.recommend_cards import (
    DishResultCard, ComboResultCard, StoreGuideDialog,
)


class RecommendationPage(QWidget):
    """推荐结果页面"""

    view_dish = pyqtSignal(str)
    go_back = pyqtSignal()
    eat_dish = pyqtSignal(str)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.result = {}
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        header = QWidget()
        header.setMaximumHeight(72)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

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
            QPushButton:hover {{ background-color: {COLORS['border_light'].name()}; }}
        """)
        back_btn.clicked.connect(self.go_back.emit)
        header_layout.addWidget(back_btn)

        self.title = QLabel("为你推荐")
        self.title.setFont(get_font(20, bold=True))
        self.title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(self.title)

        self.mode_tag = QLabel()
        self.mode_tag.setFont(get_font(10))
        header_layout.addWidget(self.mode_tag)

        header_layout.addStretch()

        self.time_lbl = QLabel()
        self.time_lbl.setFont(get_font(10))
        self.time_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header_layout.addWidget(self.time_lbl)
        main.addWidget(header)

        self.subtitle = QLabel()
        self.subtitle.setFont(get_font(11))
        self.subtitle.setStyleSheet(f"color: {COLORS['text_medium'].name()}; padding: 0 20px;")
        self.subtitle.setWordWrap(True)
        main.addWidget(self.subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        self.content = QVBoxLayout(container)
        self.content.setSpacing(16)
        self.content.setContentsMargins(20, 8, 20, 20)
        self.content.addStretch()

        scroll.setWidget(container)
        main.addWidget(scroll)

    def _resolve_related(self, dish):
        related = []
        for rid in dish.get("related_dishes", []):
            d = self.dm.get_dish_by_id(rid)
            if d:
                related.append(d)
        return related

    def set_result(self, result: dict):
        """设置完整推荐结果 {dishes, combos, recommend_mode, source, ...}"""
        self.result = result or {}
        dishes = self.result.get("dishes", [])
        combos = self.result.get("combos", [])

        while self.content.count() > 1:
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        count = len(dishes)
        mode = self.result.get("recommend_mode", "stable")
        mode_text = "稳定模式" if mode == "stable" else "探索模式"
        mode_color = COLORS["secondary"] if mode == "stable" else COLORS["accent_lavender"]
        self.mode_tag.setText(mode_text)
        self.mode_tag.setStyleSheet(f"""
            color: white;
            background: {mode_color.name()};
            border-radius: 10px;
            padding: 3px 10px;
        """)

        source = self.result.get("source", "local_algorithm")
        if source == "ai":
            self.subtitle.setText(
                f"为你推荐 {count} 款美食 · AI 智能推荐"
                + (f" · {self.result.get('reasoning', '')}" if self.result.get("reasoning") else "")
            )
        else:
            self.subtitle.setText(f"为你推荐 {count} 款美食 · 基于本地算法推荐 · {mode_text}")

        self.time_lbl.setText(datetime.now().strftime("推荐时间：%H:%M"))

        insert_at = 0
        if combos:
            section = QLabel("套餐推荐")
            section.setFont(get_font(14, bold=True))
            section.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
            self.content.insertWidget(insert_at, section)
            insert_at += 1

            for combo in combos:
                card = ComboResultCard(combo)
                card.view_dish.connect(self.view_dish.emit)
                card.select_combo.connect(self._on_select_combo)
                self.content.insertWidget(insert_at, card)
                insert_at += 1

        if dishes:
            if combos:
                section = QLabel("单菜品推荐")
                section.setFont(get_font(14, bold=True))
                section.setStyleSheet(f"color: {COLORS['text_dark'].name()}; margin-top: 8px;")
                self.content.insertWidget(insert_at, section)
                insert_at += 1

            for i, dish in enumerate(dishes, 1):
                related = self._resolve_related(dish)
                card = DishResultCard(dish, i, related)
                card.view_clicked.connect(self.view_dish.emit)
                card.eat_clicked.connect(self.on_eat)
                card.guide_clicked.connect(self._show_guide)
                self.content.insertWidget(insert_at, card)
                insert_at += 1

        tip = QLabel("点击「去吃这个！」记录就餐；套餐可一键记录全部菜品")
        tip.setFont(get_font(10))
        tip.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 8px;")
        tip.setAlignment(Qt.AlignCenter)
        self.content.insertWidget(insert_at, tip)

    def set_recommendations(self, recommendations):
        """向后兼容：仅传入菜品列表"""
        if isinstance(recommendations, dict):
            self.set_result(recommendations)
        else:
            self.set_result({"dishes": recommendations or [], "combos": [], "recommend_mode": "stable"})

    def _show_guide(self, canteen_name):
        dishes = self.dm.get_dishes_by_canteen(canteen_name)
        hint = dishes[0].get("location_hint", "") if dishes else ""
        dlg = StoreGuideDialog(canteen_name, hint, self)
        dlg.exec_()

    def _on_select_combo(self, combo):
        for did in combo.get("dishes", []):
            dish = self.dm.get_dish_by_id(did)
            if dish:
                self.dm.add_history(did, dish["name"], dish["canteen"])
        QMessageBox.information(
            self, "套餐已记录",
            f"已记录套餐：{combo.get('name', '套餐')}\n来自 {combo.get('canteen', '')}",
        )

    def on_eat(self, dish_id):
        self.eat_dish.emit(dish_id)

    def refresh(self):
        pass
