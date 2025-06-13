from linebot.models import TextSendMessage
import json
import os
from datetime import datetime

WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"
DEVELOPER_LINE_ID = "shaintane"

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def handle_admin_commands(user_input, user_id, line_bot_api, registration_buffer):
    whitelist = load_json(WHITELIST_FILE)
    pending = load_json(PENDING_FILE)

    # ✅ 測試指令：模擬新使用者
    if user_input == "測試" and user_id == DEVELOPER_LINE_ID:
        if user_id in whitelist:
            del whitelist[user_id]
            save_json(WHITELIST_FILE, whitelist)
        if user_id in pending:
            del pending[user_id]
            save_json(PENDING_FILE, pending)
        registration_buffer[user_id] = "awaiting_info"
        line_bot_api.push_message(user_id, TextSendMessage(
            text="👋 歡迎使用本系統！請輸入以下格式完成註冊：\n學校 姓名 學號 起始日 結束日"
        ))
        return True

    # ✅ 新使用者流程（尚未在白名單中）
    if user_id not in whitelist:
        if registration_buffer.get(user_id) != "awaiting_info":
            registration_buffer[user_id] = "awaiting_info"
            line_bot_api.push_message(user_id, TextSendMessage(
                text="👋 歡迎使用本系統！請輸入以下格式完成註冊：\n學校 姓名 學號 起始日 結束日"
            ))
            return True
        else:
            parts = user_input.strip().split()
            if len(parts) == 5:
                school, name, student_id, start_date, end_date = parts
                pending[user_id] = {
                    "school": school,
                    "name": name,
                    "student_id": student_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "line_id": user_id
                }
                save_json(PENDING_FILE, pending)
                del registration_buffer[user_id]
                line_bot_api.push_message(user_id, TextSendMessage(
                    text="📝 資料已送出，請等待管理者審核。"
                ))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(
                    text="⚠️ 格式錯誤，請使用：學校 姓名 學號 起始日 結束日"
                ))
            return True

    # ✅ 管理者登入
    if user_input.lower().startswith("admin"):
        if user_id not in whitelist:
            whitelist[user_id] = {
                "role": "admin",
                "name": "管理者",
                "student_id": "admin",
                "school": "System",
                "start_date": "2025-01-01",
                "end_date": "2099-12-31",
                "line_id": user_id
            }
            save_json(WHITELIST_FILE, whitelist)
        line_bot_api.push_message(user_id, TextSendMessage(text="✅ 管理者登入成功。"))
        return True

    # ✅ 手動新增 input
    if user_input.startswith("input") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, school, name, student_id, start_date, end_date, line_id = user_input.split()
            whitelist[line_id] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
                "line_id": line_id,
                "role": "intern"
            }
            save_json(WHITELIST_FILE, whitelist)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已手動新增 {name} 至白名單。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ input 格式錯誤，請使用：input 學校 姓名 學號 起始日 結束日 LINE_ID"))
        return True

    # ✅ 移除 delet
    if user_input.startswith("delet") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, key = user_input.split()
            found = False
            for k in list(whitelist.keys()):
                if key in [k, whitelist[k].get("student_id", "")]:
                    del whitelist[k]
                    found = True
            if found:
                save_json(WHITELIST_FILE, whitelist)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🗑️ 已移除 {key}。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無 {key} 於白名單內。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入格式：delet 學號 or delet LINE_ID"))
        return True

    # ✅ 顯示 pending 名單
    if user_input == "show pending" and whitelist.get(user_id, {}).get("role") == "admin":
        if pending:
            lines = [f"{v['name']} ({v['student_id']}) - {k}" for k, v in pending.items()]
            msg = "📋 待審核名單：\n" + "\n".join(lines)
        else:
            msg = "📋 無待審核資料。"
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
        return True

    # ✅ 顯示 whitelist 名單
    if user_input == "show whitelist" and whitelist.get(user_id, {}).get("role") == "admin":
        if whitelist:
            lines = [f"{v['name']} ({v['student_id']}) - {k}" for k, v in whitelist.items() if v.get("role") != "admin"]
            msg = "✅ 白名單使用者：\n" + "\n".join(lines)
        else:
            msg = "📋 白名單目前為空。"
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
        return True

    # ✅ 審核 approve LINE_ID
    if user_input.startswith("approve") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, approve_id = user_input.split()
            if approve_id in pending:
                whitelist[approve_id] = pending[approve_id]
                whitelist[approve_id]["role"] = "intern"
                save_json(WHITELIST_FILE, whitelist)
                del pending[approve_id]
                save_json(PENDING_FILE, pending)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已核准 {approve_id} 加入白名單。"))
                line_bot_api.push_message(approve_id, TextSendMessage(text="🎉 你的註冊已審核通過，可開始使用測驗功能！"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 此 LINE ID 不在待審核名單中。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入格式：approve LINE_ID"))
        return True

    return False
