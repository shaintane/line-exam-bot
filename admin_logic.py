from linebot.models import TextSendMessage
import json
import os
from datetime import datetime

WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"

# 通用 I/O 處理
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def handle_admin_commands(user_input, user_id, line_bot_api):
    whitelist = load_json(WHITELIST_FILE)
    pending = load_json(PENDING_FILE)

    # ✅ 登入 admin
    if user_input.lower() == "admin":
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

    # ✅ 查看 pending 列表
    if user_input == "show pending" and whitelist.get(user_id, {}).get("role") == "admin":
        if not pending:
            line_bot_api.push_message(user_id, TextSendMessage(text="📭 尚無 pending 使用者。"))
        else:
            entries = [f"{v['name']} ({k}) {v['school']}" for k, v in pending.items()]
            line_bot_api.push_message(user_id, TextSendMessage(text="📋 Pending 名單：\n" + "\n".join(entries)))
        return True

    # ✅ 查看 whitelist 列表
    if user_input == "show whitelist" and whitelist.get(user_id, {}).get("role") == "admin":
        if not whitelist:
            line_bot_api.push_message(user_id, TextSendMessage(text="📭 尚無白名單成員。"))
        else:
            entries = [f"{v['name']} ({k}) {v['school']}" for k, v in whitelist.items() if v.get("role") != "admin"]
            line_bot_api.push_message(user_id, TextSendMessage(text="📋 白名單名單：\n" + "\n".join(entries)))
        return True

    # ✅ Approve
    if user_input.startswith("approve") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, target_id = user_input.split()
            if target_id in pending:
                whitelist[target_id] = pending[target_id]
                del pending[target_id]
                save_json(WHITELIST_FILE, whitelist)
                save_json(PENDING_FILE, pending)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已成功核准 {target_id}。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無 {target_id} 於 pending 中。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請使用格式：approve LINE_ID"))
        return True

    # ✅ Input
    if user_input.startswith("input") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, school, name, student_id, start_date, end_date, target_id = user_input.split()
            whitelist[target_id] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
                "line_id": target_id,
                "role": "intern"
            }
            save_json(WHITELIST_FILE, whitelist)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已手動新增 {name} 至白名單。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請使用格式：input 學校 姓名 學號 起始 結束 LINE_ID"))
        return True

    # ✅ Delet
    if user_input.startswith("delet") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, identifier = user_input.split()
            target = None
            for k, v in whitelist.items():
                if identifier == k or identifier == v.get("student_id"):
                    target = k
                    break
            if target:
                del whitelist[target]
                save_json(WHITELIST_FILE, whitelist)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🗑️ 已移除 {identifier}。"))
            else:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 找不到對應使用者。"))
        except:
            line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請使用格式：delet 學號 或 delet LINE_ID"))
        return True

    # 🧪 測試：模擬 shaintane 加入
    if user_input == "測試" and user_id == "shaintane":
        pending[user_id] = {
            "school": "測試大學",
            "name": "測試者",
            "student_id": "T001",
            "start_date": datetime.today().strftime("%Y-%m-%d"),
            "end_date": "2025-12-31",
            "line_id": user_id,
            "role": "intern"
        }
        save_json(PENDING_FILE, pending)
        line_bot_api.push_message(user_id, TextSendMessage(text="🧪 模擬測試者資料已寫入 pending_register.json。"))
        return True

    return False
