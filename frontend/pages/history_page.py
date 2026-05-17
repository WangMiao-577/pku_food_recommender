"""
history_page.py - 就餐历史记录页面
展示用户的就餐历史，可以查看和删除记录
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QMessageBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font


class HistoryPage(QWidget):
    """就餐历史页面"""

    view_dish = pyqtSignal(str)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 顶部
        header = QWidget()
        header.setMaximumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("就餐记录")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(title)

        subtitle = QLabel("「粗茶淡饭，知足常乐」")
        subtitle.setFont(get_font(11, italic=True))
        subtitle.setStyleSheet(f"color: {COLORS['accent_gold'].name()};")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        # 统计
        self.stat_lbl = QLabel()
        self.stat_lbl.setFont(get_font(10))
        self.stat_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header_layout.addWidget(self.stat_lbl)

        main.addWidget(header)

        # 历史列表
        self.list = QListWidget()
        self.list.setFont(get_font(11))
        self.list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
                outline: none;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 12px 15px;
                border-bottom: 1px solid {COLORS['border_light'].name()};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_warm'].name()};
            }}
        """)
        self.list.itemClicked.connect(self.on_item_click)
        main.addWidget(self.list)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 10, 20, 10)

        clear_btn = QPushButton("清空记录")
        clear_btn.setFont(get_font(11))
        clear_btn.setMinimumHeight(36)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
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
        clear_btn.clicked.connect(self.on_clear)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        main.addLayout(btn_row)

        self.load_history()

    def load_history(self):
        """加载历史记录"""
        self.list.clear()
        history = self.dm.get_history(days=365)

        self.stat_lbl.setText(f"近一年共 {len(history)} 次就餐记录")

        for h in history:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(h["time"])
                time_str = dt.strftime("%m月%d日 %H:%M")
            except:
                time_str = h.get("time", "")

            dish = self.dm.get_dish_by_id(h.get("dish_id", ""))
            rating = dish["rating"] if dish else "?"

            item_text = f"{time_str}  |  {h['dish_name']}  @ {h['canteen']}  |  评分: {rating}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, h.get("dish_id", ""))
            item.setFont(get_font(11))
            self.list.addItem(item)

        if not history:
            item = QListWidgetItem("还没有就餐记录，快去记录第一餐吧！「唯爱与美食不可辜负」")
            item.setFont(get_font(11, italic=True))
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.list.addItem(item)

    def on_item_click(self, item):
        """点击历史记录"""
        dish_id = item.data(Qt.UserRole)
        if dish_id:
            self.view_dish.emit(dish_id)

    def on_clear(self):
        """清空记录"""
        reply = QMessageBox.question(self, "确认清空",
                                     "确定要清空所有就餐记录吗？",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.dm.history = []
            self.dm._save_history()
            self.load_history()

    def refresh(self):
        self.load_history()


from datetime import datetime
