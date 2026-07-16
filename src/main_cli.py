"""
命令行入口
职责：在终端中交互式运行 Agent，适合本地调试。

运行方式（在项目根目录 Travel-Agent-Planner/ 下）:
    python -m src.main_cli
"""

from src.agent.agent_core import run_agent

if __name__ == "__main__":
    user_input = input("请输入旅行需求（例：我下周去北京徒步3天，该带什么？）：")
    res = run_agent(user_input)

    print("\n=== Agent 完整推理过程 ===")
    for log in res["trace"]:
        print(log)

    if res.get("sources"):
        print("\n===== 参考笔记来源 =====")
        for s in res["sources"]:
            print(s)

    print("\n===== 最终旅行方案 =====")
    print(res["result"])
