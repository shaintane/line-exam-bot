# handlers.py
from linebot.models import TextSendMessage
from sheets_logic import get_latest_valid_row, write_whitelist

# === 指定 Google Sheets 的資訊 ===
SPREADSHEET_ID = "1XI0iP1iqD8aDRKG0FQF8VwtrLij-MuBEop_BM1WXRAY"  # 你的試算表ID
SHEET_NAME = "Form Responses 1"  # 分頁名稱，若中文請改成實際名稱，例如「表單回應 1」

# 你的 Google 表單（換成你的表單ID），已預填 LINE_ID
FORM_URL_TEMPLATE = (
    "https://docs.google.com/forms/d/你的表單ID/viewform"
    "?usp=pp_url&entry.LINE_ID={line_id}"
)

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

    if user_input == "註冊":
        try:
            # 依 LINE_ID 過濾 + 有效期判斷
            latest = get_latest_valid_row(
                SPREADSHEET_ID,
                SHEET_NAME,
                user_id,
                line_id_header_candidates=["LINE_ID", "第 12 題", "line_id", "Line ID"]
            )
            if latest:
                # 寫入白名單
                ok = write_whitelist(latest, path="whitelist.json")
                if ok:
                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(
                            text=(
                                "✅ 註冊完成並加入白名單！\n"
                                f"姓名：{latest.get('name','')}\n"
                                f"學校：{latest.get('school','')}\n"
                                f"有效期：{latest['start_date']} ～ {latest['end_date']}\n\n"
                                "你現在可以直接使用測驗與其他功能囉。"
                            )
                        ),
                    )
                else:
                    line_bot_api.push_message(
                        user_id, TextSendMessage(text="註冊寫入白名單時發生問題，請稍後再試或聯絡管理者。")
                    )
            else:
                # 查無有效資料 → 給表單連結（帶入 LINE_ID）
                form_url = FORM_URL_TEMPLATE.format(line_id=user_id)
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
            # 不讓使用者遇到「沒反應」；任何錯誤都回覆
            form_url = FORM_URL_TEMPLATE.format(line_id=user_id)
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

    # 其他指令/模組可在此擴充
