#!/usr/bin/env python
"""
P0：导入假数据样本到 Chroma，并打印库内文档数量。
用法（在项目根目录）：
    python scripts/seed_rag.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.rag.ingest_pipeline import ingest_sample_notes
from src.rag.vectorstore import get_vectorstore


def main():
    n = ingest_sample_notes()
    vs = get_vectorstore()
    print(f"[OK] 假数据入库完成，本次新增 chunk：{n}")
    print(f"[INFO] 向量库总量：{vs.count()}")


if __name__ == "__main__":
    main()
