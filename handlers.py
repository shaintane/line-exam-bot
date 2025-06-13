from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic

# 主邏輯函式，處理所有訊息
def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # 模擬新進使用者測試
    if user_input == "測試":
        welcome = (
            "👋 歡迎加入國考輔導系統！\n"
            "請依下列格式輸入以完成註冊：\n\n"
            "格式：學校 姓名 學號 起始日 結束日\n"
            "範例：國立醫學大學 王小明 123456 2025-06-01 2025-09-30"
        )
        line_bot_api.push_message(user_id, TextSendMessage(text=welcome))
        registration_buffer[user_id] = {"LINE_ID": user_id}
        return

    # 如果尚未註冊，等待填寫註冊資訊
    if user_id in registration_buffer and user_input.count(" ") >= 4:
        try:
            school, name, student_id, start_date, end_date = user_input.split()
            registration_buffer[user_id].update({
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
            })

            # 寫入 pending_register.json
            import json, os
            pending_file = "pending_register.json"
            if os.path.exists(pending_file):
                with open(pending_file, "r", encoding="utf-8") as f:
                    pending_data = json.load(f)
            else:
                pending_data = {}

            pending_data[user_id] = registration_buffer[user_id]
            with open(pending_file, "w", encoding="utf-8") as f:
                json.dump(pending_data, f, indent=2, ensure_ascii=False)

            line_bot_api.push_message(user_id, TextSendMessage(
                text="✅ 資料已送出，請等待管理者審核。"))
            del registration_buffer[user_id]
        except Exception as e:
            line_bot_api.push_message(user_id, TextSendMessage(
                text="⚠️ 格式錯誤，請重新輸入：學校 姓名 學號 起始日 結束日"))
        return

    # 管理者邏輯（註冊審核、白名單、刪除、查詢）
    if handle_admin_commands(user_input, user_id, line_bot_api, registration_buffer):
        return

    # 測驗流程
    handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer)
