"""
艾媒网爬虫 — Playwright 版
"""

from crawlers.base import BaseCrawler


class IIMediaCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("艾媒网", "https://www.iimedia.cn")
        self.rate_limit = 3.0

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            # 先访问首页
            await page.goto("https://www.iimedia.cn", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            # 直接访问搜索 URL
            search_url = f"https://www.iimedia.cn/search.html?query={keyword}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)

            # 等待结果
            try:
                await page.wait_for_selector("a[href*='/c400/'], a[href*='/c880/']", timeout=10000)
            except Exception:
                pass

            cards = await page.query_selector_all("a[href*='/c400/'], a[href*='/c880/'], a[href*='/c1061/'], a[href*='/c1086/']")
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
                    full_url = href if href.startswith("http") else f"https://www.iimedia.cn{href}"

                    # 分类
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
            print(f"  [{self.name}] {keyword}: 异常 {exc}")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results