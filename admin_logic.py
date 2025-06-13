import json
from datetime import datetime
from linebot.models import TextSendMessage

WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"
DEVELOPER_ID = "shaintane"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == DEVELOPER_ID

def handle_admin_commands(user_input, user_id, line_bot_api, registration_buffer):
    user_input = user_input.strip()

    # 模擬新使用者進入測試（限開發者）
    if user_input == "測試" and user_id == DEVELOPER_ID:
        welcome = (
            "👋 歡迎加入國考輔導系統！\n"
            "請依下列格式輸入以完成註冊：\n\n"
            "格式：學校 姓名 學號 起始日 結束日\n"
            "範例：國立醫學大學 王小明 123456\n"
            "2025-06-01 2025-09-30"
        )
        line_bot_api.push_message(user_id, TextSendMessage(text=welcome))
        registration_buffer[user_id] = "awaiting_info"
        return True

    # 使用者註冊輸入資訊寫入 pending_register.json
    if user_id in registration_buffer:
        try:
            parts = user_input.strip().split()
            if len(parts) != 5:
                raise ValueError
            school, name, student_id, start_date, end_date = parts
            data = load_json(PENDING_FILE)
            data[user_id] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
                "line_id": user_id
            }
            save_json(PENDING_FILE, data)
            del registration_buffer[user_id]
            line_bot_api.push_message(user_id, TextSendMessage(text="✅ 資料已送出，請等待管理者審核。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入正確格式：學校 姓名 學號 起始日 結束日"))
        return True

    # ✅ admin 功能（開發者）
    if is_admin(user_id):
        parts = user_input.strip().split()

        if user_input.startswith("approve ") and len(parts) == 2:
            target = parts[1]
            pending = load_json(PENDING_FILE)
            key = None
            for k, v in pending.items():
                if v.get("line_id") == target or v.get("student_id") == target:
                    key = k
                    break
            if key:
                entry = pending.pop(key)
                whitelist = load_json(WHITELIST_FILE)
                whitelist[entry["line_id"]] = entry
                save_json(WHITELIST_FILE, whitelist)
                save_json(PENDING_FILE, pending)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已審核 {entry['name']} 成功加入白名單。"))
                line_bot_api.push_message(entry["line_id"], TextSendMessage(text="✅ 你的帳號已成功通過審核，可開始使用測驗系統！"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 查無此學號或 LINE ID，請確認是否正確。"))
            return True

        if user_input.startswith("input ") and len(parts) == 7:
            _, school, name, student_id, start_date, end_date, target_line = parts
            whitelist = load_json(WHITELIST_FILE)
            whitelist[target_line] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
                "line_id": target_line
            }
            save_json(WHITELIST_FILE, whitelist)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已手動新增 {name} 至白名單。"))
            return True

        if user_input.startswith("delet ") and len(parts) == 2:
            target = parts[1]
            data = load_json(WHITELIST_FILE)
            key = None
            for k, v in data.items():
                if v.get("line_id") == target or v.get("student_id") == target:
                    key = k
                    break
            if key:
                removed = data.pop(key)
                save_json(WHITELIST_FILE, data)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🗑️ 已移除 {removed['name']}"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 查無此學號或 LINE ID。"))
            return True

        if user_input == "show whitelist":
            whitelist = load_json(WHITELIST_FILE)
            if not whitelist:
                msg = "📋 目前白名單為空。"
            else:
                msg = "📋 白名單名單：\n" + "\n".join(
                    [f"{v['name']} ({v['student_id']}) {v['start_date']}~{v['end_date']}" for v in whitelist.values()])
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return True

        if user_input == "show pending":
            pending = load_json(PENDING_FILE)
            if not pending:
                msg = "📋 目前無待審核資料。"
            else:
                msg = "🕐 待審核清單：\n" + "\n".join(
                    [f"{v['name']} ({v['student_id']}) {v['start_date']}~{v['end_date']}" for v in pending.values()])
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return True

    return False
