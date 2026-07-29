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
