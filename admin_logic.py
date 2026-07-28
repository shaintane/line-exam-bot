import json
import os
from datetime import datetime

from linebot.models import TextSendMessage


WHITELIST_FILE = "whitelist.json"
PENDING_FILE = "pending_register.json"


def load_json(path):
    """讀取 JSON；檔案不存在或格式錯誤時回傳空字典。"""
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

        return {}

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    """安全寫入 JSON。"""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def send(line_bot_api, user_id, text):
    """傳送 LINE 文字訊息。"""
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=text),
    )


def get_admin_ids():
    """
    從 Render 環境變數取得管理者 LINE User ID。
    多位管理者請以逗號分隔。
    """
    raw_value = os.getenv("ADMIN_LINE_USER_IDS", "")

    return {
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    }


def is_admin(user_id):
    """判斷是否為管理者。"""
    return user_id in get_admin_ids()


def is_valid_date(date_string):
    """確認日期格式是否為 YYYY-MM-DD。"""
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalize_record(record, fallback_key=""):
    """
    將舊版中文欄位與新版英文欄位統一成標準格式。
    """
    if not isinstance(record, dict):
        record = {}

    line_user_id = (
        record.get("line_user_id")
        or record.get("line_id")
        or record.get("LINE_ID")
        or ""
    )

    student_id = (
        record.get("student_id")
        or record.get("學號")
        or fallback_key
        or ""
    )

    name = (
        record.get("name")
        or record.get("姓名")
        or ""
    )

    school = (
        record.get("school")
        or record.get("學校")
        or ""
    )

    start_date = (
        record.get("start_date")
        or record.get("起始日")
        or ""
    )

    end_date = (
        record.get("end_date")
        or record.get("結束日")
        or ""
    )

    role = record.get("role") or "student"

    is_active = record.get("is_active")

    if is_active is None:
        is_active = True

    return {
        "line_user_id": line_user_id,
        "student_id": student_id,
        "name": name,
        "school": school,
        "start_date": start_date,
        "end_date": end_date,
        "role": role,
        "is_active": bool(is_active),
    }


def find_record(data, target):
    """
    依 LINE User ID 或學號搜尋資料。
    回傳：(原始 key, 標準化 record)
    """
    for key, raw_record in data.items():
        record = normalize_record(raw_record, fallback_key=key)

        if (
            key == target
            or record["line_user_id"] == target
            or record["student_id"] == target
        ):
            return key, record

    return None, None


def format_pending_list(pending):
    """建立待審核清單文字。"""
    rows = []

    for key, raw_record in pending.items():
        record = normalize_record(raw_record, fallback_key=key)

        rows.append(
            f"{record['name']}（{record['student_id']}）"
            f" LINE ID：{record['line_user_id']}"
        )

    return "\n".join(rows)


def format_whitelist(whitelist):
    """建立白名單文字。"""
    rows = []

    for key, raw_record in whitelist.items():
        record = normalize_record(raw_record, fallback_key=key)

        status = "啟用" if record["is_active"] else "停用"

        rows.append(
            f"{record['name']}（{record['student_id']}） "
            f"{record['start_date']}～{record['end_date']} "
            f"{status}"
        )

    return "\n".join(rows)


