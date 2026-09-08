"""
HS Code MCP Server — 海关商品归类智能体工具
基于2026年进出口税则，提供商品搜索、编码详情、税费计算等能力。

数据来源：财政部《2026年进出口税则》官方PDF
品目覆盖：1228个品目（100%），8972条税则条目

用法：
    pip install mcp
    python server.py
"""

import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ─── 数据加载 ───────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"

with open(DATA_DIR / "hs_codes_full.json", "r", encoding="utf-8") as f:
    HS_CODES: list[dict] = json.load(f)

with open(DATA_DIR / "hs4_descriptions.json", "r", encoding="utf-8") as f:
    HS4_DESCRIPTIONS: dict[str, str] = json.load(f)

# 建立索引
HS_CODE_INDEX: dict[str, dict] = {item["hs_code"]: item for item in HS_CODES}
CATEGORIES: list[str] = sorted({item["category"] for item in HS_CODES})

# ─── 同义词词典（含HS编码前缀直匹配） ──────────────────────

SYNONYMS: dict[str, list[str]] = {
    "口红": ["3304.1000", "唇用化妆品", "唇膏"],
    "手机": ["8517.1300", "智能手机", "移动电话"],
    "蓝牙耳机": ["8518.3000", "无线耳机", "耳机"],
    "笔记本电脑": ["8471.3090", "便携式电脑", "laptop"],
    "平板电脑": ["8471.3010", "平板", "ipad"],
    "充电宝": ["8507.6000", "移动电源", "power bank"],
    "纯棉t恤": ["6109.1000", "棉制T恤", "T恤衫"],
    "红酒": ["2204", "葡萄酒", "红葡萄酒"],
    "啤酒": ["2203", "麦芽酿造啤酒"],
    "水杯": ["3924.1000", "塑料杯", "杯子"],
    "咖啡": ["0901", "未浸除咖啡碱", "已浸除咖啡碱"],
    "茶叶": ["0902", "绿茶", "红茶"],
    "奶粉": ["0402", "乳粉", "浓缩乳"],
    "巧克力": ["1806", "可可制品"],
    "运动鞋": ["6404", "鞋靴", "运动鞋"],
    "背包": ["4202", "箱包", "书包"],
    "手表": ["9102", "腕表"],
    "相机": ["8525", "照相机", "摄像机"],
}


def _normalize(text: str) -> str:
    """归一化文本：小写、去空格、去标点"""
    return re.sub(r"[\s\W_]+", "", text.lower())


def _similarity(a: str, b: str) -> float:
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _get_hs4(code: str) -> str:
    """从8位HS编码提取4位品目"""
    return code.replace(".", "")[:4]


def _enrich_name(item: dict) -> str:
    """给简短名称补上品目描述"""
    name = item.get("name", "")
    hs4 = _get_hs4(item["hs_code"])
    desc = HS4_DESCRIPTIONS.get(hs4, "")
    # 如果名称太短（≤4字）且品目描述存在，拼接
    if len(name) <= 6 and desc and desc not in name:
        return f"{desc} - {name}"
    return name


