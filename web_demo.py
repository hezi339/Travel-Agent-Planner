"""
Streamlit Web 演示入口
职责：提供可视化界面，展示 Agent 推理链路与最终旅行方案。

运行方式（在项目根目录 Travel-Agent-Planner/ 下）:
    streamlit run web_demo.py
"""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# 确保无论从哪个目录启动，都能加载项目根目录的 .env
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from src.agent.agent_core import run_agent
from src.llm_client import ZHIPU_BASE_URL, ZHIPU_MODEL

# 页面基础配置
st.set_page_config(page_title="AI旅行规划智能体", layout="wide")
st.title("🧳 ReAct AI旅行规划助手")
st.subheader("基于工具调用的大模型智能体 Demo")
st.caption(f"当前模型：`{ZHIPU_MODEL}` | API：`{ZHIPU_BASE_URL}`")

# 用户输入区
user_query = st.text_area(
    "输入你的旅行需求",
    placeholder="例如：我去成都游玩4天，城市观光，需要一份行李清单和穿搭建议",
    height=120,
)
run_btn = st.button("开始生成旅行方案")

if run_btn and user_query.strip():
    with st.spinner("智能体正在思考、调用天气工具..."):
        output = run_agent(user_query)

    # 左栏：推理过程；右栏：最终结果
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("🔍 Agent 完整推理链路")
        for item in output["trace"]:
            st.code(item, language="text")
    with col2:
        st.subheader("📋 最终旅行规划清单")
        st.markdown(output["result"])
elif run_btn and not user_query.strip():
    st.warning("请输入旅行需求！")
