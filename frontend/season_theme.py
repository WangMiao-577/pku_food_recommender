"""
season_theme.py - 四季主题（背景 + 配色）
根据北京（北半球）季节自动切换，支持设置页手动覆盖。
"""

import os
from datetime import datetime
from typing import Dict, Optional

from PyQt5.QtGui import QColor

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "images", "Season background")

SEASON_LABELS = {
    "spring": "春·未名湖畔",
    "summer": "夏·燕园晴光",
    "autumn": "秋·银杏满园",
    "winter": "冬·雪映博雅",
}

# 背景图不透明度（越高越清晰，温馨淡雅前提下保持较高可见度）
DEFAULT_BG_OPACITY = {
    "spring": 0.78,
    "summer": 0.76,
    "autumn": 0.80,
    "winter": 0.82,
}

SEASON_PALETTES: Dict[str, Dict] = {
    "spring": {
        "primary": "#E8919A",
        "primary_light": "#F4B8BE",
        "primary_dark": "#C56B75",
        "secondary": "#8FB339",
        "secondary_light": "#B5D67A",
        "secondary_dark": "#6A8F2A",
        "bg_main": "#F8FBF4",
        "bg_card": "#FFFCF7",
        "bg_warm": "#F2F8EC",
        "text_dark": "#2D4A32",
        "text_medium": "#4A6B50",
        "text_light": "#7A9A80",
        "accent_gold": "#E8C87A",
        "accent_rose": "#F4B0C7",
        "accent_sage": "#A8D08D",
        "accent_lavender": "#D4C4E8",
        "accent_sky": "#B4D8E7",
        "border": "#C8D8C0",
        "border_light": "#E0EBDA",
        "success": "#8FB339",
        "warning": "#E8C87A",
        "error": "#C56B75",
        "panel_overlay": "rgba(255, 252, 247, 0.78)",
        "sidebar_overlay": "rgba(255, 253, 248, 0.88)",
        "header_overlay": "rgba(255, 252, 248, 0.85)",
    },
    "summer": {
        "primary": "#C0564B",
        "primary_light": "#D88A82",
        "primary_dark": "#9A3F36",
        "secondary": "#6BA3B8",
        "secondary_light": "#9BC5D4",
        "secondary_dark": "#4A7F92",
        "bg_main": "#F5FAFC",
        "bg_card": "#FFFCFA",
        "bg_warm": "#FFF5EE",
        "text_dark": "#3A3A35",
        "text_medium": "#5C5C55",
        "text_light": "#8A8A82",
        "accent_gold": "#E8B86D",
        "accent_rose": "#F497AD",
        "accent_sage": "#8FB339",
        "accent_lavender": "#C8B8D8",
        "accent_sky": "#A9D6E5",
        "border": "#D4C8C0",
        "border_light": "#EAE4DC",
        "success": "#6BA3B8",
        "warning": "#E8B86D",
        "error": "#C0564B",
        "panel_overlay": "rgba(255, 252, 250, 0.76)",
        "sidebar_overlay": "rgba(255, 253, 251, 0.86)",
        "header_overlay": "rgba(255, 252, 250, 0.84)",
    },
    "autumn": {
        "primary": "#C45C2A",
        "primary_light": "#E08A58",
        "primary_dark": "#9A4518",
        "secondary": "#5D8A7B",
        "secondary_light": "#8AB5A6",
        "secondary_dark": "#42685C",
        "bg_main": "#FFFAF3",
        "bg_card": "#FFFCF6",
        "bg_warm": "#FFF5E6",
        "text_dark": "#4A3520",
        "text_medium": "#6B5340",
        "text_light": "#9A8068",
        "accent_gold": "#D4A017",
        "accent_rose": "#D4A088",
        "accent_sage": "#8A9A70",
        "accent_lavender": "#B8A8C8",
        "accent_sky": "#8AB0B8",
        "border": "#D8C4A8",
        "border_light": "#E8DCC8",
        "success": "#5D8A7B",
        "warning": "#D4A017",
        "error": "#B85A40",
        "panel_overlay": "rgba(255, 250, 240, 0.80)",
        "sidebar_overlay": "rgba(255, 251, 243, 0.88)",
        "header_overlay": "rgba(255, 250, 242, 0.86)",
    },
    "winter": {
        "primary": "#B24545",
        "primary_light": "#D07070",
        "primary_dark": "#8A3232",
        "secondary": "#5D6D7E",
        "secondary_light": "#8A98A8",
        "secondary_dark": "#3E4A58",
        "bg_main": "#F8FAFC",
        "bg_card": "#FDFEFF",
        "bg_warm": "#FFF9E8",
        "text_dark": "#2E3A45",
        "text_medium": "#4A5660",
        "text_light": "#7A8894",
        "accent_gold": "#D8C890",
        "accent_rose": "#D8A8A8",
        "accent_sage": "#4A6361",
        "accent_lavender": "#B8C0D0",
        "accent_sky": "#D0E4F5",
        "border": "#C8D4E0",
        "border_light": "#E0E8F0",
        "success": "#4A6361",
        "warning": "#D8C890",
        "error": "#B24545",
        "panel_overlay": "rgba(253, 254, 255, 0.82)",
        "sidebar_overlay": "rgba(252, 253, 255, 0.90)",
        "header_overlay": "rgba(253, 254, 255, 0.88)",
    },
}

