# app.py (最小可運行版)

import os
import base64
from flask import Flask, request, jsonify

# ✅ 建立 credentials.json (延後才用到)
if "CREDENTIALS_JSON_B64" in os.environ:
    try:
        with open("credentials.json", "wb") as f:
            f.write(base64.b64decode(os.environ["CREDENTIALS_JSON_B64"]))
        print("✅ credentials.json 已寫入")
    except Exception as e:
        print(f"[WARNING] 無法寫入 credentials.json: {e}")

app = Flask(__name__)

# ====== Webhook 測試入口 ======
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    print("[Webhook] raw body:", body[:200])  # 只印前 200 chars，避免太長
    return "OK", 200

# ====== 健康檢查 ======
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    print("[Healthz] checked")
    return jsonify({"status": "ok", "version": version}), 200

# ====== 本地啟動 ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Flask app 啟動於 port {port}")
    app.run(host="0.0.0.0", port=port)
