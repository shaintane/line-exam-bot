# =============================================================
# V2 TEST VERSION
# Based on current production exam_logic.py uploaded by user.
# Added only:
# 1) QUESTION_BANK_BRANCH switch (default: main)
# 2) image URLs follow selected branch
# 3) single / multiple accepted / all-credit scoring support
# Old single-answer question banks remain compatible.
# =============================================================

import difflib
import json
import logging
import os
import random
import re
import time
from typing import Any

import requests
from linebot.models import (
    MessageAction,
    QuickReply,
    QuickReplyButton,
    TextSendMessage,
)
from messaging import answer_quick_reply, question_count_quick_reply
from flex_messages import build_exam_result_flex

from access_control import check_user_access
from history_service import (
    complete_exam_attempt,
    discard_exam_attempt,
    find_answer_record,
    save_answer_record,
    save_explanation_record,
    start_exam_attempt,
    sync_access_and_apply_retention,
)
from issue_report_service import create_issue_report


LOGGER = logging.getLogger(__name__)
GITHUB_OWNER = "shaintane"
QUESTION_BANK_BRANCH = os.getenv("QUESTION_BANK_BRANCH", "main").strip() or "main"

# 分科題庫分支設定：
# - 醫學分子檢驗與鏡檢學目前使用 v2-test
# - 其他科目維持 main
QUESTION_BANK_BRANCHES = {
    "exammolecu": "v2-test",
    "examimmun": "v2-test",
    "exmablood": "v2-test",
    "exambiochemicy": "v2-test",
    "exampatho": "v2-test",
    "exammicrbiog": "v2-test",
}


def get_question_bank_branch(repo: str) -> str:
    """回傳指定分科 repo 使用的 GitHub branch；未設定者使用 main。"""
    return QUESTION_BANK_BRANCHES.get(repo, "main")
NUM_QUESTIONS = 5
ALLOWED_QUESTION_COUNTS = {5, 10, 20, 30}
EXPLANATION_LIMIT = 3
EXAM_IDLE_TIMEOUT_SECONDS = 5 * 60

SUBJECTS = {
    "臨床血清免疫學": "examimmun",
    "臨床血液與血庫學": "exmablood",
    "臨床生物化學": "exambiochemicy",
    "醫學分子檢驗與鏡檢學": "exammolecu",
    "臨床生理與病理學": "exampatho",
    "臨床微生物學": "exammicrbiog",
}

ALIASES = {
    "微生物": "臨床微生物學",
    "微生": "臨床微生物學",
    "血庫": "臨床血液與血庫學",
    "血液": "臨床血液與血庫學",
    "分子": "醫學分子檢驗與鏡檢學",
    "免疫": "臨床血清免疫學",
    "生化": "臨床生物化學",
    "病理": "臨床生理與病理學",
}


def send_text(line_bot_api, user_id: str, text: str) -> None:
    """使用 push message 傳送文字訊息。"""
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=text),
    )




def explanation_quick_reply(
    text: str,
    question_count: int,
):
    """
    5 題測驗完成後提供題 1～題 5 的解析 Quick Reply。

    點擊後仍送出既有「題號N」指令，因此不改動 AI 解析核心。
    其他題數維持原本可手動輸入「題號N」的方式。
    """
    if int(question_count or 0) != 5:
        return TextSendMessage(text=text)

    items = [
        QuickReplyButton(
            action=MessageAction(
                label=f"題{number}",
                text=f"題號{number}",
            )
        )
        for number in range(1, 6)
    ]

    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=items),
    )


QUESTION_REPORT_CATEGORIES = {
    "答案疑似錯誤": "wrong_answer",
    "題目敘述有問題": "bad_question",
    "選項有問題": "bad_option",
    "圖片異常": "image_problem",
    "其他": "other",
}

AI_REPORT_CATEGORIES = {
    "解析內容疑似錯誤": "ai_wrong",
    "與題庫答案不一致": "ai_answer_mismatch",
    "解析不清楚": "ai_unclear",
    "遺漏重要內容": "ai_missing",
    "其他": "other",
}


def exam_result_quick_reply(
    text: str,
    question_count: int,
):
    """測驗完成後：題號解析按鈕 + 最後一個「回報問題」。"""
    if int(question_count or 0) != 5:
        return TextSendMessage(text=text)

    items = [
        QuickReplyButton(
            action=MessageAction(
                label=f"題{number}",
                text=f"題號{number}",
            )
        )
        for number in range(1, 6)
    ]
    items.append(
        QuickReplyButton(
            action=MessageAction(
                label="⚠️ 回報問題",
                text="回報問題",
            )
        )
    )

    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=items),
    )


def explanation_action_quick_reply(
    text: str,
    question_count: int,
    *,
    allow_more_explanations: bool,
    allow_ai_report: bool,
):
    """AI 解析完成後：題號在前，最後顯示「回報解析問題」。"""
    items = []

    if allow_more_explanations and int(question_count or 0) == 5:
        items.extend(
            QuickReplyButton(
                action=MessageAction(
                    label=f"題{number}",
                    text=f"題號{number}",
                )
            )
            for number in range(1, 6)
        )

    if allow_ai_report:
        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="🤖 回報解析問題",
                    text="回報解析問題",
                )
            )
        )

    if not items:
        return TextSendMessage(text=text)

    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=items),
    )


