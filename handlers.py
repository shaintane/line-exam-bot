import logging

from linebot.models import TextSendMessage

from access_control import check_user_access
from admin_logic import handle_admin_commands
from exam_logic import (
    SUBJECTS,
    handle_exam_logic,
    load_question_bank,
    start_exam_with_questions,
)
from history_service import sync_access_and_apply_retention
from learning_history import build_learning_history_message
from weakness_service import (
    build_weakness_analysis,
    format_weakness_analysis,
    select_weakness_questions,
)


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


def check_and_sync_access(
    user_id: str,
):
    """
    檢查使用權限並同步資料庫狀態。

    已過期者會依既定保留規則刪除學習歷程。
    """
    access = check_user_access(user_id)

    try:
        sync_access_and_apply_retention(
            user_id,
            access,
        )
    except Exception:
        LOGGER.exception(
            "Failed to synchronize access: "
            "user_id=%s status=%s",
            user_id,
            getattr(access, "status", "unknown"),
        )

    return access


def handle_learning_history_command(
    user_id: str,
    line_bot_api,
) -> None:
    """處理「學習歷程」與「我的成績」指令。"""
    access = check_and_sync_access(user_id)

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


def handle_weakness_analysis_command(
    user_id: str,
    line_bot_api,
    client,
    user_sessions,
) -> None:
    """
    處理「弱點分析」指令。

    分析結果會暫存於 user_sessions，供後續
    「開始弱點練習」建立題目時使用。
    """
    access = check_and_sync_access(user_id)

    if not access.allowed:
        user_sessions.pop(user_id, None)
        push_text(
            line_bot_api,
            user_id,
            access.message,
        )
        return

    # 不先傳送「正在分析」，避免同一事件需要第二次 push。
    # 分析完成後直接以本次 reply token 回傳完整結果。
    analysis = build_weakness_analysis(
        user_id,
        client,
    )

    existing_session = user_sessions.get(user_id)

    if existing_session is None:
        existing_session = {
            "completed": True,
        }
        user_sessions[user_id] = existing_session

    if analysis.get("has_data"):
        existing_session["weakness_analysis"] = analysis
    else:
        existing_session.pop(
            "weakness_analysis",
            None,
        )

    message = format_weakness_analysis(
        analysis
    )

    push_text(
        line_bot_api,
        user_id,
        message,
    )


def handle_start_weakness_practice_command(
    user_id: str,
    line_bot_api,
    user_sessions,
) -> None:
    """
    處理「開始弱點練習」。

    使用最近一次弱點分析結果：
    1. 取得建議優先科目
    2. 載入該科既有 GitHub 題庫
    3. 依內部 keywords/topic/subtopics 搜尋相似題
    4. 排除弱點分析來源原錯題
    5. 相似題不足 5 題時以同科其他題補滿
    6. 建立標準測驗 session，沿用既有作答與資料庫流程
    """
    access = check_and_sync_access(user_id)

    if not access.allowed:
        user_sessions.pop(user_id, None)
        push_text(
            line_bot_api,
            user_id,
            access.message,
        )
        return

    session = user_sessions.get(user_id) or {}
    analysis = session.get("weakness_analysis")

    if not isinstance(analysis, dict) or not analysis.get("has_data"):
        push_text(
            line_bot_api,
            user_id,
            (
                "⚠️ 尚未建立可使用的弱點分析。\n"
                "請先輸入「弱點分析」。"
            ),
        )
        return

    subject = str(
        analysis.get("priority_subject", "")
    ).strip()

    repo = str(
        analysis.get("repo", "")
    ).strip()

    if not repo and subject in SUBJECTS:
        repo = SUBJECTS[subject]

    if not subject or not repo:
        LOGGER.error(
            "Weakness practice missing subject or repo: "
            "user_id=%s subject=%s repo=%s",
            user_id,
            subject,
            repo,
        )
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 弱點分析資料不完整，請重新輸入「弱點分析」。",
        )
        return

    question_bank = load_question_bank(repo)

    if not question_bank:
        push_text(
            line_bot_api,
            user_id,
            (
                "⚠️ 弱點練習題庫載入失敗。\n"
                "請稍後再試。"
            ),
        )
        return

    selection = select_weakness_questions(
        question_bank=question_bank,
        analysis=analysis,
        question_count=5,
    )

    questions = selection.get("questions", [])

    if not questions:
        push_text(
            line_bot_api,
            user_id,
            (
                "⚠️ 目前沒有足夠的題目可建立弱點練習。\n"
                "請稍後再試或重新進行弱點分析。"
            ),
        )
        return

    similar_count = int(
        selection.get("similar_count", 0)
    )
    fallback_count = int(
        selection.get("fallback_count", 0)
    )

    LOGGER.info(
        (
            "Starting weakness practice: "
            "user_id=%s subject=%s repo=%s "
            "questions=%s similar=%s fallback=%s"
        ),
        user_id,
        subject,
        repo,
        len(questions),
        similar_count,
        fallback_count,
    )

    start_exam_with_questions(
        subject=subject,
        repo=repo,
        questions=questions,
        user_id=user_id,
        line_bot_api=line_bot_api,
        user_sessions=user_sessions,
        intro_text=(
            f"🎯 弱點練習：{subject}\n"
            f"本次共 {len(questions)} 題，開始練習："
        ),
        session_extra={
            "exam_mode": "weakness_practice",
            "weakness_analysis": analysis,
            "weakness_similar_count": similar_count,
            "weakness_fallback_count": fallback_count,
        },
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
    # AI 弱點分析
    # ---------------------------------------------------------
    if user_input in {
        "弱點分析",
        "分析弱點",
    }:
        handle_weakness_analysis_command(
            user_id,
            line_bot_api,
            client,
            user_sessions,
        )
        return

    # ---------------------------------------------------------
    # 開始弱點練習
    # ---------------------------------------------------------
    if user_input in {
        "開始弱點練習",
        "弱點練習",
    }:
        handle_start_weakness_practice_command(
            user_id,
            line_bot_api,
            user_sessions,
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
                "一般測驗可選 5 / 10 / 20 / 30 題。\n\n"
                "例如輸入：微生物\n\n"
                "查看個人紀錄請輸入：學習歷程\n"
                "分析近期錯題請輸入：弱點分析"
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
