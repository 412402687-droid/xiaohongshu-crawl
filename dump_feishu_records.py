"""dump 飞书数据表字段+前20条记录"""
import os, json, requests

app_id = os.getenv("FEISHU_APP_ID", "")
app_secret = os.getenv("FEISHU_APP_SECRET", "")
app_token = os.getenv("FEISHU_APP_TOKEN", "")
table_id = os.getenv("FEISHU_TABLE_ID", "")

r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret}, timeout=15)
token = r.json()["tenant_access_token"]

# 字段
r = requests.get(f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
    headers={"Authorization": f"Bearer {token}"}, timeout=15)
fields = {f["field_name"]: f.get("type", 1) for f in r.json().get("data", {}).get("items", [])}
print("字段:", fields)

# 前 20 条
r = requests.get(f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=20",
    headers={"Authorization": f"Bearer {token}"}, timeout=15)
records = r.json().get("data", {}).get("items", [])
print(f"\n前 {len(records)} 条:")
for rec in records:
    f = rec.get("fields", {})
    print("---")
    for k in f:
        v = str(f[k])[:80]
        print(f"  {k}: {v}")
