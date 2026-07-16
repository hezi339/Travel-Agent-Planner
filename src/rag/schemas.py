"""
笔记数据结构
职责：定义 Vision 解析与入库时的统一字段。
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TravelNote:
    """一篇旅行笔记（可能来自多图合并）。"""

    note_id: str
    source: str = "unknown"  # xiaohongshu / douyin / sample
    city: str = ""
    days: int | None = None
    title: str = ""
    spots: list[str] = field(default_factory=list)
    food: list[str] = field(default_factory=list)
    route_summary: str = ""
    budget: str = ""
    tips: list[str] = field(default_factory=list)
    raw_summary: str = ""  # 用于向量检索的主文本

    def to_document_text(self) -> str:
        """合并为适合 Embedding 的纯文本。"""
        parts = [
            f"标题：{self.title}" if self.title else "",
            f"城市：{self.city}" if self.city else "",
            f"天数：{self.days}" if self.days else "",
            f"路线：{self.route_summary}" if self.route_summary else "",
            f"景点：{', '.join(self.spots)}" if self.spots else "",
            f"美食：{', '.join(self.food)}" if self.food else "",
            f"预算：{self.budget}" if self.budget else "",
            f"贴士：{'; '.join(self.tips)}" if self.tips else "",
            f"摘要：{self.raw_summary}" if self.raw_summary else "",
        ]
        return "\n".join(p for p in parts if p)

    def to_metadata(self) -> dict[str, Any]:
        """Chroma metadata（值须为 str/int/float/bool）。"""
        return {
            "note_id": self.note_id,
            "source": self.source,
            "city": self.city or "未知",
            "days": int(self.days) if self.days else 0,
            "title": self.title or "",
        }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d
