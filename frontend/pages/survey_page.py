"""
survey_page.py - 智能推荐四步问卷 v2.0
Step1 场景 → Step2 模式 → Step3 需求细化 → 获取推荐
"""

from PyQt5.QtCore import Qt, pyqtSignal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QCheckBox, QGraphicsDropShadowEffect, QFrame,
    QScrollArea, QGridLayout, QStackedWidget, QMessageBox,
)

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha


SCENE_OPTIONS = [
    ("独自速食", "快速解决，一个人也好", "⚡"),
    ("独自慢食", "享受独处，慢慢品味", "☕"),
    ("同伴聚餐", "三五好友，共享美味", "👥"),
    ("团体宴请", "课题组/社团聚餐", "🎉"),
]

MODE_OPTIONS = [
    ("stable", "稳定模式", "推荐你常吃的熟悉菜品，安全不出错", "熟悉的味道", "#F0F5EE"),
    ("explore", "探索模式", "根据偏好探索从未尝试的新菜品", "发现新美味", "#F3F0F8"),
]

BUDGET_OPTIONS = ["10元以内", "10-20元", "20-30元", "30元以上"]
FLAVOR_OPTIONS = ["清淡", "微辣", "麻辣", "酸甜", "浓郁"]
LOCATION_OPTIONS = [
    "东南门/东门附近", "西南门附近", "西北门/西门附近",
    "中部教学区", "北部生活区",
]

BUDGET_MAP = {0: 10, 1: 20, 2: 30, 3: 50}


