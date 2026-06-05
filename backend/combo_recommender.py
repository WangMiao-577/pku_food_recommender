"""
combo_recommender.py - 套餐推荐（预设聚餐卡 + 动态营养搭配）
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

PRESET_FILE = Path(__file__).parent.parent / "data" / "preset_combos.json"

SCENE_CALORIE_RANGE = {
    "独自速食": (300, 650),
    "独自慢食": (400, 800),
    "同伴聚餐": (800, 1400),
    "团体宴请": (1200, 2200),
}


class ComboRecommender:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.presets = self._load_presets()

    def _load_presets(self) -> List[Dict]:
        if not PRESET_FILE.exists():
            return []
        with open(PRESET_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _find_dish_by_name(self, name: str, canteen: Optional[str] = None) -> Optional[Dict]:
        for d in self.dm.get_all_dishes():
            if d["name"] == name and (not canteen or d["canteen"] == canteen):
                return d
        for d in self.dm.get_all_dishes():
            if name in d["name"] and (not canteen or d["canteen"] == canteen):
                return d
        return None

    def _build_combo_from_names(self, preset: Dict) -> Optional[Dict]:
        dishes = []
        for name in preset.get("dish_names", []):
            d = self._find_dish_by_name(name, preset.get("canteen"))
            if d:
                dishes.append(d)
        if not dishes:
            return None

        total_price = sum(d["price"] for d in dishes)
        total_cal = sum(d.get("calories", 0) for d in dishes)
        total_protein = sum(d.get("protein", 0) for d in dishes)
        total_fat = sum(d.get("fat", 0) for d in dishes)

        return {
            "combo_id": preset["combo_id"],
            "name": preset["name"],
            "canteen": preset.get("canteen", dishes[0]["canteen"]),
            "canteen_id": dishes[0].get("canteen_id", ""),
            "window": preset.get("window", dishes[0].get("window", "")),
            "dishes": [d["id"] for d in dishes],
            "dish_details": dishes,
            "total_price": round(total_price, 1),
            "original_price": round(total_price * 1.08, 1),
            "total_calories": int(total_cal),
            "total_protein": round(total_protein, 1),
            "total_fat": round(total_fat, 1),
            "suggested_for": preset.get("suggested_for", "2-3人"),
            "reason": preset.get("reason", preset.get("description", "")),
            "scene": preset.get("scene", ""),
            "is_preset": True,
            "description": preset.get("description", ""),
        }

    def get_preset_combos(self, meal_scene: Optional[str] = None, top_n: int = 3) -> List[Dict]:
        combos = []
        for preset in self.presets:
            if meal_scene and preset.get("scene") != meal_scene:
                continue
            combo = self._build_combo_from_names(preset)
            if combo:
                combos.append(combo)
        return combos[:top_n]

    def score_combo_nutrition(self, combo: Dict, meal_scene: Optional[str]) -> float:
        cal = combo.get("total_calories", 0)
        protein = combo.get("total_protein", 0)
        scene = meal_scene or "同伴聚餐"
        cal_range = SCENE_CALORIE_RANGE.get(scene, (600, 1200))
        score = 50.0
        if cal_range[0] <= cal <= cal_range[1]:
            score += 30
        else:
            diff = min(abs(cal - cal_range[0]), abs(cal - cal_range[1]))
            score += max(0, 30 - diff * 0.05)
        if protein >= 20:
            score += 20
        return min(score, 100)

    def generate_dynamic_combos(
        self,
        candidates: List[Dict],
        budget: float,
        meal_scene: Optional[str] = None,
        top_n: int = 2,
    ) -> List[Dict]:
        """动态生成营养合理套餐（补充预设）"""
        from backend.recommender import Recommender
        engine = Recommender(self.dm)
        raw = engine.generate_combos(candidates, budget, top_n=top_n * 2)
        for c in raw:
            c["is_preset"] = False
            c["scene"] = meal_scene or ""
            c["nutrition_score"] = self.score_combo_nutrition(c, meal_scene)
        raw.sort(key=lambda x: x.get("nutrition_score", 0), reverse=True)
        return raw[:top_n]

    def recommend_combos(
        self,
        meal_scene: Optional[str] = None,
        budget: Optional[float] = None,
        candidates: Optional[List[Dict]] = None,
        top_n: int = 3,
    ) -> List[Dict]:
        budget = budget or self.dm.get_budget_limit()
        presets = self.get_preset_combos(meal_scene, top_n=2)
        for p in presets:
            p["nutrition_score"] = self.score_combo_nutrition(p, meal_scene)

        dynamic = []
        if candidates:
            dynamic = self.generate_dynamic_combos(candidates, budget, meal_scene, top_n=2)

        merged = presets + [d for d in dynamic if d["combo_id"] not in {p["combo_id"] for p in presets}]
        merged.sort(key=lambda c: (c.get("is_preset", False), c.get("nutrition_score", 0)), reverse=True)
        return merged[:top_n]
