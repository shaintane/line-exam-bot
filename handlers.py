from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic

import requests
import json

registration_buffer = {}

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

    # 註冊流程起始
    if user_input == "註冊":
        registration_buffer[user_id] = {"step": "ask_name"}
        print(f"[註冊流程] 建立暫存資料: {registration_buffer}")
        line_bot_api.push_message(user_id, TextSendMessage(text="請輸入您的【姓名】："))
        print(f"[Push] 發送註冊訊息給 {user_id}")
        return
