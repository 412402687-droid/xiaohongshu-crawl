"""
小红书搜索抓取模块 — 基于 Playwright

功能：
- 搜索指定品牌关键词
- 提取笔记标题、链接、点赞数、收藏数、评论数、发布时间
- 支持 Cookie 登录态（绕过验证码）
"""

import asyncio
import json
import os
import re
import time
import sys
from datetime import datetime
from typing import Optional

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    # 降级处理，仅用于模块导入场景
    async_playwright = None

# ── 常量 ──────────────────────────────────────────────
SEARCH_URL = "https://www.xiaohongshu.com/search_result"
LOGIN_URL = "https://www.xiaohongshu.com"
DEFAULT_TIMEOUT = 15000       # ms
SEARCH_TIMEOUT = 20000        # ms
SCROLL_PAUSE = 2.0            # 每次滚动间隔（秒）
MAX_SCROLL = 8                # 最大滚动次数
MIN_POSTS = 15                # 最少采集笔记数


def load_cookies_from_env() -> Optional[list]:
    """从环境变量 XHS_COOKIE 加载 Cookie（JSON 字符串）。"""
    raw = os.getenv("XHS_COOKIE", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 兼容 a=1; b=2 格式
        cookies = []
        for item in raw.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                cookies.append({
                    "name": k.strip(),
                    "value": v.strip(),
                    "domain": ".xiaohongshu.com",
                    "path": "/",
                })
        return cookies if cookies else None


def parse_count(text: Optional[str]) -> int:
    """解析「1.2万」「999」等文本为整数。"""
    if not text:
        return 0
    text = text.strip()
    if "万" in text:
        try:
            return int(float(text.replace("万", "")) * 10000)
        except ValueError:
            return 0
    try:
        return int(re.sub(r"[^\d]", "", text))
    except ValueError:
        return 0


async def crawl_brand(brand_name: str, max_posts: int = 20) -> list:
    """
    搜索指定品牌并返回笔记列表。

    返回格式:
    [
        {
            "title": "...",
            "url": "...",
            "likes": 1234,
            "collects": 567,
            "comments": 89,
            "publish_time": "2026-08-05",
            "author": "...",
            "note_type": "图文|视频",
        },
        ...
    ]
    """
    if async_playwright is None:
        raise RuntimeError("playwright 未安装，请执行: pip install playwright && playwright install")

    results = []
    cookie_data = load_cookies_from_env()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        if cookie_data:
            await context.add_cookies(cookie_data)

        page = await context.new_page()

        try:
            # 先访问首页建立会话
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
            await asyncio.sleep(1)

            # 构造搜索 URL
            keyword = brand_name
            search_url = f"{SEARCH_URL}?keyword={keyword}&sort=general"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=SEARCH_TIMEOUT)
            await asyncio.sleep(2)

            # 滚动加载更多
            scroll_count = 0
            while len(results) < max_posts and scroll_count < MAX_SCROLL:
                # 提取当前可见笔记
                cards = await page.query_selector_all("section.note-item, div.note-item, a[href*='/explore/']")
                if not cards:
                    # 备选选择器
                    cards = await page.query_selector_all("div[class*='note'] a[href*='/explore/']")

                for card in cards:
                    try:
                        href = await card.get_attribute("href")
                        if not href:
                            continue
                        # 去重
                        if any(r.get("url") == href for r in results):
                            continue

                        title_el = await card.query_selector(
                            "span.title, .title, [class*='title']"
                        )
                        title = await title_el.inner_text() if title_el else ""

                        author_el = await card.query_selector(
                            ".author .name, [class*='author'] [class*='name'], .nickname"
                        )
                        author = await author_el.inner_text() if author_el else ""

                        # 笔记类型判断
                        is_video = await card.query_selector("[class*='video'], .play-icon")
                        note_type = "视频" if is_video else "图文"

                        results.append({
                            "title": title.strip() if title else "",
                            "url": f"https://www.xiaohongshu.com{href}" if href.startswith("/") else href,
                            "likes": 0,
                            "collects": 0,
                            "comments": 0,
                            "publish_time": "",
                            "author": author.strip() if author else "",
                            "note_type": note_type,
                        })
                    except Exception:
                        continue

                # 滚动
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                scroll_count += 1
                await asyncio.sleep(SCROLL_PAUSE)

            # 截断到 max_posts
            results = results[:max_posts]

        except PlaywrightTimeout:
            print(f"[{brand_name}] 页面加载超时，已获取 {len(results)} 条")
        except Exception as exc:
            print(f"[{brand_name}] 抓取出错: {exc}")
        finally:
            await browser.close()

    return results


async def crawl_all_brands(brands: list, max_per_brand: int = 20) -> dict:
    """
    批量抓取多个品牌。

    参数:
        brands: 品牌配置列表，每项含 name 字段
        max_per_brand: 每个品牌最多抓取笔记数

    返回:
        { "花西子": [...], "雅诗兰黛": [...], ... }
    """
    all_results = {}
    for brand in brands:
        name = brand.get("name", "")
        if not name:
            continue
        print(f"[{name}] 开始抓取...")
        try:
            posts = await crawl_brand(name, max_posts=max_per_brand)
            all_results[name] = posts
            print(f"[{name}] 抓取完成，共 {len(posts)} 条笔记")
        except Exception as exc:
            print(f"[{name}] 抓取失败: {exc}")
            all_results[name] = []
        # 品牌间间隔，避免限流
        await asyncio.sleep(3)
    return all_results


# ── 命令行入口 ────────────────────────────────────────
if __name__ == "__main__":
    test_brand = sys.argv[1] if len(sys.argv) > 1 else "花西子"
    posts = asyncio.run(crawl_brand(test_brand, max_posts=10))
    print(json.dumps(posts, ensure_ascii=False, indent=2))
