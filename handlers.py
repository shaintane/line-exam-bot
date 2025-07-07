from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic

def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # 測驗流程邏輯
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
