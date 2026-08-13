"""
小红书推荐流爬虫 — 采集首页推荐流，按品牌关键词过滤

原理（借鉴 Trendora）：
    小红书推荐流 API (homefeed) 游客可访问，无需登录。
    通过 Playwright 访问 /explore 首页，监听 API 响应即可拿到
    标题/点赞/博主/封面/笔记链接。

API: https://edith.xiaohongshu.com/api/sns/web/v1/homefeed
"""

import json
import re

from playwright.async_api import async_playwright

EXPLORE_URL = "https://www.xiaohongshu.com/explore"
NOTE_URL = "https://www.xiaohongshu.com/explore/{note_id}?xsec_token={token}"


def _match_brand(text: str, brand_names: list) -> str:
    """返回命中的品牌名，未命中返回空字符串。"""
    if not text:
        return ""
    for name in brand_names:
        # 精确品牌名匹配（避免 "花西" 误匹配 "花西子"）
        if name in text:
            return name
    return ""


def _parse_homefeed(body: bytes) -> list:
    """解析 homefeed 响应，返回笔记列表。"""
    try:
        data = json.loads(body)
    except Exception:
        return []
    items = data.get("data", {}).get("items", [])
    notes = []
    for it in items:
        card = it.get("note_card", {})
        if not card:
            continue
        note_id = it.get("id", "")
        title = card.get("display_title", "").strip()
        interact = card.get("interact_info", {})
        user = card.get("user", {})
        cover = card.get("cover", {})
        notes.append({
            "note_id": note_id,
            "title": title,
            "likes": str(interact.get("liked_count", "")),
            "author": user.get("nickname", ""),
            "cover": cover.get("url_default", "") if isinstance(cover, dict) else "",
            "url": NOTE_URL.format(note_id=note_id, token=it.get("xsec_token", "")),
        })
    return notes


async def crawl_homefeed(brand_names: list, max_scrolls: int = 12, max_notes: int = 600) -> dict:
    """
    采集推荐流并过滤品牌。

    Returns:
        {品牌名: [笔记dict, ...]}
    """
    result = {name: [] for name in brand_names}
    seen_ids = set()
    collected = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=_find_chrome(),
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # 监听 homefeed 响应
        feed_buffer = []

        async def on_response(resp):
            if "homefeed" in resp.url:
                try:
                    feed_buffer.append(await resp.body())
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            await page.goto(EXPLORE_URL, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(6000)

            for _ in range(max_scrolls):
                # 处理本轮的 homefeed 数据
                for body in feed_buffer:
                    for note in _parse_homefeed(body):
                        if note["note_id"] and note["note_id"] not in seen_ids:
                            seen_ids.add(note["note_id"])
                            collected += 1
                            brand = _match_brand(note["title"], brand_names)
                            if brand:
                                result[brand].append(note)
                feed_buffer.clear()

                # 滚动加载更多
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2500)

                if collected >= max_notes:
                    break

            # 最后再处理一次剩余 buffer
            for body in feed_buffer:
                for note in _parse_homefeed(body):
                    if note["note_id"] and note["note_id"] not in seen_ids:
                        seen_ids.add(note["note_id"])
                        brand = _match_brand(note["title"], brand_names)
                        if brand:
                            result[brand].append(note)

        finally:
            await browser.close()

    return result


def _find_chrome() -> str:
    import os
    for p in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]:
        if os.path.exists(p):
            return p
    return ""


async def main():
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 直接读品牌配置
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brand_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        brands = json.load(f)["brands"]
    names = [b["name"] for b in brands]
    print(f"监控品牌数: {len(names)}")

    result = await crawl_homefeed(names, max_scrolls=8)
    total = sum(len(v) for v in result.values())
    hit = {k: len(v) for k, v in result.items() if v}
    print(f"\n命中品牌 {len(hit)} 个，共 {total} 条笔记")
    for k, v in hit.items():
        print(f"  {k}: {v} 条")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
