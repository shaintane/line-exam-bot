from linebot.models import TextSendMessage
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from edu_logic import handle_edu_logic

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.type != "message" or event.message.type != "text":
        return

    user_input = event.message.text.strip()
    user_id = event.source.user_id

    # ✅ 管理員指令（白名單 / 註冊 / 查詢等）
    if user_input.startswith(("input", "approve", "delet", "show")):
        handle_admin_commands(user_input, user_id, line_bot_api, client, registration_buffer)
        return

    # ✅ 教學任務系統（上傳作業、進度追蹤、照片留言等）
    if any(keyword in user_input for keyword in ["上傳", "作業", "回饋", "進度", "照片", "留言", "提醒"]):
        handle_edu_logic(user_input, user_id, line_bot_api, client)
        return

    # ✅ 國考 AI 輔助練習模組（如 免疫、血庫 等）
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
