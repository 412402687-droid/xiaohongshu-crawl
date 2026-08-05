"""
发现报告爬虫 — Playwright 版
"""

from crawlers.base import BaseCrawler


class FxBaoGaoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("发现报告", "https://www.fxbaogao.com")
        self.rate_limit = 3.5

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            # 首页
            await page.goto("https://www.fxbaogao.com", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            # 搜索页（路由 URL）
            search_url = f"https://www.fxbaogao.com/search?keyword={keyword}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(4000)

            # 提取详情页链接
            cards = await page.query_selector_all("a[href*='/detail/']")
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
            print(f"  [{self.name}] {keyword}: 异常 {exc}")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results