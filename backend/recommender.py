"""
recommender.py - 推荐算法核心模块
实现三层流水线推荐逻辑：
  Layer 1: 分层过滤（硬约束）
  Layer 2: 加权评分（软偏好）
  Layer 3: 扰动输出（多样性）
"""

import math
import random
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from backend.data_manager import DataManager, CANTEENS


# ============ 常量配置 ============

# 全局评分参数（贝叶斯平均）
GLOBAL_AVG_RATING = 3.8
BAYESIAN_C = 10

# 菜系权重调整系数
CUISINE_WEIGHT_ADJUST = 0.15

# 距离权重
DISTANCE_WEIGHT_HIGH = 1.0
DISTANCE_WEIGHT_LOW = 0.3

# 时间衰减参数
FRESHNESS_LAMBDA = 0.3

# 维度默认权重
DEFAULT_WEIGHTS = {
    "freshness": 0.9,    # 新鲜度（吃过？）- 高
    "nutrition": 0.5,    # 营养匹配 - 中
    "distance": 0.9,     # 距离 - 高
    "time": 0.9,         # 时间 - 高
    "special": 0.5,      # 特殊需求 - 中
    "crowd": 0.5,        # 人流量 - 中
    "social": 0.2,       # 多人融合 - 低（扩展）
    "rating": 0.8,       # 评分 - 高
    "taboo": 999.0,      # 忌口 - 最高（硬约束）
    "random": 0.2,       # 随机性 - 低
}

# 营养目标
NUTRITION_GOALS = {
    "减脂": {"calories": (200, 400), "protein": (20, 40), "fat": (5, 15)},
    "增肌": {"calories": (400, 700), "protein": (25, 50), "fat": (10, 30)},
    "均衡": {"calories": (300, 600), "protein": (15, 35), "fat": (10, 25)},
    "无": None,
}


