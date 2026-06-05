"""
location_selector.py - 地图节点位置选择器
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSignal

from frontend.watercolor_style import COLORS, get_font
from backend.campus_navigation import CampusNavigationService, CATEGORY_LABELS


class MapLocationSelector(QComboBox):
    """从校园地图节点中选择当前位置"""

    location_changed = pyqtSignal(int, str)

    def __init__(self, nav: CampusNavigationService = None, parent=None):
        super().__init__(parent)
        self.nav = nav or CampusNavigationService.get_instance()
        self.setFont(get_font(11))
        self.setMinimumHeight(40)
        self.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border'].name()};
                border-radius: 8px;
                padding: 6px 12px;
                background: white;
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary'].name()};
            }}
        """)
        self._populate()
        self.currentIndexChanged.connect(self._on_changed)

    def _populate(self):
        self.blockSignals(True)
        self.clear()
        self.addItem("请选择当前位置…", None)
        grouped = self.nav.list_nodes_by_category()
        order = ["gate", "landmark", "landscape", "building", "garden", "sports"]
        for cat in order:
            nodes = grouped.get(cat, [])
            if not nodes:
                continue
            label = CATEGORY_LABELS.get(cat, cat)
            for node in nodes:
                text = f"[{label}] {node['name']}"
                self.addItem(text, node["node_id"])
        self.blockSignals(False)

    def _on_changed(self, _index):
        node_id = self.currentData()
        if node_id is not None:
            node = self.nav.get_node(node_id)
            if node:
                self.location_changed.emit(node_id, node["name"])

    def set_node_id(self, node_id):
        if node_id is None:
            self.setCurrentIndex(0)
            return
        for i in range(self.count()):
            if self.currentData(i) == node_id:
                self.setCurrentIndex(i)
                return

    def get_node_id(self):
        return self.currentData()

    def get_node_name(self):
        nid = self.get_node_id()
        if nid is None:
            return ""
        node = self.nav.get_node(nid)
        return node["name"] if node else ""

    def has_selection(self) -> bool:
        return self.get_node_id() is not None
