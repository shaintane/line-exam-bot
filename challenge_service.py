import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from database import db
from history_service import get_or_create_user
from models import (
    ChallengeAnswer,
    ChallengeAttempt,
    ChallengeProfile,
    User,
)


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



def finalize_expired_challenges(
    line_user_id: str,
) -> int:
    """
    將指定使用者已超過時間、仍停留在 in_progress 的挑戰自動結算為 timeout。

    規則：
    - 只處理 status == "in_progress"
    - 若 started_at + time_limit_seconds 已超時，則自動結算
    - timeout 的 elapsed_seconds 固定記為 time_limit_seconds
    - 已作答題目照實計分，未作答題目視為 0 分
    - 回傳本次自動結算的挑戰筆數
    """
    user = (
        User.query
        .filter_by(line_user_id=line_user_id)
        .first()
    )

    if user is None:
        return 0

    attempts = (
        ChallengeAttempt.query
        .filter_by(
            user_id=user.id,
            status="in_progress",
        )
        .all()
    )

    if not attempts:
        return 0

    now = utc_now()
    finalized_count = 0

    try:
        for attempt in attempts:
            started_at = normalize_datetime(attempt.started_at)
            time_limit = max(
                int(attempt.time_limit_seconds or 0),
                0,
            )

            if time_limit <= 0:
                continue

            elapsed = int(
                (now - started_at).total_seconds()
            )

            if elapsed < time_limit:
                continue

            answers = (
                ChallengeAnswer.query
                .filter_by(attempt_id=attempt.id)
                .all()
            )

            correct_count = sum(
                1
                for answer in answers
                if bool(answer.is_correct)
            )

            total = max(
                int(attempt.question_count or 0),
                0,
            )

            score_rate = (
                (correct_count / total) * 100
                if total > 0
                else 0.0
            )

            attempt.correct_count = correct_count
            attempt.score_rate = score_rate
            attempt.elapsed_seconds = time_limit
            attempt.status = "timeout"
            attempt.completed_at = (
                started_at
                + timedelta(
                    seconds=time_limit
                )
            )

            finalized_count += 1

        if finalized_count:
            db.session.commit()

            LOGGER.info(
                "Expired challenge attempts finalized: "
                "line_user_id=%s count=%s",
                line_user_id,
                finalized_count,
            )

        return finalized_count

    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to finalize expired challenges: "
            "line_user_id=%s",
            line_user_id,
        )
        raise



def get_challenge_profile(
    line_user_id: str,
) -> ChallengeProfile | None:
    """取得使用者挑戰暱稱資料。"""
    user = (
        User.query
        .filter_by(line_user_id=line_user_id)
        .first()
    )

    if user is None:
        return None

    return (
        ChallengeProfile.query
        .filter_by(user_id=user.id)
        .first()
    )


def set_challenge_nickname(
    line_user_id: str,
    nickname: str,
) -> ChallengeProfile:
    """
    建立或更新挑戰暱稱。

    暱稱：
    - 去除前後空白
    - 1～20 個字元
    - 不可與其他使用者重複
    """
    nickname = str(nickname or "").strip()

    if not nickname:
        raise ValueError("暱稱不可空白。")

    if len(nickname) > 20:
        raise ValueError("暱稱最多 20 個字元。")

    user = get_or_create_user(line_user_id)

    duplicate = (
        ChallengeProfile.query
        .filter(
            ChallengeProfile.nickname == nickname,
            ChallengeProfile.user_id != user.id,
        )
        .first()
    )

    if duplicate is not None:
        raise ValueError("這個暱稱已有人使用，請換一個暱稱。")

    profile = (
        ChallengeProfile.query
        .filter_by(user_id=user.id)
        .first()
    )

    if profile is None:
        profile = ChallengeProfile(
            user_id=user.id,
            nickname=nickname,
        )
        db.session.add(profile)
    else:
        profile.nickname = nickname
        profile.updated_at = utc_now()

    try:
        db.session.commit()
        LOGGER.info(
            "Challenge nickname saved: user_id=%s nickname=%s",
            line_user_id,
            nickname,
        )
        return profile
    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to save challenge nickname: user_id=%s",
            line_user_id,
        )
        raise


