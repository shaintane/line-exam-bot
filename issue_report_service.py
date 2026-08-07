import logging
from datetime import datetime, timezone
from typing import Iterable

from database import db
from models import (
    AnswerRecord,
    ExplanationRecord,
    IssueReport,
    User,
)


LOGGER = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

REPORT_TYPES = {
    "question",
    "ai_explanation",
}

QUESTION_CATEGORIES = {
    "wrong_answer",
    "bad_question",
    "bad_option",
    "image_problem",
    "other",
}

AI_CATEGORIES = {
    "ai_wrong",
    "ai_answer_mismatch",
    "ai_unclear",
    "ai_missing",
    "other",
}

OPEN_STATUSES = {
    "pending",
    "reviewing",
}


def normalize_report_type(value: str) -> str:
    cleaned = str(value or "").strip().lower()
    if cleaned not in REPORT_TYPES:
        raise ValueError(f"unsupported report_type: {cleaned}")
    return cleaned


def normalize_issue_category(
    report_type: str,
    value: str,
) -> str:
    cleaned = str(value or "").strip().lower()

    allowed = (
        QUESTION_CATEGORIES
        if report_type == "question"
        else AI_CATEGORIES
    )

    if cleaned not in allowed:
        raise ValueError(
            f"unsupported issue_category for {report_type}: {cleaned}"
        )

    return cleaned


def _find_owned_answer_record(
    line_user_id: str,
    answer_record_id: int,
) -> AnswerRecord:
    """取得屬於指定 LINE 使用者的作答紀錄。"""
    cleaned_line_user_id = str(line_user_id or "").strip()
    if not cleaned_line_user_id:
        raise ValueError("line_user_id cannot be empty.")

    answer = db.session.get(
        AnswerRecord,
        int(answer_record_id),
    )
    if answer is None:
        raise ValueError(
            f"AnswerRecord not found: {answer_record_id}"
        )

    attempt = answer.attempt
    user = attempt.user if attempt is not None else None

    if (
        user is None
        or user.line_user_id != cleaned_line_user_id
    ):
        raise PermissionError(
            "answer record does not belong to this LINE user."
        )

    return answer


def _resolve_explanation_record(
    answer: AnswerRecord,
    explanation_record_id: int | None,
) -> ExplanationRecord | None:
    """
    取得指定解析；若未指定，使用該題最新一筆解析。
    """
    if explanation_record_id:
        record = db.session.get(
            ExplanationRecord,
            int(explanation_record_id),
        )

        if (
            record is None
            or record.answer_record_id != answer.id
        ):
            raise ValueError(
                "explanation record does not belong to answer record."
            )

        return record

    return (
        ExplanationRecord.query
        .filter_by(answer_record_id=answer.id)
        .order_by(
            ExplanationRecord.created_at.desc(),
            ExplanationRecord.id.desc(),
        )
        .first()
    )


def find_open_duplicate(
    *,
    line_user_id: str,
    answer_record_id: int,
    report_type: str,
    issue_category: str,
) -> IssueReport | None:
    """
    同一使用者、同一作答、同一回報類型與分類，
    若仍 pending / reviewing，視為重複回報。
    """
    return (
        IssueReport.query
        .filter(
            IssueReport.line_user_id
            == str(line_user_id or "").strip(),
            IssueReport.answer_record_id
            == int(answer_record_id),
            IssueReport.report_type
            == str(report_type or "").strip(),
            IssueReport.issue_category
            == str(issue_category or "").strip(),
            IssueReport.status.in_(OPEN_STATUSES),
        )
        .order_by(IssueReport.created_at.desc())
        .first()
    )


