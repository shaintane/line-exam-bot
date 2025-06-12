from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from linebot.models import TextSendMessage
import json
import os
from datetime import datetime

WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"
DEVELOPER_LINE_ID = "shaintane"

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return {}
    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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
    today = datetime.today().strftime("%Y-%m-%d")

    # 測試者 shaintane 可直接繞過
    if user_id == DEVELOPER_LINE_ID:
        if user_input == "測試":
            pending = load_pending()
            if user_id not in pending:
                pending[user_id] = {
                    "school": "",
                    "name": "",
                    "student_id": "",
                    "start_date": "",
                    "end_date": "",
                    "line_id": user_id
                }
                save_pending(pending)
            line_bot_api.push_message(user_id, TextSendMessage(
                text="👋 歡迎加入！請輸入：學校 姓名 學號 起始日 結束日（格式如：OO大學 王小明 123456 2025/06/01 2025/07/31）"))
            return

    # 管理者邏輯
    if handle_admin_commands(user_input, user_id, line_bot_api):
        return

    # 白名單驗證
    whitelist = load_whitelist()
    user_data = whitelist.get(user_id)
    if not user_data:
        pending = load_pending()
        if user_id not in pending:
            pending[user_id] = {
                "school": "",
                "name": "",
                "student_id": "",
                "start_date": "",
                "end_date": "",
                "line_id": user_id
            }
            save_pending(pending)
            line_bot_api.push_message(user_id, TextSendMessage(
                text="👋 歡迎使用本系統，尚未完成註冊。\n請輸入：學校 姓名 學號 起始日 結束日（例如：OO大學 王小明 123456 2025/06/01 2025/07/31）"))
        elif all(pending[user_id].values()):
            line_bot_api.push_message(user_id, TextSendMessage(
                text="✅ 資料已提交，請等待管理者審核。"))
        else:
            try:
                school, name, student_id, start_date, end_date = user_input.split()
                pending[user_id] = {
                    "school": school,
                    "name": name,
                    "student_id": student_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "line_id": user_id
                }
                save_pending(pending)
                line_bot_api.push_message(user_id, TextSendMessage(
                    text="📩 資料已接收，請等待管理者審核通過後使用系統。"))
            except:
                line_bot_api.push_message(user_id, TextSendMessage(
                    text="⚠️ 請依正確格式輸入：學校 姓名 學號 起始日 結束日（例如：OO大學 王小明 123456 2025/06/01 2025/07/31）"))
        return

    # 權限期間驗證
    start = user_data.get("start_date")
    end = user_data.get("end_date")
    if not (start <= today <= end):
        line_bot_api.push_message(user_id, TextSendMessage(
            text="⛔ 尚未被審核或使用權限已過期。\n請確認是否已填寫資料並等待管理者審核通過。"))
        return

    # 通過白名單後啟用測驗流程
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
