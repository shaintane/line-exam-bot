from linebot.models import TextSendMessage
import json
import os

WHITELIST_FILE = "whitelist.json"

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return {}
    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def handle_admin_commands(user_input, user_id, line_bot_api, event):
    whitelist = load_whitelist()

    if user_input.lower().startswith("admin"):
        print("🛠 觸發 admin 指令")
        if user_id not in whitelist:
            print("➕ 新增管理者進入白名單")
            whitelist[user_id] = {
                "role": "admin",
                "name": "管理者",
                "student_id": "admin",
                "school": "System",
                "start_date": "2025-01-01",
                "end_date": "2099-12-31",
                "line_id": user_id
            }
            save_whitelist(whitelist)
        else:
            print("✅ 已存在 whitelist")
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text="✅ 管理者登入成功。"))
        except Exception as e:
            print(f"❌ 傳送回覆失敗：{str(e)}")
        return True

    if user_input.startswith("input") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, school, name, student_id, start_date, end_date = user_input.split()
            whitelist[student_id] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
                "line_id": student_id,
                "role": "intern"
            }
            save_whitelist(whitelist)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已手動新增 {name} 進入白名單。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 輸入格式錯誤，請使用 input 學校 姓名 學號 起始日 結束日"))
        return True

    if user_input.startswith("delet") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, student_id = user_input.split()
            if student_id in whitelist:
                del whitelist[student_id]
                save_whitelist(whitelist)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🗑️ 已移除 {student_id}。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無 {student_id} 於白名單內。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入格式：delet 學號"))
        return True

    return False
