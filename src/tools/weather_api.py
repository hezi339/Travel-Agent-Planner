"""
天气 API 模块（Open-Meteo 免费接口）
职责：查询指定城市、日期的天气预报。
依赖高德地理编码把城市转成经纬度。
"""

from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.tools.amap_api import get_lat_lon

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# WMO Weather interpretation codes（官方表）→ 中文
# 之前缺 80–82、95–99，会把雷雨错误默认成「多云」
WEATHER_DESC_MAP = {
    0: "晴天",
    1: "晴间多云",
    2: "多云",
    3: "阴天",
    45: "雾",
    48: "雾凇",
    51: "小雨（毛毛雨）",
    53: "中雨（毛毛雨）",
    55: "大雨（毛毛雨）",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "强阵雪",
    95: "雷阵雨",
    96: "雷阵雨伴有冰雹",
    99: "强雷阵雨伴有冰雹",
}


def _code_to_desc(code: int) -> str:
    """未知代码不再默认「多云」，避免把雨天标成多云。"""
    return WEATHER_DESC_MAP.get(code, f"未知天气(代码{code})")


def _normalize_date(date_str: str) -> str:
    """把「今天」等自然语言转成 YYYY-MM-DD。"""
    date_str = str(date_str).strip().strip("'\"").rstrip(",")

    if date_str in ("今天", "今日", "当天", "today", "Today"):
        return date.today().isoformat()

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue

    parts = date_str.replace("/", "-").split("-")
    if len(parts) == 3:
        try:
            return date(int(parts[0]), int(parts[1]), int(parts[2])).isoformat()
        except ValueError:
            pass

    raise ValueError(
        f"无法解析日期「{date_str}」，请使用 YYYY-MM-DD，例如 {date.today().isoformat()}"
    )


@lru_cache(maxsize=64)
def get_weather(city: str, date_str: str) -> str:
    """
    查询指定城市某天天气。
    - 「今天」：优先用实时天气（current），更接近手机天气 App
    - 其他日期：用每日预报 + 降水提示
    """
    city = str(city).strip().strip("'\"").rstrip(",")
    day = _normalize_date(date_str)
    lon, lat = get_lat_lon(city)

    # 今天：实时天气更准
    if day == date.today().isoformat():
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code,precipitation"
            f"&daily=weather_code,temperature_2m_max,precipitation_sum"
            f"&start_date={day}&end_date={day}&timezone=auto"
        )
        data = requests.get(url, timeout=10).json()
        if "current" not in data:
            raise ValueError(f"Open-Meteo 实时天气失败：{data}")

        cur = data["current"]
        code = int(cur["weather_code"])
        temp = int(cur["temperature_2m"])
        desc = _code_to_desc(code)

        # 附加今日预报最高温与降水量，方便穿搭/带伞建议
        tip = ""
        daily = data.get("daily") or {}
        if daily.get("precipitation_sum"):
            rain = daily["precipitation_sum"][0]
            tmax = int(daily["temperature_2m_max"][0])
            day_code = int(daily["weather_code"][0])
            tip = (
                f"；今日预报：{_code_to_desc(day_code)}，"
                f"最高{tmax}°C，降水{rain}mm"
            )
        return f"{desc}，{temp}°C{tip}"

    # 未来某天：日预报
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=weather_code,temperature_2m_max,precipitation_sum"
        f"&start_date={day}&end_date={day}&timezone=auto"
    )
    data = requests.get(url, timeout=10).json()
    if "daily" not in data:
        reason = data.get("reason") or data.get("error") or str(data)
        raise ValueError(f"Open-Meteo 查询失败（城市={city}, 日期={day}）：{reason}")

    daily = data["daily"]
    code = int(daily["weather_code"][0])
    temp = int(daily["temperature_2m_max"][0])
    rain = daily.get("precipitation_sum", [0])[0]
    desc = _code_to_desc(code)
    return f"{desc}，最高{temp}°C，降水{rain}mm"