def question_report_question_quick_reply(
    question_count: int,
):
    """題目問題回報：先選擇要回報的題號；此階段不寫入資料庫。"""
    count = int(question_count or 0)
    if count <= 0:
        count = 5

    items = [
        QuickReplyButton(
            action=MessageAction(
                label=f"題{number}",
                text=f"回報題目|{number}",
            )
        )
        for number in range(1, min(count, 5) + 1)
    ]
    items.append(
        QuickReplyButton(
            action=MessageAction(
                label="↩️ 回測驗",
                text="回測驗|題目",
            )
        )
    )

    return TextSendMessage(
        text=(
            "⚠️ 回報問題\n\n"
            "請先選擇要回報的題號："
        ),
        quick_reply=QuickReply(items=items),
    )


def issue_category_quick_reply(
    *,
    report_type: str,
    question_number: int,
):
    """選擇問題分類；只有點選分類後才真正建立回報紀錄。"""
    if report_type == "question":
        categories = QUESTION_REPORT_CATEGORIES
        title = "⚠️ 回報問題"
        return_command = "回測驗|題目"
    elif report_type == "ai_explanation":
        categories = AI_REPORT_CATEGORIES
        title = "🤖 回報解析問題"
        return_command = "回測驗|解析"
    else:
        raise ValueError(f"unsupported report_type: {report_type}")

    items = [
        QuickReplyButton(
            action=MessageAction(
                label=label,
                text=f"問題回報分類|{code}",
            )
        )
        for label, code in categories.items()
    ]
    items.append(
        QuickReplyButton(
            action=MessageAction(
                label="↩️ 回測驗",
                text=return_command,
            )
        )
    )

    return TextSendMessage(
        text=(
            f"{title}\n"
            f"題號 {question_number}\n\n"
            "請選擇問題類型："
        ),
        quick_reply=QuickReply(items=items),
    )


def handle_question_report_question(
    *,
    question_number: int,
    user_id: str,
    line_bot_api,
    session: dict[str, Any],
) -> None:
    """題目回報選定題號後，建立暫存 context；尚不寫入 IssueReport。"""
    attempt_id = session.get("attempt_id")

    if not attempt_id:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 找不到本次測驗紀錄，暫時無法回報。",
        )
        return

    try:
        answer_record = find_answer_record(
            attempt_id=int(attempt_id),
            question_number=int(question_number),
        )
    except Exception:
        LOGGER.exception(
            "Failed to load answer record for question report: "
            "user_id=%s attempt_id=%s question=%s",
            user_id,
            attempt_id,
            question_number,
        )
        answer_record = None

    if answer_record is None:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 找不到這一題的作答紀錄，請重新操作。",
        )
        return

    session["issue_report_context"] = {
        "answer_record_id": answer_record.id,
        "explanation_record_id": None,
        "question_number": int(question_number),
        "pending_report_type": "question",
        "return_mode": "question",
    }

    line_bot_api.push_message(
        user_id,
        issue_category_quick_reply(
            report_type="question",
            question_number=int(question_number),
        ),
    )


def handle_ai_report_entry(
    *,
    user_id: str,
    line_bot_api,
    session: dict[str, Any],
) -> None:
    """針對剛完成的 AI 解析進入解析問題回報分類。"""
    context = session.get("issue_report_context")

    if not isinstance(context, dict):
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 目前沒有可回報的 AI 解析紀錄，請先查看題目解析。",
        )
        return

    answer_record_id = context.get("answer_record_id")
    explanation_record_id = context.get("explanation_record_id")
    question_number = int(context.get("question_number") or 0)

    if not answer_record_id or not explanation_record_id or question_number <= 0:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 目前的解析紀錄不完整，請重新查看該題 AI 解析後再回報。",
        )
        return

    context["pending_report_type"] = "ai_explanation"
    context["return_mode"] = "ai_explanation"

    line_bot_api.push_message(
        user_id,
        issue_category_quick_reply(
            report_type="ai_explanation",
            question_number=question_number,
        ),
    )


def handle_issue_report_category(
    *,
    category_code: str,
    user_id: str,
    line_bot_api,
    session: dict[str, Any],
) -> None:
    """最後選定分類時才建立 IssueReport。"""
    context = session.get("issue_report_context")

    if not isinstance(context, dict):
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 回報流程已失效，請重新操作。",
        )
        return

    report_type = str(
        context.get("pending_report_type", "")
    ).strip()

    if report_type == "question":
        allowed_codes = set(QUESTION_REPORT_CATEGORIES.values())
    elif report_type == "ai_explanation":
        allowed_codes = set(AI_REPORT_CATEGORIES.values())
    else:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 回報流程已失效，請重新操作。",
        )
        return

    cleaned_category = str(category_code or "").strip()

    if cleaned_category not in allowed_codes:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 無法辨識此問題分類，請重新操作。",
        )
        return

    explanation_record_id = context.get(
        "explanation_record_id"
    )

    try:
        report, created = create_issue_report(
            line_user_id=user_id,
            answer_record_id=int(context["answer_record_id"]),
            explanation_record_id=(
                int(explanation_record_id)
                if explanation_record_id
                else None
            ),
            report_type=report_type,
            issue_category=cleaned_category,
        )
    except Exception:
        LOGGER.exception(
            "Issue report creation failed: user_id=%s "
            "answer_record_id=%s report_type=%s category=%s",
            user_id,
            context.get("answer_record_id"),
            report_type,
            cleaned_category,
        )
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 問題回報暫時無法送出，請稍後再試。",
        )
        return

    context.pop("pending_report_type", None)

    if not created:
        send_text(
            line_bot_api,
            user_id,
            (
                "ℹ️ 這個問題您已經回報過，目前仍在處理中，"
                "不需要重複送出。"
            ),
        )
        return

    LOGGER.info(
        "Issue report submitted from LINE: "
        "report_id=%s user_id=%s",
        report.id,
        user_id,
    )

    send_text(
        line_bot_api,
        user_id,
        (
            "✅ 問題回報已收到\n\n"
            "管理員將進行確認，"
            "感謝協助提升題庫與 AI 解析品質。"
        ),
    )


