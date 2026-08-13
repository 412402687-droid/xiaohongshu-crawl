"""查询飞书表格的笔记链接字段，打印样本供诊断"""
import os
import requests

app_id = os.getenv("FEISHU_APP_ID", "")
app_secret = os.getenv("FEISHU_APP_SECRET", "")
app_token = os.getenv("FEISHU_APP_TOKEN", "")
table_id = os.getenv("FEISHU_TABLE_ID", "")

# 1. token
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
    timeout=15,
)
token = r.json()["tenant_access_token"]

# 2. 查询记录
records = []
page_token = None
while True:
    params = {"page_size": 500}
    if page_token:
        params["page_token"] = page_token
    r = requests.get(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=15,
    )
    data = r.json().get("data", {})
    records.extend(data.get("items", []))
    if not data.get("has_more"):
        break
    page_token = data.get("page_token")

print(f"总记录数: {len(records)}")

# 3. 统计链接字段
from collections import Counter
link_samples = Counter()
for rec in records:
    link = rec.get("fields", {}).get("笔记链接", "")
    if isinstance(link, dict):
        link = link.get("link", "")
    if not link:
        link_samples["(空)"] += 1
    elif "xiaohongshu" in link:
        link_samples["小红书链接"] += 1
    elif "cbndata" in link:
        link_samples["CBNData搜索链接"] += 1
    elif "djyanbao" in link:
        link_samples["洞见研报链接"] += 1
    elif "iimedia" in link:
        link_samples["艾媒网链接"] += 1
    else:
        link_samples["其他"] += 1

print("链接类型统计:")
for k, v in link_samples.items():
    print(f"  {k}: {v} 条")

# 4. 打印样本
print("\n样本（前10条）:")
for rec in records[:10]:
    link = rec.get("fields", {}).get("笔记链接", "")
    if isinstance(link, dict):
        link = link.get("link", "")
    brand = rec.get("fields", {}).get("品牌", "")
    title = rec.get("fields", {}).get("笔记标题", "")
    print(f"  [{brand}] {title[:20]} -> {str(link)[:60]}")
