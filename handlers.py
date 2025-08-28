from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic
from sheets_logic import get_latest_valid_row

import requests
import json
import datetime

registration_buffer = {}

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

    # ==== 處理註冊流程 ====
    if user_input == "註冊":
        registration_buffer[user_id] = {"step": "ask_name"}
        print(f"[註冊流程] 建立暫存資料: {registration_buffer}")

        # 嘗試從 Google Sheets 擷取該用戶最近註冊紀錄
        result = get_latest_valid_row(user_id)
        if result:
            start_date, end_date = result["start_date"], result["end_date"]
            line_bot_api.push_message(user_id, TextSendMessage(
                text=f"✅ 已自動識別您的註冊資訊，權限有效期間為：{start_date} ~ {end_date}"
            ))
        else:
            # 未找到有效註冊，回傳表單連結
            line_bot_api.push_message(user_id, TextSendMessage(
                text="請填寫以下註冊表單完成資料登錄：\nhttps://forms.gle/6emCTAC2XJ5Gy21x7"
            ))

        return

    # 其餘指令邏輯區塊可接續處理...

    # TODO: 可擴充其他輸入處理，例如教育模組、測驗模組、管理指令等

    return