def restore_exam_quick_reply(
    *,
    session: dict[str, Any],
    mode: str,
):
    """中途取消回報時，重新顯示原本的 Quick Reply。"""
    question_count = int(
        session.get("question_count") or 0
    )

    if mode == "ai_explanation":
        remaining = EXPLANATION_LIMIT - int(
            session.get("解析次數", 0) or 0
        )
        context = session.get("issue_report_context")
        allow_ai_report = (
            isinstance(context, dict)
            and bool(context.get("explanation_record_id"))
        )
        return explanation_action_quick_reply(
            "↩️ 已返回測驗。",
            question_count,
            allow_more_explanations=remaining > 0,
            allow_ai_report=allow_ai_report,
        )

    return exam_result_quick_reply(
        "↩️ 已返回測驗。",
        question_count,
    )



def normalize_answer(answer: str) -> str:
    """將全形、大小寫與句點等答案格式統一。"""
    return (
        answer.strip()
        .replace(".", "")
        .replace("．", "")
        .upper()
        .replace("Ａ", "A")
        .replace("Ｂ", "B")
        .replace("Ｃ", "C")
        .replace("Ｄ", "D")
    )


def get_accepted_answers(question: dict[str, Any]) -> list[str]:
    """取得單一、多答案或一律給分題目的可接受答案。"""
    scoring_rule = str(question.get("評分規則", "")).strip().lower()
    if scoring_rule in {"all_credit", "all-credit", "allcredit", "一律給分"}:
        return ["A", "B", "C", "D"]

    raw_answer = question.get("正解", "")
    if isinstance(raw_answer, (list, tuple, set)):
        raw_items = list(raw_answer)
    else:
        raw_text = str(raw_answer).strip()
        if not raw_text:
            return []
        raw_items = re.split(r"[,/、\s]+", raw_text)

    accepted: list[str] = []
    for item in raw_items:
        normalized = normalize_answer(str(item))
        if normalized in {"A", "B", "C", "D"} and normalized not in accepted:
            accepted.append(normalized)
    return accepted


def format_correct_answer(question: dict[str, Any]) -> str:
    """供 LINE 顯示及資料庫紀錄使用。"""
    scoring_rule = str(question.get("評分規則", "")).strip().lower()
    if scoring_rule in {"all_credit", "all-credit", "allcredit", "一律給分"}:
        return "一律給分"
    return "/".join(get_accepted_answers(question))


def is_correct_answer(question: dict[str, Any], student_answer: str) -> bool:
    """判斷學生答案是否屬於本題可接受答案。"""
    return normalize_answer(student_answer) in set(get_accepted_answers(question))


def match_subject_name(
    input_name: str,
    aliases: dict[str, str],
    subjects: dict[str, str],
) -> str | None:
    """依別名或相近文字判斷科目。"""
    normalized_input = input_name.strip()

    if normalized_input in aliases:
        normalized_input = aliases[normalized_input]

    if normalized_input in subjects:
        return normalized_input

    matches = difflib.get_close_matches(
        normalized_input,
        subjects.keys(),
        n=1,
        cutoff=0.4,
    )
    return matches[0] if matches else None


def github_headers() -> dict[str, str]:
    """建立 GitHub API request headers；GITHUB_TOKEN 為選用設定。"""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "line-exam-bot",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    return headers


def validate_question_bank(data: Any, repo: str, file_name: str) -> list[dict[str, Any]]:
    """確認題庫為 list，並過濾缺少必要欄位的題目。"""
    if not isinstance(data, list):
        LOGGER.error(
            "Question bank is not a list: repo=%s file=%s type=%s",
            repo,
            file_name,
            type(data).__name__,
        )
        return []

    valid_questions: list[dict[str, Any]] = []

    for index, question in enumerate(data, start=1):
        if not isinstance(question, dict):
            LOGGER.warning(
                "Skipping non-dict question: repo=%s file=%s index=%s",
                repo,
                file_name,
                index,
            )
            continue

        required_fields = ("題目", "選項", "正解")
        missing_fields = [field for field in required_fields if field not in question]

        if missing_fields:
            LOGGER.warning(
                "Skipping question with missing fields: repo=%s file=%s "
                "index=%s missing=%s",
                repo,
                file_name,
                index,
                missing_fields,
            )
            continue

        if not isinstance(question.get("選項"), list):
            LOGGER.warning(
                "Skipping question because options are not a list: "
                "repo=%s file=%s index=%s",
                repo,
                file_name,
                index,
            )
            continue

        valid_questions.append(question.copy())

    LOGGER.info(
        "Question bank validated: repo=%s file=%s total=%s valid=%s",
        repo,
        file_name,
        len(data),
        len(valid_questions),
    )
    return valid_questions