def handle_admin_commands(
    user_input,
    user_id,
    line_bot_api,
    registration_buffer,
):
    """
    處理：
    1. 學生註冊
    2. 管理者審核
    3. 白名單管理

    有處理訊息時回傳 True；
    未處理時回傳 False。
    """
    user_input = user_input.strip()

    # ---------------------------------------------------------
    # 學生申請註冊
    # ---------------------------------------------------------
    if user_input in {"註冊", "申請", "我要註冊"}:
        registration_buffer[user_id] = "awaiting_info"

        send(
            line_bot_api,
            user_id,
            (
                "👋 請依下列格式輸入申請資料：\n\n"
                "學校 姓名 學號 起始日 結束日\n\n"
                "例如：\n"
                "國立醫學大學 王小明 A123456 "
                "2026-08-01 2026-12-31"
            ),
        )
        return True

    # ---------------------------------------------------------
    # 接收學生註冊資料
    # ---------------------------------------------------------
    if registration_buffer.get(user_id) == "awaiting_info":
        parts = user_input.split()

        if len(parts) != 5:
            send(
                line_bot_api,
                user_id,
                (
                    "⚠️ 格式錯誤，請輸入：\n"
                    "學校 姓名 學號 起始日 結束日"
                ),
            )
            return True

        school, name, student_id, start_date, end_date = parts

        if not is_valid_date(start_date) or not is_valid_date(end_date):
            send(
                line_bot_api,
                user_id,
                "⚠️ 日期格式必須為 YYYY-MM-DD。",
            )
            return True

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if end < start:
            send(
                line_bot_api,
                user_id,
                "⚠️ 結束日不可早於起始日。",
            )
            return True

        pending = load_json(PENDING_FILE)

        pending[user_id] = {
            "line_user_id": user_id,
            "student_id": student_id,
            "name": name,
            "school": school,
            "start_date": start_date,
            "end_date": end_date,
            "role": "student",
            "is_active": True,
        }

        save_json(PENDING_FILE, pending)

        registration_buffer.pop(user_id, None)

        send(
            line_bot_api,
            user_id,
            "✅ 資料已送出，請等待管理者審核。",
        )
        return True

    # ---------------------------------------------------------
    # 以下指令僅限管理者
    # ---------------------------------------------------------
    admin_command_prefixes = (
        "approve ",
        "input ",
        "delet ",
        "delete ",
        "disable ",
        "enable ",
    )

    is_admin_command = (
        user_input in {"show pending", "show whitelist"}
        or user_input.startswith(admin_command_prefixes)
    )

    if is_admin_command and not is_admin(user_id):
        send(
            line_bot_api,
            user_id,
            "⚠️ 你沒有管理者權限。",
        )
        return True

    if not is_admin(user_id):
        return False

    # ---------------------------------------------------------
    # 顯示待審核清單
    # ---------------------------------------------------------
    if user_input == "show pending":
        pending = load_json(PENDING_FILE)

        if not pending:
            send(
                line_bot_api,
                user_id,
                "📋 目前無待審核資料。",
            )
            return True

        send(
            line_bot_api,
            user_id,
            "⏱️ 待審核清單：\n" + format_pending_list(pending),
        )
        return True

    # ---------------------------------------------------------
    # 顯示白名單
    # ---------------------------------------------------------
    if user_input == "show whitelist":
        whitelist = load_json(WHITELIST_FILE)

        if not whitelist:
            send(
                line_bot_api,
                user_id,
                "📋 目前白名單為空。",
            )
            return True

        send(
            line_bot_api,
            user_id,
            "📋 白名單：\n" + format_whitelist(whitelist),
        )
        return True

    # ---------------------------------------------------------
    # 核准申請
    # 用法：approve 學號
    # 或：approve LINE_USER_ID
    # ---------------------------------------------------------
    if user_input.startswith("approve "):
        parts = user_input.split(maxsplit=1)

        if len(parts) != 2 or not parts[1].strip():
            send(
                line_bot_api,
                user_id,
                "⚠️ 請輸入：approve 學號",
            )
            return True

        target = parts[1].strip()

        pending = load_json(PENDING_FILE)
        pending_key, record = find_record(pending, target)

        if pending_key is None or record is None:
            send(
                line_bot_api,
                user_id,
                "⚠️ 查無此學號或 LINE User ID。",
            )
            return True

        line_user_id = record["line_user_id"]

        if not line_user_id:
            send(
                line_bot_api,
                user_id,
                "⚠️ 此筆資料缺少 LINE User ID，無法核准。",
            )
            return True

        whitelist = load_json(WHITELIST_FILE)

        whitelist[line_user_id] = record
        pending.pop(pending_key, None)

        save_json(WHITELIST_FILE, whitelist)
        save_json(PENDING_FILE, pending)

        send(
            line_bot_api,
            user_id,
            (
                f"✅ 已核准 {record['name']} "
                f"（{record['student_id']}）。"
            ),
        )

        # 通知學生；即使通知失敗，也不回滾核准結果
        try:
            send(
                line_bot_api,
                line_user_id,
                (
                    "✅ 帳號已通過審核！\n\n"
                    "歡迎使用國考解析助手。\n"
                    "請輸入「開始」進入測驗選單。"
                ),
            )
        except Exception as error:
            print(
                "Failed to notify approved user:",
                line_user_id,
                repr(error),
            )

            send(
                line_bot_api,
                user_id,
                (
                    "⚠️ 核准已完成，但無法傳送通知給學生。\n"
                    "請確認學生 LINE User ID 是否有效。"
                ),
            )

        return True

    # ---------------------------------------------------------
    # 管理者手動新增白名單
    #
    # input 學校 姓名 學號 起始日 結束日 LINE_ID
    # ---------------------------------------------------------
    if user_input.startswith("input "):
        parts = user_input.split()

        if len(parts) != 7:
            send(
                line_bot_api,
                user_id,
                (
                    "⚠️ 格式：\n"
                    "input 學校 姓名 學號 起始日 結束日 LINE_ID"
                ),
            )
            return True

        (
            _,
            school,
            name,
            student_id,
            start_date,
            end_date,
            target_line_id,
        ) = parts

        if not is_valid_date(start_date) or not is_valid_date(end_date):
            send(
                line_bot_api,
                user_id,
                "⚠️ 日期格式必須為 YYYY-MM-DD。",
            )
            return True

        if datetime.strptime(end_date, "%Y-%m-%d") < datetime.strptime(
            start_date,
            "%Y-%m-%d",
        ):
            send(
                line_bot_api,
                user_id,
                "⚠️ 結束日不可早於起始日。",
            )
            return True

        whitelist = load_json(WHITELIST_FILE)

        whitelist[target_line_id] = {
            "line_user_id": target_line_id,
            "student_id": student_id,
            "name": name,
            "school": school,
            "start_date": start_date,
            "end_date": end_date,
            "role": "student",
            "is_active": True,
        }

        save_json(WHITELIST_FILE, whitelist)

        send(
            line_bot_api,
            user_id,
            f"✅ 已手動新增 {name} 至白名單。",
        )
        return True

    # ---------------------------------------------------------
    # 刪除白名單
    # 支援 delet 與 delete
    # ---------------------------------------------------------
    if user_input.startswith("delet ") or user_input.startswith("delete "):
        parts = user_input.split(maxsplit=1)

        if len(parts) != 2 or not parts[1].strip():
            send(
                line_bot_api,
                user_id,
                "⚠️ 請輸入：delete 學號",
            )
            return True

        target = parts[1].strip()

        whitelist = load_json(WHITELIST_FILE)
        whitelist_key, record = find_record(whitelist, target)

        if whitelist_key is None or record is None:
            send(
                line_bot_api,
                user_id,
                "⚠️ 查無此學號或 LINE User ID。",
            )
            return True

        whitelist.pop(whitelist_key, None)
        save_json(WHITELIST_FILE, whitelist)

        send(
            line_bot_api,
            user_id,
            f"🗑️ 已移除 {record['name']}。",
        )
        return True

    # ---------------------------------------------------------
    # 停用帳號
    # ---------------------------------------------------------
    if user_input.startswith("disable "):
        parts = user_input.split(maxsplit=1)

        if len(parts) != 2 or not parts[1].strip():
            send(
                line_bot_api,
                user_id,
                "⚠️ 請輸入：disable 學號",
            )
            return True

        target = parts[1].strip()

        whitelist = load_json(WHITELIST_FILE)
        whitelist_key, record = find_record(whitelist, target)

        if whitelist_key is None or record is None:
            send(
                line_bot_api,
                user_id,
                "⚠️ 查無此學號或 LINE User ID。",
            )
            return True

        record["is_active"] = False
        whitelist[record["line_user_id"] or whitelist_key] = record

        if whitelist_key != (record["line_user_id"] or whitelist_key):
            whitelist.pop(whitelist_key, None)

        save_json(WHITELIST_FILE, whitelist)

        send(
            line_bot_api,
            user_id,
            f"⛔ 已停用 {record['name']}。",
        )
        return True

    # ---------------------------------------------------------
    # 啟用帳號
    # ---------------------------------------------------------
    if user_input.startswith("enable "):
        parts = user_input.split(maxsplit=1)

        if len(parts) != 2 or not parts[1].strip():
            send(
                line_bot_api,
                user_id,
                "⚠️ 請輸入：enable 學號",
            )
            return True

        target = parts[1].strip()

        whitelist = load_json(WHITELIST_FILE)
        whitelist_key, record = find_record(whitelist, target)

        if whitelist_key is None or record is None:
            send(
                line_bot_api,
                user_id,
                "⚠️ 查無此學號或 LINE User ID。",
            )
            return True

        record["is_active"] = True
        whitelist[record["line_user_id"] or whitelist_key] = record

        if whitelist_key != (record["line_user_id"] or whitelist_key):
            whitelist.pop(whitelist_key, None)

        save_json(WHITELIST_FILE, whitelist)

        send(
            line_bot_api,
            user_id,
            f"✅ 已啟用 {record['name']}。",
        )
        return True

    return False
