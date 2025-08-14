# edu_logic.py
from linebot.models import TextSendMessage

def handle_edu_logic(user_input, user_id, line_bot_api, client):
    # ✅ 上傳作業邏輯（預計整合 Google Drive 圖片與說明文字）
    if "上傳作業" in user_input:
        line_bot_api.push_message(user_id, TextSendMessage(
            text="📤 請上傳作業照片並附上說明文字，我會幫你紀錄！"))
        return

    # ✅ 查詢進度（預計串接 Google Sheet / Drive 統計資料）
    if "查詢進度" in user_input or "進度" in user_input:
        # 後續可從 Google Sheet 擷取學生進度回傳
        line_bot_api.push_message(user_id, TextSendMessage(
            text="📊 目前你已完成 3/5 項任務，繼續加油！"))
        return

    # ✅ 回饋文字記錄（預計寫入 Google Sheet，供教師後台查看）
    if "回饋" in user_input:
        line_bot_api.push_message(user_id, TextSendMessage(
            text="📝 請輸入你今天學習的回饋，我會記錄下來給老師。"))
        return

    # ✅ fallback：沒匹配到指令
    line_bot_api.push_message(user_id, TextSendMessage(
        text="❓ 抱歉，我不太懂你的意思。你可以輸入「上傳作業」、「查詢進度」或「回饋」試試看唷！"))
