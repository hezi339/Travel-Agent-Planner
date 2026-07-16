"""
笔记检索工具（Agent 可调用）
职责：search_travel_notes(query) → Chroma 检索 → 返回格式化片段。
"""

from src.rag.config import RAG_TOP_K
from src.rag.vectorstore import get_vectorstore


def _extract_city_hint(query: str, city: str = "") -> str | None:
    """优先用显式 city 参数，否则不做硬过滤（交给向量相似度）。"""
    city = (city or "").strip()
    return city if city else None


def search_travel_notes(query: str, city: str = "") -> str:
    """
    从 Chroma 检索与 query 相关的旅行笔记片段。
    city：可选，按 metadata 过滤城市。
    """
    query = str(query).strip().strip("'\"").rstrip(",")
    city = str(city).strip().strip("'\"").rstrip(",") if city else ""

    if not query:
        return "[笔记检索] 错误：query 不能为空"

    vs = get_vectorstore()
    if vs.count() == 0:
        return (
            "[笔记检索] 向量库为空。请先运行：\n"
            "  python scripts/seed_rag.py          # 导入假数据\n"
            "  python scripts/ingest_notes.py      # 导入截图笔记"
        )

    city_filter = _extract_city_hint(query, city)
    docs = vs.search(query, top_k=RAG_TOP_K, city=city_filter)

    if not docs:
        hint = f"（city={city_filter}）" if city_filter else ""
        return f"[笔记检索] 未找到与「{query}」相关的笔记{hint}。请换关键词或先入库截图。"

    lines = [f"[笔记检索] 共 {len(docs)} 条相关片段（query={query}）：", ""]
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        lines.extend(
            [
                f"--- 片段 {i} ---",
                f"来源：{meta.get('source', 'unknown')} | 城市：{meta.get('city', '未知')} | 笔记ID：{meta.get('note_id', '')}",
                f"标题：{meta.get('title', '')}",
                f"内容：{doc.page_content}",
                "",
            ]
        )
    lines.append("提示：最终方案中的景点/店名须来自以上片段，不得编造。")
    return "\n".join(lines)
