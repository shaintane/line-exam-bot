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

    if user_input == "我的ID":
        line_bot_api.push_message(
            user_id,
            TextSendMessage(
                text=f"你的 LINE User ID 是：\n{user_id}"
            ),
        )
        return

    handled = handle_admin_commands(
        user_input,
        user_id,
        line_bot_api,
        registration_buffer,
    )

    if handled:
        return

    handle_exam_logic(
        user_input,
        user_id,
        event,
        line_bot_api,
        client,
        user_sessions,
        registration_buffer,
    )
