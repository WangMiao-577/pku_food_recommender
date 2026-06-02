"""
recommender.py - 推荐算法核心模块（重构版）
保持原有变量名与对外接口不变，内部升级算法细节。
"""

import math
import random
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from backend.data_manager import DataManager, CANTEENS

# ============ 常量配置（完全保持原样） ============

GLOBAL_AVG_RATING = 3.8
BAYESIAN_C = 10
CUISINE_WEIGHT_ADJUST = 0.15
DISTANCE_WEIGHT_HIGH = 1.0
DISTANCE_WEIGHT_LOW = 0.3
FRESHNESS_LAMBDA = 0.3

DEFAULT_WEIGHTS = {
    "freshness": 0.9,  # 新鲜度
    "nutrition": 0.5,  # 营养匹配
    "distance": 0.9,  # 距离
    "time": 0.9,  # 时间
    "special": 0.5,  # 特殊需求
    "crowd": 0.5,  # 人流量
    "social": 0.2,  # 多人融合
    "rating": 0.8,  # 评分
    "taboo": 999.0,  # 忌口硬约束
    "random": 0.0  # 原扰动权重置为0，改由内聚的UCB接管
}

# 预设的营养控制总量（套餐级匹配）
NUTRITION_GOALS = {
    "减脂": {"calories": (400, 650), "protein": (35, 55), "fat": (10, 20)},
    "增肌": {"calories": (700, 1000), "protein": (50, 80), "fat": (20, 35)},
    "均衡": {"calories": (600, 800), "protein": (30, 50), "fat": (15, 25)},
}

# 静态校园相对步行时间阵（不破坏原有CANTEENS地理坐标的前提下引入）
CAMPUS_DISTANCE_MATRIX = {
    "教学区": {"家园食堂": 3, "学一食堂": 4, "学五食堂": 5, "燕南美食": 2, "农园食堂": 3, "松林": 6, "勺园": 8},
    "宿舍区": {"家园食堂": 2, "学一食堂": 2, "学五食堂": 3, "燕南美食": 5, "农园食堂": 6, "松林": 4, "勺园": 7},
}


