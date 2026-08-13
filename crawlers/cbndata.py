"""
CBNData 爬虫 — 搜索结果页提取标题/摘要/日期/分类

CBNData 搜索结果页（/search?query=xxx）结构：
  <div class="items">
    <div class="content-item">      ← 结果卡片
      <div class="desc">
        <h3>标题</h3>
        <p>摘要</p>
        <div class="cp-tag-unit"><a>分类标签</a></div>
        <div class="date">日期</div>
      </div>
    </div>
  </div>

注意：卡片不暴露详情 URL（React 点击跳转），URL 降级为搜索链接。
"""

from crawlers.base import BaseCrawler


class CBNDataCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("CBNData", "https://www.cbndata.com")
        self.rate_limit = 2.0

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            page.set_default_timeout(15000)
            await page.goto(
                f"https://www.cbndata.com/search?query={keyword}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            await page.wait_for_timeout(4000)

            cards = await page.query_selector_all("div.content-item")
            for card in cards[:max_results]:
                try:
                    # 标题
                    h3 = await card.query_selector("h3")
                    title = (await h3.inner_text()).strip() if h3 else ""

                    # 摘要
                    p = await card.query_selector("p")
                    summary = (await p.inner_text()).strip() if p else ""

                    # 日期
                    date_el = await card.query_selector(".date")
                    date_text = (await date_el.inner_text()).strip() if date_el else ""

                    # 分类标签
                    tag_el = await card.query_selector(".cp-tag-unit a, a[href*='search?query']")
                    category = (await tag_el.inner_text()).strip() if tag_el else ""

                    if not title:
                        continue

                    results.append({
                        "source": self.name,
                        "keyword": keyword,
                        "title": title[:200],
                        "url": f"https://www.cbndata.com/search?query={keyword}",
                        "summary": summary[:300],
                        "date": self.extract_date(date_text) or date_text,
                        "category": category,
                        "read_count": 0,
                    })
                except Exception:
                    continue
        except Exception as exc:
            print(f"  [{self.name}] {keyword}: 超时/异常（已跳过）")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results
