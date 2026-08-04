"""
每日抓取主程序 — daily_crawl.py

流程:
1. 读取 brand_config.json 品牌配置
2. 对每个品牌调用 xhs_crawler 搜索抓取
3. 将结果写入飞书多维表格

运行方式:
    python3 feishu/daily_crawl.py

环境变量（GitHub Actions）:
    FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_APP_TOKEN / FEISHU_TABLE_ID
    XHS_COOKIE（选填，用于登录态）
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from feishu.bitable import (
    load_feishu_config,
    get_tenant_access_token,
    write_brand_data,
)
from xhs_crawler import crawl_all_brands


def load_brand_config() -> list:
    """加载品牌配置文件。"""
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


async def run_daily_crawl():
    """每日抓取主流程。"""
    start_time = datetime.now()
    print(f"=" * 50)
    print(f"小红书每日抓取开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 50)

    # 1. 加载品牌配置
    brands = load_brand_config()
    if not brands:
        print("错误: 品牌配置为空，退出。")
        return

    # 2. 加载飞书配置并获取 Token
    feishu_cfg = load_feishu_config()
    if not feishu_cfg.get("app_id") or not feishu_cfg.get("app_secret"):
        print("错误: 飞书应用配置不完整，退出。")
        return

    print(f"\n[飞书] 获取访问令牌...")
    try:
        token = get_tenant_access_token(feishu_cfg["app_id"], feishu_cfg["app_secret"])
        print(f"[飞书] 令牌获取成功: {token[:16]}...")
    except Exception as exc:
        print(f"[飞书] 令牌获取失败: {exc}")
        return

    # 3. 批量抓取
    print(f"\n[抓取] 开始抓取 {len(brands)} 个品牌...")
    try:
        brand_results = await crawl_all_brands(brands, max_per_brand=20)
        total_posts = sum(len(v) for v in brand_results.values())
        print(f"[抓取] 完成: 共获取 {total_posts} 条笔记")
    except Exception as exc:
        print(f"[抓取] 抓取过程出错: {exc}")
        return

    # 4. 写入飞书
    print(f"\n[飞书] 开始写入多维表格...")
    try:
        written = write_brand_data(
            brand_results=brand_results,
            brands=brands,
            app_token=feishu_cfg["app_token"],
            table_id=feishu_cfg["table_id"],
            token=token,
        )
    except Exception as exc:
        print(f"[飞书] 写入失败: {exc}")
        written = 0

    # 5. 汇总
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'=' * 50}")
    print(f"抓取完成!")
    print(f"  品牌数: {len(brands)}")
    print(f"  笔记数: {total_posts}")
    print(f"  写入飞书: {written} 条")
    print(f"  耗时: {elapsed:.1f} 秒")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    asyncio.run(run_daily_crawl())
