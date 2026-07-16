"""
入库流水线
职责：扫描截图目录 → Vision 解析 → 合并 → 切块 → 写入 Chroma。
"""

import json
from pathlib import Path

from langchain_core.documents import Document

from src.rag.chunker import chunk_note
from src.rag.config import PARSED_DIR, SAMPLE_NOTES_DIR, SCREENSHOTS_DIR
from src.rag.schemas import TravelNote
from src.rag.vectorstore import TravelNoteVectorStore, get_vectorstore
from src.rag.vision_parser import merge_notes, parse_image

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _save_parsed(note: TravelNote) -> Path:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PARSED_DIR / f"{note.note_id}.json"
    out.write_text(json.dumps(note.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def ingest_note_folder(
    folder: str | Path,
    *,
    note_id: str | None = None,
    force: bool = False,
    vectorstore: TravelNoteVectorStore | None = None,
) -> dict:
    """
    入库一个笔记文件夹（内含 1~N 张截图）。
    返回统计信息。
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"不是有效目录：{folder}")

    vs = vectorstore or get_vectorstore()
    nid = note_id or folder.name

    if vs.note_exists(nid) and not force:
        return {"note_id": nid, "status": "skipped", "chunks_added": 0, "reason": "已存在"}

    images = sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
    if not images:
        raise FileNotFoundError(f"目录内无截图：{folder}")

    parsed_list: list[TravelNote] = []
    for img in images:
        parsed_list.append(parse_image(img, note_id=nid))

    note = merge_notes(parsed_list, note_id=nid)
    _save_parsed(note)
    chunks = vs.add_note(note, force=force)

    return {
        "note_id": nid,
        "status": "ok",
        "images": len(images),
        "chunks_added": chunks,
        "city": note.city,
        "title": note.title,
    }


def ingest_all_screenshots(
    *,
    force: bool = False,
    vectorstore: TravelNoteVectorStore | None = None,
) -> list[dict]:
    """扫描 data/screenshots/ 下所有子文件夹并入库。"""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for sub in sorted(SCREENSHOTS_DIR.iterdir()):
        if sub.is_dir():
            try:
                results.append(ingest_note_folder(sub, force=force, vectorstore=vectorstore))
            except Exception as e:
                results.append({"note_id": sub.name, "status": "error", "error": str(e)})
    return results


def ingest_sample_notes(vectorstore: TravelNoteVectorStore | None = None) -> int:
    """
    P0：将 data/sample_notes/*.json 假数据入库（无需 Vision）。
    返回写入 chunk 总数。
    """
    vs = vectorstore or get_vectorstore()
    SAMPLE_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for json_file in sorted(SAMPLE_NOTES_DIR.glob("*.json")):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        note = TravelNote(
            note_id=data.get("note_id", json_file.stem),
            source=data.get("source", "sample"),
            city=data.get("city", ""),
            days=data.get("days"),
            title=data.get("title", ""),
            spots=list(data.get("spots") or []),
            food=list(data.get("food") or []),
            route_summary=data.get("route_summary", ""),
            budget=data.get("budget", ""),
            tips=list(data.get("tips") or []),
            raw_summary=data.get("raw_summary", ""),
        )
        if vs.note_exists(note.note_id):
            continue
        docs = chunk_note(note)
        total += vs.add_documents_raw(docs)
    return total
