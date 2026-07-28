import logging
from datetime import datetime

from linebot.models import TextSendMessage

from access_control import (
    DATE_FORMAT,
    PENDING_FILE,
    WHITELIST_FILE,
    is_admin,
    load_json,
    normalize_user_record,
    save_json,
)

LOGGER = logging.getLogger(__name__)


def send(line_bot_api, user_id: str, text: str) -> None:
    line_bot_api.push_message(user_id, TextSendMessage(text=text))


def valid_date_range(start_date: str, end_date: str) -> bool:
    try:
        start = datetime.strptime(start_date, DATE_FORMAT).date()
        end = datetime.strptime(end_date, DATE_FORMAT).date()
        return start <= end
    except ValueError:
        return False


def canonical_record(
    line_user_id: str,
    school: str,
    name: str,
    student_id: str,
    start_date: str,
    end_date: str,
    role: str = "student",
) -> dict:
    return {
        "line_user_id": line_user_id,
        "student_id": student_id,
        "name": name,
        "school": school,
        "role": role,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": True,
    }


def find_record_key(data: dict, target: str) -> str | None:
    for key, raw in data.items():
        if not isinstance(raw, dict):
            continue
        record = normalize_user_record(str(key), raw)
        if target in {record.get("line_user_id"), record.get("student_id")}:
            return key
    return None


def handle_admin_commands(user_input, user_id, line_bot_api, registration_buffer):
    user_input = user_input.strip()

    if user_input == "註冊":
        if is_admin(user_id):
            send(line_bot_api, user_id, "管理者帳號不需要註冊。")
            return True
        registration_buffer[user_id] = "awaiting_info"
        send(
            line_bot_api,
            user_id,
            "👋 請依下列格式輸入申請資料：\n\n"
            "學校 姓名 學號 起始日 結束日\n"
            "例如：國立醫學大學 王小明 A123456 2026-08-01 2026-12-31",
        )
        return True

    if user_id in registration_buffer:
        parts = user_input.split()
        if len(parts) != 5:
            send(line_bot_api, user_id, "⚠️ 格式錯誤，請輸入：學校 姓名 學號 起始日 結束日")
            return True

        school, name, student_id, start_date, end_date = parts
        if not valid_date_range(start_date, end_date):
            send(line_bot_api, user_id, "⚠️ 日期請使用 YYYY-MM-DD，且結束日不得早於起始日。")
            return True

        pending = load_json(PENDING_FILE)
        pending[user_id] = canonical_record(
            user_id, school, name, student_id, start_date, end_date
        )
        save_json(PENDING_FILE, pending)
        registration_buffer.pop(user_id, None)
        send(line_bot_api, user_id, "✅ 資料已送出，請等待管理者審核。")
        return True

    admin_prefixes = ("approve ", "input ", "delet ", "disable ", "enable ")
    is_admin_command = user_input in {"show whitelist", "show pending"} or user_input.startswith(admin_prefixes)
    if is_admin_command and not is_admin(user_id):
        send(line_bot_api, user_id, "⛔ 你沒有管理者權限。")
        LOGGER.warning("Unauthorized admin command from LINE user %s", user_id)
        return True

    if not is_admin(user_id):
        return False

    parts = user_input.split()

    if user_input.startswith("approve ") and len(parts) == 2:
        target = parts[1]
        pending = load_json(PENDING_FILE)
        key = find_record_key(pending, target)
        if not key:
            send(line_bot_api, user_id, "⚠️ 查無此學號或 LINE ID。")
            return True

        raw = pending.pop(key)
        record = normalize_user_record(key, raw)
        whitelist = load_json(WHITELIST_FILE)
        whitelist[record["line_user_id"]] = record
        save_json(WHITELIST_FILE, whitelist)
        save_json(PENDING_FILE, pending)
        send(line_bot_api, user_id, f"✅ 已核准 {record['name']}（{record['student_id']}）。")
        send(line_bot_api, record["line_user_id"], "✅ 帳號已通過審核，可以開始使用測驗系統。")
        return True

    if user_input.startswith("input ") and len(parts) == 7:
        _, school, name, student_id, start_date, end_date, target_line = parts
        if not target_line.startswith("U"):
            send(line_bot_api, user_id, "⚠️ LINE user ID 格式不正確，應以 U 開頭。")
            return True
        if not valid_date_range(start_date, end_date):
            send(line_bot_api, user_id, "⚠️ 日期格式或日期區間不正確。")
            return True

        whitelist = load_json(WHITELIST_FILE)
        whitelist[target_line] = canonical_record(
            target_line, school, name, student_id, start_date, end_date
        )
        save_json(WHITELIST_FILE, whitelist)
        send(line_bot_api, user_id, f"✅ 已手動新增 {name} 至白名單。")
        return True

    if user_input.startswith("delet ") and len(parts) == 2:
        whitelist = load_json(WHITELIST_FILE)
        key = find_record_key(whitelist, parts[1])
        if not key:
            send(line_bot_api, user_id, "⚠️ 查無此學號或 LINE ID。")
            return True
        removed = normalize_user_record(key, whitelist.pop(key))
        save_json(WHITELIST_FILE, whitelist)
        send(line_bot_api, user_id, f"🗑️ 已移除 {removed['name']}。")
        return True

    if user_input.startswith(("disable ", "enable ")) and len(parts) == 2:
        enabled = user_input.startswith("enable ")
        whitelist = load_json(WHITELIST_FILE)
        key = find_record_key(whitelist, parts[1])
        if not key:
            send(line_bot_api, user_id, "⚠️ 查無此學號或 LINE ID。")
            return True
        record = normalize_user_record(key, whitelist[key])
        record["is_active"] = enabled
        whitelist[record["line_user_id"]] = record
        if key != record["line_user_id"]:
            whitelist.pop(key, None)
        save_json(WHITELIST_FILE, whitelist)
        send(line_bot_api, user_id, f"✅ 已{'啟用' if enabled else '停用'} {record['name']}。")
        return True

    if user_input == "show whitelist":
        whitelist = load_json(WHITELIST_FILE)
        records = [normalize_user_record(str(k), v) for k, v in whitelist.items() if isinstance(v, dict)]
        if not records:
            send(line_bot_api, user_id, "📋 目前白名單為空。")
        else:
            lines = [
                f"{r['name']}（{r['student_id']}） {r['start_date']}～{r['end_date']} "
                f"{'啟用' if r['is_active'] else '停用'}"
                for r in records
            ]
            send(line_bot_api, user_id, "📋 白名單：\n" + "\n".join(lines))
        return True

    if user_input == "show pending":
        pending = load_json(PENDING_FILE)
        records = [normalize_user_record(str(k), v) for k, v in pending.items() if isinstance(v, dict)]
        if not records:
            send(line_bot_api, user_id, "📋 目前無待審核資料。")
        else:
            lines = [f"{r['name']}（{r['student_id']}） LINE ID：{r['line_user_id']}" for r in records]
            send(line_bot_api, user_id, "🕐 待審核清單：\n" + "\n".join(lines))
        return True

    return False