def load_question_bank(repo: str) -> list[dict[str, Any]]:
    """
    沿用原 main 版的 GitHub Contents API 載入方式，並加入：
    1. 詳細 Render log
    2. request timeout 與狀態檢查
    3. 題庫格式驗證
    4. optional GITHUB_TOKEN 支援
    """
    branch = get_question_bank_branch(repo)
    api_url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/contents"
        f"?ref={branch}"
    )

    try:
        LOGGER.info(
            "Loading question bank: repo=%s branch=%s url=%s",
            repo,
            branch,
            api_url,
        )

        response = requests.get(
            api_url,
            headers=github_headers(),
            timeout=15,
        )

        LOGGER.info(
            "GitHub contents response: repo=%s status=%s remaining=%s",
            repo,
            response.status_code,
            response.headers.get("X-RateLimit-Remaining", "unknown"),
        )

        if response.status_code != 200:
            LOGGER.error(
                "GitHub contents API failed: repo=%s status=%s body=%s",
                repo,
                response.status_code,
                response.text[:500],
            )
            return []

        files = response.json()

        if not isinstance(files, list):
            LOGGER.error(
                "GitHub contents response is not a list: repo=%s type=%s body=%s",
                repo,
                type(files).__name__,
                str(files)[:500],
            )
            return []

        candidate_files = [
            file_info
            for file_info in files
            if isinstance(file_info, dict)
            and str(file_info.get("name", "")).startswith("question_bank_")
            and str(file_info.get("name", "")).lower().endswith(".json")
        ]

        if not candidate_files:
            visible_names = [
                str(file_info.get("name", ""))
                for file_info in files
                if isinstance(file_info, dict)
            ]
            LOGGER.error(
                "No question_bank_*.json found: repo=%s files=%s",
                repo,
                visible_names,
            )
            return []

        # 若同時存在多個題庫檔，依檔名排序後取第一個，行為可預期。
        candidate_files.sort(key=lambda item: str(item.get("name", "")))
        file_info = candidate_files[0]
        file_name = str(file_info.get("name", ""))
        download_url = str(file_info.get("download_url", "")).strip()

        if not download_url:
            LOGGER.error(
                "Question bank download URL missing: repo=%s file=%s",
                repo,
                file_name,
            )
            return []

        raw_response = requests.get(
            download_url,
            headers={"User-Agent": "line-exam-bot"},
            timeout=15,
        )

        LOGGER.info(
            "Question bank download response: repo=%s file=%s status=%s",
            repo,
            file_name,
            raw_response.status_code,
        )

        raw_response.raise_for_status()
        question_bank = raw_response.json()

        validated = validate_question_bank(
            question_bank,
            repo=repo,
            file_name=file_name,
        )

        if validated:
            LOGGER.info(
                "Question bank loaded successfully: repo=%s file=%s questions=%s",
                repo,
                file_name,
                len(validated),
            )
        else:
            LOGGER.error(
                "Question bank has no usable questions: repo=%s file=%s",
                repo,
                file_name,
            )

        return validated

    except requests.Timeout:
        LOGGER.exception("Question bank request timed out: repo=%s", repo)
    except requests.RequestException:
        LOGGER.exception("Question bank HTTP request failed: repo=%s", repo)
    except ValueError:
        LOGGER.exception("Question bank JSON parsing failed: repo=%s", repo)
    except Exception:
        LOGGER.exception("Unexpected question bank loading error: repo=%s", repo)

    return []


def build_image_url(repo: str, image_path: Any) -> str:
    """依 GitHub repo 與題目圖片路徑產生 raw URL。"""
    if not image_path:
        return ""

    cleaned_path = str(image_path).strip().lstrip("/")
    if not cleaned_path:
        return ""

    branch = get_question_bank_branch(repo)
    return (
        f"https://raw.githubusercontent.com/"
        f"{GITHUB_OWNER}/{repo}/{branch}/{cleaned_path}"
    )


def format_question(question: dict[str, Any], index: int, repo: str) -> str:
    """將題目格式化為 LINE 文字訊息。"""
    question_text = str(question.get("題目", "")).strip()
    options = question.get("選項", [])
    option_text = "\n".join(str(option) for option in options)

    text = f"第 {index + 1} 題：{question_text}\n{option_text}"

    image_url = build_image_url(repo, question.get("圖片連結"))
    if image_url:
        text += f"\n\n{image_url}"

    return text


EXTENSION_PHRASES = (
    "如果你要",
    "如果你需要",
    "如果你願意",
    "如果需要",
    "如果願意",
    "若你要",
    "若你需要",
    "若你願意",
    "如有需要",
    "如需更多",
    "我也可以幫你",
    "我也可以",
    "我可以幫你",
    "我可以再幫你",
    "需要我幫你",
    "需要我再",
    "要不要我幫你",
    "歡迎再詢問",
    "歡迎繼續詢問",
)


def truncate_extension(text: str) -> str:
    """遇到主動延伸或邀請句時，刪除該句及其後全部文字。"""
    if not text:
        return ""

    cut_position = len(text)
    for phrase in EXTENSION_PHRASES:
        position = text.find(phrase)
        if position != -1:
            cut_position = min(cut_position, position)

    return text[:cut_position].strip()


def clean_plain_text(value: Any) -> str:
    """移除 Markdown、延伸邀請與不必要格式，保留純文字內容。"""
    if value is None:
        return ""

    text = truncate_extension(str(value))

    # 移除 Markdown 標題、粗斜體、反引號與分隔線。
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^\s*[-_*]{3,}\s*$", "", text)

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        line = re.sub(r"^[-*•]+\s*", "", line)
        if line:
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def first_sentence(text: str) -> str:
    """只保留第一個完整句子，供國考重點使用。"""
    cleaned = clean_plain_text(text)
    if not cleaned:
        return ""

    match = re.search(r"^.*?[。！？!?](?:\s|$)", cleaned, flags=re.S)
    if match:
        return match.group(0).strip()

    first_line = cleaned.splitlines()[0].strip()
    return first_line


