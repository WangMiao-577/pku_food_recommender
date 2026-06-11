"""
recommender.py - 推荐算法核心模块 v2.0
实现召回+排序两阶段推荐：
  Retrieve: 场景召回 / 需求召回 / 模式召回（三路并行）
  Rank: 多因子加权排序 + ε-greedy 扰动
  Combo: 同伴/团体场景下的套餐组合生成
"""

import random
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set

from backend.data_manager import DataManager, CAMPUS_REGIONS, LOCATION_TO_REGIONS
from backend.campus_navigation import CampusNavigationService
from backend.dish_availability import is_available_today


# ============ 常量配置 ============

GLOBAL_AVG_RATING = 3.8
BAYESIAN_C = 10

NUTRITION_GOALS = {
    "减脂": {"calories": (200, 400), "protein": (20, 40), "fat": (5, 15)},
    "增肌": {"calories": (400, 700), "protein": (25, 50), "fat": (10, 30)},
    "均衡": {"calories": (300, 600), "protein": (15, 35), "fat": (10, 25)},
    "无": None,
}

# 排序权重：稳定模式 / 探索模式（含出餐/营养/聚餐维度）
RANK_WEIGHTS = {
    "stable": {
        "preference": 0.28, "quality": 0.22, "location": 0.18,
        "freshness": 0.12, "explore": 0.05, "time": 0.08, "nutrition": 0.05, "social": 0.02,
    },
    "explore": {
        "preference": 0.20, "quality": 0.18, "location": 0.12,
        "freshness": 0.08, "explore": 0.28, "time": 0.06, "nutrition": 0.04, "social": 0.04,
    },
}

# 场景下动态加权（参考旧版 rush/healthy/social 思路）
SCENE_WEIGHT_DELTA = {
    "独自速食": {"time": 0.12, "nutrition": -0.04, "social": -0.02, "location": 0.05},
    "独自慢食": {"time": -0.06, "nutrition": 0.10, "quality": 0.05, "social": -0.02},
    "同伴聚餐": {"social": 0.12, "nutrition": 0.04, "time": -0.04, "preference": 0.04},
    "团体宴请": {"social": 0.15, "quality": 0.06, "time": -0.05, "nutrition": 0.02},
}

# ε-greedy 探索概率
EPSILON = {"stable": 0.05, "explore": 0.40}

MEAL_SCENES = ["独自速食", "独自慢食", "同伴聚餐", "团体宴请"]

STAPLE_KEYWORDS = {"面食", "米饭", "管饱", "早餐", "面", "饺", "包"}
MAIN_KEYWORDS = {"招牌", "经典", "下饭", "聚餐", "高蛋白", "热门"}
SOUP_SIDE_KEYWORDS = {"汤", "粥", "蔬菜", "清淡", "素食", "健康"}

LARGE_CANTEENS = {"家园食堂", "农园食堂", "学一食堂", "学五食堂", "燕南美食"}

# 旧模式 -> 新参数映射（向后兼容）
LEGACY_MODE_MAP = {
    "normal": {"recommend_mode": "stable", "meal_scene": None},
    "rush": {"recommend_mode": "stable", "meal_scene": "独自速食"},
    "explore": {"recommend_mode": "explore", "meal_scene": None},
    "healthy": {"recommend_mode": "stable", "meal_scene": "独自慢食"},
    "social": {"recommend_mode": "stable", "meal_scene": "同伴聚餐"},
}


