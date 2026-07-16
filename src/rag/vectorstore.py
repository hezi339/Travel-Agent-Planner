"""
Chroma 向量库模块
职责：笔记入库、相似度检索、去重、按城市过滤、增量更新。
"""

import hashlib
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.rag.chunker import chunk_note
from src.rag.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, RAG_TOP_K
from src.rag.embedder import get_embeddings
from src.rag.schemas import TravelNote


def _chunk_doc_id(note_id: str, chunk_index: int, content: str) -> str:
    """生成稳定 chunk ID，用于去重。"""
    digest = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
    return f"{note_id}__chunk{chunk_index}__{digest}"


class TravelNoteVectorStore:
    """旅行笔记向量库封装。"""

    def __init__(self):
        self.embeddings = get_embeddings()
        self.store = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=self.embeddings,
        )

    def note_exists(self, note_id: str) -> bool:
        """检查某 note_id 是否已入库。"""
        try:
            results = self.store.get(where={"note_id": note_id})
            return bool(results and results.get("ids"))
        except Exception:
            return False

    def delete_note(self, note_id: str) -> int:
        """删除某笔记的全部 chunk（用于强制更新）。"""
        try:
            results = self.store.get(where={"note_id": note_id})
            ids = results.get("ids") or []
            if ids:
                self.store.delete(ids=ids)
            return len(ids)
        except Exception:
            return 0

    def add_note(
        self,
        note: TravelNote,
        *,
        force: bool = False,
    ) -> int:
        """
        将一篇笔记切块后写入 Chroma。
        - force=False：若 note_id 已存在则跳过（增量）
        - force=True：先删后写（更新）
        返回写入 chunk 数量。
        """
        if self.note_exists(note.note_id):
            if not force:
                return 0
            self.delete_note(note.note_id)

        docs = chunk_note(note)
        if not docs:
            return 0

        ids = [
            _chunk_doc_id(note.note_id, doc.metadata.get("chunk_index", i), doc.page_content)
            for i, doc in enumerate(docs)
        ]
        self.store.add_documents(documents=docs, ids=ids)
        return len(docs)

    def add_documents_raw(self, documents: list[Document]) -> int:
        """直接写入 Document 列表（假数据入库用）。"""
        if not documents:
            return 0
        ids = []
        for i, doc in enumerate(documents):
            note_id = doc.metadata.get("note_id", f"raw_{i}")
            chunk_index = doc.metadata.get("chunk_index", i)
            ids.append(_chunk_doc_id(note_id, chunk_index, doc.page_content))
        self.store.add_documents(documents=documents, ids=ids)
        return len(documents)

    def search(
        self,
        query: str,
        *,
        top_k: int = RAG_TOP_K,
        city: str | None = None,
    ) -> list[Document]:
        """
        相似度检索。
        city：可选，按 metadata 过滤城市（P4）。
        """
        kwargs: dict[str, Any] = {"k": top_k}
        if city and city.strip():
            kwargs["filter"] = {"city": city.strip()}
        return self.store.similarity_search(query, **kwargs)

    def count(self) -> int:
        """向量库中文档数量。"""
        try:
            return self.store._collection.count()
        except Exception:
            return 0


def get_vectorstore() -> TravelNoteVectorStore:
    return TravelNoteVectorStore()
