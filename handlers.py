from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from linebot.models import TextSendMessage
import time
import logging

# 安全封裝 push_message，含簡易 retry 與錯誤追蹤
def safe_push_message(line_bot_api, user_id, message, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            line_bot_api.push_message(user_id, message)
            return  # 成功即結束
        except Exception as e:
            logging.error(f"[PushMessage] 第 {attempt} 次嘗試失敗: {e}")
            time.sleep(1)  # 簡單延遲
    logging.error(f"[PushMessage] 已超過最大重試次數，訊息送出失敗：{message}")

def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # 測驗流程邏輯
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
