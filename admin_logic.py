from linebot.models import TextSendMessage
import json
import os

WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"
ADMIN_IDS = ["shaintane"]  # 可自行擴充

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def handle_admin_commands(user_input, user_id, line_bot_api, event):
    # ✅ 管理者身份判定
    if user_id in ADMIN_IDS:
        if user_input.startswith("approve "):
            line_id = user_input.replace("approve", "").strip()
            pending = load_json(PENDING_FILE)
            whitelist = load_json(WHITELIST_FILE)
            if line_id in pending:
                whitelist[line_id] = pending[line_id]
                save_json(WHITELIST_FILE, whitelist)
                del pending[line_id]
                save_json(PENDING_FILE, pending)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ {line_id} 審核成功，已加入白名單。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無 LINE ID {line_id} 的暫存資料。"))
            return True

        if user_input.startswith("input "):
            try:
                parts = user_input.replace("input", "").strip().split()
                if len(parts) != 6:
                    raise ValueError
                school, name, student_id, start_date, end_date, line_id = parts
                whitelist = load_json(WHITELIST_FILE)
                whitelist[line_id] = {
                    "school": school,
                    "name": name,
                    "student_id": student_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "line_id": line_id
                }
                save_json(WHITELIST_FILE, whitelist)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 成功加入白名單：{name}"))
            except:
                line_bot_api.push_message(user_id, TextSendMessage(
                    text="⚠️ 請使用格式：input 學校 姓名 學號 起始日 結束日 LINE_ID"))
            return True

        if user_input.startswith("delet "):
            target = user_input.replace("delet", "").strip()
            whitelist = load_json(WHITELIST_FILE)
            found = False
            for k in list(whitelist.keys()):
                if k == target or whitelist[k]["student_id"] == target:
                    del whitelist[k]
                    found = True
            if found:
                save_json(WHITELIST_FILE, whitelist)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🗑️ 已刪除 {target}"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無 {target} 的紀錄"))
            return True

        # 回應成功登入管理者
        line_bot_api.push_message(user_id, TextSendMessage(text="🔐 管理者登入成功，可使用 approve / input / delet 指令。"))
        return True

    return False  # 非管理者則略過