def generate_explanation(
    client,
    question: dict[str, Any],
    student_answer: str,
) -> str | None:
    """
    以 Structured Outputs 取得固定欄位，再由 Python 組成 LINE 純文字。
    模型自由文字不會直接傳送給使用者。
    """
    accepted_answers = get_accepted_answers(question)
    correct_answer = format_correct_answer(question)
    question_text = str(question.get("題目", "")).strip()
    options = question.get("選項", [])
    model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()

    if not question_text or not isinstance(options, list) or not options or not accepted_answers:
        LOGGER.error("Explanation input incomplete: question=%s", question)
        return None

    option_text = "\n".join(str(option) for option in options)
    student_answer_normalized = normalize_answer(student_answer)

    response_schema = {
        "type": "object",
        "properties": {
            "core_explanation": {
                "type": "string",
                "description": "說明正確答案的判斷依據與必要背景知識。",
            },
            "option_analysis": {
                "type": "string",
                "description": "說明學生所選選項，並視需要辨析其他選項。",
            },
            "conclusion": {
                "type": "string",
                "description": "明確總結學生答案與正確答案的差異。",
            },
            "exam_tip": {
                "type": "string",
                "description": "一句國考鑑別或記憶重點。",
            },
        },
        "required": [
            "core_explanation",
            "option_analysis",
            "conclusion",
            "exam_tip",
        ],
        "additionalProperties": False,
    }

    system_message = (
        "你是一位專業且謹慎的醫事檢驗師國家考試解析教師。"
        "只解析目前這一題。題庫指定答案為本次評分答案。"
        "使用繁體中文，不得提供其他題目、比較表、額外教材、後續邀請或服務。"
        "不得詢問使用者是否需要更多內容。"
        "所有欄位只填解析內容，不要加入 Markdown、井字號、星號、分隔線或欄位標題。"
        "exam_tip 僅能有一句話。"
    )

    user_message = (
        f"題目：\n{question_text}\n\n"
        f"選項：\n{option_text}\n\n"
        f"學生作答：{student_answer_normalized}\n"
        f"題庫可接受答案：{correct_answer}\n\n"
        "請完整解析本題。核心解析需說明正解理由；"
        "選項辨析先處理學生所選答案，再視需要補充其他選項；"
        "結論需明確；國考重點只寫一句。"
    )

    try:
        LOGGER.info("Generating structured explanation: model=%s", model_name)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "exam_explanation",
                    "description": "醫事檢驗師國考單題解析",
                    "strict": True,
                    "schema": response_schema,
                },
            },
            timeout=30,
        )

        content = response.choices[0].message.content
        if not content:
            LOGGER.error("OpenAI returned empty structured explanation")
            return None

        data = json.loads(content)
        core = clean_plain_text(data.get("core_explanation", ""))
        option_analysis = clean_plain_text(data.get("option_analysis", ""))
        conclusion = clean_plain_text(data.get("conclusion", ""))
        exam_tip = first_sentence(str(data.get("exam_tip", "")))

        if not core or not conclusion or not exam_tip:
            LOGGER.error("Structured explanation missing required usable content: %s", data)
            return None

        result = (
            "正確"
            if student_answer_normalized in set(accepted_answers)
            else "錯誤"
        )

        explanation = (
            f"作答結果：{result}\n"
            f"正確答案：{correct_answer}\n\n"
            f"核心解析：\n{core}\n\n"
            f"選項辨析：\n{option_analysis or '本題無需額外辨析。'}\n\n"
            f"結論：\n{conclusion}\n\n"
            f"國考重點：\n{exam_tip}"
        )

        # 最後一道防線：整段再次移除延伸句及格式符號。
        explanation = clean_plain_text(explanation)

        LOGGER.info("Structured explanation generated successfully: model=%s", model_name)
        return explanation or None

    except json.JSONDecodeError:
        LOGGER.exception("Structured explanation JSON decoding failed")
    except Exception:
        LOGGER.exception("Failed to generate structured explanation")

    return None