def fuzzy_search(query: str, top_n: int = 5) -> list[dict]:
    """
    模糊搜索HS编码。
    评分规则：
    1. HS编码8位精确匹配：+300分（同义词中指定的精确编码）
    2. HS编码4位品目匹配：+100分（同义词中指定的品目）
    3. 品目描述包含查询词：+100分
    4. 商品名称相似度：0-100分
    5. 类别包含查询词：+30分
    6. 查询词是名称子串：+50分
    """
    query_norm = _normalize(query)
    results = []

    # 检查同义词中的HS编码匹配
    exact_codes = set()   # 8位精确匹配，如 8471.3090
    prefix_codes = set()  # 4位品目匹配，如 8471
    for key, values in SYNONYMS.items():
        if _normalize(key) in query_norm or query_norm in _normalize(key):
            for v in values:
                if re.match(r"^\d{4}\.\d{4}", v):
                    exact_codes.add(v)  # 8位精确编码
                elif re.match(r"^\d{4}", v):
                    prefix_codes.add(v.replace(".", "")[:4])

    for item in HS_CODES:
        score = 0.0
        hs4 = _get_hs4(item["hs_code"])
        enriched = _enrich_name(item)
        enriched_norm = _normalize(enriched)

        # 1. HS编码8位精确匹配（最高权重，+300分）
        if item["hs_code"] in exact_codes:
            score += 300

        # 2. HS编码4位品目匹配（+100分）
        if hs4 in prefix_codes:
            score += 100

        # 2. 品目描述包含查询词
        hs4_desc = HS4_DESCRIPTIONS.get(hs4, "")
        if query_norm in _normalize(hs4_desc):
            score += 100

        # 3. 商品名称相似度
        name_sim = _similarity(query, enriched)
        score += name_sim * 100

        # 4. 类别包含查询词
        if query_norm in _normalize(item.get("category", "")):
            score += 30

        # 5. 查询词是名称的子串
        if query_norm in enriched_norm:
            score += 50

        if score > 0:
            results.append({
                "hs_code": item["hs_code"],
                "name": enriched,
                "import_tariff": item["import_tariff"],
                "vat_rate": item["vat_rate"],
                "consumption_tax": item.get("consumption_tax", 0),
                "category": item["category"],
                "basis": item.get("basis", ""),
                "score": round(score, 2),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# ─── MCP Server ─────────────────────────────────────────────

mcp = FastMCP(
    "hs-code-mcp-server",
    instructions="海关商品归类工具。基于2026年进出口税则，支持商品模糊搜索、HS编码详情查询、进口税费计算和商品分类浏览。所有数据仅供参考，最终以海关官方裁定为准。",
)


@mcp.tool()
def search_hs_code(
    product_name: str,
    top_n: int = 5,
) -> str:
    """
    根据商品名称模糊搜索HS编码，返回最匹配的候选列表。

    Args:
        product_name: 商品名称，如"口红"、"笔记本电脑"、"纯棉T恤"
        top_n: 返回结果数量，默认5个，最多20个

    Returns:
        JSON格式的候选列表，每个结果包含HS编码、商品名称、进口关税、增值税、消费税、类别、来源页码和匹配分数
    """
    top_n = max(1, min(top_n, 20))
    results = fuzzy_search(product_name, top_n)

    if not results:
        return json.dumps({
            "status": "not_found",
            "message": f"未找到与'{product_name}'匹配的商品。请尝试更通用的商品名称，或使用get_categories查看完整分类。",
            "query": product_name,
        }, ensure_ascii=False, indent=2)

    return json.dumps({
        "status": "ok",
        "query": product_name,
        "count": len(results),
        "disclaimer": "数据基于2026年进出口税则，仅供参考，最终以海关官方裁定为准。",
        "results": results,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_hs_detail(hs_code: str) -> str:
    """
    根据HS编码查询详细信息。

    Args:
        hs_code: HS编码，支持格式"8471.3090"或"84713090"

    Returns:
        JSON格式的详细信息，包含商品名称、进口关税、增值税、消费税、监管条件、类别、品目描述和来源
    """
    # 标准化编码格式
    code = hs_code.strip()
    if "." not in code and len(code) == 8:
        code = f"{code[:4]}.{code[4:]}"

    item = HS_CODE_INDEX.get(code)
    if not item:
        # 尝试前缀匹配
        prefix = code.replace(".", "")[:4]
        matches = [
            {k: v for k, v in it.items() if k != "description"}
            for it in HS_CODES
            if _get_hs4(it["hs_code"]) == prefix
        ]
        if matches:
            return json.dumps({
                "status": "partial_match",
                "message": f"未找到精确编码{hs_code}，以下是同品目{prefix}下的所有子目：",
                "hs4_description": HS4_DESCRIPTIONS.get(prefix, ""),
                "count": len(matches),
                "results": matches[:20],
            }, ensure_ascii=False, indent=2)

        return json.dumps({
            "status": "not_found",
            "message": f"未找到HS编码{hs_code}。请检查编码是否正确。",
        }, ensure_ascii=False, indent=2)

    hs4 = _get_hs4(item["hs_code"])
    return json.dumps({
        "status": "ok",
        "hs_code": item["hs_code"],
        "name": _enrich_name(item),
        "hs4_description": HS4_DESCRIPTIONS.get(hs4, ""),
        "import_tariff": item["import_tariff"],
        "vat_rate": item["vat_rate"],
        "consumption_tax": item.get("consumption_tax", 0),
        "supervision": item.get("supervision", ""),
        "category": item["category"],
        "basis": item.get("basis", ""),
        "disclaimer": "数据基于2026年进出口税则，仅供参考，最终以海关官方裁定为准。",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def calculate_import_tax(
    hs_code: str,
    cif_price: float,
    quantity: float = 1.0,
    origin: str = "默认税率",
) -> str:
    """
    计算进口税费（关税+增值税+消费税）。

    Args:
        hs_code: HS编码，如"8471.3090"
        cif_price: CIF完税价格（人民币元），即货值+运费+保险费
        quantity: 数量，默认1
        origin: 原产地，用于判断协定税率，默认使用最惠国税率

    Returns:
        JSON格式的税费计算明细，包含完税价格、关税、消费税、增值税和总税费
    """
    code = hs_code.strip()
    if "." not in code and len(code) == 8:
        code = f"{code[:4]}.{code[4:]}"

    item = HS_CODE_INDEX.get(code)
    if not item:
        return json.dumps({
            "status": "error",
            "message": f"未找到HS编码{hs_code}，无法计算税费。",
        }, ensure_ascii=False, indent=2)

    total_cif = cif_price * quantity
    tariff_rate = item["import_tariff"] / 100.0  # 转为小数
    vat_rate = item["vat_rate"] / 100.0
    consumption_rate = item.get("consumption_tax", 0) / 100.0

    # 关税 = CIF × 关税税率
    tariff = total_cif * tariff_rate

    # 消费税 = (CIF + 关税) / (1 - 消费税税率) × 消费税税率
    if consumption_rate > 0:
        consumption = (total_cif + tariff) / (1 - consumption_rate) * consumption_rate
    else:
        consumption = 0

    # 增值税 = (CIF + 关税 + 消费税) × 增值税税率
    vat = (total_cif + tariff + consumption) * vat_rate

    total_tax = tariff + consumption + vat

    return json.dumps({
        "status": "ok",
        "hs_code": code,
        "product_name": _enrich_name(item),
        "cif_price_per_unit": cif_price,
        "quantity": quantity,
        "total_cif": round(total_cif, 2),
        "tariff_rate": item["import_tariff"],
        "tariff": round(tariff, 2),
        "consumption_tax_rate": item.get("consumption_tax", 0),
        "consumption_tax": round(consumption, 2),
        "vat_rate": item["vat_rate"],
        "vat": round(vat, 2),
        "total_tax": round(total_tax, 2),
        "tax_rate_overall": round(total_tax / total_cif * 100, 2) if total_cif > 0 else 0,
        "origin": origin,
        "note": "计算基于最惠国税率，未考虑协定税率/特惠税率/反倾销税等特殊情况。实际税费以海关核定为准。",
        "disclaimer": "仅供参考，不构成法律意见，最终以海关官方裁定为准。",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_categories() -> str:
    """
    获取所有商品分类（类/章）列表。

    Returns:
        JSON格式的分类列表，包含22个类
    """
    return json.dumps({
        "status": "ok",
        "count": len(CATEGORIES),
        "categories": CATEGORIES,
        "disclaimer": "数据基于2026年进出口税则。",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_stats() -> str:
    """
    获取数据库统计信息。

    Returns:
        JSON格式的统计信息，包含税则条目数、品目数、分类数等
    """
    return json.dumps({
        "status": "ok",
        "total_items": len(HS_CODES),
        "total_hs4_descriptions": len(HS4_DESCRIPTIONS),
        "total_categories": len(CATEGORIES),
        "data_source": "财政部《2026年进出口税则》官方PDF",
        "coverage": "1228个品目，100%覆盖",
        "disclaimer": "数据基于2026年进出口税则，仅供参考。",
    }, ensure_ascii=False, indent=2)


# ─── 启动 ───────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
