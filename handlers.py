from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic

# 暫存註冊資料流程狀態用
registration_buffer = {}

def handle_event(event, line_bot_api, client, user_sessions):
    if event.type != "message" or event.message.type != "text":
        return

    user_input = event.message.text.strip()
    user_id = event.source.user_id

    # ✅ 管理員指令（白名單 / 註冊 / 查詢等）
    if user_input.startswith(("input", "approve", "delet", "show")):
        handle_admin_commands(user_input, user_id, line_bot_api, client, registration_buffer)
        return

    # ✅ 教學任務系統（上傳作業、進度追蹤、照片留言等）
    if any(keyword in user_input for keyword in ["作業", "回應", "進度", "照片", "留言", "提醒"]):
        handle_edu_logic(user_input, user_id, line_bot_api, client)
        return

    # ✅ 國考 AI 輔助練習模組（如疫、血、微等）
    handle_exam_logic(user_input, user_id, line_bot_api, client, user_sessions, registration_buffer)


    # ✅ 註冊流程起點
    if user_input == "註冊":
        registration_buffer[user_id] = {"step": "ask_name"}
        line_bot_api.push_message(user_id, TextSendMessage("請輸入您的【姓名】："))
        return

    # ✅ 若正在進行註冊流程
    if user_id in registration_buffer:
        result = handle_registration_flow(user_id, user_input, registration_buffer)

        if result["action"] == "ask":
            line_bot_api.push_message(user_id, TextSendMessage(result["message"]))
            return

        elif result["action"] == "done":
            send_to_apps_script(result["data"])  # ← 實作在別處
            line_bot_api.push_message(user_id, TextSendMessage(result["message"]))
            return

        elif result["action"] == "error":
            line_bot_api.push_message(user_id, TextSendMessage(result["message"]))
            return


# ✅ 登記流程邏輯
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
        registration_buffer.pop(user_id)  # 註冊完成

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


# ✅ 將資料送到 Google Sheets（Apps Script Web App）
def send_to_apps_script(data):
    import requests
    import json

    url = "https://script.google.com/macros/s/xxxxxxxxxxxxxxxxxxxxxxxxxx/exec"  # 替換為你的 Web App URL
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ 發送 Google Sheets 寫入失敗: {e}")
