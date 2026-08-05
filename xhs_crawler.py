"""
小红书搜索抓取模块 — 基于 Playwright (增强版)

改进点:
- 启动时先访问首页建立会话，再加载 Cookie
- 添加 WebDriver 隐藏参数绕过检测
- 等待搜索结果容器出现后再提取
- 单步操作加 try/except，单页失败不影响其他品牌
"""

import asyncio
import json
import os
import re
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    async_playwright = None

# ── 常量 ──────────────────────────────────────────────
SEARCH_URL = "https://www.xiaohongshu.com/search_result"
LOGIN_URL = "https://www.xiaohongshu.com"
DEFAULT_TIMEOUT = 20000       # ms
SEARCH_TIMEOUT = 25000        # ms
SCROLL_PAUSE = 2.5            # 每次滚动间隔（秒）
MAX_SCROLL = 6                # 最大滚动次数


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


async def safe_query_all(page, selectors: list, timeout: int = 5000) -> list:
    """尝试多个选择器，返回第一个匹配的元素列表。"""
    for selector in selectors:
        try:
            els = await page.query_selector_all(selector)
            if els:
                return els
        except Exception:
            continue
        await asyncio.sleep(0.3)
    return []


async def crawl_brand(brand_name: str, max_posts: int = 20) -> list:
    """
    搜索指定品牌并返回笔记列表。
    """
    if async_playwright is None:
        raise RuntimeError("playwright 未安装")

    results = []
    cookie_data = load_cookies_from_env()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
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
            timezone_id="Asia/Shanghai",
        )

        # 注入反检测脚本
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);
        """)

        if cookie_data:
            await context.add_cookies(cookie_data)

        page = await context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        try:
            # 第一步：访问首页建立会话（带 cookie）
            print(f"  [{brand_name}] 访问首页建立会话...")
            try:
                await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
            except Exception as exc:
                print(f"  [{brand_name}] 首页访问异常(继续): {exc}")
            await asyncio.sleep(2)

            # 第二步：构造搜索 URL 并访问
            keyword_encoded = brand_name
            search_url = f"{SEARCH_URL}?keyword={keyword_encoded}&source=web_explore_feed&sort=general"
            print(f"  [{brand_name}] 访问搜索页: {search_url}")

            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=SEARCH_TIMEOUT)
            except PlaywrightTimeout:
                print(f"  [{brand_name}] 搜索页加载超时")
                return results
            except Exception as exc:
                print(f"  [{brand_name}] 搜索页访问异常: {exc}")
                return results

            await asyncio.sleep(3)

            # 调试：检测当前页面状态
            try:
                page_url = page.url
                page_title = await page.title()
                print(f"  [{brand_name}] 当前 URL: {page_url}")
                print(f"  [{brand_name}] 页面标题: {page_title}")
            except Exception:
                pass

            # 检测是否被拦截（登录墙/验证码/反爬）
            try:
                body_text = await page.evaluate("document.body.innerText")
                if any(kw in body_text for kw in ["登录", "请先登录", "未登录", "请验证", "验证码", "访问频次"]):
                    print(f"  [{brand_name}] ⚠ 检测到登录/验证墙，Cookie 可能失效")
                    return results
            except Exception:
                pass

            # 调试：截图第一轮前
            debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_screenshots")
            try:
                os.makedirs(debug_dir, exist_ok=True)
                await page.screenshot(path=os.path.join(debug_dir, f"{brand_name}_initial.png"), full_page=False)
            except Exception:
                pass

            # 第三步：滚动加载 + 提取
            scroll_count = 0
            seen_urls = set()
            selectors = [
                "section.note-item",
                "div.note-item",
                "a[href*='/explore/']",
                "a[href*='/search-result/']",
                "div[data-v]",
                "[data-v-]",
                ".feeds-page .note-item",
                ".search-result-card",
                "[class*='note-card']",
                "[class*='NoteCard']",
                "[class*='search'] [class*='card']",
            ]

            while len(results) < max_posts and scroll_count < MAX_SCROLL:
                # 安全查询元素（多选择器回退 + 容错）
                cards = await safe_query_all(page, selectors, timeout=4000)

                if not cards:
                    if scroll_count == 0:
                        print(f"  [{brand_name}] 第 1 轮: 未找到元素，截图已保存到 debug_screenshots/{brand_name}_initial.png")
                        # 抓取页面 HTML 头部用作排查
                        try:
                            html_snippet = await page.evaluate("document.body.outerHTML.substring(0, 500)")
                            print(f"  [{brand_name}] 页面 HTML 头部: {html_snippet[:300]}")
                        except Exception:
                            pass
                    else:
                        print(f"  [{brand_name}] 第 {scroll_count+1} 轮: 未找到元素")
                else:
                    print(f"  [{brand_name}] 第 {scroll_count+1} 轮: 找到 {len(cards)} 个候选元素")

                for card in cards:
                    try:
                        href = await card.get_attribute("href")
                        if not href:
                            continue
                        # 拼接完整 URL
                        full_url = (
                            f"https://www.xiaohongshu.com{href}"
                            if href.startswith("/")
                            else href
                        )
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        # 标题
                        title = ""
                        for ts in ["span.title", ".title", "[class*='title']", "[class*='Title']"]:
                            try:
                                te = await card.query_selector(ts)
                                if te:
                                    title = await te.inner_text()
                                    if title.strip():
                                        break
                            except Exception:
                                continue

                        # 作者
                        author = ""
                        for as_ in [".author .name", ".nickname", "[class*='author'] [class*='name']"]:
                            try:
                                ae = await card.query_selector(as_)
                                if ae:
                                    author = await ae.inner_text()
                                    if author.strip():
                                        break
                            except Exception:
                                continue

                        # 笔记类型
                        is_video = False
                        try:
                            is_video = bool(await card.query_selector("[class*='video'], .play-icon, svg[class*='play']"))
                        except Exception:
                            pass

                        if not title and not author:
                            continue

                        results.append({
                            "title": title.strip(),
                            "url": full_url,
                            "likes": 0,
                            "collects": 0,
                            "comments": 0,
                            "publish_time": "",
                            "author": author.strip(),
                            "note_type": "视频" if is_video else "图文",
                        })

                        if len(results) >= max_posts:
                            break
                    except Exception:
                        continue

                # 滚动加载
                try:
                    await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                except Exception:
                    break
                scroll_count += 1
                await asyncio.sleep(SCROLL_PAUSE)

            results = results[:max_posts]

        except Exception as exc:
            print(f"  [{brand_name}] 抓取过程异常: {exc}")
        finally:
            await browser.close()

    return results


async def crawl_all_brands(brands: list, max_per_brand: int = 20) -> dict:
    """
    批量抓取多个品牌。
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
        await asyncio.sleep(4)
    return all_results


# ── 命令行入口 ────────────────────────────────────────
if __name__ == "__main__":
    test_brand = sys.argv[1] if len(sys.argv) > 1 else "花西子"
    posts = asyncio.run(crawl_brand(test_brand, max_posts=10))
    print(json.dumps(posts, ensure_ascii=False, indent=2))