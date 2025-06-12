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

# 初始化記憶結構
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
        from handlers import process_message
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 僅在 DEBUG_MODE == "true" 時顯示初始回覆
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="✅ 收到訊息，系統正在處理中...")
            )

        # 處理邏輯訊息
        process_message(event, line_bot_api, client, user_sessions, registration_buffer)

    except Exception as e:
        # 發生錯誤時仍需回覆
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 系統錯誤：{str(e)}")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
