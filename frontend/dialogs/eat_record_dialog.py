"""
eat_record_dialog.py - 记录就餐时快速选择心情与同伴
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QRadioButton, QDialogButtonBox,
)
from PyQt5.QtCore import Qt

from frontend.watercolor_style import COLORS, get_font, get_button_style, get_dialog_style


class EatRecordDialog(QDialog):
    """记录一餐的足迹信息"""

    def __init__(self, dish_name: str, canteen: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("记录美食足迹")
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(f"记录：{dish_name}")
        title.setFont(get_font(14, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        layout.addWidget(title)

        sub = QLabel(f"@{canteen} · 这一顿的心情和同伴？")
        sub.setFont(get_font(10))
        sub.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        layout.addWidget(sub)

        layout.addWidget(QLabel("心情"))
        mood_row = QHBoxLayout()
        self.mood_group = QButtonGroup(self)
        for i, (text, val) in enumerate([("开心 😊", "good"), ("一般", "neutral"), ("低落 😔", "bad")]):
            rb = QRadioButton(text)
            rb.setFont(get_font(10))
            if val == "neutral":
                rb.setChecked(True)
            rb.setProperty("mood_val", val)
            self.mood_group.addButton(rb, i)
            mood_row.addWidget(rb)
        layout.addLayout(mood_row)

        layout.addWidget(QLabel("同伴"))
        comp_row = QHBoxLayout()
        self.comp_group = QButtonGroup(self)
        for i, (text, val) in enumerate([("一个人", "alone"), ("和朋友", "friends")]):
            rb = QRadioButton(text)
            rb.setFont(get_font(10))
            if val == "alone":
                rb.setChecked(True)
            rb.setProperty("comp_val", val)
            self.comp_group.addButton(rb, i)
            comp_row.addWidget(rb)
        layout.addLayout(comp_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("记录足迹")
        ok_btn.setStyleSheet(get_button_style("primary", radius=8))
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("取消")
        cancel_btn.setStyleSheet(get_button_style("secondary", radius=8))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(get_dialog_style())

    def get_mood(self) -> str:
        btn = self.mood_group.checkedButton()
        return btn.property("mood_val") if btn else "neutral"

    def get_companions(self) -> str:
        btn = self.comp_group.checkedButton()
        return btn.property("comp_val") if btn else "alone"
