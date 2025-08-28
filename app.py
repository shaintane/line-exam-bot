import os
from flask import Flask, request, jsonify
from handlers import handle_event

app = Flask(__name__)

# === LINE Webhook 路由 ===
@app.route("/callback", methods=["POST"])
def callback():
    try:
        events = request.json.get("events", [])
        for event in events:
            handle_event(event, None, None, user_sessions={}, registration_buffer={})
    except Exception as e:
        print(f"Webhook error: {e}")
    return "OK", 200

# === 健康檢查用 ===
@app.route("/healthz", methods=["GET"])
def healthz():
    version = os.getenv("APP_VERSION", "dev-1")
    return jsonify({"status": "ok", "version": version}), 200

# ✅ 不要有 app.run()
