"""
品牌导航网站生成器

读取品牌配置 + 平台链接，生成自包含的单页 HTML 导航站。
数据文件 brand_links.json 可手动维护（小红书/抖音链接）。
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "brand_config.json")
XHS_PATH = os.path.join(BASE_DIR, "brand_xhs_accounts.json")
LINKS_PATH = os.path.join(BASE_DIR, "brand_links.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "品牌导航站.html")


def load_brands():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["brands"]


def load_xhs_user_ids():
    """返回 {品牌名: user_id}"""
    result = {}
    if os.path.exists(XHS_PATH):
        with open(XHS_PATH, "r", encoding="utf-8") as f:
            for acc in json.load(f).get("accounts", []):
                if acc.get("user_id"):
                    result[acc["brand"]] = acc["user_id"]
    return result


def load_custom_links():
    """返回 {品牌名: {xiaohongshu, douyin}}"""
    if os.path.exists(LINKS_PATH):
        with open(LINKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_brand_data():
    brands = load_brands()
    xhs_ids = load_xhs_user_ids()
    custom = load_custom_links()

    data = []
    for b in brands:
        name = b["name"]
        c = custom.get(name, {})
        # 小红书链接：优先自定义，其次已验证 user_id，兜底搜索链接
        xhs = c.get("xiaohongshu", "")
        if not xhs and name in xhs_ids:
            xhs = f"https://www.xiaohongshu.com/user/profile/{xhs_ids[name]}"
        if not xhs:
            xhs = f"https://www.xiaohongshu.com/search_result?keyword={name}"
        # 抖音链接：优先自定义，兜底搜索链接
        douyin = c.get("douyin", "")
        if not douyin:
            douyin = f"https://www.douyin.com/search/{name}"

        data.append({
            "name": name,
            "industry": b["industry"],
            "style": b["style"],
            "xiaohongshu": xhs,
            "douyin": douyin,
        })
    return data


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>品牌导航站</title>
<style>
:root {
  --bg: #f7f5f2;
  --card: #ffffff;
  --text: #1a1a1a;
  --muted: #8a8a8a;
  --border: #e8e4df;
  --accent: #d4380d;
  --xhs: #ff2442;
  --douyin: #161823;
  --radius: 16px;
  --shadow: 0 2px 12px rgba(0,0,0,0.05);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
header {
  position: sticky; top: 0; z-index: 10;
  background: rgba(247,245,242,0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  padding: 18px 24px;
}
.header-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.logo { font-size: 22px; font-weight: 700; letter-spacing: 1px; }
.logo span { color: var(--accent); }
.count { color: var(--muted); font-size: 13px; }
.search-box { margin-left: auto; position: relative; }
.search-box input {
  width: 260px; padding: 10px 16px 10px 38px;
  border: 1px solid var(--border); border-radius: 24px;
  font-size: 14px; outline: none; background: #fff; transition: 0.2s;
}
.search-box input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(212,56,13,0.1); }
.search-box::before { content: "🔍"; position: absolute; left: 13px; top: 50%; transform: translateY(-50%); font-size: 14px; opacity: 0.5; }
.tabs {
  max-width: 1200px; margin: 20px auto 0; padding: 0 24px;
  display: flex; gap: 8px; flex-wrap: wrap;
}
.tab {
  padding: 7px 16px; border-radius: 20px; cursor: pointer;
  font-size: 14px; border: 1px solid var(--border);
  background: #fff; color: var(--muted); transition: 0.2s; white-space: nowrap;
}
.tab:hover { border-color: var(--accent); color: var(--accent); }
.tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
main { max-width: 1200px; margin: 20px auto 60px; padding: 0 24px; }
.industry-title { font-size: 18px; font-weight: 700; margin: 28px 0 14px; display: flex; align-items: center; gap: 10px; }
.industry-title .bar { width: 4px; height: 18px; background: var(--accent); border-radius: 2px; }
.industry-title .num { font-size: 13px; color: var(--muted); font-weight: 400; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 18px; box-shadow: var(--shadow);
  transition: 0.2s; display: flex; flex-direction: column; gap: 10px;
}
.card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.08); }
.card .name { font-size: 17px; font-weight: 700; }
.card .style { font-size: 12px; color: var(--muted); min-height: 34px; }
.card .links { display: flex; gap: 8px; margin-top: auto; }
.link-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 10px; border-radius: 10px; font-size: 13px; font-weight: 600;
  text-decoration: none; transition: 0.2s;
}
.link-btn.xhs { background: rgba(255,36,66,0.08); color: var(--xhs); }
.link-btn.xhs:hover { background: var(--xhs); color: #fff; }
.link-btn.douyin { background: rgba(22,24,35,0.06); color: var(--douyin); }
.link-btn.douyin:hover { background: var(--douyin); color: #fff; }
.empty { text-align: center; color: var(--muted); padding: 60px 0; font-size: 15px; }
@media (max-width: 600px) {
  .search-box { width: 100%; margin-left: 0; }
  .search-box input { width: 100%; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="logo">品牌<span>导航</span></div>
    <div class="count" id="count"></div>
    <div class="search-box"><input type="text" id="search" placeholder="搜索品牌名..."></div>
  </div>
</header>
<div class="tabs" id="tabs"></div>
<main id="main"></main>
<script>
const BRANDS = __BRANDS__;

const INDUSTRY_COLORS = {
  "美妆": "#fce4ec", "护肤": "#e8f5e9", "时尚": "#e3f2fd", "包具": "#f3e5f5",
  "奢侈品": "#fff3e0", "茶饮": "#e0f7fa", "香水": "#f9fbe7", "个护": "#fce4ec",
  "生活方式": "#ede7f6", "美瞳": "#e8eaf6"
};

let activeIndustry = "全部";

function renderTabs() {
  const industries = ["全部", ...new Set(BRANDS.map(b => b.industry))];
  const tabsEl = document.getElementById("tabs");
  tabsEl.innerHTML = industries.map(ind =>
    `<div class="tab ${ind === activeIndustry ? 'active' : ''}" data-ind="${ind}">${ind}</div>`
  ).join("");
  tabsEl.querySelectorAll(".tab").forEach(t => {
    t.addEventListener("click", () => {
      activeIndustry = t.dataset.ind;
      renderTabs();
      renderBrands();
    });
  });
}

function renderBrands() {
  const keyword = document.getElementById("search").value.trim().toLowerCase();
  const filtered = BRANDS.filter(b => {
    const matchInd = activeIndustry === "全部" || b.industry === activeIndustry;
    const matchKw = !keyword || b.name.toLowerCase().includes(keyword) || b.style.toLowerCase().includes(keyword);
    return matchInd && matchKw;
  });

  document.getElementById("count").textContent = `${BRANDS.length} 个品牌 · 10 个行业`;

  const main = document.getElementById("main");
  if (!filtered.length) {
    main.innerHTML = '<div class="empty">没有匹配的品牌</div>';
    return;
  }

  // 按行业分组（"全部"时）
  let html = "";
  if (activeIndustry === "全部") {
    const groups = {};
    filtered.forEach(b => { (groups[b.industry] = groups[b.industry] || []).push(b); });
    for (const [ind, list] of Object.entries(groups)) {
      html += `<div class="industry-title"><span class="bar"></span>${ind}<span class="num">${list.length} 个</span></div>`;
      html += `<div class="grid">${list.map(cardHtml).join("")}</div>`;
    }
  } else {
    html = `<div class="grid">${filtered.map(cardHtml).join("")}</div>`;
  }
  main.innerHTML = html;
}

function cardHtml(b) {
  return `<div class="card">
    <div class="name">${b.name}</div>
    <div class="style">${b.style}</div>
    <div class="links">
      <a class="link-btn xhs" href="${b.xiaohongshu}" target="_blank" rel="noopener">小红书</a>
      <a class="link-btn douyin" href="${b.douyin}" target="_blank" rel="noopener">抖音</a>
    </div>
  </div>`;
}

document.getElementById("search").addEventListener("input", renderBrands);
renderTabs();
renderBrands();
</script>
</body>
</html>
"""


def main():
    brands = build_brand_data()
    brands_json = json.dumps(brands, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__BRANDS__", brands_json)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUTPUT_PATH}")
    print(f"品牌数: {len(brands)}")
    # 统计有真实链接的
    real_xhs = sum(1 for b in brands if "user/profile" in b["xiaohongshu"])
    real_dy = sum(1 for b in brands if "douyin.com/search" not in b["douyin"])
    print(f"真实小红书链接: {real_xhs} 个")
    print(f"真实抖音链接: {real_dy} 个")


if __name__ == "__main__":
    main()