SEASON_IMAGES = {
    "spring": "Spring.png",
    "summer": "Summer.png",
    "autumn": "Autumn.png",
    "winter": "Winter.png",
}


def detect_beijing_season(when: Optional[datetime] = None) -> str:
    """北半球（北京）季节：3-5春 6-8夏 9-11秋 12-2冬"""
    month = (when or datetime.now()).month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def _qcolor(hex_str: str) -> QColor:
    return QColor(hex_str)


def palette_to_qcolors(palette: Dict) -> Dict[str, QColor]:
    colors = {}
    for key, val in palette.items():
        if key.endswith("_overlay"):
            colors[key] = val
        else:
            colors[key] = _qcolor(val)
    return colors


class SeasonThemeManager:
    """四季主题管理器"""

    def __init__(self, settings: Optional[Dict] = None):
        settings = settings or {}
        self._mode = settings.get("season_mode", "auto")
        self._manual = settings.get("season_manual", "spring")
        self._bg_opacity = settings.get("season_bg_opacity")
        self._season = self.resolve_season()

    def resolve_season(self, settings: Optional[Dict] = None) -> str:
        if settings:
            mode = settings.get("season_mode", self._mode)
            manual = settings.get("season_manual", self._manual)
        else:
            mode, manual = self._mode, self._manual
        if mode == "auto":
            return detect_beijing_season()
        return manual if manual in SEASON_PALETTES else "spring"

    def update_from_settings(self, settings: Dict):
        self._mode = settings.get("season_mode", self._mode)
        self._manual = settings.get("season_manual", self._manual)
        if "season_bg_opacity" in settings:
            self._bg_opacity = settings["season_bg_opacity"]
        self._season = self.resolve_season(settings)

    @property
    def season(self) -> str:
        return self._season

    @property
    def season_label(self) -> str:
        return SEASON_LABELS.get(self._season, self._season)

    def get_bg_opacity(self) -> float:
        if self._bg_opacity is not None:
            return float(self._bg_opacity)
        return DEFAULT_BG_OPACITY.get(self._season, 0.78)

    def get_background_path(self) -> Optional[str]:
        fname = SEASON_IMAGES.get(self._season)
        if not fname:
            return None
        path = os.path.join(IMAGES_DIR, fname)
        return path if os.path.exists(path) else None

    def get_palette(self) -> Dict:
        return palette_to_qcolors(SEASON_PALETTES[self._season])

    def apply_to_colors_dict(self, colors: Dict):
        """就地更新全局 COLORS 字典"""
        palette = self.get_palette()
        for key, val in palette.items():
            colors[key] = val

    def to_settings_fragment(self) -> Dict:
        return {
            "season_mode": self._mode,
            "season_manual": self._manual,
            "season_bg_opacity": self.get_bg_opacity(),
            "season_active": self._season,
        }
