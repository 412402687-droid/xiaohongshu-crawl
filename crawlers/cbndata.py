"""
CBNData 爬虫 — 第一财经商业数据中心（Playwright 版）
"""

from crawlers.base import BaseCrawler


class CBNDataCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("CBNData", "https://www.cbndata.com")
        self.rate_limit = 3.0

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            # 进入首页
            await page.goto("https://www.cbndata.com", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)

            # 在 URL 上拼搜索关键词（更可靠）
            search_url = f"https://www.cbndata.com/search?query={keyword}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)

            # 等待搜索结果出现
            try:
                await page.wait_for_selector(".information-card, .report-card, .search-item", timeout=10000)
            except Exception:
                pass

            # 提取
            cards = await page.query_selector_all("a[href*='/information/'], a[href*='/report/']")
            seen = set()
            for card in cards[:max_results * 3]:
                try:
                    href = await card.get_attribute("href")
                    if not href or href in seen:
                        continue
                    seen.add(href)

                    text = (await card.inner_text()).strip()
                    if not text or len(text) < 5:
                        continue

                    # 第一行作为标题
                    title = text.split("\n")[0].strip()
                    full_url = href if href.startswith("http") else f"https://www.cbndata.com{href}"

                    results.append({
                        "source": self.name,
                        "keyword": keyword,
                        "title": title[:200],
                        "url": full_url,
                        "summary": "",
                        "date": self.extract_date(text),
                        "category": "",
                        "read_count": 0,
                    })
                    if len(results) >= max_results:
                        break
                except Exception:
                    continue
        except Exception as exc:
            print(f"  [{self.name}] {keyword}: 异常 {exc}")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results