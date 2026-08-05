"""
多源品牌情报抓取主程序 — daily_crawl.py

数据来源:
    1. CBNData — 消费行业报告、品牌分析
    2. 艾媒网 — 研究报告、品牌排行榜
    3. 洞见研报 — 券商研报、行业分析

流程:
    1. 启动 VPN（本地桌面环境，CI 自动跳过）
    2. 按品牌关键词搜索各平台
    3. 按行业热点关键词搜索
    4. 汇总写入飞书多维表格
    5. 关闭 VPN
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from feishu.bitable import (
    load_feishu_config,
    get_tenant_access_token,
    write_multi_source_data,
)
from crawlers.unified import crawl_all_sources, crawl_topic_keywords
from utils.vpn import start_vpn, stop_vpn


def load_brand_config() -> list:
    """加载品牌配置。"""
    config_path = os.path.join(PROJECT_ROOT, "brand_config.json")
    if not os.path.exists(config_path):
        print(f"品牌配置文件不存在: {config_path}")
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    brands = config.get("brands", [])
    print(f"加载品牌配置: {len(brands)} 个品牌")
    for b in brands:
        print(f"  - {b['name']} ({b['industry']})")
    return brands


def load_sources_config() -> dict:
    """加载数据源配置。"""
    config_path = os.path.join(PROJECT_ROOT, "sources_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


async def run_daily_crawl():
    """每日多源情报抓取主流程。"""
    start_time = datetime.now()
    print("=" * 50)
    print(f"多源品牌情报抓取开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 0. 启动 VPN
    print(f"\n[VPN] 准备启动 Sakurucat...")
    vpn_ok = start_vpn()
    if not vpn_ok:
        print("警告: VPN 启动失败，继续尝试抓取...")

    # 1. 加载配置
    brands = load_brand_config()
    if not brands:
        print("错误: 品牌配置为空，退出。")
        return

    sources_cfg = load_sources_config()
    topic_keywords = sources_cfg.get("brand_keywords", [])

    feishu_cfg = load_feishu_config()
    if not feishu_cfg.get("app_id") or not feishu_cfg.get("app_secret"):
        print("错误: 飞书应用配置不完整，退出。")
        return

    # 2. 飞书 Token
    print(f"\n[飞书] 获取访问令牌...")
    try:
        token = get_tenant_access_token(feishu_cfg["app_id"], feishu_cfg["app_secret"])
        print(f"[飞书] 令牌获取成功: {token[:16]}...")
    except Exception as exc:
        print(f"[飞书] 令牌获取失败: {exc}")
        return

    # 3. 按品牌抓取
    print(f"\n[抓取] === 按品牌搜索（{len(brands)} 个）===")
    try:
        brand_results = await crawl_all_sources(brands, max_per_source=5)
        brand_total = sum(len(v) for v in brand_results.values())
        print(f"[品牌抓取] 完成: {len(brands)} 个品牌，共 {brand_total} 条结果")
    except Exception as exc:
        print(f"[品牌抓取] 出错: {exc}")
        brand_results = {}

    # 4. 按热点关键词抓取
    print(f"\n[抓取] === 按行业热点搜索（{len(topic_keywords)} 个）===")
    try:
        topic_results = await crawl_topic_keywords(topic_keywords, max_results=5)
        print(f"[热点抓取] 完成: {len(topic_results)} 条结果")
    except Exception as exc:
        print(f"[热点抓取] 出错: {exc}")
        topic_results = []

    # 5. 汇总写入飞书
    all_articles = []
    for brand_name, articles in brand_results.items():
        for a in articles:
            all_articles.append(a)
    all_articles.extend(topic_results)

    print(f"\n[飞书] 准备写入 {len(all_articles)} 条情报...")
    try:
        written = write_multi_source_data(
            articles=all_articles,
            app_token=feishu_cfg["app_token"],
            table_id=feishu_cfg["table_id"],
            token=token,
        )
    except Exception as exc:
        print(f"[飞书] 写入失败: {exc}")
        written = 0

    # 6. 关闭 VPN
    print(f"\n[VPN] 抓取完成，关闭 Sakurucat...")
    stop_vpn()

    # 7. 汇总
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'=' * 50}")
    print(f"多源情报抓取完成!")
    print(f"  品牌数: {len(brands)}")
    print(f"  品牌结果: {brand_total}")
    print(f"  热点结果: {len(topic_results)}")
    print(f"  总计: {len(all_articles)} 条")
    print(f"  写入飞书: {written} 条")
    print(f"  耗时: {elapsed:.1f} 秒")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    asyncio.run(run_daily_crawl())
