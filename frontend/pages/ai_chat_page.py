"""
ai_chat_page.py - AI 美食助手对话页
AI 模式专属，替代离线问卷流程
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, color_with_alpha


class ChatBubble(QFrame):
    """对话气泡"""

    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        lbl = QLabel(text)
        lbl.setFont(get_font(11))
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(lbl)

        if is_user:
            bg = "#FDF0EE"
            self.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border-radius: 16px;
                    border-bottom-right-radius: 4px;
                }}
            """)
            lbl.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        else:
            bg = "#E8F5F0"
            self.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border-radius: 16px;
                    border-bottom-left-radius: 4px;
                }}
            """)
            lbl.setStyleSheet(f"color: {COLORS['text_dark'].name()};")


class AIChatPage(QWidget):
    """AI 美食助手"""

    recommendation_ready = pyqtSignal(dict)
    switch_offline = pyqtSignal()

    def __init__(self, dm, ai_backend, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.ai = ai_backend
        self.setup_ui()
        self._show_opening()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        header = QWidget()
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 12, 24, 8)

        title = QLabel("AI 美食助手")
        title.setFont(get_font(22, bold=True))
        title.setStyleSheet(f"color: {COLORS['secondary_dark'].name()};")
        hl.addWidget(title)

        sub = QLabel("告诉我你想吃什么")
        sub.setFont(get_font(11))
        sub.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        hl.addWidget(sub)

        status_row = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setFont(get_font(10))
        self.status_lbl = QLabel()
        self.status_lbl.setFont(get_font(9))
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()

        offline_btn = QPushButton("切换离线模式")
        offline_btn.setFont(get_font(9))
        offline_btn.setCursor(Qt.PointingHandCursor)
        offline_btn.setStyleSheet(get_button_style("secondary", radius=8))
        offline_btn.clicked.connect(self.switch_offline.emit)
        status_row.addWidget(offline_btn)
        hl.addLayout(status_row)
        main.addWidget(header)

        self._update_status()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(24, 8, 24, 8)
        self.chat_layout.addStretch()
        scroll.setWidget(self.chat_container)
        main.addWidget(scroll, 1)

        input_bar = QWidget()
        input_bar.setStyleSheet(f"""
            background: {COLORS['bg_card'].name()};
            border-top: 1px solid {COLORS['border_light'].name()};
        """)
        il = QHBoxLayout(input_bar)
        il.setContentsMargins(16, 12, 16, 12)

        self.input = QLineEdit()
        self.input.setPlaceholderText("今天有点累，想吃点清淡的…")
        self.input.setFont(get_font(11))
        self.input.setMinimumHeight(44)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border'].name()};
                border-radius: 22px;
                padding: 8px 16px;
                background: white;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['secondary'].name()};
            }}
        """)
        self.input.returnPressed.connect(self.send_message)
        il.addWidget(self.input, 1)

        send_btn = QPushButton("发送")
        send_btn.setFont(get_font(11, bold=True))
        send_btn.setMinimumHeight(44)
        send_btn.setMinimumWidth(72)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(get_button_style("secondary", radius=22))
        send_btn.clicked.connect(self.send_message)
        il.addWidget(send_btn)

        retry_btn = QPushButton("重新推荐")
        retry_btn.setFont(get_font(9))
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.clicked.connect(self._retry_last)
        il.addWidget(retry_btn)

        main.addWidget(input_bar)

    def _update_status(self):
        if self.ai.is_configured():
            self.status_dot.setStyleSheet(f"color: {COLORS['success'].name()};")
            self.status_lbl.setText("AI 已配置 · 联网推荐")
            self.status_lbl.setStyleSheet(f"color: {COLORS['success'].name()};")
        else:
            self.status_dot.setStyleSheet(f"color: {COLORS['error'].name()};")
            self.status_lbl.setText("未配置 API · 将使用离线降级")
            self.status_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")

    def _show_opening(self):
        self.ai.reset_conversation()
        self._append_bubble(self.ai.get_opening_message(), is_user=False)

    def _append_bubble(self, text, is_user=False):
        row = QHBoxLayout()
        bubble = ChatBubble(text, is_user=is_user)
        bubble.setMaximumWidth(560)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        if is_user:
            wl.addStretch()
            wl.addWidget(bubble)
        else:
            wl.addWidget(bubble)
            wl.addStretch()
        insert_at = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(insert_at, wrapper)

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self._append_bubble(text, is_user=True)

        thinking = QLabel("思考中…")
        thinking.setFont(get_font(10))
        thinking.setStyleSheet(f"color: {COLORS['secondary'].name()}; padding: 4px 24px;")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, thinking)

        result = self.ai.chat_recommend(text, self.dm.get_profile())
        thinking.deleteLater()

        reply = result.get("reply", "暂时无法生成回复")
        self._append_bubble(reply, is_user=False)

        dishes = result.get("recommended_dishes", [])
        if dishes:
            summary = result.get("reasoning") or "为你找到以下推荐："
            self._append_bubble(summary, is_user=False)
            payload = {
                "dishes": dishes,
                "combos": result.get("combos", []),
                "recommend_mode": result.get("recommend_mode", "stable"),
                "source": "ai" if not result.get("fallback") else "local_algorithm",
                "reasoning": result.get("reasoning", ""),
            }
            self.recommendation_ready.emit(payload)

    def _retry_last(self):
        for msg in reversed(self.ai.conversation_history):
            if msg.get("role") == "user":
                self.input.setText(msg.get("content", ""))
                break

    def refresh(self):
        self.ai.reload_config()
        self._update_status()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.chat_layout.addStretch()
        self._show_opening()
