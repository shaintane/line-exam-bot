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
    allowed: bool
    message: str
    user: dict[str, Any] | None = None


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.exception("Failed to load JSON file %s: %s", path, exc)
        return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except (TypeError, ValueError):
        return None


def normalize_user_record(key: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Accept both the legacy Chinese schema and the new English schema."""
    line_user_id = (
        raw.get("line_user_id")
        or raw.get("line_id")
        or raw.get("LINE_ID")
        or (key if str(key).startswith("U") else "")
    )
    return {
        "line_user_id": line_user_id,
        "student_id": raw.get("student_id") or raw.get("學號") or (key if not str(key).startswith("U") else ""),
        "name": raw.get("name") or raw.get("姓名") or "未命名使用者",
        "school": raw.get("school") or raw.get("學校") or "",
        "role": raw.get("role") or "student",
        "start_date": raw.get("start_date") or raw.get("起始日") or "",
        "end_date": raw.get("end_date") or raw.get("結束日") or "",
        "is_active": raw.get("is_active", True),
    }


def load_normalized_whitelist() -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for key, raw in load_json(WHITELIST_FILE).items():
        if not isinstance(raw, dict):
            continue
        record = normalize_user_record(str(key), raw)
        line_user_id = record["line_user_id"]
        if line_user_id:
            normalized[line_user_id] = record
    return normalized


def is_admin(user_id: str) -> bool:
    admin_ids = {
        value.strip()
        for value in os.getenv("ADMIN_LINE_USER_IDS", "").split(",")
        if value.strip()
    }
    return user_id in admin_ids


def check_user_access(user_id: str, today: date | None = None) -> AccessResult:
    if is_admin(user_id):
        return AccessResult(True, "", {"line_user_id": user_id, "role": "admin", "name": "管理者"})

    user = load_normalized_whitelist().get(user_id)
    if not user:
        return AccessResult(False, "🔒 你的帳號尚未通過審核。請輸入「註冊」開始申請。")

    if not user.get("is_active", True):
        return AccessResult(False, "⛔ 此帳號目前已停用，請聯絡管理者。", user)

    start_date = parse_date(user.get("start_date", ""))
    end_date = parse_date(user.get("end_date", ""))
    if not start_date or not end_date:
        return AccessResult(False, "⚠️ 帳號使用期限設定有誤，請聯絡管理者。", user)

    current_date = today or date.today()
    if current_date < start_date:
        return AccessResult(False, f"⏳ 帳號將於 {start_date.isoformat()} 開放使用。", user)
    if current_date > end_date:
        return AccessResult(False, f"⌛ 帳號使用期限已於 {end_date.isoformat()} 結束。", user)

    return AccessResult(True, "", user)
