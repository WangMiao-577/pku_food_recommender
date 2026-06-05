"""
food_footprint.py - 美食足迹日志（滚动保留 7 天 + 永久/临时收藏）
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

ENCOURAGEMENTS = [
    "低谷也是人生的一道菜，下一顿会更好的。",
    "今天辛苦了，好好吃饭就是在照顾自己。",
    "燕园的晚风里，总有一盏灯为你留着。",
    "不必对自己太苛刻，暖胃的食物会慢慢暖胃的心。",
    "这一餐不算完美，但你在努力生活，这就很棒。",
    "食堂师傅的手艺里，藏着整座校园的温柔。",
    "明天太阳还会升起，明天还有新的味道在等你。",
    "一个人吃饭也没关系，你值得被好好对待。",
]


class FoodFootprintManager:
    """用餐足迹：专用日志文件，仅保留近 7 天"""

    RETENTION_DAYS = 7

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.footprint_file = os.path.join(data_dir, "food_footprint.json")
        self.favorites_file = os.path.join(data_dir, "footprint_favorites.json")
        self.records: List[Dict] = self._load(self.footprint_file)
        self.favorites: List[Dict] = self._load(self.favorites_file)
        self._prune_old()

    @staticmethod
    def _load(path: str) -> List:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_footprint(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.footprint_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def _save_favorites(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.favorites_file, "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)

    def _cutoff(self) -> datetime:
        return datetime.now() - timedelta(days=self.RETENTION_DAYS)

    def _prune_old(self):
        cutoff = self._cutoff()
        kept = [r for r in self.records if datetime.fromisoformat(r["time"]) > cutoff]
        if len(kept) != len(self.records):
            self.records = kept
            self._save_footprint()

    def _week_records(self) -> List[Dict]:
        cutoff = self._cutoff()
        return sorted(
            [r for r in self.records if datetime.fromisoformat(r["time"]) > cutoff],
            key=lambda x: x["time"],
            reverse=True,
        )

    def add_record(
        self,
        dish_id: str,
        dish_name: str,
        canteen: str,
        cuisine: str = "",
        mood: str = "neutral",
        companions: str = "alone",
        note: str = "",
    ) -> Dict:
        """新增足迹（mood: good/bad/neutral, companions: alone/friends）"""
        record = {
            "id": f"fp_{len(self.records) + 1:04d}_{int(datetime.now().timestamp())}",
            "dish_id": dish_id,
            "dish_name": dish_name,
            "canteen": canteen,
            "cuisine": cuisine or "其他",
            "time": datetime.now().isoformat(),
            "mood": mood if mood in ("good", "bad", "neutral") else "neutral",
            "companions": companions if companions in ("alone", "friends") else "alone",
            "favorite": None,
            "note": note,
        }
        self.records.insert(0, record)
        self._prune_old()
        self._save_footprint()
        return record

    def get_week_stats(self) -> Dict:
        records = self._week_records()
        if not records:
            return {"has_data": False, "records": []}

        canteens = {r["canteen"] for r in records}
        cuisines = {r.get("cuisine") or "其他" for r in records}
        alone = sum(1 for r in records if r.get("companions") == "alone")
        friends = sum(1 for r in records if r.get("companions") == "friends")

        good_meals = [r for r in records if r.get("mood") == "good"]
        bad_meals = [r for r in records if r.get("mood") == "bad"]
        good_pick = good_meals[0] if good_meals else None
        bad_pick = bad_meals[0] if bad_meals else None

        return {
            "has_data": True,
            "records": records,
            "canteen_count": len(canteens),
            "meal_count": len(records),
            "cuisine_count": len(cuisines),
            "alone_count": alone,
            "friends_count": friends,
            "good_meal": good_pick,
            "bad_meal": bad_pick,
            "encouragement": random.choice(ENCOURAGEMENTS) if bad_pick else "",
        }

    def random_encouragement(self) -> str:
        return random.choice(ENCOURAGEMENTS)

    def set_favorite(self, record_id: str, level: Optional[str]) -> bool:
        """level: temp / perm / None 取消"""
        rec = next((r for r in self.records if r["id"] == record_id), None)
        if not rec:
            return False

        if level == "temp":
            rec["favorite"] = "temp"
        elif level == "perm":
            rec["favorite"] = "perm"
            if not any(f.get("footprint_id") == record_id for f in self.favorites):
                self.favorites.insert(0, {
                    "footprint_id": record_id,
                    "dish_id": rec["dish_id"],
                    "dish_name": rec["dish_name"],
                    "canteen": rec["canteen"],
                    "time": rec["time"],
                    "note": rec.get("note", ""),
                    "saved_at": datetime.now().isoformat(),
                })
            self._save_favorites()
        else:
            rec["favorite"] = None
            self.favorites = [f for f in self.favorites if f.get("footprint_id") != record_id]
            self._save_favorites()

        self._save_footprint()
        return True

    def get_favorites(self) -> List[Dict]:
        return list(self.favorites)

    def should_show_weekly_popup(self, settings: Dict) -> bool:
        if not self._week_records():
            return False
        last = settings.get("footprint_popup_last")
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            return (datetime.now() - last_dt).days >= 7
        except Exception:
            return True

    def mark_popup_shown(self, settings: Dict) -> Dict:
        settings = dict(settings)
        settings["footprint_popup_last"] = datetime.now().isoformat()
        return settings

    def backfill_from_history(self, history: List[Dict], dishes_by_id: Dict):
        """首次使用时，从就餐历史回填近 7 天足迹（仅当足迹为空）"""
        if self.records:
            return
        cutoff = self._cutoff()
        moods = ["good", "neutral", "bad", "neutral"]
        for i, h in enumerate(history):
            try:
                t = datetime.fromisoformat(h["time"])
            except Exception:
                continue
            if t <= cutoff:
                continue
            dish = dishes_by_id.get(h.get("dish_id"), {})
            self.records.append({
                "id": f"fp_bf_{i:04d}",
                "dish_id": h.get("dish_id", ""),
                "dish_name": h.get("dish_name", ""),
                "canteen": h.get("canteen", ""),
                "cuisine": dish.get("cuisine", "其他"),
                "time": h["time"],
                "mood": moods[i % len(moods)],
                "companions": "friends" if i % 4 == 0 else "alone",
                "favorite": None,
                "note": "",
            })
        if self.records:
            self.records.sort(key=lambda x: x["time"], reverse=True)
            self._save_footprint()
