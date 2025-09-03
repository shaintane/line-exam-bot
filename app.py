# app.py 最終版
import os
import base64
from flask import Flask, request, jsonify
from linebot import LineBotApi
from handlers import handle_event

# ✅ 若有環境變數，解碼 credentials.json
if "CREDENTIALS_JSON_B64" in os.environ:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(os.environ["CREDENTIALS_JSON_B64"]))

# ====== 基本設定 ======
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("環境變數 CHANNEL_ACCESS_TOKEN 未設定。")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

# 共用（長存於進程）狀態，不要在每次事件重新建立
user_sessions = {}
registration_buffer = {}

app = Flask(__name__)

# ====== Webhook ======
@app.route("/callback", methods=["POST"])
def callback():
    # 1) 讀取原始 body 以利除錯
    body = request.get_data(as_text=True)
    print("[Webhook] raw body:", body)

    # 2) 安全解析 JSON（某些環境 request.json 可能為 None）
    payload = request.get_json(silent=True) or {}
    events = payload.get("events", [])
    print(f"[Webhook] parsed events: {len(events)}")

    # 3) 逐筆處理事件，但務必快速回 200 以避免 LINE 超時
    for event in events:
        try:
            handle_event(
                event=event,
                line_bot_api=line_bot_api,
                client=None,
                user_sessions=user_sessions,
                registration_buffer=registration_buffer,
            )
        except Exception as e:
            # 不讓例外影響整體回應；記錄後續排查
            print(f"[Webhook] handle_event error: {e}")

    # 4) 一律快速回 OK
    return "OK", 200


# ====== 健康檢查（供 Railway / 外部監測） ======
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200


# ====== 本地啟動 ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