def create_issue_report(
    *,
    line_user_id: str,
    answer_record_id: int,
    report_type: str,
    issue_category: str,
    explanation_record_id: int | None = None,
    user_comment: str | None = None,
) -> tuple[IssueReport, bool]:
    """
    建立問題回報。

    回傳：
    (IssueReport, created)

    created=False 代表已有相同 pending/reviewing 回報，
    不會再新增一筆。
    """
    cleaned_line_user_id = str(line_user_id or "").strip()
    cleaned_report_type = normalize_report_type(report_type)
    cleaned_category = normalize_issue_category(
        cleaned_report_type,
        issue_category,
    )

    answer = _find_owned_answer_record(
        cleaned_line_user_id,
        answer_record_id,
    )

    duplicate = find_open_duplicate(
        line_user_id=cleaned_line_user_id,
        answer_record_id=answer.id,
        report_type=cleaned_report_type,
        issue_category=cleaned_category,
    )
    if duplicate is not None:
        return duplicate, False

    explanation = None
    if cleaned_report_type == "ai_explanation":
        explanation = _resolve_explanation_record(
            answer,
            explanation_record_id,
        )
        if explanation is None:
            raise ValueError(
                "AI explanation report requires an explanation record."
            )
    elif explanation_record_id:
        # 題目／答案回報若有指定解析紀錄，也可一併保存快照。
        explanation = _resolve_explanation_record(
            answer,
            explanation_record_id,
        )

    attempt = answer.attempt
    user = attempt.user if attempt is not None else None

    record = IssueReport(
        user_id=user.id if user is not None else None,
        line_user_id=cleaned_line_user_id,
        answer_record_id=answer.id,
        explanation_record_id=(
            explanation.id
            if explanation is not None
            else None
        ),
        report_type=cleaned_report_type,
        issue_category=cleaned_category,
        subject=(
            str(attempt.subject or "").strip()
            if attempt is not None
            else None
        ),
        repo=(
            str(attempt.repo or "").strip() or None
            if attempt is not None
            else None
        ),
        question_number=answer.question_number,
        question_id=answer.question_id,
        question_text=answer.question_text,
        options_json=answer.options_json,
        student_answer=answer.student_answer,
        correct_answer=answer.correct_answer,
        ai_explanation=(
            explanation.explanation_text
            if explanation is not None
            else None
        ),
        user_comment=(
            str(user_comment).strip()
            if user_comment
            else None
        ),
        status="pending",
    )

    try:
        db.session.add(record)
        db.session.commit()

        LOGGER.info(
            "Issue report created: issue_report_id=%s "
            "line_user_id=%s answer_record_id=%s "
            "report_type=%s issue_category=%s",
            record.id,
            cleaned_line_user_id,
            answer.id,
            cleaned_report_type,
            cleaned_category,
        )
        return record, True

    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to create issue report: "
            "line_user_id=%s answer_record_id=%s",
            cleaned_line_user_id,
            answer.id,
        )
        raise


def count_issue_reports(
    statuses: Iterable[str] | None = None,
) -> int:
    """管理端後續可直接使用的回報數量查詢。"""
    query = IssueReport.query

    if statuses:
        cleaned_statuses = {
            str(item or "").strip()
            for item in statuses
            if str(item or "").strip()
        }
        if cleaned_statuses:
            query = query.filter(
                IssueReport.status.in_(cleaned_statuses)
            )

    return query.count()


VALID_ADMIN_STATUSES = {
    "pending",
    "reviewing",
    "resolved",
    "rejected",
}


def get_issue_report_counts() -> dict[str, int]:
    """回傳管理端各狀態回報數量。"""
    counts = {
        status: 0
        for status in VALID_ADMIN_STATUSES
    }

    rows = (
        db.session.query(
            IssueReport.status,
            db.func.count(IssueReport.id),
        )
        .group_by(IssueReport.status)
        .all()
    )

    for status, count in rows:
        cleaned_status = str(status or "").strip()
        if cleaned_status in counts:
            counts[cleaned_status] = int(count or 0)

    return counts


def list_issue_reports(
    *,
    status: str = "pending",
    limit: int = 8,
) -> list[IssueReport]:
    """依狀態列出最近的問題回報。"""
    cleaned_status = str(status or "").strip()

    if cleaned_status not in VALID_ADMIN_STATUSES:
        raise ValueError(
            f"unsupported issue report status: {cleaned_status}"
        )

    safe_limit = min(max(int(limit or 8), 1), 20)

    return (
        IssueReport.query
        .filter_by(status=cleaned_status)
        .order_by(
            IssueReport.created_at.desc(),
            IssueReport.id.desc(),
        )
        .limit(safe_limit)
        .all()
    )


def get_issue_report(
    report_id: int,
) -> IssueReport | None:
    """依 ID 取得單筆問題回報。"""
    return db.session.get(
        IssueReport,
        int(report_id),
    )


def update_issue_report_status(
    *,
    report_id: int,
    status: str,
    reviewed_by: str,
    admin_note: str | None = None,
) -> IssueReport:
    """更新管理端處理狀態。"""
    cleaned_status = str(status or "").strip()

    if cleaned_status not in VALID_ADMIN_STATUSES:
        raise ValueError(
            f"unsupported issue report status: {cleaned_status}"
        )

    record = get_issue_report(report_id)

    if record is None:
        raise ValueError(
            f"IssueReport not found: {report_id}"
        )

    record.status = cleaned_status
    record.reviewed_by = (
        str(reviewed_by or "").strip()
        or None
    )

    if admin_note is not None:
        cleaned_note = str(admin_note or "").strip()
        record.admin_note = cleaned_note or None

    if cleaned_status in {"resolved", "rejected"}:
        record.reviewed_at = utc_now()
    else:
        record.reviewed_at = None

    try:
        db.session.commit()

        LOGGER.info(
            "Issue report status updated: "
            "report_id=%s status=%s reviewed_by=%s",
            record.id,
            cleaned_status,
            record.reviewed_by,
        )
        return record

    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to update issue report status: "
            "report_id=%s status=%s",
            report_id,
            cleaned_status,
        )
        raise
