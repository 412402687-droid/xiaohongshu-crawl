"""饰品参考品牌站生成器（参考 a-scene-showroom 风格）"""

import json
import os

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "饰品参考站.html")

# 从图2截图中录入的15个饰品参考品牌
BRANDS = [
    {"name": "sapir_bachar", "handle": "sapir_bachar", "instagram": "https://www.instagram.com/sapir_bachar/",
     "desc_zh": "极简以色列首饰，关注身体轮廓和尺寸感",
     "desc_en": "Sapir Bachar 于 2019 年成立。设计师 Calvin Klein 从 MK 离职后创立，关注传统首饰抽象与极简美学。",
     "market": "北美市场", "level": "小众设计师", "category": "银饰", "style": "新锐极简",
     "location": "Phoenix, 以色列", "website": "https://www.sapirbachar.com/"},
    {"name": "ikaandoni", "handle": "ikaandoni", "instagram": "https://www.instagram.com/ikaandoni/",
     "desc_zh": "中性的、尖锐的、雕塑感配饰",
     "desc_en": "Ikaandoni 探索中性美学的雕塑感首饰。",
     "market": "欧洲市场", "level": "主理品牌", "category": "银饰", "style": "金属风",
     "location": "欧洲", "website": ""},
    {"name": "alafromthebronx", "handle": "alafromthebronx", "instagram": "https://www.instagram.com/alafromthebronx/",
     "desc_zh": "中古、童趣、小巧", "desc_en": "Inspired by vintage and playfulness.",
     "market": "北美市场", "level": "小众设计师", "category": "银饰", "style": "北美复古",
     "location": "Bronx, NY", "website": ""},
    {"name": "calmoonjewelry", "handle": "calmoonjewelry", "instagram": "https://www.instagram.com/calmoonjewelry/",
     "desc_zh": "极简、小巧、精致", "desc_en": "Minimalist fine jewelry with delicate details.",
     "market": "北美市场", "level": "小众设计师", "category": "银饰", "style": "新锐极简",
     "location": "美国", "website": ""},
    {"name": "wera", "handle": "wera", "instagram": "https://www.instagram.com/wera/",
     "desc_zh": "现代设计师品牌，有参考价值", "desc_en": "Contemporary designer jewelry with artistic vision.",
     "market": "欧洲市场", "level": "主理品牌", "category": "银饰", "style": "金属风",
     "location": "欧洲", "website": ""},
    {"name": "completedworks", "handle": "completedworks", "instagram": "https://www.instagram.com/completedworks/",
     "desc_zh": "陈列值得参考、当代经典", "desc_en": "Completedworks — craft-driven fine jewelry from London.",
     "market": "欧洲市场", "level": "主理品牌", "category": "银饰", "style": "金属风",
     "location": "London, UK", "website": "https://completedworks.com/"},
    {"name": "sarahmacheledwin", "handle": "sarahmacheledwin", "instagram": "https://www.instagram.com/sarahmacheledwin/",
     "desc_zh": "手工艺、设计师品牌", "desc_en": "Handcrafted fine jewelry with personal storytelling.",
     "market": "欧洲市场", "level": "小众设计师", "category": "银饰", "style": "新锐极简",
     "location": "Europe", "website": ""},
    {"name": "antiquejewel", "handle": "antiquejewel", "instagram": "https://www.instagram.com/antiquejewel/",
     "desc_zh": "古董配饰、年代感", "desc_en": "Antique and vintage jewelry with historical charm.",
     "market": "欧洲市场", "level": "小众设计师", "category": "珐琅首饰", "style": "金属风",
     "location": "Europe", "website": ""},
    {"name": "b3theAshesJP", "handle": "b3theAshesJP", "instagram": "https://www.instagram.com/b3theAshesJP/",
     "desc_zh": "古董配饰、东方元素", "desc_en": "Antique jewelry with Japanese and Eastern influences.",
     "market": "亚洲市场", "level": "主理品牌", "category": "珐琅首饰", "style": "东方艺术家",
     "location": "Japan", "website": ""},
    {"name": "nesztold_jewelry", "handle": "nesztold_jewelry", "instagram": "https://www.instagram.com/nesztold_jewelry/",
     "desc_zh": "古董配饰、复古韵味", "desc_en": "Vintage-inspired jewelry with timeless aesthetics.",
     "market": "欧洲市场", "level": "小众设计师", "category": "银饰", "style": "金属风",
     "location": "Europe", "website": ""},
    {"name": "adleruzo", "handle": "adleruzo", "instagram": "https://www.instagram.com/adleruzo/",
     "desc_zh": "现代设计师、有参考价值", "desc_en": "Contemporary jewelry with architectural design.",
     "market": "北美市场", "level": "小众设计师", "category": "银饰", "style": "新锐极简",
     "location": "USA", "website": ""},
    {"name": "littlebuzzardjewel", "handle": "littlebuzzardjewel", "instagram": "https://www.instagram.com/littlebuzzardjewel/",
     "desc_zh": "多巴胺配色、活泼童趣", "desc_en": "Colorful dopamine jewelry with playful energy.",
     "market": "北美市场", "level": "小众设计师", "category": "银饰", "style": "多巴胺",
     "location": "USA", "website": ""},
    {"name": "aglajajaaa", "handle": "aglajajaaa", "instagram": "https://www.instagram.com/aglajajaaa/",
     "desc_zh": "多巴胺配色、糖果色", "desc_en": "Sweet colorful jewelry with candy aesthetics.",
     "market": "亚洲市场", "level": "小众设计师", "category": "银饰", "style": "多巴胺",
     "location": "Asia", "website": ""},
    {"name": "birthdaybue_offici", "handle": "birthdaybue_offici", "instagram": "https://www.instagram.com/birthdaybue_offici/",
     "desc_zh": "小家碧玉、东方美学", "desc_en": "Delicate Asian-inspired fine jewelry.",
     "market": "亚洲市场", "level": "小众设计师", "category": "珐琅首饰", "style": "中式摩登",
     "location": "Asia", "website": ""},
    {"name": "nalissatradingnl", "handle": "nalissatradingnl", "instagram": "https://www.instagram.com/nalissatradingnl/",
     "desc_zh": "复古选品、有参考价值", "desc_en": "Curated vintage jewelry and accessories.",
     "market": "欧洲市场", "level": "选品品牌", "category": "银饰", "style": "金属风",
     "location": "Netherlands", "website": ""},
]

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>饰品参考 · a-scene showroom</title>
<style>
:root {
  --bg: #fafaf8;
  --card: #fff;
  --text: #1a1a1a;
  --muted: #888;
  --border: #e8e6e1;
  --accent: #d4380d;
  --radius: 14px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: var(--bg); color: var(--text); line-height: 1.55; font-size: 14px; }
