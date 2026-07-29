import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import func

from models import AnswerRecord, ExamAttempt, User


LOGGER = logging.getLogger(__name__)


def get_user_by_line_id(line_user_id: str) -> User | None:
    """依 LINE User ID 取得資料庫使用者。"""
    cleaned_user_id = str(line_user_id or "").strip()

    if not cleaned_user_id:
        return None

    return User.query.filter_by(
        line_user_id=cleaned_user_id
    ).first()


def calculate_learning_summary(
    line_user_id: str,
) -> dict[str, Any] | None:
    """
    彙整指定使用者的學習歷程。

    回傳內容：
    - 累積測驗次數
    - 累積答題數
    - 累積答對題數
    - 整體正確率
    - 各科答題數與正確率
    - 最近 5 次已完成測驗
    """
    user = get_user_by_line_id(line_user_id)

    if user is None:
        return None

    completed_attempts = (
        ExamAttempt.query
        .filter_by(
            user_id=user.id,
            status="completed",
        )
        .order_by(
            ExamAttempt.completed_at.desc(),
            ExamAttempt.id.desc(),
        )
        .all()
    )

    attempt_count = len(completed_attempts)

    aggregate = (
        AnswerRecord.query
        .join(
            ExamAttempt,
            AnswerRecord.attempt_id == ExamAttempt.id,
        )
        .filter(
            ExamAttempt.user_id == user.id,
            ExamAttempt.status == "completed",
        )
        .with_entities(
            func.count(AnswerRecord.id),
            func.sum(
                func.cast(
                    AnswerRecord.is_correct,
                    db_integer_type(),
                )
            ),
        )
        .first()
    )

    total_answers = int(
        aggregate[0] or 0
    ) if aggregate else 0

    total_correct = int(
        aggregate[1] or 0
    ) if aggregate else 0

    overall_rate = (
        round(
            (total_correct / total_answers) * 100,
            1,
        )
        if total_answers
        else 0.0
    )

    subject_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "attempt_count": 0,
            "question_count": 0,
            "correct_count": 0,
            "score_rate": 0.0,
        }
    )

    for attempt in completed_attempts:
        subject = str(
            attempt.subject or "未分類科目"
        ).strip()

        stats = subject_stats[subject]
        stats["attempt_count"] += 1
        stats["question_count"] += int(
            attempt.question_count or 0
        )
        stats["correct_count"] += int(
            attempt.correct_count or 0
        )

    for stats in subject_stats.values():
        question_count = int(
            stats["question_count"]
        )
        correct_count = int(
            stats["correct_count"]
        )

        stats["score_rate"] = (
            round(
                (correct_count / question_count) * 100,
                1,
            )
            if question_count
            else 0.0
        )

    recent_attempts = []

    for attempt in completed_attempts[:5]:
        completed_at = attempt.completed_at

        recent_attempts.append(
            {
                "attempt_id": attempt.id,
                "subject": attempt.subject,
                "question_count": int(
                    attempt.question_count or 0
                ),
                "correct_count": int(
                    attempt.correct_count or 0
                ),
                "score_rate": float(
                    attempt.score_rate or 0.0
                ),
                "completed_at": (
                    completed_at.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if completed_at
                    else ""
                ),
            }
        )

    return {
        "user": {
            "name": user.name or "未命名使用者",
            "school": user.school or "",
            "student_id": user.student_id or "",
            "status": user.status or "",
            "valid_from": (
                user.valid_from.isoformat()
                if user.valid_from
                else ""
            ),
            "valid_until": (
                user.valid_until.isoformat()
                if user.valid_until
                else ""
            ),
        },
        "attempt_count": attempt_count,
        "total_answers": total_answers,
        "total_correct": total_correct,
        "overall_rate": overall_rate,
        "subject_stats": dict(subject_stats),
        "recent_attempts": recent_attempts,
    }


def db_integer_type():
    """
    延遲匯入 SQLAlchemy Integer，避免模組頂端匯入過多名稱。
    PostgreSQL 可將 Boolean 轉為 Integer 進行加總。
    """
    from sqlalchemy import Integer

    return Integer


def format_learning_history(
    summary: dict[str, Any] | None,
) -> str:
    """將學習歷程彙整結果整理為 LINE 純文字。"""
    if not summary:
        return (
            "📊 目前尚無學習歷程資料。\n"
            "完成至少一次測驗後即可查看。"
        )

    attempt_count = int(
        summary.get("attempt_count", 0)
    )
    total_answers = int(
        summary.get("total_answers", 0)
    )
    total_correct = int(
        summary.get("total_correct", 0)
    )
    overall_rate = float(
        summary.get("overall_rate", 0.0)
    )

    if attempt_count == 0 or total_answers == 0:
        return (
            "📊 目前尚無已完成的測驗紀錄。\n"
            "完成至少一次測驗後即可查看學習歷程。"
        )

    lines = [
        "📊 個人學習歷程",
        "",
        f"累積測驗：{attempt_count} 次",
        f"累積作答：{total_answers} 題",
        f"累積答對：{total_correct} 題",
        f"整體正確率：{overall_rate}%",
    ]

    subject_stats = summary.get(
        "subject_stats",
        {},
    )

    if subject_stats:
        lines.extend(
            [
                "",
                "各科表現：",
            ]
        )

        sorted_subjects = sorted(
            subject_stats.items(),
            key=lambda item: (
                -int(
                    item[1].get(
                        "question_count",
                        0,
                    )
                ),
                item[0],
            ),
        )

        for subject, stats in sorted_subjects:
            question_count = int(
                stats.get("question_count", 0)
            )
            correct_count = int(
                stats.get("correct_count", 0)
            )
            score_rate = float(
                stats.get("score_rate", 0.0)
            )

            lines.append(
                f"{subject}："
                f"{correct_count}/{question_count} 題，"
                f"{score_rate}%"
            )

    recent_attempts = summary.get(
        "recent_attempts",
        [],
    )

    if recent_attempts:
        lines.extend(
            [
                "",
                "最近 5 次測驗：",
            ]
        )

        for index, attempt in enumerate(
            recent_attempts,
            start=1,
        ):
            subject = str(
                attempt.get(
                    "subject",
                    "未分類科目",
                )
            )
            correct_count = int(
                attempt.get("correct_count", 0)
            )
            question_count = int(
                attempt.get("question_count", 0)
            )
            score_rate = float(
                attempt.get("score_rate", 0.0)
            )
            completed_at = str(
                attempt.get("completed_at", "")
            )

            date_text = (
                completed_at.split(" ")[0]
                if completed_at
                else "日期不明"
            )

            lines.append(
                f"{index}. {date_text} {subject} "
                f"{correct_count}/{question_count} 題，"
                f"{score_rate}%"
            )

    return "\n".join(lines).strip()


def build_learning_history_message(
    line_user_id: str,
) -> str:
    """查詢並建立可直接傳送至 LINE 的學習歷程訊息。"""
    try:
        summary = calculate_learning_summary(
            line_user_id
        )
        return format_learning_history(summary)
    except Exception:
        LOGGER.exception(
            "Failed to build learning history: "
            "line_user_id=%s",
            line_user_id,
        )
        return (
            "⚠️ 學習歷程暫時無法讀取，"
            "請稍後再試。"
        )