class StepIndicator(QFrame):
    """四步进度条"""

    STEPS = ["场景", "模式", "需求", "结果"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.labels = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for i, name in enumerate(self.STEPS):
            lbl = QLabel(f"{i + 1}. {name}")
            lbl.setFont(get_font(10))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumWidth(72)
            self.labels.append(lbl)
            layout.addWidget(lbl)
            if i < len(self.STEPS) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet(f"color: {COLORS['text_light'].name()};")
                layout.addWidget(arrow)
        layout.addStretch()
        self.set_current(0)

    def set_current(self, step: int):
        for i, lbl in enumerate(self.labels):
            if i == step:
                lbl.setStyleSheet(f"""
                    color: white;
                    background: {COLORS['primary'].name()};
                    border-radius: 12px;
                    padding: 6px 10px;
                """)
            elif i < step:
                lbl.setStyleSheet(f"""
                    color: {COLORS['secondary_dark'].name()};
                    background: {color_with_alpha(COLORS['secondary'], 60)};
                    border-radius: 12px;
                    padding: 6px 10px;
                """)
            else:
                lbl.setStyleSheet(f"""
                    color: {COLORS['text_light'].name()};
                    background: {COLORS['border_light'].name()};
                    border-radius: 12px;
                    padding: 6px 10px;
                """)


class SelectableCard(QFrame):
    """可点击选择卡片"""

    clicked = pyqtSignal(int)

    def __init__(self, index, title, desc="", icon="", bg="#FFFDF8", parent=None):
        super().__init__(parent)
        self.index = index
        self.selected = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        self.bg = bg

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(get_font(22))
            layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setFont(get_font(14, bold=True))
        title_lbl.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        layout.addWidget(title_lbl)

        if desc:
            d = QLabel(desc)
            d.setFont(get_font(10))
            d.setStyleSheet(f"color: {COLORS['text_light'].name()};")
            d.setWordWrap(True)
            layout.addWidget(d)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(100)
        self._apply_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.selected = selected
        self._apply_style()

    def _apply_style(self):
        border = COLORS["primary"].name() if self.selected else COLORS["border_light"].name()
        width = 2 if self.selected else 1
        bg = self.bg if not self.selected else color_with_alpha(COLORS["primary"], 25)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: {width}px solid {border};
                border-radius: 16px;
            }}
        """)


class TagChip(QPushButton):
    """标签式选项"""

    def __init__(self, text, index, multi=False, parent=None):
        super().__init__(text, parent)
        self.chip_index = index
        self.multi = multi
        self.setCheckable(True)
        self.setFont(get_font(11))
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self._update_style()

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['primary'].name()};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_warm'].name()};
                    color: {COLORS['text_medium'].name()};
                    border: 1px solid {COLORS['border'].name()};
                    border-radius: 8px;
                    padding: 6px 14px;
                }}
                QPushButton:hover {{ background: {COLORS['border_light'].name()}; }}
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()


class SurveyPage(QWidget):
    """四步智能推荐问卷"""

    recommendation_ready = pyqtSignal(dict)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.current_step = 0
        self.answers = {
            "meal_scene": None,
            "recommend_mode": "stable",
            "remember_mode": False,
            "budget": None,
            "flavors": [],
            "location": None,
        }
        self.scene_cards = []
        self.mode_cards = []
        self.budget_chips = []
        self.flavor_chips = []
        self.location_chips = []
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 8)

        title = QLabel("智能推荐")
        title.setFont(get_font(22, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        header_layout.addWidget(title)

        subtitle = QLabel("选择你的用餐偏好")
        subtitle.setFont(get_font(11))
        subtitle.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header_layout.addWidget(subtitle)

        self.step_indicator = StepIndicator()
        header_layout.addWidget(self.step_indicator)
        main.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(24, 8, 24, 16)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_step_scene())
        self.stack.addWidget(self._build_step_mode())
        self.stack.addWidget(self._build_step_needs())
        outer_layout.addWidget(self.stack)

        nav = QHBoxLayout()
        self.back_btn = QPushButton("上一步")
        self.back_btn.setFont(get_font(11))
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(get_button_style("secondary"))
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)
        nav.addWidget(self.back_btn)

        nav.addStretch()

        self.next_btn = QPushButton("下一步")
        self.next_btn.setFont(get_font(12, bold=True))
        self.next_btn.setMinimumHeight(44)
        self.next_btn.setMinimumWidth(140)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(get_button_style("primary", radius=22))
        self.next_btn.clicked.connect(self.go_next)
        nav.addWidget(self.next_btn)

        outer_layout.addLayout(nav)
        scroll.setWidget(outer)
        main.addWidget(scroll)

    def _step_frame(self, question: str) -> tuple:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(14)
        q = QLabel(question)
        q.setFont(get_font(13, bold=True))
        q.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        q.setWordWrap(True)
        layout.addWidget(q)
        return frame, layout

    def _build_step_scene(self):
        frame, layout = self._step_frame("Step 1 · 今天的用餐场景是？")
        grid = QGridLayout()
        grid.setSpacing(12)
        self.scene_cards.clear()
        for i, (title, desc, icon) in enumerate(SCENE_OPTIONS):
            card = SelectableCard(i, title, desc, icon)
            card.clicked.connect(self._on_scene_selected)
            self.scene_cards.append(card)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return frame

    def _build_step_mode(self):
        frame, layout = self._step_frame("Step 2 · 选择推荐模式")
        self.mode_cards.clear()
        for i, (mode_id, title, desc, tag, bg) in enumerate(MODE_OPTIONS):
            card = SelectableCard(i, title, f"{desc}\n[{tag}]", bg=bg)
            card.mode_id = mode_id
            card.clicked.connect(self._on_mode_selected)
            self.mode_cards.append(card)
            layout.addWidget(card)

        self.remember_cb = QCheckBox("记住我的选择")
        self.remember_cb.setFont(get_font(11))
        self.remember_cb.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        layout.addWidget(self.remember_cb, alignment=Qt.AlignCenter)
        layout.addStretch()
        return frame

    def _build_step_needs(self):
        frame, layout = self._step_frame("Step 3 · 细化你的需求")

        layout.addWidget(self._question_block("今天的预算？", self._make_single_group(BUDGET_OPTIONS, self.budget_chips, False)))
        layout.addWidget(self._question_block("想吃什么口味？（可多选）", self._make_single_group(FLAVOR_OPTIONS, self.flavor_chips, True)))
        layout.addWidget(self._question_block("你当前大概在校园哪个位置？", self._make_single_group(LOCATION_OPTIONS, self.location_chips, False)))
        layout.addStretch()
        return frame

    def _question_block(self, title, widget):
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
                padding: 4px;
            }}
        """)
        v = QVBoxLayout(box)
        lbl = QLabel(title)
        lbl.setFont(get_font(11, bold=True))
        lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        v.addWidget(lbl)
        v.addWidget(widget)
        return box

    def _make_single_group(self, options, store_list, multi):
        w = QWidget()
        row = QHBoxLayout(w)
        row.setSpacing(8)
        store_list.clear()
        group = QButtonGroup(w) if not multi else None
        for i, opt in enumerate(options):
            chip = TagChip(opt, i, multi)
            if group:
                group.addButton(chip, i)
                chip.clicked.connect(chip._update_style)
            else:
                chip.clicked.connect(lambda checked, c=chip: c._update_style())
            row.addWidget(chip)
            store_list.append(chip)
        row.addStretch()
        return w

    def _on_scene_selected(self, index):
        self.answers["meal_scene"] = index
        for i, c in enumerate(self.scene_cards):
            c.set_selected(i == index)

    def _on_mode_selected(self, index):
        self.answers["recommend_mode"] = MODE_OPTIONS[index][0]
        for i, c in enumerate(self.mode_cards):
            c.set_selected(i == index)

    def go_back(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self.step_indicator.set_current(self.current_step)
            self.back_btn.setVisible(self.current_step > 0)
            self.next_btn.setText("下一步" if self.current_step < 2 else "获取推荐 ✨")

    def go_next(self):
        if not self._validate_step():
            return

        if self.current_step < 2:
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self.step_indicator.set_current(self.current_step)
            self.back_btn.setVisible(True)
            self.next_btn.setText("获取推荐 ✨" if self.current_step == 2 else "下一步")
            if self.current_step == 1:
                self._load_saved_mode()
            return

        self._submit()

    def _load_saved_mode(self):
        profile = self.dm.get_profile()
        mode = profile.get("default_mode", "stable")
        for i, (mode_id, *_) in enumerate(MODE_OPTIONS):
            if mode_id == mode:
                self._on_mode_selected(i)
                break

    def _validate_step(self) -> bool:
        if self.current_step == 0 and self.answers["meal_scene"] is None:
            QMessageBox.information(self, "提示", "请选择一个用餐场景~")
            return False
        if self.current_step == 1 and not any(c.selected for c in self.mode_cards):
            QMessageBox.information(self, "提示", "请选择稳定模式或探索模式~")
            return False
        if self.current_step == 2:
            if not any(c.isChecked() for c in self.budget_chips):
                QMessageBox.information(self, "提示", "请选择预算范围~")
                return False
            if not any(c.isChecked() for c in self.flavor_chips):
                QMessageBox.information(self, "提示", "请至少选择一种口味~")
                return False
            if not any(c.isChecked() for c in self.location_chips):
                QMessageBox.information(self, "提示", "请选择当前位置~")
                return False
        return True

    def _collect_step3(self):
        for c in self.budget_chips:
            if c.isChecked():
                self.answers["budget"] = c.chip_index
                break
        self.answers["flavors"] = [c.chip_index for c in self.flavor_chips if c.isChecked()]
        for c in self.location_chips:
            if c.isChecked():
                self.answers["location"] = c.chip_index
                break
        self.answers["remember_mode"] = self.remember_cb.isChecked()

    def _submit(self):
        self._collect_step3()
        self._update_profile()
        context = self._build_context()
        legacy_mode = "social" if self.answers["meal_scene"] in (2, 3) else "normal"
        if self.answers["meal_scene"] == 0:
            legacy_mode = "rush"

        result = self.recommender.recommend_full(top_k=5, mode=legacy_mode, context=context)
        if result.get("dishes"):
            self.step_indicator.set_current(3)
            self.recommendation_ready.emit(result)
        else:
            QMessageBox.information(self, "提示", "没有找到匹配的菜品，建议放宽条件再试~")

    def _update_profile(self):
        profile = self.dm.get_profile()
        scene_names = [s[0] for s in SCENE_OPTIONS]
        scene_idx = self.answers["meal_scene"]
        if scene_idx is not None:
            profile["meal_scenes"] = [scene_names[scene_idx]]
            companions_map = {0: 1, 1: 1, 2: 2, 3: 4}
            profile.setdefault("social", {})["companions"] = companions_map.get(scene_idx, 1)

        mode = self.answers["recommend_mode"]
        profile["default_mode"] = mode
        if self.answers["remember_mode"]:
            self.dm.update_settings({"default_recommend_mode": mode, "explore_mode": mode == "explore"})

        budget_idx = self.answers.get("budget")
        if budget_idx is not None:
            limit = BUDGET_MAP.get(budget_idx, 30)
            profile.setdefault("constraints", {})["budget_limit"] = limit
            profile["budget_range"] = {"min": 0, "max": limit}

        profile["preferred_flavors"] = [FLAVOR_OPTIONS[i] for i in self.answers.get("flavors", [])]

        loc_idx = self.answers.get("location")
        if loc_idx is not None:
            profile["current_location"] = LOCATION_OPTIONS[loc_idx]

        self.dm.update_profile(profile)

    def _build_context(self):
        scene_names = [s[0] for s in SCENE_OPTIONS]
        scene_idx = self.answers["meal_scene"]
        budget_idx = self.answers.get("budget", 1)

        return {
            "recommend_mode": self.answers["recommend_mode"],
            "meal_scene": scene_names[scene_idx] if scene_idx is not None else None,
            "budget_limit": BUDGET_MAP.get(budget_idx, 30),
            "preferred_flavors": [FLAVOR_OPTIONS[i] for i in self.answers.get("flavors", [])],
            "location": LOCATION_OPTIONS[self.answers["location"]] if self.answers.get("location") is not None else "",
            "include_combos": scene_idx in (2, 3),
        }

    def refresh(self):
        self.current_step = 0
        self.stack.setCurrentIndex(0)
        self.step_indicator.set_current(0)
        self.back_btn.setVisible(False)
        self.next_btn.setText("下一步")
        self.answers = {
            "meal_scene": None,
            "recommend_mode": "stable",
            "remember_mode": False,
            "budget": None,
            "flavors": [],
            "location": None,
        }
        for c in self.scene_cards:
            c.set_selected(False)
        for c in self.mode_cards:
            c.set_selected(False)
