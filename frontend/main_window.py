"""
main_window.py - 主窗口
实现整体布局、页面导航、水彩风格主题
"""

import os
import sys
import random

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QSizePolicy, QScrollArea, QGridLayout,
    QGraphicsDropShadowEffect, QSpacerItem, QMessageBox, QApplication
)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor, QPainter, QLinearGradient, QBrush
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal

from backend.data_manager import DataManager
from backend.recommender import Recommender
from backend.ai_backend import create_ai_backend
from backend.campus_navigation import CampusNavigationService
from frontend.watercolor_style import (
    COLORS, get_font, get_stylesheet, get_poem,
    get_button_style, get_card_style, color_with_alpha, POEMS
)

# 页面导入（延迟导入避免循环依赖）


class NavButton(QPushButton):
    """自定义导航按钮"""

    def __init__(self, text, icon_text="", parent=None):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.setFont(get_font(15))
        self.setMinimumHeight(60)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setFlat(True)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS["text_medium"].name()};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {color_with_alpha(COLORS["primary_light"], 48)};
                color: {COLORS["primary_dark"].name()};
            }}
            QPushButton:checked {{
                background-color: {COLORS["primary"].name()};
                color: white;
                font-weight: bold;
            }}
        """)


class PoemLabel(QLabel):
    """诗句标签 - 以优雅方式显示温馨诗句"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(get_font(11, italic=True))
        self.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 8px;")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.refresh_poem()

    def refresh_poem(self):
        poem = random.choice(POEMS)
        self.setText(f"「{poem}」")


class ModeToggleWidget(QFrame):
    """离线 / AI 模式切换胶囊"""

    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "offline"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self.offline_btn = QPushButton("离线")
        self.ai_btn = QPushButton("AI")
        for btn in (self.offline_btn, self.ai_btn):
            btn.setCheckable(True)
            btn.setFixedSize(72, 32)
            btn.setFont(get_font(10))
            btn.setCursor(Qt.PointingHandCursor)

        self.offline_btn.clicked.connect(lambda: self.set_mode("offline"))
        self.ai_btn.clicked.connect(lambda: self.set_mode("ai"))
        layout.addWidget(self.offline_btn)
        layout.addWidget(self.ai_btn)

        self.setFixedSize(156, 40)
        self.set_mode("offline", emit=False)

    def set_mode(self, mode: str, emit=True):
        self._mode = mode
        offline_active = mode == "offline"
        self.offline_btn.setChecked(offline_active)
        self.ai_btn.setChecked(not offline_active)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['border_light'].name()};
                border-radius: 20px;
            }}
        """)
        self.offline_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary'].name() if offline_active else 'transparent'};
                color: {'white' if offline_active else COLORS['text_medium'].name()};
                border: none;
                border-radius: 16px;
            }}
        """)
        self.ai_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['secondary'].name() if not offline_active else 'transparent'};
                color: {'white' if not offline_active else COLORS['text_medium'].name()};
                border: none;
                border-radius: 16px;
            }}
        """)
        if emit:
            self.mode_changed.emit(mode)

    def current_mode(self):
        return self._mode


class HeaderWidget(QFrame):
    """顶部标题栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(15)

        # Logo/标题
        self.title = QLabel("What to eat today?")
        self.title.setFont(get_font(20, bold=True))
        self.title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        layout.addWidget(self.title)

        # 副标题
        self.subtitle = QLabel("北京大学食堂智能推荐")
        self.subtitle.setFont(get_font(10))
        
        self.subtitle.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        layout.addWidget(self.subtitle)

        layout.addStretch()

        # 诗句
        self.poem = PoemLabel()
        layout.addWidget(self.poem)

        # 刷新诗句按钮
        self.refresh_btn = QPushButton("换一句")
        self.refresh_btn.setFont(get_font(9))
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent_gold'].name()};
                border: 1px solid {COLORS['accent_gold'].name()};
                border-radius: 12px;
                padding: 3px 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_gold'].name()};
                color: white;
            }}
        """)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.poem.refresh_poem)
        layout.addWidget(self.refresh_btn)

        # 离线 / AI 模式切换
        self.mode_toggle = ModeToggleWidget()
        layout.addWidget(self.mode_toggle)

        self.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['bg_warm'].name()},
                stop:0.5 {COLORS['bg_card'].name()},
                stop:1 {COLORS['bg_warm'].name()});
            border-bottom: 1px solid {COLORS['border'].name()};
        """)
        self.setMaximumHeight(120)


