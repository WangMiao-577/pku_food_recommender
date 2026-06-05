"""
ai_config.py - AI 模式配置
API 密钥与模型参数由用户在设置页填写，留空时使用 settings.json 中的值。
"""

# 默认占位（用户可在设置页或环境变量中覆盖）
# 默认占位
AI_API_KEY = ""
AI_API_BASE = "https://api.deepseek.com"  # 如果你用了中转，记得这里要改成中转的Base URL
AI_MODEL = "deepseek-v4-flash"     # 🛑 1. 默认模型改成你渠道支持的名字

SUPPORTED_MODELS = [
    ("deepseek-v4-flash", "DeepSeek Flash"), # 🛑 2. 修正元组顺序，让代码传过去正确的名字
    ("deepseek-v4-pro", "DeepSeek Pro"),     # 🛑 3. 同上
    ("gpt-4o", "GPT-4o"),
    ("gpt-3.5-turbo", "GPT-3.5"),
]

DEFAULT_SYSTEM_PROMPT = """你是北大食堂智能推荐系统的美食助手。通过自然对话了解用户用餐需求，再推荐菜品。

规则:
1. 对话风格亲切自然，有现场感，像在校园路边一起商量吃什么
2. 前 3-4 轮以确认需求为主：心情、预算、人数、口味、档口偏好；不要过早推荐具体菜名
3. 信息足够后再推荐，给出 2-5 道菜；聚餐场景可提及套餐搭配
4. 推荐理由要具体（距离、档口位置 location_hint、口味、预算、营养）
5. 若用户提到「东侧窗口」「水饺」等档口，在 extracted_preferences 中记录 location_preference
6. 每次回复末尾附带 JSON 块（```json 包裹）
"""