def handle_explanation_request(
    user_input: str,
    user_id: str,
    line_bot_api,
    client,
    session: dict[str, Any],
) -> None:
    """處理「題號3」類型的解析要求。"""
    try:
        question_number_text = user_input.replace("題號", "", 1).strip()
        question_number = int(question_number_text)
    except (TypeError, ValueError):
        send_text(line_bot_api, user_id, "⚠️ 請輸入正確格式：題號3")
        return

    if session.get("解析次數", 0) >= EXPLANATION_LIMIT:
        send_text(
            line_bot_api,
            user_id,
            f"⚠️ 你已達到本次測驗解析上限（{EXPLANATION_LIMIT} 題）。",
        )
        return

    question = next(
        (
            item
            for item in session.get("questions", [])
            if item.get("題號") == question_number
        ),
        None,
    )
    answer = next(
        (
            item
            for item in session.get("answers", [])
            if item.get("題號") == question_number
        ),
        None,
    )

    if not question or not answer:
        send_text(
            line_bot_api,
            user_id,
            f"⚠️ 查無題號 {question_number} 的作答紀錄。",
        )
        return

    explanation = generate_explanation(
        client,
        question,
        str(answer.get("作答", "")),
    )

    if not explanation:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 無法生成解析，請稍後再試。",
        )
        return

    explanation = clean_plain_text(explanation)
    if not explanation:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 解析內容格式異常，請稍後再試。",
        )
        return

    saved_answer_record_id = None
    saved_explanation_record_id = None

    attempt_id = session.get("attempt_id")
    if attempt_id:
        try:
            answer_record = find_answer_record(
                attempt_id=int(attempt_id),
                question_number=question_number,
            )
            if answer_record:
                explanation_record = save_explanation_record(
                    answer_record_id=answer_record.id,
                    explanation_text=explanation,
                    model_name=os.getenv(
                        "OPENAI_MODEL",
                        "gpt-5-mini",
                    ).strip(),
                )
                saved_answer_record_id = answer_record.id
                saved_explanation_record_id = explanation_record.id
            else:
                LOGGER.warning(
                    "Explanation not persisted because answer record was not found: "
                    "attempt_id=%s question_number=%s",
                    attempt_id,
                    question_number,
                )
        except Exception:
            LOGGER.exception(
                "Explanation not persisted: user_id=%s attempt_id=%s question=%s",
                user_id,
                attempt_id,
                question_number,
            )

    if saved_answer_record_id and saved_explanation_record_id:
        session["issue_report_context"] = {
            "answer_record_id": saved_answer_record_id,
            "explanation_record_id": saved_explanation_record_id,
            "question_number": question_number,
        }
    else:
        session.pop("issue_report_context", None)

    session["解析次數"] = session.get("解析次數", 0) + 1

    text = f"📘 題號 {question_number} 解析：\n{explanation}"
    image_url = build_image_url(
        str(session.get("repo", "")),
        question.get("圖片連結"),
    )
    if image_url:
        text += f"\n\n🔗 圖片：{image_url}"

    remaining = EXPLANATION_LIMIT - session.get("解析次數", 0)

    if remaining > 0 and int(session.get("question_count") or 0) == 5:
        text += (
            f"\n\n🤖 尚可解析 {remaining} 題，"
            "請直接點選下方題號。"
        )

    line_bot_api.push_message(
        user_id,
        explanation_action_quick_reply(
            text,
            int(session.get("question_count") or 0),
            allow_more_explanations=remaining > 0,
            allow_ai_report=bool(
                saved_answer_record_id
                and saved_explanation_record_id
            ),
        ),
    )


def start_exam_with_questions(
    subject: str,
    repo: str,
    questions: list[dict[str, Any]],
    user_id: str,
    line_bot_api,
    user_sessions: dict[str, dict[str, Any]],
    intro_text: str | None = None,
    session_extra: dict[str, Any] | None = None,
) -> None:
    """
    使用已選好的題目建立標準測驗 session。

    一般隨機測驗與弱點練習都可共用這個函式，
    因此後續 A/B/C/D 作答、資料庫紀錄、完成統計與解析
    都沿用同一套既有流程。
    """
    usable_questions = [
        dict(question)
        for question in questions
        if isinstance(question, dict)
    ]

    if not usable_questions:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 目前沒有可使用的練習題目。",
        )
        return

    selected_count = len(usable_questions)

    for index, question in enumerate(
        usable_questions,
        start=1,
    ):
        question["題號"] = index

    attempt_id = None
    try:
        attempt = start_exam_attempt(
            line_user_id=user_id,
            subject=subject,
            repo=repo,
            question_count=selected_count,
        )
        attempt_id = attempt.id
    except Exception:
        LOGGER.exception(
            "Exam started without database record: "
            "user_id=%s subject=%s",
            user_id,
            subject,
        )

    session = {
        "repo": repo,
        "subject": subject,
        "questions": usable_questions,
        "question_count": selected_count,
        "attempt_id": attempt_id,
        "current": 0,
        "answers": [],
        "解析次數": 0,
        "completed": False,
        "last_activity_at": time.time(),
    }

    if session_extra:
        session.update(session_extra)

    user_sessions[user_id] = session

    first_question = usable_questions[0]
    first_message = format_question(
        first_question,
        0,
        repo,
    )

    heading = (
        intro_text.strip()
        if intro_text
        else (
            f"✅ 已選擇『{subject}』科目。\n"
            f"本次共 {selected_count} 題，開始測驗："
        )
    )

    line_bot_api.push_message(
        user_id,
        answer_quick_reply(
            f"{heading}\n\n{first_message}"
        ),
    )


def start_exam(
    subject: str,
    user_id: str,
    line_bot_api,
    user_sessions: dict[str, dict[str, Any]],
    question_count: int = NUM_QUESTIONS,
) -> None:
    """載入題庫、依使用者指定題數隨機抽題並建立一般測驗 session。"""
    if question_count not in ALLOWED_QUESTION_COUNTS:
        send_text(
            line_bot_api,
            user_id,
            "⚠️ 題數僅能選擇 5 / 10 / 20 / 30 題。",
        )
        return

    repo = SUBJECTS[subject]
    question_bank = load_question_bank(repo)

    if not question_bank:
        send_text(
            line_bot_api,
            user_id,
            (
                "⚠️ 題庫載入失敗。\n"
                "系統已記錄錯誤，請稍後再試或通知管理者。"
            ),
        )
        return

    selected_count = min(
        question_count,
        len(question_bank),
    )
    questions = random.sample(
        question_bank,
        selected_count,
    )

    intro_text = (
        f"✅ 已選擇『{subject}』科目。\n"
        f"本次共 {selected_count} 題，開始測驗："
    )

    if selected_count < question_count:
        intro_text = (
            f"✅ 已選擇『{subject}』科目。\n"
            f"題庫目前可用 {selected_count} 題，"
            f"將以 {selected_count} 題開始測驗："
        )

    start_exam_with_questions(
        subject=subject,
        repo=repo,
        questions=questions,
        user_id=user_id,
        line_bot_api=line_bot_api,
        user_sessions=user_sessions,
        intro_text=intro_text,
        session_extra={
            "exam_mode": "standard",
            "requested_question_count": question_count,
        },
    )


