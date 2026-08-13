"""
洞见研报爬虫 — 直接调用搜索 API（无需浏览器）

API: https://api.djyanbao.com/api/report?page=1&q={keyword}&limit=20
详情页: https://www.djyanbao.com/report/detail?id={id}

返回字段：id, title, authors, orgName, publishAt, pageTotal, highlight.content
"""

import re
import requests

from crawlers.base import BaseCrawler


class DJYanbaoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("洞见研报", "https://www.djyanbao.com")
        self.rate_limit = 1.0  # API 调用可更快
        self.api = "https://api.djyanbao.com/api/report"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.djyanbao.com/",
        }

    @staticmethod
    def _strip_em(text: str) -> str:
        """去掉高亮 <em> 标签。"""
        return re.sub(r"</?em>", "", text or "").strip()

    async def search(self, page, keyword: str, max_results: int = 10) -> list:
        results = []
        try:
            resp = requests.get(
                self.api,
                params={"page": 1, "q": keyword, "limit": max_results},
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("data", [])

            for item in data[:max_results]:
                rid = item.get("id")
                title = self._strip_em(item.get("title", ""))
                if not title:
                    continue

                # 摘要：取 highlight.content 第一段，去 em 标签
                contents = item.get("highlight", {}).get("content", [])
                summary = ""
                for c in contents:
                    clean = self._strip_em(c)
                    if clean:
                        summary = clean
                        break

                publish = item.get("publishAt", "")
                date = publish[:10] if publish else ""

                results.append({
                    "source": self.name,
                    "keyword": keyword,
                    "title": title[:200],
                    "url": f"https://www.djyanbao.com/report/detail?id={rid}",
                    "summary": summary[:300],
                    "date": date,
                    "category": item.get("orgName", ""),  # 机构名放 category
                    "read_count": item.get("pageTotal", 0),
                })
        except Exception as exc:
            print(f"  [{self.name}] {keyword}: 异常 {exc}")

        print(f"  [{self.name}] {keyword}: 获取 {len(results)} 条")
        return results