class Recommender:
    """推荐引擎 v2.0 - 召回+排序两阶段"""

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.nav = CampusNavigationService.get_instance()

    # ==================== 上下文解析 ====================

    def _resolve_context(self, mode: str, context: Optional[Dict]) -> Dict:
        """合并 legacy mode、settings 与调用方 context"""
        ctx = dict(context or {})
        legacy = LEGACY_MODE_MAP.get(mode, LEGACY_MODE_MAP["normal"])

        settings = self.dm.get_settings()
        profile = self.dm.get_profile()

        recommend_mode = ctx.get("recommend_mode")
        if not recommend_mode:
            if settings.get("explore_mode"):
                recommend_mode = "explore"
            elif profile.get("default_mode") in ("stable", "explore"):
                recommend_mode = profile["default_mode"]
            elif settings.get("default_recommend_mode") in ("stable", "explore"):
                recommend_mode = settings["default_recommend_mode"]
            else:
                recommend_mode = legacy["recommend_mode"]

        meal_scene = ctx.get("meal_scene") or legacy.get("meal_scene")
        if not meal_scene and profile.get("meal_scenes"):
            meal_scene = profile["meal_scenes"][-1]

        return {
            "recommend_mode": recommend_mode,
            "meal_scene": meal_scene,
            "budget_limit": ctx.get("budget_limit", self.dm.get_budget_limit()),
            "preferred_flavors": ctx.get("preferred_flavors") or self.dm.get_preferred_flavors(),
            "location": ctx.get("location") or profile.get("current_location", ""),
            "location_node_id": ctx.get("location_node_id") or profile.get("current_location_node_id"),
            "include_combos": ctx.get(
                "include_combos",
                meal_scene in ("同伴聚餐", "团体宴请"),
            ),
            "location_preference": ctx.get("location_preference", ""),
        }

    @staticmethod
    def _get_meal_type(hour: float) -> str:
        if 6 <= hour < 10:
            return "breakfast"
        if 10 <= hour < 14.5:
            return "lunch"
        if 14.5 <= hour < 17:
            return "afternoon"
        if 17 <= hour < 20.5:
            return "dinner"
        return "late_night"

    def _normalize_dish(self, dish: Dict) -> Dict:
        """补齐 v2 字段默认值"""
        d = dish.copy()
        if "window_number" not in d:
            d["window_number"] = hash(d.get("window", "")) % 6 + 1
        if "portion_size" not in d:
            tags = d.get("tags", [])
            if any(k in tags for k in ("管饱", "聚餐")):
                d["portion_size"] = "L"
            elif d.get("price", 0) <= 10:
                d["portion_size"] = "S"
            else:
                d["portion_size"] = "M"
        if "related_dishes" not in d:
            d["related_dishes"] = []
        if not d.get("location_hint") and d.get("window"):
            floor = d.get("floor")
            prefix = f"{d.get('canteen', '')}"
            if floor:
                prefix += f"{'地下' if floor == 0 else f'{floor}层'}"
            d["location_hint"] = f"{prefix}，{d['window']}" if prefix else d["window"]
        return d

    # ==================== Retrieve: 三路召回 ====================

    def _recall_scene(self, dishes: List[Dict], scene: Optional[str]) -> List[Dict]:
        if not scene:
            return dishes

        if scene == "独自速食":
            return [
                d for d in dishes
                if d.get("prep_time", 10) <= 8 and d["price"] <= 25
            ]
        if scene == "独自慢食":
            return [
                d for d in dishes
                if d.get("rating", 0) >= 4.0
                or d.get("appearance", 0) >= 4
                or any(t in d.get("tags", []) for t in ("招牌", "特色", "经典"))
            ]
        if scene == "同伴聚餐":
            return [
                d for d in dishes
                if d.get("portion_size") == "L"
                or any(t in d.get("tags", []) for t in ("聚餐", "管饱", "热门", "下饭"))
                or d.get("rating_count", 0) >= 150
            ]
        if scene == "团体宴请":
            return [
                d for d in dishes
                if (d["price"] >= 15 or d.get("rating", 0) >= 4.3)
                and d["canteen"] in LARGE_CANTEENS
            ]
        return dishes

    def _recall_demand(self, dishes: List[Dict], ctx: Dict) -> List[Dict]:
        profile = self.dm.get_profile()
        budget = ctx["budget_limit"]
        flavors = ctx["preferred_flavors"]
        disliked = set(self.dm.get_disliked_flavors())
        taboos = set(profile.get("constraints", {}).get("taboos", []))
        taboos |= set(profile.get("disliked_ingredients", []))

        now = datetime.now()
        hour = now.hour + now.minute / 60
        meal_type = self._get_meal_type(hour)

        result = []
        for d in dishes:
            if d["price"] > budget:
                continue
            if not d.get("hours", {}).get(meal_type, True):
                continue
            if taboos and any(t in d.get("tags", []) or t in d.get("name", "") for t in taboos):
                continue
            dish_flavors = set(d.get("flavor", []))
            if disliked and dish_flavors & disliked:
                continue
            if flavors and not (dish_flavors & set(flavors)):
                continue
            if not self._passes_location(d, ctx):
                continue
            result.append(d)
        return result

    def _passes_location(self, dish: Dict, ctx: Dict) -> bool:
        node_id = ctx.get("location_node_id")
        if node_id:
            dist = self.nav.graph_distance_to_canteen(node_id, dish["canteen"])
            if dist is not None and dist > 0.32:
                return False
            return True

        location = ctx.get("location", "")
        if not location:
            return True
        target_regions = LOCATION_TO_REGIONS.get(location)
        if not target_regions:
            return True
        region = self.dm.get_canteen_region(dish["canteen"])
        return region in target_regions

    def _score_location(self, dish: Dict, ctx: Dict) -> Tuple[float, str]:
        score, note = 70.0, "一般距离"
        node_id = ctx.get("location_node_id")
        if node_id:
            score, note = self.nav.location_score_for_canteen(node_id, dish["canteen"])
        else:
            location = ctx.get("location", "")
            if location:
                target_regions = LOCATION_TO_REGIONS.get(location)
                if target_regions:
                    region = self.dm.get_canteen_region(dish["canteen"])
                    if region in target_regions:
                        score, note = 100.0, "就在附近"
                    elif region and target_regions:
                        score, note = 45.0, "需多走几步"

        hint = dish.get("location_hint") or ""
        window = dish.get("window", "")
        pref = ctx.get("location_preference", "")
        if pref:
            if pref in hint or pref in window:
                score = min(score + 22, 100)
                note = f"档口匹配·{pref}"
            elif any(k in hint for k in pref.split() if len(k) >= 2):
                score = min(score + 12, 100)
                note = "位置相近"
        elif hint:
            score = min(score + 4, 100)
            if "层" in hint:
                note = hint.split("，")[0] if "，" in hint else hint[:12]

        return score, note

    def _score_time(self, dish: Dict, ctx: Dict) -> Tuple[float, str]:
        prep = dish.get("prep_time", 10)
        scene = ctx.get("meal_scene")
        if scene == "独自速食":
            if prep <= 5:
                return 100.0, f"出餐快·约{prep}分钟"
            if prep <= 8:
                return 75.0, f"较快·{prep}分钟"
            return max(20, 60 - prep * 3), f"需等待·{prep}分钟"
        if scene in ("同伴聚餐", "团体宴请"):
            return 60.0, "可接受等待"
        if prep <= 8:
            return 85.0, "出餐适中"
        return 55.0, "现做菜品"

    def _score_nutrition(self, dish: Dict, ctx: Dict) -> Tuple[float, str]:
        goal = self.dm.get_nutrition_goal()
        cal = dish.get("calories", 400)
        protein = dish.get("protein", 0)
        fat = dish.get("fat", 0)
        scene = ctx.get("meal_scene")

        if scene == "独自速食" and cal <= 500:
            return 80.0, "轻量一餐"
        if scene in ("同伴聚餐", "团体宴请") and cal >= 350:
            return 75.0, "分量足"

        if goal in NUTRITION_GOALS and NUTRITION_GOALS[goal]:
            target = NUTRITION_GOALS[goal]
            score = 50.0
            notes = []
            cal_range = target.get("calories")
            if cal_range and cal_range[0] <= cal <= cal_range[1]:
                score += 25
                notes.append("热量合适")
            prot_range = target.get("protein")
            if prot_range and prot_range[0] <= protein <= prot_range[1]:
                score += 15
                notes.append("蛋白达标")
            fat_range = target.get("fat")
            if fat_range and fat_range[0] <= fat <= fat_range[1]:
                score += 10
                notes.append("脂肪适中")
            return min(score, 100), "; ".join(notes) or "营养一般"

        if 300 <= cal <= 600:
            return 70.0, "营养均衡"
        return 55.0, "营养一般"

    def _score_social(self, dish: Dict, ctx: Dict) -> Tuple[float, str]:
        scene = ctx.get("meal_scene")
        if scene not in ("同伴聚餐", "团体宴请"):
            return 50.0, "单人适用"

        score = 45.0
        tags = set(dish.get("tags", []))
        if dish.get("portion_size") == "L":
            score += 25
        if tags & {"聚餐", "管饱", "热门", "下饭"}:
            score += 20
        if dish.get("rating_count", 0) >= 100:
            score += 10
        note = "适合分享" if score >= 70 else "可搭配点餐"
        return min(score, 100), note

    def _recall_mode(self, dishes: List[Dict], recommend_mode: str) -> List[Dict]:
        eaten_7 = self.dm.get_eaten_dish_ids(days=7)
        eaten_30 = self.dm.get_eaten_dish_ids(days=30)

        if recommend_mode == "stable":
            if eaten_30:
                pool = [d for d in dishes if d["id"] in eaten_30]
                if pool:
                    return pool
            return self._get_trending_dishes(max(len(dishes) // 2, 5))

        pool = [d for d in dishes if d["id"] not in eaten_7]
        return pool if pool else dishes

    def _merge_recall_pools(self, *pools: List[Dict]) -> List[Dict]:
        seen: Set[str] = set()
        merged = []
        for pool in pools:
            for d in pool:
                if d["id"] not in seen:
                    seen.add(d["id"])
                    merged.append(d)
        return merged

    def _retrieve(self, ctx: Dict) -> List[Dict]:
        all_dishes = [
            self._normalize_dish(d) for d in self.dm.get_all_dishes()
            if is_available_today(d)
        ]
        if not all_dishes:
            all_dishes = [self._normalize_dish(d) for d in self.dm.get_all_dishes()]
        scene_pool = self._recall_scene(all_dishes, ctx.get("meal_scene"))
        demand_pool = self._recall_demand(all_dishes, ctx)
        mode_pool = self._recall_mode(all_dishes, ctx["recommend_mode"])

        merged = self._merge_recall_pools(scene_pool, demand_pool, mode_pool)
        if not merged:
            merged = self._recall_demand(all_dishes, ctx)
        if not merged:
            merged = all_dishes[:]
        return merged

    # ==================== Rank: 多因子排序 ====================

    def _score_preference(self, dish: Dict, ctx: Dict) -> Tuple[float, str]:
        score = 50.0
        notes = []

        flavors = set(ctx.get("preferred_flavors", []))
        dish_flavors = set(dish.get("flavor", []))
        if flavors:
            overlap = len(flavors & dish_flavors)
            if overlap:
                score += min(30, overlap * 15)
                notes.append("口味匹配")
            else:
                score -= 20

        budget = ctx.get("budget_limit", 50)
        if dish["price"] <= budget * 0.7:
            score += 15
            notes.append("预算友好")
        elif dish["price"] > budget * 0.9:
            score -= 10

        goal = self.dm.get_nutrition_goal()
        if goal in NUTRITION_GOALS and NUTRITION_GOALS[goal]:
            target = NUTRITION_GOALS[goal]
            cal_range = target.get("calories")
            if cal_range and cal_range[0] <= dish.get("calories", 400) <= cal_range[1]:
                score += 15
                notes.append("营养匹配")

        preferred_canteens = self.dm.get_profile().get("preferred_canteens", [])
        canteen_id = dish.get("canteen_id") or dish.get("canteen", "")
        if preferred_canteens and canteen_id in preferred_canteens:
            score += 10
            notes.append("偏好食堂")

        loc_pref = ctx.get("location_preference", "")
        hint = dish.get("location_hint", "")
        if loc_pref and (loc_pref in hint or loc_pref in dish.get("window", "")):
            score += 12
            notes.append(f"档口·{loc_pref}")

        return min(max(score, 0), 100), "; ".join(notes) or "一般匹配"

    def _score_quality(self, dish: Dict) -> Tuple[float, str]:
        rating = dish.get("rating", 3.5)
        count = dish.get("rating_count", 0)
        appearance = dish.get("appearance", 3)
        bayesian = (BAYESIAN_C * GLOBAL_AVG_RATING + count * rating) / (BAYESIAN_C + max(count, 1))
        rating_score = (bayesian / 5.0) * 70
        appearance_score = (appearance / 5.0) * 15
        popularity = min(count / 200, 1.0) * 15
        total = rating_score + appearance_score + popularity
        return min(total, 100), f"评分{bayesian:.1f}({count}人评)"

    def _score_freshness(self, dish: Dict, recommend_mode: str) -> Tuple[float, str]:
        eaten_count = self.dm.get_eaten_count(dish["id"], days=30)
        last_eaten = self.dm.get_last_eaten_time(dish["id"])

        if recommend_mode == "stable":
            if eaten_count >= 3:
                return 100.0, "常点熟悉"
            if eaten_count >= 1:
                return 85.0, "最近吃过"
            if last_eaten is None:
                return 40.0, "尚未尝试"
            return 60.0, "偶尔吃"

        if self.dm.is_recently_eaten(dish["id"], days=7):
            return 10.0, "刚吃过"
        if last_eaten is None:
            return 100.0, "全新菜品"
        days_ago = (datetime.now() - last_eaten).days
        return min(60 + days_ago * 3, 100), f"{days_ago}天未吃"

    def _score_explore(self, dish: Dict, recommend_mode: str) -> Tuple[float, str]:
        if recommend_mode == "explore":
            if not self.dm.has_eating_history() or self.dm.get_eaten_count(dish["id"], days=365) == 0:
                return 30.0, "新发现"
            if self.dm.is_recently_eaten(dish["id"], days=30):
                return 5.0, "近期已吃"
            return 20.0, "可尝试"

        if self.dm.get_eaten_count(dish["id"], days=30) >= 2:
            return 25.0, "熟悉味道"
        return 10.0, "稳定选择"

    def _resolve_rank_weights(self, ctx: Dict) -> Dict[str, float]:
        weights = dict(RANK_WEIGHTS[ctx["recommend_mode"]])
        is_cold_start = not self.dm.has_eating_history() and not self.dm.get_preferred_flavors()
        if is_cold_start:
            weights = {
                "preference": 0.16, "quality": 0.38, "location": 0.14,
                "freshness": 0.08, "explore": 0.05, "time": 0.08,
                "nutrition": 0.06, "social": 0.05,
            }

        scene = ctx.get("meal_scene")
        if scene in SCENE_WEIGHT_DELTA:
            for key, delta in SCENE_WEIGHT_DELTA[scene].items():
                if key in weights:
                    weights[key] = max(0.0, weights[key] + delta)

        total = sum(weights.values()) or 1.0
        return {k: v / total for k, v in weights.items()}

    def _rank_dishes(self, dishes: List[Dict], ctx: Dict) -> List[Tuple[Dict, float, Dict]]:
        weights = self._resolve_rank_weights(ctx)

        scored = []
        for dish in dishes:
            s_pref, d_pref = self._score_preference(dish, ctx)
            s_qual, d_qual = self._score_quality(dish)
            s_loc, d_loc = self._score_location(dish, ctx)
            s_fresh, d_fresh = self._score_freshness(dish, ctx["recommend_mode"])
            s_explore, d_explore = self._score_explore(dish, ctx["recommend_mode"])
            s_time, d_time = self._score_time(dish, ctx)
            s_nutri, d_nutri = self._score_nutrition(dish, ctx)
            s_social, d_social = self._score_social(dish, ctx)

            final = (
                weights["preference"] * s_pref
                + weights["quality"] * s_qual
                + weights["location"] * s_loc
                + weights["freshness"] * s_fresh
                + weights["explore"] * s_explore
                + weights.get("time", 0) * s_time
                + weights.get("nutrition", 0) * s_nutri
                + weights.get("social", 0) * s_social
            )
            details = {
                "preference": d_pref,
                "quality": d_qual,
                "location": d_loc,
                "freshness": d_fresh,
                "explore": d_explore,
                "time": d_time,
                "nutrition": d_nutri,
                "social": d_social,
            }
            scored.append((dish, final, details))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ==================== ε-greedy 扰动 ====================

    def _perturb_output(
        self,
        scored: List[Tuple[Dict, float, Dict]],
        top_k: int,
        recommend_mode: str,
    ) -> List[Dict]:
        epsilon = EPSILON.get(recommend_mode, 0.15)
        if not scored:
            return []

        result = []
        used_indices: Set[int] = set()
        greedy_count = max(1, int(top_k * (1 - epsilon)))

        for i in range(min(greedy_count, len(scored))):
            dish_data = scored[i][0].copy()
            dish_data["_score"] = round(scored[i][1], 2)
            dish_data["_score_details"] = scored[i][2]
            dish_data["_recommend_mode"] = recommend_mode
            if recommend_mode == "stable" and self.dm.get_eaten_count(dish_data["id"], days=30) >= 1:
                dish_data["_mode_label"] = "常点"
            elif recommend_mode == "explore":
                dish_data["_mode_label"] = "新发现"
                dish_data["_is_explore"] = True
            result.append(dish_data)
            used_indices.add(i)

        explore_count = top_k - len(result)
        if explore_count > 0 and len(scored) > len(result):
            remaining = [i for i in range(len(scored)) if i not in used_indices]
            if remaining:
                sample_size = min(explore_count, len(remaining))
                chosen = random.sample(remaining[: max(len(remaining), 20)], sample_size)
                for idx in chosen:
                    dish_data = scored[idx][0].copy()
                    dish_data["_score"] = round(scored[idx][1], 2)
                    dish_data["_score_details"] = scored[idx][2]
                    dish_data["_recommend_mode"] = recommend_mode
                    dish_data["_is_explore"] = True
                    dish_data["_mode_label"] = "探索推荐"
                    result.append(dish_data)

        return result

    # ==================== 套餐组合 ====================

    def _is_staple(self, dish: Dict) -> bool:
        text = dish["name"] + " " + " ".join(dish.get("tags", []))
        return any(k in text for k in STAPLE_KEYWORDS)

    def _is_main(self, dish: Dict) -> bool:
        text = dish["name"] + " " + " ".join(dish.get("tags", []))
        return any(k in text for k in MAIN_KEYWORDS) or dish.get("protein", 0) >= 20

    def _is_side_or_soup(self, dish: Dict) -> bool:
        text = dish["name"] + " " + " ".join(dish.get("tags", []))
        return any(k in text for k in SOUP_SIDE_KEYWORDS) or dish.get("calories", 999) < 250

    def _flavors_compatible(self, dishes: List[Dict]) -> bool:
        spicy = {"辣", "麻辣", "麻"}
        for d in dishes:
            flavors = set(d.get("flavor", []))
            others = [o for o in dishes if o["id"] != d["id"]]
            if flavors & spicy:
                for o in others:
                    if set(o.get("flavor", [])) & spicy:
                        return False
        return True

    def generate_combos(
        self,
        candidates: Optional[List[Dict]] = None,
        budget: Optional[float] = None,
        top_n: int = 2,
    ) -> List[Dict]:
        """生成套餐推荐（同伴/团体场景）"""
        budget = budget or self.dm.get_budget_limit()
        dishes = candidates or self.dm.get_all_dishes()
        dishes = [self._normalize_dish(d) for d in dishes if d["price"] <= budget]

        by_canteen: Dict[str, List[Dict]] = {}
        for d in dishes:
            by_canteen.setdefault(d["canteen"], []).append(d)

        combos = []
        for canteen, items in by_canteen.items():
            if len(items) < 2:
                continue
            items.sort(key=lambda x: x.get("rating", 0), reverse=True)

            for main in items:
                if not self._is_main(main):
                    continue
                for side in items:
                    if side["id"] == main["id"]:
                        continue
                    if abs(main.get("window_number", 1) - side.get("window_number", 1)) > 2:
                        continue
                    if not self._is_side_or_soup(side) and not self._is_staple(side):
                        continue

                    combo_dishes = [main, side]
                    total_price = main["price"] + side["price"]
                    total_cal = main.get("calories", 0) + side.get("calories", 0)
                    total_protein = main.get("protein", 0) + side.get("protein", 0)
                    total_fat = main.get("fat", 0) + side.get("fat", 0)

                    staple = next((d for d in items if self._is_staple(d) and d["id"] not in {main["id"], side["id"]}), None)
                    if staple and total_price + staple["price"] <= budget:
                        combo_dishes.append(staple)
                        total_price += staple["price"]
                        total_cal += staple.get("calories", 0)
                        total_protein += staple.get("protein", 0)
                        total_fat += staple.get("fat", 0)

                    if total_price > budget:
                        continue
                    if not (500 <= total_cal <= 1400):
                        continue
                    if not self._flavors_compatible(combo_dishes):
                        continue

                    original = sum(d["price"] for d in combo_dishes)
                    combo = {
                        "combo_id": f"combo_{canteen}_{main['id']}_{side['id']}",
                        "name": f"{main['name']}套餐",
                        "canteen": canteen,
                        "canteen_id": main.get("canteen_id", ""),
                        "window": main.get("window", ""),
                        "dishes": [d["id"] for d in combo_dishes],
                        "dish_details": combo_dishes,
                        "total_price": round(total_price, 1),
                        "original_price": round(original, 1),
                        "total_calories": int(total_cal),
                        "total_protein": round(total_protein, 1),
                        "total_fat": round(total_fat, 1),
                        "suggested_for": "2-4人" if len(combo_dishes) >= 2 else "1-2人",
                        "reason": "同窗口取餐，口味互补不冲突",
                    }
                    combos.append(combo)
                    if len(combos) >= top_n * 3:
                        break
                if len(combos) >= top_n * 3:
                    break

        combos.sort(key=lambda c: (c["total_price"], -c["total_calories"]))
        return combos[:top_n]

    # ==================== 主推荐流程 ====================

    def recommend(
        self,
        top_k: int = 5,
        mode: str = "normal",
        context: Optional[Dict] = None,
    ) -> List[Dict]:
        """主推荐入口（向后兼容 mode 参数）"""
        return self.recommend_full(top_k=top_k, mode=mode, context=context)["dishes"]

    def recommend_full(
        self,
        top_k: int = 5,
        mode: str = "normal",
        context: Optional[Dict] = None,
    ) -> Dict:
        """完整推荐：菜品列表 + 可选套餐"""
        ctx = self._resolve_context(mode, context)
        candidates = self._retrieve(ctx)
        scored = self._rank_dishes(candidates, ctx)
        dishes = self._perturb_output(scored, top_k, ctx["recommend_mode"])

        combos = []
        if ctx.get("include_combos"):
            from backend.combo_recommender import ComboRecommender
            combo_engine = ComboRecommender(self.dm)
            combo_candidates = candidates[: max(top_k * 3, 20)]
            combos = combo_engine.recommend_combos(
                meal_scene=ctx.get("meal_scene"),
                budget=ctx["budget_limit"],
                candidates=combo_candidates,
                top_n=3,
            )

        return {
            "dishes": dishes,
            "combos": combos,
            "recommend_mode": ctx["recommend_mode"],
            "meal_scene": ctx.get("meal_scene"),
            "source": "local_algorithm",
        }

    def get_quick_pick(self, mode: str = "stable") -> Optional[Dict]:
        """快速推荐一个今日最佳"""
        recs = self.recommend(top_k=1, mode=mode if mode in LEGACY_MODE_MAP else "normal",
                              context={"recommend_mode": mode} if mode in ("stable", "explore") else None)
        return recs[0] if recs else None

    def get_alternatives(self, dish_id: str, count: int = 3) -> List[Dict]:
        """获取某菜品的替代品（优先 related_dishes）"""
        dish = self.dm.get_dish_by_id(dish_id)
        if not dish:
            return []

        related_ids = dish.get("related_dishes", [])
        related = []
        for rid in related_ids:
            d = self.dm.get_dish_by_id(rid)
            if d:
                related.append(self._normalize_dish(d))
        if len(related) >= count:
            return related[:count]

        all_dishes = self.dm.get_all_dishes()
        candidates = [d for d in all_dishes if d["id"] != dish_id and d["id"] not in related_ids]

        same_cuisine = [d for d in candidates if d.get("cuisine") == dish.get("cuisine")]
        if len(same_cuisine) + len(related) >= count:
            combined = related + same_cuisine
            return [self._normalize_dish(d) for d in combined[:count]]

        flavors = set(dish.get("flavor", []))
        same_flavor = [d for d in candidates if any(f in d.get("flavor", []) for f in flavors)]
        combined = related + same_cuisine + [d for d in same_flavor if d not in same_cuisine]
        if len(combined) >= count:
            return [self._normalize_dish(d) for d in combined[:count]]

        return [self._normalize_dish(d) for d in
                sorted(candidates, key=lambda x: x.get("rating", 0), reverse=True)[:count]]

    def _get_trending_dishes(self, count: int) -> List[Dict]:
        dishes = self.dm.get_all_dishes()
        return sorted(
            dishes,
            key=lambda x: (x.get("rating_count", 0), x.get("rating", 0)),
            reverse=True,
        )[:count]

    def get_trending(self, count: int = 5) -> List[Dict]:
        """获取热门菜品"""
        return self._get_trending_dishes(count)


def test_recommender():
    """推荐引擎测试"""
    print("=" * 50)
    print("推荐引擎 v2.0 测试")
    print("=" * 50)

    dm = DataManager(data_dir="data")
    engine = Recommender(dm)

    print("\n【测试1】稳定模式推荐 top-5:")
    result = engine.recommend_full(top_k=5, mode="normal", context={"recommend_mode": "stable"})
    for i, r in enumerate(result["dishes"], 1):
        label = r.get("_mode_label", "")
        explore_tag = " [探索]" if r.get("_is_explore") else ""
        print(f"  {i}. {r['name']} ({r['canteen']}) 综合分:{r['_score']:.1f} {label}{explore_tag}")

    print("\n【测试2】探索模式推荐 top-3:")
    recs = engine.recommend(top_k=3, mode="explore")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r['name']} - {r.get('_mode_label', '')}")

    print("\n【测试3】聚餐场景 + 套餐:")
    combo_result = engine.recommend_full(
        top_k=3,
        mode="social",
        context={"meal_scene": "同伴聚餐", "budget_limit": 40},
    )
    for c in combo_result["combos"]:
        names = " + ".join(d["name"] for d in c["dish_details"])
        print(f"  combo: {names} @ {c['canteen']}  price={c['total_price']}")

    print("\n【测试4】热门推荐:")
    for i, d in enumerate(engine.get_trending(3), 1):
        print(f"  {i}. {d['name']} - {d['rating']}分")

    print("\n所有测试通过!")


if __name__ == "__main__":
    test_recommender()
