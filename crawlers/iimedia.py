"""
艾媒网爬虫

数据源: https://www.iimedia.cn
抓取内容: 研究报告、艾媒金榜（品牌排行）、消费趋势分析
频道结构: /c400/ 报告, /c880/ 金榜, /c1061/ 数据, /c1086/ 消费
"""

import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler


IIMEDIA_SEARCH = "https://www.iimedia.cn/search.html"

# 与品牌分析强相关的频道
TARGET_CHANNELS = ["c400", "c880", "c1061", "c1086"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class IIMediaCrawler(BaseCrawler):
    """艾媒网爬虫"""

    def __init__(self):
        super().__init__("艾媒网", "https://www.iimedia.cn")
        self.rate_limit = 3.0

    async def search(self, keyword: str, max_results: int = 10) -> list:
        """搜索品牌关键词，返回文章/报告列表。"""
        results = []
        await self._rate_limit()

        try:
            async with aiohttp.ClientSession() as session:
                params = {"query": keyword}
                async with session.get(IIMEDIA_SEARCH, params=params, headers=HEADERS, timeout=20) as resp:
                    if resp.status != 200:
                        print(f"  [艾媒网] {keyword}: HTTP {resp.status}")
                        return results
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 搜索结果卡片
            cards = soup.select("div.search-result-item, div.article-item, div.list-item")
            if not cards:
                cards = soup.select("a[href*='/c400/'], a[href*='/c880/'], a[href*='/c1061/'], a[href*='/c1086/']")

            # 去重
            seen = set()
            unique_cards = []
            for card in cards:
                href = card.get("href", "")
                if href in seen:
                    continue
                seen.add(href)
                unique_cards.append(card)

            for card in unique_cards[:max_results]:
                try:
                    href = card.get("href", "")
                    if not href:
                        continue

                    url = href if href.startswith("http") else f"{self.base_url}{href}"

                    # 标题
                    title_el = card.find("h3") or card.find("h2") or card.find(class_=re.compile("title"))
                    title = self.clean_text(title_el.get_text()) if title_el else ""

                    # 摘要
                    summary_el = card.find(class_=re.compile("desc|summary|abstract|intro"))
                    summary = self.clean_text(summary_el.get_text()) if summary_el else ""

                    # 日期
                    date_el = card.find(class_=re.compile("time|date")) or card.find("time")
                    date = self.extract_date(date_el.get_text()) if date_el else ""

                    # 分类：从 URL 推断
                    category = "研究报告" if "/c400/" in href else \
                               "品牌排行" if "/c880/" in href else \
                               "数据分析" if "/c1061/" in href else \
                               "消费趋势" if "/c1086/" in href else ""

                    if title:
                        results.append({
                            "source": self.name,
                            "keyword": keyword,
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "date": date or self.extract_date(""),
                            "category": category,
                            "read_count": 0,
                        })
                except Exception as exc:
                    print(f"  [艾媒网] 解析卡片出错: {exc}")
                    continue

        except Exception as exc:
            print(f"  [艾媒网] {keyword}: 抓取异常 {exc}")

        print(f"  [艾媒网] {keyword}: 获取 {len(results)} 条")
        return results
