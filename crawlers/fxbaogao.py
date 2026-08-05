"""
发现报告爬虫 — 简化为直接访问 + 短超时
"""

from crawlers.base import BaseCrawler


class FxBaoGaoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("发现报告", "https://www.fxbaogao.com")
        self.rate_limit = 2.5

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            page.set_default_timeout(15000)
            await page.goto(f"https://www.fxbaogao.com/search?keyword={keyword}",
                            wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3500)

            cards = await page.query_selector_all("a[href*='/detail/']")
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
                    full_url = href if href.startswith("http") else f"https://www.fxbaogao.com{href}"
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
            print(f"  [{self.name}] {keyword}: 超时/异常（已跳过）")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results