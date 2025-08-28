import os
from flask import Flask, request, abort, jsonify
from handlers import handle_event
from linebot import LineBotApi, WebhookHandler

app = Flask(__name__)

# 初始化 LINE Bot SDK（請確認環境變數都已正確設置）
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# 全域變數：記錄使用者註冊流程與狀態
user_sessions = {}
registration_buffer = {}

# === LINE Webhook 路由 ===
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    print("Received webhook:", body)

    try:
        events = request.json.get("events", [])
        for event in events:
            handle_event(
                event,
                line_bot_api=line_bot_api,
                client=None,  # 若你有 Google Sheets client 可改為實例
                user_sessions=user_sessions,
                registration_buffer=registration_buffer
            )
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
