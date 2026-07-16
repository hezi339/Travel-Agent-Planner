"""
Streamlit Web 演示入口
职责：旅行规划 + 笔记截图入库 + RAG 来源展示。
"""

from pathlib import Path
import tempfile
import shutil

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from src.agent.agent_core import run_agent
from src.llm_client import ZHIPU_BASE_URL, ZHIPU_MODEL
from src.rag.config import SCREENSHOTS_DIR
from src.rag.ingest_pipeline import ingest_note_folder
from src.rag.vectorstore import get_vectorstore

st.set_page_config(page_title="AI旅行规划智能体", layout="wide")
st.title("🧳 ReAct AI旅行规划助手")
st.subheader("RAG 私有笔记 + 实时天气工具 Agent")
st.caption(f"模型：`{ZHIPU_MODEL}` | API：`{ZHIPU_BASE_URL}`")

# ---------- 侧边栏：笔记入库 ----------
with st.sidebar:
    st.header("📥 笔记入库")
    try:
        vs = get_vectorstore()
        st.info(f"向量库文档数：**{vs.count()}**")
    except Exception as e:
        st.error(f"向量库未就绪：{e}")
        vs = None

    note_id = st.text_input("笔记 ID", placeholder="xhs_guangzhou_001")
    uploaded = st.file_uploader(
        "上传小红书/抖音截图",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    force_update = st.checkbox("强制覆盖已存在笔记", value=False)

    if st.button("入库到 Chroma", disabled=not (note_id and uploaded)):
        if not note_id or not uploaded:
            st.warning("请填写笔记 ID 并上传至少一张截图")
        else:
            with st.spinner("Vision 解析并入库中..."):
                try:
                    dest = SCREENSHOTS_DIR / note_id
                    dest.mkdir(parents=True, exist_ok=True)
                    for f in uploaded:
                        out = dest / f.name
                        out.write_bytes(f.getbuffer())
                    result = ingest_note_folder(dest, note_id=note_id, force=force_update)
                    st.success(f"入库完成：{result}")
                except Exception as e:
                    st.error(f"入库失败：{e}")

    st.divider()
    st.caption("首次使用可先运行：`python scripts/seed_rag.py` 导入假数据")

# ---------- 主区：Agent 规划 ----------
user_query = st.text_area(
    "输入你的旅行需求",
    placeholder="例如：根据我收藏的笔记，规划广州3天城市观光，并给穿搭和行李建议",
    height=120,
)
run_btn = st.button("开始生成旅行方案")

if run_btn and user_query.strip():
    with st.spinner("智能体正在检索笔记、调用天气工具..."):
        output = run_agent(user_query)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("🔍 Agent 完整推理链路")
        for item in output.get("trace", []):
            st.code(item, language="text")
    with col2:
        st.subheader("📋 最终旅行规划清单")
        st.markdown(output.get("result", ""))

        sources = output.get("sources") or []
        if sources:
            with st.expander("📚 参考笔记来源（RAG 检索）", expanded=True):
                for s in sources:
                    st.markdown(f"- {s}")
elif run_btn and not user_query.strip():
    st.warning("请输入旅行需求！")
