"""
多源统一抓取调度器

依次调用各平台爬虫，汇总结果后写入飞书。

支持的数据源:
    - CBNData: 消费行业报告、品牌分析
    - 艾媒网: 研究报告、品牌排行榜
    - 洞见研报: 券商研报、行业分析
    - 发现报告: 592万+研报聚合平台
"""

import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.cbndata import CBNDataCrawler
from crawlers.iimedia import IIMediaCrawler
from crawlers.djyanbao import DJYanbaoCrawler
from crawlers.fxbaogao import FxBaoGaoCrawler


async def crawl_all_sources(brands: list, max_per_source: int = 10) -> dict:
    """
    从所有数据源搜索品牌相关信息。

    返回格式:
    {
        "花西子": [
            {"source": "CBNData", "title": "...", "url": "..."},
            {"source": "艾媒网", "title": "...", "url": "..."},
            ...
        ],
        ...
    }
    """
    all_results = {}

    # 初始化爬虫
    crawlers = [
        CBNDataCrawler(),
        IIMediaCrawler(),
        DJYanbaoCrawler(),
        FxBaoGaoCrawler(),
    ]

    for brand in brands:
        name = brand.get("name", "")
        if not name:
            continue

        brand_results = []
        print(f"\n[{name}] === 开始多源搜索 ===")

        for crawler in crawlers:
            try:
                print(f"  [{crawler.name}] 搜索 '{name}'...")
                articles = await crawler.search(name, max_results=max_per_source)
                brand_results.extend(articles)
            except Exception as exc:
                print(f"  [{crawler.name}] 搜索失败: {exc}")

        all_results[name] = brand_results
        print(f"[{name}] 汇总: 共 {len(brand_results)} 条结果")
        await asyncio.sleep(2)

    return all_results


async def crawl_topic_keywords(keywords: list, max_results: int = 15) -> list:
    """
    按行业关键词搜索（非品牌，泛主题分析）。

    返回格式与 crawl_all_sources 相同，但 keyword 字段为行业关键词。
    """
    results = []
    crawlers = [
        CBNDataCrawler(),
        IIMediaCrawler(),
        DJYanbaoCrawler(),
        FxBaoGaoCrawler(),
    ]

    for kw in keywords:
        print(f"\n[主题] === 搜索 '{kw}' ===")
        for crawler in crawlers:
            try:
                articles = await crawler.search(kw, max_results=max_results)
                for a in articles:
                    a["keyword"] = kw
                results.extend(articles)
                print(f"  [{crawler.name}] '{kw}': {len(articles)} 条")
            except Exception as exc:
                print(f"  [{crawler.name}] 搜索 '{kw}' 失败: {exc}")
        await asyncio.sleep(2)

    return results


# ── 命令行 ────────────────────────────────────────────
if __name__ == "__main__":
    test_kw = sys.argv[1] if len(sys.argv) > 1 else "美妆"
    results = asyncio.run(crawl_all_sources([{"name": test_kw}], max_per_source=5))
    for k, v in results.items():
        print(f"\n{k}: {len(v)} 条")
        for item in v:
            print(f"  [{item['source']}] {item['title']}")
