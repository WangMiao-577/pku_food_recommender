"""
map_guide_dialog.py - 可视化找店指引（地图 + A* 路线）
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from frontend.watercolor_style import COLORS, get_font, get_button_style, get_dialog_style
from frontend.ui_scale import fit_pixmap_size
from backend.campus_navigation import CampusNavigationService


class MapGuideDialog(QDialog):
    """找店指引浮层 - 显示校园地图与 A* 规划路线"""

    def __init__(
        self,
        canteen_name: str,
        start_node_id=None,
        nav: CampusNavigationService = None,
        parent=None,
    ):
        super().__init__(parent)
        self.canteen_name = canteen_name
        self.start_node_id = start_node_id
        self.nav = nav or CampusNavigationService.get_instance()
        self.setWindowTitle("找店指引")
        self.setMinimumSize(640, 520)
        self._apply_dialog_style()
        self._build_ui()
        self._load_route()

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            pg = self.parent().geometry()
            self.resize(
                max(640, min(int(pg.width() * 0.82), 1100)),
                max(520, min(int(pg.height() * 0.82), 860)),
            )

    def _fit_map_pixmap(self, pix: QPixmap) -> QPixmap:
        max_w = max(360, self.width() - 64)
        max_h = max(260, self.height() - 200)
        size = fit_pixmap_size(pix.width(), pix.height(), max_w, max_h)
        return pix.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _apply_dialog_style(self):
        self.setStyleSheet(f"""
            {get_dialog_style()}
            QLabel {{
                background-color: transparent;
                color: {COLORS['text_dark'].name()};
            }}
            QScrollArea {{
                background-color: white;
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: white;
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        title = QLabel(f"前往 {self.canteen_name}")
        title.setFont(get_font(18, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()}; background: transparent;")
        layout.addWidget(title)

        self.route_lbl = QLabel()
        self.route_lbl.setFont(get_font(11))
        self.route_lbl.setWordWrap(True)
        self.route_lbl.setStyleSheet(f"color: {COLORS['text_medium'].name()}; background: transparent;")
        layout.addWidget(self.route_lbl)

        self.meta_lbl = QLabel()
        self.meta_lbl.setFont(get_font(10))
        self.meta_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()}; background: transparent;")
        layout.addWidget(self.meta_lbl)

        hint = QLabel("下方为校园地图，红线为推荐步行路线")
        hint.setFont(get_font(10))
        hint.setStyleSheet(f"color: {COLORS['text_light'].name()}; background: transparent;")
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: white;
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
            }}
        """)

        map_container = QFrame()
        map_container.setStyleSheet("QFrame { background-color: white; border: none; }")
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(12, 12, 12, 12)

        self.map_lbl = QLabel("正在加载地图…")
        self.map_lbl.setAlignment(Qt.AlignCenter)
        self.map_lbl.setStyleSheet(
            f"color: {COLORS['text_medium'].name()}; background-color: white; padding: 24px;"
        )
        self.map_lbl.setMinimumHeight(200)
        map_layout.addWidget(self.map_lbl)

        scroll.setWidget(map_container)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(get_button_style("primary"))
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load_route(self):
        if self.start_node_id is None:
            self.route_lbl.setText("请先在推荐前选择当前位置，以显示完整路线。")
            self._show_base_map()
            return

        route = self.nav.plan_route_to_canteen(self.start_node_id, self.canteen_name)
        if not route:
            self.route_lbl.setText(f"无法规划到 {self.canteen_name} 的路线，请检查位置设置。")
            self._show_base_map()
            return

        self.route_lbl.setText(
            f"从 {route['start_name']} 到 {route['goal_name']}\n"
            f"路线：{route['route_text']}"
        )
        self.meta_lbl.setText(
            f"步行约 {route['walk_minutes']} 分钟 · 路径距离 {route['distance']:.3f}（相对坐标）"
        )

        try:
            img_path = self.nav.render_route_image(route["path_ids"])
            pix = QPixmap(img_path)
            if not pix.isNull():
                scaled = self._fit_map_pixmap(pix)
                self.map_lbl.setPixmap(scaled)
                self.map_lbl.setText("")
                self.map_lbl.setStyleSheet("background-color: white;")
                self.map_lbl.setMinimumSize(scaled.size())
            else:
                self.map_lbl.setPixmap(QPixmap())
                self.map_lbl.setText("地图加载失败，请稍后重试")
        except Exception as e:
            self.map_lbl.setPixmap(QPixmap())
            self.map_lbl.setText(f"地图渲染失败: {e}")

    def _show_base_map(self):
        try:
            path = self.nav.mapper.annotate_map(
                output_path=str(self.nav._temp_dir / "base_map.png"),
                show_labels=False,
            )
            pix = QPixmap(path)
            if not pix.isNull():
                scaled = self._fit_map_pixmap(pix)
                self.map_lbl.setPixmap(scaled)
                self.map_lbl.setText("")
                self.map_lbl.setStyleSheet("background-color: white;")
            else:
                self.map_lbl.setText("（校园地图暂不可用）")
        except Exception:
            self.map_lbl.setText("（校园地图暂不可用）")
