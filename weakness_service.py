import json
import logging
import os
import re
from collections import Counter
from typing import Any

from models import AnswerRecord, ExamAttempt, User


LOGGER = logging.getLogger(__name__)
RECENT_WRONG_LIMIT = 20
AI_ANALYSIS_LIMIT = 5


def get_recent_wrong_answers(
    line_user_id: str,
    limit: int = RECENT_WRONG_LIMIT,
) -> list[dict[str, Any]]:
    """取得使用者最近答錯的題目，依作答時間由新到舊排序。"""
    cleaned_user_id = str(line_user_id or "").strip()

    if not cleaned_user_id:
        return []

    user = User.query.filter_by(
        line_user_id=cleaned_user_id
    ).first()

    if user is None:
        return []

    records = (
        AnswerRecord.query
        .join(
            ExamAttempt,
            AnswerRecord.attempt_id == ExamAttempt.id,
        )
        .filter(
            ExamAttempt.user_id == user.id,
            ExamAttempt.status == "completed",
            AnswerRecord.is_correct.is_(False),
        )
        .order_by(
            AnswerRecord.answered_at.desc(),
            AnswerRecord.id.desc(),
        )
        .limit(max(int(limit or 0), 1))
        .all()
    )

    results: list[dict[str, Any]] = []

    for record in records:
        attempt = record.attempt
        results.append(
            {
                "answer_record_id": record.id,
                "attempt_id": record.attempt_id,
                "subject": str(
                    attempt.subject or "未分類科目"
                ).strip(),
                "repo": str(attempt.repo or "").strip(),
                "question_number": int(
                    record.question_number or 0
                ),
                "question_id": (
                    str(record.question_id).strip()
                    if record.question_id
                    else ""
                ),
                "question_text": str(
                    record.question_text or ""
                ).strip(),
                "options": record.options_json or [],
                "student_answer": str(
                    record.student_answer or ""
                ).strip(),
                "correct_answer": str(
                    record.correct_answer or ""
                ).strip(),
                "answered_at": (
                    record.answered_at.isoformat()
                    if record.answered_at
                    else ""
                ),
            }
        )

    return results


def choose_priority_subject(
    wrong_answers: list[dict[str, Any]],
) -> tuple[str, int]:
    """依近期錯題數選出優先科目；同分時以最近出現者優先。"""
    if not wrong_answers:
        return "", 0

    counts = Counter(
        str(item.get("subject", "未分類科目"))
        for item in wrong_answers
    )
    highest_count = max(counts.values())

    for item in wrong_answers:
        subject = str(item.get("subject", "未分類科目"))
        if counts[subject] == highest_count:
            return subject, highest_count

    return "", 0


def clean_text(value: Any) -> str:
    """清除 Markdown 與主動延伸句。"""
    text = str(value or "").strip()

    extension_phrases = (
        "如果你要",
        "如果你需要",
        "如果你願意",
        "我也可以",
        "我可以幫你",
        "需要我幫你",
        "要不要我",
        "如有需要",
        "歡迎再詢問",
    )

    cut_position = len(text)
    for phrase in extension_phrases:
        position = text.find(phrase)
        if position != -1:
            cut_position = min(cut_position, position)

    text = text[:cut_position]
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^\s*[-_*]{3,}\s*$", "", text)
    text = re.sub(r"(?m)^\s*[-*•]+\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fallback_topic_analysis(
    subject_wrong_answers: list[dict[str, Any]],
) -> dict[str, Any]:
    """AI 分析失敗時的保守回退結果。"""
    keywords: list[str] = []

    for item in subject_wrong_answers[:AI_ANALYSIS_LIMIT]:
        question_text = str(item.get("question_text", "")).strip()

        for token in re.findall(
            r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,6}",
            question_text,
        ):
            token = token.strip()
            if (
                token
                and token not in keywords
                and token not in {
                    "下列何者",
                    "何者正確",
                    "何者錯誤",
                    "有關下列",
                    "最適當",
                    "最可能",
                }
            ):
                keywords.append(token)

            if len(keywords) >= 8:
                break

        if len(keywords) >= 8:
            break

    return {
        "topic": "近期錯題概念整合",
        "subtopics": ["需重新檢視近期錯題涉及的核心概念"],
        "keywords": keywords[:8],
        "recommendation": (
            "建議先從近期錯題最多的科目開始，"
            "優先練習相同概念與相近題型。"
        ),
    }


