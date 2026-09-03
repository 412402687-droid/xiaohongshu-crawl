"""用 Playwright 批量提取品牌官网图片并下载到本地（封面图）"""

import json
import os
import re
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "images")

BRAND_DOMAINS = {
    "花西子": ["www.huaxizi.cn", "www.florasis.com"],
    "完美日记": ["www.perfectdiary.com"],
    "橘朵": ["www.judydoll.com"],
    "彩棠": ["www.timage.cn"],
    "毛戈平": ["www.mgpin.com"],
    "玛丽黛佳": ["www.mariedalgar.com"],
    "优衣库": ["www.uniqlo.cn"],
    "ZARA": ["www.zara.cn"],
    "蕉内": ["www.bananain.com"],
    "太平鸟": ["www.peacebird.com.cn"],
    "MLBK": ["www.mlb-korea.com"],
    "蔻驰": ["china.coach.com", "www.coach.com"],
    "小CK": ["www.charleskeith.com.cn", "www.charleskeith.com"],
    "古良吉吉": ["www.guliangjiji.com"],
    "崧SONG": ["www.songmont.com"],
    "Songmont山下有松": ["www.songmont.com"],
    "雅诗兰黛": ["www.esteelauder.com.cn"],
    "珀莱雅": ["www.proya.com"],
    "薇诺娜": ["www.winona.cn"],
    "瑷尔博士": ["www.dralva.com"],
    "可复美": ["www.kefumei.com"],
    "兰蔻": ["www.lancome.com.cn"],
    "LV": ["www.louisvuitton.cn"],
    "香奈儿": ["www.chanel.cn"],
    "迪奥": ["www.dior.cn"],
    "古驰": ["www.gucci.cn"],
    "Tiffany & Co.": ["www.tiffany.cn"],
    "喜茶": ["www.heytea.com"],
    "霸王茶姬": ["www.chagee.com"],
    "茉莉奶白": ["www.moli.com.cn"],
    "观夏": ["www.tosummer.com"],
    "闻献": ["www.documents.com"],
    "大人糖": ["www.darentang.com"],
    "雏菊的天空": ["www.daisysky.com"],
    "欧舒丹": ["www.loccitane.cn"],
    "野兽派": ["www.thebeast.cn"],
    "Bollycon": ["www.bollycon.com"],
    "moody": ["www.moody.com"],
    "CoFancy可糖": ["www.cofancy.com"],
    "可啦啦Kilala": ["www.kilala.com"],
    "Le Labo": ["www.lelabofragrances.com"],
    "BYREDO": ["www.byredo.com"],
    "Diptyque": ["www.diptyque-paris.com"],
    "Jo Malone": ["www.jomalone.com.cn"],
    "馥郁满铺": ["www.fuyumanpu.com"],
    "伊索 Aesop": ["www.aesop.com"],
}


def safe_name(name):
    return re.sub(r'[^\w\u4e00-\u9fff-]', '_', name)


def extract_image(page):
    """从渲染后的页面提取图片 URL（优先级：og:image > logo > 大图）"""
    # og:image
    og = page.evaluate("() => { const m = document.querySelector('meta[property=\"og:image\"]'); return m ? m.content : ''; }")
    if og and 'favicon' not in og.lower() and len(og) > 10:
        return og
    # logo 大图
    logos = page.evaluate("""() => {
        const imgs = [...document.querySelectorAll('img')];
        const candidates = imgs.filter(i => /logo|brand/i.test(i.className + i.src + i.alt) && i.naturalWidth >= 100);
        return candidates.map(i => i.src);
    }""")
    for src in logos:
        if 'blob:' not in src:
            return src
    # 任意大图
    big = page.evaluate("""() => {
        const imgs = [...document.querySelectorAll('img')];
        const c = imgs.filter(i => i.naturalWidth >= 400).slice(0,1);
        return c.map(i => i.src);
    }""")
    if big and 'blob:' not in big[0]:
        return big[0]
    return ""


def download(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.baidu.com/"})
        data = urllib.request.urlopen(req, timeout=15).read()
        if len(data) > 2000:  # 至少 2KB 才算有效图片
            with open(path, "wb") as f:
                f.write(data)
            return True
    except Exception:
        pass
    return False


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    from playwright.sync_api import sync_playwright

    result = {}
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True, executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1400, 'height': 900}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36')

    for brand, domains in BRAND_DOMAINS.items():
        got = False
        for d in domains:
            if got:
                break
            for scheme in ["https", "http"]:
                url = f"{scheme}://{d}/"
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    page.wait_for_timeout(3500)
                    img = extract_image(page)
                    if img:
                        fname = f"{safe_name(brand)}.png"
                        fpath = os.path.join(IMG_DIR, fname)
                        if download(img, fpath):
                            result[brand] = f"images/{fname}"
                            got = True
                            print(f"  ✓ {brand}: {img[:50]} → {fname}")
                            break
                except Exception:
                    continue
        if not got:
            result[brand] = ""
            print(f"  ✗ {brand}: 未获取到")

    browser.close()
    p.stop()

    out = os.path.join(BASE, "brand_images.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    found = sum(1 for v in result.values() if v)
    print(f"\n共 {len(result)} 品牌，获取 {found} 张图")
    print(f"图片目录: {IMG_DIR}")


if __name__ == "__main__":
    main()
