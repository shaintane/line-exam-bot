from linebot.models import TextSendMessage

from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic


def process_message(
    event,
    line_bot_api,
    client,
    user_sessions,
    registration_buffer,
):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # ---------------------------------------------------------
    # 顯示目前使用者的 LINE User ID
    # ---------------------------------------------------------
    if user_input == "我的ID":
        line_bot_api.push_message(
            user_id,
            TextSendMessage(
                text=f"你的 LINE User ID 是：\n{user_id}"
            ),
        )
        return

    # ---------------------------------------------------------
    # 進入測驗選單
    # ---------------------------------------------------------
    if user_input in {
        "開始",
        "選單",
        "主選單",
        "menu",
        "Menu",
        "MENU",
    }:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(
                text=(
                    "📚 國考測驗系統\n\n"
                    "請輸入想練習的科目：\n\n"
                    "1️⃣ 微生物\n"
                    "2️⃣ 免疫\n"
                    "3️⃣ 血液\n"
                    "4️⃣ 生化\n"
                    "5️⃣ 分子\n"
                    "6️⃣ 病理\n\n"
                    "每次隨機測驗 5 題。\n\n"
                    "例如輸入：微生物"
                )
            ),
        )
        return

    # ---------------------------------------------------------
    # 優先處理註冊與管理者指令
    # ---------------------------------------------------------
    handled = handle_admin_commands(
        user_input,
        user_id,
        line_bot_api,
        registration_buffer,
    )

    if handled:
        return

    # ---------------------------------------------------------
    # 其餘訊息交由測驗模組處理
    # ---------------------------------------------------------
    handle_exam_logic(
        user_input,
        user_id,
        event,
        line_bot_api,
        client,
        user_sessions,
        registration_buffer,
    )
