import os
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from handlers import handle_event

# 初始化 LINE Bot
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

app = Flask(__name__)

# === LINE Webhook 路由 ===
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    print("Received webhook:", body)
    try:
        events = request.json.get("events", [])
        for event in events:
            handle_event(event, line_bot_api, None, user_sessions={}, registration_buffer={})
    except Exception as e:
        print(f"Webhook error: {e}")
    return "OK", 200

# === 健康檢查用（供 Railway 判斷服務狀態） ===
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200

# === 啟動 Flask 應用 ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
