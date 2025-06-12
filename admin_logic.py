# ✅ admin_logic.py 整合模擬新使用者與正式新使用者流程
from linebot.models import TextSendMessage
import json
import os

WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return {}
    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_pending_register():
    if not os.path.exists(PENDING_FILE):
        return {}
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_pending_register(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def handle_admin_commands(user_input, user_id, line_bot_api, registration_buffer):
    whitelist = load_whitelist()
    pending = load_pending_register()

    # ✅ 測試開發者模擬觸發新使用者進入
    if user_input == "測試" and user_id == "shaintane":
        registration_buffer[user_id] = "awaiting_info"
        line_bot_api.push_message(user_id, TextSendMessage(
            text="🧪 測試模式啟動：請依格式輸入資料\n學校 姓名 學號 起始日 結束日"
        ))
        return True

    # ✅ 指令：顯示 pending 名單
    if user_input == "show pending" and whitelist.get(user_id, {}).get("role") == "admin":
        if pending:
            summary = [f"{v['name']} | {k}" for k, v in pending.items()]
            msg = "📋 尚待審核名單：\n" + "\n".join(summary)
        else:
            msg = "📭 目前無待審核名單。"
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
        return True

    # ✅ 指令：顯示 whitelist
    if user_input == "show whitelist" and whitelist.get(user_id, {}).get("role") == "admin":
        msg = "📋 白名單使用者：\n" + "\n".join([f"{v['name']} | {k}" for k, v in whitelist.items()])
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
        return True

    # ✅ 指令：核准使用者
    if user_input.startswith("approve") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, target_id = user_input.split()
            if target_id in pending:
                whitelist[target_id] = pending[target_id]
                save_whitelist(whitelist)
                del pending[target_id]
                save_pending_register(pending)
                line_bot_api.push_message(user_id, TextSendMessage(text="✅ 已成功審核並加入白名單。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 查無此使用者於待審核區。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入格式：approve LINE_ID"))
        return True

    # ✅ 指令：手動 input
    if user_input.startswith("input") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, school, name, student_id, start, end, target_id = user_input.split()
            whitelist[target_id] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start,
                "end_date": end,
                "line_id": target_id,
                "role": "intern"
            }
            save_whitelist(whitelist)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已手動新增 {name} 至白名單。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請使用格式：input 學校 姓名 學號 起始 結束 LINE_ID"))
        return True

    # ✅ 指令：刪除使用者
    if user_input.startswith("delet") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, target = user_input.split()
            key = target
            for k, v in whitelist.items():
                if k == target or v.get("student_id") == target:
                    key = k
                    break
            if key in whitelist:
                del whitelist[key]
                save_whitelist(whitelist)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🗑️ 已移除 {target}。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無 {target}。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請使用格式：delet LINE_ID 或 delet 學號"))
        return True

    return False
