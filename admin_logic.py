import requests
import datetime
import json
from linebot.models import TextSendMessage

# ✅ 替換成你自己的 Apps Script Web App URL
APPS_SCRIPT_URL = "https://script.google.com/macros/s/你的網址/exec"

# ✅ 寫入 Google Sheets 白名單
def send_to_apps_script(data):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[AppsScript Error] {e}")
        return False


# ✅ Admin 指令處理器
def handle_admin_commands(user_input, user_id, line_bot_api, client, registration_buffer):
    # 載入 JSON 檔案
    try:
        with open("pending_register.json", "r", encoding="utf-8") as f:
            pending_data = json.load(f)
    except:
        pending_data = {}

    try:
        with open("whitelist.json", "r", encoding="utf-8") as f:
            whitelist = json.load(f)
    except:
        whitelist = {}

    # ✅ approve 指令：審核使用者（學號或 userId）
    if user_input.startswith("approve "):
        key = user_input.replace("approve ", "").strip()
        matched = None

        for uid, info in pending_data.items():
            if info.get("external_id") == key or uid == key:
                matched = info
                matched["userId"] = uid
                break

        if not matched:
            line_bot_api.push_message(user_id, TextSendMessage("❌ 查無此使用者於待審清單。"))
            return

        success = send_to_apps_script(matched)

        if success:
            whitelist[matched["userId"]] = matched
            pending_data.pop(matched["userId"])

            with open("pending_register.json", "w", encoding="utf-8") as f:
                json.dump(pending_data, f, ensure_ascii=False, indent=2)

            with open("whitelist.json", "w", encoding="utf-8") as f:
                json.dump(whitelist, f, ensure_ascii=False, indent=2)

            line_bot_api.push_message(user_id, TextSendMessage(
                f"✅ 已通過：{matched['name']}，已寫入白名單與 Google Sheets。"
            ))
        else:
            line_bot_api.push_message(user_id, TextSendMessage("❌ 無法寫入 Google Sheets，請稍後再試。"))
        return

    # ✅ delet 指令：從 pending 或 whitelist 刪除
    elif user_input.startswith("delet "):
        key = user_input.replace("delet ", "").strip()
        deleted_from = None

        for uid, info in list(pending_data.items()):
            if key == uid or key == info.get("external_id"):
                pending_data.pop(uid)
                deleted_from = "pending"
                break

        if not deleted_from:
            for uid, info in list(whitelist.items()):
                if key == uid or key == info.get("external_id"):
                    whitelist.pop(uid)
                    deleted_from = "whitelist"
                    break

        with open("pending_register.json", "w", encoding="utf-8") as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)

        with open("whitelist.json", "w", encoding="utf-8") as f:
            json.dump(whitelist, f, ensure_ascii=False, indent=2)

        msg = f"🗑 已從「{deleted_from}」中刪除帳號：{key}" if deleted_from else f"❌ 查無帳號：{key} 於待審或白名單中"
        line_bot_api.push_message(user_id, TextSendMessage(msg))
        return

    # ✅ show pending：列出所有尚未審核的註冊資料
    elif user_input.startswith("show pending"):
        if not pending_data:
            line_bot_api.push_message(user_id, TextSendMessage("📭 目前沒有待審核的註冊資料。"))
            return

        msg = "📋【待審名單】\n"
        for uid, info in pending_data.items():
            msg += f"\n👤 姓名：{info.get('name', '-')}\n"
            msg += f"🎓 學號：{info.get('external_id', '-')}\n"
            msg += f"🧩 身分：{info.get('role', '-')}\n"
            msg += f"🆔 userId：{uid}\n"
            msg += f"✅ 指令：approve {uid}\n"
            msg += "----------------------"

        line_bot_api.push_message(user_id, TextSendMessage(msg))
        return

    # ✅ show whitelist：顯示已通過名單
    elif user_input.startswith("show whitelist"):
        if not whitelist:
            line_bot_api.push_message(user_id, TextSendMessage("📭 目前白名單內尚無通過使用者。"))
            return

        msg = "📘【白名單使用者】\n"
        for uid, info in whitelist.items():
            msg += f"\n👤 姓名：{info.get('name', '-')}\n"
            msg += f"🎓 學號：{info.get('external_id', '-')}\n"
            msg += f"🧩 身分：{info.get('role', '-')}\n"
            msg += f"🆔 userId：{uid}\n"
            msg += f"🗑 指令：delet {uid}\n"
            msg += "----------------------"

        line_bot_api.push_message(user_id, TextSendMessage(msg))
        return

    # 其他：不明指令提示
    else:
        line_bot_api.push_message(user_id, TextSendMessage("❓ 不明的管理指令。"))
