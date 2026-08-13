"""清空飞书表格中的小红书链接（打开空白）"""
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

# 2. 查询所有记录
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

# 3. 筛选小红书链接的记录
targets = []
for rec in records:
    link = rec.get("fields", {}).get("笔记链接", "")
    if isinstance(link, dict):
        link = link.get("link", "")
    if link and "xiaohongshu" in str(link):
        targets.append(rec["record_id"])

print(f"小红书链接记录数: {len(targets)}")

if not targets:
    print("无需清理")
else:
    # 4. 批量清空（每次最多 500 条）
    cleared = 0
    for i in range(0, len(targets), 500):
        batch = targets[i : i + 500]
        payload = {
            "records": [
                {"record_id": rid, "fields": {"笔记链接": ""}}
                for rid in batch
            ]
        }
        r = requests.patch(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        code = r.json().get("code")
        print(f"  批次 {i // 500 + 1}: code={code}")
        if code == 0:
            cleared += len(batch)

    print(f"成功清空 {cleared} 条小红书链接")
