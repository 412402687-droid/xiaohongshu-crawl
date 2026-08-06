"""
小红书品牌官方账号监控

策略: 直接访问品牌主页/帖子详情页 → 比搜索页反爬更弱
"""

import asyncio
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


# ── 配置 ──────────────────────────────────────────────
PROFILE_URL = "https://www.xiaohongshu.com/user/profile/{user_id}"
POST_URL = "https://www.xiaohongshu.com/explore/{note_id}"
XHS_COOKIE_ENV = "XHS_COOKIE"


def load_accounts() -> list:
    """加载品牌账号配置。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand_xhs_accounts.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("accounts", [])
    return []


def load_cookies_from_env() -> list:
    raw = os.getenv(XHS_COOKIE_ENV, "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def summarize_post(text: str, max_len: int = 50) -> str:
    """简单摘要：取第一句或前 max_len 字符。"""
    if not text:
        return ""
    text = text.strip()
    # 取第一个句子
    for sep in ["。", "！", "？", "\n", "！", "?"]:
        idx = text.find(sep)
        if idx > 0:
            return text[:idx + 1].strip()
    return text[:max_len] + "…" if len(text) > max_len else text


def extract_tags(text: str) -> list:
    """提取 #话题 标签。"""
    return re.findall(r"#(\S+)", text)


async def crawl_brand_accounts(max_posts_per_brand: int = 5) -> list:
    """
    访问每个品牌的官方账号主页，提取最新帖子。
    """
    if async_playwright is None:
        raise RuntimeError("playwright 未安装")

    accounts = load_accounts()
    available = [a for a in accounts if a.get("user_id")]
    if not available:
        print("[XHS品牌监控] 没有有效的 user_id，请先填充 brand_xhs_accounts.json")
        return []

    cookies = load_cookies_from_env()
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        if cookies:
            await context.add_cookies(cookies)

        for acc in available:
            brand = acc["brand"]
            uid = acc["user_id"]
            page = await context.new_page()
            posts = []

            try:
                proUrl = PROFILE_URL.format(user_id=uid)
                print(f"  [{brand}] 访问主页: {proUrl}")
                await page.goto(proUrl, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(4000)

                # 提取笔记链接
                note_links = await page.query_selector_all("a[href*='/explore/']")
                seen = set()
                for link in note_links[:max_posts_per_brand * 2]:
                    href = await link.get_attribute("href")
                    if not href or href in seen:
                        continue
                    seen.add(href)

                    title_el = await link.query_selector("[class*='title'], .note-text, span")
                    title = (await title_el.inner_text()).strip() if title_el else ""

                    full_url = f"https://www.xiaohongshu.com{href}" if href.startswith("/") else href
                    posts.append({
                        "brand": brand,
                        "handle": acc.get("handle", ""),
                        "title": title[:200],
                        "url": full_url,
                        "summary": summarize_post(title),
                        "tags": extract_tags(title),
                    })
                    if len(posts) >= max_posts_per_brand:
                        break

                results.extend(posts)
                print(f"  [{brand}] 获取 {len(posts)} 篇笔记")

            except Exception as exc:
                print(f"  [{brand}] 抓取失败: {exc}")
            finally:
                await page.close()
                await asyncio.sleep(2)

        await browser.close()

    return results


async def crawl_post_details(posts: list) -> list:
    """逐篇访问笔记详情页，获取正文+图片+海报。"""
    if not posts:
        return []

    cookies = load_cookies_from_env()
    enriched = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        if cookies:
            await context.add_cookies(cookies)

        for post in posts[:20]:  # 限制详情抓取数量
            page = await context.new_page()
            try:
                await page.goto(post["url"], wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)

                # 正文
                body_el = await page.query_selector("[class*='content'], [class*='desc'], .note-text")
                body = (await body_el.inner_text()).strip() if body_el else ""

                # 图片
                img_els = await page.query_selector_all("img[src*='sns-img']")
                images = []
                for ie in img_els[:3]:
                    src = await ie.get_attribute("src")
                    if src:
                        images.append(src)

                # 主题概括
                theme = summarize_post(body or post.get("title", ""), max_len=60)

                enriched.append({
                    **post,
                    "body": body[:500],
                    "images": images,
                    "theme": theme,
                    "tags": extract_tags(body + post.get("title", "")),
                })

            except Exception as exc:
                enriched.append(post)
            finally:
                await page.close()
                await asyncio.sleep(2)

        await browser.close()

    return enriched


# ── 命令行 ────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "detail":
        test = [{"url": "https://www.xiaohongshu.com/explore/test"}]
        result = asyncio.run(crawl_post_details(test))
    else:
        result = asyncio.run(crawl_brand_accounts(max_posts_per_brand=3))
    print(json.dumps(result, ensure_ascii=False, indent=2))
