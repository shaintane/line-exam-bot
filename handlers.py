import logging

from linebot.models import TextSendMessage

from access_control import check_user_access
from admin_logic import handle_admin_commands
from exam_logic import handle_exam_logic
from history_service import sync_access_and_apply_retention
from learning_history import build_learning_history_message


LOGGER = logging.getLogger(__name__)


def push_text(
    line_bot_api,
    user_id: str,
    text: str,
) -> None:
    """使用 LINE push message 傳送純文字。"""
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=text),
    )


def handle_learning_history_command(
    user_id: str,
    line_bot_api,
) -> None:
    """
    處理「學習歷程」與「我的成績」指令。

    查詢前先檢查使用權限並同步期限。
    已過期者會依既定規則刪除歷程，且不得查詢。
    """
    access = check_user_access(user_id)

    try:
        sync_access_and_apply_retention(
            user_id,
            access,
        )
    except Exception:
        LOGGER.exception(
            "Failed to synchronize access before "
            "learning history query: user_id=%s status=%s",
            user_id,
            getattr(access, "status", "unknown"),
        )

    if not access.allowed:
        push_text(
            line_bot_api,
            user_id,
            access.message,
        )
        return

    message = build_learning_history_message(
        user_id
    )

    push_text(
        line_bot_api,
        user_id,
        message,
    )


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
        push_text(
            line_bot_api,
            user_id,
            f"你的 LINE User ID 是：\n{user_id}",
        )
        return

    # ---------------------------------------------------------
    # 個人學習歷程
    # ---------------------------------------------------------
    if user_input in {
        "學習歷程",
        "我的成績",
    }:
        handle_learning_history_command(
            user_id,
            line_bot_api,
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
        push_text(
            line_bot_api,
            user_id,
            (
                "📚 國考測驗系統\n\n"
                "請輸入想練習的科目：\n\n"
                "1️⃣ 微生物\n"
                "2️⃣ 免疫\n"
                "3️⃣ 血液\n"
                "4️⃣ 生化\n"
                "5️⃣ 分子\n"
                "6️⃣ 病理\n\n"
                "每次隨機測驗 5 題。\n\n"
                "例如輸入：微生物\n\n"
                "查看個人紀錄請輸入：學習歷程"
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
