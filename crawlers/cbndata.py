"""
CBNData 爬虫 — 第一财经商业数据中心

数据源: https://www.cbndata.com
抓取内容: 消费品类报告、品牌分析文章、行业洞察
搜索入口: https://www.cbndata.com/search?query={keyword}
"""

import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler


CBN_SEARCH = "https://www.cbndata.com/search"
CBN_INFO = "https://www.cbndata.com/information"
CBN_REPORT = "https://www.cbndata.com/report"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class CBNDataCrawler(BaseCrawler):
    """CBNData 爬虫"""

    def __init__(self):
        super().__init__("CBNData", "https://www.cbndata.com")
        self.rate_limit = 2.5

    async def search(self, keyword: str, max_results: int = 10) -> list:
        """搜索品牌关键词，返回文章列表。"""
        results = []
        await self._rate_limit()

        try:
            async with aiohttp.ClientSession() as session:
                params = {"query": keyword}
                async with session.get(CBN_SEARCH, params=params, headers=HEADERS, timeout=20) as resp:
                    if resp.status != 200:
                        print(f"  [CBNData] {keyword}: HTTP {resp.status}")
                        return results
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 搜索结果卡片选择器
            cards = soup.select("div.information-card, div.report-card, div.search-result-item")
            if not cards:
                # 回退：匹配文章列表（首页结构可能不同）
                cards = soup.select("a[href*='/information/'], a[href*='/report/']")
                # 去重（按 href）
                seen = set()
                unique_cards = []
                for card in cards:
                    href = card.get("href", "")
                    if href in seen:
                        continue
                    seen.add(href)
                    unique_cards.append(card)
                cards = unique_cards

            for card in cards[:max_results]:
                try:
                    href = card.get("href", "")
                    if not href:
                        continue

                    # 完整 URL
                    url = href if href.startswith("http") else f"{CBN_SEARCH.rsplit('/', 1)[0]}{href}"

                    # 标题
                    title_el = card.find("h3") or card.find(class_=re.compile("title"))
                    title = self.clean_text(title_el.get_text()) if title_el else ""

                    # 摘要
                    summary_el = card.find(class_=re.compile("desc|summary|abstract"))
                    summary = self.clean_text(summary_el.get_text()) if summary_el else ""

                    # 日期
                    date_el = card.find(class_=re.compile("time|date")) or card.find("time")
                    date = self.extract_date(date_el.get_text()) if date_el else ""

                    # 阅读量
                    read_el = card.find(class_=re.compile("read|view|count"))
                    read_count = 0
                    if read_el:
                        nums = re.findall(r"(\d+)", read_el.get_text())
                        read_count = int(nums[0]) if nums else 0

                    # 分类
                    cat_el = card.find(class_=re.compile("tag|category"))
                    category = self.clean_text(cat_el.get_text()) if cat_el else ""

                    if title:
                        results.append({
                            "source": self.name,
                            "keyword": keyword,
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "date": date or self.extract_date(""),
                            "category": category,
                            "read_count": read_count,
                        })
                except Exception as exc:
                    print(f"  [CBNData] 解析卡片出错: {exc}")
                    continue

        except Exception as exc:
            print(f"  [CBNData] {keyword}: 抓取异常 {exc}")

        print(f"  [CBNData] {keyword}: 获取 {len(results)} 条")
        return results
