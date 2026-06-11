"""
watercolor_style.py - 水彩印象派风格渲染工具
提供统一的配色方案、字体设置、水彩效果等UI主题
"""

from PyQt5.QtGui import QColor, QFont, QPainter, QLinearGradient, QBrush, QPalette, QPixmap
from PyQt5.QtCore import Qt, QRect, QPoint


# ============ 水彩印象派配色方案 ============

COLORS = {
    # 主色调 - 温暖水彩
    "primary": QColor("#D4847C"),           # 柔和珊瑚
    "primary_light": QColor("#E8AFA8"),     # 浅珊瑚
    "primary_dark": QColor("#B85A52"),      # 深珊瑚

    # 辅助色
    "secondary": QColor("#7BA598"),         # 薄荷绿
    "secondary_light": QColor("#A8C9BF"),   # 浅薄荷
    "secondary_dark": QColor("#5A8578"),     # 深薄荷

    # 背景色
    "bg_main": QColor("#FFF8F0"),           # 温暖米白
    "bg_card": QColor("#FFFDF8"),           # 卡片白
    "bg_warm": QColor("#FFF0E0"),           # 暖色背景

    # 文字色
    "text_dark": QColor("#4A3728"),         # 深棕文字
    "text_medium": QColor("#6B5344"),       # 中棕文字
    "text_light": QColor("#9B8B7B"),        # 浅棕文字
    "text_white": QColor("#FFFFFF"),        # 白色文字

    # 强调色
    "accent_gold": QColor("#D4A574"),       # 水彩金
    "accent_rose": QColor("#E8B4B8"),       # 玫瑰粉
    "accent_sage": QColor("#B8C4A8"),       # 鼠尾草绿
    "accent_lavender": QColor("#C4B8D4"),   # 淡紫
    "accent_sky": QColor("#A8C8D8"),        # 天空蓝

    # 边框和分割线
    "border": QColor("#D4C4B0"),           # 温暖边框
    "border_light": QColor("#E8DDD0"),      # 浅边框

    # 状态色
    "success": QColor("#7BA598"),
    "warning": QColor("#D4A574"),
    "error": QColor("#C4786E"),
}

# 温暖诗句集合
POEMS = [
    "四方食事，不过一碗人间烟火",
    "人间有味是清欢",
    "唯爱与美食不可辜负",
    "食不厌精，脍不厌细",
    "一粥一饭，当思来之不易",
    "粗茶淡饭，知足常乐",
    "腹有诗书气自华，胃有美食心自暖",
    "生活明朗，万物可爱",
    "好好吃饭，用心生活",
    "以欢喜之心，慢度日常",
]

# 食堂标签诗句
CANTEEN_TAGS = {
    "家园食堂": "家园味道，温暖如常",
    "农园食堂": "农园深处，食色生香",
    "学一食堂": "学一简朴，滋味悠长",
    "学五食堂": "学五灯火，暖胃暖心",
    "燕南美食": "燕南佳味，唇齿留香",
    "松林": "松林小食，清晨的味道",
    "佟园": "民族风味，清真之选",
    "勺园": "勺园食趣，西北飘香",
}


def color_with_alpha(color, alpha):
    """将QColor和alpha值转为rgba字符串，alpha范围0-255"""
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"


def get_font(size=12, bold=False, italic=False) -> QFont:
    """获取统一字体"""
    font = QFont("STXinwei", size)
    font.setBold(bold)
    font.setItalic(italic)
    return font


def get_card_style(bg_color=None, border_color=None, radius=12) -> str:
    """获取卡片样式"""
    bg = (bg_color or COLORS["bg_card"]).name()
    border = (border_color or COLORS["border_light"]).name()
    return f"""
        background-color: {bg};
        border: 1px solid {border};
        border-radius: {radius}px;
    """


DIALOG_BG = "#FFFFFF"


def button_hover_background(color_key: str = "primary") -> str:
    """悬停时使用的更浅背景色"""
    light = COLORS.get(f"{color_key}_light", COLORS[color_key])
    return light.lighter(108).name()


def button_hover_from_color(color: QColor) -> str:
    """从任意 QColor 生成悬停浅色"""
    return color.lighter(115).name()


def get_dialog_style() -> str:
    """弹窗纯白背景"""
    return f"QDialog {{ background-color: {DIALOG_BG}; }}"


