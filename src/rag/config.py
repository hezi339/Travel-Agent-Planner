"""
RAG 配置模块
职责：统一管理 Chroma、Embedding、Vision 相关路径与参数。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Chroma 持久化目录
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "chroma_db"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "travel_notes")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

# 智谱 Embedding-3
ZHIPU_EMBEDDING_MODEL = os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-3")
ZHIPU_EMBEDDING_DIMENSIONS = int(os.getenv("ZHIPU_EMBEDDING_DIMENSIONS", "1024"))

# Vision 模型（读截图，与文本 GLM-5.2 分开）
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
PARSED_DIR = DATA_DIR / "parsed"
SAMPLE_NOTES_DIR = DATA_DIR / "sample_notes"
