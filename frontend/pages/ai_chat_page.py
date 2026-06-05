"""
ai_chat_page.py - AI 美食助手对话页
多轮确认需求 + Cursor 风格对话区（发送后消息进入对话流、输入框清空）
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QPlainTextEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from frontend.watercolor_style import COLORS, get_font, get_button_style
from frontend.widgets.location_selector import MapLocationSelector
from frontend.widgets.recommend_cards import ChatInlineRecommendBlock
from backend.campus_navigation import CampusNavigationService


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


class TypingIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__("助手正在输入", parent)
        self.setFont(get_font(10))
        self.setStyleSheet(f"color: {COLORS['secondary'].name()}; padding: 4px 24px;")
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._dots = 0
        self._timer.start(400)

    def stop(self):
        self._timer.stop()

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self.setText("助手正在输入" + "." * self._dots)


class AIChatPage(QWidget):
    """AI 美食助手"""

    recommendation_ready = pyqtSignal(dict)
    switch_offline = pyqtSignal()
    view_dish = pyqtSignal(str)

    def __init__(self, dm, ai_backend, nav=None, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.ai = ai_backend
        self.nav = nav or CampusNavigationService.get_instance()
        self._typing_widget = None
        self._last_payload = None
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

        sub = QLabel("聊几句，确认需求后再推荐")
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

        self.phase_lbl = QLabel("确认位置")
        self.phase_lbl.setFont(get_font(9, bold=True))
        self.phase_lbl.setStyleSheet(f"""
            color: {COLORS['secondary_dark'].name()};
            background: {COLORS['accent_sky'].name()}33;
            border-radius: 8px;
            padding: 2px 10px;
        """)
        status_row.addWidget(self.phase_lbl)
        status_row.addStretch()

        offline_btn = QPushButton("切换离线模式")
        offline_btn.setFont(get_font(9))
        offline_btn.setCursor(Qt.PointingHandCursor)
        offline_btn.setStyleSheet(get_button_style("secondary", radius=8))
        offline_btn.clicked.connect(self.switch_offline.emit)
        status_row.addWidget(offline_btn)
        hl.addLayout(status_row)

        loc_row = QHBoxLayout()
        loc_lbl = QLabel("我的位置：")
        loc_lbl.setFont(get_font(10))
        loc_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        loc_row.addWidget(loc_lbl)
        self.location_selector = MapLocationSelector(self.nav)
        self.location_selector.location_changed.connect(self._save_location)
        loc_row.addWidget(self.location_selector, 1)
        hl.addLayout(loc_row)

        profile = self.dm.get_profile()
        saved = profile.get("current_location_node_id")
        if saved:
            self.location_selector.set_node_id(saved)
            self._sync_conv_location(saved)

        main.addWidget(header)

        self._update_status()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(24, 8, 24, 8)
        self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container)
        main.addWidget(self.scroll_area, 1)

        input_bar = QWidget()
        input_bar.setStyleSheet(f"""
            background: {COLORS['bg_card'].name()};
            border-top: 1px solid {COLORS['border_light'].name()};
        """)
        il = QVBoxLayout(input_bar)
        il.setContentsMargins(16, 10, 16, 12)
        il.setSpacing(8)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("说说今天想吃什么、预算多少、几个人吃…（Enter 发送，Shift+Enter 换行）")
        self.input.setFont(get_font(11))
        self.input.setMaximumHeight(100)
        self.input.setStyleSheet(f"""
            QPlainTextEdit {{
                border: 1px solid {COLORS['border'].name()};
                border-radius: 12px;
                padding: 10px 14px;
                background: white;
            }}
            QPlainTextEdit:focus {{
                border: 2px solid {COLORS['secondary'].name()};
            }}
        """)
        self.input.installEventFilter(self)
        il.addWidget(self.input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        new_chat_btn = QPushButton("新对话")
        new_chat_btn.setFont(get_font(9))
        new_chat_btn.setCursor(Qt.PointingHandCursor)
        new_chat_btn.clicked.connect(self.refresh)
        btn_row.addWidget(new_chat_btn)

        send_btn = QPushButton("发送")
        send_btn.setFont(get_font(11, bold=True))
        send_btn.setMinimumHeight(40)
        send_btn.setMinimumWidth(80)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(get_button_style("secondary", radius=20))
        send_btn.clicked.connect(self.send_message)
        btn_row.addWidget(send_btn)
        il.addLayout(btn_row)

        main.addWidget(input_bar)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj is self.input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def _update_status(self):
        if self.ai.is_configured():
            self.status_dot.setStyleSheet(f"color: {COLORS['success'].name()};")
            self.status_lbl.setText("AI 已配置 · 多轮对话")
            self.status_lbl.setStyleSheet(f"color: {COLORS['success'].name()};")
        else:
            self.status_dot.setStyleSheet(f"color: {COLORS['warning'].name() if hasattr(COLORS, 'warning') else COLORS['accent_gold'].name()};")
            self.status_lbl.setText("离线对话模式 · 规则追问")
            self.status_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")

    def _update_phase(self, phase: str):
        self.phase_lbl.setText(phase or "聊天中")

    def _show_opening(self):
        self.ai.reset_conversation()
        self._append_bubble(self.ai.get_opening_message(), is_user=False)
        self._update_phase("确认位置")

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

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
        self._scroll_to_bottom()

    def _append_inline_results(self, dishes, combos):
        block = ChatInlineRecommendBlock(dishes=dishes, combos=combos)
        block.view_dish.connect(self.view_dish.emit)
        block.open_full_result.connect(self._open_full_result)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(block)
        wl.addStretch()
        insert_at = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(insert_at, wrapper)
        self._scroll_to_bottom()

    def _show_typing(self):
        self._hide_typing()
        self._typing_widget = TypingIndicator()
        insert_at = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(insert_at, self._typing_widget)
        self._typing_widget.start()
        self._scroll_to_bottom()

    def _hide_typing(self):
        if self._typing_widget:
            self._typing_widget.stop()
            self._typing_widget.deleteLater()
            self._typing_widget = None

    def _save_location(self, node_id, name):
        profile = self.dm.get_profile()
        profile["current_location_node_id"] = node_id
        profile["current_location"] = name
        self.dm.update_profile(profile)
        self._sync_conv_location(node_id, name)

    def _sync_conv_location(self, node_id, name=None):
        if not name:
            node = self.nav.get_node(node_id)
            name = node["name"] if node else ""
        self.ai.conversation_manager.set_location(node_id, name)
        self._update_phase(self.ai.conversation_manager.get_phase_label())

    def _has_location(self) -> bool:
        return bool(self.dm.get_profile().get("current_location_node_id"))

    def _try_resolve_from_text(self, text: str) -> bool:
        node_id = self.ai.resolve_location_from_text(text)
        if node_id:
            node = self.nav.get_node(node_id)
            if node:
                self.location_selector.set_node_id(node_id)
                self._save_location(node_id, node["name"])
                return True
        return False

    def send_message(self):
        text = self.input.toPlainText().strip()
        if not text:
            return

        self.input.clear()
        self._append_bubble(text, is_user=True)

        if not self._has_location():
            if not self._try_resolve_from_text(text):
                self._append_bubble(
                    "请先在上方的「我的位置」中选择当前地点，"
                    "或在消息中说明你在哪里（例如：图书馆、东南门、未名湖）。",
                    is_user=False,
                )
                return

        self._sync_conv_location(self.dm.get_profile().get("current_location_node_id"))
        self._show_typing()

        QTimer.singleShot(80, lambda: self._process_message(text))

    def _process_message(self, text: str):
        result = self.ai.chat_recommend(text, self.dm.get_profile())
        self._hide_typing()

        reply = result.get("reply", "暂时无法生成回复")
        self._append_bubble(reply, is_user=False)
        self._update_phase(result.get("phase", self.ai.conversation_manager.get_phase_label()))

        dishes = result.get("recommended_dishes", [])
        combos = result.get("combos", [])
        if dishes or combos:
            profile = self.dm.get_profile()
            self._last_payload = {
                "dishes": dishes,
                "combos": combos,
                "recommend_mode": result.get("recommend_mode", "stable"),
                "source": "ai" if not result.get("fallback") else "local_algorithm",
                "reasoning": result.get("reasoning", ""),
                "location_node_id": profile.get("current_location_node_id"),
            }
            self._append_inline_results(dishes, combos)

    def _open_full_result(self, payload):
        if payload:
            self.recommendation_ready.emit(payload)

    def refresh(self):
        self.ai.reload_config()
        self._update_status()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.chat_layout.addStretch()
        self._last_payload = None
        self._show_opening()
