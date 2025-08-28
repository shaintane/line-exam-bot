from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic
import urllib.parse

# Google 表單設定
GOOGLE_FORM_BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBXwT2qoeHnMPnWbB5c9cGs1INPq_mVrIo1Qd4alGyb2gRFg/viewform"
GOOGLE_FORM_ENTRY_ID_LINEID = "entry.1933153861"

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

    # ✅ 註冊流程
    if user_input == "註冊":
        params = {GOOGLE_FORM_ENTRY_ID_LINEID: user_id}
        query_string = urllib.parse.urlencode(params)
        form_url = f"{GOOGLE_FORM_BASE_URL}?{query_string}"

        message = (
            f"📋 請點選以下連結填寫實習基本資料表單：\n{form_url}\n\n"
            "✅ 填寫完成後系統將自動審查是否符合有效期間，並回傳權限通知。"
        )
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
        return

    # 其他模組指令邏輯
    if user_input.startswith("admin"):
        handle_admin_commands(event, line_bot_api, client, user_input, user_sessions)
    elif user_input.startswith("考試") or user_input.startswith("測驗"):
        handle_exam_logic(event, line_bot_api, client, user_input, user_sessions)
    elif user_input.startswith("任務") or user_input.startswith("作業"):
        handle_edu_logic(event, line_bot_api, client, user_input, user_sessions)
