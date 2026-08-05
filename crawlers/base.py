"""
基础爬虫模块 — 提供统一的抓取接口和通用工具

所有平台爬虫继承 BaseCrawler，只需实现 search() 方法。
"""

import asyncio
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime


class BaseCrawler(ABC):
    """爬虫基类，定义统一接口。"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.last_request_time = 0
        self.rate_limit = 2.0  # 请求间隔（秒）

    @abstractmethod
    async def search(self, keyword: str, max_results: int = 10) -> list:
        """
        搜索指定关键词，返回文章/报告列表。

        返回格式:
        [
            {
                "source": "CBNData",
                "keyword": "花西子",
                "title": "...",
                "url": "...",
                "summary": "...",
                "date": "2026-08-05",
                "category": "美妆个护",
                "read_count": 0,
            },
            ...
        ]
        """
        ...

    async def _rate_limit(self):
        """请求频率控制。"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本中的空白和特殊字符。"""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def extract_date(text: str) -> str:
        """从文本中提取日期，返回 YYYY-MM-DD 格式。"""
        if not text:
            return ""
        patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{4}/\d{2}/\d{2})",
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
            r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                groups = [g.zfill(2) for g in match.groups()]
                if len(groups) == 3:
                    return f"{groups[0]}-{groups[1]}-{groups[2]}"
                return match.group()
        return datetime.now().strftime("%Y-%m-%d")
