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
from PyQt5.QtGui import QFont
from frontend.main_window import MainWindow
from frontend.watercolor_style import get_font, get_stylesheet


def main():
    """程序入口"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("今天吃什么？")
    app.setApplicationDisplayName("北大食堂智能推荐")

    # 应用全局样式
    app.setStyleSheet(get_stylesheet())

    # 设置全局字体
    app.setFont(get_font(11))

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
