import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ReplyFirstLineBotApi:
    """
    相容既有 line_bot_api.push_message() 呼叫介面的事件級包裝器。

    同一個 webhook 事件中：
    1. 第一次 push_message() 改用 reply_message()
    2. reply token 只能使用一次
    3. 後續訊息才回退到真正的 push_message()

    這樣可在不大幅重寫 exam_logic.py、admin_logic.py 的前提下，
    將一般互動改為 reply message。
    """

    def __init__(
        self,
        base_api,
        reply_token: str | None,
    ) -> None:
        self._base_api = base_api
        self._reply_token = str(
            reply_token or ""
        ).strip()
        self._reply_used = False

    def push_message(
        self,
        to: str,
        messages: Any,
        *args,
        **kwargs,
    ) -> Any:
        """
        保留舊程式的 push_message 呼叫方式。

        第一次呼叫優先使用 reply_message；
        第二次之後才使用真正的 push_message。
        """
        if self._reply_token and not self._reply_used:
            self._reply_used = True

            try:
                LOGGER.info(
                    "Sending LINE reply message: user_id=%s",
                    to,
                )
                return self._base_api.reply_message(
                    self._reply_token,
                    messages,
                )
            except Exception:
                LOGGER.exception(
                    "LINE reply message failed; "
                    "falling back to push message: user_id=%s",
                    to,
                )

        LOGGER.info(
            "Sending LINE push message: user_id=%s",
            to,
        )
        return self._base_api.push_message(
            to,
            messages,
            *args,
            **kwargs,
        )

    def reply_message(
        self,
        reply_token: str,
        messages: Any,
        *args,
        **kwargs,
    ) -> Any:
        """允許新程式直接使用 reply_message。"""
        self._reply_used = True
        return self._base_api.reply_message(
            reply_token,
            messages,
            *args,
            **kwargs,
        )

    def __getattr__(self, name: str) -> Any:
        """其他 LINE SDK 方法交由原始 LineBotApi 處理。"""
        return getattr(
            self._base_api,
            name,
        )


# ---------------------------------------------------------------------------
# Quick Reply helpers (UX v1)
# ---------------------------------------------------------------------------
def build_quick_reply_text(text: str, items: list[tuple[str, str]]):
    """建立帶有 Quick Reply 的 LINE 文字訊息。

    items 格式：[(顯示文字, 實際送出的文字), ...]
    """
    from linebot.models import (
        MessageAction,
        QuickReply,
        QuickReplyButton,
        TextSendMessage,
    )

    quick_items = [
        QuickReplyButton(
            action=MessageAction(
                label=str(label),
                text=str(value),
            )
        )
        for label, value in items
    ]

    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=quick_items),
    )


def subject_quick_reply(text: str = "請選擇想練習的科目："):
    """六科選擇 Quick Reply。"""
    return build_quick_reply_text(
        text,
        [
            ("血清免疫", "臨床血清免疫學"),
            ("血液血庫", "臨床血液與血庫學"),
            ("生物化學", "臨床生物化學"),
            ("分子鏡檢", "醫學分子檢驗與鏡檢學"),
            ("生理病理", "臨床生理與病理學"),
            ("微生物", "臨床微生物學"),
        ],
    )


def question_count_quick_reply(text: str):
    """5 / 10 / 20 / 30 題 Quick Reply。"""
    return build_quick_reply_text(
        text,
        [
            ("5 題", "5"),
            ("10 題", "10"),
            ("20 題", "20"),
            ("30 題", "30"),
        ],
    )


def answer_quick_reply(text: str):
    """A / B / C / D 作答 Quick Reply。"""
    return build_quick_reply_text(
        text,
        [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
    )
