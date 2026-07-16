"""
文本切块模块
职责：将长笔记切成适合检索的 chunk，并保留 metadata。
"""

from langchain_core.documents import Document

from src.rag.schemas import TravelNote

# 单块最大字符数（中文约 300–500 字）
CHUNK_SIZE = 450
CHUNK_OVERLAP = 80


def chunk_note(note: TravelNote) -> list[Document]:
    """
    将一篇笔记切成多个 Document。
    若全文较短则只产生 1 个 chunk。
    """
    full_text = note.to_document_text().strip()
    if not full_text:
        return []

    base_meta = note.to_metadata()
    chunks: list[Document] = []

    if len(full_text) <= CHUNK_SIZE:
        chunks.append(
            Document(
                page_content=full_text,
                metadata={**base_meta, "chunk_index": 0, "chunk_total": 1},
            )
        )
        return chunks

    # 按段落优先切，否则滑动窗口
    paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]
    current = ""
    buffer: list[str] = []

    for para in paragraphs:
        if len(current) + len(para) + 1 <= CHUNK_SIZE:
            current = f"{current}\n{para}".strip()
        else:
            if current:
                buffer.append(current)
            current = para
    if current:
        buffer.append(current)

    # 若段落合并后仍有过长块，再硬切
    final_parts: list[str] = []
    for part in buffer:
        if len(part) <= CHUNK_SIZE:
            final_parts.append(part)
        else:
            start = 0
            while start < len(part):
                final_parts.append(part[start : start + CHUNK_SIZE])
                start += CHUNK_SIZE - CHUNK_OVERLAP

    total = len(final_parts)
    for i, text in enumerate(final_parts):
        chunks.append(
            Document(
                page_content=text,
                metadata={**base_meta, "chunk_index": i, "chunk_total": total},
            )
        )
    return chunks
