"""
ai_conversation.py - AI 多轮对话状态机（3-4 轮确认需求后再推荐）
"""

from typing import Dict, List, Optional


class AIConversationManager:
    """管理对话阶段与槽位填充"""

    PHASES = ["greeting", "mood", "budget", "companions", "flavor", "ready"]

    QUESTIONS = {
        "mood": "今天心情怎么样？累了一天、还是状态不错想吃点好的？",
        "budget": "大概想花多少钱？（10元内 / 10-20 / 20-30 / 30以上）",
        "companions": "是一个人吃，还是和同学一起？",
        "flavor": "更想吃哪种口味？清淡、微辣、麻辣、酸甜都可以告诉我~",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase_index = 0
        self.turn_count = 0
        self.slots: Dict = {
            "mood": None,
            "budget": None,
            "budget_max": 30,
            "companions": 1,
            "meal_scene": "独自速食",
            "flavors": [],
            "location_node_id": None,
            "location": None,
            "location_preference": "",
        }
        self.history: List[Dict] = []

    def record_user(self, text: str):
        self.history.append({"role": "user", "content": text})
        self.turn_count += 1
        self._extract_slots(text)

    def record_assistant(self, text: str):
        self.history.append({"role": "assistant", "content": text})

    def _extract_slots(self, text: str):
        if any(w in text for w in ("累", "疲", "加班", "困")):
            self.slots["mood"] = "疲惫"
        elif any(w in text for w in ("开心", "高兴", "庆祝")):
            self.slots["mood"] = "开心"

        for label, val in [("10元", 10), ("20元", 20), ("30元", 30), ("50元", 50)]:
            if label in text or f"{val}元" in text:
                self.slots["budget_max"] = val
                self.slots["budget"] = label

        if any(w in text for w in ("一起", "同学", "朋友", "聚餐", "我们")):
            self.slots["companions"] = 2
            self.slots["meal_scene"] = "同伴聚餐"
        elif any(w in text for w in ("课题组", "社团", "宴请", "多人")):
            self.slots["companions"] = 4
            self.slots["meal_scene"] = "团体宴请"
        elif any(w in text for w in ("一个人", "独自", "单身", "自己")):
            self.slots["companions"] = 1

        flavor_map = {"清淡": "清淡", "微辣": "微辣", "麻辣": "麻辣", "酸甜": "酸甜", "浓郁": "浓郁", "辣": "微辣"}
        for kw, fv in flavor_map.items():
            if kw in text and fv not in self.slots["flavors"]:
                self.slots["flavors"].append(fv)

        window_hints = [
            "东侧窗口", "西侧窗口", "水饺", "家常菜", "日韩料理", "西北风味",
            "西式简餐", "清真", "粤菜", "麻辣烫", "铁板炒饭", "南昌拌米粉", "水果",
        ]
        for wh in window_hints:
            if wh in text:
                self.slots["location_preference"] = wh
                break
        if not self.slots["location_preference"]:
            for kw in ("二层", "一层", "地下"):
                if kw in text:
                    self.slots["location_preference"] = kw
                    break

    def set_location(self, node_id: int, name: str):
        self.slots["location_node_id"] = node_id
        self.slots["location"] = name

    def _missing_slot_phase(self) -> Optional[str]:
        if self.slots["mood"] is None and self.turn_count <= 2:
            return "mood"
        if self.slots["budget"] is None:
            return "budget"
        if self.turn_count <= 3 and self.slots["companions"] == 1 and not any(
            w in " ".join(m["content"] for m in self.history if m["role"] == "user")
            for w in ("一起", "同学", "自己", "独自")
        ):
            return "companions"
        if not self.slots["flavors"]:
            return "flavor"
        return None

    def is_ready_to_recommend(self) -> bool:
        if not self.slots.get("location_node_id"):
            return False
        if self.turn_count < 2:
            return False
        if self._missing_slot_phase() is None:
            return True
        return self.turn_count >= 4

    def get_follow_up(self) -> Optional[str]:
        if not self.slots.get("location_node_id"):
            return "先告诉我你在哪里，或在上方的「我的位置」里选一下~"
        phase = self._missing_slot_phase()
        if phase and not self.is_ready_to_recommend():
            return self.QUESTIONS.get(phase, "还有什么想补充的吗？")
        return None

    def get_phase_label(self) -> str:
        if not self.slots.get("location_node_id"):
            return "确认位置"
        if self._missing_slot_phase():
            return "了解偏好"
        if self.is_ready_to_recommend():
            return "准备推荐"
        return "聊天中"

    def to_context(self) -> Dict:
        scene = self.slots["meal_scene"]
        if self.slots["companions"] >= 4:
            scene = "团体宴请"
        elif self.slots["companions"] >= 2:
            scene = "同伴聚餐"
        elif self.slots.get("mood") == "疲惫":
            scene = "独自速食"
        return {
            "recommend_mode": "stable",
            "meal_scene": scene,
            "budget_limit": self.slots["budget_max"],
            "preferred_flavors": self.slots["flavors"],
            "location": self.slots.get("location", ""),
            "location_node_id": self.slots.get("location_node_id"),
            "location_preference": self.slots.get("location_preference", ""),
            "include_combos": self.slots["companions"] >= 2,
        }

    def build_summary(self) -> str:
        parts = []
        if self.slots.get("location"):
            parts.append(f"位置·{self.slots['location']}")
        if self.slots.get("budget"):
            parts.append(f"预算·{self.slots['budget']}")
        if self.slots["flavors"]:
            parts.append("口味·" + "/".join(self.slots["flavors"]))
        parts.append(f"{'聚餐' if self.slots['companions']>=2 else '独自'}({self.slots['companions']}人)")
        return " · ".join(parts)
