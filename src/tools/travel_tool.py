"""
旅行业务工具模块
职责：纯本地逻辑，不调用外部 API——根据天气与活动类型推荐穿搭、生成行李分类清单。
"""


def recommend_clothing(weather: str, activity: str) -> str:
    """
    根据天气字符串（如「晴天，25°C」）和活动类型推荐穿搭。
    activity 常见值：徒步 / 海滨度假 / 城市游览
    """
    # 从天气描述中解析温度数字
    temp_str = weather.split("°C")[0].split("，")[1]
    temp = int(temp_str)

    # 按温度区间选择基础衣物
    if temp < 15:
        base = "保暖内衣、厚外套"
    elif temp < 20:
        base = "长袖衬衫、薄外套"
    elif temp < 28:
        base = "短袖T恤、长裤"
    else:
        base = "短袖T恤、短裤"

    # 按活动类型追加专用装备
    if activity == "徒步":
        return f"{base}、徒步鞋、登山杖、防晒帽"
    elif activity == "海滨度假":
        return f"{base}、泳衣、沙滩裤、太阳镜、防晒霜"
    elif activity == "城市游览":
        return f"{base}、舒适运动鞋、休闲包、雨伞"
    else:
        return f"{base}、适合{activity}的舒适服装"


def checklist_categories(days: int) -> str:
    """
    根据出行天数生成行李分类清单（类别名称，非具体物品）。
    天数越多，补充的类别越多。
    """
    categories = ["证件", "衣物", "药品", "电子产品", "洗漱用品"]
    if days > 5:
        categories.extend(["换洗衣物", "便携衣架", "洗衣液旅行装"])
    if days > 1:
        categories.extend(["充电器", "充电宝"])
    if days > 3:
        categories.extend(["旅行保险", "地图"])
    return ", ".join(categories)
