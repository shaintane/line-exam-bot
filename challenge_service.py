import logging
from datetime import datetime, timezone
from typing import Any

from database import db
from history_service import get_or_create_user
from models import ChallengeAnswer, ChallengeAttempt


LOGGER = logging.getLogger(__name__)

CHALLENGE_QUESTION_COUNT = 30
CHALLENGE_TIME_LIMIT_SECONDS = 23 * 60


def utc_now() -> datetime:
    """回傳具時區資訊的 UTC 時間。"""
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    """確保資料庫時間可安全與 UTC aware datetime 計算。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def start_challenge_attempt(
    line_user_id: str,
    *,
    question_count: int = CHALLENGE_QUESTION_COUNT,
    time_limit_seconds: int = CHALLENGE_TIME_LIMIT_SECONDS,
) -> ChallengeAttempt:
    """開始一次挑戰，建立獨立的 challenge_attempts 紀錄。"""
    user = get_or_create_user(line_user_id)

    total = max(int(question_count or 0), 0)
    time_limit = max(int(time_limit_seconds or 0), 0)

    if total <= 0:
        raise ValueError("question_count must be greater than zero.")

    if time_limit <= 0:
        raise ValueError("time_limit_seconds must be greater than zero.")

    attempt = ChallengeAttempt(
        user_id=user.id,
        question_count=total,
        correct_count=0,
        score_rate=0.0,
        time_limit_seconds=time_limit,
        elapsed_seconds=None,
        status="in_progress",
        started_at=utc_now(),
        completed_at=None,
    )

    try:
        db.session.add(attempt)
        db.session.commit()
        LOGGER.info(
            "Challenge attempt created: attempt_id=%s user_id=%s questions=%s time_limit=%s",
            attempt.id,
            user.id,
            total,
            time_limit,
        )
        return attempt
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to create challenge attempt: line_user_id=%s",
            line_user_id,
        )
        raise


def save_challenge_answer(
    attempt_id: int,
    *,
    subject: str,
    repo: str,
    question: dict[str, Any],
    student_answer: str,
    correct_answer: str,
    is_correct: bool,
) -> ChallengeAnswer:
    """保存挑戰賽單題作答；不寫入一般 AnswerRecord。"""
    if not attempt_id:
        raise ValueError("attempt_id cannot be empty.")

    attempt = db.session.get(
        ChallengeAttempt,
        int(attempt_id),
    )

    if attempt is None:
        raise ValueError(
            f"Challenge attempt not found: {attempt_id}"
        )

    if attempt.status != "in_progress":
        raise ValueError(
            f"Challenge attempt is not in progress: {attempt.status}"
        )

    question_number = int(
        question.get("題號")
        or question.get("question_number")
        or 0
    )

    if question_number <= 0:
        raise ValueError(
            "question number must be greater than zero."
        )

    question_id = (
        question.get("題目ID")
        or question.get("question_id")
        or question.get("id")
    )

    record = ChallengeAnswer(
        attempt_id=int(attempt_id),
        question_number=question_number,
        subject=str(subject or "").strip(),
        repo=str(repo or "").strip() or None,
        question_id=(
            str(question_id).strip()
            if question_id is not None
            else None
        ),
        question_text=str(
            question.get("題目", "")
        ).strip(),
        options_json=question.get("選項", []),
        student_answer=str(student_answer or "").strip(),
        correct_answer=str(correct_answer or "").strip(),
        is_correct=bool(is_correct),
        answered_at=utc_now(),
    )

    try:
        db.session.add(record)
        db.session.commit()
        LOGGER.info(
            "Challenge answer saved: answer_id=%s attempt_id=%s question=%s correct=%s",
            record.id,
            record.attempt_id,
            record.question_number,
            record.is_correct,
        )
        return record
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to save challenge answer: attempt_id=%s question=%s",
            attempt_id,
            question_number,
        )
        raise


def get_challenge_timing(
    attempt_id: int,
) -> dict[str, int | bool]:
    """取得目前挑戰已用秒數、剩餘秒數與逾時狀態。"""
    attempt = db.session.get(
        ChallengeAttempt,
        int(attempt_id),
    )

    if attempt is None:
        raise ValueError(
            f"Challenge attempt not found: {attempt_id}"
        )

    started_at = normalize_datetime(attempt.started_at)
    current_time = utc_now()

    elapsed = max(
        int((current_time - started_at).total_seconds()),
        0,
    )

    time_limit = max(
        int(attempt.time_limit_seconds or 0),
        0,
    )

    remaining = max(time_limit - elapsed, 0)
    is_timeout = elapsed >= time_limit

    return {
        "elapsed_seconds": elapsed,
        "remaining_seconds": remaining,
        "is_timeout": is_timeout,
    }


def complete_challenge_attempt(
    attempt_id: int,
    *,
    force_status: str | None = None,
) -> ChallengeAttempt:
    """完成挑戰並由 challenge_answers 重算總分與實際耗時。"""
    attempt = db.session.get(
        ChallengeAttempt,
        int(attempt_id),
    )

    if attempt is None:
        raise ValueError(
            f"Challenge attempt not found: {attempt_id}"
        )

    answers = ChallengeAnswer.query.filter_by(
        attempt_id=attempt.id
    ).all()

    answered_count = len(answers)
    correct_count = sum(
        1 for answer in answers if answer.is_correct
    )

    total = max(
        int(attempt.question_count or CHALLENGE_QUESTION_COUNT),
        0,
    )

    score_rate = (
        round((correct_count / total) * 100, 1)
        if total > 0
        else 0.0
    )

    completed_at = utc_now()
    started_at = normalize_datetime(attempt.started_at)

    elapsed_seconds = max(
        int((completed_at - started_at).total_seconds()),
        0,
    )

    time_limit = max(
        int(
            attempt.time_limit_seconds
            or CHALLENGE_TIME_LIMIT_SECONDS
        ),
        0,
    )

    if force_status:
        status = str(force_status).strip()
    elif elapsed_seconds >= time_limit:
        status = "timeout"
    else:
        status = "completed"

    attempt.correct_count = correct_count
    attempt.score_rate = score_rate
    attempt.elapsed_seconds = elapsed_seconds
    attempt.status = status
    attempt.completed_at = completed_at

    try:
        db.session.commit()
        LOGGER.info(
            "Challenge attempt completed: attempt_id=%s status=%s answered=%s correct=%s total=%s elapsed=%s",
            attempt.id,
            status,
            answered_count,
            correct_count,
            total,
            elapsed_seconds,
        )
        return attempt
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to complete challenge attempt: attempt_id=%s",
            attempt_id,
        )
        raise


def get_challenge_attempt(
    attempt_id: int,
) -> ChallengeAttempt | None:
    """依 ID 取得挑戰紀錄。"""
    return db.session.get(
        ChallengeAttempt,
        int(attempt_id),
    )
