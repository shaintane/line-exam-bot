import logging
import random
from typing import Any

from exam_logic import SUBJECTS, load_question_bank


LOGGER = logging.getLogger(__name__)

CHALLENGE_QUESTIONS_PER_SUBJECT = 5
CHALLENGE_SUBJECT_COUNT = 6
CHALLENGE_TOTAL_QUESTIONS = (
    CHALLENGE_QUESTIONS_PER_SUBJECT * CHALLENGE_SUBJECT_COUNT
)


class ChallengeQuestionBuildError(RuntimeError):
    """挑戰題組建立失敗。"""


def build_challenge_questions() -> list[dict[str, Any]]:
    """
    從六科題庫各隨機抽 5 題，合併為 30 題挑戰題組。

    每題會額外保存：
    - challenge_subject：原始科目
    - challenge_repo：原始 GitHub repo

    最後將 30 題整體洗牌，再重新編號 1～30。
    """
    if len(SUBJECTS) != CHALLENGE_SUBJECT_COUNT:
        raise ChallengeQuestionBuildError(
            "挑戰模式需要六個科目，目前 SUBJECTS 數量不符。"
        )

    selected_questions: list[dict[str, Any]] = []

    for subject, repo in SUBJECTS.items():
        question_bank = load_question_bank(repo)

        if not question_bank:
            LOGGER.error(
                "Challenge question bank unavailable: subject=%s repo=%s",
                subject,
                repo,
            )
            raise ChallengeQuestionBuildError(
                f"『{subject}』題庫載入失敗，無法開始挑戰。"
            )

        if len(question_bank) < CHALLENGE_QUESTIONS_PER_SUBJECT:
            LOGGER.error(
                "Challenge question bank too small: subject=%s repo=%s count=%s",
                subject,
                repo,
                len(question_bank),
            )
            raise ChallengeQuestionBuildError(
                f"『{subject}』題庫不足 "
                f"{CHALLENGE_QUESTIONS_PER_SUBJECT} 題，無法開始挑戰。"
            )

        subject_questions = random.sample(
            question_bank,
            CHALLENGE_QUESTIONS_PER_SUBJECT,
        )

        for question in subject_questions:
            item = dict(question)
            item["challenge_subject"] = subject
            item["challenge_repo"] = repo
            selected_questions.append(item)

    if len(selected_questions) != CHALLENGE_TOTAL_QUESTIONS:
        raise ChallengeQuestionBuildError(
            "挑戰題組數量異常，未達 30 題。"
        )

    random.shuffle(selected_questions)

    for index, question in enumerate(
        selected_questions,
        start=1,
    ):
        question["題號"] = index

    LOGGER.info(
        "Challenge question set built successfully: total=%s subjects=%s per_subject=%s",
        len(selected_questions),
        CHALLENGE_SUBJECT_COUNT,
        CHALLENGE_QUESTIONS_PER_SUBJECT,
    )

    return selected_questions


def validate_challenge_question_set(
    questions: list[dict[str, Any]],
) -> bool:
    """確認挑戰題組為六科各 5 題、總數 30 題。"""
    if len(questions) != CHALLENGE_TOTAL_QUESTIONS:
        return False

    subject_counts: dict[str, int] = {}

    for question in questions:
        subject = str(
            question.get("challenge_subject", "")
        ).strip()

        repo = str(
            question.get("challenge_repo", "")
        ).strip()

        if not subject or not repo:
            return False

        if subject not in SUBJECTS:
            return False

        if SUBJECTS[subject] != repo:
            return False

        subject_counts[subject] = (
            subject_counts.get(subject, 0) + 1
        )

    return all(
        subject_counts.get(subject, 0)
        == CHALLENGE_QUESTIONS_PER_SUBJECT
        for subject in SUBJECTS
    )
