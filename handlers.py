from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from linebot.models import TextSendMessage
import json
import os

PENDING_FILE = "pending_register.json"

def load_pending():
    if not os.path.exists(PENDING_FILE):
        return {}
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_pending(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # ✅ 管理者指令優先處理
    if handle_admin_commands(user_input, user_id, line_bot_api, event):
        return

    # ✅ 使用者加入後填寫基本資料格式（姓名/學號/學校/起始日/結束日）
    if "/" in user_input and user_input.count("/") == 4:
        try:
            name, student_id, school, start_date, end_date = user_input.split("/")
            pending = load_pending()
            pending[user_id] = {
                "name": name.strip(),
                "student_id": student_id.strip(),
                "school": school.strip(),
                "start_date": start_date.strip(),
                "end_date": end_date.strip(),
                "line_id": user_id
            }
            save_pending(pending)
            line_bot_api.push_message(user_id, TextSendMessage(
                text="📥 資料已送出，請等待管理者審核。審核通過後可進入測驗系統。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(
                text="⚠️ 請輸入格式：姓名/學號/學校/起始日/結束日\n範例：王大明/112345/國立醫學大學/2025-06-01/2025-08-31"))
        return

    # ✅ 若無需進行註冊流程，則處理測驗主流程
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
