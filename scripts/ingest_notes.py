#!/usr/bin/env python
"""
P1：截图笔记入库脚本。
用法：
    python scripts/ingest_notes.py                          # 扫描 data/screenshots/*/
    python scripts/ingest_notes.py --folder data/screenshots/xhs_guangzhou_001
    python scripts/ingest_notes.py --force                  # 强制覆盖已存在笔记
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.rag.config import SCREENSHOTS_DIR
from src.rag.ingest_pipeline import ingest_all_screenshots, ingest_note_folder
from src.rag.vectorstore import get_vectorstore


def main():
    parser = argparse.ArgumentParser(description="旅行笔记截图入库")
    parser.add_argument("--folder", help="指定单个笔记文件夹")
    parser.add_argument("--note-id", help="自定义 note_id")
    parser.add_argument("--force", action="store_true", help="覆盖已存在笔记")
    args = parser.parse_args()

    if args.folder:
        result = ingest_note_folder(args.folder, note_id=args.note_id, force=args.force)
        print(result)
    else:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        results = ingest_all_screenshots(force=args.force)
        for r in results:
            print(r)

    vs = get_vectorstore()
    print(f"📦 向量库总量：{vs.count()}")


if __name__ == "__main__":
    main()
