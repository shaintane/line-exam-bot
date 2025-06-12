from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic

def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # 管理者邏輯處理，若成功處理則結束流程
    if handle_admin_commands(user_input, user_id, line_bot_api):
        return

    # 測驗流程邏輯處理
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
