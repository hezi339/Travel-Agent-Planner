"""
高德地图 API 模块
职责：地理编码（城市 → 经纬度）、景点搜索。
"""

import os
from functools import lru_cache
from pathlib import Path

import requests
from dotenv import load_dotenv

# 始终从项目根目录加载 .env，避免从其他目录启动时读不到 GAODE_KEY
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_gaode_key() -> str:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    key = (os.getenv("GAODE_KEY") or "").strip()
    if not key:
        raise ValueError("未配置 GAODE_KEY，请在 .env 中填写高德 Web 服务 Key")
    return key


@lru_cache(maxsize=64)
def get_lat_lon(city: str) -> tuple[str, str]:
    """
    将城市名转换为 (经度, 纬度)。
    使用 lru_cache 缓存结果，同一城市重复查询时不重复请求 API。
    """
    gaode_key = _get_gaode_key()

    # 去掉 LLM 可能传入的多余引号或空格
    city = city.strip().strip('"').strip("'").rstrip(",")

    url = f"https://restapi.amap.com/v3/geocode/geo?address={city}&key={gaode_key}"
    resp = requests.get(url, timeout=5)
    data = resp.json()
    if data.get("status") == "1" and data.get("geocodes"):
        # 高德返回格式为 "经度,纬度"
        loc = data["geocodes"][0]["location"]
        return tuple(loc.split(","))
    info = data.get("info") or data.get("infocode") or "未知错误"
    raise ValueError(f"无法解析城市「{city}」：{info}")


def get_attractions(city: str, keyword: str = "景点") -> list[dict]:
    """
    搜索城市内景点，默认返回前 5 个 POI。
    当前未注册到 Agent 工具表，可作为后续扩展（如行程推荐）使用。
    """
    gaode_key = _get_gaode_key()
    city = city.strip().strip('"').strip("'").rstrip(",")
    url = (
        f"https://restapi.amap.com/v3/place/text?"
        f"keywords={keyword}&city={city}&output=json&offset=5&key={gaode_key}"
    )
    resp = requests.get(url, timeout=5)
    pois = resp.json().get("pois", [])
    return [{"name": p["name"], "address": p["address"]} for p in pois]