class Recommender:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.weights = DEFAULT_WEIGHTS.copy()

        # 内部模拟UCB所需的计数器，不影响外部初始化
        self._total_recommend_actions = 1000
        self._dish_impressions = {}  # {dish_id: int}

    def set_weights(self, mode: str):
        """保持原有的模式权重切换函数名不变"""
        self.weights = DEFAULT_WEIGHTS.copy()
        if mode == "rush":
            self.weights["time"] = 1.5
            self.weights["distance"] = 1.2
        elif mode == "explore":
            self.weights["freshness"] = 1.5
        elif mode == "healthy":
            self.weights["nutrition"] = 1.5
        elif mode == "social":
            self.weights["social"] = 1.2

    # ==================== 保持原有打分函数签名，内部细化 ====================

    def _score_distance(self, dish: Dict, profile: Dict) -> Tuple[float, str]:
        """【时空细化】无缝替换内部逻辑，不改变接口"""
        canteen = dish.get("canteen", "")
        # 从原本逻辑的 profile['preferences']['distance'] 兼容读取或硬编码判定
        # 假设通过当前时间智能推断所处位置：12点下课在教学区，18点在宿舍区
        current_hour = datetime.now().hour
        current_loc = "教学区" if (11 <= current_hour <= 13) else "宿舍区"

        if current_loc in CAMPUS_DISTANCE_MATRIX and canteen in CAMPUS_DISTANCE_MATRIX[current_loc]:
            walk_time = CAMPUS_DISTANCE_MATRIX[current_loc][canteen]
            if walk_time <= 3: return 100.0, f"距离极近({walk_time}分)"
            if walk_time <= 6: return 80.0, f"距离较近({walk_time}分)"
            return 50.0, f"距离稍远({walk_time}分)"

        # 降级回原有的默认食堂划档
        if canteen in ["家园食堂", "学一食堂", "学五食堂", "燕南美食"]:
            return 100.0, "核心区域食堂"
        return 60.0, "周边食堂"

    def _score_nutrition(self, dish: Dict, profile: Dict) -> Tuple[float, str]:
        """保留单品打分原签名，方便套餐之外的情形使用"""
        goal = profile.get("goals", "无")
        if goal == "无":
            return 60.0, "营养均衡"

        # 原有的单品打分逻辑
        dish_cal = dish.get("calories", 0)
        if goal == "减脂" and dish_cal < 300:
            return 95.0, "低卡轻食"
        if goal == "增肌" and dish.get("protein", 0) > 20:
            return 95.0, "高蛋白推荐"
        return 70.0, "满足基础营养"

    def _score_time(self, dish: Dict) -> Tuple[float, str]:
        """完全保持原打分逻辑不变"""
        prep_time = dish.get("prep_time", 5)
        if prep_time <= 3: return 100.0, "极速出餐"
        if prep_time <= 7: return 80.0, "出餐速度正常"
        return 40.0, "制作较慢"

    def _score_rating(self, dish: Dict) -> Tuple[float, str]:
        """完全保持原贝叶斯打分逻辑不变"""
        r = dish.get("rating", GLOBAL_AVG_RATING)
        c = dish.get("rating_count", 0)
        br = (BAYESIAN_C * GLOBAL_AVG_RATING + c * r) / (BAYESIAN_C + c)
        return br * 20.0, f"口碑评分:{r}"

    def _score_freshness(self, dish: Dict, history: List[Dict]) -> Tuple[float, str]:
        """完全保持原新鲜度打分逻辑不变"""
        dish_id = dish.get("id")
        for h in history:
            if h.get("dish_id") == dish_id:
                return 30.0, "近期已吃过"
        return 100.0, "未尝鲜或久未食用"

    # ==================== 核心重构：一票否决与融合机制 ====================

    def _filter_hard_constraints(self, dishes: List[Dict], profile: Dict) -> List[Dict]:
        """将原有的硬过滤抽取，支持后续多画像合并后的过滤"""
        constraints = profile.get("constraints", {})
        taboos = constraints.get("taboos", [])
        disliked = profile.get("disliked_ingredients", [])
        budget = constraints.get("budget_limit", 50)

        black_list = set(taboos + disliked)
        result = []
        for d in dishes:
            if d.get("price", 0) > budget:
                continue
            if any(t in d.get("name", "") or t in d.get("tags", []) for t in black_list):
                continue
            result.append(d)
        return result

    def _assemble_bundles(self, candidates: List[Dict], goal: str) -> List[Dict]:
        """【自组装套餐】内部调用，输出格式包装为前端兼容的菜品Dict结构"""
        target = NUTRITION_GOALS.get(goal)
        if not target: return []

        # 区分餐品角色
        mains = [d for d in candidates if "主菜" in d.get("tags", []) or d.get("protein", 0) >= 15]
        sides = [d for d in candidates if "副菜" in d.get("tags", []) or "素食可选" in d.get("tags", [])]
        staples = [d for d in candidates if "主食" in d.get("tags", []) or d.get("carbs", 0) >= 30]

        # 降级防空
        if not mains or not staples:
            mains = sides = staples = candidates

        for m in mains[:8]:
            for s in sides[:8]:
                for st in staples[:8]:
                    if m["id"] == s["id"] or s["id"] == st["id"] or m["canteen"] != s["canteen"]:
                        continue

                    # 总量累加
                    tot_cal = m.get("calories", 0) + s.get("calories", 0) + st.get("calories", 0)
                    tot_pro = m.get("protein", 0) + s.get("protein", 0) + st.get("protein", 0)
                    tot_fat = m.get("fat", 0) + s.get("fat", 0) + st.get("fat", 0)

                    if (target["calories"][0] <= tot_cal <= target["calories"][1] and
                            target["protein"][0] <= tot_pro <= target["protein"][1] and
                            target["fat"][0] <= tot_fat <= target["fat"][1]):
                        # 返回前端兼容的结构体（伪装成普通菜品，保证不破坏前端渲染字段）
                        return [{
                            "id": f"bundle_{m['id']}",
                            "name": f"【{goal}推荐】{m['name']}+{s['name']}+{st['name']}",
                            "canteen": m["canteen"],
                            "window": "智能组装",
                            "price": round(m["price"] + s["price"] + st["price"], 1),
                            "calories": tot_cal,
                            "protein": tot_pro,
                            "carbs": m.get("carbs", 0) + s.get("carbs", 0) + st.get("carbs", 0),
                            "fat": tot_fat,
                            "prep_time": max(m["prep_time"], s["prep_time"], st["prep_time"]),
                            "rating": round((m["rating"] + s["rating"] + st["rating"]) / 3, 1),
                            "tags": [goal, "精选套餐"],
                            "_score": (m.get("_pure_score", 60) + s.get("_pure_score", 60) + st.get("_pure_score",
                                                                                                    60)) / 3,
                            "description": f"整餐热量:{tot_cal}kcal,蛋白:{tot_pro}g"
                        }]
        return []

    # ==================== 核心入口：完美对齐对外接口 ====================

    def recommend(self, top_k: int = 5, mode: str = "normal") -> List[Dict]:
        """【主接口保持完美一致】对外接收不变，内部运用四大机制"""
        self.set_weights(mode)

        all_dishes = self.dm.get_all_dishes()
        profile = self.dm.get_profile()
        history = self.dm.get_history()

        # 1. 【多人用餐需求融合机制】
        # 从 profile['social'] 中严格读取前端写入的数据结构，不变更变量
        social_info = profile.get("social", {})
        companions_count = social_info.get("companions", 1)

        # 默认一票否决基础池过滤
        filtered_dishes = self._filter_hard_constraints(all_dishes, profile)

        # 2. 算分迭代 pipeline
        scored_candidates = []
        for dish in filtered_dishes:
            # 基础各维度软评分
            s_fresh, _ = self._score_freshness(dish, history)
            s_time, _ = self._score_time(dish)
            s_rating, _ = self._score_rating(dish)
            s_dist, _ = self._score_distance(dish, profile)  # 内部含有时空感知细化

            # 多人社交软偏好平滑计算
            s_nutri, _ = self._score_nutrition(dish, profile)
            if companions_count > 1:
                # 若多人就餐，弱化单人营养偏好，拉高大众口味平滑分
                s_nutri = (s_nutri + s_rating) / 2

            # Exploitation 得分累计
            estimated_score = (
                    self.weights["freshness"] * s_fresh +
                    self.weights["time"] * s_time +
                    self.weights["rating"] * s_rating +
                    self.weights["distance"] * s_dist +
                    self.weights["nutrition"] * s_nutri
            )
            dish["_pure_score"] = estimated_score  # 注入给套餐算分使用

            # 3. 【UCB 智能探索替换 Layer 3 随机】
            dish_id = dish.get("id", "")
            n_i = self._dish_impressions.get(dish_id, 5)
            # UCB 公式置信上界注入
            ucb_bound = 12.0 * math.sqrt(math.log(self._total_recommend_actions) / n_i)
            final_score = estimated_score + ucb_bound

            dish["_score"] = final_score  # 覆盖原变量名 _score，让前端能正常读取并显示
            scored_candidates.append(dish)

        # 降序精排
        scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)

        # 更新全局 UCB 计数器
        self._total_recommend_actions += 1
        for d in scored_candidates[:top_k]:
            self._dish_impressions[d["id"]] = self._dish_impressions.get(d["id"], 5) + 1

        # 4. 【自组装套餐处理】
        user_goal = profile.get("goals", "无")
        if user_goal in ["减脂", "增肌", "均衡"] and (mode == "healthy" or mode == "normal"):
            bundles = self._assemble_bundles(scored_candidates, user_goal)
            if bundles:
                # 套餐完美伪装成一个单品 List 融入头部返回，保证和前端接收的 List[Dict] 强对齐
                return bundles + scored_candidates[:(top_k - len(bundles))]

        return scored_candidates[:top_k]

    # ==================== 保持原有辅助函数不变 ====================

    def get_quick_pick(self) -> Optional[Dict]:
        """保持原有方法不变"""
        recs = self.recommend(top_k=1, mode="normal")
        return recs[0] if recs else None

    def get_trending(self, count: int = 5) -> List[Dict]:
        """保持原有的热门排行不变"""
        dishes = self.dm.get_all_dishes()
        return sorted(dishes, key=lambda x: (x.get("rating", 0), x.get("rating_count", 0)), reverse=True)[:count]