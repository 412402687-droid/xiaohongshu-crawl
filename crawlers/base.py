"""
基础爬虫模块 — Playwright 通用版

所有平台爬虫继承 BaseCrawler，使用 Playwright 渲染 JavaScript 页面。
"""

import asyncio
import re
from abc import ABC, abstractmethod


class BaseCrawler(ABC):
    """爬虫基类，Playwright 异步版。"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.last_request_time = 0
        self.rate_limit = 3.0  # 请求间隔（秒）

    @abstractmethod
    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        """
        在已加载的 page 上搜索关键词，返回结果列表。

        子类需要实现具体的 URL 跳转、元素选择、提取逻辑。

        返回格式:
        [
            {"source": "...", "keyword": "...", "title": "...", "url": "...", "summary": "...", "date": "..."},
            ...
        ]
        """
        ...

    async def _rate_limit(self):
        """请求频率控制。"""
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def extract_date(text: str) -> str:
        if not text:
            return ""
        patterns = [
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", 3),
            (r"(\d{4})/(\d{1,2})/(\d{1,2})", 3),
            (r"(\d{4})\.(\d{1,2})\.(\d{1,2})", 3),
            (r"(\d{4})年(\d{1,2})月(\d{1,2})日", 3),
        ]
        for pat, n in patterns:
            m = re.search(pat, text)
            if m:
                gs = [g.zfill(2) for g in m.groups()]
                if len(gs) == 3:
                    return f"{gs[0]}-{gs[1]}-{gs[2]}"
        # 兜底：当前日期
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")