.layout { display: flex; min-height: 100vh; }
aside { width: 220px; border-right: 1px solid var(--border); padding: 28px 20px; background: #fff; flex-shrink: 0; }
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
.results { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; cursor: pointer; transition: 0.2s; }
.card:hover { transform: translateY(-3px); box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
.cover { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 32px; font-weight: 700; letter-spacing: 1px; }
.card-body { padding: 14px 16px; }
.card-name { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.card-handle { font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.card-desc { font-size: 12px; color: #555; min-height: 36px; line-height: 1.5; }
.card-tags { display: flex; gap: 4px; margin-top: 10px; flex-wrap: wrap; }
.card-tag { font-size: 10px; padding: 2px 8px; border-radius: 8px; background: #f4f1ec; color: var(--muted); }
.count { font-size: 12px; color: var(--muted); margin-bottom: 20px; }
/* Modal */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 100; }
.modal-mask.open { display: flex; }
.modal { background: #fff; border-radius: 16px; max-width: 1000px; width: 92%; max-height: 88vh; display: flex; overflow: hidden; position: relative; }
.modal-close { position: absolute; top: 14px; right: 14px; width: 32px; height: 32px; border-radius: 50%; background: rgba(0,0,0,0.05); border: none; cursor: pointer; font-size: 18px; z-index: 2; }
.modal-img { width: 50%; aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 48px; font-weight: 700; }
.modal-info { width: 50%; padding: 36px 32px; overflow-y: auto; }
.modal-handle { font-size: 11px; color: var(--muted); letter-spacing: 1px; margin-bottom: 4px; }
.modal-name { font-size: 30px; font-weight: 700; margin-bottom: 16px; }
.modal-desc { font-size: 13px; line-height: 1.7; color: #333; margin-bottom: 14px; }
.modal-desc-en { font-size: 12px; color: var(--muted); font-style: italic; line-height: 1.6; margin-bottom: 24px; }
.modal-table { width: 100%; border-collapse: collapse; margin-bottom: 28px; }
.modal-table td { padding: 8px 0; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
.modal-table td:first-child { color: var(--muted); width: 90px; }
.modal-cta { display: flex; gap: 10px; }
.cta-btn { flex: 1; padding: 10px 14px; border-radius: 22px; font-size: 13px; font-weight: 600; text-decoration: none; text-align: center; transition: 0.2s; border: 1px solid var(--border); color: var(--text); background: #fff; }
.cta-btn:hover { background: var(--text); color: #fff; border-color: var(--text); }
.cta-btn.ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: #fff; border: none; }
.cta-btn.ig:hover { opacity: 0.85; }
.cta-btn.xhs { background: #ff2442; color: #fff; border: none; }
.cta-btn.xhs:hover { opacity: 0.85; }
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
    <div class="subtitle">饰品参考 · __COUNT__ 个品牌</div>
    <div class="search-box"><input type="text" id="search" placeholder="搜索品牌"></div>
    <div class="filter" data-filter="market"><div class="filter-label">市场</div><div class="tag-list" id="tags-market"></div></div>
    <div class="filter" data-filter="level"><div class="filter-label">级别</div><div class="tag-list" id="tags-level"></div></div>
    <div class="filter" data-filter="category"><div class="filter-label">品类</div><div class="tag-list" id="tags-category"></div></div>
    <div class="filter" data-filter="style"><div class="filter-label">风格</div><div class="tag-list" id="tags-style"></div></div>
  </aside>
  <main>
    <div class="count" id="count">__COUNT__ RESULTS</div>
    <div class="results" id="results"></div>
  </main>
</div>
<div class="modal-mask" id="modal">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-img" id="m-img"></div>
    <div class="modal-info">
      <div class="modal-handle" id="m-handle"></div>
      <div class="modal-name" id="m-name"></div>
      <div class="modal-desc" id="m-desc"></div>
      <div class="modal-desc-en" id="m-desc-en"></div>
      <table class="modal-table">
        <tr><td>市场</td><td id="m-market"></td></tr>
        <tr><td>级别</td><td id="m-level"></td></tr>
        <tr><td>品类</td><td id="m-category"></td></tr>
        <tr><td>风格</td><td id="m-style"></td></tr>
        <tr><td>地理</td><td id="m-location"></td></tr>
      </table>
      <div class="modal-cta">
        <a class="cta-btn" id="m-website" href="#" target="_blank">品牌官网</a>
        <a class="cta-btn ig" id="m-ig" href="#" target="_blank">Instagram</a>
        <a class="cta-btn xhs" id="m-xhs" href="#" target="_blank">小红书</a>
      </div>
    </div>
  </div>
</div>
<script>
const BRANDS = __DATA__;
const COLORS = ['#c8a47e','#7a8b6f','#a8806b','#8a7e6e','#6b7a8b','#a89580','#9b8b6e','#b89a7a','#7c8a76','#a49080','#8a7c70','#b09a82','#978670','#a88770','#8e7d68'];
const filters = { market: 'all', level: 'all', category: 'all', style: 'all' };

function uniq(field) { return [...new Set(BRANDS.map(b => b[field]))]; }

function colorFor(name) {
  let h = 0; for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return COLORS[h % COLORS.length];
}

function renderTags() {
  for (const key of Object.keys(filters)) {
    const el = document.getElementById('tags-' + key);
    const vals = ['全部', ...uniq(key)];
    el.innerHTML = vals.map(v => `<div class="tag ${filters[key] === (v === '全部' ? 'all' : v) ? 'active' : ''}" data-key="${key}" data-val="${v === '全部' ? 'all' : v}">${v}</div>`).join('');
    el.querySelectorAll('.tag').forEach(t => {
      t.addEventListener('click', () => {
        filters[t.dataset.key] = t.dataset.val;
        renderTags(); renderResults();
      });
    });
  }
}

function renderResults() {
  const kw = document.getElementById('search').value.toLowerCase();
  const list = BRANDS.filter(b => {
    if (filters.market !== 'all' && b.market !== filters.market) return false;
    if (filters.level !== 'all' && b.level !== filters.level) return false;
    if (filters.category !== 'all' && b.category !== filters.category) return false;
    if (filters.style !== 'all' && b.style !== filters.style) return false;
    if (kw && !b.name.toLowerCase().includes(kw) && !b.handle.toLowerCase().includes(kw) && !b.desc_zh.toLowerCase().includes(kw)) return false;
    return true;
  });
  document.getElementById('count').textContent = `${list.length} RESULTS`;
  document.getElementById('results').innerHTML = list.map(b => `
    <div class="card" onclick="openModal('${b.handle}')">
      <div class="cover" style="background:${colorFor(b.handle)}">${b.name.toUpperCase()}</div>
      <div class="card-body">
        <div class="card-name">${b.name}</div>
        <div class="card-handle">@${b.handle}</div>
        <div class="card-desc">${b.desc_zh}</div>
        <div class="card-tags">
          <span class="card-tag">${b.market}</span>
          <span class="card-tag">${b.level}</span>
          <span class="card-tag">${b.style}</span>
        </div>
      </div>
    </div>
  `).join('') || '<div style="color:#999;grid-column:1/-1;text-align:center;padding:60px">没有匹配的品牌</div>';
}

function openModal(handle) {
  const b = BRANDS.find(x => x.handle === handle);
  if (!b) return;
  const color = colorFor(b.handle);
  document.getElementById('m-img').style.background = color;
  document.getElementById('m-img').textContent = b.name.toUpperCase();
  document.getElementById('m-handle').textContent = '@' + b.handle;
  document.getElementById('m-name').textContent = b.name;
  document.getElementById('m-desc').textContent = b.desc_zh;
  document.getElementById('m-desc-en').textContent = b.desc_en;
  document.getElementById('m-market').textContent = b.market;
  document.getElementById('m-level').textContent = b.level;
  document.getElementById('m-category').textContent = b.category;
  document.getElementById('m-style').textContent = b.style;
  document.getElementById('m-location').textContent = b.location;
  const w = b.website || ('https://www.' + b.handle + '.com/');
  document.getElementById('m-website').href = w;
  document.getElementById('m-ig').href = b.instagram;
  document.getElementById('m-xhs').href = 'https://www.xiaohongshu.com/search_result?keyword=' + encodeURIComponent(b.name);
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
    html = HTML.replace("__DATA__", json.dumps(BRANDS, ensure_ascii=False))
    html = html.replace("__COUNT__", str(len(BRANDS)))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUTPUT}")
    print(f"品牌数: {len(BRANDS)}")


if __name__ == "__main__":
    main()
