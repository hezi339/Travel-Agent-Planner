"""

Agent 推理核心模块

职责：实现 ReAct 循环——LLM 思考 → 解析 action → 执行工具 → 观测反馈 → 直至 final_answer。

"""



from langchain_core.messages import SystemMessage, HumanMessage

from langchain_core.prompts import PromptTemplate



from src.llm_client import create_llm

from src.agent.parser import parse_action

from src.agent.prompts import build_system_prompt

from src.tools.tool_manager import execute_tool





def run_agent(task: str, max_iter: int = 12):

    """

    运行 Agent 主循环。



    参数:

        task: 用户自然语言需求

        max_iter: 最大推理轮数，防止死循环



    返回:

        dict: {

            "success": bool,

            "trace": list[str],

            "result": str,

            "sources": list[str],  # RAG 检索来源摘要（P3 展示用）

        }

    """

    llm = create_llm()

    system_prompt = build_system_prompt()

    prompt = PromptTemplate.from_template(system_prompt)

    sys_msg = SystemMessage(content=prompt.format())

    messages = [sys_msg, HumanMessage(content=task)]

    trace_log = []

    sources: list[str] = []



    for i in range(max_iter):

        resp = llm.invoke(messages)

        content = resp.content.strip()

        trace_log.append(f"===== 第 {i + 1} 轮模型输出 =====\n{content}")



        parsed = parse_action(content)



        if parsed["type"] == "final_answer":

            return {

                "success": True,

                "trace": trace_log,

                "result": parsed["content"],

                "sources": sources,

            }

        elif parsed["type"] == "action":

            obs = execute_tool(parsed["tool_name"], parsed["tool_args"])

            if parsed["tool_name"] == "search_travel_notes" and obs.startswith("[笔记检索]"):

                # 提取来源行供 Web 展示

                for line in obs.splitlines():

                    if line.startswith("--- 片段") or line.startswith("来源："):

                        sources.append(line)

            obs_text = f"<observation>{obs}</observation>"

            trace_log.append(f"工具返回：{obs_text}")

            messages.append(SystemMessage(content=content))

            messages.append(HumanMessage(content=obs_text))

        else:

            trace_log.append("模型输出格式错误，终止推理")

            return {"success": False, "trace": trace_log, "result": "推理失败", "sources": sources}



    trace_log.append("达到最大迭代次数，终止")

    return {"success": False, "trace": trace_log, "result": "推理超时", "sources": sources}