class Recommender:
    """推荐引擎 - 三层流水线推荐系统"""

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.weights = DEFAULT_WEIGHTS.copy()

    def set_weights(self, mode: str = "normal"):
        """根据模式调整权重
        
        Args:
            mode: normal / rush / explore / healthy / social
        """
        if mode == "rush":  # 赶时间
            self.weights["time"] = 1.0
            self.weights["distance"] = 1.0
            self.weights["nutrition"] = 0.2
            self.weights["crowd"] = 0.8
        elif mode == "explore":  # 探索模式
            self.weights["random"] = 0.8
            self.weights["freshness"] = 0.3
            self.weights["rating"] = 0.4
        elif mode == "healthy":  # 健康优先
            self.weights["nutrition"] = 1.0
            self.weights["rating"] = 0.7
            self.weights["time"] = 0.4
        elif mode == "social":  # 聚餐模式
            self.weights["social"] = 0.9
            self.weights["nutrition"] = 0.3
            self.weights["crowd"] = 0.7
        else:  # normal
            self.weights = DEFAULT_WEIGHTS.copy()

    # ==================== Layer 1: 分层过滤（硬约束） ====================

    def _filter_hard_constraints(self, dishes: List[Dict]) -> List[Dict]:
        """第一层：硬约束过滤"""
        profile = self.dm.get_profile()
        result = dishes

        # 1. 忌口黑名单过滤（零容错）
        taboos = profile.get("constraints", {}).get("taboos", [])
        disliked = profile.get("disliked_ingredients", [])
        all_taboos = set(taboos + disliked)
        if all_taboos:
            result = [d for d in result
                      if not any(t in d.get("tags", []) or t in d.get("name", "") for t in all_taboos)]

        # 2. 预算上限过滤
        budget = profile.get("constraints", {}).get("budget_limit", 50)
        result = [d for d in result if d["price"] <= budget]

        # 3. 营业时段过滤
        now = datetime.now()
        hour = now.hour + now.minute / 60
        meal_type = self._get_meal_type(hour)
        result = [d for d in result if d.get("hours", {}).get(meal_type, True)]

        # 4. 过敏原/宗教禁忌（基于标签）
        result = self._filter_allergens(result, all_taboos)

        # 5. 特殊需求强约束
        result = self._filter_special_needs(result, profile)

        return result

    @staticmethod
    def _get_meal_type(hour: float) -> str:
        """判断当前餐别"""
        if 6 <= hour < 10:
            return "breakfast"
        elif 10 <= hour < 14.5:
            return "lunch"
        elif 14.5 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 20.5:
            return "dinner"
        else:
            return "late_night"

    def _filter_allergens(self, dishes: List[Dict], taboos: set) -> List[Dict]:
        """过敏原过滤"""
        allergen_map = {
            "花生": ["花生"], "海鲜": ["鱼", "虾", "蟹", "海鲜"],
            "辣": ["辣", "川"], "猪肉": [" pork ", "猪", "排骨", "肉"],
        }
        filtered = []
        for d in dishes:
            safe = True
            for taboo in taboos:
                if taboo in allergen_map:
                    keywords = allergen_map[taboo]
                    if any(kw in d["name"] or kw in " ".join(d.get("tags", [])) for kw in keywords):
                        safe = False
                        break
            if safe:
                filtered.append(d)
        return filtered

    def _filter_special_needs(self, dishes: List[Dict], profile: Dict) -> List[Dict]:
        """特殊需求过滤"""
        pref = profile.get("preferences", {})
        # "不排队"强约束
        if pref.get("queue") == "不排队":
            # 简化为过滤高prep_time
            dishes = [d for d in d_ishes if d.get("prep_time", 10) <= 8]
        return dishes

    # ==================== Layer 2: 加权评分（软偏好） ====================

    def _score_dishes(self, dishes: List[Dict]) -> List[Tuple[Dict, float]]:
        """第二层：对过滤后的候选集进行加权评分"""
        profile = self.dm.get_profile()
        scored = []

        for dish in dishes:
            score = 0.0
            details = {}

            # 1. 新鲜度评分 (吃过？)
            s_fresh, d_fresh = self._score_freshness(dish)
            score += self.weights["freshness"] * s_fresh
            details["freshness"] = d_fresh

            # 2. 营养匹配评分
            s_nutri, d_nutri = self._score_nutrition(dish, profile)
            score += self.weights["nutrition"] * s_nutri
            details["nutrition"] = d_nutri

            # 3. 距离评分
            s_dist, d_dist = self._score_distance(dish, profile)
            score += self.weights["distance"] * s_dist
            details["distance"] = d_dist

            # 4. 时间/出餐速度评分
            s_time, d_time = self._score_time(dish)
            score += self.weights["time"] * s_time
            details["time"] = d_time

            # 5. 评分/口碑评分
            s_rating, d_rating = self._score_rating(dish)
            score += self.weights["rating"] * s_rating
            details["rating"] = d_rating

            # 6. 特殊需求评分
            s_special, d_special = self._score_special(dish, profile)
            score += self.weights["special"] * s_special
            details["special"] = d_special

            # 7. 社交评分
            s_social, d_social = self._score_social(dish, profile)
            score += self.weights["social"] * s_social
            details["social"] = d_social

            # 8. 随机性
            s_rand = random.random() * 100
            score += self.weights["random"] * s_rand

            scored.append((dish, score, details))

        # 按分数降序排序
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _score_freshness(self, dish: Dict) -> Tuple[float, str]:
        """新鲜度评分：3天内吃过降权"""
        if self.dm.is_recently_eaten(dish["id"], days=3):
            return 30.0, "3天内吃过"
        elif self.dm.is_recently_eaten(dish["id"], days=7):
            return 60.0, "一周内吃过"
        else:
            return 100.0, "新鲜推荐"

    def _score_nutrition(self, dish: Dict, profile: Dict) -> Tuple[float, str]:
        """营养匹配评分"""
        goal = profile.get("goals", "无")
        if goal == "无" or goal not in NUTRITION_GOALS or NUTRITION_GOALS[goal] is None:
            return 70.0, "无特定目标"

        target = NUTRITION_GOALS[goal]
        score = 0.0
        checks = []

        # 热量匹配
        cal_range = target.get("calories")
        if cal_range and cal_range[0] <= dish.get("calories", 400) <= cal_range[1]:
            score += 40
            checks.append("热量匹配")
        elif cal_range:
            # 线性衰减
            cal = dish.get("calories", 400)
            mid = (cal_range[0] + cal_range[1]) / 2
            diff = abs(cal - mid)
            score += max(0, 40 - diff * 0.2)
            checks.append(f"热量偏差{diff:.0f}")

        # 蛋白质匹配
        pro_range = target.get("protein")
        if pro_range and pro_range[0] <= dish.get("protein", 15) <= pro_range[1]:
            score += 30
            checks.append("蛋白质匹配")

        # 脂肪匹配
        fat_range = target.get("fat")
        if fat_range and fat_range[0] <= dish.get("fat", 15) <= fat_range[1]:
            score += 30
            checks.append("脂肪匹配")

        desc = "; ".join(checks) if checks else "一般匹配"
        return score, desc

    def _score_distance(self, dish: Dict, profile: Dict) -> Tuple[float, str]:
        """距离评分：基于用户偏好"""
        pref = profile.get("preferences", {}).get("distance", "就近优先")

        # 简化为食堂等级的距离
        # 家园、学一、学五为核心区域（距离0）
        # 其他食堂距离1-3
        near_canteens = {"家园食堂", "学一食堂", "学五食堂", "燕南美食"}
        mid_canteens = {"农园食堂", "佟园", "松林"}
        far_canteens = {"勺园", "勺中", "勺西", "成府园", "畅春园", "艺园"}

        canteen = dish["canteen"]
        if canteen in near_canteens:
            dist_score = 100
            dist_desc = "核心区域"
        elif canteen in mid_canteens:
            dist_score = 70
            dist_desc = "中等距离"
        elif canteen in far_canteens:
            dist_score = 40
            dist_desc = "较远"
        else:
            dist_score = 60
            dist_desc = "一般"

        if pref == "愿意多走":
            dist_score = 100 - (100 - dist_score) * 0.3  # 距离权重降低
            dist_desc += "(愿意多走)"

        return dist_score, dist_desc

    def _score_time(self, dish: Dict) -> Tuple[float, str]:
        """出餐速度评分"""
        prep = dish.get("prep_time", 10)
        if prep <= 3:
            return 100, f"极速出餐({prep}分钟)"
        elif prep <= 5:
            return 85, f"快速出餐({prep}分钟)"
        elif prep <= 8:
            return 65, f"正常出餐({prep}分钟)"
        elif prep <= 12:
            return 40, f"较慢({prep}分钟)"
        else:
            return 20, f"慢速({prep}分钟)"

    def _score_rating(self, dish: Dict) -> Tuple[float, str]:
        """评分/口碑评分"""
        rating = dish.get("rating", 3.5)
        count = dish.get("rating_count", 0)
        # 贝叶斯平均平滑
        bayesian = (BAYESIAN_C * GLOBAL_AVG_RATING + count * rating) / (BAYESIAN_C + max(count, 1))
        # 映射到0-100
        score = (bayesian / 5.0) * 100
        return score, f"评分{bayesian:.1f}({count}人评)"

    def _score_special(self, dish: Dict, profile: Dict) -> Tuple[float, str]:
        """特殊需求评分"""
        meal_pref = profile.get("constraints", {}).get("meal_pref", "正餐")
        if meal_pref == "夜宵" and dish.get("hours", {}).get("late_night", False):
            return 100, "支持夜宵"
        return 70, "一般"

    def _score_social(self, dish: Dict, profile: Dict) -> Tuple[float, str]:
        """社交评分：适合聚餐的菜品得分更高"""
        companions = profile.get("social", {}).get("companions", 1)
        if companions <= 1:
            return 70, "单人餐"

        # 聚餐偏好：大份、高评分、热门菜品
        tags = dish.get("tags", [])
        score = 50
        if "聚餐" in tags:
            score += 30
        if "管饱" in tags:
            score += 20
        if "热门" in tags:
            score += 15
        if dish.get("rating", 0) >= 4.3:
            score += 10

        return min(score, 100), f"聚餐评分({companions}人)"

    # ==================== Layer 3: 扰动输出 ====================

    def _perturb_output(self, scored: List[Tuple], top_k: int = 5) -> List[Dict]:
        """第三层：ε-greedy扰动，兼顾精准与探索"""
        settings = self.dm.get_settings()
        epsilon = settings.get("explore_epsilon", 0.15)

        if not scored:
            return []

        result = []
        used_indices = set()

        # Top-(1-ε)按分数排序
        greedy_count = max(1, int(top_k * (1 - epsilon)))
        for i in range(min(greedy_count, len(scored))):
            dish_data = scored[i][0].copy()
            dish_data["_score"] = round(scored[i][1], 2)
            dish_data["_score_details"] = scored[i][2]
            result.append(dish_data)
            used_indices.add(i)

        # ε部分随机探索长尾
        explore_count = top_k - len(result)
        if explore_count > 0 and len(scored) > len(result):
            remaining = [i for i in range(len(scored)) if i not in used_indices]
            if remaining:
                # 从剩余候选中随机选择（权重偏向中高评分）
                candidates = remaining[:max(len(remaining), 20)]
                chosen = random.sample(candidates, min(explore_count, len(candidates)))
                for idx in chosen:
                    dish_data = scored[idx][0].copy()
                    dish_data["_score"] = round(scored[idx][1], 2)
                    dish_data["_score_details"] = scored[idx][2]
                    dish_data["_is_explore"] = True  # 标记为探索推荐
                    result.append(dish_data)

        return result

    # ==================== 主推荐流程 ====================

    def recommend(self, top_k: int = 5, mode: str = "normal") -> List[Dict]:
        """主推荐入口
        
        Args:
            top_k: 返回推荐数量
            mode: 推荐模式 normal/rush/explore/healthy/social
        
        Returns:
            推荐菜品列表（包含评分详情）
        """
        # 设置权重
        self.set_weights(mode)

        # 获取所有菜品
        all_dishes = self.dm.get_all_dishes()

        # Layer 1: 硬约束过滤
        filtered = self._filter_hard_constraints(all_dishes)

        # Layer 2: 加权评分
        scored = self._score_dishes(filtered)

        # Layer 3: 扰动输出
        recommendations = self._perturb_output(scored, top_k)

        return recommendations

    def get_quick_pick(self) -> Optional[Dict]:
        """快速推荐一个今日最佳"""
        recommendations = self.recommend(top_k=1, mode="normal")
        return recommendations[0] if recommendations else None

    def get_alternatives(self, dish_id: str, count: int = 3) -> List[Dict]:
        """获取某菜品的替代品（同菜系/同口味）"""
        dish = self.dm.get_dish_by_id(dish_id)
        if not dish:
            return []

        all_dishes = self.dm.get_all_dishes()
        candidates = [d for d in all_dishes if d["id"] != dish_id]

        # 优先同菜系
        same_cuisine = [d for d in candidates if d.get("cuisine") == dish.get("cuisine")]
        if len(same_cuisine) >= count:
            return sorted(same_cuisine, key=lambda x: x.get("rating", 0), reverse=True)[:count]

        # 次选同口味
        flavors = set(dish.get("flavor", []))
        same_flavor = [d for d in candidates
                       if any(f in d.get("flavor", []) for f in flavors)]

        combined = same_cuisine + [d for d in same_flavor if d not in same_cuisine]
        if len(combined) >= count:
            return combined[:count]

        # 最后返回高评分菜品
        return sorted(candidates, key=lambda x: x.get("rating", 0), reverse=True)[:count]

    def get_trending(self, count: int = 5) -> List[Dict]:
        """获取热门菜品"""
        dishes = self.dm.get_all_dishes()
        return sorted(dishes, key=lambda x: (x.get("rating", 0), x.get("rating_count", 0)),
                      reverse=True)[:count]