def handle_answer(
    user_input: str,
    user_id: str,
    line_bot_api,
    session: dict[str, Any],
) -> None:
    """處理 A/B/C/D 作答與測驗完成統計。"""
    question_count = int(
        session.get("question_count")
        or len(session.get("questions", []))
    )
    current_index = int(session.get("current", 0))

    if current_index >= question_count:
        session["completed"] = True
        send_text(
            line_bot_api,
            user_id,
            "📚 本次測驗已完成。請輸入「開始」選擇其他科目。",
        )
        return

    normalized_input = normalize_answer(user_input)

    if normalized_input not in {"A", "B", "C", "D"}:
        line_bot_api.push_message(
            user_id,
            answer_quick_reply(
                "⚠️ 請選擇 A / B / C / D 作答。"
            ),
        )
        return

    # 只有有效 A/B/C/D 作答才算一次活動並重設 5 分鐘閒置計時。
    session["last_activity_at"] = time.time()

    current_question = session["questions"][current_index]
    correct_answer = format_correct_answer(current_question)

    is_correct = is_correct_answer(current_question, normalized_input)

    session.setdefault("answers", []).append(
        {
            "題號": current_question.get("題號", current_index + 1),
            "作答": normalized_input,
            "正解": correct_answer,
            "是否正確": is_correct,
        }
    )

    attempt_id = session.get("attempt_id")
    if attempt_id:
        try:
            save_answer_record(
                attempt_id=int(attempt_id),
                question=current_question,
                student_answer=normalized_input,
                correct_answer=correct_answer,
                is_correct=is_correct,
            )
        except Exception:
            # 作答仍保留於目前 session；資料庫失敗不阻斷測驗。
            LOGGER.exception(
                "Answer not persisted: user_id=%s attempt_id=%s question=%s",
                user_id,
                attempt_id,
                current_question.get("題號", current_index + 1),
            )

    session["current"] = current_index + 1

    if session["current"] < question_count:
        next_question = session["questions"][session["current"]]
        next_message = format_question(
            next_question,
            session["current"],
            str(session.get("repo", "")),
        )
        line_bot_api.push_message(
            user_id,
            answer_quick_reply(next_message),
        )
        return

    answers = session.get("answers", [])
    wrong_answers = [item for item in answers if not item.get("是否正確")]
    correct_count = len(answers) - len(wrong_answers)
    rate = round((correct_count / question_count) * 100, 1) if question_count else 0

    attempt_id = session.get("attempt_id")
    if attempt_id:
        try:
            complete_exam_attempt(
                attempt_id=int(attempt_id),
                correct_count=correct_count,
                question_count=question_count,
            )
        except Exception:
            LOGGER.exception(
                "Exam result not persisted: user_id=%s attempt_id=%s",
                user_id,
                attempt_id,
            )

    session["completed"] = True

    line_bot_api.push_message(
        user_id,
        build_exam_result_flex(
            subject=str(session.get("subject", "")),
            question_count=question_count,
            correct_count=correct_count,
            rate=rate,
            wrong_answers=wrong_answers,
            explanation_limit=EXPLANATION_LIMIT,
        ),
    )


