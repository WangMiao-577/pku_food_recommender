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

DEFAULT_SYSTEM_PROMPT = """你是北大食堂智能推荐系统的美食助手。你的任务是通过自然对话了解用户的用餐需求，然后推荐最合适的食堂菜品。

规则:
1. 对话风格亲切自然，像朋友一样聊天
2. 最多追问2轮，不要问太多问题
3. 推荐时给出2-3个具体选择+1个 adventurous 选项
4. 每次回复必须在 JSON 块中包含 extracted_preferences 字段
5. 推荐理由要具体（距离、口味、预算等）
"""