class SidebarWidget(QFrame):
    """侧边导航栏"""

    nav_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nav_buttons = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(5)

        # 导航项
        nav_items = [
            ("home", "主页", "🏠"),
            ("recommend", "智能推荐", "✨"),
            ("canteens", "食堂浏览", "🍽️"),
            ("history", "就餐记录", "📖"),
            ("feedback", "我的评价", "💬"),
            ("settings", "设置", "⚙️"),
        ]

        for key, text, icon in nav_items:
            btn = NavButton(f"  {icon}  {text}")
            btn.clicked.connect(lambda checked, k=key: self.on_nav_clicked(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # 底部信息
        info = QLabel("PKU Food Recommender\nv2.0")
        info.setFont(get_font(9))
        info.setStyleSheet(f"color: {COLORS['text_light'].name()}; padding: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        self.setStyleSheet(f"""
            background-color: {COLORS['bg_card'].name()};
            border-right: 1px solid {COLORS['border_light'].name()};
        """)
        self.setMinimumWidth(350)
        self.setMaximumWidth(350)

    def on_nav_clicked(self, key):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def set_active(self, key):
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)


class WatercolorBackgroundWidget(QWidget):
    """带水彩背景的主内容区"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_image = None
        self.load_background()

    def load_background(self):
        """加载未名湖水彩背景图"""
        bg_path = os.path.join(os.path.dirname(__file__), "..", "images", "bg_weiminghu.jpg")
        if os.path.exists(bg_path):
            self.bg_image = QPixmap(bg_path)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 绘制温暖渐变底色
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#FFF8F0"))
        gradient.setColorAt(1, QColor("#FFF0E0"))
        painter.fillRect(self.rect(), gradient)

        # 绘制水彩背景图（低透明度作为水印）
        if self.bg_image and not self.bg_image.isNull():
            painter.save()
            painter.setOpacity(0.08)
            scaled = self.bg_image.scaled(self.size(), Qt.KeepAspectRatioByExpanding,
                                           Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.restore()

        # 绘制柔和水彩斑块装饰
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        colors = [COLORS["accent_rose"], COLORS["accent_sage"],
                  COLORS["accent_sky"], COLORS["accent_lavender"]]
        random.seed(42)

        for i, color in enumerate(colors):
            c = QColor(color)
            c.setAlpha(20)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.NoPen)
            for j in range(2):
                cx = random.randint(50, max(100, self.width() - 50))
                cy = random.randint(50, max(100, self.height() - 50))
                r = random.randint(80, 180)
                painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.restore()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.nav = CampusNavigationService.get_instance()
        self.recommender = Recommender(self.dm)
        self.ai_backend = create_ai_backend(self.dm)
        self.pages = {}
        self.app_mode = self.dm.get_settings().get("app_mode", "offline")

        self.setWindowTitle("今天吃什么？ - 北大食堂智能推荐")
        self.setMinimumSize(1100, 750)
        self.resize(2000, 1600)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏
        self.sidebar = SidebarWidget()
        self.sidebar.nav_clicked.connect(self.switch_page)
        main_layout.addWidget(self.sidebar)

        # 右侧主区域
        right_area = QVBoxLayout()
        right_area.setContentsMargins(0, 0, 0, 0)
        right_area.setSpacing(0)

        # 顶部标题栏
        self.header = HeaderWidget()
        self.header.mode_toggle.set_mode(self.app_mode, emit=False)
        self.header.mode_toggle.mode_changed.connect(self.on_app_mode_changed)
        right_area.addWidget(self.header)

        # 内容区（水彩背景）
        self.content_bg = WatercolorBackgroundWidget()
        content_layout = QVBoxLayout(self.content_bg)
        content_layout.setContentsMargins(20, 15, 20, 15)

        # 页面栈
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self.stack)

        right_area.addWidget(self.content_bg, 1)
        main_layout.addLayout(right_area, 1)

        # 创建页面
        self.create_pages()

        # 默认显示主页
        self.switch_page("home")
        self.sidebar.set_active("home")

    def create_pages(self):
        """创建所有页面"""
        # 延迟导入避免循环依赖
        from frontend.pages.welcome_page import WelcomePage
        from frontend.pages.survey_page import SurveyPage
        from frontend.pages.recommendation_page import RecommendationPage
        from frontend.pages.canteen_page import CanteenPage
        from frontend.pages.dish_detail_page import DishDetailPage
        from frontend.pages.history_page import HistoryPage
        from frontend.pages.feedback_page import FeedbackPage
        from frontend.pages.settings_page import SettingsPage
        from frontend.pages.ai_chat_page import AIChatPage

        # 主页（欢迎页）
        welcome = WelcomePage(self.dm, self.recommender)
        welcome.go_survey.connect(lambda: self.switch_page("recommend"))
        welcome.go_recommend.connect(lambda: self.switch_page("recommend"))
        welcome.go_canteens.connect(lambda: self.switch_page("canteens"))
        self.add_page("home", welcome)

        # 离线智能推荐（四步问卷）
        survey = SurveyPage(self.dm, self.recommender, self.nav)
        survey.recommendation_ready.connect(self.show_recommendations)
        self.add_page("recommend", survey)

        # AI 美食助手
        ai_chat = AIChatPage(self.dm, self.ai_backend, self.nav)
        ai_chat.recommendation_ready.connect(self.show_recommendations)
        ai_chat.switch_offline.connect(lambda: self.set_app_mode("offline"))
        self.add_page("ai_recommend", ai_chat)

        # 推荐结果页
        rec_page = RecommendationPage(self.dm, self.recommender, self.nav)
        rec_page.view_dish.connect(self.show_dish_detail)
        rec_page.go_back.connect(self._back_from_recommendations)
        self.add_page("recommend_result", rec_page)

        # 食堂浏览
        canteen = CanteenPage(self.dm, self.recommender)
        canteen.view_dish.connect(self.show_dish_detail)
        self.add_page("canteens", canteen)

        # 菜品详情
        detail = DishDetailPage(self.dm, self.recommender)
        detail.back_clicked.connect(self.go_back)
        detail.rate_dish.connect(self.on_rate_dish)
        detail.eat_dish.connect(self.on_eat_dish)
        self.add_page("dish_detail", detail)

        # 就餐记录
        history = HistoryPage(self.dm, self.recommender)
        history.view_dish.connect(self.show_dish_detail)
        self.add_page("history", history)

        # 评价
        feedback = FeedbackPage(self.dm, self.recommender)
        feedback.view_dish.connect(self.show_dish_detail)
        self.add_page("feedback", feedback)

        # 设置
        settings = SettingsPage(self.dm, self.recommender)
        self.add_page("settings", settings)

    def add_page(self, key, widget):
        """添加页面到栈"""
        self.pages[key] = widget
        self.stack.addWidget(widget)

    def switch_page(self, key):
        """切换页面"""
        if key == "recommend":
            key = "ai_recommend" if self.app_mode == "ai" else "recommend"

        if key in self.pages:
            # 更新页面数据
            page = self.pages[key]
            if hasattr(page, 'refresh'):
                page.refresh()

            idx = self.stack.indexOf(page)
            self.stack.setCurrentIndex(idx)

            # 更新导航状态
            if key in ["home", "recommend", "canteens", "history", "feedback", "settings"]:
                self.sidebar.set_active(key)

    def _back_from_recommendations(self):
        self.switch_page("recommend")

    def show_recommendations(self, result):
        """显示推荐结果（支持 dict 或 list）"""
        rec_page = self.pages.get("recommend_result")
        if rec_page:
            rec_page.set_recommendations(result)
            self.switch_page("recommend_result")

    def set_app_mode(self, mode: str):
        self.app_mode = mode
        self.header.mode_toggle.set_mode(mode, emit=False)
        self.dm.update_settings({"app_mode": mode})
        if mode == "ai" and not self.ai_backend.is_configured():
            QMessageBox.information(
                self, "AI 模式",
                "AI 模式需要联网并配置 API 密钥。\n可在「设置 → AI 模式配置」中填写。\n"
                "未配置时将使用离线推荐降级。",
            )

    def on_app_mode_changed(self, mode: str):
        self.set_app_mode(mode)
        current = self.stack.currentWidget()
        survey = self.pages.get("recommend")
        ai_page = self.pages.get("ai_recommend")
        if current in (survey, ai_page):
            self.switch_page("recommend")

    def show_dish_detail(self, dish_id):
        """显示菜品详情"""
        detail = self.pages.get("dish_detail")
        if detail:
            detail.set_dish(dish_id)
            self.switch_page("dish_detail")

    def go_back(self):
        """返回上一页"""
        current = self.stack.currentWidget()
        # 简单的返回逻辑
        if current == self.pages.get("dish_detail"):
            self.switch_page("canteens")
        else:
            self.switch_page("home")

    def on_rate_dish(self, dish_id, rating, tags, comment):
        """处理评价"""
        self.dm.add_review(dish_id, rating, tags, comment)
        QMessageBox.information(self, "评价提交", "感谢你的评价！你的反馈将帮助我们做得更好。")

    def on_eat_dish(self, dish_id):
        """处理就餐记录"""
        dish = self.dm.get_dish_by_id(dish_id)
        if dish:
            self.dm.add_history(dish_id, dish["name"], dish["canteen"])
            QMessageBox.information(self, "就餐记录",
                                    f"已记录：{dish['name']}\n来自{dish['canteen']}\n\n「四方食事，不过一碗人间烟火」")

    def apply_styles(self):
        """应用全局样式"""
        self.setStyleSheet(get_stylesheet())

    def showEvent(self, event):
        """显示时刷新"""
        super().showEvent(event)
        # 刷新当前页面
        current = self.stack.currentWidget()
        if current and hasattr(current, 'refresh'):
            current.refresh()


def main():
    """主入口"""
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet())

    # 设置应用字体
    font = get_font(11)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
