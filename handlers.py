# handlers.py
from urllib.parse import quote_plus
from linebot.models import TextSendMessage
from sheets_logic import get_latest_valid_row, write_whitelist

# === Google Sheets 資訊 ===
SPREADSHEET_ID = "1XI0iP1iqD8aDRKG0FQF8VwtrLij-MuBEop_BM1WXRAY"  # 若換了新試算表，請一併更新
SHEET_NAME = "註冊回應1"   # <- 改成你的實際分頁名

# === Google 表單預填參數（你提供的） ===
FORM_ID = "1lCiYdpBIlxqMihyG6ZFJdCN3zkUmyk-zlkQxEP4dlrg"
ENTRY_ID_FOR_LINE_ID = "entry.1933153861"

def build_form_url(line_id: str) -> str:
    return (
        f"https://docs.google.com/forms/d/{FORM_ID}/viewform"
        f"?usp=pp_url&{ENTRY_ID_FOR_LINE_ID}={quote_plus(line_id)}"
    )

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

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
                    role  = latest.get("role") or "student"
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

    # 其他指令/模組...