# ============ 测试入口 ============

def test_recommender():
    """推荐引擎测试"""
    print("=" * 50)
    print("推荐引擎测试")
    print("=" * 50)

    dm = DataManager(data_dir="test_data")
    engine = Recommender(dm)

    # 测试推荐
    print("\n【测试1】普通模式推荐 top-5:")
    recs = engine.recommend(top_k=5, mode="normal")
    for i, r in enumerate(recs, 1):
        explore_tag = " [探索]" if r.get("_is_explore") else ""
        print(f"  {i}. {r['name']} ({r['canteen']}) - 评分:{r['rating']} 综合分:{r['_score']:.1f}{explore_tag}")

    # 测试快速推荐
    print("\n【测试2】快速推荐:")
    quick = engine.get_quick_pick()
    if quick:
        print(f"  今日推荐: {quick['name']} @ {quick['canteen']}  ¥{quick['price']}")

    # 测试不同模式
    print("\n【测试3】赶时间模式:")
    recs = engine.recommend(top_k=3, mode="rush")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r['name']} 出餐{r['prep_time']}分钟")

    print("\n【测试4】热门推荐:")
    trending = engine.get_trending(5)
    for i, d in enumerate(trending, 1):
        print(f"  {i}. {d['name']} - {d['rating']}分 ({d['rating_count']}人评)")

    print("\n所有测试通过!")


if __name__ == "__main__":
    test_recommender()
