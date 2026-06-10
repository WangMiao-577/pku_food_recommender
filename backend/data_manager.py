"""
data_manager.py - 数据管理模块
管理菜品数据、用户画像、历史记录、评价数据等
提供数据持久化（JSON文件）
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


# ============ 默认数据 ============

CANTEENS = [
    {"id": "jiayuan", "name": "家园食堂", "floors": 4, "x": 116.316, "y": 39.999,
     "windows": ["川菜", "鲁菜", "粤菜", "面食", "快餐"]},
    {"id": "nongyuan", "name": "农园食堂", "floors": 3, "x": 116.318, "y": 39.992,
     "windows": ["家常菜", "西北风味", "日韩料理", "西式简餐"]},
    {"id": "xueyi", "name": "学一食堂", "floors": 1, "x": 116.310, "y": 39.995,
     "windows": ["基础伙", "小炒", "面食"]},
    {"id": "xuewu", "name": "学五食堂", "floors": 1, "x": 116.312, "y": 39.987,
     "windows": ["综合", "快餐", "夜宵"]},
    {"id": "yannan", "name": "燕南美食", "floors": 2, "x": 116.315, "y": 39.993,
     "windows": ["地上：精品菜", "地下：小吃"]},
    {"id": "tongyuan", "name": "佟园", "floors": 1, "x": 116.314, "y": 39.991,
     "windows": ["民族餐厅"]},
    {"id": "changchun", "name": "畅春园", "floors": 1, "x": 116.308, "y": 39.984,
     "windows": ["家常菜", "面食"]},
    {"id": "yiyuan", "name": "艺园", "floors": 1, "x": 116.320, "y": 39.997,
     "windows": ["炒菜", "烧烤"]},
    {"id": "shaoyuan", "name": "勺园", "floors": 1, "x": 116.322, "y": 40.001,
     "windows": ["自助", "小炒"]},
    {"id": "shaozhong", "name": "勺中", "floors": 1, "x": 116.321, "y": 40.000,
     "windows": ["快餐"]},
    {"id": "shaoxi", "name": "勺西", "floors": 1, "x": 116.323, "y": 40.002,
     "windows": ["西式", "咖啡简餐"]},
    {"id": "chengfu", "name": "成府园", "floors": 1, "x": 116.325, "y": 39.998,
     "windows": ["教工餐厅"]},
    {"id": "kuaicanche", "name": "快餐车", "floors": 0, "x": 116.317, "y": 39.996,
     "windows": ["快餐", "饮料"]},
    {"id": "songlin", "name": "松林", "floors": 1, "x": 116.313, "y": 39.994,
     "windows": ["包子", "粥", "快餐"]},
    {"id": "3w", "name": "二教地下3W", "floors": 1, "x": 116.319, "y": 39.990,
     "windows": ["咖啡", "简餐", "烘焙"]},
]

# 校园区域划分（用于位置推荐）
CAMPUS_REGIONS = {
    "east": {"name": "东区", "canteens": ["农园食堂", "成府园"]},
    "southeast": {"name": "东南区", "canteens": ["家园食堂"]},
    "southwest": {"name": "西南区", "canteens": ["学一食堂", "松林"]},
    "west": {"name": "西区", "canteens": ["学五食堂", "艺园"]},
    "northwest": {"name": "西北区", "canteens": ["勺园", "勺中", "勺西", "佟园"]},
    "center": {"name": "中区", "canteens": ["燕南美食", "快餐车"]},
    "south": {"name": "南区", "canteens": ["畅春园"]},
    "northeast": {"name": "东北区", "canteens": ["二教地下3W"]},
}

CANTEEN_NAME_TO_ID = {c["name"]: c["id"] for c in CANTEENS}
CANTEEN_ID_TO_NAME = {c["id"]: c["name"] for c in CANTEENS}

LOCATION_TO_REGIONS = {
    "东南门/东门附近": ["southeast", "east"],
    "西南门附近": ["southwest"],
    "西北门/西门附近": ["northwest"],
    "中部教学区": ["center", "northeast"],
    "北部生活区": ["west", "northwest"],
    "图书馆附近": ["center", "northeast"],
}

DEFAULT_DISHES = [
    {
        "id": "d001", "name": "麻婆豆腐", "canteen": "家园食堂", "window": "川菜",
        "price": 8, "cuisine": "川", "flavor": ["辣", "鲜", "咸"],
        "cooking": "红烧", "appearance": 4, "calories": 220, "protein": 12, "carbs": 8, "fat": 15,
        "fiber": 3, "prep_time": 5, "image": "dish_1_mapo_tofu.jpg",
        "tags": ["下饭", "经典", "素食可选"], "rating": 4.2, "rating_count": 156,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d002", "name": "宫保鸡丁", "canteen": "家园食堂", "window": "川菜",
        "price": 15, "cuisine": "川", "flavor": ["酸", "甜", "辣"],
        "cooking": "现炒", "appearance": 4, "calories": 320, "protein": 25, "carbs": 15, "fat": 18,
        "fiber": 2, "prep_time": 8, "image": "dish_2_kung_pao_chicken.jpg",
        "tags": ["下饭", "经典", "高蛋白"], "rating": 4.5, "rating_count": 203,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d003", "name": "红烧肉", "canteen": "农园食堂", "window": "家常菜",
        "price": 18, "cuisine": "融合", "flavor": ["甜", "咸", "鲜"],
        "cooking": "红烧", "appearance": 5, "calories": 450, "protein": 20, "carbs": 10, "fat": 35,
        "fiber": 1, "prep_time": 10, "image": "dish_3_hongshaorou.jpg",
        "tags": ["招牌", "满足", "高热量"], "rating": 4.6, "rating_count": 189,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d004", "name": "西红柿炒鸡蛋", "canteen": "学一食堂", "window": "基础伙",
        "price": 6, "cuisine": "融合", "flavor": ["酸", "甜", "鲜"],
        "cooking": "现炒", "appearance": 3, "calories": 180, "protein": 10, "carbs": 12, "fat": 10,
        "fiber": 3, "prep_time": 3, "image": "dish_4_tomato_egg.jpg",
        "tags": ["家常", "经济", "素食"], "rating": 3.9, "rating_count": 267,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d005", "name": "水煮鱼", "canteen": "农园食堂", "window": "川菜",
        "price": 22, "cuisine": "川", "flavor": ["辣", "鲜", "麻"],
        "cooking": "现炒", "appearance": 4, "calories": 380, "protein": 30, "carbs": 5, "fat": 25,
        "fiber": 2, "prep_time": 12, "image": "dish_5_shuizhuyu.jpg",
        "tags": ["招牌", "聚餐", "高蛋白"], "rating": 4.4, "rating_count": 134,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d006", "name": "红烧牛肉面", "canteen": "家园食堂", "window": "面食",
        "price": 14, "cuisine": "西北", "flavor": ["咸", "鲜"],
        "cooking": "现炒", "appearance": 4, "calories": 520, "protein": 22, "carbs": 65, "fat": 18,
        "fiber": 4, "prep_time": 8, "image": "dish_6_beef_noodle.jpg",
        "tags": ["管饱", "面食", "经典"], "rating": 4.3, "rating_count": 178,
        "hours": {"lunch": True, "dinner": True, "late_night": True}
    },
    {
        "id": "d007", "name": "石锅拌饭", "canteen": "农园食堂", "window": "日韩料理",
        "price": 16, "cuisine": "日韩", "flavor": ["甜", "辣", "鲜"],
        "cooking": "现炒", "appearance": 5, "calories": 580, "protein": 18, "carbs": 75, "fat": 22,
        "fiber": 8, "prep_time": 10, "image": "dish_7_bibimbap.jpg",
        "tags": ["热门", "营养均衡", "蔬菜多"], "rating": 4.5, "rating_count": 198,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d008", "name": "意式肉酱面", "canteen": "勺西", "window": "西式",
        "price": 20, "cuisine": "西式", "flavor": ["酸", "咸", "鲜"],
        "cooking": "预制", "appearance": 4, "calories": 480, "protein": 16, "carbs": 68, "fat": 14,
        "fiber": 5, "prep_time": 5, "image": "dish_8_pasta.jpg",
        "tags": ["西式", "人气", "快餐"], "rating": 4.1, "rating_count": 145,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d009", "name": "清蒸鲈鱼", "canteen": "农园食堂", "window": "粤菜",
        "price": 25, "cuisine": "粤", "flavor": ["鲜", "咸"],
        "cooking": "清蒸", "appearance": 5, "calories": 200, "protein": 35, "carbs": 2, "fat": 6,
        "fiber": 0, "prep_time": 15, "image": "dish_9_steamed_fish.jpg",
        "tags": ["健康", "高蛋白", "清淡"], "rating": 4.7, "rating_count": 112,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d010", "name": "糖醋里脊", "canteen": "家园食堂", "window": "鲁菜",
        "price": 16, "cuisine": "鲁", "flavor": ["酸", "甜"],
        "cooking": "油炸", "appearance": 4, "calories": 420, "protein": 18, "carbs": 35, "fat": 22,
        "fiber": 1, "prep_time": 8, "image": "dish_10_sweet_sour.jpg",
        "tags": ["下饭", "人气", "油炸"], "rating": 4.4, "rating_count": 167,
        "hours": {"lunch": True, "dinner": True, "late_night": False}
    },
    {
        "id": "d011", "name": "蒸饺", "canteen": "松林", "window": "包子",
        "price": 8, "cuisine": "融合", "flavor": ["鲜", "咸"],
        "cooking": "清蒸", "appearance": 3, "calories": 280, "protein": 12, "carbs": 35, "fat": 10,
        "fiber": 3, "prep_time": 3, "image": "dish_11_dumplings.jpg",
        "tags": ["早餐", "经济", "管饱"], "rating": 4.0, "rating_count": 234,
        "hours": {"lunch": True, "dinner": True, "late_night": True}
    },
    {
        "id": "d012", "name": "黄焖鸡米饭", "canteen": "燕南美食", "window": "地上：精品菜",
        "price": 18, "cuisine": "融合", "flavor": ["咸", "鲜", "辣"],
        "cooking": "红烧", "appearance": 4, "calories": 550, "protein": 28, "carbs": 45, "fat": 26,
        "fiber": 4, "prep_time": 10, "image": "dish_12_claypot.jpg",
        "tags": ["管饱", "热门", "下饭"], "rating": 4.5, "rating_count": 201,
        "hours": {"lunch": True, "dinner": True, "late_night": True}
    },
]


class DataManager:
    """数据管理器 - 负责所有数据的CRUD操作"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            from backend.paths import get_data_dir
            data_dir = get_data_dir()
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # 文件路径
        self.dishes_file = os.path.join(data_dir, "dishes.json")
        self.profile_file = os.path.join(data_dir, "user_profile.json")
        self.history_file = os.path.join(data_dir, "history.json")
        self.reviews_file = os.path.join(data_dir, "reviews.json")
        self.settings_file = os.path.join(data_dir, "settings.json")

        # 加载数据
        self.dishes = self._load_dishes()
        self.profile = self._load_profile()
        self.history = self._load_history()
        self.reviews = self._load_reviews()
        self.settings = self._load_settings()

    # ============ 菜品数据 ============

    def _load_dishes(self) -> List[Dict]:
        """加载菜品数据，如不存在则创建默认数据"""
        if os.path.exists(self.dishes_file):
            try:
                with open(self.dishes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        # 创建默认数据
        default = DEFAULT_DISHES.copy()
        self._save_dishes(default)
        return default

    def _save_dishes(self, dishes: List[Dict] = None):
        """保存菜品数据到JSON文件"""
        data = dishes if dishes is not None else self.dishes
        with open(self.dishes_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_dishes(self) -> List[Dict]:
        """获取所有菜品"""
        return self.dishes

    def get_dish_by_id(self, dish_id: str) -> Optional[Dict]:
        """根据ID获取菜品"""
        for d in self.dishes:
            if d["id"] == dish_id:
                return d
        return None

    def get_dishes_by_canteen(self, canteen_name: str) -> List[Dict]:
        """根据食堂获取菜品"""
        return [d for d in self.dishes if d["canteen"] == canteen_name]

    def get_dishes_by_cuisine(self, cuisine: str) -> List[Dict]:
        """根据菜系获取菜品"""
        return [d for d in self.dishes if d["cuisine"] == cuisine]

    def get_dishes_by_flavor(self, flavor: str) -> List[Dict]:
        """根据口味获取菜品"""
        return [d for d in self.dishes if flavor in d.get("flavor", [])]

    def add_dish(self, dish: Dict) -> bool:
        """添加新菜品"""
        self.dishes.append(dish)
        self._save_dishes()
        return True

    def update_dish(self, dish_id: str, updates: Dict) -> bool:
        """更新菜品信息"""
        for d in self.dishes:
            if d["id"] == dish_id:
                d.update(updates)
                self._save_dishes()
                return True
        return False

    def delete_dish(self, dish_id: str) -> bool:
        """删除菜品"""
        original_len = len(self.dishes)
        self.dishes = [d for d in self.dishes if d["id"] != dish_id]
        if len(self.dishes) < original_len:
            self._save_dishes()
            return True
        return False

    # ============ 用户画像 ============

    def _load_profile(self) -> Dict:
        """加载用户画像"""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default_profile()

    @staticmethod
    def _default_profile() -> Dict:
        """默认用户画像"""
        return {
            "constraints": {"taboos": [], "budget_limit": 50, "meal_pref": "正餐"},
            "goals": "均衡",  # 减脂/增肌/均衡/无
            "preferences": {"distance": "就近优先", "queue": "接受排队"},
            "social": {"companions": 1, "room_code": ""},
            "disliked_ingredients": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _save_profile(self):
        """保存用户画像"""
        self.profile["updated_at"] = datetime.now().isoformat()
        with open(self.profile_file, 'w', encoding='utf-8') as f:
            json.dump(self.profile, f, ensure_ascii=False, indent=2)

    def get_profile(self) -> Dict:
        """获取用户画像"""
        return self.profile

    def update_profile(self, updates: Dict):
        """更新用户画像"""
        self.profile.update(updates)
        self._save_profile()

    def reset_profile(self):
        """重置用户画像"""
        self.profile = self._default_profile()
        self._save_profile()

    # ============ 就餐历史 ============

    def _load_history(self) -> List[Dict]:
        """加载就餐历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self):
        """保存就餐历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def get_history(self, days: int = 30) -> List[Dict]:
        """获取近N天的就餐历史"""
        cutoff = datetime.now() - timedelta(days=days)
        return [h for h in self.history if datetime.fromisoformat(h["time"]) > cutoff]

    def add_history(self, dish_id: str, dish_name: str, canteen: str):
        """添加就餐记录"""
        record = {
            "id": f"h_{len(self.history)+1:04d}",
            "dish_id": dish_id,
            "dish_name": dish_name,
            "canteen": canteen,
            "time": datetime.now().isoformat(),
        }
        self.history.insert(0, record)
        self._save_history()
        return record

    def is_recently_eaten(self, dish_id: str, days: int = 3) -> bool:
        """检查是否最近N天内吃过"""
        cutoff = datetime.now() - timedelta(days=days)
        for h in self.history:
            if h["dish_id"] == dish_id and datetime.fromisoformat(h["time"]) > cutoff:
                return True
        return False

    def get_eaten_count(self, dish_id: str, days: int = 30) -> int:
        """获取近N天内某菜品的食用次数"""
        cutoff = datetime.now() - timedelta(days=days)
        return sum(1 for h in self.history
                   if h["dish_id"] == dish_id and datetime.fromisoformat(h["time"]) > cutoff)

    def get_eaten_dish_ids(self, days: int = 30) -> set:
        """获取近N天内吃过的菜品ID集合"""
        cutoff = datetime.now() - timedelta(days=days)
        return {
            h["dish_id"] for h in self.history
            if datetime.fromisoformat(h["time"]) > cutoff
        }

    def get_last_eaten_time(self, dish_id: str) -> Optional[datetime]:
        """获取某菜品最近一次就餐时间"""
        latest = None
        for h in self.history:
            if h["dish_id"] != dish_id:
                continue
            t = datetime.fromisoformat(h["time"])
            if latest is None or t > latest:
                latest = t
        return latest

    def has_eating_history(self) -> bool:
        """是否有就餐历史"""
        return len(self.history) > 0

    def get_canteen_region(self, canteen_name: str) -> Optional[str]:
        """根据食堂名称获取所属校园区域ID"""
        for region_id, info in CAMPUS_REGIONS.items():
            if canteen_name in info["canteens"]:
                return region_id
        return None

    def get_budget_limit(self) -> float:
        """从用户画像读取预算上限（兼容新旧格式）"""
        profile = self.profile
        if "budget_range" in profile:
            return profile["budget_range"].get("max", 50)
        return profile.get("constraints", {}).get("budget_limit", 50)

    def get_nutrition_goal(self) -> str:
        """读取营养目标（兼容新旧格式）"""
        return self.profile.get("nutrition_goals") or self.profile.get("goals", "均衡")

    def get_preferred_flavors(self) -> List[str]:
        """读取口味偏好（兼容新旧格式）"""
        return self.profile.get("preferred_flavors", [])

    def get_disliked_flavors(self) -> List[str]:
        """读取不喜欢的口味"""
        return self.profile.get("disliked_flavors", [])

    # ============ 评价数据 ============

    def _load_reviews(self) -> List[Dict]:
        """加载评价数据"""
        if os.path.exists(self.reviews_file):
            try:
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_reviews(self):
        """保存评价数据"""
        with open(self.reviews_file, 'w', encoding='utf-8') as f:
            json.dump(self.reviews, f, ensure_ascii=False, indent=2)

    def add_review(self, dish_id: str, rating: int, tags: List[str] = None, comment: str = ""):
        """添加评价"""
        review = {
            "id": f"r_{len(self.reviews)+1:04d}",
            "dish_id": dish_id,
            "rating": rating,
            "tags": tags or [],
            "comment": comment,
            "time": datetime.now().isoformat(),
        }
        self.reviews.append(review)
        self._save_reviews()
        # 更新菜品评分
        self._update_dish_rating(dish_id)
        return review

    def _update_dish_rating(self, dish_id: str):
        """使用贝叶斯平均更新菜品评分"""
        reviews = [r for r in self.reviews if r["dish_id"] == dish_id]
        if not reviews:
            return
        # 贝叶斯平均参数
        C = 10  # 置信参数
        m = 3.5  # 全局平均评分
        n = len(reviews)
        avg = sum(r["rating"] for r in reviews) / n
        # 贝叶斯平均
        bayesian = (C * m + n * avg) / (C + n)
        self.update_dish(dish_id, {"rating": round(bayesian, 2), "rating_count": n})

    def get_reviews_for_dish(self, dish_id: str) -> List[Dict]:
        """获取某菜品的所有评价"""
        return [r for r in self.reviews if r["dish_id"] == dish_id]

    def get_recent_reviews(self, count: int = 10) -> List[Dict]:
        """获取最近N条评价"""
        return sorted(self.reviews, key=lambda x: x["time"], reverse=True)[:count]

    # ============ 设置 ============

    def _load_settings(self) -> Dict:
        """加载设置"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default_settings()

    @staticmethod
    def _default_settings() -> Dict:
        """默认设置"""
        return {
            "explore_mode": False,
            "explore_epsilon": 0.15,
            "default_recommend_mode": "stable",
            "notifications": True,
            "theme": "watercolor",
            "font_size": "medium",
        }

    def _save_settings(self):
        """保存设置"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def get_settings(self) -> Dict:
        """获取设置"""
        return self.settings

    def update_settings(self, updates: Dict):
        """更新设置"""
        self.settings.update(updates)
        self._save_settings()

    # ============ 通用方法 ============

    def export_data(self, filepath: str) -> bool:
        """导出所有数据"""
        try:
            data = {
                "dishes": self.dishes,
                "profile": self.profile,
                "history": self.history,
                "reviews": self.reviews,
                "settings": self.settings,
                "exported_at": datetime.now().isoformat(),
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    def import_data(self, filepath: str) -> bool:
        """导入数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "dishes" in data:
                self.dishes = data["dishes"]
                self._save_dishes()
            if "profile" in data:
                self.profile = data["profile"]
                self._save_profile()
            if "history" in data:
                self.history = data["history"]
                self._save_history()
            if "reviews" in data:
                self.reviews = data["reviews"]
                self._save_reviews()
            if "settings" in data:
                self.settings = data["settings"]
                self._save_settings()
            return True
        except Exception as e:
            print(f"导入失败: {e}")
            return False