def _best_attempts_by_user() -> dict[int, ChallengeAttempt]:
    """
    取得每位使用者的歷史最佳挑戰。

    排序規則：
    1. correct_count 高者優先
    2. elapsed_seconds 短者優先
    3. 較早完成者優先
    """
    attempts = (
        ChallengeAttempt.query
        .filter(
            ChallengeAttempt.status.in_(
                ["completed", "timeout"]
            ),
            ChallengeAttempt.elapsed_seconds.isnot(None),
        )
        .all()
    )

    best_by_user: dict[int, ChallengeAttempt] = {}

    for attempt in attempts:
        current = best_by_user.get(attempt.user_id)

        if current is None:
            best_by_user[attempt.user_id] = attempt
            continue

        attempt_key = (
            -int(attempt.correct_count or 0),
            int(attempt.elapsed_seconds or 10**9),
            normalize_datetime(
                attempt.completed_at or attempt.started_at
            ),
        )
        current_key = (
            -int(current.correct_count or 0),
            int(current.elapsed_seconds or 10**9),
            normalize_datetime(
                current.completed_at or current.started_at
            ),
        )

        if attempt_key < current_key:
            best_by_user[attempt.user_id] = attempt

    return best_by_user


def get_challenge_leaderboard(
    limit: int = 10,
) -> list[dict[str, Any]]:
    """取得歷史排行榜；每位使用者只取最佳紀錄。"""
    limit = max(int(limit or 10), 1)
    best_by_user = _best_attempts_by_user()

    rows: list[dict[str, Any]] = []

    for user_id, attempt in best_by_user.items():
        profile = (
            ChallengeProfile.query
            .filter_by(user_id=user_id)
            .first()
        )

        nickname = (
            profile.nickname
            if profile is not None
            else "匿名挑戰者"
        )

        rows.append(
            {
                "user_id": user_id,
                "nickname": nickname,
                "correct_count": int(
                    attempt.correct_count or 0
                ),
                "question_count": int(
                    attempt.question_count
                    or CHALLENGE_QUESTION_COUNT
                ),
                "score_rate": float(
                    attempt.score_rate or 0.0
                ),
                "elapsed_seconds": int(
                    attempt.elapsed_seconds or 0
                ),
                "status": attempt.status,
                "attempt_id": attempt.id,
            }
        )

    rows.sort(
        key=lambda row: (
            -row["correct_count"],
            row["elapsed_seconds"],
            row["nickname"],
        )
    )

    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    return rows[:limit]


def get_personal_challenge_summary(
    line_user_id: str,
) -> dict[str, Any]:
    """取得個人最佳紀錄、名次與暱稱狀態。"""
    user = (
        User.query
        .filter_by(line_user_id=line_user_id)
        .first()
    )

    if user is None:
        return {
            "has_record": False,
            "has_profile": False,
        }

    profile = (
        ChallengeProfile.query
        .filter_by(user_id=user.id)
        .first()
    )

    best_by_user = _best_attempts_by_user()
    best = best_by_user.get(user.id)

    if best is None:
        return {
            "has_record": False,
            "has_profile": profile is not None,
            "nickname": (
                profile.nickname
                if profile is not None
                else None
            ),
        }

    ranked: list[ChallengeAttempt] = list(
        best_by_user.values()
    )
    ranked.sort(
        key=lambda attempt: (
            -int(attempt.correct_count or 0),
            int(attempt.elapsed_seconds or 10**9),
            int(attempt.user_id),
        )
    )

    rank = next(
        (
            index
            for index, attempt in enumerate(
                ranked,
                start=1,
            )
            if attempt.user_id == user.id
        ),
        None,
    )

    return {
        "has_profile": profile is not None,
        "nickname": (
            profile.nickname
            if profile is not None
            else None
        ),
        "has_record": True,
        "rank": rank,
        "correct_count": int(best.correct_count or 0),
        "question_count": int(
            best.question_count
            or CHALLENGE_QUESTION_COUNT
        ),
        "score_rate": float(best.score_rate or 0.0),
        "elapsed_seconds": int(
            best.elapsed_seconds or 0
        ),
        "status": best.status,
        "attempt_id": best.id,
    }



def discard_challenge_attempt(attempt_id: int) -> bool:
    """
    主動中斷挑戰時刪除尚未完成的 challenge attempt。

    只允許刪除 status == "in_progress" 的紀錄。
    先刪除該 attempt 的 ChallengeAnswer，再刪除 ChallengeAttempt，
    避免留下未完成挑戰與孤兒作答紀錄。
    """
    if not attempt_id:
        return False

    attempt = db.session.get(
        ChallengeAttempt,
        int(attempt_id),
    )

    if attempt is None:
        return False

    if str(attempt.status or "").strip() != "in_progress":
        return False

    try:
        (
            ChallengeAnswer.query
            .filter_by(attempt_id=attempt.id)
            .delete(synchronize_session=False)
        )

        db.session.delete(attempt)
        db.session.commit()

        LOGGER.info(
            "Challenge attempt discarded: attempt_id=%s",
            attempt_id,
        )
        return True

    except Exception:
        db.session.rollback()
        LOGGER.exception(
            "Failed to discard challenge attempt: attempt_id=%s",
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