def analyze_wrong_answer_topics(
    client,
    subject: str,
    subject_wrong_answers: list[dict[str, Any]],
) -> dict[str, Any]:
    """使用 Structured Outputs 分析錯題共同主題。"""
    selected = subject_wrong_answers[:AI_ANALYSIS_LIMIT]

    if not selected:
        return fallback_topic_analysis(subject_wrong_answers)

    model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
    items_text: list[str] = []

    for index, item in enumerate(selected, start=1):
        items_text.append(
            (
                f"錯題 {index}\n"
                f"題目：{item.get('question_text', '')}\n"
                f"學生答案：{item.get('student_answer', '')}\n"
                f"正確答案：{item.get('correct_answer', '')}"
            )
        )

    schema = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "最主要的共同弱點主題。",
            },
            "subtopics": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 3,
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 8,
            },
            "recommendation": {
                "type": "string",
                "description": "一句學習建議。",
            },
        },
        "required": [
            "topic",
            "subtopics",
            "keywords",
            "recommendation",
        ],
        "additionalProperties": False,
    }

    system_message = (
        "你是醫事檢驗師國家考試學習診斷助手。"
        "只分析提供的錯題，不產生新題目。"
        "請找出共同弱點主題、具體概念與可用於題庫搜尋的關鍵字。"
        "不得使用 Markdown，不得提供後續邀請或額外服務。"
        "使用繁體中文。"
    )

    user_message = f"科目：{subject}\n\n" + "\n\n".join(items_text)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "weakness_analysis",
                    "description": "近期錯題弱點分析",
                    "strict": True,
                    "schema": schema,
                },
            },
            timeout=30,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty weakness analysis.")

        data = json.loads(content)
        topic = clean_text(data.get("topic", ""))
        subtopics = [
            clean_text(item)
            for item in data.get("subtopics", [])
            if clean_text(item)
        ]
        keywords = [
            clean_text(item)
            for item in data.get("keywords", [])
            if clean_text(item)
        ]
        recommendation = clean_text(data.get("recommendation", ""))

        if not topic or not subtopics or not keywords:
            raise ValueError("Weakness analysis missing usable fields.")

        return {
            "topic": topic,
            "subtopics": subtopics[:3],
            "keywords": keywords[:8],
            "recommendation": (
                recommendation
                or "建議優先練習近期錯題最多的科目。"
            ),
        }

    except Exception:
        LOGGER.exception(
            "Failed to analyze wrong-answer topics: subject=%s",
            subject,
        )
        return fallback_topic_analysis(subject_wrong_answers)


def build_weakness_analysis(
    line_user_id: str,
    client,
) -> dict[str, Any]:
    """建立完整弱點分析資料。"""
    wrong_answers = get_recent_wrong_answers(
        line_user_id,
        RECENT_WRONG_LIMIT,
    )

    if not wrong_answers:
        return {
            "has_data": False,
            "message": (
                "📊 目前沒有可供分析的錯題紀錄。\n"
                "完成測驗並產生錯題後，再輸入「弱點分析」。"
            ),
        }

    priority_subject, priority_count = choose_priority_subject(wrong_answers)
    subject_wrong_answers = [
        item
        for item in wrong_answers
        if item.get("subject") == priority_subject
    ]

    topic_analysis = analyze_wrong_answer_topics(
        client,
        priority_subject,
        subject_wrong_answers,
    )

    total_wrong = len(wrong_answers)
    priority_ratio = round((priority_count / total_wrong) * 100, 1)

    repo = ""
    for item in subject_wrong_answers:
        candidate_repo = str(item.get("repo", "")).strip()
        if candidate_repo:
            repo = candidate_repo
            break

    return {
        "has_data": True,
        "total_wrong": total_wrong,
        "priority_subject": priority_subject,
        "priority_wrong_count": priority_count,
        "priority_ratio": priority_ratio,
        "repo": repo,
        "topic": topic_analysis.get("topic", "近期錯題概念整合"),
        "subtopics": topic_analysis.get("subtopics", []),
        "keywords": topic_analysis.get("keywords", []),
        "recommendation": topic_analysis.get("recommendation", ""),
        "excluded_question_ids": [
            item.get("question_id", "")
            for item in subject_wrong_answers
            if item.get("question_id")
        ],
        "excluded_question_texts": [
            item.get("question_text", "")
            for item in subject_wrong_answers
            if item.get("question_text")
        ],
    }


def format_weakness_analysis(
    analysis: dict[str, Any],
) -> str:
    """整理為可直接傳送到 LINE 的弱點分析報告。"""
    if not analysis.get("has_data"):
        return str(
            analysis.get(
                "message",
                "目前沒有可供分析的錯題紀錄。",
            )
        )

    lines = [
        "📊 弱點分析結果",
        "",
        f"近期分析錯題：{analysis.get('total_wrong', 0)} 題",
        f"建議優先科目：{analysis.get('priority_subject', '')}",
        (
            f"該科錯題：{analysis.get('priority_wrong_count', 0)} 題，"
            f"占近期錯題 {analysis.get('priority_ratio', 0.0)}%"
        ),
        "",
        f"主要弱點主題：{analysis.get('topic', '')}",
    ]

    subtopics = analysis.get("subtopics", [])
    if subtopics:
        lines.extend(["", "主要弱點概念："])
        for index, subtopic in enumerate(subtopics, start=1):
            lines.append(f"{index}. {subtopic}")

    keywords = analysis.get("keywords", [])
    if keywords:
        lines.extend(["", "題庫搜尋關鍵字：", "、".join(keywords)])

    recommendation = str(analysis.get("recommendation", "")).strip()
    if recommendation:
        lines.extend(["", f"建議：{recommendation}"])

    lines.extend(["", "輸入「開始弱點練習」進行 5 題練習。"])
    return "\n".join(lines).strip()
