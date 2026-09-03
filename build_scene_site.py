"""品牌展厅站生成器 — 46品牌，a-scene-showroom 格式（图1+图3）

数据源：brand_config.json（46品牌）+ brand_xhs_accounts.json + brand_links.json
首页：左侧品类筛选 + 右侧品牌卡片网格（图1格式）
详情：点击品牌弹 modal（图3格式：大图+品牌信息+平台按钮）
"""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "品牌展厅站.html")


def load_brands():
    with open(os.path.join(BASE, "brand_config.json"), "r", encoding="utf-8") as f:
        return json.load(f)["brands"]


def load_xhs_ids():
    result = {}
    p = os.path.join(BASE, "brand_xhs_accounts.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            for acc in json.load(f).get("accounts", []):
                if acc.get("user_id"):
                    result[acc["brand"]] = acc["user_id"]
    return result


def load_custom_links():
    p = os.path.join(BASE, "brand_links.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build():
    brands = load_brands()
    xhs_ids = load_xhs_ids()
    custom = load_custom_links()
    data = []
    for b in brands:
        name = b["name"]
        c = custom.get(name, {})
        xhs = c.get("xiaohongshu", "")
        if not xhs and name in xhs_ids:
            xhs = f"https://www.xiaohongshu.com/user/profile/{xhs_ids[name]}"
        if not xhs:
            xhs = f"https://www.xiaohongshu.com/search_result?keyword={name}"
        douyin = c.get("douyin", "")
        if not douyin:
            douyin = f"https://www.douyin.com/search/{name}"
        data.append({
            "name": name,
            "category": b["industry"],   # 品类
            "style": b["style"],         # 调性/描述
            "xhs": xhs,
            "douyin": douyin,
        })
    return data


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>品牌展厅 · SHOWROOM</title>
<style>
:root {
  --bg: #fafaf8; --card: #fff; --text: #1a1a1a; --muted: #888;
  --border: #e8e6e1; --accent: #d4380d; --radius: 14px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: var(--bg); color: var(--text); line-height: 1.55; font-size: 14px; }
.layout { display: flex; min-height: 100vh; }
aside { width: 210px; border-right: 1px solid var(--border); padding: 28px 20px; background: #fff; flex-shrink: 0; }
.title { font-size: 20px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 4px; }
.subtitle { font-size: 12px; color: var(--muted); margin-bottom: 24px; }
.search-box { position: relative; margin-bottom: 24px; }
.search-box input { width: 100%; padding: 8px 12px 8px 32px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; outline: none; background: var(--bg); }
.search-box::before { content: "🔍"; position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 12px; opacity: 0.5; }
.filter { margin-bottom: 18px; }
.filter-label { font-size: 11px; color: var(--muted); font-weight: 600; margin-bottom: 8px; letter-spacing: 0.5px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 4px 11px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border); background: #fff; color: var(--muted); cursor: pointer; transition: 0.2s; }
.tag:hover { border-color: var(--accent); color: var(--accent); }
.tag.active { background: var(--accent); color: #fff; border-color: var(--accent); }
main { flex: 1; padding: 32px 40px; }
.count { font-size: 12px; color: var(--muted); margin-bottom: 20px; }
.results { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 20px; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; cursor: pointer; transition: 0.2s; }
.card:hover { transform: translateY(-3px); box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
.cover { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 30px; font-weight: 700; letter-spacing: 1px; }
.card-body { padding: 14px 16px; }
.card-name { font-size: 15px; font-weight: 700; margin-bottom: 6px; }
.card-desc { font-size: 12px; color: #555; min-height: 34px; line-height: 1.5; }
.card-tags { display: flex; gap: 4px; margin-top: 10px; flex-wrap: wrap; }
.card-tag { font-size: 10px; padding: 2px 8px; border-radius: 8px; background: #f4f1ec; color: var(--muted); }
/* Modal */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 100; }
.modal-mask.open { display: flex; }
.modal { background: #fff; border-radius: 16px; max-width: 1000px; width: 92%; max-height: 88vh; display: flex; overflow: hidden; position: relative; }
.modal-close { position: absolute; top: 14px; right: 14px; width: 32px; height: 32px; border-radius: 50%; background: rgba(0,0,0,0.05); border: none; cursor: pointer; font-size: 18px; z-index: 2; }
.modal-img { width: 50%; aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 48px; font-weight: 700; }
.modal-info { width: 50%; padding: 40px 32px; overflow-y: auto; }
.modal-name { font-size: 30px; font-weight: 700; margin-bottom: 6px; }
.modal-cat { display: inline-block; font-size: 11px; color: var(--accent); border: 1px solid var(--accent); padding: 2px 10px; border-radius: 12px; margin-bottom: 16px; }
.modal-desc { font-size: 14px; line-height: 1.8; color: #333; margin-bottom: 26px; }
.modal-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
.modal-table td { padding: 10px 0; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
.modal-table td:first-child { color: var(--muted); width: 80px; }
.modal-cta { display: flex; gap: 10px; }
.cta-btn { flex: 1; padding: 11px 14px; border-radius: 22px; font-size: 13px; font-weight: 600; text-decoration: none; text-align: center; transition: 0.2s; border: 1px solid var(--border); color: var(--text); background: #fff; }
.cta-btn:hover { background: var(--text); color: #fff; border-color: var(--text); }
.cta-btn.xhs { background: #ff2442; color: #fff; border: none; }
.cta-btn.xhs:hover { opacity: 0.85; }
.cta-btn.dy { background: #161823; color: #fff; border: none; }
.cta-btn.dy:hover { opacity: 0.85; }
@media (max-width: 900px) {
  .layout { flex-direction: column; }
  aside { width: 100%; border-right: none; border-bottom: 1px solid var(--border); }
  .modal { flex-direction: column; max-height: 92vh; }
  .modal-img { width: 100%; aspect-ratio: 4/3; }
  .modal-info { width: 100%; }
}
</style>
</head>
<body>
<div class="layout">
  <aside>
    <div class="title">SHOWROOM</div>
    <div class="subtitle">品牌展厅 · __COUNT__ 个品牌</div>
    <div class="search-box"><input type="text" id="search" placeholder="搜索品牌"></div>
    <div class="filter"><div class="filter-label">品类</div><div class="tag-list" id="tags"></div></div>
  </aside>
  <main>
    <div class="count" id="count"></div>
    <div class="results" id="results"></div>
  </main>
</div>
<div class="modal-mask" id="modal">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-img" id="m-img"></div>
    <div class="modal-info">
      <div class="modal-name" id="m-name"></div>
      <span class="modal-cat" id="m-cat"></span>
      <div class="modal-desc" id="m-desc"></div>
      <table class="modal-table">
        <tr><td>品类</td><td id="m-cat2"></td></tr>
        <tr><td>调性</td><td id="m-style"></td></tr>
      </table>
      <div class="modal-cta">
        <a class="cta-btn xhs" id="m-xhs" href="#" target="_blank">小红书</a>
        <a class="cta-btn dy" id="m-dy" href="#" target="_blank">抖音</a>
      </div>
    </div>
  </div>
</div>
<script>
const BRANDS = __DATA__;
const COLORS = ['#c8a47e','#7a8b6f','#a8806b','#8a7e6e','#6b7a8b','#a89580','#9b8b6e','#b89a7a','#7c8a76','#a49080','#8a7c70','#b09a82','#978670','#a88770','#8e7d68','#c39a7b','#7d8b80','#a98a72'];
let activeCat = '全部';

function uniq(f) { return [...new Set(BRANDS.map(b => b[f]))]; }
function colorFor(name) { let h=0; for (let i=0;i<name.length;i++) h=(h*31+name.charCodeAt(i))>>>0; return COLORS[h%COLORS.length]; }

function renderTags() {
  const el = document.getElementById('tags');
  const cats = ['全部', ...uniq('category')];
  el.innerHTML = cats.map(c => `<div class="tag ${activeCat===c?'active':''}" data-c="${c}">${c}</div>`).join('');
  el.querySelectorAll('.tag').forEach(t => t.addEventListener('click', () => { activeCat = t.dataset.c; renderTags(); renderResults(); }));
}

function renderResults() {
  const kw = document.getElementById('search').value.toLowerCase();
  const list = BRANDS.filter(b => {
    if (activeCat !== '全部' && b.category !== activeCat) return false;
    if (kw && !b.name.toLowerCase().includes(kw) && !b.style.toLowerCase().includes(kw)) return false;
    return true;
  });
  document.getElementById('count').textContent = `${list.length} RESULTS`;
  document.getElementById('results').innerHTML = list.map(b => `
    <div class="card" onclick="openModal('${b.name}')">
      <div class="cover" style="background:${colorFor(b.name)}">${b.name}</div>
      <div class="card-body">
        <div class="card-name">${b.name}</div>
        <div class="card-desc">${b.style}</div>
        <div class="card-tags"><span class="card-tag">${b.category}</span></div>
      </div>
    </div>
  `).join('') || '<div style="color:#999;grid-column:1/-1;text-align:center;padding:60px">没有匹配的品牌</div>';
}

function openModal(name) {
  const b = BRANDS.find(x => x.name === name);
  if (!b) return;
  const c = colorFor(b.name);
  document.getElementById('m-img').style.background = c;
  document.getElementById('m-img').textContent = b.name;
  document.getElementById('m-name').textContent = b.name;
  document.getElementById('m-cat').textContent = b.category;
  document.getElementById('m-cat2').textContent = b.category;
  document.getElementById('m-style').textContent = b.style;
  document.getElementById('m-desc').textContent = b.style;
  document.getElementById('m-xhs').href = b.xhs;
  document.getElementById('m-dy').href = b.douyin;
  document.getElementById('modal').classList.add('open');
}

function closeModal() { document.getElementById('modal').classList.remove('open'); }
document.getElementById('modal').addEventListener('click', e => { if (e.target.id === 'modal') closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
document.getElementById('search').addEventListener('input', renderResults);
renderTags(); renderResults();
</script>
</body>
</html>
"""


def main():
    data = build()
    html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__COUNT__", str(len(data)))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUTPUT}")
    print(f"品牌数: {len(data)}")
    cats = {}
    for d in data:
        cats[d["category"]] = cats.get(d["category"], 0) + 1
    print("品类分布:", cats)


if __name__ == "__main__":
    main()
