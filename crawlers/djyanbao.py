"""
洞见研报爬虫 — 通过首页搜索框交互
"""

from crawlers.base import BaseCrawler


class DJYanbaoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("洞见研报", "https://www.djyanbao.com")
        self.rate_limit = 4.5

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            await page.goto("https://www.djyanbao.com", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)

            # 查找搜索框
            search_selectors = [
                'input[type="search"]',
                'input[type="text"][placeholder]',
                'input[placeholder*="搜索"]',
                'input[placeholder*="研报"]',
                'input[placeholder*="关键词"]',
                '.search-input',
                '.el-input__inner',
            ]
            search_input = None
            for sel in search_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        search_input = el
                        break
                except Exception:
                    continue

            if search_input:
                await search_input.fill(keyword)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(6000)  # SPA 渲染慢
            else:
                # 备用：尝试 URL 搜索
                await page.goto(f"https://www.djyanbao.com/#/search?keyword={keyword}",
                                wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(6000)

            # 提取报告链接
            cards = await page.query_selector_all("a[href*='/preview/'], a[href*='/detail/'], a[href*='/report/']")
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