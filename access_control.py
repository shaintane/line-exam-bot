import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
WHITELIST_FILE = BASE_DIR / "whitelist.json"
PENDING_FILE = BASE_DIR / "pending_register.json"
DATE_FORMAT = "%Y-%m-%d"


@dataclass(frozen=True)
class AccessResult:
    """
    使用者權限檢查結果。

    status 可能值：
    - admin
    - test_bypass
    - active
    - unapproved
    - disabled
    - invalid_dates
    - not_started
    - expired
    """

    allowed: bool
    message: str
    status: str
    user: dict[str, Any] | None = None
    valid_from: date | None = None
    valid_until: date | None = None


def load_json(path: Path) -> dict[str, Any]:
    """安全讀取 JSON 物件；檔案不存在或格式錯誤時回傳空字典。"""
    try:
        if not path.exists():
            return {}

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.exception(
            "Failed to load JSON file %s: %s",
            path,
            exc,
        )
        return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    """以暫存檔原子方式安全寫入 JSON。"""
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temp_path.replace(path)


def parse_date(value: Any) -> date | None:
    """將 YYYY-MM-DD 文字轉為 date；格式錯誤時回傳 None。"""
    try:
        return datetime.strptime(
            str(value).strip(),
            DATE_FORMAT,
        ).date()
    except (TypeError, ValueError):
        return None


def normalize_user_record(
    key: str,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """
    同時相容舊中文欄位與新英文欄位，
    並統一成資料庫可使用的英文欄位名稱。
    """
    line_user_id = (
        raw.get("line_user_id")
        or raw.get("line_id")
        or raw.get("LINE_ID")
        or (key if str(key).startswith("U") else "")
    )

    student_id = (
        raw.get("student_id")
        or raw.get("學號")
        or (key if not str(key).startswith("U") else "")
    )

    start_date = (
        raw.get("start_date")
        or raw.get("valid_from")
        or raw.get("起始日")
        or ""
    )

    end_date = (
        raw.get("end_date")
        or raw.get("valid_until")
        or raw.get("結束日")
        or ""
    )

    return {
        "line_user_id": str(line_user_id or "").strip(),
        "student_id": str(student_id or "").strip(),
        "name": str(
            raw.get("name")
            or raw.get("姓名")
            or "未命名使用者"
        ).strip(),
        "school": str(
            raw.get("school")
            or raw.get("學校")
            or ""
        ).strip(),
        "role": str(
            raw.get("role")
            or "student"
        ).strip(),
        "start_date": str(start_date or "").strip(),
        "end_date": str(end_date or "").strip(),
        "is_active": bool(
            raw.get("is_active", True)
        ),
    }


def load_normalized_whitelist() -> dict[str, dict[str, Any]]:
    """讀取 whitelist.json，並以 LINE User ID 為索引。"""
    normalized: dict[str, dict[str, Any]] = {}

    for key, raw in load_json(WHITELIST_FILE).items():
        if not isinstance(raw, dict):
            continue

        record = normalize_user_record(
            str(key),
            raw,
        )
        line_user_id = record["line_user_id"]

        if line_user_id:
            normalized[line_user_id] = record

    return normalized


def load_id_set_from_env(env_name: str) -> set[str]:
    """從逗號分隔的環境變數讀取 LINE User ID 集合。"""
    return {
        value.strip()
        for value in os.getenv(
            env_name,
            "",
        ).split(",")
        if value.strip()
    }


def is_admin(user_id: str) -> bool:
    """判斷 LINE User ID 是否列於管理者環境變數。"""
    return str(user_id or "").strip() in load_id_set_from_env(
        "ADMIN_LINE_USER_IDS"
    )


def is_test_bypass_user(user_id: str) -> bool:
    """
    判斷 LINE User ID 是否為測試 bypass 帳號。

    環境變數：
    TEST_BYPASS_LINE_USER_IDS

    多個帳號可用逗號分隔。
    """
    return str(user_id or "").strip() in load_id_set_from_env(
        "TEST_BYPASS_LINE_USER_IDS"
    )


def build_test_bypass_user(
    user_id: str,
) -> dict[str, Any]:
    """建立測試 bypass 帳號的標準使用者資料。"""
    return {
        "line_user_id": str(user_id or "").strip(),
        "student_id": "TEST",
        "name": "測試帳號",
        "school": "SYSTEM_TEST",
        "role": "test",
        "start_date": "",
        "end_date": "",
        "is_active": True,
    }


def check_user_access(
    user_id: str,
    today: date | None = None,
) -> AccessResult:
    """
    檢查使用者是否可進入測驗系統。

    判斷優先順序：
    1. 管理者
    2. 測試 bypass 帳號
    3. 正式 whitelist 使用者

    測試 bypass 帳號：
    - 不需註冊
    - 不需 approve
    - 不檢查起訖日期
    - 不會因期限判定為 expired
    - 可直接進入測驗系統

    正式使用者：
    結束日當天仍可使用；
    current_date > end_date 時才判定為 expired。
    """
    cleaned_user_id = str(user_id or "").strip()

    if is_admin(cleaned_user_id):
        admin_user = {
            "line_user_id": cleaned_user_id,
            "student_id": "",
            "name": "管理者",
            "school": "",
            "role": "admin",
            "start_date": "",
            "end_date": "",
            "is_active": True,
        }

        return AccessResult(
            allowed=True,
            message="",
            status="admin",
            user=admin_user,
        )

    if is_test_bypass_user(cleaned_user_id):
        test_user = build_test_bypass_user(
            cleaned_user_id
        )

        LOGGER.info(
            "Test bypass access granted: line_user_id=%s",
            cleaned_user_id,
        )

        return AccessResult(
            allowed=True,
            message="",
            status="test_bypass",
            user=test_user,
            valid_from=None,
            valid_until=None,
        )

    user = load_normalized_whitelist().get(
        cleaned_user_id
    )

    if not user:
        return AccessResult(
            allowed=False,
            message=(
                "🔒 你的帳號尚未通過審核。"
                "請輸入「註冊」開始申請。"
            ),
            status="unapproved",
        )

    start_date = parse_date(
        user.get("start_date", "")
    )
    end_date = parse_date(
        user.get("end_date", "")
    )

    if not user.get("is_active", True):
        return AccessResult(
            allowed=False,
            message="⛔ 此帳號目前已停用，請聯絡管理者。",
            status="disabled",
            user=user,
            valid_from=start_date,
            valid_until=end_date,
        )

    if not start_date or not end_date:
        return AccessResult(
            allowed=False,
            message="⚠️ 帳號使用期限設定有誤，請聯絡管理者。",
            status="invalid_dates",
            user=user,
            valid_from=start_date,
            valid_until=end_date,
        )

    current_date = today or date.today()

    if current_date < start_date:
        return AccessResult(
            allowed=False,
            message=(
                f"⏳ 帳號將於 "
                f"{start_date.isoformat()} 開放使用。"
            ),
            status="not_started",
            user=user,
            valid_from=start_date,
            valid_until=end_date,
        )

    if current_date > end_date:
        return AccessResult(
            allowed=False,
            message=(
                f"⌛ 帳號使用期限已於 "
                f"{end_date.isoformat()} 結束。"
            ),
            status="expired",
            user=user,
            valid_from=start_date,
            valid_until=end_date,
        )

    return AccessResult(
        allowed=True,
        message="",
        status="active",
        user=user,
        valid_from=start_date,
        valid_until=end_date,
    )