def get_outline_button_style(color_key="secondary", radius=8) -> str:
    """描边按钮（悬停变浅填充）"""
    color = COLORS[color_key].name()
    hover = button_hover_background(color_key)
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_medium'].name()};
            border: 1px solid {COLORS['border'].name()};
            border-radius: {radius}px;
            padding: 6px 14px;
            font-family: "Microsoft YaHei";
        }}
        QPushButton:hover {{
            background-color: {hover};
            color: white;
            border-color: {color};
        }}
    """


def get_button_style(color_key="primary", text_color="text_white", radius=8) -> str:
    """获取按钮样式（悬停变浅）"""
    color = COLORS[color_key].name()
    hover = button_hover_background(color_key)
    text = COLORS[text_color].name()
    return f"""
        QPushButton {{
            background-color: {color};
            color: {text};
            border: none;
            border-radius: {radius}px;
            padding: 10px 24px;
            font-size: 14px;
            font-family: "Microsoft YaHei";
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {color};
            padding: 11px 22px 9px 26px;
        }}
    """


def get_warm_gradient(start_color=None, end_color=None) -> QLinearGradient:
    """获取温暖渐变"""
    gradient = QLinearGradient(0, 0, 0, 1)
    gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
    sc = start_color or COLORS["bg_main"]
    ec = end_color or COLORS["bg_warm"]
    gradient.setColorAt(0, sc)
    gradient.setColorAt(1, ec)
    return gradient


def paint_watercolor_background(painter: QPainter, rect: QRect,
                                  colors: list = None, intensity: float = 0.3):
    """绘制水彩背景效果"""
    if colors is None:
        colors = [COLORS["accent_rose"], COLORS["accent_sage"],
                   COLORS["accent_sky"], COLORS["accent_lavender"]]

    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)

    # 绘制柔和的水彩斑块
    import random
    random.seed(42)  # 固定随机种子以保持美观

    for i, color in enumerate(colors):
        c = QColor(color)
        c.setAlpha(int(40 * intensity))
        painter.setBrush(QBrush(c))
        painter.setPen(Qt.NoPen)

        # 绘制不规则圆形模拟水彩晕染
        for _ in range(3):
            cx = rect.x() + random.randint(0, rect.width())
            cy = rect.y() + random.randint(0, rect.height())
            r = random.randint(50, 150)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

    painter.restore()


def get_stylesheet() -> str:
    """获取全局样式表（随四季 COLORS 动态变化）"""
    bg = COLORS["bg_main"].name()
    text = COLORS["text_dark"].name()
    bg_card = COLORS["bg_card"].name()
    border = COLORS["border"].name()
    border_light = COLORS["border_light"].name()
    primary = COLORS["primary"].name()
    secondary = COLORS["secondary"].name()
    text_light = COLORS["text_light"].name()
    bg_warm = COLORS["bg_warm"].name()
    dialog_bg = DIALOG_BG
    return f"""
    QMainWindow {{
        background-color: {bg};
    }}
    QDialog, QMessageBox {{
        background-color: {dialog_bg};
    }}
    QWidget {{
        font-family: "Microsoft YaHei";
        color: {text};
    }}
    QLabel {{
        color: {text};
    }}
    QPushButton {{
        font-family: "Microsoft YaHei";
    }}
    QComboBox {{
        background-color: {bg_card};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 5px 10px;
        color: {text};
    }}
    QComboBox:hover {{
        border-color: {primary};
    }}
    QSpinBox, QDoubleSpinBox {{
        background-color: {bg_card};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 5px;
    }}
    QLineEdit {{
        background-color: {bg_card};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 8px;
        color: {text};
    }}
    QTextEdit {{
        background-color: {bg_card};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 8px;
        color: {text};
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background-color: {border_light};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {border};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {primary};
    }}
    QProgressBar {{
        border: 1px solid {border};
        border-radius: 5px;
        text-align: center;
        color: {text};
    }}
    QProgressBar::chunk {{
        background-color: {secondary};
        border-radius: 5px;
    }}
    QCheckBox {{
        color: {text};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
    }}
    QRadioButton {{
        color: {text};
        spacing: 6px;
    }}
    QGroupBox {{
        border: 1px solid {border_light};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 10px;
        color: {COLORS["text_medium"].name()};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    QListWidget {{
        background-color: {bg_card};
        border: 1px solid {border_light};
        border-radius: 8px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {bg_warm};
    }}
    QListWidget::item:selected {{
        background-color: {COLORS["primary_light"].name()};
        color: {text};
    }}
    QListWidget::item:hover {{
        background-color: {bg_warm};
    }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: {border_light};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        background: {primary};
        border-radius: 8px;
        margin: -5px 0;
    }}
    """


def get_poem() -> str:
    """随机获取一句温馨诗句"""
    import random
    return random.choice(POEMS)


def get_canteen_tag(canteen_name: str) -> str:
    """获取食堂标签诗句"""
    return CANTEEN_TAGS.get(canteen_name, "食在燕园，味在其中")


# ============ 图像处理工具 ============

def rounded_pixmap(pixmap, radius=12):
    """将QPixmap裁剪为圆角"""
    from PyQt5.QtGui import QPainterPath, QRegion
    from PyQt5.QtWidgets import QLabel

    # 使用遮罩实现圆角
    rounded = pixmap.copy()
    return rounded
