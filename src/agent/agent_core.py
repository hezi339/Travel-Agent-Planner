"""
Agent 推理核心模块
职责：实现 ReAct 循环——LLM 思考 → 解析 action → 执行工具 → 观测反馈 → 直至 final_answer。
"""

from datetime import date

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate

from src.llm_client import create_llm
from src.agent.parser import parse_action
from src.tools.tool_manager import execute_tool

# 系统提示词：约束 LLM 输出格式，并说明可用工具
SYSTEM_PROMPT = f"""
你是专业旅行规划智能体，拥有以下工具：
1. get_weather(city, date): 查询指定城市当日天气
   - city: 城市名，如 广州、北京（不要加引号）
   - date: 日期，必须使用 YYYY-MM-DD 格式；用户说「今天」时请用 {date.today().isoformat()}
2. recommend_clothing(weather, activity): 根据天气和出行类型推荐穿搭
3. checklist_categories(days): 根据出行天数生成行李分类清单

严格遵循输出格式，只能二选一：
1. 需要调用工具时输出：
<thought>你的思考过程，说明为什么调用工具</thought>
<action>工具名(参数1,参数2)</action>

2. 信息足够后输出最终回答：
<thought>整合所有工具信息，生成完整旅行方案</thought>
<final_answer>完整旅行清单、穿搭建议、出行提示</final_answer>

禁止编造数据，所有天气、出行建议必须依赖工具返回结果。
"""


def run_agent(task: str, max_iter: int = 10):
    """
    运行 Agent 主循环。

    参数:
        task: 用户自然语言需求
        max_iter: 最大推理轮数，防止死循环

    返回:
        dict: {
            "success": bool,
            "trace": list[str],   # 完整推理链路，供 CLI / Web 展示
            "result": str         # 最终方案或错误信息
        }
    """
    llm = create_llm()
    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
    sys_msg = SystemMessage(content=prompt.format())
    messages = [sys_msg, HumanMessage(content=task)]
    trace_log = []

    for i in range(max_iter):
        # 调用 LLM 获取本轮输出
        resp = llm.invoke(messages)
        content = resp.content.strip()
        trace_log.append(f"===== 第 {i + 1} 轮模型输出 =====\n{content}")

        parsed = parse_action(content)

        if parsed["type"] == "final_answer":
            # 推理成功结束
            return {
                "success": True,
                "trace": trace_log,
                "result": parsed["content"],
            }
        elif parsed["type"] == "action":
            # 执行工具，将观测结果追加到对话历史
            obs = execute_tool(parsed["tool_name"], parsed["tool_args"])
            obs_text = f"<observation>{obs}</observation>"
            trace_log.append(f"工具返回：{obs_text}")
            messages.append(SystemMessage(content=content))
            messages.append(HumanMessage(content=obs_text))
        else:
            # LLM 输出格式不符合约定
            trace_log.append("模型输出格式错误，终止推理")
            return {"success": False, "trace": trace_log, "result": "推理失败"}

    # 超过最大轮数仍未得到 final_answer
    trace_log.append("达到最大迭代次数，终止")
    return {"success": False, "trace": trace_log, "result": "推理超时"}
