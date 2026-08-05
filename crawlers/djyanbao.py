"""
洞见研报爬虫 — 行业研究报告聚合平台

数据源: https://www.djyanbao.com
抓取内容: 券商研报、咨询报告、行业分析
搜索入口: https://www.djyanbao.com/search?keyword={keyword}
"""

import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler


DJ_SEARCH = "https://www.djyanbao.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class DJYanbaoCrawler(BaseCrawler):
    """洞见研报爬虫"""

    def __init__(self):
        super().__init__("洞见研报", "https://www.djyanbao.com")
        self.rate_limit = 3.0

    async def search(self, keyword: str, max_results: int = 10) -> list:
        """搜索研报，返回列表。"""
        results = []
        await self._rate_limit()

        try:
            async with aiohttp.ClientSession() as session:
                params = {"keyword": keyword}
                async with session.get(DJ_SEARCH, params=params, headers=HEADERS, timeout=20) as resp:
                    if resp.status != 200:
                        print(f"  [洞见研报] {keyword}: HTTP {resp.status}")
                        return results
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 报告列表选择器
            cards = soup.select("div.report-item, div.search-item, div.report-card")
            if not cards:
                cards = soup.select("a[href*='/report/'], a[href*='/preview/']")

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
                    title_el = card.find("h3") or card.find(class_=re.compile("title"))
                    title = self.clean_text(title_el.get_text()) if title_el else ""

                    # 摘要
                    summary_el = card.find(class_=re.compile("desc|summary|abstract|intro"))
                    summary = self.clean_text(summary_el.get_text()) if summary_el else ""

                    # 日期
                    date_el = card.find(class_=re.compile("time|date")) or card.find("time")
                    date = self.extract_date(date_el.get_text()) if date_el else ""

                    # 机构（券商/咨询公司）
                    org_el = card.find(class_=re.compile("org|institution|author"))
                    org = self.clean_text(org_el.get_text()) if org_el else ""

                    if title:
                        results.append({
                            "source": self.name,
                            "keyword": keyword,
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "date": date or self.extract_date(""),
                            "category": org,
                            "read_count": 0,
                        })
                except Exception as exc:
                    print(f"  [洞见研报] 解析卡片出错: {exc}")
                    continue

        except Exception as exc:
            print(f"  [洞见研报] {keyword}: 抓取异常 {exc}")

        print(f"  [洞见研报] {keyword}: 获取 {len(results)} 条")
        return results
