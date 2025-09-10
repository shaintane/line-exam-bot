# app.py (LINE Bot 最小可運行 + 回覆訊息)

import os
import base64
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage

# ====== 初始化 credentials.json (延後才用到 Google API) ======
if "CREDENTIALS_JSON_B64" in os.environ:
    try:
        with open("credentials.json", "wb") as f:
            f.write(base64.b64decode(os.environ["CREDENTIALS_JSON_B64"]))
        print("✅ credentials.json 已寫入")
    except Exception as e:
        print(f"[WARNING] 無法寫入 credentials.json: {e}")

# ====== LINE Bot API ======
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("❌ 缺少 CHANNEL_ACCESS_TOKEN")
if not CHANNEL_SECRET:
    raise RuntimeError("❌ 缺少 CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

# ====== Flask App ======
app = Flask(__name__)

# ====== Webhook ======
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    print("[Webhook] raw body:", body)

    payload = request.get_json(silent=True) or {}
    events = payload.get("events", [])

    for event in events:
        try:
            if event.get("type") == "message" and event["message"]["type"] == "text":
                user_id = event["source"]["userId"]
                user_text = event["message"]["text"]
                print(f"[Webhook] 收到訊息: {user_text} from {user_id}")

                # 回覆訊息
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=f"你剛剛說了：{user_text}")
                )
        except Exception as e:
            print(f"[Webhook] error: {e}")

    return "OK", 200

# ====== 健康檢查 ======
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    print("[Healthz] checked")
    return jsonify({"status": "ok", "version": version}), 200

# ====== 本地啟動 ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT"
