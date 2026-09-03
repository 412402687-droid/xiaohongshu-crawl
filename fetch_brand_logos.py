"""批量提取品牌官网 logo，生成 brand_images.json（封面图）"""

import json
import os
import re
import urllib.request
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))

# 品牌 → 官网域名候选（已知 + 合理猜测）
BRAND_DOMAINS = {
    "花西子": ["www.huaxizi.cn", "www.florasis.com"],
    "完美日记": ["www.perfectdiary.com", "perfectdiary.com.cn"],
    "橘朵": ["www.judydoll.com", "judydoll.com"],
    "彩棠": ["www.timage.cn", "timage.com"],
    "毛戈平": ["www.mgpin.com", "mgpin.com"],
    "玛丽黛佳": ["www.mariedalgar.com", "mariedalgar.com"],
    "优衣库": ["www.uniqlo.cn", "www.uniqlo.com"],
    "ZARA": ["www.zara.cn", "www.zara.com"],
    "蕉内": ["www.bananain.com", "bananain.com"],
    "太平鸟": ["www.peacebird.com.cn", "peacebird.com"],
    "MLBK": ["www.mlb-korea.com", "mlbk.com"],
    "蔻驰": ["www.coach.com", "china.coach.com"],
    "小CK": ["www.charleskeith.com", "charleskeith.com.cn"],
    "古良吉吉": ["www.guliangjiji.com", "guliangjiji.com"],
    "崧SONG": ["www.song.cn", "songbag.com"],
    "Songmont山下有松": ["www.songmont.com", "songmont.cn"],
    "雅诗兰黛": ["www.esteelauder.com.cn", "www.esteelauder.com"],
    "珀莱雅": ["www.proya.com", "proya.com"],
    "薇诺娜": ["www.winona.cn", "winona.com.cn"],
    "瑷尔博士": ["www.dralva.com", "dralva.com"],
    "可复美": ["www.kefumei.com", "kefumei.cn"],
    "兰蔻": ["www.lancome.com.cn", "www.lancome.com"],
    "LV": ["www.louisvuitton.cn", "www.louisvuitton.com"],
    "香奈儿": ["www.chanel.cn", "www.chanel.com"],
    "迪奥": ["www.dior.cn", "www.dior.com"],
    "古驰": ["www.gucci.cn", "www.gucci.com"],
    "Tiffany & Co.": ["www.tiffany.cn", "www.tiffany.com"],
    "喜茶": ["www.heytea.com", "heytea.com"],
    "霸王茶姬": ["www.chagee.com", "chagee.cn"],
    "茉莉奶白": ["www.mollywhite.com", "molinaibai.com"],
    "观夏": ["www.tosummer.com", "tosummer.com"],
    "闻献": ["www.documents-sh.com", "documents.com"],
    "大人糖": ["www.darentang.com", "darentang.cn"],
    "雏菊的天空": ["www.daisysky.com", "chujudetiankong.com"],
    "欧舒丹": ["www.loccitane.cn", "www.loccitane.com"],
    "野兽派": ["www.thebeast.cn", "thebeast.com"],
    "Bollycon": ["www.bollycon.com", "bollycon.com"],
    "moody": ["www.moody.com", "moodylens.com"],
    "CoFancy可糖": ["www.cofancy.com", "cofancy.com"],
    "可啦啦Kilala": ["www.kilala.com", "kekilala.com"],
    "Le Labo": ["www.lelabofragrances.com", "lelabo.com"],
    "BYREDO": ["www.byredo.com", "byredo.com"],
    "Diptyque": ["www.diptyque-paris.com", "diptyque.com"],
    "Jo Malone": ["www.jomalone.com.cn", "www.jomalone.com"],
    "馥郁满铺": ["www.fuyumanpu.com", "fuyumanpu.com"],
    "伊索 Aesop": ["www.aesop.com", "aesop.com.cn"],
}

LOGO_PATTERNS = [
    r'<img[^>]+(?:logo|brand)[^>]+src=["\']([^"\']+)["\']',
    r'<link[^>]+rel=["\'](?:apple-touch-icon|icon|shortcut icon)["\'][^>]+href=["\']([^"\']+)["\']',
    r'<img[^>]+class=["\'][^"\']*(?:logo|brand)[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
]


def fetch_logo(domain):
    """访问官网，提取 logo 图片 URL"""
    for scheme in ["https", "http"]:
        url = f"{scheme}://{domain}/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
            for pat in LOGO_PATTERNS:
                m = re.search(pat, html, re.IGNORECASE)
                if m:
                    src = m.group(1)
                    if src.startswith("//"):
                        src = scheme + ":" + src
                    elif src.startswith("/"):
                        src = f"{scheme}://{domain}{src}"
                    return src
        except Exception:
            continue
    return ""


def main():
    result = {}
    for brand, domains in BRAND_DOMAINS.items():
        logo = ""
        for d in domains:
            logo = fetch_logo(d)
            if logo:
                break
        result[brand] = logo or ""
        status = "✓" if logo else "✗"
        print(f"  {status} {brand}: {logo[:60] if logo else '未找到'}")

    out = os.path.join(BASE, "brand_images.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    found = sum(1 for v in result.values() if v)
    print(f"\n共 {len(result)} 个品牌，找到 {found} 个 logo")
    print(f"已保存 {out}")


if __name__ == "__main__":
    main()
