"""
洞见研报爬虫 — Playwright 版
"""

from crawlers.base import BaseCrawler


class DJYanbaoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("洞见研报", "https://www.djyanbao.com")
        self.rate_limit = 4.0

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            # 首页
            await page.goto("https://www.djyanbao.com", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            # 搜索页（洞见研报是 SPA，URL # 路由）
            search_url = f"https://www.djyanbao.com/#/search?keyword={keyword}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)  # JS 渲染需要更长

            # 提取所有报告链接
            cards = await page.query_selector_all("a[href*='/preview/'], a[href*='/detail/'], .report-item a")
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
                    full_url = href if href.startswith("http") else f"https://www.djyanbao.com{href}"

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