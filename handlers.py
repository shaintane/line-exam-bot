import logging

from linebot.models import TextSendMessage

from access_control import check_user_access
from challenge_logic import (
    ChallengeQuestionBuildError,
    build_challenge_questions,
)
from challenge_service import (
    complete_challenge_attempt,
    get_challenge_timing,
    save_challenge_answer,
    start_challenge_attempt,
)
from admin_logic import handle_admin_commands
from exam_logic import (
    SUBJECTS,
    format_question,
    handle_exam_logic,
    normalize_answer,
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



def handle_challenge_menu_command(
    user_id: str,
    line_bot_api,
    user_sessions,
) -> None:
    """顯示挑戰模式規則，等待使用者確認開始。"""
    access = check_and_sync_access(user_id)

    if not access.allowed:
        user_sessions.pop(user_id, None)
        push_text(
            line_bot_api,
            user_id,
            access.message,
        )
        return

    user_sessions[user_id] = {
        "completed": True,
        "challenge_pending": True,
        "exam_mode": "challenge_pending",
    }

    push_text(
        line_bot_api,
        user_id,
        (
            "🏆 挑戰模式\n\n"
            "題數：30 題\n"
            "科目：六科各 5 題\n"
            "時間：23 分鐘\n"
            "排名：先比答對題數，同分再比完成時間\n\n"
            "挑戰結果不納入一般學習歷程與弱點分析\n\n"
            "準備好後請輸入：開始挑戰"
        ),
    )


def handle_start_challenge_command(
    user_id: str,
    line_bot_api,
    user_sessions,
) -> None:
    """
    準備 30 題挑戰題組，但尚不開始計時。

    使用者輸入 S 後才建立 ChallengeAttempt，
    此時才正式記錄 started_at 並送出第 1 題。
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

    existing_session = user_sessions.get(user_id) or {}

    if not existing_session.get("challenge_pending"):
        push_text(
            line_bot_api,
            user_id,
            (
                "⚠️ 請先輸入「挑戰模式」查看規則，"
                "再輸入「開始挑戰」。"
            ),
        )
        return

    try:
        questions = build_challenge_questions()
    except ChallengeQuestionBuildError as exc:
        LOGGER.exception(
            "Failed to build challenge questions: user_id=%s",
            user_id,
        )
        push_text(
            line_bot_api,
            user_id,
            f"⚠️ {exc}",
        )
        return
    except Exception:
        LOGGER.exception(
            "Unexpected challenge question build error: user_id=%s",
            user_id,
        )
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰題組建立失敗，請稍後再試。",
        )
        return

    user_sessions[user_id] = {
        "exam_mode": "challenge_ready",
        "challenge_ready": True,
        "questions": questions,
        "question_count": len(questions),
        "current": 0,
        "answers": [],
        "completed": False,
    }

    push_text(
        line_bot_api,
        user_id,
        (
            "🏆 挑戰說明\n\n"
            "作答後不顯示對錯，會直接進入下一題\n"
            "正式開始後，中途離開時間不會暫停\n\n"
            "準備好後請輸入 S（無大小寫限制）\n"
            "輸入 S 後才開始計時並出第 1 題"
        ),
    )


def handle_confirm_challenge_start(
    user_id: str,
    line_bot_api,
    user_sessions,
) -> None:
    """使用者輸入 S 後正式開始計時並送出第 1 題。"""
    session = user_sessions.get(user_id) or {}

    if (
        session.get("exam_mode") != "challenge_ready"
        or not session.get("challenge_ready")
    ):
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 請先輸入「挑戰模式」→「開始挑戰」。",
        )
        return

    questions = session.get("questions", [])
    if not questions:
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰題組不存在，請重新輸入「挑戰模式」。",
        )
        user_sessions.pop(user_id, None)
        return

    try:
        attempt = start_challenge_attempt(
            line_user_id=user_id,
        )
    except Exception:
        LOGGER.exception(
            "Failed to start challenge attempt: user_id=%s",
            user_id,
        )
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰紀錄建立失敗，請稍後再試。",
        )
        return

    session["exam_mode"] = "challenge"
    session["challenge_ready"] = False
    session["challenge_attempt_id"] = attempt.id
    session["current"] = 0
    session["answers"] = []
    session["completed"] = False

    first_question = questions[0]
    first_repo = str(
        first_question.get("challenge_repo", "")
    ).strip()

    first_message = format_question(
        first_question,
        0,
        first_repo,
    )

    push_text(
        line_bot_api,
        user_id,
        (
            "⏱️ 計時開始！\\n"
            "23 分鐘挑戰正式開始。"
        ),
    )

    push_text(
        line_bot_api,
        user_id,
        first_message,
    )

def format_elapsed_time(seconds: int) -> str:
    """將秒數格式化為 X分Y秒。"""
    total_seconds = max(int(seconds or 0), 0)
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}分{secs:02d}秒"


def finish_challenge_session(
    user_id: str,
    line_bot_api,
    user_sessions,
    session,
    *,
    force_status: str | None = None,
) -> None:
    """完成挑戰、寫入資料庫並顯示本次結果。"""
    attempt_id = session.get("challenge_attempt_id")

    if not attempt_id:
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰紀錄不存在，請重新輸入「挑戰模式」。",
        )
        user_sessions.pop(user_id, None)
        return

    try:
        attempt = complete_challenge_attempt(
            int(attempt_id),
            force_status=force_status,
        )
    except Exception:
        LOGGER.exception(
            "Failed to finish challenge session: user_id=%s attempt_id=%s",
            user_id,
            attempt_id,
        )
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰結果儲存失敗，請稍後再試。",
        )
        return

    session["completed"] = True
    session["challenge_status"] = attempt.status

    answered_count = len(session.get("answers", []))
    total = int(attempt.question_count or 30)
    correct = int(attempt.correct_count or 0)
    rate = float(attempt.score_rate or 0.0)
    elapsed_text = format_elapsed_time(
        int(attempt.elapsed_seconds or 0)
    )

    if attempt.status == "timeout":
        title = "⏰ 挑戰時間到！"
    else:
        title = "🏆 挑戰完成！"

    if attempt.status == "timeout":
        result_text = (
            f"{title}\n\n"
            f"已完成：{answered_count} / {total} 題\n"
            f"答對題數：{correct} / {total}\n"
            f"正確率：{rate}%\n"
            f"完成時間：{elapsed_text}\n\n"
            "排行榜與個人最佳紀錄將在下一階段接上。"
        )
    else:
        result_text = (
            f"{title}\n\n"
            f"答對題數：{correct} / {total}\n"
            f"正確率：{rate}%\n"
            f"完成時間：{elapsed_text}\n\n"
            "排行榜與個人最佳紀錄將在下一階段接上。"
        )

    push_text(
        line_bot_api,
        user_id,
        result_text,
    )


def handle_challenge_answer(
    user_input: str,
    user_id: str,
    line_bot_api,
    user_sessions,
) -> None:
    """處理挑戰模式 A/B/C/D 作答、下一題與逾時。"""
    session = user_sessions.get(user_id) or {}

    if session.get("exam_mode") != "challenge":
        return

    attempt_id = session.get("challenge_attempt_id")

    if not attempt_id:
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰紀錄不存在，請重新輸入「挑戰模式」。",
        )
        user_sessions.pop(user_id, None)
        return

    # 每次作答前先檢查 23 分鐘限制。
    try:
        timing = get_challenge_timing(int(attempt_id))
    except Exception:
        LOGGER.exception(
            "Failed to check challenge timing: user_id=%s attempt_id=%s",
            user_id,
            attempt_id,
        )
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 無法確認挑戰計時，請稍後再試。",
        )
        return

    if bool(timing.get("is_timeout")):
        finish_challenge_session(
            user_id,
            line_bot_api,
            user_sessions,
            session,
            force_status="timeout",
        )
        return

    normalized_input = normalize_answer(user_input)

    if normalized_input not in {"A", "B", "C", "D"}:
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 挑戰進行中，請輸入 A / B / C / D 作答。",
        )
        return

    questions = session.get("questions", [])
    current_index = int(session.get("current", 0))
    question_count = int(
        session.get("question_count")
        or len(questions)
    )

    if current_index >= question_count:
        finish_challenge_session(
            user_id,
            line_bot_api,
            user_sessions,
            session,
        )
        return

    current_question = questions[current_index]
    correct_answer = normalize_answer(
        str(current_question.get("正解", ""))
    )
    is_correct = normalized_input == correct_answer

    subject = str(
        current_question.get("challenge_subject", "")
    ).strip()
    repo = str(
        current_question.get("challenge_repo", "")
    ).strip()

    try:
        save_challenge_answer(
            int(attempt_id),
            subject=subject,
            repo=repo,
            question=current_question,
            student_answer=normalized_input,
            correct_answer=correct_answer,
            is_correct=is_correct,
        )
    except Exception:
        LOGGER.exception(
            "Failed to save challenge answer: user_id=%s attempt_id=%s question=%s",
            user_id,
            attempt_id,
            current_question.get("題號", current_index + 1),
        )
        push_text(
            line_bot_api,
            user_id,
            "⚠️ 本題作答儲存失敗，請再輸入一次答案。",
        )
        return

    session.setdefault("answers", []).append(
        {
            "題號": current_question.get(
                "題號",
                current_index + 1,
            ),
            "作答": normalized_input,
            "正解": correct_answer,
            "是否正確": is_correct,
        }
    )

    session["current"] = current_index + 1

    # 第 30 題完成後立即結算。
    if session["current"] >= question_count:
        finish_challenge_session(
            user_id,
            line_bot_api,
            user_sessions,
            session,
        )
        return

    # 挑戰模式不顯示對錯，直接送下一題。
    next_question = questions[session["current"]]
    next_repo = str(
        next_question.get("challenge_repo", "")
    ).strip()

    next_message = format_question(
        next_question,
        session["current"],
        next_repo,
    )

    push_text(
        line_bot_api,
        user_id,
        next_message,
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
    # 挑戰模式
    # ---------------------------------------------------------
    if user_input in {
        "挑戰模式",
        "挑戰賽",
    }:
        handle_challenge_menu_command(
            user_id,
            line_bot_api,
            user_sessions,
        )
        return

    if user_input == "開始挑戰":
        handle_start_challenge_command(
            user_id,
            line_bot_api,
            user_sessions,
        )
        return

    if user_input.upper() == "S":
        active_session = user_sessions.get(user_id) or {}
        if active_session.get("exam_mode") == "challenge_ready":
            handle_confirm_challenge_start(
                user_id,
                line_bot_api,
                user_sessions,
            )
            return

    # 挑戰模式作答優先處理，避免誤走一般測驗流程。
    active_session = user_sessions.get(user_id) or {}

    if active_session.get("exam_mode") == "challenge_ready":
        push_text(
            line_bot_api,
            user_id,
            "🏆 挑戰已準備完成，請輸入 S 開始計時並出第 1 題。",
        )
        return

    if active_session.get("exam_mode") == "challenge":
        handle_challenge_answer(
            user_input,
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
                "分析近期錯題請輸入：弱點分析\n"
                "進入遊戲化測驗請輸入：挑戰模式"
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