def handle_exam_logic(
    user_input,
    user_id,
    event,
    line_bot_api,
    client,
    user_sessions,
    registration_buffer,
):
    """測驗流程主要入口；保留既有呼叫介面。"""
    del event
    del registration_buffer

    access = check_user_access(user_id)

    # 每次使用者操作時同步權限與期限。
    # 若 access.status == "expired"，history_service 會：
    # 1. 保留 users 基本資料
    # 2. 將使用者狀態設為 expired
    # 3. 刪除全部測驗、作答、錯題及 AI 解析歷程
    try:
        sync_access_and_apply_retention(
            user_id,
            access,
        )
    except Exception:
        # 資料庫同步失敗時保留原本權限判定，
        # 避免資料庫暫時異常造成整個 LINE Bot 中斷。
        LOGGER.exception(
            "Failed to synchronize access and retention: "
            "user_id=%s status=%s",
            user_id,
            getattr(access, "status", "unknown"),
        )

    if not access.allowed:
        # 已過期者同時清除記憶體中的測驗 session，
        # 避免日後重新核准時沿用舊測驗。
        if getattr(access, "status", "") == "expired":
            user_sessions.pop(user_id, None)

        send_text(
            line_bot_api,
            user_id,
            access.message,
        )
        return

    cleaned_input = str(user_input).strip()
    session = user_sessions.get(user_id)

    # ---------------------------------------------------------
    # 一般測驗 / 弱點練習：5 分鐘閒置逾時
    # ---------------------------------------------------------
    # 採 lazy timeout：不使用背景排程。
    # 使用者下一次互動時才檢查距離上次有效作答是否已超過 5 分鐘。
    # 挑戰模式不經由此流程，因此不受此規則影響。
    if (
        isinstance(session, dict)
        and not session.get("completed")
        and session.get("exam_mode") in {
            "standard",
            "weakness_practice",
        }
    ):
        last_activity_at = session.get("last_activity_at")

        try:
            idle_seconds = (
                time.time() - float(last_activity_at)
                if last_activity_at is not None
                else 0
            )
        except (TypeError, ValueError):
            idle_seconds = 0

        if idle_seconds > EXAM_IDLE_TIMEOUT_SECONDS:
            attempt_id = session.get("attempt_id")

            if attempt_id:
                try:
                    discard_exam_attempt(int(attempt_id))
                except Exception:
                    # 即使資料庫清除暫時失敗，仍先終止記憶體中的測驗，
                    # 避免使用者繼續作答舊 session。
                    LOGGER.exception(
                        "Timed-out exam attempt could not be discarded: "
                        "user_id=%s attempt_id=%s",
                        user_id,
                        attempt_id,
                    )

            user_sessions.pop(user_id, None)

            send_text(
                line_bot_api,
                user_id,
                (
                    "⏰ 本次測驗因閒置超過 5 分鐘已中斷。\n"
                    "本次未完成作答不列入學習歷程與弱點分析。\n\n"
                    "請輸入「開始」重新選擇測驗。"
                ),
            )
            return

    # ---------------------------------------------------------
    # 題目／答案問題回報：測驗完成畫面入口
    # ---------------------------------------------------------
    if cleaned_input == "回報問題":
        if not session or not session.get("completed"):
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 請先完成測驗後再使用問題回報。",
            )
            return

        line_bot_api.push_message(
            user_id,
            question_report_question_quick_reply(
                int(session.get("question_count") or 0)
            ),
        )
        return

    if cleaned_input.startswith("回報題目|"):
        if not session or not session.get("completed"):
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 回報流程已失效，請重新操作。",
            )
            return

        try:
            question_number = int(
                cleaned_input.split("|", 1)[1].strip()
            )
        except (TypeError, ValueError):
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 無法辨識題號，請重新操作。",
            )
            return

        handle_question_report_question(
            question_number=question_number,
            user_id=user_id,
            line_bot_api=line_bot_api,
            session=session,
        )
        return

    # ---------------------------------------------------------
    # AI 解析問題回報：只針對剛完成解析的題目
    # ---------------------------------------------------------
    if cleaned_input == "回報解析問題":
        if not session:
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 目前沒有可回報的 AI 解析紀錄。",
            )
            return

        handle_ai_report_entry(
            user_id=user_id,
            line_bot_api=line_bot_api,
            session=session,
        )
        return

    # 中途按「回測驗」不建立任何 IssueReport。
    if cleaned_input.startswith("回測驗|"):
        if not session:
            send_text(
                line_bot_api,
                user_id,
                "↩️ 已返回測驗。",
            )
            return

        mode_token = cleaned_input.split("|", 1)[1].strip()
        mode = (
            "ai_explanation"
            if mode_token == "解析"
            else "question"
        )

        context = session.get("issue_report_context")
        if isinstance(context, dict):
            context.pop("pending_report_type", None)

        line_bot_api.push_message(
            user_id,
            restore_exam_quick_reply(
                session=session,
                mode=mode,
            ),
        )
        return

    if cleaned_input.startswith("問題回報分類|"):
        if not session:
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 回報流程已失效，請重新操作。",
            )
            return

        category_code = cleaned_input.split("|", 1)[1].strip()
        handle_issue_report_category(
            category_code=category_code,
            user_id=user_id,
            line_bot_api=line_bot_api,
            session=session,
        )
        return

    # 「題號3」可在完成測驗後執行，因此必須先於新測驗判斷。
    if cleaned_input.startswith("題號"):
        if not session:
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 目前沒有可供解析的測驗紀錄。",
            )
            return

        handle_explanation_request(
            cleaned_input,
            user_id,
            line_bot_api,
            client,
            session,
        )
        return

    # 一般測驗：已選科目、等待使用者選擇題數。
    if session and session.get("pending_question_count"):
        try:
            selected_count = int(cleaned_input)
        except (TypeError, ValueError):
            selected_count = 0

        if selected_count not in ALLOWED_QUESTION_COUNTS:
            line_bot_api.push_message(
                user_id,
                question_count_quick_reply(
                    "請選擇本次測驗題數："
                ),
            )
            return

        subject = str(
            session.get("pending_subject", "")
        ).strip()

        if subject not in SUBJECTS:
            user_sessions.pop(user_id, None)
            send_text(
                line_bot_api,
                user_id,
                "⚠️ 科目設定已失效，請重新輸入「開始」選擇科目。",
            )
            return

        start_exam(
            subject=subject,
            user_id=user_id,
            line_bot_api=line_bot_api,
            user_sessions=user_sessions,
            question_count=selected_count,
        )
        return

    # 使用者輸入科目後，不立即出題；先進入題數選擇。
    if not session or session.get("completed"):
        subject = match_subject_name(
            cleaned_input,
            ALIASES,
            SUBJECTS,
        )

        if subject:
            existing_weakness = (
                session.get("weakness_analysis")
                if isinstance(session, dict)
                else None
            )

            pending_session = {
                "completed": True,
                "pending_question_count": True,
                "pending_subject": subject,
                "pending_repo": SUBJECTS[subject],
            }

            if existing_weakness:
                pending_session["weakness_analysis"] = existing_weakness

            user_sessions[user_id] = pending_session

            line_bot_api.push_message(
                user_id,
                question_count_quick_reply(
                    f"✅ 已選擇『{subject}』。\n\n"
                    "請選擇本次測驗題數："
                ),
            )
            return

        # 非科目文字由此結束，不額外回覆，避免干擾其他 handler。
        return

    # 測驗進行中時，只接受作答或解析指令。
    handle_answer(
        cleaned_input,
        user_id,
        line_bot_api,
        session,
    )
