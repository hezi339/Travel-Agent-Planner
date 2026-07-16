"""
Vision 解析模块（路线 A）
职责：将小红书/抖音截图通过智谱 Vision 模型解析为结构化笔记。
"""

import base64
import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.rag.config import PROJECT_ROOT, ZHIPU_VISION_MODEL
from src.rag.schemas import TravelNote
from dotenv import load_dotenv
import os

load_dotenv(PROJECT_ROOT / ".env", override=True)

VISION_PROMPT = """请解析这张旅行攻略截图，只根据图片可见信息提取，不要编造。
必须输出合法 JSON，不要 Markdown 代码块外的文字：

{
  "source": "xiaohongshu 或 douyin 或 unknown",
  "city": "城市",
  "days": 数字或 null,
  "title": "笔记标题或主题",
  "spots": ["景点1", "景点2"],
  "food": ["美食1"],
  "route_summary": "路线概要，尽量按 Day1/Day2",
  "budget": "预算或 null",
  "tips": ["避雷/小贴士"],
  "raw_summary": "200字以内纯文本摘要，用于检索"
}"""


def _get_vision_llm() -> ChatOpenAI:
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise ValueError("未配置 ZHIPU_API_KEY，无法调用 Vision 模型")
    return ChatOpenAI(
        model=ZHIPU_VISION_MODEL,
        temperature=0,
        openai_api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/",
    )


def _image_to_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix or "png"
    b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:image/{mime};base64,{b64}"


def _extract_json(text: str) -> dict:
    """从模型输出中提取 JSON。"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def parse_image(image_path: str | Path, note_id: str) -> TravelNote:
    """解析单张截图。"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"截图不存在：{path}")

    llm = _get_vision_llm()
    data_url = _image_to_data_url(path)
    msg = HumanMessage(
        content=[
            {"type": "text", "text": VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    )
    resp = llm.invoke([msg])
    parsed = _extract_json(resp.content)

    return TravelNote(
        note_id=note_id,
        source=str(parsed.get("source") or "unknown"),
        city=str(parsed.get("city") or ""),
        days=parsed.get("days"),
        title=str(parsed.get("title") or path.stem),
        spots=list(parsed.get("spots") or []),
        food=list(parsed.get("food") or []),
        route_summary=str(parsed.get("route_summary") or ""),
        budget=str(parsed.get("budget") or "") if parsed.get("budget") else "",
        tips=list(parsed.get("tips") or []),
        raw_summary=str(parsed.get("raw_summary") or ""),
    )


def merge_notes(notes: list[TravelNote], note_id: str) -> TravelNote:
    """合并同一笔记的多张截图解析结果。"""
    if not notes:
        raise ValueError("无笔记可合并")
    if len(notes) == 1:
        return notes[0]

    merged_spots: list[str] = []
    merged_food: list[str] = []
    merged_tips: list[str] = []
    routes: list[str] = []
    summaries: list[str] = []

    city = next((n.city for n in notes if n.city), "")
    source = next((n.source for n in notes if n.source != "unknown"), "unknown")
    title = next((n.title for n in notes if n.title), note_id)
    days = next((n.days for n in notes if n.days), None)
    budget = next((n.budget for n in notes if n.budget), "")

    for n in notes:
        for lst, src in [
            (merged_spots, n.spots),
            (merged_food, n.food),
            (merged_tips, n.tips),
        ]:
            for item in src:
                if item and item not in lst:
                    lst.append(item)
        if n.route_summary:
            routes.append(n.route_summary)
        if n.raw_summary:
            summaries.append(n.raw_summary)

    return TravelNote(
        note_id=note_id,
        source=source,
        city=city,
        days=days,
        title=title,
        spots=merged_spots,
        food=merged_food,
        route_summary="\n".join(routes),
        budget=budget,
        tips=merged_tips,
        raw_summary=" ".join(summaries)[:500],
    )
