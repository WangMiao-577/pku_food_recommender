"""
settings_page.py - 设置页面
用户偏好设置、AI 配置、关于信息、数据管理
"""

import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame, QScrollArea, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QMessageBox,
    QDoubleSpinBox, QFileDialog
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from frontend.watercolor_style import COLORS, get_font, get_button_style


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 顶部
        header = QWidget()
        header.setMaximumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("设置")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(title)

        header_layout.addStretch()
        main.addWidget(header)

        # 内容滚动
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        content = QVBoxLayout(container)
        content.setSpacing(15)
        content.setContentsMargins(20, 10, 20, 20)

        # ===== 用户偏好设置 =====
        pref_group = QGroupBox("用餐偏好")
        pref_group.setFont(get_font(13, bold=True))
        pref_layout = QVBoxLayout(pref_group)
        pref_layout.setSpacing(12)

        # 预算上限
        budget_row = QHBoxLayout()
        budget_row.addWidget(QLabel("预算上限 (元):"))
        self.budget = QSpinBox()
        self.budget.setRange(5, 100)
        self.budget.setValue(30)
        self.budget.valueChanged.connect(self.save_profile)
        budget_row.addWidget(self.budget)
        budget_row.addStretch()
        pref_layout.addLayout(budget_row)

        # 营养目标
        goal_row = QHBoxLayout()
        goal_row.addWidget(QLabel("营养目标:"))
        self.goal = QComboBox()
        self.goal.addItems(["无", "减脂", "均衡", "增肌"])
        self.goal.currentTextChanged.connect(self.save_profile)
        goal_row.addWidget(self.goal)
        goal_row.addStretch()
        pref_layout.addLayout(goal_row)

        # 距离偏好
        dist_row = QHBoxLayout()
        dist_row.addWidget(QLabel("距离偏好:"))
        self.distance = QComboBox()
        self.distance.addItems(["就近优先", "愿意多走"])
        self.distance.currentTextChanged.connect(self.save_profile)
        dist_row.addWidget(self.distance)
        dist_row.addStretch()
        pref_layout.addLayout(dist_row)

        # 排队偏好
        queue_row = QHBoxLayout()
        queue_row.addWidget(QLabel("排队容忍:"))
        self.queue = QComboBox()
        self.queue.addItems(["接受排队", "不排队"])
        self.queue.currentTextChanged.connect(self.save_profile)
        queue_row.addWidget(self.queue)
        queue_row.addStretch()
        pref_layout.addLayout(queue_row)

        # 忌口
        taboo_row = QHBoxLayout()
        taboo_row.addWidget(QLabel("饮食禁忌:"))
        self.taboo_input = QLineEdit()
        self.taboo_input.setPlaceholderText("如：花生,海鲜,辣 (用逗号分隔)")
        self.taboo_input.textChanged.connect(self.save_profile)
        taboo_row.addWidget(self.taboo_input)
        taboo_row.addStretch()
        pref_layout.addLayout(taboo_row)

        content.addWidget(pref_group)

        # ===== 探索模式 =====
        explore_group = QGroupBox("探索模式")
        explore_group.setFont(get_font(13, bold=True))
        explore_layout = QVBoxLayout(explore_group)

        explore_desc = QLabel("开启探索模式后，推荐会随机包含一些你从未尝试过但评价不错的菜品，"
                              "帮助你发现新的美食。「生活明朗，万物可爱」")
        explore_desc.setFont(get_font(10))
        explore_desc.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        explore_desc.setWordWrap(True)
        explore_layout.addWidget(explore_desc)

        self.explore_cb = QCheckBox("开启探索模式")
        self.explore_cb.setFont(get_font(11))
        self.explore_cb.stateChanged.connect(self.save_settings)
        explore_layout.addWidget(self.explore_cb)

        eps_row = QHBoxLayout()
        eps_row.addWidget(QLabel("探索概率:"))
        self.epsilon = QDoubleSpinBox()
        self.epsilon.setRange(0.0, 0.5)
        self.epsilon.setSingleStep(0.05)
        self.epsilon.setValue(0.15)
        self.epsilon.valueChanged.connect(self.save_settings)
        eps_row.addWidget(self.epsilon)
        eps_row.addStretch()
        explore_layout.addLayout(eps_row)

        content.addWidget(explore_group)

        # ===== 默认推荐模式 =====
        default_mode_group = QGroupBox("默认推荐模式")
        default_mode_group.setFont(get_font(13, bold=True))
        dm_layout = QVBoxLayout(default_mode_group)

        self.stable_mode_rb = QCheckBox("稳定模式（推荐熟悉的菜）")
        self.explore_mode_rb = QCheckBox("探索模式（发现新菜品）")
        for rb in (self.stable_mode_rb, self.explore_mode_rb):
            rb.setFont(get_font(11))
            rb.stateChanged.connect(self._on_default_mode_changed)
            dm_layout.addWidget(rb)

        content.addWidget(default_mode_group)

        # ===== AI 模式配置 =====
        ai_group = QGroupBox("AI 模式配置")
        ai_group.setFont(get_font(13, bold=True))
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setSpacing(10)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API 密钥:"))
        self.ai_key = QLineEdit()
        self.ai_key.setEchoMode(QLineEdit.Password)
        self.ai_key.setPlaceholderText("请输入你的 API 密钥")
        self.ai_key.textChanged.connect(self.save_ai_config)
        key_row.addWidget(self.ai_key)
        ai_layout.addLayout(key_row)

        base_row = QHBoxLayout()
        base_row.addWidget(QLabel("API 地址:"))
        self.ai_base = QLineEdit()
        self.ai_base.setPlaceholderText("https://api.deepseek.com")
        self.ai_base.textChanged.connect(self.save_ai_config)
        base_row.addWidget(self.ai_base)
        ai_layout.addLayout(base_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("模型:"))
        self.ai_model = QComboBox()
        self.ai_model.addItems(["deepseek-v4-flash", "DeepSeek Flash", "claude-3-sonnet", "deepseek"])
        self.ai_model.currentTextChanged.connect(self.save_ai_config)
        model_row.addWidget(self.ai_model)
        model_row.addStretch()
        ai_layout.addLayout(model_row)

        test_row = QHBoxLayout()
        self.ai_status = QLabel("● 未配置")
        self.ai_status.setFont(get_font(10))
        test_btn = QPushButton("测试连接")
        test_btn.setStyleSheet(get_button_style("secondary"))
        test_btn.clicked.connect(self.test_ai_connection)
        test_row.addWidget(self.ai_status)
        test_row.addStretch()
        test_row.addWidget(test_btn)
        ai_layout.addLayout(test_row)

        content.addWidget(ai_group)

        # ===== 数据管理 =====
        data_group = QGroupBox("数据管理")
        data_group.setFont(get_font(13, bold=True))
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(10)

        # 导出
        export_btn = QPushButton("导出所有数据")
        export_btn.setFont(get_font(11))
        export_btn.setMinimumHeight(36)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(get_button_style("secondary"))
        export_btn.clicked.connect(self.on_export)
        data_layout.addWidget(export_btn)

        # 导入
        import_btn = QPushButton("导入数据")
        import_btn.setFont(get_font(11))
        import_btn.setMinimumHeight(36)
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet(get_button_style("secondary"))
        import_btn.clicked.connect(self.on_import)
        data_layout.addWidget(import_btn)

        # 重置
        reset_btn = QPushButton("重置所有数据")
        reset_btn.setFont(get_font(11))
        reset_btn.setMinimumHeight(36)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error'].name()};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: #A85A52;
            }}
        """)
        reset_btn.clicked.connect(self.on_reset)
        data_layout.addWidget(reset_btn)

        content.addWidget(data_group)

        # ===== 关于 =====
        about_group = QGroupBox("关于")
        about_group.setFont(get_font(13, bold=True))
        about_layout = QVBoxLayout(about_group)

        about_text = QLabel(
            "今天吃什么？\n"
            "北京大学食堂智能推荐系统 v2.0\n\n"
            "双模式：离线问卷 + AI 对话推荐\n"
            "召回排序两阶段推荐 · 套餐组合 · 找店指引\n\n"
            "「四方食事，不过一碗人间烟火」\n\n"
            "© 2025 PKU Food Recommender"
        )
        about_text.setFont(get_font(10))
        about_text.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        about_text.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_text)

        content.addWidget(about_group)

        content.addStretch()

        scroll.setWidget(container)
        main.addWidget(scroll)

    def load_settings(self):
        """加载设置到UI"""
        profile = self.dm.get_profile()
        settings = self.dm.get_settings()

        self.budget.setValue(profile.get("constraints", {}).get("budget_limit", 30))
        self.goal.setCurrentText(profile.get("goals", "无"))
        self.distance.setCurrentText(profile.get("preferences", {}).get("distance", "就近优先"))
        self.queue.setCurrentText(profile.get("preferences", {}).get("queue", "接受排队"))

        taboos = profile.get("constraints", {}).get("taboos", [])
        self.taboo_input.setText(",".join(taboos))

        self.explore_cb.setChecked(settings.get("explore_mode", False))
        self.epsilon.setValue(settings.get("explore_epsilon", 0.15))

        default_mode = settings.get("default_recommend_mode", profile.get("default_mode", "stable"))
        self._updating_mode = True
        self.stable_mode_rb.setChecked(default_mode == "stable")
        self.explore_mode_rb.setChecked(default_mode == "explore")
        self._updating_mode = False

        ai_cfg = settings.get("ai_config", {})
        self.ai_key.setText(ai_cfg.get("api_key", ""))
        self.ai_base.setText(ai_cfg.get("api_base", ""))
        model = ai_cfg.get("model", "gpt-3.5-turbo")
        idx = self.ai_model.findText(model)
        if idx >= 0:
            self.ai_model.setCurrentIndex(idx)
        self._refresh_ai_status()

    def _on_default_mode_changed(self):
        if getattr(self, "_updating_mode", False):
            return
        if self.sender() == self.stable_mode_rb and self.stable_mode_rb.isChecked():
            self.explore_mode_rb.setChecked(False)
            self.dm.update_settings({"default_recommend_mode": "stable", "explore_mode": False})
            profile = self.dm.get_profile()
            profile["default_mode"] = "stable"
            self.dm.update_profile(profile)
        elif self.sender() == self.explore_mode_rb and self.explore_mode_rb.isChecked():
            self.stable_mode_rb.setChecked(False)
            self.dm.update_settings({"default_recommend_mode": "explore", "explore_mode": True})
            profile = self.dm.get_profile()
            profile["default_mode"] = "explore"
            self.dm.update_profile(profile)

    def save_ai_config(self):
        self.dm.update_settings({
            "ai_config": {
                "api_key": self.ai_key.text().strip(),
                "api_base": self.ai_base.text().strip(),
                "model": self.ai_model.currentText(),
            }
        })
        self._refresh_ai_status()
        if hasattr(self.recommender, "dm"):
            pass
        # 通知 AI backend 重新加载（若主窗口注入了 ai_backend 可在 refresh 时处理）

    def _refresh_ai_status(self):
        key = self.ai_key.text().strip()
        if key:
            self.ai_status.setText("● 已填写密钥")
            self.ai_status.setStyleSheet(f"color: {COLORS['success'].name()};")
        else:
            self.ai_status.setText("● 未配置")
            self.ai_status.setStyleSheet(f"color: {COLORS['error'].name()};")

    def test_ai_connection(self):
        from backend.ai_backend import AIModeBackend
        ai = AIModeBackend(
            self.dm,
            api_key=self.ai_key.text().strip(),
            api_base=self.ai_base.text().strip() or None,
            model=self.ai_model.currentText(),
        )
        result = ai.test_connection()
        if result.get("success"):
            QMessageBox.information(self, "连接成功", result.get("message", "API 可用"))
            self.ai_status.setText("● 已连接")
            self.ai_status.setStyleSheet(f"color: {COLORS['success'].name()};")
        else:
            QMessageBox.warning(self, "连接失败", result.get("message", "请检查密钥与网络"))
            self.ai_status.setText("● 连接失败")
            self.ai_status.setStyleSheet(f"color: {COLORS['error'].name()};")

    def save_profile(self):
        """保存用户画像"""
        profile = self.dm.get_profile()
        profile["constraints"]["budget_limit"] = self.budget.value()
        profile["goals"] = self.goal.currentText()
        profile["preferences"]["distance"] = self.distance.currentText()
        profile["preferences"]["queue"] = self.queue.currentText()

        taboo_text = self.taboo_input.text().strip()
        if taboo_text:
            profile["constraints"]["taboos"] = [t.strip() for t in taboo_text.split(",") if t.strip()]
        else:
            profile["constraints"]["taboos"] = []

        self.dm.update_profile(profile)

    def save_settings(self):
        """保存设置"""
        self.dm.update_settings({
            "explore_mode": self.explore_cb.isChecked(),
            "explore_epsilon": self.epsilon.value()
        })

    def on_export(self):
        """导出数据"""
        path, _ = QFileDialog.getSaveFileName(self, "导出数据", "pku_food_data.json",
                                              "JSON Files (*.json)")
        if path:
            if self.dm.export_data(path):
                QMessageBox.information(self, "导出成功", f"数据已导出到：\n{path}")
            else:
                QMessageBox.warning(self, "导出失败", "导出数据时出错")

    def on_import(self):
        """导入数据"""
        path, _ = QFileDialog.getOpenFileName(self, "导入数据", "",
                                              "JSON Files (*.json)")
        if path:
            if self.dm.import_data(path):
                QMessageBox.information(self, "导入成功", "数据已导入")
                self.load_settings()
            else:
                QMessageBox.warning(self, "导入失败", "导入数据时出错")

    def on_reset(self):
        """重置数据"""
        reply = QMessageBox.question(self, "确认重置",
                                     "确定要重置所有数据吗？此操作不可恢复！",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.dm.reset_profile()
            # 清除历史
            import shutil
            data_dir = self.dm.data_dir
            if os.path.exists(data_dir):
                for f in os.listdir(data_dir):
                    if f.endswith('.json'):
                        os.remove(os.path.join(data_dir, f))
            QMessageBox.information(self, "重置完成", "所有数据已重置为默认状态")
            self.load_settings()

    def refresh(self):
        self.load_settings()
