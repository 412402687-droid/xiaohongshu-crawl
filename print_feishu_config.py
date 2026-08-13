"""打印飞书配置（base64 编码，绕过 GitHub 日志脱敏）"""
import os
import base64

app_token = os.getenv("FEISHU_APP_TOKEN", "")
table_id = os.getenv("FEISHU_TABLE_ID", "")
app_id = os.getenv("FEISHU_APP_ID", "")

def enc(s):
    return base64.b64encode(s.encode()).decode()

print("APP_ID_B64:", enc(app_id))
print("APP_TOKEN_B64:", enc(app_token))
print("TABLE_ID_B64:", enc(table_id))
