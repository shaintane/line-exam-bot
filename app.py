
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# 初始化用的記憶結構（註冊狀態、題庫記錄）
user_sessions = {}
registration_buffer = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        # 預先快速回應，避免 webhook timeout
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ 收到訊息，系統正在處理中...")
        )

        # 呼叫核心邏輯處理
        from handlers import process_message
        process_message(event, line_bot_api, user_sessions, registration_buffer)

    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 系統錯誤：{str(e)}")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
