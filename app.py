import os
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

# ---- LINE Webhook 路由 ----
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    print("Received webhook:", body)
    
    # 你也可以加上事件處理邏輯，例如解析 JSON，處理訊息等

    return "OK", 200

# ---- Railway 健康檢查 ----
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200

# ---- 啟動 Flask ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
