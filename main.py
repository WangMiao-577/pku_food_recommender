"""
rcgg后援团
main.py - 程序入口
北京大学食堂智能推荐系统
今天吃什么？

运行方式:
    python main.py

依赖:
    PyQt5 (pip install PyQt5)
"""

import sys
import os

# 确保能正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from frontend.main_window import MainWindow
from frontend.watercolor_style import get_font, get_stylesheet
from frontend.ui_scale import setup_high_dpi, initial_window_geometry, set_viewport_size
from backend.paths import icon_path


def apply_app_icon(app: QApplication) -> QIcon:
    """设置任务栏 / 窗口图标（开发环境与打包环境均使用 my_logo.ico）"""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "PKUFoodRecommender.App.1"
            )
        except Exception:
            pass
    path = icon_path()
    if path.exists():
        icon = QIcon(str(path))
        app.setWindowIcon(icon)
        return icon
    return QIcon()


def main():
    """程序入口"""
    setup_high_dpi()
    app = QApplication(sys.argv)
    app.setApplicationName("今天吃什么？")
    app.setApplicationDisplayName("北大食堂智能推荐")
    app_icon = apply_app_icon(app)

    # 应用全局样式
    app.setStyleSheet(get_stylesheet())

    # 设置全局字体
    app.setFont(get_font(11))

    window = MainWindow()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    w, h, x, y = initial_window_geometry(app)
    window.resize(w, h)
    window.move(x, y)
    set_viewport_size(w, h)
    window.show()

    # 运行事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
