"""
多源统一抓取调度器 — Playwright 版

使用单一 Playwright 浏览器实例轮流访问各平台，避免重复启动浏览器。
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.cbndata import CBNDataCrawler
from crawlers.iimedia import IIMediaCrawler
from crawlers.djyanbao import DJYanbaoCrawler
from crawlers.fxbaogao import FxBaoGaoCrawler


async def crawl_all_sources(brands: list, max_per_source: int = 10) -> dict:
    """
    使用 Playwright 抓取各平台品牌数据。
    """
    from playwright.async_api import async_playwright

    all_results = {}
    crawlers = [
        CBNDataCrawler(),
        IIMediaCrawler(),
        DJYanbaoCrawler(),
        FxBaoGaoCrawler(),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )

        # 反检测脚本
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        for brand in brands:
            name = brand.get("name", "")
            if not name:
                continue

            brand_results = []
            print(f"\n[{name}] === 开始多源搜索 ===")

            for crawler in crawlers:
                page = await context.new_page()
                try:
                    print(f"  [{crawler.name}] 搜索 '{name}'...")
                    articles = await crawler.search(page, name, max_results=max_per_source)
                    brand_results.extend(articles)
                except Exception as exc:
                    print(f"  [{crawler.name}] 搜索失败: {exc}")
                finally:
                    await page.close()
                await crawler._rate_limit()

            all_results[name] = brand_results
            print(f"[{name}] 汇总: 共 {len(brand_results)} 条结果")
            await asyncio.sleep(2)

        await browser.close()

    return all_results


async def crawl_topic_keywords(keywords: list, max_results: int = 15) -> list:
    """按行业关键词搜索。"""
    from playwright.async_api import async_playwright

    results = []
    crawlers = [
        CBNDataCrawler(),
        IIMediaCrawler(),
        DJYanbaoCrawler(),
        FxBaoGaoCrawler(),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        for kw in keywords:
            print(f"\n[主题] === 搜索 '{kw}' ===")
            for crawler in crawlers:
                page = await context.new_page()
                try:
                    articles = await crawler.search(page, kw, max_results=max_results)
                    for a in articles:
                        a["keyword"] = kw
                    results.extend(articles)
                    print(f"  [{crawler.name}] '{kw}': {len(articles)} 条")
                except Exception as exc:
                    print(f"  [{crawler.name}] 搜索 '{kw}' 失败: {exc}")
                finally:
                    await page.close()
                await crawler._rate_limit()
            await asyncio.sleep(2)

        await browser.close()

    return results


if __name__ == "__main__":
    test_kw = sys.argv[1] if len(sys.argv) > 1 else "美妆"
    results = asyncio.run(crawl_all_sources([{"name": test_kw}], max_per_source=5))
    for k, v in results.items():
        print(f"\n{k}: {len(v)} 条")
        for item in v:
            print(f"  [{item['source']}] {item['title'][:60]}")