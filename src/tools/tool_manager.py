"""
工具调度模块
职责：维护「工具名 → 函数」映射表，供 Agent 统一调用，避免 agent_core 与具体工具耦合。
"""

from src.tools.weather_api import get_weather
from src.tools.travel_tool import recommend_clothing, checklist_categories

# Agent 可调用的工具注册表（名称须与 SYSTEM_PROMPT 中描述一致）
TOOL_MAP = {
    "get_weather": get_weather,
    "recommend_clothing": recommend_clothing,
    "checklist_categories": checklist_categories,
}


def execute_tool(tool_name: str, tool_args: list):
    """
    根据工具名和参数列表执行对应函数，返回字符串结果。
    出错时返回错误信息字符串，供 LLM 在下一轮观测中自行修正。
    """
    if tool_name not in TOOL_MAP:
        return f"Error: Tool '{tool_name}' not found"

    try:
        func = TOOL_MAP[tool_name]
        # 清理 LLM 可能传入的多余引号、逗号
        tool_args = [
            str(arg).strip().strip("'\"").rstrip(",")
            for arg in tool_args
        ]

        if tool_name == "checklist_categories":
            tool_args[0] = int(tool_args[0])
        elif tool_name == "get_weather" and len(tool_args) >= 2:
            # 确保只取前两个参数：城市、日期
            tool_args = tool_args[:2]

        result = str(func(*tool_args))
        # 成功时带上来源标记，方便确认跑的是新代码（可删）
        if tool_name == "get_weather":
            return f"[Open-Meteo] {result}"
        return result
    except Exception as e:
        return f"工具执行异常[{tool_name}] {type(e).__name__}: {e}"
