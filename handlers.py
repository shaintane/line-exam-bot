from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic

import requests
import json

# 暫存註冊資料流程狀態用（如果是 from app.py 傳進來，也會共用）
registration_buffer = {}

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    # ✅ 修正：event 是 dict，不是物件，要用中括號存取
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息：{user_input}，來自 userId：{user_id}")

    # ✅ 註冊流程起點
    if user_input == "註冊":
        registration_buffer[user_id] = {"step": "ask_name"}
        print(f"[註冊流程] 建立暫存資料: {registration_buffer}")
        line_bot_api.push_message(user_id, TextSendMessage("請輸入您的【姓名】："))
        print(f"[Push] 發送註冊訊息給 {user_id}")
        return

    # ✅ 註冊流程中
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


# ✅ 註冊邏輯
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
    url = "https://script.google.com/macros/s/🔗你的AppsScript網址/exec"  # ←請替換為你的網址
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Google Sheets 寫入失敗：{e}")
