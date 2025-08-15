from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic

import requests
import json

# ✅ 暫存註冊用
registration_buffer = {}

# ✅ LINE webhook 事件總入口
def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.type != "message" or event.message.type != "text":
        return

    user_input = event.message.text.strip()
    user_id = event.source.user_id
    print(f"[Webhook] 收到來自 {user_id} 的訊息：{user_input}")

    # ✅ 觸發註冊流程
    if user_input == "註冊":
        registration_buffer[user_id] = {"step": "ask_name"}
        line_bot_api.push_message(user_id, TextSendMessage("請輸入您的【姓名】："))
        return

    # ✅ 註冊流程進行中
    if user_id in registration_buffer:
        result = handle_registration_flow(user_id, user_input, registration_buffer)

        if result["action"] == "ask":
            line_bot_api.push_message(user_id, TextSendMessage(result["message"]))
            return

        elif result["action"] == "done":
            send_to_apps_script(result["data"])
            line_bot_api.push_message(user_id, TextSendMessage(result["message"]))
            return

        elif result["action"] == "error":
            line_bot_api.push_message(user_id, TextSendMessage(result["message"]))
            return

    # ✅ 管理員指令
    if user_input.startswith(("input", "approve", "delet", "show")):
        handle_admin_commands(user_input, user_id, line_bot_api, client, registration_buffer)
        return

    # ✅ 教學任務模組
    if any(keyword in user_input for keyword in ["作業", "回應", "進度", "照片", "留言", "提醒"]):
        handle_edu_logic(user_input, user_id, line_bot_api, client)
        return

    # ✅ 國考練習模組
    handle_exam_logic(user_input, user_id, line_bot_api, client, user_sessions, registration_buffer)


# ✅ 註冊流程步驟管理
def handle_registration_flow(user_id, user_input, registration_buffer):
    current = registration_buffer.get(user_id, {})
    step = current.get("step", "ask_name")

    if step == "ask_name":
        current["name"] = user_input.strip()
        current["step"] = "ask_id"
        registration_buffer[user_id] = current
        return {
            "action": "ask",
            "message": "請輸入您的【學號】："
        }

    elif step == "ask_id":
        current["external_id"] = user_input.strip()
        current["step"] = "ask_role"
        registration_buffer[user_id] = current
        return {
            "action": "ask",
            "message": "請輸入您的【身分】（student / teacher）："
        }

    elif step == "ask_role":
        role = user_input.strip().lower()
        if role not in ["student", "teacher"]:
            return {
                "action": "ask",
                "message": "❗請輸入正確的身分（student 或 teacher）："
            }

        current["role"] = role
        current["userId"] = user_id
        registration_buffer.pop(user_id)

        return {
            "action": "done",
            "message": f"✅ 資料登記完成：\n姓名：{current['name']}\n學號：{current['external_id']}\n身分：{current['role']}",
            "data": {
                "role": current["role"],
                "external_id": current["external_id"],
                "name": current["name"],
                "userId": user_id
            }
        }

    else:
        return {
            "action": "error",
            "message": "❌ 註冊流程出現錯誤，請重新開始。"
        }


# ✅ 寫入 Google Sheets（Apps Script Web App）
def send_to_apps_script(data):
    url = "https://script.google.com/macros/s/🔗你的AppsScript網址/exec"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Google Sheets 寫入失敗：{e}")
