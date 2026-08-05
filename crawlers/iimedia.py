"""
艾媒网爬虫 — Playwright 版（精简超时）
"""

from crawlers.base import BaseCrawler


class IIMediaCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("艾媒网", "https://www.iimedia.cn")
        self.rate_limit = 2.5

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            page.set_default_timeout(15000)

            # 直接访问搜索 URL（已验证有效）
            search_url = f"https://www.iimedia.cn/search.html?query={keyword}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2500)

            cards = await page.query_selector_all("a[href*='/c400/'], a[href*='/c880/'], a[href*='/c1061/'], a[href*='/c1086/']")
            seen = set()
            for card in cards[:max_results * 3]:
                try:
                    href = await card.get_attribute("href")
                    if not href or href in seen:
                        continue
                    seen.add(href)

                    text = (await card.inner_text()).strip()
                    if not text or len(text) < 4:
                        continue

                    title = text.split("\n")[0].strip()
                    full_url = href if href.startswith("http") else f"https://www.iimedia.cn{href}"

                    category = ""
                    if "/c400/" in href:
                        category = "研究报告"
                    elif "/c880/" in href:
                        category = "品牌排行"
                    elif "/c1061/" in href:
                        category = "数据分析"
                    elif "/c1086/" in href:
                        category = "消费趋势"

                    results.append({
                        "source": self.name,
                        "keyword": keyword,
                        "title": title[:200],
                        "url": full_url,
                        "summary": "",
                        "date": self.extract_date(text),
                        "category": category,
                        "read_count": 0,
                    })
                    if len(results) >= max_results:
                        break
                except Exception:
                    continue
        except Exception as exc:
            print(f"  [{self.name}] {keyword}: 超时/异常（已跳过）")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results