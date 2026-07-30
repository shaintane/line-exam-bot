import logging
from datetime import datetime, timezone
from typing import Any

from database import db
from models import (
    AnswerRecord,
    ExamAttempt,
    ExplanationRecord,
    User,
)


LOGGER = logging.getLogger(__name__)


def utc_now() -> datetime:
    """回傳具時區資訊的 UTC 時間。"""
    return datetime.now(timezone.utc)


def get_or_create_user(
    line_user_id: str,
    *,
    name: str | None = None,
    school: str | None = None,
    student_id: str | None = None,
    role: str = "intern",
    status: str = "approved",
) -> User:
    """
    依 LINE User ID 取得使用者。

    若資料庫中尚無此使用者，便建立基本資料。
    若已存在，僅更新有提供且非空白的欄位。
    """
    cleaned_line_user_id = str(line_user_id or "").strip()

    if not cleaned_line_user_id:
        raise ValueError("line_user_id cannot be empty.")

    user = User.query.filter_by(
        line_user_id=cleaned_line_user_id
    ).first()

    if user is None:
        user = User(
            line_user_id=cleaned_line_user_id,
            name=str(name).strip() if name else None,
            school=str(school).strip() if school else None,
            student_id=(
                str(student_id).strip()
                if student_id
                else None
            ),
            role=str(role or "intern").strip(),
            status=str(status or "approved").strip(),
        )
        db.session.add(user)
    else:
        if name:
            user.name = str(name).strip()

        if school:
            user.school = str(school).strip()

        if student_id:
            user.student_id = str(student_id).strip()

        if role:
            user.role = str(role).strip()

        if status:
            user.status = str(status).strip()

    try:
        db.session.commit()
        LOGGER.info(
            "User ready: line_user_id=%s database_user_id=%s",
            cleaned_line_user_id,
            user.id,
        )
        return user
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to create or update user: line_user_id=%s",
            cleaned_line_user_id,
        )
        raise


def start_exam_attempt(
    line_user_id: str,
    subject: str,
    repo: str,
    question_count: int,
) -> ExamAttempt:
    """開始測驗時建立 exam_attempts 紀錄。"""
    user = get_or_create_user(line_user_id)

    attempt = ExamAttempt(
        user_id=user.id,
        subject=str(subject or "").strip(),
        repo=str(repo or "").strip() or None,
        question_count=max(int(question_count or 0), 0),
        correct_count=0,
        score_rate=0.0,
        status="in_progress",
        started_at=utc_now(),
    )

    try:
        db.session.add(attempt)
        db.session.commit()

        LOGGER.info(
            "Exam attempt created: attempt_id=%s user_id=%s subject=%s",
            attempt.id,
            user.id,
            attempt.subject,
        )
        return attempt
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to create exam attempt: line_user_id=%s subject=%s",
            line_user_id,
            subject,
        )
        raise


def save_answer_record(
    attempt_id: int,
    question: dict[str, Any],
    student_answer: str,
    correct_answer: str,
    is_correct: bool,
) -> AnswerRecord:
    """每答一題時保存題目快照與作答結果。"""
    if not attempt_id:
        raise ValueError("attempt_id cannot be empty.")

    question_number = int(
        question.get("題號")
        or question.get("question_number")
        or 0
    )

    if question_number <= 0:
        raise ValueError("question number must be greater than zero.")

    question_id = (
        question.get("題目ID")
        or question.get("question_id")
        or question.get("id")
    )

    record = AnswerRecord(
        attempt_id=int(attempt_id),
        question_number=question_number,
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
            "Answer saved: answer_id=%s attempt_id=%s question_number=%s correct=%s",
            record.id,
            record.attempt_id,
            record.question_number,
            record.is_correct,
        )
        return record
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to save answer: attempt_id=%s question_number=%s",
            attempt_id,
            question_number,
        )
        raise


def complete_exam_attempt(
    attempt_id: int,
    correct_count: int,
    question_count: int,
) -> ExamAttempt:
    """測驗完成後更新總分、正確率與完成時間。"""
    attempt = db.session.get(
        ExamAttempt,
        int(attempt_id),
    )

    if attempt is None:
        raise ValueError(
            f"Exam attempt not found: {attempt_id}"
        )

    total = max(int(question_count or 0), 0)
    correct = max(int(correct_count or 0), 0)

    if total > 0:
        score_rate = round(
            (correct / total) * 100,
            1,
        )
    else:
        score_rate = 0.0

    attempt.question_count = total
    attempt.correct_count = correct
    attempt.score_rate = score_rate
    attempt.status = "completed"
    attempt.completed_at = utc_now()

    try:
        db.session.commit()

        LOGGER.info(
            "Exam attempt completed: attempt_id=%s correct=%s total=%s rate=%s",
            attempt.id,
            correct,
            total,
            score_rate,
        )
        return attempt
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to complete exam attempt: attempt_id=%s",
            attempt_id,
        )
        raise



def discard_exam_attempt(attempt_id: int) -> bool:
    """
    刪除未完成的測驗紀錄。

    ExamAttempt 與 AnswerRecord / ExplanationRecord 已設定 cascade，
    因此刪除 attempt 時，該次尚未完成的作答與解析會一併移除。
    """
    if not attempt_id:
        return False

    attempt = db.session.get(
        ExamAttempt,
        int(attempt_id),
    )

    if attempt is None:
        return False

    try:
        db.session.delete(attempt)
        db.session.commit()

        LOGGER.info(
            "Exam attempt discarded: attempt_id=%s",
            attempt_id,
        )
        return True

    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to discard exam attempt: attempt_id=%s",
            attempt_id,
        )
        raise


def find_answer_record(
    attempt_id: int,
    question_number: int,
) -> AnswerRecord | None:
    """依測驗紀錄與題號尋找作答紀錄。"""
    return AnswerRecord.query.filter_by(
        attempt_id=int(attempt_id),
        question_number=int(question_number),
    ).first()


def save_explanation_record(
    answer_record_id: int,
    explanation_text: str,
    model_name: str | None = None,
) -> ExplanationRecord:
    """使用者取得 AI 解析後保存解析內容。"""
    cleaned_text = str(explanation_text or "").strip()

    if not cleaned_text:
        raise ValueError(
            "explanation_text cannot be empty."
        )

    record = ExplanationRecord(
        answer_record_id=int(answer_record_id),
        explanation_text=cleaned_text,
        model_name=(
            str(model_name).strip()
            if model_name
            else None
        ),
        created_at=utc_now(),
    )

    try:
        db.session.add(record)
        db.session.commit()

        LOGGER.info(
            "Explanation saved: explanation_id=%s answer_record_id=%s",
            record.id,
            record.answer_record_id,
        )
        return record
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to save explanation: answer_record_id=%s",
            answer_record_id,
        )
        raise
