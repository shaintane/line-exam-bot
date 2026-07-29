import logging
from datetime import date, datetime, timezone
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


def clean_optional_text(value: Any) -> str | None:
    """將可選文字欄位整理為字串；空白值回傳 None。"""
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


def get_or_create_user(
    line_user_id: str,
    *,
    name: str | None = None,
    school: str | None = None,
    student_id: str | None = None,
    role: str | None = None,
    status: str | None = None,
    valid_from: date | None = None,
    valid_until: date | None = None,
) -> User:
    """
    依 LINE User ID 取得或建立使用者。

    既有使用者只更新本次有提供的欄位，避免每次開始測驗時
    將已同步的角色、狀態及有效期限覆蓋回預設值。
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
            name=clean_optional_text(name),
            school=clean_optional_text(school),
            student_id=clean_optional_text(student_id),
            role=clean_optional_text(role) or "student",
            status=clean_optional_text(status) or "active",
            valid_from=valid_from,
            valid_until=valid_until,
        )
        db.session.add(user)
    else:
        cleaned_name = clean_optional_text(name)
        cleaned_school = clean_optional_text(school)
        cleaned_student_id = clean_optional_text(student_id)
        cleaned_role = clean_optional_text(role)
        cleaned_status = clean_optional_text(status)

        if cleaned_name is not None:
            user.name = cleaned_name

        if cleaned_school is not None:
            user.school = cleaned_school

        if cleaned_student_id is not None:
            user.student_id = cleaned_student_id

        if cleaned_role is not None:
            user.role = cleaned_role

        if cleaned_status is not None:
            user.status = cleaned_status

        if valid_from is not None:
            user.valid_from = valid_from

        if valid_until is not None:
            user.valid_until = valid_until

    try:
        db.session.commit()
        LOGGER.info(
            "User ready: line_user_id=%s database_user_id=%s status=%s",
            cleaned_line_user_id,
            user.id,
            user.status,
        )
        return user
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to create or update user: line_user_id=%s",
            cleaned_line_user_id,
        )
        raise


def sync_user_from_access(
    line_user_id: str,
    access: Any,
) -> User:
    """
    將 access_control.check_user_access() 的結果同步到 users 資料表。

    同步內容：
    - 姓名
    - 學校
    - 學號
    - 角色
    - 權限狀態
    - 使用起始日
    - 使用截止日
    """
    user_data = getattr(access, "user", None) or {}
    access_status = str(
        getattr(access, "status", "") or ""
    ).strip()

    database_status_map = {
        "admin": "active",
        "active": "active",
        "unapproved": "unapproved",
        "disabled": "disabled",
        "invalid_dates": "invalid_dates",
        "not_started": "not_started",
        "expired": "expired",
    }

    database_status = database_status_map.get(
        access_status,
        access_status or "unknown",
    )

    return get_or_create_user(
        line_user_id=line_user_id,
        name=user_data.get("name"),
        school=user_data.get("school"),
        student_id=user_data.get("student_id"),
        role=user_data.get("role"),
        status=database_status,
        valid_from=getattr(access, "valid_from", None),
        valid_until=getattr(access, "valid_until", None),
    )


def purge_user_history(
    line_user_id: str,
) -> dict[str, int]:
    """
    刪除指定使用者的所有學習歷程，但保留 users 基本資料。

    刪除範圍：
    - exam_attempts
    - answer_records
    - explanation_records

    因模型已設定 cascade，刪除每筆 ExamAttempt 時，
    所屬作答與解析會一併刪除。
    """
    cleaned_line_user_id = str(line_user_id or "").strip()

    if not cleaned_line_user_id:
        raise ValueError("line_user_id cannot be empty.")

    user = User.query.filter_by(
        line_user_id=cleaned_line_user_id
    ).first()

    if user is None:
        LOGGER.info(
            "History purge skipped; database user not found: line_user_id=%s",
            cleaned_line_user_id,
        )
        return {
            "attempts": 0,
            "answers": 0,
            "explanations": 0,
        }

    attempts = ExamAttempt.query.filter_by(
        user_id=user.id
    ).all()

    attempt_count = len(attempts)
    answer_count = sum(
        len(attempt.answer_records)
        for attempt in attempts
    )
    explanation_count = sum(
        len(answer.explanation_records)
        for attempt in attempts
        for answer in attempt.answer_records
    )

    try:
        for attempt in attempts:
            db.session.delete(attempt)

        user.status = "expired"
        db.session.commit()

        LOGGER.warning(
            "Expired user history purged: line_user_id=%s "
            "database_user_id=%s attempts=%s answers=%s explanations=%s",
            cleaned_line_user_id,
            user.id,
            attempt_count,
            answer_count,
            explanation_count,
        )

        return {
            "attempts": attempt_count,
            "answers": answer_count,
            "explanations": explanation_count,
        }
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to purge user history: line_user_id=%s",
            cleaned_line_user_id,
        )
        raise


def sync_access_and_apply_retention(
    line_user_id: str,
    access: Any,
) -> User | None:
    """
    同步權限資料，並套用到期資料保留規則。

    - active、admin、not_started、disabled、invalid_dates：
      同步使用者資料，不刪除歷程。
    - expired：
      同步狀態後，刪除全部測驗、作答與解析歷程。
    - unapproved 且資料庫從未建立此人：
      不建立空白使用者資料。
    """
    access_status = str(
        getattr(access, "status", "") or ""
    ).strip()

    if access_status == "unapproved":
        existing_user = User.query.filter_by(
            line_user_id=str(line_user_id or "").strip()
        ).first()

        if existing_user is None:
            return None

    user = sync_user_from_access(
        line_user_id,
        access,
    )

    if access_status == "expired":
        purge_user_history(line_user_id)

    return user


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
        raise ValueError(
            "question number must be greater than zero."
        )

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
        student_answer=str(
            student_answer or ""
        ).strip(),
        correct_answer=str(
            correct_answer or ""
        ).strip(),
        is_correct=bool(is_correct),
        answered_at=utc_now(),
    )

    try:
        db.session.add(record)
        db.session.commit()

        LOGGER.info(
            "Answer saved: answer_id=%s attempt_id=%s "
            "question_number=%s correct=%s",
            record.id,
            record.attempt_id,
            record.question_number,
            record.is_correct,
        )
        return record
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to save answer: attempt_id=%s "
            "question_number=%s",
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
            "Exam attempt completed: attempt_id=%s "
            "correct=%s total=%s rate=%s",
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
    cleaned_text = str(
        explanation_text or ""
    ).strip()

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
            "Explanation saved: explanation_id=%s "
            "answer_record_id=%s",
            record.id,
            record.answer_record_id,
        )
        return record
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to save explanation: "
            "answer_record_id=%s",
            answer_record_id,
        )
        raise
