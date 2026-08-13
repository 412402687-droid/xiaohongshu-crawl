"""
飞书多维表格 (Bitable) API 写入模块

功能：
- 获取 tenant_access_token
- 动态获取表格真实字段（解决 FieldNameNotFound）
- 智能字段映射（语义匹配 + 类型自适应）
- 批量写入记录
"""

import json
import os
import re
import sys
import time
from datetime import datetime

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 配置加载 ──────────────────────────────────────────
def load_feishu_config() -> dict:
    """从 feishu_config.json 读取飞书配置，同时支持环境变量覆盖。"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "feishu_config.json")
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    config["app_id"] = os.getenv("FEISHU_APP_ID", config.get("app_id", ""))
    config["app_secret"] = os.getenv("FEISHU_APP_SECRET", config.get("app_secret", ""))
    config["app_token"] = os.getenv("FEISHU_APP_TOKEN", config.get("app_token", ""))
    config["table_id"] = os.getenv("FEISHU_TABLE_ID", config.get("table_id", ""))
    return config


# ── Token ─────────────────────────────────────────────
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    resp = requests.post(
        TOKEN_URL,
        json={"app_id": app_id, "app_secret": app_secret},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data.get('msg')}")
    return data["tenant_access_token"]


# ── 字段列表 ──────────────────────────────────────────
FIELDS_URL = (
    "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
)


def list_table_fields(app_token: str, table_id: str, token: str) -> dict:
    """
    获取表格的真实字段列表，返回 {字段名: 字段类型}。

    飞书字段类型：
      1=多行文本, 2=数字, 3=单选, 5=超链接/URL, 7=复选框,
      13=电话号码, 15=附件, 17=公式, 1001=创建时间 等
    """
    resp = requests.get(
        FIELDS_URL.format(app_token=app_token, table_id=table_id),
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取字段失败: {data.get('msg')}")

    fields = {}
    for item in data.get("data", {}).get("items", []):
        fields[item["field_name"]] = item.get("type", 1)
    return fields


# ── 智能字段映射 ──────────────────────────────────────
# 标准字段语义 → 候选关键词（按优先级）
FIELD_ALIASES = [
    ("brand",    ["品牌", "关键词", "brand", "keyword"]),
    ("title",    ["标题", "题目", "title"]),
    ("url",      ["链接", "地址", "url", "link", "来源链接"]),
    ("source",   ["来源", "平台", "类型", "source", "渠道"]),
    ("summary",  ["摘要", "内容", "正文", "summary", "描述"]),
    ("category", ["分类", "行业", "机构", "category"]),
    ("date",     ["日期", "时间", "发布", "date", "time"]),
    ("author",   ["作者", "分析师", "author"]),
]

# 标准字段 → 飞书字段类型
URL_FIELD_TYPE = 15      # 超链接 (url)
DATETIME_FIELD_TYPE = 5  # 日期 (date_time)


def build_field_map(real_fields: dict) -> dict:
    """
    将标准字段名映射到真实字段名。

    返回 {标准字段: 真实字段名}，只包含能匹配上的。
    """
    mapping = {}
    used = set()
    for std_name, keywords in FIELD_ALIASES:
        for fname, ftype in real_fields.items():
            if fname in used:
                continue
            for kw in keywords:
                if kw.lower() in fname.lower():
                    mapping[std_name] = fname
                    used.add(fname)
                    break
            if std_name in mapping:
                break
    return mapping


def _format_url_value(field_type: int, url: str, text: str):
    """根据字段类型格式化 URL 值。"""
    if field_type == URL_FIELD_TYPE:
        return {"link": url, "text": text or "查看原文"}
    return url  # 文本类型直接给 URL 字符串


def _parse_date_to_ts(date_str) -> int:
    """
    将各种日期字符串解析为毫秒时间戳（飞书日期字段要求）。

    支持：2025-12-28 / 2026年8月6日 / 2025-12-28T16:00:00.000Z
    返回 None 表示无法解析。
    """
    if not date_str:
        return None
    s = str(date_str).strip()
    try:
        m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
        if m:
            y, mo, d = map(int, m.groups())
            return int(datetime(y, mo, d).timestamp() * 1000)
        m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
        if m:
            y, mo, d = map(int, m.groups())
            return int(datetime(y, mo, d).timestamp() * 1000)
    except Exception:
        pass
    return None


# ── 记录构建 ──────────────────────────────────────────
def build_article_fields(article: dict, field_map: dict, real_fields: dict) -> dict:
    """
    根据真实字段映射，将文章数据转换为飞书字段。

    Args:
        article: 抓取到的文章 dict
        field_map: 标准字段 → 真实字段名 映射
        real_fields: 真实字段名 → 类型

    Returns:
        飞书字段 dict（只包含真实存在的字段）
    """
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "brand": article.get("keyword", ""),
        "title": article.get("title", ""),
        "url": article.get("url", ""),
        "source": article.get("source", ""),
        "summary": article.get("summary", ""),
        "category": article.get("category", ""),
        "date": article.get("date", ""),
        "author": article.get("author", ""),
    }

    fields = {}
    for std_name, real_name in field_map.items():
        ftype = real_fields.get(real_name, 1)
        val = data.get(std_name, "")
        if std_name == "url":
            val = _format_url_value(ftype, data["url"], data["title"])
        elif std_name == "date" and ftype == DATETIME_FIELD_TYPE:
            ts = _parse_date_to_ts(val)
            if ts is None:
                continue  # 日期无法解析，跳过该字段
            val = ts
        elif ftype == 2 and isinstance(val, str) and val.isdigit():
            val = int(val)
        fields[real_name] = val

    return fields


# ── 批量写入 ──────────────────────────────────────────
RECORDS_URL = (
    "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
)
MAX_BATCH = 500


def batch_create_records(app_token, table_id, records, token) -> int:
    if not records:
        return 0

    total_written = 0
    url = RECORDS_URL.format(app_token=app_token, table_id=table_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for i in range(0, len(records), MAX_BATCH):
        batch = records[i : i + MAX_BATCH]
        payload = {"records": [{"fields": r} for r in batch]}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            print(f"  写入失败 (batch {i // MAX_BATCH}): {data.get('msg')}")
            continue
        written = len(data.get("data", {}).get("records", []))
        total_written += written
        print(f"  批次 {i // MAX_BATCH + 1}: 写入 {written} 条")

    return total_written


# ── 多源情报写入 ──────────────────────────────────────
def write_multi_source_data(articles, app_token, table_id, token) -> int:
    if not articles:
        print("没有需要写入的情报")
        return 0

    # 1. 获取真实字段
    try:
        real_fields = list_table_fields(app_token, table_id, token)
        # 打印字段名 + 类型号（便于诊断）
        detail = {k: v for k, v in real_fields.items()}
        print(f"[飞书] 表格字段(名=类型): {detail}")
    except Exception as exc:
        print(f"[飞书] 获取字段失败: {exc}，使用默认字段名")
        real_fields = {
            "品牌名称": 1, "笔记标题": 1, "笔记链接": 15, "笔记类型": 1,
            "作者": 1, "发布时间": 5, "抓取时间": 1, "抓取日期": 1,
        }

    # 2. 构建字段映射
    field_map = build_field_map(real_fields)
    print(f"[飞书] 字段映射: {field_map}")
    if not field_map:
        print("[飞书] 警告: 没有字段能匹配上，请检查表格字段名")

    # 3. 去重（按 URL）
    seen = set()
    unique = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)
        elif not url:
            unique.append(a)

    # 4. 构建记录
    records = [build_article_fields(a, field_map, real_fields) for a in unique]
    records = [r for r in records if r]  # 过滤空记录
    print(f"去重后 {len(records)} 条（原始 {len(articles)} 条）")

    if not records:
        print("没有可写入的字段映射，跳过写入")
        return 0

    return batch_create_records(app_token, table_id, records, token)


# ── 命令行测试 ────────────────────────────────────────
if __name__ == "__main__":
    cfg = load_feishu_config()
    if not cfg.get("app_id") or cfg["app_id"].startswith("your_"):
        print("飞书配置未填写（占位符）。请在 feishu_config.json 或环境变量中填写。")
        sys.exit(0)

    t = get_tenant_access_token(cfg["app_id"], cfg["app_secret"])
    print(f"Token: {t[:16]}...")
    fields = list_table_fields(cfg["app_token"], cfg["table_id"], t)
    print(f"表格字段: {list(fields.keys())}")
    mapping = build_field_map(fields)
    print(f"字段映射: {mapping}")
