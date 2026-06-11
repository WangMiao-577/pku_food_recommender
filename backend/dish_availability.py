"""
dish_availability.py - 菜品按星期供应（佟园等食堂）
"""

from datetime import datetime
from typing import Dict, List, Optional, Set

WEEKDAY_CN = {
    "周一": 0, "周二": 1, "周三": 2, "周四": 3,
    "周五": 4, "周六": 5, "周日": 6,
}

DAILY_KEYWORDS = ("一周都有", "每日供应", "AB组轮换")


def parse_weekday_schedule(text: str) -> Optional[List[int]]:
    """
    解析「周几有」字段。
    返回 None 表示每日供应；否则为 weekday 列表（周一=0 … 周日=6）。
    """
    text = (text or "").strip()
    if not text:
        return None
    if any(k in text for k in DAILY_KEYWORDS):
        return None

    days: Set[int] = set()
    for sep in ("、", "，", ",", "/", " "):
        text = text.replace(sep, "|")
    for part in text.split("|"):
        part = part.strip()
        if part in WEEKDAY_CN:
            days.add(WEEKDAY_CN[part])
    return sorted(days) if days else None


def schedule_to_field(days: Optional[List[int]]) -> Optional[List[int]]:
    """写入 dishes.json 的 available_weekdays 字段（None=每日）"""
    if days is None:
        return None
    return sorted(set(days))


def is_available_today(dish: Dict, today: Optional[datetime] = None) -> bool:
    """今日是否供应（无 available_weekdays 则视为每日供应）"""
    days = dish.get("available_weekdays")
    if days is None:
        return True
    if not days:
        return True
    dt = today or datetime.now()
    return dt.weekday() in days


def availability_badge(dish: Dict, today: Optional[datetime] = None) -> str:
    """不可供应时返回角标文案，可供应返回空字符串"""
    if is_available_today(dish, today):
        return ""
    return "今日不出售"
