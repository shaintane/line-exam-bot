# edu_logic.py
from linebot.models import TextSendMessage

def handle_edu_logic(user_input, user_id, line_bot_api, client):
    if "上傳作業" in user_input:
        line_bot_api.push_message(user_id, TextSendMessage(text="📤 請上傳作業照片並附上說明文字，我會幫你紀錄。"))
        return

    if "查詢進度" in user_input or "進度" in user_input:
        # 假設日後你會整合 Google Sheet 或資料庫
        line_bot_api.push_message(user_id, TextSendMessage(text="📊 目前你已完成 3/5 項任務，繼續加油！"))
        return

    if "回饋" in user_input:
        line_bot_api.push_message(user_id, TextSendMessage(text="📝 請輸入你對今天學習的回饋，我會記錄下來給老師。"))
        return

    # 未匹配到具體命令
    line_bot_api.push_message(user_id, TextSendMessage(text="❓ 抱歉，我不太懂你的意思。你可以輸入「上傳作業」、「查詢進度」或「回饋」試試看喔！"))
