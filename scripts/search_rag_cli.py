#!/usr/bin/env python
"""
P0：CLI 检索测试。
用法：
    python scripts/search_rag_cli.py "广州 3天 城市观光"
    python scripts/search_rag_cli.py "成都 美食" --city 成都
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.tools.note_search_tool import search_travel_notes


def main():
    parser = argparse.ArgumentParser(description="Chroma 笔记检索 CLI")
    parser.add_argument("query", help="检索关键词")
    parser.add_argument("--city", default="", help="可选城市过滤")
    args = parser.parse_args()
    print(search_travel_notes(args.query, args.city))


if __name__ == "__main__":
    main()
