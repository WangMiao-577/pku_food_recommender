"""
ai_backend.py - AI 模式后端控制器
通过大模型 API 驱动对话式推荐；未配置密钥时优雅降级到离线推荐。
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Any

from backend.data_manager import DataManager
from backend.recommender import Recommender
from backend.campus_navigation import CampusNavigationService
from backend import ai_config


class AIModeBackend:
    """AI 模式后端 - 对话推荐与用户画像提取"""

    def __init__(
        self,
        data_manager: DataManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.dm = data_manager
        self.recommender = Recommender(data_manager)
        self.nav = CampusNavigationService.get_instance()
        self.conversation_history: List[Dict[str, str]] = []
        self._load_config(api_key, api_base, model)

    def _load_config(self, api_key=None, api_base=None, model=None):
        settings = self.dm.get_settings()
        ai_cfg = settings.get("ai_config", {})
        self.api_key = api_key or ai_cfg.get("api_key") or ai_config.AI_API_KEY
        self.api_base = api_base or ai_cfg.get("api_base") or ai_config.AI_API_BASE or "https://api.openai.com/v1"
        self.model = model or ai_cfg.get("model") or ai_config.AI_MODEL or "deepseek-chat"

    def reload_config(self):
        """从 settings 重新加载 API 配置"""
        self._load_config()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    # ==================== 对外 API（预留接口） ====================

    def chat_recommend(self, user_message: str, user_profile: Optional[Dict] = None) -> Dict:
        """
        对话式推荐入口

        Returns:
            {
                "success": bool,
                "reply": str,
                "recommended_dishes": [dict, ...],
                "dish_ids": ["d001", ...],
                "reasoning": str,
                "extracted_preferences": dict,
                "fallback": bool,
            }
        """
        profile = user_profile or self.dm.get_profile()
        self.conversation_history.append({"role": "user", "content": user_message})

        if not self.is_configured():
            return self._fallback_recommend(user_message, profile, reason="未配置 API 密钥")

        try:
            raw = self._call_llm_api(user_message, profile)
            parsed = self._parse_llm_response(raw)
            self.conversation_history.append({"role": "assistant", "content": parsed.get("reply", raw)})

            prefs = parsed.get("extracted_preferences") or {}
            if prefs:
                self._merge_preferences(prefs)

            dish_ids = parsed.get("recommended_dish_ids") or []
            dishes = [self.dm.get_dish_by_id(did) for did in dish_ids if self.dm.get_dish_by_id(did)]

            if not dishes:
                context = self._preferences_to_context(prefs, user_message)
                result = self.recommender.recommend_full(top_k=5, mode="normal", context=context)
                dishes = result.get("dishes", [])
                dish_ids = [d["id"] for d in dishes]

            return {
                "success": True,
                "reply": parsed.get("reply", raw),
                "recommended_dishes": dishes,
                "dish_ids": dish_ids,
                "reasoning": parsed.get("reasoning", ""),
                "extracted_preferences": prefs,
                "fallback": False,
            }
        except Exception as e:
            return self._fallback_recommend(user_message, profile, reason=str(e))

    def extract_preferences(self, conversation: Optional[List[Dict]] = None) -> Dict:
        """从对话历史中提取用户偏好（与 offline user_profile 格式一致）"""
        conv = conversation or self.conversation_history
        if not conv:
            return {}

        if not self.is_configured():
            return self._extract_preferences_local(conv)

        try:
            prompt = (
                "从以下对话中提取用户用餐偏好，仅返回 JSON，字段包括："
                "preferred_flavors, budget_range, preferred_canteens, meal_scenes, "
                "nutrition_goals, explore_stability_ratio, current_location\n\n"
                + json.dumps(conv, ensure_ascii=False)
            )
            raw = self._call_llm_api(prompt, self.dm.get_profile(), system_override="你是结构化信息提取助手。")
            return self._parse_json_block(raw) or {}
        except Exception:
            return self._extract_preferences_local(conv)

    def generate_dish_design(self, user_criteria: Dict) -> Dict:
        """
        【预留】根据用户偏好进行创意菜品设计
        未配置 API 时返回占位结构
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "需要配置 AI API 密钥",
                "concept": None,
            }
        try:
            prompt = (
                "根据以下条件设计一道适合北大食堂的新菜品概念，返回 JSON："
                "name, ingredients, cooking, price, reason\n\n"
                + json.dumps(user_criteria, ensure_ascii=False)
            )
            raw = self._call_llm_api(prompt, self.dm.get_profile(), system_override="你是校园餐饮创意顾问。")
            concept = self._parse_json_block(raw)
            return {"success": True, "concept": concept, "raw": raw}
        except Exception as e:
            return {"success": False, "error": str(e), "concept": None}

    def get_location_from_ip(self) -> str:
        """已弃用：离线运行需用户手动选择位置。返回当前已保存位置名称。"""
        return self.dm.get_profile().get("current_location", "")

    def resolve_location_from_text(self, text: str) -> Optional[int]:
        """从自然语言中解析地图节点 ID"""
        if not text:
            return None
        for node in self.nav.list_nodes():
            if node["name"] in text:
                return node["node_id"]
        return self.nav.resolve_node(text)

    def test_connection(self) -> Dict:
        """测试 API 连接"""
        if not self.is_configured():
            return {"success": False, "message": "未配置 API 密钥"}
        try:
            reply = self._call_llm_api("回复：连接成功", {}, system_override="你只回复四个字：连接成功")
            ok = "成功" in reply or "success" in reply.lower()
            return {"success": ok, "message": reply[:100]}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def reset_conversation(self):
        self.conversation_history.clear()

    def get_opening_message(self) -> str:
        return (
            "你好！我是你的 AI 美食助手。\n"
            "请先在上方选择你的当前位置，或告诉我你在哪里（如：图书馆、东南门、未名湖）。\n"
            "然后说说今天想吃点什么~"
        )

    # ==================== LLM 调用（预留实现） ====================

    def _call_llm_api(
        self,
        user_message: str,
        user_profile: Dict,
        system_override: Optional[str] = None,
    ) -> str:
        """
        调用大模型 API（OpenAI 兼容格式）- 针对 DeepSeek 严格校验优化版
        """
        import requests

        # 1. 确定 System 提示词
        system = system_override or self._build_system_prompt(user_profile)
        messages = [{"role": "system", "content": system}]
        
        # 2. 判断当前是什么任务
        # 如果有 system_override，说明是“测试连接”、“提取偏好”或“设计菜品”，属于单次结构化任务
        # 此时绝对不能混入之前的对话聊天历史，否则会因为角色错乱报 400！
        if system_override:
            messages.append({"role": "user", "content": user_message})
        else:
            # 只有在真正的聊天推荐时，才需要拼接上下文历史
            # 过滤掉最后一条（因为最后一条即将在下面重新传入，防止重复）
            history = self.conversation_history[:-1] if self.conversation_history else []
            
            # 严格做一次交替清洗，确保中间没有连续的 user-user 或 assistant-assistant
            sanitized_history = []
            for msg in history[-6:]: # 取最近 3 轮交互足够了
                if sanitized_history and sanitized_history[-1]["role"] == msg["role"]:
                    # 相同角色直接内容合并，防止触发 400
                    sanitized_history[-1]["content"] += "\n" + msg["content"]
                else:
                    sanitized_history.append({"role": msg["role"], "content": msg["content"]})
            
            messages.extend(sanitized_history)
            
            # 确保最后塞入本次最新的用户消息
            if messages[-1]["role"] == "user":
                messages[-1]["content"] = user_message
            else:
                messages.append({"role": "user", "content": user_message})

        # 3. 构建请求体
        url = self.api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2, # 降低随机性有利于返回干净的JSON
            "max_tokens": 1500, # 适当放大生成空间，防止被截断
        }

        # 如果还是报错，你可以取消下面这行注释，在终端看看打印出的完整Payload到底长什么样
        # print("发送的完整Payload为:", json.dumps(payload, ensure_ascii=False, indent=2))

        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        # 如果报 400，把详细的错误原因打印出来，方便直接定位
        if response.status_code == 400:
            print(f"🛑 DeepSeek 400 错误详情: {response.text}")
            
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _build_system_prompt(self, profile: Dict) -> str:
        dishes = self.dm.get_all_dishes()
        summary_lines = [
            f"- {d['name']} @ {d['canteen']} ¥{d['price']} 口味:{','.join(d.get('flavor', []))}"
            for d in dishes[:40]
        ]
        dishes_summary = "\n".join(summary_lines)

        node_lines = [
            f"- 节点{n['node_id']}: {n['name']} ({n['category']})"
            for n in self.nav.list_nodes()[:30]
        ]
        nodes_summary = "\n".join(node_lines)

        return f"""{ai_config.DEFAULT_SYSTEM_PROMPT}

可用菜品数据库（摘要）:
{dishes_summary}

校园地图节点（current_location 请填节点名称，如「图书馆」「东南门」）:
{nodes_summary}

当前用户画像:
{json.dumps(profile, ensure_ascii=False)}

请在回复末尾附带 JSON 块（用 ```json 包裹），格式:
{{
  "reply": "给用户的中文回复",
  "reasoning": "推荐理由摘要",
  "recommended_dish_ids": ["d001", "d002"],
  "extracted_preferences": {{
    "preferred_flavors": [],
    "budget_range": {{"min": 0, "max": 30}},
    "meal_scenes": [],
    "nutrition_goals": "均衡",
    "explore_stability_ratio": 0.3,
    "current_location": "图书馆"
  }}
}}
"""

    # ==================== 解析与降级 ====================

    def _parse_llm_response(self, raw: str) -> Dict:
        block = self._parse_json_block(raw) or {}
        if "reply" not in block:
            block["reply"] = raw.split("```")[0].strip()
        return block

    @staticmethod
    def _parse_json_block(text: str) -> Optional[Dict]:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _fallback_recommend(self, user_message: str, profile: Dict, reason: str = "") -> Dict:
        """API 不可用时的离线降级"""
        context = self._extract_preferences_local([{"role": "user", "content": user_message}])
        context = self._preferences_to_context(context, user_message)
        result = self.recommender.recommend_full(top_k=5, mode="normal", context=context)
        dishes = result.get("dishes", [])
        msg = "AI 服务暂时不可用，已切换到离线推荐模式。"
        if reason and "未配置" not in reason:
            msg += f" ({reason})"
        return {
            "success": True,
            "reply": msg + " 根据你的描述，为你挑选了以下菜品：",
            "recommended_dishes": dishes,
            "dish_ids": [d["id"] for d in dishes],
            "reasoning": "离线算法推荐",
            "extracted_preferences": context,
            "fallback": True,
            "combos": result.get("combos", []),
            "recommend_mode": result.get("recommend_mode", "stable"),
        }

    def _extract_preferences_local(self, conversation: List[Dict]) -> Dict:
        """简单关键词提取（无 API 时使用）"""
        text = " ".join(m.get("content", "") for m in conversation if m.get("role") == "user")
        budget_max = self.dm.get_budget_limit()
        prefs = {
            "preferred_flavors": [],
            "budget_range": {"min": 0, "max": budget_max},
            "meal_scenes": [],
            "nutrition_goals": self.dm.get_nutrition_goal(),
            "explore_stability_ratio": 0.3,
            "current_location": "",
        }
        flavor_keywords = {
            "清淡": "清淡", "微辣": "微辣", "麻辣": "麻辣", "甜": "酸甜", "酸": "酸甜", "浓郁": "浓郁",
        }
        for kw, flavor in flavor_keywords.items():
            if kw in text and flavor not in prefs["preferred_flavors"]:
                prefs["preferred_flavors"].append(flavor)

        node_id = self.resolve_location_from_text(text)
        if node_id:
            node = self.nav.get_node(node_id)
            if node:
                prefs["current_location"] = node["name"]
                prefs["current_location_node_id"] = node_id
        elif profile_loc := self.dm.get_profile().get("current_location"):
            prefs["current_location"] = profile_loc
            prefs["current_location_node_id"] = self.dm.get_profile().get("current_location_node_id")

        for label, val in [("10元", 10), ("20元", 20), ("30元", 30)]:
            if label in text:
                prefs["budget_range"]["max"] = val

        if any(w in text for w in ("聚餐", "同学", "朋友", "一起")):
            prefs["meal_scenes"] = ["同伴聚餐"]
        elif any(w in text for w in ("赶", "快", "急")):
            prefs["meal_scenes"] = ["独自速食"]

        return prefs

    def _preferences_to_context(self, prefs: Dict, user_message: str = "") -> Dict:
        text = user_message or ""
        explore = prefs.get("explore_stability_ratio", 0.3)
        profile = self.dm.get_profile()
        node_id = prefs.get("current_location_node_id") or profile.get("current_location_node_id")
        loc_name = prefs.get("current_location") or profile.get("current_location", "")
        return {
            "recommend_mode": "explore" if explore >= 0.5 else "stable",
            "meal_scene": (prefs.get("meal_scenes") or [None])[0],
            "budget_limit": prefs.get("budget_range", {}).get("max", self.dm.get_budget_limit()),
            "preferred_flavors": prefs.get("preferred_flavors", []),
            "location": loc_name,
            "location_node_id": node_id,
            "include_combos": "同伴聚餐" in (prefs.get("meal_scenes") or []) or "聚餐" in text,
        }

    def _merge_preferences(self, prefs: Dict):
        profile = self.dm.get_profile()
        if prefs.get("preferred_flavors"):
            profile["preferred_flavors"] = prefs["preferred_flavors"]
        if prefs.get("budget_range"):
            profile["budget_range"] = prefs["budget_range"]
            profile.setdefault("constraints", {})["budget_limit"] = prefs["budget_range"].get("max", 30)
        if prefs.get("meal_scenes"):
            profile["meal_scenes"] = prefs["meal_scenes"]
        if prefs.get("nutrition_goals"):
            profile["nutrition_goals"] = prefs["nutrition_goals"]
            profile["goals"] = prefs["nutrition_goals"]
        if prefs.get("current_location"):
            profile["current_location"] = prefs["current_location"]
            nid = prefs.get("current_location_node_id") or self.nav.resolve_node(prefs["current_location"])
            if nid:
                profile["current_location_node_id"] = nid
        if "explore_stability_ratio" in prefs:
            profile["explore_stability_ratio"] = prefs["explore_stability_ratio"]
            profile["default_mode"] = "explore" if prefs["explore_stability_ratio"] >= 0.5 else "stable"
        profile["updated_at"] = datetime.now().isoformat()
        self.dm.update_profile(profile)


def create_ai_backend(data_manager: DataManager) -> AIModeBackend:
    """工厂方法 - 供 main_window / interfaces 调用"""
    return AIModeBackend(data_manager)
