import logging
import os

from dotenv import load_dotenv
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from openai import OpenAI

from database import db, init_database
from messaging import ReplyFirstLineBotApi
import models  # noqa: F401


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

# PostgreSQL 初始化與連線測試
init_database(app)

# 確認資料表存在
with app.app_context():
    db.create_all()
    LOGGER.info(
        "Database tables created or verified successfully."
    )

# LINE Messaging API
base_line_bot_api = LineBotApi(
    os.getenv("CHANNEL_ACCESS_TOKEN")
)
handler = WebhookHandler(
    os.getenv("CHANNEL_SECRET")
)

# OpenAI
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# 暫存中的測驗與註冊狀態
user_sessions = {}
registration_buffer = {}


@app.get("/")
def health_check():
    """Render health check。"""
    return {
        "status": "ok",
        "service": "line-exam-bot",
        "database": "connected",
        "tables": "ready",
        "messaging": "reply-only-diagnostic",
    }, 200


@app.post("/callback")
def callback():
    """LINE webhook endpoint。"""
    signature = request.headers.get(
        "X-Line-Signature"
    )

    if not signature:
        abort(400)

    body = request.get_data(
        as_text=True
    )

    try:
        handler.handle(
            body,
            signature,
        )
    except InvalidSignatureError:
        LOGGER.warning(
            "Invalid LINE webhook signature."
        )
        abort(400)

    return "OK"


@handler.add(
    MessageEvent,
    message=TextMessage,
)
def handle_message(event):
    """
    LINE 文字訊息主要入口。

    每個 webhook event 都建立一個 ReplyFirstLineBotApi。
    第一則回覆使用 reply_message。

    診斷模式下：
    若處理失敗，不再額外使用 push_message 傳 fallback，
    避免 LINE 429 錯誤蓋掉真正的例外訊息。
    """
    from handlers import process_message

    reply_token = getattr(
        event,
        "reply_token",
        None,
    )

    LOGGER.info(
        "LINE message received: "
        "user_id=%s reply_token_present=%s",
        event.source.user_id,
        bool(reply_token),
    )

    event_line_bot_api = ReplyFirstLineBotApi(
        base_api=base_line_bot_api,
        reply_token=reply_token,
    )

    try:
        process_message(
            event,
            event_line_bot_api,
            openai_client,
            user_sessions,
            registration_buffer,
        )

    except Exception:
        # 重要：
        # 診斷階段不再使用 push_message 傳 fallback。
        # 如此才能在 Render Log 直接看到真正錯誤，
        # 不會再被 LINE 的 429 monthly limit 覆蓋。
        LOGGER.exception(
            "Unhandled error while processing LINE message. "
            "No fallback push was sent."
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "8080",
            )
        ),
    )
