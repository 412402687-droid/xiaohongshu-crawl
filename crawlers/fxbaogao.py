"""
发现报告爬虫 — 专业研报平台

数据源: https://www.fxbaogao.com
抓取内容: 行业报告、券商研报、公司研究
搜索入口: https://www.fxbaogao.com/search?keyword={keyword}
"""

import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler


FXB_SEARCH = "https://www.fxbaogao.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class FxBaoGaoCrawler(BaseCrawler):
    """发现报告爬虫"""

    def __init__(self):
        super().__init__("发现报告", "https://www.fxbaogao.com")
        self.rate_limit = 3.0

    async def search(self, keyword: str, max_results: int = 10) -> list:
        """搜索研报关键词。"""
        results = []
        await self._rate_limit()

        try:
            async with aiohttp.ClientSession() as session:
                params = {"keyword": keyword}
                async with session.get(FXB_SEARCH, params=params, headers=HEADERS, timeout=20) as resp:
                    if resp.status != 200:
                        print(f"  [发现报告] {keyword}: HTTP {resp.status}")
                        return results
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # 搜索结果卡片
            cards = soup.select("div.search-item, div.report-item, a[class*='result']")
            if not cards:
                cards = soup.select("a[href*='/detail/'], a[href*='/report/']")

            seen = set()
            unique = []
            for card in cards:
                href = card.get("href", "")
                if href in seen:
                    continue
                seen.add(href)
                unique.append(card)

            for card in unique[:max_results]:
                try:
                    href = card.get("href", "")
                    if not href:
                        continue
                    url = href if href.startswith("http") else f"{self.base_url}{href}"

                    title_el = card.find("h3") or card.find(class_=re.compile("title"))
                    title = self.clean_text(title_el.get_text()) if title_el else ""

                    summary_el = card.find(class_=re.compile("desc|summary|abstract"))
                    summary = self.clean_text(summary_el.get_text()) if summary_el else ""

                    date_el = card.find(class_=re.compile("time|date")) or card.find("time")
                    date = self.extract_date(date_el.get_text()) if date_el else ""

                    org_el = card.find(class_=re.compile("org|source|author|company"))
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
                    print(f"  [发现报告] 解析出错: {exc}")
                    continue

        except Exception as exc:
            print(f"  [发现报告] {keyword}: 抓取异常 {exc}")

        print(f"  [发现报告] {keyword}: 获取 {len(results)} 条")
        return results
