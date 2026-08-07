import json
import os

from linebot import LineBotApi

WHITELIST_FILE = "whitelist.json"


def load_whitelist_user_ids():
    try:
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}

    user_ids = set()

    if isinstance(data, dict):
        # 目前系統 whitelist 以 LINE user id 作為 key。
        for key, record in data.items():
            key = str(key or "").strip()
            if key.startswith("U"):
                user_ids.add(key)

            if isinstance(record, dict):
                for field in ("line_user_id", "line_id", "LINE_ID"):
                    value = str(record.get(field) or "").strip()
                    if value.startswith("U"):
                        user_ids.add(value)

    return user_ids


def load_test_bypass_user_ids():
    raw = os.getenv("TEST_BYPASS_LINE_USER_IDS", "")
    return {
        item.strip()
        for item in raw.split(",")
        if item.strip().startswith("U")
    }


def main():
    token = os.getenv("CHANNEL_ACCESS_TOKEN", "").strip()
    rich_menu_id = os.getenv("RICH_MENU_ID", "").strip()

    if not token:
        raise RuntimeError("找不到 CHANNEL_ACCESS_TOKEN")

    if not rich_menu_id:
        raise RuntimeError("找不到 RICH_MENU_ID")

    user_ids = load_whitelist_user_ids() | load_test_bypass_user_ids()

    if not user_ids:
        print("沒有找到可重新綁定的 approved/test user。")
        return

    line_bot_api = LineBotApi(token)

    success = 0
    failed = 0

    print("準備重新綁定 Rich Menu")
    print("RICH_MENU_ID =", rich_menu_id)
    print("使用者數 =", len(user_ids))

    for user_id in sorted(user_ids):
        try:
            line_bot_api.link_rich_menu_to_user(user_id, rich_menu_id)
            success += 1
            print("OK:", user_id[:5] + "..." + user_id[-4:])
        except Exception as exc:
            failed += 1
            print("FAILED:", user_id[:5] + "..." + user_id[-4:], repr(exc))

    print()
    print("Rich Menu 重新綁定完成")
    print("成功 =", success)
    print("失敗 =", failed)


if __name__ == "__main__":
    main()
