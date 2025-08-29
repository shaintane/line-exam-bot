# handlers.py
from urllib.parse import quote_plus
from linebot.models import TextSendMessage
from sheets_logic import get_latest_valid_row, write_whitelist
import json
import os

# === Google Sheets 資訊 ===
SPREADSHEET_ID = "1XI0iP1iqD8aDRKG0FQF8VwtrLij-MuBEop_BM1WXRAY"  # 若換了新試算表，請一併更新
SHEET_NAME = "註冊回應 1"   # ← 依你的需求固定在「註冊回應 1」

# === Google 表單預填參數（你提供的） ===
FORM_ID = "1lCiYdpBIlxqMihyG6ZFJdCN3zkUmyk-zlkQxEP4dlrg"
ENTRY_ID_FOR_LINE_ID = "entry.1933153861"

# === 管理員 LINE User ID ===
# 建議改成環境變數（優先讀 env，沒有就用備用值）
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "Ua14ba7a3ae8c1c046398b86fb8bb2344")  # ← 換成你的 User ID


def build_form_url(line_id: str) -> str:
    return (
        f"https://docs.google.com/forms/d/{FORM_ID}/viewform"
        f"?usp=pp_url&{ENTRY_ID_FOR_LINE_ID}={quote_plus(line_id)}"
    )


def _safe_load_whitelist():
    try:
        with open("whitelist.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        raise RuntimeError(f"讀取白名單失敗：{e}")


def _safe_save_whitelist(data: dict):
    with open("whitelist.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

    # === 查詢自己的 LINE User ID ===
    if user_input in ["我的ID", "myid", "MyID"]:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=f"你的 LINE User ID 是：\n{user_id}")
        )
        return

    # === 註冊流程 ===
    if user_input == "註冊":
        try:
            latest = get_latest_valid_row(
                SPREADSHEET_ID,
                SHEET_NAME,
                user_id,
                line_id_header_candidates=["LINE_ID", "LINE ID", "line_id", "Line ID", "第 12 題", "第12題"]
            )

            if latest:
                ok = write_whitelist(latest, path="whitelist.json")
                if ok:
                    start = latest.get("start_date") or "無期限"
                    end   = latest.get("end_date") or "無期限"
                    role  = (latest.get("role") or "student")
                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(
                            text=(
                                "✅ 註冊完成並加入白名單！\n"
                                f"姓名：{latest.get('name','')}\n"
                                f"角色：{role}\n"
                                f"有效期：{start} ～ {end}\n\n"
                                "你現在可以直接使用測驗與其他功能囉。"
                            )
                        ),
                    )
                else:
                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text="註冊寫入白名單時發生問題，請稍後再試或聯絡管理者。")
                    )
            else:
                form_url = build_form_url(user_id)
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(
                        text=(
                            "尚未找到你的有效註冊資料。\n"
                            "請先填寫註冊表單（已自動帶入你的 LINE ID）：\n"
                            f"{form_url}\n\n"
                            "送出後等 5–10 秒，再輸入一次「註冊」。"
                        )
                    ),
                )
        except Exception as e:
            form_url = build_form_url(user_id)
            line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=(
                        "目前連線 Google Sheets 發生錯誤，先請你填/確認註冊表單：\n"
                        f"{form_url}\n\n"
                        "送出後等 5–10 秒再輸入一次「註冊」。\n"
                        f"(debug: {str(e)})"
                    )
                ),
            )
        return

    # === 管理員指令（僅限 ADMIN_USER_ID） ===
    if user_id == ADMIN_USER_ID:
        parts = user_input.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()

        # help_admin → 顯示指令表
        if cmd == "help_admin":
            msg = (
                "🛠 管理員指令表：\n"
                "1. show_all [role]           → 列出白名單（可選 student/teacher 篩選）\n"
                "2. show_user <LINE_ID>       → 顯示單一用戶完整資訊\n"
                "3. remove_user <LINE_ID>     → 移除白名單用戶\n"
                "4. find_name <關鍵字>        → 依姓名關鍵字搜尋 LINE_ID\n"
                "5. help_admin                → 顯示此指令表\n"
            )
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return

        # show_all [role]
        if cmd == "show_all":
            role_filter = parts[1].lower() if len(parts) == 2 else None
            try:
                data = _safe_load_whitelist()
            except Exception as e:
                line_bot_api.push_message(user_id, TextSendMessage(text=str(e)))
                return

            items = []
            for lid, info in data.items():
                role = (info.get("role") or "").lower()
                if role_filter and role != role_filter:
                    continue
                items.append((info.get("name", ""), lid, role))

            if not items:
                line_bot_api.push_message(user_id, TextSendMessage(text="（沒有符合條件的名單）"))
                return

            items.sort(key=lambda x: (x[0], x[1]))
            MAX = 50
            head = f"白名單清單（顯示最多 {MAX} 筆）" + (f"｜篩選：{role_filter}" if role_filter else "")
            lines = [head]
            for i, (name, lid, role) in enumerate(items[:MAX], 1):
                lines.append(f"{i}. {name}  <{lid}>  [{role or 'unknown'}]")

            line_bot_api.push_message(user_id, TextSendMessage(text="\n".join(lines)))
            return

        # show_user <LINE_ID>
        if cmd == "show_user" and len(parts) == 2:
            target = parts[1]
            try:
                data = _safe_load_whitelist()
                info = data.get(target)
                if info:
                    pretty = "\n".join([f"{k}: {v}" for k, v in info.items()])
                    msg = f"白名單資訊：\nLINE_ID: {target}\n{pretty}"
                else:
                    msg = f"找不到 {target} 的白名單資料。"
            except Exception as e:
                msg = str(e)
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return

        # remove_user <LINE_ID>
        if cmd == "remove_user" and len(parts) == 2:
            target = parts[1]
            try:
                data = _safe_load_whitelist()
                if target in data:
                    data.pop(target)
                    _safe_save_whitelist(data)
                    msg = f"已移除 {target}。"
                else:
                    msg = f"找不到 {target}。"
            except Exception as e:
                msg = f"移除使用者失敗：{e}"
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return

        # find_name <關鍵字>
        if cmd == "find_name" and len(parts) == 2:
            keyword = parts[1]
            try:
                data = _safe_load_whitelist()
            except Exception as e:
                line_bot_api.push_message(user_id, TextSendMessage(text=str(e)))
                return

            results = []
            for lid, info in data.items():
                name = info.get("name", "")
                role = info.get("role", "")
                if keyword in name:
                    results.append(f"{name} <{lid}> [{role}]")

            if results:
                msg = "🔍 找到以下符合的使用者：\n" + "\n".join(results)
            else:
                msg = f"找不到包含「{keyword}」的姓名。"

            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return

    # 其他指令/模組...
