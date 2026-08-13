"""打印飞书配置和表格链接（仅用于诊断）"""
import os

app_token = os.getenv("FEISHU_APP_TOKEN", "")
table_id = os.getenv("FEISHU_TABLE_ID", "")
app_id = os.getenv("FEISHU_APP_ID", "")

print("=" * 60)
print("飞书配置信息")
print("=" * 60)
print(f"APP_ID: {app_id}")
print(f"APP_TOKEN: {app_token}")
print(f"TABLE_ID: {table_id}")
print()
print("多维表格链接（在浏览器打开）:")
print(f"https://bytedance.feishu.cn/base/{app_token}?table={table_id}")
print(f"https://www.feishu.cn/base/{app_token}?table={table_id}")
print("=" * 60)
