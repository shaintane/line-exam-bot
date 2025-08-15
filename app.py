import os
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

from handlers import handle_event  # 引入你寫的事件處理邏輯

app = Flask(__name__)

# === LINE Bot 憑證設定 ===
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# === Webhook 入口 ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    print("Received webhook:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your CHANNEL_SECRET.")
        abort(400)

    return "OK", 200

# === 訊息事件處理 ===
@handler.add(MessageEvent)
def handle_message(event):
    handle_event(
        event=event,
        line_bot_api=line_bot_api,
        client=None,  # 尚未使用
        user_sessions={},  # 預設為空字典
        registration_buffer={}  # 預設為空字典
    )

# === 健康檢查用 (供 Railway 判斷服務狀態) ===
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200

# === 啟動 Flask 應用 ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
