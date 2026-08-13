"""通过飞书 API 打印表格名称（表格名非敏感，可定位表格）"""
import os
import requests

app_id = os.getenv("FEISHU_APP_ID", "")
app_secret = os.getenv("FEISHU_APP_SECRET", "")
app_token = os.getenv("FEISHU_APP_TOKEN", "")

# 1. 获取 tenant_access_token
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
    timeout=15,
)
token = r.json().get("tenant_access_token", "")
print("TOKEN_OK:", bool(token))

# 2. 列出 app_token 下的所有表
r = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables?page_size=100",
    headers={"Authorization": f"Bearer {token}"},
    timeout=15,
)
data = r.json()
print("列出表 code:", data.get("code"))
for item in data.get("data", {}).get("items", []):
    print(f"表名: {item.get('name')} | table_id: {item.get('table_id')}")
