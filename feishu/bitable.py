"""
飞书多维表格 (Bitable) API 写入模块

功能：
- 获取 tenant_access_token
- 批量写入记录到指定多维表格
- 字段映射（品牌名、笔记标题、链接、互动数据等）
"""

import json
import os
import sys
import time
from typing import Optional

import requests

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 配置加载 ──────────────────────────────────────────
def load_feishu_config() -> dict:
    """从 feishu_config.json 读取飞书配置，同时支持环境变量覆盖。"""
    config_path = "feishu_config.json"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    # 环境变量优先（用于 GitHub Actions secrets）
    config["app_id"] = os.getenv("FEISHU_APP_ID", config.get("app_id", ""))
    config["app_secret"] = os.getenv("FEISHU_APP_SECRET", config.get("app_secret", ""))
    config["app_token"] = os.getenv("FEISHU_APP_TOKEN", config.get("app_token", ""))
    config["table_id"] = os.getenv("FEISHU_TABLE_ID", config.get("table_id", ""))
    return config


# ── Token ─────────────────────────────────────────────
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token。"""
    resp = requests.post(
        TOKEN_URL,
        json={"app_id": app_id, "app_secret": app_secret},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    code = data.get("code")
    if code != 0:
        raise RuntimeError(f"获取 token 失败: {data.get('msg', 'unknown')}")
    return data["tenant_access_token"]


# ── 记录写入 ──────────────────────────────────────────
RECORDS_URL = (
    "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
)
MAX_BATCH = 500  # 单次批量最大条数


def build_record_fields(post: dict, brand: dict) -> dict:
    """
    将小红书笔记转换为飞书多维表格字段。

    Args:
        post:  来自 xhs_crawler 的笔记数据
        brand: 品牌配置（含 name, industry, style）

    Returns:
        飞书字段映射 dict
    """
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "品牌名称": post.get("brand", brand.get("name", "")),
        "行业": brand.get("industry", ""),
        "品牌调性": brand.get("style", ""),
        "笔记标题": post.get("title", ""),
        "笔记链接": {
            "link": post.get("url", ""),
            "text": post.get("title", "") or "查看笔记",
        },
        "笔记类型": post.get("note_type", "图文"),
        "作者": post.get("author", ""),
        "点赞数": int(post.get("likes", 0)),
        "收藏数": int(post.get("collects", 0)),
        "评论数": int(post.get("comments", 0)),
        "发布时间": post.get("publish_time", ""),
        "抓取时间": now,
        "抓取日期": now[:10],
    }


def batch_create_records(
    app_token: str,
    table_id: str,
    records: list,
    tenant_access_token: str,
) -> int:
    """
    批量写入记录到飞书多维表格。

    Args:
        app_token:  多维表格应用 token
        table_id:   数据表 ID
        records:    要写入的记录列表，每项为飞书字段 dict
        token:      tenant_access_token

    Returns:
        成功写入的记录数
    """
    if not records:
        return 0

    total_written = 0
    url = RECORDS_URL.format(app_token=app_token, table_id=table_id)
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }

    # 分批写入
    for i in range(0, len(records), MAX_BATCH):
        batch = records[i : i + MAX_BATCH]
        payload = {"records": [{"fields": r} for r in batch]}

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        code = data.get("code")
        if code != 0:
            print(f"  写入失败 (batch {i // MAX_BATCH}): {data.get('msg', 'unknown')}")
            continue

        written = len(data.get("data", {}).get("records", []))
        total_written += written
        print(f"  批次 {i // MAX_BATCH + 1}: 写入 {written} 条")

    return total_written


def write_brand_data(
    brand_results: dict,
    brands: list,
    app_token: str,
    table_id: str,
    token: str,
) -> int:
    """
    将批量抓取结果写入飞书多维表格。

    Args:
        brand_results: { "花西子": [post1, post2], ... }
        brands:        品牌配置列表
        app_token:     飞书应用 token
        table_id:      表格 ID
        token:         tenant_access_token

    Returns:
        总写入记录数
    """
    # 建立品牌名 → 配置的快速映射
    brand_map = {b["name"]: b for b in brands}

    all_records = []
    for brand_name, posts in brand_results.items():
        brand_cfg = brand_map.get(brand_name, {"name": brand_name, "industry": "", "style": ""})
        for post in posts:
            post["brand"] = brand_name
            all_records.append(build_record_fields(post, brand_cfg))

    if not all_records:
        print("没有需要写入的记录")
        return 0

    print(f"准备写入 {len(all_records)} 条记录...")
    written = batch_create_records(app_token, table_id, all_records, token)
    print(f"总计成功写入 {written} 条记录")
    return written


# ── 命令行测试 ────────────────────────────────────────
if __name__ == "__main__":
    cfg = load_feishu_config()
    print(f"App ID: {cfg['app_id'][:8]}...")
    t = get_tenant_access_token(cfg["app_id"], cfg["app_secret"])
    print(f"Token: {t[:16]}...")
    print("飞书配置加载成功 ✓")
