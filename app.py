import os
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

from handlers import handle_event  # 你已經寫好的邏輯

app = Flask(__name__)

# LINE 憑證
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# ---- LINE Webhook 路由 ----
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    print("Received webhook:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200

# ---- 加入 handler 處理訊息事件 ----
@handler.add(MessageEvent)
def handle_message(event):
    # 這裡是傳給你 handlers.py 的邏輯去處理訊息
    handle_event(
        event,
        line_bot_api,
        client=None,
        user_sessions={},
        registration_buffer={}
    )

# ---- Railway 健康檢查 ----
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200

# ---- 啟動 Flask ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
