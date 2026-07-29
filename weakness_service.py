import json
import logging
import os
import random
import re
import unicodedata
from collections import Counter
from typing import Any

from models import AnswerRecord, ExamAttempt, User


LOGGER = logging.getLogger(__name__)
RECENT_WRONG_LIMIT = 20
AI_ANALYSIS_LIMIT = 5
WEAKNESS_QUESTION_COUNT = 5
MIN_SIMILARITY_SCORE = 1


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
        # keywords 保留供系統內部題庫搜尋，不顯示給使用者。
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
        "關鍵字只供系統內部搜尋題庫使用。"
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

        response_content = response.choices[0].message.content
        if not response_content:
            raise ValueError("OpenAI returned empty weakness analysis.")

        data = json.loads(response_content)
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
            # 保留於分析資料中，後續題庫搜尋使用。
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
        # keywords 不顯示，但必須保留給開始弱點練習搜尋題目。
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


def normalize_search_text(value: Any) -> str:
    """將題目與關鍵字轉為穩定的比對格式。"""
    text = unicodedata.normalize(
        "NFKC",
        str(value or ""),
    ).lower()

    text = re.sub(r"\s+", " ", text)
    text = re.sub(
        r"[，。！？、；：,.!?;:()\[\]{}「」『』（）【】]",
        " ",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def get_question_text(question: dict[str, Any]) -> str:
    """相容常見題庫欄位名稱，取得題幹文字。"""
    for key in (
        "題目",
        "題幹",
        "question",
        "question_text",
        "題目內容",
    ):
        value = question.get(key)
        if value:
            return str(value).strip()
    return ""


def get_question_id(question: dict[str, Any]) -> str:
    """相容常見題庫欄位名稱，取得題目 ID。"""
    for key in (
        "question_id",
        "id",
        "ID",
        "題目ID",
        "題號ID",
    ):
        value = question.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def get_question_search_text(
    question: dict[str, Any],
) -> str:
    """合併題幹與選項文字，作為弱點相似題搜尋內容。"""
    parts: list[str] = [get_question_text(question)]

    for key in (
        "A",
        "B",
        "C",
        "D",
        "選項A",
        "選項B",
        "選項C",
        "選項D",
    ):
        value = question.get(key)
        if value:
            parts.append(str(value))

    options = question.get("options")
    if isinstance(options, dict):
        parts.extend(str(value) for value in options.values())
    elif isinstance(options, list):
        parts.extend(str(value) for value in options)

    return normalize_search_text(" ".join(parts))


def build_search_terms(
    analysis: dict[str, Any],
) -> list[str]:
    """
    建立內部相似題搜尋詞。

    優先使用 AI keywords，並加入 topic / subtopics，
    讓搜尋不會只依單一關鍵字。
    """
    raw_terms: list[Any] = []

    raw_terms.extend(
        analysis.get("keywords", [])
        if isinstance(analysis.get("keywords"), list)
        else []
    )

    topic = analysis.get("topic")
    if topic:
        raw_terms.append(topic)

    subtopics = analysis.get("subtopics", [])
    if isinstance(subtopics, list):
        raw_terms.extend(subtopics)

    terms: list[str] = []
    for item in raw_terms:
        normalized = normalize_search_text(item)
        if normalized and normalized not in terms:
            terms.append(normalized)

    return terms


def is_excluded_question(
    question: dict[str, Any],
    analysis: dict[str, Any],
) -> bool:
    """排除弱點分析來源的原錯題。"""
    excluded_ids = {
        str(value).strip()
        for value in analysis.get(
            "excluded_question_ids",
            [],
        )
        if str(value).strip()
    }

    excluded_texts = {
        normalize_search_text(value)
        for value in analysis.get(
            "excluded_question_texts",
            [],
        )
        if normalize_search_text(value)
    }

    question_id = get_question_id(question)
    question_text = normalize_search_text(
        get_question_text(question)
    )

    if question_id and question_id in excluded_ids:
        return True

    if question_text and question_text in excluded_texts:
        return True

    return False


def score_question_similarity(
    question: dict[str, Any],
    search_terms: list[str],
) -> int:
    """
    計算題目與弱點搜尋詞的簡單相似分數。

    每命中一個搜尋詞加 1 分；
    多詞命中者優先。
    """
    if not search_terms:
        return 0

    search_text = get_question_search_text(question)
    if not search_text:
        return 0

    score = 0

    for term in search_terms:
        if term and term in search_text:
            score += 1
            continue

        # 對較長中文/英文詞組再拆成 token，比對其中內容。
        tokens = re.findall(
            r"[a-z][a-z0-9_-]{2,}|[\u4e00-\u9fff]{2,6}",
            term,
        )

        token_hits = sum(
            1
            for token in tokens
            if token and token in search_text
        )

        if token_hits:
            score += token_hits

    return score


def select_weakness_questions(
    question_bank: list[dict[str, Any]],
    analysis: dict[str, Any],
    question_count: int = WEAKNESS_QUESTION_COUNT,
) -> dict[str, Any]:
    """
    依弱點分析從既有題庫選出練習題。

    規則：
    1. 排除原錯題。
    2. 依 AI 內部 keywords + topic + subtopics 搜尋相似題。
    3. 相似題 >= 5：從高相似度題目中選 5 題。
    4. 相似題 1-4：保留相似題，再由同科其他題隨機補滿。
    5. 相似題 0：由同科可用題目隨機選 5 題。
    6. AI 不產生新題，只使用既有 question_bank。
    """
    target_count = max(int(question_count or 0), 1)

    available_questions = [
        dict(question)
        for question in question_bank
        if isinstance(question, dict)
        and not is_excluded_question(
            question,
            analysis,
        )
    ]

    if not available_questions:
        return {
            "questions": [],
            "similar_count": 0,
            "fallback_count": 0,
            "search_terms": build_search_terms(analysis),
            "available_count": 0,
        }

    search_terms = build_search_terms(analysis)

    scored_questions: list[tuple[int, dict[str, Any]]] = []

    for question in available_questions:
        score = score_question_similarity(
            question,
            search_terms,
        )

        if score >= MIN_SIMILARITY_SCORE:
            scored_questions.append(
                (score, question)
            )

    # 先依分數由高至低，再在同分群內隨機，避免每次固定同一組。
    random.shuffle(scored_questions)
    scored_questions.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    similar_questions = [
        question
        for _, question in scored_questions
    ]

    selected: list[dict[str, Any]] = []

    if similar_questions:
        selected.extend(
            similar_questions[:target_count]
        )

    selected_object_ids = {
        id(question)
        for question in selected
    }

    if len(selected) < target_count:
        remaining_pool = [
            question
            for question in available_questions
            if id(question) not in selected_object_ids
            and question not in selected
        ]

        random.shuffle(remaining_pool)

        selected.extend(
            remaining_pool[
                : target_count - len(selected)
            ]
        )

    # 最後打散題序，避免所有相似度最高題永遠排在前面。
    random.shuffle(selected)

    similar_selected_count = sum(
        1
        for question in selected
        if score_question_similarity(
            question,
            search_terms,
        ) >= MIN_SIMILARITY_SCORE
    )

    fallback_count = max(
        len(selected) - similar_selected_count,
        0,
    )

    LOGGER.info(
        (
            "Weakness questions selected: "
            "requested=%s available=%s similar_pool=%s "
            "similar_selected=%s fallback=%s"
        ),
        target_count,
        len(available_questions),
        len(similar_questions),
        similar_selected_count,
        fallback_count,
    )

    return {
        "questions": selected,
        "similar_count": similar_selected_count,
        "fallback_count": fallback_count,
        # search_terms 僅供系統內部紀錄/除錯，不應直接呈現給使用者。
        "search_terms": search_terms,
        "available_count": len(available_questions),
    }


def format_weakness_analysis(
    analysis: dict[str, Any],
) -> str:
    """
    整理為可直接傳送到 LINE 的弱點分析報告。

    注意：
    keywords 仍保留於 analysis 供弱點練習搜尋，
    但不顯示在使用者畫面。
    """
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

    # 不顯示「題庫搜尋關鍵字」。
    # analysis["keywords"] 仍保留，供 select_weakness_questions() 使用。

    recommendation = str(analysis.get("recommendation", "")).strip()
    if recommendation:
        lines.extend(["", f"建議：{recommendation}"])

    lines.extend(
        [
            "",
            "輸入「開始弱點練習」進行 5 題練習。",
        ]
    )

    return "\n".join(lines).strip()
