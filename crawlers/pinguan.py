"""
品观网爬虫 — 美妆行业垂直媒体，服务器端渲染，requests 直调

搜索 URL: https://www.pinguan.com/search?keyword={keyword}
结果结构（HTML，非 SPA）:
    <div class="message_list_one">
        <div class="message_list_right">
            <div class="search_top">
                <a href="/article/content/{id}">标题</a>
                <p>摘要</p>
            </div>
            <div class="search_bottom">
                <span class="author">作者</span>
                <span class="time">2022/12/19</span>
            </div>
        </div>
    </div>
"""

import re

import requests

from crawlers.base import BaseCrawler


class PinGuanCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("品观网", "https://www.pinguan.com")
        self.rate_limit = 1.0
        self.search_url = "https://www.pinguan.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    @staticmethod
    def _clean(text: str) -> str:
        """去掉 <strong> 等 HTML 标签和多余空白。"""
        text = re.sub(r"</?strong[^>]*>", "", text or "")
        text = re.sub(r"<[^>]+>", "", text)
        return re.sub(r"\s+", " ", text).strip()

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            resp = requests.get(
                self.search_url,
                params={"keyword": keyword},
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
            html = resp.text

            # 提取每个结果条目
            blocks = re.findall(
                r'<div class="message_list_one[^"]*">(.*?)</div>\s*</div>\s*</div>',
                html,
                re.DOTALL,
            )
            for block in blocks[: max_results * 2]:
                # 标题 + 链接（限定在 search_top 内，避免匹配到图片链接）
                top_m = re.search(
                    r'<div class="search_top">(.*?)</div>', block, re.DOTALL
                )
                if not top_m:
                    continue
                title_m = re.search(
                    r'<a[^>]+href="(/article/content/\d+[^"]*)"[^>]*>(.*?)</a>',
                    top_m.group(1),
                    re.DOTALL,
                )
                if not title_m:
                    continue
                href = title_m.group(1)
                title = self._clean(title_m.group(2))

                # 摘要
                summary_m = re.search(r"<p>(.*?)</p>", top_m.group(1), re.DOTALL)
                summary = self._clean(summary_m.group(1)) if summary_m else ""

                # 作者
                author_m = re.search(r'<span class="author">(.*?)</span>', block, re.DOTALL)
                author = self._clean(author_m.group(1)) if author_m else ""

                # 时间
                time_m = re.search(r'<span class="time">(.*?)</span>', block, re.DOTALL)
                date_raw = self._clean(time_m.group(1)) if time_m else ""
                date = date_raw.replace("/", "-") if date_raw else ""

                if not title:
                    continue

                full_url = href if href.startswith("http") else f"https://www.pinguan.com{href}"
                results.append({
                    "source": self.name,
                    "keyword": keyword,
                    "title": title[:200],
                    "url": full_url,
                    "summary": summary[:300],
                    "date": date,
                    "category": "",
                    "read_count": 0,
                    "author": author,
                })
                if len(results) >= max_results:
                    break
        except Exception as exc:
            print(f"  [{self.name}] {keyword}: 异常 {exc}")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results
