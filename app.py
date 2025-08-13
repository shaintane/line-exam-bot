# app.py  ← 直接整檔貼上這份也沒關係
import os
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

# ---- 你的既有 webhook/邏輯可以留在這裡（不要刪） ----
# 例如：
# @app.post("/webhook")
# def webhook():
#     return "ok"

# ---- 健康檢查（給 Railway 用）----
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)


