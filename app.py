import os
from flask import Flask, request, abort

app = Flask(__name__)

# --- 你的既有路由（保持不動） ---

# 健康檢查：給 Railway 用
@app.get("/healthz")
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return {"status": "ok", "version": version}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

