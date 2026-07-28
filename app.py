import logging
import os

from dotenv import load_dotenv
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

user_sessions = {}
registration_buffer = {}


@app.get("/")
def health_check():
    return {"status": "ok", "service": "line-exam-bot"}, 200


@app.post("/callback")
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400)

    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    from handlers import process_message

    try:
        process_message(
            event,
            line_bot_api,
            openai_client,
            user_sessions,
            registration_buffer,
        )
    except Exception:
        LOGGER.exception("Unhandled error while processing LINE message")
        try:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text="⚠️ 系統暫時無法處理，請稍後再試。"),
            )
        except Exception:
            LOGGER.exception("Failed to send fallback error message")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
