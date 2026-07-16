"""
Embedding 模块
职责：封装智谱 embedding-3 云端 API，供 Chroma 使用。
"""

import os
from typing import List

import requests
from langchain_core.embeddings import Embeddings

from src.rag.config import (
    PROJECT_ROOT,
    ZHIPU_EMBEDDING_DIMENSIONS,
    ZHIPU_EMBEDDING_MODEL,
)
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env", override=True)

EMBEDDING_API_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"


def _get_api_key() -> str:
    key = os.getenv("ZHIPU_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
    if not key:
        raise ValueError("未配置 ZHIPU_API_KEY，无法调用 embedding-3")
    return key


class ZhipuEmbedding3(Embeddings):
    """智谱 embedding-3 LangChain Embeddings 适配器。"""

    def __init__(
        self,
        model: str = ZHIPU_EMBEDDING_MODEL,
        dimensions: int = ZHIPU_EMBEDDING_DIMENSIONS,
    ):
        self.model = model
        self.dimensions = dimensions
        self.api_key = _get_api_key()

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        resp = requests.post(
            EMBEDDING_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": texts,
                "dimensions": self.dimensions,
            },
            timeout=30,
        )
        data = resp.json()
        if resp.status_code != 200 or "data" not in data:
            raise ValueError(f"embedding-3 调用失败：{data}")
        # 按 index 排序，保证与输入顺序一致
        items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]


def get_embeddings() -> ZhipuEmbedding3:
    """获取全局 Embedding 实例。"""
    return ZhipuEmbedding3()
