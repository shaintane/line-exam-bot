from linebot.models import TextSendMessage

# 建立一個暫存字典，用來記錄註冊流程資料
registration_buffer = {}

def handle_event(event, line_bot_api, client, user_sessions, registration_buffer):
    if event.get("type") != "message" or event["message"].get("type") != "text":
        return

    user_input = event["message"]["text"].strip()
    user_id = event["source"]["userId"]

    print(f"[handle_event] 收到訊息: {user_input}，來自 userId: {user_id}")

    # 處理「註冊」關鍵字
    if user_input == "註冊":
        registration_buffer[user_id] = {"step": "ask_name"}
        print(f"[註冊流程] 建立暫存資料: {registration_buffer}")
        if line_bot_api:
            line_bot_api.push_message(user_id, TextSendMessage(text="請輸入您的【姓名】："))
        return
