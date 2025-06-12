from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from linebot.models import TextSendMessage
import json
import os
from datetime import datetime

PENDING_FILE = "pending_register.json"
WHITELIST_FILE = "whitelist.json"

def load_json(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # ✅ 管理者指令優先處理
    if handle_admin_commands(user_input, user_id, line_bot_api, event):
        return

    # ✅ 模擬 shaintane 輸入「測試」作為新進學生測試流程
    if user_input == "測試" and user_id == "shaintane":
        pending = load_json(PENDING_FILE)
        pending[user_id] = {
            "name": "測試使用者",
            "student_id": "000000",
            "school": "測試學院",
            "start_date": datetime.today().strftime("%Y-%m-%d"),
            "end_date": "2099-12-31",
            "line_id": user_id
        }
        save_json(PENDING_FILE, pending)
        line_bot_api.push_message(user_id, TextSendMessage(
            text="✅ 已模擬加入 pending 區，等待審核通過。"))
        return

    # ✅ 學生填寫資料（自動寫入 pending 區）
    if "/" in user_input and user_input.count("/") == 4:
        try:
            name, student_id, school, start_date, end_date = user_input.split("/")
            pending = load_json(PENDING_FILE)
            pending[user_id] = {
                "name": name.strip(),
                "student_id": student_id.strip(),
                "school": school.strip(),
                "start_date": start_date.strip(),
                "end_date": end_date.strip(),
                "line_id": user_id
            }
            save_json(PENDING_FILE, pending)
            line_bot_api.push_message(user_id, TextSendMessage(
                text="📥 資料已送出，請等待管理者審核。審核通過後可進入測驗系統。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(
                text="⚠️ 請輸入格式：姓名/學號/學校/起始日/結束日\n範例：王大明/112345/國立醫學大學/2025-06-01/2025-08-31"))
        return

    # ✅ 檢查白名單權限（如不在白名單則不允許進入測驗）
    whitelist = load_json(WHITELIST_FILE)
    today = datetime.today().strftime("%Y-%m-%d")

    if user_id not in whitelist or not (whitelist[user_id]["start_date"] <= today <= whitelist[user_id]["end_date"]):
        line_bot_api.push_message(user_id, TextSendMessage(
            text="⛔️ 尚未被審核或使用權限已過期。\n請確認是否已填寫資料並等待管理者審核通過。"))
        return

    # ✅ 通過白名單則進入測驗主流程
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
