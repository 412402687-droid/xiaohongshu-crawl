"""dump 飞书 app_token 下的所有表，找饰品参考表"""
import os
import json
import requests

app_id = os.getenv("FEISHU_APP_ID", "")
app_secret = os.getenv("FEISHU_APP_SECRET", "")
app_token = os.getenv("FEISHU_APP_TOKEN", "")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret}, timeout=15,
)
token = r.json()["tenant_access_token"]

# 列出该 app_token 下所有表
r = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables?page_size=100",
    headers={"Authorization": f"Bearer {token}"}, timeout=15,
)
tables = r.json().get("data", {}).get("items", [])
print(f"该 app_token 下有 {len(tables)} 张表:")
for t in tables:
    print(f"  table_id={t.get('table_id')}  name={t.get('name')}")

# 列出所有表的记录数
print("\n各表记录数:")
for t in tables:
    tid = t.get("table_id")
    name = t.get("name")
    r2 = requests.get(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=1",
        headers={"Authorization": f"Bearer {token}"}, timeout=15,
    )
    total = r2.json().get("data", {}).get("total", 0)
    print(f"  {name} ({tid}): {total} 条")
